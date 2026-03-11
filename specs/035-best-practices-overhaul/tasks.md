# Tasks: Codebase Improvement Plan — Modern Best Practices Overhaul

**Input**: Design documents from `/specs/035-best-practices-overhaul/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Integration tests are included in Phase 7 (US6) as explicitly required by FR-026/FR-027. Unit tests for new modules (e.g., `pipeline_state_store.py`, `chat_store.py`, `CSPMiddleware`) are expected to be written as part of each implementation task where the existing test infrastructure supports it, but are not called out as separate tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. Phase 1 (Data Integrity) is the blocking foundation — all other user stories depend on it. Phases 3–6 (US2–US5) can run in parallel after Phase 2 completes. Phases 7–8 (US6–US7) are independent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Migrations: `backend/src/migrations/`
- Tests: `backend/tests/unit/`, `backend/tests/integration/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files and migration required by Phase 2 (Data Integrity)

- [ ] T001 Create pipeline state migration in `backend/src/migrations/021_pipeline_state.sql` with tables: `pipeline_states`, `issue_main_branches`, `issue_sub_issue_map`, `agent_trigger_inflight` per data-model.md schema
- [ ] T002 Verify existing migration `backend/src/migrations/012_chat_persistence.sql` is present and auto-applied by `init_database()` in `backend/src/database.py`

---

## Phase 2: User Story 1 — Pipeline State Survives Container Restart (Priority: P1) 🎯 MVP

**Goal**: Persist all pipeline orchestration and chat state to SQLite so that no data is lost on container restart. Add async-safe locking for all shared mutable state.

**Independent Test**: Stop the running container with active pipeline states. Restart. Confirm all pipeline states, chat messages, and proposals are recovered.

**⚠️ CRITICAL**: This phase blocks ALL other user story work. No other phase may begin until Phase 2 is complete.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Create `backend/src/services/pipeline_state_store.py` with write-through cache functions (`init_pipeline_state_store`, `get_pipeline_state`, `set_pipeline_state`, `delete_pipeline_state`, `get_main_branch`, `set_main_branch`, `delete_main_branch`, `get_sub_issue_map`, `set_sub_issue_map`, `delete_sub_issue_map`, `get_trigger_inflight`, `set_trigger_inflight`, `delete_trigger_inflight`) following `session_store.py` pattern and contracts/pipeline-state-store.md interface
- [ ] T004 [P] [US1] Create `backend/src/services/chat_store.py` with SQLite persistence functions (`save_message`, `get_messages`, `clear_messages`, `save_proposal`, `get_proposals`, `update_proposal_status`, `save_recommendation`, `get_recommendations`, `update_recommendation_status`) per contracts/chat-persistence.md interface
- [ ] T005 [US1] Add module-level `_state_lock = asyncio.Lock()` in `backend/src/services/workflow_orchestrator/transitions.py` and wrap all public mutation functions (`set_pipeline_state`, `delete_pipeline_state`, `set_main_branch`, `delete_main_branch`, `set_sub_issue_map`, `delete_sub_issue_map`, `set_trigger_inflight`, `delete_trigger_inflight`) with `async with _state_lock:`
- [ ] T006 [US1] Integrate `pipeline_state_store.py` into `backend/src/services/workflow_orchestrator/transitions.py` — replace direct BoundedDict writes with write-through calls to the persistent store (L1 cache + SQLite), keeping BoundedDict as the L1 read layer
- [ ] T007 [US1] Replace in-memory dicts (`_messages`, `_proposals`, `_recommendations`) in `backend/src/api/chat.py` (L91-94) with calls to `chat_store.py` functions, using `get_database()` dependency for the aiosqlite connection
- [ ] T008 [P] [US1] Add `_ws_lock = asyncio.Lock()` in `backend/src/services/websocket.py` (L12-14) and wrap `ConnectionManager.connect()` and `disconnect()` methods with `async with _ws_lock:`
- [ ] T009 [US1] Initialize pipeline state store during application startup: call `init_pipeline_state_store(db)` in the `lifespan()` function in `backend/src/main.py` to load all active pipeline states from SQLite into L1 caches

**Checkpoint**: Pipeline and chat state survive container restarts. All existing tests pass.

---

## Phase 3: User Story 2 — Developer Fixes a Bug in a High-Complexity Function (Priority: P1)

**Goal**: Decompose the 5 highest cyclomatic-complexity functions (backend CC 123/91/72+66, frontend CC 79/69) into focused handlers/sub-hooks, each below their target CC threshold.

**Independent Test**: Measure cyclomatic complexity of all 5 target functions before and after. Confirm all score at or below target thresholds. Run full test suite with zero regressions.

### Implementation for User Story 2

#### Backend Decomposition

- [ ] T010 [US2] Decompose `post_agent_outputs_from_pr` (CC 123) in `backend/src/services/copilot_polling/agent_output.py` (L20) into focused async handler functions: extract `_scan_pipeline_issues()`, `_extract_pr_outputs()`, `_route_output_to_destination()`, `_advance_pipeline_state()` — each function ≤15 CC. Use a dispatch dict or match/case for output routing per research R-004
- [ ] T011 [US2] Decompose `assign_agent_for_status` (CC 91) in `backend/src/services/workflow_orchestrator/orchestrator.py` (L798) into strategy methods on `WorkflowOrchestrator`: extract `_resolve_agent_config()`, `_determine_base_ref()`, `_resolve_sub_issue()`, `_build_tracking_table_override()` — each method ≤20 CC per research R-004
- [ ] T012 [US2] Decompose `recover_stalled_issues` (CC 72+66) in `backend/src/services/copilot_polling/recovery.py` (L102+L242) into focused recovery helpers: extract `_recover_single_issue()`, `_validate_copilot_assignment()`, `_validate_wip_pr()` — each function ≤20 CC per research R-004

#### Frontend Decomposition

- [ ] T013 [US2] Decompose `usePipelineConfig` (CC 79) in `frontend/src/hooks/usePipelineConfig.ts`: extract CRUD operations into new `frontend/src/hooks/usePipelineCrud.ts` sub-hook, return grouped objects `{ crud, validation, state, assignment, model, board }` instead of 30 flat properties — each sub-hook returns ≤8 properties per research R-005/R-012
- [ ] T014 [US2] Decompose `useAgentConfig` (CC 69) in `frontend/src/hooks/useAgentConfig.ts`: extract DnD operations into new `frontend/src/hooks/useAgentDnd.ts`, extract column mutation logic into `useAgentColumns` sub-hook, return grouped objects — each sub-hook ≤25 CC per research R-005
- [ ] T015 [US2] Update all consumers of `usePipelineConfig` and `useAgentConfig` across `frontend/src/` to use the new grouped return objects instead of flat property destructuring

**Checkpoint**: All 5 target functions/hooks are below their CC thresholds. All existing tests pass.

---

## Phase 4: User Story 3 — Developer Adds a New API Endpoint Needing Repository Info (Priority: P1)

**Goal**: Consolidate 8 duplicate repository resolution paths into one canonical function, adopt existing error infrastructure for all exception handling, and add Pydantic models for all API inputs.

**Independent Test**: Search codebase for all repository resolution call sites — confirm all use the canonical function. Search for bare `except Exception` — confirm zero remain. Confirm all API endpoints validate inputs through Pydantic models.

### Implementation for User Story 3

#### Repository Resolution Consolidation

- [ ] T016 [US3] Create FastAPI dependency `get_repository()` in `backend/src/dependencies.py` that calls `resolve_repository()` from `backend/src/utils.py` with unified error handling, eliminating the repeated try/except wrapper pattern per research R-006
- [ ] T017 [US3] Replace all duplicate repository resolution + try/except patterns in `backend/src/api/workflow.py`, `backend/src/api/agents.py`, `backend/src/api/projects.py`, `backend/src/api/tasks.py`, `backend/src/api/chat.py`, `backend/src/api/chores.py`, and `backend/src/main.py` with `Depends(get_repository)`

#### Error Handling Adoption

- [ ] T018 [P] [US3] Define specific exception types in `backend/src/exceptions.py` if not already present: `GitHubAPIError`, `ValidationError`, `DatabaseError`, `AuthenticationError`, `NotFoundError` — all inheriting from `AppException`
- [ ] T019 [US3] Replace bare `except Exception` blocks (~8) in `backend/src/api/agents.py` with `@handle_github_errors` decorator or `handle_service_error()` calls with specific exception types per contracts/error-handling.md transformation rules
- [ ] T020 [US3] Replace bare `except Exception` blocks (~6) in `backend/src/api/workflow.py` with `@handle_github_errors` decorator or `handle_service_error()` calls per contracts/error-handling.md
- [ ] T021 [US3] Replace bare `except Exception` blocks (~3) in `backend/src/api/health.py` with specific exception types (`aiosqlite.Error` for DB checks) and structured logging per contracts/error-handling.md Rule 3
- [ ] T022 [US3] Replace remaining bare `except Exception` blocks in `backend/src/api/chat.py`, `backend/src/api/projects.py`, `backend/src/api/settings.py`, `backend/src/api/webhooks.py`, and any other `backend/src/api/*.py` files per contracts/error-handling.md

#### Type-Safe API Inputs

- [ ] T023 [P] [US3] Create Pydantic v2 input models in `backend/src/models/api_inputs.py`: `SettingsUpdate` model (replacing `dict` in settings.py L120), `WebhookPRData` and `WebhookPayload` discriminated union models (replacing `dict` in webhooks.py L53) per research R-008 and data-model.md
- [ ] T024 [US3] Replace `updates: dict = {}` parameter in `backend/src/api/settings.py` with `SettingsUpdate` Pydantic model from `models/api_inputs.py`
- [ ] T025 [US3] Replace `pr_data: dict` parameter in `backend/src/api/webhooks.py` with `WebhookPRData` Pydantic model and add discriminated union dispatch for webhook payloads

**Checkpoint**: Zero duplicate resolution paths. Zero bare `except Exception` in API files. All API inputs validated through Pydantic. All existing tests pass.

---

## Phase 5: User Story 4 — Developer Writes Tests Without Service Coupling (Priority: P2)

**Goal**: Replace module-level singletons with FastAPI lifespan + `app.state` + `Depends()` pattern and break circular imports via shared protocols.

**Independent Test**: Write a unit test for any service that currently uses a module-level singleton. Confirm the test injects a mock dependency without modifying global state. Confirm the test runs in under 1 second.

### Implementation for User Story 4

- [ ] T026 [P] [US4] Create `backend/src/interfaces.py` with `typing.Protocol` definitions: `GitHubClientFactoryProtocol`, `GitHubProjectsServiceProtocol`, `SessionDependencyProtocol` per data-model.md protocol definitions and research R-009
- [ ] T027 [US4] Move `github_projects_service = GitHubProjectsService()` singleton (L343 of `backend/src/services/github_projects/service.py`) into `lifespan()` in `backend/src/main.py` using `app.state.github_projects_service`, and create corresponding `Depends()` function in `backend/src/dependencies.py`
- [ ] T028 [US4] Move lazy-initialized AI agent service singleton (`_ai_agent_service_instance` in `backend/src/services/ai_agent.py` L921-943) into `lifespan()` in `backend/src/main.py` using `app.state.ai_agent_service`, and create corresponding `Depends()` function in `backend/src/dependencies.py`
- [ ] T029 [US4] Remove lazy import hack for `get_session_dep` in `backend/src/dependencies.py` (L55-64) by importing from `backend/src/interfaces.py` protocols instead
- [ ] T030 [US4] Remove conditional factory loading in `backend/src/services/github_projects/service.py` (L55-59) by using protocol imports from `backend/src/interfaces.py`
- [ ] T031 [US4] Update all direct singleton imports across `backend/src/` to use `Depends()` injection instead — search for `from src.services.github_projects.service import github_projects_service` and `from src.services.ai_agent import get_ai_agent_service`

**Checkpoint**: Zero module-level singleton service instances. Zero lazy import hacks. All services injected via `Depends()`. All existing tests pass.

---

## Phase 6: User Story 5 — Security Auditor Reviews the Application (Priority: P2)

**Goal**: Harden CORS, add CSP headers, require explicit admin designation, and enforce user-scoped session access.

**Independent Test**: Verify CORS headers do not contain wildcards. Verify CSP header present on every response. Verify new account is not auto-promoted to admin when `ADMIN_GITHUB_USER_ID` is set.

### Implementation for User Story 5

- [ ] T032 [US5] Replace `allow_headers=["*"]` with explicit header list `["Authorization", "Content-Type", "Accept", "X-Request-ID", "X-Requested-With"]` and replace `allow_methods=["*"]` with `["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]` in CORS middleware configuration in `backend/src/main.py` per contracts/security-middleware.md
- [ ] T033 [P] [US5] Create `backend/src/middleware/csp.py` with `CSPMiddleware` class (Starlette `BaseHTTPMiddleware`) that adds `Content-Security-Policy` header to all responses with directives: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'` per contracts/security-middleware.md
- [ ] T034 [US5] Register `CSPMiddleware` in `backend/src/main.py` after CORS middleware
- [ ] T035 [US5] Add `admin_github_user_id: int | None = None` to Settings model in `backend/src/config.py` and update `require_admin()` in `backend/src/dependencies.py` (L103-115) to check `ADMIN_GITHUB_USER_ID` env var before auto-promoting first user, with fallback + warning log per contracts/security-middleware.md and research R-011
- [ ] T036 [US5] Verify all session-scoped queries in `backend/src/services/session_store.py` and `backend/src/services/chat_store.py` include `session_id` WHERE filter for user isolation

**Checkpoint**: CORS specifies explicit headers. CSP header on every response. Admin designation requires explicit config. Sessions user-scoped. All existing tests pass.

---

## Phase 7: User Story 6 — Developer Investigates a Production Error (Priority: P2)

**Goal**: Ensure every exception handler logs errors with full traceback, add frontend telemetry, create integration tests, tighten test assertions, and remove build artifacts from VCS.

**Independent Test**: Trigger a known error condition — confirm error appears in logs with full traceback. Run integration tests — confirm they cover the pipeline lifecycle.

### Implementation for User Story 6

- [ ] T037 [US6] Audit all `except` blocks in `backend/src/api/*.py` and `backend/src/services/*.py` — ensure every handler includes `logger.error("...", exc_info=True)` and no exception is silently swallowed (FR-024)
- [ ] T038 [P] [US6] Verify `window.onerror` and `unhandledrejection` handlers exist in `frontend/src/main.tsx` — add them if missing (FR-025). Note: research R-012 indicates these may already be present
- [ ] T039 [P] [US6] Create `backend/tests/integration/test_pipeline_lifecycle.py` with at least one end-to-end pipeline lifecycle test covering creation through completion (FR-026)
- [ ] T040 [US6] Audit all test files in `backend/tests/` — tighten overly broad assertions like `assert response.status_code in (200, 503)` to check for specific expected status codes (FR-027)
- [ ] T041 [US6] Add `htmlcov/`, `coverage/`, `e2e-report/`, `test-results/` to root `.gitignore` and remove any committed instances from version control tracking using `git rm -r --cached` (FR-028)

**Checkpoint**: Every exception handler logs with traceback. Frontend captures unhandled errors. Integration test suite covers pipeline lifecycle. All assertions specific. Build artifacts excluded from VCS. All existing tests pass.

---

## Phase 8: User Story 7 — Developer Uses a Frontend Hook with a Clean API (Priority: P3)

**Goal**: Restructure frontend hook APIs to return focused, grouped objects instead of flat property bags. Standardize retry logic.

**Independent Test**: Import the restructured hook in a test component. Confirm it provides grouped objects. Confirm all existing components that use the hook continue to function.

### Implementation for User Story 7

- [ ] T042 [US7] Finalize grouped return API for `usePipelineConfig` in `frontend/src/hooks/usePipelineConfig.ts` — if not fully done in T013, ensure return type is `{ crud, validation, state, assignment, model, board }` with each group ≤8 properties per research R-012
- [ ] T043 [US7] Finalize grouped return API for `useAgentConfig` in `frontend/src/hooks/useAgentConfig.ts` — ensure return type uses grouped objects with each group ≤8 properties
- [ ] T044 [US7] Verify all retry logic: backend uses `tenacity` decorators (already standardized per research R-013), frontend uses TanStack Query `retry` option. Confirm no custom parallel retry implementations exist outside these patterns

**Checkpoint**: Hook APIs return grouped objects. Retry logic standardized. All existing tests pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup across all phases

- [ ] T045 Run full backend verification: `cd backend && uv run --extra dev pytest tests/unit/ -x && uv run --extra dev ruff check src/ && uv run --extra dev pyright src/`
- [ ] T046 Run full frontend verification: `cd frontend && npm run test && npm run type-check && npm run lint`
- [ ] T047 Run integration tests: `cd backend && uv run --extra dev pytest tests/integration/ -x`
- [ ] T048 [P] Verify cyclomatic complexity targets: re-measure all 5 target functions/hooks — confirm `post_agent_outputs_from_pr` ≤15, `assign_agent_for_status` ≤20, `recover_stalled_issues` ≤20, `usePipelineConfig` ≤25, `useAgentConfig` ≤25
- [ ] T049 [P] Verify security hardening: confirm CORS allow-list (no wildcards), CSP header on responses, admin designation via env var, session-scoped queries
- [ ] T050 Run quickstart.md validation: follow steps in `specs/035-best-practices-overhaul/quickstart.md` to verify each phase independently

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Data Integrity / US1 (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **Complexity / US2 (Phase 3)**: Depends on Phase 2 completion
- **DRY & Errors / US3 (Phase 4)**: Depends on Phase 2 completion — can run in parallel with Phase 3
- **DI Modernization / US4 (Phase 5)**: Depends on Phase 2 completion — can run in parallel with Phases 3–4
- **Security / US5 (Phase 6)**: Depends on Phase 2 completion — can run in parallel with Phases 3–5
- **Observability / US6 (Phase 7)**: Independent — can start any time (benefits from Phases 4–5 completion)
- **Dev Experience / US7 (Phase 8)**: Independent — can start any time (builds on Phase 3 frontend work)
- **Polish (Phase 9)**: Depends on all desired phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Setup (Phase 1) — **Critical foundation, blocks all other stories**
- **US2 (P1)**: Can start after US1 (Phase 2) — No dependencies on other stories
- **US3 (P1)**: Can start after US1 (Phase 2) — No dependencies on other stories; can run in parallel with US2
- **US4 (P2)**: Can start after US1 (Phase 2) — Independent of US2/US3; enables better testing in US6
- **US5 (P2)**: Can start after US1 (Phase 2) — Independent of US2–US4
- **US6 (P2)**: Can start at any time — Benefits from US3 (error handling) and US4 (DI for test isolation)
- **US7 (P3)**: Can start at any time — Builds on US2 frontend hooks but can be done independently

### Within Each User Story

- Models/stores before services
- Services before endpoints
- Core implementation before integration
- Infrastructure before consumers
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (different files)
- **Phase 2 (US1)**: T003 and T004 can run in parallel (new independent files); T005 and T008 can run in parallel (different files: transitions.py vs websocket.py)
- **Phase 3 (US2)**: T010, T011, T012 are sequential within backend but T013/T014 (frontend) can run in parallel with backend tasks
- **Phase 4 (US3)**: T018 and T023 can run in parallel (exceptions.py vs models/api_inputs.py — different files, no dependencies)
- **Phase 5 (US4)**: T026 can run in parallel with Phase 2 wrap-up (new file, no dependencies)
- **Phase 6 (US5)**: T033 can run in parallel with T032 (new file vs existing file)
- **Phase 7 (US6)**: T038, T039, T041 can run in parallel (frontend vs backend integration tests vs .gitignore — different files)
- **Cross-phase**: After Phase 2, Phases 3–6 can run in parallel if staffed by different developers

---

## Parallel Example: User Story 1 (Phase 2)

```bash
# Launch both new store files together (no dependencies between them):
Task T003: "Create pipeline_state_store.py in backend/src/services/"
Task T004: "Create chat_store.py in backend/src/services/"

# After stores are created, launch locking tasks in parallel:
Task T005: "Add asyncio.Lock to transitions.py"
Task T008: "Add asyncio.Lock to websocket.py"

# Then sequential integration:
Task T006: "Integrate pipeline_state_store into transitions.py" (depends on T003, T005)
Task T007: "Wire chat_store.py into chat.py" (depends on T004)
Task T009: "Initialize stores in main.py lifespan" (depends on T003, T004)
```

## Parallel Example: After Phase 2 Completion

```bash
# Launch all independent phases in parallel with different developers:
Developer A: Phase 3 (US2 — Complexity Reduction)
Developer B: Phase 4 (US3 — DRY & Error Handling)
Developer C: Phase 5 (US4 — DI Modernization)
Developer D: Phase 6 (US5 — Security Hardening)

# Independent phases can start immediately:
Developer E: Phase 7 (US6 — Observability)
Developer F: Phase 8 (US7 — Dev Experience)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: User Story 1 — Data Integrity (T003–T009)
3. **STOP and VALIDATE**: Test pipeline state survives container restart
4. Deploy/demo if ready — this alone eliminates the most critical production risk

### Incremental Delivery

1. Complete Setup + US1 (Data Integrity) → Foundation ready — **MVP!**
2. Add US2 (Complexity) → All high-CC functions decomposed → Deploy/Demo
3. Add US3 (DRY/Errors) → Consistent error handling, type-safe inputs → Deploy/Demo
4. Add US4 (DI) → Test-friendly architecture → Deploy/Demo
5. Add US5 (Security) → Hardened HTTP posture → Deploy/Demo
6. Add US6 (Observability) → Full error visibility + integration tests → Deploy/Demo
7. Add US7 (Dev Experience) → Clean hook APIs → Deploy/Demo
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + US1 (Data Integrity) together — this is the critical path
2. Once US1 is done:
   - Developer A: US2 (Complexity — backend)
   - Developer B: US3 (DRY/Errors)
   - Developer C: US4 (DI Modernization)
   - Developer D: US5 (Security)
   - Developer E: US6 (Observability) — can start immediately
   - Developer F: US7 (Dev Experience) — can start immediately
3. Stories complete and integrate independently
4. Phase 9 (Polish) once all target stories are done

---

## Notes

- [P] tasks = different files, no dependencies on in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Phase 2 (Data Integrity / US1) is the critical path — all other user story work is blocked until it completes
- Phases 3–6 are NOT sequential — they can run in parallel after Phase 2 completes
- Research decisions (R-001 through R-013) provide implementation guidance for each task
- Contracts in `specs/035-best-practices-overhaul/contracts/` define exact interfaces for new modules
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
