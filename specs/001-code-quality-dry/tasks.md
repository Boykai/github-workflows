# Tasks: Phase 2 — Code Quality & DRY Consolidation

**Input**: Design documents from `/specs/001-code-quality-dry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are REQUIRED — explicitly requested in the feature specification (FR-020 through FR-025).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Phases A (US4), B (US2), and C (US3) can proceed in parallel. Phase D (US1) is internally sequential.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Web application (backend + frontend)
- **All changes**: `solune/backend/` (pure backend refactoring — zero frontend changes)
- **Source**: `solune/backend/src/`
- **Tests**: `solune/backend/tests/unit/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify baseline state and confirm existing tests pass before any refactoring

- [ ] T001 Run baseline test suite (`pytest tests/unit/ -x -q`) to confirm all existing tests pass before changes
- [ ] T002 Run baseline lint/type checks (`ruff check src/` and `pyright src/`) to capture pre-existing state

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create and extend the shared utilities that user story implementation tasks depend on

**⚠️ CRITICAL**: No user story work can begin until the relevant foundational tasks are complete:
- US1 depends on T006 (middleware inspection)
- US2 depends on T003 + T004 (cached_fetch extensions)
- US3 depends on T005 (_with_fallback creation)
- US4 has no foundational dependencies (can start after Phase 1)

- [ ] T003 [P] Extend `cached_fetch()` with keyword-only `rate_limit_fallback: bool = False` parameter in `solune/backend/src/services/cache.py` — when True and `fetch_fn` raises `RateLimitError`, return stale data via `get_stale()` and log rate-limit warning; if no stale data, re-raise
- [ ] T004 [P] Extend `cached_fetch()` with keyword-only `data_hash_fn: Callable[[T], str] | None = None` parameter in `solune/backend/src/services/cache.py` — when provided, compute hash of fetched data; if hash matches existing entry's `data_hash`, call `refresh_ttl()` instead of `set()`; if different, call `set()` with new hash
- [ ] T005 [P] Create `async def _with_fallback[T](self, primary_fn, fallback_fn, operation, verify_fn=None) -> T | None` on base service class in `solune/backend/src/services/github_projects/service.py` — implement primary → optional verify → fallback pattern with soft-failure contract (returns None on total failure, never raises)
- [ ] T006 Inspect FastAPI exception handler middleware in `solune/backend/src/main.py` (lines ~486-515) and confirm research.md Task 1 decision: do NOT convert HTTPException sites in tools.py that would change the `{"detail": ...}` response contract to `{"error": ..., "details": {...}}`; migrate only sites where the raised type has an AppException equivalent

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Unified Error-Handling Across Services (Priority: P1) 🎯 MVP

**Goal**: Consolidate 14 manual catch→raise error-handling patterns into calls to `handle_service_error()`, ensuring consistent logging, message sanitisation, and exception classification across the API layer.

**Independent Test**: Trigger each migrated error path in unit tests and verify that the logged message, raised exception class, and client-visible payload are identical to pre-migration behaviour. Run grep audit to confirm only excluded patterns remain outside `handle_service_error()`.

### Implementation for User Story 1

- [ ] T007 [P] [US1] Migrate 3 error-handling sites in `solune/backend/src/api/board.py` to `handle_service_error()`: lines ~246-260 (rate-limit/auth split — use isinstance checks before calling with appropriate `error_cls`), lines ~405-407 (ValueError→NotFoundError), lines ~408-433 (rate-limit/auth/generic split)
- [ ] T008 [P] [US1] Migrate applicable error-handling sites in `solune/backend/src/api/tools.py` to `handle_service_error()` — evaluate each of the 7 sites individually per research.md Task 1 decision: sites raising `HTTPException(500)` for internal errors → migrate to `handle_service_error(e, op, GitHubAPIError)`; sites raising `HTTPException(4xx)` consumed by MCP framework → keep as-is with justification comment
- [ ] T009 [P] [US1] Migrate 1 error-handling site in `solune/backend/src/api/pipelines.py` (line ~140) to `handle_service_error()`
- [ ] T010 [P] [US1] Migrate 1 error-handling site in `solune/backend/src/api/tasks.py` (line ~137) to `handle_service_error()`
- [ ] T011 [P] [US1] Migrate 2 error-handling sites in `solune/backend/src/api/webhooks.py` (lines ~246) to `handle_service_error()`
- [ ] T012 [US1] Verify no error-returning handlers (health checks, WebSocket, error-returning webhook handlers) were migrated — these MUST remain as-is (return dicts, not raise)

**Checkpoint**: All 14 error-handling sites migrated (or explicitly excluded with justification). Grep audit should show only excluded patterns outside `handle_service_error()`.

---

## Phase 4: User Story 2 — Standardised Caching with Graceful Degradation (Priority: P2)

**Goal**: Migrate 4 inline cache-aside patterns (~260 LOC combined) to the extended `cached_fetch()` utility, reducing duplicated cache logic by at least 60% while preserving identical endpoint behaviour for cache-hit, cache-miss, stale-fallback, and rate-limit scenarios.

**Independent Test**: Call each migrated endpoint with cache warm, cold, and stale (simulated fetch failure) and verify identical response payloads and status codes compared to pre-migration implementation.

### Implementation for User Story 2

- [ ] T013 [P] [US2] Migrate `list_projects()` in `solune/backend/src/api/projects.py` (~50 LOC inline cache) to `cached_fetch()` — map: cache check → `cached_fetch(stale_fallback=True)`, remove manual `cache.get/set` calls
- [ ] T014 [US2] Migrate `list_board_projects()` in `solune/backend/src/api/board.py` (~87 LOC inline cache) to `cached_fetch()` — compose a `fetch_fn` that checks secondary `user_projects:{user_id}` cache key internally, transforms via `_to_board_projects()` if present, or fetches fresh from GitHub API and caches under both keys
- [ ] T015 [US2] Migrate `get_board_data()` in `solune/backend/src/api/board.py` (~90 LOC inline cache) to `cached_fetch()` with `stale_fallback=True` and `rate_limit_fallback=True` — preserve pagination, sub-issue enrichment, and DB-cached Done items fallback
- [ ] T016 [P] [US2] Migrate `send_message()` cache reads in `solune/backend/src/api/chat.py` (~30 LOC) to `cached_fetch()` read pattern — these are cache-read-only (no set); use `cached_fetch()` with a no-op `fetch_fn` or use `cache.get()` directly if overhead is unjustified
- [ ] T017 [US2] Evaluate `send_tasks()` in `solune/backend/src/api/projects.py` for migration to `cached_fetch()` — **Decision (from research.md Task 6): Do not migrate** — add justification comment documenting why the stale-revalidation counter pattern is incompatible with `cached_fetch()`
- [ ] T018 [US2] Add unit tests for `cached_fetch()` extensions in `solune/backend/tests/unit/test_cache.py`: (a) `rate_limit_fallback` with stale data available, (b) `rate_limit_fallback` with no stale data (verify re-raise), (c) `data_hash_fn` with matching hash (verify `refresh_ttl` called), (d) `data_hash_fn` with different hash (verify `set` called with hash), (e) backward compatibility (existing callers unchanged)

**Checkpoint**: All 4 cache patterns migrated, `send_tasks()` evaluated and documented. Cache-hit/miss/stale behaviour verified identical for each endpoint.

---

## Phase 5: User Story 3 — Resilient Fallback Abstraction for Service Operations (Priority: P3)

**Goal**: Refactor `add_issue_to_project()` to use the `_with_fallback()` abstraction, demonstrating the declarative primary→verify→fallback pattern. Evaluate and document non-adoption for copilot/PR operations.

**Independent Test**: Invoke `_with_fallback()` with mock primary/fallback/verify functions covering: primary succeeds, primary fails but fallback succeeds, and both fail. Verify the refactored `add_issue_to_project()` produces identical behaviour for all three scenarios.

### Implementation for User Story 3

- [ ] T019 [US3] Refactor `add_issue_to_project()` in `solune/backend/src/services/github_projects/issues.py` to use `_with_fallback()` — map: GraphQL add → `primary_fn`, `_verify_item_on_project()` → `verify_fn`, REST fallback → `fallback_fn`; verify identical behaviour for primary success, primary+verify fail+fallback success, and both-fail scenarios
- [ ] T020 [P] [US3] Evaluate and document `_with_fallback()` non-adoption for `assign_copilot_to_issue()` in `solune/backend/src/services/github_projects/copilot.py` — **Decision (from research.md Task 7): Do not apply** — add documentation comment explaining pre-step logic and `bool` return type make it a poor fit
- [ ] T021 [P] [US3] Evaluate and document `_with_fallback()` non-adoption for `find_existing_pr_for_issue()` in `solune/backend/src/services/github_projects/pull_requests.py` — **Decision (from research.md Task 7): Do not apply** — add documentation comment explaining divergent post-processing between primary/fallback paths
- [ ] T022 [US3] Add unit tests for `_with_fallback()` in `solune/backend/tests/unit/test_service.py`: (a) primary succeeds without verify, (b) primary succeeds with verify passing, (c) primary succeeds but verify fails → fallback succeeds, (d) primary raises → fallback succeeds, (e) both raise → returns None (soft-failure), (f) verify raises → treated as failure → fallback called

**Checkpoint**: `add_issue_to_project()` refactored. `_with_fallback()` tested with 100% branch coverage. Copilot/PR operations evaluated and documented.

---

## Phase 6: User Story 4 — Repository Resolution Hardening and Deduplication (Priority: P3)

**Goal**: Add a REST-based repository lookup step to `resolve_repository()` for resilience against GraphQL failures, and eliminate duplicated owner/repo extraction logic in application startup.

**Independent Test**: Mock GraphQL project-items to fail, mock REST to succeed, verify repository resolved without reaching the workflow-config step. Confirm startup still resolves repositories correctly after replacing inline logic.

### Implementation for User Story 4

- [ ] T023 [US4] Add `_resolve_repository_rest()` helper to `solune/backend/src/utils.py` — uses `github_projects_service._get_project_rest_info()` + REST project items endpoint to extract repository owner/name; returns `tuple[str, str] | None`
- [ ] T024 [US4] Insert REST fallback as Step 3 in `resolve_repository()` in `solune/backend/src/utils.py` — between GraphQL project-items (current Step 2) and workflow-config (current Step 3); on success, cache result with 300s TTL; on failure, log warning and proceed to next step
- [ ] T025 [US4] Replace inline owner/repo extraction in `_auto_start_copilot_polling()` in `solune/backend/src/main.py` (~15 LOC) with `resolve_repository()` call — preserve existing webhook-token fallback strategy on failure
- [ ] T026 [US4] Add unit test for REST fallback path in `resolve_repository()` in `solune/backend/tests/unit/test_utils.py` — mock GraphQL project-items to fail, mock REST to succeed, verify repository resolved without reaching workflow-config step

**Checkpoint**: Repository resolution has a new REST fallback step. Startup logic deduplicated. REST fallback verified by unit test.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end verification across all user stories and final quality checks

- [ ] T027 Run full test suite (`pytest tests/unit/ -x -q`) and confirm all existing + new tests pass with zero regressions (FR-020)
- [ ] T028 Run `ruff check src/` and `pyright src/` — confirm no new lint or type errors introduced
- [ ] T029 Run grep audit: `grep -rn 'logger.error\|logger.exception' src/api/ | grep -v handle_service_error` — output must contain only excluded patterns (health checks, WebSocket, error-returning handlers) (FR-025)
- [ ] T030 Integration smoke tests across board, project-list, and chat endpoints via the UI — confirm identical responses, no user-facing regressions (FR-024)
- [ ] T031 Run quickstart.md validation — verify all example commands and patterns in `specs/001-code-quality-dry/quickstart.md` match the final implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS user story tasks as specified:
  - T003, T004 (cached_fetch extensions) → blocks US2 migration tasks (T013–T018)
  - T005 (_with_fallback creation) → blocks US3 refactoring task (T019)
  - T006 (middleware inspection) → blocks US1 migration tasks (T007–T012)
  - T003, T004, T005 can run in **parallel** (different files)
- **User Story 1 (Phase 3)**: Depends on T006 completion. Tasks T007–T011 can run in **parallel** (different files)
- **User Story 2 (Phase 4)**: Depends on T003 + T004 completion. T013 and T016 can run in parallel; T014, T015 are sequential (same file — board.py)
- **User Story 3 (Phase 5)**: Depends on T005 completion. T020 and T021 can run in parallel (different files)
- **User Story 4 (Phase 6)**: No foundational dependencies — can start after Phase 1. T023 → T024 → T025 are sequential
- **Polish (Phase 7)**: Depends on ALL user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after T006 (middleware inspection) — No dependencies on other stories
- **User Story 2 (P2)**: Can start after T003 + T004 (cached_fetch extensions) — No dependencies on other stories
- **User Story 3 (P3)**: Can start after T005 (_with_fallback creation) — No dependencies on other stories
- **User Story 4 (P3)**: Can start after Phase 1 — No dependencies on other stories

### Cross-Story Parallelism

All four user stories can proceed **in parallel** once their respective foundational dependencies are met:

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ├── T003 + T004 ────► Phase 4 (US2: Caching)
    ├── T005 ───────────► Phase 5 (US3: Fallback)
    ├── T006 ───────────► Phase 3 (US1: Error Handling)
    └── (no dependency) ► Phase 6 (US4: Repo Resolution)
                              │
                              ▼
                        Phase 7 (Polish & Verification)
```

### Within Each User Story

- Foundational dependency MUST complete before story tasks
- Implementation tasks before test tasks
- Evaluation/documentation tasks can run in parallel with implementation (different files)
- Story complete before moving to Phase 7

### Parallel Opportunities

- **Foundational**: T003, T004, T005 can run in parallel (three different files)
- **US1**: T007, T008, T009, T010, T011 can run in parallel (five different files)
- **US2**: T013 and T016 can run in parallel (projects.py and chat.py)
- **US3**: T020 and T021 can run in parallel (copilot.py and pull_requests.py)
- **Cross-story**: All four user stories can run in parallel after their foundational dependencies

---

## Parallel Example: User Story 1

```bash
# After T006 (middleware inspection) completes, launch all US1 migrations together:
Task: T007 "Migrate 3 error sites in board.py"
Task: T008 "Migrate applicable error sites in tools.py"
Task: T009 "Migrate 1 error site in pipelines.py"
Task: T010 "Migrate 1 error site in tasks.py"
Task: T011 "Migrate 2 error sites in webhooks.py"

# Then verify:
Task: T012 "Verify no error-returning handlers were migrated"
```

## Parallel Example: Foundational Phase

```bash
# All three foundational tasks can run simultaneously:
Task: T003 "Extend cached_fetch() with rate_limit_fallback in cache.py"
Task: T004 "Extend cached_fetch() with data_hash_fn in cache.py"
Task: T005 "Create _with_fallback() on base service in service.py"

# T006 (middleware inspection) can also run in parallel:
Task: T006 "Inspect FastAPI exception handler middleware in main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline verification)
2. Complete Phase 2: Foundational — specifically T006 (middleware inspection)
3. Complete Phase 3: User Story 1 (error handling consolidation)
4. **STOP and VALIDATE**: Run grep audit (T029) to confirm all 14 sites migrated correctly
5. This delivers the highest-risk, highest-value improvement first

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Error handling consolidated → Grep audit passes (MVP!)
3. Add User Story 2 → Cache patterns unified → ~260 LOC reduced to ~100 LOC
4. Add User Story 3 → Fallback abstraction operational → `add_issue_to_project()` declarative
5. Add User Story 4 → Repository resolution hardened → Startup deduplicated
6. Complete Phase 7 → Full verification across all stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (error handling — P1)
   - Developer B: User Story 2 (caching — P2)
   - Developer C: User Story 3 (fallback abstraction — P3)
   - Developer D: User Story 4 (repo resolution — P3) — can start immediately after Setup
3. Stories complete and integrate independently
4. Team runs Phase 7 verification together

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 31 |
| **US1 tasks (Error Handling, P1)** | 6 (T007–T012) |
| **US2 tasks (Caching, P2)** | 6 (T013–T018) |
| **US3 tasks (Fallback Abstraction, P3)** | 4 (T019–T022) |
| **US4 tasks (Repo Resolution, P3)** | 4 (T023–T026) |
| **Setup tasks** | 2 (T001–T002) |
| **Foundational tasks** | 4 (T003–T006) |
| **Polish/Verification tasks** | 5 (T027–T031) |
| **Parallel opportunities** | 5 groups (Foundational: 4 tasks, US1: 5 tasks, US2: 2 tasks, US3: 2 tasks, cross-story: 4 stories) |
| **Suggested MVP scope** | User Story 1 only (error handling consolidation) |
| **Format validation** | ✅ All 31 tasks follow checklist format (checkbox, ID, labels, file paths) |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Tests are included per spec requirements FR-020 through FR-025
- Research decisions (send_tasks non-migration, copilot/PR non-adoption) are pre-made — tasks document and confirm them
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
