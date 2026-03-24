# Tasks: Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix

**Input**: Design documents from `/specs/001-help-tour-refresh/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests ARE required — FR-012 explicitly mandates backend parametrized boundary tests and frontend `totalSteps` assertion updates.

**Organization**: Tasks are grouped by user story from spec.md. Five user stories: US1 (P1), US2 (P2), US3 (P2), US4 (P3), US5 (P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Exact file paths included in all descriptions

## Path Conventions

- **Web app (monorepo)**: `solune/backend/src/`, `solune/backend/tests/`, `solune/frontend/src/`
- Migrations: `solune/backend/src/migrations/`
- Frontend assets: `solune/frontend/src/assets/onboarding/`
- Frontend components: `solune/frontend/src/components/onboarding/`
- Frontend hooks: `solune/frontend/src/hooks/`
- Frontend layout: `solune/frontend/src/layout/`
- Frontend pages: `solune/frontend/src/pages/`

---

## Phase 1: Setup

**Purpose**: Verify existing code state and confirm migration numbering before making changes.

- [ ] T001 Confirm next migration sequence number is 038 by listing files in solune/backend/src/migrations/ and verifying 037_phase8_recovery_log.sql is the latest

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix the backend step-count bug (Pydantic validator + DB CHECK constraint) that silently rejects tour steps 11–13. This fix is required before US2 can add a 14th tour step at index 13.

**⚠️ CRITICAL**: US1 test verification and US2 frontend tour changes cannot succeed until this phase is complete.

- [ ] T002 [P] Update `OnboardingStateUpdate.current_step` Pydantic validator from `le=10` to `le=13` in solune/backend/src/api/onboarding.py (FR-001)
- [ ] T003 [P] Create DB migration solune/backend/src/migrations/038_onboarding_step_limit.sql that rebuilds `onboarding_tour_state` table with `CHECK (current_step >= 0 AND current_step <= 13)` using the standard SQLite table-rebuild pattern: create temp table → copy data → drop original → recreate with new constraint → copy data back → drop temp (FR-002)

**Checkpoint**: Backend validation now accepts steps 0–13; database constraint aligned with Pydantic validator

---

## Phase 3: User Story 1 — Tour Steps Persist Correctly Beyond Step 10 (Priority: P1) 🎯 MVP

**Goal**: Steps 11–13 persist without silent failures. Backend API tests cover the full 0–13 range with boundary coverage.

**Independent Test**: Run `pytest tests/unit/test_api_onboarding.py -v` — all step boundary tests pass for range 0–13, and step 14 is rejected.

**Note**: US1's core implementation (Pydantic fix + migration) lives in Phase 2 (Foundational). This phase focuses on test verification to prove the fix works.

### Tests for User Story 1

- [ ] T004 [US1] Update `test_valid_step_accepted` parametrization from `[0, 5, 10]` to `[0, 5, 13]` in solune/backend/tests/unit/test_api_onboarding.py
- [ ] T005 [US1] Update `test_invalid_step_rejected` parametrization from `[-1, 11, 100]` to `[-1, 14, 100]` in solune/backend/tests/unit/test_api_onboarding.py
- [ ] T006 [US1] Add new parametrized test `test_step_boundary_11_to_13` covering steps 11, 12, 13 specifically to verify the expanded boundary in solune/backend/tests/unit/test_api_onboarding.py
- [ ] T007 [US1] Run `pytest tests/unit/test_api_onboarding.py -v` from solune/backend/ and verify all step boundary tests pass

**Checkpoint**: Backend accepts steps 0–13, rejects step 14+, boundary steps 11–13 have dedicated coverage — all tests green

---

## Phase 4: User Story 2 — Activity Page Appears in the Spotlight Tour (Priority: P2)

**Goal**: A new 14th tour step highlights the Activity page sidebar link with a celestial-themed icon. The `totalSteps` constant reflects the expanded tour.

**Independent Test**: Start or resume the Spotlight Tour and verify a step highlights the Activity sidebar link with `data-tour-step="activity-link"`. Check `totalSteps` reads 14 in `useOnboarding`. Run `npx vitest run` — `useOnboarding.test.tsx` passes with updated assertions.

### Tests for User Story 2

- [ ] T008 [US2] Update `totalSteps` assertion from `13` to `14` and update completion test loop to iterate through all 14 steps (index 0–13) in solune/frontend/src/hooks/useOnboarding.test.tsx

### Implementation for User Story 2

- [ ] T009 [P] [US2] Create `TimelineStarsIcon` SVG component (24×24 viewBox, `currentColor` stroke, `strokeWidth={1.5}`, celestial timeline theme with stars at intervals) in solune/frontend/src/assets/onboarding/icons.tsx and export it (FR-006)
- [ ] T010 [P] [US2] Add `"/activity": "activity-link"` to the Sidebar `data-tour-step` dynamic mapping object in solune/frontend/src/layout/Sidebar.tsx (FR-004)
- [ ] T011 [US2] Add 14th `TOUR_STEPS` array entry with `{ id: 14, targetSelector: "activity-link", title: "Activity", description: <activity description>, icon: TimelineStarsIcon, placement: "right" }` in solune/frontend/src/components/onboarding/SpotlightTour.tsx — import `TimelineStarsIcon` from icons.tsx (FR-003)
- [ ] T012 [US2] Update `TOTAL_STEPS` constant from `13` to `14` in solune/frontend/src/hooks/useOnboarding.tsx (FR-005)

**Checkpoint**: Tour includes Activity step at index 13, `totalSteps=14`, sidebar has `data-tour-step="activity-link"`, `useOnboarding.test.tsx` passes

---

## Phase 5: User Story 3 — Activity Page Listed in Help Page Feature Guides (Priority: P2)

**Goal**: Help page displays an Activity feature guide entry with a Clock icon and `/activity` route, bringing the total to 9 feature guides.

**Independent Test**: Navigate to the Help page and verify the Activity feature guide is displayed with a Clock icon and links to `/activity`. Count confirms exactly 9 feature guides.

### Implementation for User Story 3

- [ ] T013 [US3] Add Activity entry to `FEATURE_GUIDES` array with `{ title: "Activity", description: <activity description>, icon: Clock, href: "/activity" }` in solune/frontend/src/pages/HelpPage.tsx — import `Clock` from `lucide-react` if not already imported (FR-007)
- [ ] T014 [US3] Verify `FEATURE_GUIDES` array contains exactly 9 entries by counting entries in solune/frontend/src/pages/HelpPage.tsx

**Checkpoint**: Help page renders 9 feature guides including Activity with Clock icon

---

## Phase 6: User Story 4 — FAQ Content Is Accurate and Comprehensive (Priority: P3)

**Goal**: All FAQ entries are accurate against current app behavior. 4 new entries bring the total to 16, appended to existing categories.

**Independent Test**: Navigate to the FAQ section and verify 16 total entries. Confirm new entries appear under their respective categories: Getting Started, Settings & Integration, Agents & Pipelines.

### Implementation for User Story 4

- [ ] T015 [US4] Audit all 12 existing FAQ entries against current app behavior and correct any inaccuracies in solune/frontend/src/pages/HelpPage.tsx (FR-008)
- [ ] T016 [US4] Add 4 new FAQ entries to existing categories in solune/frontend/src/pages/HelpPage.tsx using the `{category}-{number}` ID pattern (FR-009, FR-011):
  - `"What is the Activity page?"` under `getting-started` category
  - `"How do I create a new app?"` under `settings-integration` category
  - `"What are MCP tools?"` under `settings-integration` category
  - `"Can Solune monitor multiple projects?"` under `agents-pipelines` category

**Checkpoint**: FAQ section shows exactly 16 entries across existing categories — no new categories added

---

## Phase 7: User Story 5 — Dead Help Link Mapping Removed from Sidebar (Priority: P3)

**Goal**: The orphaned `/help: "help-link"` entry is removed from the Sidebar's `data-tour-step` mapping. The help link resides in TopBar, not in `NAV_ROUTES`.

**Independent Test**: Inspect the Sidebar component's `data-tour-step` mapping object — no `/help` entry exists. Help link in TopBar continues to function.

### Implementation for User Story 5

- [ ] T017 [US5] Remove the `"/help": "help-link"` entry from the `data-tour-step` dynamic mapping object in solune/frontend/src/layout/Sidebar.tsx (FR-010)

**Checkpoint**: Sidebar has no dead `data-tour-step` mappings for routes not in `NAV_ROUTES`

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Full verification suite, lint, typecheck, and manual verification.

- [ ] T018 [P] Run `ruff format --check src/ tests/` and `ruff check src/ tests/` from solune/backend/ — fix any issues (FR-012)
- [ ] T019 [P] Run `pyright src/` from solune/backend/ — fix any type errors (FR-012)
- [ ] T020 [P] Run `npx vitest run` from solune/frontend/ — all tests pass including updated useOnboarding.test.tsx (FR-012)
- [ ] T021 [P] Run `npx tsc --noEmit` from solune/frontend/ — zero type errors (FR-012)
- [ ] T022 Run quickstart.md manual verification checkpoints: tour replays correctly with Activity step highlighted; Help page renders 9 feature guides and 16 FAQ entries

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — **BLOCKS** US1 test verification and US2 tour expansion
- **US1 (Phase 3)**: Depends on Phase 2 — verifies backend fix works
- **US2 (Phase 4)**: Depends on Phase 2 — step 13 must persist for the new Activity tour step
- **US3 (Phase 5)**: No dependencies on other stories — only modifies `FEATURE_GUIDES` in HelpPage.tsx
- **US4 (Phase 6)**: No dependencies on other stories — only modifies FAQ entries in HelpPage.tsx
- **US5 (Phase 7)**: No dependencies on other stories — only modifies Sidebar.tsx mapping
- **Polish (Phase 8)**: Depends on all user story phases (Phases 3–7)

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 (foundational backend fix) — no dependencies on other stories
- **US2 (P2)**: Depends on Phase 2 (backend fix for step 13 persistence) — otherwise independent
- **US3 (P2)**: Fully independent — only adds to `FEATURE_GUIDES` array
- **US4 (P3)**: Fully independent — only adds/audits FAQ entries
- **US5 (P3)**: Fully independent — only removes dead mapping

### Within Each User Story

- Tests (where applicable) updated FIRST to verify expected behavior
- Backend changes before frontend changes
- Constants and icons before components that consume them
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T002 and T003 can run in parallel (different files: onboarding.py vs migration SQL)
- **Phase 4**: T009 and T010 can run in parallel (different files: icons.tsx vs Sidebar.tsx)
- **Cross-story**: US3, US4, and US5 can all run in parallel after Phase 2 (different files or different sections)
- **Phase 8**: T018, T019, T020, T021 can all run in parallel (independent verification tools)

---

## Parallel Example: User Story 2

```bash
# Launch parallel icon creation and sidebar mapping (different files):
Task T009: "Create TimelineStarsIcon in solune/frontend/src/assets/onboarding/icons.tsx"
Task T010: "Add data-tour-step='activity-link' in solune/frontend/src/layout/Sidebar.tsx"

# Then sequential (T011 depends on T009 for icon import):
Task T011: "Add 14th TOUR_STEPS entry in solune/frontend/src/components/onboarding/SpotlightTour.tsx"
Task T012: "Update TOTAL_STEPS in solune/frontend/src/hooks/useOnboarding.tsx"
```

## Parallel Example: Independent User Stories

```bash
# After Phase 2 (Foundational) completes, these stories can start simultaneously:
# Developer A: US1 (Phase 3) — T004–T007 in test_api_onboarding.py
# Developer B: US3 (Phase 5) — T013 in HelpPage.tsx (FEATURE_GUIDES section)
# Developer C: US4 (Phase 6) — T015–T016 in HelpPage.tsx (FAQ section)
# Developer D: US5 (Phase 7) — T017 in Sidebar.tsx

# Note: US3 and US4 both modify HelpPage.tsx but in different sections
# (FEATURE_GUIDES vs FAQ_ENTRIES), so they can run in parallel with careful merge.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (backend step-count fix)
3. Complete Phase 3: US1 (test verification for step boundaries 0–13)
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_api_onboarding.py -v` — steps 0–13 accepted, step 14 rejected
5. Deploy/demo if ready — backend data-integrity bug is fixed

### Incremental Delivery

1. Setup + Foundational → Backend step-count bug fixed (silent failures eliminated)
2. Add US1 → Test verification → Backend stable (**MVP!**)
3. Add US2 → Tour shows Activity step with celestial icon → Demo
4. Add US3 → Help page lists Activity feature guide → Demo
5. Add US4 → FAQ comprehensive with 16 entries → Demo
6. Add US5 → Dead code removed → Clean codebase
7. Polish → Full verification suite green → Merge-ready
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (backend tests) then US2 (frontend tour expansion)
   - Developer B: US3 (help page guide) + US4 (FAQ entries)
   - Developer C: US5 (dead code removal)
3. Stories complete and integrate independently
4. Team converges on Phase 8 (Polish) for final verification

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Step indexing: 0-indexed; `TOTAL_STEPS = 14` means valid indices 0–13; backend `le=13` matches max index
- SQLite CHECK constraint update requires table rebuild (standard migration pattern in this codebase)
- FAQ entry IDs follow `{category}-{number}` pattern (e.g., `getting-started-4`)
- Tour icons: custom celestial SVGs in `icons.tsx` (not Lucide); Help page guide icons: Lucide
- 10 files modified, 1 new migration file created, 1 new icon component added
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 22 |
| **US1 tasks** | 4 (T004–T007) |
| **US2 tasks** | 5 (T008–T012) |
| **US3 tasks** | 2 (T013–T014) |
| **US4 tasks** | 2 (T015–T016) |
| **US5 tasks** | 1 (T017) |
| **Setup/Foundational/Polish** | 8 (T001–T003, T018–T022) |
| **Parallel opportunities** | 4 groups (Phase 2, Phase 4, cross-story, Phase 8) |
| **Suggested MVP scope** | US1 only (Phases 1–3): backend bug fix + test verification |
| **Format validation** | ✅ All 22 tasks follow checklist format: checkbox + ID + labels + file paths |
