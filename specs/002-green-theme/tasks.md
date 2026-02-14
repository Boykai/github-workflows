---

description: "Task list for green theme feature implementation"
---

# Tasks: Green Theme Option

**Input**: Design documents from `/specs/002-green-theme/`
**Prerequisites**: spec.md (user stories with priorities)

**Tests**: Tests are NOT requested in the feature specification, so no test tasks are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No additional setup required - existing React app with theme infrastructure already in place

**Status**: ✅ Complete - App already has theme system with useAppTheme hook and CSS variables

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend theme system to support multiple themes beyond dark/light toggle

**⚠️ CRITICAL**: This phase MUST be complete before ANY user story can be implemented

- [ ] T001 Refactor useAppTheme hook to support multiple theme options (not just dark/light toggle) in frontend/src/hooks/useAppTheme.ts
- [ ] T002 Update theme type definitions to support 'default', 'dark', 'green' theme values in frontend/src/hooks/useAppTheme.ts

**Checkpoint**: Foundation ready - theme system can handle multiple themes, user story implementation can now begin

---

## Phase 3: User Story 1 - Theme Selection and Instant Application (Priority: P1) 🎯 MVP

**Goal**: Users can select the "Green" theme from settings and see all UI elements instantly update to green tones across the entire application interface.

**Independent Test**: Navigate to user settings, select "Green" theme from the theme selector, and verify all visible UI elements (buttons, headers, links, backgrounds) display green colors immediately. Navigate to different screens to confirm green theme is applied consistently.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Define green theme CSS custom properties (color palette for primary, backgrounds, text, borders) in frontend/src/index.css
- [ ] T004 [P] [US1] Update App.tsx to replace theme toggle button with theme selector dropdown in frontend/src/App.tsx
- [ ] T005 [US1] Add green theme option to the theme selector UI control in frontend/src/App.tsx
- [ ] T006 [US1] Connect theme selector to useAppTheme hook to apply selected theme in frontend/src/App.tsx
- [ ] T007 [US1] Verify theme changes apply instantly without page refresh across all app screens

**Checkpoint**: At this point, User Story 1 should be fully functional - users can select green theme and see it applied immediately across the entire app.

---

## Phase 4: User Story 2 - Theme Persistence Across Sessions (Priority: P2)

**Goal**: Users' green theme selection is remembered and automatically applied when they return to the app (after closing/reopening or logout/login).

**Independent Test**: Select green theme, close and reopen the browser/app (or logout and login), and verify the green theme is automatically applied on startup. Test on different browsers/devices to confirm device-specific persistence.

### Implementation for User Story 2

- [ ] T008 [US2] Update localStorage logic in useAppTheme hook to persist multi-theme selection (not just dark/light) in frontend/src/hooks/useAppTheme.ts
- [ ] T009 [US2] Implement graceful fallback to default theme if stored theme value is corrupted or invalid in frontend/src/hooks/useAppTheme.ts
- [ ] T010 [US2] Verify theme preference persists across browser close/reopen scenarios
- [ ] T011 [US2] Verify theme preference is device-specific (each browser/device maintains its own selection)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - users can select green theme, it applies instantly, and persists across sessions.

---

## Phase 5: User Story 3 - Accessible Color Contrast (Priority: P3)

**Goal**: The green theme maintains WCAG 2.1 Level AA accessibility standards with sufficient contrast ratios (4.5:1 for normal text, 3:1 for large text) between text and backgrounds.

**Independent Test**: With green theme active, use automated accessibility tools (browser DevTools Lighthouse, axe DevTools, or WebAIM contrast checker) to verify all text elements meet minimum contrast ratios. Manually review all screens to check text readability against green backgrounds.

### Implementation for User Story 3

- [ ] T012 [US3] Review green theme color values against WCAG 2.1 Level AA contrast requirements in frontend/src/index.css
- [ ] T013 [US3] Adjust green theme colors to ensure 4.5:1 contrast ratio for normal text in frontend/src/index.css
- [ ] T014 [US3] Adjust green theme colors to ensure 3:1 contrast ratio for large text in frontend/src/index.css
- [ ] T015 [US3] Run accessibility audit using browser DevTools or automated tools to validate contrast ratios
- [ ] T016 [US3] Document green theme color values and their contrast ratios for future reference

**Checkpoint**: All user stories should now be independently functional - green theme is selectable, persists across sessions, and meets accessibility standards.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements and validation

- [ ] T017 [P] Update README or documentation to mention new green theme option
- [ ] T018 Manual testing across different screens and components to ensure consistent green theme application
- [ ] T019 Cross-browser testing (Chrome, Firefox, Safari, Edge) for theme persistence and display

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: ✅ Complete - No work needed
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories (T001-T002)
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational → T003-T007
  - User Story 2 (P2): Depends on User Story 1 completion → T008-T011
  - User Story 3 (P3): Depends on User Story 1 completion (needs green theme CSS to exist) → T012-T016
- **Polish (Phase 6)**: Depends on all user stories being complete → T017-T019

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core MVP functionality
- **User Story 2 (P2)**: Depends on User Story 1 (needs theme selection to work first, then adds persistence)
- **User Story 3 (P3)**: Depends on User Story 1 (needs green theme colors to exist before validating contrast)

### Within Each User Story

- **User Story 1**: T003 and T004 are parallel [P] - can be done simultaneously. T005-T007 are sequential (need T004 complete first).
- **User Story 2**: All tasks are sequential (each builds on previous)
- **User Story 3**: All tasks are sequential (color review → adjustments → validation → documentation)

### Parallel Opportunities

- Foundational tasks T001 and T002 can be done together (both edit the same file but different concerns)
- User Story 1: T003 (CSS) and T004 (UI component) can be done in parallel initially
- Polish phase: T017 and T018 can be done in parallel

---

## Parallel Example: User Story 1

```bash
# Launch foundational tasks together:
Task T001: "Refactor useAppTheme hook to support multiple theme options"
Task T002: "Update theme type definitions"

# Launch initial User Story 1 tasks in parallel:
Task T003: "Define green theme CSS custom properties in frontend/src/index.css"
Task T004: "Update App.tsx to replace theme toggle with selector in frontend/src/App.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001-T002) → Theme system ready for multiple themes
2. Complete Phase 3: User Story 1 (T003-T007) → Green theme selectable and instantly applied
3. **STOP and VALIDATE**: Test User Story 1 independently - select green theme, verify it applies across all screens
4. Deploy/demo if ready → Users can now select and use green theme

### Incremental Delivery

1. Complete Foundational → Foundation ready (multi-theme support)
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Green theme works)
3. Add User Story 2 → Test independently → Deploy/Demo (Green theme persists)
4. Add User Story 3 → Test independently → Deploy/Demo (Green theme is accessible)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Foundational together (T001-T002)
2. Once Foundational is done:
   - Developer A: User Story 1 (T003-T007) - Core implementation
   - Developer B: Prepare documentation (T017) in parallel
3. After User Story 1 complete:
   - Developer A: User Story 2 (T008-T011) - Persistence
   - Developer B: User Story 3 (T012-T016) - Accessibility
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files or independent concerns, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No tests included (not requested in specification)
- Theme system leverages existing CSS custom properties pattern
- Existing localStorage pattern will be extended for multi-theme support
- Stop at any checkpoint to validate story independently
- FR-006 (visual feedback for active theme) is satisfied by selector UI showing current selection
- FR-007 (graceful fallback) is handled in Task T009
