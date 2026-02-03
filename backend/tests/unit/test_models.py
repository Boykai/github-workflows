"""Unit tests for user models."""

import pytest
from datetime import datetime
from uuid import UUID

from src.models.user import UserSession, UserResponse


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
        assert not hasattr(response, 'access_token')
        assert not hasattr(response, 'refresh_token')
        assert not hasattr(response, 'session_id')


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
        import pytest

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
        from src.models.chat import (
            IssueRecommendation,
            IssueMetadata,
            IssuePriority,
            IssueSize,
            RecommendationStatus,
        )
        from uuid import uuid4

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
        from src.models.chat import IssueRecommendation, IssuePriority, IssueSize
        from uuid import uuid4

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
