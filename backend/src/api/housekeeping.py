"""Housekeeping API router — templates, tasks, triggers, and history."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from src.api.auth import get_session_dep
from src.models.housekeeping import (
    EvaluateTriggersRequest,
    EvaluateTriggersResponse,
    HousekeepingTask,
    HousekeepingTaskCreate,
    HousekeepingTaskUpdate,
    IssueTemplate,
    IssueTemplateCreate,
    IssueTemplateUpdate,
    TaskListResponse,
    TaskToggleRequest,
    TemplateListResponse,
    TriggerHistoryResponse,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.housekeeping.service import HousekeepingService

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> HousekeepingService:
    """Get a HousekeepingService instance."""
    return HousekeepingService(get_db())


# ── Templates ───────────────────────────────────────────────────────────


@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    session: Annotated[UserSession, Depends(get_session_dep)],
    category: str | None = Query(None, description="Filter by 'built-in' or 'custom'"),
) -> TemplateListResponse:
    """List all issue templates."""
    svc = _get_service()
    templates = await svc.list_templates(category=category)
    return TemplateListResponse(templates=templates)


@router.get("/templates/{template_id}", response_model=IssueTemplate)
async def get_template(
    template_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> IssueTemplate:
    """Get a single issue template."""
    svc = _get_service()
    tmpl = await svc.get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return tmpl


@router.post("/templates", response_model=IssueTemplate, status_code=status.HTTP_201_CREATED)
async def create_template(
    body: IssueTemplateCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> IssueTemplate:
    """Create a new custom issue template."""
    svc = _get_service()
    try:
        return await svc.create_template(
            name=body.name,
            title_pattern=body.title_pattern,
            body_content=body.body_content,
        )
    except Exception as e:
        logger.exception("Failed to create template")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to create template",
        ) from e


@router.put("/templates/{template_id}", response_model=IssueTemplate)
async def update_template(
    template_id: str,
    body: IssueTemplateUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> IssueTemplate:
    """Update an existing template."""
    svc = _get_service()
    try:
        result = await svc.update_template(
            template_id,
            **body.model_dump(exclude_unset=True),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify built-in templates",
        ) from e

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return result


@router.delete("/templates/{template_id}", response_model=None)
async def delete_template(
    template_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    force: bool = Query(False, description="Force delete even if referenced by tasks"),
) -> dict | JSONResponse:
    """Delete a template."""
    svc = _get_service()
    result = await svc.delete_template(template_id, force=force)

    if result.get("error") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    if result.get("error") == "built_in":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete built-in templates",
        )
    if result.get("error") == "in_use":
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Template is referenced by active housekeeping tasks",
                "details": {
                    "referencing_tasks": result["referencing_tasks"],
                },
            },
        )
    return result


@router.post(
    "/templates/{template_id}/duplicate",
    response_model=IssueTemplate,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_template(
    template_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> IssueTemplate:
    """Duplicate a template as a custom copy."""
    svc = _get_service()
    result = await svc.duplicate_template(template_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return result


# ── Tasks ───────────────────────────────────────────────────────────────


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    session: Annotated[UserSession, Depends(get_session_dep)],
    project_id: str = Query(..., description="GitHub Project node ID"),
    enabled: bool | None = Query(None, description="Filter by enabled/disabled"),
) -> TaskListResponse:
    """List housekeeping tasks for a project."""
    svc = _get_service()
    tasks = await svc.list_tasks(project_id, enabled=enabled)
    return TaskListResponse(tasks=tasks)


@router.get("/tasks/{task_id}", response_model=HousekeepingTask)
async def get_task(
    task_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> HousekeepingTask:
    """Get a single housekeeping task."""
    svc = _get_service()
    task = await svc.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Housekeeping task not found",
        )
    return task


@router.post("/tasks", response_model=HousekeepingTask, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: HousekeepingTaskCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> HousekeepingTask:
    """Create a new housekeeping task."""
    svc = _get_service()
    try:
        return await svc.create_task(
            name=body.name,
            template_id=body.template_id,
            trigger_type=body.trigger_type,
            trigger_value=body.trigger_value,
            project_id=body.project_id,
            description=body.description,
            sub_issue_config=body.sub_issue_config,
            cooldown_minutes=body.cooldown_minutes,
            current_issue_count=body.current_issue_count,
        )
    except ValueError as e:
        logger.warning("Invalid task creation request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid task configuration",
        ) from e


@router.put("/tasks/{task_id}", response_model=HousekeepingTask)
async def update_task(
    task_id: str,
    body: HousekeepingTaskUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> HousekeepingTask:
    """Update a housekeeping task."""
    svc = _get_service()
    try:
        result = await svc.update_task(task_id, **body.model_dump(exclude_unset=True))
    except ValueError as e:
        logger.warning("Invalid task update request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid task configuration",
        ) from e

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Housekeeping task not found",
        )
    return result


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Delete a housekeeping task and its history."""
    svc = _get_service()
    deleted = await svc.delete_task(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Housekeeping task not found",
        )
    return {"deleted": True}


@router.patch("/tasks/{task_id}/toggle", response_model=HousekeepingTask)
async def toggle_task(
    task_id: str,
    body: TaskToggleRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> HousekeepingTask:
    """Enable or disable a housekeeping task."""
    svc = _get_service()
    result = await svc.toggle_task(task_id, body.enabled)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Housekeeping task not found",
        )
    return result


# ── Manual Run ──────────────────────────────────────────────────────────


@router.post("/tasks/{task_id}/run", response_model=None)
async def run_task(
    task_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    force: bool = Query(False, description="Skip cooldown warning"),
) -> dict | JSONResponse:
    """Manually trigger a housekeeping task."""
    svc = _get_service()
    result = await svc.run_task(task_id, force=force)

    if result.get("error") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Housekeeping task not found",
        )
    if result.get("cooldown"):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "Task was triggered recently",
                "details": {
                    "last_triggered_at": result["last_triggered_at"],
                    "cooldown_remaining_seconds": result["cooldown_remaining_seconds"],
                    "message": "Use ?force=true to override cooldown",
                },
            },
        )

    return result


# ── Trigger Evaluation ──────────────────────────────────────────────────


@router.post("/evaluate-triggers", response_model=EvaluateTriggersResponse)
async def evaluate_triggers(
    body: EvaluateTriggersRequest,
) -> EvaluateTriggersResponse:
    """
    Evaluate and execute due time-based triggers for a project.

    Called by the GitHub Actions cron workflow. Does not require user session.
    """
    svc = _get_service()
    return await svc.evaluate_triggers(body.project_id)


# ── Trigger History ─────────────────────────────────────────────────────


@router.get("/tasks/{task_id}/history", response_model=TriggerHistoryResponse)
async def get_task_history(
    task_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by success/failure"
    ),
) -> TriggerHistoryResponse:
    """Get trigger history for a housekeeping task."""
    svc = _get_service()
    events, total = await svc.get_task_history(
        task_id, limit=limit, offset=offset, status=status_filter
    )
    return TriggerHistoryResponse(
        history=events,
        total=total,
        limit=limit,
        offset=offset,
    )
