# Tasks: Add Purple Background Color to App

**Input**: Design documents from `/specs/005-purple-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Tests are NOT included (not explicitly requested in spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Define the purple color as a centralized design token in the theming system

- [x] T001 Add `--color-bg-app: #7C3AED` CSS custom property to `:root` and `html.dark-mode-active` selectors in frontend/src/index.css

---

## Phase 2: User Story 1 - Purple Background Visible on All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply the purple background (#7C3AED) to the app's root/main container so it is visible on all primary screens

**Independent Test**: Open the app and navigate through all primary screens (home, login, loading) and verify the purple background is consistently visible with no flicker

### Implementation for User Story 1

- [x] T002 [US1] Update `body` background property in frontend/src/index.css to use `var(--color-bg-app)` instead of `var(--color-bg-secondary)`

**Checkpoint**: At this point, the purple background should be visible on all screens

---

## Phase 3: User Story 2 - Accessible Text and Icons on Purple Background (Priority: P2)

**Goal**: Ensure all text and icons remain clearly readable against the purple background with WCAG AA compliance (minimum 4.5:1 contrast ratio)

**Independent Test**: Verify all text elements on the purple background achieve a WCAG AA contrast ratio of at least 4.5:1 (white #FFFFFF on #7C3AED = 6.65:1 ✅)

### Implementation for User Story 2

- [x] T003 [US2] Update `.app-login h1` color to `#ffffff` in frontend/src/App.css for WCAG AA contrast against purple background
- [x] T004 [P] [US2] Update `.app-login p` color to `#E9D5FF` in frontend/src/App.css for WCAG AA contrast against purple background

**Checkpoint**: At this point, all text on exposed surfaces should be clearly readable against the purple background

---

## Phase 4: User Story 3 - Consistent Rendering Across Browsers (Priority: P3)

**Goal**: Ensure the purple background renders identically across Chrome, Firefox, Safari, and Edge

**Independent Test**: Load the app in Chrome, Firefox, Safari, and Edge and visually compare the purple background color

### Implementation for User Story 3

- [x] T005 [US3] Verify `--color-bg-app` uses the specific hex value `#7C3AED` (not a CSS keyword like `purple`) in frontend/src/index.css to ensure cross-browser consistency

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [x] T006 [P] Verify existing UI components (header, sidebar, cards, modals) remain visually legible against the purple background in frontend/src/App.css
- [x] T007 Run the app and confirm zero FOUC or background color flicker during page load and route transitions

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001)
    ↓
Phase 2: US1 - Purple Background (T002)
    ↓
Phase 3: US2 - Accessibility (T003∥T004, different selectors in same file)
    ↓
Phase 4: US3 - Cross-Browser (T005)
    ↓
Phase 5: Polish (T006∥T007)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Setup (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (must have purple background applied before adjusting contrast)
- **User Story 3 (P3)**: Depends on US1 (must have purple background to verify cross-browser)

### Parallel Opportunities

- T003 and T004 can run in parallel (different selectors in same file, non-overlapping)
- T006 and T007 can run in parallel (audit vs. runtime validation)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (add CSS variable)
2. Complete Phase 2: User Story 1 (apply purple background)
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
| US1 - Purple Background | T002 | frontend/src/index.css |
| US2 - Accessibility | T003-T004 | frontend/src/App.css |
| US3 - Cross-Browser | T005 | frontend/src/index.css |
| Polish | T006-T007 | frontend/src/App.css |

**Total Tasks**: 7
**Tasks per User Story**: US1: 1, US2: 2, US3: 1, Setup: 1, Polish: 2
**Parallel Opportunities**: 2 (T003∥T004, T006∥T007)
**Independent Test Criteria**: Each story can be verified independently
**Suggested MVP Scope**: User Story 1 (Phase 1 + Phase 2, Tasks T001-T002)
