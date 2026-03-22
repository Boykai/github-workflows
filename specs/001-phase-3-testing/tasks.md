# Tasks: Phase 3 — Testing: Coverage, Mutation Enforcement, E2E, Property-Based & Keyboard Navigation

**Input**: Design documents from `/specs/001-phase-3-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: This feature is entirely about testing — all tasks produce test files, test configuration, or CI enforcement. Tests ARE the deliverable.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories map to plan.md phases: US1→Phase A, US2→Phase B, US3→Phase C, US4→Phase G, US5→Phase D, US6→Phase E, US7→Phase F.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/` and `solune/frontend/`
- **Frontend tests**: `solune/frontend/src/hooks/`, `solune/frontend/e2e/`
- **Backend tests**: `solune/backend/tests/unit/`, `solune/backend/tests/integration/`, `solune/backend/tests/property/`
- **CI config**: `.github/workflows/`
- **Frontend config**: `solune/frontend/vitest.config.ts`, `solune/frontend/stryker.config.mjs`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup required — all testing infrastructure is already installed. This phase covers any shared test utility or configuration that multiple user stories depend on.

- [ ] T001 Verify existing test infrastructure is operational: run `npm run test:coverage` in solune/frontend/ and `pytest --co -q` in solune/backend/ to confirm baseline
- [ ] T002 [P] Review and document current coverage baselines by running `pytest --cov=src --cov-report=term-missing` in solune/backend/ and `npm run test:coverage` in solune/frontend/ (record starting numbers for SC-001 and SC-002)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blocking work is required — all user stories can proceed independently after baseline verification in Phase 1. The dependency graph allows US1 (frontend) and US2 (backend) to start in parallel immediately.

**⚠️ NOTE**: Phase 1 baseline verification should complete before user story work begins to establish metrics.

**Checkpoint**: Baseline recorded — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Frontend Coverage Enforcement (Priority: P1) 🎯 MVP

**Goal**: Raise frontend Vitest coverage thresholds from 50/44/41/50 to 75/65/65/75 in two incremental phases by testing ~6 untested hooks and 7 untested high-LOC components.

**Independent Test**: Run `npm run test:coverage` in solune/frontend/ — must pass at each threshold level (65/55/55/65, then 75/65/65/75).

**Parallel with**: User Story 2 (backend coverage) — no shared files.

### A.1 — Hook Tests (Highest ROI)

- [ ] T003 [P] [US1] Write tests for useActivityFeed hook using TanStack Query wrapper + createMockApi() pattern in solune/frontend/src/hooks/useActivityFeed.test.tsx
- [ ] T004 [P] [US1] Write tests for useBoardDragDrop hook using TanStack Query wrapper + createMockApi() pattern in solune/frontend/src/hooks/useBoardDragDrop.test.tsx
- [ ] T005 [P] [US1] Write tests for useCommandPalette hook using TanStack Query wrapper + createMockApi() pattern in solune/frontend/src/hooks/useCommandPalette.test.tsx
- [ ] T006 [P] [US1] Write tests for useEntityHistory hook using TanStack Query wrapper + createMockApi() pattern in solune/frontend/src/hooks/useEntityHistory.test.tsx
- [ ] T007 [P] [US1] Write tests for useInfiniteList hook using TanStack Query wrapper + createMockApi() pattern in solune/frontend/src/hooks/useInfiniteList.test.tsx
- [ ] T008 [P] [US1] Write tests for useUnsavedPipelineGuard hook using TanStack Query wrapper + createMockApi() pattern in solune/frontend/src/hooks/useUnsavedPipelineGuard.test.tsx

### A.2 — High-LOC Component Tests

- [ ] T009 [P] [US1] Write tests for ProjectBoard component covering primary render and interaction paths in solune/frontend/src/components/board/ProjectBoard.test.tsx
- [ ] T010 [P] [US1] Write tests for ChatInterface component covering primary render, streaming, and interaction paths in solune/frontend/src/components/chat/ChatInterface.test.tsx
- [ ] T011 [P] [US1] Write tests for CleanUpConfirmModal component covering render, confirm, and cancel flows in solune/frontend/src/components/modals/CleanUpConfirmModal.test.tsx
- [ ] T012 [P] [US1] Write tests for PipelineAnalytics component covering metrics rendering and data-driven views in solune/frontend/src/components/pipeline/PipelineAnalytics.test.tsx
- [ ] T013 [P] [US1] Write tests for MarkdownRenderer component covering markdown-to-HTML rendering edge cases in solune/frontend/src/components/common/MarkdownRenderer.test.tsx
- [ ] T014 [P] [US1] Write tests for McpSettings component covering configuration UI render and form interactions in solune/frontend/src/components/settings/McpSettings.test.tsx
- [ ] T015 [P] [US1] Write tests for WorkflowSettings component covering configuration UI render and form interactions in solune/frontend/src/components/settings/WorkflowSettings.test.tsx

### A.3 — Phase 1 Threshold Raise

- [ ] T016 [US1] Update Vitest coverage thresholds to Phase 1 levels (statements: 65, branches: 55, functions: 55, lines: 65) in solune/frontend/vitest.config.ts and verify `npm run test:coverage` passes

### A.4 — Phase 2 Threshold Raise

- [ ] T017 [US1] Update Vitest coverage thresholds to Phase 2 final levels (statements: 75, branches: 65, functions: 65, lines: 75) in solune/frontend/vitest.config.ts and verify `npm run test:coverage` passes

**Checkpoint**: Frontend coverage enforced at 75/65/65/75 — `npm run test:coverage` passes. SC-001 satisfied.

---

## Phase 4: User Story 2 — Backend Coverage Enforcement (Priority: P1)

**Goal**: Extend backend test suites to meet per-file coverage floors: board.py ≥80%, pipelines.py ≥80%, pipeline.py ≥85%, agent_creator.py ≥70%.

**Independent Test**: Run per-module pytest coverage reports — `pytest --cov=src/api/board --cov-fail-under=80`, `pytest --cov=src/api/pipelines --cov-fail-under=80`, `pytest --cov=src/services/copilot_polling/pipeline --cov-fail-under=85`, `pytest --cov=src/services/agent_creator --cov-fail-under=70` — all must pass.

**Parallel with**: User Story 1 (frontend coverage) — no shared files.

### B.1 — board.py ≥80%

- [ ] T018 [P] [US2] Extend test_api_board.py with column transform edge case tests (empty columns, reordered columns, duplicate handling) in solune/backend/tests/unit/test_api_board.py
- [ ] T019 [P] [US2] Extend test_api_board.py with rate-limit recovery tests (429 response handling, retry logic, backoff behavior) in solune/backend/tests/unit/test_api_board.py
- [ ] T020 [P] [US2] Extend test_api_board.py with token expiration and refresh flow tests in solune/backend/tests/unit/test_api_board.py
- [ ] T021 [P] [US2] Extend test_api_board.py with cache hash computation branch tests and error branch coverage in solune/backend/tests/unit/test_api_board.py

### B.2 — pipelines.py ≥80%

- [ ] T022 [P] [US2] Extend pipeline API tests with queue mode routing tests (L388-406 branches) in solune/backend/tests/unit/test_api_pipelines.py
- [ ] T023 [P] [US2] Extend pipeline API tests with position calculation logic tests in solune/backend/tests/unit/test_api_pipelines.py
- [ ] T024 [P] [US2] Extend pipeline API tests with dequeue trigger path tests in solune/backend/tests/unit/test_api_pipelines.py
- [ ] T025 [P] [US2] Extend pipeline API tests with sub-issue error handling tests in solune/backend/tests/unit/test_api_pipelines.py

### B.3 — pipeline.py ≥85%

- [ ] T026 [P] [US2] Extend copilot polling pipeline tests with _dequeue_next_pipeline() complete path coverage in solune/backend/tests/unit/test_pipeline.py (or appropriate test file for copilot_polling/pipeline.py)
- [ ] T027 [P] [US2] Extend copilot polling pipeline tests with grace period expiration and stale reclaim tests in solune/backend/tests/unit/test_pipeline.py
- [ ] T028 [P] [US2] Extend copilot polling pipeline tests with BoundedDict race condition tests in solune/backend/tests/unit/test_pipeline.py

### B.4 — agent_creator.py ≥70%

- [ ] T029 [P] [US2] Extend test_agent_creator.py with GitHub API exception path tests (network errors, API rate limits, 500 responses) in solune/backend/tests/unit/test_agent_creator.py
- [ ] T030 [P] [US2] Extend test_agent_creator.py with config parsing edge case tests (malformed YAML, missing fields, empty config) in solune/backend/tests/unit/test_agent_creator.py
- [ ] T031 [P] [US2] Extend test_agent_creator.py with tool assignment logic branch tests in solune/backend/tests/unit/test_agent_creator.py

**Checkpoint**: Backend per-file coverage floors met — all 4 targeted pytest coverage commands pass. SC-002 satisfied.

---

## Phase 5: User Story 3 — Full-Workflow Integration Test (Priority: P1)

**Goal**: Implement an end-to-end pipeline lifecycle integration test that exercises cross-module interactions from issue creation through cleanup and dequeue using httpx.ASGITransport.

**Independent Test**: Run `pytest tests/integration/test_full_workflow.py -v` in solune/backend/ — pipeline must traverse all 4 statuses (Backlog → Ready → In Progress → In Review).

**Depends on**: User Story 2 (backend coverage) should land first — integration test builds on the same backend modules.

### C.1 — Test Scaffold

- [ ] T032 [US3] Create test_full_workflow.py test scaffold using httpx.ASGITransport pattern (following test_webhook_dispatch.py) with FastAPI app including all relevant routers, HMAC webhook signing helper, and integration-level fixtures in solune/backend/tests/integration/test_full_workflow.py

### C.2 — Issue Lifecycle

- [ ] T033 [US3] Implement test case for issue creation → project add → pipeline launch → agent assignment flow in solune/backend/tests/integration/test_full_workflow.py

### C.3 — Status Transitions

- [ ] T034 [US3] Implement test case for status transitions Backlog → Ready → In Progress → In Review in solune/backend/tests/integration/test_full_workflow.py

### C.4 — PR Lifecycle

- [ ] T035 [US3] Implement test case for PR creation webhook → pipeline state update → PR merge webhook → cleanup trigger → dequeue next pipeline in solune/backend/tests/integration/test_full_workflow.py

**Checkpoint**: Full-workflow integration test passes with pipeline traversing all 4 statuses. SC-003 satisfied.

---

## Phase 6: User Story 4 — FIFO Queue Integration Tests (Priority: P2)

**Goal**: Extend queue integration tests to verify strict FIFO ordering across 3+ pipelines with real interactions.

**Independent Test**: Run `pytest tests/unit/test_queue_mode.py -v` in solune/backend/ — 3+ pipeline FIFO ordering assertions pass.

**Depends on**: User Story 2 (backend coverage) should stabilize first — queue tests build on backend queue coverage.

**Parallel with**: User Stories 5, 6, 7 (all P2 stories are independent).

### G.1 — Two-Pipeline FIFO

- [ ] T036 [US4] Extend test_queue_mode.py with two-pipeline FIFO test: Pipeline A launches → Pipeline B queued → A completes → B dequeues automatically in solune/backend/tests/unit/test_queue_mode.py

### G.2 — Three-Pipeline Strict Ordering

- [ ] T037 [US4] Extend test_queue_mode.py with three-pipeline strict FIFO ordering test: Pipelines A, B, C submitted in order → A runs, B and C queued → A completes → B starts → B completes → C starts in solune/backend/tests/unit/test_queue_mode.py

**Checkpoint**: FIFO queue ordering verified with 3+ pipelines. SC-004 satisfied.

---

## Phase 7: User Story 5 — Mutation Testing CI Enforcement (Priority: P2)

**Goal**: Make mutation testing CI jobs blocking (not informational) by setting Stryker break threshold and removing continue-on-error flags.

**Independent Test**: Verify `npx stryker run` in solune/frontend/ exits non-zero when score < 50; verify CI mutation jobs fail on low kill ratios.

**Parallel with**: User Stories 4, 6, 7 (all P2 stories are independent).

### D.1 — Stryker Threshold

- [ ] T038 [P] [US5] Set Stryker mutation score break threshold from null to 50 in solune/frontend/stryker.config.mjs (thresholds.break: 50)

### D.2 — Stryker CI

- [ ] T039 [P] [US5] Remove continue-on-error: true from the frontend-mutation job's Stryker step in .github/workflows/mutation-testing.yml

### D.3 — mutmut Aggregation

- [ ] T040 [US5] Add a new backend-mutation-check job to .github/workflows/mutation-testing.yml that: depends on all backend-mutation matrix shards (needs: [backend-mutation]), downloads all mutmut report artifacts, parses kill ratios from each shard report, and fails the workflow if any shard kill ratio < 60%

### D.4 — mutmut CI

- [ ] T041 [P] [US5] Remove continue-on-error: true from the backend-mutation job's mutmut run step in .github/workflows/mutation-testing.yml

**Checkpoint**: Mutation testing CI is blocking — exits non-zero on low kill ratios. SC-005 and SC-009 satisfied.

---

## Phase 8: User Story 6 — Property-Based Queue Tests (Priority: P2)

**Goal**: Extend property-based testing with queue-specific rules and invariants using Hypothesis RuleBasedStateMachine (≥200 examples in CI).

**Independent Test**: Run `HYPOTHESIS_PROFILE=ci pytest tests/property/ -v` in solune/backend/ — all queue rules pass across ≥200 Hypothesis examples.

**Parallel with**: User Stories 4, 5, 7 (all P2 stories are independent).

### E.1 — State Machine Queue Rules

- [ ] T042 [US6] Extend RuleBasedStateMachine in test_pipeline_state_machine.py with enqueue_pipeline rule (idle → queued when active pipeline exists for the project) in solune/backend/tests/property/test_pipeline_state_machine.py
- [ ] T043 [US6] Extend RuleBasedStateMachine with dequeue_pipeline rule (queued → running when no active pipeline for the project) in solune/backend/tests/property/test_pipeline_state_machine.py
- [ ] T044 [US6] Extend RuleBasedStateMachine with cancel_queued rule (queued → cancelled) in solune/backend/tests/property/test_pipeline_state_machine.py

### E.2 — State Machine Invariants

- [ ] T045 [US6] Add invariant to state machine: FIFO order preserved (queued pipelines sorted by started_at ascending) in solune/backend/tests/property/test_pipeline_state_machine.py
- [ ] T046 [US6] Add invariant to state machine: queued pipelines have no assigned agent in solune/backend/tests/property/test_pipeline_state_machine.py
- [ ] T047 [US6] Add invariant to state machine: active pipeline count per project never exceeds 1 in solune/backend/tests/property/test_pipeline_state_machine.py

### E.3 — Blocking Queue Property Tests

- [ ] T048 [P] [US6] Create test_blocking_queue.py with property tests exercising count_active_pipelines_for_project() with random pipeline state combinations (≥200 Hypothesis examples) in solune/backend/tests/property/test_blocking_queue.py
- [ ] T049 [P] [US6] Add property tests exercising get_queued_pipelines_for_project() FIFO ordering invariant with random state combinations in solune/backend/tests/property/test_blocking_queue.py
- [ ] T050 [US6] Add property tests for should_skip_agent_trigger() exclusivity within grace period and stale reclaim at > 120 seconds in solune/backend/tests/property/test_blocking_queue.py (or test_pipeline_state_machine.py as state machine rules)

**Checkpoint**: Property-based queue tests pass across ≥200 examples with all invariants enforced. SC-006 satisfied.

---

## Phase 9: User Story 7 — Keyboard Navigation E2E & Accessibility (Priority: P2)

**Goal**: Create a dedicated keyboard navigation E2E suite and extend accessibility coverage with axe-core scans across all primary pages.

**Independent Test**: Run `npx playwright test keyboard-navigation.spec.ts` in solune/frontend/ — all keyboard navigation assertions pass. Verify axe-core scans are present in ≥8 Playwright specs.

**Parallel with**: User Stories 4, 5, 6 (all P2 stories are independent).

### F.1 — Keyboard Navigation Suite

- [ ] T051 [US7] Create keyboard-navigation.spec.ts with per-page Tab order verification for all primary pages (Dashboard/Board, Agents, Settings, Chat, Pipeline monitoring, MCP tool config) in solune/frontend/e2e/keyboard-navigation.spec.ts
- [ ] T052 [US7] Add Enter/Space activation assertions for interactive elements across all primary pages in solune/frontend/e2e/keyboard-navigation.spec.ts
- [ ] T053 [US7] Add Escape closing modals assertions (verify modals close on Escape key press) in solune/frontend/e2e/keyboard-navigation.spec.ts
- [ ] T054 [US7] Add focus trapping assertions for modal dialogs (Tab cycle stays within modal) in solune/frontend/e2e/keyboard-navigation.spec.ts
- [ ] T055 [US7] Add correct initial focus assertions on page load for all primary pages in solune/frontend/e2e/keyboard-navigation.spec.ts

### F.2 — Focus Assertions in Existing Specs

- [ ] T056 [P] [US7] Extend board-navigation.spec.ts with expect(locator).toBeFocused() assertions for Tab/Enter/Escape flows in solune/frontend/e2e/board-navigation.spec.ts
- [ ] T057 [P] [US7] Extend agent-creation.spec.ts with expect(locator).toBeFocused() assertions for Tab/Enter/Escape flows in solune/frontend/e2e/agent-creation.spec.ts
- [ ] T058 [P] [US7] Extend chat-interaction.spec.ts with expect(locator).toBeFocused() assertions for Tab/Enter/Escape flows in solune/frontend/e2e/chat-interaction.spec.ts

### F.3 — axe-core Scan Extension

- [ ] T059 [P] [US7] Add AxeBuilder accessibility scan to agent-creation.spec.ts using @axe-core/playwright in solune/frontend/e2e/agent-creation.spec.ts
- [ ] T060 [P] [US7] Add AxeBuilder accessibility scan to pipeline-monitoring.spec.ts using @axe-core/playwright in solune/frontend/e2e/pipeline-monitoring.spec.ts
- [ ] T061 [P] [US7] Add AxeBuilder accessibility scan to mcp-tool-config.spec.ts using @axe-core/playwright in solune/frontend/e2e/mcp-tool-config.spec.ts
- [ ] T062 [P] [US7] Add AxeBuilder accessibility scan to chat-interaction.spec.ts using @axe-core/playwright in solune/frontend/e2e/chat-interaction.spec.ts
- [ ] T063 [P] [US7] Add AxeBuilder accessibility scan to keyboard-navigation.spec.ts using @axe-core/playwright in solune/frontend/e2e/keyboard-navigation.spec.ts

### F.4 — Cross-Service E2E Evaluation

- [ ] T064 [US7] Document cross-service Playwright E2E feasibility assessment (docker-compose + DB + GitHub API mock + auth bypass) as future work in specs/001-phase-3-testing/research.md (append to R-007 findings)

**Checkpoint**: Keyboard navigation E2E passes; axe-core scans present in ≥8 specs. SC-007 and SC-008 satisfied.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cross-cutting verification.

- [ ] T065 Run full frontend test suite with final coverage thresholds: `npm run test:coverage` in solune/frontend/
- [ ] T066 Run full backend test suite with all per-file coverage checks in solune/backend/
- [ ] T067 Verify all CI workflows pass without continue-on-error masking (SC-009) by reviewing .github/workflows/mutation-testing.yml
- [ ] T068 Run quickstart.md verification checklist (all 7 verification commands from specs/001-phase-3-testing/quickstart.md)
- [ ] T069 Update specs/001-phase-3-testing/quickstart.md verification section with final pass/fail results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 baseline verification
- **US1 — Frontend Coverage (Phase 3)**: Can start after Phase 1 — parallel with US2
- **US2 — Backend Coverage (Phase 4)**: Can start after Phase 1 — parallel with US1
- **US3 — Full-Workflow Integration (Phase 5)**: Depends on US2 (backend coverage) landing first
- **US4 — FIFO Queue Integration (Phase 6)**: Depends on US2 stabilizing — parallel with US5, US6, US7
- **US5 — Mutation Enforcement (Phase 7)**: Independent — parallel with US4, US6, US7
- **US6 — Property Tests (Phase 8)**: Independent — parallel with US4, US5, US7
- **US7 — Keyboard E2E (Phase 9)**: Independent — parallel with US4, US5, US6
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

```text
US1 (Frontend Coverage, P1) ──────────────────────────────────┐
                                                               ├─→ Phase 10 (Polish)
US2 (Backend Coverage, P1) ──→ US3 (Full Workflow, P1) ───────┤
                             ──→ US4 (Queue FIFO, P2) ────────┤
                                                               │
US5 (Mutation Enforcement, P2) ────────────────────────────────┤
US6 (Property Tests, P2) ─────────────────────────────────────┤
US7 (Keyboard E2E, P2) ───────────────────────────────────────┘
```

### Within Each User Story

- Models/data structures before service-level tests
- Unit/component tests before integration tests
- Core implementation before threshold/configuration changes
- Verification before moving to next priority

### Parallel Opportunities

**Across P1 stories**:
- US1 (frontend) and US2 (backend) are fully parallel — different directories, no shared files

**Across P2 stories**:
- US4, US5, US6, US7 are all fully parallel — independent concerns (queue integration, mutation config, property tests, E2E keyboard)

**Within US1 (Frontend Coverage)**:
- All 6 hook tests (T003–T008) are parallel — different test files
- All 7 component tests (T009–T015) are parallel — different test files
- Threshold raises (T016, T017) are sequential — same config file

**Within US2 (Backend Coverage)**:
- B.1 tests (T018–T021) are parallel within the group — same file but independent test functions
- B.2 tests (T022–T025) are parallel within the group
- B.3 tests (T026–T028) are parallel within the group
- B.4 tests (T029–T031) are parallel within the group
- All 4 groups (B.1–B.4) are parallel — different target modules

**Within US5 (Mutation Enforcement)**:
- Stryker threshold (T038) and Stryker CI (T039) are parallel — different files
- mutmut CI (T041) can parallel with Stryker changes — different workflow sections

**Within US7 (Keyboard E2E)**:
- Focus assertion extensions (T056–T058) are parallel — different spec files
- axe-core additions (T059–T063) are parallel — different spec files

---

## Parallel Example: User Story 1 (Frontend Coverage)

```bash
# Launch all hook tests in parallel (T003–T008):
Task: "Write tests for useActivityFeed in solune/frontend/src/hooks/useActivityFeed.test.tsx"
Task: "Write tests for useBoardDragDrop in solune/frontend/src/hooks/useBoardDragDrop.test.tsx"
Task: "Write tests for useCommandPalette in solune/frontend/src/hooks/useCommandPalette.test.tsx"
Task: "Write tests for useEntityHistory in solune/frontend/src/hooks/useEntityHistory.test.tsx"
Task: "Write tests for useInfiniteList in solune/frontend/src/hooks/useInfiniteList.test.tsx"
Task: "Write tests for useUnsavedPipelineGuard in solune/frontend/src/hooks/useUnsavedPipelineGuard.test.tsx"

# Then launch all component tests in parallel (T009–T015):
Task: "Write tests for ProjectBoard in solune/frontend/src/components/board/ProjectBoard.test.tsx"
Task: "Write tests for ChatInterface in solune/frontend/src/components/chat/ChatInterface.test.tsx"
Task: "Write tests for CleanUpConfirmModal in solune/frontend/src/components/modals/CleanUpConfirmModal.test.tsx"
Task: "Write tests for PipelineAnalytics in solune/frontend/src/components/pipeline/PipelineAnalytics.test.tsx"
Task: "Write tests for MarkdownRenderer in solune/frontend/src/components/common/MarkdownRenderer.test.tsx"
Task: "Write tests for McpSettings in solune/frontend/src/components/settings/McpSettings.test.tsx"
Task: "Write tests for WorkflowSettings in solune/frontend/src/components/settings/WorkflowSettings.test.tsx"
```

## Parallel Example: User Story 7 (Keyboard E2E)

```bash
# Launch all axe-core scan additions in parallel (T059–T063):
Task: "Add AxeBuilder scan to agent-creation.spec.ts"
Task: "Add AxeBuilder scan to pipeline-monitoring.spec.ts"
Task: "Add AxeBuilder scan to mcp-tool-config.spec.ts"
Task: "Add AxeBuilder scan to chat-interaction.spec.ts"
Task: "Add AxeBuilder scan to keyboard-navigation.spec.ts"

# Launch all focus assertion extensions in parallel (T056–T058):
Task: "Extend board-navigation.spec.ts with focus assertions"
Task: "Extend agent-creation.spec.ts with focus assertions"
Task: "Extend chat-interaction.spec.ts with focus assertions"
```

---

## Implementation Strategy

### MVP First (P1 Stories: US1 + US2)

1. Complete Phase 1: Baseline verification
2. **In parallel**: US1 (frontend coverage) + US2 (backend coverage)
3. **STOP and VALIDATE**: Run `npm run test:coverage` and all 4 per-file pytest coverage commands
4. Then US3 (full-workflow integration) — depends on US2

### Incremental Delivery

1. US1 + US2 (parallel) → Frontend at 75/65/65/75 + backend floors met → **Core Coverage MVP**
2. US3 → Full-workflow integration passes → **Integration Confidence**
3. US4 → FIFO queue verified with 3+ pipelines → **Queue Correctness**
4. US5 → Mutation testing blocking in CI → **Quality Enforcement**
5. US6 → Property tests pass ≥200 examples → **Invariant Verification**
6. US7 → Keyboard E2E + axe-core in ≥8 specs → **Accessibility Coverage**
7. Phase 10 → All verification commands pass → **Phase 3 Complete**

### Parallel Team Strategy

With multiple developers:

1. **Developer A**: US1 (Frontend Coverage, P1) — hooks, components, threshold raises
2. **Developer B**: US2 (Backend Coverage, P1) — board, pipelines, pipeline, agent_creator
3. **Developer C**: US5 (Mutation Enforcement, P2) + US7 (Keyboard E2E, P2) — config changes + E2E specs
4. After US2 completes: **Developer B** → US3 (Full-Workflow Integration) + US4 (FIFO Queue)
5. **Developer D**: US6 (Property Tests, P2) — state machine rules + blocking queue properties

### Suggested MVP Scope

**MVP = User Story 1 (Frontend Coverage)** — provides the highest ROI (~2,200 new covered statements) with immediate CI enforcement. Can be shipped independently as a Phase 1 PR (65/55/55/65 thresholds) for quick value delivery.

---

## Task Summary

| Category | Count | Stories |
|----------|-------|---------|
| Setup & Foundational | 2 | — |
| US1 — Frontend Coverage | 15 | T003–T017 |
| US2 — Backend Coverage | 14 | T018–T031 |
| US3 — Full-Workflow Integration | 4 | T032–T035 |
| US4 — FIFO Queue Integration | 2 | T036–T037 |
| US5 — Mutation Enforcement | 4 | T038–T041 |
| US6 — Property-Based Tests | 9 | T042–T050 |
| US7 — Keyboard E2E & Accessibility | 14 | T051–T064 |
| Polish & Cross-Cutting | 5 | T065–T069 |
| **Total** | **69** | — |

### Per-Story Task Counts

| User Story | Priority | Tasks | Parallel Tasks |
|-----------|----------|-------|----------------|
| US1 — Frontend Coverage | P1 | 15 | 13 (T003–T015) |
| US2 — Backend Coverage | P1 | 14 | 14 (all) |
| US3 — Full-Workflow Integration | P1 | 4 | 0 (sequential) |
| US4 — FIFO Queue Integration | P2 | 2 | 0 (sequential) |
| US5 — Mutation Enforcement | P2 | 4 | 3 (T038, T039, T041) |
| US6 — Property-Based Tests | P2 | 9 | 2 (T048, T049) |
| US7 — Keyboard E2E & Accessibility | P2 | 14 | 8 (T056–T058, T059–T063) |

### Format Validation

✅ ALL 69 tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ Setup/Foundational tasks: NO story label
✅ User Story phase tasks: MUST have [USn] story label
✅ Polish tasks: NO story label
✅ All tasks include exact file paths
✅ [P] markers applied only to genuinely parallelizable tasks (different files, no dependencies)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Coverage thresholds are delivered via separate PRs (Phase 1 and Phase 2) to reduce risk
- Mutation testing defers PR-level `--since` mode until weekly blocking runs are stable
- Cross-service E2E is documented as future work (T064) per spec FR-012
- Exclusions: health.py error paths, WebSocket handlers, error-returning webhooks (per spec)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
