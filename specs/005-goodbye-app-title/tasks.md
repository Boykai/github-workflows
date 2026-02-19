# Tasks: Update App Title to "Goodbye"

**Input**: Design documents from `/specs/005-goodbye-app-title/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md
**Tests**: Not explicitly requested in feature specification. Existing E2E test assertions must be updated to match the new title but no new test files are required.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/` (backend requires no changes)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Audit current title references to confirm scope of changes

- [x] T001 Audit all occurrences of "Agent Projects" in the repository to confirm the 6 files identified in research.md (3 source + 3 E2E test files)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: N/A — no foundational infrastructure changes are required for this feature. The title is a static display string with no dependencies on models, services, or configuration systems.

**Checkpoint**: No blocking prerequisites — user story implementation can begin immediately after audit.

---

## Phase 3: User Story 1 — App Title Displays "Goodbye" Everywhere (Priority: P1) 🎯 MVP

**Goal**: Replace "Agent Projects" with "Goodbye" in all user-facing surfaces — browser tab title and page headings.

**Independent Test**: Open the application in a browser → verify the browser tab displays "Goodbye" → verify the login page heading reads "Goodbye" → verify the authenticated app header reads "Goodbye".

### Implementation for User Story 1

- [x] T002 [P] [US1] Update `<title>` tag from "Agent Projects" to "Goodbye" in frontend/index.html (line 7)
- [x] T003 [US1] Update both `<h1>` elements from "Agent Projects" to "Goodbye" in frontend/src/App.tsx (lines 72 and 89)

**Checkpoint**: MVP complete — all user-facing title surfaces display "Goodbye". Browser tab, login page heading, and app header all show the new title.

---

## Phase 4: User Story 2 — Title-Dependent Tests Pass After Update (Priority: P2)

**Goal**: Update all E2E test assertions that reference the old title to expect "Goodbye", ensuring CI/CD pipeline remains green.

**Independent Test**: Run the full E2E test suite (`npm run test:e2e`) → all tests pass with zero failures.

### Implementation for User Story 2

- [x] T004 [P] [US2] Update all "Agent Projects" assertions (5 heading + 1 title) to "Goodbye" in frontend/e2e/auth.spec.ts
- [x] T005 [P] [US2] Update all "Agent Projects" heading assertions (2 occurrences) to "Goodbye" in frontend/e2e/ui.spec.ts
- [x] T006 [P] [US2] Update "Agent Projects" heading assertion (1 occurrence) to "Goodbye" in frontend/e2e/integration.spec.ts

**Checkpoint**: All E2E test assertions updated — full test suite passes with zero regressions.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all changes

- [x] T007 Run quickstart.md verification checklist — confirm all manual and automated checks from specs/005-goodbye-app-title/quickstart.md pass (browser tab, login heading, app heading, lint, type-check, tests)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: N/A — no blocking prerequisites for this feature
- **US1 (Phase 3)**: Can start immediately after audit (Phase 1)
- **US2 (Phase 4)**: Can start in parallel with Phase 3 (different files) but logically depends on knowing the new title
- **Polish (Phase 5)**: Depends on Phases 3 and 4 being complete

### User Story Dependencies

- **US1 (P1)**: No dependencies on other stories — standalone source file changes
- **US2 (P2)**: No code dependency on US1 (different files), but logically should use the same replacement string "Goodbye"

### Within Each Phase

- Phase 3: T002 and T003 can run in parallel (different files)
- Phase 4: T004, T005, and T006 can all run in parallel (different files)

### Parallel Opportunities

Within Phase 3:
- T002 (index.html) and T003 (App.tsx) are in different files — can run in parallel

Within Phase 4:
- T004, T005, T006 are all in different E2E test files — can all run in parallel

Cross-phase:
- Phase 3 and Phase 4 operate on entirely different files — can run in parallel if desired

---

## Parallel Example: Phase 3 (US1) + Phase 4 (US2)

```
# All source file updates (Phase 3) — parallel:
T002: Update <title> in frontend/index.html
T003: Update <h1> elements in frontend/src/App.tsx

# All E2E test updates (Phase 4) — parallel:
T004: Update assertions in frontend/e2e/auth.spec.ts
T005: Update assertions in frontend/e2e/ui.spec.ts
T006: Update assertions in frontend/e2e/integration.spec.ts

# Since Phase 3 and Phase 4 touch different files, ALL 5 tasks (T002-T006) can run in parallel
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 3)

1. Complete Phase 1: Audit title references
2. Complete Phase 3: US1 (update source files)
3. **STOP and VALIDATE**: Open app in browser — "Goodbye" appears in tab, login heading, and app heading
4. Deploy/demo if ready

### Incremental Delivery

1. Audit → Confirm scope (6 files, 3 source + 3 test)
2. Update source files (US1) → "Goodbye" visible everywhere → **MVP!**
3. Update test assertions (US2) → CI/CD pipeline green → **Production-ready**
4. Run full verification → quickstart.md checklist passes → Complete

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 7 |
| US1 tasks | 2 (T002, T003) |
| US2 tasks | 3 (T004, T005, T006) |
| Setup/Polish tasks | 2 (T001, T007) |
| Parallel opportunities | 5 tasks (T002–T006) can all run in parallel |
| Files modified | 5 (index.html, App.tsx, auth.spec.ts, ui.spec.ts, integration.spec.ts) |
| MVP scope | US1 only (Phase 3 — 2 tasks) |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- This is a display-only text change — no functional logic, routing, or API behavior is affected
- Code comments referencing "Agent Projects" (in types/index.ts and services/api.ts) are NOT updated per spec scope — they are not user-facing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
