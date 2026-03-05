# Tasks: Ruby-Colored Background Theme

**Input**: Design documents from `/specs/018-ruby-background-theme/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No automated tests requested in the feature specification. Verification is manual (visual inspection and contrast ratio checks per quickstart.md).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React + Tailwind CSS frontend)
- Theme tokens defined in `frontend/src/index.css` (`:root` and `.dark` scopes)
- Tailwind config in `frontend/tailwind.config.js` (consumes CSS custom properties via `hsl(var(--token))`)
- Theme toggling handled by `frontend/src/components/ThemeProvider.tsx`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current state and confirm no prerequisite changes are needed

- [ ] T001 Verify current theme token values in `frontend/src/index.css` match expected baseline (`:root` `--background: 0 0% 100%`, `--foreground: 222.2 84% 4.9%`; `.dark` `--background: 222.2 84% 4.9%`, `--foreground: 210 40% 98%`)
- [ ] T002 Confirm `frontend/tailwind.config.js` maps `background` to `hsl(var(--background))` and `foreground` to `hsl(var(--foreground))` — no changes needed
- [ ] T003 Confirm `frontend/src/components/ThemeProvider.tsx` toggles `.dark` class on `document.documentElement` — no changes needed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking infrastructure changes are needed for this feature

**⚠️ NOTE**: This feature is a pure CSS token update in a single file (`frontend/src/index.css`). The existing theming infrastructure (Tailwind config, ThemeProvider, `bg-background`/`text-foreground` utility classes) already supports the change with no modifications. Phase 1 verification confirms the foundation is ready.

**Checkpoint**: Foundation verified — user story implementation can now begin

---

## Phase 3: User Story 1 — Ruby Background Applied Across All Views (Priority: P1) 🎯 MVP

**Goal**: Apply a ruby-colored background (deep red, #9B111E) to the main application background so that every primary view displays the ruby theme in both light and dark modes.

**Independent Test**: Open the application in a browser; verify the main background is ruby red (#9B111E) in light mode and dark ruby (#6B0C15) in dark mode across all primary views (project board, chat, settings).

### Implementation for User Story 1

- [ ] T004 [US1] Update `:root` scope `--background` token from `0 0% 100%` to `355 80% 34%` (ruby #9B111E) in `frontend/src/index.css`
- [ ] T005 [US1] Update `.dark` scope `--background` token from `222.2 84% 4.9%` to `355 80% 22%` (dark ruby #6B0C15) in `frontend/src/index.css`
- [ ] T006 [US1] Verify ruby background renders on all primary views by running `cd frontend && npm run dev` and navigating through the application

**Checkpoint**: At this point, the ruby background should be visible across all views in both light and dark modes. Text may not yet be optimally readable — that is addressed in User Story 2.

---

## Phase 4: User Story 2 — Accessible Contrast with Ruby Background (Priority: P1)

**Goal**: Ensure all foreground text and UI elements maintain WCAG AA 4.5:1 contrast ratio against the ruby background by updating foreground color tokens to white/near-white.

**Independent Test**: Use a contrast checker (e.g., WebAIM) to verify: light mode — #FFFFFF on #9B111E yields ≥ 5.57:1; dark mode — #FAFAFA on #6B0C15 yields ≥ 8.2:1. Visually confirm all text, icons, and interactive elements are clearly readable.

### Implementation for User Story 2

- [ ] T007 [US2] Update `:root` scope `--foreground` token from `222.2 84% 4.9%` to `0 0% 100%` (white #FFFFFF) in `frontend/src/index.css`
- [ ] T008 [US2] Update `.dark` scope `--foreground` token from `210 40% 98%` to `0 0% 98%` (near-white #FAFAFA) in `frontend/src/index.css`
- [ ] T009 [US2] Verify contrast ratios using a contrast checker tool — confirm light mode (#FFFFFF on #9B111E) ≥ 4.5:1 and dark mode (#FAFAFA on #6B0C15) ≥ 4.5:1
- [ ] T010 [US2] Visually verify that card, popover, modal, and input components retain their own distinct surface/foreground colors and remain readable (these use `--card`, `--popover`, `--muted` tokens which are unchanged)

**Checkpoint**: At this point, the ruby background with accessible foreground text should be fully functional. User Stories 1 AND 2 together form the MVP — the application is visually themed and accessible.

---

## Phase 5: User Story 3 — Responsive Ruby Background (Priority: P2)

**Goal**: Confirm the ruby background renders correctly and consistently at mobile (≤ 640px), tablet (641–1024px), and desktop (> 1024px) breakpoints with no gaps, artifacts, or inconsistencies.

**Independent Test**: Load the application at common breakpoints (375px, 768px, 1440px) using browser DevTools responsive mode and verify the ruby background fills the entire viewport without gaps or visual artifacts.

### Implementation for User Story 3

- [ ] T011 [US3] Test ruby background at mobile breakpoint (375px width) using browser DevTools — verify full viewport coverage in `frontend/src/index.css` body styles
- [ ] T012 [US3] Test ruby background at tablet breakpoint (768px width) using browser DevTools — verify consistent rendering
- [ ] T013 [US3] Test ruby background at desktop breakpoint (1440px width) using browser DevTools — verify no horizontal or vertical gaps
- [ ] T014 [US3] Verify the existing diamond background pattern (applied via `body::before` in `frontend/src/index.css`) harmonizes with the ruby background color — adjust `--diamond-color` if needed to complement ruby

**Checkpoint**: The ruby background should now render consistently across all device sizes. No code changes are expected in this phase unless the diamond pattern needs color adjustment.

---

## Phase 6: User Story 4 — Design Token for Ruby Color (Priority: P3)

**Goal**: Ensure the ruby background color is defined as a centralized, reusable design token (CSS custom property) so a developer can change it in one place and have the update reflected application-wide.

**Independent Test**: A developer changes the `--background` value in `:root` to a different color, reloads, and verifies the change is reflected across all views without touching any other file.

### Implementation for User Story 4

- [ ] T015 [US4] Add a CSS fallback `background-color: #9B111E;` and `color: #FFFFFF;` before the `@apply` directive in the `body` rule in `frontend/src/index.css` for browsers without CSS custom property support
- [ ] T016 [US4] Verify the ruby color is defined exclusively via CSS custom properties (`--background` in `:root` and `.dark` scopes) and not hardcoded elsewhere — confirm single-source-of-truth by searching for `#9B111E` in the codebase (should only appear as fallback)
- [ ] T017 [US4] Verify that changing the `--background` token value in `frontend/src/index.css` updates the ruby color application-wide on reload without any additional file changes

**Checkpoint**: The ruby color is centralized as a design token with a CSS fallback. A developer can modify the color in one place.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all user stories

- [ ] T018 Verify no existing UI components (modals, cards, forms, navigation) exhibit layout, spacing, or styling regressions after the ruby background change — run the application and navigate all views
- [ ] T019 Verify the diamond background pattern in `frontend/src/index.css` (body::before pseudo-element) displays correctly over the ruby background in both light and dark modes
- [ ] T020 Run quickstart.md validation steps end-to-end: start dev server, check light mode, toggle dark mode, check components, check responsive, verify contrast ratios
- [ ] T021 Verify the existing frontend build succeeds with no errors by running `cd frontend && npm run build`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (verification only)
- **Foundational (Phase 2)**: Depends on Setup confirmation — no blocking work needed
- **User Story 1 (Phase 3)**: Can start after Phase 1 verification — updates `--background` tokens
- **User Story 2 (Phase 4)**: Can start after Phase 1 verification — updates `--foreground` tokens
  - US1 and US2 modify different tokens in the same file but are independent changes
  - For best results, complete US1 first so foreground changes can be visually verified against the ruby background
- **User Story 3 (Phase 5)**: Depends on US1 + US2 completion — responsive testing requires the final colors to be in place
- **User Story 4 (Phase 6)**: Can start after US1 + US2 — adds fallback and validates token centralization
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — changes `--background` tokens only
- **User Story 2 (P1)**: Logically depends on US1 (need ruby background to test foreground contrast), but the token changes are independent
- **User Story 3 (P2)**: Depends on US1 + US2 — responsive testing requires final color values
- **User Story 4 (P3)**: Depends on US1 + US2 — token validation requires colors to be in place; adds fallback

### Within Each User Story

- Token updates before visual verification
- Verification confirms the story's acceptance criteria
- Story complete before moving to next priority

### Parallel Opportunities

- **US1 (T004–T005) and US2 (T007–T008)** can be implemented in parallel — they modify different CSS tokens (`--background` vs `--foreground`) in the same file, non-overlapping sections
- **T011, T012, T013** (responsive breakpoint tests) can run in parallel — independent verification at different widths
- **T018, T019, T020** (polish verification tasks) can run in parallel — independent checks

---

## Parallel Example: User Story 1 + User Story 2

```bash
# US1 and US2 modify non-overlapping tokens in the same file:
Task T004: "Update :root --background to 355 80% 34% in frontend/src/index.css"
Task T005: "Update .dark --background to 355 80% 22% in frontend/src/index.css"
Task T007: "Update :root --foreground to 0 0% 100% in frontend/src/index.css"
Task T008: "Update .dark --foreground to 0 0% 98% in frontend/src/index.css"

# These 4 token changes can be made in a single editing session since they are
# non-overlapping lines in the same file. The verification steps (T006, T009, T010)
# should run after all token changes are complete.
```

## Parallel Example: User Story 3 — Responsive Testing

```bash
# All responsive breakpoint tests can run simultaneously:
Task T011: "Test ruby background at mobile breakpoint (375px)"
Task T012: "Test ruby background at tablet breakpoint (768px)"
Task T013: "Test ruby background at desktop breakpoint (1440px)"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (verify current state)
2. Phase 2: Foundational (no work needed — confirmed ready)
3. Complete Phase 3: User Story 1 (apply ruby `--background` tokens)
4. Complete Phase 4: User Story 2 (apply accessible `--foreground` tokens)
5. **STOP and VALIDATE**: All 4 token changes in `frontend/src/index.css` deliver a functional, accessible ruby-themed application
6. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation verified
2. Add User Story 1 + User Story 2 → Ruby background with accessible contrast → Deploy/Demo (MVP!)
3. Add User Story 3 → Responsive verification complete → Confirm no device-specific issues
4. Add User Story 4 → CSS fallback added, token centralization verified → Deploy/Demo (final)
5. Polish phase → Full regression check, build verification, quickstart validation

### Single Developer Strategy

Given the small scope (1 file, 4 token changes + 2 fallback lines):

1. Make all token changes (T004, T005, T007, T008) in a single editing session
2. Add fallback (T015) in the same session
3. Run dev server and verify all acceptance criteria (T006, T009–T014, T016–T020)
4. Run build (T021) to confirm no regressions
5. Total estimated time: ~30 minutes

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 21 |
| **User Story 1 (P1)** | 3 tasks (T004–T006) |
| **User Story 2 (P1)** | 4 tasks (T007–T010) |
| **User Story 3 (P2)** | 4 tasks (T011–T014) |
| **User Story 4 (P3)** | 3 tasks (T015–T017) |
| **Setup** | 3 tasks (T001–T003) |
| **Polish** | 4 tasks (T018–T021) |
| **Parallel opportunities** | US1 + US2 tokens in parallel; responsive tests in parallel; polish checks in parallel |
| **MVP scope** | User Stories 1 + 2 (Phases 3–4): Ruby background + accessible contrast |
| **Files modified** | 1 (`frontend/src/index.css`) |
| **Suggested MVP estimate** | ~15 minutes (4 token changes + visual verification) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- This feature is intentionally minimal: 4 CSS token updates + 2 fallback lines in a single file
- No new dependencies, no structural changes, no backend modifications
- The existing Tailwind + CSS custom property architecture handles propagation automatically
