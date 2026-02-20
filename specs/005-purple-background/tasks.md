# Tasks: Add Purple Background Color to App

**Input**: Design documents from `/specs/005-purple-background/`
**Prerequisites**: plan.md ✅, spec.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Define the purple color as a centralized design token in the theming system

- [ ] T001 Add `--color-bg-primary: #7C3AED` CSS custom property to `:root` and `html.dark-mode-active` selectors in frontend/src/index.css

---

## Phase 2: User Story 1 - Purple Background Visible on All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply the purple background (#7C3AED) to the app's root/main container so it is visible on all primary screens

**Independent Test**: Open the app and navigate through all primary screens (home, login, loading) and verify the purple background is consistently visible with no flicker

### Implementation for User Story 1

- [ ] T002 [US1] Update `body` background property in frontend/src/index.css to use `var(--color-bg-primary)` instead of `var(--color-bg-secondary)`
- [ ] T003 [P] [US1] Add inline `background-color: #7C3AED` style to `<body>` tag in frontend/index.html to prevent FOUC during page load

**Checkpoint**: At this point, the purple background should be visible on all screens with no flicker during load or navigation

---

## Phase 3: User Story 2 - Accessible Text and Icons on Purple Background (Priority: P2)

**Goal**: Ensure all text and icons remain clearly readable against the purple background with WCAG AA compliance (minimum 4.5:1 contrast ratio)

**Independent Test**: Verify all text elements on the purple background achieve a WCAG AA contrast ratio of at least 4.5:1 (white #FFFFFF on #7C3AED = 7.28:1 ✅)

### Implementation for User Story 2

- [ ] T004 [US2] Update `--color-text` and `--color-text-secondary` CSS variables in `:root` selector in frontend/src/index.css to ensure WCAG AA contrast against #7C3AED (e.g., set to white/light tones)
- [ ] T005 [P] [US2] Update `--color-text` and `--color-text-secondary` CSS variables in `html.dark-mode-active` selector in frontend/src/index.css to ensure WCAG AA contrast against #7C3AED
- [ ] T006 [US2] Audit `.app-login`, `.app-loading`, and `.chat-placeholder` styles in frontend/src/App.css to ensure foreground colors are legible against the purple background

**Checkpoint**: At this point, all text and icons should be clearly readable against the purple background in both light and dark modes

---

## Phase 4: User Story 3 - Consistent Rendering Across Browsers (Priority: P3)

**Goal**: Ensure the purple background renders identically across Chrome, Firefox, Safari, and Edge

**Independent Test**: Load the app in Chrome, Firefox, Safari, and Edge and visually compare the purple background color

### Implementation for User Story 3

- [ ] T007 [US3] Verify `--color-bg-primary` uses the specific hex value `#7C3AED` (not a CSS keyword like `purple`) in frontend/src/index.css to ensure cross-browser consistency

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T008 [P] Verify existing UI components (header, sidebar, cards, modals) remain visually legible against the purple background in frontend/src/App.css
- [ ] T009 Run the app and confirm zero FOUC or background color flicker during page load and route transitions

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001)
    ↓
Phase 2: US1 - Purple Background (T002-T003, T003 parallelizable)
    ↓
Phase 3: US2 - Accessibility (T004-T006, T005 parallelizable with T004)
    ↓
Phase 4: US3 - Cross-Browser (T007)
    ↓
Phase 5: Polish (T008-T009, T008 parallelizable)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Setup (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (must have purple background applied before adjusting contrast)
- **User Story 3 (P3)**: Depends on US1 (must have purple background to verify cross-browser)

### Parallel Opportunities

- T003 (FOUC prevention) can run in parallel with T002 (body background update) — different files
- T005 (dark mode contrast) can run in parallel with T004 (light mode contrast) — different selectors
- T008 (component audit) can run in parallel with T009 (FOUC validation)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (add CSS variable)
2. Complete Phase 2: User Story 1 (apply purple background + FOUC prevention)
3. **STOP and VALIDATE**: Verify purple background on all screens
4. Deploy/demo if ready

### Incremental Delivery

1. Add CSS variable → Foundation ready
2. Apply purple background → Test on all screens → MVP! (US1)
3. Adjust text colors for contrast → Verify WCAG AA → Deploy (US2)
4. Verify cross-browser → Final sign-off (US3)
5. Polish → Complete

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001 | frontend/src/index.css |
| US1 - Purple Background | T002-T003 | frontend/src/index.css, frontend/index.html |
| US2 - Accessibility | T004-T006 | frontend/src/index.css, frontend/src/App.css |
| US3 - Cross-Browser | T007 | frontend/src/index.css |
| Polish | T008-T009 | frontend/src/App.css |

**Total Tasks**: 9
**Tasks per User Story**: US1: 2, US2: 3, US3: 1, Setup: 1, Polish: 2
**Parallel Opportunities**: 3 (T002∥T003, T004∥T005, T008∥T009)
**Independent Test Criteria**: Each story can be verified independently
**Suggested MVP Scope**: User Story 1 (Phase 1 + Phase 2, Tasks T001-T003)
