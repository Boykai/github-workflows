"""Pydantic models for the Agents section — Custom GitHub Agent CRUD."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentStatus(StrEnum):
    ACTIVE = "active"
    PENDING_PR = "pending_pr"
    PENDING_DELETION = "pending_deletion"


class AgentSource(StrEnum):
    LOCAL = "local"
    REPO = "repo"
    BOTH = "both"


class Agent(BaseModel):
    """API response model for repo-backed agent availability and agent workflow results."""

    id: str
    name: str
    slug: str
    description: str
    icon_name: str | None = None
    system_prompt: str = ""
    default_model_id: str = ""
    default_model_name: str = ""
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
    icon_name: str | None = Field(default=None, max_length=100)
    system_prompt: str = Field(..., min_length=1, max_length=30000)
    tools: list[str] = Field(default_factory=list)
    status_column: str = ""
    default_model_id: str = ""
    default_model_name: str = ""
    raw: bool = False  # If True, use exact content as-is without AI generation


class AgentUpdate(BaseModel):
    """Request body for updating an existing agent (P3)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    icon_name: str | None = Field(default=None, max_length=100)
    system_prompt: str | None = Field(default=None, min_length=1, max_length=30000)
    tools: list[str] | None = None
    default_model_id: str | None = None
    default_model_name: str | None = None


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


class AgentPendingCleanupResult(BaseModel):
    """Response for deleting stale pending agent rows from SQLite."""

    success: bool = True
    deleted_count: int


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
    icon_name: str | None = None
    system_prompt: str
    status_column: str = ""
    tools: list[str] = Field(default_factory=list)


class BulkModelUpdateRequest(BaseModel):
    """Request body for bulk model update — applies a target model to all agents."""

    target_model_id: str = Field(..., min_length=1, max_length=200)
    target_model_name: str = Field(..., min_length=1, max_length=200)


class BulkModelUpdateResult(BaseModel):
    """Response from bulk model update endpoint."""

    success: bool = True
    updated_count: int
    failed_count: int = 0
    updated_agents: list[str] = Field(default_factory=list)
    failed_agents: list[str] = Field(default_factory=list)
    target_model_id: str
    target_model_name: str
