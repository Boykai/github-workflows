"""Unit tests for Workflow Orchestrator - Agent mapping assignment."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.chat import DEFAULT_AGENT_MAPPINGS, WorkflowConfiguration
from src.services.workflow_orchestrator import (
    PipelineState,
    WorkflowContext,
    WorkflowOrchestrator,
    WorkflowState,
)


class TestHandleReadyStatusWithAgentMappings:
    """Tests for handle_ready_status with agent_mappings configuration."""

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
        service.find_existing_pr_for_issue = AsyncMock(return_value=None)
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
    def workflow_config_with_agents(self):
        """Create a workflow config with agent mappings."""
        return WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="test-owner",
            repository_name="test-repo",
            agent_mappings={
                "Backlog": ["speckit.specify"],
                "Ready": ["speckit.plan", "speckit.tasks"],
                "In Progress": ["speckit.implement"],
            },
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
        )

    @pytest.fixture
    def workflow_config_no_agents(self):
        """Create a workflow config without agent mappings."""
        return WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="test-owner",
            repository_name="test-repo",
            agent_mappings={},
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
        )

    @pytest.mark.asyncio
    async def test_handle_ready_fetches_issue_details_for_agent(
        self,
        orchestrator,
        workflow_context,
        workflow_config_with_agents,
        mock_github_service,
    ):
        """Should fetch issue details when agent_mappings has In Progress agents."""
        workflow_context.config = workflow_config_with_agents

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
    async def test_handle_ready_passes_agent_from_mappings(
        self,
        orchestrator,
        workflow_context,
        workflow_config_with_agents,
        mock_github_service,
    ):
        """Should pass agent name from agent_mappings to assign_copilot_to_issue."""
        workflow_context.config = workflow_config_with_agents

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

        # handle_ready_status now delegates to assign_agent_for_status
        mock_github_service.assign_copilot_to_issue.assert_called_once()
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args.kwargs["custom_agent"] == "speckit.implement"
        assert call_args.kwargs["issue_node_id"] == "I_123"
        assert call_args.kwargs["issue_number"] == 42

    @pytest.mark.asyncio
    async def test_handle_ready_no_agents_skips_issue_fetch(
        self,
        orchestrator,
        workflow_context,
        workflow_config_no_agents,
        mock_github_service,
    ):
        """Should not fetch issue details when no agents configured for In Progress."""
        workflow_context.config = workflow_config_no_agents

        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.update_item_status_by_name.return_value = True

        await orchestrator.handle_ready_status(workflow_context)

        # No agents for In Progress → assign_agent_for_status returns True without calling Copilot
        mock_github_service.get_issue_with_comments.assert_not_called()
        mock_github_service.assign_copilot_to_issue.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_ready_transitions_to_in_progress(
        self,
        orchestrator,
        workflow_context,
        workflow_config_with_agents,
        mock_github_service,
    ):
        """Should transition issue to In Progress status."""
        workflow_context.config = workflow_config_with_agents

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
        self,
        orchestrator,
        workflow_context,
        workflow_config_with_agents,
        mock_github_service,
    ):
        """Should still transition status even if Copilot assignment fails."""
        workflow_context.config = workflow_config_with_agents

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
        self,
        orchestrator,
        workflow_context,
        workflow_config_with_agents,
        mock_github_service,
    ):
        """Should return False when status update fails."""
        workflow_context.config = workflow_config_with_agents

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


class TestAssignAgentForStatus:
    """Tests for assign_agent_for_status helper."""

    @pytest.fixture
    def mock_ai_service(self):
        return Mock()

    @pytest.fixture
    def mock_github_service(self):
        service = Mock()
        service.get_issue_with_comments = AsyncMock()
        service.format_issue_context_as_prompt = Mock()
        service.assign_copilot_to_issue = AsyncMock()
        service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def orchestrator(self, mock_ai_service, mock_github_service):
        return WorkflowOrchestrator(mock_ai_service, mock_github_service)

    @pytest.fixture
    def workflow_context(self):
        ctx = WorkflowContext(
            session_id="test-session",
            project_id="PROJECT_123",
            access_token="test-token",
            repository_owner="test-owner",
            repository_name="test-repo",
            issue_id="I_123",
            issue_number=42,
            project_item_id="ITEM_456",
        )
        ctx.config = WorkflowConfiguration(
            project_id="PROJECT_123",
            repository_owner="test-owner",
            repository_name="test-repo",
            agent_mappings={
                "Backlog": ["speckit.specify"],
                "Ready": ["speckit.plan", "speckit.tasks"],
                "In Progress": ["speckit.implement"],
            },
        )
        return ctx

    @pytest.mark.asyncio
    async def test_assign_first_backlog_agent(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should assign speckit.specify for Backlog status."""
        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True

        result = await orchestrator.assign_agent_for_status(workflow_context, "Backlog", 0)

        assert result is True
        mock_github_service.assign_copilot_to_issue.assert_called_once()
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args.kwargs["custom_agent"] == "speckit.specify"

    @pytest.mark.asyncio
    async def test_assign_second_ready_agent(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should assign speckit.tasks for Ready status at index 1."""
        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True

        result = await orchestrator.assign_agent_for_status(workflow_context, "Ready", 1)

        assert result is True
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args.kwargs["custom_agent"] == "speckit.tasks"

    @pytest.mark.asyncio
    async def test_assign_no_agents_configured(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should return True when no agents configured for status."""
        result = await orchestrator.assign_agent_for_status(workflow_context, "In Review", 0)

        assert result is True
        mock_github_service.assign_copilot_to_issue.assert_not_called()

    @pytest.mark.asyncio
    async def test_assign_out_of_range_index(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should return True when agent index is beyond the list."""
        result = await orchestrator.assign_agent_for_status(workflow_context, "Backlog", 5)

        assert result is True
        mock_github_service.assign_copilot_to_issue.assert_not_called()


class TestPipelineState:
    """Tests for PipelineState dataclass."""

    def test_current_agent(self):
        """Should return current agent by index."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
        )
        assert state.current_agent == "speckit.plan"

    def test_current_agent_second(self):
        """Should return second agent when index is 1."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=1,
        )
        assert state.current_agent == "speckit.tasks"

    def test_current_agent_complete(self):
        """Should return None when pipeline is complete."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=2,
        )
        assert state.current_agent is None

    def test_is_complete(self):
        """Should be True when index >= len(agents)."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=2,
        )
        assert state.is_complete is True

    def test_is_not_complete(self):
        """Should be False when agents remain."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=1,
        )
        assert state.is_complete is False

    def test_next_agent(self):
        """Should return next agent."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=0,
        )
        assert state.next_agent == "speckit.tasks"

    def test_next_agent_last(self):
        """Should return None when current is last agent."""
        state = PipelineState(
            issue_number=42,
            project_id="P1",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            current_agent_index=1,
        )
        assert state.next_agent is None
