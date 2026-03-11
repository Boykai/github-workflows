# Contract: Backend Cache Behavior

**Feature**: 034-performance-review
**Date**: 2026-03-11
**Traces to**: FR-004, FR-005, FR-008, SC-001, SC-002

## Cache TTL Contract

All cache entries follow consistent TTL policies:

| Cache Key Pattern | TTL | Stale Fallback | Invalidation |
|-------------------|-----|----------------|--------------|
| `board_data:{project_id}` | 300s | Yes (rate-limited) | Manual refresh clears entry |
| `SUB_ISSUES:{owner}/{repo}#{issue_number}` | 300s | No | Manual refresh clears all; TTL expiry otherwise |
| `PROJECT_ITEMS:{project_id}` | 300s | Yes (rate-limited) | TTL expiry |
| `PROJECTS:{user_id}` | 3600s | No | TTL expiry |
| Metadata entries | 3600s | No | TTL expiry |

### Invariants

1. **No TTL drift**: Board data and sub-issue caches MUST share the same TTL (300s) so sub-issues never outlive their parent board data.
2. **Stale-only-on-rate-limit**: `get_stale()` MUST only be called when the GitHub API returns a rate-limit error, never as a performance shortcut.
3. **Manual refresh bypass**: When `refresh=True` is passed to the board endpoint, the handler MUST call `cache.delete()` on the board data key AND iterate all related sub-issue keys, deleting each one, BEFORE fetching new data.

## Sub-Issue Cache Reuse Contract

**Goal**: Warm sub-issue caches reduce GitHub API calls during non-manual board refreshes (SC-002: ≥ 30% reduction).

### Behavior

```text
Board refresh (non-manual):
  1. Fetch board data (from cache if fresh, from API if stale/expired)
  2. For each task with has_sub_issues=true:
     a. Check SUB_ISSUES cache for this task
     b. If cache hit (fresh): use cached data, skip API call
     c. If cache miss or expired: fetch from API, cache result
  3. Return assembled board data

Board refresh (manual, refresh=true):
  1. Delete board_data cache entry
  2. Delete ALL SUB_ISSUES cache entries for this project
  3. Fetch board data from API (no cache)
  4. For each task with has_sub_issues=true:
     a. Fetch from API (no cache)
     b. Cache result with TTL=300s
  5. Cache assembled board data with TTL=300s
  6. Return assembled board data
```

### Measurement Contract

- **Metric**: `board_refresh_github_api_calls`
- **Cold cache**: Count of API calls when no cache entries exist
- **Warm cache**: Count of API calls when sub-issue caches are populated
- **Target**: Warm cache count ≤ 70% of cold cache count (SC-002)

## Cache Bounded Growth Contract

- `BoundedSet` and `BoundedDict` use FIFO eviction when capacity is reached.
- Default capacity is configurable per instance.
- GraphQL in-flight coalescing uses `BoundedDict(maxlen=256)`.
- Repository resolution memoization uses `BoundedDict(maxlen=128)`.
- No cache entry persists beyond its TTL + stale window.

## First-Pass Verification Notes

- **Sub-issue TTL alignment**: Fixed from 600s to 300s to match board data TTL (prevents inconsistent staleness).
- **Warm cache reuse**: `get_sub_issues()` in `issues.py` already checks cache before API call (confirmed).
- **Manual refresh bypass**: Board endpoint clears sub-issue caches and logs count before fetching fresh data (enhanced with instrumentation).
- **Repository resolution**: Memoized with `BoundedDict(maxlen=128)` to avoid repeated GraphQL lookups across refresh flows.
