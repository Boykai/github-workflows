"""Agent function tools for the Microsoft Agent Framework.

Each tool corresponds to a capability the agent can invoke:
- create_task_proposal — generate a structured task from a description
- create_issue_recommendation — generate a GitHub issue from a feature request
- update_task_status — change a task's status on the project board
- analyze_transcript — extract action items from a meeting transcript
- ask_clarifying_question — request more information from the user
- get_project_context — retrieve the active project's tasks and columns
- get_pipeline_list — list available pipelines for the project

Runtime context (project_id, github_token, session_id) is injected via
``tool_context`` keyword arguments — invisible to the LLM schema.
"""

from __future__ import annotations

import json
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)

# ── Tool result helpers ──────────────────────────────────────────────────


def _tool_result(action_type: str, data: dict[str, Any], message: str) -> dict[str, Any]:
    """Build a standard tool result dict consumed by ChatAgentService."""
    return {
        "action_type": action_type,
        "action_data": data,
        "message": message,
    }


# ── Function tools ───────────────────────────────────────────────────────
#
# These are plain async functions.  The ChatAgentService wraps them as
# agent-framework ``FunctionTool`` instances at agent build time, passing
# runtime context (project_id, github_token, session_id, ai_service) via
# the ``tool_context`` dict.


async def create_task_proposal(
    title: str,
    description: str,
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a structured task proposal for the project board.

    Args:
        title: Short, action-oriented task title (max 100 chars).
        description: Detailed description with acceptance criteria.
        tool_context: Injected runtime context (invisible to LLM).

    Returns:
        Dict with action_type, action_data, and a user-facing message.
    """
    ctx = tool_context or {}
    project_name = ctx.get("project_name", "Unknown Project")
    pipeline_id = ctx.get("pipeline_id")

    # When ai_service is available and we want AI enhancement, delegate
    ai_service = ctx.get("ai_service")
    github_token = ctx.get("github_token")

    if ai_service and title and not description:
        try:
            generated = await ai_service.generate_task_from_description(
                user_input=title,
                project_name=project_name,
                github_token=github_token,
            )
            title = generated.title
            description = generated.description
        except Exception as exc:
            logger.warning("AI task generation fallback: %s", exc)
            description = title  # Fallback: use title as description

    # Enforce max title length
    if len(title) > 100:
        title = title[:97] + "..."

    return _tool_result(
        action_type="task_create",
        data={
            "proposed_title": title,
            "proposed_description": description,
            "pipeline_id": pipeline_id,
        },
        message=(
            f"I've created a task proposal:\n\n**{title}**\n\n"
            f"{description[:200]}{'...' if len(description) > 200 else ''}"
            "\n\nClick **Confirm** to create this task."
        ),
    )


async def create_issue_recommendation(
    title: str,
    user_story: str,
    functional_requirements: list[str] | None = None,
    ui_ux_description: str | None = None,
    technical_notes: str | None = None,
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a GitHub issue recommendation from a feature request.

    Args:
        title: Issue title (max 256 chars).
        user_story: User story in "As a ... I want ... so that ..." format.
        functional_requirements: List of "System MUST/SHOULD" requirements.
        ui_ux_description: UI/UX design guidance.
        technical_notes: Implementation hints.
        tool_context: Injected runtime context.

    Returns:
        Dict with action_type, action_data, and a user-facing message.
    """
    ctx = tool_context or {}
    pipeline_id = ctx.get("pipeline_id")
    file_urls = ctx.get("file_urls", [])

    requirements = functional_requirements or []
    ui_desc = ui_ux_description or "No UI/UX description provided."
    tech_notes = technical_notes or ""

    if len(title) > 256:
        title = title[:253] + "..."

    requirements_preview = "\n".join(f"- {req}" for req in requirements)
    tech_preview = ""
    if tech_notes:
        tech_preview = (
            f"\n\n**Technical Notes:**\n{tech_notes[:300]}{'...' if len(tech_notes) > 300 else ''}"
        )

    return _tool_result(
        action_type="issue_create",
        data={
            "proposed_title": title,
            "user_story": user_story,
            "ui_ux_description": ui_desc,
            "functional_requirements": requirements,
            "technical_notes": tech_notes,
            "pipeline_id": pipeline_id,
            "file_urls": file_urls,
        },
        message=(
            f"I've generated a GitHub issue recommendation:\n\n"
            f"**{title}**\n\n"
            f"**User Story:**\n{user_story}\n\n"
            f"**UI/UX Description:**\n{ui_desc}\n\n"
            f"**Functional Requirements:**\n{requirements_preview}"
            f"{tech_preview}\n\n"
            f"Click **Confirm** to create this issue in GitHub, or **Reject** to discard."
        ),
    )


async def update_task_status(
    task_reference: str,
    target_status: str,
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update a task's status on the project board.

    Args:
        task_reference: Task title or description to search for.
        target_status: The status to move the task to (e.g., "Done", "In Progress").
        tool_context: Injected runtime context.

    Returns:
        Dict with action_type, action_data, and a user-facing message.
    """
    ctx = tool_context or {}
    current_tasks = ctx.get("current_tasks", [])
    cached_projects = ctx.get("cached_projects")
    selected_project_id = ctx.get("project_id", "")

    # Use the existing identify_target_task utility
    ai_service = ctx.get("ai_service")
    target_task = None
    if ai_service:
        target_task = ai_service.identify_target_task(
            task_reference=task_reference,
            available_tasks=current_tasks,
        )

    if not target_task:
        return _tool_result(
            action_type="",
            data={},
            message=(
                f"I couldn't find a task matching '{task_reference}'. "
                "Please try again with a more specific task name."
            ),
        )

    # Resolve status option and field IDs
    status_option_id = ""
    status_field_id = ""
    resolved_status = target_status
    if cached_projects:
        for p in cached_projects:
            if p.project_id == selected_project_id:
                for col in p.status_columns:
                    if col.name.lower() == target_status.lower():
                        status_option_id = col.option_id
                        status_field_id = col.field_id
                        resolved_status = col.name
                        break
                break

    return _tool_result(
        action_type="status_update",
        data={
            "task_id": target_task.github_item_id,
            "task_title": target_task.title,
            "current_status": target_task.status,
            "target_status": resolved_status,
            "status_option_id": status_option_id,
            "status_field_id": status_field_id,
        },
        message=(
            f"I'll update the status of **{target_task.title}** "
            f"from **{target_task.status}** to **{resolved_status}**.\n\n"
            "Click confirm to apply this change."
        ),
    )


async def analyze_transcript(
    transcript_content: str,
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Analyse a meeting transcript and extract structured requirements.

    Args:
        transcript_content: Raw transcript text to analyse.
        tool_context: Injected runtime context.

    Returns:
        Dict with action_type, action_data, and a user-facing message.
    """
    ctx = tool_context or {}
    ai_service = ctx.get("ai_service")
    github_token = ctx.get("github_token")
    project_name = ctx.get("project_name", "Unknown Project")
    session_id = ctx.get("session_id", "")
    pipeline_id = ctx.get("pipeline_id")
    file_urls = ctx.get("file_urls", [])

    if not ai_service:
        return _tool_result(
            action_type="",
            data={},
            message="Transcript analysis is not available — AI service not configured.",
        )

    try:
        metadata_context = ctx.get("metadata_context")
        recommendation = await ai_service.analyze_transcript(
            transcript_content=transcript_content,
            project_name=project_name,
            session_id=session_id,
            github_token=github_token,
            metadata_context=metadata_context,
        )

        requirements_preview = "\n".join(
            f"- {req}" for req in recommendation.functional_requirements
        )
        tech_preview = ""
        if recommendation.technical_notes:
            tech_preview = (
                f"\n\n**Technical Notes:**\n"
                f"{recommendation.technical_notes[:300]}"
                f"{'...' if len(recommendation.technical_notes) > 300 else ''}"
            )

        return _tool_result(
            action_type="issue_create",
            data={
                "recommendation_id": str(recommendation.recommendation_id),
                "proposed_title": recommendation.title,
                "user_story": recommendation.user_story,
                "original_context": recommendation.original_context,
                "ui_ux_description": recommendation.ui_ux_description,
                "functional_requirements": recommendation.functional_requirements,
                "technical_notes": recommendation.technical_notes,
                "file_urls": file_urls,
                "pipeline_id": pipeline_id,
            },
            message=(
                f"I've analysed the uploaded transcript and generated a "
                f"GitHub issue recommendation:\n\n"
                f"**{recommendation.title}**\n\n"
                f"**User Story:**\n{recommendation.user_story}\n\n"
                f"**UI/UX Description:**\n{recommendation.ui_ux_description}\n\n"
                f"**Functional Requirements:**\n{requirements_preview}"
                f"{tech_preview}\n\n"
                f"Click **Confirm** to create this issue in GitHub, or "
                f"**Reject** to discard."
            ),
        )
    except Exception as exc:
        logger.error("Transcript analysis failed: %s", exc, exc_info=True)
        return _tool_result(
            action_type="",
            data={},
            message=(
                f"I couldn't extract requirements from the transcript "
                f"({type(exc).__name__}). Please try again or paste the "
                f"transcript content directly."
            ),
        )


async def ask_clarifying_question(
    question: str,
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ask the user a clarifying question before taking action.

    Args:
        question: The question to ask.
        tool_context: Injected runtime context.

    Returns:
        Dict with the question as the message (no action_type).
    """
    return _tool_result(
        action_type="",
        data={},
        message=question,
    )


async def get_project_context(
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Retrieve the current project's tasks, columns, and metadata.

    Args:
        tool_context: Injected runtime context.

    Returns:
        Dict with project context information.
    """
    ctx = tool_context or {}
    project_name = ctx.get("project_name", "Unknown Project")
    project_columns = ctx.get("project_columns", [])
    current_tasks = ctx.get("current_tasks", [])

    task_summaries = [
        {
            "title": getattr(task, "title", str(task)),
            "status": getattr(task, "status", "unknown"),
        }
        for task in current_tasks[:20]
    ]

    context_info = {
        "project_name": project_name,
        "status_columns": project_columns,
        "task_count": len(current_tasks),
        "recent_tasks": task_summaries,
    }

    return _tool_result(
        action_type="",
        data=context_info,
        message=json.dumps(context_info, indent=2),
    )


async def get_pipeline_list(
    *,
    tool_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """List available pipelines for the current project.

    Args:
        tool_context: Injected runtime context.

    Returns:
        Dict with pipeline information.
    """
    ctx = tool_context or {}
    project_id = ctx.get("project_id", "")

    try:
        from src.services.database import get_db
        from src.services.pipelines.service import PipelineService

        db = get_db()
        pipeline_svc = PipelineService(db)
        pipelines = await pipeline_svc.list_pipelines(project_id)

        pipeline_summaries = [
            {"id": p.pipeline_id, "name": p.name, "description": getattr(p, "description", "")}
            for p in pipelines
        ]

        return _tool_result(
            action_type="",
            data={"pipelines": pipeline_summaries},
            message=json.dumps(pipeline_summaries, indent=2),
        )
    except Exception as exc:
        logger.warning("Failed to list pipelines: %s", exc)
        return _tool_result(
            action_type="",
            data={"pipelines": []},
            message="No pipelines available or pipeline service unavailable.",
        )


# ── Tool registry ────────────────────────────────────────────────────────

AGENT_TOOLS = [
    create_task_proposal,
    create_issue_recommendation,
    update_task_status,
    analyze_transcript,
    ask_clarifying_question,
    get_project_context,
    get_pipeline_list,
]
"""List of all tool functions to register with the agent."""
