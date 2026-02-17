# Tasks: Orange Background Throughout the App

**Input**: Design documents from `/specs/003-orange-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Visual and accessibility verification via browser DevTools and contrast checker tools.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Verify Baseline)

**Purpose**: Confirm current CSS state matches expected baseline before making changes

- [ ] T001 Verify current light mode CSS variables in frontend/src/index.css match expected values (--color-bg: #ffffff, --color-bg-secondary: #f6f8fa, etc.)
- [ ] T002 [P] Verify current dark mode CSS variables in frontend/src/index.css match expected values (--color-bg: #0d1117, --color-bg-secondary: #161b22, etc.)

---

## Phase 2: User Story 1 - Consistent Orange Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply orange background (#FF8C00) to all app screens via CSS custom property updates in `:root` selector

**Independent Test**: Open each screen (login, dashboard, profile, settings) and visually confirm the orange background is present and all content is readable

### Implementation for User Story 1

- [ ] T003 [US1] Update --color-bg from #ffffff to #FF8C00 in :root selector of frontend/src/index.css
- [ ] T004 [US1] Update --color-bg-secondary from #f6f8fa to #E07B00 in :root selector of frontend/src/index.css
- [ ] T005 [US1] Update --color-border from #d0d7de to #C06500 in :root selector of frontend/src/index.css
- [ ] T006 [US1] Update --shadow from rgba(0, 0, 0, 0.1) to rgba(0, 0, 0, 0.2) in :root selector of frontend/src/index.css

**Checkpoint**: All app screens now display orange background in light mode. Navigate between screens to confirm consistency.

---

## Phase 3: User Story 2 - Accessible Text and UI Contrast (Priority: P2)

**Goal**: Ensure all text and UI elements meet WCAG 2.1 AA contrast requirements against the orange background

**Independent Test**: Measure contrast ratios using accessibility audit tools — primary text ≥ 4.5:1, large text/UI ≥ 3:1

### Implementation for User Story 2

- [ ] T007 [US2] Update --color-text from #24292f to #000000 in :root selector of frontend/src/index.css (achieves 4.54:1 contrast on #FF8C00)
- [ ] T008 [US2] Update --color-text-secondary from #57606a to #4A2800 in :root selector of frontend/src/index.css (achieves ~4.8:1 contrast on #FF8C00)
- [ ] T009 [US2] Verify login button in frontend/src/App.css remains accessible — .login-button uses var(--color-text) as background, which resolves to #000000 (black button with white text on orange)

**Checkpoint**: All text is readable on orange background. Login button is clearly visible. Run contrast checker to confirm WCAG AA compliance.

---

## Phase 4: User Story 3 - Dark Mode Orange Variant (Priority: P3)

**Goal**: Apply darker orange background (#CC7000) for dark mode with accessible text contrast

**Independent Test**: Toggle dark mode and verify background shifts to darker orange with all text and UI elements readable

### Implementation for User Story 3

- [ ] T010 [US3] Update --color-bg from #0d1117 to #CC7000 in html.dark-mode-active selector of frontend/src/index.css
- [ ] T011 [US3] Update --color-bg-secondary from #161b22 to #A35800 in html.dark-mode-active selector of frontend/src/index.css
- [ ] T012 [US3] Update --color-border from #30363d to #8B4800 in html.dark-mode-active selector of frontend/src/index.css
- [ ] T013 [US3] Update --color-text from #e6edf3 to #FFFFFF in html.dark-mode-active selector of frontend/src/index.css
- [ ] T014 [US3] Update --color-text-secondary from #8b949e to #D4A574 in html.dark-mode-active selector of frontend/src/index.css
- [ ] T015 [US3] Update --shadow from rgba(0, 0, 0, 0.4) to rgba(0, 0, 0, 0.3) in html.dark-mode-active selector of frontend/src/index.css

**Checkpoint**: Dark mode displays darker orange background. Toggle between light and dark mode to confirm smooth transition and text readability in both modes.

---

## Phase 5: User Story 4 - Responsive Orange Background (Priority: P4)

**Goal**: Verify orange background renders correctly across all screen sizes and orientations

**Independent Test**: Resize browser window from 320px to 2560px wide, test portrait/landscape — orange background fills viewport without gaps or layout shifts

### Implementation for User Story 4

- [ ] T016 [US4] Verify orange background fills full viewport at mobile (320px), tablet (768px), and desktop (1440px) widths — no CSS changes expected since CSS variables apply globally via body and container elements in frontend/src/index.css
- [ ] T017 [US4] Verify no layout shifts or visual gaps when rotating between portrait and landscape orientations

**Checkpoint**: Orange background renders correctly at all viewport sizes. No responsive-specific CSS changes needed (CSS variables cascade to all elements automatically).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T018 Run accessibility contrast audit on light mode: black (#000000) on #FF8C00 = 4.54:1 (must pass WCAG AA ≥ 4.5:1)
- [ ] T019 [P] Run accessibility contrast audit on dark mode: white (#FFFFFF) on #CC7000 (must pass WCAG AA for large text ≥ 3:1)
- [ ] T020 [P] Verify all interactive elements (buttons, cards, forms, sidebar) are visually distinguishable from the orange background
- [ ] T021 Run quickstart.md validation checklist from specs/003-orange-background/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001-T002, parallel)
    ↓
Phase 2: US1 - Orange Background (T003-T006, sequential within index.css)
    ↓
Phase 3: US2 - Accessibility (T007-T009, sequential)
    ↓
Phase 4: US3 - Dark Mode (T010-T015, sequential within index.css)
    ↓
Phase 5: US4 - Responsive (T016-T017, parallel verification)
    ↓
Phase 6: Polish (T018-T021, parallel)
```

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (background must be orange before measuring contrast)
- **User Story 3 (P3)**: Can start after Setup — Independent from US1/US2 (different CSS selector)
- **User Story 4 (P4)**: Depends on US1 and US3 (both light and dark themes must be applied before responsive verification)

### Within Each User Story

- All changes are in the same file (frontend/src/index.css), so tasks within a story are sequential
- US1 and US3 modify different CSS selectors (:root vs html.dark-mode-active), so they CAN run in parallel
- US2 depends on US1 (text color contrast is measured against the orange background)
- US4 is verification only — no code changes expected

### Parallel Opportunities

- T001 and T002 can run in parallel (verifying different selectors)
- US1 (Phase 2) and US3 (Phase 4) can run in parallel (different CSS selectors in same file)
- T018, T019, T020 can run in parallel (independent verification tasks)

---

## Parallel Example: US1 + US3

```bash
# These modify different CSS selectors in the same file, so can be done in one edit session:
Task T003-T006: Update :root selector variables (light mode orange)
Task T010-T015: Update html.dark-mode-active selector variables (dark mode orange)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline CSS
2. Complete Phase 2: Apply orange background (US1)
3. **STOP and VALIDATE**: Open app, confirm orange background on all screens
4. If orange background works → feature delivers immediate visual value

### Incremental Delivery

1. Complete Setup → Baseline verified
2. Add US1 (Orange Background) → Visual impact delivered (MVP!)
3. Add US2 (Accessibility) → Text contrast verified and WCAG compliant
4. Add US3 (Dark Mode) → Dark orange variant available
5. Add US4 (Responsive) → Cross-device verification complete
6. Polish → Final accessibility audit and validation

### Single Developer Strategy (Recommended)

Since all changes are in 1-2 CSS files, the most efficient approach is:

1. Edit frontend/src/index.css once — update all :root and html.dark-mode-active variables together (T003-T015)
2. Verify login button compatibility in frontend/src/App.css (T009)
3. Run visual and accessibility checks (T016-T021)
4. Total estimated time: 10-15 minutes

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001-T002 | (verification only) |
| US1 - Orange Background | T003-T006 | frontend/src/index.css |
| US2 - Accessibility | T007-T009 | frontend/src/index.css, frontend/src/App.css (verify) |
| US3 - Dark Mode | T010-T015 | frontend/src/index.css |
| US4 - Responsive | T016-T017 | (verification only) |
| Polish | T018-T021 | (verification only) |

**Total Tasks**: 21
**Tasks per User Story**: US1: 4, US2: 3, US3: 6, US4: 2
**Parallel Opportunities**: Setup (2 tasks), US1+US3 (different selectors), Polish (3 tasks)
**Independent Test Criteria**: Each user story has specific, measurable verification criteria
**Suggested MVP Scope**: User Story 1 (Phase 2) — apply orange background to all screens
**Format Validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- All CSS changes use the existing CSS custom properties theming system
- No new files, dependencies, or architectural changes required
- Login button uses var(--color-text) as background — changing to #000000 makes it a black button on orange, which is accessible
- The feature is instantly reversible via git revert of frontend/src/index.css
- Color values chosen per research.md WCAG analysis: #FF8C00 (light), #CC7000 (dark)
