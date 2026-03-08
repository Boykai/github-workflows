"""SQLite persistence layer for the blocking queue table."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from src.models.blocking import BlockingQueueEntry
from src.services.database import get_db

logger = logging.getLogger(__name__)


def _row_to_entry(row) -> BlockingQueueEntry:
    """Convert an aiosqlite Row to a BlockingQueueEntry."""
    data = dict(row)
    data["is_blocking"] = bool(data.get("is_blocking", 0))
    return BlockingQueueEntry(**data)


async def insert(
    repo_key: str,
    issue_number: int,
    project_id: str,
    is_blocking: bool,
) -> BlockingQueueEntry:
    """Insert a new entry into the blocking queue."""
    db = get_db()
    cursor = await db.execute(
        """INSERT INTO blocking_queue (repo_key, issue_number, project_id, is_blocking)
           VALUES (?, ?, ?, ?)""",
        (repo_key, issue_number, project_id, int(is_blocking)),
    )
    await db.commit()

    row = await (
        await db.execute("SELECT * FROM blocking_queue WHERE id = ?", (cursor.lastrowid,))
    ).fetchone()
    return _row_to_entry(row)


async def update_status(
    repo_key: str,
    issue_number: int,
    *,
    queue_status: str,
    parent_branch: str | None = None,
    blocking_source_issue: int | None = None,
    activated_at: str | None = None,
    completed_at: str | None = None,
) -> BlockingQueueEntry | None:
    """Update the status and related fields of a queue entry."""
    db = get_db()

    sets: list[str] = ["queue_status = ?"]
    vals: list = [queue_status]

    if parent_branch is not None:
        sets.append("parent_branch = ?")
        vals.append(parent_branch)
    if blocking_source_issue is not None:
        sets.append("blocking_source_issue = ?")
        vals.append(blocking_source_issue)
    if activated_at is not None:
        sets.append("activated_at = ?")
        vals.append(activated_at)
    if completed_at is not None:
        sets.append("completed_at = ?")
        vals.append(completed_at)

    vals.extend([repo_key, issue_number])
    await db.execute(
        f"UPDATE blocking_queue SET {', '.join(sets)} WHERE repo_key = ? AND issue_number = ?",
        vals,
    )
    await db.commit()
    return await get_by_issue(repo_key, issue_number)


async def get_by_repo(
    repo_key: str,
    *,
    status: str | None = None,
) -> list[BlockingQueueEntry]:
    """Return queue entries for a repo, optionally filtered by status, ordered by created_at ASC."""
    db = get_db()
    if status:
        cursor = await db.execute(
            "SELECT * FROM blocking_queue WHERE repo_key = ? AND queue_status = ? ORDER BY created_at ASC",
            (repo_key, status),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM blocking_queue WHERE repo_key = ? ORDER BY created_at ASC",
            (repo_key,),
        )
    rows = await cursor.fetchall()
    return [_row_to_entry(r) for r in rows]


async def get_by_issue(repo_key: str, issue_number: int) -> BlockingQueueEntry | None:
    """Fetch a single queue entry by repo + issue number."""
    db = get_db()
    cursor = await db.execute(
        "SELECT * FROM blocking_queue WHERE repo_key = ? AND issue_number = ?",
        (repo_key, issue_number),
    )
    row = await cursor.fetchone()
    return _row_to_entry(row) if row else None


async def get_pending(repo_key: str) -> list[BlockingQueueEntry]:
    """Return all pending entries for a repo, ordered by created_at ASC."""
    return await get_by_repo(repo_key, status="pending")


async def get_open_blocking(repo_key: str) -> list[BlockingQueueEntry]:
    """Return blocking entries that are active or in_review, ordered by created_at ASC."""
    db = get_db()
    cursor = await db.execute(
        """SELECT * FROM blocking_queue
           WHERE repo_key = ? AND is_blocking = 1
             AND queue_status IN ('active', 'in_review')
           ORDER BY created_at ASC""",
        (repo_key,),
    )
    rows = await cursor.fetchall()
    return [_row_to_entry(r) for r in rows]


async def get_active_or_in_review(repo_key: str) -> list[BlockingQueueEntry]:
    """Return all entries that are active or in_review."""
    db = get_db()
    cursor = await db.execute(
        """SELECT * FROM blocking_queue
           WHERE repo_key = ? AND queue_status IN ('active', 'in_review')
           ORDER BY created_at ASC""",
        (repo_key,),
    )
    rows = await cursor.fetchall()
    return [_row_to_entry(r) for r in rows]


async def get_repos_with_non_completed(
) -> list[str]:
    """Return distinct repo_keys that have non-completed queue entries."""
    db = get_db()
    cursor = await db.execute(
        "SELECT DISTINCT repo_key FROM blocking_queue WHERE queue_status != 'completed'"
    )
    rows = await cursor.fetchall()
    return [row["repo_key"] for row in rows]


async def get_by_project(
    project_id: str,
    *,
    exclude_completed: bool = True,
) -> list[BlockingQueueEntry]:
    """Return queue entries for a project, optionally excluding completed, ordered by created_at ASC."""
    db = get_db()
    if exclude_completed:
        cursor = await db.execute(
            """SELECT * FROM blocking_queue
               WHERE project_id = ? AND queue_status != 'completed'
               ORDER BY created_at ASC""",
            (project_id,),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM blocking_queue WHERE project_id = ? ORDER BY created_at ASC",
            (project_id,),
        )
    rows = await cursor.fetchall()
    return [_row_to_entry(r) for r in rows]


async def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
