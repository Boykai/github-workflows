# Tasks: Apply Red Background Color to App

**Input**: Design documents from `/specs/003-red-background-app/`
**Prerequisites**: spec.md ✅, plan.md (not committed — color values and architecture confirmed in spec.md)

**Tests**: Tests are NOT included (not explicitly requested in spec).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No setup tasks required — the project already exists with a centralized CSS custom properties theming system in `frontend/src/index.css`.

*(No tasks — the existing `:root` and `html.dark-mode-active` selectors provide the theme infrastructure.)*

---

## Phase 2: Foundational

**Purpose**: No foundational tasks required — the existing CSS custom properties (`--color-bg`, `--color-bg-secondary`) already serve as the centralized theme mechanism. No new infrastructure is needed.

*(No tasks — all prerequisites are already in place.)*

---

## Phase 3: User Story 1 - Red Background Visible Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply a red-themed background color to the root-level page background in light mode so it is visible across all screens and views.

**Independent Test**: Open the application in light mode and navigate through all primary views to confirm a red-tinted background is visible and consistent on every screen.

### Implementation for User Story 1

- [ ] T001 [US1] Update `--color-bg` CSS custom property from `#ffffff` to `#fff5f5` (light red, 13.7:1 contrast with `#24292f` text) in `:root` selector in `frontend/src/index.css`
- [ ] T002 [US1] Update `--color-bg-secondary` CSS custom property from `#f6f8fa` to `#ffebee` (Material Red 50, 12.8:1 contrast with `#24292f` text) in `:root` selector in `frontend/src/index.css`

**Checkpoint**: Light mode now displays red-themed backgrounds. All screens show the red background consistently across all responsive breakpoints. Component-level backgrounds (cards, modals, inputs) retain their own colors since they reference `--color-bg` which is a subtle red tint.

---

## Phase 4: User Story 2 - Accessible Text and UI on Red Background (Priority: P2)

**Goal**: Ensure all foreground text and interactive elements maintain WCAG AA-compliant contrast ratios (minimum 4.5:1) against the red background in both light and dark modes.

**Independent Test**: Inspect all text elements on the red background and verify contrast ratios meet WCAG AA standards using browser dev tools or an accessibility audit tool.

### Implementation for User Story 2

- [ ] T003 [US2] Verify contrast ratios for light mode: confirm `--color-text` (`#24292f`) against `--color-bg` (`#fff5f5`) achieves ≥4.5:1 ratio (expected 13.7:1), and against `--color-bg-secondary` (`#ffebee`) achieves ≥4.5:1 ratio (expected 12.8:1) — no code change needed, document verification in commit message
- [ ] T004 [US2] Verify contrast ratios for dark mode: confirm `--color-text` (`#e6edf3`) against `--color-bg` (`#2d0a0a`) achieves ≥4.5:1 ratio (expected 15.3:1), and against `--color-bg-secondary` (`#1a0505`) achieves ≥4.5:1 ratio (expected 16.6:1) — no code change needed, document verification in commit message

**Checkpoint**: All text and UI elements meet WCAG AA contrast requirements. No text readability regressions introduced.

---

## Phase 5: User Story 3 - Dark Mode Compatibility (Priority: P3)

**Goal**: Apply dark red-themed background colors in dark mode so the red theme is maintained across both light and dark modes.

**Independent Test**: Toggle dark mode on and verify the background changes to a dark red variant while maintaining text readability.

### Implementation for User Story 3

- [ ] T005 [US3] Update `--color-bg` CSS custom property from `#0d1117` to `#2d0a0a` (dark red, 15.3:1 contrast with `#e6edf3` text) in `html.dark-mode-active` selector in `frontend/src/index.css`
- [ ] T006 [US3] Update `--color-bg-secondary` CSS custom property from `#161b22` to `#1a0505` (dark red page background, 16.6:1 contrast with `#e6edf3` text) in `html.dark-mode-active` selector in `frontend/src/index.css`

**Checkpoint**: Dark mode now displays dark red-themed backgrounds. Toggling between light and dark mode shows appropriate red shades for each context.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T007 Visually verify red background appears on all screens in light mode across mobile, tablet, and desktop breakpoints
- [ ] T008 Visually verify dark red background appears on all screens in dark mode across mobile, tablet, and desktop breakpoints
- [ ] T009 Confirm component-level backgrounds (cards, modals, input fields) are not overridden by the global red background change

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup → (no tasks)
    ↓
Phase 2: Foundational → (no tasks)
    ↓
Phase 3: US1 - Light Mode Red Background (T001-T002)
    ↓
Phase 4: US2 - Accessibility Verification (T003-T004)
    ↓
Phase 5: US3 - Dark Mode Red Background (T005-T006)
    ↓
Phase 6: Polish (T007-T009)
```

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — can start immediately. Only modifies `:root` CSS variables.
- **User Story 2 (P2)**: Depends on US1 and US3 color values being finalized. Verification-only tasks.
- **User Story 3 (P3)**: No dependency on US1 — modifies `html.dark-mode-active` CSS variables (different selector). Can run in parallel with US1 if desired.

### Within Each User Story

- T001 and T002 modify the same file but different lines — can be done together in a single edit
- T005 and T006 modify the same file but different lines — can be done together in a single edit

### Parallel Opportunities

- T001 and T002 can be applied in a single file edit (same `:root` selector block)
- T005 and T006 can be applied in a single file edit (same `html.dark-mode-active` selector block)
- US1 (light mode) and US3 (dark mode) can technically run in parallel since they modify different selectors in the same file

---

## Parallel Example: User Story 1 + User Story 3

```bash
# Since US1 and US3 modify different CSS selector blocks in the same file,
# they can be combined into a single edit session:
# Edit :root selector (US1): --color-bg and --color-bg-secondary
# Edit html.dark-mode-active selector (US3): --color-bg and --color-bg-secondary
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 3: User Story 1 (T001-T002) — light mode red background
2. **STOP and VALIDATE**: Open app in light mode, confirm red background on all screens
3. Deploy/demo if ready — light mode red background is the core deliverable

### Incremental Delivery

1. Add User Story 1 → Light mode red background visible → Deploy/Demo (MVP!)
2. Add User Story 2 → Accessibility verified → Confidence in color choices
3. Add User Story 3 → Dark mode red background → Deploy/Demo (Complete feature)
4. Polish → Cross-device and cross-component verification

### All-at-Once Strategy (Recommended for XS feature)

Since the entire feature is 4 CSS variable value changes in a single file:

1. Apply all 4 changes to `frontend/src/index.css` (T001, T002, T005, T006)
2. Verify accessibility (T003, T004)
3. Validate across breakpoints and modes (T007, T008, T009)

---

## Summary

| Phase | Tasks | File Modified |
|-------|-------|---------------|
| US1 - Light Mode | T001-T002 | frontend/src/index.css (`:root`) |
| US2 - Accessibility | T003-T004 | (verification only) |
| US3 - Dark Mode | T005-T006 | frontend/src/index.css (`html.dark-mode-active`) |
| Polish | T007-T009 | (verification only) |

**Total Tasks**: 9
**Code Change Tasks**: 4 (T001, T002, T005, T006)
**Verification Tasks**: 5 (T003, T004, T007, T008, T009)
**Files Modified**: 1 (`frontend/src/index.css`)
**CSS Variables Changed**: 4 (`--color-bg` and `--color-bg-secondary` in both `:root` and `html.dark-mode-active`)

---

## Notes

- This is an XS feature (estimated 0.5h) requiring only 4 CSS variable value changes
- No new files are created — only existing values are updated
- The centralized CSS custom properties architecture means the change propagates to all components automatically
- Component-level backgrounds that explicitly set their own colors will NOT be affected
- All proposed color values have been pre-verified for WCAG AA contrast compliance
