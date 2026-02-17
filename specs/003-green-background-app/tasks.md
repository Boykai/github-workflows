# Tasks: Green Background for Tech Connect App

**Input**: Design documents from `/specs/003-green-background-app/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). No new tests required per plan.md — visual verification is sufficient.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current CSS variable state before making changes

- [ ] T001 Verify current --color-bg and --color-bg-secondary values in :root and html.dark-mode-active selectors in frontend/src/index.css

---

## Phase 2: User Story 1 - Consistent Green Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply green background colors to all app screens via CSS custom properties in light mode

**Independent Test**: Navigate through all screens (landing, dashboard, settings, modals) and verify each displays a green background in light mode

### Implementation for User Story 1

- [ ] T002 [US1] Update --color-bg from #ffffff to #E8F5E9 in :root selector in frontend/src/index.css
- [ ] T003 [US1] Update --color-bg-secondary from #f6f8fa to #C8E6C9 in :root selector in frontend/src/index.css

**Checkpoint**: Light mode displays mint green (#E8F5E9) primary background and light green (#C8E6C9) secondary background across all screens. Verify no flicker during navigation and modal overlays harmonize with green theme.

---

## Phase 3: User Story 2 - Text and UI Element Readability on Green Background (Priority: P1)

**Goal**: Ensure all text, buttons, icons, and input fields remain clearly readable against the green background

**Independent Test**: Review each screen for text legibility (WCAG 2.1 AA: 4.5:1 normal text, 3:1 large text), button visibility, and input field clarity against the green background

### Implementation for User Story 2

- [ ] T004 [US2] Verify WCAG AA contrast of --color-text (#24292f) against new --color-bg (#E8F5E9) achieves 13.03:1 ratio in frontend/src/index.css
- [ ] T005 [US2] Verify WCAG AA contrast of --color-text-secondary (#57606a) against new --color-bg (#E8F5E9) achieves 5.77:1 ratio and against --color-bg-secondary (#C8E6C9) achieves 4.83:1 ratio in frontend/src/index.css

**Checkpoint**: All text and interactive elements are clearly readable against green backgrounds. No component-level CSS changes needed — existing text colors maintain sufficient contrast.

---

## Phase 4: User Story 3 - Dark Mode Adaptation (Priority: P2)

**Goal**: Adapt green background to darker green shades in dark mode for reduced eye strain

**Independent Test**: Toggle between light and dark mode and verify the background adapts to appropriate green shades while maintaining WCAG contrast

### Implementation for User Story 3

- [ ] T006 [US3] Update --color-bg from #0d1117 to #0D2818 in html.dark-mode-active selector in frontend/src/index.css
- [ ] T007 [US3] Update --color-bg-secondary from #161b22 to #1A3A2A in html.dark-mode-active selector in frontend/src/index.css

**Checkpoint**: Dark mode displays dark green (#0D2818) primary background and (#1A3A2A) secondary background. Dark mode text (#e6edf3) achieves 13.32:1 and 10.56:1 contrast ratios respectively. Transition between modes is smooth without visual glitches.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T008 Verify all 4 CSS variable changes are correct by running grep -n "color-bg" frontend/src/index.css
- [ ] T009 Verify no layout breakage on desktop and mobile viewports by visual inspection
- [ ] T010 Run quickstart.md validation checklist against running application

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001)
    ↓
Phase 2: US1 - Green Background (T002-T003)
    ↓
Phase 3: US2 - Readability Verification (T004-T005)
    ↓
Phase 4: US3 - Dark Mode (T006-T007)
    ↓
Phase 5: Polish (T008-T010)
```

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — Core deliverable
- **User Story 2 (P1)**: Depends on US1 completion — Verifies readability of green background
- **User Story 3 (P2)**: Can start after Setup (Phase 1) — Independent dark mode change, but sequenced after US1 for logical flow

### Within Each User Story

- US1: Change light mode CSS variables → Verify green renders on all screens
- US2: Verify contrast ratios meet WCAG AA → Confirm no component changes needed
- US3: Change dark mode CSS variables → Verify dark green renders correctly

### Parallel Opportunities

- T002 and T003 modify different CSS properties in the same selector — execute sequentially (same file region)
- T006 and T007 modify different CSS properties in the same selector — execute sequentially (same file region)
- T004 and T005 are verification tasks — can run in parallel conceptually
- US1 (light mode) and US3 (dark mode) are independent changes but share the same file

---

## Parallel Example: User Story 1

```bash
# User Story 1 tasks are sequential (same file, same selector region):
Task: "Update --color-bg from #ffffff to #E8F5E9 in :root selector in frontend/src/index.css"
Task: "Update --color-bg-secondary from #f6f8fa to #C8E6C9 in :root selector in frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify current state
2. Complete Phase 2: Update light mode --color-bg and --color-bg-secondary
3. **STOP and VALIDATE**: Verify green background on all screens in light mode
4. Deploy/demo if ready — core green background is visible

### Incremental Delivery

1. Setup verification → Baseline confirmed
2. Add User Story 1 (light mode green) → Visual inspection → MVP complete
3. Add User Story 2 (readability verification) → Contrast confirmed → Accessibility validated
4. Add User Story 3 (dark mode green) → Toggle test → Full feature complete
5. Polish → Final validation → Feature ready

### Single Developer Strategy

This feature modifies 1 file with 4 value changes. All tasks are best executed sequentially by a single developer in approximately 5 minutes.

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001 | frontend/src/index.css (read only) |
| US1 - Green Background | T002-T003 | frontend/src/index.css |
| US2 - Readability | T004-T005 | frontend/src/index.css (verification only) |
| US3 - Dark Mode | T006-T007 | frontend/src/index.css |
| Polish | T008-T010 | frontend/src/index.css (verification only) |

**Total Tasks**: 10
**Tasks per User Story**: US1: 2, US2: 2, US3: 2
**Parallel Opportunities**: Limited (single file modification)
**Independent Test Criteria**: Each user story has clear visual verification criteria
**Suggested MVP Scope**: User Story 1 (T001-T003) — light mode green background
**Format Validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- All changes are in a single file: `frontend/src/index.css`
- No new dependencies, no architectural changes — CSS variable value replacements only
- WCAG 2.1 AA contrast ratios pre-verified in research.md for all color combinations
- Existing component styles auto-update via CSS variable resolution — no per-component changes needed
- Rollback is instant: revert 4 hex values or `git revert` the commit
