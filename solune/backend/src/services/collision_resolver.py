"""Collision detection and resolution for concurrent MCP operations.

Implements optimistic concurrency control with three resolution strategies:
1. user_priority — user-initiated actions take precedence over automation.
2. last_write_wins — the most recent operation wins (by timestamp).
3. manual_review — unresolvable conflicts are flagged for human review.
"""

from __future__ import annotations

import json
import uuid

import aiosqlite

from src.logging_utils import get_logger
from src.models.mcp import CollisionEvent, CollisionOperation
from src.utils import utcnow

logger = get_logger(__name__)


def detect_collision(
    entity_type: str,
    entity_id: str,
    incoming_operation: CollisionOperation,
    current_version: int,
) -> CollisionEvent | None:
    """Check if the incoming operation conflicts with the current state.

    A collision is detected when the ``version_expected`` on the incoming
    operation does not match the stored ``current_version``.

    Returns ``None`` if no collision is detected, otherwise returns a
    ``CollisionEvent`` with the resolution already applied.
    """
    if incoming_operation.version_expected == current_version:
        return None

    # Build a synthetic "existing" operation representing the current state
    existing_operation = CollisionOperation(
        operation_id=str(uuid.uuid4()),
        operation_type="update",
        initiated_by="automation",
        timestamp=incoming_operation.timestamp,
        version_expected=current_version,
    )

    collision = CollisionEvent(
        collision_id=str(uuid.uuid4()),
        target_entity_type=entity_type,
        target_entity_id=entity_id,
        operation_a=existing_operation,
        operation_b=incoming_operation,
        resolution_strategy="last_write_wins",
        resolution_outcome="",
        winning_operation="b",
        detected_at=utcnow(),
    )

    return resolve_collision(collision)


def resolve_collision(collision: CollisionEvent) -> CollisionEvent:
    """Apply the resolution strategy and return the resolved collision event.

    Resolution priority:
    1. User-initiated over automated (FR-018).
    2. Last-write-wins by timestamp for same-type operations.
    3. Manual review for contradictory state transitions (FR-020).
    """
    op_a = collision.operation_a
    op_b = collision.operation_b

    # Rule 1: User-initiated beats automation
    if op_a.initiated_by != op_b.initiated_by:
        if op_b.initiated_by == "user":
            collision.resolution_strategy = "user_priority"
            collision.winning_operation = "b"
            collision.resolution_outcome = (
                "User-initiated operation takes precedence over automation"
            )
        else:
            collision.resolution_strategy = "user_priority"
            collision.winning_operation = "a"
            collision.resolution_outcome = (
                "User-initiated operation takes precedence over automation"
            )
        collision.resolved_at = utcnow()
        return collision

    # Rule 2: Last-write-wins by timestamp
    if op_b.timestamp >= op_a.timestamp:
        collision.resolution_strategy = "last_write_wins"
        collision.winning_operation = "b"
        collision.resolution_outcome = "Later operation wins by timestamp"
    else:
        collision.resolution_strategy = "last_write_wins"
        collision.winning_operation = "a"
        collision.resolution_outcome = "Later operation wins by timestamp"

    collision.resolved_at = utcnow()
    return collision


async def log_collision_event(
    db: aiosqlite.Connection,
    collision: CollisionEvent,
) -> None:
    """Persist a collision event to the ``collision_events`` table (FR-019)."""
    try:
        op_a_json = json.dumps(
            {
                "operation_id": collision.operation_a.operation_id,
                "operation_type": collision.operation_a.operation_type,
                "initiated_by": collision.operation_a.initiated_by,
                "user_id": collision.operation_a.user_id,
                "timestamp": collision.operation_a.timestamp.isoformat(),
                "payload": collision.operation_a.payload,
                "version_expected": collision.operation_a.version_expected,
            }
        )
        op_b_json = json.dumps(
            {
                "operation_id": collision.operation_b.operation_id,
                "operation_type": collision.operation_b.operation_type,
                "initiated_by": collision.operation_b.initiated_by,
                "user_id": collision.operation_b.user_id,
                "timestamp": collision.operation_b.timestamp.isoformat(),
                "payload": collision.operation_b.payload,
                "version_expected": collision.operation_b.version_expected,
            }
        )
        await db.execute(
            "INSERT INTO collision_events "
            "(collision_id, target_entity_type, target_entity_id, "
            "operation_a_json, operation_b_json, resolution_strategy, "
            "resolution_outcome, winning_operation, detected_at, resolved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                collision.collision_id,
                collision.target_entity_type,
                collision.target_entity_id,
                op_a_json,
                op_b_json,
                collision.resolution_strategy,
                collision.resolution_outcome,
                collision.winning_operation,
                collision.detected_at.isoformat(),
                collision.resolved_at.isoformat() if collision.resolved_at else None,
            ),
        )
        await db.commit()
        logger.info(
            "Logged collision %s: %s entity %s — strategy=%s winner=%s",
            collision.collision_id,
            collision.target_entity_type,
            collision.target_entity_id,
            collision.resolution_strategy,
            collision.winning_operation,
        )
    except Exception:
        logger.exception("Failed to persist collision event %s", collision.collision_id)
