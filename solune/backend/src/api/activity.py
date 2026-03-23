"""Activity feed API — paginated activity events and entity-scoped history."""

from __future__ import annotations

import base64
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from src.api.auth import get_session_dep
from src.dependencies import get_database, verify_project_access
from src.logging_utils import get_logger
from src.models.activity import ActivityEvent
from src.models.user import UserSession

logger = get_logger(__name__)
router = APIRouter()

ALLOWED_ENTITY_TYPES = {"pipeline", "chore", "agent", "app", "tool", "issue"}


def _encode_cursor(created_at: str, event_id: str) -> str:
    """Encode a compound cursor as a base64 string."""
    raw = json.dumps([created_at, event_id])
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, str]:
    """Decode a base64 compound cursor into (created_at, id)."""
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    parts = json.loads(raw)
    return parts[0], parts[1]


async def _query_events(
    db,
    *,
    project_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    event_type_filter: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
) -> dict:
    """Shared query logic for feed and entity-history endpoints."""
    conditions: list[str] = []
    params: list[str | int] = []

    if project_id:
        conditions.append("project_id = ?")
        params.append(project_id)

    if entity_type:
        conditions.append("entity_type = ?")
        params.append(entity_type)

    if entity_id:
        conditions.append("entity_id = ?")
        params.append(entity_id)

    if event_type_filter:
        types = [t.strip() for t in event_type_filter.split(",") if t.strip()]
        if types:
            placeholders = ",".join("?" for _ in types)
            conditions.append(f"event_type IN ({placeholders})")
            params.extend(types)

    if cursor:
        try:
            cursor_ts, cursor_id = _decode_cursor(cursor)
            conditions.append("(created_at < ? OR (created_at = ? AND id < ?))")
            params.extend([cursor_ts, cursor_ts, cursor_id])
        except Exception:
            logger.warning("Invalid cursor value: %s", cursor)

    where = " AND ".join(conditions) if conditions else "1=1"

    # Fetch one extra row to determine has_more
    query = f"""
        SELECT id, event_type, entity_type, entity_id, project_id,
               actor, action, summary, detail, created_at
        FROM activity_events
        WHERE {where}
        ORDER BY created_at DESC, id DESC
        LIMIT ?
    """
    params.append(limit + 1)

    rows = await db.execute(query, params)
    results = await rows.fetchall()

    has_more = len(results) > limit
    page_rows = results[:limit]

    items: list[dict] = []
    for row in page_rows:
        detail_raw = row[8]  # detail column
        detail_parsed = None
        if detail_raw:
            try:
                detail_parsed = json.loads(detail_raw)
            except (json.JSONDecodeError, TypeError):
                detail_parsed = None

        items.append(
            ActivityEvent(
                id=row[0],
                event_type=row[1],
                entity_type=row[2],
                entity_id=row[3],
                project_id=row[4],
                actor=row[5],
                action=row[6],
                summary=row[7],
                detail=detail_parsed,
                created_at=row[9],
            ).model_dump()
        )

    next_cursor = None
    if has_more and page_rows:
        last = page_rows[-1]
        next_cursor = _encode_cursor(last[9], last[0])

    # Total count on first page only (no cursor)
    total_count = None
    if not cursor:
        count_query = f"SELECT COUNT(*) FROM activity_events WHERE {where}"
        count_params = params[:-1]  # remove the LIMIT param
        count_row = await db.execute(count_query, count_params)
        count_result = await count_row.fetchone()
        total_count = count_result[0] if count_result else 0

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "total_count": total_count,
    }


@router.get("")
async def get_activity_feed(
    request: Request,
    session: Annotated[UserSession, Depends(get_session_dep)],
    project_id: Annotated[str, Query(description="Project ID to scope the feed")],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    event_type: Annotated[
        str | None, Query(description="Comma-separated event type filter")
    ] = None,
    db=Depends(get_database),  # noqa: B008
) -> dict:
    """Paginated activity feed scoped to a project."""
    await verify_project_access(request, project_id, session)
    return await _query_events(
        db,
        project_id=project_id,
        event_type_filter=event_type,
        limit=limit,
        cursor=cursor,
    )


@router.get("/{entity_type}/{entity_id}")
async def get_entity_history(
    request: Request,
    entity_type: str,
    entity_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    project_id: Annotated[str, Query(description="Project ID to scope entity history")],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    db=Depends(get_database),  # noqa: B008
) -> dict:
    """Activity history for a specific entity."""
    if entity_type not in ALLOWED_ENTITY_TYPES:
        from src.exceptions import ValidationError

        raise ValidationError(
            f"Invalid entity_type '{entity_type}'. "
            f"Must be one of: {', '.join(sorted(ALLOWED_ENTITY_TYPES))}"
        )

    await verify_project_access(request, project_id, session)
    return await _query_events(
        db,
        project_id=project_id,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
        cursor=cursor,
    )
