"""Unit tests for Workflow Orchestrator - Custom agent assignment on Ready status."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.chat import WorkflowConfiguration
from src.services.workflow_orchestrator import (
    WorkflowContext,
    WorkflowOrchestrator,
    WorkflowState,
)


class TestHandleReadyStatusWithCustomAgent:
    """Tests for handle_ready_status with custom agent assignment."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service."""
        return Mock()

    @pytest.fixture
    def mock_github_service(self):
        """Create mock GitHub service."""
        service = Mock()
        service.get_issue_with_comments = AsyncMock()
        service.format_issue_context_as_prompt = Mock()
        service.assign_copilot_to_issue = AsyncMock()
        service.update_item_status_by_name = AsyncMock()
        service.validate_assignee = AsyncMock()
        service.assign_issue = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_ai_service, mock_github_service):
        """Create WorkflowOrchestrator with mocked services."""
        return WorkflowOrchestrator(mock_ai_service, mock_github_service)

    @pytest.fixture
    def workflow_context(self):
        """Create a workflow context for testing."""
        return WorkflowContext(
            session_id="test-session",
            project_id="PROJECT_123",
            access_token="test-token",
            repository_owner="test-owner",
            repository_name="test-repo",
            issue_id="I_123",
            issue_number=42,
            project_item_id="ITEM_456",
            current_state=WorkflowState.READY,
        )

    @pytest.fixture
    def workflow_config_with_custom_agent(self):
        """Create a workflow config with custom agent."""
        return WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="test-owner",
            repository_name="test-repo",
            custom_agent="speckit.specify",
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
        )

    @pytest.fixture
    def workflow_config_no_custom_agent(self):
        """Create a workflow config without custom agent."""
        return WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="test-owner",
            repository_name="test-repo",
            custom_agent="",
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
        )

    @pytest.mark.asyncio
    async def test_handle_ready_fetches_issue_details_for_custom_agent(
        self, orchestrator, workflow_context, workflow_config_with_custom_agent, mock_github_service
    ):
        """Should fetch issue details when custom agent is configured."""
        workflow_context.config = workflow_config_with_custom_agent

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test Issue",
            "body": "Issue body",
            "comments": [{"author": "user", "body": "Comment", "created_at": "2026-01-01"}],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Formatted prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        result = await orchestrator.handle_ready_status(workflow_context)

        assert result is True
        mock_github_service.get_issue_with_comments.assert_called_once_with(
            access_token="test-token",
            owner="test-owner",
            repo="test-repo",
            issue_number=42,
        )
        mock_github_service.format_issue_context_as_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ready_passes_custom_agent_to_assignment(
        self, orchestrator, workflow_context, workflow_config_with_custom_agent, mock_github_service
    ):
        """Should pass custom agent name and instructions to assign_copilot_to_issue."""
        workflow_context.config = workflow_config_with_custom_agent

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Feature Request",
            "body": "Add new feature",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = (
            "## Issue Title\nFeature Request"
        )
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        await orchestrator.handle_ready_status(workflow_context)

        mock_github_service.assign_copilot_to_issue.assert_called_once_with(
            access_token="test-token",
            owner="test-owner",
            repo="test-repo",
            issue_node_id="I_123",
            issue_number=42,
            custom_agent="speckit.specify",
            custom_instructions="## Issue Title\nFeature Request",
        )

    @pytest.mark.asyncio
    async def test_handle_ready_no_custom_agent_skips_issue_fetch(
        self, orchestrator, workflow_context, workflow_config_no_custom_agent, mock_github_service
    ):
        """Should not fetch issue details when no custom agent is configured."""
        workflow_context.config = workflow_config_no_custom_agent

        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        await orchestrator.handle_ready_status(workflow_context)

        mock_github_service.get_issue_with_comments.assert_not_called()
        mock_github_service.assign_copilot_to_issue.assert_called_once_with(
            access_token="test-token",
            owner="test-owner",
            repo="test-repo",
            issue_node_id="I_123",
            issue_number=42,
            custom_agent="",
            custom_instructions="",
        )

    @pytest.mark.asyncio
    async def test_handle_ready_transitions_to_in_progress(
        self, orchestrator, workflow_context, workflow_config_with_custom_agent, mock_github_service
    ):
        """Should transition issue to In Progress status."""
        workflow_context.config = workflow_config_with_custom_agent

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        result = await orchestrator.handle_ready_status(workflow_context)

        assert result is True
        assert workflow_context.current_state == WorkflowState.IN_PROGRESS
        mock_github_service.update_item_status_by_name.assert_called_once_with(
            access_token="test-token",
            project_id="PROJECT_123",
            item_id="ITEM_456",
            status_name="In Progress",
        )

    @pytest.mark.asyncio
    async def test_handle_ready_assignment_failure_still_transitions(
        self, orchestrator, workflow_context, workflow_config_with_custom_agent, mock_github_service
    ):
        """Should still transition status even if Copilot assignment fails."""
        workflow_context.config = workflow_config_with_custom_agent

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = False  # Assignment fails
        mock_github_service.update_item_status_by_name.return_value = True
        mock_github_service.validate_assignee.return_value = False

        result = await orchestrator.handle_ready_status(workflow_context)

        # Should still succeed (assignment failure doesn't block transition)
        assert result is True
        mock_github_service.update_item_status_by_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ready_status_update_failure_returns_false(
        self, orchestrator, workflow_context, workflow_config_with_custom_agent, mock_github_service
    ):
        """Should return False when status update fails."""
        workflow_context.config = workflow_config_with_custom_agent

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.update_item_status_by_name.return_value = False  # Status update fails

        result = await orchestrator.handle_ready_status(workflow_context)

        assert result is False

    @pytest.mark.asyncio
    async def test_handle_ready_no_config_returns_false(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should return False when no workflow config exists."""
        workflow_context.config = None

        # Clear any global config
        with patch("src.services.workflow_orchestrator.get_workflow_config", return_value=None):
            result = await orchestrator.handle_ready_status(workflow_context)

        assert result is False


class TestHandleInProgressStatus:
    """Tests for handle_in_progress_status - PR completion detection."""

    @pytest.fixture
    def mock_ai_service(self):
        """Create mock AI service."""
        return Mock()

    @pytest.fixture
    def mock_github_service(self):
        """Create mock GitHub service."""
        service = Mock()
        service.check_copilot_pr_completion = AsyncMock()
        service.mark_pr_ready_for_review = AsyncMock()
        service.update_item_status_by_name = AsyncMock()
        service.get_repository_owner = AsyncMock(return_value="repo-owner")
        service.assign_issue = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_ai_service, mock_github_service):
        """Create WorkflowOrchestrator with mocked services."""
        return WorkflowOrchestrator(mock_ai_service, mock_github_service)

    @pytest.fixture
    def workflow_context(self):
        """Create a workflow context for testing."""
        return WorkflowContext(
            session_id="test-session",
            project_id="PROJECT_123",
            access_token="test-token",
            repository_owner="test-owner",
            repository_name="test-repo",
            issue_id="I_123",
            issue_number=42,
            project_item_id="ITEM_456",
            current_state=WorkflowState.IN_PROGRESS,
        )

    @pytest.fixture
    def workflow_config(self):
        """Create a workflow config."""
        return WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="test-owner",
            repository_name="test-repo",
            status_in_progress="In Progress",
            status_in_review="In Review",
        )

    @pytest.mark.asyncio
    async def test_handle_in_progress_pr_completed(
        self, orchestrator, workflow_context, workflow_config, mock_github_service
    ):
        """Should transition to In Review when Copilot has finished (draft + has commits)."""
        workflow_context.config = workflow_config

        mock_github_service.check_copilot_pr_completion.return_value = {
            "id": "PR_123",
            "number": 99,
            "is_draft": True,  # Copilot leaves in draft when done
            "state": "OPEN",
            "author": "copilot-swe-agent[bot]",
            "last_commit": {"sha": "abc123"},  # Has commits = finished
        }
        mock_github_service.mark_pr_ready_for_review.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        result = await orchestrator.handle_in_progress_status(workflow_context)

        assert result is True
        assert workflow_context.current_state == WorkflowState.IN_REVIEW
        mock_github_service.mark_pr_ready_for_review.assert_called_once()
        mock_github_service.update_item_status_by_name.assert_called_once_with(
            access_token="test-token",
            project_id="PROJECT_123",
            item_id="ITEM_456",
            status_name="In Review",
        )

    @pytest.mark.asyncio
    async def test_handle_in_progress_pr_still_draft(
        self, orchestrator, workflow_context, workflow_config, mock_github_service
    ):
        """Should not transition when Copilot PR has no commits yet."""
        workflow_context.config = workflow_config

        mock_github_service.check_copilot_pr_completion.return_value = None

        result = await orchestrator.handle_in_progress_status(workflow_context)

        assert result is False
        assert workflow_context.current_state == WorkflowState.IN_PROGRESS
        mock_github_service.update_item_status_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_in_progress_marks_draft_pr_ready(
        self, orchestrator, workflow_context, workflow_config, mock_github_service
    ):
        """Should mark draft PR ready when Copilot has finished work."""
        workflow_context.config = workflow_config

        mock_github_service.check_copilot_pr_completion.return_value = {
            "id": "PR_123",
            "number": 99,
            "is_draft": True,  # Copilot leaves in draft when done
            "state": "OPEN",
            "author": "copilot-swe-agent[bot]",
            "last_commit": {"sha": "abc123"},  # Has commits = work is done
        }
        mock_github_service.mark_pr_ready_for_review.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        await orchestrator.handle_in_progress_status(workflow_context)

        mock_github_service.mark_pr_ready_for_review.assert_called_once_with(
            access_token="test-token",
            pr_node_id="PR_123",
        )

    @pytest.mark.asyncio
    async def test_handle_in_progress_no_config_returns_false(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should return False when no workflow config exists."""
        workflow_context.config = None

        with patch("src.services.workflow_orchestrator.get_workflow_config", return_value=None):
            result = await orchestrator.handle_in_progress_status(workflow_context)

        assert result is False
        mock_github_service.check_copilot_pr_completion.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_in_progress_no_linked_prs(
        self, orchestrator, workflow_context, workflow_config, mock_github_service
    ):
        """Should return False when no linked PRs found."""
        workflow_context.config = workflow_config

        mock_github_service.check_copilot_pr_completion.return_value = None

        result = await orchestrator.handle_in_progress_status(workflow_context)

        assert result is False
        mock_github_service.update_item_status_by_name.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_in_progress_status_update_failure(
        self, orchestrator, workflow_context, workflow_config, mock_github_service
    ):
        """Should return False when status update fails."""
        workflow_context.config = workflow_config

        mock_github_service.check_copilot_pr_completion.return_value = {
            "id": "PR_123",
            "number": 99,
            "is_draft": True,  # Copilot leaves in draft
            "state": "OPEN",
            "last_commit": {"sha": "abc123"},  # Has commits
        }
        mock_github_service.mark_pr_ready_for_review.return_value = True
        mock_github_service.update_item_status_by_name.return_value = False

        result = await orchestrator.handle_in_progress_status(workflow_context)

        assert result is False


class TestWorkflowConfigurationCustomAgent:
    """Tests for WorkflowConfiguration with custom_agent field."""

    def test_config_with_custom_agent(self):
        """Should support custom_agent field."""
        config = WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="owner",
            repository_name="repo",
            custom_agent="speckit.specify",
        )

        assert config.custom_agent == "speckit.specify"

    def test_config_default_empty_custom_agent(self):
        """Should default to empty string for custom_agent."""
        config = WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="owner",
            repository_name="repo",
        )

        assert config.custom_agent == ""

    def test_config_all_fields(self):
        """Should support all configuration fields."""
        config = WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="owner",
            repository_name="repo",
            copilot_assignee="fallback-user",
            review_assignee="reviewer",
            custom_agent="speckit.specify",
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
            enabled=True,
        )

        assert config.project_id == "PROJECT_123"
        assert config.custom_agent == "speckit.specify"
        assert config.copilot_assignee == "fallback-user"
        assert config.enabled is True
