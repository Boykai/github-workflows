# Tasks: Code Quality & Technical Debt Overhaul

**Input**: Design documents from `specs/033-code-quality-overhaul/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests ARE required — spec FR-026 mandates dedicated unit tests for all refactored high-complexity functions, SC-006 mandates ≥70% coverage.

**Organization**: Tasks grouped by user story (from spec.md priorities). Each phase is a self-contained commit per FR-030.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story: [US1]–[US6]
- Setup/Foundational/Polish phases: No story label

---

## Phase 1: Setup (Dead Code & Build Artifact Cleanup)

**Purpose**: Remove dead code, false positives, and stale artifacts so static analysis gives clean baselines before any refactoring begins. Maps to spec Phase 1 (FR-001, FR-002, FR-003).

- [X] T001 Identify and remove stale/broken tests related to dead code and unused utility functions in backend/tests/
- [X] T002 Add `backend/htmlcov/` exclusion to static analysis tool config (cgc, ruff) to eliminate false positives per FR-001
- [X] T003 [P] Remove all commented-out code blocks (without active tracked TODOs) from backend/src/services/copilot_polling/agent_output.py
- [X] T004 [P] Remove all commented-out code blocks from backend/src/services/copilot_polling/pipeline.py
- [X] T005 [P] Remove all commented-out code blocks from backend/src/services/workflow_orchestrator/orchestrator.py
- [X] T006 Evaluate `handle_service_error()` and `safe_error_response()` in backend/src/logging_utils.py — mark for Phase 2 adoption or delete per FR-003
- [X] T007 Run `ruff check backend/src/` and `pytest -x` to verify clean baseline; commit Phase 1

**Checkpoint**: Static analysis produces no dead-code false positives. All commented-out code removed. Tests pass.

---

## Phase 2: Foundational (DRY Helpers & Structured Logging Infrastructure)

**Purpose**: Create shared helpers and logging infrastructure that ALL subsequent user stories depend on. Maps to FR-004–FR-008 (DRY), FR-027–FR-028 (logging). BLOCKS all user story phases.

**CRITICAL**: No user story work can begin until this phase is complete.

### Structured Logging Setup

- [X] T008 Wire existing `StructuredJsonFormatter` as root handler in backend/src/main.py lifespan per contracts/structured-logging.md
- [X] T009 Update all backend/src/ files using bare `import logging` to use `from src.logging_utils import get_logger` convention. Verify: `grep -rn "^import logging" backend/src/` returns 0 results after completion.
- [X] T010 Add structured `extra={}` context to service-layer log calls in backend/src/services/ (operation, duration_ms where available)

### DRY Helper Extraction

- [X] T011 Create `require_selected_project()` dependency in backend/src/dependencies.py — returns project ID or raises HTTPException per FR-005
- [X] T012 Create `cached_fetch()` async wrapper in backend/src/utils.py — generic cache check/refresh/set/stale-fallback per FR-006
- [X] T013 [P] Adopt (if T006 decided to keep) or delete `handle_service_error()`/`safe_error_response()` in backend/src/logging_utils.py — create `@handle_github_errors` decorator if adopting per FR-007
- [X] T014 Run `pytest -x` and `ruff check backend/src/` to verify foundational helpers work; commit Phase 2

**Checkpoint**: Foundation ready — structured logging active, DRY helpers available. All user story implementation can now begin.

---

## Phase 3: User Story 2 — DRY Consolidation (Priority: P1)

**Goal**: Eliminate all duplicate code patterns: repository resolution (8 paths → 1), project validation (5 checks → 1 helper), cache patterns (4 inline → wrapper), error handling (shared decorator). Remove ~230 lines.

**Independent Test**: `ruff check` passes. `pytest -x` passes. All callers use canonical functions. SC-002: ≥200 lines removed. SC-010: zero DRY violations remaining.

- [X] T015 Identify and remove/update stale tests that mock removed duplicate functions in backend/tests/
- [X] T016 [US2] Consolidate all 8 repository resolution code paths to use canonical `resolve_repository()` from backend/src/utils.py — update callers in backend/src/api/workflow.py, backend/src/api/chat.py, backend/src/api/projects.py, backend/src/main.py
- [X] T017 [US2] Delete `_get_repository_info()` from backend/src/api/workflow.py and remove 102-line inlined fallback from backend/src/main.py
- [X] T018 [US2] Replace 5 inline "no project selected" checks with `require_selected_project()` in backend/src/api/chat.py, backend/src/api/workflow.py, backend/src/api/tasks.py
- [X] T019 [US2] Replace 4 inline cache check/refresh/set patterns with `cached_fetch()`: 2 patterns in backend/src/api/projects.py, 1 in backend/src/api/board.py, 1 in backend/src/api/chat.py
- [X] T020 [US2] Apply `@handle_github_errors` decorator (or shared helper) to endpoints in backend/src/api/board.py, backend/src/api/projects.py, backend/src/api/workflow.py per FR-007
- [X] T021 [P] [US2] Create `case_insensitive_get()` utility in frontend/src/lib/case-utils.ts and replace 5 inline `Object.keys().find()` in frontend/src/hooks/useAgentConfig.ts per FR-008
- [X] T022 [US2] Run `pytest -x`, `ruff check`, `npx vitest run` — verify SC-002 (≥200 lines removed), SC-010 (zero DRY violations); commit Phase 3

**Checkpoint**: All DRY violations resolved. ~230 lines removed. All tests pass.

---

## Phase 4: User Story 1 — Backend Complexity Reduction (Priority: P1)

**Goal**: Reduce all 8 backend functions scoring complexity >40 to below 25. Extract focused helpers, create typed dataclasses, replace emoji string matching with enum. Migrate chat storage to SQLite.

**Independent Test**: `cgc analyze complexity` → all functions below 25. `pytest -x` passes. SC-001 met.

- [X] T023 Identify and remove/update stale tests related to refactored functions in backend/tests/

### 4.1: agent_output.py (Complexity 123 → <25 each)

- [X] T024 [US1] Add `CommentScanResult` dataclass to backend/src/services/copilot_polling/agent_output.py per data-model.md
- [X] T025 [US1] Extract `_reconstruct_pipeline_if_missing()` helper (~230 lines) from `post_agent_outputs_from_pr()` in backend/src/services/copilot_polling/agent_output.py
- [X] T026 [US1] Extract `_detect_completion_signals()` helper from `post_agent_outputs_from_pr()` in backend/src/services/copilot_polling/agent_output.py
- [X] T027 [US1] Extract `_post_markdown_outputs()` helper from `post_agent_outputs_from_pr()` in backend/src/services/copilot_polling/agent_output.py
- [X] T028 [US1] Extract `_merge_and_claim_child_pr()` helper from `post_agent_outputs_from_pr()` in backend/src/services/copilot_polling/agent_output.py
- [X] T029 [US1] Extract `_post_done_marker()` helper from `post_agent_outputs_from_pr()` in backend/src/services/copilot_polling/agent_output.py
- [X] T030 [US1] Refactor `post_agent_outputs_from_pr()` to orchestrate extracted helpers — verify complexity <25 in backend/src/services/copilot_polling/agent_output.py

### 4.2: orchestrator.py (Complexity 91 → <25 each)

- [X] T031 [US1] Add `AgentResolution` dataclass to backend/src/services/workflow_orchestrator/orchestrator.py per data-model.md
- [X] T032 [US1] Extract `_resolve_agents_from_tracking_table()` from `assign_agent_for_status()` in backend/src/services/workflow_orchestrator/orchestrator.py
- [X] T033 [US1] Extract `_resolve_agents_from_config()` from `assign_agent_for_status()` in backend/src/services/workflow_orchestrator/orchestrator.py
- [X] T034 [US1] Extract `_determine_base_ref()` from `assign_agent_for_status()` in backend/src/services/workflow_orchestrator/orchestrator.py
- [X] T035 [US1] Extract `_resolve_model()` from `assign_agent_for_status()` in backend/src/services/workflow_orchestrator/orchestrator.py
- [X] T036 [US1] Refactor `assign_agent_for_status()` to use extracted helpers + `AgentResolution` dataclass in backend/src/services/workflow_orchestrator/orchestrator.py

### 4.3: recovery.py (Complexity 72 → <20 each)

- [X] T037 [US1] Add `AgentStepState` enum to backend/src/models/agent.py per data-model.md — replace emoji string matching per FR-011
- [X] T038 [US1] Extract `_should_skip_recovery()` from `recover_stalled_issues()` in backend/src/services/copilot_polling/recovery.py
- [X] T039 [US1] Extract `_validate_tracking_table()` from `recover_stalled_issues()` in backend/src/services/copilot_polling/recovery.py
- [X] T040 [US1] Extract `_attempt_reassignment()` from `recover_stalled_issues()` in backend/src/services/copilot_polling/recovery.py
- [X] T041 [US1] Replace all emoji string matching in recovery.py with `AgentStepState.from_markdown()` calls in backend/src/services/copilot_polling/recovery.py

### 4.4: polling_loop.py (Complexity 43 → <15)

- [X] T042 [US1] Add `PollStep` dataclass and `POLL_STEPS` list to backend/src/services/copilot_polling/polling_loop.py per data-model.md and FR-013
- [X] T043 [US1] Refactor `_poll_loop()` to iterate over `POLL_STEPS` list instead of repeated inline conditional blocks in backend/src/services/copilot_polling/polling_loop.py

### 4.5: chat.py (Complexity 42 → <20)

- [X] T044 [US1] Create `chat_messages` SQLite table migration in backend/src/migrations/ per data-model.md schema (FR-012)
- [X] T045 [US1] Replace `_messages` dict with SQLite-backed storage + TTL cleanup in backend/src/api/chat.py
- [X] T046 [US1] Extract chat command dispatch handlers from `send_message()` in backend/src/api/chat.py. The 5 command handlers are: (1) `/agent` — custom agent creation, (2) `#block` — blocking issue detection, (3) feature request — issue generation, (4) status change — board column move, (5) task generation — task from description

### 4.6: cleanup_service.py (Complexity 42 → <20)

- [X] T047 [US1] Add `ItemClassification` dataclass to backend/src/services/cleanup_service.py per data-model.md
- [X] T048 [US1] Extract `_link_by_branch_name()` from `preflight()` in backend/src/services/cleanup_service.py
- [X] T049 [US1] Extract `_link_by_pr_body()` from `preflight()` in backend/src/services/cleanup_service.py
- [X] T050 [US1] Extract `_link_by_ownership()` from `preflight()` in backend/src/services/cleanup_service.py
- [X] T051 [US1] Refactor `preflight()` to use extracted helpers + `ItemClassification` dataclass in backend/src/services/cleanup_service.py

### 4.7: get_board_data in service.py (Complexity 63 → <25)

- [X] T052 [US1] Extract `_build_column_map()` from `get_board_data()` in backend/src/services/github_projects/service.py
- [X] T053 [US1] Extract `_classify_board_items()` from `get_board_data()` in backend/src/services/github_projects/service.py
- [X] T054 [US1] Refactor `get_board_data()` to orchestrate extracted helpers — verify complexity <25 in backend/src/services/github_projects/service.py

### 4.8: _reconstruct_pipeline_state in pipeline.py (Complexity 49 → <25)

- [X] T055 [US1] Extract `_parse_tracking_table_rows()` from `_reconstruct_pipeline_state()` in backend/src/services/copilot_polling/pipeline.py
- [X] T056 [US1] Extract `_reconcile_issue_states()` from `_reconstruct_pipeline_state()` in backend/src/services/copilot_polling/pipeline.py
- [X] T057 [US1] Refactor `_reconstruct_pipeline_state()` to use extracted helpers — verify complexity <25 in backend/src/services/copilot_polling/pipeline.py

### 4.9: Verification

- [X] T058 [US1] Run `cgc analyze complexity` — verify all 8 refactored backend functions score <25 (SC-001). Additionally verify FR-010: confirm all extracted helpers accept explicit parameters (no closures over parent scope). Run `pytest -x`; commit Phase 4

**Checkpoint**: All 8 high-complexity backend functions refactored below threshold 25. Chat storage migrated to SQLite. Emoji matching replaced with typed enum. All tests pass.

---

## Phase 5: User Story 3 — God Class Decomposition (Priority: P2)

**Goal**: Split 5,338-line `GitHubProjectsService` into domain-specific services inheriting from shared base client. Each extracted incrementally without facade — all callers updated in the same step (FR-014).

**Independent Test**: `wc -l service.py` < 1,500. Each extracted service < 800 lines. `pytest -x` passes. SC-003 met.

- [x] T059 Identify and remove/update stale tests that mock `GitHubProjectsService` methods being extracted in backend/tests/

### 5.1: Static Utilities (Warmup)

- [x] T060 [US3] Extract bot detection functions to backend/src/services/github_projects/identities.py — move `is_copilot_author`, `is_copilot_swe_agent`, `is_copilot_reviewer_bot` per FR-016
- [x] T061 [US3] Update all callers of bot detection methods to import from identities.py (search all files importing from service.py)

### 5.2: Rate Limit Manager

- [x] T062 [US3] Extract `RateLimitManager` class to backend/src/services/github_projects/rate_limit.py per data-model.md and FR-015
- [x] T063 [US3] Update service.py to use `RateLimitManager` instead of inline contextvars + instance attributes in backend/src/services/github_projects/service.py

### 5.3: Base Client

- [x] T064 [US3] Extract `GitHubBaseClient` to backend/src/services/github_projects/base_client.py — move `_graphql()`, `_rest()`, `_request_with_retry()`, ETag cache, request coalescing per contracts/github-base-client.md
- [x] T065 [US3] Have `GitHubProjectsService` inherit from `GitHubBaseClient` in backend/src/services/github_projects/service.py

### 5.4: Domain Service Extraction (sequential — each updates all callers)

- [x] T066 [US3] Extract `GitHubBranchService` to backend/src/services/github_projects/branches.py — move branch/commit/PR-creation methods + update all callers per contracts/domain-services.md
- [x] T067 [US3] Extract `GitHubPullRequestService` to backend/src/services/github_projects/pull_requests.py — move PR methods + update all callers per contracts/domain-services.md
- [x] T068 [US3] Extract `GitHubIssuesService` to backend/src/services/github_projects/issues.py — move issue methods + update all callers per contracts/domain-services.md
- [x] T069 [US3] Extract `GitHubProjectBoardService` to backend/src/services/github_projects/projects.py — move board/project methods + update all callers per contracts/domain-services.md

### 5.5: Dependency Injection & Typed Returns

- [x] T070 [US3] Add domain service dependency getters to backend/src/dependencies.py — `get_github_issues_service`, `get_github_pr_service`, `get_github_branch_service`, `get_github_board_service`
- [x] T071 [US3] Add Pydantic response models for the following domain service methods: `create_issue`, `get_issue_with_comments`, `get_linked_pull_requests`, `merge_pull_request`, `create_branch`, `create_pull_request`, `get_project_items`, `update_item_status`, `get_board_data`, `get_status_columns` per FR-017
- [x] T072 [US3] Run `pytest -x`, `pyright backend/src/`, verify `wc -l service.py` < 1,500, each domain service < 800 lines (SC-003); commit Phase 5

**Checkpoint**: God class decomposed. 7 new focused files. All callers updated. DI providers added. All tests pass.

---

## Phase 6: User Story 4 — Frontend Complexity Reduction (Priority: P2)

**Goal**: No frontend component or hook exceeds 200 lines. Monolithic components split into focused sub-components. Form state modernized with react-hook-form + zod.

**Independent Test**: `npx vitest run`, `npx tsc --noEmit`. All components < 200 lines. SC-004 met.

- [ ] T073 Identify and remove/update stale frontend tests related to components being refactored in frontend/src/

### 6.1: Settings Form (GlobalSettings.tsx)

- [ ] T074 [P] [US4] Install `react-hook-form` and `zod` + `@hookform/resolvers` in frontend/package.json
- [ ] T075 [US4] Extract `<AISettingsSection />` component from frontend/src/components/settings/GlobalSettings.tsx (<100 lines)
- [ ] T076 [US4] Extract `<DisplaySettings />` component from frontend/src/components/settings/GlobalSettings.tsx (<100 lines)
- [ ] T077 [US4] Extract `<WorkflowSettings />` component from frontend/src/components/settings/GlobalSettings.tsx (<100 lines)
- [ ] T078 [US4] Extract `<NotificationSettings />` component from frontend/src/components/settings/GlobalSettings.tsx (<100 lines)
- [ ] T079 [US4] Migrate GlobalSettings.tsx to react-hook-form + zod schema — eliminate manual flatten/unflatten per FR-021

### 6.2: Pipeline Config Hook

- [ ] T080 [US4] Extract `usePipelineBoard()` hook from frontend/src/hooks/usePipelineConfig.ts (<200 lines)
- [ ] T081 [US4] Extract `usePipelineValidation()` hook from frontend/src/hooks/usePipelineConfig.ts (<200 lines)
- [ ] T082 [US4] Extract `usePipelineModelOverride()` hook from frontend/src/hooks/usePipelineConfig.ts (<200 lines)
- [ ] T083 [US4] Refactor remaining usePipelineConfig.ts to use `useReducer` for complex state instead of 10+ `useState` calls

### 6.3: Shared Utilities

- [ ] T084 [P] [US4] Create `frontend/src/lib/time-utils.ts` — extract `msToReadable()`, `daysToMs()`, `getProgressPercent()` per FR-019
- [ ] T085 [P] [US4] Replace inline time calculations in frontend/src/components/chores/FeaturedRitualsPanel.tsx and ChoreCard.tsx with time-utils
- [ ] T086 [P] [US4] Replace `as unknown as ...` casts with zod-validated schemas in frontend/src/hooks/useChat.ts per FR-020

### 6.4: Login Page

- [ ] T087 [US4] Extract `<AnimatedBackground />` component from frontend/src/pages/LoginPage.tsx — reduce nesting per FR-018

### 6.5: Verification

- [ ] T088 [US4] Run `npx vitest run`, `npx tsc --noEmit`, `npx eslint .` — verify all components/hooks < 200 lines (SC-004); commit Phase 6

**Checkpoint**: All frontend complexity hotspots resolved. Form state modernized. All components under 200 lines.

---

## Phase 7: User Story 5 — Infrastructure & Build Reproducibility (Priority: P3)

**Goal**: All Docker images pinned. All Python dependencies have upper bounds. Pyright upgraded to standard mode. Builds are fully reproducible.

**Independent Test**: `docker compose build` succeeds. No `latest` tags. All deps have upper bounds. SC-008 met.

- [ ] T089 [US5] FR-029 check: no stale tests expected from Docker/dependency changes — verify with `pytest -x` baseline before proceeding
- [ ] T090 [US5] Pin signal-api Docker image to specific semantic version in docker-compose.yml (replace `bbernhard/signal-cli-rest-api:latest`)
- [ ] T091 [P] [US5] Pin nginx version in frontend/Dockerfile (e.g., `nginx:1.27-alpine` instead of `nginx:alpine`) per FR-022
- [ ] T092 [US5] Add upper-bound version constraints to all major Python dependencies in backend/pyproject.toml per FR-023 — bounds must include currently installed versions
- [ ] T093 [US5] Upgrade pyright from `basic` to `standard` mode in backend/pyproject.toml — fix or document all new type errors per SC-007
- [ ] T094 [US5] Run `docker compose build`, `pytest -x`, `pyright backend/src/` — verify SC-008 (reproducible builds); commit Phase 7

**Checkpoint**: Infrastructure hardened. All Docker tags pinned. All dependency versions bounded. Pyright standard mode active.

---

## Phase 8: User Story 6 — Testing Hygiene (Priority: P3)

**Goal**: Consolidate mock factories. Add `spec=` to mocks. Write dedicated tests for all refactored high-complexity functions. Achieve ≥70% coverage on refactored modules.

**Independent Test**: `pytest --cov` → refactored modules ≥70% coverage. SC-006 met.

### 8.1: Mock Consolidation

- [ ] T095 [US6] Merge all mock factories from backend/tests/helpers/mocks.py into backend/tests/conftest.py per FR-025
- [ ] T096 [US6] Delete backend/tests/helpers/mocks.py after consolidation — update all test imports
- [ ] T097 [US6] Add `spec=` parameter to mock constructors in backend/tests/conftest.py per FR-024

### 8.2: Unit Tests for Refactored Functions

- [ ] T098 [P] [US6] Write unit tests for extracted agent_output.py helpers in backend/tests/unit/test_agent_output.py
- [ ] T099 [P] [US6] Write unit tests for extracted orchestrator.py helpers in backend/tests/unit/test_orchestrator.py
- [ ] T100 [P] [US6] Write unit tests for extracted recovery.py helpers + AgentStepState enum in backend/tests/unit/test_recovery.py
- [ ] T101 [P] [US6] Write unit tests for chat.py command handlers + SQLite storage in backend/tests/unit/test_chat.py
- [ ] T102 [P] [US6] Write unit tests for cleanup_service.py extracted helpers in backend/tests/unit/test_cleanup_service.py
- [ ] T103 [P] [US6] Write unit tests for polling_loop.py PollStep iteration in backend/tests/unit/test_polling_loop.py

### 8.3: Verification

- [ ] T104 [US6] Run `pytest --cov=src --cov-report=term` — verify refactored modules ≥70% coverage (SC-006); commit Phase 8

**Checkpoint**: All refactored functions have dedicated tests. Mock factories consolidated. ≥70% coverage on refactored modules.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all phases. Verify all success criteria. Update documentation.

- [ ] T105 FR-029 check: no stale tests expected from verification-only phase
- [ ] T106 Run `cgc analyze complexity` — verify SC-001 (all backend functions <25)
- [ ] T107 Run `wc -l` on all backend source files — verify SC-003 (no file >1,500 lines)
- [ ] T108 [P] Run full static analysis suite: `ruff check backend/src/`, `pyright backend/src/`, `npx tsc --noEmit`, `npx eslint .` — verify SC-007 (zero new warnings)
- [ ] T109 [P] Verify SC-002: count total backend LOC reduction (target ≥200 lines removed)
- [ ] T110 [P] Verify SC-009 proxy: confirm no function in backend/src/ requires reading >200 lines to understand a single responsibility (`wc -l` on all extracted helpers <200)
- [ ] T111 Run quickstart.md validation — verify all before/after examples from specs/033-code-quality-overhaul/quickstart.md match actual code
- [ ] T112 Final commit with comprehensive message listing all success criteria verified

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └──→ Phase 2 (Foundational) [BLOCKS ALL]
        ├──→ Phase 3 (US2: DRY) ──→ Phase 4 (US1: Complexity) ──→ Phase 5 (US3: God Class) ──┐
        ├──→ Phase 6 (US4: Frontend) [independent of backend phases] ─────┤
        └──→ Phase 7 (US5: Infra) [independent of code phases] ───────────┤
                                                                              └─→ Phase 8 (US6: Testing) [depends on Phase 4 + Phase 5 + Phase 7]
                                                                                    └──→ Phase 9 (Polish)
```

### Phase Mapping (Spec → Tasks)

| Spec Phase | Tasks Phase | User Story | Description |
|------------|-------------|------------|-------------|
| (new) | Phase 1 | — | Setup: dead code cleanup |
| (new) | Phase 2 | — | Foundational: DRY helpers + logging infra |
| Phase 2 | Phase 3 | US2 | DRY Consolidation |
| Phase 3 | Phase 4 | US1 | Backend Complexity Reduction |
| Phase 4 | Phase 5 | US3 | God Class Decomposition |
| Phase 5 | Phase 6 | US4 | Frontend Complexity Reduction |
| Phase 6 (infra) | Phase 7 | US5 | Infrastructure & Build Reproducibility |
| Phase 6 (testing) | Phase 8 | US6 | Testing Hygiene |
| (new) | Phase 9 | — | Polish & Cross-Cutting Verification |

### User Story Dependencies

- **US2 (DRY)**: Depends on Phase 2 foundational helpers. Should complete before US1 because DRY helpers are used during complexity refactoring.
- **US1 (Complexity)**: Depends on US2 completion (DRY helpers available). No dependency on US3/US4.
- **US3 (God Class)**: Depends on US1 completion (complexity-reduced service.py is easier to split). Sequential extraction within phase.
- **US4 (Frontend)**: Independent of all backend stories. Can run in parallel with backend work after Phase 2.
- **US5 (Infra)**: Independent of code refactoring. Can run in parallel after Phase 2.
- **US6 (Testing)**: Depends on US1 + US3 (needs refactored code to test). Must be last backend phase.

### Within Each User Story

- Stale test cleanup FIRST (FR-029)
- Dataclasses/enums before code that uses them
- Sequential extraction within a function (avoid merge conflicts)
- Verification + commit LAST (FR-030)

### Parallel Opportunities

**Phase 2** (Foundational):
- T008–T010 (logging) can run in parallel with T011–T013 (DRY helpers)

**Phase 4** (US1: Complexity):
- T024–T030 (agent_output.py) ‖ T031–T036 (orchestrator.py) ‖ T037–T041 (recovery.py) — different files
- T042–T043 (polling_loop.py) ‖ T044–T046 (chat.py) ‖ T047–T051 (cleanup_service.py) ‖ T052–T054 (service.py get_board_data) ‖ T055–T057 (pipeline.py) — different files

**Phase 6** (US4: Frontend):
- T075–T079 (GlobalSettings) ‖ T080–T083 (usePipelineConfig) ‖ T084–T086 (utilities) — different files

**Phase 8** (US6: Testing):
- T098–T103 — all test files are independent, fully parallelizable

**Cross-phase parallelism**: Phase 6 (Frontend) can run in parallel with Phases 3–5 (all backend).

---

## Parallel Example: Phase 4 (Backend Complexity)

```
# Parallel batch 1 — different files, no dependencies:
T024 CommentScanResult dataclass in agent_output.py
T031 AgentResolution dataclass in orchestrator.py
T037 AgentStepState enum in models/agent.py
T042 PollStep dataclass in polling_loop.py
T044 chat_messages SQLite migration
T047 ItemClassification dataclass in cleanup_service.py

# Parallel batch 2 — extract helpers (within same file, sequential per file but parallel across files):
T025–T030 (agent_output.py) ‖ T032–T036 (orchestrator.py) ‖ T038–T041 (recovery.py) ‖ T043 (polling_loop.py) ‖ T045–T046 (chat.py) ‖ T048–T051 (cleanup_service.py) ‖ T052–T054 (service.py) ‖ T055–T057 (pipeline.py)
```

---

## Implementation Strategy

### MVP First (US2 + US1 = DRY + Complexity)

1. Complete Phase 1: Setup (dead code cleanup)
2. Complete Phase 2: Foundational (logging + DRY helpers)
3. Complete Phase 3: US2 DRY consolidation
4. Complete Phase 4: US1 Backend complexity reduction
5. **STOP and VALIDATE**: Run `cgc analyze complexity` + `pytest -x` — MVP complete
6. All high-complexity functions fixed, all DRY violations resolved

### Incremental Delivery

1. Setup + Foundational → Clean baseline
2. Add US2 (DRY) → ~230 lines removed, consistent patterns
3. Add US1 (Complexity) → All functions below threshold 25
4. Add US3 (God Class) → service.py under 1,500 lines
5. Add US4 (Frontend) → All components under 200 lines [can overlap with backend]
6. Add US5 (Infra) → Reproducible builds [can overlap with any phase]
7. Add US6 (Testing) → ≥70% coverage on refactored modules
8. Polish → Final verification

### Per-Phase Commit Workflow (FR-029 + FR-030)

1. Remove stale/broken tests for this phase's scope
2. Implement the phase's tasks
3. Run ALL tests (`pytest -x`, `vitest run` as applicable)
4. Commit with detailed message: what changed, why, which SC-* verified
