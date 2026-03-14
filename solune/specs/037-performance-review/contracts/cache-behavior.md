# Cache Contract: Backend Caching Behavior

**Feature**: 037-performance-review  
**Date**: 2026-03-12  
**Version**: 1.0

## Purpose

Defines the caching behavior for board-related data in the backend, ensuring consistent TTLs, invalidation semantics, and stale-data fallback behavior across all API endpoints and background services.

## Cache Entries

### Board Data Cache

| Property | Value |
|----------|-------|
| Key pattern | `board_data:{project_id}` |
| TTL | 300 seconds (5 minutes) |
| Invalidation | Manual refresh (`refresh=true`) bypasses and repopulates |
| Stale fallback | Served on rate limit (429) and server errors (5xx) |
| Scope | Per-project, shared across all users viewing the same project |

### Board Projects Cache

| Property | Value |
|----------|-------|
| Key pattern | `board_projects:{user_id}` |
| TTL | 300 seconds (5 minutes) |
| Fallback chain | 1. board_projects cache → 2. generic projects cache → 3. fresh fetch |
| Stale fallback | Served on rate limit and server errors |

### Sub-Issue Cache

| Property | Value |
|----------|-------|
| Key pattern | `sub_issues:{owner}/{repo}#{issue_number}` |
| TTL | 300 seconds (5 minutes) |
| Invalidation | Cleared per-item on manual refresh BEFORE re-fetching board data |
| Reuse | MUST be consulted during board data construction when warm (new requirement) |
| Scope | Per-issue, shared across all board views containing this issue |

### Project Tasks Cache

| Property | Value |
|----------|-------|
| Key pattern | `project:items:{project_id}` |
| TTL | 300 seconds (5 minutes) |
| Invalidation | `refresh=true` parameter bypasses cache |
| Stale fallback | Served on rate limit and server errors |

### Metadata Cache

| Property | Value |
|----------|-------|
| Key pattern | Various (`repo:agents:*`, labels, branches) |
| TTL | 3600 seconds (1 hour) |
| Rationale | Metadata changes infrequently; longer TTL reduces API pressure |

## Cache Interaction Rules

### Rule 1: Sub-Issue Cache Reuse

When constructing board data (non-manual refresh path):
1. For each board item with sub-issues, check `sub_issues:{owner}/{repo}#{issue_number}` cache
2. If cache entry exists and is not expired, use cached sub-issue data
3. If cache entry is expired or missing, fetch from GitHub and populate cache
4. This MUST reduce the total outbound call count when sub-issue caches are warm

### Rule 2: Manual Refresh Cache Bypass

When manual refresh is requested (`refresh=true`):
1. Clear sub-issue caches for ALL items in the current board
2. Bypass board data cache
3. Fetch fresh board data from GitHub (including fresh sub-issues)
4. Populate board data cache and sub-issue caches with fresh data

### Rule 3: Stale Data Fallback

When GitHub API returns an error during a non-manual refresh:
1. Check for rate limit error (429 or `X-RateLimit-Remaining: 0`)
2. Check for server error (5xx)
3. If stale cached data is available (`get_stale()` method), return it with appropriate headers
4. If no stale data available, propagate the error

### Rule 4: Hash-Based Change Detection

For WebSocket subscription periodic checks:
1. Fetch data (from cache if available)
2. Compute SHA-256 hash with `compute_data_hash()` (deterministic, `sort_keys=True`)
3. Compare against previously stored hash
4. Send to client ONLY if hash differs
5. This prevents unnecessary network traffic and client-side processing

### Rule 5: Cycle Cache Management

For polling loop operations:
1. Clear cycle cache (`clear_cycle_cache()`) at the start of each polling cycle
2. Within a cycle, cycle cache prevents redundant fetches for the same data
3. Cycle cache is NOT the same as the main InMemoryCache — it is per-cycle only
4. Inflight request coalescing (BoundedDict, max 256) prevents duplicate concurrent GraphQL requests

## TTL Alignment

| Component | Interval/TTL | Purpose |
|-----------|-------------|---------|
| Board data cache (backend) | 300s | Prevents redundant GitHub API calls |
| Auto-refresh timer (frontend) | 300s (5 min) | Periodic board data refresh |
| WebSocket poll interval (backend) | 30s | Check for data changes |
| Fallback polling interval (frontend) | 30s | Check for changes when WS down |
| Task query stale time (frontend) | 60s | TanStack Query freshness window |
| Board data stale time (frontend) | 60s | TanStack Query freshness window |
| Projects list stale time (frontend) | 900s (15 min) | Projects change infrequently |

## Non-Goals

- This contract does NOT define cache size limits or eviction policies beyond TTL.
- This contract does NOT define distributed cache behavior (current implementation is single-process in-memory).
- This contract does NOT define cache warming strategies on application startup.
