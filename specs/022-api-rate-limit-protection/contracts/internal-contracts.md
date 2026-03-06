# Internal Contracts: Reduce GitHub API Rate Limit Consumption

**Feature**: 022-api-rate-limit-protection  
**Date**: 2026-03-06

## Overview

This feature introduces no new API endpoints. All changes are internal behavioral modifications to existing endpoints and WebSocket handlers. This document defines the behavioral contracts that must be preserved.

## Contract 1: WebSocket Refresh Message Contract

**Location**: `backend/src/api/projects.py` — WebSocket `/ws/projects/{project_id}/subscribe`

### Current behavior (to be changed):
- Every 30 seconds, sends `{"type": "refresh", "tasks": [...], "count": N}` unconditionally

### New behavior:
- Every 30 seconds, fetches tasks and computes SHA-256 hash of serialized task list
- **Only sends** `{"type": "refresh", ...}` if hash differs from previous send
- First cycle always sends (no previous hash to compare)
- Message format unchanged — no breaking changes to frontend contract

### Invariants:
- `initial_data` message on connection open: always sent (unchanged)
- `refresh` message: sent only when data has changed
- `pong` response to `ping`: always sent (unchanged)

## Contract 2: Frontend Query Invalidation Contract

**Location**: `frontend/src/hooks/useRealTimeSync.ts`

### Current behavior (to be changed):
- On `initial_data`, `refresh`, `task_update`, `task_created`, `status_changed` messages:
  - Invalidates `['projects', projectId, 'tasks']` ✅
  - Invalidates `['board', 'data', projectId]` ❌ (to be removed)

### New behavior:
- On all WebSocket message types:
  - Invalidates `['projects', projectId, 'tasks']` only
  - Does NOT invalidate `['board', 'data', projectId]`
- Board data refreshes on its own schedule via `refetchInterval` / `AUTO_REFRESH_INTERVAL_MS`

### Invariants:
- Manual refresh (user-initiated) still invalidates both query keys (unchanged path)
- Board data auto-refresh interval remains 5 minutes

## Contract 3: Sub-Issue Cache Contract

**Location**: `backend/src/services/github_projects/service.py` — `get_sub_issues()`

### Current behavior (to be changed):
- Always makes REST API call to `GET /repos/{owner}/{repo}/issues/{issue_number}/sub_issues`

### New behavior:
- Checks `InMemoryCache` for key `sub_issues:{owner}/{repo}#{issue_number}`
- On cache hit: returns cached value, no API call
- On cache miss: makes REST API call, caches result with 600s TTL, returns result
- Logs cache hit/miss events at DEBUG level

### Invariants:
- Return type unchanged: `list[dict]`
- Error handling unchanged: returns `[]` on failure
- API call parameters unchanged when cache miss occurs

## Contract 4: Board Data Cache TTL Contract

**Location**: `backend/src/api/board.py`

### Current behavior (to be changed):
- `cache.set(cache_key, board_data, ttl_seconds=120)`

### New behavior:
- `cache.set(cache_key, board_data, ttl_seconds=300)`

### Invariants:
- `refresh=true` query parameter bypasses cache entirely (unchanged)
- Cache key format unchanged
- Cached data structure unchanged

## Contract 5: Manual Refresh Cache Bypass

**Location**: `backend/src/api/board.py` — board data endpoint

### Behavior (preserved):
- When `refresh=true` query parameter is present:
  - Board data cache is bypassed
  - Sub-issue caches for the project's issues should also be cleared (new behavior)
  - All data is fetched fresh from GitHub API

### Invariants:
- Manual refresh always produces fresh data
- Manual refresh repopulates all caches with fresh data
