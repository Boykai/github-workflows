# Tasks: Add Blue Background Color to App

**Input**: Design documents from `/specs/009-blue-background/`
**Prerequisites**: spec.md (available), plan.md (not available — tasks derived from spec.md and codebase analysis)

**Tests**: No test tasks included — tests were not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for frontend source files

## Tech Context (from codebase analysis)

- **Framework**: React + Vite + TypeScript
- **Styling**: CSS custom properties (`:root` for light, `html.dark-mode-active` for dark) in `frontend/src/index.css`
- **Theme hook**: `frontend/src/hooks/useAppTheme.ts` toggles `dark-mode-active` class on `<html>`
- **Root component**: `frontend/src/App.tsx` renders `<div className="app-container">`
- **Global styles**: `frontend/src/App.css` (component styles), `frontend/src/index.css` (design tokens + base styles)
- **Body background**: Currently `var(--color-bg-secondary)` (`#f6f8fa` light / `#161b22` dark)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No additional project setup needed — existing project structure and tooling are sufficient for this feature.

- [ ] T001 Verify existing design token structure and identify insertion points in frontend/src/index.css

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the blue background design token that all user stories depend on

**⚠️ CRITICAL**: No user story work can begin until the design token is established

- [ ] T002 Add `--color-bg-blue` CSS custom property to `:root` block in frontend/src/index.css with a brand-appropriate blue value (e.g., #1E90FF) that meets WCAG AA contrast with existing `--color-text` (#24292f)
- [ ] T003 Add `--color-bg-blue` CSS custom property to `html.dark-mode-active` block in frontend/src/index.css with an appropriate darker blue value that meets WCAG AA contrast with dark mode `--color-text` (#e6edf3)

**Checkpoint**: Blue background design token defined for both light and dark themes — user story implementation can now begin

---

## Phase 3: User Story 1 — Cohesive Blue Background Experience (Priority: P1) 🎯 MVP

**Goal**: Apply the blue background globally so it is visible across all pages and routes, on all viewport sizes, with no white flash on load

**Independent Test**: Navigate to any page in the app and verify the blue background is visible. Switch between routes and confirm no white flash occurs. Resize the viewport from mobile (320px) to desktop (1920px) and verify the background is consistent.

### Implementation for User Story 1

- [ ] T004 [US1] Update `body` background in frontend/src/index.css to use `var(--color-bg-blue)` instead of `var(--color-bg-secondary)`
- [ ] T005 [US1] Add `background-color: var(--color-bg-blue)` to `html` element in frontend/src/index.css to prevent white flash before body styles load
- [ ] T006 [US1] Verify blue background renders on all routes (chat view, project board, settings) by loading each view in the browser

**Checkpoint**: User Story 1 complete — blue background visible across all pages, responsive, no white flash

---

## Phase 4: User Story 2 — Accessible and Readable Content (Priority: P1)

**Goal**: Ensure all foreground text and UI elements remain readable against the blue background, meeting WCAG AA contrast requirements

**Independent Test**: Use a contrast checker tool to verify the blue background color against `--color-text` (#24292f light, #e6edf3 dark) achieves ≥4.5:1 ratio for normal text and ≥3:1 for large text. Visually inspect all pages for readability.

### Implementation for User Story 2

- [ ] T007 [US2] Validate contrast ratio of `--color-bg-blue` (light mode) against `--color-text` (#24292f) and `--color-text-secondary` (#57606a) — adjust blue value in frontend/src/index.css if ratio is below 4.5:1
- [ ] T008 [US2] Validate contrast ratio of `--color-bg-blue` (dark mode) against `--color-text` (#e6edf3) and `--color-text-secondary` (#8b949e) — adjust dark blue value in frontend/src/index.css if ratio is below 4.5:1
- [ ] T009 [US2] Review interactive elements (buttons, links, form fields) in frontend/src/App.css and component styles for readability against blue background — update specific foreground colors if needed

**Checkpoint**: User Story 2 complete — all text and UI elements meet WCAG AA contrast requirements on blue background

---

## Phase 5: User Story 3 — Maintainable Background Token (Priority: P2)

**Goal**: Ensure the blue background value is defined as a single reusable design token so future color changes require updating only one location

**Independent Test**: Change the `--color-bg-blue` value in frontend/src/index.css to a different color, reload the app, and verify the background updates globally from that single change.

### Implementation for User Story 3

- [ ] T010 [US3] Confirm `--color-bg-blue` token is the single source of truth — search frontend/src/ for any hardcoded blue background values and replace with `var(--color-bg-blue)` if found
- [ ] T011 [US3] Add a comment documenting the chosen blue hex value and its purpose above the `--color-bg-blue` token definition in frontend/src/index.css

**Checkpoint**: User Story 3 complete — blue background color defined in exactly one centralized location with documentation

---

## Phase 6: User Story 4 — Component Background Compatibility (Priority: P2)

**Goal**: Ensure individual UI components (modals, cards, sidebars) retain their own background colors and are not overridden by the global blue background

**Independent Test**: Navigate to pages with cards, modals, and the project sidebar. Verify each component displays its intended background color, distinct from the global blue.

### Implementation for User Story 4

- [ ] T012 [US4] Inspect sidebar component styles in frontend/src/App.css for explicit background declarations — verify they take precedence over global blue background
- [ ] T013 [US4] Inspect card and modal component styles in frontend/src/App.css and component-specific CSS for explicit background declarations — verify they are not overridden
- [ ] T014 [US4] Fix any component background styles in frontend/src/App.css that rely on inherited background instead of setting their own explicit background color

**Checkpoint**: User Story 4 complete — all components with intentional backgrounds render correctly against the blue app background

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [ ] T015 Perform full visual walkthrough of all views (login, chat, project board, settings) in both light and dark modes to confirm blue background and component rendering
- [ ] T016 Verify blue background extends fully on tall scrollable pages with no gaps or white areas visible at any scroll position

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) — needs the blue background applied to validate contrast
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — can run in parallel with US1/US2
- **User Story 4 (Phase 6)**: Depends on User Story 1 (Phase 3) — needs the blue background applied to verify component compatibility
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (needs blue background applied to test contrast against)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — Independent of other stories
- **User Story 4 (P2)**: Depends on US1 (needs blue background applied to verify component rendering)

### Within Each User Story

- Core CSS changes before visual validation
- Validation tasks depend on implementation tasks within the same story
- Story complete before moving to next priority

### Parallel Opportunities

- T002 and T003 (light and dark mode tokens) can run in parallel
- US3 (token maintainability) can run in parallel with US1 (background application)
- T012, T013 (component inspection) can run in parallel within US4

---

## Parallel Example: Foundational Phase

```bash
# Define blue tokens for both themes in parallel:
Task T002: "Add --color-bg-blue to :root in frontend/src/index.css"
Task T003: "Add --color-bg-blue to html.dark-mode-active in frontend/src/index.css"
```

## Parallel Example: User Story 4

```bash
# Inspect component backgrounds in parallel:
Task T012: "Inspect sidebar styles in frontend/src/App.css"
Task T013: "Inspect card/modal styles in frontend/src/App.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify token structure)
2. Complete Phase 2: Foundational (define `--color-bg-blue` tokens)
3. Complete Phase 3: User Story 1 (apply blue background globally)
4. **STOP and VALIDATE**: Blue background visible on all pages, all viewports, no white flash
5. Deploy/demo if ready — delivers primary visual value

### Incremental Delivery

1. Complete Setup + Foundational → Token infrastructure ready
2. Add User Story 1 → Blue background applied → Deploy/Demo (MVP!)
3. Add User Story 2 → Contrast validated → Deploy/Demo
4. Add User Story 3 → Token maintainability confirmed → Deploy/Demo
5. Add User Story 4 → Component compatibility verified → Deploy/Demo
6. Each story adds quality without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (apply background) → then User Story 2 (contrast validation)
   - Developer B: User Story 3 (token maintainability)
3. After US1 complete: Developer C: User Story 4 (component compatibility)
4. All complete → Polish phase

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 16 |
| Phase 1 (Setup) | 1 task |
| Phase 2 (Foundational) | 2 tasks |
| Phase 3 (US1 — Blue Background) | 3 tasks |
| Phase 4 (US2 — Accessibility) | 3 tasks |
| Phase 5 (US3 — Token Maintainability) | 2 tasks |
| Phase 6 (US4 — Component Compatibility) | 3 tasks |
| Phase 7 (Polish) | 2 tasks |
| Parallel opportunities | 3 sets (T002∥T003, US1∥US3, T012∥T013) |
| MVP scope | Phase 1 + 2 + 3 (User Story 1) — 6 tasks |
| Key files modified | frontend/src/index.css, frontend/src/App.css |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The exact blue hex value should be confirmed with stakeholders; the default choice should meet WCAG AA contrast with the existing text tokens
- No plan.md was available; tasks were derived from spec.md user stories and codebase analysis of the frontend theming system
