# Tasks: Add Pink Background Color to App

**Input**: Design documents from `/specs/012-pink-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in the feature specification. Existing vitest and Playwright suites cover regression. No new test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. This feature is a CSS-only change — 1 file modified (`frontend/src/index.css`), 2 CSS custom property values updated.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature modifies only `frontend/src/index.css`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No setup tasks needed — the project already exists, all dependencies are installed, and the theming infrastructure (CSS custom properties, Tailwind config, shadcn/ui) is already in place.

*No tasks in this phase.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational tasks needed — the existing `--background` CSS custom property in `frontend/src/index.css` already serves as the centralized design token for the app-level background. The body element already applies it via `@apply bg-background`. No new infrastructure, tokens, or abstractions are required.

*No tasks in this phase.*

**Checkpoint**: Foundation already in place — user story implementation can begin immediately.

---

## Phase 3: User Story 1 — Pink Background Across All Pages (Priority: P1) 🎯 MVP

**Goal**: Apply a pink background color (#FFC0CB) to the app's root-level background so it is visible on all pages and routes. This is the core deliverable.

**Independent Test**: Open the app in a browser and navigate through every available page/route. Verify the background color is pink on each page with no page showing the previous default white background.

### Implementation for User Story 1

- [ ] T001 [US1] Update light mode `--background` CSS custom property from `0 0% 100%` to `350 100% 88%` in the `:root` selector in `frontend/src/index.css`

**Checkpoint**: At this point, the light mode pink background should be visible on all pages. Verify by opening the app and navigating through all routes — every page should display a pink background.

---

## Phase 4: User Story 2 — Readable Content Against Pink Background (Priority: P1)

**Goal**: Ensure all text, icons, and UI components remain clearly readable and usable against the pink background, maintaining WCAG AA contrast ratios (minimum 4.5:1 for normal text).

**Independent Test**: Visually inspect all pages for text legibility, icon visibility, and UI component clarity against the pink background. Use a contrast checker to verify the foreground color (`--foreground: 222.2 84% 4.9%` ≈ #020817) against the pink background (`350 100% 88%` ≈ #FFC0CB) achieves ≥ 4.5:1 contrast ratio.

### Implementation for User Story 2

- [ ] T002 [US2] Verify WCAG AA contrast compliance: confirm existing `--foreground` value (`222.2 84% 4.9%`) against new `--background` value (`350 100% 88%`) provides ≥ 4.5:1 contrast ratio (~12.5:1 expected) — no code changes needed, validation only in `frontend/src/index.css`
- [ ] T003 [US2] Verify component backgrounds (`--card`, `--popover`, `--secondary`, `--muted`, `--accent`) remain unchanged and visually distinct from the pink background — no code changes needed, visual inspection of `frontend/src/index.css` token values

**Checkpoint**: At this point, User Stories 1 AND 2 should both be complete. All text is readable against the pink background and component surfaces are visually distinct.

---

## Phase 5: User Story 3 — Dark Mode Handling (Priority: P2)

**Goal**: Provide a dark-mode-appropriate pink variant background so dark mode users have a comfortable experience that maintains the pink color theme.

**Independent Test**: Toggle the operating system or browser to dark mode (or toggle the app's dark mode if available). Verify the background displays a dark muted pink (#281519 / `350 30% 12%`) rather than the light pink or the previous dark mode default.

### Implementation for User Story 3

- [ ] T004 [US3] Update dark mode `--background` CSS custom property from `222.2 84% 4.9%` to `350 30% 12%` in the `.dark` selector in `frontend/src/index.css`

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all be complete. Both light mode (pink) and dark mode (dark muted pink) backgrounds are applied correctly.

---

## Phase 6: User Story 4 — Centralized Color Definition for Future Theming (Priority: P2)

**Goal**: Confirm the pink color value is defined in a single, centralized location (the `--background` CSS custom property) so future theme changes require updating only one place.

**Independent Test**: Search the codebase for the pink color value and confirm it is declared in exactly one place (`frontend/src/index.css`). Verify that changing the value in that one location updates the background everywhere.

### Implementation for User Story 4

- [ ] T005 [US4] Verify centralized color definition: confirm `--background` in `frontend/src/index.css` is the single source of truth — Tailwind's `tailwind.config.js` maps `background` to `hsl(var(--background))`, body applies `@apply bg-background`, and no hardcoded pink values exist elsewhere — no code changes needed, validation only

**Checkpoint**: All 4 user stories are complete. The pink background is globally applied, readable, dark-mode-compatible, and centrally defined.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T006 Run `npm run type-check` in `frontend/` to confirm no type errors introduced
- [ ] T007 [P] Run `npm run lint` in `frontend/` to confirm no linting errors introduced
- [ ] T008 [P] Run `npm run test` in `frontend/` to confirm existing unit tests still pass
- [ ] T009 Run `npm run build` in `frontend/` to confirm production build succeeds
- [ ] T010 Run quickstart.md verification checklist from `specs/012-pink-background/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Skipped — infrastructure already exists
- **Foundational (Phase 2)**: Skipped — theming system already in place
- **User Story 1 (Phase 3)**: No dependencies — can start immediately. This is the core CSS change.
- **User Story 2 (Phase 4)**: Depends on T001 (pink background must be applied to verify contrast). Validation-only, no code changes.
- **User Story 3 (Phase 5)**: No dependency on US1/US2 — independent CSS change in the `.dark` selector. Can run in parallel with US2.
- **User Story 4 (Phase 6)**: Depends on T001 and T004 (both values must be set to verify centralization). Validation-only, no code changes.
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies — start immediately
- **User Story 2 (P1)**: Depends on US1 (need pink background applied to verify contrast)
- **User Story 3 (P2)**: Independent of US1/US2 (different CSS selector, different line)
- **User Story 4 (P2)**: Depends on US1 and US3 (need both values set to verify centralization)

### Within Each User Story

- US1: Single CSS value change → visual verification
- US2: Contrast ratio validation only (no code changes)
- US3: Single CSS value change → visual verification
- US4: Centralization audit only (no code changes)

### Parallel Opportunities

- T001 (US1 light mode) and T004 (US3 dark mode) modify different lines in the same file — they CAN be done in parallel as they touch different CSS selectors (`:root` vs `.dark`)
- T002 and T003 (US2 validations) can run in parallel
- T006, T007, T008 (Polish validations) can run in parallel after all code changes
- US2 and US4 are validation-only and can be done concurrently once their dependencies are met

---

## Parallel Example: User Story 1 + User Story 3

```bash
# These two tasks modify different selectors in the same file and can be done together:
Task T001: "Update --background in :root selector (light mode) in frontend/src/index.css"
Task T004: "Update --background in .dark selector (dark mode) in frontend/src/index.css"

# After both changes, run validations in parallel:
Task T002: "Verify WCAG AA contrast for light mode"
Task T003: "Verify component backgrounds unchanged"
Task T005: "Verify centralized color definition"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001: Change light mode `--background` to `350 100% 88%`
2. **STOP and VALIDATE**: Open app, verify pink background on all pages
3. Deploy/demo if ready — the core feature is delivered

### Incremental Delivery

1. T001 (US1) → Pink background visible on all pages (MVP!)
2. T002–T003 (US2) → Contrast and readability validated
3. T004 (US3) → Dark mode pink variant applied
4. T005 (US4) → Centralization confirmed
5. T006–T010 → Polish and regression validation
6. Each story adds confidence without breaking previous stories

### Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 10 |
| **Code-change tasks** | 2 (T001, T004) |
| **Validation-only tasks** | 3 (T002, T003, T005) |
| **CI/regression tasks** | 5 (T006–T010) |
| **Files modified** | 1 (`frontend/src/index.css`) |
| **Lines changed** | 2 |
| **New dependencies** | 0 |
| **New files** | 0 |
| **Suggested MVP** | User Story 1 (T001 only) |

---

## Notes

- [P] tasks = different files or different selectors, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests were NOT requested in the feature specification — existing vitest and Playwright suites provide regression coverage
- This is a CSS-only change: no backend, no new components, no new dependencies
- The `--background` token is already the centralized design token — no new abstractions needed
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
