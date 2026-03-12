# Tasks: Bug Basher — Full Codebase Review & Fix

**Input**: Design documents from `/specs/037-bug-basher/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Regression tests are required for every obvious bug fix per `specs/037-bug-basher/spec.md` FR-003. Each user story therefore starts with explicit test work before implementation.

**Organization**: Tasks are grouped by user story to preserve the issue’s priority order: Security → Runtime → Logic → Test Quality → Code Quality. Setup and Foundational phases establish the review inventory, baseline validation, per-fix commit workflow, and findings-tracking artifacts that all bug-fix work depends on.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend app**: `backend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Frontend app**: `frontend/src/`
- **Frontend tests**: colocated `frontend/src/**/*.test.ts(x)`
- **Feature artifacts**: `specs/037-bug-basher/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Bootstrap the local environment and establish the audit baseline before touching source files.

- [ ] T001 Bootstrap the backend review environment from `backend/pyproject.toml` and the frontend review environment from `frontend/package.json` so the validation commands in `specs/037-bug-basher/quickstart.md` can run locally before fixes begin
- [ ] T002 Run the baseline commands documented in `specs/037-bug-basher/quickstart.md` against `backend/tests/unit/`, `backend/src/`, and the frontend scripts in `frontend/package.json`; record any pre-existing failures so later bug-fix validation only tracks net-new regressions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the review inventory, findings artifacts, and per-fix workflow that MUST exist before any user-story bug fixing starts.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T003 Build `specs/037-bug-basher/review-inventory.md` with every repository-authored file in scope for FR-001 — `backend/src/`, `backend/tests/unit/`, `frontend/src/`, `docs/`, `scripts/`, `.github/workflows/`, `.specify/`, and top-level authored files such as `README.md` and `docker-compose.yml` — marking which bug-category passes apply to each path per `specs/037-bug-basher/research.md`
- [ ] T004 [P] Create `specs/037-bug-basher/findings-ledger.md` in the shape required by `specs/037-bug-basher/contracts/bug-report-schema.yaml` and `specs/037-bug-basher/data-model.md`, capturing `BugReportEntry` fields (`number`, `file_path`, `line_range`, `category`, `description`, `status`, `commit_ref`, `regression_test`), TODO metadata, and final summary aggregates (`total_fixed`, `total_flagged`, `files_reviewed`, `files_with_bugs`, `files_clean`)
- [ ] T005 Establish the per-fix execution and commit loop in `specs/037-bug-basher/findings-ledger.md`: review one bug from `specs/037-bug-basher/review-inventory.md`, apply the smallest change in the exact source file, update the nearest regression test file, run the targeted test subset, create a commit using the format from `specs/037-bug-basher/research.md`, and record the resulting `commit_ref` before moving on

**Checkpoint**: Review coverage, bug tracking, and validation cadence are ready; category work can proceed in priority order.

---

## Phase 3: User Story 1 — Security Vulnerability Remediation (Priority: P1) 🎯 MVP

**Goal**: Eliminate confirmed security vulnerabilities across backend, frontend, and configuration surfaces without changing public APIs or adding dependencies.

**Independent Test**: Re-run the targeted security regression tests plus the relevant backend/frontend validation commands after each fix; confirm no remaining auth-bypass, injection, secret-exposure, or insecure-default issues in the touched files.

### Tests for User Story 1 (Required by FR-003) ⚠️

> **NOTE**: Add or update the regression tests for each confirmed security bug before finalizing the corresponding source fix.

- [ ] T006 [P] [US1] Add or strengthen security regression coverage in `backend/tests/unit/` and the nearest existing validation path named in `specs/037-bug-basher/quickstart.md` for vulnerabilities discovered in `backend/src/config.py`, `backend/src/constants.py`, `backend/src/dependencies.py`, `backend/src/api/`, `backend/src/middleware/`, `backend/src/services/database.py`, `backend/src/services/encryption.py`, `backend/src/prompts/`, and any runtime-consumed repo files listed in `specs/037-bug-basher/review-inventory.md`
- [ ] T007 [P] [US1] Add or strengthen frontend security regression tests in colocated files under `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/pages/`, `frontend/src/services/`, and `frontend/src/utils/` for XSS, credential exposure, unsafe storage, or other confirmed client-side security issues

### Implementation for User Story 1

- [ ] T008 [P] [US1] Audit and fix hardcoded secrets or insecure defaults in `backend/src/config.py`, `backend/src/constants.py`, `docker-compose.yml`, `README.md`, `.env.example` (if present), `.github/workflows/`, `.specify/`, and `scripts/` wherever `specs/037-bug-basher/review-inventory.md` identifies a runtime-consumed security issue, replacing unsafe values with existing environment-driven configuration patterns
- [ ] T009 [P] [US1] Audit and fix authentication, authorization, and request-validation vulnerabilities in `backend/src/api/`, `backend/src/middleware/`, and `backend/src/dependencies.py` with minimal guards that preserve the existing REST surface
- [ ] T010 [P] [US1] Audit and fix injection, query-safety, and cryptography issues in `backend/src/services/database.py`, `backend/src/services/encryption.py`, `backend/src/services/github_projects/`, and `backend/src/prompts/`
- [ ] T011 [P] [US1] Audit and fix frontend security issues in `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/pages/`, `frontend/src/services/`, and `frontend/src/utils/`, including unsafe HTML rendering, credential persistence, and unvalidated user input flows
- [ ] T012 [US1] Add `TODO(bug-bash)` comments in the exact security-sensitive files under `backend/src/`, `frontend/src/`, `.github/workflows/`, `.specify/`, `scripts/`, or the relevant top-level config file using the format from `specs/037-bug-basher/data-model.md` (`issue description`, `Options: ...`, `Needs human decision because: ...`) whenever a vulnerability cannot be fixed safely, and record each flagged item in `specs/037-bug-basher/findings-ledger.md`

**Checkpoint**: Security-critical defects are either fixed with regression coverage or explicitly flagged with `TODO(bug-bash)` comments and ledger entries.

---

## Phase 4: User Story 2 — Runtime Error Elimination (Priority: P2)

**Goal**: Remove confirmed crash paths, missing imports, null/undefined failures, and resource-leak issues across backend and frontend execution paths.

**Independent Test**: Re-run the targeted runtime regression tests after each fix and confirm the affected code paths no longer raise unhandled exceptions, leak resources, or fail on null/undefined input.

### Tests for User Story 2 (Required by FR-003) ⚠️

- [ ] T013 [P] [US2] Add or strengthen backend runtime regression tests in `backend/tests/unit/` for failures discovered in `backend/src/api/`, `backend/src/services/`, `backend/src/dependencies.py`, `backend/src/main.py`, and `backend/src/utils.py`, covering null guards, import/load failures, cleanup paths, and exception handling
- [ ] T014 [P] [US2] Add or strengthen frontend runtime regression tests in colocated files under `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/services/`, `frontend/src/lib/`, and `frontend/src/pages/` for undefined access, async cleanup, rejected promises, and race-condition scenarios

### Implementation for User Story 2

- [ ] T015 [P] [US2] Fix runtime defects in `backend/src/api/`, `backend/src/services/`, `backend/src/dependencies.py`, `backend/src/main.py`, `backend/src/utils.py`, and any executable automation files in `scripts/`, `.github/workflows/`, or `.specify/` identified by `specs/037-bug-basher/review-inventory.md`, including unhandled exceptions, missing imports, null references, and cleanup bugs
- [ ] T016 [P] [US2] Fix frontend runtime defects in `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/services/`, `frontend/src/lib/`, and `frontend/src/pages/`, including null/undefined guards, stale async updates, and missing cleanup on unmount
- [ ] T017 [US2] Add `TODO(bug-bash)` comments in the exact runtime-affected files under `backend/src/`, `frontend/src/`, `scripts/`, `.github/workflows/`, or `.specify/` using the format from `specs/037-bug-basher/data-model.md` whenever the safest fix would require changing the public API or architecture forbidden by `specs/037-bug-basher/spec.md`

**Checkpoint**: Known crash paths are removed or explicitly flagged, and each fix is backed by regression coverage.

---

## Phase 5: User Story 3 — Logic Bug Correction (Priority: P3)

**Goal**: Correct confirmed state-transition, branching, boundary-condition, API-parameter, and return-value bugs while preserving existing external contracts.

**Independent Test**: Run the targeted logic regression tests for each corrected bug and confirm the affected workflows now produce the expected states, outputs, and side effects at their edge conditions.

### Tests for User Story 3 (Required by FR-003) ⚠️

- [ ] T018 [P] [US3] Add or strengthen backend logic regression tests in `backend/tests/unit/` for defects found in `backend/src/services/workflow_orchestrator/`, `backend/src/services/github_projects/`, `backend/src/api/`, `backend/src/models/`, and `backend/src/utils.py`
- [ ] T019 [P] [US3] Add or strengthen frontend logic regression tests in colocated files under `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/pages/`, `frontend/src/services/`, and `frontend/src/utils/` for incorrect state updates, broken branching, event-handler flaws, or wrong derived values

### Implementation for User Story 3

- [ ] T020 [P] [US3] Fix logic defects in `backend/src/services/workflow_orchestrator/`, `backend/src/services/github_projects/`, `backend/src/api/`, `backend/src/models/`, `backend/src/utils.py`, and any authored automation/config logic in `scripts/`, `.github/workflows/`, or `.specify/` identified by `specs/037-bug-basher/review-inventory.md`, focusing on incorrect transitions, wrong parameters, off-by-one logic, and invalid return values
- [ ] T021 [P] [US3] Fix frontend logic defects in `frontend/src/components/`, `frontend/src/hooks/`, `frontend/src/pages/`, `frontend/src/services/`, and `frontend/src/utils/`, focusing on rendering branches, state sequencing, and event-driven control flow
- [ ] T022 [US3] Add `TODO(bug-bash)` comments in ambiguous logic hotspots under `backend/src/`, `frontend/src/`, `scripts/`, `.github/workflows/`, or `.specify/` using the format from `specs/037-bug-basher/data-model.md` whenever multiple plausible behaviors exist and a human product or architecture decision is required

**Checkpoint**: Confirmed correctness bugs are fixed or clearly flagged, and the new regression tests pin the intended behavior.

---

## Phase 6: User Story 4 — Test Quality Improvement (Priority: P4)

**Goal**: Ensure the test suite fails for the right reasons by removing weak assertions, mock leaks, and missing coverage around the bugs fixed in earlier phases.

**Independent Test**: Re-run the improved tests after intentionally reasoning about the guarded behavior; confirm each changed test would fail if the associated bug were reintroduced and that mocks no longer leak into production paths.

### Tests for User Story 4 (Required by FR-003 / FR-004) ⚠️

- [ ] T023 [P] [US4] Audit and strengthen backend tests in `backend/tests/unit/` that cover the source files touched in Phases 3–5, replacing weak assertions, adding negative-path checks, and tightening fixture usage around `backend/src/`
- [ ] T024 [P] [US4] Audit and strengthen frontend tests in colocated `frontend/src/**/*.test.ts(x)` files that cover the source files touched in Phases 3–5, replacing weak assertions, adding meaningful interaction coverage, and removing false-positive expectations

### Implementation for User Story 4

- [ ] T025 [P] [US4] Remove backend mock leaks, shared-state issues, and non-deterministic patches in `backend/tests/unit/`, especially where `MagicMock` or `Mock` values can flow into file paths, database paths, URLs, or other production inputs exercised by `backend/src/`
- [ ] T026 [P] [US4] Remove frontend mock leaks and cleanup gaps in colocated tests under `frontend/src/`, ensuring timers, spies, DOM state, and async mocks are reset between test cases
- [ ] T027 [US4] Backfill missing regression coverage in the exact `backend/tests/unit/` and `frontend/src/**/*.test.ts(x)` files touched by Phases 3–5 so every fixed bug in `backend/src/` or `frontend/src/` is linked to at least one named guard test in the findings ledger

**Checkpoint**: The tests that guard fixed bugs are trustworthy, isolated, and traceable back to the findings ledger.

---

## Phase 7: User Story 5 — Code Quality Cleanup (Priority: P5)

**Goal**: Remove or explicitly flag dead code, unreachable branches, duplicated logic, and silent failures that still represent real bugs or maintenance hazards.

**Independent Test**: Run the targeted regression tests and relevant existing suites after each cleanup change; confirm removed branches were truly dead, surfaced errors are now observable, and deduplicated logic still behaves correctly.

### Tests for User Story 5 (Required for any actual bug fix) ⚠️

- [ ] T028 [P] [US5] Add or strengthen backend regression tests in `backend/tests/unit/` for silent-failure paths, deduplicated helper behavior, and reachable replacement branches in the `backend/src/` files cleaned up during this phase
- [ ] T029 [P] [US5] Add or strengthen frontend regression tests in colocated `frontend/src/**/*.test.ts(x)` files for silent-failure UI/service paths, deduplicated client logic, and any code-quality bug fix applied under `frontend/src/`

### Implementation for User Story 5

- [ ] T030 [P] [US5] Remove dead code, unreachable branches, and silent failures in `backend/src/`, `scripts/`, `.github/workflows/`, and `.specify/` wherever the intended behavior is obvious, surfacing errors with existing logging or error-reporting patterns instead of swallowing them
- [ ] T031 [P] [US5] Remove dead code, unreachable branches, and silent failures in `frontend/src/` wherever the intended behavior is obvious, surfacing failures through existing UI or service error-handling patterns
- [ ] T032 [US5] Consolidate clearly duplicated bug-prone logic in the exact `backend/src/`, `frontend/src/`, `scripts/`, `.github/workflows/`, or `.specify/` files where duplication caused incorrect behavior; add `TODO(bug-bash)` comments in the `specs/037-bug-basher/data-model.md` format instead of refactoring when the canonical behavior is ambiguous
- [ ] T033 [US5] Finalize `specs/037-bug-basher/findings-ledger.md` into the internal source of truth for the issue-required Markdown table, ensuring every entry includes line ranges, categories, status, `commit_ref`, `regression_test`, TODO metadata, and the summary totals defined in `specs/037-bug-basher/contracts/bug-report-schema.yaml`

**Checkpoint**: Remaining code-quality bugs are either fixed with tests or captured as explicit `TODO(bug-bash)` items in source and summary form.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Run full validation, confirm minimal diffs, and prepare the final deliverables for the bug-bash PR.

- [ ] T034 Run the full backend validation from `specs/037-bug-basher/quickstart.md`: `cd backend && python -m pytest tests/unit/ -v && python -m ruff check src/`
- [ ] T035 Run the full frontend validation from `specs/037-bug-basher/quickstart.md`: `cd frontend && npx vitest run && npm run type-check && npm run lint`
- [ ] T036 Review every modified file under `backend/src/`, `backend/tests/unit/`, `frontend/src/`, `frontend/src/**/*.test.ts(x)`, and top-level config files to confirm each change is minimal, every clear bug has a regression test, and every ambiguous issue has a `TODO(bug-bash)` comment
- [ ] T037 Publish the final PR summary table from `specs/037-bug-basher/findings-ledger.md` in the format defined by `specs/037-bug-basher/contracts/bug-report-schema.yaml`, omitting clean files per FR-014 and including every fixed or flagged finding from the source and test files touched across all five user stories

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**
- **US1 Security (Phase 3)**: Depends on Foundational completion
- **US2 Runtime (Phase 4)**: Depends on Foundational completion
- **US3 Logic (Phase 5)**: Depends on Foundational completion
- **US4 Test Quality (Phase 6)**: Depends on Foundational completion
- **US5 Code Quality (Phase 7)**: Depends on Foundational completion
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — this is the MVP because it addresses the highest-risk defects first
- **US2 (P2)**: Can start after Foundational — recommend running it after US1 for priority discipline, but it remains independently testable
- **US3 (P3)**: Can start after Foundational — recommend running it after US1/US2 so logic fixes build on a more stable codebase
- **US4 (P4)**: Can start after Foundational — often most effective after some fixes land, but it remains independently executable as written
- **US5 (P5)**: Can start after Foundational — recommend deferring until higher-priority fixes are addressed, but it does not require another story to be complete

### Within Each User Story

- Add or update regression tests before finalizing the source fix
- Fix backend and frontend issues in parallel only when they target different files
- Update `specs/037-bug-basher/findings-ledger.md` immediately after each fix, commit, or `TODO(bug-bash)` decision
- Re-run the nearest targeted tests before continuing to the next bug
- Complete the story checkpoint before moving to the next priority category when following the recommended P1→P5 delivery order

### Parallel Opportunities

- T003 and T004 can run in parallel once environment bootstrap is complete
- Within US1, backend and frontend regression tests (T006/T007) and most implementation tracks (T008–T011) can run in parallel because they target different files
- Within US2, backend and frontend test work (T013/T014) and bug-fix work (T015/T016) can run in parallel
- Within US3, backend and frontend test work (T018/T019) and logic fixes (T020/T021) can run in parallel
- Within US4, backend and frontend test hardening (T023–T026) can run in parallel
- Within US5, backend and frontend cleanup/test work (T028–T031) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch security regression work in parallel:
Task T006: "Add backend security regression tests in backend/tests/unit/ for backend/src security findings"
Task T007: "Add frontend security regression tests in frontend/src/**/*.test.ts(x) for frontend/src security findings"

# Then split backend/frontend remediation:
Task T008-T010: "Backend/config security fixes in backend/src/ and top-level config files"
Task T011: "Frontend security fixes in frontend/src/"
```

## Parallel Example: User Story 2

```bash
# Run runtime test preparation in parallel:
Task T013: "Add backend runtime regression tests in backend/tests/unit/"
Task T014: "Add frontend runtime regression tests in frontend/src/**/*.test.ts(x)"

# Then fix runtime defects in parallel:
Task T015: "Backend runtime fixes in backend/src/"
Task T016: "Frontend runtime fixes in frontend/src/"
```

## Parallel Example: User Story 3

```bash
# Prepare logic regression coverage in parallel:
Task T018: "Add backend logic regression tests in backend/tests/unit/"
Task T019: "Add frontend logic regression tests in frontend/src/**/*.test.ts(x)"

# Then correct logic defects in parallel:
Task T020: "Backend logic fixes in backend/src/"
Task T021: "Frontend logic fixes in frontend/src/"
```

## Parallel Example: User Story 4

```bash
# Harden backend and frontend tests in parallel:
Task T023: "Strengthen backend tests in backend/tests/unit/"
Task T024: "Strengthen frontend tests in frontend/src/**/*.test.ts(x)"

# Then remove test-quality hazards in parallel:
Task T025: "Remove backend mock leaks in backend/tests/unit/"
Task T026: "Remove frontend mock leaks in frontend/src/**/*.test.ts(x)"
```

## Parallel Example: User Story 5

```bash
# Prepare code-quality regression coverage in parallel:
Task T028: "Add backend cleanup regression tests in backend/tests/unit/"
Task T029: "Add frontend cleanup regression tests in frontend/src/**/*.test.ts(x)"

# Then clean backend and frontend code in parallel:
Task T030: "Backend code-quality fixes in backend/src/"
Task T031: "Frontend code-quality fixes in frontend/src/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Security)
4. **STOP and VALIDATE**: Re-run the targeted security regression suite plus the relevant commands from `specs/037-bug-basher/quickstart.md`
5. Publish the first tranche of findings and confirm the highest-risk issues are resolved before moving to runtime bugs

### Incremental Delivery

1. Setup + Foundational → review coverage and findings workflow established
2. US1 Security → validate → update summary ledger
3. US2 Runtime → validate → update summary ledger
4. US3 Logic → validate → update summary ledger
5. US4 Test Quality → validate → update summary ledger
6. US5 Code Quality → validate → publish final summary table

### Parallel Team Strategy

With multiple developers:

1. One developer owns `specs/037-bug-basher/review-inventory.md` and `specs/037-bug-basher/findings-ledger.md` (T003–T005)
2. During each user story, split backend and frontend work along the `[P]` tasks
3. Re-converge after each story to reconcile the findings ledger and run the required validation commands
4. Prefer the P1→P5 story order for delivery, but keep each story independently executable after Foundational so teams can overlap work when coordination avoids file conflicts

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 37 |
| **Setup (Phase 1)** | 2 tasks |
| **Foundational (Phase 2)** | 3 tasks |
| **US1 — Security** | 7 tasks |
| **US2 — Runtime** | 5 tasks |
| **US3 — Logic** | 5 tasks |
| **US4 — Test Quality** | 5 tasks |
| **US5 — Code Quality** | 6 tasks |
| **Polish (Phase 8)** | 4 tasks |
| **Parallel opportunities** | 6 major groups plus per-story backend/frontend splits |
| **Suggested MVP scope** | Phases 1–3 (Setup + Foundational + US1 Security) |

### Independent Test Criteria by Story

- **US1**: Targeted security regression tests pass and no confirmed auth/injection/secret issues remain in the touched files
- **US2**: Targeted runtime regression tests pass and the touched crash/leak/null paths no longer fail
- **US3**: Targeted logic regression tests pass and the corrected workflows now return the expected states and values
- **US4**: Improved tests demonstrably guard the earlier fixes and no mock leakage or false-positive assertions remain
- **US5**: Cleanup regressions pass, removed branches stay unnecessary, and every remaining ambiguous cleanup is marked with `TODO(bug-bash)`

### Format Validation

- Every task uses the required checklist format: `- [ ] T### [P?] [US?] Description with file path`
- Setup, Foundational, and Polish tasks intentionally omit story labels
- All user-story tasks include `[US1]` through `[US5]`
- All `[P]` markers are limited to tasks that can run on different files without incomplete-task dependencies

---

## Notes

- Keep fixes surgical: no drive-by refactors, no new dependencies, no public API changes
- Update the findings ledger after every fix or `TODO(bug-bash)` decision so the final summary table is easy to assemble
- If a bug spans multiple categories, fix it in the earliest applicable story and reference the same regression test from later ledger entries instead of duplicating work
