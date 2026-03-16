# Tasks: Modernize Testing to Surface Unknown Bugs

**Input**: Design documents from `/specs/046-modernize-testing/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: This feature is explicitly about adding testing infrastructure — test tasks ARE the core deliverables.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `solune/backend/src/`, `solune/backend/tests/`
- **Frontend**: `solune/frontend/src/`, `solune/frontend/e2e/`
- **CI**: `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install all new dev dependencies across backend and frontend so subsequent phases can reference them immediately

- [X] T001 Add hypothesis, mutmut, pip-audit, and bandit to `[project.optional-dependencies] dev` in `solune/backend/pyproject.toml`
- [X] T002 [P] Add @fast-check/vitest, @stryker-mutator/core, @stryker-mutator/vitest-runner, eslint-plugin-security, and @axe-core/playwright to devDependencies in `solune/frontend/package.json` and run `npm install`
- [X] T003 [P] Create `solune/backend/tests/property/__init__.py` directory for Hypothesis property tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared configuration that multiple user stories depend on — CI workflow structure, ESLint security plugin, and Hypothesis settings profile

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `[tool.coverage.run]` and `[tool.coverage.report]` sections (with `fail_under` placeholder of 0) to `solune/backend/pyproject.toml`
- [X] T005 [P] Add `[tool.bandit]` configuration section to `solune/backend/pyproject.toml` targeting `src/` with medium severity and confidence
- [X] T006 [P] Add eslint-plugin-security to the ESLint flat config in `solune/frontend/eslint.config.js`
- [X] T007 [P] Add Hypothesis settings profiles (ci and dev) via a `conftest.py` at `solune/backend/tests/property/conftest.py`

**Checkpoint**: All dependencies installed, base configuration in place. User story work can begin.

---

## Phase 3: User Story 1 — Coverage Enforcement Catches Blind Spots (Priority: P1) 🎯 MVP

**Goal**: CI fails when backend or frontend test coverage drops below the configured threshold

**Independent Test**: Delete a backend test file and run `pytest --cov=src` — verify it reports coverage below threshold. Delete a frontend test file and run `npm run test:coverage` — verify it fails.

### Implementation for User Story 1

- [X] T008 [US1] Run `pytest --cov=src --cov-report=term-missing` locally, record baseline percentage, then set `fail_under` to `baseline - 2` in `[tool.coverage.report]` in `solune/backend/pyproject.toml`
- [X] T009 [US1] Add `coverage` block with `provider: 'v8'` and `thresholds` (lines, branches, functions, statements set to baseline - 2) to `test` in `solune/frontend/vitest.config.ts`
- [X] T010 [US1] Update the backend CI job `Run tests` step in `.github/workflows/ci.yml` to use `pytest --cov=src --cov-report=term-missing --cov-fail-under=$THRESHOLD` (the `fail_under` from pyproject.toml will be picked up automatically, but confirm the step name reflects coverage enforcement)
- [X] T011 [US1] Update the frontend CI job `Run tests` step in `.github/workflows/ci.yml` to use `npm run test:coverage` instead of `npm test`

**Checkpoint**: Coverage thresholds enforced in CI. Any PR dropping coverage below threshold is rejected.

---

## Phase 4: User Story 2 — Property-Based Tests Discover Edge-Case Bugs (Priority: P2)

**Goal**: Hypothesis (backend) and fast-check (frontend) generate thousands of random inputs to discover edge-case bugs in models and utility functions

**Independent Test**: Run `pytest tests/property/` and `npm test -- --reporter=verbose src/lib/` — property tests should either pass or surface minimized counterexamples.

### Implementation for User Story 2

- [X] T012 [P] [US2] Write Hypothesis property test for Pydantic model serialization round-trips (agent, pipeline, tools models) in `solune/backend/tests/property/test_model_roundtrips.py`
- [X] T013 [P] [US2] Write Hypothesis property test for model validation edge cases (unicode, empty strings, extreme lengths) in `solune/backend/tests/property/test_model_validation.py`
- [X] T014 [P] [US2] Write Hypothesis property test for pipeline state transition sequences in `solune/backend/tests/property/test_pipeline_states.py`
- [X] T015 [P] [US2] Write fast-check property test for `buildGitHubMcpConfig` in `solune/frontend/src/lib/buildGitHubMcpConfig.property.test.ts`
- [X] T016 [P] [US2] Write fast-check property test for `case-utils.ts` functions in `solune/frontend/src/lib/case-utils.property.test.ts`
- [X] T017 [P] [US2] Write fast-check property test for `time-utils.ts` functions in `solune/frontend/src/lib/time-utils.property.test.ts`
- [X] T018 [P] [US2] Write fast-check property test for `utils.ts` utility functions in `solune/frontend/src/lib/utils.property.test.ts`
- [X] T019 [P] [US2] Write fast-check property test for `pipelineMigration.ts` functions in `solune/frontend/src/lib/pipelineMigration.property.test.ts`

**Checkpoint**: At least 10 property-based tests exist across backend and frontend. Run them to surface any unknown edge-case bugs.

---

## Phase 5: User Story 3 — Mutation Testing Identifies Weak Tests (Priority: P3)

**Goal**: mutmut (backend) and Stryker (frontend) are configured and produce reports identifying surviving mutants (weak test spots)

**Independent Test**: Run `cd solune/backend && mutmut run --paths-to-mutate=src/services/` and verify a report is generated. Run `cd solune/frontend && npx stryker run` and verify an HTML report is generated.

### Implementation for User Story 3

- [X] T020 [P] [US3] Add `[tool.mutmut]` configuration to `solune/backend/pyproject.toml` scoping mutations to `src/services/` with tests in `tests/`
- [X] T021 [P] [US3] Create Stryker configuration file at `solune/frontend/stryker.config.mjs` targeting `src/hooks/**/*.ts` and `src/lib/**/*.ts` with vitest runner
- [X] T022 [US3] Create a separate scheduled GitHub Actions workflow at `.github/workflows/mutation-testing.yml` with weekly cron, running mutmut for backend and Stryker for frontend, uploading reports as artifacts
- [X] T023 [US3] Add `test:mutate` script to `solune/frontend/package.json` running `stryker run`

**Checkpoint**: Mutation testing configured. Weekly scheduled runs will identify surviving mutants.

---

## Phase 6: User Story 4 — API Contract Validation Detects Frontend-Backend Drift (Priority: P4)

**Goal**: CI exports the FastAPI OpenAPI spec and validates that frontend mock factories conform to the backend's response shapes

**Independent Test**: Rename a field in a backend Pydantic response model. Run the contract-validation step. Verify it reports the mismatch.

### Implementation for User Story 4

- [X] T024 [P] [US4] Create OpenAPI export script at `solune/scripts/export-openapi.py` that imports `create_app()` from `src.main`, calls `app.openapi()`, and writes `openapi.json`
- [X] T025 [US4] Create contract validation script at `solune/scripts/validate-contracts.sh` that runs `openapi-typescript` to generate types from `openapi.json` and diffs against existing frontend type definitions
- [X] T026 [US4] Add a `contract-validation` job to `.github/workflows/ci.yml` that runs the export and validation scripts, failing on drift

**Checkpoint**: Contract validation catches API drift. Backend schema changes that aren't reflected in frontend mocks will fail CI.

---

## Phase 7: User Story 5 — Visual & Accessibility Regression Prevention (Priority: P5)

**Goal**: Playwright screenshots catch visual regressions; axe-core catches accessibility violations in both component and E2E tests; Firefox added as second browser

**Independent Test**: Change a CSS property in a component, run E2E tests — visual regression fails. Remove a form label, run component test — a11y audit fails.

### Implementation for User Story 5

- [X] T027 [P] [US5] Add Firefox project (with `ignoreSnapshots: true`) to `projects` array in `solune/frontend/playwright.config.ts`
- [X] T028 [P] [US5] Add `toHaveScreenshot()` assertions with `maxDiffPixels` config to existing E2E specs in `solune/frontend/e2e/board-navigation.spec.ts`
- [X] T029 [P] [US5] Add `toHaveScreenshot()` assertions to `solune/frontend/e2e/settings-flow.spec.ts`
- [X] T030 [P] [US5] Add `toHaveScreenshot()` assertions to `solune/frontend/e2e/ui.spec.ts`
- [X] T031 [US5] Generate initial screenshot baselines by running `npx playwright test --update-snapshots` and commit the snapshot files
- [X] T032 [P] [US5] Add `@axe-core/playwright` accessibility checks using `AxeBuilder` to `solune/frontend/e2e/ui.spec.ts`
- [X] T033 [P] [US5] Add `@axe-core/playwright` accessibility checks to `solune/frontend/e2e/board-navigation.spec.ts`
- [X] T034 [US5] Add `expectNoA11yViolations()` calls to all existing component tests in `solune/frontend/src/components/board/` that render without it
- [X] T035 [P] [US5] Add `expectNoA11yViolations()` calls to all existing component tests in `solune/frontend/src/components/chat/`
- [X] T036 [P] [US5] Add `expectNoA11yViolations()` calls to all existing component tests in `solune/frontend/src/components/common/`
- [X] T037 [P] [US5] Add `expectNoA11yViolations()` calls to all existing component tests in `solune/frontend/src/components/ui/`
- [X] T038 [P] [US5] Add `expectNoA11yViolations()` calls to all existing component tests in `solune/frontend/src/components/pipeline/`
- [X] T039 [US5] Update CI frontend job in `.github/workflows/ci.yml` to install Playwright browsers for both Chromium and Firefox (`npx playwright install --with-deps chromium firefox`)

**Checkpoint**: Visual regression and a11y audits active. CSS changes produce screenshot diffs; missing labels produce a11y failures; Firefox is tested.

---

## Phase 8: User Story 6 — Security & Dependency Scanning Catches Known Vulnerabilities (Priority: P6)

**Goal**: pip-audit, bandit, npm audit, and eslint-plugin-security run on every PR and fail on findings

**Independent Test**: Temporarily pin a dependency to a known-CVE version — audit fails. Add a hardcoded secret pattern — bandit fails. Add `eval()` — ESLint security plugin fails.

### Implementation for User Story 6

- [X] T040 [P] [US6] Add `pip-audit` step to the backend CI job in `.github/workflows/ci.yml` after dependency installation
- [X] T041 [P] [US6] Add `bandit -r src/ -ll -ii` step to the backend CI job in `.github/workflows/ci.yml` after linting
- [X] T042 [P] [US6] Add `npm audit --audit-level=moderate` step to the frontend CI job in `.github/workflows/ci.yml` after dependency installation
- [X] T043 [US6] Verify that `npm run lint` now catches eslint-plugin-security violations (the plugin was configured in T006) — no additional CI step needed since lint already runs

**Checkpoint**: Security scanning active on every PR. Known CVEs and security anti-patterns are caught.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Fill critical coverage gaps (FR-018), verify all tooling end-to-end, update documentation

- [X] T044 [P] Write smoke-level page test for `solune/frontend/src/pages/AgentsPage.tsx` in `solune/frontend/src/pages/AgentsPage.test.tsx`
- [X] T045 [P] Write smoke-level page test for `solune/frontend/src/pages/ChoresPage.tsx` in `solune/frontend/src/pages/ChoresPage.test.tsx`
- [X] T046 [P] Write smoke-level page test for `solune/frontend/src/pages/HelpPage.tsx` in `solune/frontend/src/pages/HelpPage.test.tsx`
- [X] T047 [P] Write smoke-level page test for `solune/frontend/src/pages/LoginPage.tsx` in `solune/frontend/src/pages/LoginPage.test.tsx`
- [X] T048 [P] Write smoke-level page test for `solune/frontend/src/pages/NotFoundPage.tsx` in `solune/frontend/src/pages/NotFoundPage.test.tsx`
- [X] T049 [P] Write smoke-level page test for `solune/frontend/src/pages/SettingsPage.tsx` in `solune/frontend/src/pages/SettingsPage.test.tsx`
- [X] T050 [P] Write smoke-level page test for `solune/frontend/src/pages/ToolsPage.tsx` in `solune/frontend/src/pages/ToolsPage.test.tsx`
- [X] T051 [P] Write smoke-level component tests for `solune/frontend/src/components/apps/` (0 existing tests)
- [X] T052 [P] Write smoke-level component tests for `solune/frontend/src/components/help/` (0 existing tests)
- [X] T053 [P] Write smoke-level component tests for `solune/frontend/src/components/onboarding/` (0 existing tests)
- [X] T054 [P] Write smoke-level test for `solune/frontend/src/services/api.ts` in `solune/frontend/src/services/api.test.ts`
- [X] T055 Run quickstart.md verification checklist end-to-end and fix any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 Coverage (Phase 3)**: Depends on Phase 2 (coverage config sections created in T004)
- **US2 Property Tests (Phase 4)**: Depends on Phase 2 (Hypothesis conftest in T007, dependencies in T001)
- **US3 Mutation Testing (Phase 5)**: Depends on Phase 2 (dependencies in T001/T002)
- **US4 Contract Validation (Phase 6)**: Depends on Phase 2 (dependencies in T001)
- **US5 Visual/A11y (Phase 7)**: Depends on Phase 2 (dependencies in T002, ESLint in T006 not needed but a11y deps needed)
- **US6 Security Scanning (Phase 8)**: Depends on Phase 2 (bandit config in T005, ESLint security in T006)
- **Polish (Phase 9)**: Depends on US1 (Phase 3) for coverage thresholds to validate new test coverage

### User Story Independence

- **US1 (Coverage)** ↔ **US2 (Property)**: Independent. Can run in parallel.
- **US1 (Coverage)** ↔ **US3 (Mutation)**: Independent. Can run in parallel.
- **US1 (Coverage)** ↔ **US4 (Contract)**: Independent. Can run in parallel.
- **US1 (Coverage)** ↔ **US5 (Visual/A11y)**: Independent. Can run in parallel.
- **US1 (Coverage)** ↔ **US6 (Security)**: Independent. Can run in parallel.
- All user stories are independent after Foundational phase.

### Within Each User Story

- Configuration before test files
- CI workflow changes after local verification
- Checkpoint validation before moving to next story

### Parallel Opportunities

**Phase 1**: T001 and T002 can run in parallel (different package managers). T003 in parallel with T002.
**Phase 2**: T004, T005, T006, T007 can all run in parallel (different files).
**Phase 4 (US2)**: All property test files (T012–T019) can run in parallel (different files).
**Phase 5 (US3)**: T020 and T021 can run in parallel (different files).
**Phase 7 (US5)**: T027–T030 can run in parallel; T032–T033 in parallel; T034–T038 in parallel.
**Phase 8 (US6)**: T040, T041, T042 can run in parallel (different CI steps).
**Phase 9 (Polish)**: T044–T054 can all run in parallel (different test files).

---

## Parallel Example: User Story 2 (Property-Based Tests)

```bash
# All property test files can be written simultaneously (different files):
T012: solune/backend/tests/property/test_model_roundtrips.py
T013: solune/backend/tests/property/test_model_validation.py
T014: solune/backend/tests/property/test_pipeline_states.py
T015: solune/frontend/src/lib/buildGitHubMcpConfig.property.test.ts
T016: solune/frontend/src/lib/case-utils.property.test.ts
T017: solune/frontend/src/lib/time-utils.property.test.ts
T018: solune/frontend/src/lib/utils.property.test.ts
T019: solune/frontend/src/lib/pipelineMigration.property.test.ts
```

## Parallel Example: Phase 9 (Coverage Gap Fill)

```bash
# All page smoke tests can be written simultaneously:
T044: solune/frontend/src/pages/AgentsPage.test.tsx
T045: solune/frontend/src/pages/ChoresPage.test.tsx
T046: solune/frontend/src/pages/HelpPage.test.tsx
T047: solune/frontend/src/pages/LoginPage.test.tsx
T048: solune/frontend/src/pages/NotFoundPage.test.tsx
T049: solune/frontend/src/pages/SettingsPage.test.tsx
T050: solune/frontend/src/pages/ToolsPage.test.tsx
T051: solune/frontend/src/components/apps/*.test.tsx
T052: solune/frontend/src/components/help/*.test.tsx
T053: solune/frontend/src/components/onboarding/*.test.tsx
T054: solune/frontend/src/services/api.test.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (install all dependencies)
2. Complete Phase 2: Foundational (config scaffolding)
3. Complete Phase 3: US1 — Coverage Enforcement
4. **STOP and VALIDATE**: Run `pytest --cov=src` and `npm run test:coverage` — verify both enforce thresholds
5. This alone provides immediate value: coverage visibility and regression prevention

### Incremental Delivery

1. Setup + Foundational → All tools available
2. US1 (Coverage) → Coverage gates in CI (MVP!)
3. US2 (Property Tests) → Unknown edge-case bugs surfaced
4. US3 (Mutation Testing) → Weak test spots identified on schedule
5. US4 (Contract Validation) → Frontend-backend drift caught
6. US5 (Visual/A11y) → Visual regressions and a11y violations caught
7. US6 (Security) → Known CVEs and anti-patterns caught
8. Polish → All 7 untested pages covered, end-to-end verification

### Parallel Team Strategy

With multiple developers after Foundational phase:

- Developer A: US1 (Coverage) + US4 (Contract)
- Developer B: US2 (Property Tests) + US3 (Mutation)
- Developer C: US5 (Visual/A11y) + US6 (Security)
- All developers: Phase 9 (Polish — page smoke tests can be split)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable after Phase 2
- Mutation testing (US3) runs on schedule only — not blocking PRs
- Coverage thresholds use the ratchet pattern — start below baseline, only increase over time
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
