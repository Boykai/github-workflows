# Tasks: Add Purple Background Color to Application

**Input**: Design documents from `/specs/012-purple-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Existing vitest suite covers regression. Manual visual inspection and WCAG contrast audit are the primary verification methods.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (existing project structure)
- Only `frontend/src/index.css` requires code modification
- All other files consume the `--background` CSS custom property indirectly through Tailwind's `bg-background` utility

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project structure and confirm theming system baseline before making changes

- [ ] T001 Verify frontend dependencies are installed by running `cd frontend && npm install`
- [ ] T002 Verify current CSS custom property values in `frontend/src/index.css` match expected baseline (`:root` and `.dark` selectors)
- [ ] T003 Confirm `frontend/src/index.css` body rule applies `@apply bg-background text-foreground` to verify token propagation path

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking infrastructure tasks needed — the existing shadcn/ui CSS variable system, Tailwind config (`frontend/tailwind.config.js`), and theme provider (`frontend/src/components/ThemeProvider.tsx`) are already in place. The `--background` token is already consumed via `bg-background` across all components.

**⚠️ CRITICAL**: No changes to Tailwind config, ThemeProvider, or component files are required. Only CSS custom property _values_ in `index.css` need updating.

**Checkpoint**: Foundation verified — user story implementation can now begin.

---

## Phase 3: User Story 1 — Purple Background on All Pages (Priority: P1) 🎯 MVP

**Goal**: Apply a purple background color to the application's primary background surface on all pages and routes by updating the `--background` CSS custom property value in both light and dark mode.

**Independent Test**: Navigate to every page/route in the application and visually confirm the primary background surface is purple on each one.

### Implementation for User Story 1

- [ ] T004 [US1] Update light-mode `--background` value from `0 0% 100%` to `270 50% 40%` in `:root` selector in `frontend/src/index.css`
- [ ] T005 [US1] Update dark-mode `--background` value from `222.2 84% 4.9%` to `270 50% 20%` in `.dark` selector in `frontend/src/index.css`
- [ ] T006 [US1] Visually verify purple background renders on all pages/routes (Home, Project Board, Settings) in both light and dark mode

**Checkpoint**: At this point, the primary background surface should be purple on all pages. Text may not yet be readable — that is addressed in User Story 2.

---

## Phase 4: User Story 2 — Readable Text and Interactive Elements (Priority: P1)

**Goal**: Ensure all text and interactive elements meet WCAG AA contrast ratio standards (≥ 4.5:1) against the purple background by updating foreground and surface token values.

**Independent Test**: Run a WCAG contrast checker on all text/surface combinations and confirm all meet ≥ 4.5:1 contrast ratio.

### Implementation for User Story 2

- [ ] T007 [US2] Update light-mode `--foreground` value from `222.2 84% 4.9%` to `210 40% 98%` in `:root` selector in `frontend/src/index.css`
- [ ] T008 [P] [US2] Update light-mode `--primary` value to `210 40% 98%` and `--primary-foreground` to `270 50% 40%` in `:root` selector in `frontend/src/index.css`
- [ ] T009 [P] [US2] Update light-mode `--secondary` value to `270 40% 50%` and `--secondary-foreground` to `210 40% 98%` in `:root` selector in `frontend/src/index.css`
- [ ] T010 [P] [US2] Update light-mode `--muted` value to `270 30% 50%` and `--muted-foreground` to `270 20% 80%` in `:root` selector in `frontend/src/index.css`
- [ ] T011 [P] [US2] Update light-mode `--accent` value to `270 40% 50%` and `--accent-foreground` to `210 40% 98%` in `:root` selector in `frontend/src/index.css`
- [ ] T012 [P] [US2] Update light-mode `--destructive-foreground` to `210 40% 98%` in `:root` selector in `frontend/src/index.css` (destructive hue unchanged)
- [ ] T013 [P] [US2] Update light-mode `--border` to `270 30% 55%`, `--input` to `270 30% 55%`, and `--ring` to `210 40% 98%` in `:root` selector in `frontend/src/index.css`
- [ ] T014 [US2] Update dark-mode `--primary-foreground` to `270 50% 20%` in `.dark` selector in `frontend/src/index.css`
- [ ] T015 [P] [US2] Update dark-mode `--secondary` to `270 40% 30%` and `--secondary-foreground` to `210 40% 98%` in `.dark` selector in `frontend/src/index.css`
- [ ] T016 [P] [US2] Update dark-mode `--muted` to `270 30% 30%` and `--muted-foreground` to `270 20% 70%` in `.dark` selector in `frontend/src/index.css`
- [ ] T017 [P] [US2] Update dark-mode `--accent` to `270 40% 30%` and `--accent-foreground` to `210 40% 98%` in `.dark` selector in `frontend/src/index.css`
- [ ] T018 [P] [US2] Update dark-mode `--border` to `270 30% 35%`, `--input` to `270 30% 35%`, and `--ring` to `270 30% 70%` in `.dark` selector in `frontend/src/index.css`
- [ ] T019 [US2] Verify WCAG AA contrast ratio ≥ 4.5:1 for all foreground/surface token combinations using a contrast checker tool

**Checkpoint**: At this point, the purple background should be applied AND all text/interactive elements should be readable and meet WCAG AA standards.

---

## Phase 5: User Story 3 — Consistent Appearance Across Browsers (Priority: P2)

**Goal**: Verify the purple background renders correctly and identically across Chrome, Firefox, Safari, and Edge.

**Independent Test**: Open the application in each browser and compare purple background rendering.

### Implementation for User Story 3

- [ ] T020 [US3] Verify purple background renders correctly in Chrome (latest) by loading all pages
- [ ] T021 [P] [US3] Verify purple background renders correctly in Firefox (latest) and matches Chrome appearance
- [ ] T022 [P] [US3] Verify purple background renders correctly in Safari (latest) and matches Chrome appearance
- [ ] T023 [P] [US3] Verify purple background renders correctly in Edge (latest) and matches Chrome appearance

**Checkpoint**: At this point, the purple background should render identically across all major browsers.

---

## Phase 6: User Story 4 — No Visual Regressions on Existing Components (Priority: P2)

**Goal**: Confirm that all existing UI components remain visually coherent and functional after the background color change.

**Independent Test**: Navigate through all pages and interact with every UI component to confirm no visual or functional regressions.

### Implementation for User Story 4

- [ ] T024 [US4] Update light-mode `--card` to `270 50% 45%` and `--card-foreground` to `210 40% 98%` in `:root` selector in `frontend/src/index.css`
- [ ] T025 [P] [US4] Update light-mode `--popover` to `270 50% 45%` and `--popover-foreground` to `210 40% 98%` in `:root` selector in `frontend/src/index.css`
- [ ] T026 [US4] Update dark-mode `--card` to `270 50% 25%` and `--card-foreground` to `210 40% 98%` in `.dark` selector in `frontend/src/index.css`
- [ ] T027 [P] [US4] Update dark-mode `--popover` to `270 50% 25%` and `--popover-foreground` to `210 40% 98%` in `.dark` selector in `frontend/src/index.css`
- [ ] T028 [US4] Visually audit header, sidebar, and navigation components for coherence with purple background
- [ ] T029 [P] [US4] Visually audit card, modal, and popover components for distinct boundaries against purple background
- [ ] T030 [P] [US4] Visually audit button variants (default, outline, secondary, ghost, destructive) for visibility and usability
- [ ] T031 [P] [US4] Visually audit input fields, select dropdowns, and form elements for visible borders and text legibility
- [ ] T032 [US4] Visually audit board columns, chat interface, and any content-rich pages for readability

**Checkpoint**: All existing components remain visually correct and functional with the purple background.

---

## Phase 7: User Story 5 — Theme Mode Compatibility (Priority: P3)

**Goal**: Ensure the purple background uses appropriate light and dark mode variants with smooth transitions between modes.

**Independent Test**: Toggle between light and dark modes and confirm appropriate purple variants display with smooth transitions.

### Implementation for User Story 5

- [ ] T033 [US5] Verify light-mode purple variant (`270 50% 40%`) displays correctly when application is in light mode
- [ ] T034 [US5] Verify dark-mode purple variant (`270 50% 20%`) displays correctly when application is in dark mode
- [ ] T035 [US5] Toggle between light and dark modes and confirm smooth transition with no flash of non-purple color
- [ ] T036 [US5] Verify ThemeProvider (`frontend/src/components/ThemeProvider.tsx`) correctly toggles `.dark` class to switch between purple variants

**Checkpoint**: Purple background works correctly in both theme modes with smooth transitions.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, build verification, and cleanup

- [ ] T037 Run frontend type checking with `cd frontend && npm run type-check`
- [ ] T038 [P] Run frontend linting with `cd frontend && npm run lint`
- [ ] T039 [P] Run frontend unit tests with `cd frontend && npm run test`
- [ ] T040 Run frontend build with `cd frontend && npm run build`
- [ ] T041 Run quickstart.md verification checklist from `specs/012-purple-background/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — verification only (no code changes)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — updates `--background` token
- **User Story 2 (Phase 4)**: Depends on Phase 3 — updates foreground/surface tokens to ensure contrast
- **User Story 3 (Phase 5)**: Depends on Phase 4 — cross-browser verification requires all token changes to be in place
- **User Story 4 (Phase 6)**: Depends on Phase 4 — updates `--card` and `--popover` tokens, audits all components
- **User Story 5 (Phase 7)**: Depends on Phase 4 — both mode variants must be final before testing transitions
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — core background change, no story dependencies
- **User Story 2 (P1)**: Depends on User Story 1 — contrast is only meaningful after background is purple
- **User Story 3 (P2)**: Depends on User Story 2 — cross-browser verification should cover final token state
- **User Story 4 (P2)**: Depends on User Story 2 — component audit requires all contrast fixes in place; can run in parallel with User Story 3
- **User Story 5 (P3)**: Depends on User Story 2 — both mode variants must be finalized before testing transitions; can run in parallel with User Stories 3 and 4

### Within Each User Story

- Token value changes before visual verification
- Surface tokens before foreground tokens (where applicable)
- Core implementation before integration/audit tasks

### Parallel Opportunities

- T008–T013 (Phase 4): All light-mode token updates can run in parallel (different CSS properties)
- T014–T018 (Phase 4): All dark-mode token updates can run in parallel
- T020–T023 (Phase 5): All browser verifications can run in parallel
- T024–T027 (Phase 6): Card and popover token updates can run in parallel
- T028–T032 (Phase 6): Component audits can run in parallel
- T037–T039 (Phase 8): Type checking, linting, and unit tests can run in parallel
- **User Stories 3, 4, and 5 can run in parallel** once User Story 2 is complete

---

## Parallel Example: User Story 2

```bash
# Launch all light-mode token updates together (after T007):
Task: "T008 [P] [US2] Update light-mode --primary and --primary-foreground in frontend/src/index.css"
Task: "T009 [P] [US2] Update light-mode --secondary and --secondary-foreground in frontend/src/index.css"
Task: "T010 [P] [US2] Update light-mode --muted and --muted-foreground in frontend/src/index.css"
Task: "T011 [P] [US2] Update light-mode --accent and --accent-foreground in frontend/src/index.css"
Task: "T012 [P] [US2] Update light-mode --destructive-foreground in frontend/src/index.css"
Task: "T013 [P] [US2] Update light-mode --border, --input, --ring in frontend/src/index.css"

# Launch all dark-mode token updates together (after T014):
Task: "T015 [P] [US2] Update dark-mode --secondary and --secondary-foreground in frontend/src/index.css"
Task: "T016 [P] [US2] Update dark-mode --muted and --muted-foreground in frontend/src/index.css"
Task: "T017 [P] [US2] Update dark-mode --accent and --accent-foreground in frontend/src/index.css"
Task: "T018 [P] [US2] Update dark-mode --border, --input, --ring in frontend/src/index.css"
```

## Parallel Example: User Story 4

```bash
# Launch all component audits together:
Task: "T028 [US4] Visually audit header, sidebar, and navigation components"
Task: "T029 [P] [US4] Visually audit card, modal, and popover components"
Task: "T030 [P] [US4] Visually audit button variants"
Task: "T031 [P] [US4] Visually audit input fields and form elements"
Task: "T032 [US4] Visually audit board columns and content-rich pages"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete Phase 1: Setup verification
2. Complete Phase 2: Foundational verification
3. Complete Phase 3: User Story 1 — Purple background on all pages
4. Complete Phase 4: User Story 2 — Readable text and interactive elements
5. **STOP and VALIDATE**: All pages have purple background with readable text
6. Deploy/demo if ready — this is the minimum viable purple background

### Incremental Delivery

1. Complete Setup + Foundational → Baseline verified
2. Add User Story 1 → Purple background visible → Visual confirmation
3. Add User Story 2 → All text readable → WCAG audit passes (MVP!)
4. Add User Story 3 → Cross-browser verified → Browser testing complete
5. Add User Story 4 → No regressions → Component audit complete
6. Add User Story 5 → Theme mode compatible → Full feature complete
7. Each story adds quality assurance without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational verification together
2. Developer A: User Story 1 → User Story 2 (sequential dependency)
3. Once User Story 2 is done:
   - Developer A: User Story 3 (browser testing)
   - Developer B: User Story 4 (regression audit)
   - Developer C: User Story 5 (theme mode testing)
4. Stories 3, 4, and 5 complete and validate independently

---

## Notes

- [P] tasks = different CSS properties or independent verification, no dependencies
- [Story] label maps task to specific user story for traceability
- This is a single-file change (`frontend/src/index.css`) — all implementation tasks modify CSS custom property values in that file
- No new files, components, or dependencies are introduced
- Tests are not explicitly requested — verification is via manual visual inspection and WCAG contrast audit
- All HSL values use space-separated format without `hsl()` wrapper per shadcn/ui convention
- Commit after each task or logical group (e.g., all light-mode tokens, all dark-mode tokens)
- Stop at any checkpoint to validate story independently
