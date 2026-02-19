# Tasks: Add Teal Background Color to App

**Input**: Design documents from `/specs/007-teal-background/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/file-changes.md, quickstart.md

**Tests**: Not explicitly requested in feature specification. Test tasks are omitted per Test Optionality principle. Visual verification via existing E2E infrastructure is sufficient.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify project structure and existing design token system

- [ ] T001 Verify existing CSS custom property system in frontend/src/index.css — confirm `:root` and `html.dark-mode-active` blocks exist with `--color-*` tokens and that `body` uses `var(--color-bg-secondary)` for background

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the teal background design token as a single source of truth in the CSS custom property system

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Add `--color-bg-app: #0D9488;` CSS custom property to the `:root` block in frontend/src/index.css — insert after `--color-bg-secondary` line to group background tokens together

**Checkpoint**: Design token defined — user story implementation can now begin

---

## Phase 3: User Story 1 — Teal Background Visible Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply the teal background color globally so all screens and views inherit it by default with no flash of white during transitions

**Independent Test**: Navigate through every screen/route in the app and confirm the teal (#0D9488) background is visible behind all content areas on all viewport sizes

### Implementation

- [ ] T003 [US1] Update `body` background property from `var(--color-bg-secondary)` to `var(--color-bg-app)` in frontend/src/index.css — this applies the teal background globally across all routes and screens
- [ ] T004 [US1] Verify teal background renders on login screen, loading screen, and main app layout — confirm no white flash during route transitions and full viewport coverage on mobile, tablet, and desktop in frontend/src/index.css

**Checkpoint**: MVP complete — teal background visible across all screens. Cards, modals, sidebar, and header retain their own backgrounds (var(--color-bg) / var(--color-bg-secondary)) and remain visually distinct.

---

## Phase 4: User Story 2 — Readable Content on Teal Background (Priority: P1)

**Goal**: Ensure all text, icons, and interactive elements remain clearly readable against the teal background with WCAG AA contrast compliance

**Independent Test**: Inspect all text elements rendered directly on the teal background and verify WCAG AA compliance (4.5:1 minimum for normal text, 3:1 for large text) using a contrast checker

### Implementation

- [ ] T005 [US2] Verify WCAG AA contrast compliance for all text on teal background in frontend/src/index.css — confirm white text (#FFFFFF) on #0D9488 achieves ≥4.53:1 ratio and dark text (#24292F) on #0D9488 achieves ≥5.5:1 ratio per research.md contrast data
- [ ] T006 [US2] Verify existing UI components are not broken — confirm cards (var(--color-bg)), modals (var(--color-bg)), sidebar (var(--color-bg)), header (var(--color-bg)), and board columns (var(--color-bg-secondary)) layer correctly on top of the teal background in frontend/src/index.css

**Checkpoint**: Accessibility verified — all text meets WCAG AA contrast and all existing components remain legible and visually distinct.

---

## Phase 5: User Story 3 — Dark Mode Teal Variant (Priority: P2)

**Goal**: Apply a darker teal shade when dark mode is active so the background adapts to low-light conditions

**Independent Test**: Toggle dark mode via the theme toggle (🌙/☀️) and confirm the background shifts to #0F766E without jarring flashes

### Implementation

- [ ] T007 [US3] Add `--color-bg-app: #0F766E;` to the `html.dark-mode-active` block in frontend/src/index.css — the existing useAppTheme hook and class-toggling mechanism handle the switch automatically, no other files need changes
- [ ] T008 [US3] Verify dark mode teal variant renders correctly — confirm toggling dark mode transitions smoothly between #0D9488 (light) and #0F766E (dark) and that light text (#E6EDF3) on #0F766E achieves ≥6.8:1 contrast ratio in frontend/src/index.css

**Checkpoint**: Dark mode support complete — both light and dark teal variants defined as design tokens in a single file.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [ ] T009 Run quickstart.md verification checklist — verify all items from specs/007-teal-background/quickstart.md pass (login screen teal, main app teal, dark mode toggle, route transitions, component backgrounds)
- [ ] T010 Confirm single source of truth — verify `--color-bg-app` is defined in exactly one location (`:root` for light, `html.dark-mode-active` for dark) and no hardcoded teal overrides exist elsewhere in frontend/src/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP delivery target
- **US2 (Phase 4)**: Depends on Phase 3 (teal background must be applied to verify contrast)
- **US3 (Phase 5)**: Depends on Phase 2 (only needs the token pattern, not US1/US2 completion)
- **Polish (Phase 6)**: Depends on all prior phases being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **US2 (P1)**: Depends on US1 (teal background must be visible to verify contrast compliance)
- **US3 (P2)**: Can start after Foundational (Phase 2) — independent of US1/US2 (different selector block in same file)

### Within Each Phase

- Token definition before token usage
- Implementation before verification
- All changes in a single file (frontend/src/index.css) — no cross-file dependencies

### Parallel Opportunities

- US1 (Phase 3) and US3 (Phase 5) can run in parallel after Phase 2 — they modify different CSS selector blocks in the same file
- T005 and T006 (US2 verification tasks) can run in parallel

---

## Parallel Example: After Foundational Phase

```
# These can start in parallel after Phase 2:
T003: Update body background to var(--color-bg-app) in frontend/src/index.css [:root applied]
T007: Add --color-bg-app to dark mode block in frontend/src/index.css [html.dark-mode-active]
```

---

## Implementation Strategy

### MVP First (Phase 1 + 2 + 3)

1. Complete Phase 1: Verify existing token system
2. Complete Phase 2: Define --color-bg-app token
3. Complete Phase 3: Apply token to body background
4. **STOP and VALIDATE**: All screens show teal background, no white flashes
5. Deploy/demo — teal background visible across entire app

### Incremental Delivery

1. Setup + Foundational → Token defined as single source of truth
2. Add US1 → Teal background visible globally → **MVP!**
3. Add US2 → Contrast verified, accessibility confirmed → Production-safe
4. Add US3 → Dark mode variant applied → Complete feature
5. Polish → Final verification → Ready for merge

### Key Optimization

All changes are in a single file (`frontend/src/index.css`), making this a minimal, low-risk change. The entire feature can be implemented and verified in a single session with no build-step or dependency changes required.

---

## Notes

- [P] tasks = different files or selector blocks, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- This feature modifies exactly ONE file: `frontend/src/index.css`
- No new dependencies, no structural changes — purely CSS token additions
- The teal values (#0D9488 light, #0F766E dark) are pre-validated for WCAG AA compliance (see research.md)
- Existing components already use var(--color-bg) and var(--color-bg-secondary) for their own backgrounds, so they will naturally layer on top of the teal root background
- Commit after each task or logical group
- Stop at any checkpoint to validate the increment independently
