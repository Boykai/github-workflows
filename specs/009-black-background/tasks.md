# Tasks: Add Black Background Theme to App

**Input**: Design documents from `/specs/009-black-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/theme-tokens.md ✅, quickstart.md ✅

**Tests**: No tests explicitly requested in the feature specification. This is a CSS-only visual change. Existing tests must continue to pass as a regression baseline.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/` at repository root
- Key files: `frontend/index.html`, `frontend/src/index.css`, `frontend/src/App.css`, `frontend/src/components/chat/ChatInterface.css`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing theme infrastructure and establish regression baseline

- [ ] T001 Verify existing CSS custom property theme system and current token values in frontend/src/index.css
- [ ] T002 Run baseline regression tests (npm test, npm run lint, npm run type-check) in frontend/

---

## Phase 2: Foundational (Flash Prevention)

**Purpose**: Prevent white background flash before CSS loads — MUST be complete before any token changes

**⚠️ CRITICAL**: This prevents a white flash on every page load. Must be done first.

- [ ] T003 Add inline style="background-color: #000000" to the `<html>` element in frontend/index.html

**Checkpoint**: Page load now shows black background from first paint, even before CSS loads

---

## Phase 3: User Story 1 — Black Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Set the global root background color to true black (#000000) on all pages and views, with no white flash on load or route transitions.

**Independent Test**: Navigate through every page/view in the app and verify the root background color is black (#000000) with no white or light-colored areas bleeding through. Hard-refresh (Ctrl+Shift+R) to confirm no flash.

### Implementation for User Story 1

- [ ] T004 [US1] Update :root light-mode background tokens in frontend/src/index.css — set --color-bg: #000000 and --color-bg-secondary: #121212
- [ ] T005 [US1] Update html.dark-mode-active dark-mode background tokens in frontend/src/index.css — set --color-bg: #000000 and --color-bg-secondary: #0a0a0a

**Checkpoint**: App displays true black background on all screens in both light and dark modes. No white flash on load.

---

## Phase 4: User Story 2 — Readable Text and Accessible Contrast (Priority: P1)

**Goal**: All text is clearly legible against the black background, meeting WCAG AA 4.5:1 minimum contrast ratio.

**Independent Test**: Audit all text elements and verify every text color achieves at least 4.5:1 contrast ratio against the black background (#000000).

### Implementation for User Story 2

- [ ] T006 [US2] Update :root light-mode text tokens in frontend/src/index.css — set --color-text: #ffffff (21:1 ratio) and --color-text-secondary: #a0a0a0 (10.4:1 ratio)
- [ ] T007 [US2] Update html.dark-mode-active dark-mode text tokens in frontend/src/index.css — set --color-text: #f0f0f0 (18.1:1 ratio) and --color-text-secondary: #8a8a8a (7.4:1 ratio)

**Checkpoint**: All text is white/light and readable against the black background in both modes. WCAG AA contrast ratios verified.

---

## Phase 5: User Story 3 — Dark-Themed Elevated Surfaces (Priority: P2)

**Goal**: Cards, modals, sidebars, navbars, and other elevated components use dark gray surface colors to maintain visual hierarchy against the black root background.

**Independent Test**: Inspect each elevated component (cards, modals, sidebars, navbars, dropdowns, footers) and verify they use a dark gray surface color (#121212 or #0a0a0a) distinguishable from the black root background.

### Implementation for User Story 3

- [ ] T008 [US3] Update :root shadow token in frontend/src/index.css — set --shadow: 0 1px 3px rgba(0,0,0,0.6) for visible elevation on black backgrounds
- [ ] T009 [US3] Update html.dark-mode-active shadow token in frontend/src/index.css — set --shadow: 0 1px 3px rgba(0,0,0,0.8)

**Checkpoint**: Elevated surfaces (cards, sidebar, navbar) are visually distinct from the black root background. Shadow provides depth.

> **Note**: Surface colors are driven by --color-bg-secondary (set in Phase 3, T004/T005). Components already use `var(--color-bg-secondary)` for elevated backgrounds via existing CSS. No additional surface color changes needed.

---

## Phase 6: User Story 4 — Styled Interactive Elements (Priority: P2)

**Goal**: All interactive elements (buttons, links, inputs, checkboxes) are clearly visible and usable on the dark background.

**Independent Test**: Interact with every type of interactive element (buttons, links, text inputs, checkboxes, dropdowns) and verify they are visually distinct, clearly labeled, and usable on the dark background.

### Implementation for User Story 4

- [ ] T010 [US4] Update :root accent tokens in frontend/src/index.css — set --color-primary: #539bf5, --color-secondary: #8b949e, --color-success: #3fb950, --color-warning: #d29922, --color-danger: #f85149
- [ ] T011 [US4] Update html.dark-mode-active accent tokens in frontend/src/index.css — set --color-primary: #539bf5, --color-secondary: #8b949e, --color-success: #3fb950, --color-warning: #d29922, --color-danger: #f85149
- [ ] T012 [US4] Replace hardcoded success notification background #dafbe1 → rgba(63, 185, 80, 0.15) in frontend/src/App.css
- [ ] T013 [P] [US4] Replace hardcoded error notification/alert backgrounds #fff1f0 → rgba(248, 81, 73, 0.15) at lines ~407 and ~446 in frontend/src/App.css
- [ ] T014 [US4] Verify chat interactive element colors (#15652d, #0860ca, #22c55e) are dark-compatible in frontend/src/components/chat/ChatInterface.css — no changes expected

**Checkpoint**: All buttons, links, inputs, and interactive elements are clearly visible. Notification backgrounds use dark-compatible semi-transparent variants.

---

## Phase 7: User Story 5 — Dark-Compatible Borders and Dividers (Priority: P3)

**Goal**: Borders, dividers, and outlines use subtle dark variants that are visible without being harsh, creating a cohesive dark theme.

**Independent Test**: Inspect all visible borders, dividers, and outlines across the app and verify they use dark-compatible colors visible against the black background.

### Implementation for User Story 5

- [ ] T015 [US5] Update :root border token in frontend/src/index.css — set --color-border: #2c2c2c
- [ ] T016 [US5] Update html.dark-mode-active border token in frontend/src/index.css — set --color-border: #1f1f1f

**Checkpoint**: All borders and dividers are visible but subtle against the black background.

---

## Phase 8: User Story 6 — Responsive Theme Consistency (Priority: P3)

**Goal**: The black background theme is applied consistently across all viewport sizes (mobile, tablet, desktop).

**Independent Test**: Load the app at mobile (375px), tablet (768px), and desktop (1280px) viewport widths and verify the black background and all themed styles are applied consistently at each breakpoint.

### Implementation for User Story 6

- [ ] T017 [US6] Verify black background theme consistency across mobile (375px), tablet (768px), and desktop (1280px) viewports — CSS custom properties are viewport-independent; confirm no breakpoint-specific overrides exist in frontend/src/App.css and frontend/src/index.css

**Checkpoint**: Theme renders identically at all breakpoints with no regressions.

> **Note**: CSS custom properties apply globally regardless of viewport size. No code changes expected — this is a verification task to confirm no existing media queries override theme colors.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Regression verification and build validation

- [ ] T018 Run full regression test suite (npm test) in frontend/
- [ ] T019 [P] Run lint check (npm run lint) in frontend/
- [ ] T020 [P] Run type check (npm run type-check) in frontend/
- [ ] T021 Run production build verification (npm run build) in frontend/
- [ ] T022 Run quickstart.md visual verification checklist against running dev server

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (flash prevention must be first)
- **US1 (Phase 3)**: Depends on Foundational — background tokens must be set before other visual changes
- **US2 (Phase 4)**: Depends on US1 — text contrast only meaningful once background is black
- **US3 (Phase 5)**: Depends on US1 — surface elevation relative to black root background
- **US4 (Phase 6)**: Depends on US1 + US2 — interactive elements need both background and text context
- **US5 (Phase 7)**: Depends on US1 — border visibility relative to black background
- **US6 (Phase 8)**: Depends on US1–US5 — verification of all theme changes across viewports
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Can start after US1 — text tokens are independent but verification requires black background
- **US3 (P2)**: Can start after US1 — elevated surfaces are relative to root background
- **US4 (P2)**: Can start after US1 + US2 — interactive styling needs both background and text context
- **US5 (P3)**: Can start after US1 — border tokens are independent of text/accent tokens
- **US6 (P3)**: Depends on all other stories — responsive verification is a cross-cutting concern

### Within Each User Story

- Token changes in `index.css` before hardcoded replacements in component CSS
- `:root` (light mode) before `html.dark-mode-active` (dark mode) for consistent ordering
- Verification tasks after implementation tasks

### Parallel Opportunities

- T004 and T005 (US1 light + dark background tokens) edit the same file but different selectors — sequential recommended
- T006 and T007 (US2 light + dark text tokens) — same file, sequential recommended
- T008 and T009 (US3 shadow tokens) — same file, sequential recommended
- T010 and T011 (US4 accent tokens) — same file, sequential recommended
- T012 and T013 (US4 App.css hardcoded replacements) — same file but different selectors, T013 is [P]
- T018, T019, T020 (regression suite) — T019 and T020 can run in parallel
- **Cross-story parallelism**: US3 and US5 could theoretically run in parallel (shadow vs border tokens in same file) but sequential is safer for a single file

---

## Parallel Example: User Story 4

```bash
# After accent token updates (T010, T011), these can run in parallel:
Task: T012 "Replace hardcoded success notification bg in frontend/src/App.css"
Task: T013 "Replace hardcoded error notification/alert bg in frontend/src/App.css"

# Verification can run after both:
Task: T014 "Verify chat interactive element colors in frontend/src/components/chat/ChatInterface.css"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup — verify baseline
2. Complete Phase 2: Foundational — flash prevention on `<html>`
3. Complete Phase 3: US1 — black background tokens
4. Complete Phase 4: US2 — text contrast tokens
5. **STOP and VALIDATE**: App has black background with readable white text on all screens
6. This is a shippable MVP — the core visual change is complete

### Incremental Delivery

1. Setup + Foundational → flash prevention ready
2. US1 + US2 → Black background with readable text (MVP!)
3. US3 → Elevated surfaces have visual depth
4. US4 → Interactive elements restyled, notification backgrounds fixed
5. US5 → Borders and dividers refined
6. US6 → Cross-viewport verification complete
7. Polish → Regression tests pass, build verified

### Single-Developer Strategy (Recommended)

Since all changes are in 3-4 CSS files with ~27 lines total:

1. Complete all phases sequentially in one session
2. Each phase modifies different token groups in the same files
3. Verify visually after each phase checkpoint
4. Run full regression suite once at the end (Phase 9)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 22 |
| **US1 tasks** | 2 (background tokens) |
| **US2 tasks** | 2 (text tokens) |
| **US3 tasks** | 2 (shadow tokens) |
| **US4 tasks** | 5 (accent tokens + hardcoded replacements) |
| **US5 tasks** | 2 (border tokens) |
| **US6 tasks** | 1 (viewport verification) |
| **Setup/Foundational** | 3 |
| **Polish** | 5 |
| **Parallel opportunities** | 3 (T013, T019, T020 marked [P]) |
| **Files modified** | 3 (`index.html`, `index.css`, `App.css`) + 1 verified (`ChatInterface.css`) |
| **Lines changed** | ~27 across 3 files + 1 HTML attribute |
| **MVP scope** | Phases 1–4 (US1 + US2): black background + readable text |

## Notes

- [P] tasks = different files or non-overlapping selectors, no dependencies
- [Story] label maps task to specific user story for traceability
- No test tasks included — tests not requested in spec (Constitution Check IV: Test Optionality)
- Both light and dark modes become black-themed — existing toggle still works but both modes are dark
- All proposed colors verified against WCAG AA 4.5:1 minimum contrast ratio (see data-model.md validation table)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
