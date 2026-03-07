"""Pydantic models for Agent Pipeline configurations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PipelineAgentNode(BaseModel):
    """An agent placed within a stage, configured with a specific model."""

    id: str
    agent_slug: str
    agent_display_name: str = ""
    model_id: str = ""
    model_name: str = ""
    config: dict = Field(default_factory=dict)


class PipelineStage(BaseModel):
    """A named step within a pipeline containing agents."""

    id: str
    name: str = Field(..., min_length=1, max_length=100)
    order: int
    agents: list[PipelineAgentNode] = Field(default_factory=list)


class PipelineConfig(BaseModel):
    """Full pipeline configuration record."""

    id: str
    project_id: str
    name: str
    description: str = ""
    stages: list[PipelineStage] = Field(default_factory=list)
    created_at: str
    updated_at: str


class PipelineConfigCreate(BaseModel):
    """Request body for creating a new pipeline."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    stages: list[PipelineStage] = Field(default_factory=list)


class PipelineConfigUpdate(BaseModel):
    """Request body for updating an existing pipeline."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    stages: list[PipelineStage] | None = None


class PipelineConfigSummary(BaseModel):
    """Summary of a pipeline for the list endpoint."""

    id: str
    name: str
    description: str
    stage_count: int
    agent_count: int
    updated_at: str


class PipelineConfigListResponse(BaseModel):
    """Response for the list endpoint."""

    pipelines: list[PipelineConfigSummary]
    total: int


class AIModel(BaseModel):
    """An available AI model for agent assignment."""

    id: str
    name: str
    provider: str
    context_window_size: int
    cost_tier: str
    capability_category: str = ""
