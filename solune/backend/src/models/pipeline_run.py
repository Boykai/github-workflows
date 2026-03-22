"""Pydantic models for pipeline run state persistence (FR-001, FR-002, FR-003)."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class PipelineRunCreate(BaseModel):
    """Request body for creating a new pipeline run."""

    trigger: str = Field(default="manual", pattern=r"^(manual|webhook|scheduled)$")


class PipelineRunStageState(BaseModel):
    """Stage state within a pipeline run response."""

    id: int
    stage_id: str
    group_id: int | None = None
    status: str = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    agent_id: str | None = None
    label_name: str | None = None
    error_message: str | None = None


class PipelineRunStageSummary(BaseModel):
    """Aggregated stage counts for list responses."""

    total: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    pending: int = 0
    skipped: int = 0


class PipelineRun(BaseModel):
    """Full pipeline run record with stage details."""

    id: int
    pipeline_config_id: str
    project_id: str
    status: str = "pending"
    started_at: str
    completed_at: str | None = None
    trigger: str = "manual"
    error_message: str | None = None
    metadata: dict | None = None
    stages: list[PipelineRunStageState] = Field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    # Phase 8: Concurrent execution tracking
    execution_mode: str = "sequential"
    concurrent_group_id: str | None = None
    is_isolated: bool = True

    @model_validator(mode="after")
    def _validate_completion(self) -> PipelineRun:
        """Validate completed_at presence based on status."""
        terminal = {"completed", "failed", "cancelled"}
        active = {"pending", "running"}
        if self.status in terminal and not self.completed_at:
            raise ValueError(f"completed_at must be set when status is '{self.status}'")
        if self.status in active and self.completed_at:
            raise ValueError(f"completed_at must be None when status is '{self.status}'")
        return self


class PipelineRunSummary(BaseModel):
    """Summary of a pipeline run for list responses."""

    id: int
    pipeline_config_id: str
    status: str
    started_at: str
    completed_at: str | None = None
    trigger: str = "manual"
    stage_summary: PipelineRunStageSummary = Field(default_factory=PipelineRunStageSummary)
    # Phase 8: Concurrent execution tracking
    execution_mode: str = "sequential"
    concurrent_group_id: str | None = None
    is_isolated: bool = True


class PipelineRunListResponse(BaseModel):
    """Response for listing pipeline runs (FR-003)."""

    runs: list[PipelineRunSummary]
    total: int
    limit: int = 50
    offset: int = 0
