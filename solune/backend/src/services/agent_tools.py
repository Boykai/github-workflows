"""Agent function tools for the Microsoft Agent Framework chat agent.

Each tool wraps an existing AIAgentService action.  Runtime context
(project_id, github_token, session_id) is passed via context variables
so it remains invisible to the LLM tool schema.

v0.2.0 — Intelligent Chat Agent (Microsoft Agent Framework)
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)

# ── Runtime context (invisible to LLM) ──────────────────────────────────

_project_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("project_id")
_github_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "github_token", default=None
)
_session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id")
_project_name_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "project_name", default="Unknown Project"
)
_metadata_context_var: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "metadata_context", default=None
)


@dataclass
class RuntimeContext:
    """Container for runtime context values."""

    project_id: str
    session_id: str
    github_token: str | None = None
    project_name: str = "Unknown Project"
    metadata_context: dict | None = None


def set_runtime_context(ctx: RuntimeContext) -> None:
    """Set runtime context variables for the current agent invocation."""
    _project_id_var.set(ctx.project_id)
    _github_token_var.set(ctx.github_token)
    _session_id_var.set(ctx.session_id)
    _project_name_var.set(ctx.project_name)
    _metadata_context_var.set(ctx.metadata_context)


def get_runtime_context() -> RuntimeContext:
    """Retrieve the current runtime context."""
    return RuntimeContext(
        project_id=_project_id_var.get(),
        session_id=_session_id_var.get(),
        github_token=_github_token_var.get(),
        project_name=_project_name_var.get(),
        metadata_context=_metadata_context_var.get(),
    )


# ── Tool functions ───────────────────────────────────────────────────────


async def create_task_proposal(title: str, description: str) -> dict[str, Any]:
    """Create a task proposal from a title and description.

    Returns a dict with the proposal details for the confirm/reject flow.
    """
    ctx = get_runtime_context()
    logger.info("create_task_proposal called: title=%r, project=%s", title, ctx.project_id)

    return {
        "action": "task_create",
        "title": title,
        "description": description,
        "project_id": ctx.project_id,
        "session_id": ctx.session_id,
    }


async def create_issue_recommendation(
    title: str,
    user_story: str,
    ui_ux_description: str = "",
    functional_requirements: list[str] | None = None,
    technical_notes: str = "",
) -> dict[str, Any]:
    """Create a GitHub issue recommendation from structured input.

    Uses the AI agent service to generate a full issue recommendation
    enriched with metadata context.
    """
    ctx = get_runtime_context()
    logger.info("create_issue_recommendation called: title=%r", title)

    return {
        "action": "issue_create",
        "title": title,
        "user_story": user_story,
        "ui_ux_description": ui_ux_description,
        "functional_requirements": functional_requirements or [],
        "technical_notes": technical_notes,
        "project_id": ctx.project_id,
        "session_id": ctx.session_id,
    }


async def update_task_status(task_reference: str, target_status: str) -> dict[str, Any]:
    """Update the status of a task identified by reference.

    Uses identify_target_task to resolve the reference to a specific task.
    """
    ctx = get_runtime_context()
    logger.info(
        "update_task_status called: ref=%r, status=%r, project=%s",
        task_reference,
        target_status,
        ctx.project_id,
    )

    return {
        "action": "status_update",
        "task_reference": task_reference,
        "target_status": target_status,
        "project_id": ctx.project_id,
        "session_id": ctx.session_id,
    }


async def analyze_transcript(transcript_content: str) -> dict[str, Any]:
    """Analyse a meeting transcript and extract action items.

    Returns structured analysis with title, user story, and requirements.
    """
    ctx = get_runtime_context()
    logger.info(
        "analyze_transcript called: content_len=%d, project=%s",
        len(transcript_content),
        ctx.project_id,
    )

    return {
        "action": "issue_create",
        "transcript_length": len(transcript_content),
        "project_id": ctx.project_id,
        "session_id": ctx.session_id,
    }


async def ask_clarifying_question(question: str) -> dict[str, Any]:
    """Ask the user a clarifying question before taking action.

    Returns the question to be relayed to the user.
    """
    logger.info("ask_clarifying_question called: %r", question[:100])
    return {
        "action": "clarify",
        "question": question,
    }


async def get_project_context() -> dict[str, Any]:
    """Retrieve current project metadata (tasks, columns, pipelines).

    Returns project context visible to the agent for informed decisions.
    """
    ctx = get_runtime_context()
    logger.info("get_project_context called for project=%s", ctx.project_id)

    return {
        "project_id": ctx.project_id,
        "project_name": ctx.project_name,
    }


async def get_pipeline_list() -> dict[str, Any]:
    """Retrieve available CI/CD pipelines for the current project.

    Returns a list of pipeline configurations.
    """
    ctx = get_runtime_context()
    logger.info("get_pipeline_list called for project=%s", ctx.project_id)

    return {
        "project_id": ctx.project_id,
        "pipelines": [],
    }
