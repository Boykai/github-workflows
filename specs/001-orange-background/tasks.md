---

description: "Task list for orange background color feature implementation"
---

# Tasks: Orange Background Color

**Input**: Design documents from `/specs/001-orange-background/`
**Prerequisites**: spec.md (user stories with priorities P1-P3)

**Tests**: Not explicitly requested in the specification, so test tasks are omitted per constitution principle of Test Optionality.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for React components and styles, `frontend/src/hooks/` for custom hooks

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Review existing theme system and understand current CSS structure

- [ ] T001 Review existing CSS theme system in frontend/src/index.css
- [ ] T002 Review theme hook implementation in frontend/src/hooks/useAppTheme.ts
- [ ] T003 Document current color variables and their usage patterns

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

No foundational tasks required - the application already has a working CSS theming system with color variables and a dark mode toggle. The existing infrastructure supports the orange background implementation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Application with Orange Background (Priority: P1) 🎯 MVP

**Goal**: Apply orange (#FFA500) background color to all primary application screens so users can view the vibrant orange interface.

**Independent Test**: Load any primary screen of the application and visually verify the background color is #FFA500 (orange). Check main app container, header background, and secondary backgrounds.

### Implementation for User Story 1

- [ ] T004 [US1] Update --color-bg variable to #FFA500 in :root selector in frontend/src/index.css
- [ ] T005 [US1] Update --color-bg-secondary variable to complement orange (lighter shade) in frontend/src/index.css
- [ ] T006 [US1] Verify orange background applies to body element via var(--color-bg-secondary) in frontend/src/index.css
- [ ] T007 [US1] Verify app-header background uses var(--color-bg) for orange in frontend/src/App.css
- [ ] T008 [US1] Verify sidebar background uses var(--color-bg) for orange in frontend/src/App.css

**Checkpoint**: At this point, User Story 1 should be fully functional - all primary screens display with orange background and can be tested independently by loading the application

---

## Phase 4: User Story 2 - Read Content with Maintained Contrast (Priority: P2)

**Goal**: Ensure all text and interactive elements maintain sufficient contrast against the orange background for accessibility and readability.

**Independent Test**: Review text elements and interactive controls on orange background screens using browser dev tools or accessibility checker to verify WCAG AA contrast requirements (4.5:1 for normal text, 3:1 for large text).

### Implementation for User Story 2

- [ ] T009 [US2] Update --color-text variable to ensure 4.5:1 contrast ratio against orange background in frontend/src/index.css
- [ ] T010 [US2] Update --color-text-secondary variable to ensure adequate contrast for secondary text in frontend/src/index.css
- [ ] T011 [US2] Adjust --color-primary for buttons/links to be distinguishable on orange background in frontend/src/index.css
- [ ] T012 [US2] Update --color-border variable to ensure borders are visible on orange background in frontend/src/index.css
- [ ] T013 [US2] Review and adjust status badge colors for visibility on orange in frontend/src/App.css
- [ ] T014 [US2] Verify button hover states maintain contrast on orange background in frontend/src/App.css
- [ ] T015 [US2] Test interactive elements (form controls, links) for sufficient contrast and visibility

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - orange background is applied with all text and interactive elements clearly readable and accessible

---

## Phase 5: User Story 3 - Experience Consistent Theming Across Modes (Priority: P3)

**Goal**: Apply orange background consistently in both light and dark modes to provide a unified visual experience.

**Independent Test**: Toggle between light and dark modes using the theme toggle button and verify the orange background is appropriately applied in both contexts with smooth transitions.

### Implementation for User Story 3

- [ ] T016 [US3] Update dark mode --color-bg to orange or appropriate dark variant in html.dark-mode-active selector in frontend/src/index.css
- [ ] T017 [US3] Update dark mode --color-bg-secondary to complement dark orange theme in frontend/src/index.css
- [ ] T018 [US3] Adjust dark mode text colors for contrast on orange background in frontend/src/index.css
- [ ] T019 [US3] Verify smooth transition when toggling between light and dark modes with orange background
- [ ] T020 [US3] Ensure no flickering occurs during theme transitions in frontend/src/hooks/useAppTheme.ts

**Checkpoint**: All user stories should now be independently functional - orange background appears consistently across both light and dark modes with smooth transitions

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final refinements and validation across all user stories

- [ ] T021 [P] Visual verification of orange background across all main screens (header, sidebar, main content, chat)
- [ ] T022 [P] Accessibility validation using browser dev tools or automated checker
- [ ] T023 Review edge cases: high contrast mode, different display types, CSS load failures
- [ ] T024 Performance check: ensure page load times remain within 5% variance
- [ ] T025 [P] Update README or documentation if color scheme is documented
- [ ] T026 Final review: verify no layout shifts or rendering issues introduced

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (review only)
- **Foundational (Phase 2)**: No additional foundation needed - existing theme system is sufficient
- **User Stories (Phase 3-5)**: Can proceed sequentially or in parallel once setup review is complete
  - User Story 1 (P1): Can start immediately after setup review
  - User Story 2 (P2): Should follow User Story 1 to build on orange background
  - User Story 3 (P3): Should follow User Stories 1 & 2 to extend theme to dark mode
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies - applies basic orange background
- **User Story 2 (P2)**: Builds on US1 - refines text/element colors for contrast on orange background
- **User Story 3 (P3)**: Builds on US1 & US2 - extends the complete orange theme to dark mode

### Within Each User Story

- Phase 3 (US1): Tasks T004-T008 modify the same file (index.css, App.css) but different CSS rules - should be done sequentially to avoid conflicts
- Phase 4 (US2): Tasks T009-T015 modify CSS variables and rules - sequential execution recommended for consistency
- Phase 5 (US3): Tasks T016-T020 modify dark mode selectors - sequential execution recommended

### Parallel Opportunities

- Tasks T001-T003 in Setup can be done in parallel (review tasks, no file modifications)
- Within Phase 6, tasks T021-T022 and T025 marked [P] can run in parallel (different concerns)
- If multiple developers available: after completing US1, one developer can work on US2 while another explores US3 dark mode requirements

---

## Parallel Example: User Story 1

```bash
# For User Story 1, tasks must be done sequentially since they all modify frontend/src/index.css:
# Complete in order: T004 → T005 → T006 → T007 → T008

# Phase 6 Polish tasks can run in parallel:
Task T021: "Visual verification of orange background across all screens"
Task T022: "Accessibility validation using browser dev tools"
Task T025: "Update README or documentation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (review existing structure)
2. Skip Phase 2: Foundational (not needed - infrastructure exists)
3. Complete Phase 3: User Story 1 (apply orange background)
4. **STOP and VALIDATE**: Visually verify orange background on all screens
5. Deploy/demo if ready - orange background is visible

### Incremental Delivery

1. Complete Setup → understand existing theme system
2. Add User Story 1 → Orange background applied → Validate independently
3. Add User Story 2 → Text contrast improved → Validate accessibility → Deploy/Demo
4. Add User Story 3 → Dark mode consistency → Validate theme switching → Deploy/Demo
5. Each story adds value without breaking previous stories

### Sequential Implementation (Recommended)

Given that most tasks modify the same CSS files (index.css, App.css):

1. Complete Setup (Phase 1): Review current system
2. Implement User Story 1 (Phase 3): Apply orange background to all screens
3. Implement User Story 2 (Phase 4): Refine text and element contrast
4. Implement User Story 3 (Phase 5): Extend to dark mode with smooth transitions
5. Polish (Phase 6): Final validation and edge case review

---

## Notes

- Tasks primarily modify frontend/src/index.css and frontend/src/App.css
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable by loading the app
- Sequential execution recommended for CSS modifications to avoid merge conflicts
- Visual verification is critical - check orange (#FFA500) appears correctly
- Accessibility contrast validation is required per WCAG AA standards (4.5:1 normal text, 3:1 large text)
- No new files need to be created - only existing CSS files are modified
- Theme toggle functionality already exists in frontend/src/hooks/useAppTheme.ts
- Stop at any checkpoint to validate story independently before proceeding
