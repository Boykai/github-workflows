"""User session model for OAuth tokens and preferences."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class UserSession(BaseModel):
    """Represents an authenticated user's session with GitHub OAuth tokens."""

    session_id: UUID = Field(default_factory=uuid4, description="Unique session identifier")
    github_user_id: str = Field(..., description="GitHub user ID from OAuth")
    github_username: str = Field(..., description="GitHub username for display")
    github_avatar_url: str | None = Field(None, description="User's avatar URL")
    access_token: str = Field(..., description="Encrypted GitHub OAuth access token")
    refresh_token: str | None = Field(None, description="Encrypted OAuth refresh token")
    token_expires_at: datetime | None = Field(None, description="Token expiration timestamp")
    selected_project_id: str | None = Field(
        None, description="Currently selected GitHub Project ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Session creation time",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last activity time",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "github_user_id": "12345678",
                "github_username": "octocat",
                "github_avatar_url": "https://avatars.githubusercontent.com/u/12345678",
                "access_token": "gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "refresh_token": "ghr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                "token_expires_at": "2026-01-31T12:00:00Z",
                "selected_project_id": "PVT_kwDOABCD1234",
                "created_at": "2026-01-30T10:00:00Z",
                "updated_at": "2026-01-30T11:00:00Z",
            }
        }
    }


class UserResponse(BaseModel):
    """User response for API endpoints (excludes sensitive tokens)."""

    github_user_id: str
    github_username: str
    github_avatar_url: str | None = None
    selected_project_id: str | None = None

    @classmethod
    def from_session(cls, session: UserSession) -> "UserResponse":
        """Create UserResponse from UserSession."""
        return cls(
            github_user_id=session.github_user_id,
            github_username=session.github_username,
            github_avatar_url=session.github_avatar_url,
            selected_project_id=session.selected_project_id,
        )
