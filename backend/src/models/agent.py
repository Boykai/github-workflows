"""Agent assignment and discovery models."""

from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, BeforeValidator, Field

from src.constants import AGENT_DISPLAY_NAMES, DEFAULT_AGENT_MAPPINGS


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
    source: AgentSource = Field(..., description="Discovery source")


class AvailableAgentsResponse(BaseModel):
    """Response for listing available agents."""

    agents: list[AvailableAgent]


__all__ = [
    "AgentSource",
    "AgentAssignment",
    "AgentAssignmentInput",
    "AvailableAgent",
    "AvailableAgentsResponse",
]
