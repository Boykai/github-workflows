"""App management API endpoints — CRUD and lifecycle for Solune applications."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from src.api.auth import get_session_dep
from src.dependencies import get_github_service
from src.logging_utils import get_logger
from src.middleware.rate_limit import limiter
from src.models.app import (
    App,
    AppAssetInventory,
    AppCreate,
    AppStatus,
    AppStatusResponse,
    AppUpdate,
    DeleteAppResult,
    RepoType,
)
from src.models.user import UserSession
from src.services.activity_logger import log_event
from src.services.app_service import (
    create_app,
    delete_app,
    get_app,
    get_app_assets,
    get_app_status,
    list_apps,
    start_app,
    stop_app,
    update_app,
)
from src.services.database import get_db

logger = get_logger(__name__)

router = APIRouter()

_SessionDep = Annotated[UserSession, Depends(get_session_dep)]


@router.get("/owners")
async def list_owners_endpoint(
    request: Request,
    session: _SessionDep,
) -> list[dict]:
    """List accounts where the authenticated user can create repositories."""
    github_service = get_github_service(request)
    return await github_service.list_available_owners(session.access_token)


@router.get("")
async def list_apps_endpoint(
    _session: _SessionDep,
    status: Annotated[AppStatus | None, Query(description="Filter by app status")] = None,
    limit: Annotated[int | None, Query(ge=1, le=100, description="Items per page")] = None,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
) -> list[App] | dict:
    """List all managed applications."""
    db = get_db()
    apps = await list_apps(db, status_filter=status)

    if limit is not None or cursor is not None:
        from src.services.pagination import apply_pagination

        try:
            result = apply_pagination(
                apps, limit=limit or 25, cursor=cursor, key_fn=lambda a: a.name
            )
        except ValueError as exc:
            from src.exceptions import ValidationError

            raise ValidationError(str(exc)) from exc
        return result.model_dump()

    return apps


@router.post("", response_model=App, status_code=201)
@limiter.limit("10/minute")
async def create_app_endpoint(
    request: Request,
    payload: AppCreate,
    session: _SessionDep,
) -> App:
    """Create a new application with directory scaffolding on the target branch."""
    db = get_db()
    github_service = get_github_service(request)
    app = await create_app(
        db,
        payload,
        access_token=session.access_token,
        github_service=github_service,
    )

    # If a pipeline was selected and a project context exists, launch the pipeline.
    # Route based on repo_type: same-repo uses the user-supplied project_id;
    # new-repo and external-repo use the app's own github_project_id.
    if app.repo_type == RepoType.SAME_REPO:
        launch_project_id = payload.project_id
    else:
        launch_project_id = app.github_project_id
    if payload.pipeline_id and launch_project_id:
        try:
            from src.api.pipelines import execute_pipeline_launch

            # For non-same-repo apps the pipeline config lives under its
            # original project, not the new repo's project.  Look it up so
            # execute_pipeline_launch can find the config while still routing
            # issues to the target project.
            pipeline_project_id: str | None = None
            if app.repo_type != RepoType.SAME_REPO:
                cursor = await db.execute(
                    "SELECT project_id FROM pipeline_configs WHERE id = ?",
                    (payload.pipeline_id,),
                )
                row = await cursor.fetchone()
                if row:
                    pipeline_project_id = row["project_id"]

            # For new-repo / external-repo apps the target project is
            # empty so resolve_repository would fall back to the default
            # repo.  Pass the known target repo directly.
            target_repo: tuple[str, str] | None = None
            if app.repo_type != RepoType.SAME_REPO and app.github_repo_url:
                from src.utils import parse_github_url

                target_repo = parse_github_url(app.github_repo_url)

            result = await execute_pipeline_launch(
                project_id=launch_project_id,
                issue_description=payload.description or app.description or app.display_name,
                pipeline_id=payload.pipeline_id,
                session=session,
                pipeline_project_id=pipeline_project_id,
                target_repo=target_repo,
            )
            if result.success and result.issue_number and result.issue_url:
                await db.execute(
                    "UPDATE apps SET parent_issue_number = ?, parent_issue_url = ? WHERE name = ?",
                    (result.issue_number, result.issue_url, app.name),
                )
                await db.commit()
                app = app.model_copy(
                    update={
                        "parent_issue_number": result.issue_number,
                        "parent_issue_url": result.issue_url,
                    }
                )
        except Exception as exc:
            logger.warning("Pipeline launch failed for app '%s': %s", app.name, exc)
            warnings = list(app.warnings or [])
            warnings.append(f"Pipeline launch failed: {exc}")
            app = app.model_copy(update={"warnings": warnings})
    elif payload.pipeline_id and not launch_project_id:
        logger.warning(
            "Pipeline launch skipped for app '%s' (repo_type=%s): no project_id available",
            app.name,
            app.repo_type,
        )

    await log_event(
        db,
        event_type="app_crud",
        entity_type="app",
        entity_id=app.name,
        project_id=payload.project_id or "",
        actor=session.github_username,
        action="created",
        summary=f"App '{app.display_name}' created",
        detail={"entity_name": app.display_name},
    )

    return app


@router.get("/{app_name}", response_model=App)
async def get_app_endpoint(
    app_name: str,
    _session: _SessionDep,
) -> App:
    """Get details of a specific application."""
    db = get_db()
    return await get_app(db, app_name)


@router.put("/{app_name}", response_model=App)
async def update_app_endpoint(
    app_name: str,
    payload: AppUpdate,
    _session: _SessionDep,
) -> App:
    """Update application metadata."""
    db = get_db()
    result = await update_app(db, app_name, payload)
    await log_event(
        db,
        event_type="app_crud",
        entity_type="app",
        entity_id=app_name,
        project_id=result.github_project_id or "",
        actor=_session.github_username,
        action="updated",
        summary=f"App '{app_name}' updated",
        detail={"entity_name": app_name},
    )
    return result


@router.get("/{app_name}/assets", response_model=AppAssetInventory)
async def get_app_assets_endpoint(
    request: Request,
    app_name: str,
    session: _SessionDep,
) -> AppAssetInventory:
    """Get an inventory of all GitHub assets associated with an app."""
    db = get_db()
    github_service = get_github_service(request)
    return await get_app_assets(
        db,
        app_name,
        access_token=session.access_token,
        github_service=github_service,
    )


@router.delete("/{app_name}")
@limiter.limit("10/minute")
async def delete_app_endpoint(
    request: Request,
    app_name: str,
    session: _SessionDep,
    response: Response,
    force: Annotated[bool, Query(description="Perform full asset cleanup when True")] = False,
) -> DeleteAppResult | None:
    """Delete an application (must be stopped first).

    When ``force=true``, all related GitHub assets (issues, branches,
    project, and repository) are deleted before removing the DB record.
    Returns 204 for non-force delete, 200 with ``DeleteAppResult`` for force.
    """
    db = get_db()
    github_service = get_github_service(request)
    existing = await get_app(db, app_name)
    result = await delete_app(
        db,
        app_name,
        access_token=session.access_token,
        github_service=github_service,
        force=force,
    )
    await log_event(
        db,
        event_type="app_crud",
        entity_type="app",
        entity_id=app_name,
        project_id=existing.github_project_id or "",
        actor=session.github_username,
        action="deleted",
        summary=f"App '{app_name}' deleted",
        detail={"entity_name": app_name, "force": force},
    )
    if not force:
        response.status_code = 204
    return result


@router.post("/{app_name}/start", response_model=AppStatusResponse)
@limiter.limit("10/minute")
async def start_app_endpoint(
    request: Request,
    app_name: str,
    _session: _SessionDep,
) -> AppStatusResponse:
    """Start an application."""
    db = get_db()
    return await start_app(db, app_name)


@router.post("/{app_name}/stop", response_model=AppStatusResponse)
@limiter.limit("10/minute")
async def stop_app_endpoint(
    request: Request,
    app_name: str,
    _session: _SessionDep,
) -> AppStatusResponse:
    """Stop a running application."""
    db = get_db()
    return await stop_app(db, app_name)


@router.get("/{app_name}/status", response_model=AppStatusResponse)
async def get_app_status_endpoint(
    app_name: str,
    _session: _SessionDep,
) -> AppStatusResponse:
    """Get the current status of an application."""
    db = get_db()
    return await get_app_status(db, app_name)
