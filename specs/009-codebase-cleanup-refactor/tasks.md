# Tasks: Codebase Cleanup & Refactor

**Input**: Design documents from `/specs/009-codebase-cleanup-refactor/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: No new tests required. Existing tests must pass after every task (FR-009).

**Organization**: Tasks are grouped by user story (6 stories: P1×2, P2×3, P3×1) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US6)
- All paths are relative to repository root

## Path Conventions

- **Backend**: `backend/src/` (Python 3.11+, FastAPI)
- **Frontend**: `frontend/src/` (TypeScript, React 18, TanStack Query v5)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture baselines and create shared scaffolding needed by multiple stories

- [x] T001 Capture pre-refactor LOC baseline (`find backend/src frontend/src -name '*.py' -o -name '*.ts' -o -name '*.tsx' | xargs wc -l`) and performance baseline per `specs/009-codebase-cleanup-refactor/quickstart.md` Performance Baseline section
- [x] T002 Create `backend/src/utils.py` with `utcnow()` helper function: `from datetime import datetime, UTC; def utcnow() -> datetime: return datetime.now(UTC)` — single chokepoint per research.md R3

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking foundational work required — this is a pure refactor on an existing codebase. Phase 1 setup provides the only shared prerequisite (`utils.py`).

**⚠️ CRITICAL**: Phase 1 must be complete before user story work begins (T002 creates `utils.py` needed by US3 and US5).

**Checkpoint**: Setup ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Eliminate Dead Code and Stale Artifacts (Priority: P1) 🎯 MVP

**Goal**: Remove all unused code, stale imports, and dead code paths so the codebase only contains actively-used code.

**Independent Test**: Application builds, all tests pass, workspace-wide search confirms zero references to removed symbols.

### Implementation for User Story 1

- [x] T003 [P] [US1] Remove unused `RateLimiter` class from `backend/src/main.py` (confirm zero references first via grep)
- [x] T004 [P] [US1] Remove unused `identify_target_status` function from `backend/src/services/ai_agent.py` (confirm zero callers first)
- [x] T005 [P] [US1] Delete unused frontend components `ErrorToast`, `ErrorBanner`, and `RateLimitIndicator` from `frontend/src/components/common/` and remove any stale imports referencing them
- [x] T006 [P] [US1] Remove unused exports `AVAILABLE_LABELS` and `NotificationEventType` from `frontend/src/types/index.ts`
- [x] T007 [P] [US1] Remove redundant default exports (keep named exports only) from `frontend/src/hooks/useWorkflow.ts` and `frontend/src/components/chat/IssueRecommendationPreview.tsx`
- [x] T008 [US1] Run full test suite (`cd backend && python -m pytest tests/ -v` and `cd frontend && npm run build && npm run test -- --run`), verify zero references to removed symbols via `grep -rn 'RateLimiter\|ErrorToast\|ErrorBanner\|RateLimitIndicator\|identify_target_status' backend/src/ frontend/src/`

**Checkpoint**: Dead code eliminated. All tests pass. Proceed to Story 2.

---

## Phase 4: User Story 2 — Decompose Oversized Backend Modules (Priority: P1)

**Goal**: Break 3 oversized files (10,541 lines total) into focused single-responsibility packages using Extract & Re-export pattern (research.md R1).

**Independent Test**: All existing tests pass, each new sub-module has one responsibility, no circular imports exist, all external import paths still resolve via `__init__.py` re-exports.

**Decomposition order**: workflow_orchestrator FIRST (its `models.py` is the leaf node that breaks the circular dependency with copilot_polling per research.md R2), then copilot_polling, then github_projects.

### Implementation: workflow_orchestrator decomposition

- [x] T009 [US2] Create `backend/src/services/workflow_orchestrator/` package directory and extract `models.py` with shared data classes (`WorkflowContext`, `PipelineState`, `WorkflowState`, `WorkflowConfig`) — this is the LEAF module that breaks the circular dependency with copilot_polling per research.md R2
- [x] T010 [P] [US2] Extract workflow config load/persist/defaults logic to `backend/src/services/workflow_orchestrator/config.py` (imports from `models.py`)
- [x] T011 [P] [US2] Extract status transition logic and review assignment to `backend/src/services/workflow_orchestrator/transitions.py` (imports from `models.py` and `config.py`)
- [x] T012 [US2] Extract main `WorkflowOrchestrator` class and `assign_agent_for_status()` to `backend/src/services/workflow_orchestrator/orchestrator.py` (imports from `models.py`, `config.py`, `transitions.py`)
- [x] T013 [US2] Create `backend/src/services/workflow_orchestrator/__init__.py` with `__all__` re-exporting all public names for backward compatibility, then delete original `backend/src/services/workflow_orchestrator.py`

### Implementation: copilot_polling decomposition

- [x] T014 [US2] Create `backend/src/services/copilot_polling/` package directory and extract `state.py` with all module-level mutable state (global dicts/sets: `_polling_state`, `_polling_task`, `_processed_issue_prs`, `_posted_agent_outputs`, `_claimed_child_prs`, `_pending_agent_assignments`, etc.)
- [x] T015 [P] [US2] Extract polling lifecycle (start/stop/tick, scheduling) to `backend/src/services/copilot_polling/polling_loop.py` (imports from `state.py`)
- [x] T016 [P] [US2] Extract agent output extraction and posting logic to `backend/src/services/copilot_polling/agent_output.py` (imports from `state.py`)
- [x] T017 [P] [US2] Extract pipeline advancement and transition logic to `backend/src/services/copilot_polling/pipeline.py` (imports from `state.py` and `workflow_orchestrator.models`)
- [x] T018 [P] [US2] Extract stalled issue recovery and cooldown management to `backend/src/services/copilot_polling/recovery.py` (imports from `state.py`)
- [x] T019 [P] [US2] Extract PR completion detection (main + child PRs) to `backend/src/services/copilot_polling/completion.py` (imports from `state.py`)
- [x] T020 [US2] Create `backend/src/services/copilot_polling/__init__.py` with `__all__` re-exporting all public names, then delete original `backend/src/services/copilot_polling.py`

### Implementation: github_projects decomposition

- [x] T021 [US2] Create `backend/src/services/github_projects/` package directory and extract `graphql.py` with all GraphQL query/mutation strings and fragments (`PROJECT_FIELDS_FRAGMENT`, `LIST_USER_PROJECTS_QUERY`, etc.)
- [x] T022 [US2] Extract main `GitHubProjectsService` class, singleton instance, and HTTP client management to `backend/src/services/github_projects/service.py`
- [x] T023 [P] [US2] Extract issue CRUD operations (create, update, get, search, sub-issues) to `backend/src/services/github_projects/issue_ops.py` (imports from `service.py`)
- [x] T024 [P] [US2] Extract PR detection, completion checking, and timeline events to `backend/src/services/github_projects/pr_ops.py` (imports from `service.py`)
- [x] T025 [P] [US2] Extract board data retrieval and transformation to `backend/src/services/github_projects/board_ops.py` (imports from `service.py`)
- [x] T026 [P] [US2] Extract Copilot agent assignment logic (GraphQL + REST paths) to `backend/src/services/github_projects/copilot_assignment.py` (imports from `service.py`)
- [x] T027 [US2] Create `backend/src/services/github_projects/__init__.py` with `__all__` re-exporting all public names, then delete original `backend/src/services/github_projects.py`

### Verification

- [x] T028 [US2] Verify no circular imports (`python -c "import importlib; [importlib.import_module(m) for m in ['src.services.copilot_polling','src.services.workflow_orchestrator','src.services.github_projects']]"`), run full backend test suite, confirm all existing import paths still resolve

**Checkpoint**: Three monolithic files decomposed into 19 focused sub-modules across 3 packages. No circular imports. All tests pass.

---

## Phase 5: User Story 3 — Consolidate Duplicated Backend Patterns (Priority: P2)

**Goal**: Extract repeated backend code patterns into shared utilities so bug fixes happen in one place.

**Independent Test**: Each duplicated pattern exists in exactly one location, all callers use the shared implementation, all tests pass.

### Implementation for User Story 3

- [x] T029 [P] [US3] Extract `resolve_repository(project, settings)` helper to `backend/src/utils.py`, update callers in `backend/src/api/chat.py`, `backend/src/api/tasks.py`, and `backend/src/api/workflow.py` to use it
- [x] T030 [P] [US3] Consolidate Copilot polling startup logic into a single `ensure_polling_started()` function in `backend/src/services/copilot_polling/__init__.py`, update duplicate startup code in `backend/src/api/chat.py`, `backend/src/api/projects.py`, and `backend/src/api/workflow.py`
- [x] T031 [P] [US3] Extract `_row_to_session(row)` private helper in `backend/src/services/session_store.py`, update `get_session()` and `get_sessions_by_user()` to use it
- [x] T032 [P] [US3] Extract `_upsert_row(db, table, ...)` private helper in `backend/src/services/settings_store.py`, update `upsert_user_preferences()` and `upsert_project_settings()` to use it
- [x] T033 [P] [US3] Extract `_transition_to_in_review()` shared helper in `backend/src/services/workflow_orchestrator/transitions.py`, update `handle_in_progress_status()` and `handle_completion()` to delegate to it
- [x] T034 [US3] Consolidate label definitions: unify `PREDEFINED_LABELS` from `backend/src/prompts/issue_generation.py` and `AVAILABLE_LABELS` from `backend/src/models/chat.py` into single canonical `LABELS` constant in `backend/src/constants.py`, update all consumers
- [x] T035 [US3] Run full backend test suite, verify each extracted utility has exactly one definition via grep

**Checkpoint**: All backend DRY violations resolved. Each utility exists in one place. All tests pass.

---

## Phase 6: User Story 4 — Consolidate Duplicated Frontend Patterns (Priority: P2)

**Goal**: Extract duplicated frontend code into shared hooks, utilities, and types for consistency and maintainability.

**Independent Test**: Duplicate definitions no longer exist, all affected components render correctly, frontend builds and all tests pass.

### Implementation for User Story 4

- [x] T036 [P] [US4] Move `StatusChangeProposal` type definition to `frontend/src/types/index.ts`, update imports in `frontend/src/hooks/useChat.ts` and `frontend/src/components/chat/ChatInterface.tsx`
- [x] T037 [P] [US4] Extract `generateId()` utility to `frontend/src/utils/generateId.ts`, update imports in `frontend/src/hooks/useAgentConfig.ts` and `frontend/src/components/settings/AgentPresetSelector.tsx`
- [x] T038 [P] [US4] Extract `formatTimeAgo(date)` utility to `frontend/src/utils/formatTime.ts`, replace `formatLastUpdated()` in `frontend/src/pages/ProjectBoardPage.tsx` and `formatLastUpdate()` in `frontend/src/components/sidebar/ProjectSidebar.tsx`
- [x] T039 [US4] Extract generic `useSettingsForm<T>(serverState)` hook to `frontend/src/hooks/useSettingsForm.ts`, refactor `AIPreferences`, `DisplayPreferences`, `WorkflowDefaults`, and `NotificationPreferences` components to use it
- [x] T040 [US4] Refactor `frontend/src/components/settings/GlobalSettings.tsx` to compose existing section components (`AIPreferences`, `DisplayPreferences`, etc.) instead of re-implementing all 17 fields
- [x] T041 [US4] Migrate `frontend/src/hooks/useWorkflow.ts` from raw `fetch()` to centralized API client (`services/api.ts`) + TanStack Query (`useQuery`/`useMutation`) per research.md R6 migration map
- [x] T042 [US4] Migrate `useAvailableAgents` in `frontend/src/hooks/useAgentConfig.ts` from raw `fetch()` to centralized API client + TanStack Query with `staleTime: Infinity` and `gcTime: 10 * 60 * 1000` per research.md R6
- [x] T043 [US4] Run frontend build (`npm run build`) and test suite (`npm run test -- --run`), verify no duplicate type/utility definitions remain

**Checkpoint**: All frontend DRY violations resolved. All data-fetching uses centralized pattern. Build and tests pass.

---

## Phase 7: User Story 5 — Modernize Deprecated Patterns and Enforce Best Practices (Priority: P2)

**Goal**: Replace deprecated API calls with modern equivalents and standardize inconsistent practices.

**Independent Test**: Search for deprecated patterns returns zero results, all tests pass on target runtime.

### Implementation for User Story 5

- [x] T044 [US5] Replace all 30+ `datetime.utcnow()` calls with `utcnow()` helper (from `backend/src/utils.py`) across entire backend — MUST be atomic (all files in one change) to avoid TypeError from mixing naive and aware datetimes per research.md R3
- [x] T045 [P] [US5] Replace `asyncio.get_event_loop().time()` with `asyncio.get_running_loop().time()` (or `time.monotonic()`) in `backend/src/api/projects.py`
- [x] T046 [P] [US5] Add `COOKIE_SECURE` and `COOKIE_MAX_AGE` settings to `backend/src/config.py`, update `backend/src/api/auth.py` to derive cookie `secure` and `max_age` from config instead of hardcoded values
- [x] T047 [US5] Migrate synchronous `sqlite3` database calls to async `aiosqlite` in `backend/src/services/workflow_orchestrator/config.py` to stop blocking the event loop
- [x] T048 [P] [US5] Fix `get_pr_timeline_events` in `backend/src/services/github_projects/pr_ops.py` to use the shared `httpx.AsyncClient` from `service.py` instead of creating a new client per call
- [x] T049 [US5] Add `idempotent` parameter to `_request_with_retry()` in `backend/src/services/github_projects/service.py`, route GraphQL queries and GET/PUT/PATCH calls through retry logic, make non-idempotent POST mutations fail fast per research.md R7
- [x] T050 [P] [US5] Extract frontend magic numbers (poll intervals, timeouts, expiry durations) to named constants in `frontend/src/constants.ts`, update `useChat.ts`, `useRealTimeSync.ts`, `useProjectBoard.ts`, and other hooks/components
- [x] T051 [US5] Run full test suite (backend + frontend), verify zero deprecated patterns via `grep -rn 'datetime\.utcnow()\|get_event_loop()\.time()' backend/src/`

**Checkpoint**: All deprecated APIs replaced. Best practices enforced uniformly. All tests pass.

---

## Phase 8: User Story 6 — Improve Structural Organization (Priority: P3)

**Goal**: Establish clear module boundaries, proper separation of concerns, and consistent patterns.

**Independent Test**: Application starts and behaves identically, all tests pass, code organization follows established conventions.

### Implementation for User Story 6

- [x] T052 [US6] Split `backend/src/models/chat.py` into focused files per data-model.md: trim `chat.py` to chat-only models, create `backend/src/models/workflow.py` (StatusChangeRecommendation, IssueRecommendation, WorkflowConfig models), `backend/src/models/agent.py` (AgentConfig, AgentMapping models), `backend/src/models/recommendation.py` (AITaskProposal, ProposalConfirmRequest, ProposalResponse)
- [x] T053 [US6] Update `backend/src/models/__init__.py` with re-exports for all moved models, update every import site across `backend/src/api/` and `backend/src/services/` to use the new module paths (or __init__ re-exports)
- [x] T054 [US6] Create `backend/src/dependencies.py` with DI getter functions using `request.app.state` pattern per research.md R4 (`get_github_service()`, `get_connection_manager()`, `get_database()`)
- [x] T055 [US6] Update `backend/src/main.py` lifespan handler to register singleton services on `app.state` (`github_service`, `connection_manager`) per research.md R4, keep module-level globals as thin wrappers during transition
- [x] T056 [P] [US6] Consolidate `get_current_session` and `get_session_dep` into a single session dependency function in `backend/src/api/auth.py`, update all endpoint handlers that use either function
- [x] T057 [P] [US6] Create `ErrorBoundary` class component (~40 lines) in `frontend/src/components/common/ErrorBoundary.tsx` with `componentDidCatch`, `getDerivedStateFromError`, reset callback, and fallback UI per research.md R5
- [x] T058 [US6] Integrate `ErrorBoundary` with `QueryErrorResetBoundary` in `frontend/src/App.tsx` per research.md R5 pattern, refactor `AppContent` to distribute hook concerns to view-specific wrappers so hooks only execute when their view is active
- [x] T059 [P] [US6] Normalize all frontend import paths to use `@/` path alias consistently across all files in `frontend/src/` (replace relative `../../` imports)
- [x] T060 [US6] Run full test suite (backend + frontend) and Docker build (`docker compose build`) to verify no regressions

**Checkpoint**: All structural improvements complete. Module boundaries clear. DI in place. Error boundary active. All tests and Docker build pass.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories

- [x] T061 [P] Measure post-refactor LOC and compare against T001 baseline — verify ≥10% reduction (SC-008)
- [x] T062 [P] Run performance comparison against T001 baseline — verify no measurable regression in startup time or API p95 latency (SC-011)
- [x] T063 Run full `specs/009-codebase-cleanup-refactor/quickstart.md` verification checklist end-to-end (all story-by-story checks)
- [x] T064 Final cleanup: remove any TODO/FIXME comments added during refactoring, ensure no empty directories remain, update `README.md` if module paths are referenced

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: N/A — Phase 1 setup is the only prerequisite
- **US1 (Phase 3, P1)**: Depends on Phase 1 only — can start immediately after setup
- **US2 (Phase 4, P1)**: Depends on Phase 1 only — can start immediately after setup
- **US3 (Phase 5, P2)**: Depends on **US2** completion (shared utilities go into decomposed module paths)
- **US4 (Phase 6, P2)**: **Independent of backend stories** — can start after Phase 1
- **US5 (Phase 7, P2)**: Depends on **US2** completion (deprecated patterns in decomposed files)
- **US6 (Phase 8, P3)**: Depends on **US1–US5** completion (structural changes assume clean codebase)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1: Setup
    │
    ├──→ US1 (P1): Dead Code Removal ──────────────────────────┐
    │                                                           │
    ├──→ US2 (P1): Module Decomposition ──┬──→ US3 (P2): Backend DRY ──┐
    │                                     │                             │
    │                                     └──→ US5 (P2): Deprecation ──┤
    │                                                                   │
    └──→ US4 (P2): Frontend DRY (independent) ─────────────────────────┤
                                                                        │
                                                                        └──→ US6 (P3): Structural Org
                                                                                │
                                                                                └──→ Polish
```

### Within Each User Story

1. Sequential tasks execute in listed order
2. Tasks marked [P] can run in parallel with other [P] tasks in the same group
3. Verification task (last in each story) runs after all other story tasks complete
4. Story complete = all tests pass, checkpoint criteria met

### Parallel Opportunities

- **US1 and US2** can run in parallel (US1 = dead code removal, US2 = decomposition — different concerns)
- **US4** (frontend DRY) can run in parallel with **US2**, **US3**, or **US5** (frontend vs backend)
- **US3 and US5** can run in parallel (after US2 completes — different backend concerns)
- Within US2: workflow_orchestrator sub-modules T010+T011 are parallel; copilot_polling sub-modules T015–T019 are parallel; github_projects sub-modules T023–T026 are parallel
- Within US3: T029–T033 are all parallel (different files)
- Within US4: T036–T038 are all parallel (different files)
- Within US5: T045, T046, T048, T050 are parallel (different files)

---

## Parallel Example: User Story 2 (Module Decomposition)

```text
# Sequential: workflow_orchestrator (must be first — breaks circular dep)
T009: Create dir + extract models.py (LEAF)
  → T010 + T011 can run in parallel (config.py and transitions.py)
  → T012: Extract orchestrator.py
  → T013: Create __init__.py, delete original

# After T009 (models.py exists), copilot_polling can start in parallel with remaining workflow_orchestrator tasks:
T014: Create dir + extract state.py (LEAF)
  → T015 + T016 + T017 + T018 + T019 all parallel (5 sub-modules, all import from state.py)
  → T020: Create __init__.py, delete original

# github_projects is independent (no circular dep involvement) — can start anytime:
T021: Create dir + extract graphql.py
  → T022: Extract service.py
  → T023 + T024 + T025 + T026 all parallel (4 ops modules, all import from service.py)
  → T027: Create __init__.py, delete original

# Final verification after all three packages:
T028: Verify no circular imports + run tests
```

---

## Parallel Example: User Story 3 + 4 + 5 (after US2 completes)

```text
# All three stories can run concurrently since US3/US5 are backend and US4 is frontend:

# Backend stream 1 (US3):
T029 + T030 + T031 + T032 + T033 all parallel → T034 → T035

# Frontend stream (US4):
T036 + T037 + T038 parallel → T039 → T040 → T041 → T042 → T043

# Backend stream 2 (US5):
T044 (atomic datetime migration) → T045 + T046 + T048 + T050 parallel → T047 → T049 → T051
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 3: User Story 1 — Dead Code Removal (T003–T008)
3. **STOP and VALIDATE**: All tests pass, zero references to removed symbols
4. This alone delivers measurable LOC reduction and cleaner codebase

### Incremental Delivery

1. **Setup** → Foundation ready
2. **US1** (P1) → Dead code eliminated → Validate independently
3. **US2** (P1) → Monoliths decomposed → Validate independently
4. **US3 + US4 + US5** (P2, can parallel) → DRY consolidated, deprecated patterns fixed → Validate each independently
5. **US6** (P3) → Structural improvements, DI, error boundary → Validate independently
6. **Polish** → Final metrics and verification

### Single-Agent Sequential Strategy

Execute stories in priority order: Setup → US1 → US2 → US3 → US5 → US4 → US6 → Polish

(US4 placed after US5 for developer focus — complete all backend work before switching to frontend context)

---

## Notes

- **[P]** tasks = different files, no incomplete dependencies within their group
- **[US#]** label maps task to specific user story for traceability
- **No new tests** required — existing test suite is the regression gate (FR-009)
- **Atomic delivery**: Each user story lands as one commit/PR with all tests passing (per clarification)
- **Extract & Re-export**: All module decompositions use `__init__.py` re-exports for backward compatibility (research.md R1)
- **Circular dep resolution**: workflow_orchestrator `models.py` must exist before copilot_polling `pipeline.py` (research.md R2)
- **Datetime migration**: Must be atomic across all 30+ files — no partial migration (research.md R3)
- Commit after each task or logical group; stop at any checkpoint to validate
