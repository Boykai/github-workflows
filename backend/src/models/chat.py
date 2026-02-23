"""Chat message models.

Agent, workflow, and recommendation models have been extracted to their own
modules.  This file re-exports all previously-public names so existing
``from src.models.chat import …`` statements continue to work.
"""

import re
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from src.constants import DEFAULT_AGENT_MAPPINGS  # noqa: F401  — backward compat

# ---- Re-exports for backward compatibility --------------------------------
from src.models.agent import (  # noqa: F401
    AgentAssignment,
    AgentAssignmentInput,
    AgentSource,
    AvailableAgent,
    AvailableAgentsResponse,
)
from src.models.recommendation import (  # noqa: F401
    AVAILABLE_LABELS,
    AITaskProposal,
    IssueLabel,
    IssueMetadata,
    IssuePriority,
    IssueRecommendation,
    IssueSize,
    ProposalConfirmRequest,
    ProposalStatus,
    RecommendationStatus,
)
from src.models.workflow import (  # noqa: F401
    TriggeredBy,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)
from src.utils import utcnow

# ============================================================================
# Chat-specific models
# ============================================================================


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


class ChatMessage(BaseModel):
    """Represents a single message in the chat conversation."""

    message_id: UUID = Field(default_factory=uuid4, description="Unique message identifier")
    session_id: UUID = Field(..., description="Parent session ID (FK)")
    sender_type: SenderType = Field(..., description="Message sender type")
    content: str = Field(..., max_length=100000, description="Message text content")
    action_type: ActionType | None = Field(default=None, description="Associated action type")
    action_data: dict[str, Any] | None = Field(default=None, description="Action-specific payload")
    timestamp: datetime = Field(default_factory=utcnow, description="Message timestamp")

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
