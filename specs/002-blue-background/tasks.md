---
description: "Task list for Blue Background Color feature implementation"
---

# Tasks: Blue Background Color

**Input**: Design documents from `/specs/002-blue-background/`
**Prerequisites**: spec.md (user stories with priorities)

**Tests**: Tests are not explicitly requested in this specification, so test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a web application with `frontend/src/` structure.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification of existing theme system

- [ ] T001 Verify existing CSS custom properties theme system in frontend/src/index.css
- [ ] T002 Review useAppTheme hook implementation in frontend/src/hooks/useAppTheme.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

No foundational tasks required - the application already has a working CSS custom properties theme system and dark mode support.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Blue Background Application (Priority: P1) 🎯 MVP

**Goal**: Apply blue background color (#2196F3) consistently across all core screens of the application

**Independent Test**: Open the application and verify that the main layout displays a blue background color across all core screens (login, dashboard, settings). Use browser DevTools color picker to confirm #2196F3 is applied.

### Implementation for User Story 1

- [ ] T003 [US1] Update --color-bg CSS variable to #2196F3 in :root selector in frontend/src/index.css
- [ ] T004 [US1] Verify blue background applies to body element via var(--color-bg-secondary) in frontend/src/index.css
- [ ] T005 [US1] Test visual consistency by opening the application and navigating between screens (login, dashboard, settings)
- [ ] T006 [US1] Use browser color picker to validate #2196F3 is consistently applied across all screens

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - blue background visible on all screens

---

## Phase 4: User Story 2 - Accessible Contrast Compliance (Priority: P2)

**Goal**: Ensure all text and interactive elements maintain WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for interactive elements) against the blue background

**Independent Test**: Use accessibility testing tools (browser DevTools Accessibility tab, WAVE, axe DevTools) to check contrast ratios of all text and interactive elements against the blue background, verifying WCAG AA compliance.

### Implementation for User Story 2

- [ ] T007 [P] [US2] Update --color-text CSS variable to ensure 4.5:1 contrast ratio against #2196F3 in frontend/src/index.css
- [ ] T008 [P] [US2] Update --color-text-secondary CSS variable to ensure 4.5:1 contrast ratio against #2196F3 in frontend/src/index.css
- [ ] T009 [P] [US2] Update --color-border CSS variable to ensure 3:1 contrast ratio against #2196F3 in frontend/src/index.css
- [ ] T010 [P] [US2] Update button text colors to ensure contrast against button backgrounds in frontend/src/index.css
- [ ] T011 [US2] Test all text elements with contrast checker tools (DevTools, WAVE, or axe)
- [ ] T012 [US2] Test interactive elements (buttons, links, form controls) with contrast checker tools
- [ ] T013 [US2] Verify login page text and buttons meet WCAG AA standards
- [ ] T014 [US2] Verify dashboard text and interactive elements meet WCAG AA standards
- [ ] T015 [US2] Document contrast ratios achieved for key elements in implementation notes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - blue background with accessible contrast

---

## Phase 5: User Story 3 - Dark Mode Consistency (Priority: P3)

**Goal**: Adapt blue background for dark mode while maintaining accessibility and visual coherence

**Independent Test**: Enable dark mode using the theme toggle button, verify that a blue background treatment is present and appropriately adapted for dark theme, then use accessibility tools to confirm WCAG AA compliance in dark mode.

### Implementation for User Story 3

- [ ] T016 [P] [US3] Update --color-bg in html.dark-mode-active selector with dark-adjusted blue in frontend/src/index.css
- [ ] T017 [P] [US3] Update --color-bg-secondary in html.dark-mode-active with complementary dark blue in frontend/src/index.css
- [ ] T018 [P] [US3] Update dark mode --color-text to ensure 4.5:1 contrast against dark blue background in frontend/src/index.css
- [ ] T019 [P] [US3] Update dark mode --color-text-secondary to ensure 4.5:1 contrast against dark blue in frontend/src/index.css
- [ ] T020 [P] [US3] Update dark mode --color-border to ensure 3:1 contrast against dark blue in frontend/src/index.css
- [ ] T021 [US3] Test dark mode visual consistency by toggling theme and navigating all screens
- [ ] T022 [US3] Use contrast checker tools to verify WCAG AA compliance in dark mode
- [ ] T023 [US3] Verify smooth transition when toggling between light and dark modes
- [ ] T024 [US3] Test dark mode on login, dashboard, and settings screens

**Checkpoint**: All user stories should now be independently functional - blue background in both light and dark modes with proper accessibility

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Test blue background on different screen sizes (mobile, tablet, desktop)
- [ ] T026 [P] Test blue background in different browsers (Chrome, Firefox, Safari, Edge)
- [ ] T027 Verify no content visibility or readability issues introduced by blue background
- [ ] T028 [P] Document color values and contrast ratios in code comments in frontend/src/index.css
- [ ] T029 Take screenshots of application with blue background in light and dark modes for documentation
- [ ] T030 Verify application performance is not degraded by CSS changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: No tasks - existing theme system ready
- **User Stories (Phase 3+)**: Can proceed immediately after Phase 1
  - User stories can proceed sequentially in priority order (P1 → P2 → P3)
  - US2 and US3 should wait for US1 completion to verify contrast against actual blue background
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start immediately after Phase 1 - No dependencies on other stories
- **User Story 2 (P2)**: Should start after US1 (needs actual blue background to test contrast) - Independently testable
- **User Story 3 (P3)**: Should start after US1 and US2 (needs baseline colors established) - Independently testable

### Within Each User Story

- **US1**: Tasks are sequential (change color → test visually → validate)
- **US2**: CSS changes marked [P] can run in parallel → then test tasks sequentially
- **US3**: CSS changes marked [P] can run in parallel → then test tasks sequentially

### Parallel Opportunities

- Setup tasks (T001-T002) can run in parallel
- Within US2: All CSS updates (T007-T010) can run in parallel
- Within US3: All CSS updates (T016-T020) can run in parallel
- Polish tasks (T025, T026, T028) can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all CSS updates for User Story 2 together:
Task: "Update --color-text CSS variable to ensure 4.5:1 contrast ratio against #2196F3 in frontend/src/index.css"
Task: "Update --color-text-secondary CSS variable to ensure 4.5:1 contrast ratio against #2196F3 in frontend/src/index.css"
Task: "Update --color-border CSS variable to ensure 3:1 contrast ratio against #2196F3 in frontend/src/index.css"
Task: "Update button text colors to ensure contrast against button backgrounds in frontend/src/index.css"

# Then sequentially test contrast compliance
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing system)
2. Complete Phase 3: User Story 1 (apply blue background)
3. **STOP and VALIDATE**: Test User Story 1 independently - verify blue visible on all screens
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Foundation verified
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! - Blue background applied)
3. Add User Story 2 → Test independently → Deploy/Demo (Accessible contrast achieved)
4. Add User Story 3 → Test independently → Deploy/Demo (Dark mode support complete)
5. Complete Polish → Final validation → Deploy/Demo (Production ready)
6. Each story adds value without breaking previous stories

### Sequential Implementation Strategy

With one developer:

1. Complete Setup (T001-T002) - verify existing theme system
2. Implement User Story 1 (T003-T006) - blue background applied
3. Validate US1 independently before proceeding
4. Implement User Story 2 (T007-T015) - accessibility ensured
5. Validate US2 independently before proceeding
6. Implement User Story 3 (T016-T024) - dark mode adapted
7. Validate US3 independently before proceeding
8. Complete Polish tasks (T025-T030) - cross-cutting improvements
9. Final validation across all scenarios

---

## Notes

- [P] tasks = different files or independent CSS variables, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each logical group of tasks
- Stop at any checkpoint to validate story independently
- Primary file: frontend/src/index.css (all color changes in one file)
- Use browser DevTools and accessibility testing tools for validation
- Take screenshots for documentation purposes
- Blue color #2196F3 chosen for accessibility (Material Design Blue 500)
- WCAG AA standards: 4.5:1 for normal text, 3:1 for large text/interactive elements
