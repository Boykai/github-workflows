"""Pydantic models for housekeeping tasks, templates, and trigger events."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# ── Enums ──


class TemplateCategory(StrEnum):
    """Template category types."""

    BUILT_IN = "built-in"
    CUSTOM = "custom"


class TriggerType(StrEnum):
    """Housekeeping task trigger types."""

    TIME = "time"
    COUNT = "count"


class TriggerEventType(StrEnum):
    """Trigger event types for history records."""

    SCHEDULED = "scheduled"
    COUNT_BASED = "count-based"
    MANUAL = "manual"


class TriggerStatus(StrEnum):
    """Trigger event status."""

    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"  # Recorded when GitHub API integration is not yet wired


# ── Issue Template Models ──


class IssueTemplate(BaseModel):
    """Issue template response model."""

    id: str
    name: str
    title_pattern: str
    body_content: str
    category: TemplateCategory
    created_at: str
    updated_at: str


class IssueTemplateCreate(BaseModel):
    """Request body for creating a template."""

    name: str = Field(..., min_length=1, max_length=200)
    title_pattern: str = Field(..., min_length=1, max_length=500)
    body_content: str = Field(..., min_length=1)


class IssueTemplateUpdate(BaseModel):
    """Request body for updating a template (partial)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    title_pattern: str | None = Field(default=None, min_length=1, max_length=500)
    body_content: str | None = Field(default=None, min_length=1)


class TemplateListResponse(BaseModel):
    """Response for listing templates."""

    templates: list[IssueTemplate]


# ── Housekeeping Task Models ──


class HousekeepingTask(BaseModel):
    """Housekeeping task response model."""

    id: str
    name: str
    description: str | None = None
    template_id: str
    template_name: str | None = None
    sub_issue_config: dict | None = None
    trigger_type: TriggerType
    trigger_value: str
    last_triggered_at: str | None = None
    last_triggered_issue_count: int = 0
    enabled: bool = True
    cooldown_minutes: int = 5
    project_id: str
    created_at: str
    updated_at: str


class HousekeepingTaskCreate(BaseModel):
    """Request body for creating a housekeeping task."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    template_id: str
    sub_issue_config: dict | None = None
    trigger_type: TriggerType
    trigger_value: str = Field(..., min_length=1)
    cooldown_minutes: int = Field(default=5, ge=1)
    project_id: str
    current_issue_count: int | None = Field(
        default=None,
        ge=0,
        description=(
            "For count-based triggers, the current number of issues in the "
            "project.  Stored as the baseline so the task only fires after "
            "*new* issues exceed the threshold."
        ),
    )


class HousekeepingTaskUpdate(BaseModel):
    """Request body for updating a housekeeping task (partial)."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    template_id: str | None = None
    sub_issue_config: dict | None = None
    trigger_type: TriggerType | None = None
    trigger_value: str | None = Field(default=None, min_length=1)
    cooldown_minutes: int | None = Field(default=None, ge=1)


class TaskListResponse(BaseModel):
    """Response for listing housekeeping tasks."""

    tasks: list[HousekeepingTask]


class TaskToggleRequest(BaseModel):
    """Request body for toggling task enabled state."""

    enabled: bool


# ── Trigger Event Models ──


class TriggerEvent(BaseModel):
    """Trigger event history record."""

    id: str
    task_id: str
    timestamp: str
    trigger_type: TriggerEventType
    issue_url: str | None = None
    issue_number: int | None = None
    status: TriggerStatus
    error_details: str | None = None
    sub_issues_created: int = 0


class TriggerHistoryResponse(BaseModel):
    """Response for listing trigger history."""

    history: list[TriggerEvent]
    total: int
    limit: int
    offset: int


# ── Evaluate Triggers Models ──


class EvaluateTriggersRequest(BaseModel):
    """Request body for evaluate-triggers endpoint."""

    trigger_source: str = "scheduled"
    project_id: str


class EvaluateTriggersResult(BaseModel):
    """Single task evaluation result."""

    task_id: str
    task_name: str
    action: str
    issue_url: str | None = None
    reason: str | None = None


class EvaluateTriggersResponse(BaseModel):
    """Response for evaluate-triggers endpoint."""

    evaluated: int
    triggered: int
    skipped: int
    results: list[EvaluateTriggersResult]
