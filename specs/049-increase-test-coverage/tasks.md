# Tasks: Increase Test Coverage to Surface Unknown Bugs

**Input**: Design documents from `/specs/049-increase-test-coverage/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature's entire deliverable IS tests and CI configuration. All tasks produce test files, CI workflows, or threshold updates.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app monorepo**: `solune/backend/` (Python/FastAPI) + `solune/frontend/` (TypeScript/React)
- **CI**: `.github/workflows/`
- **Backend tests**: `solune/backend/tests/`
- **Frontend tests**: Co-located `*.test.{ts,tsx}` files

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing test infrastructure and establish baseline understanding

- [ ] T001 Audit existing backend test infrastructure — review fixtures in solune/backend/tests/conftest.py, factories in solune/backend/tests/helpers/factories.py, and template test files (test_issues.py, test_polling_loop.py, test_chores_service.py, test_api_apps.py)
- [ ] T002 Audit existing frontend test infrastructure — review createMockApi() in solune/frontend/src/test/setup.ts, renderWithProviders() in solune/frontend/src/test/test-utils.tsx, expectNoA11yViolations() in solune/frontend/src/test/a11y-helpers.ts, and data factories in solune/frontend/src/test/factories/index.ts

---

## Phase 2: User Story 1 — CI Runs All Existing Advanced Tests (Priority: P1) 🎯 MVP

**Goal**: Wire all existing local-only advanced tests (property, fuzz, chaos, concurrency) into CI so regressions in complex behaviors are caught before merge. Establish mutation testing on a weekly schedule.

**Independent Test**: Run a CI pipeline on a pull request and verify that backend property, fuzz, chaos, and concurrency test suites all execute and report results. Frontend fuzz tests must appear in CI output. Mutation workflow runs weekly.

**Maps to**: FR-001, FR-002, FR-003, FR-005

### Implementation for User Story 1

- [ ] T003 [US1] Add backend advanced tests job to .github/workflows/ci.yml — separate job running `pytest tests/property/ tests/fuzz/ tests/chaos/ tests/concurrency/ --timeout=120 -v` with `HYPOTHESIS_PROFILE=ci`, Python 3.12, working-directory solune/backend
- [ ] T004 [P] [US1] Verify frontend fuzz test discovery — confirm `src/__tests__/fuzz/jsonParse.test.tsx` and `src/__tests__/fuzz/zodFieldRename.test.ts` are discovered by Vitest glob in solune/frontend/vitest.config.ts; add explicit include if needed
- [ ] T005 [P] [US1] Create mutation testing workflow in .github/workflows/mutation.yml — weekly schedule (Monday 03:00 UTC), backend mutmut with 4 shards via solune/backend/scripts/run_mutmut_shard.py, frontend Stryker (hooks+lib) via `npm run test:mutate`, artifact upload with 30-day retention
- [ ] T006 [US1] Configure advanced tests as non-blocking in .github/workflows/ci.yml — set `continue-on-error: true` on the backend advanced tests job; add comment documenting transition to blocking once baselines stabilize

**Checkpoint**: CI logs show property/fuzz/chaos/concurrency tests executing on every PR. Mutation workflow runs weekly. Advanced tests are non-blocking.

---

## Phase 3: User Story 2 — Backend Coverage Reaches 80% (Priority: P1)

**Goal**: Raise backend line coverage from 71% to 80% and branch coverage to ≥70% by testing 9 high-risk untested modules and then hardening with mutation-targeted tests.

**Independent Test**: `cd solune/backend && pytest --cov=src --cov-report=term-missing` shows ≥80% line coverage, ≥70% branch coverage.

**Maps to**: FR-006 through FR-010, FR-019, FR-027

### Backend High-ROI Gap Tests (71% → 76%)

- [ ] T007 [P] [US2] Write tests for GitHub integration agents in solune/backend/tests/unit/test_github_agents.py — mock GitHub API via mock_github_service fixture, verify request construction, error paths (429 rate-limit, timeout, 404 not-found); follow tests/unit/test_issues.py as template
- [ ] T008 [P] [US2] Write tests for Copilot polling helpers in solune/backend/tests/unit/test_polling_helpers.py — test rate-limit tier logic with boundary values (50/51, 100/101), adaptive polling interval calculations; follow tests/unit/test_polling_loop.py as template
- [ ] T009 [P] [US2] Write tests for Copilot polling pipeline in solune/backend/tests/unit/test_polling_pipeline.py — test pipeline orchestration, stage transitions, error recovery; follow tests/unit/test_polling_loop.py as template
- [ ] T010 [P] [US2] Write tests for chores chat in solune/backend/tests/unit/test_chores_chat.py — test message construction, chat flow, error handling; follow tests/unit/test_chores_service.py as template
- [ ] T011 [P] [US2] Write tests for chores template builder in solune/backend/tests/unit/test_chores_template_builder.py — test template rendering, variable substitution, edge cases; follow tests/unit/test_chores_service.py as template
- [ ] T012 [P] [US2] Write tests for API agents routes in solune/backend/tests/unit/test_api_agents.py — test status codes, response shapes, input validation, error handling; follow tests/unit/test_api_apps.py (test client pattern)
- [ ] T013 [P] [US2] Write tests for API health route in solune/backend/tests/unit/test_api_health.py — test health endpoint responses, dependency checks; follow tests/unit/test_api_apps.py (test client pattern)
- [ ] T014 [P] [US2] Write tests for API webhook models in solune/backend/tests/unit/test_api_webhook_models.py — test webhook payload validation, model parsing, edge cases; follow tests/unit/test_api_apps.py (test client pattern)
- [ ] T015 [US2] Bump backend fail_under from 71 to 76 in solune/backend/pyproject.toml — update `[tool.coverage.report] fail_under` value

### Backend Mutation Hardening (76% → 80%)

- [ ] T016 [US2] Run mutmut against solune/backend/src/services/, identify top 20 surviving mutants, and document findings — focus on boundary conditions, boolean negations, arithmetic mutations
- [ ] T017 [US2] Write targeted mutation-kill tests for ≥10 surviving mutants in solune/backend/tests/unit/test_mutation_kills.py — target boundary conditions (rate-limit tiers: 50/51, 100/101), boolean negation (guard/auth checks), arithmetic mutations (polling intervals, backoff formulas)
- [ ] T018 [US2] Bump backend fail_under from 76 to 80 in solune/backend/pyproject.toml — update `[tool.coverage.report] fail_under` value; verify ≥70% branch coverage

**Checkpoint**: `pytest --cov=src --cov-report=term-missing` shows ≥80% lines, ≥70% branches. CI enforces 80% threshold.

---

## Phase 4: User Story 3 — Frontend Coverage Reaches Target Thresholds (Priority: P1)

**Goal**: Raise frontend coverage from ~50/45/42/51% to 60/55/52/60% (statements/branches/functions/lines) by testing schema validators, 24 hooks, and 53 components.

**Independent Test**: `cd solune/frontend && npm run test:coverage` shows ≥60/55/52/60% (stmt/branch/func/lines).

**Maps to**: FR-011 through FR-018, FR-020, FR-027

### Schema Validation Tests (100% coverage target)

- [ ] T019 [P] [US3] Write tests for all 6 Zod schema files under solune/frontend/src/services/schemas/ — create co-located *.test.ts files; pure input/output testing with zero mocking; validate correct inputs, reject invalid inputs, verify default values and transformations

### Hook Tests — P1 Business-Critical (highest risk first)

- [ ] T020 [P] [US3] Write tests for useSettings hook in solune/frontend/src/hooks/useSettings.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T021 [P] [US3] Write tests for useAgents hook in solune/frontend/src/hooks/useAgents.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T022 [P] [US3] Write tests for useChores hook in solune/frontend/src/hooks/useChores.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T023 [P] [US3] Write tests for useTools hook in solune/frontend/src/hooks/useTools.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T024 [P] [US3] Write tests for useApps hook in solune/frontend/src/hooks/useApps.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T025 [P] [US3] Write tests for useChatProposals hook in solune/frontend/src/hooks/useChatProposals.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T026 [P] [US3] Write tests for usePipelineValidation hook in solune/frontend/src/hooks/usePipelineValidation.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states
- [ ] T027 [P] [US3] Write tests for usePipelineBoardMutations hook in solune/frontend/src/hooks/usePipelineBoardMutations.test.tsx — renderHook() with createMockApi(), assert query keys, mutation calls, error states

### Hook Tests — P2 UI State

- [ ] T028 [P] [US3] Write tests for useAgentConfig hook in solune/frontend/src/hooks/useAgentConfig.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T029 [P] [US3] Write tests for useAgentTools hook in solune/frontend/src/hooks/useAgentTools.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T030 [P] [US3] Write tests for useMcpSettings hook in solune/frontend/src/hooks/useMcpSettings.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T031 [P] [US3] Write tests for useMcpPresets hook in solune/frontend/src/hooks/useMcpPresets.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T032 [P] [US3] Write tests for useMetadata hook in solune/frontend/src/hooks/useMetadata.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T033 [P] [US3] Write tests for useModels hook in solune/frontend/src/hooks/useModels.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T034 [P] [US3] Write tests for useNotifications hook in solune/frontend/src/hooks/useNotifications.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T035 [P] [US3] Write tests for useRecentParentIssues hook in solune/frontend/src/hooks/useRecentParentIssues.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states
- [ ] T036 [P] [US3] Write tests for useRepoMcpConfig hook in solune/frontend/src/hooks/useRepoMcpConfig.test.tsx — renderHook() with createMockApi(), assert query keys, state management, error states

### Hook Tests — P3 Simple

- [ ] T037 [P] [US3] Write tests for useAppTheme hook in solune/frontend/src/hooks/useAppTheme.test.tsx — renderHook(), assert theme state, toggling behavior
- [ ] T038 [P] [US3] Write tests for useCleanup hook in solune/frontend/src/hooks/useCleanup.test.tsx — renderHook(), assert cleanup lifecycle behavior
- [ ] T039 [P] [US3] Write tests for useMentionAutocomplete hook in solune/frontend/src/hooks/useMentionAutocomplete.test.tsx — renderHook(), assert autocomplete query and filter behavior
- [ ] T040 [P] [US3] Write tests for usePipelineModelOverride hook in solune/frontend/src/hooks/usePipelineModelOverride.test.tsx — renderHook(), assert model override state and mutations
- [ ] T041 [P] [US3] Write tests for useSidebarState hook in solune/frontend/src/hooks/useSidebarState.test.tsx — renderHook(), assert sidebar open/close state management
- [ ] T042 [P] [US3] Write tests for useUnsavedChanges hook in solune/frontend/src/hooks/useUnsavedChanges.test.tsx — renderHook(), assert dirty state tracking and prompt behavior

### Ratchet: Hooks & Services Threshold

- [ ] T043 [US3] Bump frontend coverage thresholds to 53/48/45/54% in solune/frontend/vitest.config.ts — update `coverage.thresholds` to `{ statements: 53, branches: 48, functions: 45, lines: 54 }`

### Component Tests — Settings (14 untested)

- [ ] T044 [P] [US3] Write tests for settings components (GlobalSettings, AIPreferences, McpSettings, ProjectSettings, and remaining 10 settings components) in solune/frontend/src/components/settings/*.test.tsx — follow SettingsSection.test.tsx as template; use renderWithProviders() + expectNoA11yViolations()

### Component Tests — Board (11 untested)

- [ ] T045 [P] [US3] Write tests for board components (ProjectBoard, BoardToolbar, CleanUpButton, cleanup modals, and remaining 7 board components) in solune/frontend/src/components/board/*.test.tsx — follow BoardColumn.test.tsx as template; use renderWithProviders() + expectNoA11yViolations()

### Component Tests — Pipeline (9 untested)

- [ ] T046 [P] [US3] Write tests for pipeline components (PipelineToolbar, ModelSelector, ExecutionGroupCard, ParallelStageGroup, and remaining 5 pipeline components) in solune/frontend/src/components/pipeline/*.test.tsx — use renderWithProviders() + expectNoA11yViolations()

### Component Tests — Chat, Chores, Tools, Agents (~19 untested)

- [ ] T047 [P] [US3] Write tests for remaining ~19 untested components across chat, chores, tools, and agents directories in solune/frontend/src/components/**/*.test.tsx — use renderWithProviders() + expectNoA11yViolations(); verify user interactions with userEvent

### Ratchet: Components Threshold

- [ ] T048 [US3] Bump frontend coverage thresholds to 60/55/52/60% in solune/frontend/vitest.config.ts — update `coverage.thresholds` to `{ statements: 60, branches: 55, functions: 52, lines: 60 }`

### Frontend Mutation Hardening

- [ ] T049 [US3] Run Stryker against solune/frontend/ hooks and lib, identify top 20 surviving mutants, and document findings
- [ ] T050 [US3] Strengthen tests to kill ≥10 surviving frontend mutants — improve assertions on return values, conditional branches, and error paths across solune/frontend/src/**/*.test.{ts,tsx}

**Checkpoint**: `npm run test:coverage` shows ≥60/55/52/60% (stmt/branch/func/lines). CI enforces thresholds. ≥10 frontend mutants killed.

---

## Phase 5: User Story 4 — Production-Parity & Time-Controlled Tests (Priority: P2)

**Goal**: Surface bugs hidden by test-mode shortcuts and timing assumptions by running tests under production-like configuration and controlling time-dependent behavior at exact boundaries.

**Independent Test**: Production-parity tests surface ≥1 behavior difference vs test mode. Time-controlled tests exercise all 15 temporal behaviors at exact boundaries (±1s).

**Maps to**: FR-021, FR-022, FR-023

### Implementation for User Story 4

- [ ] T051 [US4] Add freezegun as a dev dependency in solune/backend/pyproject.toml — add `freezegun` to `[project.optional-dependencies] dev` list
- [ ] T052 [US4] Write production-parity integration tests in solune/backend/tests/integration/test_production_mode.py — test with production config: ENCRYPTION_KEY (Fernet), GITHUB_WEBHOOK_SECRET (hex), CSRF enabled, TESTING=false; exercise auth flow, webhook verification, rate limiting; test invalid env combinations
- [ ] T053 [US4] Write time-controlled tests for 15+ temporal behaviors in solune/backend/tests/unit/test_time_dependent.py — use @freeze_time for: session expiry boundaries (±1s), token refresh timing, rate-limit window resets, polling backoff formulas, reconnection delays, cache TTL, debounce timers, assignment grace periods, recovery cooldowns (depends on T051 for freezegun dependency)
- [ ] T054 [P] [US4] Write WebSocket lifecycle E2E test — full connect → receive → disconnect → polling fallback → reconnect → data freshness verification using Playwright WebSocket interception

**Checkpoint**: Production-parity tests surface ≥1 behavior difference. Time-controlled tests cover all 15 temporal behaviors. WebSocket lifecycle verified.

---

## Phase 6: User Story 5 — Architecture Fitness Tests Prevent Regression (Priority: P2)

**Goal**: Add automated architectural boundary tests and contract validation to prevent cross-layer import violations and API contract drift.

**Independent Test**: `cd solune/backend && pytest tests/architecture/ -v` passes. Frontend architecture test passes. `solune/scripts/validate-contracts.sh` exits 0.

**Maps to**: FR-024, FR-025, FR-026

### Implementation for User Story 5

- [ ] T055 [P] [US5] Write backend import boundary tests in solune/backend/tests/architecture/test_import_rules.py — AST-based analysis: services/ never imports api/, api/ never imports *_store directly, models/ never imports services/; include known-violations allowlist for pre-existing exceptions
- [ ] T056 [P] [US5] Write frontend import boundary tests in solune/frontend/src/__tests__/architecture/import-rules.test.ts — verify: pages/ never imports other pages, hooks/ never imports components, utils/ never imports hooks or components; include known-violations allowlist
- [ ] T057 [US5] Wire contract validation into CI in .github/workflows/ci.yml — add step to run solune/scripts/validate-contracts.sh verifying createMockApi() types align with openapi.json schemas

**Checkpoint**: Architecture tests catch violations. Contract validation exits 0. No new violations in allowlist.

---

## Phase 7: User Story 6 — Flaky Tests Are Detected and Eliminated (Priority: P3)

**Goal**: Detect unreliable tests through automated 3× execution, flag inconsistent results, and report the 20 slowest tests to identify optimization targets.

**Independent Test**: Scheduled flaky detection job completes, correctly identifies any flaky tests, and reports the 20 slowest tests.

**Maps to**: FR-004, FR-005 (partially — flaky detection is part of CI foundation)

### Implementation for User Story 6

- [ ] T058 [US6] Create flaky test detection script in solune/backend/scripts/detect_flaky.py — parse 3 JUnit XML result files, compare pass/fail per test, flag tests with inconsistent results across runs
- [ ] T059 [US6] Add flaky test detection scheduled job to .github/workflows/ci.yml — weekly schedule + workflow_dispatch trigger; run backend suite 3× with `--junitxml=run-$i.xml`; invoke detect_flaky.py; report 20 slowest tests via `pytest --durations=20`
- [ ] T060 [US6] Remediate identified flaky tests and verify subsequent detection runs report zero flaky tests

**Checkpoint**: Flaky detection job runs on schedule. Any flaky tests are identified and remediated. 20 slowest tests are reported.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate no regressions, CI budget compliance, and overall completeness

- [ ] T061 Verify all pre-existing tests still pass — run full backend suite (`pytest tests/`) and full frontend suite (`npm run test`) and confirm zero regressions
- [ ] T062 Validate CI execution time budget — measure backend test suite increase (must be ≤+90s) and frontend test suite increase (must be ≤+60s); if exceeded, apply pytest-xdist parallelization or Vitest thread tuning
- [ ] T063 Run quickstart.md validation scenarios from specs/049-increase-test-coverage/quickstart.md — verify all setup, execution, and verification commands produce expected results
- [ ] T064 Transition advanced tests from non-blocking to blocking — once baselines stabilize (0 flaky after 2+ weeks), update .github/workflows/ci.yml to remove `continue-on-error: true` from advanced tests job

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1: CI Foundation (Phase 2)**: Depends on Setup — provides CI infrastructure for all other stories
- **US2: Backend Coverage (Phase 3)**: Can start after Setup — does not require US1 CI to be merged (tests run locally)
- **US3: Frontend Coverage (Phase 4)**: Can start after Setup — does not require US1 CI to be merged (tests run locally)
  - Schema tests and hook tests (T019–T043) can start immediately
  - Component tests (T044–T048) are recommended after hook tests for pattern familiarity but have no hard technical dependency
  - Mutation hardening (T049–T050) depends on baseline coverage from schemas + hooks + components
- **US4: Production-Parity (Phase 5)**: Can start after Setup — independent of coverage phases
- **US5: Architecture Fitness (Phase 6)**: Can start after Setup — independent of coverage phases
- **US6: Flaky Detection (Phase 7)**: Can start after Setup — independent of coverage phases
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 1 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 1 — Mutation hardening (T016–T018) depends on gap tests (T007–T015)
- **US3 (P1)**: Can start after Phase 1 — Component tests (T044–T047) are recommended after hook tests for pattern familiarity but have no hard technical dependency; mutation hardening (T049–T050) depends on baseline coverage from schemas + hooks + components
- **US4 (P2)**: Can start after Phase 1 — T051 (freezegun dependency) must complete before T053 (time-controlled tests); T052 and T054 are independent of T051
- **US5 (P2)**: Can start after Phase 1 — Independent of all other stories
- **US6 (P3)**: Can start after Phase 1 — Independent of all other stories

### Within Each User Story

- High-ROI gap tests before mutation hardening (coverage baseline first)
- Ratchet threshold bumps after corresponding tests pass
- P1 priority hooks before P2 hooks before P3 hooks
- Schema tests and hook tests recommended before component tests (pattern familiarity, not a hard dependency)

### Parallel Opportunities

- **Phase 2 (US1)**: T004 and T005 can run in parallel (different files)
- **Phase 3 (US2)**: T007–T014 can ALL run in parallel (8 different test files, no dependencies)
- **Phase 4 (US3)**: T019–T042 can ALL run in parallel (schemas + all 24 hooks = different files); T044–T047 can ALL run in parallel (different component directories)
- **Phase 5 (US4)**: T052 and T054 can run in parallel (different test approaches); T053 depends on T051 (freezegun install)
- **Phase 6 (US5)**: T055 and T056 can run in parallel (backend vs frontend)
- **Cross-story**: US1, US2, US3, US4, US5, US6 can all start in parallel after Phase 1 (if team capacity allows)

---

## Parallel Example: User Story 2 (Backend Coverage)

```bash
# Launch all 8 backend gap tests in parallel (different files, no dependencies):
Task: T007 "Write tests for GitHub integration agents in solune/backend/tests/unit/test_github_agents.py"
Task: T008 "Write tests for Copilot polling helpers in solune/backend/tests/unit/test_polling_helpers.py"
Task: T009 "Write tests for Copilot polling pipeline in solune/backend/tests/unit/test_polling_pipeline.py"
Task: T010 "Write tests for chores chat in solune/backend/tests/unit/test_chores_chat.py"
Task: T011 "Write tests for chores template builder in solune/backend/tests/unit/test_chores_template_builder.py"
Task: T012 "Write tests for API agents routes in solune/backend/tests/unit/test_api_agents.py"
Task: T013 "Write tests for API health route in solune/backend/tests/unit/test_api_health.py"
Task: T014 "Write tests for API webhook models in solune/backend/tests/unit/test_api_webhook_models.py"

# Then sequentially:
Task: T015 "Bump backend fail_under from 71 to 76" (depends on T007–T014 passing)
```

## Parallel Example: User Story 3 (Frontend Coverage)

```bash
# Launch all schema + hook tests in parallel (different files):
Task: T019 "Write tests for all 6 Zod schema files"
Task: T020–T042 "Write tests for all 24 hooks" (each is a separate file)

# Then sequentially:
Task: T043 "Bump frontend thresholds to 53/48/45/54%"

# Launch all component test groups in parallel:
Task: T044 "Write tests for 14 settings components"
Task: T045 "Write tests for 11 board components"
Task: T046 "Write tests for 9 pipeline components"
Task: T047 "Write tests for ~19 remaining components"

# Then sequentially:
Task: T048 "Bump frontend thresholds to 60/55/52/60%"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (audit existing infrastructure)
2. Complete Phase 2: US1 — Wire advanced tests into CI
3. **STOP and VALIDATE**: Verify CI runs advanced tests on a PR
4. Immediate value: existing tests now run in CI with zero new test code

### Incremental Delivery

1. Complete Setup → Infrastructure understood
2. Add US1 (CI Foundation) → Advanced tests in CI (MVP!)
3. Add US2 (Backend 80%) → Backend coverage raised, threshold enforced
4. Add US3 (Frontend 60/55/52/60%) → Frontend coverage raised, threshold enforced
5. Add US4 (Production-Parity) → Hidden bugs surfaced
6. Add US5 (Architecture) → Structural regression prevented
7. Add US6 (Flaky Detection) → CI reliability improved
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team reviews Setup (Phase 1) together
2. Once Setup is understood:
   - Developer A: US1 (CI Foundation) + US6 (Flaky Detection)
   - Developer B: US2 (Backend Coverage — 8 test files in parallel)
   - Developer C: US3 (Frontend Coverage — schemas + hooks in parallel)
   - Developer D: US4 (Production-Parity) + US5 (Architecture Fitness)
3. Stories complete and integrate independently
4. Ratchet thresholds bumped as each story's tests merge

---

## Notes

- [P] tasks = different files, no dependencies — safe to run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Coverage thresholds follow ratchet pattern: only increase, never decrease (FR-027)
- Advanced tests start non-blocking, transition to blocking after stabilization
- Mutation testing is weekly (not per-PR) to stay within CI budget (FR-029)
- All new tests must follow existing fixture/pattern conventions (research.md RT-001, RT-002)
- CI budget constraints: backend ≤+90s, frontend ≤+60s across all phases (FR-029)
