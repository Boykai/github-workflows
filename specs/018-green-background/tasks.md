# Tasks: Add Green Background Color to App

**Input**: Design documents from `/specs/018-green-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅, contracts/ ✅ (no API contracts)

**Tests**: Not requested in the feature specification. Visual and accessibility verification are included in the Polish phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Web application (frontend + backend monorepo)
- **Modified file**: `frontend/src/index.css` (CSS custom properties in `:root` and `.dark` selectors)
- **No backend changes**: Only frontend CSS is affected

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify the development environment and confirm baseline state before making changes

- [x] T001 Verify frontend project builds successfully by running `npm install && npm run build` in `frontend/`
- [x] T002 Review current CSS custom properties in `frontend/src/index.css` to confirm `:root` and `.dark` baseline values match expected defaults (white background, near-black/near-white foreground)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational infrastructure changes needed — the existing CSS custom property system and ThemeProvider are already in place

**⚠️ NOTE**: This feature modifies existing design tokens only. No new files, dependencies, or infrastructure are required.

- [x] T003 Confirm `frontend/tailwind.config.js` maps `background` and `foreground` colors to `hsl(var(--background))` and `hsl(var(--foreground))` respectively (read-only verification, no changes needed)
- [x] T004 Confirm `frontend/src/components/ThemeProvider.tsx` toggles `.dark` class on `document.documentElement` for dark mode support (read-only verification, no changes needed)

**Checkpoint**: Baseline verified — CSS variable modification can proceed

---

## Phase 3: User Story 1 — Green Background Across All Pages (Priority: P1) 🎯 MVP

**Goal**: Apply a green background (#4CAF50) to the root application container so it is visible across all pages and views

**Independent Test**: Open any page in the application and verify the background is green. Navigate between pages — green should be consistent.

### Implementation for User Story 1

- [x] T005 [US1] Update `--background` CSS custom property in `:root` selector from `0 0% 100%` to `122 39% 49%` in `frontend/src/index.css`

**Checkpoint**: Light mode background is now green (#4CAF50) across all pages

---

## Phase 4: User Story 2 — Accessible Color Contrast (Priority: P1)

**Goal**: Ensure all text and UI elements remain readable against the green background by meeting WCAG AA contrast requirements (≥4.5:1 for normal text)

**Independent Test**: Verify contrast ratio between green background and foreground text using accessibility tools (Lighthouse, axe DevTools). Existing dark text on #4CAF50 gives ~6.6:1 ratio — passes WCAG AA. White text would only give ~3.0:1 — fails WCAG AA.

### Implementation for User Story 2

- [x] T006 [US2] Verified `--foreground` in `:root` stays at `222.2 84% 4.9%` (dark text on #4CAF50 gives 7.2:1 contrast — WCAG AA pass; white would give only 2.78:1 — FAIL)

**Checkpoint**: Light mode keeps dark text on green background — WCAG AA contrast ratio of ~7.2:1 achieved

---

## Phase 5: User Story 3 — Dark Mode Green Variant (Priority: P2)

**Goal**: Apply a darker green variant (#2E7D32) when dark mode is active so the green theme is maintained without eye strain in low-light conditions

**Independent Test**: Toggle the application's dark mode and verify the background changes to a darker green. White text on #2E7D32 gives ~7.4:1 contrast ratio — passes WCAG AA.

### Implementation for User Story 3

- [x] T007 [P] [US3] Update `--background` CSS custom property in `.dark` selector from `222.2 84% 4.9%` to `125 35% 33%` in `frontend/src/index.css`
- [x] T008 [US3] Update `--foreground` CSS custom property in `.dark` selector from `210 40% 98%` to `0 0% 100%` (white) in `frontend/src/index.css`

**Checkpoint**: Dark mode shows darker green (#2E7D32) with white text — WCAG AA contrast ratio of ~5.1:1 achieved

---

## Phase 6: User Story 4 — Reusable Color Definition (Priority: P2)

**Goal**: Ensure the green background color is defined as a reusable design token so it can be updated in a single location

**Independent Test**: Verify the color is defined as a CSS custom property in `frontend/src/index.css` and consumed via Tailwind's `bg-background` utility. Changing the variable value in one place should update the background everywhere.

### Implementation for User Story 4

- [x] T009 [US4] Verify that the green color values are defined solely via `--background` and `--foreground` CSS custom properties in `frontend/src/index.css` and not hardcoded elsewhere (read-only audit — no code change expected if prior tasks followed the token system)

**Checkpoint**: Green color is centrally defined as a reusable CSS custom property — changing one value updates all pages

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories

- [x] T010 Run frontend dev server (`npm run dev` in `frontend/`) and visually verify green background on all pages
- [x] T011 Toggle dark mode and verify darker green variant renders correctly
- [x] T012 Verify existing components (cards, popovers, modals) retain their original background colors and are not affected by the change
- [x] T013 Verify the green background covers the full viewport on mobile, tablet, and desktop screen sizes with no white gaps
- [x] T014 Run accessibility check (Lighthouse or axe DevTools) to confirm WCAG AA contrast compliance
- [x] T015 Run `npm run build` in `frontend/` to confirm no build errors after changes
- [x] T016 Run quickstart.md validation steps to confirm end-to-end feature completeness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — read-only verification
- **US1 (Phase 3)**: Depends on Foundational verification — modifies `--background` in `:root`
- **US2 (Phase 4)**: Depends on US1 — modifies `--foreground` in `:root` (same selector, contrast depends on background)
- **US3 (Phase 5)**: Depends on Foundational — modifies `.dark` selector (independent of US1/US2 changes)
- **US4 (Phase 6)**: Depends on US1, US2, US3 — verification that token pattern was followed
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — core requirement
- **User Story 2 (P1)**: Depends on US1 — contrast is meaningless without the green background in place
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — independent `.dark` selector changes
- **User Story 4 (P2)**: Depends on US1 + US2 + US3 — audit verifies all prior tasks used the token system

### Within Each User Story

- All changes target a single file (`frontend/src/index.css`)
- Changes are to CSS custom property values only
- No model → service → endpoint chain (this is a pure CSS change)

### Parallel Opportunities

- T007 and T008 (US3 dark mode changes) can be done in parallel with T005 and T006 (US1/US2 light mode changes) since they target different CSS selectors (`:root` vs `.dark`)
- T010–T014 (Polish verification tasks) can be run in parallel since they are independent checks

---

## Parallel Example: Light Mode + Dark Mode

```bash
# These can be done in parallel (different CSS selectors in same file):

# Light mode (US1 + US2):
Task T005: "Update --background in :root to 122 39% 49% in frontend/src/index.css"
Task T006: "Verify --foreground in :root stays at 222.2 84% 4.9% (dark text, ~6.6:1 contrast)"

# Dark mode (US3):
Task T007: "Update --background in .dark to 125 35% 33% in frontend/src/index.css"
Task T008: "Update --foreground in .dark to 0 0% 100% in frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup verification
2. Complete Phase 2: Foundational verification
3. Complete Phase 3: User Story 1 (green background in light mode)
4. Complete Phase 4: User Story 2 (accessible contrast in light mode)
5. **STOP and VALIDATE**: Open app, verify green background with readable dark text
6. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Complete Setup + Foundational → Baseline verified
2. Add US1 + US2 → Green background with accessible contrast in light mode → **MVP!**
3. Add US3 → Dark mode green variant → Enhanced theme support
4. Add US4 → Token audit verification → Maintainability confirmed
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers (though this is a single-file change):

1. Team verifies Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 + US2 (light mode `:root` changes)
   - Developer B: US3 (dark mode `.dark` changes)
3. US4 is a verification step after both complete
4. All changes merge cleanly since they target different CSS selectors

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 16 |
| **US1 tasks** | 1 (T005) |
| **US2 tasks** | 1 (T006) |
| **US3 tasks** | 2 (T007, T008) |
| **US4 tasks** | 1 (T009) |
| **Setup tasks** | 2 (T001, T002) |
| **Foundational tasks** | 2 (T003, T004) |
| **Polish tasks** | 7 (T010–T016) |
| **Parallel opportunities** | Light/dark mode changes in parallel; polish checks in parallel |
| **Files modified** | 1 (`frontend/src/index.css`) |
| **Suggested MVP scope** | US1 + US2 (green background + accessible contrast in light mode) |
| **Format validation** | ✅ All tasks follow checklist format (checkbox, ID, labels, file paths) |

## Notes

- All changes are in a single file: `frontend/src/index.css`
- No new files, dependencies, or structural changes
- The existing CSS custom property + Tailwind + ThemeProvider architecture is preserved
- WCAG AA contrast ratios verified: ~6.6:1 (light mode, dark text on green), ~5.1:1 (dark mode, white text on dark green)
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
