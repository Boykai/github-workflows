"""Chores API endpoints — CRUD, trigger, and chat for recurring maintenance tasks."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_session_dep
from src.exceptions import (
    AppException,
    GitHubAPIError,
    NotFoundError,
    ValidationError,
)
from src.logging_utils import get_logger, handle_service_error
from src.models.chores import (
    Chore,
    ChoreChatMessage,
    ChoreChatResponse,
    ChoreCreate,
    ChoreCreateResponse,
    ChoreCreateWithConfirmation,
    ChoreInlineUpdate,
    ChoreInlineUpdateResponse,
    ChoreStatus,
    ChoreTemplate,
    ChoreTriggerResult,
    ChoreUpdate,
    EvaluateChoreTriggersRequest,
    EvaluateChoreTriggersResponse,
    ScheduleType,
    TriggerChoreRequest,
)
from src.models.user import UserSession
from src.services.activity_logger import log_event
from src.services.chores.service import ChoreConflictError, ChoresService
from src.services.chores.template_builder import (
    build_template,
    commit_template_to_repo,
)
from src.services.database import get_db
from src.services.github_projects import github_projects_service
from src.utils import resolve_repository

logger = get_logger(__name__)
router = APIRouter()


def _get_service() -> ChoresService:
    """Instantiate ChoresService with the current DB connection."""
    return ChoresService(get_db())


# ── Seed Presets ──


@router.post("/{project_id}/seed-presets")
async def seed_presets(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Idempotently seed built-in chore presets for a project."""
    # Verify the authenticated user has access to this project
    await resolve_repository(session.access_token, project_id)
    service = _get_service()
    created = await service.seed_presets(project_id)
    return {"created": len(created)}


# ── Evaluate Triggers (Cron) ──


@router.post("/evaluate-triggers", response_model=EvaluateChoreTriggersResponse)
async def evaluate_triggers(
    session: Annotated[UserSession, Depends(get_session_dep)],
    body: EvaluateChoreTriggersRequest | None = None,
) -> EvaluateChoreTriggersResponse:
    """Evaluate all active chores for trigger conditions."""
    service = _get_service()

    project_id = body.project_id if body else None
    parent_issue_count = body.parent_issue_count if body else None
    if not project_id:
        logger.warning("evaluate-triggers called without project_id; returning empty result")
        return EvaluateChoreTriggersResponse(evaluated=0, triggered=0, skipped=0, results=[])

    # Resolve repository for the specified project
    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as e:
        handle_service_error(e, "resolve repository for chore triggers")

    result = await service.evaluate_triggers(
        github_service=github_projects_service,
        access_token=session.access_token,
        owner=owner,
        repo=repo,
        project_id=project_id,
        parent_issue_count=parent_issue_count,
    )
    return EvaluateChoreTriggersResponse(**result)


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


# ── Chore Names (lightweight, unpaginated) ──


@router.get("/{project_id}/chore-names", response_model=list[str])
async def list_chore_names(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[str]:
    """Return ALL chore names for a project — unpaginated and unfiltered.

    This lightweight endpoint supports accurate template membership checks
    without pulling full chore objects or being affected by pagination/filter
    state on the client.
    """
    await resolve_repository(session.access_token, project_id)
    service = _get_service()
    chores = await service.list_chores(project_id)
    return [c.name for c in chores]


# ── List ──


@router.get("/{project_id}")
async def list_chores(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    limit: Annotated[int | None, Query(ge=1, le=100, description="Items per page")] = None,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    status: Annotated[ChoreStatus | None, Query(description="Filter by status")] = None,
    schedule_type: Annotated[
        ScheduleType | Literal["unscheduled"] | None,
        Query(description="Filter by schedule type"),
    ] = None,
    search: Annotated[str | None, Query(description="Search by name or template_path")] = None,
    sort: Annotated[
        Literal["name", "updated_at", "created_at", "attention"] | None,
        Query(description="Sort field"),
    ] = None,
    order: Annotated[Literal["asc", "desc"] | None, Query(description="Sort order")] = None,
) -> list[Chore] | dict:
    """List all chores for a project."""
    await resolve_repository(session.access_token, project_id)
    service = _get_service()
    chores = await service.list_chores(project_id)

    # ── Server-side filtering ──
    if status is not None:
        chores = [c for c in chores if c.status == status]

    if schedule_type is not None:
        if schedule_type == "unscheduled":
            chores = [c for c in chores if c.schedule_type is None]
        else:
            chores = [
                c
                for c in chores
                if c.schedule_type is not None and c.schedule_type == schedule_type
            ]

    if search is not None:
        query = search.strip().lower()
        if query:
            chores = [
                c for c in chores if query in c.name.lower() or query in c.template_path.lower()
            ]

    # ── Server-side sorting ──
    if sort is not None:
        reverse = order == "desc"
        if sort == "name":
            chores.sort(key=lambda c: c.name.lower(), reverse=reverse)
        elif sort == "updated_at":
            chores.sort(key=lambda c: c.updated_at, reverse=reverse)
        elif sort == "created_at":
            chores.sort(key=lambda c: c.created_at, reverse=reverse)
        elif sort == "attention":

            def _attention_score(c: Chore) -> int:
                if c.status == "active" and c.schedule_type is None:
                    return 0
                if c.current_issue_number is not None:
                    return 1
                if c.status == "paused":
                    return 3
                return 2

            chores.sort(key=_attention_score, reverse=reverse)

    if limit is not None or cursor is not None:
        from src.services.pagination import apply_pagination

        try:
            result = apply_pagination(
                chores, limit=limit or 25, cursor=cursor, key_fn=lambda c: c.id
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return result.model_dump()

    return chores


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
        raise ValidationError("Could not resolve repository for this project") from exc

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
        handle_service_error(exc, "commit template to repository", GitHubAPIError)

    # Create the chore record in the database
    try:
        chore = await service.create_chore(
            project_id,
            body,
            template_path=result["template_path"],
        )
    except ValueError as exc:
        logger.warning("Invalid chore creation request: %s", exc)
        raise ValidationError("Invalid chore configuration") from exc

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
        raise AppException("Failed to retrieve created chore", status_code=500)
    await log_event(
        get_db(),
        event_type="chore_crud",
        entity_type="chore",
        entity_id=updated.id,
        project_id=project_id,
        actor=session.github_username,
        action="created",
        summary=f"Chore '{updated.name}' created",
        detail={"entity_name": updated.name},
    )
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
        raise NotFoundError("Chore not found")

    try:
        updated = await service.update_chore(chore_id, body)
    except ValueError as exc:
        logger.warning("Invalid chore update request: %s", exc)
        raise ValidationError("Invalid chore configuration") from exc

    if updated is None:
        raise NotFoundError("Chore not found after update")
    await log_event(
        get_db(),
        event_type="chore_crud",
        entity_type="chore",
        entity_id=chore_id,
        project_id=project_id,
        actor=session.github_username,
        action="updated",
        summary=f"Chore '{updated.name}' updated",
        detail={"entity_name": updated.name},
    )
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
        raise NotFoundError("Chore not found")

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

    await log_event(
        get_db(),
        event_type="chore_crud",
        entity_type="chore",
        entity_id=chore_id,
        project_id=project_id,
        actor=session.github_username,
        action="deleted",
        summary=f"Chore '{existing.name}' deleted",
        detail={"entity_name": existing.name},
    )

    return {"deleted": True, "closed_issue_number": closed_issue_number}


# ── Manual Trigger ──


@router.post("/{project_id}/{chore_id}/trigger", response_model=ChoreTriggerResult)
async def trigger_chore(
    project_id: str,
    chore_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    body: TriggerChoreRequest | None = None,
) -> ChoreTriggerResult:
    """Manually trigger a chore — creates a GitHub issue and runs agent pipeline."""
    service = _get_service()

    chore = await service.get_chore(chore_id)
    if chore is None or chore.project_id != project_id:
        raise NotFoundError("Chore not found")

    owner, repo = await resolve_repository(session.access_token, project_id)

    result = await service.trigger_chore(
        chore,
        github_service=github_projects_service,
        access_token=session.access_token,
        owner=owner,
        repo=repo,
        project_id=project_id,
        parent_issue_count=body.parent_issue_count if body else None,
        github_user_id=session.github_user_id,
    )

    if not result.triggered:
        raise AppException(
            result.skip_reason or "Chore trigger skipped",
            status_code=409,
        )

    await log_event(
        get_db(),
        event_type="chore_trigger",
        entity_type="chore",
        entity_id=chore_id,
        project_id=project_id,
        actor=session.github_username,
        action="triggered",
        summary=f"Chore '{chore.name}' triggered manually",
        detail={"chore_name": chore.name, "trigger_type": "manual"},
    )

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
            ai_enhance=body.ai_enhance,
        )
    except Exception as exc:
        handle_service_error(exc, "complete chat", AppException)

    return ChoreChatResponse(
        message=response,
        conversation_id=conversation_id,
        template_ready=template_ready,
        template_content=template_content,
    )


# ── Inline Update ──


@router.put("/{project_id}/{chore_id}/inline-update", response_model=ChoreInlineUpdateResponse)
async def inline_update_chore(
    project_id: str,
    chore_id: str,
    body: ChoreInlineUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChoreInlineUpdateResponse:
    """Inline update a chore definition and create a PR with changes."""
    service = _get_service()

    existing = await service.get_chore(chore_id)
    if existing is None or existing.project_id != project_id:
        raise NotFoundError("Chore not found")

    needs_pr = body.name is not None or body.template_content is not None
    owner = None
    repo = None
    if needs_pr:
        try:
            owner, repo = await resolve_repository(session.access_token, project_id)
        except Exception as exc:
            logger.warning(
                "Failed to resolve repository for project %s when performing inline chore update",
                project_id,
                exc_info=True,
            )
            raise ValidationError(
                "Could not resolve repository for project; inline update cannot create a pull request."
            ) from exc

    try:
        result = await service.inline_update_chore(
            chore_id,
            body,
            github_service=github_projects_service,
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            project_id=project_id,
        )
    except ChoreConflictError as exc:
        raise AppException(
            str(exc),
            status_code=409,
            details={
                "current_sha": exc.current_sha,
                "current_content": exc.current_content,
            },
        ) from exc
    except ValueError as exc:
        logger.warning("Invalid inline update: %s", exc)
        raise ValidationError(str(exc)) from exc

    return ChoreInlineUpdateResponse(
        chore=result["chore"],
        pr_number=result.get("pr_number"),
        pr_url=result.get("pr_url"),
    )


# ── Create with Auto-Merge ──


@router.post("/{project_id}/create-with-merge", response_model=ChoreCreateResponse, status_code=201)
async def create_chore_with_merge(
    project_id: str,
    body: ChoreCreateWithConfirmation,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChoreCreateResponse:
    """Create a new chore with branch + PR + auto-merge flow."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error(
            "Failed to resolve repository for project %s: %s", project_id, exc, exc_info=True
        )
        raise ValidationError("Could not resolve repository for this project") from exc

    try:
        result = await service.create_chore_with_auto_merge(
            project_id,
            body,
            github_service=github_projects_service,
            access_token=session.access_token,
            owner=owner,
            repo=repo,
        )
    except ValueError as exc:
        logger.warning("Invalid chore creation: %s", exc)
        raise ValidationError(str(exc)) from exc
    except RuntimeError as exc:
        handle_service_error(exc, "create chore", GitHubAPIError)

    return ChoreCreateResponse(**result)
