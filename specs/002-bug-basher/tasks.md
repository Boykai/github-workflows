# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/002-bug-basher/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `quickstart.md`, `contracts/`

**Tests**: Tests are required by the specification. Reuse the existing suites from `specs/002-bug-basher/quickstart.md`: backend (`uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, `uv run pyright`, `uv run bandit`, `uv run pip-audit`) and frontend (`npm run lint`, `npm run type-check`, `npm run test`, `npm audit --audit-level=high`).

**Organization**: Tasks are grouped by user story so each review pass can be implemented, validated, and reported independently while still honoring the required priority order (security → runtime/logic → test quality → code quality → summary report).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete work)
- **[Story]**: Which user story this task belongs to (`US1`, `US2`, `US3`, `US4`, `US5`)
- Include exact file paths in every task description

## Path Conventions

- **Backend source**: `solune/backend/src/`
- **Backend tests**: `solune/backend/tests/`
- **Frontend source**: `solune/frontend/src/`
- **Frontend tests**: `solune/frontend/src/__tests__/`
- **Feature docs**: `specs/002-bug-basher/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a clean baseline and a complete repository review inventory before the bug-bash passes begin.

- [ ] T001 Run the backend baseline verification from `specs/002-bug-basher/quickstart.md` in `solune/backend/` (`uv sync --dev`, `uv run pytest tests/ -x --timeout=30`, `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`) and record any pre-existing failures before modifying source files
- [ ] T002 Run the frontend baseline verification from `specs/002-bug-basher/quickstart.md` in `solune/frontend/` (`npm ci`, `npm run lint`, `npm run type-check`, `npm run test`) and record any pre-existing failures before modifying source files
- [ ] T003 Inventory the review targets under `solune/backend/src/`, `solune/backend/tests/`, `solune/frontend/src/`, `solune/frontend/src/__tests__/`, `.github/workflows/`, and repository-root config files so every file is assigned to a bug-bash pass

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared tracking and execution rules that every user-story phase depends on.

**⚠️ CRITICAL**: No user-story work should begin until the findings tracker, regression-test placement, and category-first pass plan are defined.

- [ ] T004 Build a working findings tracker from `specs/002-bug-basher/data-model.md` and `specs/002-bug-basher/contracts/bug-report.yaml` so every fix or `TODO(bug-bash)` records file, lines, category, status, commit, and regression-test reference
- [ ] T005 Define regression-test destinations in matching modules under `solune/backend/tests/` and `solune/frontend/src/__tests__/`; only fall back to `solune/backend/tests/test_regression_bugfixes.py` when no module-specific suite exists
- [ ] T006 Map the category-first review order from `specs/002-bug-basher/research.md` and `specs/002-bug-basher/plan.md` to concrete sweeps for `solune/backend/src/`, `solune/frontend/src/`, test suites, scripts, and config so later phases can execute without missing files

**Checkpoint**: Foundation ready — every future fix has a target area, a regression-test destination, and a reporting slot.

---

## Phase 3: User Story 1 — Security Vulnerability Detection and Remediation (Priority: P1) 🎯 MVP

**Goal**: Audit the entire repository for security issues, fix every clear vulnerability with a regression test, and flag ambiguous security trade-offs with `TODO(bug-bash)` comments.

**Independent Test**: Re-run the affected backend/frontend regression tests plus the security commands from `specs/002-bug-basher/quickstart.md`, then verify that auth paths, input validation, secret handling, and client-side rendering no longer expose known vulnerabilities.

### Tests for User Story 1

- [ ] T007 [P] [US1] Add or extend backend security regression tests in matching files under `solune/backend/tests/` for auth, CSRF, secret-handling, and input-validation bugs before patching the corresponding files in `solune/backend/src/`
- [ ] T008 [P] [US1] Add or extend frontend security regression tests in matching files under `solune/frontend/src/__tests__/` for XSS, unsafe URL handling, and client-side validation bugs before patching the corresponding files in `solune/frontend/src/`

### Implementation for User Story 1

- [ ] T009 [P] [US1] Audit and fix authentication and authorization flaws in `solune/backend/src/api/auth.py`, `solune/backend/src/services/github_auth.py`, `solune/backend/src/middleware/admin_guard.py`, and `solune/backend/src/middleware/csrf.py`; add `TODO(bug-bash)` comments for ambiguous cases
- [ ] T010 [P] [US1] Audit and fix secret, token, encryption, and insecure-default issues in `solune/backend/src/config.py`, `solune/backend/src/services/encryption.py`, `solune/backend/src/services/session_store.py`, `solune/backend/src/main.py`, and related repository-root environment/config files
- [ ] T011 [P] [US1] Audit and fix backend input-validation and injection risks across route handlers in `solune/backend/src/api/` and request/response models in `solune/backend/src/models/`, including webhook and SQL-adjacent code paths
- [ ] T012 [P] [US1] Audit and fix frontend XSS, markdown-rendering, and unsafe navigation risks in dynamic UI files under `solune/frontend/src/components/`, `solune/frontend/src/pages/`, and helpers under `solune/frontend/src/lib/`
- [ ] T013 [US1] Run security validation from `solune/backend/` and `solune/frontend/` (`uv run bandit -r src/ -ll -ii`, `uv run pip-audit`, `npm audit --audit-level=high`, plus affected regression tests) and update the findings tracker with every fixed or flagged security item

**Checkpoint**: Security-critical paths are fixed or explicitly flagged, and security validation is clean for all changed files.

---

## Phase 4: User Story 2 — Runtime Error and Logic Bug Resolution (Priority: P2)

**Goal**: Remove unhandled runtime failures and logic defects across backend and frontend flows without changing public APIs or architecture.

**Independent Test**: Re-run the affected regression suites and smoke-test the corrected flows so exception handling, cleanup, state transitions, and control-flow outputs match expected behavior for valid and invalid inputs.

### Tests for User Story 2

- [ ] T014 [P] [US2] Add or extend backend regression tests in matching `solune/backend/tests/` modules for unhandled exceptions, resource leaks, null access, and state-transition bugs before patching the corresponding files in `solune/backend/src/`
- [ ] T015 [P] [US2] Add or extend frontend regression tests in matching `solune/frontend/src/__tests__/` modules for async state, cleanup, race, and control-flow bugs before patching the corresponding files in `solune/frontend/src/`

### Implementation for User Story 2

- [ ] T016 [P] [US2] Audit and fix exception handling, None/type guards, and resource cleanup in `solune/backend/src/services/`, `solune/backend/src/api/`, `solune/backend/src/services/database.py`, and file-handling utilities such as `solune/backend/src/services/template_files.py`
- [ ] T017 [P] [US2] Audit and fix backend logic and state-transition bugs in `solune/backend/src/services/workflow_orchestrator/`, `solune/backend/src/services/copilot_polling/`, `solune/backend/src/services/pipelines/`, and adjacent coordinator/service modules
- [ ] T018 [P] [US2] Audit and fix frontend runtime and logic bugs in `solune/frontend/src/hooks/`, `solune/frontend/src/context/`, `solune/frontend/src/services/`, and stateful pages/components under `solune/frontend/src/pages/` and `solune/frontend/src/components/`
- [ ] T019 [US2] Run targeted runtime/logic validation from `solune/backend/` and `solune/frontend/` (affected `pytest`/`vitest` suites plus smoke paths from `specs/002-bug-basher/quickstart.md`) and update the findings tracker with every fixed or flagged runtime/logic item

**Checkpoint**: Runtime crashes, cleanup leaks, and logic defects uncovered in the P2 sweep are fixed or explicitly flagged.

---

## Phase 5: User Story 3 — Test Quality Improvement (Priority: P3)

**Goal**: Strengthen the existing test suites so bugs fixed in earlier passes are covered by meaningful, non-leaky regression tests.

**Independent Test**: Re-run the updated backend and frontend test suites with coverage-focused commands and confirm that critical paths fixed in US1/US2 are now exercised by assertions that can genuinely fail.

### Tests for User Story 3

- [ ] T020 [P] [US3] Add focused failing regression tests in affected `solune/backend/tests/` modules for bugs exposed by mock leaks, dead assertions, and untested paths before correcting the existing fixtures or assertions
- [ ] T021 [P] [US3] Add focused failing regression tests in affected `solune/frontend/src/__tests__/` modules for stale snapshots, missing assertions, and incorrectly passing UI tests before correcting the existing test code

### Implementation for User Story 3

- [ ] T022 [P] [US3] Audit and fix backend test-fixture and helper leaks in `solune/backend/tests/conftest.py`, `solune/backend/tests/unit/`, `solune/backend/tests/integration/`, `solune/backend/tests/property/`, `solune/backend/tests/fuzz/`, `solune/backend/tests/chaos/`, and `solune/backend/tests/concurrency/`
- [ ] T023 [P] [US3] Audit and fix frontend test-quality issues in `solune/frontend/src/__tests__/` and colocated `solune/frontend/src/**/*.test.ts` or `solune/frontend/src/**/*.test.tsx` files, replacing assertions that pass for the wrong reason and adding missing edge-case checks
- [ ] T024 [US3] Run coverage-oriented validation from `solune/backend/` and `solune/frontend/` (`uv run pytest tests/unit/ --cov=src --cov-report=term-missing --timeout=30`, `npm run test:coverage`) and update the findings tracker with each test-quality fix

**Checkpoint**: Every bug fixed so far has a trustworthy regression test, and weak or misleading tests have been corrected.

---

## Phase 6: User Story 4 — Code Quality Cleanup (Priority: P4)

**Goal**: Remove dead code, unreachable branches, silent failures, and other maintainability problems that remain after the functional bug passes.

**Independent Test**: Re-run the changed backend/frontend tests plus lint/type checks and confirm that removed dead code, surfaced error messages, and configurable defaults do not change externally observable behavior.

### Tests for User Story 4

- [ ] T025 [P] [US4] Add or extend backend regression tests in matching `solune/backend/tests/` modules for dead-code removal, surfaced error handling, and configurable-default fixes before patching the corresponding files in `solune/backend/src/`
- [ ] T026 [P] [US4] Add or extend frontend regression tests in matching `solune/frontend/src/__tests__/` modules for surfaced error messages, removed unreachable UI branches, and hardcoded-value cleanup before patching the corresponding files in `solune/frontend/src/`

### Implementation for User Story 4

- [ ] T027 [P] [US4] Audit and fix backend code-quality issues in `solune/backend/src/`, `solune/backend/tests/`, `.github/workflows/`, and repository-root scripts/config files; only consolidate duplication when it does not change public APIs
- [ ] T028 [P] [US4] Audit and fix frontend code-quality issues in `solune/frontend/src/`, `solune/frontend/src/__tests__/`, and frontend config/scripts under `solune/frontend/`
- [ ] T029 [US4] Run code-quality validation from `solune/backend/` and `solune/frontend/` (`uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, `uv run pyright src/`, `npm run lint`, `npm run type-check`) and update the findings tracker with every fixed or flagged code-quality item

**Checkpoint**: Remaining code-quality findings are resolved or flagged without altering public interfaces or introducing new dependencies.

---

## Phase 7: User Story 5 — Summary Report Generation (Priority: P5)

**Goal**: Produce the final bug-bash summary table with complete traceability from each finding to its fix, test, or `TODO(bug-bash)` comment.

**Independent Test**: Validate that the final report includes every fixed or flagged finding, omits files with no bugs, and matches the schema and column order required by the feature contract.

### Implementation for User Story 5

- [ ] T030 [US5] Compile the final `BugFinding` inventory from all modified files under `solune/backend/`, `solune/frontend/`, `.github/`, and repository-root config paths using the schema in `specs/002-bug-basher/contracts/bug-report.yaml`
- [ ] T031 [US5] Verify every ✅ Fixed finding links to a regression test in `solune/backend/tests/` or `solune/frontend/src/__tests__/` and every ⚠️ Flagged finding links to a `TODO(bug-bash)` comment in the affected source file
- [ ] T032 [US5] Produce the final summary table for the PR or issue using the column order and validation rules in `specs/002-bug-basher/contracts/bug-report.yaml` and `specs/002-bug-basher/data-model.md`, omitting files with no bugs

**Checkpoint**: The summary report is complete, schema-aligned, and ready to share with stakeholders.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Perform the final full-suite validation and scope review across every bug-bash phase.

- [ ] T033 [P] Run the full backend verification suite from `solune/backend/` (`uv run pytest tests/ --timeout=30`, `uv run ruff check src/ tests/`, `uv run ruff format --check src/ tests/`, `uv run pyright src/`, `uv run bandit -r src/ -ll -ii`, `uv run pip-audit`)
- [ ] T034 [P] Run the full frontend verification suite from `solune/frontend/` (`npm run lint`, `npm run type-check`, `npm run test`, `npm audit --audit-level=high`)
- [ ] T035 Review the final diff across `solune/backend/`, `solune/frontend/`, `.github/`, and repository-root files to confirm there are no architecture changes, public-API changes, or new dependencies
- [ ] T036 Run the full verification checklist in `specs/002-bug-basher/quickstart.md` and confirm the findings tracker plus final summary table are complete before handing off the bug-bash results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately
- **Foundational (Phase 2)**: Depends on Setup completion — blocks all user stories
- **User Story 1 / Security (Phase 3)**: Depends on Foundational completion — highest-priority MVP
- **User Story 2 / Runtime + Logic (Phase 4)**: Depends on User Story 1 completion so security fixes land before broader behavioral changes
- **User Story 3 / Test Quality (Phase 5)**: Depends on User Stories 1–2 because it hardens and extends the regression coverage for those fixes
- **User Story 4 / Code Quality (Phase 6)**: Depends on User Stories 1–3 because cleanup should happen only after functional fixes and test hardening are in place
- **User Story 5 / Summary Report (Phase 7)**: Depends on User Stories 1–4 so the report includes the final fixed/flagged inventory
- **Polish (Phase 8)**: Depends on all prior phases

### User Story Dependencies

- **US1 (P1)**: Starts after T001–T006; internal order is T007–T008 → T009–T012 → T013
- **US2 (P2)**: Starts after US1 is complete; internal order is T014–T015 → T016–T018 → T019
- **US3 (P3)**: Starts after US2 is complete; internal order is T020–T021 → T022–T023 → T024
- **US4 (P4)**: Starts after US3 is complete; internal order is T025–T026 → T027–T028 → T029
- **US5 (P5)**: Starts after US4 is complete; internal order is T030 → T031 → T032

### Parallel Opportunities

- T007 and T008 can run in parallel because backend and frontend security tests live in different directories
- T009, T010, T011, and T012 can run in parallel once the security tests are outlined because they target different security surfaces
- T014 and T015 can run in parallel, followed by T016, T017, and T018 in parallel across backend/frontend runtime domains
- T020 and T021 can run in parallel, followed by T022 and T023 in parallel across backend/frontend test suites
- T025 and T026 can run in parallel, followed by T027 and T028 in parallel across backend/frontend code-quality surfaces
- T033 and T034 can run in parallel for final backend/frontend verification

---

## Parallel Example: User Story 1

```bash
# Backend and frontend security regression tests can be prepared at the same time:
Task T007: "Add or extend backend security regression tests under solune/backend/tests/"
Task T008: "Add or extend frontend security regression tests under solune/frontend/src/__tests__/"

# After the tests are outlined, split the security audit by surface:
Task T009: "Audit auth/authz files in solune/backend/src/api/auth.py and middleware/services"
Task T010: "Audit config, encryption, and session handling in solune/backend/src/config.py and services"
Task T011: "Audit input validation across solune/backend/src/api/ and solune/backend/src/models/"
Task T012: "Audit XSS and unsafe navigation risks in solune/frontend/src/components/, pages/, and lib/"
```

## Parallel Example: User Story 2

```bash
# Prepare regression tests in parallel:
Task T014: "Add backend runtime/logic regression tests under solune/backend/tests/"
Task T015: "Add frontend runtime/logic regression tests under solune/frontend/src/__tests__/"

# Then split implementation by execution surface:
Task T016: "Fix backend exception handling and resource cleanup in solune/backend/src/services/ and api/"
Task T017: "Fix backend workflow/pipeline state transitions in solune/backend/src/services/workflow_orchestrator/ and related modules"
Task T018: "Fix frontend runtime and control-flow bugs in solune/frontend/src/hooks/, context/, services/, pages/, and components/"
```

## Parallel Example: User Story 3

```bash
# Backend and frontend test-quality work can proceed independently:
Task T020: "Add backend failing regression tests in solune/backend/tests/"
Task T021: "Add frontend failing regression tests in solune/frontend/src/__tests__/"

Task T022: "Fix backend fixture/mock leaks and weak assertions across solune/backend/tests/"
Task T023: "Fix frontend weak assertions and missing edge-case checks across solune/frontend/src/__tests__/"
```

## Parallel Example: User Story 4

```bash
# Start with parallel regression coverage:
Task T025: "Add backend code-quality regression tests under solune/backend/tests/"
Task T026: "Add frontend code-quality regression tests under solune/frontend/src/__tests__/"

# Then split cleanup by stack:
Task T027: "Fix backend dead code, silent failures, and duplication across solune/backend/src/ and repo scripts"
Task T028: "Fix frontend dead code, hardcoded values, and unreachable branches across solune/frontend/src/"
```

## Parallel Example: User Story 5

```bash
# Summary generation is mostly sequential, but evidence gathering can be parallelized:
Task T030: "Compile findings from changed backend, frontend, workflow, and config files"
Task T031: "Verify regression-test links and TODO(bug-bash) links in the affected source and test files"
Task T032: "Assemble the final summary table using specs/002-bug-basher/contracts/bug-report.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 — Security Vulnerability Detection and Remediation
4. **STOP and VALIDATE**: Re-run the US1 security checks and confirm the findings tracker is accurate
5. Share the security-only results if the bug bash must ship incrementally

### Incremental Delivery

1. Setup + Foundational → repository inventory, tracker, and test destinations ready
2. Add User Story 1 → validate security fixes and TODOs
3. Add User Story 2 → validate runtime/logic fixes
4. Add User Story 3 → harden regression coverage for earlier fixes
5. Add User Story 4 → clean up remaining code-quality issues
6. Add User Story 5 → publish the final summary report
7. Finish with Phase 8 full-suite verification

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. During each user-story phase, split backend and frontend [P] tasks across engineers
3. Rejoin for each story-level validation task (`T013`, `T019`, `T024`, `T029`, `T032`)
4. Rejoin again for final verification (`T033`–`T036`)

---

## Notes

- Every fixed bug must have at least one regression test in `solune/backend/tests/` or `solune/frontend/src/__tests__/`
- Every ambiguous issue must become a `TODO(bug-bash)` comment in the affected source file
- Do not change architecture, public APIs, or dependencies while completing these tasks
- Files with no bugs must not appear in the final summary table
- Reuse the existing commands and tools already configured in `solune/backend/pyproject.toml` and `solune/frontend/package.json`
