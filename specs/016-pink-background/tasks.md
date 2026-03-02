# Tasks: Add Pink Background Color to App

**Input**: Design documents from `/specs/016-pink-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/no-api.md, quickstart.md

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification. Visual verification is sufficient per the constitution check.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing theming infrastructure and confirm implementation approach

- [ ] T001 Verify existing CSS custom property infrastructure (--background variable in :root and .dark scopes, Tailwind bg-background mapping, body @apply) in frontend/src/index.css and frontend/tailwind.config.js

---

## Phase 2: User Story 1 — Pink Background Visible Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Update the light mode background color from white (#FFFFFF) to light pink (#FFC0CB) by changing the --background CSS variable in the :root scope. The pink background should be visible across all screens and responsive breakpoints.

**Independent Test**: Open the app in a browser in light mode, navigate through every screen, and verify the background is consistently light pink (#FFC0CB) on all pages, on mobile/tablet/desktop viewports, with no white gaps on minimal-content pages.

### Implementation for User Story 1

- [ ] T002 [US1] Update --background CSS variable in :root scope from `0 0% 100%` to `350 100% 88%` (light pink #FFC0CB) in frontend/src/index.css
- [ ] T003 [US1] Verify light mode pink background renders correctly by running frontend build and lint in frontend/ (npm run build && npm run lint)

**Checkpoint**: Light mode pink background is applied globally — all screens display #FFC0CB background in light mode

---

## Phase 3: User Story 2 — Readable Content on Pink Background (Priority: P1)

**Goal**: Ensure all foreground text, icons, and interactive elements maintain WCAG AA-compliant contrast ratios against the new pink background. Per research.md (R3), no foreground color changes are needed — existing tokens already pass.

**Independent Test**: Inspect all text, icons, and interactive elements across all screens in light mode. Verify primary text (#020817) achieves ~16.5:1 contrast against #FFC0CB. Verify muted foreground (#64748b) achieves ~3.7:1 (passes for large text/UI elements). Verify all button states (hover, focus, active, disabled) are distinguishable.

### Implementation for User Story 2

- [ ] T004 [US2] Audit all foreground token contrast ratios against new light pink background (#FFC0CB) — confirm --foreground (~16.5:1), --primary (~15.2:1), --muted-foreground (~3.7:1) all pass WCAG AA thresholds per research.md (R3) in frontend/src/index.css

**Checkpoint**: All foreground tokens verified for WCAG AA compliance against light pink background — no changes required

---

## Phase 4: User Story 3 — Dark Mode Pink Background Variant (Priority: P2)

**Goal**: Update the dark mode background from near-black (#020817) to a muted dark pink (#8B475D) by changing the --background CSS variable in the .dark scope. The dark pink variant should be comfortable for low-light viewing while maintaining the pink aesthetic.

**Independent Test**: Toggle dark mode (add class="dark" to <html> or use app toggle), verify background displays muted dark pink (#8B475D), verify all text remains readable (foreground ~7.2:1 contrast ratio), and verify smooth transition between light and dark modes.

### Implementation for User Story 3

- [ ] T005 [US3] Update --background CSS variable in .dark scope from `222.2 84% 4.9%` to `340 33% 41%` (muted dark pink #8B475D) in frontend/src/index.css
- [ ] T006 [US3] Audit all foreground token contrast ratios against new dark pink background (#8B475D) — confirm --foreground (~7.2:1), --primary (~7.2:1), --muted-foreground (~3.1:1) all pass WCAG AA thresholds per research.md (R3) in frontend/src/index.css

**Checkpoint**: Dark mode pink variant applied — muted dark pink (#8B475D) displays correctly with all text readable

---

## Phase 5: User Story 4 — No Layout or Visual Regressions (Priority: P1)

**Goal**: Confirm that the background color change does not break any existing layout, component positioning, z-index stacking, or visual rendering. Components with their own background colors (cards, modals, popovers) should retain their existing backgrounds.

**Independent Test**: Perform a visual comparison of all screens before and after the change. Verify component positions, spacing, alignment are unchanged. Verify overlays, modals, and dropdowns display correctly. Verify scrolling behavior is unaffected. Verify component backgrounds (--card, --popover) are independent of --background.

### Implementation for User Story 4

- [ ] T007 [US4] Verify no layout regressions by confirming all other CSS variables in :root and .dark scopes remain unchanged in frontend/src/index.css
- [ ] T008 [US4] Run existing frontend test suite to confirm no regressions (npm test in frontend/)

**Checkpoint**: Zero layout regressions — only --background values changed, all other styling intact

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T009 [P] Verify pink background fills entire viewport on minimal-content pages (body bg-background already covers viewport per research.md R6)
- [ ] T010 [P] Verify no visual artifacts or color flashes during page transitions (pink background persists via body-level CSS variable)
- [ ] T011 Run quickstart.md full validation (light mode, dark mode, responsive, accessibility checks) per specs/016-pink-background/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **User Story 1 (Phase 2)**: Depends on Setup — core light mode change
- **User Story 2 (Phase 3)**: Depends on User Story 1 — verifies contrast against new light mode background
- **User Story 3 (Phase 4)**: Depends on Setup — modifies .dark scope independently of :root scope, but recommended sequential after US1 since both edit the same file
- **User Story 4 (Phase 5)**: Depends on User Stories 1 AND 3 — regression check after all CSS changes are made
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 — contrast audit requires the new background to be defined
- **User Story 3 (P2)**: Recommended after US1 — modifies .dark scope independently but same file; sequential avoids merge conflicts
- **User Story 4 (P1)**: Depends on US1 and US3 — regression check after all CSS changes are made

### Within Each User Story

- CSS variable change before verification
- Contrast audit after background change
- Build/test validation after implementation

### Parallel Opportunities

- T009 and T010 (polish verification tasks) can run in parallel — independent validation checks
- US1 and US3 implementation tasks modify different CSS scopes but the same file — recommended sequential to avoid conflicts

---

## Parallel Example: User Stories 1 and 3

```bash
# Both modify frontend/src/index.css but at different CSS scopes:
Task: T002 "Update --background in :root scope (light mode) in frontend/src/index.css"
Task: T005 "Update --background in .dark scope (dark mode) in frontend/src/index.css"
# Recommended: Run sequentially (US1 then US3) to avoid merge conflicts in same file
```

## Parallel Example: Polish Phase

```bash
# Launch verification tasks in parallel (independent checks):
Task: T009 "Verify viewport fill on minimal-content pages"
Task: T010 "Verify no visual artifacts during page transitions"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify infrastructure)
2. Complete Phase 2: User Story 1 (light mode pink background)
3. **STOP and VALIDATE**: Test light mode pink background independently
4. Deploy/demo if ready — core pink background is visible

### Incremental Delivery

1. Complete Setup → Infrastructure verified
2. Add User Story 1 → Light mode pink → Deploy/Demo (MVP!)
3. Add User Story 2 → Contrast verified → Confidence in accessibility
4. Add User Story 3 → Dark mode pink → Deploy/Demo
5. Add User Story 4 → Regression check → Confidence in stability
6. Polish → Full validation → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
   - Developer A: User Story 1 (light mode) → User Story 2 (contrast audit)
   - Developer A (continued): User Story 3 (dark mode) → User Story 4 (regression check after all changes)
3. Note: Since all changes are in a single file, parallel team work is limited; sequential execution is recommended

---

## Summary

- **Total tasks**: 11
- **Phase 1 (Setup)**: 1 task
- **Phase 2 (US1 — Pink Background Visible)**: 2 tasks
- **Phase 3 (US2 — Readable Content)**: 1 task
- **Phase 4 (US3 — Dark Mode Variant)**: 2 tasks
- **Phase 5 (US4 — No Regressions)**: 2 tasks
- **Phase 6 (Polish)**: 3 tasks
- **Parallel opportunities**: 1 identified (Polish verification tasks)
- **Independent test criteria**: Each user story has a clear independent test defined
- **Suggested MVP scope**: User Story 1 only (Phase 1–2, 3 tasks — light mode pink background)
- **Format validation**: ✅ All 11 tasks follow checklist format (checkbox, ID, labels, file paths)
- **File changes**: 1 file modified (`frontend/src/index.css`), 2 CSS variable values changed

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is an XS feature (0.5h estimate) — a 2-line CSS variable change in a single file
- No new files, dependencies, or backend changes are required
- The existing Tailwind + shadcn/ui theming system handles propagation automatically
- No test tasks included (tests not explicitly requested in specification; visual verification sufficient)
- HSL values must be without hsl() wrapper to match existing shadcn/ui format (R4)
- Component backgrounds (--card, --popover, etc.) are independent of --background and unaffected (R5)
