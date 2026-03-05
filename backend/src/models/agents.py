"""Pydantic models for the Agents section — Custom GitHub Agent CRUD."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    ACTIVE = "active"
    PENDING_PR = "pending_pr"


class AgentSource(StrEnum):
    LOCAL = "local"
    REPO = "repo"
    BOTH = "both"


class Agent(BaseModel):
    """API response model — merged view from SQLite + GitHub repo."""

    id: str
    name: str
    slug: str
    description: str
    system_prompt: str = ""
    status: AgentStatus = AgentStatus.ACTIVE
    tools: list[str] = Field(default_factory=list)
    status_column: str | None = None
    github_issue_number: int | None = None
    github_pr_number: int | None = None
    branch_name: str | None = None
    source: AgentSource = AgentSource.LOCAL
    created_at: str | None = None


class AgentCreate(BaseModel):
    """Request body for creating a new agent."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    system_prompt: str = Field(..., min_length=1, max_length=30000)
    tools: list[str] = Field(default_factory=list)
    status_column: str = ""
    raw: bool = False  # If True, use exact content as-is without AI generation


class AgentUpdate(BaseModel):
    """Request body for updating an existing agent (P3)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    system_prompt: str | None = Field(default=None, min_length=1, max_length=30000)
    tools: list[str] | None = None


class AgentCreateResult(BaseModel):
    """Response for agent creation / update."""

    agent: Agent
    pr_url: str
    pr_number: int
    issue_number: int | None = None
    branch_name: str


class AgentDeleteResult(BaseModel):
    """Response for agent deletion."""

    success: bool
    pr_url: str
    pr_number: int
    issue_number: int | None = None


class AgentChatMessage(BaseModel):
    """Request body for chat refinement."""

    message: str
    session_id: str | None = None


class AgentChatResponse(BaseModel):
    """Response from chat refinement."""

    reply: str
    session_id: str
    is_complete: bool = False
    preview: AgentPreviewResponse | None = None


class AgentPreviewResponse(BaseModel):
    """Agent preview returned in chat responses."""

    name: str
    slug: str
    description: str
    system_prompt: str
    status_column: str = ""
    tools: list[str] = Field(default_factory=list)
