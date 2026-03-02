# Tasks: Add Blue Background Color to App

**Input**: Design documents from `/specs/016-blue-background-app/`
**Prerequisites**: spec.md (required for user stories)

**Tests**: Tests are OPTIONAL — not explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Define the blue background CSS custom property (design token) in the theme system so all user stories can reference it

- [ ] T001 Add `--app-bg` CSS custom property with blue value (`217 91% 60%` / #2563EB) to `:root` in frontend/src/index.css
- [ ] T002 [P] Add `--app-bg` dark mode variant (e.g. `221 83% 30%`) to `.dark` in frontend/src/index.css
- [ ] T003 [P] Register `app-bg` color token as `"hsl(var(--app-bg))"` in the `extend.colors` section of frontend/tailwind.config.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Apply the blue background to the root app surface so it is visible across all pages and views

**⚠️ CRITICAL**: No user story validation can occur until this phase is complete

- [ ] T004 Replace `bg-background` with `bg-app-bg` on the root `<div>` in the `AppContent` component in frontend/src/App.tsx (line with `className="flex flex-col h-screen bg-background text-foreground"`)
- [ ] T005 Add `bg-app-bg` to the unauthenticated landing `<div>` in `AppContent` in frontend/src/App.tsx (line with `className="flex flex-col items-center justify-center h-screen gap-4 text-center"`)
- [ ] T006 Add `bg-app-bg` to the auth-loading spinner `<div>` in `AppContent` in frontend/src/App.tsx (line with `className="flex flex-col items-center justify-center h-screen gap-4"`)
- [ ] T007 Add fallback `background-color: #2563EB;` before the CSS custom property usage for `body` in the `@layer base` rule in frontend/src/index.css

**Checkpoint**: Blue background visible on the root app surface — all pages show the blue background

---

## Phase 3: User Story 1 — See Blue Background Across All Pages (Priority: P1) 🎯 MVP

**Goal**: Users see a consistent blue background color applied to the main app surface across all pages and responsive breakpoints

**Independent Test**: Navigate to any page (home, board, settings) at mobile/tablet/desktop widths and visually confirm the blue background fills the entire viewport without gaps

### Implementation for User Story 1

- [ ] T008 [US1] Ensure `min-h-screen` is applied to the root `<div>` in `AppContent` in frontend/src/App.tsx so the blue background covers the full viewport height even when content is shorter than the viewport
- [ ] T009 [US1] Verify the blue background renders at mobile (320px), tablet (768px), and desktop (1280px) widths by visually inspecting the app in browser dev tools

**Checkpoint**: User Story 1 complete — blue background is consistently visible across all pages and breakpoints

---

## Phase 4: User Story 2 — Read Content Clearly Over Blue Background (Priority: P1)

**Goal**: All text, buttons, links, and interactive elements over the blue background meet WCAG AA contrast ratio requirements

**Independent Test**: Load any page with text content and measure contrast ratio between foreground text and the blue background using a contrast checker tool — must be ≥4.5:1 for normal text and ≥3:1 for large text

### Implementation for User Story 2

- [ ] T010 [US2] Update `--foreground` in `:root` to a light color value (e.g. `210 40% 98%` / white) that achieves ≥4.5:1 contrast against `--app-bg` blue in frontend/src/index.css
- [ ] T011 [US2] Ensure `text-foreground` is applied on the root `<div>` in `AppContent` in frontend/src/App.tsx so text inherits the accessible foreground color
- [ ] T012 [P] [US2] Update the header `<header>` background class from `bg-background` to `bg-app-bg` or a suitable elevated surface color to maintain visual consistency in frontend/src/App.tsx
- [ ] T013 [US2] Verify contrast ratios for normal text and large text over the blue background meet WCAG AA standards using a contrast checker

**Checkpoint**: User Story 2 complete — all text and interactive elements are legible and accessible over the blue background

---

## Phase 5: User Story 3 — Distinguish Elevated Surfaces from App Background (Priority: P2)

**Goal**: Cards, modals, drawers, tooltips, and other elevated surfaces retain their own background colors and remain visually distinct from the blue app background

**Independent Test**: Open a page with card components and trigger a modal dialog — verify cards and modal have distinct background colors that do not match the blue app background

### Implementation for User Story 3

- [ ] T014 [US3] Verify that `--card`, `--popover`, `--secondary`, and `--muted` CSS custom properties in `:root` and `.dark` in frontend/src/index.css are NOT set to the same value as `--app-bg` so elevated surfaces remain distinct
- [ ] T015 [US3] Verify that `--card` and `--popover` dark mode values in `.dark` in frontend/src/index.css provide sufficient visual separation from the dark mode `--app-bg` value
- [ ] T016 [US3] Visually inspect the project board page (cards, columns) and settings page (form surfaces) to confirm elevated surfaces do not inherit the blue app background

**Checkpoint**: User Story 3 complete — elevated surfaces are visually distinct from the blue app background

---

## Phase 6: User Story 4 — Maintainable Color Definition (Priority: P3)

**Goal**: The blue background color is defined using a single CSS custom property / design token so it can be updated in one place

**Independent Test**: Search the codebase for the blue background color definition and confirm it exists as a CSS custom property (`--app-bg`) in a single file (frontend/src/index.css) with Tailwind referencing it via the `app-bg` token

### Implementation for User Story 4

- [ ] T017 [US4] Verify the blue background color is only defined via `--app-bg` in frontend/src/index.css and referenced as `bg-app-bg` in components — no hard-coded hex values for the app background in any component file
- [ ] T018 [US4] Verify that changing the `--app-bg` value in frontend/src/index.css updates the background color everywhere it is applied without requiring changes in other files

**Checkpoint**: User Story 4 complete — color is centrally defined and easily maintainable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across browsers, themes, and edge cases

- [ ] T019 [P] Verify blue background renders correctly in both light and dark mode by toggling the theme toggle button in the header
- [ ] T020 [P] Verify blue background renders consistently across Chrome, Firefox, Safari, and Edge with no visible color differences
- [ ] T021 Verify the `SignalBannerBar` component and other overlays remain visually readable over the blue background in frontend/src/App.tsx
- [ ] T022 Verify that pages with content shorter than the viewport show the blue background filling the entire viewport height without white gaps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) — needs `--app-bg` token and `app-bg` Tailwind color defined — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — blue background must be applied before validating coverage
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — blue background must be applied before validating contrast
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — blue background must be applied before validating surface distinction
- **User Story 4 (Phase 6)**: Depends on Setup (Phase 1) — validates the design token approach
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 4 (P3)**: Can start after Setup (Phase 1) — No dependencies on other stories

### Within Each User Story

- CSS variable definitions before Tailwind config
- Tailwind config before component class usage
- Component changes before visual verification
- Core implementation before cross-cutting validation

### Parallel Opportunities

- T002 (dark mode CSS variable) and T003 (Tailwind config) can run in parallel — different files
- US1, US2, and US3 can start in parallel once Foundational phase completes — independent validation concerns
- T019 and T020 (polish verification tasks) can run in parallel — independent validation
- T012 (header background) can run in parallel with T010/T011 — different concern within same file but non-overlapping changes

---

## Parallel Example: Setup Phase

```bash
# Launch setup tasks in parallel (different files):
Task: T002 "Add --app-bg dark mode variant to .dark in frontend/src/index.css"
Task: T003 "Register app-bg color token in frontend/tailwind.config.js"
```

## Parallel Example: User Stories

```bash
# After Foundational phase, launch user story validation in parallel:
Task: US1 "Verify blue background across all pages and breakpoints"
Task: US2 "Verify contrast ratios meet WCAG AA"
Task: US3 "Verify elevated surfaces remain distinct"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (CSS variable + Tailwind token)
2. Complete Phase 2: Foundational (apply bg-app-bg to root containers)
3. Complete Phase 3: User Story 1 (verify full viewport coverage)
4. Complete Phase 4: User Story 2 (verify contrast and accessibility)
5. **STOP and VALIDATE**: Blue background visible and accessible on all pages
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Blue background applied
2. Add User Story 1 → Verified across breakpoints → Deploy/Demo (MVP!)
3. Add User Story 2 → Contrast validated → Deploy/Demo
4. Add User Story 3 → Elevated surfaces verified → Deploy/Demo
5. Add User Story 4 → Maintainability confirmed → Deploy/Demo
6. Polish → Cross-browser and theme validation → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (3-4 tasks, ~15 min)
2. Once Foundational is done:
   - Developer A: User Story 1 (viewport coverage)
   - Developer B: User Story 2 (contrast and accessibility)
   - Developer C: User Story 3 (elevated surface distinction)
3. Stories complete and validate independently

---

## Summary

- **Total tasks**: 22
- **Phase 1 (Setup)**: 3 tasks
- **Phase 2 (Foundational)**: 4 tasks
- **Phase 3 (US1 — Blue Background Across All Pages)**: 2 tasks
- **Phase 4 (US2 — Readable Content Over Blue Background)**: 4 tasks
- **Phase 5 (US3 — Elevated Surface Distinction)**: 3 tasks
- **Phase 6 (US4 — Maintainable Color Definition)**: 2 tasks
- **Phase 7 (Polish)**: 4 tasks
- **Parallel opportunities**: 4 identified (Setup, User Stories, Polish, US2 internal)
- **Independent test criteria**: Each user story has a clear independent test defined
- **Suggested MVP scope**: User Stories 1 + 2 (Blue background applied + contrast validated — Phases 1–4, 13 tasks)
- **Format validation**: ✅ All 22 tasks follow checklist format (checkbox, ID, labels, file paths)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Frontend follows existing React 18 + Tailwind CSS + HSL CSS custom property theming patterns
- Uses `--app-bg` as a new CSS custom property to avoid conflicting with the existing `--background` token used by cards, popovers, and other surfaces
- Dark mode is class-based (`darkMode: ["class"]`) — the `.dark` variant of `--app-bg` must be defined for dark mode support
- No test tasks included (tests not explicitly requested in specification)
- XS feature (~1 hour estimate) — minimal file changes: frontend/src/index.css, frontend/tailwind.config.js, frontend/src/App.tsx
