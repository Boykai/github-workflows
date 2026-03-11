# Refresh Contract: Performance Review

**Feature**: 001-performance-review
**Date**: 2026-03-11
**Version**: 1.0

## Purpose

This document defines the single coherent refresh policy governing all paths that can trigger board-related data updates. It satisfies FR-009 (one documented refresh contract) and prevents the previous pattern of broad invalidation recreating a polling storm (FR-011).

## Refresh Sources

| Source | Trigger | Default Scope | Condition for Full Board Reload |
|--------|---------|---------------|-------------------------------|
| WebSocket `task_update` / `task_created` / `status_changed` | Server pushes task-level change | **Task only** | Never — task changes do not trigger board reload |
| WebSocket `refresh` | Server pushes periodic task-level event | **Task only** | Never — board data refreshes on its own 5-minute auto-refresh schedule |
| WebSocket `blocking_queue_updated` | Server pushes blocking queue change | **Blocking queue only** | Never — blocking queue changes do not trigger board reload |
| Fallback polling | 30-second interval when WebSocket unavailable | **Task only** | Never — fallback polling never triggers board reload |
| Auto-refresh | 5-minute interval via `useBoardRefresh` | **Full board** | Always — this is the scheduled board freshness mechanism |
| Manual refresh | User clicks refresh button | **Full board** | Always — manual refresh bypasses all caches (FR-008) |

## Rules

### Rule 1: Lightweight Updates Stay Lightweight

Task-level updates (WebSocket `task_*` messages, fallback polling) MUST invalidate only the tasks query (`['projects', projectId, 'tasks']`). They MUST NOT trigger a full board data refetch.

**Rationale**: Decoupling task freshness from board freshness prevents the O(N) cost of a full board reload for every O(1) task change (FR-010).

### Rule 2: Board Reloads Are Gated

A full board data refetch occurs only when one of these conditions is met:

1. The auto-refresh timer fires (5-minute interval, gated by page visibility).
2. The user explicitly triggers a manual refresh.

All other refresh paths produce lightweight updates only.

**Rationale**: Suppressing unchanged-state board reloads satisfies FR-004 (no repeated automatic full refreshes for unchanged state) and SC-001 (0 repeated automatic full board refreshes during idle observation).

### Rule 3: Deduplication

If multiple full-board-reload triggers arrive within a short window, only one refetch executes. Priority order:

1. Manual refresh (always wins, bypasses cache).
2. Auto-refresh (subsequent duplicates within the window are suppressed).

**Rationale**: Prevents concurrent triggers from producing two full board reloads in rapid succession.

### Rule 4: Fallback Coordination

When the system is in fallback polling mode (WebSocket unavailable):

- The fallback poll continues at 30-second intervals for task freshness.
- The auto-refresh timer continues at 5-minute intervals for board freshness.
- The auto-refresh timer MAY be extended (not shortened) if the most recent fallback poll already confirmed no task changes, to reduce combined invalidation volume.

**Rationale**: Both paths serve different purposes (task freshness vs. board freshness) and should not be collapsed, but their combined activity should not exceed what either path would produce alone (FR-006, FR-011).

### Rule 5: Manual Refresh Is Unconditional

Manual refresh MUST always:

- Send `refresh=true` to the backend, bypassing the TTL cache.
- Clear the sub-issue cache for the refreshed board.
- Return a fully fresh board state regardless of cache or change-detection status.

**Rationale**: The user's explicit intent to see fresh data must not be suppressed by optimization logic (FR-008, SC-007).

## Sequence Diagrams

### Lightweight Task Update (WebSocket)

```text
Server ──[task_update]──▶ useRealTimeSync
                              │
                              ▼
                    invalidate(['projects', projectId, 'tasks'])
                              │
                              ▼
                    TanStack Query refetches tasks only
                              │
                              ▼
                    Board components with changed tasks re-render
                    (unchanged columns/cards skip via React.memo)
```

### WebSocket Refresh (Task-Level)

```text
Server ──[refresh (task hash changed)]──▶ useRealTimeSync
                                               │
                                               ▼
                                     invalidate(['projects', projectId, 'tasks'])
                                               │
                                               ▼
                                     TanStack Query refetches tasks only
                                               │
                                               ▼
                                     Board auto-refresh timer reset
```

### WebSocket Refresh (Unchanged)

```text
Server ──[task hash unchanged]──▶ (suppressed server-side, no message sent)
```

### Manual Refresh

```text
User ──[click refresh]──▶ useBoardRefresh
                               │
                               ▼
                     fetch board with refresh=true
                     (bypass cache, clear sub-issue cache)
                               │
                               ▼
                     Full board re-render with fresh data
```

## Frontend Query Key Reference

| Query Key Pattern | Refresh Sources | Stale Time |
|-------------------|----------------|------------|
| `['board', 'data', projectId]` | Auto-refresh, manual refresh | 5 minutes (aligned with auto-refresh) |
| `['projects', projectId, 'tasks']` | WebSocket `task_*`, fallback polling | 60 seconds |
| `['blocking-queue', projectId]` | WebSocket `blocking_queue_updated` | 60 seconds |
| `['projects']` (list) | None (stale-while-revalidate) | 15 minutes |

## Success Criteria Mapping

| Contract Rule | Success Criterion |
|--------------|-------------------|
| Rule 1 (Lightweight stays lightweight) | SC-004: Task updates appear within 5s without full board reload |
| Rule 2 (Board reloads are gated) | SC-001: 0 repeated automatic full board refreshes during idle |
| Rule 2 (Board reloads are gated) | SC-002: ≥30% fewer upstream requests for warm refresh |
| Rule 3 (Deduplication) | SC-001, SC-003: No unnecessary full reloads |
| Rule 4 (Fallback coordination) | SC-003: 0 unnecessary full board reloads in fallback mode |
| Rule 5 (Manual is unconditional) | SC-007: Manual refresh returns full fresh board 100% of the time |
