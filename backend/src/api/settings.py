"""Settings API endpoints — user preferences, global settings, project settings."""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.dependencies import require_admin
from src.models.settings import (
    EffectiveProjectSettings,
    EffectiveUserSettings,
    GlobalSettingsResponse,
    GlobalSettingsUpdate,
    ProjectSettingsUpdate,
    UserPreferencesUpdate,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.settings_store import (
    flatten_global_settings_update,
    flatten_user_preferences_update,
    get_effective_project_settings,
    get_effective_user_settings,
    get_global_settings,
    update_global_settings,
    upsert_project_settings,
    upsert_user_preferences,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/user", response_model=EffectiveUserSettings)
async def get_user_settings(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> EffectiveUserSettings:
    """Get authenticated user's effective settings (merged with global defaults)."""
    db = get_db()
    return await get_effective_user_settings(db, session.github_user_id)


@router.put("/user", response_model=EffectiveUserSettings)
async def update_user_settings(
    body: UserPreferencesUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> EffectiveUserSettings:
    """Update authenticated user's preferences (partial update)."""
    db = get_db()

    # Flatten nested update structure to flat column dict
    flat = flatten_user_preferences_update(body.model_dump(exclude_unset=True))

    if flat:
        await upsert_user_preferences(db, session.github_user_id, flat)
        logger.info("Updated user preferences for %s", session.github_username)

    return await get_effective_user_settings(db, session.github_user_id)


@router.get("/global", response_model=GlobalSettingsResponse)
async def get_global_settings_endpoint(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> GlobalSettingsResponse:
    """Get global/instance-level settings."""
    db = get_db()
    return await get_global_settings(db)


@router.put("/global", response_model=GlobalSettingsResponse)
async def update_global_settings_endpoint(
    body: GlobalSettingsUpdate,
    session: Annotated[UserSession, Depends(require_admin)],
) -> GlobalSettingsResponse:
    """Update global/instance-level settings (partial update). Requires admin."""
    db = get_db()

    flat = flatten_global_settings_update(body.model_dump(exclude_unset=True))

    if flat:
        result = await update_global_settings(db, flat)
        logger.info("Updated global settings by %s", session.github_username)
        return result

    return await get_global_settings(db)


@router.get("/project/{project_id}", response_model=EffectiveProjectSettings)
async def get_project_settings_endpoint(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> EffectiveProjectSettings:
    """Get per-project effective settings for authenticated user."""
    db = get_db()
    return await get_effective_project_settings(db, session.github_user_id, project_id)


@router.put("/project/{project_id}", response_model=EffectiveProjectSettings)
async def update_project_settings_endpoint(
    project_id: str,
    body: ProjectSettingsUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> EffectiveProjectSettings:
    """Update per-project settings for authenticated user (partial update)."""
    db = get_db()

    updates: dict = {}
    update_data = body.model_dump(exclude_unset=True)

    if "board_display_config" in update_data:
        val = update_data["board_display_config"]
        updates["board_display_config"] = json.dumps(val) if val is not None else None

    if "agent_pipeline_mappings" in update_data:
        val = update_data["agent_pipeline_mappings"]
        updates["agent_pipeline_mappings"] = json.dumps(val) if val is not None else None

    if updates:
        await upsert_project_settings(db, session.github_user_id, project_id, updates)
        logger.info(
            "Updated project settings for user=%s project=%s",
            session.github_username,
            project_id,
        )

    return await get_effective_project_settings(db, session.github_user_id, project_id)
