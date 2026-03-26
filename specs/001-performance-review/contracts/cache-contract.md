# Cache Contract

**Feature**: 001-performance-review  
**Date**: 2026-03-26  
**Governs**: FR-004, FR-005, FR-006, FR-007

## Purpose

Define the backend cache behavior contract for board data and sub-issue data. This contract specifies when caches are populated, reused, refreshed, and invalidated, ensuring consistent behavior across all code paths that interact with board data.

## Cache Entries

### Board Data Cache

**Key Pattern**: `board_data:{project_id}`  
**TTL**: 300 seconds (5 minutes)  
**Hash**: SHA256 of JSON-serialized board payload

| Operation | Trigger | Behavior |
|-----------|---------|----------|
| **Populate** | First board request for a project | Fetch from GitHub API, compute hash, store with TTL |
| **Serve (warm)** | Board request within TTL | Return cached value; zero GitHub API calls (FR-007) |
| **Serve (stale)** | Board request after TTL, API error | Return expired value as degraded fallback |
| **Refresh TTL** | `cached_fetch()` detects unchanged hash | Reset `expires_at` without replacing value (prevents cache thrashing) |
| **Replace** | `cached_fetch()` detects changed hash | Store new value, new hash, new TTL |
| **Invalidate** | Manual refresh (`refresh=true`) | Delete cache entry; next request forces cold fetch |
| **Invalidate** | Status update (`PATCH .../status`) | Delete `board_data:{project_id}` entry |

**Invariants**:
- A warm-cache board request MUST NOT make any upstream GitHub API call (SC-002).
- Hash comparison MUST use the stored `data_hash` field, not full value comparison.
- Stale fallback MUST only be used when the upstream API call fails, not as a default path.

### Sub-Issue Cache

**Key Pattern**: `sub_issues:{owner}/{repo}#{issue_number}`  
**TTL**: 300 seconds (5 minutes)  
**Hash**: SHA256 of JSON-serialized sub-issue list

| Operation | Trigger | Behavior |
|-----------|---------|----------|
| **Populate** | First sub-issue expansion for an issue | Fetch from GitHub API, store with TTL |
| **Reuse** | Automatic board refresh (non-manual) | Return cached value; skip GitHub API call for sub-issues (FR-005) |
| **Invalidate** | Manual refresh (`refresh=true`) | Clear all sub-issue cache entries for the project |
| **Expire** | TTL elapsed | Next access triggers fresh fetch |

**Invariants**:
- Automatic refreshes (auto-refresh timer, WebSocket-triggered) MUST reuse cached sub-issue data (FR-005).
- Only manual refresh (`refresh=true`) SHOULD clear sub-issue cache entries.
- Sub-issue cache MUST NOT be invalidated by status updates to individual items.

### Projects List Cache

**Key Pattern**: `board_projects:{user_id}`  
**TTL**: 300 seconds (5 minutes)

| Operation | Trigger | Behavior |
|-----------|---------|----------|
| **Populate** | First projects list request | Fetch from GitHub API, store with TTL |
| **Serve** | Request within TTL | Return cached list |
| **Expire** | TTL elapsed | Next request fetches fresh list |

### Repository Resolution Cache

**Key Pattern**: In-memory dict in `resolve_repository()`, scoped by `token_hash`  
**TTL**: 300 seconds (5 minutes)

| Operation | Trigger | Behavior |
|-----------|---------|----------|
| **Populate** | First `resolve_repository()` call for a token+project | Execute 4-step fallback, cache result |
| **Serve** | Subsequent call within TTL for same token+project | Return cached `(owner, repo)` tuple |
| **Expire** | TTL elapsed | Next call re-executes fallback chain |

**Invariants**:
- Cache MUST be scoped by access token hash to prevent cross-user pollution.
- Fallback order: in-memory cache → GraphQL → REST → workflow config → default repo.

## WebSocket Change Detection

**Scope**: `projects.py` WebSocket subscription endpoint

| Step | Behavior |
|------|----------|
| 1. Fetch tasks | Use `cached_fetch()` with stale revalidation |
| 2. Compute hash | SHA256 of task payload |
| 3. Compare hash | Compare against last-sent hash for this connection |
| 4a. Hash unchanged | Suppress `refresh` message; log as no-change (FR-004) |
| 4b. Hash changed | Send `refresh` message with new data; update stored hash |
| 5. Stale limit | After 10 consecutive stale returns, force fresh fetch |

**Invariants**:
- Unchanged data MUST NOT generate a `refresh` WebSocket message (FR-004).
- Stale revalidation counter MUST reset on any actual data change.
- Connection failure MUST fall back to stale data, not error out.

## Rate-Limit-Aware Behavior

| Remaining Quota | Cache Behavior |
|-----------------|----------------|
| > 200 | Normal operation |
| 100–200 | Skip expensive polling steps; cache serves more aggressively |
| 50–100 | Serve stale cache on errors; skip non-essential fetches |
| < 50 | Pause polling; serve only cached data; wait for reset window |

**Invariants**:
- Rate-limited responses MUST be served from stale cache, not retried in a tight loop.
- Rate limit state MUST be exposed to the frontend for UI indication (`isRateLimitLow`).
