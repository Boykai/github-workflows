"""Tests for workflow API routes (src/api/workflow.py).

Covers:
- POST /api/v1/workflow/recommendations/{id}/confirm
- POST /api/v1/workflow/recommendations/{id}/reject
- GET  /api/v1/workflow/config
- PUT  /api/v1/workflow/config
- GET  /api/v1/workflow/agents
- GET  /api/v1/workflow/transitions
- GET  /api/v1/workflow/pipeline-states
- GET  /api/v1/workflow/pipeline-states/{issue_number}
- POST /api/v1/workflow/notify/in-review
- GET  /api/v1/workflow/polling/status
- POST /api/v1/workflow/polling/stop
- POST /api/v1/workflow/polling/start
- POST /api/v1/workflow/polling/check-issue/{issue_number}
- POST /api/v1/workflow/polling/check-all
- _check_duplicate helper
- _get_repository_info helper
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from src.api.workflow import _check_duplicate, _get_repository_info, _recent_requests
from src.models.chat import (
    IssueRecommendation,
    RecommendationStatus,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)
from src.models.user import UserSession
from src.utils import utcnow

# ── Helpers ─────────────────────────────────────────────────────────────────

SESSION_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_PROJECT_ID = "PVT_wf_test"


def _recommendation(**kw) -> IssueRecommendation:
    defaults = {
        "recommendation_id": uuid4(),
        "session_id": SESSION_ID,
        "original_input": "Add CSV export",
        "title": "CSV Export Feature",
        "user_story": "As a user I want CSV export",
        "ui_ux_description": "Export button in profile",
        "functional_requirements": ["Must export CSV"],
    }
    defaults.update(kw)
    return IssueRecommendation(**defaults)


def _workflow_config(**kw) -> WorkflowConfiguration:
    defaults = {
        "project_id": TEST_PROJECT_ID,
        "repository_owner": "testowner",
        "repository_name": "testrepo",
    }
    defaults.update(kw)
    return WorkflowConfiguration(**defaults)


@dataclass
class FakePipelineState:
    """Lightweight stand-in for PipelineState (a dataclass in orchestrator)."""

    issue_number: int = 42
    project_id: str = TEST_PROJECT_ID
    status: str = "In Progress"
    agents: list[str] = field(default_factory=lambda: ["copilot-coding"])
    current_agent_index: int = 0
    completed_agents: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    error: str | None = None

    @property
    def current_agent(self) -> str | None:
        if self.current_agent_index < len(self.agents):
            return self.agents[self.current_agent_index]
        return None

    @property
    def is_complete(self) -> bool:
        return self.current_agent_index >= len(self.agents)


WF = "src.api.workflow"
ORCH = "src.services.workflow_orchestrator"


# ── Reject Recommendation ──────────────────────────────────────────────────


class TestRejectRecommendation:
    async def test_reject_pending(self, client, mock_session):
        rec = _recommendation(session_id=mock_session.session_id)
        rec_id = str(rec.recommendation_id)
        with patch(f"{WF}._recommendations", {rec_id: rec}):
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/reject")
        assert resp.status_code == 200
        assert resp.json()["recommendation_id"] == rec_id
        assert rec.status == RecommendationStatus.REJECTED

    async def test_reject_not_found(self, client):
        resp = await client.post("/api/v1/workflow/recommendations/nonexistent/reject")
        assert resp.status_code == 404

    async def test_reject_already_rejected(self, client, mock_session):
        rec = _recommendation(
            session_id=mock_session.session_id,
            status=RecommendationStatus.REJECTED,
        )
        rec_id = str(rec.recommendation_id)
        with patch(f"{WF}._recommendations", {rec_id: rec}):
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/reject")
        assert resp.status_code == 422  # ValidationError


# ── Workflow Config ─────────────────────────────────────────────────────────


class TestGetConfig:
    async def test_returns_existing_config(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        cfg = _workflow_config()
        with patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=cfg):
            resp = await client.get("/api/v1/workflow/config")
        assert resp.status_code == 200
        assert resp.json()["repository_owner"] == "testowner"

    async def test_returns_default_when_no_config(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        with (
            patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch(f"{WF}._get_repository_info", return_value=("me", "")),
        ):
            resp = await client.get("/api/v1/workflow/config")
        assert resp.status_code == 200
        assert resp.json()["repository_owner"] == "me"

    async def test_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.get("/api/v1/workflow/config")
        assert resp.status_code == 404


class TestUpdateConfig:
    async def test_update_config(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        body = _workflow_config().model_dump(mode="json")
        with patch(f"{WF}.set_workflow_config", new_callable=AsyncMock) as mock_set:
            resp = await client.put("/api/v1/workflow/config", json=body)
        assert resp.status_code == 200
        mock_set.assert_called_once()

    async def test_update_config_no_project(self, client, mock_session):
        mock_session.selected_project_id = None
        body = _workflow_config().model_dump(mode="json")
        resp = await client.put("/api/v1/workflow/config", json=body)
        assert resp.status_code == 404


# ── List Agents ─────────────────────────────────────────────────────────────


class TestListAgents:
    async def test_list_agents(self, client, mock_session, mock_github_service):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.list_available_agents.return_value = []
        with patch(
            f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=_workflow_config()
        ):
            resp = await client.get("/api/v1/workflow/agents")
        assert resp.status_code == 200
        assert "agents" in resp.json()

    async def test_no_project(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.get("/api/v1/workflow/agents")
        assert resp.status_code == 404


# ── Transitions ─────────────────────────────────────────────────────────────


class TestTransitions:
    async def test_returns_transitions(self, client):
        t = WorkflowTransition(
            issue_id="I_1",
            project_id=TEST_PROJECT_ID,
            to_status="Ready",
            triggered_by="automatic",
            success=True,
        )
        with patch(f"{WF}.get_transitions", return_value=[t]):
            resp = await client.get("/api/v1/workflow/transitions")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_filter_by_issue(self, client):
        with patch(f"{WF}.get_transitions", return_value=[]) as mock_get:
            resp = await client.get("/api/v1/workflow/transitions", params={"issue_id": "I_1"})
        assert resp.status_code == 200
        mock_get.assert_called_once_with(issue_id="I_1", limit=50)


# ── Pipeline States ────────────────────────────────────────────────────────


class TestPipelineStates:
    async def test_list_all(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        ps = FakePipelineState()
        with patch(f"{WF}.get_all_pipeline_states", return_value={42: ps}):
            resp = await client.get("/api/v1/workflow/pipeline-states")
        data = resp.json()
        assert resp.status_code == 200
        assert data["count"] == 1

    async def test_empty(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        with patch(f"{WF}.get_all_pipeline_states", return_value={}):
            resp = await client.get("/api/v1/workflow/pipeline-states")
        assert resp.json()["count"] == 0


class TestGetPipelineStateForIssue:
    async def test_found(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        ps = FakePipelineState()
        with patch(f"{WF}.get_pipeline_state", return_value=ps):
            resp = await client.get("/api/v1/workflow/pipeline-states/42")
        assert resp.status_code == 200
        assert resp.json()["issue_number"] == 42

    async def test_not_found(self, client, mock_session):
        mock_session.selected_project_id = TEST_PROJECT_ID
        with patch(f"{WF}.get_pipeline_state", return_value=None):
            resp = await client.get("/api/v1/workflow/pipeline-states/999")
        assert resp.status_code == 404


# ── Notify In Review ───────────────────────────────────────────────────────


class TestNotifyInReview:
    async def test_send_notification(self, client, mock_session, mock_websocket_manager):
        mock_session.selected_project_id = TEST_PROJECT_ID
        resp = await client.post(
            "/api/v1/workflow/notify/in-review",
            params={
                "issue_id": "I_1",
                "issue_number": 42,
                "title": "Fix bug",
                "reviewer": "alice",
            },
        )
        assert resp.status_code == 200
        mock_websocket_manager.broadcast_to_project.assert_awaited_once()

    async def test_no_project(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.post(
            "/api/v1/workflow/notify/in-review",
            params={
                "issue_id": "I_1",
                "issue_number": 42,
                "title": "Fix bug",
                "reviewer": "alice",
            },
        )
        assert resp.status_code == 404


# ── Polling Status/Stop ────────────────────────────────────────────────────


class TestPollingStatus:
    async def test_get_status(self, client):
        status = {"is_running": False, "iterations": 0}
        with patch(
            f"{WF}.get_polling_status",
            create=True,
            return_value=status,
        ):
            # The endpoint imports get_polling_status dynamically.
            # We need to patch it at the copilot_polling service level.
            with patch(
                "src.services.copilot_polling.get_polling_status",
                return_value=status,
            ):
                resp = await client.get("/api/v1/workflow/polling/status")
        assert resp.status_code == 200
        assert resp.json()["is_running"] is False


class TestStopPolling:
    async def test_stop_when_not_running(self, client):
        status = {"is_running": False, "iterations": 0}
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value=status,
            ),
            patch("src.services.copilot_polling.stop_polling"),
        ):
            resp = await client.post("/api/v1/workflow/polling/stop")
        assert resp.status_code == 200
        assert "not running" in resp.json()["message"].lower()


# ── Confirm Recommendation (happy path) ────────────────────────────────────


class TestConfirmRecommendation:
    async def test_not_found(self, client):
        resp = await client.post("/api/v1/workflow/recommendations/missing/confirm")
        assert resp.status_code == 404

    async def test_already_confirmed(self, client, mock_session):
        rec = _recommendation(
            session_id=mock_session.session_id,
            status=RecommendationStatus.CONFIRMED,
        )
        rec_id = str(rec.recommendation_id)
        with patch(f"{WF}._recommendations", {rec_id: rec}):
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/confirm")
        assert resp.status_code == 422

    async def test_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        rec = _recommendation(session_id=mock_session.session_id)
        rec_id = str(rec.recommendation_id)
        with patch(f"{WF}._recommendations", {rec_id: rec}):
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/confirm")
        assert resp.status_code == 422

    async def test_confirm_success(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = TEST_PROJECT_ID
        rec = _recommendation(session_id=mock_session.session_id)
        rec_id = str(rec.recommendation_id)

        mock_github_service.get_project_repository.return_value = (
            "testowner",
            "testrepo",
        )

        wf_result = WorkflowResult(
            success=True,
            issue_id="I_99",
            issue_number=99,
            issue_url="https://github.com/testowner/testrepo/issues/99",
            project_item_id="PVTI_99",
            current_status="Backlog",
            message="Created issue #99",
        )
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_full_workflow.return_value = wf_result

        with (
            patch(f"{WF}._recommendations", {rec_id: rec}),
            patch(f"{WF}._recent_requests", {}),
            patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch(f"{WF}.set_workflow_config", new_callable=AsyncMock),
            patch(f"{WF}.get_workflow_orchestrator", return_value=mock_orchestrator),
            patch(f"{WF}.get_agent_slugs", return_value=["copilot-coding"]),
            patch(
                "src.services.copilot_polling.get_polling_status", return_value={"is_running": True}
            ),
            patch("src.config.get_settings") as mock_settings,
        ):
            mock_settings.return_value = MagicMock(
                default_assignee="copilot",
                default_repo_owner="testowner",
                default_repo_name="testrepo",
            )
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/confirm")

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["issue_number"] == 99

    async def test_confirm_workflow_failure(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """When orchestrator raises, endpoint returns success=False."""
        mock_session.selected_project_id = TEST_PROJECT_ID
        rec = _recommendation(session_id=mock_session.session_id)
        rec_id = str(rec.recommendation_id)

        mock_github_service.get_project_repository.return_value = ("o", "r")
        mock_orchestrator = AsyncMock()
        mock_orchestrator.execute_full_workflow.side_effect = Exception("boom")

        with (
            patch(f"{WF}._recommendations", {rec_id: rec}),
            patch(f"{WF}._recent_requests", {}),
            patch(
                f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=_workflow_config()
            ),
            patch(f"{WF}.set_workflow_config", new_callable=AsyncMock),
            patch(f"{WF}.get_workflow_orchestrator", return_value=mock_orchestrator),
            patch("src.config.get_settings") as ms,
        ):
            ms.return_value = MagicMock(default_assignee="copilot")
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/confirm")

        assert resp.status_code == 200
        assert resp.json()["success"] is False

    async def test_confirm_duplicate_detection(self, client, mock_session):
        """Duplicate request within window raises ValidationError."""
        mock_session.selected_project_id = TEST_PROJECT_ID
        rec = _recommendation(session_id=mock_session.session_id)
        rec_id = str(rec.recommendation_id)

        import hashlib

        input_hash = hashlib.sha256(rec.original_input.encode()).hexdigest()
        fake_recent = {input_hash: (utcnow(), "other-rec-id")}

        with (
            patch(f"{WF}._recommendations", {rec_id: rec}),
            patch(f"{WF}._recent_requests", fake_recent),
        ):
            resp = await client.post(f"/api/v1/workflow/recommendations/{rec_id}/confirm")

        assert resp.status_code == 422


# ── _check_duplicate Helper ───────────────────────────────────────────────


class TestCheckDuplicate:
    def setup_method(self):
        _recent_requests.clear()

    def test_first_request_not_duplicate(self):
        assert _check_duplicate("hello", "rec-1") is False

    def test_same_input_same_id_not_duplicate(self):
        _check_duplicate("hello", "rec-1")
        assert _check_duplicate("hello", "rec-1") is False

    def test_same_input_different_id_is_duplicate(self):
        _check_duplicate("hello", "rec-1")
        assert _check_duplicate("hello", "rec-2") is True

    def test_expired_entries_cleaned(self):
        import hashlib

        h = hashlib.sha256(b"old").hexdigest()
        _recent_requests[h] = (utcnow() - timedelta(minutes=10), "old-id")
        _check_duplicate("new", "rec-1")
        assert h not in _recent_requests

    def teardown_method(self):
        _recent_requests.clear()


# ── _get_repository_info Helper ───────────────────────────────────────────


class TestGetRepositoryInfo:
    def test_no_cached_projects(self):
        session = MagicMock(spec=UserSession)
        session.github_user_id = "u1"
        session.selected_project_id = "proj-1"
        session.github_username = "myuser"
        with patch(f"{WF}.cache") as mock_cache:
            mock_cache.get.return_value = None
            owner, repo = _get_repository_info(session)
        assert owner == "myuser"
        assert repo == ""

    def test_user_project_url(self):
        session = MagicMock(spec=UserSession)
        session.github_user_id = "u1"
        session.selected_project_id = "proj-1"
        session.github_username = "fallback"
        mock_project = MagicMock(
            project_id="proj-1", url="https://github.com/users/alice/projects/2"
        )
        with patch(f"{WF}.cache") as mock_cache:
            mock_cache.get.return_value = [mock_project]
            owner, repo = _get_repository_info(session)
        assert owner == "alice"
        assert repo == ""

    def test_org_project_url(self):
        session = MagicMock(spec=UserSession)
        session.github_user_id = "u1"
        session.selected_project_id = "proj-1"
        session.github_username = "fallback"
        mock_project = MagicMock(
            project_id="proj-1", url="https://github.com/orgs/myorg/projects/5"
        )
        with patch(f"{WF}.cache") as mock_cache:
            mock_cache.get.return_value = [mock_project]
            owner, repo = _get_repository_info(session)
        assert owner == "myorg"
        assert repo == ""

    def test_no_matching_project(self):
        session = MagicMock(spec=UserSession)
        session.github_user_id = "u1"
        session.selected_project_id = "proj-1"
        session.github_username = "me"
        mock_project = MagicMock(project_id="proj-other", url="")
        with patch(f"{WF}.cache") as mock_cache:
            mock_cache.get.return_value = [mock_project]
            owner, repo = _get_repository_info(session)
        assert owner == "me"


# ── Polling Check Issue ───────────────────────────────────────────────────


class TestCheckIssueCopilotCompletion:
    async def test_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.post("/api/v1/workflow/polling/check-issue/42")
        assert resp.status_code == 422

    async def test_no_repo_configured(self, client, mock_session, mock_github_service):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = None
        with (
            patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.config.get_settings") as ms,
        ):
            ms.return_value = MagicMock(default_repo_owner="", default_repo_name="")
            resp = await client.post("/api/v1/workflow/polling/check-issue/42")
        assert resp.status_code == 422

    async def test_check_issue_success_broadcasts(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = ("o", "r")
        result = {"status": "success", "task_title": "Bug", "pr_number": 10}
        with patch(
            "src.services.copilot_polling.check_issue_for_copilot_completion",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = await client.post("/api/v1/workflow/polling/check-issue/42")
        assert resp.status_code == 200
        mock_websocket_manager.broadcast_to_project.assert_awaited_once()

    async def test_check_issue_no_update(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = ("o", "r")
        result = {"status": "no_pr_found"}
        with patch(
            "src.services.copilot_polling.check_issue_for_copilot_completion",
            new_callable=AsyncMock,
            return_value=result,
        ):
            resp = await client.post("/api/v1/workflow/polling/check-issue/42")
        assert resp.status_code == 200
        mock_websocket_manager.broadcast_to_project.assert_not_awaited()

    async def test_check_issue_falls_back_to_config(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        """Falls back to workflow config when get_project_repository returns None."""
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = None
        result = {"status": "no_pr_found"}
        with (
            patch(
                f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=_workflow_config()
            ),
            patch(
                "src.services.copilot_polling.check_issue_for_copilot_completion",
                new_callable=AsyncMock,
                return_value=result,
            ),
        ):
            resp = await client.post("/api/v1/workflow/polling/check-issue/42")
        assert resp.status_code == 200


# ── Polling Start ─────────────────────────────────────────────────────────


class TestStartPolling:
    async def test_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.post("/api/v1/workflow/polling/start")
        assert resp.status_code == 422

    async def test_already_running(self, client, mock_session, mock_github_service):
        mock_session.selected_project_id = TEST_PROJECT_ID
        with patch(
            "src.services.copilot_polling.get_polling_status",
            return_value={"is_running": True, "iterations": 5},
        ):
            resp = await client.post("/api/v1/workflow/polling/start")
        assert resp.status_code == 200
        assert "already running" in resp.json()["message"].lower()

    async def test_start_success(self, client, mock_session, mock_github_service):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = ("o", "r")
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(
                "src.services.copilot_polling.poll_for_copilot_completion",
                new_callable=AsyncMock,
            ),
            patch("src.services.copilot_polling._polling_task", None),
        ):
            resp = await client.post("/api/v1/workflow/polling/start")
        assert resp.status_code == 200
        assert "started" in resp.json()["message"].lower()

    async def test_start_no_repo_configured(self, client, mock_session, mock_github_service):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = None
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                return_value={"is_running": False},
            ),
            patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.config.get_settings") as ms,
        ):
            ms.return_value = MagicMock(default_repo_owner="", default_repo_name="")
            resp = await client.post("/api/v1/workflow/polling/start")
        assert resp.status_code == 422


# ── Polling Check All ─────────────────────────────────────────────────────


class TestCheckAllInProgressIssues:
    async def test_no_project_selected(self, client, mock_session):
        mock_session.selected_project_id = None
        resp = await client.post("/api/v1/workflow/polling/check-all")
        assert resp.status_code == 422

    async def test_check_all_with_results(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = ("o", "r")
        results = [
            {"status": "success", "issue_number": 1, "task_title": "A", "pr_number": 10},
            {"status": "no_pr_found", "issue_number": 2},
        ]
        with patch(
            "src.services.copilot_polling.check_in_progress_issues",
            new_callable=AsyncMock,
            return_value=results,
        ):
            resp = await client.post("/api/v1/workflow/polling/check-all")
        assert resp.status_code == 200
        assert resp.json()["checked_count"] == 2
        # Only 1 success should broadcast
        assert mock_websocket_manager.broadcast_to_project.await_count == 1

    async def test_check_all_no_repo(self, client, mock_session, mock_github_service):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = None
        with (
            patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.config.get_settings") as ms,
        ):
            ms.return_value = MagicMock(default_repo_owner="", default_repo_name="")
            resp = await client.post("/api/v1/workflow/polling/check-all")
        assert resp.status_code == 422

    async def test_check_all_falls_back_to_settings(
        self, client, mock_session, mock_github_service, mock_websocket_manager
    ):
        mock_session.selected_project_id = TEST_PROJECT_ID
        mock_github_service.get_project_repository.return_value = None
        with (
            patch(f"{WF}.get_workflow_config", new_callable=AsyncMock, return_value=None),
            patch("src.config.get_settings") as ms,
            patch(
                "src.services.copilot_polling.check_in_progress_issues",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            ms.return_value = MagicMock(
                default_repo_owner="def_owner", default_repo_name="def_repo"
            )
            resp = await client.post("/api/v1/workflow/polling/check-all")
        assert resp.status_code == 200


# ── Stop Polling When Running ─────────────────────────────────────────────


class TestStopPollingRunning:
    async def test_stop_when_running(self, client):
        status_running = {"is_running": True, "iterations": 10}
        status_stopped = {"is_running": False, "iterations": 10}
        with (
            patch(
                "src.services.copilot_polling.get_polling_status",
                side_effect=[status_running, status_stopped],
            ),
            patch("src.services.copilot_polling.stop_polling") as mock_stop,
        ):
            resp = await client.post("/api/v1/workflow/polling/stop")
        assert resp.status_code == 200
        assert "stopped" in resp.json()["message"].lower()
        mock_stop.assert_called_once()
