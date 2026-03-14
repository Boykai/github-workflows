"""Agent assignment and discovery models."""

from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, BeforeValidator, Field


class AgentSource(StrEnum):
    """Source of an available agent."""

    BUILTIN = "builtin"
    REPOSITORY = "repository"


class AgentAssignment(BaseModel):
    """A single agent assignment within a workflow status column."""

    id: UUID = Field(default_factory=uuid4, description="Unique instance ID")
    slug: str = Field(..., description="Agent identifier slug")
    display_name: str | None = Field(default=None, description="Human-readable display name")
    config: dict | None = Field(
        default=None, description="Reserved for future per-assignment config"
    )


def _coerce_agent(v: str | dict | AgentAssignment) -> AgentAssignment | dict:
    """Accept a bare slug string and promote to AgentAssignment."""
    if isinstance(v, str):
        return AgentAssignment(slug=v)
    return v


AgentAssignmentInput = Annotated[AgentAssignment, BeforeValidator(_coerce_agent)]


class AvailableAgent(BaseModel):
    """An agent available for assignment, from discovery."""

    slug: str = Field(..., description="Unique agent identifier")
    display_name: str = Field(..., description="Human-readable name")
    description: str | None = Field(default=None, description="Agent description")
    avatar_url: str | None = Field(default=None, description="Avatar URL")
    icon_name: str | None = Field(default=None, description="Celestial icon identifier")
    default_model_id: str = Field(default="", description="Saved default model ID")
    default_model_name: str = Field(default="", description="Saved default model name")
    tools_count: int | None = Field(default=None, description="Number of configured tools")
    source: AgentSource = Field(..., description="Discovery source")


class AvailableAgentsResponse(BaseModel):
    """Response for listing available agents."""

    agents: list[AvailableAgent]


class AgentStepState(StrEnum):
    """Typed state values from tracking table markdown cells.

    Replaces emoji-based string matching (e.g., "✅ Done", "🔄 Active")
    with exhaustive enum matching.
    """

    DONE = "done"
    ACTIVE = "active"
    QUEUED = "queued"
    ERROR = "error"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"

    @classmethod
    def from_markdown(cls, cell_text: str) -> "AgentStepState":
        """Parse tracking table cell text into typed state."""
        text = cell_text.strip()
        if text.startswith("✅"):
            return cls.DONE
        if text.startswith("🔄"):
            return cls.ACTIVE
        if text.startswith("⏳"):
            return cls.QUEUED
        if text.startswith("❌"):
            return cls.ERROR
        if text.startswith("⏭"):
            return cls.SKIPPED
        return cls.UNKNOWN


__all__ = [
    "AgentAssignment",
    "AgentAssignmentInput",
    "AgentSource",
    "AgentStepState",
    "AvailableAgent",
    "AvailableAgentsResponse",
]
