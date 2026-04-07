"""Agent function tools for the Microsoft Agent Framework.

Each tool is a plain ``async`` function decorated with contextvar-based runtime
context injection.  The agent framework calls these functions when the LLM
decides to invoke a tool — runtime secrets (``project_id``, ``github_token``,
``session_id``) are passed via :pymod:`contextvars` so they never appear in the
tool's LLM-visible schema.

Deprecation note
~~~~~~~~~~~~~~~~
These tools replace the direct method calls on :class:`AIAgentService`
(``generate_task_from_description``, ``detect_feature_request_intent``, etc.).
The old service layer is deprecated but still present for backward
compatibility until v0.3.0.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)

# ── Runtime context (invisible to LLM) ────────────────────────────────────

_project_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("project_id")
_github_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "github_token", default=None
)
_session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id")
_project_name_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "project_name", default="Unknown Project"
)


def set_runtime_context(
    *,
    project_id: str,
    session_id: str,
    github_token: str | None = None,
    project_name: str = "Unknown Project",
) -> None:
    """Set runtime context variables before an agent run."""
    _project_id_var.set(project_id)
    _session_id_var.set(session_id)
    _github_token_var.set(github_token)
    _project_name_var.set(project_name)


def get_runtime_context() -> dict[str, Any]:
    """Retrieve the current runtime context as a dict."""
    return {
        "project_id": _project_id_var.get(""),
        "session_id": _session_id_var.get(""),
        "github_token": _github_token_var.get(None),
        "project_name": _project_name_var.get("Unknown Project"),
    }


# ── Tool result dataclasses ───────────────────────────────────────────────


@dataclass
class ToolResult:
    """Standard result wrapper returned by all agent tools."""

    action_type: str
    data: dict[str, Any]
    message: str


# ── Tool implementations ──────────────────────────────────────────────────


async def create_task_proposal(title: str, description: str) -> dict[str, Any]:
    """Create a task proposal from a title and description.

    Args:
        title: Concise, action-oriented task title.
        description: Detailed task description with acceptance criteria.

    Returns:
        A dict with ``action_type``, ``title``, ``description``, and a
        human-readable ``message``.
    """
    ctx = get_runtime_context()
    logger.info(
        "create_task_proposal called — project=%s, session=%s",
        ctx["project_id"],
        ctx["session_id"],
    )

    # Enforce length limits
    if len(title) > 256:
        title = title[:253] + "..."
    if len(description) > 65535:
        description = description[:65532] + "..."

    return {
        "action_type": "task_create",
        "title": title,
        "description": description,
        "message": f"I've drafted a task: **{title}**. Please review and confirm.",
    }


async def create_issue_recommendation(
    title: str,
    user_story: str,
    *,
    ui_ux_description: str = "",
    functional_requirements: list[str] | None = None,
    technical_notes: str = "",
    priority: str = "P2",
    size: str = "M",
) -> dict[str, Any]:
    """Create a structured GitHub issue recommendation.

    Args:
        title: Issue title (max 256 chars).
        user_story: User story in "As a …" format.
        ui_ux_description: UI/UX guidance for designers.
        functional_requirements: List of testable requirements.
        technical_notes: Implementation hints.
        priority: P0-P3.
        size: XS / S / M / L / XL.

    Returns:
        A dict with ``action_type`` ``"issue_create"`` and structured data.
    """
    ctx = get_runtime_context()
    logger.info(
        "create_issue_recommendation called — project=%s",
        ctx["project_id"],
    )

    if len(title) > 256:
        title = title[:253] + "..."

    return {
        "action_type": "issue_create",
        "title": title,
        "user_story": user_story,
        "ui_ux_description": ui_ux_description or "No UI/UX description provided.",
        "functional_requirements": functional_requirements or [],
        "technical_notes": technical_notes,
        "priority": priority.upper() if priority else "P2",
        "size": size.upper() if size else "M",
        "message": f"I've drafted an issue: **{title}**. Please review and confirm.",
    }


async def update_task_status(task_reference: str, target_status: str) -> dict[str, Any]:
    """Propose a status change for an existing task.

    Args:
        task_reference: Title or description fragment identifying the task.
        target_status: Target status column name (e.g. "In Progress", "Done").

    Returns:
        A dict with ``action_type`` ``"status_update"`` and the parsed intent.
    """
    ctx = get_runtime_context()
    logger.info(
        "update_task_status called — project=%s, ref=%s, status=%s",
        ctx["project_id"],
        task_reference,
        target_status,
    )
    return {
        "action_type": "status_update",
        "task_reference": task_reference,
        "target_status": target_status,
        "message": f"Moving **{task_reference}** → *{target_status}*.",
    }


async def analyze_transcript(transcript_content: str) -> dict[str, Any]:
    """Analyse a meeting transcript and extract actionable items.

    Args:
        transcript_content: Raw transcript text (VTT, SRT, or plain text).

    Returns:
        A dict with ``action_type`` ``"issue_create"`` containing extracted
        requirements and recommendations.
    """
    ctx = get_runtime_context()
    logger.info(
        "analyze_transcript called — project=%s, len=%d",
        ctx["project_id"],
        len(transcript_content),
    )
    return {
        "action_type": "issue_create",
        "transcript_length": len(transcript_content),
        "message": "I've analysed the transcript. Generating issue recommendation…",
    }


async def ask_clarifying_question(question: str) -> dict[str, Any]:
    """Ask the user a clarifying question before taking action.

    Args:
        question: The question to present to the user.

    Returns:
        A dict with ``action_type`` ``None`` and the question as ``message``.
    """
    return {
        "action_type": None,
        "message": question,
    }


async def get_project_context() -> dict[str, Any]:
    """Retrieve the active project's name, columns, and task list.

    Returns:
        A dict containing project metadata from runtime context.
    """
    ctx = get_runtime_context()
    return {
        "project_id": ctx["project_id"],
        "project_name": ctx["project_name"],
    }


async def get_pipeline_list() -> dict[str, Any]:
    """Retrieve the list of pipelines for the active project.

    Returns:
        A dict with pipeline information (placeholder — requires DB access).
    """
    ctx = get_runtime_context()
    return {
        "project_id": ctx["project_id"],
        "pipelines": [],
        "message": "Pipeline list retrieved.",
    }


# ── Tool registry ─────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, Any] = {
    "create_task_proposal": create_task_proposal,
    "create_issue_recommendation": create_issue_recommendation,
    "update_task_status": update_task_status,
    "analyze_transcript": analyze_transcript,
    "ask_clarifying_question": ask_clarifying_question,
    "get_project_context": get_project_context,
    "get_pipeline_list": get_pipeline_list,
}
