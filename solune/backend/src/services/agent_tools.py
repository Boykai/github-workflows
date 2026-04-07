"""Agent Framework function tools for Solune chat actions.

Each tool is a ``@tool``-decorated async function that the Agent can invoke
based on user intent.  Runtime context (project_id, github_token, session_id)
is passed through a module-level ``contextvars.ContextVar`` so that the LLM
never sees sensitive values in the tool schema.  This approach works with both
``Agent`` and ``GitHubCopilotAgent`` (which has a different ``run()`` signature).

Design note — tool registration is a flat list so that future MCP tools
(v0.4.0 scope) can simply be appended without changing the tool interface.
"""

from __future__ import annotations

import contextvars
import json
from typing import Any
from uuid import UUID

from agent_framework import tool

from src.logging_utils import get_logger
from src.models.recommendation import (
    IssueMetadata,
    IssuePriority,
    IssueRecommendation,
    IssueSize,
)
from src.utils import utcnow

logger = get_logger(__name__)

# ── Runtime context (set before agent.run(), read by tools) ────────────────

_runtime_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "agent_runtime_context", default=None
)


def set_runtime_context(ctx: dict[str, Any]) -> contextvars.Token[dict[str, Any]]:
    """Set runtime context for the current agent invocation.

    Must be called before ``agent.run()`` in the same async task.
    Returns a token that can be used to reset the context.
    """
    return _runtime_context.set(ctx)


def get_runtime_context() -> dict[str, Any]:
    """Read the current runtime context (called by tools)."""
    return _runtime_context.get() or {}


# ── Tool: Create Task Proposal ─────────────────────────────────────────────


@tool(
    name="create_task_proposal",
    description=(
        "Create a structured task proposal with a title and detailed description. "
        "Use when the user wants to create a new task or ticket."
    ),
)
async def create_task_proposal(
    title: str,
    description: str,
) -> str:
    """Create a task proposal for the user to confirm.

    Args:
        title: Short action-oriented task title (≤100 chars, start with a verb).
        description: Detailed markdown description with acceptance criteria.

    Returns:
        JSON string with the proposal data.
    """
    runtime = get_runtime_context()
    project_name = runtime.get("project_name", "Unknown")
    logger.info("Tool create_task_proposal invoked for project=%s", project_name)

    return json.dumps(
        {
            "action_type": "task_create",
            "proposed_title": title[:256],
            "proposed_description": description[:65536],
            "project_name": project_name,
        }
    )


# ── Tool: Create Issue Recommendation ──────────────────────────────────────


@tool(
    name="create_issue_recommendation",
    description=(
        "Create a structured issue recommendation for a feature request, bug report, "
        "or enhancement. Use when the user describes something that should become a "
        "GitHub issue."
    ),
)
async def create_issue_recommendation(
    title: str,
    user_story: str,
    functional_requirements: str,
    ui_ux_description: str = "",
    technical_notes: str = "",
    priority: str = "P2",
    size: str = "M",
) -> str:
    """Create an issue recommendation for user review.

    Args:
        title: Issue title (≤256 chars).
        user_story: "As a … I want … so that …" format.
        functional_requirements: Comma-separated list of requirements.
        ui_ux_description: Optional UI/UX notes.
        technical_notes: Optional technical implementation notes.
        priority: P0 (critical) through P3 (low). Default P2.
        size: XS / S / M / L / XL t-shirt size. Default M.

    Returns:
        JSON string with the recommendation data.
    """
    runtime = get_runtime_context()
    project_name = runtime.get("project_name", "Unknown")
    session_id = runtime.get("session_id", "")
    logger.info("Tool create_issue_recommendation invoked for project=%s", project_name)

    # Parse requirements list
    reqs = [r.strip() for r in functional_requirements.split(",") if r.strip()]
    if not reqs:
        reqs = [functional_requirements]

    # Normalize priority/size with safe defaults
    try:
        prio = IssuePriority(priority.upper())
    except (ValueError, KeyError):
        prio = IssuePriority.P2

    try:
        sz = IssueSize(size.upper())
    except (ValueError, KeyError):
        sz = IssueSize.M

    # Size → estimate hours mapping
    size_hours = {"XS": 0.5, "S": 2.0, "M": 4.0, "L": 12.0, "XL": 24.0}
    estimate = size_hours.get(sz.value, 4.0)

    now = utcnow()
    metadata = IssueMetadata(
        priority=prio,
        size=sz,
        estimate_hours=estimate,
        start_date=now.strftime("%Y-%m-%d"),
        target_date=now.strftime("%Y-%m-%d"),
        labels=["ai-generated", "feature"],
    )

    rec = IssueRecommendation(
        session_id=UUID(session_id) if session_id else UUID(int=0),
        original_input=title[:500],
        original_context=user_story,
        title=title[:256],
        user_story=user_story,
        ui_ux_description=ui_ux_description,
        functional_requirements=reqs,
        technical_notes=technical_notes,
        metadata=metadata,
    )

    return json.dumps(
        {
            "action_type": "issue_create",
            "recommendation": rec.model_dump(mode="json"),
        }
    )


# ── Tool: Update Task Status ──────────────────────────────────────────────


@tool(
    name="update_task_status",
    description=(
        "Update a task's status (e.g. move to 'In Progress', 'Done'). "
        "Use when the user asks to change a task's status column."
    ),
)
async def update_task_status(
    task_reference: str,
    target_status: str,
) -> str:
    """Update a task's status.

    Args:
        task_reference: Name or ID of the task to update.
        target_status: Target status column (e.g. "In Progress", "Done").

    Returns:
        JSON string with the status update data.
    """
    logger.info(
        "Tool update_task_status: ref=%s target=%s",
        task_reference,
        target_status,
    )

    return json.dumps(
        {
            "action_type": "status_update",
            "task_reference": task_reference,
            "target_status": target_status,
        }
    )


# ── Tool: Analyze Transcript ──────────────────────────────────────────────


@tool(
    name="analyze_transcript",
    description=(
        "Analyze meeting transcript or notes to extract actionable items, "
        "feature requests, and requirements. Use when the user uploads or "
        "pastes meeting notes."
    ),
)
async def analyze_transcript(
    transcript_content: str,
) -> str:
    """Analyze a meeting transcript.

    Args:
        transcript_content: The transcript text to analyze.

    Returns:
        JSON string with extracted items.
    """
    runtime = get_runtime_context()
    project_name = runtime.get("project_name", "Unknown")
    logger.info("Tool analyze_transcript invoked, length=%d", len(transcript_content))

    return json.dumps(
        {
            "action_type": "issue_create",
            "source": "transcript",
            "transcript_length": len(transcript_content),
            "project_name": project_name,
        }
    )


# ── Tool: Ask Clarifying Question ─────────────────────────────────────────


@tool(
    name="ask_clarifying_question",
    description=(
        "Ask the user a clarifying question when their intent is ambiguous. "
        "Use this instead of guessing which action to take."
    ),
)
async def ask_clarifying_question(
    question: str,
) -> str:
    """Ask the user for clarification.

    Args:
        question: The clarifying question to ask.

    Returns:
        JSON string with the question.
    """
    logger.debug("Tool ask_clarifying_question: %s", question)
    return json.dumps(
        {
            "action_type": "clarification",
            "question": question,
        }
    )


# ── Tool: Get Project Context ──────────────────────────────────────────────


@tool(
    name="get_project_context",
    description=(
        "Get information about the current project including name, columns, "
        "and recent activity. Use when you need project details to give a "
        "better response."
    ),
)
async def get_project_context() -> str:
    """Retrieve current project context.

    Returns:
        JSON string with project metadata.
    """
    runtime = get_runtime_context()
    project_name = runtime.get("project_name", "Unknown")
    project_id = runtime.get("project_id", "")
    logger.debug("Tool get_project_context for project=%s", project_name)

    return json.dumps(
        {
            "project_name": project_name,
            "project_id": project_id,
        }
    )


# ── Tool Registry ─────────────────────────────────────────────────────────

ALL_TOOLS = [
    create_task_proposal,
    create_issue_recommendation,
    update_task_status,
    analyze_transcript,
    ask_clarifying_question,
    get_project_context,
]
"""Flat list of all agent tools — passed to ``Agent(tools=ALL_TOOLS)``."""
