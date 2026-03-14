# Research: Dead Code & Technical Debt Cleanup

**Feature**: 039-dead-code-cleanup
**Date**: 2026-03-13
**Status**: Complete

## Research Tasks

### R1: Error Handling Consolidation — `handle_service_error` Adoption

**Decision**: Migrate 20 inline error handlers across 6 API files to use the existing `handle_service_error` utility in `backend/src/logging_utils.py`.

**Rationale**: The `handle_service_error(exc, operation, error_cls)` function already exists (lines 224–261 of `logging_utils.py`) and is actively used by 22+ call sites across `workflow.py`, `cleanup.py`, `chores.py`, and `agents.py`. The function centralizes the pattern of logging the full exception context server-side and raising a structured `AppException` with a safe message that does not leak internal details.

The 20 remaining inline handlers fall into three categories:
1. **Direct candidates** (15): `except Exception as e: logger.error(...); raise FooError(...)` — direct replacement with `handle_service_error(e, "operation", FooError)`
2. **Error-response patterns** (3): Chat endpoints (lines 249, 389, 437) that create `ChatMessage` error responses before returning — these need a thin wrapper or should remain inline since they return values rather than raising
3. **Intentional exceptions** (2): Line 167 (silent fail for feature request detection) and WebSocket handlers — these should be preserved as-is

**Alternatives considered**: Creating a decorator-based approach was rejected — the existing function-call pattern is simpler and already adopted. A context manager approach was considered but adds unnecessary abstraction for a one-liner replacement.

---

### R2: Cache Pattern Extraction — `cached_fetch` Design

**Decision**: Create `cached_fetch` as an async utility in `backend/src/services/cache.py` that wraps the repeated cache-check/fetch/set pattern.

**Rationale**: Three API modules (`projects.py`, `board.py`, `chat.py`) repeat the same pattern:
1. Check `InMemoryCache.get(key)` for a warm entry
2. If warm and not `refresh=True`, return cached value
3. Otherwise call the fetch function
4. Store the result via `InMemoryCache.set(key, value, ttl_seconds)`
5. Return the fresh value

The `InMemoryCache` class already provides `get()`, `get_stale()`, `set()`, `get_entry()`, and `refresh_ttl()` methods. The `cached_fetch` utility consolidates the orchestration logic without changing the underlying cache implementation.

Proposed signature:
```python
async def cached_fetch(
    cache: InMemoryCache,
    key: str,
    fetch_fn: Callable[..., Awaitable[T]],
    ttl_seconds: int = 300,
    refresh: bool = False,
    stale_fallback: bool = False,
) -> T:
```

The `stale_fallback` parameter enables serving expired data when the fetch function raises (matches the existing pattern in `board.py` for rate-limit/5xx scenarios).

**Alternatives considered**: Decorator-based caching (e.g., `@cached(ttl=300)`) was rejected because the cache key construction varies per endpoint and the refresh flag comes from request parameters, not function arguments.

---

### R3: Complexity Decomposition Strategy for Backend Functions

**Decision**: Extract logical sub-functions from the three high-CC backend functions using a "extract method" refactoring pattern, keeping all sub-functions private (prefixed with `_`) and co-located in the same module.

**Rationale**: Code inspection reveals clear decomposition boundaries:

**`post_agent_outputs_from_pr` (CC=123)**:
- Per-task iteration with pipeline state checks
- PR detection and file extraction logic
- Comment posting (markdown files → sub-issue, Done marker → parent)
- Tracking table update
- Target: 4–5 extracted functions, each CC < 30

**`assign_agent_for_status` (CC=91)**:
- Agent resolution from config with tracking table overrides (T032–T033)
- Issue context validation and agent-index bounds checking
- Branch creation and Copilot assignment
- Pipeline state tracking update
- Target: 4 extracted functions, each CC < 25

**`recover_stalled_issues` (CC=72)**:
- Bootstrap logic for missing config and task list
- Per-issue stall detection with cooldown check
- PR verification (draft PR exists for agent)
- Reassignment attempt with state reconciliation
- Target: 4 extracted functions, each CC < 20

All extracted functions are kept private (`_` prefix) to preserve the existing public API contract. No new modules are created.

**Alternatives considered**: Moving sub-functions to separate files was rejected — co-location keeps related logic together and avoids circular imports. Using a class-based approach (strategy pattern) was rejected as over-engineering for what are fundamentally procedural workflows.

---

### R4: Frontend Component Decomposition Assessment

**Decision**: `GlobalSettings` is already well-decomposed. `LoginPage` needs decomposition into 3 sub-components.

**Rationale**:

**`GlobalSettings` (CC=96)**: Despite the high reported CC, inspection reveals the component already delegates to focused subcomponents: `AISettingsSection`, `DisplaySettings`, `WorkflowSettings`, `NotificationSettings`, and `SettingsSection`. The form state uses `react-hook-form` with `zodResolver`. The remaining complexity is in the form orchestration (reset on settings change, submit handler). Further decomposition would fragment the form context unnecessarily.

**Recommendation**: Verify the CC measurement is accurate. If the CC includes subcomponent code measured at the file level, the actual component CC may be lower. If the form orchestration genuinely exceeds CC=30, extract the submit handler into a custom hook (`useGlobalSettingsForm`).

**`LoginPage` (CC=90)**: The component contains significant inline JSX with theme toggling, hero section markup, feature highlights, and authentication panel. Clear decomposition boundaries:
1. `HeroSection` — Branding, tagline, feature highlights
2. `ThemeToggle` — Dark/light mode switch button
3. `AuthPanel` — Login button and OAuth callback display

Each sub-component would be CC < 30 and independently testable.

**Alternatives considered**: Using a render-props pattern was rejected — simple component extraction is more idiomatic in modern React. Extracting to a separate `auth/` directory was considered but rejected to keep login-specific components co-located with the page.

---

### R5: Legacy Pipeline Code Deprecation Strategy

**Decision**: Add structured `DEPRECATED(vX.Y)` annotations to all 8 legacy code paths in `pipeline.py` with linked tracking issues, rather than removing code.

**Rationale**: The legacy pipeline path (L2075+) is still actively used as a fallback for issues without agent pipelines. Premature removal would break production workflows. The deprecation strategy:

1. **Annotation format**: `# DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking. See issue #XXXX`
2. **Migration tracking**: Add `logger.info("legacy_format_encountered", ...)` calls when legacy format is detected in `pipelines/service.py` to monitor adoption rate
3. **Removal criteria**: Legacy code can be removed when monitoring shows zero legacy format encounters over a 30-day period
4. **_ROW_RE_OLD**: The old 4-column regex in `agent_tracking.py` (L61–62) with fallback usage at L206 should get the same treatment — annotate, monitor, remove when encounters drop to zero

The same approach applies to deprecated fields in `pipeline.py` (L44–46: `agents`, `execution_mode`) and `index.ts` (L1072–1075).

**Alternatives considered**: Immediate removal behind a feature flag was rejected — the legacy path is a production fallback, not a feature toggle. A/B testing was irrelevant since the legacy path serves different data states, not different UI experiences.

---

### R6: Singleton and In-Memory Store Migration Scope Assessment

**Decision**: Produce planning documents only. Do not implement singleton removal or SQLite migration in this feature.

**Rationale**:

**Singleton removal** (`github_projects_service`): 17+ files import the module-level singleton directly, including non-request contexts (background tasks, signal bridge, orchestrator) where `Request.app.state` is not available. A provider pattern that works in both contexts requires:
- A module-level `get_service()` function that checks `app.state` first, falls back to global
- Updating 17+ import sites across backend
- This is already partially designed — `backend/src/dependencies.py` has `get_github_service()` with fallback logic
- Full migration requires a separate spec due to cross-cutting nature

**In-memory store migration** (`_messages`, `_proposals`, `_recommendations`): Migration 012 created the SQLite tables (`chat_messages`, `chat_proposals`, `chat_recommendations`). Migration requires:
- Updating ~15 code paths in `chat.py` (713 lines) with transaction management
- Adding error handling for database failures (fallback to in-memory?)
- Testing concurrent access patterns
- Full migration requires a separate spec due to complexity

**Alternatives considered**: Implementing as part of this feature was rejected per the spec — Stories 1–4 must complete first to avoid merge conflicts. The planning artifacts serve as handoff documents for dedicated implementation specs.

---

### R7: Backward-Compatibility Alias Audit Approach

**Decision**: Search for consumers of old names before removing any alias. Keep aliases that have external consumers or are part of public API.

**Rationale**: Three backward-compat aliases exist:
1. `backend/src/models/chat.py` L16–18 — re-exports of renamed models
2. `backend/src/prompts/issue_generation.py` L8 — alias for renamed prompt function
3. `backend/src/api/auth.py` L94 — alias for renamed auth utility

The audit approach:
- Use `grep` to find all import sites for each old name across the codebase
- Check if any external scripts, tests, or configuration files reference old names
- If all consumers use new names: remove alias and verify tests pass
- If consumers remain: add `@deprecated` annotation with migration instructions

**Alternatives considered**: Removing all aliases immediately was rejected — breaking external consumers (if any) would violate the zero-regression constraint. A bulk search-and-replace was considered but individual audit is safer for backward-compat code.

---

### R8: Documentation Currency Assessment

**Decision**: Update `docs/configuration.md` to reflect migration count through 022 and annotate historical migrations.

**Rationale**: The documentation states "001 through 020" but the actual `backend/src/migrations/` directory contains 28 files numbered 001 through 022, with some duplicate version numbers (013, 014, 015, 021, 022 each appear twice as parallel feature migrations). The blocking-related migrations (017, 018, 021) have been fully removed from the codebase (verified by `test_blocking_removal.py`) and should be annotated as historical.

**Alternatives considered**: Renumbering migrations to avoid duplicates was rejected — this would break existing database migration tracking on deployed instances. Adding a migration manifest file was considered but deferred as over-engineering for a documentation update.
