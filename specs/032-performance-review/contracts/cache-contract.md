# Cache Contract: Performance Review

**Feature**: 032-performance-review
**Date**: 2026-03-09
**Source**: [spec.md](../spec.md) FR-004 through FR-007, [research.md](../research.md) Areas 1-2

## Overview

Defines the caching behavior contracts for backend board data and sub-issue data. These contracts ensure that caches reduce external API call volume without serving stale data when freshness is required.

## Contract 1: Board Data Cache

**Location**: `backend/src/api/board.py` → `backend/src/services/cache.py`

### Invariants

1. Board data cache TTL MUST be 300 seconds (5 minutes), aligned with the frontend auto-refresh interval.
2. A request with `refresh=true` MUST bypass the board data cache entirely and fetch fresh data from the external API.
3. A request without `refresh=true` MUST serve from cache if the entry exists and TTL has not expired.
4. Cache entries MUST be keyed by project ID to prevent cross-project data leaks.

### Behavior Table

| Request Type | Cache State | Expected Behavior | External API Calls |
|--------------|-------------|-------------------|--------------------|
| Automatic refresh | Cache valid (TTL not expired) | Serve from cache | 0 |
| Automatic refresh | Cache expired or missing | Fetch from API, cache result | 1+ (GraphQL pagination) |
| Manual refresh (`refresh=true`) | Any | Fetch from API, update cache | 1+ (GraphQL pagination) |

### Error Behavior

- If the external API returns an error during a cache miss, the endpoint MUST NOT cache the error response.
- If stale cache data exists and the API is unavailable, the system MAY serve stale data with appropriate headers (graceful degradation).

---

## Contract 2: Sub-Issue Data Cache

**Location**: `backend/src/services/github_projects/service.py` → `backend/src/services/cache.py`

### Invariants

1. Sub-issue data MUST be cached per-issue with key format `sub_issues:{owner}/{repo}#{issue_number}`.
2. Sub-issue cache TTL MUST be 600 seconds (10 minutes).
3. Cache hit: the system MUST NOT make an external API call for that issue's sub-issues.
4. Cache miss: the system MUST make a REST call to `/repos/{owner}/{repo}/issues/{issue_number}/sub_issues`.
5. Manual refresh (`refresh=true`) MUST clear sub-issue caches for affected issues before fetching.
6. Automatic refresh MUST use cached sub-issue data when available (no cache bypass).

### Behavior Table

| Refresh Type | Sub-Issue Cache State | Expected Behavior | Per-Issue API Calls |
|--------------|-----------------------|-------------------|---------------------|
| Automatic | Cache valid | Serve from cache | 0 |
| Automatic | Cache expired or missing | Fetch from API, cache result | 1 |
| Manual (`refresh=true`) | Any | Clear cache, fetch from API, cache result | 1 |

### Performance Contract

- Cold-cache board refresh with N issues: up to N+M external API calls (N sub-issue fetches + M GraphQL calls)
- Warm-cache board refresh with N issues: at most M external API calls (0 sub-issue fetches + M GraphQL calls)
- Target: warm-cache refresh uses at least 50% fewer external API calls than cold-cache refresh (SC-002)

### Error Behavior

- If a sub-issue fetch fails, return an empty list for that issue (graceful degradation).
- Failed fetches MUST NOT be cached (prevent caching error state).
- Cache hit/miss events SHOULD be logged at debug level for observability (FR-010 from Spec 022).

---

## Contract 3: Change Detection Cache (WebSocket)

**Location**: `backend/src/api/projects.py` (subscription flow)

### Invariants

1. The server MUST maintain a hash of the last-sent task data per active WebSocket subscription.
2. Before sending a refresh/update message, the server MUST compare the current data hash with the stored hash.
3. If hashes are equal (no change), the server MUST NOT send a message (no-op).
4. If hashes differ (data changed), the server MUST send the message and update the stored hash.
5. On new connection, the stored hash MUST be null/empty (first message always sent).
6. On disconnection, the stored hash MUST be cleaned up.

### Behavior Table

| Subscription State | Data Hash Comparison | Expected Behavior |
|--------------------|---------------------|-------------------|
| New connection | No previous hash | Send message, store hash |
| Active, data unchanged | Current == stored | No-op (no message sent) |
| Active, data changed | Current != stored | Send message, update hash |
| Disconnected | N/A | Clean up stored hash |

### Performance Contract

- Idle board with no data changes: zero WebSocket messages after initial data delivery.
- Target: idle API calls reduced to <100/hour (SC-001), primarily achieved by preventing unnecessary refresh cascades.
