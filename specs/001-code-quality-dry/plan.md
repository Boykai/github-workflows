# Implementation Plan: Phase 2 — Code Quality & DRY Consolidation

**Branch**: `001-code-quality-dry` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-code-quality-dry/spec.md`

## Summary

Consolidate duplicated code patterns across the Solune backend API layer into shared, tested utilities: extend `cached_fetch()` with rate-limit-aware fallback and data-hash deduplication; create `_with_fallback()` on the base service for primary→verify→fallback resilience; migrate 14 manual catch→raise error-handling blocks to `handle_service_error()`; add a REST-based repository lookup fallback to `resolve_repository()` and deduplicate startup logic. Research confirmed all technical decisions — see [research.md](research.md) for rationale on tools.py exception types, send_tasks() non-migration, and _with_fallback() non-applicability to copilot/PR operations.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13, ruff/pyright configured for 3.13)  
**Primary Dependencies**: FastAPI ≥0.135.0, githubkit ≥0.14.6, httpx ≥0.28.0, pydantic ≥2.12.0  
**Storage**: SQLite (aiosqlite ≥0.22.0) + in-memory cache (`InMemoryCache`)  
**Testing**: pytest ≥9.0.0, pytest-asyncio ≥1.3.0, pytest-cov ≥7.0.0, ruff ≥0.15.0, pyright ≥1.1.408  
**Target Platform**: Linux server (Docker), ASGI (uvicorn)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: No degradation from refactoring; cached responses ≤5ms, fresh fetches bounded by GitHub API latency  
**Constraints**: 75% code coverage threshold; zero behavioural regressions  
**Scale/Scope**: ~30 API endpoints, ~27 service modules, mixin-based service architecture

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | `spec.md` complete with prioritised user stories, acceptance scenarios, scope boundaries |
| II | Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III | Agent-Orchestrated Execution | ✅ PASS | Single-responsibility: `speckit.plan` produces plan, research, data-model, contracts, quickstart |
| IV | Test Optionality with Clarity | ✅ PASS | Tests explicitly required by spec (FR-020 through FR-025); TDD not mandated |
| V | Simplicity and DRY | ✅ PASS | Feature's primary purpose is DRY consolidation; all abstractions justified by 3+ callers or spec mandate |

### Post-Design Re-Check

| # | Principle | Status | Notes |
|---|-----------|--------|-------|
| I | Specification-First Development | ✅ PASS | Plan aligns with all 25 functional requirements in spec |
| II | Template-Driven Workflow | ✅ PASS | Plan, research, data-model, contracts, quickstart all generated |
| III | Agent-Orchestrated Execution | ✅ PASS | Clear phase structure with defined inputs/outputs |
| IV | Test Optionality with Clarity | ✅ PASS | Test requirements mapped to specific test files and scenarios |
| V | Simplicity and DRY | ✅ PASS | No premature abstractions — `send_tasks()` left in place (research Task 6), `_with_fallback()` not forced on copilot/PR operations (research Task 7) |

**Gate Result**: PASS — No violations. No complexity tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/001-code-quality-dry/
├── plan.md                                # This file
├── research.md                            # Phase 0: Technical decisions and rationale
├── data-model.md                          # Phase 1: Entity contracts and relationships
├── quickstart.md                          # Phase 1: Developer getting-started guide
├── contracts/
│   └── internal-api-contracts.md          # Phase 1: Function-level behavioural contracts
├── checklists/
│   └── requirements.md                    # Pre-existing: spec quality checklist
└── tasks.md                               # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/                              # FastAPI route handlers (board, chat, projects, tools, etc.)
│   ├── services/
│   │   ├── github_projects/              # GitHub API service layer (mixin pattern)
│   │   │   ├── service.py                # Base service class — _with_fallback() added here
│   │   │   ├── issues.py                 # add_issue_to_project() refactored
│   │   │   ├── copilot.py                # Evaluated, not migrated (research Task 7)
│   │   │   └── pull_requests.py          # Evaluated, not migrated (research Task 7)
│   │   └── cache.py                      # cached_fetch() extended
│   ├── exceptions.py                     # AppException hierarchy (unchanged)
│   ├── logging_utils.py                  # handle_service_error() (unchanged signature)
│   ├── utils.py                          # resolve_repository() — REST fallback added
│   └── main.py                           # Startup deduplication
└── tests/
    └── unit/
        ├── test_cache.py                 # Extended: cached_fetch() new parameters
        ├── test_service.py               # New/extended: _with_fallback() tests
        └── test_utils.py                 # Extended: REST fallback in resolve_repository()
```

**Structure Decision**: Web application structure (backend + frontend). All changes are in `solune/backend/`. Frontend requires zero modifications — this is a pure backend refactoring.

## Implementation Phases

### Phase A: Repository Resolution Hardening (FR-017, FR-018, FR-019)

*Can run in parallel with Phases B and C.*

| Step | Action | Files | FR |
|------|--------|-------|----|
| A1 | Add `_resolve_repository_rest()` helper to `utils.py` that uses `github_projects_service._get_project_rest_info()` + REST project items endpoint to extract repository owner/name. Returns `tuple[str, str] | None`. | `src/utils.py` | FR-017, FR-018 |
| A2 | Insert REST fallback as Step 3 in `resolve_repository()` between GraphQL project-items (current Step 2) and workflow-config (current Step 3). On success, cache result with 300s TTL. On failure, log warning and proceed to next step. | `src/utils.py` | FR-017 |
| A3 | Replace inline owner/repo extraction in `main.py` `_auto_start_copilot_polling()` (~15 LOC) with `resolve_repository()` call. Preserve existing webhook-token fallback strategy on failure. | `src/main.py` | FR-019 |
| A4 | Add unit test: mock GraphQL project-items to fail, mock REST to succeed, verify repository resolved without reaching workflow-config step. | `tests/unit/test_utils.py` | FR-023 |

### Phase B: Cache Pattern Unification (FR-005 through FR-011)

*Can run in parallel with Phases A and C. Steps B1–B2 must complete before B3–B7.*

| Step | Action | Files | FR |
|------|--------|-------|----|
| B1 | Extend `cached_fetch()` in `cache.py` with keyword-only `rate_limit_fallback: bool = False` parameter. When `True` and `fetch_fn` raises `RateLimitError`, return stale data (via `get_stale()`) and log rate-limit warning. If no stale data, re-raise. | `src/services/cache.py` | FR-005 |
| B2 | Extend `cached_fetch()` with keyword-only `data_hash_fn: Callable[[T], str] | None = None` parameter. When provided, compute hash of fetched data. If hash matches existing entry's `data_hash`, call `refresh_ttl()` instead of `set()`. If different, call `set()` with the new hash. | `src/services/cache.py` | FR-006 |
| B3 | Migrate `list_projects()` in `projects.py` (~50 LOC inline cache) to `cached_fetch()`. Map: cache check → `cached_fetch(stale_fallback=True)`, manual `cache.get/set` → removed. Verify identical responses for cache-hit, cache-miss, stale-fallback scenarios. | `src/api/projects.py` | FR-007 |
| B4 | Migrate `list_board_projects()` in `board.py` (~87 LOC inline cache) to `cached_fetch()`. Compose a `fetch_fn` that checks the secondary user-projects cache key internally, transforms via `_to_board_projects()` if present, or fetches fresh from GitHub API and caches under both keys. | `src/api/board.py` | FR-008 |
| B5 | Migrate `get_board_data()` in `board.py` (~90 LOC inline cache) to `cached_fetch()` with `stale_fallback=True` and `rate_limit_fallback=True`. Preserve pagination, sub-issue enrichment, and DB-cached Done items fallback. | `src/api/board.py` | FR-009 |
| B6 | Migrate `send_message()` cache reads in `chat.py` (~30 LOC) to `cached_fetch()` read pattern. These are cache-read-only (no set), so use `cached_fetch()` with a no-op `fetch_fn` that returns the default value, or use `cache.get()` directly if `cached_fetch()` overhead is unjustified. | `src/api/chat.py` | FR-010 |
| B7 | Evaluate `send_tasks()` in `projects.py` for migration. **Decision: Do not migrate** (see [research.md Task 6](research.md#research-task-6-send_tasks-migration-evaluation)). Add justification comment to `send_tasks()` documenting why the stale-revalidation counter pattern is not compatible with `cached_fetch()`. | `src/api/projects.py` | FR-011 |
| B8 | Add unit tests for `cached_fetch()` extensions: (a) `rate_limit_fallback` with stale data available, (b) `rate_limit_fallback` with no stale data (re-raise), (c) `data_hash_fn` with matching hash (verify `refresh_ttl` called), (d) `data_hash_fn` with different hash (verify `set` called with hash), (e) backward compatibility (existing callers unchanged). | `tests/unit/test_cache.py` | FR-021 |

### Phase C: Fallback Abstraction (FR-012 through FR-016)

*Can run in parallel with Phases A and B.*

| Step | Action | Files | FR |
|------|--------|-------|----|
| C1 | Create `async def _with_fallback[T](self, primary_fn, fallback_fn, operation, verify_fn=None) -> T | None` on the base service in `service.py`. Implement: call primary → if verify_fn and not verified → call fallback → return result or None. All exceptions caught and logged. | `src/services/github_projects/service.py` | FR-012, FR-013, FR-014 |
| C2 | Refactor `add_issue_to_project()` in `issues.py` to use `_with_fallback()`. Map: GraphQL add → `primary_fn`, `_verify_item_on_project()` → `verify_fn`, REST fallback → `fallback_fn`. Verify identical behaviour for all three scenarios (primary success, primary+verify fail+fallback success, both fail). | `src/services/github_projects/issues.py` | FR-015 |
| C3 | Evaluate `assign_copilot_to_issue()` and `find_existing_pr_for_issue()` for `_with_fallback()` adoption. **Decision: Do not apply** (see [research.md Task 7](research.md#research-task-7-_with_fallback-applicability--copilotpy-and-pull_requestspy)). Add documentation comments to both functions explaining the rationale. | `src/services/github_projects/copilot.py`, `src/services/github_projects/pull_requests.py` | FR-016 |
| C4 | Add unit tests for `_with_fallback()`: (a) primary succeeds without verify, (b) primary succeeds with verify passing, (c) primary succeeds but verify fails → fallback succeeds, (d) primary raises → fallback succeeds, (e) both raise → returns None (soft-failure), (f) verify raises → treated as failure → fallback. | `tests/unit/test_service.py` | FR-022 |

### Phase D: Error Handling Consolidation (FR-001 through FR-004)

*Sequential: D1 must complete before D2–D5.*

| Step | Action | Files | FR |
|------|--------|-------|----|
| D1 | Inspect FastAPI exception handler middleware in `main.py:486-515`. Verify `AppException` vs `HTTPException` handling. **Decision documented in [research.md Task 1](research.md#research-task-1-exception-middleware-behaviour--httpexception-vs-appexception)**: Do not convert `HTTPException` sites that would change response contract; migrate only sites where the raised type has an `AppException` equivalent. | `src/main.py` (read-only inspection) | FR-004 |
| D2 | Migrate 3 error-handling sites in `board.py` to `handle_service_error()`. Sites: lines 246-260 (rate-limit/auth split), 405-407 (ValueError→NotFoundError), 408-433 (rate-limit/auth/generic split). For split patterns, use `isinstance` checks before calling `handle_service_error()` with the appropriate `error_cls`. | `src/api/board.py` | FR-001, FR-002 |
| D3 | Migrate applicable error-handling sites in `tools.py` to `handle_service_error()`. For each of the 7 sites, evaluate individually: sites raising `HTTPException(500)` for internal errors → migrate to `handle_service_error(e, op, GitHubAPIError)`; sites raising `HTTPException(4xx)` consumed by MCP framework → keep as-is. | `src/api/tools.py` | FR-001, FR-002, FR-004 |
| D4 | Migrate 1 error site in `pipelines.py:140`, 1 in `tasks.py:137`, and 2 in `webhooks.py:246` to `handle_service_error()`. Verify each produces identical client-visible responses. | `src/api/pipelines.py`, `src/api/tasks.py`, `src/api/webhooks.py` | FR-001, FR-002 |
| D5 | Verify no error-returning handlers (health checks, WebSocket, error-returning webhooks) were migrated. These MUST remain as-is (return dicts, not raise). | All API files | FR-003 |

### Phase E: Verification (FR-020 through FR-025)

*After all phases complete.*

| Step | Action | FR |
|------|--------|----|
| E1 | Run `pytest tests/unit/ -x -q` — all existing tests must pass with zero modifications. | FR-020 |
| E2 | Run new unit tests for `cached_fetch()` extensions (B8). | FR-021 |
| E3 | Run new unit tests for `_with_fallback()` (C4). | FR-022 |
| E4 | Run REST fallback test for `resolve_repository()` (A4). | FR-023 |
| E5 | Integration smoke tests: board, project-list, and chat endpoints via the UI. Confirm identical responses. | FR-024 |
| E6 | Grep audit: `grep -rn 'logger.error\|logger.exception' src/api/ \| grep -v handle_service_error` — output must contain only excluded patterns (health checks, WebSocket, error-returning handlers). | FR-025 |
| E7 | Run `ruff check src/` and `pyright src/` — no new lint or type errors introduced. | — |

## Dependencies

```
Phase A ──────────────── independent ──────────────── Phase E (verification)
Phase B: B1,B2 ──► B3,B4,B5,B6,B7 ──► B8 ─────────► Phase E
Phase C ──────────────── independent ──────────────── Phase E
Phase D: D1 ──► D2,D3,D4,D5 ──────────────────────► Phase E
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Response contract change from error migration | Medium | High | Per-site verification of status code + message format; test assertions |
| `cached_fetch()` backward incompatibility | Low | High | Keyword-only parameters; existing callers require zero changes |
| `_with_fallback()` alters soft-failure contract | Low | Medium | Explicit `None` return on total failure; never re-raises |
| Dual-cache-key regression in `list_board_projects()` | Medium | Medium | Composed `fetch_fn` tested with both keys warm, cold, and stale |
| REST fallback in `resolve_repository()` returns incorrect repo | Low | Low | Same validation as existing steps; treat inaccessible repos as lookup failure |

## Complexity Tracking

> No constitution violations detected. No entries required.
