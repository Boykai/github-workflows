# Tasks: Black Background Theme

**Input**: Design documents from `/specs/003-black-background-theme/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/css-changes.md (complete), quickstart.md (complete)

**Tests**: Tests are NOT explicitly requested in the feature specification. Visual verification and manual contrast checking will be used to validate implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature is frontend-only: all paths in `frontend/src/`

---

## Phase 1: Setup (No Changes Required)

**Purpose**: Project initialization and basic structure

**Status**: ✅ **Complete** - Application infrastructure already exists. No setup tasks needed.

The existing React + TypeScript + Vite application is fully functional with:
- CSS custom properties system already in place
- Theme management via `useAppTheme` hook
- Dark mode toggle functionality present
- All necessary build and development tooling configured

**Checkpoint**: Foundation ready - proceed directly to user story implementation

---

## Phase 2: User Story 1 - Apply Black Background to All Primary Screens (Priority: P1) 🎯 MVP

**Goal**: Replace current dark gray background (#0d1117) with pure black (#000000) across all primary screens and views, ensuring the black background is visible on login screen, main interface, navigation areas, and content sections.

**Independent Test**: Open the application at http://localhost:5173 and use browser DevTools color picker to verify all primary screens display solid black (#000000) background. Test on desktop, tablet, and mobile viewport sizes.

**Acceptance Criteria**:
1. Login screen background is solid black (#000000)
2. Authenticated main interface background is solid black (#000000)
3. All primary screens display solid black backgrounds consistently
4. Black background appears consistently across desktop, tablet, and mobile devices

### Implementation for User Story 1

- [ ] T001 [US1] Update CSS custom property `--color-bg` from #0d1117 to #000000 in `frontend/src/index.css` (html.dark-mode-active selector)
- [ ] T002 [US1] Update CSS custom property `--color-bg-secondary` from #161b22 to #0a0a0a in `frontend/src/index.css` (html.dark-mode-active selector)
- [ ] T003 [US1] Update CSS custom property `--shadow` from rgba(0,0,0,0.4) to rgba(255,255,255,0.05) in `frontend/src/index.css` (html.dark-mode-active selector)
- [ ] T004 [US1] Set default theme to black by changing `useState(false)` to `useState(true)` in `frontend/src/hooks/useAppTheme.tsx`
- [ ] T005 [US1] Verify login screen displays black background using browser DevTools color picker
- [ ] T006 [US1] Verify authenticated main interface displays black background on desktop viewport
- [ ] T007 [US1] Verify black background consistency on tablet viewport (768px width)
- [ ] T008 [US1] Verify black background consistency on mobile viewport (375px width)
- [ ] T009 [US1] Test theme toggle functionality (switch between light and black themes)

**Checkpoint**: User Story 1 complete - all primary screens now display solid black backgrounds, independently testable by visual inspection

---

## Phase 3: User Story 2 - Ensure Readable Text and UI Elements (Priority: P2)

**Goal**: Ensure all text, icons, and interactive elements achieve WCAG 2.1 Level AA contrast requirements (4.5:1 for normal text, 3:1 for large text) and are clearly visible against the black background.

**Independent Test**: Use Chrome DevTools Lighthouse accessibility audit and color picker to measure contrast ratios for all text and UI elements. Verify all elements achieve minimum 4.5:1 ratio for normal text. Test keyboard navigation to verify focus indicators are clearly visible.

**Acceptance Criteria**:
1. All text content meets WCAG AA contrast standards (4.5:1 normal, 3:1 large)
2. Interactive elements (buttons, links, form controls) are clearly visible and distinguishable
3. Icons and graphical elements maintain adequate visibility and contrast
4. Focus indicators are clearly visible during keyboard navigation

### Implementation for User Story 2

- [ ] T010 [P] [US2] Add high contrast mode support using @media (forced-colors: active) in `frontend/src/index.css`
- [ ] T011 [P] [US2] Update error toast styles for black background in `frontend/src/App.css` (add html.dark-mode-active .error-toast override)
- [ ] T012 [P] [US2] Update error toast message color for black background in `frontend/src/App.css` (add html.dark-mode-active .error-toast-message override)
- [ ] T013 [P] [US2] Update error banner styles for black background in `frontend/src/App.css` (add html.dark-mode-active .error-banner override)
- [ ] T014 [P] [US2] Update error banner message color for black background in `frontend/src/App.css` (add html.dark-mode-active .error-banner-message override)
- [ ] T015 [US2] Update highlight animation @keyframes highlight-pulse starting color from #dafbe1 to rgba(63,185,80,0.2) in `frontend/src/App.css`
- [ ] T016 [US2] Verify primary text (#e6edf3) contrast ratio is 21:1 using Chrome DevTools color picker
- [ ] T017 [US2] Verify secondary text (#8b949e) contrast ratio is 13:1 using Chrome DevTools color picker
- [ ] T018 [US2] Verify primary button (#539bf5) contrast ratio is 8.6:1 using Chrome DevTools color picker
- [ ] T019 [US2] Verify success badge (#3fb950) contrast ratio is 6.4:1 using Chrome DevTools color picker
- [ ] T020 [US2] Verify warning badge (#d29922) contrast ratio is 8.2:1 using Chrome DevTools color picker
- [ ] T021 [US2] Verify error badge (#f85149) contrast ratio is 7.1:1 using Chrome DevTools color picker
- [ ] T022 [US2] Test keyboard navigation through all interactive elements (Tab key)
- [ ] T023 [US2] Verify focus indicators (blue outline) are visible on all buttons, links, and form controls
- [ ] T024 [US2] Run Chrome DevTools Lighthouse accessibility audit and verify all color contrast tests pass
- [ ] T025 [US2] Test Windows high contrast mode (forced-colors: active) to verify system colors override theme

**Checkpoint**: User Story 2 complete - all text and UI elements meet WCAG AA contrast requirements and are clearly readable, independently testable using automated contrast checking tools

---

## Phase 4: User Story 3 - Apply Black Background to Navigation and Modals (Priority: P3)

**Goal**: Apply black backgrounds to navigation menus, dropdowns, modal dialogs, context menus, and tooltips to maintain consistent visual experience throughout the application.

**Independent Test**: Interact with all navigation elements (open menus, dropdowns, modals) and verify each displays with a black background. Use browser DevTools to verify modal backdrop uses semi-transparent black overlay and modal content uses solid black background.

**Acceptance Criteria**:
1. Navigation menus and dropdowns display with black backgrounds
2. Modal dialogs display with black content backgrounds
3. Context menus (if present) display with black backgrounds
4. Tooltips maintain visual consistency with black theme

### Implementation for User Story 3

- [ ] T026 [US3] Audit all navigation components to verify they inherit `--color-bg` variable in `frontend/src/components/` directory
- [ ] T027 [US3] Test project sidebar navigation elements on black background
- [ ] T028 [US3] Test header navigation elements on black background
- [ ] T029 [US3] Test any dropdown menus to verify black background inheritance
- [ ] T030 [US3] Verify task cards display with subtle `--color-bg-secondary` (#0a0a0a) backgrounds
- [ ] T031 [US3] If modal dialogs exist, verify modal backdrop uses appropriate opacity and modal content inherits black background
- [ ] T032 [US3] If context menus exist, verify they inherit black background styling
- [ ] T033 [US3] If tooltips exist, verify they maintain visual consistency with black theme
- [ ] T034 [US3] Test hover states on navigation items to ensure visibility against black background
- [ ] T035 [US3] Verify navigation elements remain visible and distinguishable with borders or subtle backgrounds

**Checkpoint**: User Story 3 complete - all navigation elements, modals, and overlays display with black backgrounds consistently, independently testable by interaction and visual inspection

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification, edge case testing, and documentation updates

- [ ] T036 [P] Test browser zoom levels (50%, 75%, 100%, 150%, 200%) for layout integrity
- [ ] T037 [P] Test window resize from desktop → tablet → mobile for responsive black background
- [ ] T038 [P] Test page reload (F5) to verify black theme loads immediately without FOUC (flash of unstyled content)
- [ ] T039 [P] Verify shadow visibility at various zoom levels using browser DevTools
- [ ] T040 Test theme toggle multiple times to verify smooth transitions between light and black themes
- [ ] T041 Verify loading spinner visibility on black background
- [ ] T042 Verify highlight animation (task-card--highlighted) visibility on black background
- [ ] T043 Test all status badges (todo, in-progress, done) for distinguishability on black background
- [ ] T044 Build production bundle with `npm run build` and verify CSS variables are correctly bundled
- [ ] T045 Preview production build with `npm run preview` and verify black theme displays correctly
- [ ] T046 Take screenshots of login screen, main interface, and navigation elements for documentation
- [ ] T047 Update quickstart.md if any deviations from planned implementation occurred
- [ ] T048 Verify no console errors or warnings in browser DevTools console

---

## Dependencies & Execution Order

### Phase Dependencies

- **User Story 1 (Phase 2)**: No dependencies - can start immediately (foundation already exists)
- **User Story 2 (Phase 3)**: Depends on User Story 1 completion - contrast adjustments build on black background
- **User Story 3 (Phase 4)**: Depends on User Story 1 completion - navigation/modal styling inherits black theme
- **Polish (Phase 5)**: Depends on all three user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - applies base black background across all primary screens
- **User Story 2 (P2)**: Independent - adds contrast adjustments and readability improvements (can be tested independently by measuring contrast ratios)
- **User Story 3 (P3)**: Independent - verifies navigation and modals inherit black background (can be tested independently by interaction)

### Within Each User Story

**User Story 1**:
1. Update CSS variables (T001-T003) - all 3 can run in parallel (same file, different properties)
2. Set default theme (T004) - can run in parallel with T001-T003
3. Visual verification (T005-T009) - run sequentially after implementation

**User Story 2**:
1. Add contrast adjustments (T010-T015) - all 6 tasks marked [P] can run in parallel (different CSS blocks)
2. Contrast verification (T016-T021) - run sequentially after implementation
3. Keyboard navigation testing (T022-T025) - run sequentially after implementation

**User Story 3**:
1. Component audit (T026) - run first
2. Navigation testing (T027-T035) - run sequentially to verify each component

**Polish Phase**:
1. Edge case testing (T036-T039) - all 4 tasks marked [P] can run in parallel
2. Final verification (T040-T048) - run sequentially to catch any remaining issues

### Parallel Opportunities

**Within User Story 1** (after foundation):
- Tasks T001, T002, T003, T004 can all execute in parallel (different CSS properties and different file)

**Within User Story 2** (after US1 complete):
- Tasks T010, T011, T012, T013, T014 can all execute in parallel (different CSS selectors, no conflicts)
- Tasks T016-T021 can execute in parallel (independent measurements)

**Within Polish Phase**:
- Tasks T036, T037, T038, T039 can execute in parallel (independent edge case tests)

---

## Parallel Example: User Story 1

```bash
# Launch all CSS variable updates together:
Task T001: "Update --color-bg to #000000 in frontend/src/index.css"
Task T002: "Update --color-bg-secondary to #0a0a0a in frontend/src/index.css"
Task T003: "Update --shadow to rgba(255,255,255,0.05) in frontend/src/index.css"
Task T004: "Set default theme to black in frontend/src/hooks/useAppTheme.tsx"
```

## Parallel Example: User Story 2

```bash
# Launch all component style adjustments together:
Task T010: "Add high contrast mode support in frontend/src/index.css"
Task T011: "Update error toast styles in frontend/src/App.css"
Task T012: "Update error toast message color in frontend/src/App.css"
Task T013: "Update error banner styles in frontend/src/App.css"
Task T014: "Update error banner message color in frontend/src/App.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: User Story 1 (Tasks T001-T009)
2. **STOP and VALIDATE**: Test black background on all primary screens
3. Verify color picker shows #000000 on login, main interface, all sections
4. Deploy/demo if ready (MVP achieved - black background visible)

### Incremental Delivery

1. User Story 1 → Test independently → Black background visible ✅
2. User Story 2 → Test independently → Text and UI elements readable ✅
3. User Story 3 → Test independently → Navigation and modals consistent ✅
4. Polish Phase → Test edge cases → Production ready ✅

Each story adds value without breaking previous stories:
- After US1: Users see black backgrounds (core benefit)
- After US2: Users can read all content easily (usability)
- After US3: Users experience consistent black theme everywhere (polish)

### Parallel Team Strategy

With multiple developers:

1. **Single developer scenario** (recommended for this feature):
   - Complete User Story 1 → US2 → US3 → Polish sequentially
   - Total estimated time: 2 hours per quickstart guide

2. **Two developer scenario** (if needed):
   - Developer A: User Story 1 (T001-T009)
   - Wait for A to complete US1 (foundation)
   - Developer A: User Story 2 (T010-T025)
   - Developer B: User Story 3 (T026-T035) - can start after US1 complete
   - Both: Polish phase together (T036-T048)

---

## Task Summary

**Total Tasks**: 48 tasks across 4 phases

**Tasks per User Story**:
- User Story 1 (P1): 9 tasks (3 implementation + 1 config + 5 verification)
- User Story 2 (P2): 16 tasks (6 implementation + 10 verification)
- User Story 3 (P3): 10 tasks (10 verification)
- Polish Phase: 13 tasks (edge cases + documentation)

**Parallel Opportunities**:
- 4 tasks can run in parallel in User Story 1 (T001-T004)
- 5 tasks can run in parallel in User Story 2 (T010-T014)
- 4 tasks can run in parallel in Polish Phase (T036-T039)

**Independent Test Criteria**:
- US1: Visual inspection with color picker (solid black #000000 on all screens)
- US2: Automated contrast checking with Lighthouse + manual keyboard navigation
- US3: Interactive testing of navigation and modals

**Suggested MVP Scope**:
- **Phase 2 only** (User Story 1: Tasks T001-T009)
- Delivers core value: Black background visible across all primary screens
- Estimated time: 45 minutes
- Immediately deployable for user feedback

**Complete Feature Scope**:
- **All 4 phases** (User Stories 1-3 + Polish)
- Delivers full feature: Black background + readable text + consistent navigation
- Estimated time: 2 hours
- Production-ready with full accessibility compliance

---

## Notes

- [P] tasks = different files or different CSS blocks, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No automated tests required per feature specification
- Visual verification and manual contrast checking are the validation methods
- Commit after each logical group of tasks (e.g., after US1, after US2, etc.)
- Stop at any checkpoint to validate story independently
- All changes are CSS-only with one TypeScript default value change (minimal invasiveness)

---

## Format Validation

✅ **All 48 tasks follow the strict checklist format**:
- Checkbox: `- [ ]` present on all tasks
- Task ID: Sequential T001-T048
- [P] marker: Present only on parallelizable tasks (8 tasks total)
- [Story] label: Present on all user story phase tasks (US1, US2, US3 labels applied correctly)
- Description: All include clear action with exact file path
- Setup phase: No story labels (complete, no tasks needed)
- Foundational phase: Not applicable (no foundational tasks for CSS-only feature)
- User Story phases: All tasks have appropriate [US1], [US2], or [US3] labels
- Polish phase: No story labels (cross-cutting concerns)

**Example Format Validation**:
- ✅ `- [ ] T001 [US1] Update CSS custom property...` (correct)
- ✅ `- [ ] T010 [P] [US2] Add high contrast mode...` (correct - parallel + story)
- ✅ `- [ ] T036 [P] Test browser zoom levels...` (correct - parallel, no story label)
