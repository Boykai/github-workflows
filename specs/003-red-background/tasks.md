# Tasks: Apply Red Background Color to Entire App Interface

**Input**: Design documents from `/specs/003-red-background/`
**Prerequisites**: spec.md ✅, plan.md (not generated — tasks derived from spec.md and codebase analysis)

**Tests**: Tests are NOT included (not explicitly requested in feature specification).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — this is a CSS-only change to an existing frontend app. Setup verifies the existing theme system is understood and no structural changes are required.

- [ ] T001 Verify existing CSS custom properties and theme toggle work correctly in frontend/src/index.css and frontend/src/hooks/useAppTheme.ts

---

## Phase 2: User Story 1 - Global Red Background Display (Priority: P1) 🎯 MVP

**Goal**: Set the app background to solid red (#FF0000) in light mode and dark red (#8B0000) in dark mode across all screens and routes by updating CSS custom properties.

**Independent Test**: Open the app in a browser. Confirm the background is red on the login screen, dashboard, sidebar, and chat area. Toggle dark mode and confirm background switches to dark red. Navigate between views and confirm no flickering.

### Implementation for User Story 1

- [ ] T002 [US1] Update `:root` CSS custom properties in frontend/src/index.css to set `--color-bg: #FF0000` and `--color-bg-secondary: #CC0000` for light-mode red background
- [ ] T003 [US1] Update `html.dark-mode-active` CSS custom properties in frontend/src/index.css to set `--color-bg: #8B0000` and `--color-bg-secondary: #660000` for dark-mode red background
- [ ] T004 [US1] Verify `body` element in frontend/src/index.css uses `background: var(--color-bg-secondary)` to inherit the red background globally (no change expected — confirm only)

**Checkpoint**: Red background visible on all screens in both light and dark mode. MVP delivered.

---

## Phase 3: User Story 2 - Accessibility-Compliant Foreground Elements (Priority: P2)

**Goal**: Update text and interactive element colors to maintain WCAG AA contrast ratios (4.5:1 normal text, 3:1 large text) against the red background.

**Independent Test**: Use a contrast checker tool to verify all body text, headings, buttons, and interactive elements meet WCAG AA contrast ratios against #FF0000 (light) and #8B0000 (dark) backgrounds.

### Implementation for User Story 2

- [ ] T005 [US2] Update `:root` CSS custom properties in frontend/src/index.css to set `--color-text: #FFFFFF` and `--color-text-secondary: #FFD6D6` for readable light-mode text on red background
- [ ] T006 [US2] Update `html.dark-mode-active` CSS custom properties in frontend/src/index.css to set `--color-text: #FFFFFF` and `--color-text-secondary: #FFCCCC` for readable dark-mode text on dark red background
- [ ] T007 [US2] Update `:root` CSS custom properties in frontend/src/index.css to set `--color-border: #FF6666` and `--shadow` to use `rgba(0, 0, 0, 0.3)` for visible borders on red background
- [ ] T008 [US2] Update `html.dark-mode-active` CSS custom properties in frontend/src/index.css to set `--color-border: #AA3333` and `--shadow` to use `rgba(0, 0, 0, 0.5)` for visible borders on dark red background
- [ ] T009 [US2] Update `.login-button` background in frontend/src/App.css from `var(--color-text)` to a high-contrast value (e.g., `#333333` or `var(--color-primary)`) since --color-text is now white
- [ ] T010 [US2] Update `.login-button:hover` background in frontend/src/App.css to match the updated login button color scheme

**Checkpoint**: All text and interactive elements are readable and meet WCAG AA contrast standards against the red background.

---

## Phase 4: User Story 3 - Responsive Red Background Across Devices (Priority: P3)

**Goal**: Confirm red background displays correctly across all viewport sizes (mobile, tablet, desktop) with no gaps or overflow issues.

**Independent Test**: Open the app at mobile (375px), tablet (768px), and desktop (1440px) viewport widths. Rotate between portrait and landscape. Confirm red background fills entire viewport without gaps.

### Implementation for User Story 3

- [ ] T011 [US3] Verify `html` and `body` elements in frontend/src/index.css have no fixed height/width constraints that would prevent full viewport coverage (confirm `min-height: 100vh` or equivalent is set, add if missing)
- [ ] T012 [US3] Verify `.app-container` in frontend/src/App.css uses `height: 100vh` to ensure red background fills the viewport on all device sizes (no change expected — confirm only)

**Checkpoint**: Red background fills entire viewport on mobile, tablet, and desktop without gaps.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T013 Verify red background persists during navigation between login, dashboard, sidebar, and chat views without flickering in frontend/src/App.tsx
- [ ] T014 Verify modals and popup overlays preserve the red background behind them in frontend/src/components/chat/ChatInterface.css
- [ ] T015 Run visual audit of all screens to confirm component-level backgrounds (cards, headers, sidebars) are preserved per FR-007

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001) — No dependencies
    ↓
Phase 2: US1 - Red Background (T002-T004) — Depends on Phase 1
    ↓
Phase 3: US2 - Accessibility (T005-T010) — Depends on Phase 2
    ↓
Phase 4: US3 - Responsive (T011-T012) — Depends on Phase 2
    ↓
Phase 5: Polish (T013-T015) — Depends on Phases 2, 3, 4
```

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (red background must be applied before adjusting contrast)
- **User Story 3 (P3)**: Depends on US1 completion (red background must exist to validate responsiveness). Can run in parallel with US2.

### Parallel Opportunities

- T005 and T006 can run in parallel (different CSS rule blocks in same file, non-overlapping)
- T007 and T008 can run in parallel (different CSS rule blocks in same file, non-overlapping)
- T009 and T010 can run in parallel with T005-T008 (different file: App.css vs index.css)
- T011 and T012 can run in parallel (different files: index.css vs App.css)
- T013, T014, and T015 can run in parallel (different verification scopes)
- US2 (Phase 3) and US3 (Phase 4) can run in parallel after US1 completes

---

## Parallel Example: User Story 2

```bash
# Launch CSS variable updates in parallel (different rule blocks):
Task: "Update :root text colors in frontend/src/index.css"
Task: "Update html.dark-mode-active text colors in frontend/src/index.css"

# Launch button fixes in parallel with CSS variable updates (different file):
Task: "Update .login-button background in frontend/src/App.css"
Task: "Update .login-button:hover background in frontend/src/App.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify theme system)
2. Complete Phase 2: User Story 1 (apply red background CSS variables)
3. **STOP and VALIDATE**: Open app, confirm red background on all screens, toggle dark mode
4. Deploy/demo if ready — core red background is live

### Incremental Delivery

1. Phase 1: Setup → Verify existing theme works
2. Phase 2: US1 → Red background applied → Test independently → **MVP!**
3. Phase 3: US2 → Accessibility fixes → Test contrast ratios
4. Phase 4: US3 → Responsive validation → Test on multiple viewports
5. Phase 5: Polish → Cross-cutting verification
6. Each story adds value without breaking previous stories

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001 | (verification only) |
| US1 - Red Background | T002-T004 | frontend/src/index.css |
| US2 - Accessibility | T005-T010 | frontend/src/index.css, frontend/src/App.css |
| US3 - Responsive | T011-T012 | frontend/src/index.css, frontend/src/App.css |
| Polish | T013-T015 | (verification only) |

**Total Tasks**: 15
**Tasks per User Story**: US1: 3, US2: 6, US3: 2, Polish: 3
**Parallel Opportunities**: 6 identified (within US2, within US3, US2+US3 in parallel)
**Independent Test Criteria**: Each user story has its own test criteria documented above
**Suggested MVP Scope**: User Story 1 only (Phase 2 — 3 tasks)

## Notes

- All changes are CSS-only — no TypeScript/React logic changes required
- [P] tasks = different files or non-overlapping rule blocks, no dependencies
- [Story] label maps task to specific user story for traceability
- The login button (`.login-button`) uses `var(--color-text)` as its background — changing `--color-text` to white requires updating this to maintain a dark button appearance
- Dark mode variant uses #8B0000 (dark red) per spec assumption #1
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
