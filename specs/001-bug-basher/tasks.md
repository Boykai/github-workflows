# Tasks: Bug Basher - Full Codebase Review & Fix

**Input**: Design documents from `/specs/001-bug-basher/`
**Prerequisites**: `/specs/001-bug-basher/plan.md`, `/specs/001-bug-basher/spec.md`, `/specs/001-bug-basher/research.md`, `/specs/001-bug-basher/data-model.md`, `/specs/001-bug-basher/quickstart.md`, `/specs/001-bug-basher/contracts/bug-report.yaml`

**Tests**: Mandatory. `spec.md` FR-004, FR-007, and the user stories require at least one regression test per clear fix plus full backend/frontend validation before completion.

**Organization**: Tasks are grouped by user story so each audit pass can be executed, verified, and summarized independently while preserving the category order defined in `plan.md` and `research.md`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other tasks in the same phase because it targets different files or directories
- **[Story]**: Maps tasks to user stories from `/specs/001-bug-basher/spec.md`
- Every task references an exact repository path so the work is immediately executable in this monorepo

## Path Conventions

- **Backend source**: `solune/backend/src/`
- **Backend tests**: `solune/backend/tests/`
- **Frontend source**: `solune/frontend/src/`
- **Frontend E2E/tests**: `solune/frontend/e2e/`, `solune/frontend/src/**/*.test.ts`, `solune/frontend/src/**/*.test.tsx`
- **Feature docs/contracts**: `specs/001-bug-basher/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the monorepo for the bug-bash workflow without changing architecture, public APIs, or dependencies.

- [ ] T001 Review scope, priorities, and constraints in specs/001-bug-basher/plan.md and specs/001-bug-basher/spec.md
- [ ] T002 Install backend development tooling from solune/backend/pyproject.toml in solune/backend/
- [ ] T003 [P] Install frontend development tooling from solune/frontend/package.json in solune/frontend/
- [ ] T004 [P] Capture baseline backend test, lint, type-check, and Bandit results for solune/backend/ using specs/001-bug-basher/quickstart.md
- [ ] T005 [P] Capture baseline frontend test, lint, type-check, and build results for solune/frontend/ using specs/001-bug-basher/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared operating rules for the bug bash before category-specific work begins.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T006 Review the summary-table contract in specs/001-bug-basher/contracts/bug-report.yaml and the entity rules in specs/001-bug-basher/data-model.md
- [ ] T007 Review the TODO(bug-bash) decision rules and comment format in specs/001-bug-basher/research.md and specs/001-bug-basher/spec.md
- [ ] T008 [P] Build the backend audit checklist for solune/backend/src/api/, solune/backend/src/middleware/, solune/backend/src/models/, solune/backend/src/services/, solune/backend/src/utils.py, solune/backend/src/config.py, solune/backend/src/dependencies.py, and solune/backend/src/main.py
- [ ] T009 [P] Build the frontend audit checklist for solune/frontend/src/components/, solune/frontend/src/hooks/, solune/frontend/src/services/, solune/frontend/src/utils/, solune/frontend/src/__tests__/, solune/frontend/src/test/, and solune/frontend/e2e/
- [ ] T010 Define the per-fix workflow for updating affected tests and adding co-located regression tests in solune/backend/tests/**/test_*.py and solune/frontend/src/**/*.{test.ts,test.tsx}
- [ ] T011 Establish the final validation checklist from solune/backend/pyproject.toml, solune/frontend/package.json, and specs/001-bug-basher/quickstart.md

**Checkpoint**: Setup, scope, and validation rules are locked; bug-category work can now proceed in priority order.

---

## Phase 3: User Story 1 - Security Vulnerability Remediation (Priority: P1) 🎯 MVP

**Goal**: Remove clear security issues across backend and frontend paths while preserving the current architecture and API surface.

**Independent Test**: `bandit -r src/` passes when run from `solune/backend/`, frontend lint/security checks pass from `solune/frontend/`, and every security fix is covered by at least one targeted regression test.

### Tests for User Story 1 ⚠️

> **NOTE**: Add or update the regression tests before finalizing each security fix, and confirm they fail against the pre-fix behavior when practical.

- [ ] T012 [P] [US1] Add or update backend security regression tests in the nearest files under solune/backend/tests/unit/ and solune/backend/tests/integration/ for fixes in solune/backend/src/api/, solune/backend/src/middleware/, solune/backend/src/dependencies.py, solune/backend/src/config.py, and solune/backend/src/main.py
- [ ] T013 [P] [US1] Add or update frontend security regression tests in existing files under solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx for fixes in solune/frontend/src/components/, solune/frontend/src/hooks/, solune/frontend/src/services/, and solune/frontend/src/utils/

### Implementation for User Story 1

- [ ] T014 [P] [US1] Run a Bandit-guided security audit and apply minimal fixes in solune/backend/src/api/ and solune/backend/src/models/
- [ ] T015 [P] [US1] Audit authentication, authorization, CORS, and dependency guards and apply minimal fixes in solune/backend/src/middleware/, solune/backend/src/dependencies.py, solune/backend/src/config.py, and solune/backend/src/main.py
- [ ] T016 [P] [US1] Audit backend secret handling, unsafe I/O, and injection-prone code paths and apply minimal fixes in solune/backend/src/services/ and solune/backend/src/utils.py
- [ ] T017 [P] [US1] Audit frontend security lint findings, unsafe rendering, and input/data handling and apply minimal fixes in solune/frontend/src/components/, solune/frontend/src/hooks/, solune/frontend/src/services/, and solune/frontend/src/utils/
- [ ] T018 [US1] Add TODO(bug-bash) comments for unresolved security trade-offs directly in affected files under solune/backend/src/ and solune/frontend/src/ using the format from specs/001-bug-basher/research.md
- [ ] T019 [US1] Verify User Story 1 with Bandit in solune/backend/, frontend lint checks from solune/frontend/eslint.config.js in solune/frontend/, and the new security regression tests in solune/backend/tests/ and solune/frontend/src/

**Checkpoint**: Security audit fixes are complete, regression-tested, and safe to build on.

---

## Phase 4: User Story 2 - Runtime Error Elimination (Priority: P1)

**Goal**: Eliminate clear runtime failures, null dereferences, resource leaks, and type-driven crash paths across the monorepo.

**Independent Test**: `pyright src` passes in `solune/backend/`, `npm run type-check` passes in `solune/frontend/`, and every runtime fix has a targeted regression test covering the failing path.

### Tests for User Story 2 ⚠️

- [ ] T020 [P] [US2] Add or update backend runtime regression tests in the nearest files under solune/backend/tests/unit/, solune/backend/tests/integration/, and solune/backend/tests/concurrency/ for fixes in solune/backend/src/api/, solune/backend/src/services/, solune/backend/src/utils.py, and solune/backend/src/dependencies.py
- [ ] T021 [P] [US2] Add or update frontend runtime regression tests in existing files under solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx for fixes in solune/frontend/src/hooks/, solune/frontend/src/services/, and solune/frontend/src/components/

### Implementation for User Story 2

- [ ] T022 [P] [US2] Audit exception handling and crash paths and apply minimal fixes in solune/backend/src/api/, solune/backend/src/services/, and solune/backend/src/logging_utils.py
- [ ] T023 [P] [US2] Audit null or None dereferences, file/DB resource management, and guard clauses and apply minimal fixes in solune/backend/src/services/, solune/backend/src/utils.py, solune/backend/src/dependencies.py, and solune/backend/src/migrations/
- [ ] T024 [P] [US2] Audit async and concurrency risks and apply minimal fixes in solune/backend/src/services/copilot_polling/, solune/backend/src/services/github_projects/, and solune/backend/src/services/workflow_orchestrator/
- [ ] T025 [P] [US2] Audit frontend runtime safety, async cleanup, and state-guard issues and apply minimal fixes in solune/frontend/src/hooks/, solune/frontend/src/services/, and solune/frontend/src/components/
- [ ] T026 [US2] Add TODO(bug-bash) comments for ambiguous runtime or race-condition findings directly in affected files under solune/backend/src/ and solune/frontend/src/
- [ ] T027 [US2] Verify User Story 2 with pyright in solune/backend/, npm run type-check in solune/frontend/, and the new runtime regression tests in solune/backend/tests/ and solune/frontend/src/

**Checkpoint**: Runtime-critical paths are guarded, typed, and regression-tested.

---

## Phase 5: User Story 3 - Logic Bug Resolution (Priority: P2)

**Goal**: Correct clear logic errors in workflow state transitions, API parameter handling, control flow, and boundary conditions.

**Independent Test**: Targeted backend and frontend tests for changed logic paths pass, with boundary cases covered for every corrected logic bug.

### Tests for User Story 3 ⚠️

- [ ] T028 [P] [US3] Add or update backend logic regression tests in the nearest files under solune/backend/tests/unit/ and solune/backend/tests/integration/ for fixes in solune/backend/src/services/workflow_orchestrator/, solune/backend/src/services/pipelines/, solune/backend/src/services/github_projects/, and solune/backend/src/api/
- [ ] T029 [P] [US3] Add or update frontend logic regression tests in existing files under solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx for fixes in solune/frontend/src/services/, solune/frontend/src/hooks/, and solune/frontend/src/components/

### Implementation for User Story 3

- [ ] T030 [P] [US3] Audit workflow and state-transition behavior and apply minimal fixes in solune/backend/src/services/workflow_orchestrator/ and solune/backend/src/services/pipelines/
- [ ] T031 [P] [US3] Audit API parameter passing, return-value handling, and repository-resolution logic and apply minimal fixes in solune/backend/src/api/ and solune/backend/src/services/github_projects/
- [ ] T032 [P] [US3] Audit boundary conditions, indexing, and control-flow bugs and apply minimal fixes in solune/backend/src/services/, solune/backend/src/utils.py, and solune/frontend/src/hooks/
- [ ] T033 [P] [US3] Audit frontend API-client and UI-state logic and apply minimal fixes in solune/frontend/src/services/, solune/frontend/src/hooks/, and solune/frontend/src/components/
- [ ] T034 [US3] Verify User Story 3 with targeted pytest runs in solune/backend/tests/, targeted Vitest runs in solune/frontend/src/, and any affected integration coverage in solune/backend/tests/integration/

**Checkpoint**: Logic paths behave correctly and remain independently testable.

---

## Phase 6: User Story 4 - Test Quality Improvement (Priority: P2)

**Goal**: Strengthen the test suite so it catches real regressions across backend and frontend paths.

**Independent Test**: Backend coverage remains at or above the threshold in solune/backend/pyproject.toml, frontend coverage remains at or above the thresholds in solune/frontend/package.json tooling, and no audited tests pass for tautological or mock-leak reasons.

### Tests for User Story 4 ⚠️

- [ ] T035 [P] [US4] Add or update backend regression and coverage tests in solune/backend/tests/unit/, solune/backend/tests/integration/, solune/backend/tests/property/, and solune/backend/tests/concurrency/ for critical paths fixed during earlier stories
- [ ] T036 [P] [US4] Add or update frontend regression and coverage tests in solune/frontend/src/**/*.test.ts, solune/frontend/src/**/*.test.tsx, and solune/frontend/e2e/ for critical paths fixed during earlier stories

### Implementation for User Story 4

- [ ] T037 [P] [US4] Audit mock leakage, brittle fixtures, and test-only values escaping into runtime behavior in solune/backend/tests/ and fix affected tests alongside the referenced modules under solune/backend/src/
- [ ] T038 [P] [US4] Audit tautological, non-assertive, or ineffective tests in solune/backend/tests/, solune/frontend/src/__tests__/, and collocated tests under solune/frontend/src/
- [ ] T039 [P] [US4] Add missing high-risk backend coverage for previously untested paths in solune/backend/src/services/ and solune/backend/src/api/ with matching tests in solune/backend/tests/
- [ ] T040 [P] [US4] Add missing high-risk frontend coverage for previously untested paths in solune/frontend/src/components/, solune/frontend/src/hooks/, and solune/frontend/src/services/ with matching tests in solune/frontend/src/
- [ ] T041 [US4] Verify User Story 4 with pytest --cov from solune/backend/ and npm run test:coverage from solune/frontend/ against the thresholds defined in solune/backend/pyproject.toml and solune/frontend/package.json

**Checkpoint**: The test suite is more trustworthy and better aligned with real bug risks.

---

## Phase 7: User Story 5 - Code Quality Cleanup (Priority: P3)

**Goal**: Remove low-risk code-quality defects that hide bugs or make the codebase harder to maintain, without introducing refactors outside the scope of the audited fixes.

**Independent Test**: Ruff and ESLint pass for changed areas, targeted regression tests cover any behavior-affecting cleanup, and no cleanup task changes public APIs or adds dependencies.

### Tests for User Story 5 ⚠️

- [ ] T042 [P] [US5] Add or update backend regression tests in the nearest files under solune/backend/tests/**/test_*.py for minimal cleanup changes in solune/backend/src/
- [ ] T043 [P] [US5] Add or update frontend regression tests in existing files under solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx for minimal cleanup changes in solune/frontend/src/

### Implementation for User Story 5

- [ ] T044 [P] [US5] Audit dead code, unused imports, and unreachable branches and apply minimal fixes in solune/backend/src/, solune/frontend/src/, and the lint-scoped paths governed by solune/backend/pyproject.toml and solune/frontend/eslint.config.js
- [ ] T045 [P] [US5] Audit duplicated logic that can be consolidated without public-API changes and apply minimal fixes in solune/backend/src/api/, solune/backend/src/services/, solune/frontend/src/hooks/, and solune/frontend/src/utils/
- [ ] T046 [P] [US5] Audit silent failures and missing diagnostics and add minimal logging or error feedback in solune/backend/src/logging_utils.py, solune/backend/src/services/, and solune/frontend/src/services/
- [ ] T047 [P] [US5] Audit hardcoded values that should already be configurable and apply minimal fixes in solune/backend/src/config.py, solune/backend/src/main.py, solune/frontend/src/services/, and solune/frontend/src/utils/
- [ ] T048 [US5] Verify User Story 5 with ruff check src tests in solune/backend/, npm run lint in solune/frontend/, and targeted regression tests for every changed file under solune/backend/tests/ and solune/frontend/src/

**Checkpoint**: Low-risk code-quality bugs are cleaned up without scope creep.

---

## Phase 8: User Story 6 - Ambiguous Issue Documentation (Priority: P3)

**Goal**: Capture every unresolved trade-off with an inline TODO(bug-bash) comment and publish an accurate final summary table for all fixed and flagged findings.

**Independent Test**: Every ambiguous issue has a correctly formatted TODO(bug-bash) comment in source, every summary row conforms to specs/001-bug-basher/contracts/bug-report.yaml, and no ambiguous case was silently “fixed” without explicit justification.

### Tests for User Story 6 ⚠️

- [ ] T049 [P] [US6] Add or update automated validation for TODO(bug-bash) comment format in solune/backend/tests/architecture/test_bug_bash_todos.py covering affected files under solune/backend/src/ and solune/frontend/src/
- [ ] T050 [P] [US6] Add or update automated validation for summary-table rows in solune/backend/tests/architecture/test_bug_bash_report_contract.py using specs/001-bug-basher/contracts/bug-report.yaml and specs/001-bug-basher/data-model.md

### Implementation for User Story 6

- [ ] T051 [P] [US6] Add TODO(bug-bash) comments for ambiguous backend decisions directly in affected files under solune/backend/src/ using the format defined in specs/001-bug-basher/research.md
- [ ] T052 [P] [US6] Add TODO(bug-bash) comments for ambiguous frontend decisions directly in affected files under solune/frontend/src/ using the format defined in specs/001-bug-basher/research.md
- [ ] T053 [US6] Compile the final summary table for all fixed and flagged findings using specs/001-bug-basher/contracts/bug-report.yaml and publish the content from this contract in the issue or PR summary
- [ ] T054 [US6] Cross-check every summary row against changed files under solune/backend/src/, solune/frontend/src/, solune/backend/tests/, and solune/frontend/src/**/*.test.tsx to confirm Fixed vs Flagged status is accurate

**Checkpoint**: Every ambiguous item is documented in code and every finding is represented in the final summary output.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Run the full validation pipeline and verify the final delivery stays within the issue constraints.

- [ ] T055 [P] Run the full backend validation pipeline from specs/001-bug-basher/quickstart.md in solune/backend/ using the commands defined by solune/backend/pyproject.toml
- [ ] T056 [P] Run the full frontend validation pipeline from specs/001-bug-basher/quickstart.md in solune/frontend/ using the scripts defined by solune/frontend/package.json
- [ ] T057 Re-run repository-wide TODO(bug-bash) discovery under solune/backend/src/ and solune/frontend/src/ and reconcile flagged items with specs/001-bug-basher/contracts/bug-report.yaml
- [ ] T058 Review all changed files under solune/backend/src/, solune/frontend/src/, solune/backend/tests/, and solune/frontend/src/**/*.test.tsx to ensure every fix remains minimal, focused, dependency-free, and API-compatible with specs/001-bug-basher/spec.md
- [ ] T059 Confirm the final delivery satisfies the verification checklist in specs/001-bug-basher/quickstart.md and the constraints in specs/001-bug-basher/spec.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** → no dependencies
- **Phase 2: Foundational** → depends on Setup and blocks all user stories
- **Phase 3: US1 Security** → depends on Foundational; establishes the MVP security-hardened baseline
- **Phase 4: US2 Runtime** → depends on US1, matching the category order in specs/001-bug-basher/research.md
- **Phase 5: US3 Logic** → depends on US2
- **Phase 6: US4 Test Quality** → depends on US3
- **Phase 7: US5 Code Quality** → depends on US4
- **Phase 8: US6 Ambiguous Issue Documentation** → depends on outputs from US1-US5, though TODO(bug-bash) comments should be added during each earlier story as issues are found
- **Phase 9: Polish** → depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Starts immediately after Foundational and is the recommended MVP scope
- **US2 (P1)**: Starts after US1 because runtime fixes should build on the hardened security baseline
- **US3 (P2)**: Starts after US2 so logic fixes are evaluated on stabilized runtime paths
- **US4 (P2)**: Starts after US3 so test improvements target the final fixed behavior
- **US5 (P3)**: Starts after US4 to avoid cleanup conflicts while higher-priority fixes are still moving
- **US6 (P3)**: Finalizes after US1-US5 because the summary table and flagged-item inventory depend on the full audit output

### Within Each User Story

- Add or update regression tests before finalizing the corresponding code change
- Fix source files before updating the summary output for that category
- Add `TODO(bug-bash)` comments only for truly ambiguous cases that cannot be resolved without human product or architecture input
- Keep each fix limited to the audited bug and its directly affected tests

### Parallel Opportunities

- Setup tasks marked **[P]** can run in parallel between backend and frontend
- Foundational checklist-building tasks marked **[P]** can run in parallel for backend vs frontend scope
- Within each user story, backend and frontend regression-test tasks can run in parallel
- Within each user story, backend and frontend audit tasks marked **[P]** can run in parallel when they touch different paths
- Do **not** run entire user stories in parallel; `research.md` explicitly chooses sequential category passes to avoid rework and merge conflicts

---

## Parallel Example: User Story 1

```bash
# Tests in parallel
Task: "T012 Add or update backend security regression tests in solune/backend/tests/unit/ and solune/backend/tests/integration/"
Task: "T013 Add or update frontend security regression tests in solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx"

# Audits in parallel
Task: "T015 Audit auth/CORS/dependency guards in solune/backend/src/middleware/, solune/backend/src/dependencies.py, solune/backend/src/config.py, and solune/backend/src/main.py"
Task: "T017 Audit frontend security handling in solune/frontend/src/components/, solune/frontend/src/hooks/, solune/frontend/src/services/, and solune/frontend/src/utils/"
```

## Parallel Example: User Story 2

```bash
# Tests in parallel
Task: "T020 Add or update backend runtime regression tests in solune/backend/tests/unit/, solune/backend/tests/integration/, and solune/backend/tests/concurrency/"
Task: "T021 Add or update frontend runtime regression tests in solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx"

# Audits in parallel
Task: "T023 Audit backend null/resource-management paths in solune/backend/src/services/, solune/backend/src/utils.py, solune/backend/src/dependencies.py, and solune/backend/src/migrations/"
Task: "T025 Audit frontend runtime safety in solune/frontend/src/hooks/, solune/frontend/src/services/, and solune/frontend/src/components/"
```

## Parallel Example: User Story 3

```bash
# Tests in parallel
Task: "T028 Add or update backend logic regression tests in solune/backend/tests/unit/ and solune/backend/tests/integration/"
Task: "T029 Add or update frontend logic regression tests in solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx"

# Audits in parallel
Task: "T030 Audit workflow/state transitions in solune/backend/src/services/workflow_orchestrator/ and solune/backend/src/services/pipelines/"
Task: "T033 Audit frontend API-client and UI-state logic in solune/frontend/src/services/, solune/frontend/src/hooks/, and solune/frontend/src/components/"
```

## Parallel Example: User Story 4

```bash
# Coverage work in parallel
Task: "T035 Add or update backend regression and coverage tests in solune/backend/tests/unit/, solune/backend/tests/integration/, solune/backend/tests/property/, and solune/backend/tests/concurrency/"
Task: "T036 Add or update frontend regression and coverage tests in solune/frontend/src/**/*.test.ts, solune/frontend/src/**/*.test.tsx, and solune/frontend/e2e/"

# Audit work in parallel
Task: "T037 Audit mock leakage in solune/backend/tests/"
Task: "T038 Audit tautological tests in solune/backend/tests/, solune/frontend/src/__tests__/, and collocated tests under solune/frontend/src/"
```

## Parallel Example: User Story 5

```bash
# Tests in parallel
Task: "T042 Add or update backend regression tests in solune/backend/tests/**/test_*.py"
Task: "T043 Add or update frontend regression tests in solune/frontend/src/**/*.test.ts and solune/frontend/src/**/*.test.tsx"

# Cleanup work in parallel
Task: "T044 Audit dead code and unreachable branches in solune/backend/src/ and solune/frontend/src/"
Task: "T046 Audit silent failures in solune/backend/src/logging_utils.py, solune/backend/src/services/, and solune/frontend/src/services/"
```

## Parallel Example: User Story 6

```bash
# Validation work in parallel
Task: "T049 Add or update TODO(bug-bash) format validation in solune/backend/tests/architecture/test_bug_bash_todos.py"
Task: "T050 Add or update summary-table contract validation in solune/backend/tests/architecture/test_bug_bash_report_contract.py"

# Documentation work in parallel
Task: "T051 Add TODO(bug-bash) comments in affected files under solune/backend/src/"
Task: "T052 Add TODO(bug-bash) comments in affected files under solune/frontend/src/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete **Phase 1: Setup**
2. Complete **Phase 2: Foundational**
3. Complete **Phase 3: US1 Security Vulnerability Remediation**
4. **Stop and validate** with Bandit, frontend lint/security checks, and the new security regression tests
5. Use the hardened codebase as the baseline for all later category passes

### Incremental Delivery

1. Setup + Foundational establish the rules of engagement and validation pipeline
2. Deliver **US1** to remove the highest-risk vulnerabilities first
3. Deliver **US2** to stabilize runtime behavior on top of the security baseline
4. Deliver **US3** to correct workflow, API, and boundary-condition logic
5. Deliver **US4** to strengthen regression protection around the fixed behavior
6. Deliver **US5** to remove remaining low-risk quality defects without scope creep
7. Deliver **US6** to finalize all TODO(bug-bash) decisions and publish the required summary table
8. Finish with **Phase 9 Polish** to ensure the full backend/frontend validation pipeline is green

### Parallel Team Strategy

1. One engineer handles backend setup while another handles frontend setup in **Phase 1**
2. Split backend vs frontend scope for the **[P]** tasks inside each story, but keep the stories themselves sequential
3. Reserve one reviewer to maintain the running summary table contract in specs/001-bug-basher/contracts/bug-report.yaml terms while implementation proceeds
4. Publish the final summary only after all category passes and validation tasks are complete

---

## Notes

- Every task in user-story phases includes a `[US#]` label for traceability back to `/specs/001-bug-basher/spec.md`
- Tests are mandatory because the spec requires at least one regression test per clear fix.
- The final summary table is an external delivery artifact (issue or PR summary), but its required structure is defined by `specs/001-bug-basher/contracts/bug-report.yaml`
- Use the exact `TODO(bug-bash)` formats from `specs/001-bug-basher/research.md` and `specs/001-bug-basher/data-model.md`
- Keep fixes minimal: no new dependencies, no architecture changes, no public API changes, and no drive-by refactors
