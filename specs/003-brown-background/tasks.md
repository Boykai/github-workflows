# Tasks: Brown Background Color

**Input**: Design documents from `/specs/003-brown-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No test tasks included. The spec and plan confirm no new tests are required — this is a CSS variable value change with no component logic modifications. Existing tests should continue to pass. Verification is manual + accessibility audit tools.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for all CSS changes
- All color changes centralized in `frontend/src/index.css` per FR-009
- Selective hardcoded color updates in `frontend/src/App.css`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify current baseline and confirm existing theming infrastructure

- [ ] T001 Verify current CSS custom properties in `frontend/src/index.css` match expected baseline (`:root` and `html.dark-mode-active` blocks contain `--color-bg`, `--color-bg-secondary`, `--color-border`, `--color-text`, `--color-text-secondary`, `--shadow`)
- [ ] T002 Verify existing dark mode toggle mechanism works (confirm `useAppTheme` hook in `frontend/src/hooks/useAppTheme.ts` toggles `dark-mode-active` class on `<html>`)
- [ ] T003 Run existing frontend build (`cd frontend && npm install && npm run build`) to confirm clean baseline with no pre-existing errors

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking prerequisites exist for this feature. All changes are CSS custom property value updates in existing files. The theming infrastructure (CSS variables, dark mode toggle) is already in place.

**⚠️ NOTE**: This phase is intentionally empty. The existing CSS variable theming system is the foundation, and it requires no modifications — only value changes in subsequent phases.

**Checkpoint**: Foundation confirmed ready — user story implementation can begin

---

## Phase 3: User Story 1 - Consistent Brown Background Across All Screens (Priority: P1) 🎯 MVP

**Goal**: Apply brown background color (#8B5C2B) to all main screens by updating CSS custom properties in the `:root` block of `frontend/src/index.css`. All text must maintain WCAG AA contrast ratio against the brown background.

**Independent Test**: Open the app in a browser, navigate through all screens (home, project board, sidebar, settings), and verify the background is consistently brown (#8B5C2B). Confirm white text (#FFFFFF) is clearly readable. Run Lighthouse accessibility audit to verify no contrast violations. Resize browser to mobile/tablet/desktop viewports and confirm brown background fills the entire viewport without gaps.

### Implementation for User Story 1

- [ ] T004 [US1] Update light mode CSS custom properties in `:root` block of `frontend/src/index.css`: change `--color-bg` from `#ffffff` to `#8B5C2B`, change `--color-bg-secondary` from `#f6f8fa` to `#7A4F24`, change `--color-text` from `#24292f` to `#FFFFFF`, change `--color-text-secondary` from `#57606a` to `#E8D5B5`, change `--color-border` from `#d0d7de` to `#A67B4A`, change `--shadow` from `rgba(0, 0, 0, 0.1)` to `rgba(0, 0, 0, 0.2)`
- [ ] T005 [US1] Add hardcoded fallback color for body background in `frontend/src/index.css`: add `background: #8B5C2B;` line before existing `background: var(--color-bg-secondary);` in the `body` rule to support browsers without CSS custom property support (FR-006)
- [ ] T006 [US1] Add print media query at the end of `frontend/src/index.css`: add `@media print { body { background: #ffffff !important; color: #000000 !important; } }` to override brown background for print (edge case from spec)
- [ ] T007 [US1] Build frontend (`cd frontend && npm run build`) and verify no CSS syntax errors or build failures introduced by the color changes

**Checkpoint**: At this point, the app should display a brown background on all main screens in light mode. All text should be white and readable. The brown background should be responsive across all device sizes. Print preview should show white background. This is the MVP — the core user request is fulfilled.

---

## Phase 4: User Story 2 - Brown Background on Overlays and Navigation (Priority: P2)

**Goal**: Ensure modals, pop-ups, sidebars, navigation bars, and overlay components display brown backgrounds consistent with the main theme. Since these components already use CSS variables (`var(--color-bg)`, `var(--color-bg-secondary)`), they automatically inherit the brown values from US1. This phase focuses on hardcoded colors that may clash with the brown theme.

**Independent Test**: Open any modal or dialog in the app, open the sidebar navigation, and trigger any overlay/pop-up. Verify that all backgrounds harmonize with the brown theme. Confirm no visual clashing between overlay backgrounds and main content.

### Implementation for User Story 2

- [ ] T008 [US2] Update login button hover color in `frontend/src/App.css`: change `.login-button:hover` background from `#32383f` to `#5A3D25` to harmonize with brown theme
- [ ] T009 [US2] Update task highlight animation in `frontend/src/App.css`: change `@keyframes highlightTask` initial background-color from `#dafbe1` to `#C4956A` to harmonize with brown theme
- [ ] T010 [US2] Visually verify that modals, sidebar, navigation bars, and overlay components inherit brown background from CSS variables — no additional code changes needed for components using `var(--color-bg)` and `var(--color-bg-secondary)`

**Checkpoint**: At this point, all overlays, modals, navigation panels, and interactive components should display brown backgrounds consistent with the main app theme. No visual clashing between overlay and main content backgrounds.

---

## Phase 5: User Story 3 - Dark Mode Brown Variant (Priority: P3)

**Goal**: Apply a darker brown variant (#2C1A0E) to dark mode by updating CSS custom properties in the `html.dark-mode-active` block of `frontend/src/index.css`. Existing dark mode text colors already meet WCAG AA contrast against the dark brown background.

**Independent Test**: Toggle dark mode on using the app's theme toggle. Verify the background changes to a dark brown (#2C1A0E) instead of the previous dark gray (#0d1117). Confirm text remains readable. Toggle back to light mode and verify the light brown returns. Confirm smooth transition between modes with no visual glitches.

### Implementation for User Story 3

- [ ] T011 [US3] Update dark mode CSS custom properties in `html.dark-mode-active` block of `frontend/src/index.css`: change `--color-bg` from `#0d1117` to `#2C1A0E`, change `--color-bg-secondary` from `#161b22` to `#3D2817`, change `--color-border` from `#30363d` to `#5A3D25`
- [ ] T012 [US3] Verify dark mode text colors (`--color-text: #e6edf3` and `--color-text-secondary: #8b949e`) remain unchanged — they already meet WCAG AA contrast against the dark brown background (#2C1A0E yields ~12.5:1 ratio)
- [ ] T013 [US3] Build frontend (`cd frontend && npm run build`) and verify no errors; test dark mode toggle to confirm smooth transition between light brown and dark brown variants

**Checkpoint**: All three user stories should now be fully functional. Light mode shows brown (#8B5C2B), dark mode shows dark brown (#2C1A0E), toggle works smoothly, and all components inherit the theme.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all user stories

- [ ] T014 Run full frontend test suite (`cd frontend && npm test`) to verify no regressions from CSS changes
- [ ] T015 Run Lighthouse or axe accessibility audit to verify WCAG AA contrast compliance for all text-on-background combinations (FR-002, SC-002)
- [ ] T016 Visual regression check across 5 screen sizes: mobile portrait (375px), mobile landscape (667px), tablet (768px), laptop (1024px), desktop (1440px) — verify brown background fills viewport without gaps or artifacts (FR-004, SC-003)
- [ ] T017 Verify centralized color definition: confirm all brown color changes exist only in `frontend/src/index.css` (primary) and `frontend/src/App.css` (hardcoded overrides) — future color adjustment requires modifying no more than one file for theme colors (FR-009, SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — confirms existing infrastructure is ready (empty phase)
- **User Story 1 (Phase 3)**: Depends on Setup — core brown background in light mode
- **User Story 2 (Phase 4)**: Depends on User Story 1 — hardcoded color harmonization relies on brown theme being active
- **User Story 3 (Phase 5)**: Can start after Setup — dark mode changes are independent of light mode changes in US1, but logically follows US1 for implementation consistency
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No dependencies on other stories. Delivers full MVP.
- **User Story 2 (P2)**: Depends on US1 being complete — hardcoded color adjustments are meant to harmonize with the brown background established in US1. However, US2 changes are in a different file (`App.css`) and can technically be done in parallel.
- **User Story 3 (P3)**: Can start after Setup (Phase 1) — dark mode block is independent of light mode block. No dependencies on US1 or US2. Can proceed in parallel with US1 if desired.

### Within Each User Story

- CSS variable updates before visual verification
- Build verification after CSS changes
- No test-first approach — CSS value changes verified visually and with accessibility tools

### Parallel Opportunities

- T004, T005, T006 are sequential within US1 (same file: `frontend/src/index.css`)
- T008 and T009 can run in parallel within US2 (different CSS rules in `App.css`)
- US1 (Phase 3) and US3 (Phase 5) can be implemented in parallel — they modify different blocks (`:root` vs `html.dark-mode-active`) in the same file, but the changes are non-overlapping
- T014, T015, T016, T017 in Phase 6 can all run in parallel — they are independent verification tasks

---

## Parallel Example: User Story 1

```bash
# US1 tasks are sequential (same file, same block):
Task T004: "Update light mode CSS custom properties in frontend/src/index.css"
Task T005: "Add hardcoded fallback color in frontend/src/index.css body rule"
Task T006: "Add print media query at end of frontend/src/index.css"
Task T007: "Build frontend and verify no errors"
```

## Parallel Example: User Story 2

```bash
# US2 tasks can run in parallel (different CSS rules):
Task T008: "Update login button hover in frontend/src/App.css"
Task T009: "Update task highlight animation in frontend/src/App.css"
# Then verify:
Task T010: "Visual verification of overlays and modals"
```

## Parallel Example: Cross-Story

```bash
# These user stories can be implemented in parallel by different developers:
Developer A: US1 (Phase 3) — Light mode brown background in index.css :root block
Developer B: US3 (Phase 5) — Dark mode brown variant in index.css html.dark-mode-active block
# US2 follows after US1 completes (different file: App.css)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify baseline)
2. Phase 2: Foundational (confirmed — no blocking work needed)
3. Complete Phase 3: User Story 1 (brown background on all screens)
4. **STOP and VALIDATE**: Open app, verify brown background, check text contrast
5. Deploy/demo if ready — core user request fulfilled

### Incremental Delivery

1. Complete Setup → Baseline confirmed
2. Add User Story 1 → Brown background on all screens → Validate → Deploy/Demo (MVP!)
3. Add User Story 2 → Overlays and hardcoded colors harmonized → Validate → Deploy/Demo
4. Add User Story 3 → Dark mode brown variant → Validate → Deploy/Demo
5. Polish → Accessibility audit, responsive check, centralization verification
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team confirms Setup (Phase 1) together
2. Once baseline verified:
   - Developer A: User Story 1 (light mode — `:root` in `index.css`)
   - Developer B: User Story 3 (dark mode — `html.dark-mode-active` in `index.css`)
3. After US1 completes:
   - Developer A or C: User Story 2 (hardcoded colors in `App.css`)
4. All developers: Phase 6 Polish (parallel verification tasks)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 17 |
| **User Story 1 (P1) Tasks** | 4 (T004–T007) |
| **User Story 2 (P2) Tasks** | 3 (T008–T010) |
| **User Story 3 (P3) Tasks** | 3 (T011–T013) |
| **Setup Tasks** | 3 (T001–T003) |
| **Polish Tasks** | 4 (T014–T017) |
| **Parallel Opportunities** | US1 ∥ US3 (different CSS blocks); T008 ∥ T009 (different rules); T014–T017 (independent verification) |
| **Files Modified** | 2 (`frontend/src/index.css`, `frontend/src/App.css`) |
| **Suggested MVP Scope** | User Story 1 only (4 tasks, ~10 minutes) |
| **Format Validation** | ✅ All tasks follow `- [ ] [TaskID] [Story?] Description with file path` format |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No new test files needed — CSS value changes only
- Commit after each phase or logical group
- Stop at any checkpoint to validate story independently
- All color values pre-validated for WCAG AA contrast (see data-model.md contrast table)
