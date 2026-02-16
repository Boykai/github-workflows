"""Unit tests for Workflow Orchestrator - Agent mapping assignment."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.chat import TriggeredBy, WorkflowConfiguration
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
        # get_issue_with_comments is called once for issue context and once
        # by _update_agent_tracking_state to mark the agent as Active.
        assert mock_github_service.get_issue_with_comments.call_count >= 1
        mock_github_service.get_issue_with_comments.assert_any_call(
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

    @pytest.mark.asyncio
    async def test_subsequent_agent_uses_branch_name_as_base_ref(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Subsequent agents should use branch name as base_ref to work on same branch."""
        from src.services.workflow_orchestrator import set_issue_main_branch

        # Simulate main branch being set by a prior agent (speckit.specify)
        set_issue_main_branch(42, "copilot/test-feature", 99, "abc123def456")

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.get_pull_request = AsyncMock(
            return_value={
                "last_commit": {"sha": "latest789sha000"},
                "is_draft": True,
            }
        )

        result = await orchestrator.assign_agent_for_status(workflow_context, "In Progress", 0)

        assert result is True
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args.kwargs["custom_agent"] == "speckit.implement"
        # Must use branch name so Copilot works on the same branch
        assert call_args.kwargs["base_ref"] == "copilot/test-feature"

        # Should pass existing_pr context to format_issue_context_as_prompt
        prompt_call = mock_github_service.format_issue_context_as_prompt.call_args
        existing_pr = prompt_call.kwargs.get("existing_pr") or prompt_call[1].get("existing_pr")
        assert existing_pr is not None
        assert existing_pr["number"] == 99
        assert existing_pr["head_ref"] == "copilot/test-feature"

        # Cleanup
        from src.services.workflow_orchestrator import clear_issue_main_branch

        clear_issue_main_branch(42)

    @pytest.mark.asyncio
    async def test_all_subsequent_agents_use_branch_name(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """ALL subsequent agents (plan, tasks) should use branch name to work on same PR."""
        from src.services.workflow_orchestrator import set_issue_main_branch

        set_issue_main_branch(42, "copilot/test-feature", 99, "abc123def456")

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.get_pull_request = AsyncMock(
            return_value={
                "last_commit": {"sha": "commit789abc"},
                "is_draft": True,
            }
        )

        result = await orchestrator.assign_agent_for_status(workflow_context, "Ready", 0)

        assert result is True
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args.kwargs["custom_agent"] == "speckit.plan"
        # Must use branch name so Copilot continues on the same branch
        assert call_args.kwargs["base_ref"] == "copilot/test-feature"

        # Should pass existing_pr context
        prompt_call = mock_github_service.format_issue_context_as_prompt.call_args
        existing_pr = prompt_call.kwargs.get("existing_pr") or prompt_call[1].get("existing_pr")
        assert existing_pr is not None
        assert existing_pr["number"] == 99
        assert existing_pr["head_ref"] == "copilot/test-feature"

        # Cleanup
        from src.services.workflow_orchestrator import clear_issue_main_branch

        clear_issue_main_branch(42)

    @pytest.mark.asyncio
    async def test_first_agent_uses_main_as_base_ref(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Only the first agent should use repo main as base_ref."""
        # No main_branch_info set — this is the first agent

        mock_github_service.get_issue_with_comments.return_value = {
            "title": "Test",
            "body": "Body",
            "comments": [],
        }
        mock_github_service.format_issue_context_as_prompt.return_value = "Prompt"
        mock_github_service.assign_copilot_to_issue.return_value = True
        mock_github_service.find_existing_pr_for_issue.return_value = None

        result = await orchestrator.assign_agent_for_status(workflow_context, "Backlog", 0)

        assert result is True
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args.kwargs["custom_agent"] == "speckit.specify"
        # First agent uses repo main
        assert call_args.kwargs["base_ref"] == "main"


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


class TestWorkflowConfigManagement:
    """Tests for workflow configuration management functions."""

    def setup_method(self):
        """Clear configs before each test."""
        from src.services.workflow_orchestrator import _workflow_configs

        _workflow_configs.clear()

    def test_get_workflow_config_returns_none_for_unknown(self):
        """Should return None for unknown project ID."""
        from src.services.workflow_orchestrator import get_workflow_config

        result = get_workflow_config("unknown_project")
        assert result is None

    def test_set_and_get_workflow_config(self):
        """Should store and retrieve workflow config."""
        from src.services.workflow_orchestrator import (
            get_workflow_config,
            set_workflow_config,
        )

        config = WorkflowConfiguration(
            project_id="PVT_123",
            repository_owner="owner",
            repository_name="repo",
        )

        set_workflow_config("PVT_123", config)
        result = get_workflow_config("PVT_123")

        assert result is not None
        assert result.project_id == "PVT_123"


class TestPipelineStateManagement:
    """Tests for pipeline state management functions."""

    def setup_method(self):
        """Clear pipeline states before each test."""
        from src.services.workflow_orchestrator import _pipeline_states

        _pipeline_states.clear()

    def test_get_pipeline_state_returns_none_for_unknown(self):
        """Should return None for unknown issue number."""
        from src.services.workflow_orchestrator import get_pipeline_state

        result = get_pipeline_state(999)
        assert result is None

    def test_set_and_get_pipeline_state(self):
        """Should store and retrieve pipeline state."""
        from src.services.workflow_orchestrator import (
            get_pipeline_state,
            set_pipeline_state,
        )

        state = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan"],
            current_agent_index=0,
        )

        set_pipeline_state(42, state)
        result = get_pipeline_state(42)

        assert result is not None
        assert result.issue_number == 42

    def test_remove_pipeline_state(self):
        """Should remove pipeline state."""
        from src.services.workflow_orchestrator import (
            get_pipeline_state,
            remove_pipeline_state,
            set_pipeline_state,
        )

        state = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan"],
            current_agent_index=0,
        )

        set_pipeline_state(42, state)
        remove_pipeline_state(42)
        result = get_pipeline_state(42)

        assert result is None

    def test_get_all_pipeline_states(self):
        """Should return all pipeline states."""
        from src.services.workflow_orchestrator import (
            get_all_pipeline_states,
            set_pipeline_state,
        )

        state1 = PipelineState(
            issue_number=1,
            project_id="PVT_1",
            status="Ready",
            agents=["a"],
            current_agent_index=0,
        )
        state2 = PipelineState(
            issue_number=2,
            project_id="PVT_2",
            status="Backlog",
            agents=["b"],
            current_agent_index=0,
        )

        set_pipeline_state(1, state1)
        set_pipeline_state(2, state2)

        result = get_all_pipeline_states()

        assert len(result) == 2
        assert 1 in result
        assert 2 in result


class TestIssueMainBranchManagement:
    """Tests for issue main branch management functions."""

    def setup_method(self):
        """Clear main branches before each test."""
        from src.services.workflow_orchestrator import _issue_main_branches

        _issue_main_branches.clear()

    def test_get_issue_main_branch_returns_none_for_unknown(self):
        """Should return None for unknown issue number."""
        from src.services.workflow_orchestrator import get_issue_main_branch

        result = get_issue_main_branch(999)
        assert result is None

    def test_set_and_get_issue_main_branch(self):
        """Should store and retrieve main branch info."""
        from src.services.workflow_orchestrator import (
            get_issue_main_branch,
            set_issue_main_branch,
        )

        set_issue_main_branch(42, "copilot/feature-42", 100)
        result = get_issue_main_branch(42)

        assert result is not None
        assert result["branch"] == "copilot/feature-42"
        assert result["pr_number"] == 100

    def test_set_issue_main_branch_does_not_overwrite(self):
        """Should not overwrite existing main branch."""
        from src.services.workflow_orchestrator import (
            get_issue_main_branch,
            set_issue_main_branch,
        )

        set_issue_main_branch(42, "first-branch", 100)
        set_issue_main_branch(42, "second-branch", 200)  # Should be ignored

        result = get_issue_main_branch(42)
        assert result["branch"] == "first-branch"
        assert result["pr_number"] == 100

    def test_clear_issue_main_branch(self):
        """Should clear main branch info."""
        from src.services.workflow_orchestrator import (
            clear_issue_main_branch,
            get_issue_main_branch,
            set_issue_main_branch,
        )

        set_issue_main_branch(42, "copilot/feature-42", 100)
        clear_issue_main_branch(42)
        result = get_issue_main_branch(42)

        assert result is None


class TestTransitionLogging:
    """Tests for workflow transition logging."""

    def setup_method(self):
        """Clear transitions before each test."""
        from src.services.workflow_orchestrator import _transitions

        _transitions.clear()

    def test_get_transitions_empty(self):
        """Should return empty list when no transitions."""
        from src.services.workflow_orchestrator import get_transitions

        result = get_transitions()
        assert result == []

    def test_get_transitions_by_issue_id(self):
        """Should filter transitions by issue_id."""

        from src.models.chat import WorkflowTransition
        from src.services.workflow_orchestrator import (
            _transitions,
            get_transitions,
        )

        _transitions.append(
            WorkflowTransition(
                session_id="s1",
                project_id="p1",
                issue_id="I_1",
                from_status="Backlog",
                to_status="Ready",
                triggered_by=TriggeredBy.AUTOMATIC,
                success=True,
            )
        )
        _transitions.append(
            WorkflowTransition(
                session_id="s2",
                project_id="p1",
                issue_id="I_2",
                from_status="Ready",
                to_status="In Progress",
                triggered_by=TriggeredBy.AUTOMATIC,
                success=True,
            )
        )

        result = get_transitions(issue_id="I_1")
        assert len(result) == 1
        assert result[0].issue_id == "I_1"


class TestCreateIssueFromRecommendation:
    """Tests for create_issue_from_recommendation."""

    @pytest.fixture
    def mock_ai_service(self):
        return Mock()

    @pytest.fixture
    def mock_github_service(self):
        service = Mock()
        service.create_issue = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_ai_service, mock_github_service):
        return WorkflowOrchestrator(mock_ai_service, mock_github_service)

    @pytest.fixture
    def workflow_context(self):
        return WorkflowContext(
            session_id="test",
            project_id="PVT_123",
            access_token="token",
            repository_owner="owner",
            repository_name="repo",
        )

    @pytest.mark.asyncio
    async def test_creates_issue_successfully(
        self, orchestrator, workflow_context, mock_github_service
    ):
        """Should create GitHub issue from recommendation."""
        from uuid import uuid4

        from src.models.chat import IssueRecommendation

        recommendation = IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            title="Test Issue",
            body="Issue body",
            reasoning="Because",
            labels=["enhancement"],
            original_input="User request",
            user_story="As a user...",
            ui_ux_description="UI description",
            functional_requirements=["Req 1"],
        )

        mock_github_service.create_issue.return_value = {
            "node_id": "I_123",
            "number": 42,
            "html_url": "https://github.com/owner/repo/issues/42",
        }

        result = await orchestrator.create_issue_from_recommendation(
            workflow_context, recommendation
        )

        assert result["number"] == 42
        assert workflow_context.issue_id == "I_123"
        assert workflow_context.issue_number == 42
        mock_github_service.create_issue.assert_called_once()


class TestAddToProjectWithBacklog:
    """Tests for add_to_project_with_backlog."""

    @pytest.fixture
    def mock_ai_service(self):
        return Mock()

    @pytest.fixture
    def mock_github_service(self):
        service = Mock()
        service.add_issue_to_project = AsyncMock()
        service.update_item_status_by_name = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_ai_service, mock_github_service):
        return WorkflowOrchestrator(mock_ai_service, mock_github_service)

    @pytest.fixture
    def workflow_context(self):
        ctx = WorkflowContext(
            session_id="test",
            project_id="PVT_123",
            access_token="token",
            repository_owner="owner",
            repository_name="repo",
            issue_id="I_123",
        )
        ctx.config = WorkflowConfiguration(
            project_id="PVT_123",
            repository_owner="owner",
            repository_name="repo",
        )
        return ctx

    @pytest.mark.asyncio
    async def test_adds_issue_to_project(self, orchestrator, workflow_context, mock_github_service):
        """Should add issue to project with Backlog status."""
        mock_github_service.add_issue_to_project.return_value = "PVTI_123"
        mock_github_service.update_item_status_by_name.return_value = True

        result = await orchestrator.add_to_project_with_backlog(workflow_context)

        assert result == "PVTI_123"
        assert workflow_context.project_item_id == "PVTI_123"
        mock_github_service.add_issue_to_project.assert_called_once()
        mock_github_service.update_item_status_by_name.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_no_issue_id(self, orchestrator, mock_github_service):
        """Should raise when no issue_id in context."""
        ctx = WorkflowContext(
            session_id="test",
            project_id="PVT_123",
            access_token="token",
        )

        with pytest.raises(ValueError, match="No issue_id"):
            await orchestrator.add_to_project_with_backlog(ctx)
