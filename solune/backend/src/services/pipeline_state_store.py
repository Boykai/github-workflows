"""Pipeline state persistence — SQLite write-through cache.

Provides durable SQLite-backed storage for pipeline orchestration state,
with ``BoundedDict`` as an L1 in-memory cache.  All writes go through
both layers atomically under ``asyncio.Lock``.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import aiosqlite

from src.logging_utils import get_logger
from src.utils import BoundedDict, utcnow

if TYPE_CHECKING:
    from .workflow_orchestrator.models import MainBranchInfo

logger = get_logger(__name__)

# L1 in-memory caches — no artificial cap (FR-003).  The BoundedDict
# maxlen is set high enough to be effectively unbounded for any realistic
# deployment while still preventing runaway memory in pathological cases.
_pipeline_states: BoundedDict[int, Any] = BoundedDict(maxlen=50_000)
_issue_main_branches: BoundedDict[int, Any] = BoundedDict(maxlen=50_000)
_issue_sub_issue_map: BoundedDict[int, dict[str, dict]] = BoundedDict(maxlen=50_000)
_agent_trigger_inflight: BoundedDict[str, datetime] = BoundedDict(maxlen=50_000)

# Module-level lock for all mutations
_store_lock: asyncio.Lock | None = None

# Per-project launch locks — serialises the queue-gate check-and-register
# sequence so concurrent launches for the same project cannot race.
_project_launch_locks: dict[str, asyncio.Lock] = {}

# Module-level DB reference (set during init)
_db: aiosqlite.Connection | None = None


def _get_store_lock() -> asyncio.Lock:
    """Create the shared store lock lazily inside the active event loop."""
    global _store_lock
    if _store_lock is None:
        _store_lock = asyncio.Lock()
    return _store_lock


def get_project_launch_lock(project_id: str) -> asyncio.Lock:
    """Return (or create) an asyncio.Lock for the given project.

    Serialises the queue-gate decision so that concurrent pipeline
    launches for the same project cannot both see ``active_count == 0``
    and bypass the queue.
    """
    if project_id not in _project_launch_locks:
        _project_launch_locks[project_id] = asyncio.Lock()
    return _project_launch_locks[project_id]


# ── Initialization ──────────────────────────────────────────────


async def init_pipeline_state_store(db: aiosqlite.Connection) -> None:
    """Load all active pipeline states from SQLite into L1 caches.

    Called once during application startup (in ``lifespan()``).
    Phase 8: If the pipeline state table is empty or unavailable, the
    system attempts label-driven state recovery.
    """
    global _db
    _db = db
    pipeline_state_count = 0

    # Load pipeline states
    try:
        cursor = await db.execute("SELECT * FROM pipeline_states")
        rows = list(await cursor.fetchall())
        for row in rows:
            try:
                issue_number = row[0] if isinstance(row, tuple) else row["issue_number"]
                state = _row_to_pipeline_state(row)
                _pipeline_states[issue_number] = state
            except Exception:
                logger.error("Failed to load pipeline state row: %s", row, exc_info=True)
        pipeline_state_count = len(rows)
        logger.info("Loaded %d pipeline states from SQLite", pipeline_state_count)
    except aiosqlite.Error:
        logger.warning(
            "pipeline_states table not available; starting with empty cache", exc_info=True
        )

    # Load main branches
    try:
        cursor = await db.execute("SELECT * FROM issue_main_branches")
        rows = list(await cursor.fetchall())
        for row in rows:
            try:
                issue_number = row[0] if isinstance(row, tuple) else row["issue_number"]
                _issue_main_branches[issue_number] = _row_to_main_branch(row)
            except Exception:
                logger.error("Failed to load main branch row: %s", row, exc_info=True)
        logger.info("Loaded %d main branches from SQLite", len(rows))
    except aiosqlite.Error:
        logger.warning(
            "issue_main_branches table not available; starting with empty cache", exc_info=True
        )

    # Load sub-issue map
    try:
        cursor = await db.execute("SELECT * FROM issue_sub_issue_map")
        rows = await cursor.fetchall()
        for row in rows:
            try:
                issue_number = row[0] if isinstance(row, tuple) else row["issue_number"]
                agent_name = row[1] if isinstance(row, tuple) else row["agent_name"]
                entry = _row_to_sub_issue_entry(row)
                if issue_number not in _issue_sub_issue_map:
                    _issue_sub_issue_map[issue_number] = {}
                _issue_sub_issue_map[issue_number][agent_name] = entry
            except Exception:
                logger.error("Failed to load sub-issue map row: %s", row, exc_info=True)
        logger.info("Loaded sub-issue maps for %d issues from SQLite", len(_issue_sub_issue_map))
    except aiosqlite.Error:
        logger.warning(
            "issue_sub_issue_map table not available; starting with empty cache", exc_info=True
        )

    # Load trigger inflight markers
    try:
        cursor = await db.execute("SELECT * FROM agent_trigger_inflight")
        rows = list(await cursor.fetchall())
        for row in rows:
            try:
                key = row[0] if isinstance(row, tuple) else row["trigger_key"]
                started_str = row[1] if isinstance(row, tuple) else row["started_at"]
                started_at = datetime.fromisoformat(started_str)
                _agent_trigger_inflight[key] = started_at
            except Exception:
                logger.error("Failed to load trigger inflight row: %s", row, exc_info=True)
        logger.info("Loaded %d trigger inflight markers from SQLite", len(rows))
    except aiosqlite.Error:
        logger.warning(
            "agent_trigger_inflight table not available; starting with empty cache", exc_info=True
        )

    # Phase 8: If pipeline state table was empty or corrupt, log that
    # label-driven recovery is available. Actual recovery is triggered
    # on demand when a project poll cycle starts, not at startup, to
    # avoid needing an access token at init time.
    if pipeline_state_count == 0:
        logger.info(
            "No pipeline states loaded from SQLite. "
            "Label-driven recovery will be attempted when polling starts."
        )


# ── Row conversion helpers ──────────────────────────────────────


def _safe_parse_datetime(value: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _row_to_pipeline_state(row) -> Any:
    """Convert a database row to a PipelineState dataclass."""
    from .workflow_orchestrator.models import PipelineState

    if isinstance(row, tuple):
        # Positional: issue_number, project_id, status, agent_name, agent_instance_id,
        #             pr_number, pr_url, sub_issues, metadata, created_at, updated_at
        sub_issues_raw = row[7]
        metadata_raw = row[8]
    else:
        sub_issues_raw = row["sub_issues"]
        metadata_raw = row["metadata"]

    issue_number = row[0] if isinstance(row, tuple) else row["issue_number"]
    project_id = row[1] if isinstance(row, tuple) else row["project_id"]
    status_val = row[2] if isinstance(row, tuple) else row["status"]
    agent_name = row[3] if isinstance(row, tuple) else row["agent_name"]

    # Decode JSON fields
    sub_issues: dict[str, dict] = {}
    if sub_issues_raw:
        try:
            sub_issues = json.loads(sub_issues_raw)
        except (json.JSONDecodeError, TypeError):
            logger.error("Corrupt sub_issues JSON for issue %d", issue_number, exc_info=True)

    metadata: dict = {}
    if metadata_raw:
        try:
            metadata = json.loads(metadata_raw)
        except (json.JSONDecodeError, TypeError):
            logger.error("Corrupt metadata JSON for issue %d", issue_number, exc_info=True)

    # Reconstruct PipelineState with stored + metadata fields
    agents = metadata.get("agents", [agent_name] if agent_name else [])

    # Parse started_at defensively — malformed timestamps in persisted
    # metadata must not crash the entire state reload.
    started_at_val = None
    if metadata.get("started_at"):
        try:
            started_at_val = datetime.fromisoformat(metadata["started_at"])
        except (ValueError, TypeError):
            logger.error(
                "Corrupt started_at timestamp for issue %d: %r",
                issue_number,
                metadata["started_at"],
                exc_info=True,
            )

    return PipelineState(
        issue_number=issue_number,
        project_id=project_id,
        status=status_val,
        agents=agents,
        current_agent_index=metadata.get("current_agent_index", 0),
        completed_agents=metadata.get("completed_agents", []),
        started_at=started_at_val,
        error=metadata.get("error"),
        agent_assigned_sha=metadata.get("agent_assigned_sha", ""),
        agent_sub_issues=sub_issues,
        original_status=metadata.get("original_status"),
        target_status=metadata.get("target_status"),
        execution_mode=metadata.get("execution_mode", "sequential"),
        parallel_agent_statuses=metadata.get("parallel_agent_statuses", {}),
        failed_agents=metadata.get("failed_agents", []),
        queued=metadata.get("queued", False),
        concurrent_group_id=metadata.get("concurrent_group_id"),
        is_isolated=metadata.get("is_isolated", True),
        recovered_at=_safe_parse_datetime(metadata.get("recovered_at")),
        auto_merge=metadata.get("auto_merge", False),
    )


def _pipeline_state_to_row(issue_number: int, state: Any) -> tuple:
    """Convert a PipelineState to SQLite row values."""
    metadata = {
        "agents": state.agents,
        "current_agent_index": state.current_agent_index,
        "completed_agents": state.completed_agents,
        "started_at": state.started_at.isoformat() if state.started_at else None,
        "error": state.error,
        "agent_assigned_sha": state.agent_assigned_sha,
        "original_status": state.original_status,
        "target_status": state.target_status,
        "execution_mode": state.execution_mode,
        "parallel_agent_statuses": state.parallel_agent_statuses,
        "failed_agents": state.failed_agents,
        "queued": state.queued,
        "concurrent_group_id": state.concurrent_group_id,
        "is_isolated": state.is_isolated,
        "recovered_at": state.recovered_at.isoformat() if state.recovered_at else None,
        "auto_merge": state.auto_merge,
    }
    now = utcnow().isoformat()
    return (
        issue_number,
        state.project_id,
        state.status,
        state.current_agent,
        getattr(state, "agent_instance_id", None),
        getattr(state, "pr_number", None),
        getattr(state, "pr_url", None),
        json.dumps(state.agent_sub_issues) if state.agent_sub_issues else None,
        json.dumps(metadata),
        now,
        now,
    )


def _row_to_main_branch(row) -> MainBranchInfo:
    """Convert a database row to a MainBranchInfo TypedDict."""
    from .workflow_orchestrator.models import MainBranchInfo

    if isinstance(row, tuple):
        return MainBranchInfo(branch=row[1], pr_number=row[2], head_sha=row[3] or "")
    return MainBranchInfo(
        branch=row["branch"],
        pr_number=row["pr_number"],
        head_sha=row["head_sha"] if "head_sha" in row.keys() else "",
    )


def _row_to_sub_issue_entry(row) -> dict:
    """Convert a database row to a sub-issue entry dict."""
    if isinstance(row, tuple):
        return {
            "number": row[2],
            "node_id": row[3],
            "url": row[4] or "",
        }
    return {
        "number": row["sub_issue_number"],
        "node_id": row["sub_issue_node_id"],
        "url": row["sub_issue_url"] or "",
    }


# ── Pipeline States ─────────────────────────────────────────────


def get_pipeline_state(issue_number: int) -> Any:
    """Read pipeline state from L1 cache.

    Returns ``None`` on L1 miss.  Callers in async contexts should prefer
    ``get_pipeline_state_async()`` which falls back to SQLite on cache miss.
    """
    return _pipeline_states.get(issue_number)


async def get_pipeline_state_async(issue_number: int) -> Any:
    """Read pipeline state with async SQLite fallback on L1 miss."""
    state = _pipeline_states.get(issue_number)
    if state is not None:
        return state
    # L1 miss (eviction or cold start) — fall back to SQLite
    if _db is not None:
        try:
            cursor = await _db.execute(
                "SELECT * FROM pipeline_states WHERE issue_number = ?",
                (issue_number,),
            )
            row = await cursor.fetchone()
            if row is not None:
                state = _row_to_pipeline_state(row)
                _pipeline_states[issue_number] = state  # repopulate L1
                return state
        except aiosqlite.Error:
            logger.error(
                "Failed to read pipeline state from SQLite for issue %d",
                issue_number,
                exc_info=True,
            )
    return None


def get_all_pipeline_states() -> dict[int, Any]:
    """Get all pipeline states from L1 cache."""
    return dict(_pipeline_states)


def count_active_pipelines_for_project(
    project_id: str,
    *,
    exclude_issue: int | None = None,
) -> int:
    """Count non-queued pipelines for a project from L1 cache.

    Scans the in-memory cache — O(n) but fast for realistic cardinality.
    Only counts pipelines that are actively running (not queued).

    Args:
        project_id: Project to count active pipelines for.
        exclude_issue: Issue number to exclude from the count (prevents
            a pipeline from counting itself during the queue gate check).
    """
    count = 0
    for issue_number, state in _pipeline_states.items():
        if issue_number == exclude_issue:
            continue
        if getattr(state, "project_id", None) == project_id and not getattr(state, "queued", False):
            count += 1
    return count


def get_queued_pipelines_for_project(project_id: str) -> list[Any]:
    """Return all queued pipelines for a project, sorted by started_at (FIFO).

    Used by the dequeue logic to find the next pipeline to start.
    """
    queued = [
        state
        for state in _pipeline_states.values()
        if getattr(state, "project_id", None) == project_id and getattr(state, "queued", False)
    ]
    # Sort by started_at (oldest first) for FIFO ordering
    _epoch = datetime.min.replace(tzinfo=UTC)
    queued.sort(key=lambda s: s.started_at or _epoch)
    return queued


async def set_pipeline_state(issue_number: int, state: Any) -> None:
    """Write-through: persist to SQLite first, then update L1 cache.

    SQLite is written first so that L1 only reflects successfully persisted
    state.  Uses ``ON CONFLICT … DO UPDATE`` to preserve the original
    ``created_at`` timestamp on updates.
    """
    async with _get_store_lock():
        if _db is not None:
            try:
                row = _pipeline_state_to_row(issue_number, state)
                await _db.execute(
                    """INSERT INTO pipeline_states
                       (issue_number, project_id, status, agent_name, agent_instance_id,
                        pr_number, pr_url, sub_issues, metadata, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(issue_number) DO UPDATE SET
                         project_id = excluded.project_id,
                         status = excluded.status,
                         agent_name = excluded.agent_name,
                         agent_instance_id = excluded.agent_instance_id,
                         pr_number = excluded.pr_number,
                         pr_url = excluded.pr_url,
                         sub_issues = excluded.sub_issues,
                         metadata = excluded.metadata,
                         updated_at = excluded.updated_at""",
                    row,
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to persist pipeline state for issue %d", issue_number, exc_info=True
                )
                return  # Don't update L1 if SQLite write failed
        _pipeline_states[issue_number] = state


async def persist_pipeline_state_to_db(issue_number: int, state: Any) -> None:
    """Persist pipeline state to SQLite only (no L1 cache update).

    Used by background write-behind tasks where L1 is already updated
    synchronously by the caller to avoid stale-overwrite race conditions.
    """
    async with _get_store_lock():
        if _db is not None:
            try:
                row = _pipeline_state_to_row(issue_number, state)
                await _db.execute(
                    """INSERT INTO pipeline_states
                       (issue_number, project_id, status, agent_name, agent_instance_id,
                        pr_number, pr_url, sub_issues, metadata, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(issue_number) DO UPDATE SET
                         project_id = excluded.project_id,
                         status = excluded.status,
                         agent_name = excluded.agent_name,
                         agent_instance_id = excluded.agent_instance_id,
                         pr_number = excluded.pr_number,
                         pr_url = excluded.pr_url,
                         sub_issues = excluded.sub_issues,
                         metadata = excluded.metadata,
                         updated_at = excluded.updated_at""",
                    row,
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to persist pipeline state for issue %d", issue_number, exc_info=True
                )


async def delete_pipeline_state(issue_number: int) -> None:
    """Remove from both L1 cache and SQLite."""
    async with _get_store_lock():
        _pipeline_states.pop(issue_number, None)
        if _db is not None:
            try:
                await _db.execute(
                    "DELETE FROM pipeline_states WHERE issue_number = ?", (issue_number,)
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to delete pipeline state for issue %d", issue_number, exc_info=True
                )


# ── Issue Main Branches ─────────────────────────────────────────


def get_main_branch(issue_number: int) -> Any:
    """Read main branch info — L1 cache with SQLite fallback via async variant."""
    return _issue_main_branches.get(issue_number)


async def get_main_branch_async(issue_number: int) -> Any:
    """Read main branch info with async SQLite fallback on L1 miss."""
    info = _issue_main_branches.get(issue_number)
    if info is not None:
        return info
    if _db is not None:
        try:
            cursor = await _db.execute(
                "SELECT * FROM issue_main_branches WHERE issue_number = ?",
                (issue_number,),
            )
            row = await cursor.fetchone()
            if row is not None:
                info = _row_to_main_branch(row)
                _issue_main_branches[issue_number] = info
                return info
        except aiosqlite.Error:
            logger.error(
                "Failed to read main branch from SQLite for issue %d",
                issue_number,
                exc_info=True,
            )
    return None


async def set_main_branch(issue_number: int, info: Any) -> None:
    """Write-through: update L1 cache AND SQLite atomically."""
    async with _get_store_lock():
        _issue_main_branches[issue_number] = info
        if _db is not None:
            try:
                await _db.execute(
                    """INSERT OR REPLACE INTO issue_main_branches
                       (issue_number, branch, pr_number, head_sha) VALUES (?, ?, ?, ?)""",
                    (issue_number, info["branch"], info["pr_number"], info.get("head_sha", "")),
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to persist main branch for issue %d", issue_number, exc_info=True
                )


async def delete_main_branch(issue_number: int) -> None:
    """Remove from both L1 cache and SQLite."""
    async with _get_store_lock():
        _issue_main_branches.pop(issue_number, None)
        if _db is not None:
            try:
                await _db.execute(
                    "DELETE FROM issue_main_branches WHERE issue_number = ?", (issue_number,)
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to delete main branch for issue %d", issue_number, exc_info=True
                )


# ── Sub-Issue Map ────────────────────────────────────────────────


def get_sub_issue_map(issue_number: int) -> dict[str, dict]:
    """Read sub-issue mapping from L1 cache."""
    mappings = _issue_sub_issue_map.get(issue_number)
    return dict(mappings) if mappings is not None else {}


async def set_sub_issue_map(issue_number: int, mappings: dict[str, dict]) -> None:
    """Write-through: merge into L1 cache AND SQLite atomically."""
    async with _get_store_lock():
        existing = _issue_sub_issue_map.get(issue_number, {})
        existing.update(mappings)
        _issue_sub_issue_map[issue_number] = existing

        if _db is not None:
            try:
                for agent_name, entry in mappings.items():
                    await _db.execute(
                        """INSERT OR REPLACE INTO issue_sub_issue_map
                           (issue_number, agent_name, sub_issue_number, sub_issue_node_id, sub_issue_url)
                           VALUES (?, ?, ?, ?, ?)""",
                        (
                            issue_number,
                            agent_name,
                            entry.get("number", 0),
                            entry.get("node_id", ""),
                            entry.get("url", ""),
                        ),
                    )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to persist sub-issue map for issue %d", issue_number, exc_info=True
                )


async def delete_sub_issue_map(issue_number: int) -> None:
    """Remove from both L1 cache and SQLite."""
    async with _get_store_lock():
        _issue_sub_issue_map.pop(issue_number, None)
        if _db is not None:
            try:
                await _db.execute(
                    "DELETE FROM issue_sub_issue_map WHERE issue_number = ?", (issue_number,)
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error(
                    "Failed to delete sub-issue map for issue %d", issue_number, exc_info=True
                )


# ── Trigger Inflight Guard ──────────────────────────────────────


def get_trigger_inflight(trigger_key: str) -> datetime | None:
    """Read trigger guard timestamp from L1 cache."""
    return _agent_trigger_inflight.get(trigger_key)


async def set_trigger_inflight(trigger_key: str, started_at: datetime) -> None:
    """Write-through: update L1 cache AND SQLite atomically."""
    async with _get_store_lock():
        _agent_trigger_inflight[trigger_key] = started_at
        if _db is not None:
            try:
                await _db.execute(
                    "INSERT OR REPLACE INTO agent_trigger_inflight (trigger_key, started_at) VALUES (?, ?)",
                    (trigger_key, started_at.isoformat()),
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error("Failed to persist trigger inflight: %s", trigger_key, exc_info=True)


async def delete_trigger_inflight(trigger_key: str) -> None:
    """Remove from both L1 cache and SQLite."""
    async with _get_store_lock():
        _agent_trigger_inflight.pop(trigger_key, None)
        if _db is not None:
            try:
                await _db.execute(
                    "DELETE FROM agent_trigger_inflight WHERE trigger_key = ?", (trigger_key,)
                )
                await _db.commit()
            except aiosqlite.Error:
                logger.error("Failed to delete trigger inflight: %s", trigger_key, exc_info=True)


async def clear_all_trigger_inflights() -> None:
    """Clear all trigger inflight markers from both L1 and SQLite."""
    async with _get_store_lock():
        _agent_trigger_inflight.clear()
        if _db is not None:
            try:
                await _db.execute("DELETE FROM agent_trigger_inflight")
                await _db.commit()
            except aiosqlite.Error:
                logger.error("Failed to clear trigger inflights", exc_info=True)
