"""Done-items persistence — SQLite cache for "Done" status project items.

On cold start (fresh login or server restart), GitHub Projects items in
"Done" status are loaded from the local SQLite cache instead of hitting
the GitHub GraphQL API.  This significantly reduces cold-refresh latency
and rate-limit consumption because Done items change infrequently.

Two item types are stored:
  - ``task``  — lightweight ``Task`` dicts used by GET /projects/{id}/tasks
  - ``board`` — rich ``BoardItem`` dicts used by GET /board/projects/{id}
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import aiosqlite

from src.logging_utils import get_logger
from src.utils import utcnow

logger = get_logger(__name__)

# Module-level DB reference (set during init)
_db: aiosqlite.Connection | None = None


# ── Initialization ──────────────────────────────────────────────


async def init_done_items_store(db: aiosqlite.Connection) -> None:
    """Register the database connection. Called once during lifespan startup."""
    global _db
    _db = db
    logger.info("Done-items store initialised")


# ── Public API ──────────────────────────────────────────────────


async def get_done_items(project_id: str, item_type: str = "task") -> list[dict[str, Any]] | None:
    """Load cached Done items for *project_id* from SQLite.

    Returns ``None`` when no cached data exists (cold start with empty DB).
    Returns an empty list when the last snapshot explicitly contained zero
    Done items.
    """
    if _db is None:
        return None

    try:
        cursor = await _db.execute(
            "SELECT items_json FROM done_items_cache WHERE project_id = ? AND item_type = ?",
            (project_id, item_type),
        )
        row = await cursor.fetchone()
        if row is None:
            return None

        raw = row[0] if isinstance(row, tuple) else row["items_json"]
        return json.loads(raw)
    except (aiosqlite.Error, json.JSONDecodeError, TypeError):
        logger.warning(
            "Failed to load done items cache for project %s (%s)",
            project_id,
            item_type,
            exc_info=True,
        )
        return None


async def save_done_items(
    project_id: str,
    items: list[dict[str, Any]],
    item_type: str = "task",
) -> None:
    """Persist a snapshot of Done items for *project_id* to SQLite.

    The snapshot is stored as a JSON array.  A content hash is computed
    so callers can later detect whether the data actually changed.
    """
    if _db is None:
        return

    items_json = json.dumps(items, sort_keys=True, default=str)
    data_hash = hashlib.sha256(items_json.encode()).hexdigest()
    now = utcnow().isoformat()

    try:
        await _db.execute(
            """
            INSERT INTO done_items_cache (project_id, item_type, items_json, item_count, data_hash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(project_id, item_type) DO UPDATE SET
                items_json = excluded.items_json,
                item_count = excluded.item_count,
                data_hash  = excluded.data_hash,
                updated_at = excluded.updated_at
            """,
            (project_id, item_type, items_json, len(items), data_hash, now),
        )
        await _db.commit()
        logger.debug("Saved %d done items for project %s (%s)", len(items), project_id, item_type)
    except aiosqlite.Error:
        logger.warning(
            "Failed to save done items cache for project %s (%s)",
            project_id,
            item_type,
            exc_info=True,
        )


async def clear_done_items(project_id: str, item_type: str | None = None) -> None:
    """Remove cached Done items for a project.

    If *item_type* is ``None`` both ``task`` and ``board`` rows are removed.
    """
    if _db is None:
        return

    try:
        if item_type:
            await _db.execute(
                "DELETE FROM done_items_cache WHERE project_id = ? AND item_type = ?",
                (project_id, item_type),
            )
        else:
            await _db.execute(
                "DELETE FROM done_items_cache WHERE project_id = ?",
                (project_id,),
            )
        await _db.commit()
    except aiosqlite.Error:
        logger.warning("Failed to clear done items cache for project %s", project_id, exc_info=True)


# ── Test helpers ────────────────────────────────────────────────


def _reset_store() -> None:
    """Reset module state — test use only."""
    global _db
    _db = None
