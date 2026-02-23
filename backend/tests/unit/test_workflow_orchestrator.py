"""Unit tests for Workflow Orchestrator - Agent mapping assignment."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from src.models.chat import (
    AgentAssignment,
    IssueMetadata,
    IssueRecommendation,
    TriggeredBy,
    WorkflowConfiguration,
    WorkflowResult,
)
from src.services.workflow_orchestrator import (
    PipelineState,
    WorkflowContext,
    WorkflowOrchestrator,
    WorkflowState,
    _ci_get,
    _issue_main_branches,
    _pipeline_states,
    _workflow_configs,
    find_next_actionable_status,
    get_agent_slugs,
    get_next_status,
    get_pipeline_state,
    get_status_order,
    get_transitions,
    get_workflow_config,
    get_workflow_orchestrator,
    set_pipeline_state,
    set_workflow_config,
    update_issue_main_branch_sha,
)
from src.utils import utcnow


class TestHandleReadyStatusWithAgentMappings:
    """Tests for handle_ready_status with agent_mappings configuration."""

    @pytest.fixture(autouse=True)
    def clear_pending_state(self):
        """Clear global pending assignment state between tests."""
        from src.services.copilot_polling import (
            _pending_agent_assignments,
            _recovery_last_attempt,
        )

        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()
        yield
        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()

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
        with patch(
            "src.services.workflow_orchestrator.orchestrator.get_workflow_config",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await orchestrator.handle_ready_status(workflow_context)

        assert result is False


class TestAssignAgentForStatus:
    """Tests for assign_agent_for_status helper."""

    @pytest.fixture(autouse=True)
    def clear_pending_state(self):
        """Clear global pending assignment state between tests."""
        from src.services.copilot_polling import (
            _pending_agent_assignments,
            _recovery_last_attempt,
        )

        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()
        yield
        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()

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
        # Subsequent agents use the main PR's branch name as base_ref
        # (GitHub's API requires a branch name, not a commit SHA)
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
        # Subsequent agents use the main PR's branch name as base_ref
        # (GitHub's API requires a branch name, not a commit SHA)
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
        mock_github_service.find_existing_pr_for_issue = AsyncMock(return_value=None)

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

    @pytest.mark.asyncio
    async def test_get_workflow_config_returns_none_for_unknown(self):
        """Should return None for unknown project ID."""
        from src.services.workflow_orchestrator import get_workflow_config

        result = await get_workflow_config("unknown_project")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get_workflow_config(self):
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

        await set_workflow_config("PVT_123", config)
        result = await get_workflow_config("PVT_123")

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


# ── Pure Helper Function Tests ──────────────────────────────────────────────


class TestCiGet:
    """Tests for _ci_get case-insensitive dict lookup."""

    def test_exact_match(self):
        assert _ci_get({"Backlog": ["a"]}, "Backlog") == ["a"]

    def test_case_insensitive_match(self):
        assert _ci_get({"backlog": ["a"]}, "Backlog") == ["a"]

    def test_missing_key_returns_default(self):
        assert _ci_get({"Ready": ["a"]}, "Missing") == []

    def test_missing_key_custom_default(self):
        assert _ci_get({"Ready": ["a"]}, "Missing", "custom") == "custom"


class TestGetAgentSlugs:
    """Tests for get_agent_slugs."""

    def _config(self, **kw):
        return WorkflowConfiguration(
            project_id="P1", repository_owner="o", repository_name="r", **kw
        )

    def test_returns_slugs(self):
        cfg = self._config(agent_mappings={"Backlog": ["speckit.specify", "speckit.plan"]})
        assert get_agent_slugs(cfg, "Backlog") == ["speckit.specify", "speckit.plan"]

    def test_empty_status_returns_empty(self):
        cfg = self._config(agent_mappings={"Backlog": ["a"]})
        assert get_agent_slugs(cfg, "Ready") == []

    def test_case_insensitive(self):
        cfg = self._config(agent_mappings={"backlog": ["a"]})
        assert get_agent_slugs(cfg, "Backlog") == ["a"]


class TestGetStatusOrder:
    """Tests for get_status_order."""

    def test_default_order(self):
        cfg = WorkflowConfiguration(project_id="P1", repository_owner="o", repository_name="r")
        order = get_status_order(cfg)
        assert order == ["Backlog", "Ready", "In Progress", "In Review"]

    def test_custom_status_names(self):
        cfg = WorkflowConfiguration(
            project_id="P1",
            repository_owner="o",
            repository_name="r",
            status_backlog="Todo",
            status_ready="Pending",
            status_in_progress="Active",
            status_in_review="Review",
        )
        assert get_status_order(cfg) == ["Todo", "Pending", "Active", "Review"]


class TestGetNextStatus:
    """Tests for get_next_status."""

    def _config(self):
        return WorkflowConfiguration(project_id="P1", repository_owner="o", repository_name="r")

    def test_backlog_to_ready(self):
        assert get_next_status(self._config(), "Backlog") == "Ready"

    def test_in_review_is_last(self):
        assert get_next_status(self._config(), "In Review") is None

    def test_unknown_status_returns_none(self):
        assert get_next_status(self._config(), "Unknown") is None


class TestFindNextActionableStatus:
    """Tests for find_next_actionable_status."""

    def test_finds_next_with_agents(self):
        cfg = WorkflowConfiguration(
            project_id="P1",
            repository_owner="o",
            repository_name="r",
            agent_mappings={"In Progress": ["copilot-coding"]},
        )
        # From Backlog, Ready has no agents → skip to In Progress which has agents
        result = find_next_actionable_status(cfg, "Backlog")
        assert result == "In Progress"

    def test_returns_last_status_even_without_agents(self):
        """The final status (In Review) should always be returned."""
        cfg = WorkflowConfiguration(
            project_id="P1",
            repository_owner="o",
            repository_name="r",
            agent_mappings={},
        )
        result = find_next_actionable_status(cfg, "In Progress")
        assert result == "In Review"

    def test_already_at_last_status(self):
        cfg = WorkflowConfiguration(
            project_id="P1",
            repository_owner="o",
            repository_name="r",
        )
        assert find_next_actionable_status(cfg, "In Review") is None

    def test_unknown_status_returns_none(self):
        cfg = WorkflowConfiguration(
            project_id="P1",
            repository_owner="o",
            repository_name="r",
        )
        assert find_next_actionable_status(cfg, "Unknown") is None


class TestLogTransition:
    """Tests for WorkflowOrchestrator.log_transition."""

    def setup_method(self):
        from src.services.workflow_orchestrator import _transitions

        _transitions.clear()

    @pytest.fixture
    def orchestrator(self):
        return WorkflowOrchestrator(Mock(), Mock())

    def _make_ctx(self, **overrides):
        defaults = {
            "session_id": "s1",
            "project_id": "p1",
            "issue_id": "I_1",
            "issue_number": 1,
            "repository_owner": "o",
            "repository_name": "r",
            "access_token": "tok",
        }
        defaults.update(overrides)
        return WorkflowContext(**defaults)

    def test_log_transition(self, orchestrator):
        from src.services.workflow_orchestrator import _transitions

        ctx = self._make_ctx()
        orchestrator.log_transition(
            ctx=ctx,
            from_status="Backlog",
            to_status="Ready",
            triggered_by=TriggeredBy.AUTOMATIC,
            success=True,
        )
        assert len(_transitions) == 1
        assert _transitions[0].to_status == "Ready"
        assert _transitions[0].project_id == "p1"

    def test_log_multiple_transitions(self, orchestrator):
        from src.services.workflow_orchestrator import _transitions

        ctx = self._make_ctx()
        for i in range(5):
            orchestrator.log_transition(
                ctx=ctx,
                from_status=f"status-{i}",
                to_status=f"status-{i + 1}",
                triggered_by=TriggeredBy.MANUAL,
                success=True,
            )
        assert len(_transitions) == 5

    def teardown_method(self):
        from src.services.workflow_orchestrator import _transitions

        _transitions.clear()


class TestGetWorkflowOrchestrator:
    """Tests for get_workflow_orchestrator singleton."""

    def test_returns_same_instance(self):
        o1 = get_workflow_orchestrator()
        o2 = get_workflow_orchestrator()
        assert o1 is o2

    def test_returns_workflow_orchestrator(self):
        o = get_workflow_orchestrator()
        assert isinstance(o, WorkflowOrchestrator)


class TestFormatIssueBody:
    """Tests for WorkflowOrchestrator.format_issue_body."""

    @pytest.fixture
    def orchestrator(self):
        return WorkflowOrchestrator(Mock(), Mock())

    def test_basic_body(self, orchestrator):
        rec = IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            original_input="Add CSV export",
            title="CSV Export",
            user_story="As a user I want CSV export",
            ui_ux_description="Export button in toolbar",
            functional_requirements=["Must export CSV", "Must support filtering"],
        )
        body = orchestrator.format_issue_body(rec)
        assert "## User Story" in body
        assert "## UI/UX Description" in body
        assert "## Functional Requirements" in body
        assert "- Must export CSV" in body
        assert "- Must support filtering" in body
        assert "Generated by AI" in body

    def test_body_with_metadata(self, orchestrator):
        rec = IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            original_input="Test",
            title="Test",
            user_story="Story",
            ui_ux_description="UI",
            functional_requirements=["Req"],
            metadata=IssueMetadata(
                labels=["bug", "urgent"],
                estimate_hours=4,
                start_date="2026-01-01",
                target_date="2026-02-01",
            ),
        )
        body = orchestrator.format_issue_body(rec)
        assert "## Metadata" in body
        assert "`bug`" in body
        assert "4.0h" in body

    def test_body_with_original_context(self, orchestrator):
        rec = IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            original_input="Short text",
            title="T",
            user_story="S",
            ui_ux_description="U",
            functional_requirements=["R"],
        )
        # original_input is included in Original Request section
        body = orchestrator.format_issue_body(rec)
        assert "## Original Request" in body
        assert "Short text" in body


class TestUpdateAgentTrackingState:
    """Tests for _update_agent_tracking_state."""

    @pytest.fixture
    def mock_github_service(self):
        service = Mock()
        service.get_issue_with_comments = AsyncMock()
        service.update_issue_body = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_github_service):
        return WorkflowOrchestrator(Mock(), mock_github_service)

    @pytest.fixture
    def ctx(self):
        return WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            repository_owner="o",
            repository_name="r",
            issue_number=42,
        )

    @pytest.mark.asyncio
    async def test_no_issue_number_returns_false(self, orchestrator):
        ctx = WorkflowContext(session_id="s", project_id="P1", access_token="tok")
        result = await orchestrator._update_agent_tracking_state(ctx, "agent", "active")
        assert result is False

    @pytest.mark.asyncio
    async def test_unknown_state_returns_false(self, orchestrator, ctx, mock_github_service):
        mock_github_service.get_issue_with_comments.return_value = {"body": "content"}
        result = await orchestrator._update_agent_tracking_state(ctx, "agent", "invalid")
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_body_returns_false(self, orchestrator, ctx, mock_github_service):
        mock_github_service.get_issue_with_comments.return_value = {"body": ""}
        result = await orchestrator._update_agent_tracking_state(ctx, "agent", "active")
        assert result is False


# ──────────────────────────────────────────────────────────────────────────────
# Module-level helpers: update_issue_main_branch_sha, get_workflow_config, etc.
# ──────────────────────────────────────────────────────────────────────────────


class TestUpdateIssueMainBranchSha:
    """Tests for update_issue_main_branch_sha."""

    def setup_method(self):
        _issue_main_branches.clear()

    def teardown_method(self):
        _issue_main_branches.clear()

    def test_updates_sha_when_branch_exists(self):
        _issue_main_branches[1] = {"branch": "main", "head_sha": "old_sha"}
        update_issue_main_branch_sha(1, "new_sha_1234")
        assert _issue_main_branches[1]["head_sha"] == "new_sha_1234"

    def test_noop_when_no_branch(self):
        # Issue not in _issue_main_branches → early return, no crash
        update_issue_main_branch_sha(99, "sha123")
        assert 99 not in _issue_main_branches


class TestGetTransitions:
    """Tests for get_transitions."""

    def setup_method(self):
        from src.services.workflow_orchestrator import _transitions

        _transitions.clear()

    def teardown_method(self):
        from src.services.workflow_orchestrator import _transitions

        _transitions.clear()

    def test_returns_empty_list(self):
        assert get_transitions() == []

    def test_returns_filtered_by_issue_id(self):
        orch = WorkflowOrchestrator(Mock(), Mock())
        ctx = WorkflowContext(
            session_id="s",
            project_id="p",
            access_token="t",
            issue_id="I_1",
            issue_number=1,
            repository_owner="o",
            repository_name="r",
        )
        orch.log_transition(
            ctx=ctx,
            from_status=None,
            to_status="Ready",
            triggered_by=TriggeredBy.AUTOMATIC,
            success=True,
        )
        ctx2 = WorkflowContext(
            session_id="s",
            project_id="p",
            access_token="t",
            issue_id="I_2",
            issue_number=2,
            repository_owner="o",
            repository_name="r",
        )
        orch.log_transition(
            ctx=ctx2,
            from_status=None,
            to_status="Backlog",
            triggered_by=TriggeredBy.MANUAL,
            success=True,
        )
        assert len(get_transitions(issue_id="I_1")) == 1
        assert len(get_transitions()) == 2


class TestDetectCompletionSignal:
    """Tests for detect_completion_signal."""

    @pytest.fixture
    def orch(self):
        return WorkflowOrchestrator(Mock(), Mock())

    def test_closed_state(self, orch):
        assert orch.detect_completion_signal({"state": "closed"}) is True

    def test_copilot_complete_label(self, orch):
        task = {"labels": [{"name": "copilot-complete"}]}
        assert orch.detect_completion_signal(task) is True

    def test_open_state_no_label(self, orch):
        task = {"state": "open", "labels": [{"name": "bug"}]}
        assert orch.detect_completion_signal(task) is False

    def test_empty_task(self, orch):
        assert orch.detect_completion_signal({}) is False


class TestSetIssueMetadata:
    """Tests for _set_issue_metadata."""

    @pytest.fixture
    def mock_github(self):
        svc = Mock()
        svc.set_issue_metadata = AsyncMock(return_value={"priority": True})
        return svc

    @pytest.fixture
    def orch(self, mock_github):
        return WorkflowOrchestrator(Mock(), mock_github)

    @pytest.fixture
    def ctx(self):
        return WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            repository_owner="o",
            repository_name="r",
            project_item_id="ITEM_1",
        )

    @pytest.mark.asyncio
    async def test_sets_metadata(self, orch, ctx, mock_github):
        from src.models.chat import IssueMetadata

        meta = IssueMetadata(estimate_hours=4, start_date="2026-01-01")
        await orch._set_issue_metadata(ctx, meta)
        mock_github.set_issue_metadata.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_project_item_id_skips(self, orch, mock_github):
        ctx = WorkflowContext(session_id="s", project_id="P1", access_token="tok")
        from src.models.chat import IssueMetadata

        meta = IssueMetadata()
        await orch._set_issue_metadata(ctx, meta)
        mock_github.set_issue_metadata.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_does_not_raise(self, orch, ctx, mock_github):
        from src.models.chat import IssueMetadata

        mock_github.set_issue_metadata.side_effect = Exception("API error")
        meta = IssueMetadata(estimate_hours=2)
        # Should not raise
        await orch._set_issue_metadata(ctx, meta)


class TestTransitionToReady:
    """Tests for transition_to_ready."""

    @pytest.fixture
    def mock_github(self):
        svc = Mock()
        svc.update_item_status_by_name = AsyncMock(return_value=True)
        return svc

    @pytest.fixture
    def orch(self, mock_github):
        return WorkflowOrchestrator(Mock(), mock_github)

    @pytest.fixture
    def ctx(self):
        return WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            repository_owner="o",
            repository_name="r",
            project_item_id="ITEM_1",
            config=WorkflowConfiguration(
                project_id="P1",
                repository_owner="o",
                repository_name="r",
            ),
        )

    @pytest.mark.asyncio
    async def test_success(self, orch, ctx, mock_github):
        result = await orch.transition_to_ready(ctx)
        assert result is True
        mock_github.update_item_status_by_name.assert_awaited_once()
        assert ctx.current_state == WorkflowState.READY

    @pytest.mark.asyncio
    async def test_no_project_item_id_raises(self, orch):
        ctx = WorkflowContext(session_id="s", project_id="P1", access_token="tok")
        with pytest.raises(ValueError, match="No project_item_id"):
            await orch.transition_to_ready(ctx)

    @pytest.mark.asyncio
    async def test_no_config_returns_false(self, orch):
        ctx = WorkflowContext(
            session_id="s",
            project_id="NO_CONFIG",
            access_token="tok",
            project_item_id="ITEM_1",
        )
        with patch(
            "src.services.workflow_orchestrator.orchestrator.get_workflow_config",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await orch.transition_to_ready(ctx)
        assert result is False

    @pytest.mark.asyncio
    async def test_status_update_failure(self, orch, ctx, mock_github):
        mock_github.update_item_status_by_name.return_value = False
        result = await orch.transition_to_ready(ctx)
        assert result is False


class TestAssignAgentGuardClauses:
    """Tests for assign_agent_for_status guard clauses."""

    @pytest.fixture
    def orch(self):
        return WorkflowOrchestrator(Mock(), Mock())

    @pytest.mark.asyncio
    async def test_no_issue_id_raises(self, orch):
        ctx = WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            issue_number=1,
            config=WorkflowConfiguration(
                project_id="P1",
                repository_owner="o",
                repository_name="r",
                agent_mappings={"Ready": ["copilot"]},
            ),
        )
        with pytest.raises(ValueError, match="issue_id required"):
            await orch.assign_agent_for_status(ctx, "Ready")

    @pytest.mark.asyncio
    async def test_no_issue_number_raises(self, orch):
        ctx = WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            issue_id="I_1",
            config=WorkflowConfiguration(
                project_id="P1",
                repository_owner="o",
                repository_name="r",
                agent_mappings={"Ready": ["copilot"]},
            ),
        )
        with pytest.raises(ValueError, match="issue_number required"):
            await orch.assign_agent_for_status(ctx, "Ready")

    @pytest.mark.asyncio
    async def test_no_config_returns_false(self, orch):
        ctx = WorkflowContext(
            session_id="s",
            project_id="NO_CFG",
            access_token="tok",
            issue_id="I_1",
            issue_number=1,
        )
        with patch(
            "src.services.workflow_orchestrator.orchestrator.get_workflow_config",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await orch.assign_agent_for_status(ctx, "Ready")
        assert result is False

    @pytest.mark.asyncio
    async def test_no_agents_returns_true(self, orch):
        ctx = WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            issue_id="I_1",
            issue_number=1,
            config=WorkflowConfiguration(
                project_id="P1",
                repository_owner="o",
                repository_name="r",
                agent_mappings={},
            ),
        )
        result = await orch.assign_agent_for_status(ctx, "Ready")
        assert result is True

    @pytest.mark.asyncio
    async def test_agent_index_out_of_range_returns_true(self, orch):
        ctx = WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            issue_id="I_1",
            issue_number=1,
            config=WorkflowConfiguration(
                project_id="P1",
                repository_owner="o",
                repository_name="r",
                agent_mappings={"Ready": ["copilot"]},
            ),
        )
        result = await orch.assign_agent_for_status(ctx, "Ready", agent_index=5)
        assert result is True


class TestUpdateAgentTrackingDonePath:
    """Tests for _update_agent_tracking_state - 'done' and 'active' paths."""

    @pytest.fixture
    def mock_github(self):
        svc = Mock()
        svc.get_issue_with_comments = AsyncMock(
            return_value={"body": "## Agent Tracking\n- agent-1: pending"}
        )
        svc.update_issue_body = AsyncMock(return_value=True)
        return svc

    @pytest.fixture
    def orch(self, mock_github):
        return WorkflowOrchestrator(Mock(), mock_github)

    @pytest.fixture
    def ctx(self):
        return WorkflowContext(
            session_id="s",
            project_id="P1",
            access_token="tok",
            repository_owner="o",
            repository_name="r",
            issue_number=42,
        )

    @pytest.mark.asyncio
    async def test_active_path(self, orch, ctx, mock_github):
        with patch("src.services.agent_tracking.mark_agent_active", return_value="updated body"):
            result = await orch._update_agent_tracking_state(ctx, "agent-1", "active")
        assert result is True
        mock_github.update_issue_body.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_done_path(self, orch, ctx, mock_github):
        with patch("src.services.agent_tracking.mark_agent_done", return_value="updated body"):
            result = await orch._update_agent_tracking_state(ctx, "agent-1", "done")
        assert result is True
        mock_github.update_issue_body.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_change_needed(self, orch, ctx, mock_github):
        body = "unchanged body"
        mock_github.get_issue_with_comments.return_value = {"body": body}
        with patch("src.services.agent_tracking.mark_agent_active", return_value=body):
            result = await orch._update_agent_tracking_state(ctx, "agent-1", "active")
        assert result is True
        mock_github.update_issue_body.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_exception_returns_false(self, orch, ctx, mock_github):
        mock_github.get_issue_with_comments.side_effect = Exception("API error")
        result = await orch._update_agent_tracking_state(ctx, "agent-1", "active")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_failure_returns_false(self, orch, ctx, mock_github):
        mock_github.update_issue_body.return_value = False
        with patch("src.services.agent_tracking.mark_agent_active", return_value="new body"):
            result = await orch._update_agent_tracking_state(ctx, "agent-1", "active")
        assert result is False


class TestGetWorkflowConfigWithDB:
    """Tests for get_workflow_config with DB fallback."""

    def setup_method(self):
        _workflow_configs.clear()

    def teardown_method(self):
        _workflow_configs.clear()

    @pytest.mark.asyncio
    async def test_returns_cached_config(self):
        cfg = WorkflowConfiguration(project_id="P1", repository_owner="o", repository_name="r")
        _workflow_configs["P1"] = cfg
        assert await get_workflow_config("P1") is cfg

    @pytest.mark.asyncio
    async def test_loads_from_db_and_caches(self):
        cfg = WorkflowConfiguration(project_id="P1", repository_owner="o", repository_name="r")
        with patch(
            "src.services.workflow_orchestrator.config._load_workflow_config_from_db",
            new_callable=AsyncMock,
            return_value=cfg,
        ):
            result = await get_workflow_config("P1")
        assert result is cfg
        assert _workflow_configs["P1"] is cfg

    @pytest.mark.asyncio
    async def test_db_returns_none(self):
        with patch(
            "src.services.workflow_orchestrator.config._load_workflow_config_from_db",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await get_workflow_config("MISSING")
        assert result is None
        assert "MISSING" not in _workflow_configs


class TestSetWorkflowConfig:
    """Tests for set_workflow_config."""

    def setup_method(self):
        _workflow_configs.clear()

    def teardown_method(self):
        _workflow_configs.clear()

    @pytest.mark.asyncio
    async def test_updates_cache_and_persists(self):
        cfg = WorkflowConfiguration(project_id="P1", repository_owner="o", repository_name="r")
        with patch(
            "src.services.workflow_orchestrator.config._persist_workflow_config_to_db",
            new_callable=AsyncMock,
        ) as mock_persist:
            await set_workflow_config("P1", cfg, "user123")
        assert _workflow_configs["P1"] is cfg
        mock_persist.assert_called_once_with("P1", cfg, "user123")


class TestFormatIssueBodyTechnicalNotes:
    """Tests for format_issue_body - technical_notes path."""

    @pytest.fixture
    def orch(self):
        return WorkflowOrchestrator(Mock(), Mock())

    def test_body_with_technical_notes(self, orch):
        rec = IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            original_input="Fix performance",
            title="Perf Fix",
            user_story="As a user I want fast loads",
            ui_ux_description="N/A",
            functional_requirements=["Optimize queries"],
            technical_notes="Use Redis caching for hot queries",
        )
        body = orch.format_issue_body(rec)
        assert "## Technical Notes" in body
        assert "Redis caching" in body


# ────────────────────────────────────────────────────────────────────
# Shared helpers for the new test classes below
# ────────────────────────────────────────────────────────────────────


def _make_orch() -> WorkflowOrchestrator:
    """Create orchestrator with fully mocked GitHub / AI services."""
    gh = Mock()
    for m in (
        "check_copilot_pr_completion",
        "mark_pr_ready_for_review",
        "update_item_status_by_name",
        "get_repository_owner",
        "assign_issue",
        "get_issue_with_comments",
        "format_issue_context_as_prompt",
        "assign_copilot_to_issue",
        "validate_assignee",
        "find_existing_pr_for_issue",
        "tailor_body_for_agent",
        "create_sub_issue",
        "add_issue_to_project",
        "update_issue_state",
        "update_sub_issue_project_status",
        "link_pull_request_to_issue",
        "get_pull_request",
        "create_issue",
        "update_project_item_field",
        "set_issue_metadata",
    ):
        setattr(gh, m, AsyncMock())
    gh.tailor_body_for_agent = Mock(return_value="tailored body")
    gh.format_issue_context_as_prompt = Mock(return_value="prompt")
    return WorkflowOrchestrator(Mock(), gh)


def _make_ctx(**overrides) -> WorkflowContext:
    """Build a minimal WorkflowContext, applying *overrides*."""
    defaults = {
        "session_id": "s1",
        "project_id": "P1",
        "access_token": "tok",
        "repository_owner": "owner",
        "repository_name": "repo",
        "issue_id": "I_1",
        "issue_number": 10,
        "project_item_id": "PVTI_1",
        "current_state": WorkflowState.IN_PROGRESS,
    }
    defaults.update(overrides)
    return WorkflowContext(**defaults)


def _make_config(**overrides) -> WorkflowConfiguration:
    """Build a minimal WorkflowConfiguration."""
    defaults = {
        "project_id": "P1",
        "repository_owner": "owner",
        "repository_name": "repo",
        "agent_mappings": {
            "Backlog": [AgentAssignment(slug="speckit.specify")],
            "In Progress": [AgentAssignment(slug="speckit.implement")],
        },
    }
    defaults.update(overrides)
    return WorkflowConfiguration(**defaults)


# ────────────────────────────────────────────────────────────────────
# handle_in_progress_status  (~111 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestHandleInProgressStatus:
    """Tests for handle_in_progress_status."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _workflow_configs.clear()
        yield
        _workflow_configs.clear()

    @pytest.mark.asyncio
    async def test_missing_issue_number(self):
        orch = _make_orch()
        ctx = _make_ctx(issue_number=None)
        with pytest.raises(ValueError, match="issue_number required"):
            await orch.handle_in_progress_status(ctx)

    @pytest.mark.asyncio
    async def test_missing_project_item_id(self):
        orch = _make_orch()
        ctx = _make_ctx(project_item_id=None)
        with pytest.raises(ValueError, match="project_item_id required"):
            await orch.handle_in_progress_status(ctx)

    @pytest.mark.asyncio
    async def test_no_config_returns_false(self):
        orch = _make_orch()
        ctx = _make_ctx(config=None)
        result = await orch.handle_in_progress_status(ctx)
        assert result is False

    @pytest.mark.asyncio
    async def test_no_completed_pr_returns_false(self):
        orch = _make_orch()
        cfg = _make_config()
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(return_value=None)
        result = await orch.handle_in_progress_status(ctx)
        assert result is False

    @pytest.mark.asyncio
    async def test_completed_pr_not_draft_happy_path(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="reviewer-user")
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 99, "is_draft": False}
        )
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=True)

        result = await orch.handle_in_progress_status(ctx)

        assert result is True
        assert ctx.current_state == WorkflowState.IN_REVIEW
        orch.github.assign_issue.assert_awaited_once()
        assert orch.github.assign_issue.call_args.kwargs["assignees"] == ["reviewer-user"]

    @pytest.mark.asyncio
    async def test_completed_pr_draft_marks_ready(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="rev")
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 99, "is_draft": True, "id": "PR_NODE"}
        )
        orch.github.mark_pr_ready_for_review = AsyncMock(return_value=True)
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=True)

        result = await orch.handle_in_progress_status(ctx)
        assert result is True
        orch.github.mark_pr_ready_for_review.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_mark_ready_for_review_failure_still_continues(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="rev")
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 99, "is_draft": True, "id": "PR_NODE"}
        )
        orch.github.mark_pr_ready_for_review = AsyncMock(return_value=False)
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=True)

        result = await orch.handle_in_progress_status(ctx)
        assert result is True  # continues despite mark_ready failure

    @pytest.mark.asyncio
    async def test_status_update_fails_returns_false(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="rev")
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 99, "is_draft": False}
        )
        orch.github.update_item_status_by_name = AsyncMock(return_value=False)

        result = await orch.handle_in_progress_status(ctx)
        assert result is False

    @pytest.mark.asyncio
    async def test_fallback_to_repo_owner_when_no_reviewer(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="")
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 99, "is_draft": False}
        )
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.get_repository_owner = AsyncMock(return_value="fallback-owner")
        orch.github.assign_issue = AsyncMock(return_value=True)

        result = await orch.handle_in_progress_status(ctx)
        assert result is True
        orch.github.get_repository_owner.assert_awaited_once()
        assert orch.github.assign_issue.call_args.kwargs["assignees"] == ["fallback-owner"]

    @pytest.mark.asyncio
    async def test_assign_reviewer_fails_still_returns_true(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="rev")
        ctx = _make_ctx(config=cfg)
        orch.github.check_copilot_pr_completion = AsyncMock(
            return_value={"number": 3, "is_draft": False}
        )
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=False)

        result = await orch.handle_in_progress_status(ctx)
        assert result is True  # assignment failure doesn't fail the transition


# ────────────────────────────────────────────────────────────────────
# handle_completion  (~67 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestHandleCompletion:
    """Tests for handle_completion."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _workflow_configs.clear()
        yield
        _workflow_configs.clear()

    @pytest.mark.asyncio
    async def test_missing_issue_number(self):
        orch = _make_orch()
        with pytest.raises(ValueError, match="issue_number required"):
            await orch.handle_completion(_make_ctx(issue_number=None))

    @pytest.mark.asyncio
    async def test_missing_project_item_id(self):
        orch = _make_orch()
        with pytest.raises(ValueError, match="project_item_id required"):
            await orch.handle_completion(_make_ctx(project_item_id=None))

    @pytest.mark.asyncio
    async def test_no_config_returns_false(self):
        orch = _make_orch()
        result = await orch.handle_completion(_make_ctx(config=None))
        assert result is False

    @pytest.mark.asyncio
    async def test_status_update_fails(self):
        orch = _make_orch()
        cfg = _make_config()
        orch.github.update_item_status_by_name = AsyncMock(return_value=False)
        result = await orch.handle_completion(_make_ctx(config=cfg))
        assert result is False

    @pytest.mark.asyncio
    async def test_happy_path_with_configured_reviewer(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="my-reviewer")
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=True)
        ctx = _make_ctx(config=cfg)

        result = await orch.handle_completion(ctx)
        assert result is True
        assert ctx.current_state == WorkflowState.IN_REVIEW
        assert orch.github.assign_issue.call_args.kwargs["assignees"] == ["my-reviewer"]

    @pytest.mark.asyncio
    async def test_fallback_to_repo_owner(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="")
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.get_repository_owner = AsyncMock(return_value="repo-owner")
        orch.github.assign_issue = AsyncMock(return_value=True)

        result = await orch.handle_completion(_make_ctx(config=cfg))
        assert result is True
        orch.github.get_repository_owner.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_assign_failure_still_returns_true(self):
        orch = _make_orch()
        cfg = _make_config(review_assignee="rev")
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=False)

        result = await orch.handle_completion(_make_ctx(config=cfg))
        assert result is True  # warn-only


# ────────────────────────────────────────────────────────────────────
# create_all_sub_issues  (~99 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestCreateAllSubIssues:
    """Tests for create_all_sub_issues."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _workflow_configs.clear()
        yield
        _workflow_configs.clear()

    @pytest.mark.asyncio
    async def test_no_config_returns_empty(self):
        orch = _make_orch()
        ctx = _make_ctx(config=None)
        result = await orch.create_all_sub_issues(ctx)
        assert result == {}

    @pytest.mark.asyncio
    async def test_no_issue_number_returns_empty(self):
        orch = _make_orch()
        ctx = _make_ctx(config=_make_config(), issue_number=None)
        result = await orch.create_all_sub_issues(ctx)
        assert result == {}

    @pytest.mark.asyncio
    async def test_no_repo_owner_returns_empty(self):
        orch = _make_orch()
        ctx = _make_ctx(config=_make_config(), repository_owner="")
        result = await orch.create_all_sub_issues(ctx)
        assert result == {}

    @pytest.mark.asyncio
    async def test_parent_fetch_fails_returns_empty(self):
        orch = _make_orch()
        orch.github.get_issue_with_comments = AsyncMock(side_effect=Exception("network"))
        ctx = _make_ctx(config=_make_config())
        result = await orch.create_all_sub_issues(ctx)
        assert result == {}

    @pytest.mark.asyncio
    async def test_no_agents_returns_empty(self):
        orch = _make_orch()
        cfg = _make_config(agent_mappings={})
        orch.github.get_issue_with_comments = AsyncMock(
            return_value={"body": "parent body", "title": "Parent"}
        )
        ctx = _make_ctx(config=cfg)
        result = await orch.create_all_sub_issues(ctx)
        assert result == {}

    @pytest.mark.asyncio
    async def test_happy_path_creates_sub_issues(self):
        orch = _make_orch()
        cfg = _make_config(
            agent_mappings={
                "Backlog": [AgentAssignment(slug="agent-a")],
                "In Progress": [AgentAssignment(slug="agent-b")],
            }
        )
        orch.github.get_issue_with_comments = AsyncMock(
            return_value={"body": "parent body", "title": "Parent Title"}
        )
        orch.github.create_sub_issue = AsyncMock(
            side_effect=[
                {"number": 11, "node_id": "N11", "html_url": "http://11"},
                {"number": 12, "node_id": "N12", "html_url": "http://12"},
            ]
        )
        orch.github.add_issue_to_project = AsyncMock()
        ctx = _make_ctx(config=cfg)

        result = await orch.create_all_sub_issues(ctx)

        assert len(result) == 2
        assert result["agent-a"]["number"] == 11
        assert result["agent-b"]["number"] == 12
        assert orch.github.add_issue_to_project.await_count == 2

    @pytest.mark.asyncio
    async def test_individual_sub_issue_failure_continues(self):
        orch = _make_orch()
        cfg = _make_config(
            agent_mappings={
                "Backlog": [AgentAssignment(slug="ok-agent")],
                "In Progress": [AgentAssignment(slug="fail-agent")],
            }
        )
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b", "title": "T"})
        orch.github.create_sub_issue = AsyncMock(
            side_effect=[
                {"number": 11, "node_id": "N11", "html_url": "u"},
                Exception("fail"),
            ]
        )
        orch.github.add_issue_to_project = AsyncMock()
        ctx = _make_ctx(config=cfg)

        result = await orch.create_all_sub_issues(ctx)
        assert "ok-agent" in result
        assert "fail-agent" not in result

    @pytest.mark.asyncio
    async def test_add_to_project_failure_continues(self):
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"Backlog": [AgentAssignment(slug="a1")]})
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b", "title": "T"})
        orch.github.create_sub_issue = AsyncMock(
            return_value={"number": 11, "node_id": "N11", "html_url": "u"}
        )
        orch.github.add_issue_to_project = AsyncMock(side_effect=Exception("proj fail"))
        ctx = _make_ctx(config=cfg)

        result = await orch.create_all_sub_issues(ctx)
        assert "a1" in result  # sub-issue still returned despite project add failure


# ────────────────────────────────────────────────────────────────────
# execute_full_workflow  (~97 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestExecuteFullWorkflow:
    """Tests for execute_full_workflow."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _workflow_configs.clear()
        _pipeline_states.clear()
        yield
        _workflow_configs.clear()
        _pipeline_states.clear()

    def _make_rec(self):
        return IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            original_input="Add feature",
            title="New Feature",
            user_story="As a user I want to do X",
            ui_ux_description="N/A",
            functional_requirements=["Do X"],
        )

    @pytest.mark.asyncio
    async def test_happy_path_returns_success(self):
        orch = _make_orch()
        cfg = _make_config(
            agent_mappings={
                "Backlog": [AgentAssignment(slug="speckit.specify")],
                "In Progress": [AgentAssignment(slug="speckit.implement")],
            }
        )
        await set_workflow_config("P1", cfg)
        ctx = _make_ctx(config=cfg)
        rec = self._make_rec()

        orch.create_issue_from_recommendation = AsyncMock()
        orch.add_to_project_with_backlog = AsyncMock()
        orch.create_all_sub_issues = AsyncMock(return_value={})
        orch.assign_agent_for_status = AsyncMock(return_value=True)

        result = await orch.execute_full_workflow(ctx, rec)
        assert isinstance(result, WorkflowResult)
        assert result.success is True
        orch.assign_agent_for_status.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_backlog_pass_through_no_agents(self):
        """When Backlog has no agents, should advance to next actionable status."""
        orch = _make_orch()
        cfg = _make_config(
            agent_mappings={
                "Backlog": [],  # empty
                "In Progress": [AgentAssignment(slug="speckit.implement")],
            }
        )
        await set_workflow_config("P1", cfg)
        ctx = _make_ctx(config=cfg)
        rec = self._make_rec()

        orch.create_issue_from_recommendation = AsyncMock()
        orch.add_to_project_with_backlog = AsyncMock()
        orch.create_all_sub_issues = AsyncMock(return_value={})
        orch.assign_agent_for_status = AsyncMock(return_value=True)
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)

        result = await orch.execute_full_workflow(ctx, rec)
        assert result.success is True
        # Should have called update_item_status to advance past Backlog
        orch.github.update_item_status_by_name.assert_awaited()

    @pytest.mark.asyncio
    async def test_sub_issues_stored_in_pipeline_state(self):
        orch = _make_orch()
        cfg = _make_config()
        await set_workflow_config("P1", cfg)
        ctx = _make_ctx(config=cfg)
        rec = self._make_rec()

        sub_issues = {"speckit.specify": {"number": 20, "node_id": "N20", "url": "u"}}
        orch.create_issue_from_recommendation = AsyncMock()
        orch.add_to_project_with_backlog = AsyncMock()
        orch.create_all_sub_issues = AsyncMock(return_value=sub_issues)
        orch.assign_agent_for_status = AsyncMock(return_value=True)

        result = await orch.execute_full_workflow(ctx, rec)
        assert result.success is True
        ps = get_pipeline_state(ctx.issue_number)
        assert ps is not None
        assert ps.agent_sub_issues == sub_issues

    @pytest.mark.asyncio
    async def test_exception_returns_failure(self):
        orch = _make_orch()
        cfg = _make_config()
        ctx = _make_ctx(config=cfg)
        rec = self._make_rec()

        orch.create_issue_from_recommendation = AsyncMock(side_effect=RuntimeError("boom"))

        result = await orch.execute_full_workflow(ctx, rec)
        assert result.success is False
        assert "boom" in result.message


# ────────────────────────────────────────────────────────────────────
# handle_ready_status fallback paths  (~25 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestHandleReadyStatusFallback:
    """Tests for handle_ready_status fallback (assign_agent fails)."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _workflow_configs.clear()
        from src.services.copilot_polling import (
            _pending_agent_assignments,
            _recovery_last_attempt,
        )

        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()
        yield
        _workflow_configs.clear()
        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()

    @pytest.mark.asyncio
    async def test_agent_fails_fallback_to_assignee(self):
        orch = _make_orch()
        cfg = _make_config(copilot_assignee="fallback-user")
        ctx = _make_ctx(config=cfg)
        orch.assign_agent_for_status = AsyncMock(return_value=False)
        orch.github.validate_assignee = AsyncMock(return_value=True)
        orch.github.assign_issue = AsyncMock(return_value=True)
        orch.github.update_item_status_by_name = AsyncMock(return_value=True)

        result = await orch.handle_ready_status(ctx)
        assert result is True
        orch.github.validate_assignee.assert_awaited_once()
        orch.github.assign_issue.assert_awaited()

    @pytest.mark.asyncio
    async def test_status_update_fails_returns_false(self):
        orch = _make_orch()
        cfg = _make_config()
        ctx = _make_ctx(config=cfg)
        orch.assign_agent_for_status = AsyncMock(return_value=True)
        orch.github.update_item_status_by_name = AsyncMock(return_value=False)

        result = await orch.handle_ready_status(ctx)
        assert result is False


# ────────────────────────────────────────────────────────────────────
# assign_agent_for_status inner paths  (~130 uncovered lines)
# ────────────────────────────────────────────────────────────────────


class TestAssignAgentInnerPaths:
    """Tests for deeper branching inside assign_agent_for_status."""

    @pytest.fixture(autouse=True)
    def _clear(self):
        _workflow_configs.clear()
        _pipeline_states.clear()
        _issue_main_branches.clear()
        from src.services.copilot_polling import (
            _pending_agent_assignments,
            _recovery_last_attempt,
        )

        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()
        yield
        _workflow_configs.clear()
        _pipeline_states.clear()
        _issue_main_branches.clear()
        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()

    @pytest.mark.asyncio
    async def test_first_agent_discovers_existing_pr(self):
        """First agent (agent_index=0) finds existing PR, establishes main branch."""
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"In Progress": [AgentAssignment(slug="impl-agent")]})
        ctx = _make_ctx(config=cfg)
        orch.github.find_existing_pr_for_issue = AsyncMock(
            return_value={"number": 77, "head_ref": "copilot-branch"}
        )
        orch.github.get_pull_request = AsyncMock(return_value={"last_commit": {"sha": "abc123def"}})
        orch.github.link_pull_request_to_issue = AsyncMock()
        orch.github.assign_copilot_to_issue = AsyncMock(return_value=True)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})

        result = await orch.assign_agent_for_status(ctx, "In Progress", agent_index=0)
        assert result is True
        orch.github.link_pull_request_to_issue.assert_awaited_once()
        # Should have stored main branch
        assert _issue_main_branches.get(10) is not None

    @pytest.mark.asyncio
    async def test_first_agent_link_pr_fails_continues(self):
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"In Progress": [AgentAssignment(slug="impl")]})
        ctx = _make_ctx(config=cfg)
        orch.github.find_existing_pr_for_issue = AsyncMock(
            return_value={"number": 77, "head_ref": "branch"}
        )
        orch.github.get_pull_request = AsyncMock(return_value={"last_commit": {"sha": "s"}})
        orch.github.link_pull_request_to_issue = AsyncMock(side_effect=Exception("link fail"))
        orch.github.assign_copilot_to_issue = AsyncMock(return_value=True)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})

        result = await orch.assign_agent_for_status(ctx, "In Progress", agent_index=0)
        assert result is True  # continues despite link failure

    @pytest.mark.asyncio
    async def test_sub_issue_from_pipeline_state(self):
        """When pipeline state has pre-created sub-issues, uses them."""
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"Backlog": [AgentAssignment(slug="agent-x")]})
        ctx = _make_ctx(config=cfg)
        sub_info = {"number": 20, "node_id": "NODE_20", "url": "u"}
        set_pipeline_state(
            ctx.issue_number,
            PipelineState(
                issue_number=ctx.issue_number,
                project_id="P1",
                status="Backlog",
                agents=["agent-x"],
                agent_sub_issues={"agent-x": sub_info},
            ),
        )
        orch.github.find_existing_pr_for_issue = AsyncMock(return_value=None)
        orch.github.assign_copilot_to_issue = AsyncMock(return_value=True)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})
        orch.github.update_issue_state = AsyncMock()
        orch.github.update_sub_issue_project_status = AsyncMock()

        result = await orch.assign_agent_for_status(ctx, "Backlog", agent_index=0)
        assert result is True
        # Should have used sub-issue number for assignment
        call_kwargs = orch.github.assign_copilot_to_issue.call_args.kwargs
        assert call_kwargs["issue_number"] == 20

    @pytest.mark.asyncio
    async def test_dedup_guard_skips_recent_assignment(self):
        """If agent was recently assigned (within grace period), skip."""
        from src.services.copilot_polling import _pending_agent_assignments

        orch = _make_orch()
        cfg = _make_config(agent_mappings={"Backlog": [AgentAssignment(slug="myagent")]})
        ctx = _make_ctx(config=cfg)
        pending_key = f"{ctx.issue_number}:myagent"
        _pending_agent_assignments[pending_key] = utcnow()

        orch.github.find_existing_pr_for_issue = AsyncMock(return_value=None)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})

        result = await orch.assign_agent_for_status(ctx, "Backlog", agent_index=0)
        assert result is True  # treated as success (original in flight)
        orch.github.assign_copilot_to_issue.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self):
        """First attempt fails, second succeeds with retry."""
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"Backlog": [AgentAssignment(slug="retry-agent")]})
        ctx = _make_ctx(config=cfg)
        orch.github.find_existing_pr_for_issue = AsyncMock(return_value=None)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})
        orch.github.assign_copilot_to_issue = AsyncMock(
            side_effect=[False, True]  # fail then succeed
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await orch.assign_agent_for_status(ctx, "Backlog", agent_index=0)
        assert result is True
        assert orch.github.assign_copilot_to_issue.await_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_fail(self):
        """All 3 retry attempts fail."""
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"Backlog": [AgentAssignment(slug="fail-agent")]})
        ctx = _make_ctx(config=cfg)
        orch.github.find_existing_pr_for_issue = AsyncMock(return_value=None)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})
        orch.github.assign_copilot_to_issue = AsyncMock(return_value=False)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await orch.assign_agent_for_status(ctx, "Backlog", agent_index=0)
        assert result is False
        assert orch.github.assign_copilot_to_issue.await_count == 3

    @pytest.mark.asyncio
    async def test_success_marks_sub_issue_in_progress(self):
        """After successful assignment, sub-issue gets 'in-progress' label."""
        orch = _make_orch()
        cfg = _make_config(agent_mappings={"Backlog": [AgentAssignment(slug="agent-x")]})
        ctx = _make_ctx(config=cfg)
        sub_info = {"number": 20, "node_id": "NODE_20", "url": "u"}
        set_pipeline_state(
            ctx.issue_number,
            PipelineState(
                issue_number=ctx.issue_number,
                project_id="P1",
                status="Backlog",
                agents=["agent-x"],
                agent_sub_issues={"agent-x": sub_info},
            ),
        )
        orch.github.find_existing_pr_for_issue = AsyncMock(return_value=None)
        orch.github.assign_copilot_to_issue = AsyncMock(return_value=True)
        orch.github.get_issue_with_comments = AsyncMock(return_value={"body": "b"})
        orch.github.update_issue_state = AsyncMock()
        orch.github.update_sub_issue_project_status = AsyncMock()

        result = await orch.assign_agent_for_status(ctx, "Backlog", agent_index=0)
        assert result is True
        orch.github.update_issue_state.assert_awaited_once()
        assert orch.github.update_issue_state.call_args.kwargs["labels_add"] == ["in-progress"]


# ────────────────────────────────────────────────────────────────────
# _load_workflow_config_from_db / _persist_workflow_config_to_db
# ────────────────────────────────────────────────────────────────────


class TestWorkflowConfigDb:
    """Tests for DB-backed workflow config persistence."""

    @pytest.mark.asyncio
    async def test_load_from_db_settings_error_returns_none(self):
        from src.services.workflow_orchestrator import _load_workflow_config_from_db

        with patch("src.config.get_settings", side_effect=Exception("oops")):
            result = await _load_workflow_config_from_db("P1")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_from_db_workflow_config_column(self, tmp_path):
        import json
        import sqlite3

        from src.services.workflow_orchestrator import _load_workflow_config_from_db

        db = tmp_path / "test.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE project_settings (project_id TEXT, workflow_config TEXT, agent_pipeline_mappings TEXT)"
        )
        cfg_data = {
            "project_id": "P1",
            "repository_owner": "o",
            "repository_name": "r",
            "agent_mappings": {},
        }
        conn.execute(
            "INSERT INTO project_settings (project_id, workflow_config) VALUES (?, ?)",
            ("P1", json.dumps(cfg_data)),
        )
        conn.commit()
        conn.close()

        mock_settings = Mock()
        mock_settings.database_path = str(db)
        with patch("src.config.get_settings", return_value=mock_settings):
            result = await _load_workflow_config_from_db("P1")
        assert result is not None
        assert result.project_id == "P1"

    @pytest.mark.asyncio
    async def test_load_from_db_fallback_to_agent_pipeline_mappings(self, tmp_path):
        import json
        import sqlite3

        from src.services.workflow_orchestrator import _load_workflow_config_from_db

        db = tmp_path / "test.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE project_settings (project_id TEXT, workflow_config TEXT, agent_pipeline_mappings TEXT, github_user_id TEXT, updated_at TEXT)"
        )
        mappings = {"Backlog": [{"slug": "speckit.specify"}]}
        conn.execute(
            "INSERT INTO project_settings (project_id, agent_pipeline_mappings, github_user_id) VALUES (?, ?, ?)",
            ("P1", json.dumps(mappings), "__workflow__"),
        )
        conn.commit()
        conn.close()

        mock_settings = Mock()
        mock_settings.database_path = str(db)
        with patch("src.config.get_settings", return_value=mock_settings):
            result = await _load_workflow_config_from_db("P1")
        assert result is not None
        assert "Backlog" in result.agent_mappings

    @pytest.mark.asyncio
    async def test_load_from_db_no_row_returns_none(self, tmp_path):
        import sqlite3

        from src.services.workflow_orchestrator import _load_workflow_config_from_db

        db = tmp_path / "test.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE project_settings (project_id TEXT, workflow_config TEXT, agent_pipeline_mappings TEXT)"
        )
        conn.commit()
        conn.close()

        mock_settings = Mock()
        mock_settings.database_path = str(db)
        with patch("src.config.get_settings", return_value=mock_settings):
            result = await _load_workflow_config_from_db("P1")
        assert result is None

    @pytest.mark.asyncio
    async def test_persist_insert(self, tmp_path):
        import sqlite3

        from src.services.workflow_orchestrator import _persist_workflow_config_to_db

        db = tmp_path / "test.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE project_settings (github_user_id TEXT, project_id TEXT, agent_pipeline_mappings TEXT, workflow_config TEXT, updated_at TEXT)"
        )
        conn.commit()
        conn.close()

        cfg = _make_config()
        mock_settings = Mock()
        mock_settings.database_path = str(db)
        with patch("src.config.get_settings", return_value=mock_settings):
            await _persist_workflow_config_to_db("P1", cfg)

        conn = sqlite3.connect(str(db))
        row = conn.execute("SELECT * FROM project_settings WHERE project_id = 'P1'").fetchone()
        conn.close()
        assert row is not None

    @pytest.mark.asyncio
    async def test_persist_update(self, tmp_path):
        import sqlite3

        from src.services.workflow_orchestrator import _persist_workflow_config_to_db

        db = tmp_path / "test.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE project_settings (github_user_id TEXT, project_id TEXT, agent_pipeline_mappings TEXT, workflow_config TEXT, updated_at TEXT)"
        )
        conn.execute(
            "INSERT INTO project_settings (github_user_id, project_id) VALUES ('__workflow__', 'P1')"
        )
        conn.commit()
        conn.close()

        cfg = _make_config()
        mock_settings = Mock()
        mock_settings.database_path = str(db)
        with patch("src.config.get_settings", return_value=mock_settings):
            await _persist_workflow_config_to_db("P1", cfg)

        conn = sqlite3.connect(str(db))
        row = conn.execute(
            "SELECT workflow_config FROM project_settings WHERE project_id = 'P1'"
        ).fetchone()
        conn.close()
        assert row[0] is not None

    @pytest.mark.asyncio
    async def test_persist_settings_error_silent(self):
        from src.services.workflow_orchestrator import _persist_workflow_config_to_db

        cfg = _make_config()
        with patch("src.config.get_settings", side_effect=Exception("nope")):
            # Should not raise
            await _persist_workflow_config_to_db("P1", cfg)


class TestIssueSubIssueStore:
    """Tests for the global sub-issue mapping store."""

    def setup_method(self):
        """Clear global sub-issue store before each test."""
        from src.services.workflow_orchestrator import _issue_sub_issue_map

        _issue_sub_issue_map.clear()

    def teardown_method(self):
        from src.services.workflow_orchestrator import _issue_sub_issue_map

        _issue_sub_issue_map.clear()

    def test_get_returns_empty_for_unknown_issue(self):
        """Should return empty dict for unknown issue number."""
        from src.services.workflow_orchestrator import get_issue_sub_issues

        result = get_issue_sub_issues(999)
        assert result == {}

    def test_set_and_get_sub_issues(self):
        """Should store and retrieve sub-issue mappings."""
        from src.services.workflow_orchestrator import (
            get_issue_sub_issues,
            set_issue_sub_issues,
        )

        mappings = {
            "speckit.specify": {"number": 100, "node_id": "I_100", "url": "https://..."},
            "speckit.plan": {"number": 101, "node_id": "I_101", "url": "https://..."},
        }
        set_issue_sub_issues(42, mappings)
        result = get_issue_sub_issues(42)
        assert result == mappings
        assert result["speckit.specify"]["number"] == 100
        assert result["speckit.plan"]["number"] == 101

    def test_set_merges_with_existing(self):
        """Should merge new mappings with existing ones."""
        from src.services.workflow_orchestrator import (
            get_issue_sub_issues,
            set_issue_sub_issues,
        )

        set_issue_sub_issues(42, {"speckit.specify": {"number": 100}})
        set_issue_sub_issues(42, {"speckit.plan": {"number": 101}})

        result = get_issue_sub_issues(42)
        assert "speckit.specify" in result
        assert "speckit.plan" in result
        assert result["speckit.specify"]["number"] == 100
        assert result["speckit.plan"]["number"] == 101

    def test_set_overwrites_existing_agent(self):
        """Should overwrite existing agent mapping."""
        from src.services.workflow_orchestrator import (
            get_issue_sub_issues,
            set_issue_sub_issues,
        )

        set_issue_sub_issues(42, {"speckit.specify": {"number": 100}})
        set_issue_sub_issues(42, {"speckit.specify": {"number": 200}})

        result = get_issue_sub_issues(42)
        assert result["speckit.specify"]["number"] == 200

    def test_survives_pipeline_state_reset(self):
        """Sub-issue mappings should persist after remove_pipeline_state()."""
        from src.services.workflow_orchestrator import (
            _pipeline_states,
            get_issue_sub_issues,
            remove_pipeline_state,
            set_issue_sub_issues,
            set_pipeline_state,
        )

        _pipeline_states.clear()

        mappings = {
            "speckit.specify": {"number": 100, "node_id": "I_100", "url": ""},
            "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
        }
        set_issue_sub_issues(42, mappings)

        # Create and then remove pipeline state
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Backlog",
            agents=["speckit.specify"],
            agent_sub_issues=mappings,
        )
        set_pipeline_state(42, pipeline)
        remove_pipeline_state(42)

        # Global store should still have the mappings
        result = get_issue_sub_issues(42)
        assert len(result) == 2
        assert result["speckit.specify"]["number"] == 100
        assert result["speckit.plan"]["number"] == 101

        _pipeline_states.clear()


class TestAssignAgentUsesGlobalSubIssueStore:
    """Tests that assign_agent_for_status falls back to the global sub-issue store."""

    @pytest.fixture(autouse=True)
    def clear_states(self):
        """Clear global states between tests."""
        from src.services.copilot_polling import (
            _pending_agent_assignments,
            _recovery_last_attempt,
        )
        from src.services.workflow_orchestrator import (
            _issue_sub_issue_map,
            _pipeline_states,
        )

        _pipeline_states.clear()
        _issue_sub_issue_map.clear()
        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()
        yield
        _pipeline_states.clear()
        _issue_sub_issue_map.clear()
        _pending_agent_assignments.clear()
        _recovery_last_attempt.clear()

    @pytest.fixture
    def mock_github_service(self):
        """Create mock GitHub service."""
        service = Mock()
        service.get_issue_with_comments = AsyncMock(
            return_value={"body": "test body", "title": "Test"}
        )
        service.format_issue_context_as_prompt = Mock(return_value="")
        service.assign_copilot_to_issue = AsyncMock(return_value=True)
        service.update_item_status_by_name = AsyncMock(return_value=True)
        service.validate_assignee = AsyncMock()
        service.assign_issue = AsyncMock()
        service.find_existing_pr_for_issue = AsyncMock(return_value=None)
        service.update_issue_state = AsyncMock(return_value=True)
        service.update_sub_issue_project_status = AsyncMock()
        return service

    @pytest.fixture
    def orchestrator(self, mock_github_service):
        """Create WorkflowOrchestrator with mocked services."""
        return WorkflowOrchestrator(Mock(), mock_github_service)

    @pytest.fixture
    def config(self):
        """Create a workflow configuration."""
        return WorkflowConfiguration(
            project_id="PVT_123",
            repository_owner="owner",
            repository_name="repo",
            status_backlog="Backlog",
            status_ready="Ready",
            status_in_progress="In Progress",
            status_in_review="In Review",
            status_done="Done",
            agent_mappings={
                "Ready": ["speckit.plan", "speckit.tasks"],
            },
        )

    async def test_uses_global_store_when_pipeline_has_no_sub_issues(
        self,
        orchestrator,
        mock_github_service,
        config,
    ):
        """When pipeline state has no sub-issue mappings (cleared during transition),
        assign_agent_for_status should fall back to the global sub-issue store."""
        from src.services.workflow_orchestrator import (
            set_issue_sub_issues,
            set_pipeline_state,
            set_workflow_config,
        )

        await set_workflow_config("PVT_123", config)

        # Simulate: global store has sub-issue mappings from create_all_sub_issues
        set_issue_sub_issues(
            42,
            {
                "speckit.plan": {"number": 101, "node_id": "I_101", "url": ""},
                "speckit.tasks": {"number": 102, "node_id": "I_102", "url": ""},
            },
        )

        # Simulate: pipeline state was reset during transition (no agent_sub_issues)
        pipeline = PipelineState(
            issue_number=42,
            project_id="PVT_123",
            status="Ready",
            agents=["speckit.plan", "speckit.tasks"],
            agent_sub_issues={},  # Lost during remove_pipeline_state
        )
        set_pipeline_state(42, pipeline)

        ctx = WorkflowContext(
            session_id="test",
            project_id="PVT_123",
            access_token="token",
            repository_owner="owner",
            repository_name="repo",
            issue_id="I_parent",
            issue_number=42,
            project_item_id="PVTI_123",
            current_state=WorkflowState.READY,
        )
        ctx.config = config

        await orchestrator.assign_agent_for_status(ctx, "Ready", agent_index=0)

        # The agent should have been assigned to the sub-issue, not the parent
        call_args = mock_github_service.assign_copilot_to_issue.call_args
        assert call_args is not None
        # The issue_node_id should be from the sub-issue (I_101), not parent (I_parent)
        assert (
            call_args.kwargs.get("issue_node_id") == "I_101"
            or call_args[1].get("issue_node_id") == "I_101"
        )
