"""Models for the #agent custom agent creation feature."""

from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from src.utils import utcnow


class CreationStep(StrEnum):
    """Steps in the guided agent creation conversation."""

    PARSE = "parse"
    RESOLVE_PROJECT = "resolve_project"
    RESOLVE_STATUS = "resolve_status"
    PREVIEW = "preview"
    EDIT_LOOP = "edit_loop"
    EXECUTING = "executing"
    DONE = "done"


class AgentPreview(BaseModel):
    """AI-generated agent configuration shown to the user for review."""

    name: str = Field(..., description="Agent display name")
    slug: str = Field(..., description="Kebab-case derived identifier")
    description: str = Field(..., description="One-line summary")
    icon_name: str | None = Field(default=None, description="Celestial icon identifier")
    system_prompt: str = Field(..., description="Full system prompt text")
    status_column: str = Field(..., description="Assigned status column")
    tools: list[str] = Field(default_factory=list, description="Human-readable selected tools")
    tool_allowlist: list[str] = Field(
        default_factory=list,
        description="Exact GitHub tool allowlist written to agent frontmatter",
    )
    tool_ids: list[str] = Field(
        default_factory=list,
        description="Persisted MCP tool identifiers selected in the app",
    )
    mcp_servers: dict[str, object] = Field(
        default_factory=dict,
        description="GitHub custom-agent MCP server configuration written to frontmatter",
    )

    @staticmethod
    def name_to_slug(name: str) -> str:
        """Derive a kebab-case slug from an agent display name.

        Lowercase, replace spaces/special chars with hyphens, collapse
        consecutive hyphens, strip leading/trailing hyphens.
        """
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = re.sub(r"-{2,}", "-", slug)
        return slug.strip("-")


class PipelineStepResult(BaseModel):
    """Result of a single step in the creation pipeline."""

    step_name: str = Field(..., description="Human-readable step name")
    success: bool = Field(..., description="Whether the step completed successfully")
    error: str | None = Field(default=None, description="Error message if failed")
    detail: str | None = Field(default=None, description="Extra info (e.g., issue URL)")


class AgentCreationState(BaseModel):
    """Tracks the multi-step guided conversation for a single agent creation session."""

    step: CreationStep = Field(default=CreationStep.PARSE)
    session_id: str = Field(..., description="Web chat session ID or Signal user ID")
    github_user_id: str = Field(default="", description="GitHub user ID for created_by tracking")
    project_id: str | None = Field(default=None, description="Target GitHub Project node ID")
    owner: str | None = Field(default=None, description="Repository owner")
    repo: str | None = Field(default=None, description="Repository name")
    raw_description: str = Field(default="", description="Original description from #agent command")
    raw_status: str | None = Field(default=None, description="Optional status from #<status-name>")
    resolved_status: str | None = Field(default=None, description="Matched or new column name")
    is_new_column: bool = Field(
        default=False, description="Whether resolved status is a new column"
    )
    preview: AgentPreview | None = Field(default=None, description="AI-generated agent preview")
    pipeline_results: list[PipelineStepResult] = Field(
        default_factory=list, description="Results from each pipeline step"
    )
    created_at: datetime = Field(default_factory=utcnow)
    # Columns presented to the user for disambiguation (transient)
    ambiguous_columns: list[str] = Field(
        default_factory=list, description="Columns to present when status is ambiguous"
    )
    # Available projects for Signal multi-project selection (transient)
    available_projects: list[dict] = Field(
        default_factory=list, description="Projects for selection (id, name)"
    )


__all__ = [
    "AgentCreationState",
    "AgentPreview",
    "CreationStep",
    "PipelineStepResult",
]
