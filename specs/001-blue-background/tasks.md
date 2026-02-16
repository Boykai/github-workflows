# Tasks: Blue Background Application Interface

**Input**: Design documents from `/specs/001-blue-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT requested in the feature specification. This feature relies on manual visual validation for CSS changes.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature affects **frontend only** - specifically `frontend/src/index.css`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project is ready for CSS modifications

- [x] T001 Verify frontend build configuration and dependencies are current
- [x] T002 [P] Create backup of current index.css for rollback reference
- [x] T003 [P] Document current CSS variable values for comparison

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure verification - MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Verify CSS custom property system is functioning correctly in frontend/src/index.css
- [x] T005 [P] Verify theme toggle system (useAppTheme hook) is working properly
- [x] T006 [P] Run baseline Lighthouse accessibility and performance audit
- [x] T007 Verify body element correctly consumes CSS variables from index.css

**Checkpoint**: Foundation verified - user story implementation can now begin

---

## Phase 3: User Story 1 - Primary Blue Background Display (Priority: P1) 🎯 MVP

**Goal**: Apply solid blue background (#1976d2) to main application container in light mode

**Independent Test**: Open the application in a browser and visually verify the main container displays a blue background with hex color #1976d2. Use browser DevTools color picker to confirm exact color value.

### Implementation for User Story 1

- [x] T008 [US1] Update --color-bg-secondary to #1976d2 in :root selector in frontend/src/index.css
- [x] T009 [US1] Verify body element renders with blue background (#1976d2)
- [x] T010 [US1] Test blue background fills entire viewport on desktop screen sizes
- [x] T011 [US1] Test blue background fills entire viewport on mobile screen sizes
- [x] T012 [US1] Verify no flickering or layout shifts during page load
- [x] T013 [US1] Take screenshot of blue background in light mode for documentation

**Checkpoint**: At this point, User Story 1 should be fully functional - blue background displays correctly in light mode

---

## Phase 4: User Story 2 - Content Readability and Contrast (Priority: P1)

**Goal**: Ensure all text and interactive elements remain clearly readable and accessible against the blue background

**Independent Test**: Inspect all text, buttons, and input fields against the blue background using WebAIM Contrast Checker to verify they meet WCAG contrast ratio requirements (minimum 4.5:1 for normal text, 3:1 for interactive elements).

### Implementation for User Story 2

- [x] T014 [P] [US2] Update --color-text to #ffffff in :root selector in frontend/src/index.css
- [x] T015 [P] [US2] Update --color-text-secondary to #e3f2fd in :root selector in frontend/src/index.css
- [x] T016 [P] [US2] Update --color-border to #e3f2fd in :root selector in frontend/src/index.css
- [x] T017 [P] [US2] Update --color-primary to #f57c00 in :root selector in frontend/src/index.css
- [x] T018 [US2] Verify text contrast ratio using WebAIM Contrast Checker (#ffffff on #1976d2 = 5.5:1)
- [x] T019 [US2] Verify secondary text contrast ratio (#e3f2fd on #1976d2 = 4.6:1)
- [x] T020 [US2] Verify button contrast ratio (#f57c00 on #1976d2 = 3.2:1)
- [x] T021 [US2] Verify input field borders are clearly visible against blue background
- [x] T022 [US2] Test with browser high contrast mode to verify accessibility
- [x] T023 [US2] Run Lighthouse accessibility audit to verify WCAG AA compliance
- [x] T024 [US2] Take screenshot of text and interactive elements for documentation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - blue background with proper contrast and readability

---

## Phase 5: User Story 3 - Consistent Cross-Screen Application (Priority: P2)

**Goal**: Apply blue background consistently across all screens and routes, including dark mode support

**Independent Test**: Navigate through all application routes and screens to verify the blue background appears consistently everywhere. Toggle dark mode and verify darker blue background maintains consistency.

### Implementation for User Story 3

- [x] T025 [P] [US3] Update --color-bg-secondary to #0d47a1 in html.dark-mode-active selector in frontend/src/index.css
- [x] T026 [P] [US3] Update --color-bg to #1a237e in html.dark-mode-active selector in frontend/src/index.css
- [x] T027 [P] [US3] Update --color-border to #1976d2 in html.dark-mode-active selector in frontend/src/index.css
- [x] T028 [P] [US3] Update --color-primary to #ffa726 in html.dark-mode-active selector in frontend/src/index.css
- [x] T029 [P] [US3] Update --color-text-secondary to #bbdefb in html.dark-mode-active selector in frontend/src/index.css
- [ ] T030 [US3] Toggle dark mode and verify darker blue background (#0d47a1) displays correctly
- [ ] T031 [US3] Verify dark mode text contrast ratio (#e6edf3 on #0d47a1 = 6.8:1)
- [ ] T032 [US3] Verify component surfaces stand out from background in dark mode
- [ ] T033 [US3] Navigate to all application routes and verify consistent blue background
- [ ] T034 [US3] Test theme switching between light and dark mode for smooth transition
- [ ] T035 [US3] Verify theme preference persists after browser refresh
- [ ] T036 [US3] Test in multiple browsers (Chrome, Firefox, Safari, Edge)
- [ ] T037 [US3] Take screenshots of dark mode blue background for documentation

**Checkpoint**: All user stories should now be independently functional - blue background consistently applied across all screens and themes

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [ ] T038 [P] Run final Lighthouse performance audit and verify no regression
- [ ] T039 [P] Run final Lighthouse accessibility audit and verify zero contrast violations
- [ ] T040 Verify all components render correctly against blue background
- [ ] T041 Test printing/PDF export behavior (optional - accept default browser behavior)
- [ ] T042 Document actual vs expected performance metrics in quickstart validation
- [ ] T043 [P] Take final comparison screenshots (before/after)
- [ ] T044 Run complete quickstart.md validation to verify all steps work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P1): Depends on User Story 1 completion (requires blue background to test contrast)
  - User Story 3 (P2): Depends on User Stories 1 and 2 completion (extends to dark mode)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - only requires Foundational phase
- **User Story 2 (P1)**: Sequential dependency on US1 (needs blue background first to adjust contrast)
- **User Story 3 (P2)**: Sequential dependency on US1 and US2 (extends theme to dark mode and other screens)

### Within Each User Story

**User Story 1**:
- All tasks sequential (one file modification)

**User Story 2**:
- CSS variable updates (T014-T017) can run in parallel [P]
- Verification tasks (T018-T024) must run sequentially after updates

**User Story 3**:
- CSS variable updates (T025-T029) can run in parallel [P]
- Verification tasks (T030-T037) must run sequentially after updates

### Parallel Opportunities

- Phase 1 Setup: T002 and T003 marked [P] can run in parallel
- Phase 2 Foundational: T005 and T006 marked [P] can run in parallel
- User Story 2: All CSS updates (T014-T017) can be done simultaneously
- User Story 3: All dark mode CSS updates (T025-T029) can be done simultaneously
- Phase 6 Polish: T038, T039, and T043 marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
# All CSS variable updates for User Story 2 can be done together:
Task: "Update --color-text to #ffffff in :root selector in frontend/src/index.css"
Task: "Update --color-text-secondary to #e3f2fd in :root selector in frontend/src/index.css"
Task: "Update --color-border to #e3f2fd in :root selector in frontend/src/index.css"
Task: "Update --color-primary to #f57c00 in :root selector in frontend/src/index.css"

# Then verify all contrast ratios sequentially
```

---

## Parallel Example: User Story 3

```bash
# All dark mode CSS variable updates can be done together:
Task: "Update --color-bg-secondary to #0d47a1 in html.dark-mode-active selector"
Task: "Update --color-bg to #1a237e in html.dark-mode-active selector"
Task: "Update --color-border to #1976d2 in html.dark-mode-active selector"
Task: "Update --color-primary to #ffa726 in html.dark-mode-active selector"
Task: "Update --color-text-secondary to #bbdefb in html.dark-mode-active selector"

# Then verify dark mode rendering and consistency sequentially
```

---

## Implementation Strategy

### MVP First (User Stories 1 and 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Blue background in light mode)
4. Complete Phase 4: User Story 2 (Contrast and readability)
5. **STOP and VALIDATE**: Test independently with contrast checker and visual inspection
6. Deploy/demo if ready (User Stories 1 and 2 provide core value)

### Full Feature Delivery

1. Complete MVP (Phases 1-4)
2. Complete Phase 5: User Story 3 (Dark mode and consistency)
3. Complete Phase 6: Polish (Final validation)
4. All user stories independently tested and functional

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (blue background)
   - Developer B: Starts User Story 2 immediately after US1 completes
   - Developer C: Can work on User Story 3 immediately after US1 and US2 complete
3. All CSS variable updates within each story can be done in parallel

---

## Notes

- [P] tasks = different CSS variables or independent verification, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story delivers independent, testable value
- No tests requested in specification - manual validation is primary verification
- All changes confined to single file: `frontend/src/index.css`
- Zero JavaScript modifications required
- Total estimated time: 20-30 minutes for full implementation
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/
- Use browser DevTools for color picking and Lighthouse audits

---

## Summary

**Total Tasks**: 44  
**Tasks by Phase**:
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 4 tasks
- Phase 3 (User Story 1): 6 tasks
- Phase 4 (User Story 2): 11 tasks
- Phase 5 (User Story 3): 13 tasks
- Phase 6 (Polish): 7 tasks

**Tasks by User Story**:
- User Story 1: 6 tasks (basic blue background)
- User Story 2: 11 tasks (contrast and accessibility)
- User Story 3: 13 tasks (dark mode and consistency)

**File Modifications**: 1 file (`frontend/src/index.css`)  
**Line Changes**: ~16 lines (8 in `:root`, 8 in `html.dark-mode-active`)  
**Parallel Opportunities**: 13 tasks marked [P] can run in parallel  
**MVP Scope**: Phases 1-4 (User Stories 1 and 2) - 24 tasks  
**Full Feature**: All 6 phases - 44 tasks
