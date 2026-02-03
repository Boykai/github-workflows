"""Chat message and AI task proposal models."""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SenderType(str, Enum):
    """Sender type for chat messages."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ActionType(str, Enum):
    """Action type for chat messages with associated actions."""

    TASK_CREATE = "task_create"
    STATUS_UPDATE = "status_update"
    PROJECT_SELECT = "project_select"
    ISSUE_CREATE = "issue_create"


class ProposalStatus(str, Enum):
    """Status of an AI task proposal."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    CANCELLED = "cancelled"


class RecommendationStatus(str, Enum):
    """Status of an AI issue recommendation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ChatMessage(BaseModel):
    """Represents a single message in the chat conversation."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    session_id: UUID = Field(..., description="Parent session ID (FK)")
    sender_type: SenderType = Field(..., description="Message sender type")
    content: str = Field(..., max_length=10000, description="Message text content")
    action_type: ActionType | None = Field(None, description="Associated action type")
    action_data: dict[str, Any] | None = Field(None, description="Action-specific payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "message_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "sender_type": "user",
                "content": "Create a task to fix the login bug",
                "action_type": None,
                "action_data": None,
                "timestamp": "2026-01-30T10:00:00Z",
            }
        }


class AITaskProposal(BaseModel):
    """Temporary entity for AI-generated tasks awaiting user confirmation."""

    proposal_id: UUID = Field(default_factory=uuid4, description="Unique proposal identifier")
    session_id: UUID = Field(..., description="Parent session ID (FK)")
    original_input: str = Field(..., description="User's original natural language input")
    proposed_title: str = Field(..., max_length=256, description="AI-generated task title")
    proposed_description: str = Field(
        ..., max_length=65535, description="AI-generated task description"
    )
    status: ProposalStatus = Field(
        default=ProposalStatus.PENDING, description="Proposal status"
    )
    edited_title: str | None = Field(None, description="User-modified title")
    edited_description: str | None = Field(None, description="User-modified description")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Proposal creation time")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=10),
        description="Auto-expiration time",
    )

    @property
    def is_expired(self) -> bool:
        """Check if proposal has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def final_title(self) -> str:
        """Get final title (edited or proposed)."""
        return self.edited_title or self.proposed_title

    @property
    def final_description(self) -> str:
        """Get final description (edited or proposed)."""
        return self.edited_description or self.proposed_description

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "proposal_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "original_input": "Add authentication so users can log in with their GitHub accounts",
                "proposed_title": "Add OAuth2 authentication flow",
                "proposed_description": "## Overview\\nImplement GitHub OAuth2...",
                "status": "pending",
                "edited_title": None,
                "edited_description": None,
                "created_at": "2026-01-30T10:00:00Z",
                "expires_at": "2026-01-30T10:10:00Z",
            }
        }


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""

    content: str = Field(..., max_length=10000, description="Message content")

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Sanitize message content to prevent injection attacks."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        
        # Strip leading/trailing whitespace
        v = v.strip()
        
        # Remove any null bytes
        v = v.replace('\x00', '')
        
        # Limit consecutive newlines to prevent formatting abuse
        v = re.sub(r'\n{4,}', '\n\n\n', v)
        
        return v


class ChatMessagesResponse(BaseModel):
    """Response for listing chat messages."""

    messages: list[ChatMessage]


class ProposalConfirmRequest(BaseModel):
    """Request to confirm an AI task proposal."""

    edited_title: str | None = Field(None, max_length=256, description="Edited title")
    edited_description: str | None = Field(None, max_length=65535, description="Edited description")


# ============================================================================
# Issue Recommendation Models (T004-T006, T028)
# ============================================================================


class TriggeredBy(str, Enum):
    """Source that triggered a workflow transition."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    DETECTION = "detection"


class IssueRecommendation(BaseModel):
    """AI-generated issue recommendation awaiting user confirmation."""

    recommendation_id: UUID = Field(default_factory=uuid4, description="Unique recommendation ID")
    session_id: UUID = Field(..., description="Parent session ID")
    original_input: str = Field(..., description="User's original feature request text")
    title: str = Field(..., max_length=256, description="AI-generated issue title")
    user_story: str = Field(..., description="User story in As a/I want/So that format")
    ui_ux_description: str = Field(..., description="UI/UX guidance for implementation")
    functional_requirements: list[str] = Field(..., description="List of testable requirements")
    status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING, description="Recommendation status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    confirmed_at: datetime | None = Field(None, description="Confirmation timestamp")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "recommendation_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "original_input": "Add CSV export functionality for user data",
                "title": "Add CSV export functionality for user data",
                "user_story": "As a user, I want to export my data as CSV so that I can analyze it.",
                "ui_ux_description": "Add an Export button in the user profile section.",
                "functional_requirements": [
                    "System MUST generate CSV with all user profile fields",
                    "System MUST include timestamps in ISO 8601 format",
                ],
                "status": "pending",
                "created_at": "2026-02-02T10:00:00Z",
                "confirmed_at": None,
            }
        }


class WorkflowConfiguration(BaseModel):
    """Configuration for the workflow orchestrator."""

    project_id: str = Field(..., description="GitHub Project node ID")
    repository_owner: str = Field(..., description="Target repository owner")
    repository_name: str = Field(..., description="Target repository name")
    copilot_assignee: str = Field(default="", description="Username for implementation (empty to skip assignment)")
    review_assignee: str | None = Field(None, description="Username for review (default: repo owner)")
    status_backlog: str = Field(default="Backlog", description="Backlog status column name")
    status_ready: str = Field(default="Ready", description="Ready status column name")
    status_in_progress: str = Field(default="In Progress", description="In Progress column name")
    status_in_review: str = Field(default="In Review", description="In Review column name")
    enabled: bool = Field(default=True, description="Whether workflow automation is active")


class WorkflowTransition(BaseModel):
    """Audit log for workflow status transitions."""

    transition_id: UUID = Field(default_factory=uuid4, description="Unique transition ID")
    issue_id: str = Field(..., description="GitHub Issue node ID")
    project_id: str = Field(..., description="GitHub Project node ID")
    from_status: str | None = Field(None, description="Previous status (null for initial)")
    to_status: str = Field(..., description="New status")
    assigned_user: str | None = Field(None, description="User assigned (if applicable)")
    triggered_by: TriggeredBy = Field(..., description="Transition trigger source")
    success: bool = Field(..., description="Whether transition succeeded")
    error_message: str | None = Field(None, description="Error details if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transition timestamp")


class WorkflowResult(BaseModel):
    """Result of a workflow operation (confirm/reject)."""

    success: bool = Field(..., description="Whether operation succeeded")
    issue_id: str | None = Field(None, description="GitHub Issue node ID")
    issue_number: int | None = Field(None, description="Human-readable issue number")
    issue_url: str | None = Field(None, description="URL to issue on GitHub")
    project_item_id: str | None = Field(None, description="GitHub Project item ID")
    current_status: str | None = Field(None, description="Current workflow status")
    message: str = Field(..., description="Human-readable result message")
