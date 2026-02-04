"""Settings API endpoints - User preferences management."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_current_session
from src.models.user import UserSession, UserSettings, UserSettingsUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/settings")
async def get_settings(
    session: Annotated[UserSession, Depends(get_current_session)],
) -> UserSettings:
    """Get current user settings."""
    return session.settings


@router.patch("/settings")
async def update_settings(
    settings_update: UserSettingsUpdate,
    session: Annotated[UserSession, Depends(get_current_session)],
) -> UserSettings:
    """Update user settings."""
    from src.services.github_auth import github_auth_service

    # Update only the fields that were provided
    update_dict = settings_update.model_dump(exclude_unset=True)
    
    # Update the settings
    for field, value in update_dict.items():
        setattr(session.settings, field, value)
    
    # Save the updated session
    github_auth_service.update_session(session)
    
    logger.info("Updated settings for user %s", session.github_username)
    
    return session.settings
