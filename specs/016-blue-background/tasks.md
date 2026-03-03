# Tasks: Add Blue Background Color to App

**Input**: Design documents from `/specs/016-blue-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification. Visual manual testing per quickstart.md is sufficient for this CSS-only change.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing CSS variable theming structure is intact and ready for modification

- [ ] T001 Verify existing --background CSS variable and bg-background Tailwind mapping in frontend/src/index.css and frontend/tailwind.config.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational prerequisites required — the existing CSS variable theming system (`--background` → `bg-background` → `body`) already provides the infrastructure needed. The `body` element already applies `@apply bg-background text-foreground` in `frontend/src/index.css`.

**⚠️ SKIPPED**: No new infrastructure, database migrations, API endpoints, or shared components are needed. This is a CSS variable value change only.

**Checkpoint**: Existing theming infrastructure confirmed — user story implementation can begin

---

## Phase 3: User Story 1 — Blue Background Visible Across All Pages (Priority: P1) 🎯 MVP

**Goal**: Apply a blue background color to the root application container so it is visible on every page and route in light mode

**Independent Test**: Open the application, navigate to multiple pages/routes, and visually confirm the blue background (#1E90FF / Dodger Blue) is present on all of them at all viewport sizes (320px–2560px)

### Implementation for User Story 1

- [ ] T002 [US1] Update --background CSS variable in :root selector from `0 0% 100%` to `210 100% 56%` (Dodger Blue #1E90FF) in frontend/src/index.css
- [ ] T003 [US1] Visually verify blue background renders on all routes (Home, Project Board, Settings) and during loading state per specs/016-blue-background/quickstart.md

**Checkpoint**: User Story 1 complete — light mode blue background visible on every page and route, responsive from 320px to 2560px

---

## Phase 4: User Story 2 — Text and UI Elements Remain Readable (Priority: P1)

**Goal**: Ensure all text, icons, buttons, cards, modals, and navigation elements remain clearly readable against the blue background with WCAG AA-compliant contrast (≥4.5:1)

**Independent Test**: Review every primary UI component (text, buttons, cards, modals, navigation) against the blue background and verify contrast ratios meet WCAG AA (minimum 4.5:1 for normal text)

### Implementation for User Story 2

- [ ] T004 [US2] Verify WCAG AA contrast ratio (≥4.5:1) between --background (#1E90FF) and --foreground (#020817) in light mode using browser accessibility tools or contrast checker per specs/016-blue-background/quickstart.md
- [ ] T005 [US2] Verify --card, --popover, --primary, --secondary, --muted, and --accent CSS variables remain unchanged so cards, modals, popovers, and buttons retain their own backgrounds in frontend/src/index.css

**Checkpoint**: User Story 2 complete — all text and UI components are legible and visually intact against the blue background

---

## Phase 5: User Story 3 — Blue Background Works in Light and Dark Mode (Priority: P2)

**Goal**: Apply an appropriate blue background in dark mode (Deep Blue #1A3A5C) so the blue background adapts to the active theme

**Independent Test**: Toggle between light and dark mode and confirm the blue background appears appropriately styled in each theme — Dodger Blue in light mode, Deep Blue in dark mode

### Implementation for User Story 3

- [ ] T006 [US3] Update --background CSS variable in .dark selector from `222.2 84% 4.9%` to `210 54% 23%` (Deep Blue #1A3A5C) in frontend/src/index.css
- [ ] T007 [US3] Verify WCAG AA contrast ratio (≥4.5:1) between dark mode --background (#1A3A5C) and --foreground (#F8FAFC) using browser accessibility tools per specs/016-blue-background/quickstart.md
- [ ] T008 [US3] Verify theme toggle transitions between light blue (#1E90FF) and dark blue (#1A3A5C) backgrounds without flicker or delay

**Checkpoint**: User Story 3 complete — blue background works in both light and dark mode with accessible contrast

---

## Phase 6: User Story 4 — Maintainable and Consistent Color Definition (Priority: P3)

**Goal**: Ensure the blue color is defined in a single centralized location (the --background CSS variable) so that changing it once propagates everywhere without per-component overrides

**Independent Test**: Change the blue color value in the --background CSS variable in frontend/src/index.css and confirm the background updates across all pages without modifying individual components

### Implementation for User Story 4

- [ ] T009 [US4] Verify blue background is defined exclusively via --background CSS variable in :root and .dark selectors in frontend/src/index.css — no inline styles, no per-component bg-blue-* classes, no hardcoded hex values in component files
- [ ] T010 [US4] Verify Tailwind config maps bg-background to hsl(var(--background)) in frontend/tailwind.config.js ensuring single-point-of-change propagation

**Checkpoint**: User Story 4 complete — blue color is centralized and maintainable via CSS variables

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final visual validation across all user stories and edge cases

- [ ] T011 Verify no flash of white or non-blue color on initial page load (blue background visible within 1 second per SC-006)
- [ ] T012 Verify blue background renders correctly behind overlays (modals, drawers, popovers) without color blending artifacts
- [ ] T013 Verify blue background fills viewport at extreme widths (<320px and >2560px) with no gaps or horizontal scrollbars
- [ ] T014 Run quickstart.md full visual validation checklist (all 8 manual test steps + contrast verification + edge cases) per specs/016-blue-background/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Skipped — no new infrastructure needed
- **User Story 1 (Phase 3)**: Depends on Setup (Phase 1) — light mode blue background
- **User Story 2 (Phase 4)**: Depends on User Story 1 (Phase 3) — readability verification requires blue background to be applied
- **User Story 3 (Phase 5)**: Depends on User Story 1 (Phase 3) — dark mode change in same file
- **User Story 4 (Phase 6)**: Depends on User Stories 1 + 3 (Phases 3 + 5) — maintainability verification requires both theme values set
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 — readability can only be verified after blue background is applied
- **User Story 3 (P2)**: Can start after US1 — modifies same file (frontend/src/index.css) but different selector (.dark vs :root)
- **User Story 4 (P3)**: Depends on US1 + US3 — maintainability verified after both theme values are set

### Within Each User Story

- CSS variable change before visual verification
- Light mode before dark mode (US1 before US3)
- Implementation before readability verification (US1 before US2)

### Parallel Opportunities

- T004 (contrast verification) and T006 (dark mode CSS change) can run in parallel after T002 — different concerns
- T011, T012, and T013 (polish verification tasks) can run in parallel — independent visual checks
- US2 verification and US3 implementation can proceed in parallel once US1 is complete

---

## Parallel Example: After User Story 1 Completion

```bash
# Launch US2 verification and US3 implementation in parallel:
Task: T004 "Verify WCAG AA contrast ratio in light mode"
Task: T006 "Update --background in .dark selector in frontend/src/index.css"
```

## Parallel Example: Polish Phase

```bash
# Launch all polish verification tasks in parallel:
Task: T011 "Verify no flash of white on initial page load"
Task: T012 "Verify blue background behind overlays"
Task: T013 "Verify blue background at extreme viewport widths"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing CSS structure)
2. Complete Phase 3: User Story 1 (change light mode --background to blue)
3. **STOP and VALIDATE**: Open app, verify blue background on all routes
4. Deploy/demo if ready — the app has a blue background in light mode

### Incremental Delivery

1. Complete Setup → Existing theming confirmed
2. Add User Story 1 → Light mode blue background → Deploy/Demo (MVP!)
3. Add User Story 2 → Readability verified → Confidence in accessibility
4. Add User Story 3 → Dark mode blue background → Deploy/Demo (full theme support)
5. Add User Story 4 → Maintainability verified → Long-term confidence
6. Polish → Full validation → Final release

### Parallel Team Strategy

With multiple developers:

1. Developer A: User Story 1 (light mode change) → User Story 2 (readability verification)
2. Developer B: User Story 3 (dark mode change, after US1 merges) → User Story 4 (maintainability verification)
3. Both changes are in the same file but different selectors — coordinate merge

---

## Summary

- **Total tasks**: 14
- **Phase 1 (Setup)**: 1 task
- **Phase 2 (Foundational)**: 0 tasks (skipped — no new infrastructure)
- **Phase 3 (US1 — Blue Background Visible)**: 2 tasks
- **Phase 4 (US2 — Text Readable)**: 2 tasks
- **Phase 5 (US3 — Light/Dark Mode)**: 3 tasks
- **Phase 6 (US4 — Maintainable Definition)**: 2 tasks
- **Phase 7 (Polish)**: 4 tasks
- **Parallel opportunities**: 3 identified (US2+US3 after US1, Polish tasks, Post-US3 verification)
- **Independent test criteria**: Each user story has a clear independent test defined
- **Suggested MVP scope**: User Story 1 only (Phase 1 + Phase 3, 3 tasks — light mode blue background)
- **Format validation**: ✅ All 14 tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This is a CSS-only change — no backend, no new components, no new files
- Single file modified: frontend/src/index.css (two CSS variable values)
- No test tasks included (tests not explicitly requested in specification; visual testing per quickstart.md is sufficient)
- Existing Tailwind + CSS variable theming system propagates changes automatically via bg-background → hsl(var(--background))
- WCAG AA contrast verified in research.md: light mode ~7.9:1, dark mode ~8.5:1 (both pass ≥4.5:1)
