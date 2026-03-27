"""Pydantic models for the Self-Evolving Roadmap Engine (FR-002, FR-003)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class RoadmapItem(BaseModel):
    """A single AI-generated feature proposal (FR-002)."""

    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    priority: Literal["P0", "P1", "P2", "P3"]
    size: Literal["XS", "S", "M", "L", "XL"]


class RoadmapBatch(BaseModel):
    """A batch of AI-generated feature proposals from one cycle (FR-002)."""

    items: list[RoadmapItem] = Field(..., min_length=1, max_length=10)
    project_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RoadmapCycleStatus(StrEnum):
    """Possible states for a roadmap generation cycle."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class RoadmapCycleLog(BaseModel):
    """Audit record for a roadmap generation cycle (FR-003)."""

    id: int
    project_id: str
    user_id: str
    batch_json: str  # Serialized RoadmapBatch
    status: RoadmapCycleStatus = RoadmapCycleStatus.PENDING
    created_at: str

    @property
    def batch(self) -> RoadmapBatch:
        """Deserialize batch_json into a RoadmapBatch."""
        return RoadmapBatch.model_validate_json(self.batch_json)
