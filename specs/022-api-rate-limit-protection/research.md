# Research: Reduce GitHub API Rate Limit Consumption

**Feature**: 022-api-rate-limit-protection  
**Date**: 2026-03-06  
**Status**: Complete — all unknowns resolved

## R1: WebSocket Change Detection Strategy

**Decision**: Use `hashlib.sha256` on the JSON-serialized task list to detect changes before sending WebSocket refresh messages.

**Rationale**: Hashing is O(n) on the serialized data, which is already being serialized for sending anyway. A hash comparison is simpler and more reliable than field-by-field diffing. The `json.dumps()` call with `sort_keys=True` ensures deterministic serialization for consistent hashes.

**Alternatives considered**:
- **Field-by-field diffing**: Rejected — more complex, fragile against schema changes, and the serialization cost is already paid.
- **Sequence number / version tracking**: Rejected — requires the GitHub API to provide a version, which it doesn't for project items queries.
- **ETag-based detection**: Not applicable — the project items are fetched via GraphQL, which doesn't return ETags.

**Implementation detail**: Store `last_sent_hash: str | None` as a local variable in the WebSocket handler function scope. Compare hash on each refresh cycle. Only send if hash differs. On first cycle (hash is None), always send.

## R2: Frontend Query Invalidation Decoupling

**Decision**: Remove `['board', 'data', projectId]` invalidation from the WebSocket message handler for `initial_data`, `refresh`, `task_update`, `task_created`, and `status_changed` message types. Board data refreshes on its own 5-minute `AUTO_REFRESH_INTERVAL_MS` schedule via TanStack Query's `refetchInterval`.

**Rationale**: The board data endpoint is expensive (~23 API calls per fetch). WebSocket messages already provide task data directly; invalidating the board query causes a redundant, expensive re-fetch. The board's own polling interval handles eventual consistency.

**Alternatives considered**:
- **Conditional board invalidation** (only on status_changed): Rejected — the board has its own refresh schedule, and status changes don't warrant immediate board re-fetch since the user sees task-level changes immediately.
- **Debounced board invalidation**: Rejected — adds complexity for marginal benefit; the 5-minute schedule is sufficient.

**Manual refresh path**: The user's manual refresh (button click) already uses a separate code path that directly calls `queryClient.invalidateQueries()` for both keys. This remains unchanged (FR-004).

## R3: Sub-Issue Caching Strategy

**Decision**: Add per-issue sub-issue caching in the existing `InMemoryCache` with a 600-second TTL, using cache key `sub_issues:{owner}/{repo}#{issue_number}`.

**Rationale**: Sub-issues change infrequently (typically only when explicitly edited). A 600-second TTL (10 minutes) balances freshness with API savings. The existing `InMemoryCache` is battle-tested and already used throughout the codebase. No new infrastructure needed.

**Alternatives considered**:
- **Batched GraphQL query for all sub-issues**: Rejected for now — would require a custom GraphQL query and the Sub-Issues API is REST-only. Could be a future optimization.
- **Indefinite cache with webhook invalidation**: Rejected — requires webhook configuration for sub-issue events which adds deployment complexity.
- **Shorter TTL (120s)**: Rejected — sub-issues don't change frequently enough to justify the higher API consumption.

**Cache invalidation**: The `refresh=true` query parameter on the board endpoint will clear sub-issue caches for the affected project, ensuring manual refresh bypasses all caches (FR-009).

## R4: Board Data Cache TTL Alignment

**Decision**: Change board data cache TTL from 120 seconds to 300 seconds.

**Rationale**: The frontend's `AUTO_REFRESH_INTERVAL_MS` is 5 minutes (300,000ms). With a 120-second backend cache TTL, every other frontend auto-refresh hits an expired cache and triggers a full API fetch. Aligning to 300 seconds means the cache stays warm across auto-refresh cycles. Combined with WebSocket change detection (R1) and query decoupling (R2), board data is only re-fetched on its natural 5-minute schedule.

**Alternatives considered**:
- **600-second TTL**: Rejected — would cause stale data for significantly longer than the frontend expects.
- **Dynamic TTL based on activity**: Rejected — over-engineering for this use case. A static 300s is simple and effective.

## R5: Reconciliation Optimization (Deferred)

**Decision**: Keep reconciliation running on every board refresh for now. Mark as optional future optimization.

**Rationale**: Reconciliation makes M GraphQL calls (one per repository). With sub-issue caching and WebSocket change detection in place, board refreshes happen infrequently enough (~12/hour) that M calls per refresh is acceptable. The total impact is ~24 calls/hour for 2 repos, well within budget.

**Future optimization**: Make reconciliation conditional on `refresh=true` (manual refresh only). This would save ~24 calls/hour but adds conditional logic that's not needed given the other optimizations.
