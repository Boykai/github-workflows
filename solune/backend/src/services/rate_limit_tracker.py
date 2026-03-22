"""Rate-limit snapshot storage for capacity planning (optional, P3).

Stores point-in-time GitHub API rate-limit data in SQLite with 24-hour
automatic retention.  Snapshots are recorded once per polling cycle and
exposed via ``GET /api/v1/rate-limit/history``.
"""

from __future__ import annotations

from src.logging_utils import get_logger

logger = get_logger(__name__)

_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS rate_limit_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    remaining INTEGER NOT NULL,
    "limit" INTEGER NOT NULL,
    reset_at INTEGER NOT NULL
)
"""

_INDEX_DDL = """
CREATE INDEX IF NOT EXISTS idx_rate_limit_snapshots_timestamp
    ON rate_limit_snapshots(timestamp)
"""


class RateLimitTracker:
    """Records and queries rate-limit snapshots in SQLite."""

    _table_ready: bool = False

    async def _ensure_table(self) -> None:
        """Create the snapshots table if it does not exist (once per process)."""
        if self._table_ready:
            return
        from src.services.database import get_db

        db = get_db()
        await db.execute(_TABLE_DDL)
        await db.execute(_INDEX_DDL)
        await db.commit()
        self._table_ready = True

    async def record_snapshot(self, remaining: int, limit: int, reset_at: int) -> None:
        """Insert a snapshot and prune rows older than 24 hours."""
        from src.services.database import get_db

        await self._ensure_table()
        db = get_db()
        await db.execute(
            'INSERT INTO rate_limit_snapshots (remaining, "limit", reset_at) VALUES (?, ?, ?)',
            (remaining, limit, reset_at),
        )
        # Prune old rows
        await db.execute(
            "DELETE FROM rate_limit_snapshots "
            "WHERE timestamp < strftime('%Y-%m-%dT%H:%M:%SZ', 'now', '-24 hours')",
        )
        await db.commit()

    async def get_history(self, hours: int = 24) -> list[dict]:
        """Query snapshots within the given time window."""
        from src.services.database import get_db

        await self._ensure_table()
        db = get_db()
        cursor = await db.execute(
            'SELECT timestamp, remaining, "limit", reset_at '
            "FROM rate_limit_snapshots "
            "WHERE timestamp >= strftime('%Y-%m-%dT%H:%M:%SZ', 'now', ?) "
            "ORDER BY timestamp ASC",
            (f"-{hours} hours",),
        )
        rows = await cursor.fetchall()
        return [
            {
                "timestamp": row[0] if isinstance(row, tuple) else row["timestamp"],
                "remaining": row[1] if isinstance(row, tuple) else row["remaining"],
                "limit": row[2] if isinstance(row, tuple) else row["limit"],
                "reset_at": row[3] if isinstance(row, tuple) else row["reset_at"],
            }
            for row in rows
        ]


# ── Module-level singleton ─────────────────────────────────────────────
_tracker = RateLimitTracker()


def get_tracker() -> RateLimitTracker:
    """Return the shared ``RateLimitTracker`` singleton."""
    return _tracker
