# Tasks: Add Brown Background Color to App

**Input**: Design documents from `/specs/005-brown-background/`
**Prerequisites**: spec.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Existing E2E tests may need assertion updates if they check background colors.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Design Token Definition)

**Purpose**: Define the brown color as a reusable CSS custom property

- [ ] T001 Define `--color-bg-primary: #795548` CSS custom property in `:root` and dark-mode variant in `html.dark-mode-active` in frontend/src/index.css

---

## Phase 2: User Story 1 - Brown Background Visible Across All Pages (Priority: P1) 🎯 MVP

**Goal**: Apply brown background to the app's root container so it is visible across all pages and views

**Independent Test**: Open the app in a browser and navigate across all pages/views, verifying the brown background is visible everywhere with no white or default-colored gaps

### Implementation for User Story 1

- [ ] T002 [US1] Update `body` background from `var(--color-bg-secondary)` to `var(--color-bg-primary)` in frontend/src/index.css
- [ ] T003 [US1] Update `.app-header` background from `var(--color-bg)` to `var(--color-bg-primary)` in frontend/src/App.css
- [ ] T004 [P] [US1] Update `.board-page` background from `var(--color-bg)` to `var(--color-bg-primary)` in frontend/src/App.css
- [ ] T005 [P] [US1] Update `.chat-section` background from `var(--color-bg)` to `var(--color-bg-primary)` in frontend/src/App.css

**Checkpoint**: At this point, the brown background should be visible across all pages and views

---

## Phase 3: User Story 2 - Text and UI Elements Remain Legible (Priority: P1)

**Goal**: Ensure all text, icons, and interactive elements maintain WCAG AA contrast (4.5:1) against the brown background

**Independent Test**: Visually inspect all text and UI elements against the brown background and verify contrast ratios meet WCAG AA (4.5:1 for normal text, 3:1 for large text). Use a contrast checker tool with #795548 as background.

### Implementation for User Story 2

- [ ] T006 [US2] Verify and update `--color-text` value to ensure 4.5:1 contrast ratio against #795548 in frontend/src/index.css (current #24292f has ~3.1:1 ratio — update to #ffffff for sufficient contrast)
- [ ] T007 [US2] Verify and update `--color-text-secondary` value to ensure sufficient contrast against #795548 in frontend/src/index.css (update to a lighter tone e.g. #d7ccc8 for legibility)
- [ ] T008 [US2] Verify `.login-button` and `.logout-button` styles remain visually distinct against the brown background in frontend/src/App.css

**Checkpoint**: All text and interactive elements should be clearly legible against the brown background

---

## Phase 4: User Story 3 - Brown Color Defined as Reusable Design Token (Priority: P2)

**Goal**: Document the brown color value and ensure it is defined once and referenced everywhere

**Independent Test**: Inspect CSS and verify the brown color is defined as `--color-bg-primary` in one place and referenced wherever the background is applied. Changing the variable should update all surfaces.

### Implementation for User Story 3

- [ ] T009 [US3] Verify `--color-bg-primary` is used consistently (not hardcoded hex values) across all background declarations in frontend/src/index.css and frontend/src/App.css

**Checkpoint**: The brown color is defined once as a design token and referenced everywhere

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases and cleanup

- [ ] T010 [P] Verify scoped component backgrounds (cards, inputs, modals) retain their own background colors and are not overridden by the brown background in frontend/src/App.css
- [ ] T011 [P] Verify dark mode (`html.dark-mode-active`) has an appropriate brown variant or retains its existing dark theme in frontend/src/index.css

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001)
    ↓
Phase 2: US1 - Brown Background (T002-T005)
    ↓
Phase 3: US2 - Legibility (T006-T008)
    ↓
Phase 4: US3 - Design Token (T009)
    ↓
Phase 5: Polish (T010-T011, parallel)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Setup (Phase 1) — core background change
- **User Story 2 (P1)**: Depends on US1 — contrast adjustments require the brown background to be in place
- **User Story 3 (P2)**: Depends on US1 — token verification requires background to be applied

### Parallel Opportunities

- T003, T004, T005 can run in parallel (different CSS selectors in same file, but non-overlapping)
- T010, T011 can run in parallel (different concerns)
- Within Phase 3, T006 and T007 modify different CSS variables

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Define `--color-bg-primary` token
2. Complete Phase 2: Apply brown background to body and primary surfaces
3. **STOP and VALIDATE**: Verify brown background is visible across all pages
4. Deploy/demo if ready

### Incremental Delivery

1. Define token → Apply background → Brown is visible (MVP!)
2. Adjust text contrast → All content is legible
3. Verify token consistency → Maintainable and documented
4. Polish edge cases → Scoped components and dark mode verified

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001 | frontend/src/index.css |
| US1 - Background | T002-T005 | frontend/src/index.css, frontend/src/App.css |
| US2 - Legibility | T006-T008 | frontend/src/index.css, frontend/src/App.css |
| US3 - Token | T009 | frontend/src/index.css, frontend/src/App.css |
| Polish | T010-T011 | frontend/src/App.css, frontend/src/index.css |

**Total Tasks**: 11
**Tasks per User Story**: US1: 4, US2: 3, US3: 1, Setup: 1, Polish: 2
**Parallel Opportunities**: 5 tasks marked [P]
**Suggested MVP Scope**: Phase 1 + Phase 2 (User Story 1 — 5 tasks)
