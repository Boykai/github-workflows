"""Chat message and AI task proposal models."""

import re
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, BeforeValidator, Field, field_validator

from src.constants import AGENT_DISPLAY_NAMES, DEFAULT_AGENT_MAPPINGS


# ============================================================================
# Agent Assignment Models (004-agent-workflow-config-ui)
# ============================================================================


class AgentSource(StrEnum):
    """Source of an available agent."""

    BUILTIN = "builtin"
    REPOSITORY = "repository"


class AgentAssignment(BaseModel):
    """A single agent assignment within a workflow status column."""

    id: UUID = Field(default_factory=uuid4, description="Unique instance ID")
    slug: str = Field(..., description="Agent identifier slug")
    display_name: str | None = Field(default=None, description="Human-readable display name")
    config: dict | None = Field(default=None, description="Reserved for future per-assignment config")


def _coerce_agent(v: str | dict | AgentAssignment) -> AgentAssignment | dict:
    """Accept a bare slug string and promote to AgentAssignment."""
    if isinstance(v, str):
        return AgentAssignment(slug=v)
    return v


AgentAssignmentInput = Annotated[AgentAssignment, BeforeValidator(_coerce_agent)]


class AvailableAgent(BaseModel):
    """An agent available for assignment, from discovery."""

    slug: str = Field(..., description="Unique agent identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str | None = Field(default=None, description="Agent description")
    avatar_url: str | None = Field(default=None, description="Avatar URL")
    source: AgentSource = Field(..., description="Discovery source")


class AvailableAgentsResponse(BaseModel):
    """Response for listing available agents."""

    agents: list[AvailableAgent]


class SenderType(StrEnum):
    """Sender type for chat messages."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ActionType(StrEnum):
    """Action type for chat messages with associated actions."""

    TASK_CREATE = "task_create"
    STATUS_UPDATE = "status_update"
    PROJECT_SELECT = "project_select"
    ISSUE_CREATE = "issue_create"


class ProposalStatus(StrEnum):
    """Status of an AI task proposal."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    CANCELLED = "cancelled"


class RecommendationStatus(StrEnum):
    """Status of an AI issue recommendation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class ChatMessage(BaseModel):
    """Represents a single message in the chat conversation."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    session_id: UUID = Field(..., description="Parent session ID (FK)")
    sender_type: SenderType = Field(..., description="Message sender type")
    content: str = Field(..., max_length=100000, description="Message text content")
    action_type: ActionType | None = Field(default=None, description="Associated action type")
    action_data: dict[str, Any] | None = Field(default=None, description="Action-specific payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

    model_config = {
        "json_schema_extra": {
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
    status: ProposalStatus = Field(default=ProposalStatus.PENDING, description="Proposal status")
    edited_title: str | None = Field(default=None, description="User-modified title")
    edited_description: str | None = Field(default=None, description="User-modified description")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Proposal creation time"
    )
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

    model_config = {
        "json_schema_extra": {
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
    }


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""

    content: str = Field(..., max_length=100000, description="Message content")

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Sanitize message content to prevent injection attacks."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")

        # Strip leading/trailing whitespace
        v = v.strip()

        # Remove any null bytes
        v = v.replace("\x00", "")

        # Limit consecutive newlines to prevent formatting abuse
        v = re.sub(r"\n{4,}", "\n\n\n", v)

        return v


class ChatMessagesResponse(BaseModel):
    """Response for listing chat messages."""

    messages: list[ChatMessage]


class ProposalConfirmRequest(BaseModel):
    """Request to confirm an AI task proposal."""

    edited_title: str | None = Field(default=None, max_length=256, description="Edited title")
    edited_description: str | None = Field(
        default=None, max_length=65535, description="Edited description"
    )


# ============================================================================
# Issue Recommendation Models (T004-T006, T028)
# ============================================================================


class TriggeredBy(StrEnum):
    """Source that triggered a workflow transition."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    DETECTION = "detection"


class IssuePriority(StrEnum):
    """Priority levels for issues."""

    P0 = "P0"  # Critical - immediate attention
    P1 = "P1"  # High - complete ASAP
    P2 = "P2"  # Medium - standard priority
    P3 = "P3"  # Low - nice to have


class IssueSize(StrEnum):
    """Size estimates for issues (T-shirt sizing)."""

    XS = "XS"  # < 1 hour
    S = "S"  # 1-4 hours
    M = "M"  # 4-8 hours (1 day)
    L = "L"  # 1-3 days
    XL = "XL"  # 3-5 days


class IssueLabel(StrEnum):
    """Pre-defined labels for GitHub Issues."""

    # Type labels
    FEATURE = "feature"  # New functionality
    BUG = "bug"  # Bug fix
    ENHANCEMENT = "enhancement"  # Improvement to existing feature
    REFACTOR = "refactor"  # Code refactoring
    DOCUMENTATION = "documentation"  # Documentation updates
    TESTING = "testing"  # Test-related work
    INFRASTRUCTURE = "infrastructure"  # DevOps, CI/CD, config

    # Scope labels
    FRONTEND = "frontend"  # Frontend/UI work
    BACKEND = "backend"  # Backend/API work
    DATABASE = "database"  # Database changes
    API = "api"  # API changes

    # Status labels
    AI_GENERATED = "ai-generated"  # Created by AI
    GOOD_FIRST_ISSUE = "good first issue"  # Simple issue
    HELP_WANTED = "help wanted"  # Needs assistance

    # Domain labels
    SECURITY = "security"  # Security-related
    PERFORMANCE = "performance"  # Performance optimization
    ACCESSIBILITY = "accessibility"  # A11y improvements
    UX = "ux"  # User experience


# List of all available labels for AI reference
AVAILABLE_LABELS = [label.value for label in IssueLabel]


class IssueMetadata(BaseModel):
    """AI-generated metadata for GitHub Issues."""

    priority: IssuePriority = Field(
        default=IssuePriority.P2,
        description="Issue priority (P0=Critical, P1=High, P2=Medium, P3=Low)",
    )
    size: IssueSize = Field(
        default=IssueSize.M,
        description="Estimated size (XS=<1hr, S=1-4hrs, M=1day, L=1-3days, XL=3-5days)",
    )
    estimate_hours: float = Field(
        default=4.0, ge=0.5, le=40.0, description="Estimated hours to complete (0.5-40)"
    )
    start_date: str = Field(default="", description="Suggested start date (ISO format YYYY-MM-DD)")
    target_date: str = Field(
        default="", description="Target completion date (ISO format YYYY-MM-DD)"
    )
    labels: list[str] = Field(
        default_factory=lambda: ["ai-generated"],
        description="Suggested labels for the issue",
    )


class IssueRecommendation(BaseModel):
    """AI-generated issue recommendation awaiting user confirmation."""

    recommendation_id: UUID = Field(default_factory=uuid4, description="Unique recommendation ID")
    session_id: UUID = Field(..., description="Parent session ID")
    original_input: str = Field(..., description="User's original feature request text")
    original_context: str = Field(
        default="", description="User's complete input preserved verbatim by the AI"
    )
    title: str = Field(..., max_length=256, description="AI-generated issue title")
    user_story: str = Field(..., description="User story in As a/I want/So that format")
    ui_ux_description: str = Field(..., description="UI/UX guidance for implementation")
    functional_requirements: list[str] = Field(..., description="List of testable requirements")
    technical_notes: str = Field(
        default="", description="Implementation hints and architecture considerations"
    )
    metadata: IssueMetadata = Field(
        default_factory=IssueMetadata,
        description="AI-generated issue metadata (priority, size, dates, labels)",
    )
    status: RecommendationStatus = Field(
        default=RecommendationStatus.PENDING, description="Recommendation status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    confirmed_at: datetime | None = Field(default=None, description="Confirmation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "recommendation_id": "550e8400-e29b-41d4-a716-446655440000",
                "session_id": "550e8400-e29b-41d4-a716-446655440001",
                "original_input": "Add CSV export functionality for user data",
                "original_context": "I need to be able to export my user data as CSV. It should include all profile fields and timestamps. Files could be up to 10MB.",
                "title": "Add CSV export functionality for user data",
                "user_story": "As a user, I want to export my data as CSV so that I can analyze it.",
                "ui_ux_description": "Add an Export button in the user profile section.",
                "functional_requirements": [
                    "System MUST generate CSV with all user profile fields",
                    "System MUST include timestamps in ISO 8601 format",
                ],
                "technical_notes": "Use streaming CSV response for large datasets. Rate-limit exports to 5 per minute per user.",
                "metadata": {
                    "priority": "P2",
                    "size": "M",
                    "estimate_hours": 4.0,
                    "start_date": "2026-02-03",
                    "target_date": "2026-02-04",
                    "labels": ["ai-generated", "feature", "export"],
                },
                "status": "pending",
                "created_at": "2026-02-02T10:00:00Z",
                "confirmed_at": None,
            }
        }
    }


class WorkflowConfiguration(BaseModel):
    """Configuration for the workflow orchestrator."""

    project_id: str = Field(..., description="GitHub Project node ID")
    repository_owner: str = Field(..., description="Target repository owner")
    repository_name: str = Field(..., description="Target repository name")
    copilot_assignee: str = Field(
        default="", description="Username for implementation (empty to skip assignment)"
    )
    review_assignee: str | None = Field(
        default=None, description="Username for review (default: repo owner)"
    )
    agent_mappings: dict[str, list[AgentAssignmentInput]] = Field(
        default_factory=lambda: {
            k: [
                AgentAssignment(
                    slug=s,
                    display_name=AGENT_DISPLAY_NAMES.get(s),
                )
                for s in v
            ]
            for k, v in DEFAULT_AGENT_MAPPINGS.items()
        },
        description="Status name → ordered list of agent assignments",
    )
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
    from_status: str | None = Field(default=None, description="Previous status (null for initial)")
    to_status: str = Field(..., description="New status")
    assigned_user: str | None = Field(default=None, description="User assigned (if applicable)")
    triggered_by: TriggeredBy = Field(..., description="Transition trigger source")
    success: bool = Field(..., description="Whether transition succeeded")
    error_message: str | None = Field(default=None, description="Error details if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transition timestamp")


class WorkflowResult(BaseModel):
    """Result of a workflow operation (confirm/reject)."""

    success: bool = Field(..., description="Whether operation succeeded")
    issue_id: str | None = Field(default=None, description="GitHub Issue node ID")
    issue_number: int | None = Field(default=None, description="Human-readable issue number")
    issue_url: str | None = Field(default=None, description="URL to issue on GitHub")
    project_item_id: str | None = Field(default=None, description="GitHub Project item ID")
    current_status: str | None = Field(default=None, description="Current workflow status")
    message: str = Field(..., description="Human-readable result message")
