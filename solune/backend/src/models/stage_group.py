"""Pydantic models for stage group configuration (FR-016, FR-017)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class StageGroup(BaseModel):
    """A logical grouping of pipeline stages with execution mode."""

    id: int
    pipeline_config_id: str
    name: str
    execution_mode: str = "sequential"
    order_index: int
    created_at: str = ""
    updated_at: str = ""

    @field_validator("execution_mode")
    @classmethod
    def validate_execution_mode(cls, v: str) -> str:
        if v not in ("sequential", "parallel"):
            raise ValueError("execution_mode must be 'sequential' or 'parallel'")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class StageGroupCreate(BaseModel):
    """Request body for creating a stage group."""

    name: str = Field(..., min_length=1, max_length=100)
    execution_mode: str = Field(default="sequential", pattern=r"^(sequential|parallel)$")
    order_index: int = Field(..., ge=0)


class StageGroupUpdate(BaseModel):
    """Request body for updating a stage group."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    execution_mode: str | None = Field(default=None, pattern=r"^(sequential|parallel)$")
    order_index: int | None = Field(default=None, ge=0)


class StageGroupListResponse(BaseModel):
    """Response for listing stage groups."""

    groups: list[StageGroup]
    total: int
