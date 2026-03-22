"""Pydantic models for MCP (Model Context Protocol) configuration management."""

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field

from src.utils import utcnow


class McpConfigurationCreate(BaseModel):
    """Request body for creating a new MCP configuration."""

    name: str = Field(min_length=1, max_length=100)
    endpoint_url: str = Field(min_length=1, max_length=2048)


class McpConfigurationUpdate(BaseModel):
    """Request body for updating an MCP configuration with optimistic concurrency."""

    name: str = Field(min_length=1, max_length=100)
    endpoint_url: str = Field(min_length=1, max_length=2048)
    expected_version: int = Field(
        ge=1, description="Expected current version for concurrency check"
    )


class CollisionSummary(BaseModel):
    """Summary of a resolved collision returned in update responses."""

    collision_id: str
    resolution_strategy: str
    resolution_outcome: str
    winning_operation: str


class McpConfigurationResponse(BaseModel):
    """Single MCP configuration in API responses."""

    id: str
    name: str
    endpoint_url: str
    is_active: bool
    version: int = 1
    created_at: str
    updated_at: str
    collision: CollisionSummary | None = None


class McpConfigurationListResponse(BaseModel):
    """List of MCP configurations for a user."""

    mcps: list[McpConfigurationResponse]
    count: int


# ── Phase 8: Collision Resolution Models ──


@dataclass
class CollisionOperation:
    """Represents one side of a detected collision."""

    operation_id: str
    operation_type: str  # "update" | "delete" | "move" | "label_change"
    initiated_by: str  # "user" | "automation"
    user_id: str | None = None
    timestamp: datetime = field(default_factory=utcnow)
    payload: dict = field(default_factory=dict)
    version_expected: int = 0


@dataclass
class CollisionEvent:
    """Represents a detected collision between concurrent operations."""

    collision_id: str
    target_entity_type: str
    target_entity_id: str
    operation_a: CollisionOperation
    operation_b: CollisionOperation
    resolution_strategy: str  # "last_write_wins" | "user_priority" | "manual_review"
    resolution_outcome: str
    winning_operation: str  # "a" | "b" | "neither"
    detected_at: datetime = field(default_factory=utcnow)
    resolved_at: datetime | None = None
