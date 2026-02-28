# Research: Codebase Cleanup — Remove Dead Code, Backwards Compatibility & Stale Tests

**Feature**: `010-codebase-cleanup-refactor` | **Date**: 2026-02-28

## R1: Legacy Code Path Identification and Safe Removal Strategy

**Decision**: Audit all "legacy" code paths in the backend and remove those that are pure backwards compatibility shims with no current consumers. Retain code paths that support active functionality (e.g., non-pipeline issue handling in `pipeline.py`).

**Rationale**:
- The `pipeline.py` file contains 4 comments referencing "legacy" PR completion detection, but these paths handle real cases where issues don't have agent pipelines — they are not purely backwards-compatible shims but active fallback logic
- The `encryption.py` plaintext fallback (`gho_` prefix detection) is genuine backwards compatibility for tokens stored before encryption was added. It should be evaluated: if all tokens have been re-encrypted, the fallback can be removed; if not, it must be retained with a deprecation timeline
- The `custom_agent` field deprecation (referenced in `test_custom_agent_assignment.py`) has been fully migrated to `agent_mappings` — any remaining references to the old field name are candidates for removal

**Alternatives Considered**:
- Remove all "legacy" references regardless of active usage → Rejected because pipeline.py's non-pipeline handling is actively used for issues created outside the workflow system
- Keep all legacy code with deprecation warnings → Rejected because the spec mandates removal of backwards compatibility code that is no longer needed

---

## R2: Silent Exception Handling — Logging vs. Suppression

**Decision**: Replace bare `pass` statements in exception handlers with `logger.debug()` or `logger.warning()` calls, preserving the suppression behavior but adding observability. The exception level depends on the criticality of the suppressed operation.

**Rationale**:
- 10+ bare `pass` exception handlers found across the codebase (see plan.md Technical Context)
- Silent suppression makes debugging production issues extremely difficult — engineers cannot distinguish "operation succeeded" from "operation failed silently"
- Most suppressed exceptions are for non-critical operations (cache pops, JSON parsing, PR linking) where failure is acceptable but should be logged
- Python best practice (PEP 8) recommends against bare except/pass; at minimum, a comment or log should explain why

**Implementation Pattern**:
```python
# Before (current)
try:
    link_pr_to_issue(...)
except Exception:
    pass

# After
try:
    link_pr_to_issue(...)
except Exception:
    logger.debug("Failed to link PR to issue, continuing", exc_info=True)
```

**Alternatives Considered**:
- Re-raise as custom exceptions → Rejected because these are intentionally non-fatal operations
- Add structured error tracking/metrics → Rejected as over-engineering for this scope; logging is sufficient

---

## R3: Unused Type Export Cleanup Strategy

**Decision**: Remove unused type exports from `frontend/src/types/index.ts` after verifying they are not consumed by any file in the repository (including test files, type-only imports, and dynamic references).

**Rationale**:
- Static analysis identified 6+ type exports with no import references: `IssueLabel`, `PipelineStateInfo`, `AgentNotification`, `SignalConnectionStatus`, `SignalNotificationMode`, `SignalLinkStatus`
- These types may have been used by code that was removed in previous cleanup iterations (specs 007, 009)
- TypeScript's `isolatedModules` and tree-shaking do not remove unused type exports, so they accumulate as dead code
- Removing them reduces the cognitive load of the types file (currently 616 lines)

**Verification Method**:
1. `grep -r "IssueLabel" frontend/src/` — confirm zero matches outside `types/index.ts`
2. `grep -r "PipelineStateInfo" frontend/src/` — same verification
3. Run `npm run type-check` after removal to confirm no type errors
4. Run `npm test` to confirm no runtime impact

**Alternatives Considered**:
- Mark types as `@deprecated` with JSDoc → Rejected because they have zero consumers; deprecation implies there are users to notify
- Move to a `legacy-types.ts` file → Rejected because moving dead code to a different file is not cleanup

---

## R4: Cache Pattern Consolidation Approach

**Decision**: Extract the repeated cache-check-get-set pattern into a reusable decorator or utility function in `backend/src/services/cache.py`. The pattern appears in `board.py`, `projects.py`, and `chat.py` with identical logic.

**Rationale**:
- The cache pattern is duplicated 8+ times across API handlers with identical structure: construct key → check `refresh` flag → get from cache → return if hit → else proceed with API call → set cache → return
- Consolidation reduces the risk of inconsistent cache behavior (e.g., one handler forgetting the refresh check)
- The existing `cache.py` module already provides `get()` and `set()` — extending it with a higher-level `cached_response()` utility is natural

**Implementation Pattern**:
```python
# In cache.py — new utility
async def cached_response(cache_key: str, refresh: bool, fetch_fn, logger, description: str):
    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached %s", description)
            return cached
    result = await fetch_fn()
    cache.set(cache_key, result)
    return result
```

**Alternatives Considered**:
- Python decorator with `@cached` → Rejected because the `refresh` parameter varies per endpoint and decorators are harder to debug
- Keep duplication and add comments → Rejected because the spec mandates DRY consolidation (FR-004)
- Use a third-party caching library (e.g., `aiocache`) → Rejected because the existing cache module is sufficient and adding dependencies contradicts simplicity

---

## R5: Frontend Hook Duplication — Consolidation vs. Composition

**Decision**: Use TanStack Query's built-in patterns (query key factories, mutation helpers) to reduce boilerplate rather than creating a custom hook factory. The `useQuery`/`useMutation` pattern across hooks is similar but not identical — each hook has unique cache invalidation, error handling, and return shaping logic.

**Rationale**:
- The hooks (`useAuth`, `useProjects`, `useSettings`, `useMcpSettings`) all use `useQuery` + `useMutation` but differ in: query keys, stale times, invalidation targets, error extraction, and return types
- Creating a generic `useApiResource()` factory would require so many configuration options that it becomes harder to understand than the individual hooks
- TanStack Query already provides query key factories as a recommended pattern for organizing keys — adopting this would reduce the most common duplication (key strings)
- The `useAgentConfig.ts` dirty-checking duplication (lines 108-120 vs 122-133) is a clear consolidation target — extract to a shared comparison helper

**Implementation Pattern**:
```typescript
// Consolidate dirty-checking in useAgentConfig.ts
function hasAgentOrderChanged(
  serverAgents: AgentConfig[],
  localAgents: AgentConfig[]
): boolean {
  if (serverAgents.length !== localAgents.length) return true;
  return serverAgents.some((agent, i) => agent.slug !== localAgents[i].slug);
}
```

**Alternatives Considered**:
- Generic `useApiResource<T>()` hook factory → Rejected because the hooks differ too much in behavior; a one-size-fits-all abstraction would be the "wrong abstraction" (constitution V: "Duplication is preferable to wrong abstraction")
- Extract shared `useQueryWithCache()` wrapper → Rejected because TanStack Query already handles caching; wrapping it adds indirection without value

---

## R6: Stale Test Identification Criteria

**Decision**: A test is considered stale if it meets any of these criteria: (a) it tests code that no longer exists, (b) it validates deprecated behavior that has been removed, (c) it is a pure duplicate of another test with no additional coverage, (d) it is perpetually skipped with no active fix plan. Apply criteria systematically using import analysis and code coverage mapping.

**Rationale**:
- Current test suite: 41 backend unit tests, 3 integration tests, 7+ frontend hook tests — no skipped or xfail tests found
- The `test_legacy_plaintext_fallback_on_decrypt` test in `test_token_encryption.py` tests backwards compatibility for plaintext tokens — this is stale only if the plaintext fallback in `encryption.py` is removed (Story 1 dependency)
- No purely stale tests were identified through static analysis; the test suite appears well-maintained after previous cleanup iterations
- The spec requires documented rationale for any test removal (acceptance scenario 4.1)

**Verification Method**:
1. Run full test suite to establish baseline (all pass)
2. For each backwards compatibility removal, check if a test exists that covers it
3. Remove test + code atomically in same commit
4. Verify full suite still passes after removal

**Alternatives Considered**:
- Aggressive test removal based on code coverage metrics → Rejected because low coverage doesn't mean a test is stale; it might test edge cases
- Keep all existing tests regardless → Rejected because tests for removed code are actively harmful (they give false confidence)

---

## R7: Error Handling Consolidation in API Endpoints

**Decision**: Do not create a generic error handling decorator for API endpoints. The try/except patterns across API handlers are similar in structure but differ in exception types, HTTP status codes, error messages, and logging levels. The cost of a generic wrapper exceeds the benefit for 6 occurrences.

**Rationale**:
- API error handling in `board.py`, `auth.py`, `chat.py`, etc. follows a similar pattern but each handler catches different exception types (`ValueError`, `AppException`, generic `Exception`) and returns different HTTP status codes (400, 401, 500)
- FastAPI already provides exception handler middleware for cross-cutting error handling — the existing approach of route-specific try/except is appropriate for endpoint-specific error messages
- Creating a decorator that maps exception types to HTTP responses would essentially replicate FastAPI's built-in `HTTPException` handling with extra indirection
- Constitution V states "Duplication is preferable to wrong abstraction" — the error handling duplication is structural similarity, not semantic duplication

**Alternatives Considered**:
- `@handle_api_errors` decorator → Rejected because exception-to-status-code mapping varies per endpoint
- Middleware-based error handling → Already exists via `exceptions.py` and FastAPI's exception handlers; no additional middleware needed
- Reduce to single `except Exception` per handler → Rejected because differentiated exception handling (ValueError vs. generic Exception) provides better error messages
