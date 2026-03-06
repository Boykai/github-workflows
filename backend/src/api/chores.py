"""Chores API endpoints — CRUD, trigger, and chat for recurring maintenance tasks."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_session_dep
from src.models.chores import (
    Chore,
    ChoreChatMessage,
    ChoreChatResponse,
    ChoreCreate,
    ChoreTemplate,
    ChoreTriggerResult,
    ChoreUpdate,
    EvaluateChoreTriggersRequest,
    EvaluateChoreTriggersResponse,
)
from src.models.user import UserSession
from src.services.chores.service import ChoresService
from src.services.chores.template_builder import (
    build_template,
    commit_template_to_repo,
)
from src.services.database import get_db
from src.services.github_projects import github_projects_service
from src.utils import resolve_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> ChoresService:
    """Instantiate ChoresService with the current DB connection."""
    return ChoresService(get_db())


# ── Templates (from repo) ──


@router.get("/{project_id}/templates", response_model=list[ChoreTemplate])
async def list_templates(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[ChoreTemplate]:
    """List available chore templates from .github/ISSUE_TEMPLATE/ in the repo."""
    import re as _re

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception:
        logger.warning(
            "Failed to resolve repository for project %s when listing chore templates",
            project_id,
            exc_info=True,
        )
        return []

    entries = await github_projects_service.get_directory_contents(
        session.access_token, owner, repo, ".github/ISSUE_TEMPLATE"
    )
    chore_files = [
        e
        for e in entries
        if e.get("name", "").startswith("chore-") and e.get("name", "").endswith(".md")
    ]

    templates: list[ChoreTemplate] = []
    for entry in chore_files:
        file_data = await github_projects_service.get_file_content(
            session.access_token, owner, repo, entry["path"]
        )
        if not file_data:
            continue
        raw = file_data["content"]

        # Parse YAML front matter
        tpl_name = entry["name"].replace("chore-", "").replace(".md", "").replace("-", " ").title()
        about = ""
        fm_match = _re.match(r"^---\n(.*?)\n---", raw, _re.DOTALL)
        if fm_match:
            for line in fm_match.group(1).splitlines():
                if line.startswith("name:"):
                    tpl_name = line.split(":", 1)[1].strip().strip("'\"")
                elif line.startswith("about:"):
                    about = line.split(":", 1)[1].strip().strip("'\"")

        templates.append(
            ChoreTemplate(
                name=tpl_name,
                about=about,
                path=entry["path"],
                content=raw,
            )
        )

    return templates


# ── List ──


@router.get("/{project_id}", response_model=list[Chore])
async def list_chores(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[Chore]:
    """List all chores for a project."""
    service = _get_service()
    return await service.list_chores(project_id)


# ── Create ──


@router.post("/{project_id}", response_model=Chore, status_code=201)
async def create_chore(
    project_id: str,
    body: ChoreCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> Chore:
    """Create a new chore (generates template, commits via PR, creates tracking issue)."""
    service = _get_service()

    # Build the full template content
    template_content = build_template(body.name, body.template_content)

    # Resolve repository for the project
    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error(
            "Failed to resolve repository for project %s: %s", project_id, exc, exc_info=True
        )
        raise HTTPException(
            status_code=400,
            detail="Could not resolve repository for this project",
        ) from exc

    # Commit template to repo via branch + PR + tracking issue
    try:
        result = await commit_template_to_repo(
            github_service=github_projects_service,
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            project_id=project_id,
            name=body.name,
            template_content=template_content,
        )
    except RuntimeError as exc:
        logger.error("Failed to commit template to repository: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to commit template to repository",
        ) from exc

    # Create the chore record in the database
    try:
        chore = await service.create_chore(
            project_id,
            body,
            template_path=result["template_path"],
        )
    except ValueError as exc:
        logger.warning("Invalid chore creation request: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid chore configuration") from exc

    # Update chore with PR and tracking issue info

    await service.update_chore_fields(
        chore.id,
        pr_number=result.get("pr_number"),
        pr_url=result.get("pr_url"),
        tracking_issue_number=result.get("tracking_issue_number"),
        template_content=template_content,
    )

    # Re-fetch to include updated fields
    updated = await service.get_chore(chore.id)
    if updated is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve created chore")
    return updated


# ── Update ──


@router.patch("/{project_id}/{chore_id}", response_model=Chore)
async def update_chore(
    project_id: str,
    chore_id: str,
    body: ChoreUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> Chore:
    """Update a chore (schedule, status)."""
    service = _get_service()

    # Verify the chore exists and belongs to this project
    existing = await service.get_chore(chore_id)
    if existing is None or existing.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chore not found")

    try:
        updated = await service.update_chore(chore_id, body)
    except ValueError as exc:
        logger.warning("Invalid chore update request: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid chore configuration") from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Chore not found after update")
    return updated


# ── Delete ──


@router.delete("/{project_id}/{chore_id}")
async def delete_chore(
    project_id: str,
    chore_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Remove a chore, closing any open associated issue."""
    service = _get_service()

    # Verify the chore exists and belongs to this project
    existing = await service.get_chore(chore_id)
    if existing is None or existing.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chore not found")

    closed_issue_number = None

    # Close the associated GitHub issue if one is open
    if existing.current_issue_number is not None:
        try:
            owner, repo = await resolve_repository(session.access_token, project_id)
            await github_projects_service.update_issue_state(
                session.access_token,
                owner,
                repo,
                existing.current_issue_number,
                state="closed",
                state_reason="not_planned",
            )
            closed_issue_number = existing.current_issue_number
        except Exception:
            logger.warning(
                "Failed to close issue #%s when deleting chore %s",
                existing.current_issue_number,
                chore_id,
            )

    await service.delete_chore(chore_id)

    return {"deleted": True, "closed_issue_number": closed_issue_number}


# ── Manual Trigger ──


@router.post("/{project_id}/{chore_id}/trigger", response_model=ChoreTriggerResult)
async def trigger_chore(
    project_id: str,
    chore_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChoreTriggerResult:
    """Manually trigger a chore — creates a GitHub issue and runs agent pipeline."""
    service = _get_service()

    chore = await service.get_chore(chore_id)
    if chore is None or chore.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chore not found")

    owner, repo = await resolve_repository(session.access_token, project_id)

    result = await service.trigger_chore(
        chore,
        github_service=github_projects_service,
        access_token=session.access_token,
        owner=owner,
        repo=repo,
        project_id=project_id,
        github_user_id=session.github_user_id,
    )

    if not result.triggered:
        raise HTTPException(status_code=409, detail=result.skip_reason)

    return result


# ── Chat ──


@router.post("/{project_id}/chat", response_model=ChoreChatResponse)
async def chore_chat(
    project_id: str,
    body: ChoreChatMessage,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChoreChatResponse:
    """Interactive chat for sparse-input template refinement."""
    from src.services.chores.chat import generate_chat_response

    try:
        conversation_id, response, template_ready, template_content = await generate_chat_response(
            body.conversation_id,
            body.content,
            github_token=session.access_token,
        )
    except Exception as exc:
        logger.error("Chat completion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Chat completion failed") from exc

    return ChoreChatResponse(
        message=response,
        conversation_id=conversation_id,
        template_ready=template_ready,
        template_content=template_content,
    )


# ── Evaluate Triggers (Cron) ──


@router.post("/evaluate-triggers", response_model=EvaluateChoreTriggersResponse)
async def evaluate_triggers(
    session: Annotated[UserSession, Depends(get_session_dep)],
    body: EvaluateChoreTriggersRequest | None = None,
) -> EvaluateChoreTriggersResponse:
    """Evaluate all active chores for trigger conditions."""
    service = _get_service()

    project_id = body.project_id if body else None
    if not project_id:
        logger.warning("evaluate-triggers called without project_id; returning empty result")
        return EvaluateChoreTriggersResponse(evaluated=0, triggered=0, skipped=0, results=[])

    # Resolve repository for the specified project
    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception:
        logger.warning("Could not resolve repository for project %s", project_id)
        return EvaluateChoreTriggersResponse(evaluated=0, triggered=0, skipped=0, results=[])

    result = await service.evaluate_triggers(
        github_service=github_projects_service,
        access_token=session.access_token,
        owner=owner,
        repo=repo,
    )
    return EvaluateChoreTriggersResponse(**result)
