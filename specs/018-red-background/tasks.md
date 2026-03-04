# Tasks: Add Red Background Color to App

**Input**: Design documents from `/specs/018-red-background/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted per Test Optionality principle.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Primary change target: `frontend/src/index.css`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing theme infrastructure and establish baseline

- [x] T001 Verify current CSS variable structure in frontend/src/index.css confirming :root and .dark blocks exist with --background and --foreground tokens
- [x] T002 Verify Tailwind config maps CSS variables correctly in frontend/tailwind.config.js confirming bg-background and text-foreground utility classes reference hsl(var(--background)) and hsl(var(--foreground))
- [x] T003 [P] Verify ThemeProvider component in frontend/src/components/ThemeProvider.tsx confirms .dark class toggle on html element for light/dark/system mode switching

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm baseline build and existing theme system works before making changes

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Run frontend build (npm run build in frontend/) to confirm clean baseline with no pre-existing errors
- [x] T005 Run existing frontend tests (npm run test in frontend/) to establish baseline test pass rate
- [x] T006 [P] Document current --background and --foreground HSL values in both :root and .dark blocks of frontend/src/index.css for rollback reference

**Checkpoint**: Baseline confirmed — theme system is intact and build passes. User story implementation can begin.

---

## Phase 3: User Story 1 — Global Red Background Applied (Priority: P1) 🎯 MVP

**Goal**: Apply Material Red 700 (#D32F2F) background globally to all pages via the --background CSS variable in light mode

**Independent Test**: Open the application in a browser and verify every page/view displays a red background. Navigate between routes to confirm consistency.

### Implementation for User Story 1

- [x] T007 [US1] Update --background value from `0 0% 100%` to `0 70% 50%` in the :root block of frontend/src/index.css
- [x] T008 [US1] Verify the body element styling in frontend/src/index.css applies bg-background and text-foreground classes (via @apply or @layer base) ensuring the updated --background value cascades globally
- [x] T009 [US1] Run frontend dev server (npm run dev in frontend/) and visually verify red background appears on all pages and routes in light mode

**Checkpoint**: Light mode displays red background (#D32F2F) on all pages. Core requirement of the feature is delivered.

---

## Phase 4: User Story 2 — Accessibility and Readability Maintained (Priority: P1)

**Goal**: Ensure all text and UI elements remain readable against the red background by updating --foreground to white (#FFFFFF) for WCAG 2.1 AA compliance

**Independent Test**: Inspect text contrast against the red background — verify white text on #D32F2F yields ≥4.5:1 contrast ratio. Check that buttons, inputs, modals, and cards remain visually distinct.

### Implementation for User Story 2

- [x] T010 [US2] Update --foreground value from `222.2 84% 4.9%` to `0 0% 100%` in the :root block of frontend/src/index.css
- [x] T011 [US2] Visually verify all text elements are readable (white on red) across all pages with frontend dev server running
- [x] T012 [P] [US2] Verify card, popover, modal, and input components retain their own background colors (--card, --popover, etc. tokens unchanged) in frontend/src/index.css
- [x] T013 [US2] Verify buttons, links, and interactive elements remain visually distinct and usable against the red background

**Checkpoint**: All text meets WCAG 2.1 AA contrast (4.68:1 for light mode). Components with explicit backgrounds are unaffected.

---

## Phase 5: User Story 3 — Theme System Integration (Priority: P2)

**Goal**: Ensure the red background adapts correctly for dark mode by updating the .dark block CSS variables, maintaining theme consistency across light/dark/system modes

**Independent Test**: Toggle between light, dark, and system theme modes. Verify dark mode uses a deeper red (#B71C1C) and light mode uses the brighter red (#D32F2F). Confirm theme switching works without page reload.

### Implementation for User Story 3

- [x] T014 [US3] Update --background value from `222.2 84% 4.9%` to `0 73% 41%` in the .dark block of frontend/src/index.css
- [x] T015 [US3] Update --foreground value from `210 40% 98%` to `0 0% 100%` in the .dark block of frontend/src/index.css
- [x] T016 [US3] Visually verify dark mode displays deeper red background (#B71C1C) with white text by toggling theme in the running application
- [x] T017 [US3] Verify system theme preference correctly selects the appropriate red shade based on OS dark/light mode setting

**Checkpoint**: All three theme modes (light, dark, system) display correct red background variants. Theme switching works seamlessly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification across all user stories and production readiness

- [x] T018 Run full frontend test suite (npm run test in frontend/) to confirm no regressions from CSS variable changes
- [x] T019 Run production build (npm run build in frontend/) to verify successful build with updated styles
- [x] T020 [P] Verify no layout, spacing, or component rendering regressions across all pages by visual inspection
- [x] T021 [P] Verify contrast ratios: light mode #D32F2F + #FFFFFF = 4.68:1 ✅ and dark mode #B71C1C + #FFFFFF = 6.27:1 ✅
- [x] T022 Run quickstart.md verification checklist against the running application in frontend/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — core background change
- **User Story 2 (Phase 4)**: Depends on User Story 1 — foreground contrast requires background to be red first
- **User Story 3 (Phase 5)**: Depends on Foundational — can proceed in parallel with US1+US2 (different CSS block: .dark vs :root)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — modifies :root --background only
- **User Story 2 (P1)**: Logically follows US1 — modifies :root --foreground; verification requires red background to be in place
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — modifies .dark block independently of :root changes

### Within Each User Story

- CSS variable update before visual verification
- Visual verification before checkpoint sign-off
- All changes in single file: `frontend/src/index.css`

### Parallel Opportunities

- T002 and T003 in Setup can run in parallel (different files)
- T005 and T006 in Foundational can run in parallel
- US3 (.dark block) can be implemented in parallel with US1+US2 (:root block) — different CSS blocks in the same file
- T012 can run in parallel with T011 and T013 (read-only verification vs active testing)
- T020 and T021 in Polish can run in parallel (independent verification tasks)

---

## Parallel Example: User Story 1 + User Story 3

```text
# Since US1 modifies :root and US3 modifies .dark, they can be worked in parallel:

# Developer A (User Story 1 - :root block):
Task T007: Update --background in :root to 0 70% 50% in frontend/src/index.css
Task T008: Verify bg-background class on body in frontend/src/index.css

# Developer B (User Story 3 - .dark block):
Task T014: Update --background in .dark to 0 73% 41% in frontend/src/index.css
Task T015: Update --foreground in .dark to 0 0% 100% in frontend/src/index.css
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify theme infrastructure)
2. Complete Phase 2: Foundational (confirm baseline build)
3. Complete Phase 3: User Story 1 (red background in light mode)
4. **STOP and VALIDATE**: Verify red background appears on all pages
5. This alone delivers the core "add red background" request

### Incremental Delivery

1. Setup + Foundational → Infrastructure verified
2. Add User Story 1 → Red background visible (MVP! ✅)
3. Add User Story 2 → Text readable, WCAG compliant
4. Add User Story 3 → Dark mode support complete
5. Polish → Production-ready, all verifications pass

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + User Story 2 (:root block changes + verification)
   - Developer B: User Story 3 (.dark block changes + verification)
3. Both converge at Polish phase for cross-cutting verification

---

## Notes

- All implementation tasks modify a single file: `frontend/src/index.css`
- CSS variable values use HSL space-separated format (e.g., `0 70% 50%`) — no commas
- The Tailwind + CSS variable architecture means changing tokens propagates globally with zero component changes
- Component-level tokens (--card, --popover, etc.) are intentionally NOT modified
- Rollback is trivial: restore original HSL values documented in T006
- Total: 22 tasks across 6 phases
