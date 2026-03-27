"""REST endpoints for the Self-Evolving Roadmap Engine (FR-008).

Routes:
  GET  /roadmap/config             — Retrieve roadmap configuration
  PUT  /roadmap/config             — Update roadmap configuration
  POST /roadmap/generate           — Manually trigger generation
  GET  /roadmap/history            — Retrieve cycle history
  POST /roadmap/items/{issue}/skip — Veto (skip) a roadmap item
"""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.auth import get_session_dep
from src.dependencies import verify_project_access
from src.logging_utils import get_logger
from src.models.roadmap import RoadmapBatch, RoadmapCycleLog, RoadmapCycleStatus
from src.models.user import UserSession
from src.services.database import get_db

logger = get_logger(__name__)

router = APIRouter()


# ── Request/Response Models ──────────────────────────────────────────────


class RoadmapConfigResponse(BaseModel):
    """Roadmap configuration fields from ProjectBoardConfig."""

    roadmap_enabled: bool = False
    roadmap_seed: str = ""
    roadmap_batch_size: int = 3
    roadmap_pipeline_id: str | None = None
    roadmap_auto_launch: bool = False
    roadmap_grace_minutes: int = 0


class RoadmapConfigUpdate(BaseModel):
    """Partial update for roadmap configuration."""

    roadmap_enabled: bool | None = None
    roadmap_seed: str | None = Field(default=None, max_length=10000)
    roadmap_batch_size: int | None = Field(default=None, ge=1, le=10)
    roadmap_pipeline_id: str | None = None
    roadmap_auto_launch: bool | None = None
    roadmap_grace_minutes: int | None = Field(default=None, ge=0, le=1440)


class GenerateResponse(BaseModel):
    """Response from the generate endpoint."""

    cycle_id: int
    batch: RoadmapBatch


class HistoryResponse(BaseModel):
    """Paginated cycle history response."""

    cycles: list[RoadmapCycleLog]
    total: int


class SkipResponse(BaseModel):
    """Response from the skip (veto) endpoint."""

    issue_number: int
    skipped: bool


# ── Endpoints ────────────────────────────────────────────────────────────


@router.get(
    "/config",
    response_model=RoadmapConfigResponse,
    dependencies=[Depends(verify_project_access)],
)
async def get_roadmap_config(
    project_id: str = Query(..., description="GitHub project node ID"),
    session: UserSession = Depends(get_session_dep),
) -> RoadmapConfigResponse:
    """Retrieve roadmap configuration for a project."""
    config = await _load_board_config(project_id)
    return RoadmapConfigResponse(
        roadmap_enabled=config.roadmap_enabled,
        roadmap_seed=config.roadmap_seed,
        roadmap_batch_size=config.roadmap_batch_size,
        roadmap_pipeline_id=config.roadmap_pipeline_id,
        roadmap_auto_launch=config.roadmap_auto_launch,
        roadmap_grace_minutes=config.roadmap_grace_minutes,
    )


@router.put(
    "/config",
    response_model=RoadmapConfigResponse,
    dependencies=[Depends(verify_project_access)],
)
async def update_roadmap_config(
    body: RoadmapConfigUpdate,
    project_id: str = Query(..., description="GitHub project node ID"),
    session: UserSession = Depends(get_session_dep),
) -> RoadmapConfigResponse:
    """Update roadmap configuration for a project.

    Merges with existing board config (does not overwrite non-roadmap fields).
    """
    db = get_db()
    from src.services.settings_store import get_project_settings_row, upsert_project_settings

    # Load existing board config
    config = await _load_board_config(project_id)

    # Apply partial updates
    update_data = body.model_dump(exclude_unset=True)
    config_dict = config.model_dump()
    for key, value in update_data.items():
        config_dict[key] = value

    # Persist updated board config
    from src.models.settings import ProjectBoardConfig

    updated_config = ProjectBoardConfig(**config_dict)
    board_json = json.dumps(updated_config.model_dump())

    await upsert_project_settings(
        db, session.github_user_id, project_id, {"board_display_config": board_json}
    )
    # Sync to __workflow__ canonical row
    await upsert_project_settings(
        db, "__workflow__", project_id, {"board_display_config": board_json}
    )

    logger.info("Updated roadmap config for project %s", project_id)

    return RoadmapConfigResponse(
        roadmap_enabled=updated_config.roadmap_enabled,
        roadmap_seed=updated_config.roadmap_seed,
        roadmap_batch_size=updated_config.roadmap_batch_size,
        roadmap_pipeline_id=updated_config.roadmap_pipeline_id,
        roadmap_auto_launch=updated_config.roadmap_auto_launch,
        roadmap_grace_minutes=updated_config.roadmap_grace_minutes,
    )


@router.post(
    "/generate",
    response_model=GenerateResponse,
    dependencies=[Depends(verify_project_access)],
)
async def generate_roadmap(
    project_id: str = Query(..., description="GitHub project node ID"),
    session: UserSession = Depends(get_session_dep),
) -> GenerateResponse:
    """Manually trigger a roadmap generation cycle."""
    from src.services.roadmap.generator import generate_roadmap_batch

    try:
        batch = await generate_roadmap_batch(
            project_id=project_id,
            user_id=session.github_user_id,
            access_token=session.access_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Get the cycle ID from the most recent cycle for this project
    db = get_db()
    cursor = await db.execute(
        "SELECT id FROM roadmap_cycles WHERE project_id = ? ORDER BY id DESC LIMIT 1",
        (project_id,),
    )
    row = await cursor.fetchone()
    cycle_id = row[0] if row else 0

    # Launch items immediately when grace_minutes is 0 (default).
    # When grace_minutes > 0, items are held for the veto window.
    config = await _load_board_config(project_id)
    if config.roadmap_grace_minutes == 0 and config.roadmap_pipeline_id:
        from src.services.roadmap.launcher import launch_roadmap_batch

        await launch_roadmap_batch(
            batch=batch,
            pipeline_id=config.roadmap_pipeline_id,
            session=session,
        )

    # Send Signal notification (FR-009)
    try:
        from src.services.signal_delivery import deliver_roadmap_notification

        await deliver_roadmap_notification(batch, project_id, session.github_user_id)
    except Exception:
        logger.warning("Failed to send roadmap notification", exc_info=True)

    return GenerateResponse(cycle_id=cycle_id, batch=batch)


@router.get(
    "/history",
    response_model=HistoryResponse,
    dependencies=[Depends(verify_project_access)],
)
async def get_roadmap_history(
    project_id: str = Query(..., description="GitHub project node ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of cycles to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    session: UserSession = Depends(get_session_dep),
) -> HistoryResponse:
    """Retrieve roadmap cycle history for a project."""
    db = get_db()

    # Count total
    cursor = await db.execute(
        "SELECT COUNT(*) FROM roadmap_cycles WHERE project_id = ?",
        (project_id,),
    )
    row = await cursor.fetchone()
    total = row[0] if row else 0

    # Fetch page
    cursor = await db.execute(
        "SELECT id, project_id, user_id, batch_json, status, created_at "
        "FROM roadmap_cycles WHERE project_id = ? "
        "ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (project_id, limit, offset),
    )
    rows = await cursor.fetchall()

    cycles = [
        RoadmapCycleLog(
            id=r[0],
            project_id=r[1],
            user_id=r[2],
            batch_json=r[3],
            status=RoadmapCycleStatus(r[4]),
            created_at=r[5],
        )
        for r in rows
    ]

    return HistoryResponse(cycles=cycles, total=total)


@router.post(
    "/items/{issue_number}/skip",
    response_model=SkipResponse,
    dependencies=[Depends(verify_project_access)],
)
async def skip_roadmap_item(
    issue_number: int,
    project_id: str = Query(..., description="GitHub project node ID"),
    session: UserSession = Depends(get_session_dep),
) -> SkipResponse:
    """Veto (skip) a roadmap item by delegating to the existing blocking-queue skip."""
    from src.services.copilot_polling import get_pipeline_state, remove_pipeline_state

    state = get_pipeline_state(issue_number)
    if state is None:
        raise HTTPException(status_code=404, detail="Issue not found in pipeline queue")

    remove_pipeline_state(issue_number)
    logger.info(
        "Roadmap item #%d vetoed (skipped) for project %s by user %s",
        issue_number,
        project_id,
        session.github_user_id,
    )

    return SkipResponse(issue_number=issue_number, skipped=True)


# ── Internal Helpers ─────────────────────────────────────────────────────


async def _load_board_config(project_id: str):
    """Load the ProjectBoardConfig for the project from the canonical row."""
    db = get_db()
    from src.services.settings_store import get_project_settings_row

    row = await get_project_settings_row(db, "__workflow__", project_id)

    from src.models.settings import ProjectBoardConfig

    if row is None or not row["board_display_config"]:
        return ProjectBoardConfig()

    raw = json.loads(row["board_display_config"])
    return ProjectBoardConfig(**raw)
