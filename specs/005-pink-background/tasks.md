# Tasks: Pink Background Color

**Input**: Design documents from `/specs/005-pink-background/`
**Prerequisites**: spec.md ✅

**Tests**: Not explicitly requested in specification. No test tasks included.

**Organization**: Tasks grouped by user story for independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths included

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Define the centralized pink background color variable

- [ ] T001 Add `--color-bg-pink` CSS custom property set to `#FFC0CB` in the `:root` block in frontend/src/index.css

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Update the core background color tokens that ALL UI elements depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Update `--color-bg-secondary` value from `#f6f8fa` to `var(--color-bg-pink)` in the `:root` block in frontend/src/index.css so the body and secondary backgrounds use pink
- [ ] T003 Override `--color-bg-pink` with an appropriately dark/desaturated pink (e.g., `#2b1a1e`) in the `html.dark-mode-active` block in frontend/src/index.css (CSS scoping ensures this overrides the `:root` value when dark mode is active)
- [ ] T004 Update `--color-bg-secondary` value from `#161b22` to `var(--color-bg-pink)` in the `html.dark-mode-active` block in frontend/src/index.css

**Checkpoint**: Foundation ready - centralized pink variable defined for both light and dark themes

---

## Phase 3: User Story 1 - Consistent Pink Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: The entire app displays a pink background color consistently on every screen

**Independent Test**: Open the application, navigate through all primary screens, and verify the pink background (#FFC0CB) is visible everywhere including scrollable areas

### Implementation for User Story 1

- [ ] T005 [US1] Verify the `body` selector in frontend/src/index.css uses `background: var(--color-bg-secondary)` which now resolves to pink, and confirm full-height coverage with `min-height: 100vh` if not already set
- [ ] T006 [US1] Audit `.app-container`, `.app-header`, `.board-page`, `.chat-section`, and `.project-sidebar` background declarations in frontend/src/App.css to ensure they use `var(--color-bg)` or `var(--color-bg-secondary)` tokens rather than hardcoded colors
- [ ] T007 [US1] Verify the pink background renders correctly on mobile, tablet, and desktop viewports by checking no fixed-height containers clip the background in frontend/src/App.css

**Checkpoint**: User Story 1 complete - pink background visible across all screens and viewport sizes

---

## Phase 4: User Story 2 - Readable Text and UI Elements on Pink Background (Priority: P1)

**Goal**: All text, buttons, icons, and interactive elements remain clearly legible against the pink background

**Independent Test**: Visually inspect all UI elements (headings, body text, buttons, input fields, cards, badges) against the pink background and verify contrast ratios meet WCAG AA (4.5:1 minimum for normal text)

### Implementation for User Story 2

- [ ] T008 [US2] Verify `--color-text` (#24292f dark text) maintains at least 4.5:1 contrast ratio against #FFC0CB background in frontend/src/index.css; adjust text color if needed
- [ ] T009 [P] [US2] Verify `--color-text-secondary` (#57606a) maintains at least 4.5:1 contrast ratio against #FFC0CB background in frontend/src/index.css; darken if needed (e.g., to #4d5561)
- [ ] T010 [P] [US2] Verify buttons (.login-button, .logout-button, .board-retry-btn) remain visually distinct on the pink background in frontend/src/App.css
- [ ] T011 [P] [US2] Verify card components (.task-card, .board-issue-card, .agent-tile) with `var(--color-bg)` backgrounds remain distinguishable from the pink `var(--color-bg-secondary)` background in frontend/src/App.css
- [ ] T012 [US2] Verify dark mode text colors maintain WCAG AA contrast against the dark pink variant in frontend/src/index.css

**Checkpoint**: User Story 2 complete - all text and UI elements pass WCAG AA contrast requirements

---

## Phase 5: User Story 3 - Centralized Color Definition for Easy Future Updates (Priority: P2)

**Goal**: The pink background color is defined in a single centralized location so future color changes require editing only one value

**Independent Test**: Change the `--color-bg-pink` value in `:root` to a different color (e.g., `#90EE90`) and verify the entire app updates from that single change in light mode; also change the `--color-bg-pink` value in `html.dark-mode-active` and verify the dark mode app updates accordingly

### Implementation for User Story 3

- [ ] T013 [US3] Search the entire codebase for hardcoded background color values (`#f6f8fa`, `#ffffff`, `background: white`, `bg-white`) and replace with appropriate CSS variable references in frontend/src/App.css and frontend/src/index.css
- [ ] T014 [US3] Verify no inline background styles exist in React components by searching frontend/src/App.tsx, frontend/src/components/, and frontend/src/pages/ for hardcoded background values

**Checkpoint**: User Story 3 complete - single centralized color token controls the pink background everywhere

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and edge case handling

- [ ] T015 [P] Verify the pink background extends to full scrollable height on pages with long content in frontend/src/App.css
- [ ] T016 [P] Verify existing component background overrides (cards, modals, inputs) retain their intentional styling and remain visually distinct against the pink background in frontend/src/App.css
- [ ] T017 Run full visual regression check across all pages to confirm no layout or contrast regressions

**Checkpoint**: Feature complete and polished

---

## Dependencies Graph

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 3 (US1)    Phase 4 (US2)     Phase 5 (US3)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                Phase 6 (Polish)
```

**Notes**:
- US1, US2, US3 can be implemented in parallel after Phase 2
- US2 (contrast verification) can run alongside US1 (background application)
- US3 (centralization) can start once US1 confirms the variable approach works
- Phase 6 tasks are all parallelizable

---

## Parallel Execution Examples

**Maximum parallelism after Phase 2**:
- T005 + T008 + T013 (US1 + US2 + US3 starting tasks) in parallel
- T009 + T010 + T011 (US2 contrast checks) in parallel
- T015 + T016 (polish tasks) in parallel

**Suggested execution order for single developer**:
1. T001 (setup variable)
2. T002-T004 (foundational tokens)
3. T005-T007 (US1 background application)
4. T008-T012 (US2 contrast verification)
5. T013-T014 (US3 centralization)
6. T015-T017 (polish)

---

## Implementation Strategy

**MVP Scope**: Complete Phase 1, 2, and 3 (User Story 1) for minimum viable feature — pink background visible everywhere

**Incremental Delivery**:
1. **MVP**: Pink background applied globally via centralized CSS variable (US1)
2. **+US2**: All text and UI elements verified for WCAG AA contrast compliance
3. **+US3**: All hardcoded colors replaced with centralized token
4. **+Polish**: Edge cases handled, visual regression check passed

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 17 |
| Phase 1 (Setup) | 1 task |
| Phase 2 (Foundational) | 3 tasks |
| US1 tasks | 3 tasks |
| US2 tasks | 5 tasks |
| US3 tasks | 2 tasks |
| Polish tasks | 3 tasks |
| Parallel opportunities | 8 tasks marked [P] or parallelizable within phases |
| MVP scope | US1 (Phases 1-3, tasks T001-T007) |
