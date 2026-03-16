# Tasks: Increase Test Coverage & Surface Unknown Bugs

**Input**: Design documents from `/specs/048-test-coverage-bugs/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests ARE the feature deliverable — every phase produces test files, CI configuration, or coverage threshold updates. This is explicitly a test-writing feature.

**Organization**: Tasks grouped by user story (11 stories from spec.md, P1–P11). Each story can be implemented and tested independently after Setup and Foundational phases complete. Stories are ordered by execution priority (not story number) per the plan's recommended order.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks in this phase)
- **[Story]**: Which user story this task belongs to (US1–US11)
- All paths are relative to repository root

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`
- **CI**: `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structures, install new dev dependencies, and prepare the project for all test-writing phases.

- [ ] T001 Create backend architecture test directory `solune/backend/tests/architecture/` with `__init__.py`
- [ ] T002 [P] Add `freezegun>=1.4` to dev dependencies in `solune/backend/pyproject.toml` `[project.optional-dependencies] dev` section
- [ ] T003 [P] Create backend integration test directory `solune/backend/tests/integration/` with `__init__.py` (if not existing)
- [ ] T004 [P] Create frontend architecture test directory `solune/frontend/src/__tests__/architecture/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Verify existing CI infrastructure and test fixtures are ready. MUST complete before ANY user story can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T005 Verify backend conftest.py fixtures (`client`, `mock_db`, `mock_session`, `mock_github_service`, `mock_github_auth_service`, `mock_ai_agent_service`) are importable and functional by running `pytest solune/backend/tests/unit/ -x --co -q` from repository root
- [ ] T006 [P] Verify frontend test infrastructure (`src/test/setup.ts`, `src/test/factories/`, `src/test/utils/`) is intact by running `npx vitest --run --reporter=verbose 2>&1 | head -20` from `solune/frontend/`
- [ ] T007 [P] Verify Hypothesis CI profile is configured in `solune/backend/tests/property/conftest.py` with 200 examples for the `ci` profile

**Checkpoint**: Foundation ready — user story implementation can now begin. Stories can proceed in parallel or sequentially in the recommended execution order.

---

## Phase 3: User Story 1 — Promote Existing Advanced Tests to CI (Priority: P1) 🎯 MVP

**Goal**: Promote existing local-only property-based, fuzz, chaos, and concurrency tests into CI. Add scheduled mutation testing. Zero new test code — only CI configuration changes. Delivers immediate bug-finding capability on every PR.

**Independent Test**: Trigger a CI run and verify the new "Backend Advanced Tests" job appears, runs all advanced test directories, and the mutation testing workflow is available for manual dispatch.

### Implementation for User Story 1

- [ ] T008 [US1] Add `backend-advanced-tests` job to `.github/workflows/ci.yml` that runs `pytest tests/property/ --timeout=120 -v` with `HYPOTHESIS_PROFILE=ci`, `pytest tests/fuzz/ --timeout=120 -v`, `pytest tests/chaos/ --timeout=120 -v`, and `pytest tests/concurrency/ --timeout=120 -v` as separate steps (working-directory: `solune/backend`), per contract in `specs/048-test-coverage-bugs/contracts/ci-advanced-tests.md`
- [ ] T009 [P] [US1] Verify frontend fuzz tests in `solune/frontend/src/__tests__/fuzz/` are discovered by Vitest by running `npx vitest --run --reporter=verbose 2>&1 | grep -i fuzz` from `solune/frontend/`; if excluded, update `include` glob in `solune/frontend/vitest.config.ts`
- [ ] T010 [P] [US1] Create `.github/workflows/mutation.yml` with weekly schedule (cron: `0 3 * * 1`), `workflow_dispatch` trigger, backend job running `mutmut run --paths-to-mutate=src/services/ --tests-dir=tests/ --no-progress` (working-directory: `solune/backend`), and frontend job running `npm run test:mutate` (working-directory: `solune/frontend`), uploading results as artifacts with 30-day retention, per contract in `specs/048-test-coverage-bugs/contracts/ci-mutation.md`
- [ ] T011 [US1] Verify known xfail tests in `solune/backend/tests/concurrency/` (interleaving and polling race tests) do not block CI by running `pytest solune/backend/tests/concurrency/ -v` and confirming `[XFAIL]` markers appear without build failure

**Checkpoint**: CI now runs advanced tests on every PR and mutation testing is scheduled weekly. SC-004, SC-005, SC-006 are achievable. This phase requires zero new test code.

---

## Phase 4: User Story 2 — Backend Coverage: GitHub Integration Layer, 69% → 74% (Priority: P2)

**Goal**: Write tests for the 9 untested GitHub integration modules — the single largest coverage gap. Mock the external API client, verify request construction, response transformation, and error paths. Backend line coverage increases to ~74%.

**Independent Test**: Run `pytest solune/backend/tests/unit/test_graphql.py solune/backend/tests/unit/test_issues.py solune/backend/tests/unit/test_pull_requests.py solune/backend/tests/unit/test_repository.py solune/backend/tests/unit/test_branches.py solune/backend/tests/unit/test_copilot.py solune/backend/tests/unit/test_identities.py solune/backend/tests/unit/test_projects.py solune/backend/tests/unit/test_board.py -v` and verify all pass. Then run `pytest --cov=src --cov-report=term-missing` and verify line coverage ≥74%.

### Implementation for User Story 2

- [ ] T012 [P] [US2] Create tests for `graphql.py` in `solune/backend/tests/unit/test_graphql.py`: mock githubkit client, assert query variables and response transformation, cover rate-limit error path, cover timeout error path. Template: `test_github_projects_service.py`. Target: ≥80% line coverage for `graphql.py`
- [ ] T013 [P] [US2] Create tests for `issues.py` in `solune/backend/tests/unit/test_issues.py`: mock REST client, verify CRUD operations, status transitions, label operations, cover 404 response, cover 429 response. Template: `test_github_projects_service.py`. Target: ≥80% line coverage for `issues.py`
- [ ] T014 [P] [US2] Create tests for `pull_requests.py` in `solune/backend/tests/unit/test_pull_requests.py`: mock REST client, verify CRUD operations, review operations, cover 404/429 responses. Template: `test_github_projects_service.py`. Target: ≥80% line coverage for `pull_requests.py`
- [ ] T015 [P] [US2] Create tests for `repository.py` in `solune/backend/tests/unit/test_repository.py`: mock REST client, verify repository metadata retrieval, cover error responses. Template: `test_github_projects_service.py`. Target: ≥80% line coverage for `repository.py`
- [ ] T016 [P] [US2] Create tests for `branches.py` in `solune/backend/tests/unit/test_branches.py`: mock client, verify API path and parameter correctness, cover error responses. Target: ≥70% line coverage for `branches.py`
- [ ] T017 [P] [US2] Create tests for `copilot.py` in `solune/backend/tests/unit/test_copilot.py`: mock client, verify API path and parameter correctness, cover error responses. Target: ≥70% line coverage for `copilot.py`
- [ ] T018 [P] [US2] Create tests for `identities.py` in `solune/backend/tests/unit/test_identities.py`: mock client, verify API path and parameter correctness, cover error responses. Target: ≥70% line coverage for `identities.py`
- [ ] T019 [P] [US2] Create tests for `projects.py` in `solune/backend/tests/unit/test_projects.py`: mock client, verify API path and parameter correctness, cover error responses. Target: ≥70% line coverage for `projects.py`
- [ ] T020 [P] [US2] Create tests for `board.py` in `solune/backend/tests/unit/test_board.py`: mock client, verify API path and parameter correctness, cover error responses. Target: ≥70% line coverage for `board.py`
- [ ] T021 [US2] Create tests for `agents.py` (github_projects) in `solune/backend/tests/unit/test_github_agents.py`: test agent GitHub resolution logic. Target: ≥70% line coverage
- [ ] T022 [US2] Bump backend CI coverage threshold from 69 to 74 in `solune/backend/pyproject.toml` `[tool.coverage.run] fail_under` after all Phase 4 tests pass

**Checkpoint**: All 9 GitHub integration modules plus agents.py are tested. Backend line coverage ≥74%. CI threshold ratcheted. FR-001, SC-013 (GitHub layer) verified.

---

## Phase 5: User Story 3 — Backend Coverage: Polling, Services & API Routes, 74% → 78% (Priority: P3)

**Goal**: Test the 4 untested polling modules, 6+ untested services, and 4 untested API routes. Backend coverage reaches ~78%.

**Independent Test**: Run all new test files from this phase and verify they pass. Then run `pytest --cov=src --cov-report=term-missing` and verify line coverage ≥78%.

### Implementation for User Story 3

#### Polling Modules

- [ ] T023 [P] [US3] Create tests for `copilot_polling/state.py` in `solune/backend/tests/unit/test_polling_state.py`: test rate-limit tier logic (≤50: pause, ≤100: skip expensive, ≤200: warn), adaptive interval math, state predicates. Target: ≥80% line coverage
- [ ] T024 [P] [US3] Create tests for `copilot_polling/pipeline.py` in `solune/backend/tests/unit/test_polling_pipeline.py`: test pipeline processing logic, state transitions. Target: ≥80% line coverage
- [ ] T025 [P] [US3] Create tests for `copilot_polling/state_validation.py` in `solune/backend/tests/unit/test_state_validation.py`: test state validation predicates, boundary conditions. Target: ≥80% line coverage
- [ ] T026 [P] [US3] Create tests for `copilot_polling/helpers.py` in `solune/backend/tests/unit/test_polling_helpers.py`: test helper utility functions. Target: ≥80% line coverage

#### High-Value Services

- [ ] T027 [P] [US3] Create tests for `metadata_service.py` in `solune/backend/tests/unit/test_metadata_service.py`: test label caching, metadata retrieval. Template: `test_pipeline_state_store.py` (in-memory SQLite + fixture). Target: ≥75% line coverage
- [ ] T028 [P] [US3] Create tests for `guard_service.py` in `solune/backend/tests/unit/test_guard_service.py`: test policy enforcement logic, authorization checks. Template: `test_pipeline_state_store.py`. Target: ≥75% line coverage
- [ ] T029 [P] [US3] Create tests for `chat_store.py` in `solune/backend/tests/unit/test_chat_store.py`: test message persistence, retrieval, deletion using in-memory SQLite fixture. Template: `test_pipeline_state_store.py`. Target: ≥75% line coverage

#### Integration-Point Services

- [ ] T030 [P] [US3] Create tests for `app_service.py` in `solune/backend/tests/unit/test_app_service.py`: test app service logic, registration, retrieval. Target: ≥75% line coverage
- [ ] T031 [P] [US3] Create tests for `signal_delivery.py` in `solune/backend/tests/unit/test_signal_delivery.py`: test signal delivery logic, retry behavior. Target: ≥75% line coverage
- [ ] T032 [P] [US3] Create tests for `github_commit_workflow.py` in `solune/backend/tests/unit/test_github_commit_workflow.py`: test commit workflow orchestration. Target: ≥75% line coverage
- [ ] T033 [P] [US3] Create tests for `signal_bridge.py` in `solune/backend/tests/unit/test_signal_bridge.py`: test WebSocket message bridging logic. Target: ≥75% line coverage

#### Remaining Services

- [ ] T034 [P] [US3] Create tests for `chores/template_builder.py` in `solune/backend/tests/unit/test_template_builder.py`: test template construction logic. Target: ≥70% line coverage
- [ ] T035 [P] [US3] Create tests for `chores/chat.py` in `solune/backend/tests/unit/test_chores_chat.py`: test chore chat logic. Target: ≥70% line coverage
- [ ] T036 [P] [US3] Create tests for `tools/presets.py` in `solune/backend/tests/unit/test_tools_presets.py`: test tool preset retrieval, validation. Target: ≥70% line coverage
- [ ] T037 [P] [US3] Create tests for `pipelines/service.py` in `solune/backend/tests/unit/test_pipelines_service.py`: test pipeline service operations. Target: ≥70% line coverage
- [ ] T038 [P] [US3] Create tests for `workflow_orchestrator/models.py` in `solune/backend/tests/unit/test_workflow_orchestrator_models.py`: test orchestrator model validation, serialization. Target: ≥70% line coverage

#### API Routes

- [ ] T039 [P] [US3] Create tests for `api/apps.py` in `solune/backend/tests/unit/test_api_apps.py`: test app route handlers using `client` fixture and dependency override pattern. Template: `test_api_chat.py`. Target: ≥75% line coverage
- [ ] T040 [P] [US3] Create tests for `api/cleanup.py` in `solune/backend/tests/unit/test_api_cleanup.py`: test cleanup route handlers. Template: `test_api_chat.py`. Target: ≥75% line coverage
- [ ] T041 [P] [US3] Create tests for `api/metadata.py` in `solune/backend/tests/unit/test_api_metadata.py`: test metadata route handlers. Template: `test_api_chat.py`. Target: ≥75% line coverage
- [ ] T042 [P] [US3] Create tests for `api/signal.py` in `solune/backend/tests/unit/test_api_signal.py`: test signal route handlers. Template: `test_api_chat.py`. Target: ≥75% line coverage

#### DI & Protocols

- [ ] T043 [P] [US3] Create tests for `dependencies.py` in `solune/backend/tests/unit/test_dependencies.py`: test dependency injection resolution, protocol conformance. Target: ≥70% line coverage
- [ ] T044 [P] [US3] Create tests for `protocols.py` in `solune/backend/tests/unit/test_protocols.py`: test protocol definitions, type conformance. Target: ≥70% line coverage

#### Threshold Bump

- [ ] T045 [US3] Bump backend CI coverage threshold from 74 to 78 in `solune/backend/pyproject.toml` `[tool.coverage.run] fail_under` after all Phase 5 tests pass

**Checkpoint**: Polling, services, and API routes are tested. Backend line coverage ≥78%. CI threshold ratcheted. FR-002, FR-003, FR-004, SC-013 (polling layer) verified.

---

## Phase 6: User Story 4 — Backend Coverage: Branch Coverage & Edge Cases, 78% → 80% (Priority: P4)

**Goal**: Inspect HTML coverage report for top 10 files with most uncovered branches. Add edge-case tests targeting error handlers, fallback paths, and early-return conditions. Backend reaches 80% target.

**Independent Test**: Run `pytest --cov=src --cov-report=html` and verify line coverage ≥80%. Inspect HTML report to confirm top 10 highest-uncovered-branch files have each improved by ≥15 percentage points.

### Implementation for User Story 4

- [ ] T046 [US4] Run `pytest --cov=src --cov-report=html` in `solune/backend/` and identify top 10 files with most uncovered branches from HTML report. Document findings in a comment within the first edge-case test file.
- [ ] T047 [P] [US4] Create edge-case tests for top 3 files (by uncovered branches) in `solune/backend/tests/unit/test_edge_cases_batch1.py`: inject specific exceptions to hit `except` clauses, test empty/None inputs for early returns. Target: ≥15pp branch coverage improvement per file
- [ ] T048 [P] [US4] Create edge-case tests for files 4–6 (by uncovered branches) in `solune/backend/tests/unit/test_edge_cases_batch2.py`: test with `TESTING=0` to hit CSRF/rate-limiting branches, test fallback code paths. Target: ≥15pp branch coverage improvement per file
- [ ] T049 [P] [US4] Create edge-case tests for files 7–10 (by uncovered branches) in `solune/backend/tests/unit/test_edge_cases_batch3.py`: cover remaining production-only code paths, error handlers, boundary conditions. Target: ≥15pp branch coverage improvement per file
- [ ] T050 [US4] Bump backend CI coverage threshold from 78 to 80 in `solune/backend/pyproject.toml` `[tool.coverage.run] fail_under` after all Phase 6 tests pass

**Checkpoint**: Backend line coverage reaches 80% target. FR-005, FR-006, SC-001 verified. All backend coverage goals achieved.

---

## Phase 7: User Story 5 — Frontend Coverage: Services & Hooks, 46% → 53% (Priority: P5)

**Goal**: Test 6 schema validation files, API error-handling layer, and 24 untested hooks. Highest ROI per test written — pure logic with no JSX complexity.

**Independent Test**: Run `npm run test:coverage` from `solune/frontend/` and verify statement/branch/function/line coverage reaches ≥53/48/45/54.

### Implementation for User Story 5

#### Schema Validation Tests

- [ ] T051 [P] [US5] Create tests for schema files in `solune/frontend/src/services/schemas/` — test 1 of 6 schemas: valid data passes, invalid data fails, field rename detection. New file pattern: `solune/frontend/src/services/schemas/<schema>.test.ts`. Target: ≥90% coverage per schema file
- [ ] T052 [P] [US5] Create tests for schema files 2–3 of 6 in `solune/frontend/src/services/schemas/<schema>.test.ts`: valid data acceptance, invalid data rejection, edge cases. Target: ≥90% coverage per schema
- [ ] T053 [P] [US5] Create tests for schema files 4–6 of 6 in `solune/frontend/src/services/schemas/<schema>.test.ts`: valid data acceptance, invalid data rejection, edge cases. Target: ≥90% coverage per schema

#### API Error Handling

- [ ] T054 [US5] Create tests for API error handling in `solune/frontend/src/services/api.test.ts`: mock `fetch`, verify error normalization for each HTTP status (400, 401, 403, 404, 429, 500), test auth-expired listener flow. Target: ≥80% coverage for `api.ts`

#### High-Value Hook Tests

- [ ] T055 [P] [US5] Create tests for `useMcpSettings` hook in `solune/frontend/src/hooks/useMcpSettings.test.tsx`: renderHook + mock API + waitFor pattern. Template: `useAuth.test.tsx`
- [ ] T056 [P] [US5] Create tests for `usePipelineValidation` hook in `solune/frontend/src/hooks/usePipelineValidation.test.tsx`
- [ ] T057 [P] [US5] Create tests for `usePipelineModelOverride` hook in `solune/frontend/src/hooks/usePipelineModelOverride.test.tsx`
- [ ] T058 [P] [US5] Create tests for `useAgentConfig` hook in `solune/frontend/src/hooks/useAgentConfig.test.tsx`
- [ ] T059 [P] [US5] Create tests for `useAgentTools` hook in `solune/frontend/src/hooks/useAgentTools.test.tsx`
- [ ] T060 [P] [US5] Create tests for `useAgents` hook in `solune/frontend/src/hooks/useAgents.test.tsx`
- [ ] T061 [P] [US5] Create tests for `useChores` hook in `solune/frontend/src/hooks/useChores.test.tsx`
- [ ] T062 [P] [US5] Create tests for `useCleanup` hook in `solune/frontend/src/hooks/useCleanup.test.tsx`
- [ ] T063 [P] [US5] Create tests for `useTools` hook in `solune/frontend/src/hooks/useTools.test.tsx`
- [ ] T064 [P] [US5] Create tests for `useMetadata` hook in `solune/frontend/src/hooks/useMetadata.test.tsx`
- [ ] T065 [P] [US5] Create tests for `useModels` hook in `solune/frontend/src/hooks/useModels.test.tsx`
- [ ] T066 [P] [US5] Create tests for `useApps` hook in `solune/frontend/src/hooks/useApps.test.tsx`

#### Medium Hook Tests

- [ ] T067 [P] [US5] Create tests for `useAppTheme` hook in `solune/frontend/src/hooks/useAppTheme.test.tsx`
- [ ] T068 [P] [US5] Create tests for `useSidebarState` hook in `solune/frontend/src/hooks/useSidebarState.test.tsx`
- [ ] T069 [P] [US5] Create tests for `useChatProposals` hook in `solune/frontend/src/hooks/useChatProposals.test.tsx`
- [ ] T070 [P] [US5] Create tests for `useMcpPresets` hook in `solune/frontend/src/hooks/useMcpPresets.test.tsx`
- [ ] T071 [P] [US5] Create tests for `useMentionAutocomplete` hook in `solune/frontend/src/hooks/useMentionAutocomplete.test.tsx`
- [ ] T072 [P] [US5] Create tests for `useNotifications` hook in `solune/frontend/src/hooks/useNotifications.test.tsx`
- [ ] T073 [P] [US5] Create tests for `usePipelineBoardMutations` hook in `solune/frontend/src/hooks/usePipelineBoardMutations.test.tsx`
- [ ] T074 [P] [US5] Create tests for `useRecentParentIssues` hook in `solune/frontend/src/hooks/useRecentParentIssues.test.tsx`
- [ ] T075 [P] [US5] Create tests for `useRepoMcpConfig` hook in `solune/frontend/src/hooks/useRepoMcpConfig.test.tsx`
- [ ] T076 [P] [US5] Create tests for `useUnsavedChanges` hook in `solune/frontend/src/hooks/useUnsavedChanges.test.tsx`
- [ ] T077 [P] [US5] Create tests for `useOnboarding` hook in `solune/frontend/src/hooks/useOnboarding.test.tsx`

#### Context Tests

- [ ] T078 [US5] Create tests for `RateLimitContext.tsx` in `solune/frontend/src/contexts/RateLimitContext.test.tsx`: test provider rendering, context value consumption, rate-limit state management

#### Threshold Bump

- [ ] T079 [US5] Bump frontend coverage thresholds from 46/41/38/47 to 53/48/45/54 in `solune/frontend/vitest.config.ts` `coverage.thresholds` after all Phase 7 tests pass

**Checkpoint**: Frontend services and hooks tested. Coverage reaches ≥53/48/45/54. FR-007, FR-008, FR-009 verified. Highest ROI frontend work complete.

---

## Phase 8: User Story 6 — Frontend Coverage: Components to 60% (Priority: P6)

**Goal**: Test remaining untested frontend components across settings, pipeline, board, agents, tools, chores, chat, and layout. Reach 60/55/52/60 coverage target.

**Independent Test**: Run `npm run test:coverage` and verify coverage reaches ≥60/55/52/60 after each sub-phase.

### Sub-Phase 8a: Settings, Pipeline, Board Components (→ 58%)

- [ ] T080 [P] [US6] Create tests for 14 untested settings components in `solune/frontend/src/components/settings/`: render, interaction, error states using `renderWithProviders()` + `userEvent`. Template: `SettingsSection.test.tsx`. Create `<component>.test.tsx` alongside each component. Target: ≥70% coverage for settings directory
- [ ] T081 [P] [US6] Create tests for 8 untested pipeline components in `solune/frontend/src/components/pipeline/`: graph rendering, node interactions, execution state display. Create `<component>.test.tsx` alongside each component. Focus on render-correctness assertions
- [ ] T082 [P] [US6] Create tests for 12 untested board components in `solune/frontend/src/components/board/`: BoardToolbar, CleanUp modal/history/summary, ProjectBoard, RefreshButton, agent overlays. Template: `BoardColumn.test.tsx`, `IssueCard.test.tsx`. Create `<component>.test.tsx` alongside each component
- [ ] T083 [US6] Bump frontend coverage thresholds from 53/48/45/54 to 58/53/50/59 in `solune/frontend/vitest.config.ts` `coverage.thresholds` after sub-phase 8a tests pass

### Sub-Phase 8b: Remaining Components (→ 60%)

- [ ] T084 [P] [US6] Create tests for 8 untested agents components in `solune/frontend/src/components/agents/`: cards, editors, modals. Create `<component>.test.tsx` alongside each component
- [ ] T085 [P] [US6] Create tests for 9 untested tools components in `solune/frontend/src/components/tools/`: cards, editors, toolbars. Create `<component>.test.tsx` alongside each component
- [ ] T086 [P] [US6] Create tests for 10 untested chores components in `solune/frontend/src/components/chores/`: cards, editors, modals, toolbars. Create `<component>.test.tsx` alongside each component
- [ ] T087 [P] [US6] Create tests for 6 untested chat components in `solune/frontend/src/components/chat/`: ChatInterface, ChatToolbar, FilePreviewChips, MentionAutocomplete, PipelineIndicator, SystemMessage. Create `<component>.test.tsx` alongside each component
- [ ] T088 [P] [US6] Create tests for 8 untested layout components in `solune/frontend/src/layout/`: AppLayout, AuthGate, Sidebar, TopBar, ProjectSelector, Breadcrumb, RateLimitBar. Create `<component>.test.tsx` alongside each component
- [ ] T089 [P] [US6] Create tests for remaining untested files: apps (2), help (1), onboarding (3), common (1), lib (3), utils (3). Create `<module>.test.ts(x)` alongside each file
- [ ] T090 [US6] Bump frontend coverage thresholds from 58/53/50/59 to 60/55/52/60 in `solune/frontend/vitest.config.ts` `coverage.thresholds` after all Phase 8 tests pass

**Checkpoint**: All frontend coverage targets reached. FR-010, FR-011, SC-002 verified. Coverage at 60/55/52/60.

---

## Phase 9: User Story 7 — Production-Parity Testing (Priority: P7)

**Goal**: Create integration tests that run with production-like configuration (TESTING=0, DEBUG=false, encryption enabled, webhook secrets set). Exercise code paths that are never tested in default test mode.

**Independent Test**: Run `pytest solune/backend/tests/integration/test_production_mode.py solune/backend/tests/integration/test_config_matrix.py -v` and verify all production code paths are exercised.

### Implementation for User Story 7

- [ ] T091 [US7] Create production-mode integration tests in `solune/backend/tests/integration/test_production_mode.py`: create fixture with `TESTING=0`, `DEBUG=false`, `ENCRYPTION_KEY=<generated Fernet key>`, `GITHUB_WEBHOOK_SECRET=<generated hex>`. Test auth flow under production config, test webhook signature verification (valid and invalid signatures), test CSRF protection enforcement, test rate limiting behavior. Target: exercise ≥4 production-only code paths (FR-017)
- [ ] T092 [P] [US7] Create configuration matrix tests in `solune/backend/tests/integration/test_config_matrix.py`: for every invalid env var combination that should cause startup failure (production mode + missing ENCRYPTION_KEY, production mode + missing GITHUB_WEBHOOK_SECRET, etc.), verify the correct `ValueError` is raised. For every valid combination, verify startup succeeds. Target: cover all critical env var combinations (FR-018)

**Checkpoint**: Production-only code paths are tested. SC-007 verified — at least one code path behaves differently than expected. FR-016, FR-017, FR-018 verified.

---

## Phase 10: User Story 8 — Time-Controlled Testing (Priority: P8)

**Goal**: Add time-controlled tests for 15+ temporal behaviors across backend and frontend. Use `freezegun` (backend) and `vi.useFakeTimers()` (frontend) to verify behavior at exact boundaries.

**Independent Test**: Run `pytest solune/backend/tests/unit/test_time_dependent.py -v` and relevant frontend time tests. Verify boundary behavior is tested at exact thresholds.

### Implementation for User Story 8

#### Backend Time-Controlled Tests

- [ ] T093 [US8] Create time-controlled backend tests in `solune/backend/tests/unit/test_time_dependent.py` using `freezegun`:
  - Session expiry boundary (`expire - 1s` valid, `expire + 1s` expired)
  - Rate-limit reset window behavior (frozen at `reset_at - 1s` and `reset_at + 1s`)
  - Token refresh 5-minute buffer trigger
  - Adaptive polling interval doubling on idle cycles, reset on state change, MAX cap (300s)
  - Assignment grace period (120s) boundary
  - Recovery cooldown (300s) boundary
  Target: all 6+ temporal behaviors covered at exact boundaries (FR-019, FR-021)

#### Frontend Time-Controlled Tests

- [ ] T094 [P] [US8] Create frontend time-controlled tests for WebSocket reconnection backoff in `solune/frontend/src/hooks/useRealTimeSync.test.tsx` using `vi.useFakeTimers()`: verify backoff sequence (1s, 2s, 4s... capped at 30s) (FR-020)
- [ ] T095 [P] [US8] Create frontend time-controlled tests for polling fallback interval (10s) and auto-refresh timer reset on WebSocket sync event in `solune/frontend/src/hooks/useRealTimeSync.timer.test.tsx` using `vi.useFakeTimers()`
- [ ] T096 [P] [US8] Create frontend time-controlled test for `lazyWithRetry` chunk reload loop prevention in `solune/frontend/src/lib/lazyWithRetry.test.ts` using `vi.useFakeTimers()`
- [ ] T097 [P] [US8] Create frontend time-controlled test for debounced `initial_data` reconnection (max 1×/2000ms) in `solune/frontend/src/hooks/useRealTimeSync.debounce.test.tsx` using `vi.useFakeTimers()`

**Checkpoint**: All 15+ temporal behaviors tested at exact boundaries. SC-008 verified — at least one boundary bug surfaced. FR-019, FR-020, FR-021 verified.

---

## Phase 11: User Story 9 — Architecture Fitness Functions (Priority: P9)

**Goal**: Add automated import-direction enforcement tests that prevent layer violations. Known violations captured in an allowlist that shrinks over time.

**Independent Test**: Run `pytest solune/backend/tests/architecture/test_import_rules.py -v` and `npx vitest --run src/__tests__/architecture/test_import_rules.test.ts`. Introduce a deliberate violation, verify it's caught, then remove it.

### Implementation for User Story 9

- [ ] T098 [US9] Create backend import-direction enforcement tests in `solune/backend/tests/architecture/test_import_rules.py` using Python's `ast` module:
  - Assert `services/` never imports from `api/`
  - Assert `api/` never imports from `*_store` directly
  - Assert `models/` never imports from `services/` or `api/`
  - Include known-violations allowlist (initial baseline from scanning existing code)
  Target: all 3 rules enforced (FR-022, FR-024)
- [ ] T099 [P] [US9] Create frontend dependency-direction tests in `solune/frontend/src/__tests__/architecture/test_import_rules.test.ts`:
  - Assert pages don't import other pages
  - Assert hooks don't import UI components
  - Assert utils don't import hooks
  - Include known-violations allowlist
  Target: all 3 rules enforced (FR-023, FR-024)

**Checkpoint**: Architecture boundaries enforced. SC-009 verified — deliberate violation caught, allowlist shrinks. FR-022, FR-023, FR-024 verified.

---

## Phase 12: User Story 10 — Expanded Property & Fuzz Testing (Priority: P10)

**Goal**: Expand property-based and fuzz testing to new modules with rich property opportunities: rate-limit tiers, prompt generators, webhook payloads, frontend utilities.

**Independent Test**: Run `pytest solune/backend/tests/property/ solune/backend/tests/fuzz/ -v` and frontend property tests. Verify broad input space exploration.

### Implementation for User Story 10

- [ ] T100 [P] [US10] Create property tests for polling rate-limit tier logic in `solune/backend/tests/property/test_polling_tiers.py`: generate random `remaining` values, verify correct tier selection (≤50: pause, ≤100: skip expensive, ≤200: warn), test boundary values (50/51, 100/101, 200/201). Use Hypothesis strategies. Target: FR-025
- [ ] T101 [P] [US10] Create property tests for prompt generators in `solune/backend/tests/property/test_prompt_generators.py`: test `issue_generation.py` and `task_generation.py` with random inputs (Unicode, empty strings, extreme lengths), verify prompts always contain required sections and never crash. Target: FR-026
- [ ] T102 [P] [US10] Expand webhook fuzz tests in `solune/backend/tests/fuzz/test_webhook_fuzz_expanded.py`: add coverage for `issues`, `pull_request_review`, `check_suite` event types. Verify no unhandled exceptions for any well-formed-but-unexpected payload. Target: FR-027
- [ ] T103 [P] [US10] Create frontend property tests for untested utility functions in `solune/frontend/src/utils/formatTime.property.test.ts`, `solune/frontend/src/utils/generateId.property.test.ts`, and remaining utils. Generate random inputs, verify output invariants (no crashes, consistent formatting). Template: `src/lib/utils.property.test.ts`. Target: FR-028

**Checkpoint**: Property and fuzz testing expanded to 3+ new modules. SC-010 verified — at least one edge-case bug discovered. FR-025, FR-026, FR-027, FR-028 verified.

---

## Phase 13: User Story 11 — WebSocket & Real-Time State Testing (Priority: P11)

**Goal**: Add end-to-end tests for the WebSocket lifecycle and reconnection debounce mechanism using Playwright.

**Independent Test**: Run Playwright WebSocket lifecycle test. Verify full connect → disconnect → fallback → reconnect → data-current flow.

### Implementation for User Story 11

- [ ] T104 [US11] Create Playwright WebSocket lifecycle E2E test in `solune/frontend/e2e/websocket-lifecycle.spec.ts`: connect → receive data → kill WebSocket → verify polling fallback activates → reconnect → verify data is current (not stale). Target: FR-029
- [ ] T105 [P] [US11] Create reconnection debounce test in `solune/frontend/e2e/websocket-debounce.spec.ts`: send 5 rapid reconnect events, verify only one cache invalidation fires within the 2000ms debounce window. Target: FR-030

**Checkpoint**: WebSocket lifecycle tested end-to-end. SC-011 verified — data freshness after reconnection confirmed. FR-029, FR-030 verified.

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, documentation, and CI time budget validation.

- [ ] T106 [P] Run full backend test suite `pytest --cov=src --cov-report=term-missing --durations=20` in `solune/backend/` and verify: (a) line coverage ≥80%, (b) all tests pass, (c) total suite runtime increase ≤90s from baseline (SC-012)
- [ ] T107 [P] Run full frontend test suite `npm run test:coverage` in `solune/frontend/` and verify: (a) coverage ≥60/55/52/60, (b) all tests pass, (c) total suite runtime increase ≤60s from baseline (SC-012)
- [ ] T108 Verify all CI jobs pass: backend unit tests, backend advanced tests, frontend tests. Verify mutation testing workflow is dispatchable
- [ ] T109 Run `specs/048-test-coverage-bugs/quickstart.md` verification commands to confirm all documented test commands work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 / Phase 3** (CI config): Depends on Phase 2 only — can start first (highest priority, zero new test code)
- **US2 / Phase 4** (Backend GitHub): Depends on Phase 2 — can start in parallel with US1
- **US3 / Phase 5** (Backend Polling/Services): Depends on Phase 4 completion (threshold ratchet at 74%)
- **US4 / Phase 6** (Backend Edge Cases): Depends on Phase 5 completion (threshold ratchet at 78%)
- **US5 / Phase 7** (Frontend Services/Hooks): Depends on Phase 2 — can start in parallel with backend phases
- **US6 / Phase 8** (Frontend Components): Depends on Phase 7 completion (threshold ratchet at 53/48/45/54)
- **US7 / Phase 9** (Production-Parity): Depends on Phase 2 — independent of coverage phases
- **US8 / Phase 10** (Time-Controlled): Depends on Phase 1 (freezegun install) — independent of coverage phases
- **US9 / Phase 11** (Architecture): Depends on Phase 1 (directory creation) — independent of coverage phases
- **US10 / Phase 12** (Property/Fuzz): Depends on Phase 2 — independent of coverage phases
- **US11 / Phase 13** (WebSocket E2E): Depends on Phase 2 — independent of coverage phases
- **Polish (Phase 14)**: Depends on all desired phases being complete

### User Story Independence

| Story | Can Start After | Depends On Other Stories? |
|-------|----------------|--------------------------|
| US1 (CI Config) | Phase 2 | No — only CI configuration |
| US2 (Backend GitHub) | Phase 2 | No — new test files only |
| US3 (Backend Polling) | Phase 4 (US2) | Yes — needs 74% threshold from US2 |
| US4 (Backend Edge) | Phase 5 (US3) | Yes — needs 78% threshold from US3 |
| US5 (Frontend Svc/Hooks) | Phase 2 | No — new test files only |
| US6 (Frontend Components) | Phase 7 (US5) | Yes — needs 53% thresholds from US5 |
| US7 (Production-Parity) | Phase 2 | No — independent integration tests |
| US8 (Time-Controlled) | Phase 1 | No — independent test files |
| US9 (Architecture) | Phase 1 | No — independent fitness tests |
| US10 (Property/Fuzz) | Phase 2 | No — independent test files |
| US11 (WebSocket E2E) | Phase 2 | No — independent E2E tests |

### Within Each User Story

- Tests are the deliverable — no separate "implementation before test" pattern
- Models/fixtures before service/integration tests
- Core tests before edge-case tests
- Threshold bumps ONLY after all tests in that phase pass
- Commit after each task or logical group

### Parallel Opportunities

Within Phase 4 (US2): All 10 test file tasks (T012–T021) can run in parallel — different files, no dependencies
Within Phase 5 (US3): All polling (T023–T026), service (T027–T038), API route (T039–T042), and DI (T043–T044) tasks can run in parallel
Within Phase 7 (US5): All schema (T051–T053), hook (T055–T077), and context (T078) tasks can run in parallel
Within Phase 8 (US6): All component test tasks within each sub-phase can run in parallel
Independent stories (US1, US5, US7, US8, US9, US10, US11) can all run in parallel with each other after their prerequisites are met

---

## Parallel Example: User Story 2 (Backend GitHub Integration)

```bash
# Launch all test files in parallel (different files, no dependencies):
Task T012: "Create tests for graphql.py in tests/unit/test_graphql.py"
Task T013: "Create tests for issues.py in tests/unit/test_issues.py"
Task T014: "Create tests for pull_requests.py in tests/unit/test_pull_requests.py"
Task T015: "Create tests for repository.py in tests/unit/test_repository.py"
Task T016: "Create tests for branches.py in tests/unit/test_branches.py"
Task T017: "Create tests for copilot.py in tests/unit/test_copilot.py"
Task T018: "Create tests for identities.py in tests/unit/test_identities.py"
Task T019: "Create tests for projects.py in tests/unit/test_projects.py"
Task T020: "Create tests for board.py in tests/unit/test_board.py"
Task T021: "Create tests for agents.py in tests/unit/test_github_agents.py"
# Then sequentially:
Task T022: "Bump CI threshold to 74%"
```

## Parallel Example: User Story 5 (Frontend Services & Hooks)

```bash
# Launch all schema tests in parallel:
Task T051-T053: Schema test files (6 schemas across 3 tasks)

# Launch all hook tests in parallel:
Task T055-T077: Hook test files (23 hooks)

# Then sequentially:
Task T079: "Bump frontend thresholds to 53/48/45/54"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (CI config changes only)
4. **STOP and VALIDATE**: Verify advanced tests run in CI, mutation workflow is dispatchable
5. Deploy/demo — immediate bug-finding capability with zero new test code

### Recommended Execution Order (Maximum Impact)

1. **US1** (Phase 3) — Promote advanced tests to CI. Zero new code, maximum immediate value.
2. **US2** (Phase 4) — Backend GitHub layer. Highest line-count gap, straightforward mocking.
3. **US5** (Phase 7) — Frontend services + hooks. Pure logic, no JSX complexity.
4. **US7** (Phase 9) — Production-mode tests. Security-critical untested code paths.
5. **US8** (Phase 10) — Time-controlled tests. 15+ temporal behaviors with zero coverage.
6. **US3** (Phase 5) → **US4** (Phase 6) → **US6** (Phase 8) → **US9** (Phase 11) → **US10** (Phase 12) → **US11** (Phase 13)

### Incremental Delivery

1. Phase 1 + 2 → Foundation ready
2. US1 → Advanced tests in CI → Bug-finding on every PR (MVP!)
3. US2 → Backend 74% → Ratchet threshold
4. US3 → Backend 78% → Ratchet threshold
5. US4 → Backend 80% → Final backend target achieved
6. US5 → Frontend 53% → Ratchet threshold
7. US6 → Frontend 60% → Final frontend target achieved
8. US7–US11 → Bug-surfacing capabilities added incrementally
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (CI config) then US2 (backend GitHub) then US3 → US4
   - Developer B: US5 (frontend services/hooks) then US6 (frontend components)
   - Developer C: US7 (production-parity) + US8 (time-controlled) + US9 (architecture)
   - Developer D: US10 (property/fuzz) + US11 (WebSocket E2E)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable (with noted exceptions for sequential threshold ratcheting in US2→US3→US4 and US5→US6)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Ratchet, don't aspirate** — Set thresholds at actual coverage, never at a goal
- **Follow existing patterns** — Every test category has templates. Match them structurally
- **Highest ROI first** — Services/hooks/utils yield more coverage per test than UI components
- **Promote before writing** — Moving existing local-only tests into CI catches bugs with zero new code
- All new tests must respect CI time budget: backend ≤90s increase, frontend ≤60s increase (SC-012)
- All advanced tests must respect 120-second per-test timeout in CI
