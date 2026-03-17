# Tasks: Comprehensive Test Coverage to 90%+

**Input**: Design documents from `/specs/050-comprehensive-test-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: This feature is inherently about testing — test tasks are explicitly requested across all user stories.

**Organization**: Tasks are grouped by user story (mapped from spec.md user stories US1–US8) to enable independent implementation and testing of each story. Phases from plan.md map directly to user stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/` (Python/FastAPI), `solune/frontend/` (TypeScript/React)
- **CI/CD**: `.github/workflows/`
- **Scripts**: `solune/scripts/`
- **Repo root**: `.coverage-baseline.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing tooling works and establish project-wide baseline before any coverage work begins.

- [ ] T001 Verify backend test suite runs cleanly with `cd solune/backend && pytest --cov=src --cov-report=term-missing` and record current line coverage
- [ ] T002 [P] Verify frontend test suite runs cleanly with `cd solune/frontend && npx vitest run --coverage` and record current coverage metrics
- [ ] T003 [P] Verify E2E suite runs cleanly with `cd solune/frontend && npx playwright test` and record current test count

---

## Phase 2: Foundational — CI Coverage Ratchet (Blocking Prerequisites)

**Purpose**: Establish regression protection infrastructure that MUST be complete before ANY test-writing story can safely begin. Maps to **User Story 1 — CI Coverage Ratchet Prevents Regression (P1)**.

**⚠️ CRITICAL**: No user story work (Phases 3–9) can begin until this phase is complete. The ratchet ensures all subsequent coverage improvements are permanently locked in.

- [ ] T004 Create `.coverage-baseline.json` at repository root with current backend and frontend metrics per schema in `specs/050-comprehensive-test-coverage/contracts/coverage-baseline-schema.md`
- [ ] T005 Add backend coverage ratchet step to `.github/workflows/ci.yml` after pytest step — compare `coverage.xml` against `.coverage-baseline.json` per contract in `specs/050-comprehensive-test-coverage/contracts/ci-pipeline-steps.md`
- [ ] T006 Add frontend coverage ratchet step to `.github/workflows/ci.yml` after vitest step — compare `coverage/coverage-summary.json` against `.coverage-baseline.json` per contract in `specs/050-comprehensive-test-coverage/contracts/ci-pipeline-steps.md`
- [ ] T007 Create `solune/scripts/update-coverage-baseline.sh` that reads current coverage reports, validates no regression, writes updated `.coverage-baseline.json`, and prints diff (exit codes: 0=success, 1=regression, 2=missing files)
- [ ] T008 [P] Add backend diff-cover step to `.github/workflows/ci.yml` — install `diff-cover`, run on `coverage.xml` against `origin/${{ github.base_ref }}`, `continue-on-error: true`
- [ ] T009 [P] Add frontend diff-cover step to `.github/workflows/ci.yml` — run on `coverage/cobertura-coverage.xml` against `origin/${{ github.base_ref }}`, `continue-on-error: true`
- [ ] T010 Bump backend `fail_under` from 71 to 75 in `solune/backend/pyproject.toml` under `[tool.coverage.report]`
- [ ] T011 [P] Bump frontend coverage thresholds to current-minus-1% in `solune/frontend/vitest.config.ts` under `coverage.thresholds`
- [ ] T012 [P] Create `solune/backend/scripts/detect_flaky.py` — reruns test suite with `--count=5` (pytest-repeat), identifies inconsistent results, outputs `flaky-report.json`
- [ ] T013 [P] Add nightly flaky detection workflow in `.github/workflows/flaky-detection.yml` per contract in `specs/050-comprehensive-test-coverage/contracts/ci-pipeline-steps.md`
- [ ] T014 [P] Configure `@pytest.mark.flaky` marker in `solune/backend/pyproject.toml` under `[tool.pytest.ini_options]` markers list

**Checkpoint**: CI ratchet active — any PR that reduces coverage now fails. Diff-cover reports untested new code. Flaky detection runs nightly.

---

## Phase 3: User Story 2 — Backend Coverage 90%+ (Priority: P1) 🎯 MVP

**Goal**: Raise backend line coverage from 71% → 85% (intermediate) → 90% (final) by filling service-layer gaps, adding API error-path tests, and creating integration workflow tests.

**Independent Test**: Run `cd solune/backend && pytest --cov=src --cov-report=term-missing` → verify ≥85% line coverage at checkpoint, ≥90% at Phase 9 final lock.

### Service Layer Gap Fill

- [ ] T015 [P] [US2] Create `solune/backend/tests/unit/test_github_commit_workflow.py` — test all public functions in `src/services/github_commit_workflow.py` (happy path + error paths)
- [ ] T016 [P] [US2] Create `solune/backend/tests/unit/test_signal_bridge.py` — test all public functions in `src/services/signal_bridge.py` (happy path + error paths, use `mock_db` fixture)
- [ ] T017 [P] [US2] Create `solune/backend/tests/unit/test_signal_chat.py` — test all public functions in `src/services/signal_chat.py` (happy path + error paths)
- [ ] T018 [P] [US2] Create `solune/backend/tests/unit/test_signal_delivery.py` — test all public functions in `src/services/signal_delivery.py` (happy path + error paths)
- [ ] T019 [P] [US2] Expand `solune/backend/tests/unit/test_ai_agent.py` — add tests for all provider paths (OpenAI, Anthropic, Ollama fallback), streaming error recovery, and timeout handling
- [ ] T020 [P] [US2] Expand `solune/backend/tests/unit/test_tools_service.py` — add tests for all public functions in `src/services/tools/service.py` (tool registration, invocation, error handling)
- [ ] T021 [P] [US2] Expand `solune/backend/tests/unit/test_workflow_orchestrator.py` — add tests for ALL state transitions in `src/services/workflow_orchestrator/` (pending→running→complete, pending→running→failed, cancel from any state)

### API Error-Path Matrix

- [ ] T022 [US2] Add parameterized error-path tests to ALL `solune/backend/tests/unit/test_api_*.py` files — each endpoint must cover status codes 200, 401, 403, 404, 422, 429, 500 per pattern in `specs/050-comprehensive-test-coverage/contracts/test-conventions.md`

### Integration Workflow Tests

- [ ] T023 [P] [US2] Create `solune/backend/tests/integration/test_pipeline_lifecycle.py` — test full pipeline creation → configuration → execution → completion cycle using `mock_db` with real SQLite
- [ ] T024 [P] [US2] Create `solune/backend/tests/integration/test_chat_flow.py` — test chat message dispatch → processing → response cycle end-to-end
- [ ] T025 [P] [US2] Create `solune/backend/tests/integration/test_webhook_processing.py` — test webhook receipt → validation → processing → side-effect cycle

### Threshold Bump

- [ ] T026 [US2] Bump backend `fail_under` to 85 in `solune/backend/pyproject.toml` under `[tool.coverage.report]`
- [ ] T027 [US2] Run `bash solune/scripts/update-coverage-baseline.sh` to update `.coverage-baseline.json` with new backend metrics

**Checkpoint**: `pytest --cov=src` reports ≥85%. Every API test file covers ≥6 of 7 status codes. Integration tests validate pipeline, chat, and webhook flows.

---

## Phase 4: User Story 3 — Frontend Coverage 90%+ (Priority: P1)

**Goal**: Raise frontend statement coverage from 49% → 80% (intermediate) → 90% (final) by expanding hook branch coverage, adding ~30 component tests, and hardening service/schema tests.

**Independent Test**: Run `cd solune/frontend && npx vitest run --coverage` → verify ≥80% statements, ≥75% branches at checkpoint.

### Hook Branch Coverage Expansion

- [ ] T028 [P] [US3] Expand all 44 hook test files in `solune/frontend/src/hooks/*.test.tsx` — add error state tests (API failure, network error, timeout) for each hook
- [ ] T029 [P] [US3] Expand all 44 hook test files in `solune/frontend/src/hooks/*.test.tsx` — add loading state tests (initial load, refetch, background update) for each hook
- [ ] T030 [P] [US3] Expand all 44 hook test files in `solune/frontend/src/hooks/*.test.tsx` — add empty/null edge case tests (empty array, null response, undefined fields) for each hook
- [ ] T031 [P] [US3] Expand all 44 hook test files in `solune/frontend/src/hooks/*.test.tsx` — add cache invalidation tests (mutation triggers, stale data, optimistic updates) for each hook
- [ ] T032 [US3] Deep-dive priority hooks: expand `solune/frontend/src/hooks/useChat.test.tsx`, `useWorkflow.test.tsx`, `usePipelineConfig.test.tsx`, `useAgentConfig.test.tsx`, `useApps.test.tsx` — add race condition, retry, and complex interaction tests

### Component Coverage — High Priority (Interactive)

- [ ] T033 [P] [US3] Create `solune/frontend/src/components/TopBar.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T034 [P] [US3] Create `solune/frontend/src/components/Sidebar.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T035 [P] [US3] Create `solune/frontend/src/components/AppLayout.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T036 [P] [US3] Create `solune/frontend/src/components/ProjectSelector.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T037 [P] [US3] Create `solune/frontend/src/components/ChatInterface.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T038 [P] [US3] Create `solune/frontend/src/components/ChatToolbar.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T039 [P] [US3] Create `solune/frontend/src/components/BoardToolbar.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T040 [P] [US3] Create `solune/frontend/src/components/CleanUpConfirmModal.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T041 [P] [US3] Create tests for all settings sub-components in `solune/frontend/src/components/settings/*.test.tsx` — render → interact → assert + `expectNoA11yViolations()`

### Component Coverage — Medium Priority

- [ ] T042 [P] [US3] Create `solune/frontend/src/components/ChoreCard.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T043 [P] [US3] Create `solune/frontend/src/components/ChoreInlineEditor.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T044 [P] [US3] Create `solune/frontend/src/components/AgentPresetSelector.test.tsx` — render → interact → assert + `expectNoA11yViolations()`
- [ ] T045 [P] [US3] Create `solune/frontend/src/components/RateLimitBar.test.tsx` — render → interact → assert + `expectNoA11yViolations()`

### Service & Schema Hardening

- [ ] T046 [US3] Expand `solune/frontend/src/services/api.test.ts` to cover every exported function — add tests for all API client methods not currently tested
- [ ] T047 [P] [US3] Add negative tests to all `solune/frontend/src/lib/schemas/*.test.ts` files — malformed payloads, missing required fields, type coercion attempts

### Threshold Bump

- [ ] T048 [US3] Bump frontend thresholds to 80/75/70/80 (statements/branches/functions/lines) in `solune/frontend/vitest.config.ts`
- [ ] T049 [US3] Run `bash solune/scripts/update-coverage-baseline.sh` to update `.coverage-baseline.json` with new frontend metrics

**Checkpoint**: `npx vitest run --coverage` reports ≥80% statements, ≥75% branches. Every component test includes `expectNoA11yViolations()`. Schema tests include negative cases.

---

## Phase 5: User Story 4 — Mutation Testing Validates Test Quality (Priority: P2)

**Goal**: Expand mutation testing scope and set enforced score thresholds to validate that tests genuinely detect code changes, not just execute lines.

**Independent Test**: Run `cd solune/backend && python scripts/run_mutmut_shard.py --shard <name>` per shard → verify ≥75% mutation score. Run `cd solune/frontend && npm run test:mutate` → verify ≥60% mutation score.

### Backend Mutation Expansion

- [ ] T050 [US4] Add 3 new named shards (`api-endpoints`, `middleware`, `models`) to `solune/backend/scripts/run_mutmut_shard.py` — map `api-endpoints` → `src/api/*.py`, `middleware` → `src/middleware/*.py`, `models` → `src/models/*.py`
- [ ] T051 [US4] Update `.github/workflows/mutation.yml` matrix to include the 3 new shards (`api-endpoints`, `middleware`, `models`) alongside existing 4 shards
- [ ] T052 [US4] Run each new backend shard and verify ≥75% mutation score; write additional tests in `solune/backend/tests/unit/` to kill surviving mutants if below threshold

### Frontend Mutation Expansion

- [ ] T053 [P] [US4] Expand Stryker `mutate` array in `solune/frontend/stryker.config.mjs` to add `'src/services/**/*.ts'` and `'src/utils/**/*.ts'` (excluding test files and property test files)
- [ ] T054 [US4] Set `thresholds.break: 60` in `solune/frontend/stryker.config.mjs` to make frontend mutation score blocking
- [ ] T055 [US4] Run `npx stryker run` and verify ≥60% mutation score; write additional tests to kill surviving mutants if below threshold

### Mutant Tracking

- [ ] T056 [US4] Review surviving mutant reports from all shards — file GitHub issues for each batch of surviving mutants that indicate test gaps

**Checkpoint**: `mutmut run` per shard → ≥75% mutation score. `npx stryker run` → ≥60% mutation score (blocking). Surviving mutant issues filed.

---

## Phase 6: User Story 5 — Property-Based & Fuzz Testing (Priority: P2)

**Goal**: Add property-based tests (Hypothesis/fast-check) and fuzz tests to discover edge cases that example-based tests miss. Catches boundary conditions, malformed inputs, and invalid state transitions.

**Independent Test**: Run property and fuzz test suites and verify all pass without failures with 100+ generated examples each.

### Backend Property Tests (Hypothesis)

- [ ] T057 [P] [US5] Create `solune/backend/tests/property/test_graphql_invariants.py` — Hypothesis tests for GraphQL query construction invariants (valid queries always parse, invalid inputs rejected)
- [ ] T058 [P] [US5] Create `solune/backend/tests/property/test_state_machines.py` — Hypothesis tests for state machine transition validity in `copilot_polling` and `workflow_orchestrator` (no invalid state reachable)
- [ ] T059 [P] [US5] Create `solune/backend/tests/property/test_model_roundtrips.py` — Hypothesis tests for Pydantic model serialize → deserialize → equals round-trip on all models in `src/models/`
- [ ] T060 [P] [US5] Create `solune/backend/tests/property/test_encryption_roundtrip.py` — Hypothesis tests for encryption encrypt → decrypt → equals round-trip
- [ ] T061 [P] [US5] Create `solune/backend/tests/property/test_pipeline_config.py` — Hypothesis tests for pipeline config validation (valid configs accepted, invalid configs rejected with appropriate errors)

### Frontend Property Tests (fast-check)

- [ ] T062 [P] [US5] Create `solune/frontend/src/services/api.property.test.ts` — fast-check tests for URL construction invariants (all generated URLs are valid and well-formed)
- [ ] T063 [P] [US5] Create `solune/frontend/src/hooks/usePipelineConfig.property.test.ts` — fast-check tests for pipeline reducer state machine invariants (no invalid state reachable)
- [ ] T064 [P] [US5] Create `solune/frontend/src/lib/schemas/pipeline.property.test.ts` (and other schema files) — fast-check tests for Zod schema parse round-trip (valid data parses and re-serializes identically)
- [ ] T065 [P] [US5] Create `solune/frontend/src/lib/pipeline-migration.property.test.ts` — fast-check tests for pipeline migration idempotency (migrating twice yields same result as once)

### Backend Fuzz Tests

- [ ] T066 [P] [US5] Create `solune/backend/tests/fuzz/test_webhook_fuzz.py` — fuzz tests for webhook payloads (malformed JSON, oversized payloads, injection attempts → graceful rejection)
- [ ] T067 [P] [US5] Create `solune/backend/tests/fuzz/test_chat_injection.py` — fuzz tests for chat message injection (XSS, SQL injection, command injection → sanitized or rejected)
- [ ] T068 [P] [US5] Create `solune/backend/tests/fuzz/test_upload_fuzz.py` — fuzz tests for file upload path traversal (directory traversal, symlink attacks, null bytes → rejected)

### Frontend Fuzz Tests

- [ ] T069 [P] [US5] Create `solune/frontend/src/test/fuzz/paste-events.test.ts` — fuzz tests for paste events (malformed clipboard data, oversized pastes, binary content)
- [ ] T070 [P] [US5] Create `solune/frontend/src/test/fuzz/nested-json.test.ts` — fuzz tests for deeply nested JSON handling (stack overflow prevention, depth limits)
- [ ] T071 [P] [US5] Create `solune/frontend/src/test/fuzz/emoji-sequences.test.ts` — fuzz tests for emoji sequences (multi-byte, ZWJ sequences, skin tone modifiers → correct rendering/storage)

**Checkpoint**: All property tests pass with 100+ generated examples. All fuzz tests pass without crashes or unhandled exceptions.

---

## Phase 7: User Story 6 — E2E & Visual Regression Testing (Priority: P2)

**Goal**: Add 10 new Playwright E2E spec files and ~42 visual regression snapshots (3 viewports × 2 color modes × 7 pages) to protect complete user workflows and visual consistency.

**Independent Test**: Run `cd solune/frontend && npx playwright test` → verify all specs pass (68+ tests). Visual snapshots match baselines.

### New E2E Spec Files

- [ ] T072 [P] [US6] Create `solune/frontend/e2e/pipeline-builder.spec.ts` — test pipeline creation, step configuration, save/load, and error handling
- [ ] T073 [P] [US6] Create `solune/frontend/e2e/agent-management.spec.ts` — test agent creation, configuration, activation/deactivation, deletion
- [ ] T074 [P] [US6] Create `solune/frontend/e2e/apps-page.spec.ts` — test app listing, creation, configuration, deletion
- [ ] T075 [P] [US6] Create `solune/frontend/e2e/chores-workflow.spec.ts` — test chore creation, status transitions, scheduling, completion
- [ ] T076 [P] [US6] Create `solune/frontend/e2e/projects-page.spec.ts` — test project listing, creation, selection, board view
- [ ] T077 [P] [US6] Create `solune/frontend/e2e/tools-page.spec.ts` — test tools listing, configuration, enable/disable
- [ ] T078 [P] [US6] Create `solune/frontend/e2e/help-page.spec.ts` — test help page rendering, navigation, search
- [ ] T079 [P] [US6] Create `solune/frontend/e2e/keyboard-navigation.spec.ts` — test tab navigation, focus management, keyboard shortcuts across all pages
- [ ] T080 [P] [US6] Create `solune/frontend/e2e/dark-mode.spec.ts` — test dark mode toggle, persistence, all pages render correctly in dark mode
- [ ] T081 [P] [US6] Create `solune/frontend/e2e/error-recovery.spec.ts` — test error boundary display, retry mechanisms, navigation after errors

### E2E Fixtures Extension

- [ ] T082 [US6] Extend `solune/frontend/e2e/fixtures.ts` with mock routes for all new pages (pipeline builder, agent management, apps, chores, projects, tools, help)

### Visual Regression

- [ ] T083 [US6] Add `toHaveScreenshot()` assertions to E2E specs for every major page at 3 viewports (mobile: 375×667, tablet: 768×1024, desktop: 1280×720) × 2 color modes (light/dark) — approximately 42 new snapshots per `specs/050-comprehensive-test-coverage/contracts/test-conventions.md`

### E2E Stabilization

- [ ] T084 [US6] Track E2E test stability for 2+ consecutive weeks of zero flaky failures — document stability window in CI monitoring
- [ ] T085 [US6] After stability confirmed: remove `continue-on-error: true` from E2E step in `.github/workflows/ci.yml` to make E2E tests blocking

**Checkpoint**: `npx playwright test` → all specs pass (68+ tests). Visual snapshots match baselines. E2E blocking after stabilization.

---

## Phase 8: User Story 7 — Contract & Integration Testing (Priority: P3)

**Goal**: Validate system boundaries through schema-driven contract testing (schemathesis) and expanded integration tests covering database migrations, WebSocket, rate limiting, guards, and scheduling.

**Independent Test**: Run `bash solune/scripts/validate-contracts.sh` → passes with schemathesis and response body validation.

### Schemathesis Integration

- [ ] T086 [US7] Integrate schemathesis for auto-generated API test cases from `openapi.json` — add as CI step in `.github/workflows/ci.yml` or dedicated workflow

### Integration Test Expansion

- [ ] T087 [P] [US7] Create `solune/backend/tests/integration/test_db_migrations.py` — test database migration correctness (up/down, idempotency, data preservation)
- [ ] T088 [P] [US7] Create `solune/backend/tests/integration/test_websocket_lifecycle.py` — test WebSocket connect → message → disconnect lifecycle
- [ ] T089 [P] [US7] Create `solune/backend/tests/integration/test_rate_limiting.py` — test rate limiting end-to-end (requests within limit succeed, excess requests get 429)
- [ ] T090 [P] [US7] Create `solune/backend/tests/integration/test_guard_config.py` — test guard config validation (valid configs accepted, invalid rejected with clear errors)
- [ ] T091 [P] [US7] Create `solune/backend/tests/integration/test_chore_scheduling.py` — test chore scheduling cycle (create → schedule → trigger → complete)

### Contract Script Enhancement

- [ ] T092 [US7] Enhance `solune/scripts/validate-contracts.sh` with response body validation — validate response bodies match documented schema, not just status codes

**Checkpoint**: `bash solune/scripts/validate-contracts.sh` passes with schemathesis. All integration tests pass.

---

## Phase 9: User Story 8 — Flaky Test Management (Priority: P3) + User Story 1 Final Lock

**Goal**: Establish flaky test management processes and lock all coverage thresholds at final targets. This is the final phase that depends on all prior phases being complete.

**Independent Test**: Run all verification commands from spec. Verify max 5 quarantined flaky tests. Verify ratchet prevents any threshold decrease.

### Flaky Test Management

- [ ] T093 [US8] Review `flaky-report.json` output from nightly runs — mark identified flaky tests with `@pytest.mark.flaky` (backend) or `test.fixme()` (frontend)
- [ ] T094 [US8] Verify quarantined test count ≤5 — resolve or remove tests quarantined >30 days

### Final Coverage Push

- [ ] T095 Run `cd solune/backend && pytest --cov=src --cov-report=term-missing` — identify ALL uncovered lines and write tests or justify `# pragma: no cover` for each
- [ ] T096 [P] Run `cd solune/frontend && npx vitest run --coverage` — identify ALL uncovered lines and write tests or justify exclusions for each

### Lock Final Thresholds

- [ ] T097 Lock backend `fail_under: 90` in `solune/backend/pyproject.toml` under `[tool.coverage.report]`
- [ ] T098 Lock frontend thresholds `{ statements: 90, branches: 85, functions: 85, lines: 90 }` in `solune/frontend/vitest.config.ts`
- [ ] T099 Run `bash solune/scripts/update-coverage-baseline.sh` to update `.coverage-baseline.json` with final locked values

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Maintenance processes and documentation that affect all user stories.

- [ ] T100 [P] Add PR template checklist item for test coverage in `.github/pull_request_template.md` — "New/changed code includes appropriate test coverage"
- [ ] T101 [P] Create `solune/scripts/audit-coverage.sh` — monthly per-file audit script that identifies files with coverage below team threshold
- [ ] T102 Verify all `# pragma: no cover` annotations are limited to `__main__` guards, `TYPE_CHECKING` blocks, and platform-specific code — document justifications
- [ ] T103 Run full verification suite per spec: `pytest --cov=src` ≥90%, `npx vitest run --coverage` ≥90/85/85/90, `npx playwright test` 68+ tests, `mutmut run` ≥75%, `npx stryker run` ≥60%, `validate-contracts.sh` passes
- [ ] T104 Run `bash solune/scripts/update-coverage-baseline.sh` final time to commit definitive `.coverage-baseline.json`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational / CI Ratchet (Phase 2)**: Depends on Setup — BLOCKS all user story phases
- **Backend Coverage US2 (Phase 3)**: Depends on Phase 2 — can run parallel with Phase 4
- **Frontend Coverage US3 (Phase 4)**: Depends on Phase 2 — can run parallel with Phase 3
- **Mutation Testing US4 (Phase 5)**: Depends on Phases 3 AND 4 (need sufficient tests before measuring mutation quality)
- **Property & Fuzz US5 (Phase 6)**: Depends on Phase 2 — can run parallel with Phases 3–4
- **E2E & Visual US6 (Phase 7)**: Depends on Phase 2 — can run parallel with Phases 3–4
- **Contract & Integration US7 (Phase 8)**: Depends on Phase 2 — can run parallel with Phases 3–4
- **Flaky Mgmt US8 + Final Lock (Phase 9)**: Depends on ALL prior phases
- **Polish (Phase 10)**: Depends on Phase 9

### User Story Dependencies

- **US1 (CI Ratchet)**: Phase 2 — foundation, no dependencies on other stories
- **US2 (Backend 90%+)**: Phase 3 — depends only on US1 (ratchet must be active)
- **US3 (Frontend 90%+)**: Phase 4 — depends only on US1, parallel with US2
- **US4 (Mutation Testing)**: Phase 5 — depends on US2 + US3 (need tests before mutations)
- **US5 (Property & Fuzz)**: Phase 6 — depends only on US1, parallel with US2/US3
- **US6 (E2E & Visual)**: Phase 7 — depends only on US1, parallel with US2/US3
- **US7 (Contract & Integration)**: Phase 8 — depends only on US1, parallel with US2/US3
- **US8 (Flaky Mgmt)**: Phase 9 — depends on all prior stories for final lock-down

### Within Each User Story

- Tests written to fill gaps → coverage verified → thresholds bumped → baseline updated
- Service/model tests before integration tests
- Hook/component tests before E2E tests
- Property tests can run in parallel with unit/integration tests

### Parallel Opportunities

- **Phase 2**: T008+T009 (diff-cover steps), T011+T012+T013+T014 (config tasks)
- **Phase 3**: All service test files T015–T021 can run in parallel (different files); T023–T025 integration tests in parallel
- **Phase 4**: All hook expansion tasks T028–T031 in parallel; all component tests T033–T045 in parallel
- **Phase 5**: T050 and T053 (backend/frontend mutation expansion) in parallel
- **Phase 6**: All property test files T057–T065 in parallel; all fuzz test files T066–T071 in parallel
- **Phase 7**: All E2E spec files T072–T081 in parallel
- **Phase 8**: All integration test files T087–T091 in parallel
- **Across phases**: Phases 3+4+6+7+8 can all run in parallel after Phase 2 completes

---

## Parallel Example: User Story 2 (Backend Coverage)

```bash
# Launch all service layer gap fill tests together (different files, no dependencies):
Task T015: "Create test_github_commit_workflow.py"
Task T016: "Create test_signal_bridge.py"
Task T017: "Create test_signal_chat.py"
Task T018: "Create test_signal_delivery.py"
Task T019: "Expand test_ai_agent.py"
Task T020: "Expand test_tools_service.py"
Task T021: "Expand test_workflow_orchestrator.py"

# Then launch integration tests together:
Task T023: "Create test_pipeline_lifecycle.py"
Task T024: "Create test_chat_flow.py"
Task T025: "Create test_webhook_processing.py"

# API error matrix (T022) depends on understanding existing test files - run after review
```

## Parallel Example: User Story 3 (Frontend Coverage)

```bash
# Launch all hook expansion tasks together (different test aspects, same files but additive):
Task T028: "Error state tests for all hooks"
Task T029: "Loading state tests for all hooks"
Task T030: "Empty/null edge case tests for all hooks"
Task T031: "Cache invalidation tests for all hooks"

# Launch all component test files together (different files):
Task T033: "TopBar.test.tsx"
Task T034: "Sidebar.test.tsx"
Task T035: "AppLayout.test.tsx"
# ... through T045
```

## Parallel Example: Cross-Story Parallelism

```bash
# After Phase 2 (CI Ratchet) completes, these can ALL start simultaneously:
Phase 3 (US2 Backend): Developer A starts T015-T027
Phase 4 (US3 Frontend): Developer B starts T028-T049
Phase 6 (US5 Property/Fuzz): Developer C starts T057-T071
Phase 7 (US6 E2E): Developer D starts T072-T085
Phase 8 (US7 Contract/Integration): Developer E starts T086-T092
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup (verify current state)
2. Complete Phase 2: CI Ratchet (US1) — CRITICAL foundation
3. Complete Phase 3: Backend Coverage (US2) — highest impact
4. **STOP and VALIDATE**: `pytest --cov=src` → ≥85%, ratchet active
5. Deploy/demo — backend is protected and well-tested

### Incremental Delivery

1. Phase 1 + 2 → CI Ratchet active (immediate protection) ✅
2. Phase 3 → Backend ≥85% → bump baseline ✅
3. Phase 4 → Frontend ≥80% → bump baseline ✅
4. Phase 5 → Mutation scores enforced → quality validated ✅
5. Phase 6 → Property/fuzz tests → edge cases caught ✅
6. Phase 7 → E2E + visual regression → user experience protected ✅
7. Phase 8 → Contracts + integration → system boundaries validated ✅
8. Phase 9 → Final lock 90%/85% → permanent quality floor ✅
9. Phase 10 → Maintenance processes → sustainable long-term ✅

### Parallel Team Strategy

With multiple developers after Phase 2 is complete:

1. **All developers**: Complete Phase 1 + Phase 2 together (foundation)
2. **Once Phase 2 (CI Ratchet) is done**:
   - Developer A: Phase 3 (US2 — Backend Coverage)
   - Developer B: Phase 4 (US3 — Frontend Coverage)
   - Developer C: Phase 6 (US5 — Property & Fuzz Tests)
   - Developer D: Phase 7 (US6 — E2E & Visual Regression)
   - Developer E: Phase 8 (US7 — Contract & Integration)
3. **After Phases 3+4 complete**: Developer A+B → Phase 5 (US4 — Mutation Testing)
4. **After all complete**: Any developer → Phase 9 (Final Lock) → Phase 10 (Polish)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after Phase 2 (CI Ratchet)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Threshold bumps (T010, T026, T048, T097, T098) MUST only happen after sufficient tests pass
- Baseline updates (T027, T049, T099, T104) MUST follow every threshold bump
- `pragma: no cover` limited to `__main__` guards, `TYPE_CHECKING`, platform-specific code
- Maximum 5 quarantined flaky tests at any time
- E2E becomes blocking only after 2+ weeks of zero flaky failures
