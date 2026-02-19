# Tasks: Blue Background Color

**Input**: Design documents from `/specs/007-blue-background/`
**Prerequisites**: spec.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). FR-008 suggests visual regression tests as SHOULD, not MUST.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Design Tokens)

**Purpose**: Define the blue background color as reusable CSS custom properties for light and dark themes

- [ ] T001 Add `--color-bg-app: #1E3A5F` CSS variable to `:root` in frontend/src/index.css
- [ ] T002 Add `--color-bg-app: #0F2440` CSS variable to `html.dark-mode-active` in frontend/src/index.css

---

## Phase 2: User Story 1 - Blue Background Across All Pages (Priority: P1) 🎯 MVP

**Goal**: Apply blue background globally so every page displays the branded blue color on all devices

**Independent Test**: Open any page in the app and confirm the background is blue (#1E3A5F in light mode, #0F2440 in dark mode). Resize to mobile/tablet/desktop and verify no gaps, artifacts, or layout shifts.

### Implementation for User Story 1

- [ ] T003 [US1] Update `body` background from `var(--color-bg-secondary)` to `var(--color-bg-app)` in frontend/src/index.css

**Checkpoint**: At this point, User Story 1 should be fully functional — all pages display a blue background in both light and dark modes across all viewport sizes.

---

## Phase 3: User Story 2 - Readable Content on Blue Background (Priority: P1)

**Goal**: Ensure all text and interactive elements meet WCAG AA contrast requirements against the blue background

**Independent Test**: Run an accessibility contrast checker (e.g., Lighthouse or axe-core) on pages with the blue background. Confirm all normal text achieves ≥4.5:1 and large text achieves ≥3:1 contrast ratio.

### Implementation for User Story 2

- [ ] T004 [P] [US2] Add `--color-text-on-app: #ffffff` and `--color-text-on-app-secondary: rgba(255, 255, 255, 0.8)` tokens to `:root` in frontend/src/index.css
- [ ] T005 [P] [US2] Add `--color-text-on-app: #e6edf3` and `--color-text-on-app-secondary: rgba(230, 237, 243, 0.8)` tokens to `html.dark-mode-active` in frontend/src/index.css
- [ ] T006 [P] [US2] Update loading screen `.app-loading` color to `var(--color-text-on-app)` in frontend/src/App.css
- [ ] T007 [P] [US2] Update login screen `.app-login h1` color to `var(--color-text-on-app)` in frontend/src/App.css
- [ ] T008 [P] [US2] Update login screen `.app-login p` color to `var(--color-text-on-app-secondary)` in frontend/src/App.css

**Checkpoint**: At this point, all text rendered directly on the blue background uses high-contrast design tokens meeting WCAG AA minimums.

---

## Phase 4: User Story 3 - Content Surfaces Stand Out from Background (Priority: P2)

**Goal**: Ensure cards, modals, panels, and overlays use contrasting backgrounds that visually separate them from the blue page background

**Independent Test**: Open a page with cards, trigger a modal or dropdown, and verify that surface backgrounds (using `--color-bg` or `--color-bg-secondary`) are clearly distinguishable from the blue page background.

### Implementation for User Story 3

- [ ] T009 [US3] Verify existing surface components (`.app-header`, sidebar, cards, modals) already use `var(--color-bg)` or `var(--color-bg-secondary)` in frontend/src/App.css — no changes needed if surfaces already contrast against `--color-bg-app`

**Checkpoint**: All content surfaces (header, sidebar, cards, modals, dropdowns) visually separate from the blue background in both themes.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across themes and viewports

- [ ] T010 Verify dark mode toggle correctly switches `--color-bg-app` between #1E3A5F (light) and #0F2440 (dark) by toggling theme in the app
- [ ] T011 [P] Verify full-width alerts, banners, and notification bars retain their own background colors and are not overridden by the blue page background

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup (T001-T002, sequential)
    ↓
Phase 2: US1 - Blue Background (T003)
    ↓
Phase 3: US2 - Readable Content (T004-T008, T004+T005 parallel, T006+T007+T008 parallel)
    ↓
Phase 4: US3 - Surface Contrast (T009)
    ↓
Phase 5: Polish (T010-T011, parallel)
```

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Setup (Phase 1) — defines the CSS variable, applies it to body
- **User Story 2 (P1)**: Depends on US1 — text tokens are only needed once the blue background is applied
- **User Story 3 (P2)**: Depends on US1 — surface contrast only matters once the background is blue

### Parallel Opportunities

- T004 and T005 can run in parallel (different CSS rule blocks in frontend/src/index.css)
- T006, T007, and T008 can run in parallel (different CSS selectors in frontend/src/App.css)
- T010 and T011 can run in parallel (independent verifications)

---

## Parallel Example: User Story 2

```bash
# Launch parallel text token tasks:
Task: "Add --color-text-on-app tokens to :root in frontend/src/index.css"
Task: "Add --color-text-on-app tokens to html.dark-mode-active in frontend/src/index.css"

# Launch parallel App.css updates:
Task: "Update .app-loading color in frontend/src/App.css"
Task: "Update .app-login h1 color in frontend/src/App.css"
Task: "Update .app-login p color in frontend/src/App.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (define CSS tokens)
2. Complete Phase 2: User Story 1 (apply to body)
3. **STOP and VALIDATE**: Open the app — background should be blue
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → Tokens defined
2. Add User Story 1 → Blue background visible → Deploy/Demo (MVP!)
3. Add User Story 2 → Text contrast verified → Deploy/Demo
4. Add User Story 3 → Surface hierarchy verified → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| Setup | T001-T002 | frontend/src/index.css |
| US1 - Background | T003 | frontend/src/index.css |
| US2 - Contrast | T004-T008 | frontend/src/index.css, frontend/src/App.css |
| US3 - Surfaces | T009 | frontend/src/App.css (verification only) |
| Polish | T010-T011 | (verification only) |

**Total Tasks**: 11
**Tasks per User Story**: US1: 1, US2: 5, US3: 1
**Parallel Opportunities**: 3 groups (T004+T005, T006+T007+T008, T010+T011)
**Suggested MVP Scope**: User Story 1 (Phases 1-2, tasks T001-T003)
**Format Validation**: ✅ All tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files or different CSS selectors, no dependencies
- [Story] label maps task to specific user story for traceability
- This is an XS feature (~0.5h) — all changes are in 2 CSS files
- No new dependencies or libraries required
- Dark mode support is included in setup phase via separate CSS variable declarations
