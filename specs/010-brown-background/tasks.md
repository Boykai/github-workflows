# Tasks: Add Brown Background Color to App

**Input**: Design documents from `/specs/010-brown-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: No tests explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature is frontend-only (CSS theming change)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Audit existing theme system and identify all files that reference background colors

- [ ] T001 Audit existing CSS custom properties and background usage in frontend/src/index.css to catalog current --color-bg and --color-bg-secondary values for light and dark modes
- [ ] T002 [P] Audit component-level background overrides in frontend/src/App.css and frontend/src/components/chat/ChatInterface.css to identify styles that may conflict with the new global brown background

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the brown color design tokens that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Define a brown background design token --color-bg-brown in :root in frontend/src/index.css with a warm brown value (e.g., #795548) that meets WCAG AA contrast with white/light text, and add a comment referencing the design decision
- [ ] T004 [P] Select appropriate text color values (--color-text, --color-text-secondary) that achieve minimum 4.5:1 contrast ratio against the chosen brown background and document the contrast ratios as comments in frontend/src/index.css

**Checkpoint**: Brown design tokens defined — user story implementation can now begin

---

## Phase 3: User Story 1 — Global Brown Background (Priority: P1) 🎯 MVP

**Goal**: Apply a brown background color to the root/global container visible on all pages and views with full viewport coverage

**Independent Test**: Navigate to any page in the application and visually confirm the brown background is present, covers the full viewport with no white/grey/transparent gaps, and persists across route navigations without flickering

### Implementation for User Story 1

- [ ] T005 [US1] Update --color-bg and --color-bg-secondary values in :root to brown shades (using --color-bg-brown token) in frontend/src/index.css
- [ ] T006 [US1] Ensure body selector in frontend/src/index.css uses var(--color-bg-secondary) with min-height: 100vh to guarantee full viewport coverage with no gaps
- [ ] T007 [US1] Add inline background-color style matching the light-mode brown value to the <html> or <body> tag in frontend/index.html to prevent flash of white/default color on initial page load
- [ ] T008 [P] [US1] Review and update the .app-header background in frontend/src/App.css (line 57) to use a brown-compatible value (e.g., var(--color-bg)) so the header does not show a conflicting white/grey background
- [ ] T009 [P] [US1] Review and update the .theme-toggle-btn background in frontend/src/App.css (line 73) to ensure it is visually distinguishable against the brown background

**Checkpoint**: At this point, User Story 1 should be fully functional — brown background visible on all pages, full viewport coverage, no flickering on navigation

---

## Phase 4: User Story 2 — Accessible Contrast with Brown Background (Priority: P1)

**Goal**: Ensure all text, icons, and interactive UI elements maintain WCAG AA contrast ratios (4.5:1 normal text, 3:1 large text) against the brown background

**Independent Test**: Run a contrast checker on every page to verify all text and icon elements meet the minimum contrast ratio against the brown background

### Implementation for User Story 2

- [ ] T010 [US2] Update --color-text and --color-text-secondary in :root in frontend/src/index.css to colors that achieve ≥4.5:1 contrast ratio against the brown background
- [ ] T011 [P] [US2] Update --color-border and --color-primary token values in :root in frontend/src/index.css if they do not meet 3:1 contrast against the brown background for UI element visibility
- [ ] T012 [P] [US2] Audit hardcoded color values in frontend/src/App.css (e.g., #2da44e at line 348, #32383f at line 101) and update any that fail contrast requirements against the brown background
- [ ] T013 [US2] Verify the .app-login h1 and .app-login p text styles in frontend/src/App.css are readable against the brown background and adjust if needed

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — brown background with all text and UI elements meeting WCAG AA contrast

---

## Phase 5: User Story 3 — Dark Mode Compatibility (Priority: P2)

**Goal**: Provide an appropriate darker brown shade for dark mode that is visually comfortable and consistent with the dark theme

**Independent Test**: Toggle dark mode on and off and confirm the brown background adapts to a darker shade in dark mode and reverts to the lighter shade in light mode, with no flicker or visual artifacts

### Implementation for User Story 3

- [ ] T014 [US3] Update --color-bg and --color-bg-secondary values in html.dark-mode-active in frontend/src/index.css to darker brown shades appropriate for a dark theme context
- [ ] T015 [US3] Update --color-text and --color-text-secondary in html.dark-mode-active in frontend/src/index.css to ensure ≥4.5:1 contrast ratio against the dark brown background
- [ ] T016 [P] [US3] Update the inline background-color in frontend/index.html (added in T007) to use a CSS custom property or add a <script> that sets the correct initial brown shade based on stored theme preference to prevent flash on dark mode reload

**Checkpoint**: Light and dark modes both display appropriate brown shades with smooth toggling

---

## Phase 6: User Story 4 — Maintainable Color Definition (Priority: P2)

**Goal**: Ensure the brown color value is defined exactly once as a reusable design token so future theming changes require editing only one location

**Independent Test**: Change the --color-bg-brown token value in frontend/src/index.css and confirm the background updates everywhere without modifying any other file

### Implementation for User Story 4

- [ ] T017 [US4] Verify all brown background references in frontend/src/index.css use the --color-bg-brown token (or derived tokens like --color-bg, --color-bg-secondary) rather than hardcoded hex values
- [ ] T018 [P] [US4] Verify no hardcoded brown hex values exist in frontend/src/App.css or frontend/src/components/chat/ChatInterface.css — all must reference CSS custom properties
- [ ] T019 [US4] Add a design-decision comment block at the top of the :root section in frontend/src/index.css documenting the chosen brown shade, contrast ratios, and reference to spec FR-002

**Checkpoint**: Brown color defined as a single design token; changing it in one place updates the entire app

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and cross-cutting verification

- [ ] T020 [P] Remove any remaining default white or grey background overrides in frontend/src/App.css that conflict with the global brown (FR-007)
- [ ] T021 [P] Remove any remaining default white or grey background overrides in frontend/src/components/chat/ChatInterface.css that conflict with the global brown
- [ ] T022 Perform visual review across all major pages (login, dashboard, board, chat, settings) to confirm consistent brown background rendering
- [ ] T023 Verify the brown background renders consistently on Chrome, Firefox, Safari, and Edge at desktop and mobile viewport sizes (FR-008)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — core visual change
- **US2 (Phase 4)**: Depends on US1 (Phase 3) — contrast validation requires brown background to be applied
- **US3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US2
- **US4 (Phase 6)**: Depends on US1 and US3 — validates token usage after all color changes are made
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (brown background must be applied before contrast can be audited)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — independent of US1/US2 (dark mode tokens only)
- **User Story 4 (P2)**: Should run after US1 and US3 to validate all token references are consistent

### Within Each User Story

- Models/tokens before application
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel (audit phase)
- T003 and T004 can run in parallel (foundational tokens)
- T008 and T009 can run in parallel (App.css component updates)
- T011 and T012 can run in parallel (contrast fixes)
- US1 and US3 can proceed in parallel after Foundational (different CSS selectors)
- T017 and T018 can run in parallel (token validation in different files)
- T020 and T021 can run in parallel (cleanup in different files)

---

## Parallel Example: User Story 1

```bash
# After Foundational phase completes, launch parallelizable US1 tasks:
Task T008: "Review and update .app-header background in frontend/src/App.css"
Task T009: "Review and update .theme-toggle-btn background in frontend/src/App.css"

# These can also run in parallel with US3 tasks (different CSS selectors):
Task T005 [US1]: "Update :root --color-bg values in frontend/src/index.css"
Task T014 [US3]: "Update html.dark-mode-active --color-bg values in frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (audit existing styles)
2. Complete Phase 2: Foundational (define brown design tokens)
3. Complete Phase 3: User Story 1 (apply global brown background)
4. **STOP and VALIDATE**: Visually confirm brown background on all pages, full viewport, no flickering
5. Deploy/demo if ready — this delivers the core feature value

### Incremental Delivery

1. Complete Setup + Foundational → Design tokens ready
2. Add User Story 1 → Brown background visible globally → Deploy/Demo (MVP!)
3. Add User Story 2 → Contrast verified, all text readable → Deploy/Demo
4. Add User Story 3 → Dark mode brown support → Deploy/Demo
5. Add User Story 4 → Token maintainability verified → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (light mode brown) + User Story 2 (contrast)
   - Developer B: User Story 3 (dark mode brown)
3. Both converge on User Story 4 (token validation)
4. Polish phase as a team

---

## Summary

- **Total tasks**: 23
- **User Story 1 (Global Brown BG)**: 5 tasks (T005–T009)
- **User Story 2 (Accessible Contrast)**: 4 tasks (T010–T013)
- **User Story 3 (Dark Mode)**: 3 tasks (T014–T016)
- **User Story 4 (Maintainable Token)**: 3 tasks (T017–T019)
- **Setup**: 2 tasks (T001–T002)
- **Foundational**: 2 tasks (T003–T004)
- **Polish**: 4 tasks (T020–T023)
- **Parallel opportunities**: 7 identified (see Parallel Opportunities section)
- **Suggested MVP scope**: User Story 1 only (Phase 1 + Phase 2 + Phase 3)

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No test tasks generated (tests not explicitly requested in spec)
- All paths reference the web app structure: frontend/src/
