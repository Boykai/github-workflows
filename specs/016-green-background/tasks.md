# Tasks: Add Green Background Color to App

**Input**: Design documents from `/specs/016-green-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md, contracts/no-api.md

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification. Visual/manual verification is sufficient per plan.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature only touches frontend CSS — no backend changes required

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No project initialization needed — this feature modifies a single existing file with zero new dependencies, zero new files, and zero configuration changes.

*(No setup tasks required — the existing project structure and theming system are already in place.)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The single CSS custom property change that enables all user stories. This MUST be complete before any story-level verification can proceed.

**⚠️ CRITICAL**: All user stories depend on this change being applied first.

- [X] T001 Update `--background` CSS custom property in `:root` block from `0 0% 100%` (white) to `122 39% 49%` (green, #4CAF50) in frontend/src/index.css

**Checkpoint**: Green background is now applied globally via the existing `bg-background` Tailwind utility on `body`, root `<div>`, and header in `App.tsx`. All user story verification can begin.

---

## Phase 3: User Story 1 — See Green Background Across All Pages (Priority: P1) 🎯 MVP

**Goal**: User opens the application and immediately sees a green background color applied consistently across every page, route, and view with no flash of white during load or navigation.

**Independent Test**: Open every page/route (Home `/`, Board `/#board`, Settings `/#settings`) and visually confirm the green background is present. Navigate between pages and verify no flash of white during transitions.

### Implementation for User Story 1

- [X] T002 [US1] Verify green background renders on Home page (`/`) by running the frontend dev server (`cd frontend && npm run dev`) and visually inspecting `http://localhost:5173/`
- [ ] T003 [US1] Verify green background renders on Board page (`/#board`) and Settings page (`/#settings`) via visual inspection
- [ ] T004 [US1] Verify no flash of white or default background on initial cold-start page load and on route transitions between pages

**Checkpoint**: User Story 1 is complete — green background is visible on all pages with no flash of unstyled background.

---

## Phase 4: User Story 2 — Read All Content Clearly on Green Background (Priority: P1)

**Goal**: All text, icons, and interactive elements maintain sufficient visual contrast against the green background so that content is clearly legible (WCAG AA compliance).

**Independent Test**: Review every page for text and icon readability against the green background. Confirm the existing `--foreground` value (`222.2 84% 4.9%`, dark navy) provides ≥4.5:1 contrast ratio against `#4CAF50` (research.md confirms ~8.6:1).

### Implementation for User Story 2

- [X] T005 [US2] Confirm existing `--foreground` value in `:root` block of frontend/src/index.css provides WCAG AA contrast (≥4.5:1 for normal text, ≥3:1 for large text) against the new green `--background` value — no change expected per research.md R1
- [ ] T006 [US2] Visually audit all pages for any text, icons, or UI elements with hardcoded colors that may have poor contrast against the green background

**Checkpoint**: User Story 2 is complete — all content is clearly readable on the green background with WCAG AA contrast compliance.

---

## Phase 5: User Story 3 — Interact with Overlays Without Green Bleed-Through (Priority: P2)

**Goal**: Modals, dropdowns, tooltips, and drawers retain their own intended background colors and are not unintentionally overridden by the global green background.

**Independent Test**: Open each type of overlay component (modals, dropdowns, tooltips, drawers) on top of the green background and verify each retains its intended white/card background color.

### Implementation for User Story 3

- [X] T007 [US3] Verify that `--popover` and `--card` CSS custom properties in frontend/src/index.css remain independently defined and unchanged (currently `0 0% 100%` in `:root`) — no modification needed per research.md R4
- [ ] T008 [US3] Visually verify modals (e.g., issue detail modal), dropdowns, tooltips, and drawer/panel components retain their own background colors when opened over the green background

**Checkpoint**: User Story 3 is complete — overlay components are visually distinct from the green page background.

---

## Phase 6: User Story 4 — Consistent Appearance Across Browsers and Display Modes (Priority: P3)

**Goal**: The green background renders consistently across Chrome, Firefox, Safari, and Edge, and in both light and dark OS display modes.

**Independent Test**: Load the application in each major browser and toggle between light/dark OS modes, confirming the green background appears the same in light mode and dark mode retains its dark background.

### Implementation for User Story 4

- [ ] T009 [US4] Verify green background renders identically in Chrome, Firefox, Safari, and Edge browsers
- [X] T010 [US4] Verify dark mode toggle (☀️/🌙) switches to dark background (unchanged `--background: 222.2 84% 4.9%` in `.dark` block) and back to green in light mode — no modification needed per research.md R3
- [ ] T011 [US4] Verify OS light/dark mode switching does not override the green background in light mode

**Checkpoint**: User Story 4 is complete — green background is consistent across browsers and display modes.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and build validation

- [X] T012 Run frontend build verification (`cd frontend && npm run build`) to confirm no build errors from the CSS change
- [X] T013 Run frontend lint check (`cd frontend && npm run lint`) to confirm no lint errors
- [X] T014 Run frontend tests (`cd frontend && npm test`) to confirm no test regressions
- [ ] T015 Run quickstart.md verification checklist (visual verification, overlay verification, contrast verification, build verification)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks needed — existing infrastructure is sufficient
- **Foundational (Phase 2)**: No dependencies — single CSS variable change (T001)
- **User Stories (Phases 3–6)**: All depend on T001 (Foundational) being applied first
  - User stories are verification-focused and can proceed in priority order
- **Polish (Phase 7)**: Depends on T001 being applied; can run after Foundational

### User Story Dependencies

- **User Story 1 (P1)**: Depends on T001 — verify green background across all pages
- **User Story 2 (P1)**: Depends on T001 — verify contrast and readability
- **User Story 3 (P2)**: Depends on T001 — verify overlay isolation
- **User Story 4 (P3)**: Depends on T001 — verify cross-browser consistency

### Within Each User Story

- All verification tasks can proceed after T001 is complete
- No inter-story dependencies — each story is independently testable

### Parallel Opportunities

- T002, T003, T004 (US1 verification) can run in parallel after T001
- T005, T006 (US2 verification) can run in parallel after T001
- T007, T008 (US3 verification) can run in parallel after T001
- T009, T010, T011 (US4 verification) can run in parallel after T001
- T012, T013, T014 (build/lint/test) can run in parallel after T001
- All user story phases can be verified in parallel after T001

---

## Parallel Example: All User Stories

```bash
# After T001 (Foundational) is applied, ALL verification can run in parallel:

# User Story 1 — Visual page verification:
Task: "Verify green background on Home page"
Task: "Verify green background on Board and Settings pages"
Task: "Verify no flash of white on load/transitions"

# User Story 2 — Contrast verification:
Task: "Confirm --foreground contrast ratio against green"
Task: "Audit pages for hardcoded color conflicts"

# User Story 3 — Overlay verification:
Task: "Verify --popover and --card tokens unchanged"
Task: "Visually verify overlays retain own backgrounds"

# User Story 4 — Browser/mode verification:
Task: "Verify in Chrome, Firefox, Safari, Edge"
Task: "Verify dark mode toggle behavior"
Task: "Verify OS display mode switching"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001 — single CSS variable change)
2. Complete Phase 3: User Story 1 (verify green on all pages)
3. **STOP and VALIDATE**: Green background is visible everywhere, no flash
4. Deploy/demo if ready — this delivers the core feature

### Incremental Delivery

1. Apply T001 → Green background is live (Foundational)
2. Verify US1 → Green on all pages → Deploy/Demo (MVP!)
3. Verify US2 → Contrast and readability confirmed
4. Verify US3 → Overlays work correctly
5. Verify US4 → Cross-browser consistency confirmed
6. Run Polish phase → Build/lint/test validation

### Single Developer Strategy

This is an XS-sized feature (estimated 30 minutes). A single developer can:
1. Apply T001 (the only code change)
2. Run through all verification tasks sequentially
3. Run build/lint/test
4. Complete in a single session

---

## Notes

- This feature involves exactly **1 code change** (T001) and **14 verification tasks** (T002–T015)
- The CSS custom property system propagates the color automatically — no component-level changes needed
- Dark mode is intentionally left unchanged (dark navy background per research.md R3)
- Overlay components are already isolated by the design token system (research.md R4)
- No flash prevention is handled by Vite's synchronous CSS injection (research.md R5)
- Rollback: Change `--background` back to `0 0% 100%` in `frontend/src/index.css`
