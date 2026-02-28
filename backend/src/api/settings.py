"""Settings API endpoints — user preferences, global settings, project settings."""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_session_dep
from src.dependencies import require_admin
from src.models.settings import (
    AIProvider,
    EffectiveProjectSettings,
    EffectiveUserSettings,
    GlobalSettingsResponse,
    GlobalSettingsUpdate,
    ModelsResponse,
    ProjectSettingsUpdate,
    UserPreferencesUpdate,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.model_fetcher import get_model_fetcher_service
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

        # Sync agent_pipeline_mappings to the canonical __workflow__ row so the
        # workflow orchestrator picks up the user's configuration.  Also
        # invalidate the in-memory config cache for this project.
        if "agent_pipeline_mappings" in updates:
            workflow_updates = {
                "agent_pipeline_mappings": updates["agent_pipeline_mappings"],
            }
            await upsert_project_settings(db, "__workflow__", project_id, workflow_updates)
            logger.info(
                "Synced agent_pipeline_mappings to __workflow__ canonical row for project=%s",
                project_id,
            )
            # Invalidate in-memory workflow config cache
            try:
                from src.services.workflow_orchestrator.config import _workflow_configs

                _workflow_configs.pop(project_id, None)
            except Exception:
                pass

    return await get_effective_project_settings(db, session.github_user_id, project_id)


# ── Dynamic Model Fetching ──────────────────────────────────────────────────


@router.get("/models/{provider}", response_model=ModelsResponse)
async def get_models_for_provider(
    provider: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh values"),
) -> ModelsResponse:
    """Fetch available models for a provider.

    Returns cached values when available. Checks authentication prerequisites
    before attempting external fetches.
    """
    # Validate provider
    valid_providers = [p.value for p in AIProvider]
    if provider not in valid_providers:
        return ModelsResponse(
            status="error",
            message=f"Unknown provider: {provider}. Valid providers: {', '.join(valid_providers)}",
        )

    # Use the session's access_token for providers that need auth
    token = session.access_token if session else None

    service = get_model_fetcher_service()
    return await service.get_models(provider, token=token, force_refresh=force_refresh)
