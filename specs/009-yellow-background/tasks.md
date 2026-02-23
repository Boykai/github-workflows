# Tasks: Add Yellow Background to App

**Input**: Design documents from `/specs/009-yellow-background/`
**Prerequisites**: spec.md (required — loaded), plan.md (not available — tasks derived from spec.md and codebase analysis)

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for frontend code

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project initialization needed — the app already exists with a working theme system using CSS custom properties in `frontend/src/index.css`. This phase ensures the design token is defined centrally before any user story work begins.

- [ ] T001 Define yellow background design token `--color-bg: #FFF9C4` in `:root` of `frontend/src/index.css`
- [ ] T002 Define yellow secondary background token `--color-bg-secondary: #FFF8E1` in `:root` of `frontend/src/index.css`

**Checkpoint**: Yellow design tokens are defined centrally. All subsequent phases reference these tokens.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No additional foundational infrastructure is needed. The existing CSS custom property system (`frontend/src/index.css`) and theme toggle hook (`frontend/src/hooks/useAppTheme.ts`) already provide the foundation. Phase 1 tokens are the only prerequisite.

**⚠️ CRITICAL**: Phase 1 must be complete before proceeding — all user stories depend on the design tokens being defined.

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Global Yellow Background (Priority: P1) 🎯 MVP

**Goal**: Apply a yellow background (#FFF9C4) globally at the root level so it appears on all pages and views in light mode.

**Independent Test**: Open the app in a browser in light mode, navigate to any page (login, dashboard, settings, chat), and visually confirm the background is yellow. Inspect `:root` and `body` to confirm yellow color values are applied via CSS custom properties.

### Implementation for User Story 1

- [ ] T003 [US1] Apply `background-color: var(--color-bg)` to the `body` selector in `frontend/src/index.css` (replace current `background: var(--color-bg-secondary)` if needed, or verify it cascades correctly)
- [ ] T004 [US1] Verify the root app wrapper element in `frontend/src/App.tsx` does not override the body background with a conflicting color
- [ ] T005 [P] [US1] Audit `frontend/src/App.css` for any hard-coded background colors on layout containers that would override the yellow background, and update them to use `var(--color-bg)` or `var(--color-bg-secondary)`
- [ ] T006 [US1] Verify yellow background persists across all routes and views (authenticated and unauthenticated pages) by inspecting page components in `frontend/src/pages/`

**Checkpoint**: At this point, the app displays a yellow background on all pages in light mode. User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Accessibility and Readability (Priority: P1)

**Goal**: Ensure all text, icons, and interactive elements maintain a minimum 4.5:1 contrast ratio against the yellow background (#FFF9C4) per WCAG 2.1 AA.

**Independent Test**: Use a contrast-checking tool (e.g., browser DevTools accessibility panel, axe DevTools, or WebAIM Contrast Checker) to verify all foreground text against `#FFF9C4` meets 4.5:1. Visually confirm buttons, cards, modals, and inputs remain legible.

### Implementation for User Story 2

- [ ] T007 [US2] Audit `--color-text` (#24292f) contrast against `#FFF9C4` in `frontend/src/index.css` — verify it meets 4.5:1 ratio and adjust if below (expected: passes, dark text on light yellow)
- [ ] T008 [US2] Audit `--color-text-secondary` (#57606a) contrast against `#FFF9C4` in `frontend/src/index.css` — adjust if below 4.5:1 ratio
- [ ] T009 [P] [US2] Verify button styles in `frontend/src/App.css` remain legible against yellow background — check `.login-button`, `.modal-github-btn`, and other button classes
- [ ] T010 [P] [US2] Verify card, modal, and input component backgrounds in `frontend/src/App.css` retain their own background colors and remain visually distinct against yellow
- [ ] T011 [US2] Verify `--color-secondary` (#6e7781) and `--color-warning` (#9a6700) tokens in `frontend/src/index.css` maintain sufficient contrast against yellow for any elements using them as foreground colors — adjust if below 4.5:1 ratio

**Checkpoint**: All text and UI elements meet WCAG 2.1 AA contrast requirements against the yellow background. User Story 2 is complete.

---

## Phase 5: User Story 3 — Dark Mode Handling (Priority: P2)

**Goal**: Ensure dark mode retains its existing dark background colors and is not affected by the yellow background change. Yellow appears only in light mode.

**Independent Test**: Toggle the app to dark mode using the theme switch and verify the background is dark (#0d1117 / #161b22). Toggle back to light mode and verify yellow (#FFF9C4) appears.

### Implementation for User Story 3

- [ ] T012 [US3] Verify `html.dark-mode-active` overrides in `frontend/src/index.css` still define `--color-bg: #0d1117` and `--color-bg-secondary: #161b22` — confirm dark values are not affected by the light-mode yellow token change
- [ ] T013 [US3] Verify `useAppTheme` hook in `frontend/src/hooks/useAppTheme.ts` correctly toggles the `dark-mode-active` class on the `<html>` element, ensuring CSS specificity allows dark mode to override light mode tokens
- [ ] T014 [US3] Test theme toggle round-trip: light (yellow) → dark (dark bg) → light (yellow) to confirm no visual glitches or stuck states

**Checkpoint**: Dark mode is fully unaffected by the yellow background. Light/dark toggle works correctly. User Story 3 is complete.

---

## Phase 6: User Story 4 — Cross-Browser and Cross-Device Consistency (Priority: P3)

**Goal**: Confirm the yellow background renders consistently across Chrome, Firefox, Safari, and Edge on desktop and mobile viewports.

**Independent Test**: Open the app in each of the four major browsers on desktop and resize to mobile viewport widths. Visually confirm the yellow background covers the full viewport with no gaps or rendering artifacts.

### Implementation for User Story 4

- [ ] T015 [US4] Test yellow background rendering in Chrome (desktop and mobile viewport) — verify no gaps, no rendering artifacts
- [ ] T016 [P] [US4] Test yellow background rendering in Firefox (desktop and mobile viewport)
- [ ] T017 [P] [US4] Test yellow background rendering in Safari (desktop and mobile viewport)
- [ ] T018 [P] [US4] Test yellow background rendering in Edge (desktop and mobile viewport)
- [ ] T019 [US4] Verify `min-height: 100vh` or equivalent is applied so yellow background covers full viewport on short-content pages — check `body` and root wrapper in `frontend/src/index.css` and `frontend/src/App.css`

**Checkpoint**: Yellow background renders consistently across all target browsers and viewports. User Story 4 is complete.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup and validation across all user stories.

- [ ] T020 Confirm yellow color value `#FFF9C4` is defined in exactly one location (`:root` in `frontend/src/index.css`) with no duplicate hard-coded values across the codebase
- [ ] T021 Run a full accessibility audit (e.g., Lighthouse or axe DevTools) on the app to flag any remaining contrast or accessibility regressions introduced by the yellow background
- [ ] T022 Verify modals and overlays display correctly — yellow background should be visible behind semi-transparent overlays, modal content areas retain their own background in `frontend/src/App.css`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (design tokens defined) — no additional work needed
- **User Story 1 (Phase 3)**: Depends on Phase 1 tokens being defined
- **User Story 2 (Phase 4)**: Depends on Phase 3 (yellow background must be applied before contrast can be audited)
- **User Story 3 (Phase 5)**: Depends on Phase 1 (dark mode verification requires tokens to be changed)
- **User Story 4 (Phase 6)**: Depends on Phase 3 (yellow background must be applied before cross-browser testing)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 (yellow background must be visible to audit contrast)
- **User Story 3 (P2)**: Can start after Phase 1 — independent of US1 and US2 (dark mode verification only needs the token change)
- **User Story 4 (P3)**: Depends on US1 (background must be applied before cross-browser testing)

### Parallel Opportunities

- T001 and T002 (Phase 1 token definitions) are in the same file — must be sequential
- T005 can run in parallel with T003/T004 (different files or independent audit)
- T009 and T010 (US2 button and component audit) can run in parallel (independent inspections)
- T016, T017, T018 (US4 browser testing) can run in parallel (independent browser tests)
- US3 (Phase 5) can start in parallel with US2 (Phase 4) since they are independent

---

## Parallel Example: User Story 2

```bash
# Launch parallel audit tasks:
Task: T009 "Verify button styles in frontend/src/App.css"
Task: T010 "Verify card, modal, and input component backgrounds in frontend/src/App.css"
```

## Parallel Example: User Story 4

```bash
# Launch parallel browser tests:
Task: T016 "Test yellow background in Firefox"
Task: T017 "Test yellow background in Safari"
Task: T018 "Test yellow background in Edge"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Define yellow design tokens in `frontend/src/index.css`
2. Complete Phase 3: Apply yellow background globally (US1)
3. **STOP and VALIDATE**: Open app, confirm yellow background on all pages in light mode
4. Deploy/demo if ready — core feature is delivered

### Incremental Delivery

1. Phase 1 → Design tokens defined
2. Add User Story 1 → Yellow background visible → Deploy/Demo (MVP!)
3. Add User Story 2 → Contrast/accessibility verified → Deploy/Demo
4. Add User Story 3 → Dark mode verified → Deploy/Demo
5. Add User Story 4 → Cross-browser verified → Deploy/Demo
6. Each story adds confidence without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Developer A: Phase 1 → US1 → US2 (sequential dependency chain)
2. Developer B: After Phase 1, start US3 (independent of US1/US2)
3. After US1 complete: Developer B can also start US4
4. Polish phase after all stories complete

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 22 |
| Phase 1 (Setup) | 2 tasks |
| Phase 2 (Foundational) | 0 tasks (no additional infrastructure needed) |
| Phase 3 / US1 — Global Yellow Background (P1) | 4 tasks |
| Phase 4 / US2 — Accessibility and Readability (P1) | 5 tasks |
| Phase 5 / US3 — Dark Mode Handling (P2) | 3 tasks |
| Phase 6 / US4 — Cross-Browser Consistency (P3) | 5 tasks |
| Phase 7 (Polish) | 3 tasks |
| Parallel Opportunities | 8 tasks marked [P] |
| MVP Scope | Phase 1 + US1 (6 tasks) |
| Files Modified | Primarily `frontend/src/index.css`, audit `frontend/src/App.css` and `frontend/src/App.tsx` |

---

## Notes

- [P] tasks = different files or independent audits, no dependencies
- [Story] label maps task to specific user story for traceability
- No test tasks generated — tests were not explicitly requested in the feature specification
- The yellow color (#FFF9C4) is a warm, light yellow chosen for readability per spec.md assumptions
- Dark mode values in `html.dark-mode-active` are NOT modified — yellow applies only in light mode
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
