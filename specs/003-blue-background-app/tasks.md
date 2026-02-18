# Tasks: Add Blue Background Color to App

**Input**: Design documents from `/specs/003-blue-background-app/`
**Prerequisites**: plan.md ✅, spec.md ✅

**Tests**: Tests are NOT included (not explicitly requested in spec). Existing visual regression test baselines may need updating.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Design Token Preparation)

**Purpose**: No setup needed — the existing CSS custom property infrastructure in `frontend/src/index.css` already supports the change. Proceed directly to user stories.

---

## Phase 2: User Story 1 - Blue Background in Light Mode (Priority: P1) 🎯 MVP

**Goal**: Apply light blue background (#DBEAFE) across all pages in light mode, replacing the current white/neutral default

**Independent Test**: Open the application in a browser with the default (light) theme and visually confirm the entire viewport has a light blue background. All text, buttons, and interactive elements remain readable.

### Implementation for User Story 1

- [x] T001 [US1] Update `--color-bg` from `#ffffff` to `#DBEAFE` in the `:root` selector in frontend/src/index.css
- [x] T002 [US1] Update `--color-bg-secondary` from `#f6f8fa` to `#BFDBFE` in the `:root` selector in frontend/src/index.css
- [x] T003 [US1] Add `transition: background-color 0.3s ease;` to the `body` rule in frontend/src/index.css for smooth theme toggling

**Checkpoint**: Light mode now displays a blue background across all pages. All text remains readable (WCAG AA 11.7:1 contrast ratio with #24292f text).

---

## Phase 3: User Story 2 - Blue Background in Dark Mode (Priority: P2)

**Goal**: Apply deep navy blue background (#1E3A8A) across all pages in dark mode, replacing the current dark gray/black default

**Independent Test**: Toggle the application to dark mode and visually confirm the entire viewport has a deep navy blue background. All text and interactive elements remain readable.

### Implementation for User Story 2

- [x] T004 [US2] Update `--color-bg` from `#0d1117` to `#1E3A8A` in the `html.dark-mode-active` selector in frontend/src/index.css
- [x] T005 [US2] Update `--color-bg-secondary` from `#161b22` to `#1E3A5C` in the `html.dark-mode-active` selector in frontend/src/index.css

**Checkpoint**: Dark mode now displays a deep navy blue background. Theme toggle transitions smoothly between light blue and dark navy. All text remains readable (WCAG AA 9.4:1 contrast ratio with #e6edf3 text).

---

## Phase 4: User Story 3 - Consistent UI Elements on Blue Background (Priority: P3)

**Goal**: Verify all overlay elements (modals, dropdowns, tooltips, cards) render correctly against the new blue backgrounds

**Independent Test**: Interact with all modal dialogs, dropdown menus, tooltips, and card components to confirm they appear correctly on the blue background with proper visual hierarchy.

### Implementation for User Story 3

- [x] T006 [US3] Visually audit all modal, dropdown, tooltip, and card components in both light and dark mode against the new blue backgrounds in the running application
- [x] T007 [US3] Verify no component-level CSS in frontend/src/App.css or frontend/src/components/ overrides the blue background with conflicting hardcoded colors

**Checkpoint**: All overlay and floating UI elements render correctly on the blue background. No visual regressions.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across browsers and viewports

- [x] T008 Verify full-bleed blue background renders on mobile viewport sizes with no white gaps or overscroll artifacts
- [x] T009 Update any existing Playwright snapshot baselines in frontend/e2e/ if tests reference background color values

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped — no setup needed
- **User Story 1 (Phase 2)**: Can start immediately — light mode CSS variable changes
- **User Story 2 (Phase 3)**: Independent of US1 — dark mode CSS variable changes (same file, different selectors)
- **User Story 3 (Phase 4)**: Depends on US1 and US2 completion — visual audit requires both themes active
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — modifies `:root` selector only
- **User Story 2 (P2)**: No dependencies — modifies `html.dark-mode-active` selector only
- **User Story 3 (P3)**: Depends on US1 + US2 — requires both blue backgrounds to be applied before auditing

### Within Each User Story

- CSS variable changes are atomic per selector
- Body transition property (T003) can be added alongside US1 changes

### Parallel Opportunities

- T001 and T002 modify the same selector (`:root`) — execute sequentially
- T004 and T005 modify the same selector (`html.dark-mode-active`) — execute sequentially
- US1 (T001-T003) and US2 (T004-T005) modify different selectors — can execute in parallel

---

## Parallel Example: User Story 1 + User Story 2

```bash
# US1 and US2 can be implemented in parallel since they modify different CSS selectors:
# Developer A: US1 - Update :root variables (T001, T002, T003)
# Developer B: US2 - Update html.dark-mode-active variables (T004, T005)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: User Story 1 (T001-T003)
2. **STOP and VALIDATE**: Open app in light mode, confirm blue background
3. Deploy/demo if ready — light mode blue background is the core deliverable

### Incremental Delivery

1. Add User Story 1 → Light mode blue background → Validate (MVP!)
2. Add User Story 2 → Dark mode blue background → Validate
3. Complete User Story 3 → Visual audit of all UI elements → Validate
4. Polish → Cross-browser and mobile verification

### Single Developer Strategy

Since all changes are in one file (`frontend/src/index.css`):

1. Apply all CSS variable changes (T001-T005) in a single editing session
2. Verify light mode (US1 checkpoint)
3. Verify dark mode (US2 checkpoint)
4. Audit overlay elements (US3 checkpoint)
5. Cross-browser/mobile check (Polish)

---

## Summary

| Phase | Tasks | Files Modified |
|-------|-------|---------------|
| US1 - Light Mode | T001-T003 | frontend/src/index.css |
| US2 - Dark Mode | T004-T005 | frontend/src/index.css |
| US3 - UI Audit | T006-T007 | Visual audit only |
| Polish | T008-T009 | frontend/e2e/ (if needed) |

**Total Tasks**: 9
**Tasks per User Story**: US1: 3, US2: 2, US3: 2, Polish: 2
**Parallel Opportunities**: US1 and US2 can execute in parallel (different CSS selectors)
**Independent Test Criteria**: Each story has a standalone visual verification
**Suggested MVP Scope**: User Story 1 only (light mode blue background)
**Format Validation**: ✅ ALL tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- All changes confined to `frontend/src/index.css` — no component-level modifications needed
- WCAG contrast ratios pre-verified: Light mode 11.7:1, Dark mode 9.4:1 (both exceed 4.5:1 AA requirement)
- Commit after each phase checkpoint
