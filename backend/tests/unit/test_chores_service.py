"""Unit tests for ChoresService and template builder."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.services.chores.template_builder import (
    build_template,
    derive_template_path,
    is_sparse_input,
)

# =============================================================================
# build_template
# =============================================================================


class TestBuildTemplate:
    """Tests for YAML front matter generation."""

    def test_adds_front_matter_to_plain_content(self):
        """Plain content gets default YAML front matter prepended."""
        result = build_template("Bug Bash", "Run a bug bash across the codebase")
        assert result.startswith("---")
        assert "name: Bug Bash" in result
        assert "about: Recurring chore — Bug Bash" in result
        assert "title: '[CHORE] Bug Bash'" in result
        assert "labels: chore" in result
        assert "Run a bug bash across the codebase" in result

    def test_preserves_existing_front_matter(self):
        """Content that already has front matter is used as-is."""
        content = "---\nname: Custom\nabout: My custom template\n---\n\nBody here"
        result = build_template("Custom", content)
        assert result.startswith("---")
        assert "name: Custom" in result
        assert "Body here" in result
        # Should NOT have double front matter
        assert result.count("---") == 2

    def test_whitespace_handling(self):
        """Content with leading whitespace before front matter is detected."""
        content = "  ---\nname: Spaced\n---\nBody"
        result = build_template("Spaced", content)
        # Should detect existing front matter
        assert result.count("name: Spaced") == 1


# =============================================================================
# derive_template_path
# =============================================================================


class TestDeriveTemplatePath:
    """Tests for template path generation."""

    def test_basic_slug(self):
        assert derive_template_path("Bug Bash") == ".github/ISSUE_TEMPLATE/chore-bug-bash.md"

    def test_special_characters(self):
        result = derive_template_path("Dependency Update (weekly)")
        assert result == ".github/ISSUE_TEMPLATE/chore-dependency-update-weekly.md"

    def test_numbers_preserved(self):
        result = derive_template_path("Sprint 42 Review")
        assert result == ".github/ISSUE_TEMPLATE/chore-sprint-42-review.md"


# =============================================================================
# is_sparse_input
# =============================================================================


class TestIsSparseInput:
    """Tests for sparse vs rich input detection heuristic."""

    def test_empty_is_sparse(self):
        assert is_sparse_input("") is True

    def test_short_phrase_is_sparse(self):
        assert is_sparse_input("create refactor chore") is True

    def test_medium_phrase_without_structure_is_sparse(self):
        assert is_sparse_input("bug bash review all code for security issues") is True

    def test_single_line_under_40_words_is_sparse(self):
        text = " ".join(["word"] * 30)
        assert is_sparse_input(text) is True

    def test_long_text_without_structure_is_rich(self):
        text = " ".join(["word"] * 50)
        assert is_sparse_input(text) is False

    def test_markdown_with_headings_is_rich(self):
        text = "## Overview\nThis is a bug bash\n\n## Steps\n1. Do this\n2. Do that"
        assert is_sparse_input(text) is False

    def test_markdown_with_lists_is_rich(self):
        text = "- Item one\n- Item two\n- Item three"
        assert is_sparse_input(text) is False

    def test_multi_paragraph_is_rich(self):
        text = "First paragraph\n\nSecond paragraph\n\nThird paragraph\n\nFourth"
        assert is_sparse_input(text) is False


# =============================================================================
# _strip_front_matter
# =============================================================================


class TestStripFrontMatter:
    """Tests for YAML front matter stripping from issue bodies."""

    def test_strips_yaml_front_matter(self):
        text = "---\nname: Bug Bash\nabout: Chore\n---\n## Steps\n1. Do stuff"
        from src.services.chores.service import _strip_front_matter

        assert _strip_front_matter(text) == "## Steps\n1. Do stuff"

    def test_no_front_matter_unchanged(self):
        text = "## Steps\n1. Do stuff"
        from src.services.chores.service import _strip_front_matter

        assert _strip_front_matter(text) == text

    def test_empty_string(self):
        from src.services.chores.service import _strip_front_matter

        assert _strip_front_matter("") == ""


class TestExtractFrontMatterField:
    """Tests for YAML front matter scalar-field extraction."""

    def _fn(self, text: str, field: str):
        from src.services.chores.service import _extract_front_matter_field

        return _extract_front_matter_field(text, field)

    def test_extracts_single_quoted_title(self):
        text = "---\nname: Bug Bash\ntitle: '[CHORE] Bug Bash'\nlabels: chore\n---\nBody"
        assert self._fn(text, "title") == "[CHORE] Bug Bash"

    def test_extracts_double_quoted_value(self):
        text = '---\ntitle: "[CHORE] My Chore"\n---\nBody'
        assert self._fn(text, "title") == "[CHORE] My Chore"

    def test_extracts_unquoted_value(self):
        text = "---\nlabels: chore\n---\nBody"
        assert self._fn(text, "labels") == "chore"

    def test_empty_value_returns_none(self):
        text = "---\nassignees: ''\n---\nBody"
        assert self._fn(text, "assignees") is None

    def test_missing_field_returns_none(self):
        text = "---\nname: Test\n---\nBody"
        assert self._fn(text, "title") is None

    def test_no_front_matter_returns_none(self):
        assert self._fn("Just a body", "title") is None

    def test_real_chore_template(self):
        template = (
            "---\n"
            "name: Bug Basher\n"
            "about: Recurring chore — Bug Basher\n"
            "title: '[CHORE] Bug Basher'\n"
            "labels: chore\n"
            "assignees: ''\n"
            "---\n\n"
            "## Bug Bash\nbody here\n"
        )
        assert self._fn(template, "title") == "[CHORE] Bug Basher"
        assert self._fn(template, "labels") == "chore"
        assert self._fn(template, "assignees") is None


# =============================================================================
# chat._is_template_ready defensive parsing
# =============================================================================


class TestIsTemplateReady:
    """Tests for template readiness detection in chat module."""

    def test_complete_template_detected(self):
        from src.services.chores.chat import _is_template_ready

        response = "Here is your template:\n```template\n---\nname: X\n---\nbody\n```\nDone!"
        ready, content = _is_template_ready(response)
        assert ready is True
        assert content is not None
        assert "name: X" in content

    def test_unterminated_fence_returns_false(self):
        from src.services.chores.chat import _is_template_ready

        response = "Here is your template:\n```template\n---\nname: X\n---\nbody"
        ready, content = _is_template_ready(response)
        assert ready is False
        assert content is None

    def test_no_template_marker(self):
        from src.services.chores.chat import _is_template_ready

        ready, content = _is_template_ready("Just a regular message")
        assert ready is False
        assert content is None


# =============================================================================
# chat._evict_stale_conversations
# =============================================================================


class TestConversationEviction:
    """Tests for TTL and size-bound eviction of in-memory conversations."""

    def test_evicts_expired_conversations(self):
        from datetime import timedelta

        from src.services.chores.chat import (
            _conversations,
            _evict_stale_conversations,
        )

        _conversations.clear()
        # Add a conversation that expired 2 hours ago
        _conversations["old"] = {
            "messages": [],
            "created_at": (datetime.now(UTC) - timedelta(hours=2)).isoformat(),
        }
        _conversations["recent"] = {
            "messages": [],
            "created_at": datetime.now(UTC).isoformat(),
        }
        _evict_stale_conversations()
        assert "old" not in _conversations
        assert "recent" in _conversations
        _conversations.clear()

    def test_evicts_when_over_capacity(self):
        from src.services.chores.chat import (
            _MAX_CONVERSATIONS,
            _conversations,
            _evict_stale_conversations,
        )

        _conversations.clear()
        for i in range(_MAX_CONVERSATIONS + 5):
            _conversations[f"c{i}"] = {
                "messages": [],
                "created_at": datetime.now(UTC).isoformat(),
            }
        _evict_stale_conversations()
        assert len(_conversations) <= _MAX_CONVERSATIONS
        _conversations.clear()


# =============================================================================
# ChoresService.create_chore duplicate rejection
# =============================================================================


class TestCreateChoreValidation:
    """Tests for chore creation validation."""

    @pytest.mark.anyio
    async def test_duplicate_name_rejected(self, mock_db):
        """Attempting to create a chore with a duplicate name raises ValueError."""
        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Weekly Review", template_content="Review content")

        await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-weekly-review.md"
        )

        with pytest.raises(ValueError, match="already exists"):
            await service.create_chore(
                "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-weekly-review-2.md"
            )

    @pytest.mark.anyio
    async def test_same_name_different_project_allowed(self, mock_db):
        """Same name in different projects should succeed."""
        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Shared Name", template_content="Content")

        c1 = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-shared-name.md"
        )
        c2 = await service.create_chore(
            "PVT_2", body, template_path=".github/ISSUE_TEMPLATE/chore-shared-name.md"
        )

        assert c1.project_id == "PVT_1"
        assert c2.project_id == "PVT_2"


# =============================================================================
# ChoresService.trigger_chore
# =============================================================================


class TestTriggerChore:
    """Tests for the trigger_chore() method."""

    @pytest.mark.anyio
    async def test_trigger_creates_issue_and_updates_record(self, mock_db):
        """trigger_chore creates a GitHub issue and updates the chore record."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Trigger Test", template_content="Content body")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-trigger-test.md"
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 1,
            "node_id": "I_1",
            "number": 42,
            "html_url": "https://github.com/test/repo/issues/42",
        }
        mock_github.add_issue_to_project.return_value = "item-1"

        result = await service.trigger_chore(
            chore,
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is True
        assert result.issue_number == 42
        mock_github.create_issue.assert_awaited_once()
        mock_github.add_issue_to_project.assert_awaited_once()

        # Verify chore record updated
        updated = await service.get_chore(chore.id)
        assert updated.current_issue_number == 42
        assert updated.current_issue_node_id == "I_1"
        assert updated.last_triggered_at is not None

    @pytest.mark.anyio
    async def test_trigger_runs_full_agent_pipeline(self, mock_db, monkeypatch):
        """trigger_chore sets Backlog status, creates sub-issues, assigns agent, and starts polling."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Pipeline Test", template_content="---\nname: Test\n---\nContent")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-pipeline-test.md"
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 10,
            "node_id": "I_10",
            "number": 100,
            "html_url": "https://github.com/test/repo/issues/100",
        }
        mock_github.add_issue_to_project.return_value = "item-10"

        # Mock workflow config
        mock_config = MagicMock()
        mock_config.status_backlog = "Backlog"
        mock_config.copilot_assignee = "copilot-bot"
        mock_config.agent_mappings = {
            "Backlog": [MagicMock(slug="speckit.specify")],
            "Ready": [MagicMock(slug="speckit.plan")],
        }

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {
            "speckit.specify": {"number": 101, "node_id": "I_101", "url": ""},
            "speckit.plan": {"number": 102, "node_id": "I_102", "url": ""},
        }
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_ensure_polling = AsyncMock()
        mock_set_state = MagicMock()

        # Mock settings for copilot_assignee
        mock_settings = MagicMock()
        mock_settings.default_assignee = "copilot-bot"

        # Patch the re-exported names that the lazy import in trigger_chore resolves
        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=mock_config))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", AsyncMock())
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", mock_set_state)
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch(
            "src.services.copilot_polling.ensure_polling_started",
            mock_ensure_polling,
        ):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert result.triggered is True
        assert result.issue_number == 100

        # Issue body should include the tracking table
        create_call = mock_github.create_issue.call_args
        issue_body = create_call.kwargs.get("body") or create_call[0][3]
        assert "🤖 Agent Pipeline" in issue_body
        assert "speckit.specify" in issue_body

        # Issue body should include the agent metadata summary
        assert "Assigned Agents" in issue_body

        # Should have set status to Backlog
        mock_github.update_item_status_by_name.assert_awaited_once_with(
            access_token="token",
            project_id="PVT_1",
            item_id="item-10",
            status_name="Backlog",
        )

        # Should have created sub-issues
        mock_orchestrator.create_all_sub_issues.assert_awaited_once()

        # Should have stored pipeline state
        mock_set_state.assert_called_once()
        ps = mock_set_state.call_args[0]
        assert ps[0] == 100  # issue_number

        # Should have assigned the first agent
        mock_orchestrator.assign_agent_for_status.assert_awaited_once_with(
            mock_orchestrator.assign_agent_for_status.call_args[0][0],  # ctx
            "Backlog",
            agent_index=0,
        )

        # Should have started polling
        mock_ensure_polling.assert_awaited_once_with(
            access_token="token",
            project_id="PVT_1",
            owner="test",
            repo="repo",
            caller="chore_trigger",
        )

    @pytest.mark.anyio
    async def test_trigger_bootstraps_config_when_none(self, mock_db, monkeypatch):
        """When get_workflow_config returns None, trigger_chore bootstraps a default config."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Bootstrap Test", template_content="Template body here")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-bootstrap.md"
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 20,
            "node_id": "I_20",
            "number": 200,
            "html_url": "https://github.com/test/repo/issues/200",
        }
        mock_github.add_issue_to_project.return_value = "item-20"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {
            "speckit.specify": {"number": 201, "node_id": "I_201", "url": ""},
        }
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "test-copilot-user"

        mock_set_config = AsyncMock()

        import src.services.workflow_orchestrator as wo_pkg

        # Return None → trigger should bootstrap
        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=None))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", mock_set_config)
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch(
            "src.services.copilot_polling.ensure_polling_started",
            AsyncMock(),
        ):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert result.triggered is True

        # set_workflow_config should have been called to persist the bootstrapped config
        mock_set_config.assert_awaited()
        saved_config = mock_set_config.call_args[0][1]
        assert saved_config.project_id == "PVT_1"
        assert saved_config.repository_owner == "test"
        assert saved_config.repository_name == "repo"
        assert saved_config.copilot_assignee == "test-copilot-user"

        # Issue body should still have the tracking table from default agent_mappings
        create_call = mock_github.create_issue.call_args
        issue_body = create_call.kwargs.get("body") or create_call[0][3]
        assert "Agent Pipeline" in issue_body or "Assigned Agents" in issue_body

    @pytest.mark.anyio
    async def test_trigger_sets_copilot_assignee_when_missing(self, mock_db, monkeypatch):
        """When config exists but copilot_assignee is empty, it's set from settings."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.models.workflow import WorkflowConfiguration
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Assignee Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-assignee.md"
        )

        # Config with empty copilot_assignee
        config = WorkflowConfiguration(
            project_id="PVT_1",
            repository_owner="old-owner",
            repository_name="old-repo",
            copilot_assignee="",
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 30,
            "node_id": "I_30",
            "number": 300,
            "html_url": "https://github.com/test/repo/issues/300",
        }
        mock_github.add_issue_to_project.return_value = "item-30"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "my-copilot-bot"

        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=config))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", AsyncMock())
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch(
            "src.services.copilot_polling.ensure_polling_started",
            AsyncMock(),
        ):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert result.triggered is True
        # copilot_assignee should now be set from settings
        assert config.copilot_assignee == "my-copilot-bot"
        # repository_owner/name should be updated
        assert config.repository_owner == "test"
        assert config.repository_name == "repo"

    @pytest.mark.anyio
    async def test_trigger_loads_user_agent_mappings(self, mock_db, monkeypatch):
        """User-specific agent mappings are loaded and applied when github_user_id is provided."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.models.workflow import WorkflowConfiguration
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="UserMap Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-usermap.md"
        )

        config = WorkflowConfiguration(
            project_id="PVT_1",
            repository_owner="test",
            repository_name="repo",
            copilot_assignee="bot",
        )

        # Custom user mappings
        custom_mappings = {
            "Backlog": [MagicMock(slug="custom.agent")],
        }

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 40,
            "node_id": "I_40",
            "number": 400,
            "html_url": "https://github.com/test/repo/issues/400",
        }
        mock_github.add_issue_to_project.return_value = "item-40"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "bot"

        mock_set_config = AsyncMock()

        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=config))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", mock_set_config)
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=custom_mappings),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch(
            "src.services.copilot_polling.ensure_polling_started",
            AsyncMock(),
        ):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
                github_user_id="user-123",
            )

        assert result.triggered is True
        # Config should have the custom mappings applied
        assert config.agent_mappings == custom_mappings
        # set_workflow_config should have been called to persist the updated mappings
        mock_set_config.assert_awaited()

    @pytest.mark.anyio
    async def test_issue_body_contains_agent_metadata(self, mock_db, monkeypatch):
        """The created issue body includes agent assignment summary with copilot assignee."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.models.workflow import WorkflowConfiguration
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Metadata Test", template_content="## My template\nDo stuff")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-meta.md"
        )

        config = WorkflowConfiguration(
            project_id="PVT_1",
            repository_owner="test",
            repository_name="repo",
            copilot_assignee="copilot-bot",
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 50,
            "node_id": "I_50",
            "number": 500,
            "html_url": "https://github.com/test/repo/issues/500",
        }
        mock_github.add_issue_to_project.return_value = "item-50"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "copilot-bot"

        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=config))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", AsyncMock())
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch(
            "src.services.copilot_polling.ensure_polling_started",
            AsyncMock(),
        ):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert result.triggered is True

        create_call = mock_github.create_issue.call_args
        issue_body = create_call.kwargs.get("body") or create_call[0][3]

        # Template content should be present (front matter stripped)
        assert "## My template" in issue_body
        assert "Do stuff" in issue_body

        # Tracking table should be present
        assert "Agent Pipeline" in issue_body

        # Agent metadata summary section
        assert "Assigned Agents" in issue_body
        assert "speckit.specify" in issue_body
        assert "Copilot Assignee" in issue_body
        assert "copilot-bot" in issue_body

    @pytest.mark.anyio
    async def test_open_instance_skips_trigger(self, mock_db):
        """trigger_chore skips when an open instance exists."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Skip Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-skip-test.md"
        )

        # Simulate an open issue
        await service.update_chore_fields(
            chore.id, current_issue_number=10, current_issue_node_id="I_10"
        )
        chore = await service.get_chore(chore.id)

        mock_github = AsyncMock()
        mock_github.check_issue_closed.return_value = False

        result = await service.trigger_chore(
            chore,
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is False
        assert "Open instance" in result.skip_reason
        mock_github.create_issue.assert_not_awaited()

    @pytest.mark.anyio
    async def test_closed_issue_allows_retrigger(self, mock_db):
        """trigger_chore proceeds when the open instance was closed externally."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Closed Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-closed-test.md"
        )

        await service.update_chore_fields(
            chore.id, current_issue_number=10, current_issue_node_id="I_10"
        )
        chore = await service.get_chore(chore.id)

        mock_github = AsyncMock()
        mock_github.check_issue_closed.return_value = True
        mock_github.create_issue.return_value = {
            "id": 2,
            "node_id": "I_2",
            "number": 43,
            "html_url": "https://github.com/test/repo/issues/43",
        }
        mock_github.add_issue_to_project.return_value = "item-2"

        result = await service.trigger_chore(
            chore,
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is True
        assert result.issue_number == 43

    @pytest.mark.anyio
    async def test_cas_prevents_double_fire(self, mock_db):
        """CAS update prevents double-fire when last_triggered_at has changed."""
        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="CAS Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-cas-test.md"
        )

        # Simulate a concurrent trigger by modifying last_triggered_at
        await service.update_chore_fields(chore.id, last_triggered_at="2024-01-01T00:00:00Z")

        # Try CAS with the old (None) value — should fail
        result = await service.update_chore_after_trigger(
            chore.id,
            current_issue_number=99,
            current_issue_node_id="I_99",
            last_triggered_at="2024-06-01T00:00:00Z",
            last_triggered_count=0,
            old_last_triggered_at=None,  # stale value
        )
        assert result is False

    @pytest.mark.anyio
    async def test_cas_failure_closes_duplicate_issue(self, mock_db):
        """When CAS fails, trigger_chore closes the duplicate issue and returns not-triggered."""
        from unittest.mock import AsyncMock

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="CAS Close Test", template_content="Content")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-cas-close.md"
        )

        # Simulate a concurrent trigger by modifying last_triggered_at
        await service.update_chore_fields(chore.id, last_triggered_at="2024-01-01T00:00:00Z")
        # But pass the stale chore (old last_triggered_at=None) to trigger_chore
        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 3,
            "node_id": "I_3",
            "number": 50,
            "html_url": "https://github.com/test/repo/issues/50",
        }
        mock_github.add_issue_to_project.return_value = "item-3"

        result = await service.trigger_chore(
            chore,  # stale: last_triggered_at is None
            github_service=mock_github,
            access_token="token",
            owner="test",
            repo="repo",
            project_id="PVT_1",
        )

        assert result.triggered is False
        assert "CAS conflict" in result.skip_reason
        # Duplicate issue should have been closed
        mock_github.update_issue_state.assert_awaited_once_with(
            "token", "test", "repo", 50, state="closed", state_reason="not_planned"
        )

    @pytest.mark.anyio
    async def test_trigger_uses_template_title_from_front_matter(self, mock_db, monkeypatch):
        """trigger_chore uses the `title:` value from YAML front matter, not bare chore.name."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        template_with_title = (
            "---\n"
            "name: Bug Basher\n"
            "title: '[CHORE] Bug Basher'\n"
            "labels: chore\n"
            "assignees: ''\n"
            "---\n\n"
            "## Bug Bash body here\n"
        )

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Bug Basher", template_content=template_with_title)
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-bug-basher.md"
        )

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 99,
            "node_id": "I_99",
            "number": 999,
            "html_url": "https://github.com/test/repo/issues/999",
        }
        mock_github.add_issue_to_project.return_value = "item-99"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "Copilot"

        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=None))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", AsyncMock())
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch("src.services.copilot_polling.ensure_polling_started", AsyncMock()):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert result.triggered is True

        create_call = mock_github.create_issue.call_args
        # Title should use template front-matter value, not bare chore.name
        assert create_call.kwargs["title"] == "[CHORE] Bug Basher"

    @pytest.mark.anyio
    async def test_trigger_sets_copilot_assignee_at_issue_creation(self, mock_db, monkeypatch):
        """trigger_chore passes copilot_assignee in assignees at issue creation time."""
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.models.workflow import WorkflowConfiguration
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Assignee Chore", template_content="## Body here")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-assignee.md"
        )

        mock_config = MagicMock(spec=WorkflowConfiguration)
        mock_config.status_backlog = "Backlog"
        mock_config.copilot_assignee = "my-copilot"
        mock_config.repository_owner = "test"
        mock_config.repository_name = "repo"
        mock_config.agent_mappings = {}

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 88,
            "node_id": "I_88",
            "number": 888,
            "html_url": "https://github.com/test/repo/issues/888",
        }
        mock_github.add_issue_to_project.return_value = "item-88"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "my-copilot"

        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=mock_config))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", AsyncMock())
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch("src.services.copilot_polling.ensure_polling_started", AsyncMock()):
            result = await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        assert result.triggered is True

        create_call = mock_github.create_issue.call_args
        # Copilot assignee must be passed at creation time, not relying on pipeline step
        assigned = create_call.kwargs.get("assignees") or []
        assert "my-copilot" in assigned

    @pytest.mark.anyio
    async def test_trigger_assigned_agents_section_before_tracking_table(
        self, mock_db, monkeypatch
    ):
        """The 'Assigned Agents' summary appears BEFORE the tracking table in the issue body.

        This is critical: the tracking-update helpers strip everything from
        '---\\n## 🤖 Agent Pipeline' to end-of-string on every state update.
        If the summary comes AFTER the table it would be erased on the first update.
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        from src.models.chores import ChoreCreate
        from src.services.chores.service import ChoresService

        service = ChoresService(mock_db)
        body = ChoreCreate(name="Order Test", template_content="## Body")
        chore = await service.create_chore(
            "PVT_1", body, template_path=".github/ISSUE_TEMPLATE/chore-order.md"
        )

        mock_config = MagicMock()
        mock_config.status_backlog = "Backlog"
        mock_config.copilot_assignee = "bot"
        mock_config.repository_owner = "test"
        mock_config.repository_name = "repo"
        mock_config.agent_mappings = {
            "Backlog": [MagicMock(slug="speckit.specify")],
        }

        mock_github = AsyncMock()
        mock_github.create_issue.return_value = {
            "id": 77,
            "node_id": "I_77",
            "number": 777,
            "html_url": "https://github.com/test/repo/issues/777",
        }
        mock_github.add_issue_to_project.return_value = "item-77"

        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.default_assignee = "bot"

        import src.services.workflow_orchestrator as wo_pkg

        monkeypatch.setattr(wo_pkg, "get_workflow_config", AsyncMock(return_value=mock_config))
        monkeypatch.setattr(wo_pkg, "set_workflow_config", AsyncMock())
        monkeypatch.setattr(wo_pkg, "get_workflow_orchestrator", lambda: mock_orchestrator)
        monkeypatch.setattr(wo_pkg, "set_pipeline_state", MagicMock())
        monkeypatch.setattr(
            "src.services.workflow_orchestrator.config.load_user_agent_mappings",
            AsyncMock(return_value=None),
        )
        monkeypatch.setattr("src.config.get_settings", lambda: mock_settings)

        with patch("src.services.copilot_polling.ensure_polling_started", AsyncMock()):
            await service.trigger_chore(
                chore,
                github_service=mock_github,
                access_token="token",
                owner="test",
                repo="repo",
                project_id="PVT_1",
            )

        create_call = mock_github.create_issue.call_args
        issue_body: str = create_call.kwargs.get("body") or create_call[0][3]

        assigned_pos = issue_body.find("Assigned Agents")
        pipeline_pos = issue_body.find("🤖 Agent Pipeline")

        assert assigned_pos != -1, "'Assigned Agents' section not found in issue body"
        assert pipeline_pos != -1, "'🤖 Agent Pipeline' table not found in issue body"
        assert assigned_pos < pipeline_pos, (
            "'Assigned Agents' must come BEFORE '🤖 Agent Pipeline' in the body "
            "so tracking-table updates don't erase it"
        )


# =============================================================================
# commit_template_to_repo — existing branch handling
# =============================================================================


class TestCommitTemplateExistingBranch:
    """Tests for commit_template_to_repo when the branch already exists."""

    @pytest.mark.anyio
    async def test_uses_branch_head_when_branch_exists(self):
        """When create_branch returns 'existing', commit should use the branch HEAD OID."""
        from unittest.mock import AsyncMock

        from src.services.chores.template_builder import commit_template_to_repo

        mock_github = AsyncMock()
        mock_github.get_repository_info.return_value = {
            "repository_id": "R_1",
            "default_branch": "main",
            "head_oid": "default-oid",
        }
        mock_github.create_branch.return_value = "existing"
        mock_github.get_branch_head_oid.return_value = "branch-head-oid"
        mock_github.commit_files.return_value = "commit-oid"
        mock_github.create_pull_request.return_value = {
            "id": "PR_1",
            "number": 10,
            "url": "https://github.com/o/r/pull/10",
        }
        mock_github.create_issue.return_value = {
            "id": 1,
            "node_id": "I_1",
            "number": 20,
            "html_url": "https://github.com/o/r/issues/20",
        }
        mock_github.add_issue_to_project.return_value = "item-1"

        await commit_template_to_repo(
            github_service=mock_github,
            access_token="tok",
            owner="o",
            repo="r",
            project_id="PVT_1",
            name="Bug Bash",
            template_content="---\nname: Bug Bash\n---\ncontent",
        )

        # Should have fetched the branch-specific HEAD
        mock_github.get_branch_head_oid.assert_awaited_once_with(
            "tok", "o", "r", "chore/add-template-bug-bash"
        )
        # commit_files should be called with the branch HEAD, not the default branch HEAD
        commit_call = mock_github.commit_files.call_args
        assert commit_call[0][4] == "branch-head-oid"

    @pytest.mark.anyio
    async def test_uses_default_oid_for_new_branch(self):
        """When create_branch returns a new ref ID, commit uses the default branch HEAD."""
        from unittest.mock import AsyncMock

        from src.services.chores.template_builder import commit_template_to_repo

        mock_github = AsyncMock()
        mock_github.get_repository_info.return_value = {
            "repository_id": "R_1",
            "default_branch": "main",
            "head_oid": "default-oid",
        }
        mock_github.create_branch.return_value = "ref-id-new"
        mock_github.commit_files.return_value = "commit-oid"
        mock_github.create_pull_request.return_value = {
            "id": "PR_1",
            "number": 10,
            "url": "https://github.com/o/r/pull/10",
        }
        mock_github.create_issue.return_value = {
            "id": 1,
            "node_id": "I_1",
            "number": 20,
            "html_url": "https://github.com/o/r/issues/20",
        }
        mock_github.add_issue_to_project.return_value = "item-1"

        await commit_template_to_repo(
            github_service=mock_github,
            access_token="tok",
            owner="o",
            repo="r",
            project_id="PVT_1",
            name="Bug Bash",
            template_content="---\nname: Bug Bash\n---\ncontent",
        )

        # Should NOT have fetched branch HEAD
        mock_github.get_branch_head_oid.assert_not_awaited()
        # commit_files should be called with the default branch HEAD
        commit_call = mock_github.commit_files.call_args
        assert commit_call[0][4] == "default-oid"
