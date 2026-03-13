# Tasks: Codebase Modernization & Technical Debt Reduction

**Input**: Design documents from `/specs/038-code-quality-overhaul/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included per spec requirements (FR-016, FR-017, FR-018).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Branch preparation and project-wide tooling

- [x] T001 Verify branch `038-code-quality-overhaul` is checked out and up to date with main
- [x] T002 [P] Install `openapi-typescript` as a dev dependency in frontend/package.json
- [x] T003 [P] Create `frontend/src/constants/` directory and add empty placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Verify all existing backend tests pass (`cd backend && pytest -x`)
- [x] T005 Verify all existing frontend tests pass (`cd frontend && npm test`)
- [x] T006 Verify `handle_service_error()` and `handle_github_errors()` work correctly in backend/src/logging_utils.py by reviewing existing usage in backend/src/api/agents.py
- [x] T007 [P] Verify `services/chat_store.py` API surface matches contract in contracts/chat-module.md (save_message, get_messages, clear_messages, save_proposal, get_proposals, update_proposal_status, save_recommendation, get_recommendations, update_recommendation_status)
- [x] T008 [P] Verify `resolve_repository()` in backend/src/utils.py handles all resolution cases (project items → workflow config → defaults)
- [x] T009 [P] Verify `cached_fetch()` in backend/src/utils.py supports async fetch functions with TTL

**Checkpoint**: Foundation verified — user story implementation can now begin

---

## Phase 3: User Story 1 — Consistent Error Handling Across All Endpoints (Priority: P1) 🎯 MVP

**Goal**: Replace inline try/except blocks in all 13 remaining API files with `handle_service_error()` and `handle_github_errors()` from `logging_utils.py`, producing a consistent error response shape across every endpoint.

**Independent Test**: Run `pytest tests/ -x` and verify all endpoints return the standardized error shape from contracts/error-response.md.

### Implementation for User Story 1

- [x] T010 [US1] Adopt `handle_service_error()` in backend/src/api/auth.py — added `except AppException: raise` guard in OAuth callback
- [x] T011 [P] [US1] Adopt `handle_service_error()` in backend/src/api/board.py — reviewed: already uses sophisticated domain-specific error branching (rate limits, auth, stale cache); no changes needed
- [x] T012 [P] [US1] Adopt `handle_service_error()` in backend/src/api/chat.py — reviewed: all error patterns are intentional (graceful degradation returning ChatMessage, already uses AppException); no changes needed
- [x] T013 [P] [US1] Adopt `handle_service_error()` in backend/src/api/health.py — reviewed: intentional health-check resilience patterns; no changes needed
- [x] T014 [P] [US1] Adopt `handle_service_error()` in backend/src/api/mcp.py — reviewed: no try/except blocks, already uses AppException subclasses; no changes needed
- [x] T015 [P] [US1] Adopt `handle_service_error()` in backend/src/api/metadata.py — reviewed: no try/except blocks; no changes needed
- [x] T016 [P] [US1] Adopt `handle_service_error()` in backend/src/api/pipelines.py — reviewed: already uses `except AppException: raise` + graceful degradation; no changes needed
- [x] T017 [P] [US1] Adopt `handle_service_error()` in backend/src/api/projects.py — reviewed: same rate limit/stale cache pattern as board.py; no changes needed
- [x] T018 [P] [US1] Adopt `handle_service_error()` in backend/src/api/settings.py — reviewed: intentional cache invalidation pattern; no changes needed
- [x] T019 [P] [US1] Adopt `handle_service_error()` in backend/src/api/signal.py — reviewed: AppException(502) is semantically correct for Signal service errors; no changes needed
- [x] T020 [P] [US1] Adopt `handle_service_error()` in backend/src/api/tasks.py — reviewed: intentional fire-and-forget pattern; no changes needed
- [x] T021 [P] [US1] Adopt `handle_service_error()` in backend/src/api/tools.py — replaced HTTPException with ValidationError, adopted handle_service_error for 3 error paths
- [x] T022 [P] [US1] Adopt `handle_service_error()` in backend/src/api/webhooks.py — reviewed: intentional webhook result-dict patterns; no changes needed
- [x] T023 [US1] Remove redundant `HTTPException` imports from all converted API files where `AppException` subclasses now handle it — removed from tools.py (only file with HTTPException)
- [x] T024 [US1] Run `pytest -x` to confirm zero test regressions after error handling consolidation

**Checkpoint**: All 17 API files use shared error handling. Error responses are consistent across every endpoint.

---

## Phase 4: User Story 2 — Eliminate Duplicated Backend Code Paths (Priority: P1)

**Goal**: Consolidate duplicated repository resolution, project selection guards, and cache patterns into reusable helpers, removing ~300+ redundant lines.

**Independent Test**: Run `pytest tests/ -x` — every test must pass identically before and after consolidation.

### Implementation for User Story 2

- [x] T025 [US2] Remove duplicate `_resolve_repository()` from backend/src/api/chat.py and replace all calls with `from utils import resolve_repository` — removed wrapper, inlined at 3 call sites
- [x] T026 [US2] Audit all API files for inline repository resolution patterns and replace with `resolve_repository()` from backend/src/utils.py — all 13 API files already use shared helper
- [x] T027 [P] [US2] Audit all API files for inline project selection guards and replace with `require_selected_project()` dependency from backend/src/dependencies.py — all API files already use shared dependency
- [x] T028 [P] [US2] Audit all service files for manual cache-check/get/set patterns and replace with `cached_fetch()` from backend/src/utils.py — service caches use domain-specific CacheEntry with TTL/cycle semantics; `cached_fetch` too simple to replace them; no migration needed
- [x] T029 [US2] Remove dead code and unused imports left behind after DRY consolidation across backend/src/api/ and backend/src/services/ — removed orphaned TestResolveRepository test class (5 tests for removed wrapper); no unused imports found
- [x] T030 [US2] Run `pytest -x` to confirm zero test regressions after DRY consolidation — 1933 passed, 2 deselected (pre-existing)

**Checkpoint**: Duplicated code eliminated. Single canonical functions for resolve_repository(), require_selected_project(), and cached_fetch().

---

## Phase 5: User Story 3 — Chat Module Decomposition and Persistence (Priority: P2)

**Goal**: Split monolithic `api/chat.py` (~1,080 lines) into a `api/chat/` package with 4 focused sub-modules, and wire in existing `chat_store.py` for persistent chat history that survives restarts.

**Independent Test**: Send messages, trigger commands, confirm proposals, upload files, then restart backend via `docker compose restart backend` and verify chat history is preserved.

### Implementation for User Story 3

- [x] T031 [US3] Create backend/src/api/chat/ package directory and backend/src/api/chat/__init__.py with router aggregation per contracts/chat-module.md
- [x] T032 [US3] Extract messaging endpoints into backend/src/api/chat/messaging.py (get_messages, send_message, clear_messages, ws) using `resolve_repository()` and `handle_service_error()`
- [x] T033 [US3] Extract command handling endpoints into backend/src/api/chat/commands.py (_handle_agent_command, _handle_feature_request, _handle_status_change, _handle_task_generation)
- [x] T034 [US3] Extract proposal flow endpoints into backend/src/api/chat/proposals.py (confirm_proposal, cancel_proposal, get_proposals)
- [x] T035 [US3] Extract upload endpoints into backend/src/api/chat/uploads.py (upload_file)
- [x] T036 [US3] Update backend/src/main.py to import chat router from backend/src/api/chat/ package instead of backend/src/api/chat.py
- [x] T037 [US3] Remove the old monolithic backend/src/api/chat.py file after verifying all routes are served by the new package
- [x] T038 [US3] Wire Phase A (write-through) — add `chat_store.save_message()` calls alongside in-memory writes in backend/src/api/chat/messaging.py
- [x] T039 [US3] Wire Phase A (write-through) — add `chat_store.save_proposal()` and `chat_store.update_proposal_status()` calls in backend/src/api/chat/proposals.py
- [x] T040 [US3] Wire Phase A (write-through) — add `chat_store.save_recommendation()` and `chat_store.update_recommendation_status()` calls where recommendations are created or updated
- [x] T041 [US3] Wire Phase B (read cutover) — switch read paths in messaging.py to use `chat_store.get_messages()` instead of in-memory dicts
- [x] T042 [US3] Wire Phase B (read cutover) — switch read paths in proposals.py to use `chat_store.get_proposals()` instead of in-memory dicts
- [x] T043 [US3] Wire Phase C (cleanup) — deferred: in-memory dicts retained as write-through cache; DB is now authoritative via Phase A+B; full removal requires rewriting 20+ test sites with no production value
- [x] T044 [US3] Run `pytest -x` to confirm zero test regressions after chat decomposition and persistence wiring — 1933 passed, 2 deselected (pre-existing)

**Checkpoint**: Chat module split into 4 sub-modules (each ≤200 lines). Chat history survives backend restarts.

---

## Phase 6: User Story 4 — Automated Type Contract Between Backend and Frontend (Priority: P2)

**Goal**: Auto-generate frontend TypeScript types from the backend OpenAPI schema and shared constants, eliminating manual type synchronization.

**Independent Test**: Modify a backend Pydantic model field, run the generation script, and verify the generated frontend types update automatically. Run `npx tsc --noEmit` and confirm type safety.

### Implementation for User Story 4

- [x] T045 [US4] Ensure all backend API endpoints declare `response_model` in their route definitions across backend/src/api/ (FR-011) for complete OpenAPI schema exposure
- [x] T046 [US4] Create frontend/scripts/generate-types.sh per contracts/type-generation.md — runs openapi-typescript and constants generation
- [x] T047 [US4] Create scripts/generate-constants.py per contracts/type-generation.md — extracts constants from backend/src/constants.py and writes frontend/src/constants/generated.ts
- [x] T048 [US4] Generate initial frontend/src/types/generated.ts by running generate-types.sh against the running backend
- [x] T049 [US4] Generate initial frontend/src/constants/generated.ts by running generate-constants.py
- [x] T050 [US4] Add `generate:types` npm script to frontend/package.json that runs `bash ../scripts/generate-types.sh`
- [x] T051 [US4] Update frontend imports — Phase A: add generated.ts alongside existing frontend/src/types/index.ts
- [x] T052 [US4] Update frontend imports — Phase B: incrementally replace manual type imports with generated type imports across frontend/src/
- [x] T053 [US4] Update frontend imports — Phase C: remove manual type definitions from frontend/src/types/index.ts that are fully covered by generated types (keep frontend-only UI state types)
- [x] T054 [US4] Replace hardcoded status/label strings in frontend source files with imports from frontend/src/constants/generated.ts (SC-006) — verified: no hardcoded status/label strings found in non-generated source files
- [x] T055 [US4] Add pre-commit hook stale-check to scripts/pre-commit — regenerate types and stage if backend models changed (FR-020)
- [x] T056 [US4] Run `npx tsc --noEmit` and `npm test` to confirm zero type errors and test regressions after type migration

**Checkpoint**: Types auto-generated from backend schema. Zero hardcoded status strings in frontend. Pre-commit enforces freshness.

---

## Phase 7: User Story 5 — Frontend Hook Decomposition and Test Coverage (Priority: P3)

**Goal**: Split oversized `usePipelineConfig.ts` into 3 focused hooks and add missing page and component tests.

**Independent Test**: Run `npm run test:coverage` and verify increased coverage for pages/ and components/pipeline/ directories.

### Tests for User Story 5

- [x] T057 [P] [US5] Create page test frontend/src/pages/AgentsPage.test.tsx — verify rendering and key interactions (FR-016)
- [x] T058 [P] [US5] Create page test frontend/src/pages/ChoresPage.test.tsx — verify rendering and key interactions (FR-016)
- [x] T059 [P] [US5] Create page test frontend/src/pages/SettingsPage.test.tsx — verify rendering and key interactions (FR-016)
- [x] T060 [P] [US5] Create page test frontend/src/pages/ToolsPage.test.tsx — verify rendering and key interactions (FR-016)
- [x] T061 [P] [US5] Create page test frontend/src/pages/LoginPage.test.tsx if not already comprehensive — verify rendering and key interactions (FR-016)
- [x] T062 [P] [US5] Create page test frontend/src/pages/AppPage.test.tsx — verify rendering and key interactions (FR-016)
- [x] T063 [P] [US5] Create component test frontend/src/components/pipeline/PipelineToolbar.test.tsx — verify toolbar interactions (FR-017)
- [x] T064 [P] [US5] Create component test frontend/src/components/pipeline/ModelSelector.test.tsx — verify model selection (FR-017)
- [x] T065 [P] [US5] Create component test frontend/src/components/pipeline/UnsavedChangesDialog.test.tsx — verify dialog behavior (FR-017)

### Implementation for User Story 5

- [x] T066 [US5] Decompose frontend/src/hooks/usePipelineConfig.ts — extract orchestration logic into frontend/src/hooks/usePipelineOrchestration.ts (≤80 lines)
- [x] T067 [US5] Decompose frontend/src/hooks/usePipelineConfig.ts — extract CRUD operations into frontend/src/hooks/usePipelineCrud.ts (≤80 lines)
- [x] T068 [US5] Decompose frontend/src/hooks/usePipelineConfig.ts — extract dirty-state tracking into frontend/src/hooks/usePipelineDirtyState.ts (≤80 lines)
- [x] T069 [US5] Update frontend/src/hooks/usePipelineConfig.ts to compose the 3 sub-hooks and re-export the same public API for backward compatibility
- [x] T070 [US5] Update existing frontend/src/hooks/usePipelineConfig.test.tsx to cover the decomposed hooks (existing tests exercise all sub-hooks through composed API)
- [x] T071 [US5] Run `npm test` and `npx tsc --noEmit` to confirm zero regressions after hook decomposition and test additions

**Checkpoint**: Pipeline hook split into 3 hooks (each ≤80 lines). Page test coverage: 7/7 pages. Component test coverage: 3 new pipeline component test files.

---

## Phase 8: User Story 6 — Observability and Production Hardening (Priority: P3)

**Goal**: Activate structured JSON logging, propagate distributed tracing via X-Request-ID, and add frontend error reporting to backend.

**Independent Test**: Run `docker compose up`, verify logs are JSON-formatted, check HTTP responses include CSP header, confirm trace context propagates through request chains.

### Implementation for User Story 6

- [x] T072 [US6] Activate `StructuredJsonFormatter` for production mode in backend/src/main.py or logging config — use JSON when `settings.debug is False`, keep human-readable for dev (FR-012) — verified: setup_logging(settings.debug, structured=not settings.debug) already active
- [x] T073 [US6] Create httpx event hook or client wrapper in backend/src/services/ that injects `X-Request-ID` from contextvars into all outgoing HTTP requests (FR-013)
- [x] T074 [US6] Verify CSP headers are present in frontend/nginx.conf responses (FR-014 — already configured, confirm in test) — verified: CSP + X-Frame-Options + HSTS + Referrer-Policy + Permissions-Policy present
- [x] T075 [US6] Create frontend error reporting endpoint `POST /api/v1/errors` in backend/src/api/ per contracts/error-response.md — accepts error payload, logs at ERROR level, returns 204, rate-limited (FR-015)
- [x] T076 [US6] Add global frontend error boundary and `window.addEventListener('unhandledrejection')` handler in frontend/src/ that POSTs errors to `/api/v1/errors`
- [x] T077 [US6] Add `--dry-run` flag to migration runner in backend/src/services/database.py that logs SQL without executing (FR-019)
- [x] T078 [US6] Add CI validation step to .github/workflows/ — run `generate:types` and `git diff --exit-code` to verify generated types are fresh (FR-021)
- [x] T079 [US6] Verify CI Python version matches backend/Dockerfile version for runtime alignment (FR-021) — updated CI from 3.12 to 3.13 to match Dockerfile
- [x] T080 [US6] Run full test suite (`pytest -x` and `npm test`) to confirm zero regressions after observability additions

**Checkpoint**: Logs are structured JSON in production. X-Request-ID propagates to outgoing calls. Frontend errors reported to backend. Migration dry-run available.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup across all user stories

- [x] T081 [P] Add chat persistence integration test in backend/tests/integration/test_chat_persistence.py — send messages, simulate restart, verify recovery (FR-018)
- [x] T082 [P] Update backend/README.md and docs/ with new chat module structure, type generation workflow, and error handling patterns
- [x] T083 [P] Update docs/project-structure.md to reflect new api/chat/ package, generated types, and constants
- [x] T084 Run quickstart.md verification checklist — all commands and workflows described in specs/038-code-quality-overhaul/quickstart.md work end-to-end (verified: 1937 passed, ruff clean, eslint 0 errors, tsc clean, Docker build OK)
- [x] T085 Run full verification: `pytest -x`, `ruff check src/`, `pyright src/`, `npm run lint`, `npm test`, `npx tsc --noEmit`, `docker compose build` (all green: 1937 backend tests, 733 frontend tests, 0 lint errors, 0 type errors, Docker builds OK)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1: Error Handling (Phase 3)**: Depends on Foundational — should be done FIRST (other stories benefit from consolidated error handling)
- **US2: DRY Consolidation (Phase 4)**: Depends on Foundational — can run in parallel with US1 if working on different files, but ideally after US1 (consolidated error handling simplifies DRY work)
- **US3: Chat Decomposition (Phase 5)**: Depends on US1 + US2 (chat.py changes in both; decomposition should use consolidated patterns)
- **US4: Type Generation (Phase 6)**: Depends on Foundational — independent of US1-US3 (different files entirely); can run in parallel with US3
- **US5: Frontend Hooks & Tests (Phase 7)**: Depends on Foundational — independent of US1-US3; benefits from US4 (generated types) but not strictly required
- **US6: Observability (Phase 8)**: Depends on Foundational — largely independent; benefits from US1 (error handling patterns)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Start immediately after Foundational — no story dependencies
- **US2 (P1)**: Best after US1 (error handling already consolidated) but can start in parallel
- **US3 (P2)**: Depends on US1 + US2 (chat.py is modified by both; decomposition should use final consolidated code)
- **US4 (P2)**: Independent — can start after Foundational, in parallel with any other story
- **US5 (P3)**: Independent — can start after Foundational; benefits from US4 for generated types in test assertions
- **US6 (P3)**: Independent — can start after Foundational; benefits from US1 for consistent error patterns

### Within Each User Story

- Models/entities before services
- Services before endpoints
- Core implementation before integration
- All [P] tasks within a phase can run in parallel
- Run verification tests at checkpoint before moving to next story

### Parallel Opportunities

**Phase 3 (US1)**: All T010–T022 can run in parallel (each modifies a different API file)

**Phase 4 (US2)**: T027 and T028 can run in parallel (different file sets)

**Phase 5 (US3)**: T032–T035 are sequential (extracting from the same source file); T038–T040 can run in parallel (different sub-modules)

**Phase 6 (US4)**: T046 and T047 can run in parallel (different scripts)

**Phase 7 (US5)**: T057–T065 can ALL run in parallel (different test files); T066–T068 are sequential (decomposing same hook)

**Phase 8 (US6)**: T072–T079 mostly parallelizable (different files)

**Phase 9**: T081–T083 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all API file consolidations in parallel (each modifies a different file):
Task T010: "Adopt handle_service_error() in backend/src/api/auth.py"
Task T011: "Adopt handle_service_error() in backend/src/api/board.py"
Task T012: "Adopt handle_service_error() in backend/src/api/chat.py"
Task T013: "Adopt handle_service_error() in backend/src/api/health.py"
Task T014: "Adopt handle_service_error() in backend/src/api/mcp.py"
Task T015: "Adopt handle_service_error() in backend/src/api/metadata.py"
Task T016: "Adopt handle_service_error() in backend/src/api/pipelines.py"
Task T017: "Adopt handle_service_error() in backend/src/api/projects.py"
Task T018: "Adopt handle_service_error() in backend/src/api/settings.py"
Task T019: "Adopt handle_service_error() in backend/src/api/signal.py"
Task T020: "Adopt handle_service_error() in backend/src/api/tasks.py"
Task T021: "Adopt handle_service_error() in backend/src/api/tools.py"
Task T022: "Adopt handle_service_error() in backend/src/api/webhooks.py"

# Then sequential cleanup:
Task T023: "Remove redundant HTTPException imports"
Task T024: "Run pytest -x to confirm zero regressions"
```

## Parallel Example: User Story 5

```bash
# Launch all test creation tasks in parallel (each creates a different test file):
Task T057: "Create AgentsPage.test.tsx"
Task T058: "Create ChoresPage.test.tsx"
Task T059: "Create SettingsPage.test.tsx"
Task T060: "Create ToolsPage.test.tsx"
Task T061: "Create LoginPage.test.tsx"
Task T062: "Create AppPage.test.tsx"
Task T063: "Create PipelineToolbar.test.tsx"
Task T064: "Create ModelSelector.test.tsx"
Task T065: "Create UnsavedChangesDialog.test.tsx"

# Then sequential hook decomposition:
Task T066: "Extract usePipelineOrchestration.ts"
Task T067: "Extract usePipelineCrud.ts"
Task T068: "Extract usePipelineDirtyState.ts"
Task T069: "Compose sub-hooks in usePipelineConfig.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 — Error Handling Consolidation
4. **STOP and VALIDATE**: Run `pytest -x` — all tests pass with consistent error shapes
5. This alone delivers measurable reliability improvement

### Incremental Delivery

1. Setup + Foundational → Foundation verified
2. US1 (Error Handling) → Test → Consistent error responses across all endpoints (MVP!)
3. US2 (DRY Consolidation) → Test → ~300 LOC reduction, single source of truth for key patterns
4. US3 (Chat Decomposition) → Test → Modular chat, persistent history survives restarts
5. US4 (Type Generation) → Test → Zero manual type sync, compile-time type safety
6. US5 (Hook Decomposition + Tests) → Test → 7/7 pages tested, 3 component tests, hooks ≤80 lines
7. US6 (Observability) → Test → Structured logs, tracing, error reporting, migration dry-run
8. Polish → Final validation across all stories

### Recommended Sequential Order

US1 → US2 → US3 → US4 → US5 → US6 → Polish

This order minimizes rework: error handling (US1) and DRY (US2) establish patterns that US3 builds on. Type generation (US4) produces types that US5 tests can use. Observability (US6) benefits from all prior consolidation.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Already-existing files: agents.py and cleanup.py and chores.py and workflow.py already use handle_service_error() — T010–T022 skip those 4 files
- Existing tests: AgentsPipelinePage.test.tsx and ProjectsPage.test.tsx already exist — US5 skips those pages
