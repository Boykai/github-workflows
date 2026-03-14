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
    execution_count: int = 0
    ai_enhance_enabled: bool = True
    agent_pipeline_id: str = ""
    is_preset: bool = False
    preset_id: str = ""
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
    ai_enhance_enabled: bool | None = None
    agent_pipeline_id: str | None = None


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
    parent_issue_count: int | None = None


class TriggerChoreRequest(BaseModel):
    """Optional request body for the manual trigger endpoint."""

    parent_issue_count: int | None = None


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
    ai_enhance: bool = True


class ChoreChatResponse(BaseModel):
    """Response from the chore chat endpoint."""

    message: str
    conversation_id: str
    template_ready: bool = False
    template_content: str | None = None
    template_name: str | None = None


# ── Inline Editing Models ──


class ChoreInlineUpdate(BaseModel):
    """Request body for inline editing of a Chore definition.

    A PR is only created when ``name`` or ``template_content`` is set.
    All other fields are config-only and saved directly without creating a PR.
    """

    name: str | None = Field(default=None, min_length=1, max_length=200)
    template_content: str | None = Field(default=None, min_length=1)
    schedule_type: ScheduleType | None = None
    schedule_value: int | None = Field(default=None, gt=0)
    ai_enhance_enabled: bool | None = None
    agent_pipeline_id: str | None = None
    expected_sha: str | None = None


class ChoreInlineUpdateResponse(BaseModel):
    """Response from inline Chore update with PR creation result."""

    chore: Chore
    pr_number: int | None = None
    pr_url: str | None = None
    pr_merged: bool = False
    merge_error: str | None = None


# ── Creation with Auto-Merge Models ──


class ChoreCreateWithConfirmation(BaseModel):
    """Request body for creating a new Chore with the full auto-merge flow."""

    name: str = Field(..., min_length=1, max_length=200)
    template_content: str = Field(..., min_length=1)
    ai_enhance_enabled: bool = True
    agent_pipeline_id: str = ""
    auto_merge: bool = True


class ChoreCreateResponse(BaseModel):
    """Response from Chore creation with full flow result."""

    chore: Chore
    issue_number: int | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    pr_merged: bool = False
    merge_error: str | None = None
