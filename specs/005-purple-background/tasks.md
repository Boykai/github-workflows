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

- [X] T001 Add `--color-bg-primary: #7C3AED` CSS custom property to `:root` and `html.dark-mode-active` selectors in frontend/src/index.css

---

## Phase 2: User Story 1 - Purple Background Visible on All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply the purple background (#7C3AED) to the app's root/main container so it is visible on all primary screens

**Independent Test**: Open the app and navigate through all primary screens (home, login, loading) and verify the purple background is consistently visible with no flicker

### Implementation for User Story 1

- [X] T002 [US1] Update `body` background property in frontend/src/index.css to use `var(--color-bg-primary)` instead of `var(--color-bg-secondary)`
- [X] T003 [P] [US1] Add inline `background-color: #7C3AED` style to `<body>` tag in frontend/index.html to prevent FOUC during page load

**Checkpoint**: At this point, the purple background should be visible on all screens with no flicker during load or navigation

---

## Phase 3: User Story 2 - Accessible Text and Icons on Purple Background (Priority: P2)

**Goal**: Ensure all text and icons remain clearly readable against the purple background with WCAG AA compliance (minimum 4.5:1 contrast ratio)

**Independent Test**: Verify all text elements on the purple background achieve a WCAG AA contrast ratio of at least 4.5:1 (white #FFFFFF on #7C3AED = 5.70:1 ✅)

### Implementation for User Story 2

- [X] T004 [US2] Update `--color-text` and `--color-text-secondary` CSS variables in `:root` selector in frontend/src/index.css to ensure WCAG AA contrast against #7C3AED (e.g., set to white/light tones)
- [X] T005 [P] [US2] Update `--color-text` and `--color-text-secondary` CSS variables in `html.dark-mode-active` selector in frontend/src/index.css to ensure WCAG AA contrast against #7C3AED
- [X] T006 [US2] Audit `.app-login`, `.app-loading`, and `.chat-placeholder` styles in frontend/src/App.css to ensure foreground colors are legible against the purple background

**Checkpoint**: At this point, all text and icons should be clearly readable against the purple background in both light and dark modes

---

## Phase 4: User Story 3 - Consistent Rendering Across Browsers (Priority: P3)

**Goal**: Ensure the purple background renders identically across Chrome, Firefox, Safari, and Edge

**Independent Test**: Load the app in Chrome, Firefox, Safari, and Edge and visually compare the purple background color

### Implementation for User Story 3

- [X] T007 [US3] Verify `--color-bg-primary` uses the specific hex value `#7C3AED` (not a CSS keyword like `purple`) in frontend/src/index.css to ensure cross-browser consistency

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [X] T008 [P] Verify existing UI components (header, sidebar, cards, modals) remain visually legible against the purple background in frontend/src/App.css
- [X] T009 Run the app and confirm zero FOUC or background color flicker during page load and route transitions

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
**All Tasks**: Complete ✅
