"""Pydantic models for Chores — recurring maintenance tasks."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──


class ScheduleType(StrEnum):
    """Chore schedule types."""

    TIME = "time"
    COUNT = "count"


class ChoreStatus(StrEnum):
    """Chore status values."""

    ACTIVE = "active"
    PAUSED = "paused"


# ── Core Models ──


class Chore(BaseModel):
    """Full chore record returned from the API."""

    id: str
    project_id: str
    name: str
    template_path: str
    template_content: str
    schedule_type: ScheduleType | None = None
    schedule_value: int | None = None
    status: ChoreStatus = ChoreStatus.ACTIVE
    last_triggered_at: str | None = None
    last_triggered_count: int = 0
    current_issue_number: int | None = None
    current_issue_node_id: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    tracking_issue_number: int | None = None
    created_at: str
    updated_at: str


class ChoreCreate(BaseModel):
    """Request body for creating a new chore."""

    name: str = Field(..., min_length=1, max_length=200)
    template_content: str = Field(..., min_length=1)


class ChoreUpdate(BaseModel):
    """Request body for updating a chore (partial)."""

    schedule_type: ScheduleType | None = None
    schedule_value: int | None = Field(default=None, gt=0)
    status: ChoreStatus | None = None


# ── Trigger Models ──


class ChoreTriggerResult(BaseModel):
    """Result of triggering (or attempting to trigger) a single chore."""

    chore_id: str
    chore_name: str
    triggered: bool
    issue_number: int | None = None
    issue_url: str | None = None
    skip_reason: str | None = None


class EvaluateChoreTriggersResponse(BaseModel):
    """Response for the evaluate-triggers endpoint."""

    evaluated: int
    triggered: int
    skipped: int
    results: list[ChoreTriggerResult]


class EvaluateChoreTriggersRequest(BaseModel):
    """Optional request body for the evaluate-triggers endpoint."""

    project_id: str | None = None


# ── Template Models ──


class ChoreTemplate(BaseModel):
    """A chore template discovered from .github/ISSUE_TEMPLATE/."""

    name: str
    about: str
    path: str
    content: str


# ── Chat Models ──


class ChoreChatMessage(BaseModel):
    """Request body for the chore chat endpoint."""

    content: str
    conversation_id: str | None = None


class ChoreChatResponse(BaseModel):
    """Response from the chore chat endpoint."""

    message: str
    conversation_id: str
    template_ready: bool = False
    template_content: str | None = None
    template_name: str | None = None
