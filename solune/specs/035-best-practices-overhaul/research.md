# Research: Codebase Improvement Plan — Modern Best Practices Overhaul

**Feature**: `035-best-practices-overhaul` | **Date**: 2026-03-11 | **Plan**: [plan.md](plan.md)

## Research Tasks & Findings

### R-001: SQLite Write-Through Cache Pattern for Pipeline State

**Context**: Pipeline state uses `BoundedDict(maxlen=500)` in `transitions.py` — container restarts silently lose all in-flight data. Need a persistence layer.

**Decision**: Create `pipeline_state_store.py` following the existing `session_store.py` pattern — direct aiosqlite queries with `INSERT OR REPLACE`, no ORM.

**Rationale**:
- The codebase already uses this pattern successfully for sessions, settings, MCP configs, and blocking queue entries.
- `session_store.py` demonstrates the exact approach: async functions accepting `aiosqlite.Connection`, row-to-model conversion, `INSERT OR REPLACE` for upserts.
- aiosqlite is already a dependency (0.22+) and the migration system is proven across 20 migrations.
- BoundedDict remains as L1 cache for hot-path reads; SQLite is the durable backing store.

**Alternatives Considered**:
- **Redis**: Rejected — adds infrastructure complexity for a single-instance deployment. SQLite is sufficient at current scale.
- **SQLAlchemy async**: Rejected — the codebase deliberately avoids ORM layers. All existing persistence uses raw SQL via aiosqlite.
- **Pickle/JSON file**: Rejected — no transactional guarantees, race conditions with concurrent writes.

---

### R-002: Chat Persistence Integration

**Context**: `012_chat_persistence.sql` migration exists but chat state is stored in in-memory dicts (`chat.py` L91-94). Migration creates `chat_messages`, `chat_proposals`, and `chat_recommendations` tables.

**Decision**: Wire the existing migration (it already runs — migrations are auto-applied in `init_database()`) and replace in-memory dicts with SQLite read/write functions following the `session_store.py` pattern.

**Rationale**:
- The migration file is already numbered in sequence (012) and the migration runner in `database.py` executes all `.sql` files in order. The tables likely already exist in production databases.
- The TODO comment in `chat.py` explicitly calls for this change.
- The existing table schema (message_id, session_id, sender_type, content, action_type, action_data, timestamp) matches the current in-memory dict structure.

**Alternatives Considered**:
- **Keep in-memory with periodic flush**: Rejected — still loses data between flushes on crash. Write-through is more reliable.
- **New migration file**: Rejected — `012_chat_persistence.sql` already has the correct schema. No changes needed to the migration itself.

---

### R-003: Async-Safe Locking Strategy

**Context**: `BoundedDict`, `ConnectionManager`, and module-level singletons lack `asyncio.Lock` for concurrent mutations.

**Decision**: Add `asyncio.Lock` at the module level in `transitions.py` (guards all four BoundedDict instances) and in `websocket.py` (guards `ConnectionManager` mutations). Use a single lock per module to avoid deadlock complexity.

**Rationale**:
- Python's GIL protects against thread-level races, but `asyncio` coroutines can interleave at `await` points. The write-through cache pattern introduces `await db.execute(...)` calls inside mutations, creating genuine interleaving windows.
- A single `asyncio.Lock` per module (not per dict) is the simplest correct approach. Fine-grained locks per key could improve throughput but add deadlock risk with no measured need.
- FastAPI docs recommend `asyncio.Lock` for shared mutable state in async endpoints.

**Alternatives Considered**:
- **Per-key locks**: Rejected — adds complexity with no demonstrated throughput need.
- **threading.Lock**: Rejected — blocks the event loop. `asyncio.Lock` is the correct primitive for async code.
- **No locks (rely on GIL)**: Rejected — GIL doesn't protect against logical interleaving at await points. A coroutine can yield during a write-through, allowing another coroutine to read stale data.

---

### R-004: Cyclomatic Complexity Reduction — Backend Strategy

**Context**: Three backend functions with CC scores of 123, 91, and 72+66. Need to decompose without changing behavior.

**Decision**: Extract into handler/strategy patterns:
- `post_agent_outputs_from_pr` (CC 123, 213 lines) → Extract scanning, analysis, extraction, advancement phases into separate async functions. Use a dispatch dict or match/case for output routing.
- `assign_agent_for_status` (CC 91, 117 lines) → Extract config resolution, tracking table override, base ref determination, and sub-issue resolution into separate methods on `WorkflowOrchestrator`.
- `recover_stalled_issues` (CC 72+66, 505 lines) → Already has helpers (`_should_skip_recovery`, `_attempt_reassignment`). Extract per-issue recovery logic, copilot assignment check, and PR validation into additional helpers.

**Rationale**:
- The strategy pattern (dispatch dict or match/case) is the standard approach for reducing CC in functions with many conditional branches.
- Extracting into methods/functions at the same module level preserves call locality and makes the refactoring reversible.
- The existing helper pattern in `recovery.py` (`_should_skip_recovery`, `_attempt_reassignment`) proves the codebase already uses this decomposition approach.

**Alternatives Considered**:
- **Class-per-strategy**: Rejected — over-engineering for internal decomposition. Simple functions are sufficient and match existing codebase style.
- **Plugin/registry system**: Rejected — adds abstraction without demonstrated extensibility need. YAGNI per constitution.

---

### R-005: Cyclomatic Complexity Reduction — Frontend Strategy

**Context**: `usePipelineConfig` (CC 79, returns 30 properties) and `useAgentConfig` (CC 69) need decomposition.

**Decision**: Apply React hook composition:
- `usePipelineConfig` already composes with `usePipelineValidation`, `usePipelineModelOverride`, and `usePipelineBoardMutations`. Extend this pattern: extract CRUD operations into `usePipelineCrud` and return grouped objects (`{ crud, validation, state }`) instead of flat properties.
- `useAgentConfig` → Extract DnD operations into `useAgentDnd`, column mutation logic into `useAgentColumns`. Return grouped objects.

**Rationale**:
- The hook already demonstrates the composition pattern (it composes 3 sub-hooks). The issue is that it destructures and re-exports all sub-hook returns as flat properties.
- Returning grouped objects (`{ crud: { save, load, delete }, validation: { errors, validate, clear } }`) reduces the API surface without changing internal logic.
- Each sub-hook should return ≤8 properties per spec requirement.

**Alternatives Considered**:
- **Single mega-refactor**: Rejected — too risky. Incremental extraction preserves existing behavior at each step.
- **State machine library (XState)**: Rejected — adds dependency. `useReducer` + composition is sufficient and already in use.

---

### R-006: DRY Repository Resolution

**Context**: 8 separate `(owner, repo)` resolution paths. Canonical `resolve_repository()` exists in `utils.py` with 3-step fallback.

**Decision**: All 8 duplicate resolution paths already call `resolve_repository()` from `utils.py`. The "duplication" identified in the issue is the repeated `try/except` wrapper around `resolve_repository()` calls at each call site in API endpoints (e.g., `api/agents.py` wraps every call in `try: owner, repo = await resolve_repository(...) except Exception as exc: raise ValidationError(...)`). Consolidate by using the `@handle_github_errors` decorator or creating a FastAPI dependency that performs resolution.

**Rationale**:
- After investigation, the actual code shows that most API files already call the canonical `resolve_repository()`. The duplication is in the error-handling boilerplate around each call, not in the resolution logic itself.
- A FastAPI `Depends()` function that calls `resolve_repository()` and handles the error once eliminates the boilerplate from every endpoint.

**Alternatives Considered**:
- **Middleware-level resolution**: Rejected — not all endpoints need repository info. A dependency is more targeted.
- **Keep individual try/except**: Rejected — 25+ identical patterns violate DRY and make error handling inconsistent.

---

### R-007: Error Handling Infrastructure Adoption

**Context**: `handle_service_error()` and `@handle_github_errors` decorator exist in `logging_utils.py` but bare `except Exception` blocks persist across 15+ locations.

**Decision**: Replace bare `except Exception` blocks with:
1. The `@handle_github_errors("operation description")` decorator for entire endpoint functions.
2. Direct calls to `handle_service_error(exc, "operation")` for targeted catch blocks.
3. Specific exception types (e.g., `httpx.HTTPStatusError`, `aiosqlite.Error`) where the exception class is known.

**Rationale**:
- The decorator pattern is already built and documented in `logging_utils.py` L264-303. It catches all non-`AppException` errors, logs with full context, and re-raises as structured `AppException` — exactly what the spec requires.
- Specific exception types improve debugging by narrowing the catch scope.
- The existing `AppException` hierarchy (`GitHubAPIError`, `ValidationError`, etc.) in `exceptions.py` provides the right granularity.

**Alternatives Considered**:
- **Global exception handler only**: Rejected — too coarse. Per-endpoint decorators provide operation-specific error messages.
- **New error infrastructure**: Rejected — existing infrastructure is well-designed and just needs adoption.

---

### R-008: Pydantic v2 Input Validation

**Context**: `api/settings.py` accepts `updates: dict = {}`, `api/webhooks.py` accepts `pr_data: dict`. Need Pydantic models.

**Decision**: Create Pydantic v2 models for all API inputs:
- `SettingsUpdate` model with typed fields for settings.
- `WebhookPayload` base model with discriminated unions for different event types (PR, issue, etc.).
- Leverage `model_validator` for complex cross-field validation.

**Rationale**:
- FastAPI natively integrates with Pydantic — replacing `dict` with a model requires zero framework changes. FastAPI auto-validates and returns 422 on invalid input.
- Pydantic v2 discriminated unions (`Annotated[Union[...], Discriminator(...)]`) handle the webhook payload dispatch cleanly.
- The codebase already uses Pydantic models extensively in `models/` directory.

**Alternatives Considered**:
- **TypedDict**: Rejected — no runtime validation. FastAPI won't auto-validate TypedDict parameters.
- **Marshmallow/attrs**: Rejected — the codebase standardizes on Pydantic.

---

### R-009: Dependency Injection via FastAPI Lifespan

**Context**: Module-level singletons (`github_projects_service`, `_ai_agent_service_instance`) lack test isolation. Circular imports force lazy import hacks.

**Decision**: Use FastAPI's lifespan pattern (already used in `main.py`) + `app.state` + `Depends()`:
1. Create all service instances in `lifespan()` (some are already done: `_app.state.github_service`, `_app.state.connection_manager`).
2. Add remaining services: AI agent service, pipeline state store.
3. Create `Depends()` functions in `dependencies.py` that read from `request.app.state`.
4. Extract shared protocols into `backend/src/interfaces.py` using `typing.Protocol` to break circular imports.

**Rationale**:
- The lifespan pattern is already used (`main.py` creates db, github_service, connection_manager in lifespan). This extends the existing pattern rather than introducing a new one.
- `typing.Protocol` provides structural subtyping — classes satisfy the protocol without inheriting from it, avoiding import cycles.
- FastAPI's `Depends()` is the canonical DI mechanism and is already used throughout the codebase.

**Alternatives Considered**:
- **dependency-injector library**: Rejected — adds a third-party dependency. FastAPI's built-in DI is sufficient.
- **Factory functions with caching**: Rejected — the current lazy singleton pattern is what we're replacing.

---

### R-010: Security Hardening — CORS and CSP

**Context**: `allow_headers=["*"]` in CORS config. No CSP headers.

**Decision**:
- **CORS**: Replace `allow_headers=["*"]` with explicit list: `["Authorization", "Content-Type", "Accept", "X-Request-ID", "X-Requested-With"]`. These are the headers the application actually uses.
- **CSP**: Add a Starlette middleware that sets `Content-Security-Policy` header on all responses. Policy: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'`. The `'unsafe-inline'` for styles is required for Tailwind's runtime injection.

**Rationale**:
- The current CORS wildcard allows any custom header, which could be leveraged in CSRF attacks or header injection.
- CSP headers are a defense-in-depth measure against XSS. The policy restricts content sources to the application's own origin.
- Starlette middleware (FastAPI is built on Starlette) is the standard approach for adding response headers.

**Alternatives Considered**:
- **CSP via reverse proxy**: Rejected — not all deployments have a reverse proxy. Application-level CSP works everywhere.
- **Report-only CSP first**: Viable but deferred — start with enforcing mode since the application is controlled.

---

### R-011: Security Hardening — Admin Designation

**Context**: First authenticated user is auto-promoted to admin (`dependencies.py` L103-115).

**Decision**: Add `ADMIN_GITHUB_USER_ID` environment variable. When set, only that user gets admin. When unset, fall back to current behavior (first user auto-promotes) with a startup warning log.

**Rationale**:
- An environment variable is the standard mechanism for deployment-time configuration in containerized applications.
- Maintaining backward compatibility (first-user promotion as fallback) prevents breaking existing deployments that rely on the current behavior.
- The startup warning ensures operators are aware of the security implication.

**Alternatives Considered**:
- **Hard requirement (no fallback)**: Rejected — would break all existing deployments on upgrade.
- **Admin invite workflow**: Rejected — out of scope. This is a security hardening, not a feature addition.

---

### R-012: Frontend Hook Composition Pattern

**Context**: `usePipelineConfig` returns 30 flat properties. Need grouped objects.

**Decision**: Return grouped objects from existing composition:
```typescript
return {
  crud: { pipelines, pipelinesLoading, newPipeline, loadPipeline, savePipeline, saveAsCopy, deletePipeline, discardChanges },
  validation: { validationErrors, validatePipeline, clearValidationError },
  state: { pipeline, editingPipelineId, isDirty, isSaving, saveError, isPreset },
  assignment: { assignedPipelineId, assignPipeline },
  model: { modelOverride, setModelOverride },
  board: { ...boardMutations }
}
```

**Rationale**:
- The hook already composes 3 sub-hooks internally. Grouping the return value is a non-breaking API change if consumers are updated simultaneously.
- Each group has ≤8 properties, meeting the spec requirement.
- Consumers destructure only the group they need, making code self-documenting.

**Alternatives Considered**:
- **Multiple separate hooks at call sites**: Rejected — would require every consumer to call 5 hooks instead of 1. The grouped return preserves the single-import convenience.
- **Context-based state**: Rejected — TanStack Query + local state is the correct pattern (per spec).

---

### R-013: Retry Standardization on Tenacity

**Context**: `tenacity` is a dependency but custom retry logic exists alongside it.

**Decision**: After investigation, the frontend uses TanStack Query's built-in `retry` option (not custom retry logic). The backend uses `tenacity` decorators in Signal messaging. No custom backend retry implementations were found outside of `tenacity`. The "custom retry logic" mentioned in the issue refers to per-hook `retry` overrides in TanStack Query (e.g., `retry: 2`, `retry: false`). These are intentional per-query tuning, not duplicated infrastructure.

**Rationale**:
- TanStack Query's `retry` option is the idiomatic approach for frontend data fetching retries. Replacing it with a custom wrapper around `tenacity` would fight the framework.
- Backend retry is already standardized on `tenacity`.
- The global retry policy in `App.tsx` provides sensible defaults; per-query overrides are intentional.

**Alternatives Considered**:
- **Custom frontend retry wrapper**: Rejected — TanStack Query's retry is more capable (exponential backoff, error-type-aware) than a manual wrapper.
- **Remove all per-query retry overrides**: Rejected — some queries legitimately need different retry behavior (e.g., auth queries should not retry on 401).

## Technology Decisions Summary

| Area | Decision | Key Dependency |
|------|----------|----------------|
| Pipeline persistence | SQLite write-through cache | aiosqlite (existing) |
| Chat persistence | Wire existing migration 012 | aiosqlite (existing) |
| Concurrency safety | `asyncio.Lock` per module | stdlib (no dependency) |
| Backend decomposition | Extract functions + strategy pattern | No dependency |
| Frontend decomposition | Hook composition + grouped returns | React (existing) |
| Error handling | Adopt `@handle_github_errors` decorator | logging_utils (existing) |
| API validation | Pydantic v2 models | Pydantic (existing) |
| DI modernization | FastAPI lifespan + `Depends()` | FastAPI (existing) |
| Circular imports | `typing.Protocol` in `interfaces.py` | stdlib (no dependency) |
| CORS hardening | Explicit header allow-list | FastAPI CORSMiddleware (existing) |
| CSP headers | Starlette middleware | Starlette (existing) |
| Admin designation | `ADMIN_GITHUB_USER_ID` env var | No dependency |
| Retry | Keep TanStack Query retry (frontend), tenacity (backend) | Existing |
