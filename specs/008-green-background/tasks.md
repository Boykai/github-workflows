# Tasks: Add Green Background Color to App

**Input**: Design documents from `/specs/008-green-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in the feature specification. Visual verification is sufficient for this CSS-only change (per plan.md Constitution Check IV). Existing tests should not break.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature modifies only `frontend/src/` CSS files

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing project builds and tooling works before making changes

- [x] T001 Verify frontend builds successfully by running `npm run build` in `frontend/`
- [x] T002 Verify existing tests pass by running `npm run test` in `frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the new `--color-bg-surface` CSS token required before migrating component backgrounds

**⚠️ CRITICAL**: Component migration in US1 depends on this token existing first

- [x] T003 Add `--color-bg-surface: #ffffff` CSS custom property to `:root` selector in `frontend/src/index.css`
- [x] T004 Add `--color-bg-surface: #0d1117` CSS custom property to `html.dark-mode-active` selector in `frontend/src/index.css`

**Checkpoint**: Foundation ready — `--color-bg-surface` token available for component migration

---

## Phase 3: User Story 1 — Green Background Displayed Across App (Priority: P1) 🎯 MVP

**Goal**: Apply green background color (#4CAF50 light / #2E7D32 dark) to the app root container, visible on all pages and all viewport sizes

**Independent Test**: Open the app in a browser at mobile (≤768px), tablet (769–1024px), and desktop (>1024px) widths and visually confirm the green background is present on the main app container while component surfaces (cards, panels, inputs) remain neutral

### Implementation for User Story 1

- [x] T005 [US1] Update `--color-bg` from `#ffffff` to `#4CAF50` and `--color-bg-secondary` from `#f6f8fa` to `#45A849` in `:root` selector in `frontend/src/index.css`
- [x] T006 [US1] Update `--color-bg` from `#0d1117` to `#2E7D32` and `--color-bg-secondary` from `#161b22` to `#1B5E20` in `html.dark-mode-active` selector in `frontend/src/index.css`
- [x] T007 [P] [US1] Replace all `var(--color-bg)` background references with `var(--color-bg-surface)` for component surface elements in `frontend/src/App.css` (~17 background declarations, ~2 border declarations)
- [x] T008 [P] [US1] Replace all `var(--color-bg)` background references with `var(--color-bg-surface)` for chat surface elements in `frontend/src/components/chat/ChatInterface.css` (~5 declarations)
- [x] T009 [US1] Verify frontend builds with no errors after CSS changes by running `npm run build` in `frontend/`

**Checkpoint**: Green background visible on app root; component surfaces remain neutral (white/dark). User Story 1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Accessible Text and UI Elements on Green Background (Priority: P1)

**Goal**: Ensure all foreground text and interactive elements meet WCAG 2.1 AA contrast ratios against the new green background and the neutral surface backgrounds

**Independent Test**: Use a contrast-ratio checker to verify: `#24292f` on `#4CAF50` ≥ 4.5:1 (light mode), `#e6edf3` on `#2E7D32` ≥ 4.5:1 (dark mode), and text on `--color-bg-surface` backgrounds remains compliant

### Implementation for User Story 2

- [x] T010 [US2] Audit contrast ratios for `--color-text` (#24292f) against `--color-bg` (#4CAF50) and `--color-bg-surface` (#ffffff) in light mode and confirm ≥ 4.5:1 in `frontend/src/index.css`
- [x] T011 [US2] Audit contrast ratios for `--color-text` (#e6edf3) against `--color-bg` (#2E7D32) and `--color-bg-surface` (#0d1117) in dark mode and confirm ≥ 4.5:1 in `frontend/src/index.css`
- [x] T012 [US2] Adjust `--color-text`, `--color-text-secondary`, or green shade values in `frontend/src/index.css` if any contrast ratio fails WCAG AA thresholds (skip if all pass)

**Checkpoint**: All text and UI elements meet WCAG 2.1 AA contrast requirements on both green and surface backgrounds.

---

## Phase 5: User Story 3 — Centralized Color for Easy Future Updates (Priority: P2)

**Goal**: Confirm the green background color is defined in exactly one centralized location so future adjustments require changing only a single value

**Independent Test**: Change `--color-bg` to a different color value in `frontend/src/index.css` and confirm the entire app background updates with no stale references elsewhere

### Implementation for User Story 3

- [x] T013 [US3] Search the entire `frontend/src/` directory for any hard-coded green hex values (#4CAF50, #43A047, #2E7D32, #1B5E20) outside of `frontend/src/index.css` and remove or replace with `var()` references
- [x] T014 [US3] Verify that changing `--color-bg` in `:root` in `frontend/src/index.css` to a test color propagates the background change across the entire app with no stale references

**Checkpoint**: Green background is defined in exactly one location. Changing the single CSS custom property value updates the background everywhere.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation

- [x] T015 Run `npm run build` and `npm run lint` in `frontend/` to confirm no build or lint errors
- [x] T016 Visually verify green background across mobile, tablet, and desktop viewports and toggle dark mode to confirm darker green shade applies
- [x] T017 Run existing test suite via `npm run test` in `frontend/` to confirm no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (provides `--color-bg-surface` token)
- **User Story 1 (Phase 3)**: Depends on Foundational — core green background implementation
- **User Story 2 (Phase 4)**: Depends on US1 — contrast audit requires green values in place
- **User Story 3 (Phase 5)**: Depends on US1 — centralization check requires green values in place
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after US1 (Phase 3) — Requires green background values to be in place for contrast auditing
- **User Story 3 (P2)**: Can start after US1 (Phase 3) — Requires green values to exist to verify centralization. Can run in parallel with US2.

### Within Each User Story

- CSS token definitions before component migrations
- Build verification after each set of changes
- Story complete before moving to next priority

### Parallel Opportunities

- T003 and T004 can run together (same file, different selectors, but sequential edits are safer)
- T007 and T008 can run in parallel (different files: App.css vs ChatInterface.css)
- US2 (T010–T012) and US3 (T013–T014) can run in parallel after US1 completes

---

## Parallel Example: User Story 1

```bash
# After T005-T006 complete (green token values set), launch component migrations in parallel:
Task T007: "Replace var(--color-bg) with var(--color-bg-surface) in frontend/src/App.css"
Task T008: "Replace var(--color-bg) with var(--color-bg-surface) in frontend/src/components/chat/ChatInterface.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify build)
2. Complete Phase 2: Foundational (add `--color-bg-surface` token)
3. Complete Phase 3: User Story 1 (apply green, migrate components)
4. **STOP and VALIDATE**: Visually confirm green background on all viewports, component surfaces neutral
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Contrast audit → Adjust if needed
4. Add User Story 3 → Centralization verified
5. Each story adds assurance without breaking previous stories

### Single Developer Strategy

This is an XS-sized feature (~0.5h estimate). Recommended approach:

1. Complete all phases sequentially (T001 → T017)
2. Commit after each phase checkpoint
3. Total: 17 tasks across 6 phases, 3 files modified

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Files modified: `frontend/src/index.css`, `frontend/src/App.css`, `frontend/src/components/chat/ChatInterface.css`
- No new dependencies or libraries required
- No test tasks included — visual verification sufficient per spec
