"""Pipeline API endpoints — CRUD for Agent Pipeline configurations and model listing."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_session_dep
from src.models.pipeline import (
    AIModel,
    PipelineConfig,
    PipelineConfigCreate,
    PipelineConfigListResponse,
    PipelineConfigUpdate,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.pipelines.service import PipelineService

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> PipelineService:
    """Instantiate PipelineService with the current DB connection."""
    return PipelineService(get_db())


# ── List Models ──
# NOTE: This static route must be defined BEFORE dynamic /{project_id}
# routes to avoid being shadowed by /{project_id}/{pipeline_id}.


@router.get("/models/available", response_model=list[AIModel])
async def list_models(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[AIModel]:
    """List available AI models for agent assignment."""
    return PipelineService.list_models()


# ── List Pipelines ──


@router.get("/{project_id}", response_model=PipelineConfigListResponse)
async def list_pipelines(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    sort: str = "updated_at",
    order: str = "desc",
) -> PipelineConfigListResponse:
    """List all pipeline configurations for a project."""
    service = _get_service()
    return await service.list_pipelines(project_id, sort=sort, order=order)


# ── Create Pipeline ──


@router.post("/{project_id}", response_model=PipelineConfig, status_code=201)
async def create_pipeline(
    project_id: str,
    body: PipelineConfigCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> PipelineConfig:
    """Create a new pipeline configuration."""
    service = _get_service()
    try:
        return await service.create_pipeline(project_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


# ── Get Pipeline ──


@router.get("/{project_id}/{pipeline_id}", response_model=PipelineConfig)
async def get_pipeline(
    project_id: str,
    pipeline_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> PipelineConfig:
    """Get a single pipeline configuration."""
    service = _get_service()
    pipeline = await service.get_pipeline(project_id, pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


# ── Update Pipeline ──


@router.put("/{project_id}/{pipeline_id}", response_model=PipelineConfig)
async def update_pipeline(
    project_id: str,
    pipeline_id: str,
    body: PipelineConfigUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> PipelineConfig:
    """Update an existing pipeline configuration."""
    service = _get_service()
    try:
        updated = await service.update_pipeline(project_id, pipeline_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if updated is None:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return updated


# ── Delete Pipeline ──


@router.delete("/{project_id}/{pipeline_id}")
async def delete_pipeline(
    project_id: str,
    pipeline_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Delete a pipeline configuration."""
    service = _get_service()
    deleted = await service.delete_pipeline(project_id, pipeline_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"success": True, "deleted_id": pipeline_id}
