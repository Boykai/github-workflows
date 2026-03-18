"""App management API endpoints — CRUD and lifecycle for Solune applications."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from src.api.auth import get_session_dep
from src.dependencies import get_github_service
from src.logging_utils import get_logger
from src.models.app import App, AppCreate, AppStatus, AppStatusResponse, AppUpdate
from src.models.user import UserSession
from src.services.app_service import (
    create_app,
    delete_app,
    get_app,
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


@router.get("", response_model=list[App])
async def list_apps_endpoint(
    _session: _SessionDep,
    status: Annotated[AppStatus | None, Query(description="Filter by app status")] = None,
) -> list[App]:
    """List all managed applications."""
    db = get_db()
    return await list_apps(db, status_filter=status)


@router.post("", response_model=App, status_code=201)
async def create_app_endpoint(
    request: Request,
    payload: AppCreate,
    session: _SessionDep,
) -> App:
    """Create a new application with directory scaffolding on the target branch."""
    db = get_db()
    github_service = get_github_service(request)
    return await create_app(
        db,
        payload,
        access_token=session.access_token,
        github_service=github_service,
    )


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
    return await update_app(db, app_name, payload)


@router.delete("/{app_name}", status_code=204)
async def delete_app_endpoint(
    request: Request,
    app_name: str,
    session: _SessionDep,
) -> None:
    """Delete an application (must be stopped first)."""
    db = get_db()
    github_service = get_github_service(request)
    await delete_app(
        db,
        app_name,
        access_token=session.access_token,
        github_service=github_service,
    )


@router.post("/{app_name}/start", response_model=AppStatusResponse)
async def start_app_endpoint(
    app_name: str,
    _session: _SessionDep,
) -> AppStatusResponse:
    """Start an application."""
    db = get_db()
    return await start_app(db, app_name)


@router.post("/{app_name}/stop", response_model=AppStatusResponse)
async def stop_app_endpoint(
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
