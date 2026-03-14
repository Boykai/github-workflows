# Tasks: Remove Blocking Feature Entirely from Application

**Input**: Design documents from `/specs/035-remove-blocking-feature/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not included — this is a pure removal feature. No new tests are required. Existing tests that reference blocking will be updated or removed. Spec requires all existing tests pass after removal (FR-014, Constitution Check IV).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. The blocking feature was partially implemented — database migrations and integration call sites exist, but core modules (models, services) were never created. Removal proceeds from leaf references (tests, frontend mocks) inward through integration call sites to database migrations.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Backend migrations**: `backend/src/migrations/`
- **Frontend tests**: `frontend/src/components/`, `frontend/src/pages/`

---

## Phase 1: Setup (Identify Removal Scope)

**Purpose**: No setup tasks required — this is a pure removal feature. No new files, dependencies, or infrastructure to create. The codebase audit was completed in research.md (R-001) and all removal targets are identified. Proceed directly to Foundational phase.

---

## Phase 2: Foundational (Backend Test Cleanup)

**Purpose**: Remove or update backend test files that reference blocking modules. These tests import non-existent modules or mock blocking services, so they must be cleaned first to prevent import errors during subsequent phases.

**⚠️ CRITICAL**: Test files must be cleaned before service code to maintain a buildable codebase at each step.

- [x] T001 Delete entire test file `backend/tests/unit/test_chat_block.py` — this file tests `#block` detection in chat which is part of the blocking feature being removed
- [x] T002 [P] Remove `TestSkipBlockingIssue` and `TestDeleteBlockingIssue` test classes from `backend/tests/unit/test_api_board.py` — these test unimplemented blocking queue endpoints (POST skip and DELETE per contracts/blocking-queue-removal.md)
- [x] T003 [P] Remove blocking queue mock patches and references from `backend/tests/unit/test_copilot_polling.py` — clean up mock patches for `blocking_queue` service calls that were never implemented
- [x] T004 [P] Remove blocking mock references from `backend/tests/unit/test_api_pipelines.py` — clean up `blocking: false` and blocking-related mock data in pipeline test fixtures

**Checkpoint**: All backend tests that reference blocking are cleaned. `python -m pytest tests/unit/` should pass without blocking import errors.

---

## Phase 3: User Story 2 — Backend and API Operate Without Blocking Logic (Priority: P1) 🎯 MVP

**Goal**: Remove all blocking-related imports, service calls, parameters, and logic from backend services and API endpoints. After this phase, no blocking logic executes in the backend at runtime.

**Independent Test**: Start the application, exercise all API endpoints, and verify zero blocking-related fields in responses, zero blocking-related runtime errors, and all features (task views, agent pipelines, issue workflows) operate correctly.

### Implementation for User Story 2

#### Copilot Polling Services (leaf dependencies — remove first)

- [x] T005 [US2] Remove `_step_sweep_blocking_queue()` function and its Step 4c registration from `_POLL_STEPS` list in `backend/src/services/copilot_polling/polling_loop.py`
- [x] T006 [P] [US2] Remove `BlockingQueueStatus` import and blocking queue guard block (lines ~110, 124–139, 338) from `backend/src/services/copilot_polling/recovery.py`
- [x] T007 [P] [US2] Remove `mark_completed`/`mark_in_review` blocking queue calls and `_activate_queued_issue()` function from `backend/src/services/copilot_polling/pipeline.py` — preserve all "non-blocking" I/O comments (per R-003)

#### Signal Chat and Chores Services

- [x] T008 [P] [US2] Remove `with_blocking_label` import and replace `with_blocking_label([], ...)` calls with plain `[]` in `backend/src/services/signal_chat.py` — remove lines accessing `proposal.is_blocking` and `rec.is_blocking`
- [x] T009 [US2] Remove all blocking references from `backend/src/services/chores/service.py`: remove `"blocking"` key from preset dictionaries (security-review, performance-review, bug-basher), remove `"blocking"` from `_CHORE_UPDATABLE_COLUMNS` set, remove blocking flag resolution logic block, and remove blocking_queue enqueue try/except block

#### Workflow Orchestrator

- [x] T010 [US2] Remove blocking references from `backend/src/services/workflow_orchestrator/orchestrator.py`: remove `with_blocking_label` import from constants, remove blocking_queue import and enqueue logic, remove `is_blocking` parameter from `execute_full_workflow`, and replace `with_blocking_label(labels, ...)` calls with plain `labels`

#### API Layer

- [x] T011 [US2] Remove blocking references from `backend/src/api/chat.py`: remove `proposal_is_blocking` variable, remove all blocking queue enqueue code (lines ~885–887, 913–928), and remove blocking-related comments
- [x] T012 [P] [US2] Remove `is_blocking=recommendation.is_blocking` parameter from `backend/src/api/workflow.py` (line ~269)

#### Constants Cleanup

- [x] T013 [P] [US2] Remove `with_blocking_label()` function and any blocking-related constants from `backend/src/constants.py` if present — research confirms the function was never defined, but verify and remove any stub or import reference

**Checkpoint**: Backend runs with zero blocking logic. `python -m pytest tests/unit/ -v` passes. `python -m ruff check src/` produces no blocking-related lint errors. Application starts without import errors.

---

## Phase 4: User Story 3 — Database Schema Is Cleaned of Blocking Artifacts (Priority: P1)

**Goal**: Create a rollback migration that drops all blocking-related schema elements. Existing migration files 017 and 018 are preserved for migration history integrity (per R-002).

**Independent Test**: Apply migration 019 against a test database and verify: `blocking_queue` table is dropped, `blocking` column removed from `pipeline_configs` and `chores`, `pipeline_blocking_override` column removed from `project_settings`, and all remaining queries execute without errors.

### Implementation for User Story 3

- [x] T014 [US3] Create rollback migration `backend/src/migrations/019_remove_blocking.sql` that drops `blocking_queue` table, drops `blocking` column from `pipeline_configs`, drops `blocking` column from `chores`, and drops `pipeline_blocking_override` column from `project_settings` — per data-model.md and R-002

**Checkpoint**: Migration 019 exists and is syntactically correct. Schema changes are reversible via the migration history.

---

## Phase 5: User Story 1 — Application UI Is Free of All Blocking References (Priority: P1)

**Goal**: Remove all blocking-related fields from frontend test mock data. Research (R-004) confirmed that no blocking UI components exist — the blocking UI was never built. Only test mocks reference blocking fields.

**Independent Test**: Run `npx vitest run` and verify all frontend tests pass. Inspect mock data in test files and confirm zero `blocking` or `blocking_override` fields remain.

### Implementation for User Story 1

- [x] T015 [P] [US1] Remove `blocking: false` field from mock pipeline config objects in `frontend/src/components/board/ProjectIssueLaunchPanel.test.tsx`
- [x] T016 [P] [US1] Remove `blocking: false` field from mock pipeline config objects in `frontend/src/components/pipeline/SavedWorkflowsList.test.tsx`
- [x] T017 [P] [US1] Remove `blocking_override` mock references from `frontend/src/pages/ProjectsPage.test.tsx`

**Checkpoint**: All frontend tests pass with zero blocking references in mock data. `npm run type-check` and `npm run lint` produce no errors.

---

## Phase 6: User Story 4 — Codebase Contains Zero Residual Blocking References (Priority: P2)

**Goal**: Comprehensive audit confirming zero blocking feature references remain in application source code. Verify disambiguation between blocking feature identifiers and generic "non-blocking" I/O references (per R-003).

**Independent Test**: Run `grep -ri "blocking_queue\|BlockingQueue\|is_blocked\|is_blocking\|with_blocking_label\|blocking_override" backend/src/ frontend/src/` and verify zero matches. Run `grep -ri "blocking" backend/src/ frontend/src/` and verify only generic non-blocking I/O comments remain.

### Implementation for User Story 4

- [x] T018 [US4] Run comprehensive codebase grep for blocking feature identifiers across `backend/src/` and `frontend/src/` — fix any residual references missed in earlier phases
- [x] T019 [P] [US4] Review and update documentation, comments, or inline notes that reference the Blocking feature in `backend/src/` and `frontend/src/` — ensure no blocking feature documentation remains (FR-013)

**Checkpoint**: Zero blocking feature identifiers found in application source code. Only generic "non-blocking" I/O comments remain (per R-003 allowlist: pipeline.py:454, pipeline.py:486, pipeline.py:1237, recovery.py:189, recovery.py:200).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all modified files and full test suite execution.

- [x] T020 Run all backend unit tests via `cd backend && python -m pytest tests/unit/ -v` to confirm zero failures and zero blocking-related errors
- [x] T021 [P] Run all frontend tests via `cd frontend && npx vitest run` to confirm zero failures
- [x] T022 [P] Run backend linter via `cd backend && python -m ruff check src/` to confirm no lint errors
- [x] T023 [P] Run frontend type-check and linter via `cd frontend && npm run type-check && npm run lint` to confirm no errors
- [x] T024 Run comprehensive verification grep per quickstart.md checklist — confirm `grep -ri "blocking_queue\|BlockingQueue\|is_blocked\|is_blocking\|with_blocking_label\|blocking_override" backend/src/ frontend/src/` returns zero matches
- [x] T025 Verify application starts without import errors — confirm zero runtime exceptions related to blocking modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — proceed to Foundational
- **Foundational (Phase 2)**: No dependencies — start immediately. BLOCKS all user stories.
- **US2 Backend (Phase 3)**: Depends on Phase 2 (test cleanup) — service code removal after test cleanup
- **US3 Database (Phase 4)**: Depends on Phase 3 (backend code removal) — migration after code references are gone
- **US1 Frontend (Phase 5)**: Can run in parallel with Phase 3 — frontend mocks are independent of backend changes
- **US4 Audit (Phase 6)**: Depends on Phases 3, 4, 5 — comprehensive audit after all removals
- **Polish (Phase 7)**: Depends on all previous phases being complete

### User Story Dependencies

- **US2 Backend (P1)**: Can start after Phase 2 — primary removal work, all other stories depend on this
- **US3 Database (P1)**: Depends on US2 — migration must run after code references to blocking columns are removed
- **US1 Frontend (P1)**: Can start after Phase 2 — independent of backend removal (different files)
- **US4 Audit (P2)**: Depends on US1, US2, US3 — audit must run after all removals are complete

### Within Each User Story

- Leaf dependencies removed before parent dependencies (tests → services → API → database)
- Each file edited at most once per task
- Build should be green after each task group

### Parallel Opportunities

- **Phase 2**: T002, T003, T004 can all run in parallel (different test files)
- **Phase 3 (US2)**: T006, T007, T008 can run in parallel (different backend files); T012, T013 can run in parallel (different files)
- **Phase 5 (US1)**: T015, T016, T017 can all run in parallel (different frontend test files)
- **Phase 6 (US4)**: T019 can run in parallel with T018 (documentation vs. code audit)
- **Phase 7**: T021, T022, T023 can run in parallel (different toolchains)
- **Cross-story**: US1 (frontend) can proceed entirely in parallel with US2 (backend) once Phase 2 is complete

---

## Parallel Example: User Story 2 (Backend Removal)

```text
# After Phase 2 (test cleanup) is complete:

# Copilot polling services — T006 and T007 in parallel:
Parallel group A:
  Task T006: "Remove BlockingQueueStatus import from recovery.py"
  Task T007: "Remove blocking queue calls from pipeline.py"

# Signal chat and chores — T008 in parallel with T005:
Parallel group B:
  Task T005: "Remove _step_sweep_blocking_queue from polling_loop.py"
  Task T008: "Remove with_blocking_label from signal_chat.py"

# Then sequential: T009 (chores) → T010 (orchestrator) → T011 (chat.py)
# T012 and T013 can run in parallel with T011 (different files)
```

## Parallel Example: Cross-Story Parallelism

```text
# Once Phase 2 (Foundational) is complete:
Developer A (backend): US2 (Phase 3) → US3 (Phase 4) → US4 audit (Phase 6)
Developer B (frontend): US1 (Phase 5) → joins US4 audit (Phase 6)

# Both developers converge at Phase 7 (Polish) for final verification
```

---

## Implementation Strategy

### MVP First (US2 Backend + US3 Database)

1. Complete Phase 2: Foundational (backend test cleanup)
2. Complete Phase 3: US2 — Remove all backend blocking logic
3. Complete Phase 4: US3 — Create rollback migration
4. **STOP and VALIDATE**: `python -m pytest tests/unit/ -v` passes, application starts without errors
5. Deploy/demo if ready — backend is fully clean of blocking

### Incremental Delivery

1. Phase 2 (test cleanup) → Tests pass without blocking imports
2. Add Phase 3 (US2 backend removal) → Backend clean → **Core removal complete**
3. Add Phase 4 (US3 database migration) → Schema clean → **Database clean**
4. Add Phase 5 (US1 frontend mocks) → Frontend clean → **Full stack clean**
5. Add Phase 6 (US4 audit) → Comprehensive verification → **Deploy MVP!**
6. Phase 7 (Polish) → Final verification → **Release**
7. Each phase adds confidence without breaking previous phases

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 2 (test cleanup) together
2. Once Phase 2 is done:
   - Developer A: Phase 3 (backend) → Phase 4 (database) → Phase 6 (audit backend)
   - Developer B: Phase 5 (frontend) → Phase 6 (audit frontend)
3. Both converge at Phase 7 (Polish) for final verification

---

## Task Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 25 |
| **Phase 2 (Foundational)** | 4 tasks |
| **US2 Backend (Phase 3)** | 9 tasks |
| **US3 Database (Phase 4)** | 1 task |
| **US1 Frontend (Phase 5)** | 3 tasks |
| **US4 Audit (Phase 6)** | 2 tasks |
| **Polish (Phase 7)** | 6 tasks |
| **Parallel opportunities** | 6 groups identified |
| **Suggested MVP scope** | Phase 2 + Phase 3 (US2) + Phase 4 (US3) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- This is a pure removal feature — no new source code is created (only migration 019)
- Migration files 017 and 018 are preserved for migration history integrity (R-002)
- Only blocking *feature* references are removed — generic "non-blocking" I/O comments are preserved (R-003)
- Disambiguation allowlist: pipeline.py:454, pipeline.py:486, pipeline.py:1237, recovery.py:189, recovery.py:200
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Avoid: deleting historical migration files, removing generic "non-blocking" I/O references, adding new features
