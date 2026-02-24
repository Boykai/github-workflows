# Tasks: Add Blue Background Color to App

**Input**: Design documents from `/specs/010-blue-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/css-tokens.md

**Tests**: Not requested in the feature specification. This is a CSS-only change — visual verification is the primary validation method.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `frontend/index.html`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing theming system and prepare for token updates

- [ ] T001 Review existing CSS custom property system and document current token values in frontend/src/index.css
- [ ] T002 [P] Audit child components for hardcoded background-color or background values that may conflict with blue theme in frontend/src/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure needed — the existing CSS custom property theming system in `frontend/src/index.css` and `useAppTheme` hook provides all required infrastructure.

**⚠️ CRITICAL**: Phase 1 audit results must be reviewed before proceeding to ensure no hardcoded backgrounds will conflict.

- [ ] T003 Verify contracts/css-tokens.md contrast ratios against WCAG AA requirements (≥4.5:1 for normal text)

**Checkpoint**: Foundation ready — existing theming system confirmed, contrast ratios verified, user story implementation can begin.

---

## Phase 3: User Story 1 - Blue Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply a blue background color at the root level so it is visible across all pages and views of the application, with no flash of unstyled content on page load.

**Independent Test**: Navigate through every screen in the application and verify the blue background is visible, consistent, and does not flash or flicker during navigation or cold start.

### Implementation for User Story 1

- [ ] T004 [US1] Update `:root` `--color-bg` from current value to `#2563EB` in frontend/src/index.css
- [ ] T005 [US1] Update `:root` `--color-bg-secondary` from current value to `#1D4ED8` in frontend/src/index.css
- [ ] T006 [US1] Add inline `background-color: #1D4ED8` style to `<body>` tag in frontend/index.html to prevent flash of non-blue background on page load

**Checkpoint**: Blue background visible across all screens. Text may not yet be fully accessible — proceed to US2 for contrast adjustments.

---

## Phase 4: User Story 2 - Accessible and Readable Content (Priority: P1)

**Goal**: Ensure all text, icons, buttons, and UI elements remain clearly readable against the blue background by updating foreground color tokens to meet WCAG AA contrast ratios.

**Independent Test**: Review all text and interactive elements on every screen and verify contrast ratios meet ≥4.5:1 for normal text and ≥3:1 for large text using browser DevTools or a contrast checker tool.

### Implementation for User Story 2

- [ ] T007 [P] [US2] Update `:root` `--color-text` to `#FFFFFF` and `--color-text-secondary` to `#CBD5E1` in frontend/src/index.css
- [ ] T008 [P] [US2] Update `:root` `--color-border` to `#3B82F6` and `--color-shadow` to `0 1px 3px rgba(0, 0, 0, 0.2)` in frontend/src/index.css
- [ ] T009 [US2] Update `:root` semantic color tokens (`--color-primary: #93C5FD`, `--color-secondary: #94A3B8`, `--color-success: #4ADE80`, `--color-warning: #FBBF24`, `--color-danger: #F87171`) in frontend/src/index.css

**Checkpoint**: Light mode blue background with fully accessible, readable content. All WCAG AA contrast ratios met. MVP is complete — app is usable with blue branding in light mode.

---

## Phase 5: User Story 3 - Consistent Experience Across Devices and Browsers (Priority: P2)

**Goal**: Verify the blue background displays consistently across mobile, tablet, and desktop viewports and across major modern browsers.

**Independent Test**: Load the application at viewport widths 320px, 768px, and 1920px and in Chrome, Firefox, Safari, and Edge — verify the blue background renders identically with no gaps, artifacts, or layout issues.

### Implementation for User Story 3

- [ ] T010 [US3] Verify blue background renders at viewport widths 320px, 768px, 1920px, and 2560px with no gaps or layout artifacts
- [ ] T011 [US3] Verify blue background renders identically in Chrome, Firefox, Safari, and Edge (latest stable versions)
- [ ] T012 [US3] Verify browser window resize from desktop to mobile width produces smooth background adaptation with no visual glitches

**Checkpoint**: Blue background confirmed consistent across all target devices and browsers.

---

## Phase 6: User Story 4 - Theme Compatibility (Priority: P3)

**Goal**: Ensure the blue background adapts appropriately for dark mode with a deep navy blue shade, maintaining visual cohesion and accessibility in both light and dark themes.

**Independent Test**: Toggle between light and dark mode and verify the background transitions smoothly to an appropriate blue shade for each theme, with all text remaining readable.

### Implementation for User Story 4

- [ ] T013 [P] [US4] Update `html.dark-mode-active` `--color-bg` to `#1E3A5F` and `--color-bg-secondary` to `#162D4A` in frontend/src/index.css
- [ ] T014 [P] [US4] Update `html.dark-mode-active` `--color-text-secondary` to `#94A3B8` and `--color-border` to `#2563EB` in frontend/src/index.css
- [ ] T015 [US4] Update `html.dark-mode-active` semantic color tokens (`--color-primary: #60A5FA`, `--color-secondary: #94A3B8`, `--color-success: #4ADE80`, `--color-warning: #FBBF24`, `--color-danger: #F87171`) and `--shadow` to `0 1px 3px rgba(0, 0, 0, 0.4)` in frontend/src/index.css

**Checkpoint**: Both light and dark mode display appropriate blue backgrounds with accessible, readable content.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and cleanup across all user stories

- [ ] T016 [P] Resolve any hardcoded background conflicts identified in T002 audit across frontend/src/ component files
- [ ] T017 Run production build verification (`npm run build`) in frontend/
- [ ] T018 Run quickstart.md validation steps (local dev server, accessibility check, cross-browser test)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 audit completion — BLOCKS user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 completion — core background change
- **User Story 2 (Phase 4)**: Depends on Phase 3 (US1) — contrast adjustments require blue background to be in place
- **User Story 3 (Phase 5)**: Depends on Phase 3 (US1) and Phase 4 (US2) — verification requires complete light mode implementation
- **User Story 4 (Phase 6)**: Depends on Phase 2 only — dark mode tokens can be updated independently of light mode, but logically follows US1+US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Practically depends on US1 (same file, foreground colors only meaningful with blue background in place)
- **User Story 3 (P2)**: Verification-only — depends on US1 + US2 being complete
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) — Modifies different CSS selector (`html.dark-mode-active`) than US1/US2 (`:root`)

### Within Each User Story

- Models before services (N/A for CSS-only feature)
- Core token changes before verification
- Light mode before dark mode
- Commit after each task or logical group

### Parallel Opportunities

- T001 and T002 (Setup phase) can run in parallel — different activities
- T007 and T008 (US2) can run in parallel — different token groups
- T013 and T014 (US4) can run in parallel — different token groups in same selector
- US4 (dark mode) can theoretically start in parallel with US1+US2 (light mode) — different CSS selectors

---

## Parallel Example: User Story 2

```bash
# Launch foreground token updates in parallel (different token groups):
Task: "T007 [P] [US2] Update --color-text and --color-text-secondary in frontend/src/index.css"
Task: "T008 [P] [US2] Update --color-border and --shadow in frontend/src/index.css"
```

## Parallel Example: User Story 4

```bash
# Launch dark mode token updates in parallel (different token groups):
Task: "T013 [P] [US4] Update --color-bg and --color-bg-secondary in frontend/src/index.css"
Task: "T014 [P] [US4] Update --color-text-secondary and --color-border in frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (review existing system)
2. Complete Phase 2: Foundational (verify contrast ratios)
3. Complete Phase 3: User Story 1 (blue background applied)
4. Complete Phase 4: User Story 2 (foreground colors adjusted for accessibility)
5. **STOP and VALIDATE**: Blue background visible and accessible in light mode
6. Deploy/demo if ready — core feature is complete

### Incremental Delivery

1. Complete Setup + Foundational → System reviewed and ready
2. Add User Story 1 + 2 → Blue background with accessible content → Deploy/Demo (MVP!)
3. Add User Story 3 → Cross-device/browser verification → Confidence in consistency
4. Add User Story 4 → Dark mode support → Full theme compatibility
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + 2 (light mode: background + contrast)
   - Developer B: User Story 4 (dark mode tokens — different CSS selector)
3. After light mode complete: User Story 3 (verification)

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 18 |
| Setup tasks | 2 |
| Foundational tasks | 1 |
| US1 tasks | 3 |
| US2 tasks | 3 |
| US3 tasks (verification) | 3 |
| US4 tasks | 3 |
| Polish tasks | 3 |
| Parallel opportunities | 4 groups (T001∥T002, T007∥T008, T013∥T014, US4∥US1+US2) |
| Suggested MVP scope | User Story 1 + User Story 2 (light mode blue with accessible content) |
| Files modified | 2 (frontend/src/index.css, frontend/index.html) + potential component fixes |

## Notes

- [P] tasks = different files or different token groups, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests not included — not explicitly requested in the feature specification
- This is a CSS-only feature: visual verification via browser DevTools and contrast checkers is the primary validation method
- All color values sourced from contracts/css-tokens.md with verified WCAG AA contrast ratios
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
