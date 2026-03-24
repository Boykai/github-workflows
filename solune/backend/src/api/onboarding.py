"""Onboarding tour state API endpoints (FR-038)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.api.auth import get_session_dep
from src.logging_utils import get_logger
from src.models.user import UserSession
from src.services.database import get_db

logger = get_logger(__name__)
router = APIRouter()


class OnboardingState(BaseModel):
    """Onboarding tour state response."""

    user_id: str
    current_step: int = 0
    completed: bool = False
    dismissed_at: str | None = None
    completed_at: str | None = None


class OnboardingStateUpdate(BaseModel):
    """Request body for updating onboarding state."""

    current_step: int = Field(..., ge=0, le=13)
    completed: bool = False
    dismissed: bool = False


@router.get("/onboarding/state")
async def get_onboarding_state(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> OnboardingState:
    """Get onboarding tour state for the current user."""
    db = get_db()
    user_id = str(session.github_user_id)

    cursor = await db.execute(
        "SELECT * FROM onboarding_tour_state WHERE user_id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()

    if row is None:
        return OnboardingState(user_id=user_id)

    return OnboardingState(
        user_id=row["user_id"],
        current_step=row["current_step"],
        completed=bool(row["completed"]),
        dismissed_at=row["dismissed_at"],
        completed_at=row["completed_at"],
    )


@router.put("/onboarding/state")
async def update_onboarding_state(
    body: OnboardingStateUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> OnboardingState:
    """Update onboarding tour state for the current user."""
    from src.utils import utcnow

    db = get_db()
    user_id = str(session.github_user_id)
    now = utcnow().isoformat()

    completed_val = 1 if body.completed else 0
    completed_at = now if body.completed else None
    dismissed_at = now if body.dismissed else None

    await db.execute(
        """
        INSERT INTO onboarding_tour_state
            (user_id, current_step, completed, completed_at, dismissed_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            current_step = excluded.current_step,
            completed = excluded.completed,
            completed_at = COALESCE(excluded.completed_at, completed_at),
            dismissed_at = COALESCE(excluded.dismissed_at, dismissed_at)
        """,
        (user_id, body.current_step, completed_val, completed_at, dismissed_at),
    )
    await db.commit()

    return OnboardingState(
        user_id=user_id,
        current_step=body.current_step,
        completed=body.completed,
        dismissed_at=dismissed_at,
        completed_at=completed_at,
    )
