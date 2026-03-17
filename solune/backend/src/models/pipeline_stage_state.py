"""Pydantic models for pipeline stage state tracking."""

from __future__ import annotations

from pydantic import BaseModel


class PipelineStageState(BaseModel):
    """Individual stage execution state within a pipeline run.

    Tracks state for each stage from initiation through completion.
    """

    id: int
    pipeline_run_id: int
    stage_id: str
    group_id: int | None = None
    status: str = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    agent_id: str | None = None
    output: dict | None = None
    label_name: str | None = None
    error_message: str | None = None
    created_at: str = ""
    updated_at: str = ""


class PipelineStageStateUpdate(BaseModel):
    """Partial update for a pipeline stage state."""

    status: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    agent_id: str | None = None
    output: dict | None = None
    label_name: str | None = None
    error_message: str | None = None
