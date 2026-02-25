# Tasks: Add Red Background Color to Application

**Input**: Design documents from `/specs/011-red-background/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No test tasks included — tests were not explicitly requested in the feature specification. Existing tests must continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- This feature only modifies `frontend/src/index.css` — a single-file CSS token change

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Audit existing styles and confirm the token-based theming architecture before making changes

- [ ] T001 Audit current CSS custom property values in `frontend/src/index.css` `:root` and `html.dark-mode-active` selectors to document baseline token values
- [ ] T002 Audit component-level CSS files under `frontend/src/components/` and `frontend/src/pages/` for any hardcoded background colors that would conflict with the new red background

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational/blocking infrastructure tasks needed — the existing CSS custom property architecture is already in place and all components consume tokens via `var()` references. Phase 1 audit confirms readiness.

**⚠️ CRITICAL**: Phase 1 audit must confirm no hardcoded background conflicts before proceeding to user story phases.

**Checkpoint**: Audit complete — user story implementation can now begin

---

## Phase 3: User Story 1 — Global Red Background Applied (Priority: P1) 🎯 MVP

**Goal**: Update the application's primary and secondary background colors to red in both light and dark modes so the red background is visible across all pages and viewports.

**Independent Test**: Open any page in the application — the background should be visibly red in both light and dark mode, responsive across all viewports (320px–2560px).

### Implementation for User Story 1

- [ ] T003 [US1] Update light mode `--color-bg` from `#ffffff` to `#DC2626` in `:root` selector in `frontend/src/index.css`
- [ ] T004 [US1] Update light mode `--color-bg-secondary` from `#f6f8fa` to `#B91C1C` in `:root` selector in `frontend/src/index.css`
- [ ] T005 [US1] Update dark mode `--color-bg` from `#0d1117` to `#7F1D1D` in `html.dark-mode-active` selector in `frontend/src/index.css`
- [ ] T006 [US1] Update dark mode `--color-bg-secondary` from `#161b22` to `#991B1B` in `html.dark-mode-active` selector in `frontend/src/index.css`
- [ ] T007 [US1] Verify red background displays on all pages/routes by running `cd frontend && npm run dev` and navigating through the application

**Checkpoint**: At this point, the red background should be visible globally in both light and dark modes across all viewports

---

## Phase 4: User Story 2 — UI Readability and Accessibility Maintained (Priority: P1)

**Goal**: Ensure all text, borders, and foreground elements remain readable and accessible against the new red backgrounds by updating text and border color tokens to meet WCAG AA contrast requirements (≥4.5:1).

**Independent Test**: Inspect all page elements — text should be clearly legible against red backgrounds. Contrast ratios: white text `#FFFFFF` on `#DC2626` = 4.63:1 (AA pass), light text `#e6edf3` on `#7F1D1D` = 7.2:1 (AAA pass).

### Implementation for User Story 2

- [ ] T008 [US2] Update light mode `--color-text` from `#24292f` to `#FFFFFF` in `:root` selector in `frontend/src/index.css`
- [ ] T009 [US2] Update light mode `--color-text-secondary` from `#57606a` to `#FCA5A5` in `:root` selector in `frontend/src/index.css`
- [ ] T010 [US2] Update light mode `--color-border` from `#d0d7de` to `#FECACA` in `:root` selector in `frontend/src/index.css`
- [ ] T011 [US2] Update dark mode `--color-border` from `#30363d` to `#7F1D1D` in `html.dark-mode-active` selector in `frontend/src/index.css`
- [ ] T012 [US2] Verify all text, buttons, cards, modals, navigation, and forms remain readable against the red background in both light and dark modes
- [ ] T013 [US2] Run existing frontend tests to confirm no regressions: `cd frontend && npm run test -- --run`

**Checkpoint**: At this point, all UI elements should be readable and accessible against the red background in both modes

---

## Phase 5: User Story 3 — Centralized and Maintainable Color Definition (Priority: P2)

**Goal**: Confirm the red background is defined exclusively through centralized CSS custom properties so that a single token value change updates the background globally.

**Independent Test**: Change `--color-bg` to a different value in `frontend/src/index.css` — the entire application background should update on reload without any other file changes.

### Implementation for User Story 3

- [ ] T014 [US3] Verify no hardcoded background colors were introduced during US1/US2 implementation — all background values must use `var(--color-bg)` or `var(--color-bg-secondary)` in `frontend/src/index.css` and component CSS files
- [ ] T015 [US3] Confirm that changing the `--color-bg` token value in `:root` in `frontend/src/index.css` updates the background globally across the entire application on reload

**Checkpoint**: All user stories should now be independently functional — red background is applied, accessible, and maintainable

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across browsers, viewports, and build pipeline

- [ ] T016 Run full frontend build to confirm no errors: `cd frontend && npm run build`
- [ ] T017 Run full frontend test suite to confirm no regressions: `cd frontend && npm run test -- --run`
- [ ] T018 Visual verification across viewports (320px, 768px, 1024px, 1920px) per quickstart.md checklist
- [ ] T019 Run quickstart.md validation checklist (light mode, dark mode, responsive, components intact)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 audit completion — confirms no hardcoded conflicts
- **User Story 1 (Phase 3)**: Depends on Phase 2 — delivers the core red background (MVP)
- **User Story 2 (Phase 4)**: Depends on Phase 3 — adjusts text/border tokens for readability against red backgrounds
- **User Story 3 (Phase 5)**: Depends on Phase 4 — validates centralized token architecture
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — delivers the primary red background change
- **User Story 2 (P1)**: Depends on User Story 1 — text/border token adjustments are meaningless without the red background in place
- **User Story 3 (P2)**: Can start after User Story 2 — validates the token architecture holds after all changes

### Within Each User Story

- Token updates before visual verification
- All token changes in `frontend/src/index.css` for a given story can be applied together
- Verification step at the end of each story

### Parallel Opportunities

- T003 and T004 (light mode bg tokens) can be applied together in a single edit
- T005 and T006 (dark mode bg tokens) can be applied together in a single edit
- T008, T009, T010 (light mode text/border tokens) can be applied together in a single edit
- T011 (dark mode border token) can be applied in the same edit session as T008–T010
- In practice, all token updates (T003–T011) target the same file (`frontend/src/index.css`) and can be applied in a single commit

---

## Parallel Example: User Story 1

```bash
# All light mode background token updates can be applied together:
Task: "T003 [US1] Update light mode --color-bg to #DC2626 in frontend/src/index.css"
Task: "T004 [US1] Update light mode --color-bg-secondary to #B91C1C in frontend/src/index.css"

# All dark mode background token updates can be applied together:
Task: "T005 [US1] Update dark mode --color-bg to #7F1D1D in frontend/src/index.css"
Task: "T006 [US1] Update dark mode --color-bg-secondary to #991B1B in frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Audit existing styles
2. Complete Phase 2: Confirm no blocking conflicts
3. Complete Phase 3: User Story 1 — Apply red background tokens
4. **STOP and VALIDATE**: Red background visible on all pages in both modes
5. Deploy/demo if ready — core red background is live

### Incremental Delivery

1. Complete Setup + Foundational → Audit confirms readiness
2. Add User Story 1 → Red background applied globally → Validate (MVP!)
3. Add User Story 2 → Text/border contrast fixed → Validate accessibility
4. Add User Story 3 → Token architecture confirmed → Validate maintainability
5. Polish → Full build, tests, cross-browser validation

### Single-Developer Strategy (Recommended)

This is an XS-sized feature (~1 hour). All changes target a single file (`frontend/src/index.css`). The recommended approach:

1. Apply all token updates (T003–T011) in a single editing session
2. Run build + tests (T016–T017)
3. Visual verification (T018–T019)
4. Total: 19 tasks, ~1 hour estimated effort

---

## Notes

- All 19 tasks target a single file: `frontend/src/index.css`
- No new files, dependencies, or structural changes needed
- No tests are generated — spec does not mandate new tests (FR-008 visual regression is SHOULD-level)
- Existing frontend tests must continue to pass after token changes
- Color values sourced from research.md WCAG AA contrast verification
- Token dependency graph: `body { background: var(--color-bg-secondary) }` cascades globally through existing architecture
