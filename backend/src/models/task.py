"""Task model for GitHub Project items."""

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Task(BaseModel):
    """Represents a work item in a GitHub Project."""

    task_id: UUID = Field(default_factory=uuid4, description="Internal task identifier")
    project_id: str = Field(..., description="Parent project ID (FK)")
    github_item_id: str = Field(..., description="GitHub Project item node ID")
    github_content_id: str | None = Field(None, description="Linked issue/PR node ID (if not draft)")
    github_issue_id: str | None = Field(None, description="GitHub Issue node ID")
    issue_number: int | None = Field(None, description="GitHub Issue number")
    repository_owner: str | None = Field(None, description="Repository owner")
    repository_name: str | None = Field(None, description="Repository name")
    title: str = Field(..., max_length=256, description="Task title")
    description: str | None = Field(None, max_length=65535, description="Task body/description")
    status: str = Field(..., description="Current status column name")
    status_option_id: str = Field(..., description="Status field option ID")
    assignees: list[str] | None = Field(None, description="List of assigned user logins")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last modification time")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "project_id": "PVT_kwDOABCD1234",
                "github_item_id": "PVTI_lADOABCD",
                "github_content_id": None,
                "title": "Add OAuth2 authentication flow",
                "description": "## Overview\\nImplement GitHub OAuth2...",
                "status": "Todo",
                "status_option_id": "f75ad846",
                "assignees": ["octocat"],
                "created_at": "2026-01-30T10:00:00Z",
                "updated_at": "2026-01-30T11:00:00Z",
            }
        }


class TaskCreateRequest(BaseModel):
    """Request to create a new task."""

    project_id: str = Field(..., description="Target project ID")
    title: str = Field(..., max_length=256, description="Task title")
    description: str | None = Field(None, max_length=65535, description="Task description")


class TaskListResponse(BaseModel):
    """Response for listing tasks."""

    tasks: list[Task]
