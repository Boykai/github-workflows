# Data Model: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09

## Overview

This feature introduces no new database entities or API models. All changes modify existing in-memory state, cache behavior, rendering patterns, and event handling. This document describes the data structures and behavioral entities affected by the optimization work.

## Entities

### 1. Board Data Cache Entry (existing, verified)

**Location**: `backend/src/services/cache.py` global `cache` instance
**Key format**: `board_data:{project_id}`
**TTL**: 300 seconds (5 minutes) — aligned with frontend `AUTO_REFRESH_INTERVAL_MS`

| Field | Type | Description |
|-------|------|-------------|
| `value` | `BoardDataResponse` | Cached board data including columns, items, and metadata |
| `expires_at` | `datetime` | UTC expiration timestamp (entry creation + 300s) |
| `etag` | `str \| None` | Optional ETag from API response |
| `last_modified` | `str \| None` | Optional Last-Modified header |

**Lifecycle**:
- Created on board data fetch via `get_board_data()`
- Served from cache on non-manual refresh requests
- Expires after 300 seconds
- Force-cleared when `refresh=true` is passed to the board endpoint

### 2. Sub-Issue Cache Entry (existing, verified)

**Location**: `backend/src/services/cache.py` global `cache` instance
**Key format**: `sub_issues:{owner}/{repo}#{issue_number}`
**TTL**: 600 seconds (10 minutes)

| Field | Type | Description |
|-------|------|-------------|
| `value` | `list[dict]` | Raw sub-issue data from GitHub REST API response |
| `expires_at` | `datetime` | UTC expiration timestamp (entry creation + 600s) |

**Lifecycle**:
- Created on first `get_sub_issues()` call for an issue
- Served from cache on subsequent calls within TTL window
- Expires automatically after 600 seconds
- Force-cleared when `refresh=true` is passed to the board endpoint (iterates all items, deletes per-issue cache entries)

### 3. WebSocket Refresh Hash (existing, verified)

**Location**: Local variable in `backend/src/api/projects.py` WebSocket handler
**Scope**: Per-connection, lives for the duration of a WebSocket session
**Not persisted**: Garbage collected when WebSocket disconnects

| Field | Type | Description |
|-------|------|-------------|
| `last_sent_hash` | `str \| None` | SHA-256 hex digest of the last sent task list JSON. `None` on first cycle. |

**Lifecycle**:
- Initialized to `None` when WebSocket connection opens
- Updated to new hash value each time a refresh message is sent
- Compared against current data hash on each 30-second cycle
- Garbage collected when WebSocket connection closes

### 4. Performance Baseline (new documentation artifact — not code)

**Location**: Captured in measurement protocol documentation before optimization work begins
**Scope**: Project-level, captured once before changes and once after for comparison

| Metric | Type | Description |
|--------|------|-------------|
| `idle_api_call_count` | `int` | Number of outbound API calls during 5-minute idle window |
| `board_endpoint_response_time_ms` | `float` | Board endpoint response time in milliseconds |
| `sub_issue_fetch_count` | `int` | Number of sub-issue API calls per board refresh |
| `board_initial_render_time_ms` | `float` | Time from page load to board fully rendered |
| `single_card_rerender_count` | `int` | Number of component re-renders for a single-card update |
| `drag_fps` | `float` | Frames per second during chat popup drag interaction |
| `event_handler_invocations_per_sec` | `float` | Event handler frequency during drag/scroll interactions |

**Lifecycle**:
- Captured before any optimization code changes (Phase 1)
- Recaptured after optimization changes using identical protocol (Phase 3)
- Before/after comparison documented with improvement percentages

### 5. Refresh Event (behavioral entity — not a data structure)

**Description**: Represents a trigger to update board data. Has a source and a scope.

| Property | Values | Description |
|----------|--------|-------------|
| `source` | `websocket`, `fallback_polling`, `auto_refresh`, `manual_refresh` | What triggered the refresh |
| `scope` | `task_only`, `full_board` | Whether the refresh targets individual task data or the entire board |
| `bypasses_cache` | `boolean` | Whether the refresh bypasses backend caches |

**Refresh Policy Matrix** (target state):

| Source | Scope | Bypasses Cache | Triggers Board Re-fetch |
|--------|-------|----------------|------------------------|
| WebSocket message | task_only | No | No |
| Fallback polling | task_only | No | No |
| Auto-refresh (5 min timer) | full_board | No (uses backend cache) | Yes (via `invalidateQueries`) |
| Manual refresh (button click) | full_board | Yes (`refresh=true`) | Yes (direct fetch + `setQueryData`) |

### 6. Frontend Query Keys (existing, documented)

**Location**: TanStack React Query cache in frontend

| Query Key | Owner Hook | staleTime | Refresh Mechanism |
|-----------|------------|-----------|-------------------|
| `['board', 'projects']` | `useProjectBoard.ts` | 15 min (900s) | Background refetch |
| `['board', 'data', projectId]` | `useProjectBoard.ts` | 60 sec | `useBoardRefresh` auto/manual |
| `['projects', projectId, 'tasks']` | External (tasks hook) | Default | `useRealTimeSync` WebSocket/polling |
| `['blocking-queue', projectId]` | External (blocking hook) | Default | `useRealTimeSync` WebSocket |

## Relationships

```text
Board Data Request
  ├── Board Data Cache (TTL: 300s)
  │     └── on cache miss → GitHub GraphQL API
  └── Sub-Issue Cache (TTL: 600s, per-issue)
        └── on cache miss → GitHub REST API

WebSocket Connection
  └── last_sent_hash (per-connection, in-memory)
        └── compared against SHA-256(current_tasks_json)

Manual Refresh
  ├── Bypasses Board Data Cache (refresh=true)
  ├── Clears Sub-Issue Cache (iterates all items)
  └── Resets Auto-Refresh Timer

Frontend Refresh Coordination
  ├── useRealTimeSync → invalidates tasks query only (not board data)
  ├── useBoardRefresh → manages board data refresh (auto + manual)
  │     ├── Auto: invalidateQueries (allows backend cache hit)
  │     └── Manual: direct fetch with refresh=true
  └── useProjectBoard → owns query definitions and staleTime config
```

## Validation Rules

- Board data cache TTL (300s) must be ≥ frontend auto-refresh interval (300s) to prevent unnecessary cache misses
- Sub-issue cache TTL (600s) must be > board data cache TTL (300s) to ensure sub-issue cache is warm across board refreshes
- Manual refresh must always bypass both board data and sub-issue caches
- WebSocket reconnection debounce (2s) must prevent cascading invalidation storms
- Fallback polling (30s) must not trigger board data invalidation, only task query invalidation
- Refresh deduplication (`isRefreshingRef`) must prevent concurrent board data fetches

## State Transitions

### WebSocket Connection State

```text
disconnected → connecting → connected
                    ↓
               polling (fallback)
                    ↓
              connecting (reconnect with exponential backoff)
                    ↓
               connected (stops polling)
```

### Refresh Deduplication State

```text
idle → refreshing (isRefreshingRef = true)
            ↓
       [concurrent request arrives → rejected]
            ↓
       idle (isRefreshingRef = false)
```

### Page Visibility and Auto-Refresh

```text
visible + timer running → hidden (timer paused)
                              ↓
                         visible (check staleness)
                              ↓
                     [stale: immediate refresh + restart timer]
                     [fresh: restart timer only]
```
