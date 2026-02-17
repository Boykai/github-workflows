# Tasks: Orange Background Throughout the App

**Input**: Design documents from `/specs/003-orange-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Visual verification and accessibility audit tools are sufficient per plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Verify Baseline)

**Purpose**: Confirm current CSS variable structure before making changes

- [ ] T001 Verify current `:root` CSS custom property values in frontend/src/index.css match expected baseline (#ffffff for --color-bg, #f6f8fa for --color-bg-secondary)
- [ ] T002 Verify current `html.dark-mode-active` CSS custom property values in frontend/src/index.css match expected baseline (#0d1117 for --color-bg)

---

## Phase 2: User Story 1 - Consistent Orange Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply orange background (#FF8C00) to all app screens via light mode CSS custom properties in `frontend/src/index.css`

**Independent Test**: Open each screen (login, dashboard, profile, settings) and visually confirm the orange background is present and all content is readable

### Implementation for User Story 1

- [ ] T003 [US1] Update `--color-bg` from `#ffffff` to `#FF8C00` in `:root` selector of frontend/src/index.css
- [ ] T004 [US1] Update `--color-bg-secondary` from `#f6f8fa` to `#E07B00` in `:root` selector of frontend/src/index.css
- [ ] T005 [US1] Update `--color-border` from `#d0d7de` to `#C06500` in `:root` selector of frontend/src/index.css
- [ ] T006 [US1] Update `--shadow` from `rgba(0, 0, 0, 0.1)` to `rgba(0, 0, 0, 0.2)` in `:root` selector of frontend/src/index.css

**Checkpoint**: All screens display orange background. Cards, header, sidebar, and chat sections are orange. Borders are orange-tinted.

---

## Phase 3: User Story 2 - Accessible Text and UI Contrast on Orange Background (Priority: P2)

**Goal**: Ensure all text meets WCAG 2.1 AA contrast requirements (4.5:1 for normal text, 3:1 for large text/UI) against the orange background

**Independent Test**: Measure contrast ratios of text and interactive elements against #FF8C00 using accessibility audit tools; confirm all ratios meet WCAG 2.1 AA thresholds

### Implementation for User Story 2

- [ ] T007 [US2] Update `--color-text` from `#24292f` to `#000000` in `:root` selector of frontend/src/index.css for 4.54:1 contrast on #FF8C00
- [ ] T008 [US2] Update `--color-text-secondary` from `#57606a` to `#4A2800` in `:root` selector of frontend/src/index.css for ~4.8:1 contrast on #FF8C00
- [ ] T009 [US2] Verify login button in frontend/src/App.css remains accessible (uses `var(--color-text)` as background, resolves to black #000000 with white text)

**Checkpoint**: All text is readable on orange background. Primary text (#000000) achieves 4.54:1 contrast. Secondary text (#4A2800) achieves ~4.8:1 contrast. Login button is black with white text.

---

## Phase 4: User Story 3 - Dark Mode Orange Variant (Priority: P3)

**Goal**: Apply darker orange (#CC7000) background for dark mode with WCAG-compliant text colors in `frontend/src/index.css`

**Independent Test**: Toggle dark mode and verify background shifts to darker orange; confirm text and interactive elements remain readable

### Implementation for User Story 3

- [ ] T010 [US3] Update `--color-bg` from `#0d1117` to `#CC7000` in `html.dark-mode-active` selector of frontend/src/index.css
- [ ] T011 [US3] Update `--color-bg-secondary` from `#161b22` to `#A35800` in `html.dark-mode-active` selector of frontend/src/index.css
- [ ] T012 [US3] Update `--color-border` from `#30363d` to `#8B4800` in `html.dark-mode-active` selector of frontend/src/index.css
- [ ] T013 [US3] Update `--color-text` from `#e6edf3` to `#FFFFFF` in `html.dark-mode-active` selector of frontend/src/index.css
- [ ] T014 [US3] Update `--color-text-secondary` from `#8b949e` to `#D4A574` in `html.dark-mode-active` selector of frontend/src/index.css
- [ ] T015 [US3] Update `--shadow` from `rgba(0, 0, 0, 0.4)` to `rgba(0, 0, 0, 0.3)` in `html.dark-mode-active` selector of frontend/src/index.css

**Checkpoint**: Dark mode displays darker orange (#CC7000). White text (#FFFFFF) on dark orange is readable. Theme toggle transitions smoothly between light and dark orange variants.

---

## Phase 5: User Story 4 - Responsive Orange Background (Priority: P4)

**Goal**: Verify orange background renders correctly across all screen sizes and orientations without layout shifts

**Independent Test**: Resize browser window and test on different device viewports; confirm orange background covers full viewport without gaps or layout shifts

### Implementation for User Story 4

- [ ] T016 [US4] Verify orange background fills full viewport without gaps at mobile (320px), tablet (768px), and desktop (1920px) widths in frontend/src/index.css — no additional CSS changes needed as CSS custom properties apply globally via existing body and container selectors

**Checkpoint**: Orange background renders correctly across all viewport sizes. No gaps, scrolling artifacts, or layout shifts.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [ ] T017 Run visual verification of all screens (login, dashboard, settings) in both light and dark mode to confirm orange background consistency
- [ ] T018 Run accessibility contrast check for light mode: #000000 on #FF8C00 ≥ 4.5:1 and #4A2800 on #FF8C00 ≥ 4.5:1
- [ ] T019 Run accessibility contrast check for dark mode: #FFFFFF on #CC7000 ≥ 3:1 (large text) and #D4A574 on #CC7000 for secondary text
- [ ] T020 Run quickstart.md validation checklist from specs/003-orange-background/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001-T002, parallel) — Verify baseline
    ↓
Phase 2: US1 - Orange Background (T003-T006) — Core feature
    ↓
Phase 3: US2 - Accessibility (T007-T009) — Text contrast on orange
    ↓
Phase 4: US3 - Dark Mode (T010-T015) — Dark orange variant
    ↓
Phase 5: US4 - Responsive (T016) — Viewport verification
    ↓
Phase 6: Polish (T017-T020, parallel) — Final validation
```

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — applies orange background via CSS variables
- **User Story 2 (P2)**: Depends on US1 — needs orange background in place to verify text contrast
- **User Story 3 (P3)**: Independent of US1/US2 — modifies dark mode selector separately, but logically follows light mode changes
- **User Story 4 (P4)**: Depends on US1+US3 — verifies responsive rendering of both light and dark orange

### Within Each User Story

- All changes are in a single file (`frontend/src/index.css`), so tasks within a story are sequential
- US1 and US3 modify different CSS selectors (`:root` vs `html.dark-mode-active`) and could technically run in parallel

### Parallel Opportunities

- T001 and T002 (baseline verification) can run in parallel
- T017, T018, T019, and T020 (polish/verification) can run in parallel
- US1 (`:root` changes) and US3 (`html.dark-mode-active` changes) modify different selectors in the same file and could be parallelized if implemented as separate edits

---

## Parallel Example: User Story 1 + User Story 3

```bash
# Since US1 modifies :root and US3 modifies html.dark-mode-active,
# these can be implemented in parallel as they touch different selectors:

# US1 - Light mode orange:
Task: "Update --color-bg from #ffffff to #FF8C00 in :root of frontend/src/index.css"
Task: "Update --color-bg-secondary from #f6f8fa to #E07B00 in :root of frontend/src/index.css"

# US3 - Dark mode orange (parallel):
Task: "Update --color-bg from #0d1117 to #CC7000 in html.dark-mode-active of frontend/src/index.css"
Task: "Update --color-bg-secondary from #161b22 to #A35800 in html.dark-mode-active of frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline
2. Complete Phase 2: Apply orange background (US1)
3. **STOP and VALIDATE**: Open app — background should be orange on all screens
4. Deploy/demo if ready — immediate visual impact

### Incremental Delivery

1. US1 (orange background) → Visible change, immediate value
2. US2 (accessibility) → Text contrast fixed, WCAG compliance
3. US3 (dark mode) → Dark orange variant, complete theme
4. US4 (responsive) → Verification across devices
5. Each story adds value without breaking previous stories

### Suggested MVP Scope

User Story 1 (T003-T006) + User Story 2 (T007-T009) together form the practical MVP, as the orange background without accessible text colors would be unusable.

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001-T002 | frontend/src/index.css (read-only verification) |
| US1 - Orange BG | T003-T006 | frontend/src/index.css (`:root` selector) |
| US2 - Accessibility | T007-T009 | frontend/src/index.css (`:root` selector), frontend/src/App.css (verification only) |
| US3 - Dark Mode | T010-T015 | frontend/src/index.css (`html.dark-mode-active` selector) |
| US4 - Responsive | T016 | frontend/src/index.css (verification only) |
| Polish | T017-T020 | Cross-cutting verification |

**Total Tasks**: 20
**Tasks per User Story**: US1: 4, US2: 3, US3: 6, US4: 1
**Parallel Opportunities**: Setup (2 tasks), US1+US3 (different selectors), Polish (4 tasks)
**Independent Test Criteria**: Each user story has its own verification method documented above
**Suggested MVP**: US1 + US2 (Tasks T003-T009) — Orange background with accessible text

## Notes

- All implementation changes are in a single file: `frontend/src/index.css`
- No new files, dependencies, or architectural changes required
- Login button compatibility confirmed — `var(--color-text)` resolves to black (#000000), providing visible button
- Existing `useAppTheme` hook handles dark mode toggle without modification
- Rollback is instant: `git checkout -- frontend/src/index.css`
