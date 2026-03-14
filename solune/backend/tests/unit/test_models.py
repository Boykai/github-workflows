"""Unit tests for user models."""

from datetime import datetime
from uuid import UUID

import pytest

from src.models.user import UserResponse, UserSession


class TestUserSession:
    """Tests for UserSession model."""

    def test_create_session_with_required_fields(self):
        """Should create a session with required fields only."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token_12345",
        )

        assert session.github_user_id == "12345678"
        assert session.github_username == "testuser"
        assert session.access_token == "gho_test_token_12345"
        assert isinstance(session.session_id, UUID)
        assert session.github_avatar_url is None
        assert session.refresh_token is None
        assert session.token_expires_at is None
        assert session.selected_project_id is None

    def test_create_session_with_all_fields(self):
        """Should create a session with all fields."""
        expires_at = datetime(2026, 12, 31, 23, 59, 59)

        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            github_avatar_url="https://avatars.githubusercontent.com/u/12345678",
            access_token="gho_test_token_12345",
            refresh_token="ghr_refresh_token_12345",
            token_expires_at=expires_at,
            selected_project_id="PVT_kwDOABCD1234",
        )

        assert session.github_avatar_url == "https://avatars.githubusercontent.com/u/12345678"
        assert session.refresh_token == "ghr_refresh_token_12345"
        assert session.token_expires_at == expires_at
        assert session.selected_project_id == "PVT_kwDOABCD1234"

    def test_session_has_timestamps(self):
        """Should auto-generate created_at and updated_at timestamps."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token",
        )

        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_generates_unique_ids(self):
        """Should generate unique session IDs."""
        session1 = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token",
        )
        session2 = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_test_token",
        )

        assert session1.session_id != session2.session_id


class TestUserResponse:
    """Tests for UserResponse model."""

    def test_create_response(self):
        """Should create a response with required fields."""
        response = UserResponse(
            github_user_id="12345678",
            github_username="testuser",
        )

        assert response.github_user_id == "12345678"
        assert response.github_username == "testuser"
        assert response.github_avatar_url is None
        assert response.selected_project_id is None

    def test_from_session(self):
        """Should create UserResponse from UserSession."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            github_avatar_url="https://avatars.githubusercontent.com/u/12345678",
            access_token="gho_test_token",
            selected_project_id="PVT_kwDOABCD1234",
        )

        response = UserResponse.from_session(session)

        assert response.github_user_id == session.github_user_id
        assert response.github_username == session.github_username
        assert response.github_avatar_url == session.github_avatar_url
        assert response.selected_project_id == session.selected_project_id

    def test_from_session_excludes_sensitive_data(self):
        """Should not include access_token or refresh_token in response."""
        session = UserSession(
            github_user_id="12345678",
            github_username="testuser",
            access_token="gho_sensitive_token",
            refresh_token="ghr_sensitive_refresh",
        )

        response = UserResponse.from_session(session)

        # Verify sensitive fields are not in the response
        assert not hasattr(response, "access_token")
        assert not hasattr(response, "refresh_token")
        assert not hasattr(response, "session_id")


class TestIssueMetadata:
    """Tests for IssueMetadata model."""

    def test_create_metadata_with_defaults(self):
        """Should create metadata with default values."""
        from src.models.chat import IssueMetadata, IssuePriority, IssueSize

        metadata = IssueMetadata()

        assert metadata.priority == IssuePriority.P2
        assert metadata.size == IssueSize.M
        assert metadata.estimate_hours == 4.0
        assert metadata.start_date == ""
        assert metadata.target_date == ""
        assert "ai-generated" in metadata.labels

    def test_create_metadata_with_custom_values(self):
        """Should create metadata with custom values."""
        from src.models.chat import IssueMetadata, IssuePriority, IssueSize

        metadata = IssueMetadata(
            priority=IssuePriority.P0,
            size=IssueSize.XL,
            estimate_hours=20.0,
            start_date="2026-02-03",
            target_date="2026-02-07",
            labels=["ai-generated", "critical", "feature"],
        )

        assert metadata.priority == IssuePriority.P0
        assert metadata.size == IssueSize.XL
        assert metadata.estimate_hours == 20.0
        assert metadata.start_date == "2026-02-03"
        assert metadata.target_date == "2026-02-07"
        assert len(metadata.labels) == 3

    def test_estimate_hours_bounds(self):
        """Should enforce bounds on estimate_hours."""
        from src.models.chat import IssueMetadata

        # Valid values should work
        metadata = IssueMetadata(estimate_hours=0.5)
        assert metadata.estimate_hours == 0.5

        metadata = IssueMetadata(estimate_hours=40.0)
        assert metadata.estimate_hours == 40.0

        # Out of bounds should fail validation
        with pytest.raises(ValueError):
            IssueMetadata(estimate_hours=0.1)  # Below min

        with pytest.raises(ValueError):
            IssueMetadata(estimate_hours=50.0)  # Above max


class TestIssueRecommendation:
    """Tests for IssueRecommendation model with metadata."""

    def test_create_recommendation_with_metadata(self):
        """Should create recommendation with metadata."""
        from uuid import uuid4

        from src.models.chat import (
            IssueMetadata,
            IssuePriority,
            IssueRecommendation,
            IssueSize,
            RecommendationStatus,
        )

        metadata = IssueMetadata(
            priority=IssuePriority.P1,
            size=IssueSize.S,
            estimate_hours=2.0,
            start_date="2026-02-03",
            target_date="2026-02-03",
            labels=["ai-generated", "quick-fix"],
        )

        recommendation = IssueRecommendation(
            session_id=uuid4(),
            original_input="Fix the login button color",
            title="Fix login button color contrast",
            user_story="As a user, I want the login button to be visible",
            ui_ux_description="Update button to use primary color",
            functional_requirements=["Button MUST use primary theme color"],
            metadata=metadata,
        )

        assert recommendation.title == "Fix login button color contrast"
        assert recommendation.metadata.priority == IssuePriority.P1
        assert recommendation.metadata.size == IssueSize.S
        assert recommendation.metadata.estimate_hours == 2.0
        assert recommendation.status == RecommendationStatus.PENDING

    def test_recommendation_with_default_metadata(self):
        """Should use default metadata when not provided."""
        from uuid import uuid4

        from src.models.chat import IssuePriority, IssueRecommendation, IssueSize

        recommendation = IssueRecommendation(
            session_id=uuid4(),
            original_input="Add feature",
            title="Add new feature",
            user_story="As a user, I want a new feature",
            ui_ux_description="Add button",
            functional_requirements=["Feature MUST work"],
        )

        # Should have default metadata
        assert recommendation.metadata is not None
        assert recommendation.metadata.priority == IssuePriority.P2
        assert recommendation.metadata.size == IssueSize.M


# =============================================================================
# Group-Aware Pipeline Models
# =============================================================================


class TestExecutionGroupMapping:
    """Tests for ExecutionGroupMapping model."""

    def test_create_sequential_group(self):
        from src.models.agent import AgentAssignment
        from src.models.workflow import ExecutionGroupMapping

        agents = [AgentAssignment(slug="agent1"), AgentAssignment(slug="agent2")]
        egm = ExecutionGroupMapping(
            group_id="g1", order=0, execution_mode="sequential", agents=agents
        )
        assert egm.group_id == "g1"
        assert egm.order == 0
        assert egm.execution_mode == "sequential"
        assert len(egm.agents) == 2

    def test_create_parallel_group(self):
        from src.models.workflow import ExecutionGroupMapping

        egm = ExecutionGroupMapping(group_id="g2", order=1, execution_mode="parallel")
        assert egm.execution_mode == "parallel"
        assert egm.agents == []

    def test_invalid_execution_mode_raises(self):
        from src.models.workflow import ExecutionGroupMapping

        with pytest.raises(ValueError, match="execution_mode"):
            ExecutionGroupMapping(group_id="g1", order=0, execution_mode="invalid")

    def test_default_values(self):
        from src.models.workflow import ExecutionGroupMapping

        egm = ExecutionGroupMapping(group_id="g1")
        assert egm.order == 0
        assert egm.execution_mode == "sequential"
        assert egm.agents == []


class TestWorkflowConfigurationGroupMappings:
    """Tests for WorkflowConfiguration.group_mappings field."""

    def test_default_group_mappings_is_empty(self):
        from src.models.workflow import WorkflowConfiguration

        config = WorkflowConfiguration(
            project_id="p1", repository_owner="owner", repository_name="repo"
        )
        assert config.group_mappings == {}

    def test_serialization_roundtrip(self):
        from src.models.agent import AgentAssignment
        from src.models.workflow import ExecutionGroupMapping, WorkflowConfiguration

        egm = ExecutionGroupMapping(
            group_id="g1",
            order=0,
            execution_mode="parallel",
            agents=[AgentAssignment(slug="agent1")],
        )
        config = WorkflowConfiguration(
            project_id="p1",
            repository_owner="o",
            repository_name="r",
            group_mappings={"Ready": [egm]},
        )
        data = config.model_dump()
        restored = WorkflowConfiguration(**data)
        assert len(restored.group_mappings["Ready"]) == 1
        assert restored.group_mappings["Ready"][0].group_id == "g1"
        assert restored.group_mappings["Ready"][0].execution_mode == "parallel"


class TestPipelineStateGroupProperties:
    """Tests for PipelineState group-aware properties."""

    def test_current_agent_with_groups(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(group_id="g1", execution_mode="sequential", agents=["a1", "a2"]),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1", "a2"],
            groups=groups,
        )
        assert ps.current_agent == "a1"

    def test_current_agent_flat_fallback(self):
        from src.services.workflow_orchestrator.models import PipelineState

        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1", "a2"],
        )
        assert ps.current_agent == "a1"

    def test_is_complete_with_groups_all_done(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(group_id="g1", execution_mode="sequential", agents=["a1"]),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1"],
            groups=groups,
            current_group_index=1,
        )
        assert ps.is_complete is True

    def test_is_complete_with_groups_not_done(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(group_id="g1", execution_mode="sequential", agents=["a1", "a2"]),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1", "a2"],
            groups=groups,
        )
        assert ps.is_complete is False

    def test_is_complete_parallel_group_all_terminal(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(
                group_id="g1",
                execution_mode="parallel",
                agents=["a1", "a2"],
                agent_statuses={"a1": "completed", "a2": "failed"},
            ),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1", "a2"],
            groups=groups,
        )
        # All agents terminal but group index hasn't advanced yet
        assert ps.is_complete is True  # All agents in group are terminal

    def test_is_complete_parallel_group_partial(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(
                group_id="g1",
                execution_mode="parallel",
                agents=["a1", "a2"],
                agent_statuses={"a1": "completed", "a2": "active"},
            ),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1", "a2"],
            groups=groups,
        )
        assert ps.is_complete is False

    def test_current_agent_with_groups_second_group(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(group_id="g1", execution_mode="sequential", agents=["a1"]),
            PipelineGroupInfo(group_id="g2", execution_mode="parallel", agents=["a2", "a3"]),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1", "a2", "a3"],
            groups=groups,
            current_group_index=1,
            current_agent_index_in_group=0,
        )
        assert ps.current_agent == "a2"

    def test_current_agent_returns_none_when_all_groups_done(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState

        groups = [
            PipelineGroupInfo(group_id="g1", execution_mode="sequential", agents=["a1"]),
        ]
        ps = PipelineState(
            issue_number=1,
            project_id="p1",
            status="Ready",
            agents=["a1"],
            groups=groups,
            current_group_index=1,
        )
        assert ps.current_agent is None


class TestPipelineGroupInfo:
    """Tests for PipelineGroupInfo dataclass."""

    def test_default_values(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo

        gi = PipelineGroupInfo(group_id="g1")
        assert gi.execution_mode == "sequential"
        assert gi.agents == []
        assert gi.agent_statuses == {}

    def test_parallel_with_statuses(self):
        from src.services.workflow_orchestrator.models import PipelineGroupInfo

        gi = PipelineGroupInfo(
            group_id="g1",
            execution_mode="parallel",
            agents=["a1", "a2"],
            agent_statuses={"a1": "active", "a2": "pending"},
        )
        assert gi.execution_mode == "parallel"
        assert len(gi.agent_statuses) == 2
