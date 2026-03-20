"""Pydantic models for the activity log / audit trail."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ActivityEvent(BaseModel):
    """Response model for a single activity event."""

    id: str
    event_type: str
    entity_type: str
    entity_id: str
    project_id: str
    actor: str
    action: str
    summary: str
    detail: dict[str, Any] | None = None
    created_at: str


class ActivityEventCreate(BaseModel):
    """Internal model used by log_event() — no id/created_at (DB-generated)."""

    event_type: str
    entity_type: str
    entity_id: str
    project_id: str
    actor: str = "system"
    action: str
    summary: str
    detail: dict[str, Any] | None = None
