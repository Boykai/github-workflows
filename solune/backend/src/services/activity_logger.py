"""Fire-and-forget activity event logger.

Writes denormalized summary rows to the ``activity_events`` table.
All exceptions are caught and logged — activity logging must never
block or break the primary operation.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Any

from src.logging_utils import get_logger

if TYPE_CHECKING:
    import aiosqlite

logger = get_logger(__name__)


async def log_event(
    db: aiosqlite.Connection,
    *,
    event_type: str,
    entity_type: str,
    entity_id: str,
    project_id: str,
    actor: str = "system",
    action: str,
    summary: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """Insert an activity event row.  Never raises."""
    try:
        event_id = str(uuid.uuid4())
        detail_json = json.dumps(detail) if detail else None
        await db.execute(
            """INSERT INTO activity_events
               (id, event_type, entity_type, entity_id, project_id, actor, action, summary, detail)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                event_id,
                event_type,
                entity_type,
                entity_id,
                project_id,
                actor,
                action,
                summary,
                detail_json,
            ),
        )
        await db.commit()
    except Exception:
        logger.exception("Activity logging failed (non-fatal)")
