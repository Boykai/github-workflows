# Contract: Pipeline State Store

**Feature**: `035-best-practices-overhaul` | **Phase**: 1 — Data Integrity
**File**: `backend/src/services/pipeline_state_store.py`

## Purpose

Provides durable SQLite-backed storage for pipeline orchestration state, with `BoundedDict` as an L1 in-memory cache. All writes go through both layers atomically under `asyncio.Lock`.

## Interface

```python
"""Pipeline state persistence — SQLite write-through cache."""

import asyncio
from typing import Any

import aiosqlite

from src.services.workflow_orchestrator.models import MainBranchInfo, PipelineState


# ── Initialization ──────────────────────────────────────────────

async def init_pipeline_state_store(db: aiosqlite.Connection) -> None:
    """Load all active pipeline states from SQLite into the L1 cache.

    Called once during application startup (in ``lifespan()``).
    """
    ...


# ── Pipeline States ─────────────────────────────────────────────

async def get_pipeline_state(issue_number: int) -> PipelineState | None:
    """Read pipeline state — L1 first, then SQLite fallback."""
    ...

async def set_pipeline_state(
    db: aiosqlite.Connection,
    issue_number: int,
    state: PipelineState,
) -> None:
    """Write-through: update L1 cache AND SQLite atomically."""
    ...

async def delete_pipeline_state(
    db: aiosqlite.Connection,
    issue_number: int,
) -> None:
    """Remove from both L1 cache and SQLite."""
    ...


# ── Issue Main Branches ─────────────────────────────────────────

async def get_main_branch(issue_number: int) -> MainBranchInfo | None:
    """Read main branch info — L1 first, then SQLite fallback."""
    ...

async def set_main_branch(
    db: aiosqlite.Connection,
    issue_number: int,
    info: MainBranchInfo,
) -> None:
    """Write-through: update L1 cache AND SQLite atomically."""
    ...

async def delete_main_branch(
    db: aiosqlite.Connection,
    issue_number: int,
) -> None:
    """Remove from both L1 cache and SQLite."""
    ...


# ── Sub-Issue Map ────────────────────────────────────────────────

async def get_sub_issue_map(issue_number: int) -> dict[str, dict] | None:
    """Read sub-issue mapping — L1 first, then SQLite fallback."""
    ...

async def set_sub_issue_map(
    db: aiosqlite.Connection,
    issue_number: int,
    mapping: dict[str, dict],
) -> None:
    """Write-through: update L1 cache AND SQLite atomically."""
    ...

async def delete_sub_issue_map(
    db: aiosqlite.Connection,
    issue_number: int,
) -> None:
    """Remove from both L1 cache and SQLite."""
    ...


# ── Trigger Inflight Guard ──────────────────────────────────────

async def get_trigger_inflight(trigger_key: str) -> datetime | None:
    """Read trigger guard timestamp — L1 first, then SQLite fallback."""
    ...

async def set_trigger_inflight(
    db: aiosqlite.Connection,
    trigger_key: str,
    started_at: datetime,
) -> None:
    """Write-through: update L1 cache AND SQLite atomically."""
    ...

async def delete_trigger_inflight(
    db: aiosqlite.Connection,
    trigger_key: str,
) -> None:
    """Remove from both L1 cache and SQLite."""
    ...
```

## Behavior Contract

1. **Read path**: Check L1 `BoundedDict` first. On miss, query SQLite, populate L1, return result.
2. **Write path**: Acquire `asyncio.Lock`, write to both L1 and SQLite, release lock. If SQLite write fails, the L1 write is rolled back.
3. **Startup**: `init_pipeline_state_store()` loads all active rows from SQLite into L1 caches.
4. **Eviction**: L1 evicts FIFO when at capacity (500/2000). Evicted entries remain in SQLite and are reloaded on next read.
5. **Concurrency**: All mutations are serialized per module-level `asyncio.Lock`. Reads from L1 do not require the lock (BoundedDict reads are atomic in Python).

## Migration

```sql
-- Migration: 021_pipeline_state.sql

CREATE TABLE IF NOT EXISTS pipeline_states (
    issue_number INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL,
    agent_name TEXT,
    agent_instance_id TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    sub_issues TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS issue_main_branches (
    issue_number INTEGER PRIMARY KEY,
    branch TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS issue_sub_issue_map (
    issue_number INTEGER NOT NULL,
    agent_name TEXT NOT NULL,
    sub_issue_number INTEGER NOT NULL,
    sub_issue_node_id TEXT NOT NULL,
    sub_issue_url TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (issue_number, agent_name)
);

CREATE TABLE IF NOT EXISTS agent_trigger_inflight (
    trigger_key TEXT PRIMARY KEY,
    started_at TEXT NOT NULL
);
```

## Error Handling

- SQLite connection errors during write: Log error with `logger.error(exc_info=True)`, raise `DatabaseError`.
- SQLite unavailable at startup: Log warning, start with L1 cache only. Attempt reconnection on next write.
- Corrupt JSON in `sub_issues`/`metadata` fields: Log error, return `None` (treat as cache miss), do not propagate corrupt data to L1.
