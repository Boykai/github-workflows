"""Tests for chat API routes (src/api/chat.py).

Covers:
- GET    /api/v1/chat/messages                     → get_messages
- DELETE /api/v1/chat/messages                     → clear_messages
- POST   /api/v1/chat/messages                     → send_message (branches)
- POST   /api/v1/chat/proposals/{id}/confirm       → confirm_proposal
- DELETE /api/v1/chat/proposals/{id}               → cancel_proposal
- _resolve_repository                              → all fallback branches
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.models.chat import (
    AITaskProposal,
    IssueRecommendation,
    ProposalStatus,
)
from src.models.task import Task
from src.models.user import UserSession

# ── Helpers ─────────────────────────────────────────────────────────────────


def _recommendation(session_id, **kw) -> IssueRecommendation:
    defaults = {
        "session_id": session_id,
        "original_input": "add dark mode",
        "title": "Add dark mode",
        "user_story": "As a user I want dark mode",
        "ui_ux_description": "Toggle in header",
        "functional_requirements": ["Must toggle theme"],
    }
    defaults.update(kw)
    return IssueRecommendation(**defaults)


def _proposal(session_id, **kw) -> AITaskProposal:
    defaults = {
        "session_id": session_id,
        "original_input": "fix login bug",
        "proposed_title": "Fix login bug",
        "proposed_description": "Fix the login flow",
    }
    defaults.update(kw)
    return AITaskProposal(**defaults)


# ── GET /chat/messages ──────────────────────────────────────────────────────


class TestGetMessages:
    async def test_empty_messages(self, client):
        resp = await client.get("/api/v1/chat/messages")
        assert resp.status_code == 200
        assert resp.json()["messages"] == []


# ── DELETE /chat/messages ───────────────────────────────────────────────────


class TestClearMessages:
    async def test_clear_messages(self, client):
        resp = await client.delete("/api/v1/chat/messages")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Chat history cleared"


# ── POST /chat/messages — feature request path ─────────────────────────────


class TestSendMessageFeatureRequest:
    async def test_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.post("/api/v1/chat/messages", json={"content": "add dark mode"})
        assert resp.status_code == 422

    async def test_ai_not_configured(self, client, mock_session, mock_ai_agent_service):
        mock_session.selected_project_id = "PVT_1"
        with patch("src.api.chat.get_ai_agent_service", side_effect=ValueError("not configured")):
            resp = await client.post("/api/v1/chat/messages", json={"content": "add dark mode"})
        assert resp.status_code == 200
        data = resp.json()
        assert "not configured" in data["content"].lower() or "AI features" in data["content"]

    async def test_feature_request_generates_recommendation(
        self, client, mock_session, mock_ai_agent_service
    ):
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = True

        rec = _recommendation(mock_session.session_id)
        mock_ai_agent_service.generate_issue_recommendation.return_value = rec

        resp = await client.post(
            "/api/v1/chat/messages", json={"content": "I want dark mode support"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_type"] == "issue_create"
        assert "recommendation_id" in data["action_data"]

    async def test_feature_detection_fails_gracefully(
        self, client, mock_session, mock_ai_agent_service
    ):
        """If feature detection throws, falls through to status/task branch."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.side_effect = RuntimeError("ai down")
        mock_ai_agent_service.parse_status_change_request.return_value = None
        mock_ai_agent_service.generate_task_from_description.return_value = MagicMock(
            title="Dark mode", description="Add dark mode feature"
        )
        resp = await client.post("/api/v1/chat/messages", json={"content": "add dark mode"})
        assert resp.status_code == 200
        # Falls through to task generation
        data = resp.json()
        assert data["action_type"] == "task_create"


# ── POST /chat/messages — status change path ───────────────────────────────


class TestSendMessageStatusChange:
    async def test_status_change_found(self, client, mock_session, mock_ai_agent_service):
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False

        # Build a status change response
        status_change = MagicMock()
        status_change.task_reference = "login bug"
        status_change.target_status = "Done"
        mock_ai_agent_service.parse_status_change_request.return_value = status_change

        # Need cached tasks for identify_target_task
        target_task = Task(
            project_id="PVT_1",
            github_item_id="PVTI_1",
            title="Fix login bug",
            status="In Progress",
            status_option_id="opt2",
        )
        mock_ai_agent_service.identify_target_task = MagicMock(return_value=target_task)

        # cache.get is called multiple times with different keys:
        # 1st: user_projects cache → return None (no projects)
        # 2nd: project_items cache → return tasks list
        def _cache_get(key):
            if "items" in key:
                return [target_task]
            return None

        with patch("src.api.chat.cache") as mock_cache:
            mock_cache.get.side_effect = _cache_get
            resp = await client.post(
                "/api/v1/chat/messages",
                json={"content": "move login bug to Done"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_type"] == "status_update"

    async def test_status_change_task_not_found(self, client, mock_session, mock_ai_agent_service):
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False

        status_change = MagicMock()
        status_change.task_reference = "nonexistent"
        status_change.target_status = "Done"
        mock_ai_agent_service.parse_status_change_request.return_value = status_change
        mock_ai_agent_service.identify_target_task = MagicMock(return_value=None)

        with patch("src.api.chat.cache") as mock_cache:
            mock_cache.get.return_value = None
            resp = await client.post(
                "/api/v1/chat/messages",
                json={"content": "move X to Done"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "couldn't find" in data["content"].lower()


# ── POST /chat/messages — task generation path ─────────────────────────────


class TestSendMessageTaskGeneration:
    async def test_generates_task_proposal(self, client, mock_session, mock_ai_agent_service):
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False
        mock_ai_agent_service.parse_status_change_request.return_value = None

        generated = MagicMock()
        generated.title = "Fix auth bug"
        generated.description = "Fix the authentication flow bug in the login page"
        mock_ai_agent_service.generate_task_from_description.return_value = generated

        resp = await client.post("/api/v1/chat/messages", json={"content": "fix the auth bug"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_type"] == "task_create"
        assert data["action_data"]["proposed_title"] == "Fix auth bug"

    async def test_task_generation_error(self, client, mock_session, mock_ai_agent_service):
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False
        mock_ai_agent_service.parse_status_change_request.return_value = None
        mock_ai_agent_service.generate_task_from_description.side_effect = RuntimeError("AI error")
        resp = await client.post("/api/v1/chat/messages", json={"content": "do something"})
        assert resp.status_code == 200
        assert "couldn't generate" in resp.json()["content"].lower()

    async def test_ai_enhance_off_uses_raw_input(self, client, mock_session, mock_ai_agent_service):
        """When ai_enhance=False, raw user input is used as description, title is AI-generated."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False
        mock_ai_agent_service.parse_status_change_request.return_value = None
        mock_ai_agent_service.generate_title_from_description.return_value = "Fix login flow"

        user_input = "The login page has a bug where users can't sign in"
        resp = await client.post(
            "/api/v1/chat/messages",
            json={"content": user_input, "ai_enhance": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_type"] == "task_create"
        assert data["action_data"]["proposed_title"] == "Fix login flow"
        assert data["action_data"]["proposed_description"] == user_input
        # generate_task_from_description must NOT be called
        mock_ai_agent_service.generate_task_from_description.assert_not_called()

    async def test_ai_enhance_off_metadata_error_returns_specific_message(
        self, client, mock_session, mock_ai_agent_service
    ):
        """When the fallback branch fails after title generation, show a specific error."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False
        mock_ai_agent_service.parse_status_change_request.return_value = None
        mock_ai_agent_service.generate_title_from_description.return_value = "Some task"

        with patch("src.api.chat.AITaskProposal", side_effect=RuntimeError("storage failed")):
            resp = await client.post(
                "/api/v1/chat/messages",
                json={"content": "some task", "ai_enhance": False},
            )
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "metadata" in content.lower()
        assert "preserved" in content.lower()
        # Must NOT show the generic error
        assert "couldn't generate a task" not in content.lower()

    async def test_ai_enhance_on_uses_full_pipeline(
        self, client, mock_session, mock_ai_agent_service
    ):
        """When ai_enhance=True (default), the full AI pipeline is used."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False
        mock_ai_agent_service.parse_status_change_request.return_value = None

        generated = MagicMock()
        generated.title = "Enhanced Title"
        generated.description = "AI-enhanced description of the task"
        mock_ai_agent_service.generate_task_from_description.return_value = generated

        resp = await client.post(
            "/api/v1/chat/messages",
            json={"content": "do something", "ai_enhance": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_data"]["proposed_title"] == "Enhanced Title"
        assert data["action_data"]["proposed_description"] == "AI-enhanced description of the task"
        # generate_title_from_description must NOT be called
        mock_ai_agent_service.generate_title_from_description.assert_not_called()


# ── POST /chat/proposals/{id}/confirm ───────────────────────────────────────


class TestConfirmProposal:
    async def test_proposal_not_found(self, client):
        resp = await client.post(
            "/api/v1/chat/proposals/nonexistent/confirm",
            json={},
        )
        assert resp.status_code == 404

    async def test_confirm_creates_issue(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = "PVT_1"
        proposal = _proposal(mock_session.session_id)

        # Insert into module-level storage
        import src.api.chat as chat_mod

        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100010,
            "number": 10,
            "node_id": "I_10",
            "html_url": "https://github.com/owner/repo/issues/10",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_10"

        # Patch workflow functions to avoid side effects
        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=[]),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "confirmed"

        # Cleanup
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_confirm_wrong_session(self, client, mock_session):
        """Proposal owned by different session → 404."""
        other_session_id = uuid4()
        proposal = _proposal(other_session_id)

        import src.api.chat as chat_mod

        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        resp = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
        )
        assert resp.status_code == 404

        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_confirm_already_confirmed(self, client, mock_session):
        proposal = _proposal(mock_session.session_id)
        proposal.status = ProposalStatus.CONFIRMED

        import src.api.chat as chat_mod

        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        mock_session.selected_project_id = "PVT_1"
        resp = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
        )
        assert resp.status_code == 422

        chat_mod._proposals.pop(str(proposal.proposal_id), None)


# ── DELETE /chat/proposals/{id} ─────────────────────────────────────────────


class TestCancelProposal:
    async def test_cancel_success(self, client, mock_session):
        proposal = _proposal(mock_session.session_id)

        import src.api.chat as chat_mod

        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        resp = await client.delete(f"/api/v1/chat/proposals/{proposal.proposal_id}")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Proposal cancelled"

        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_cancel_not_found(self, client):
        resp = await client.delete("/api/v1/chat/proposals/nonexistent")
        assert resp.status_code == 404


# ── _resolve_repository (direct unit tests) ────────────────────────────────


class TestResolveRepository:
    """Direct tests for _resolve_repository covering all fallback branches."""

    async def test_no_project_selected_raises(self):
        from src.api.chat import _resolve_repository
        from src.exceptions import ValidationError

        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            selected_project_id=None,
        )
        with pytest.raises(ValidationError, match="No project selected"):
            await _resolve_repository(session)

    async def test_project_repository_found(self):
        from src.api.chat import _resolve_repository

        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            selected_project_id="PVT_1",
        )
        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = ("owner", "repo")
        with patch("src.services.github_projects.github_projects_service", mock_svc):
            result = await _resolve_repository(session)
        assert result == ("owner", "repo")

    async def test_workflow_config_fallback(self):
        from src.api.chat import _resolve_repository

        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            selected_project_id="PVT_1",
        )
        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = None
        mock_config = MagicMock(repository_owner="wf_owner", repository_name="wf_repo")
        with (
            patch("src.services.github_projects.github_projects_service", mock_svc),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                new_callable=AsyncMock,
                return_value=mock_config,
            ),
        ):
            result = await _resolve_repository(session)
        assert result == ("wf_owner", "wf_repo")

    async def test_settings_default_fallback(self):
        from src.api.chat import _resolve_repository

        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            selected_project_id="PVT_1",
        )
        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = None
        with (
            patch("src.services.github_projects.github_projects_service", mock_svc),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.config.get_settings") as mock_s,
        ):
            mock_s.return_value = MagicMock(
                default_repo_owner="def_owner", default_repo_name="def_repo"
            )
            result = await _resolve_repository(session)
        assert result == ("def_owner", "def_repo")

    async def test_all_fallbacks_fail_raises(self):
        from src.api.chat import _resolve_repository
        from src.exceptions import ValidationError

        session = UserSession(
            github_user_id="1",
            github_username="u",
            access_token="t",
            selected_project_id="PVT_1",
        )
        mock_svc = AsyncMock()
        mock_svc.get_project_repository.return_value = None
        with (
            patch("src.services.github_projects.github_projects_service", mock_svc),
            patch(
                "src.services.workflow_orchestrator.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.config.get_settings") as mock_s,
        ):
            mock_s.return_value = MagicMock(default_repo_owner=None, default_repo_name=None)
            with pytest.raises(ValidationError, match="No repository found"):
                await _resolve_repository(session)


# ── cancel_proposal (direct unit tests) ─────────────────────────────────────


class TestCancelProposalDirect:
    """Direct tests for cancel_proposal covering wrong-session and happy path."""

    async def test_cancel_wrong_session(self, client, mock_session):
        """Proposal owned by different session → 404."""
        import src.api.chat as chat_mod

        other_id = uuid4()
        proposal = _proposal(other_id)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        resp = await client.delete(f"/api/v1/chat/proposals/{proposal.proposal_id}")
        assert resp.status_code == 404
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_cancel_sets_status_cancelled(self, client, mock_session):
        """Should set proposal status to CANCELLED and add system message."""
        import src.api.chat as chat_mod

        proposal = _proposal(mock_session.session_id)
        await chat_mod.store_proposal(proposal)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        resp = await client.delete(f"/api/v1/chat/proposals/{proposal.proposal_id}")
        assert resp.status_code == 200
        assert proposal.status == ProposalStatus.CANCELLED
        chat_mod._proposals.pop(str(proposal.proposal_id), None)
        reloaded = await chat_mod.get_proposal(str(proposal.proposal_id))
        assert reloaded is not None
        assert reloaded.status == ProposalStatus.CANCELLED


# ── confirm_proposal edge cases (direct) ─────────────────────────────────


class TestConfirmProposalEdgeCases:
    """Tests for confirm_proposal edge cases: expired, edits."""

    async def test_confirm_expired_proposal(self, client, mock_session):
        """Expired proposal → 422 with expiration message."""
        from datetime import timedelta

        import src.api.chat as chat_mod
        from src.utils import utcnow

        proposal = _proposal(mock_session.session_id)
        # Force expiration by setting expires_at in the past
        proposal.expires_at = utcnow() - timedelta(hours=1)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        mock_session.selected_project_id = "PVT_1"
        resp = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
        )
        assert resp.status_code == 422
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_get_proposal_loads_persisted_timestamps_and_edits(self, client, mock_session):
        """SQLite reload should preserve proposal lifecycle fields."""
        from datetime import timedelta

        import src.api.chat as chat_mod
        from src.utils import utcnow

        created_at = utcnow()
        proposal = _proposal(
            mock_session.session_id,
            status=ProposalStatus.EDITED,
            edited_title="Edited title",
            edited_description="Edited description",
            created_at=created_at,
            expires_at=created_at + timedelta(minutes=5),
        )

        await chat_mod.store_proposal(proposal)
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

        loaded = await chat_mod.get_proposal(str(proposal.proposal_id))

        assert loaded is not None
        assert loaded.status == ProposalStatus.EDITED
        assert loaded.edited_title == "Edited title"
        assert loaded.edited_description == "Edited description"
        assert loaded.created_at.isoformat() == proposal.created_at.isoformat()
        assert loaded.expires_at.isoformat() == proposal.expires_at.isoformat()

    async def test_confirm_with_edited_title(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """Should apply edited title before creating issue."""
        import src.api.chat as chat_mod

        proposal = _proposal(mock_session.session_id)
        await chat_mod.store_proposal(proposal)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100020,
            "number": 20,
            "node_id": "I_20",
            "html_url": "https://github.com/owner/repo/issues/20",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_20"

        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=[]),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={"edited_title": "Better Title"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("edited", "confirmed")
        assert proposal.edited_title == "Better Title"
        chat_mod._proposals.pop(str(proposal.proposal_id), None)
        reloaded = await chat_mod.get_proposal(str(proposal.proposal_id))
        assert reloaded is not None
        assert reloaded.status == ProposalStatus.CONFIRMED
        assert reloaded.edited_title == "Better Title"
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_confirm_with_edited_description(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """Should apply edited description before creating issue."""
        import src.api.chat as chat_mod

        proposal = _proposal(mock_session.session_id)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100021,
            "number": 21,
            "node_id": "I_21",
            "html_url": "https://github.com/owner/repo/issues/21",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_21"

        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=[]),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={"edited_description": "Updated description text"},
            )

        assert resp.status_code == 200
        assert proposal.edited_description == "Updated description text"
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_confirm_proposal_applies_selected_pipeline_from_chat_mention(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """A selected chat pipeline must override project/user/default mappings on confirm."""
        import src.api.chat as chat_mod

        proposal = _proposal(mock_session.session_id, selected_pipeline_id="pipe-easy")
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100022,
            "number": 22,
            "node_id": "I_22",
            "html_url": "https://github.com/owner/repo/issues/22",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_22"

        selected_mappings = {
            "Backlog": [
                {
                    "slug": "easy",
                    "display_name": "Easy",
                }
            ]
        }

        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock) as mock_set_config,
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=["easy"]),
            patch(
                "src.services.workflow_orchestrator.config.load_pipeline_as_agent_mappings",
                new_callable=AsyncMock,
                return_value=(selected_mappings, "Easy", {}, {}),
            ) as mock_load_selected,
            patch(
                "src.services.workflow_orchestrator.config.resolve_project_pipeline_mappings",
                new_callable=AsyncMock,
            ) as mock_resolve_fallback,
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])

            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
            )

        assert resp.status_code == 200
        mock_load_selected.assert_awaited_once_with("PVT_1", "pipe-easy")
        mock_resolve_fallback.assert_not_called()
        set_config_call = mock_set_config.await_args_list[-1]
        assert set_config_call.args[1].agent_mappings == selected_mappings
        create_subissues_ctx = mock_orch.return_value.create_all_sub_issues.await_args.args[0]
        assert create_subissues_ctx.selected_pipeline_id == "pipe-easy"
        assert create_subissues_ctx.config.agent_mappings == selected_mappings
        assert proposal.pipeline_name == "Easy"
        assert proposal.pipeline_source == "pipeline"
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_feature_request_generation_error(
        self, client, mock_session, mock_ai_agent_service
    ):
        """Feature request recommendation generation failure → error message."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = True
        mock_ai_agent_service.generate_issue_recommendation.side_effect = RuntimeError("AI down")

        resp = await client.post("/api/v1/chat/messages", json={"content": "add dark mode"})
        assert resp.status_code == 200
        assert "couldn't generate" in resp.json()["content"].lower()


# ── Preserve full description tests ─────────────────────────────────────────


class TestConfirmProposalPreservesFullDescription:
    """T006, T010, T016, T018, T021: Verify confirm_proposal passes full descriptions unchanged."""

    async def test_full_description_passed_unchanged(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """T006: confirm_proposal passes the full final_description to create_issue(body=...)."""
        import src.api.chat as chat_mod

        long_desc = "A" * 10_000
        proposal = _proposal(mock_session.session_id, proposed_description=long_desc)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100030,
            "number": 30,
            "node_id": "I_30",
            "html_url": "https://github.com/owner/repo/issues/30",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_30"

        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=[]),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
            )

        assert resp.status_code == 200
        # Verify the full body was passed to create_issue
        call_kwargs = mock_github_service.create_issue.call_args
        assert call_kwargs.kwargs["body"] == long_desc
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    @pytest.mark.parametrize("length", [256, 1024, 4096, 32768, 65536])
    async def test_boundary_length_descriptions_preserved(
        self, client, mock_session, mock_github_service, mock_websocket_manager, length
    ):
        """T010: Parametrized boundary-length tests for proposal path."""
        import src.api.chat as chat_mod

        desc = "B" * length
        proposal = _proposal(mock_session.session_id, proposed_description=desc)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100031,
            "number": 31,
            "node_id": "I_31",
            "html_url": "https://github.com/owner/repo/issues/31",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_31"

        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=[]),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
            )

        assert resp.status_code == 200
        call_kwargs = mock_github_service.create_issue.call_args
        assert call_kwargs.kwargs["body"] == desc
        assert len(call_kwargs.kwargs["body"]) == length
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_oversized_description_returns_422(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """T016: confirm_proposal returns HTTP 422 when description exceeds 65,536 chars."""
        import src.api.chat as chat_mod

        oversized_desc = "C" * 65_537
        proposal = _proposal(mock_session.session_id, proposed_description=oversized_desc[:65_536])
        # Bypass Pydantic max_length by setting the field directly
        object.__setattr__(proposal, "proposed_description", oversized_desc)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")

        resp = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
        )
        assert resp.status_code == 422
        resp_json = resp.json()
        assert "exceeds" in resp_json["error"].lower()
        # Verify structured details payload is preserved (not lost by
        # exception re-wrapping) per the issue-creation contract.
        assert resp_json["details"]["body_length"] == 65_537
        assert resp_json["details"]["max_length"] == 65_536
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_exactly_65537_chars_fails(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """T018: Body at exactly 65,537 chars fails with 422."""
        import src.api.chat as chat_mod

        desc = "D" * 65_537
        proposal = _proposal(mock_session.session_id, proposed_description="short")
        object.__setattr__(proposal, "proposed_description", desc)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")

        resp = await client.post(
            f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
            json={},
        )
        assert resp.status_code == 422
        # Verify the 422 response includes the structured details payload.
        resp_json = resp.json()
        assert resp_json["details"]["body_length"] == 65_537
        assert resp_json["details"]["max_length"] == 65_536
        chat_mod._proposals.pop(str(proposal.proposal_id), None)

    async def test_rich_markdown_description_preserved(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """T021: Rich markdown description is preserved through proposal path."""
        import src.api.chat as chat_mod

        markdown_desc = (
            "# Feature Request\n\n"
            "## Overview\n\n"
            "- bullet point 1\n"
            "- bullet point 2\n"
            "  - nested bullet\n\n"
            "```python\ndef hello():\n    print('world')\n```\n\n"
            "> blockquote with **bold** and *italic*\n\n"
            "| Header1 | Header2 |\n|---------|----------|\n| cell1 | cell2 |\n\n"
            "[link](https://example.com) and `inline code`\n\n"
            "---\n\n"
            "~~strikethrough~~ and 🚀 emoji\n"
        )
        proposal = _proposal(mock_session.session_id, proposed_description=markdown_desc)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal
        mock_session.selected_project_id = "PVT_1"

        mock_github_service.get_project_repository.return_value = ("owner", "repo")
        mock_github_service.create_issue.return_value = {
            "id": 100032,
            "number": 32,
            "node_id": "I_32",
            "html_url": "https://github.com/owner/repo/issues/32",
        }
        mock_github_service.add_issue_to_project.return_value = "PVTI_32"

        with (
            patch("src.api.chat.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.api.chat.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.chat.get_workflow_orchestrator") as mock_orch,
            patch("src.api.chat.get_agent_slugs", return_value=[]),
        ):
            mock_orch.return_value.assign_agent_for_status = AsyncMock()
            mock_orch.return_value.create_all_sub_issues = AsyncMock(return_value=[])
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
            )

        assert resp.status_code == 200
        call_kwargs = mock_github_service.create_issue.call_args
        assert call_kwargs.kwargs["body"] == markdown_desc
        chat_mod._proposals.pop(str(proposal.proposal_id), None)


# ── Regression: error messages MUST NOT leak exception details ──────────────


class TestErrorMessageSanitization:
    """Bug-bash regression: chat error messages must not expose internal
    exception details to the end user (information leakage)."""

    async def test_agent_command_error_does_not_leak_exception(
        self, client, mock_session, mock_ai_agent_service
    ):
        """#agent command errors must not include raw exception text."""
        mock_session.selected_project_id = "PVT_1"
        with patch(
            "src.services.agent_creator.handle_agent_command",
            side_effect=RuntimeError("secret db error"),
        ):
            with patch("src.services.agent_creator.get_active_session", return_value=None):
                resp = await client.post(
                    "/api/v1/chat/messages", json={"content": "#agent create foo"}
                )
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "secret db error" not in content
        assert "unexpected error" in content.lower() or "Error" in content

    async def test_task_generation_error_does_not_leak_exception(
        self, client, mock_session, mock_ai_agent_service
    ):
        """Task generation failure message must not include raw exception."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = False
        mock_ai_agent_service.parse_status_change_request.return_value = None
        mock_ai_agent_service.generate_task_from_description.side_effect = RuntimeError(
            "internal: connection refused to ai-backend:8080"
        )
        resp = await client.post("/api/v1/chat/messages", json={"content": "do something"})
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "connection refused" not in content
        assert "ai-backend" not in content

    async def test_recommendation_error_does_not_leak_exception(
        self, client, mock_session, mock_ai_agent_service
    ):
        """Issue recommendation failure message must not include raw exception."""
        mock_session.selected_project_id = "PVT_1"
        mock_ai_agent_service.detect_feature_request_intent.return_value = True
        mock_ai_agent_service.generate_issue_recommendation.side_effect = RuntimeError(
            "internal: model_endpoint timed out after 30s"
        )
        resp = await client.post("/api/v1/chat/messages", json={"content": "I want a new feature"})
        assert resp.status_code == 200
        content = resp.json()["content"]
        assert "model_endpoint" not in content
        assert "timed out" not in content

    async def test_confirm_proposal_error_does_not_leak_exception(
        self, client, mock_session, mock_github_service
    ):
        """confirm_proposal must not leak internal exception details."""
        import src.api.chat as chat_mod

        mock_session.selected_project_id = "PVT_1"
        proposal = _proposal(mock_session.session_id)
        chat_mod._proposals[str(proposal.proposal_id)] = proposal

        mock_github_service.create_issue.side_effect = RuntimeError(
            "GraphQL error: token expired for user 12345"
        )

        with (
            patch(
                "src.api.chat.resolve_repository", new_callable=AsyncMock, return_value=("o", "r")
            ),
        ):
            resp = await client.post(
                f"/api/v1/chat/proposals/{proposal.proposal_id}/confirm",
                json={},
            )
        assert resp.status_code == 422
        body = resp.json()
        # Must not leak the internal error message
        assert "token expired" not in str(body)
        assert "12345" not in str(body)
        chat_mod._proposals.pop(str(proposal.proposal_id), None)


# ── POST /chat/upload — path-traversal regression ──────────────────────────


class TestUploadFilePathTraversal:
    """Regression tests for path-traversal vulnerability in file upload (bug-bash)."""

    async def test_path_traversal_filename_is_sanitised(self, client):
        """A filename containing '../' should be stripped to its base component."""
        import io

        file_content = b"harmless"
        resp = await client.post(
            "/api/v1/chat/upload",
            files={"file": ("../../etc/passwd.txt", io.BytesIO(file_content), "text/plain")},
        )
        assert resp.status_code == 200
        body = resp.json()
        # The traversal components must not appear in the returned URL
        assert "../" not in body["file_url"]
        assert "passwd.txt" in body["file_url"]

    async def test_normal_filename_accepted(self, client):
        """A simple filename should be accepted without modification."""
        import io

        file_content = b"hello"
        resp = await client.post(
            "/api/v1/chat/upload",
            files={"file": ("report.txt", io.BytesIO(file_content), "text/plain")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "report.txt" in body["file_url"]
        assert body["filename"] == "report.txt"

    async def test_blocked_type_rejected(self, client):
        """Executable file extensions should be rejected."""
        import io

        resp = await client.post(
            "/api/v1/chat/upload",
            files={"file": ("malware.exe", io.BytesIO(b"\x00"), "application/octet-stream")},
        )
        assert resp.status_code == 415
