# Research: Codebase Modernization & Technical Debt Reduction

**Branch**: `038-code-quality-overhaul` | **Date**: 2026-03-12
**Phase**: 0 — Outline & Research

## 1. Error Handling Consolidation Strategy

### Decision
Adopt `handle_service_error()` and the `handle_github_errors()` decorator from `logging_utils.py` across all 13 API endpoint files that currently use inline try/except patterns.

### Rationale
- These helpers already exist, are tested, and are used in 4/17 endpoint files (~28 invocations)
- `handle_service_error()` logs the full exception server-side and raises a safe `AppException` without leaking internals
- `handle_github_errors()` is an async decorator that wraps entire endpoint/service functions
- The `AppException` hierarchy (11 classes in `exceptions.py`) already maps to correct HTTP status codes
- The global exception handler in `main.py` already catches `AppException` and returns structured JSON with request ID

### Alternatives Considered
- **Custom middleware for all error handling**: Rejected — too coarse-grained, loses context about which operation failed
- **New error handling library (e.g., `returns`)**: Rejected — adds dependency for something already solved inline; violates Simplicity principle
- **Per-module custom wrappers**: Rejected — creates divergent patterns; the existing decorator pattern is sufficient

### Migration Approach
1. For each API file not using the shared helpers:
   - Replace inline `try/except Exception as e: logger.error(...); raise HTTPException(...)` with `handle_service_error(e, "operation_name", SpecificErrorClass)`
   - For functions with multiple error-prone operations, apply `@handle_github_errors("operation_name")` decorator
2. Remove redundant `HTTPException` imports where `AppException` subclasses now cover the cases
3. Verify each file's test coverage passes unchanged

---

## 2. DRY Consolidation: Repository Resolution

### Decision
Remove the duplicate `_resolve_repository()` in `api/chat.py` and use the canonical `resolve_repository()` from `utils.py`.

### Rationale
- `utils.py` already has the canonical 3-step fallback: project items → workflow config → defaults
- `chat.py` reimplements the same logic inline as `_resolve_repository()` (~40 lines)
- Consolidation eliminates a maintenance hazard — any fix to resolution logic needs to happen in one place

### Alternatives Considered
- **Keep both and add a redirect**: Rejected — indirection without benefit
- **Move resolution to a FastAPI dependency**: Considered for future but over-engineering for current scope — a regular utility function is simpler and testable without request context

---

## 3. DRY Consolidation: Cache Wrapper Adoption

### Decision
Use the existing `cached_fetch()` from `utils.py` for all cacheable data fetches. Verify all service modules that implement manual cache-check/get/set patterns are migrated.

### Rationale
- `cached_fetch(cache_key, fetch_fn, *args, refresh=False)` is a generic cache wrapper already in utils.py
- `InMemoryCache` in `services/cache.py` provides TTL, ETag, and data-hash support
- Manual inline caching creates inconsistent TTL handling and missed cache invalidation

### Alternatives Considered
- **Redis/external cache**: Rejected — out of scope per spec; SQLite + in-memory is sufficient at current scale
- **Decorator-based caching (e.g., `@lru_cache`)**: Rejected — doesn't support TTL expiration or async patterns

---

## 4. Chat Module Decomposition Strategy

### Decision
Split `api/chat.py` (~1,080 lines) into a `api/chat/` package with 4 sub-modules:
- `messaging.py` — Core CRUD: `get_messages()`, `send_message()`, `clear_messages()`
- `commands.py` — Command dispatch: `_handle_agent_command()`, `_handle_feature_request()`, `_handle_status_change()`, `_handle_task_generation()`
- `proposals.py` — Proposal flow: `confirm_proposal()`, `cancel_proposal()`
- `uploads.py` — File uploads: `upload_file()`

The `__init__.py` aggregates routes into a single `chat_router`.

### Rationale
- 1,080 lines with 14 functions spanning 5 responsibilities violates single-responsibility
- Each sub-module is independently testable and changeable
- The split aligns with spec SC-004: "chat module file count increases from 1 to 4, with no single file exceeding 200 lines"
- Shared state (session messages, proposals) moves to `chat_store.py` (persistence), eliminating global dicts

### Alternatives Considered
- **Keep as single file, just refactor internals**: Rejected — doesn't address merge conflict bottleneck or testability
- **Class-based approach (ChatService)**: Rejected — adds unnecessary OOP layer to what are fundamentally stateless request handlers
- **Separate routers without package**: Rejected — loses organizational cohesion

---

## 5. Chat Persistence Wiring Strategy

### Decision
Wire `services/chat_store.py` into the new chat sub-modules using a write-through strategy per FR-007.

### Rationale
- `chat_store.py` already implements `save_message()`, `get_messages()`, `clear_messages()`, `save_proposal()`, `get_proposals()`, `update_proposal_status()`, `save_recommendation()`, `get_recommendations()`
- Migration `012_chat_persistence.sql` already creates the required tables
- Write-through minimizes risk: write to both stores initially, then progressively switch reads, then remove in-memory state

### Migration Phases
1. **Phase A (write-through)**: On every chat write operation, also call `chat_store.save_*()`. Reads still come from in-memory dicts.
2. **Phase B (read cutover)**: Switch reads to `chat_store.get_*()`. Keep in-memory as fallback.
3. **Phase C (cleanup)**: Remove in-memory dicts and fallback code.

### Alternatives Considered
- **Big-bang switch**: Rejected — high regression risk; write-through is safer
- **New persistence layer with different schema**: Rejected — `chat_store.py` and migration 012 are already correct and tested
- **Event sourcing**: Rejected — massive over-engineering for chat message history

---

## 6. OpenAPI-to-TypeScript Type Generation

### Decision
Use `openapi-typescript` (npm package) to generate TypeScript type definitions from the FastAPI-generated OpenAPI schema.

### Rationale
- `openapi-typescript` is zero-runtime (types only), aligns with spec assumption
- FastAPI auto-generates OpenAPI 3.1 JSON schema at `/openapi.json`
- Generated types replace manually-maintained `types/index.ts`
- Pipeline: `curl http://localhost:8000/openapi.json | npx openapi-typescript --stdin -o src/types/generated.ts`

### Integration Points
- Add `generate-types.sh` script to `frontend/scripts/`
- Backend must declare `response_model` on all routes for complete schema exposure (FR-011)
- Pre-commit hook validates generated types are fresh (FR-020)
- CI step runs type generation and checks for uncommitted changes

### Alternatives Considered
- **`orval` (full client generation)**: Rejected per spec assumption — over-engineering; types-only is sufficient
- **`swagger-typescript-api`**: Rejected — generates runtime code, not just types
- **Manual synchronization with linting**: Rejected — doesn't eliminate drift, just detects it late
- **Runtime schema validation (e.g., zod from OpenAPI)**: Rejected — adds runtime overhead for compile-time problem

---

## 7. Shared Constants Generation

### Decision
Build-time generation of a `frontend/src/constants/generated.ts` file containing status names, agent slugs, and pipeline defaults extracted from `backend/src/constants.py`.

### Rationale
- Per spec assumption: "Build-time codegen for shared constants (file generation) is preferred over a runtime API endpoint"
- Eliminates hardcoded status strings in frontend (SC-006)
- Single source of truth in `backend/src/constants.py`

### Implementation
- Python script reads `constants.py`, extracts exported constants, and writes TypeScript const declarations
- Runs as part of `generate-types.sh` pipeline
- Pre-commit hook ensures freshness

### Alternatives Considered
- **Runtime API endpoint**: Rejected per spec — adds request overhead and coupling
- **Shared npm/pip package**: Rejected — over-engineering for monorepo
- **JSON file import**: Considered but TypeScript const declarations provide better type inference

---

## 8. Frontend Hook Decomposition: usePipelineConfig

### Decision
Split `usePipelineConfig.ts` (193 lines, 5 concerns) into 3 hooks:
- `usePipelineOrchestration.ts` — Coordinates loading, saving, and state transitions
- `usePipelineCrud.ts` — Create, read, update, delete operations via TanStack Query
- `usePipelineDirtyState.ts` — Tracks unsaved changes and dirty state

### Rationale
- Aligns with SC-012: "Pipeline configuration hook is split into 3 hooks, each under 80 lines"
- Each hook is independently testable
- `usePipelineReducer.ts` and `usePipelineValidation.ts` already exist as separate hooks — this continues the decomposition pattern

### Alternatives Considered
- **useReducer consolidation**: Rejected — a single reducer doesn't address the testability concern
- **Context-based state management**: Rejected — hooks are simpler and don't require provider nesting
- **Keep as-is with better comments**: Rejected — doesn't address testability or single-responsibility

---

## 9. Structured Logging Activation

### Decision
Activate the existing `StructuredJsonFormatter` for production mode. Keep human-readable logs for development.

### Rationale
- `StructuredJsonFormatter` already exists in `logging_utils.py` — just needs to be the default formatter when `debug=False`
- `RequestIDMiddleware` already injects correlation IDs into `contextvars`
- `RequestIDFilter` already injects request ID into log records
- SC-010 requires "Backend logs are parseable as valid JSON by standard log aggregation tools"

### Implementation
- In `main.py` or logging configuration: use `StructuredJsonFormatter` when `settings.debug is False`
- Keep `SanitizingFormatter` (human-readable) for `debug=True` mode
- Verify all `get_logger()` calls continue to work (they use the module-level factory)

### Alternatives Considered
- **structlog library**: Rejected — adds dependency for what's already built
- **python-json-logger**: Rejected — `StructuredJsonFormatter` already implements this
- **Always JSON (even in dev)**: Rejected — hurts developer experience

---

## 10. Distributed Tracing Strategy

### Decision
Propagate trace context via the existing `X-Request-ID` header through outgoing `httpx` calls to GitHub API.

### Rationale
- `RequestIDMiddleware` already generates/propagates `X-Request-ID` and stores in `contextvars`
- FR-013 requires "context propagates from incoming requests through outgoing external API calls"
- The backend uses `httpx` for all external calls — inject `X-Request-ID` header into outgoing requests

### Implementation
- Create a thin `httpx` middleware/event hook that reads `request_id_var` from `contextvars` and adds it to outgoing request headers
- Alternatively, wrap the httpx client factory to always include the request ID
- No new dependencies required — `contextvars` and `httpx` event hooks are sufficient

### Alternatives Considered
- **OpenTelemetry**: Rejected — adds significant dependency and complexity for what can be achieved with request ID propagation; out of scope per constraints
- **W3C Trace Context (traceparent header)**: Rejected — full trace-context is over-engineering; request ID correlation is sufficient at current scale
- **Jaeger/Zipkin integration**: Rejected — external monitoring services are out of scope

---

## 11. Frontend Error Reporting

### Decision
Add a minimal error reporting endpoint on the backend (`POST /api/v1/errors`) and a global `window.onerror` / `ErrorBoundary` handler on the frontend.

### Rationale
- FR-015: "Unhandled frontend errors MUST be reported to the backend for server-side logging"
- No external error tracking service (Sentry) is in scope
- Backend already has structured logging — frontend errors logged server-side get the same treatment

### Implementation
- Backend: Add `/api/v1/errors` endpoint that accepts error payload (message, stack, url, timestamp) and logs at ERROR level
- Frontend: Global error boundary wrapping the app + `window.addEventListener('unhandledrejection', ...)` 
- Errors are fire-and-forget (no response needed beyond 202 Accepted)
- Rate-limit the endpoint to prevent abuse

### Alternatives Considered
- **Sentry**: Rejected — external service, out of scope
- **Console-only**: Rejected — doesn't meet FR-015 requirement
- **WebSocket reporting**: Rejected — over-engineering; HTTP POST is simpler and sufficient

---

## 12. CI Runtime Alignment

### Decision
Update CI workflow to use the same Python version the project targets.

### Rationale
- FR-021: "CI pipeline MUST use the same runtime version the project targets"
- `pyproject.toml` specifies `requires-python = ">=3.12"` 
- CI currently runs Python 3.12 — this aligns, but should be explicit and pinned to the same version used in the Docker image

### Implementation
- Check `backend/Dockerfile` for the Python version used in production
- Align CI matrix to match
- Use a shared variable or matrix strategy to keep versions in sync

### Alternatives Considered
- **Matrix testing multiple Python versions**: Rejected — adds CI time for a single-deployment application; one pinned version is sufficient
- **Use `pyenv` in CI**: Rejected — GitHub Actions `setup-python` is simpler

---

## 13. Database Migration Dry-Run / Rollback

### Decision
Add a `--dry-run` flag to the migration runner that reports which migrations would run without executing them. Add down-migration SQL files for reversibility.

### Rationale
- FR-019: "Database migrations MUST support a dry-run mode or rollback capability"
- Current migration runner in `services/database.py` runs all pending migrations sequentially
- Dry-run mode logs migration names and SQL without executing
- Down-migrations provide rollback capability

### Implementation
- Add `--dry-run` parameter to `run_migrations()` that logs SQL statements without executing
- For each migration `NNN_name.sql`, optionally support `NNN_name_down.sql` for rollback
- New migrations created for this feature (if any) must include down-migrations

### Alternatives Considered
- **Alembic**: Rejected — SQLite + raw SQL migrations are simpler; adding an ORM migration tool for existing raw SQL is over-engineering
- **Backup-before-migrate**: Complementary but not a substitute for dry-run visibility
- **Transaction-based rollback**: SQLite DDL is partially transactional — some statements (CREATE TABLE) can be rolled back, but ALTER TABLE cannot; explicit down-migrations are more reliable

---

## 14. Test Coverage Strategy

### Decision
Add test files for the 6 untested pages and 3 key pipeline components. Add a chat persistence integration test.

### Rationale
- SC-008: "Page-level test coverage increases from 1 tested page to 7 tested pages"
- SC-009: "Pipeline component test coverage increases from 0 to 3 dedicated component test files"
- FR-018: "Chat persistence MUST be verified by an integration test that confirms messages survive a backend restart cycle"

### Pages Needing Tests
Currently only `LoginPage` appears to have tests. Add tests for:
1. `AgentsPage.tsx`
2. `AgentsPipelinePage.tsx`
3. `ChoresPage.tsx`
4. `ProjectsPage.tsx`
5. `SettingsPage.tsx`
6. `ToolsPage.tsx`

### Components Needing Tests
1. Pipeline toolbar component
2. Model selector component
3. Unsaved changes dialog component

### Integration Test
- Start backend, send messages, restart backend, verify messages persist
- Uses `chat_store.py` persistence layer

### Alternatives Considered
- **Snapshot testing for pages**: Rejected — brittle, doesn't verify behavior
- **E2E only (Playwright)**: Complements but doesn't replace unit/component tests; E2E is slower for CI
- **Coverage threshold enforcement**: Considered as follow-up; current focus is filling specific gaps
