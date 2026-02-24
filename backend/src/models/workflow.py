"""Workflow configuration, transition audit, and result models."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.constants import AGENT_DISPLAY_NAMES, DEFAULT_AGENT_MAPPINGS
from src.models.agent import AgentAssignment, AgentAssignmentInput
from src.utils import utcnow


class TriggeredBy(StrEnum):
    """Source that triggered a workflow transition."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    DETECTION = "detection"


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
    timestamp: datetime = Field(default_factory=utcnow, description="Transition timestamp")


class WorkflowResult(BaseModel):
    """Result of a workflow operation (confirm/reject)."""

    success: bool = Field(..., description="Whether operation succeeded")
    issue_id: str | None = Field(default=None, description="GitHub Issue node ID")
    issue_number: int | None = Field(default=None, description="Human-readable issue number")
    issue_url: str | None = Field(default=None, description="URL to issue on GitHub")
    project_item_id: str | None = Field(default=None, description="GitHub Project item ID")
    current_status: str | None = Field(default=None, description="Current workflow status")
    message: str = Field(..., description="Human-readable result message")


__all__ = [
    "TriggeredBy",
    "WorkflowConfiguration",
    "WorkflowTransition",
    "WorkflowResult",
]
