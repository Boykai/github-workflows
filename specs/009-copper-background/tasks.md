# Tasks: Add Copper Background Theme to App

**Input**: Design documents from `/specs/009-copper-background/`
**Prerequisites**: spec.md (user stories and requirements)

**Tests**: No test tasks are included — tests were not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for all frontend files
- CSS theming tokens: `frontend/src/index.css`
- Component styles: `frontend/src/App.css`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Apply copper background to the root-level theme tokens so it cascades globally via the existing CSS custom property system

- [ ] T001 Update `:root` `--color-bg` from `#ffffff` to `#B87333` (copper) in `frontend/src/index.css`
- [ ] T002 Update `:root` `--color-bg-secondary` from `#f6f8fa` to a complementary copper shade (e.g., `#C47F3F` or `#D4956A`) in `frontend/src/index.css`
- [ ] T003 Update `html.dark-mode-active` `--color-bg` from `#0d1117` to `#8C4A2F` (dark copper) in `frontend/src/index.css`
- [ ] T004 Update `html.dark-mode-active` `--color-bg-secondary` from `#161b22` to a darker copper shade (e.g., `#6B3A24`) in `frontend/src/index.css`

**Checkpoint**: Foundation ready — copper background now cascades globally via CSS custom properties. All `var(--color-bg)` and `var(--color-bg-secondary)` references automatically pick up the copper tones.

---

## Phase 2: User Story 1 — Copper Background Applied Globally (Priority: P1) 🎯 MVP

**Goal**: Every page, route, and container in the app displays the copper background. No screen shows the previous white/light background.

**Independent Test**: Navigate to every route in the app (login, chat, project board, settings) and visually confirm the background is a copper tone.

### Implementation for User Story 1

- [ ] T005 [US1] Update `--color-text` to ensure readable text on copper background (e.g., `#1a1a1a` or `#FFFFFF`) in `:root` block in `frontend/src/index.css`
- [ ] T006 [US1] Update `--color-text-secondary` to ensure readable secondary text on copper background in `:root` block in `frontend/src/index.css`
- [ ] T007 [US1] Update `--color-border` to harmonize with copper background in `:root` block in `frontend/src/index.css`
- [ ] T008 [P] [US1] Audit `.app-loading` and `.app-login` backgrounds in `frontend/src/App.css` — ensure they inherit copper via `var(--color-bg)` or `var(--color-bg-secondary)` (no hardcoded white/light values)
- [ ] T009 [P] [US1] Audit `.app-header` background in `frontend/src/App.css` — update if using hardcoded values instead of copper-compatible tokens
- [ ] T010 [P] [US1] Audit `.chat-section` and `.chat-placeholder` backgrounds in `frontend/src/App.css` — ensure copper compatibility
- [ ] T011 [P] [US1] Audit `.project-sidebar` background in `frontend/src/App.css` — ensure it uses copper-compatible token (currently `var(--color-bg)`)
- [ ] T012 [US1] Verify copper background renders consistently on mobile, tablet, and desktop by checking no fixed-width or overflow issues in `frontend/src/App.css` responsive rules

**Checkpoint**: At this point, User Story 1 should be fully functional — copper background visible on all pages and routes.

---

## Phase 3: User Story 2 — Accessible Text and UI Elements on Copper Background (Priority: P1)

**Goal**: All text, icons, buttons, inputs, badges, and alerts maintain at least 4.5:1 contrast ratio against the copper background per WCAG 2.1 AA.

**Independent Test**: Run a contrast-ratio check on any page and verify all foreground elements pass 4.5:1 against the copper background.

### Implementation for User Story 2

- [ ] T013 [US2] Verify and adjust `.login-button` and `.header-nav-btn` contrast against copper background in `frontend/src/App.css`
- [ ] T014 [P] [US2] Verify and adjust `.task-card` text, status badges (`.task-status`), and priority labels contrast against copper in `frontend/src/App.css`
- [ ] T015 [P] [US2] Verify and adjust `.chat-input`, `.chat-message`, and `.chat-bubble` text contrast against copper background in `frontend/src/App.css`
- [ ] T016 [P] [US2] Verify and adjust settings page form inputs and labels contrast in `frontend/src/App.css`
- [ ] T017 [US2] Audit all hardcoded color values (e.g., `#fff1f0`, `#dafbe1`, `rgba(...)` backgrounds) in `frontend/src/App.css` for contrast against copper and update as needed
- [ ] T018 [US2] Update `--color-shadow` / `--shadow` value in `frontend/src/index.css` to be visible against copper background

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — copper background is visible everywhere with accessible contrast.

---

## Phase 4: User Story 3 — Harmonized Overlays and Secondary Surfaces (Priority: P2)

**Goal**: Modals, drawers, sidebars, cards, and overlay components visually complement the copper background without clashing.

**Independent Test**: Open a modal, drawer, and sidebar. Visually confirm each either uses the copper tone or a complementary color that harmonizes.

### Implementation for User Story 3

- [ ] T019 [P] [US3] Audit and update modal overlay background (`.modal-overlay`, `.modal-content`) in `frontend/src/App.css` to harmonize with copper theme
- [ ] T020 [P] [US3] Audit and update sidebar/drawer backgrounds (`.project-sidebar`, `.sidebar-header`) in `frontend/src/App.css` to use copper-complementary tones
- [ ] T021 [P] [US3] Audit and update card backgrounds (`.task-card`, `.board-column`) in `frontend/src/App.css` to be distinguishable from copper background while maintaining cohesion
- [ ] T022 [US3] Audit and update tooltip, dropdown, and popover backgrounds in `frontend/src/App.css` for copper theme harmony

**Checkpoint**: All overlay and secondary surface components now harmonize with the copper background.

---

## Phase 5: User Story 4 — Dark Mode Copper Variant (Priority: P3)

**Goal**: Toggling dark mode produces a darker copper variant that maintains accessibility and visual coherence.

**Independent Test**: Toggle dark mode on and off. Verify the copper background shifts to a darker variant in dark mode and returns to standard copper in light mode.

### Implementation for User Story 4

- [ ] T023 [US4] Update `html.dark-mode-active` `--color-text` to ensure readable text on dark copper background in `frontend/src/index.css`
- [ ] T024 [US4] Update `html.dark-mode-active` `--color-text-secondary` for readable secondary text on dark copper in `frontend/src/index.css`
- [ ] T025 [US4] Update `html.dark-mode-active` `--color-border` to harmonize with dark copper in `frontend/src/index.css`
- [ ] T026 [US4] Audit all dark-mode-specific overrides in `frontend/src/App.css` for compatibility with dark copper background (search for `dark-mode-active` selectors or media queries)
- [ ] T027 [US4] Verify seamless transition between light copper and dark copper when toggling theme via `useAppTheme` hook in `frontend/src/hooks/useAppTheme.ts` (no visual artifacts)

**Checkpoint**: Dark mode copper variant is fully functional with accessible contrast.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all user stories

- [ ] T028 [P] Run full visual regression check across all routes (login, chat, board, settings) in both light and dark copper modes
- [ ] T029 [P] Run accessibility contrast audit on all pages using browser DevTools or axe-core to confirm WCAG 2.1 AA compliance
- [ ] T030 Verify the copper color is defined in exactly one location (design tokens in `frontend/src/index.css`) and changing the token value updates the entire app
- [ ] T031 Remove any remaining hardcoded white/light background values that conflict with the copper theme in `frontend/src/App.css`
- [ ] T032 Verify no component-level CSS files in `frontend/src/components/` or `frontend/src/pages/` contain hardcoded backgrounds that override copper

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately; BLOCKS all user stories
- **User Story 1 (Phase 2)**: Depends on Setup (Phase 1)
- **User Story 2 (Phase 3)**: Depends on Setup (Phase 1); works best after US1 is in place
- **User Story 3 (Phase 4)**: Depends on Setup (Phase 1)
- **User Story 4 (Phase 5)**: Depends on Setup (Phase 1); builds on dark mode tokens from Phase 1
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Phase 1 — best done after US1 so copper background is visible during contrast auditing
- **User Story 3 (P2)**: Can start after Phase 1 — independent of US1/US2
- **User Story 4 (P3)**: Can start after Phase 1 — independent but benefits from US1+US2 being done

### Within Each User Story

- Audit existing styles before making changes
- Update token values before component-level overrides
- Core implementation before integration testing
- Story complete before moving to next priority

### Parallel Opportunities

- Within Phase 1: T001–T004 are sequential (same file, related values)
- Within US1: T008, T009, T010, T011 marked [P] — different CSS selectors, no dependencies
- Within US2: T014, T015, T016 marked [P] — different component areas
- Within US3: T019, T020, T021 marked [P] — different overlay types
- US1 and US3 can proceed in parallel after Phase 1
- US4 can proceed in parallel with US2/US3 after Phase 1

---

## Parallel Example: User Story 1

```bash
# After Phase 1 tokens are set, launch parallel audits:
Task T008: "Audit .app-loading and .app-login backgrounds in frontend/src/App.css"
Task T009: "Audit .app-header background in frontend/src/App.css"
Task T010: "Audit .chat-section backgrounds in frontend/src/App.css"
Task T011: "Audit .project-sidebar background in frontend/src/App.css"
```

---

## Parallel Example: User Story 3

```bash
# Overlay harmonization tasks can run in parallel:
Task T019: "Audit modal overlay backgrounds in frontend/src/App.css"
Task T020: "Audit sidebar/drawer backgrounds in frontend/src/App.css"
Task T021: "Audit card backgrounds in frontend/src/App.css"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Apply copper to root theme variables
2. Complete Phase 2: User Story 1 — copper background on all pages
3. Complete Phase 3: User Story 2 — accessible contrast on copper
4. **STOP and VALIDATE**: Copper background is visible everywhere with accessible text
5. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Complete Phase 1 (Setup) → Copper tokens applied globally
2. Add User Story 1 (Phase 2) → Copper visible on all pages → Deploy/Demo (MVP!)
3. Add User Story 2 (Phase 3) → Contrast accessibility verified → Deploy/Demo
4. Add User Story 3 (Phase 4) → Overlays harmonized → Deploy/Demo
5. Add User Story 4 (Phase 5) → Dark mode copper variant → Deploy/Demo
6. Each story adds visual polish without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) together (small, fast)
2. Once Phase 1 is done:
   - Developer A: User Story 1 (global background) + User Story 2 (contrast)
   - Developer B: User Story 3 (overlays) + User Story 4 (dark mode)
3. Stories integrate independently via shared CSS tokens

---

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 32 |
| Phase 1 (Setup) | 4 tasks |
| Phase 2 (US1 — Global Background) | 8 tasks |
| Phase 3 (US2 — Accessibility) | 6 tasks |
| Phase 4 (US3 — Overlays) | 4 tasks |
| Phase 5 (US4 — Dark Mode) | 5 tasks |
| Phase 6 (Polish) | 5 tasks |
| Parallel Opportunities | 12 tasks marked [P] |
| MVP Scope | US1 + US2 (Phases 1–3, 18 tasks) |
| Primary Files Modified | `frontend/src/index.css`, `frontend/src/App.css` |

## Notes

- [P] tasks = different files or selectors, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- The copper theme leverages the existing CSS custom property system — no new theming infrastructure needed
- The `useAppTheme` hook already manages dark mode toggling — no hook changes required, only CSS token updates
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
