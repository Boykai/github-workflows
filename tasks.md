# Tasks: Add Brown Background Color to App

**Input**: Issue #679 — Add Brown Background Color to App
**Prerequisites**: Frontend CSS theming system (`frontend/src/index.css`), theme hook (`frontend/src/hooks/useAppTheme.ts`)

**Tests**: No tests explicitly requested in the feature specification. Test tasks are omitted per task generation rules.

**Organization**: This is a single-user-story feature (XS size). Tasks are organized into Setup, Implementation (US1), and Polish phases.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` for frontend source files

---

## Phase 1: Setup

**Purpose**: Verify current theming infrastructure and identify impacted files

- [ ] T001 Review current CSS custom properties and theming structure in `frontend/src/index.css`
- [ ] T002 Review body background usage and confirm `var(--color-bg-secondary)` is the global background token in `frontend/src/index.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define the brown color as a reusable design token before applying it

**⚠️ CRITICAL**: The brown color token must be defined before any visual changes are applied

- [ ] T003 Define brown background CSS custom property `--color-bg` as `#4E342E` in `:root` selector in `frontend/src/index.css`
- [ ] T004 Define brown secondary background CSS custom property `--color-bg-secondary` as `#3E2723` in `:root` selector in `frontend/src/index.css`
- [ ] T005 [P] Update `--color-text` to `#FFFFFF` in `:root` selector to ensure WCAG AA contrast (minimum 4.5:1) against brown background in `frontend/src/index.css`
- [ ] T006 [P] Update `--color-text-secondary` to a lighter value (e.g., `#D7CCC8`) in `:root` selector for readable secondary text against brown background in `frontend/src/index.css`

**Checkpoint**: Brown color tokens defined — implementation can proceed

---

## Phase 3: User Story 1 — Apply Brown Background Globally (Priority: P1) 🎯 MVP

**Goal**: Apply the brown background color globally across the application so it renders consistently on all pages, routes, viewports, and both light/dark modes.

**Independent Test**: Open the application in a browser. The background should be a warm brown (#4E342E) in light mode and a dark brown variant in dark mode. All text should be readable. Modals, cards, and overlays should layer correctly without bleed or transparency issues.

### Implementation for User Story 1

- [ ] T007 [US1] Update dark mode `--color-bg` to a dark brown value (e.g., `#2C1A12`) in `html.dark-mode-active` selector in `frontend/src/index.css`
- [ ] T008 [US1] Update dark mode `--color-bg-secondary` to a dark brown value (e.g., `#1B0E08`) in `html.dark-mode-active` selector in `frontend/src/index.css`
- [ ] T009 [P] [US1] Update dark mode `--color-text` to `#E6EDF3` (or keep current) ensuring WCAG AA contrast against dark brown background in `frontend/src/index.css`
- [ ] T010 [P] [US1] Update dark mode `--color-text-secondary` to a readable value against dark brown background in `frontend/src/index.css`
- [ ] T011 [US1] Update `--color-border` in both `:root` and `html.dark-mode-active` selectors to complement the brown background in `frontend/src/index.css`
- [ ] T012 [US1] Verify `body` background remains bound to `var(--color-bg-secondary)` (the global body background token) — no changes needed if token values are updated correctly in `frontend/src/index.css`
- [ ] T013 [US1] Verify `--color-primary`, `--color-success`, `--color-warning`, `--color-danger` contrast ratios against brown backgrounds and adjust if needed in `frontend/src/index.css`
- [ ] T014 [US1] Visually verify modals, drawers, tooltips, and overlay components layer correctly on top of brown background (manual browser check)
- [ ] T015 [US1] Visually verify existing UI components (buttons, cards, inputs, navigation) remain readable against brown background across Chrome, Firefox, Safari, Edge (manual cross-browser check)

**Checkpoint**: Brown background fully applied and verified — US1 is complete and independently testable

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and cleanup

- [ ] T016 [P] Add inline CSS comment documenting the brown color palette choice and hex values in `frontend/src/index.css`
- [ ] T017 Perform final visual regression check across all pages and responsive viewports (mobile, tablet, desktop)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — defines brown color tokens (BLOCKS user story)
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2) — applies and verifies brown background
- **Polish (Phase 4)**: Depends on User Story 1 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — single user story, no cross-story dependencies

### Within User Story 1

- Token definitions (T003–T006) before application (T007–T011)
- Light mode tokens before dark mode tokens
- Token updates before visual verification (T012–T015)
- Core implementation before polish (T016–T017)

### Parallel Opportunities

- T005 and T006 can run in parallel (different CSS properties, same file section)
- T009 and T010 can run in parallel (different dark mode properties)
- T016 can run in parallel with T017 (documentation vs. visual check)
- Within Phase 2, text color updates (T005, T006) can be parallelized after background tokens (T003, T004)

---

## Parallel Example: User Story 1

```bash
# After T003 and T004 (brown background tokens defined):
# Launch text color updates in parallel:
Task: "T005 - Update --color-text for WCAG AA contrast in frontend/src/index.css"
Task: "T006 - Update --color-text-secondary for readability in frontend/src/index.css"

# After T007 and T008 (dark mode background tokens):
# Launch dark mode text updates in parallel:
Task: "T009 - Update dark mode --color-text in frontend/src/index.css"
Task: "T010 - Update dark mode --color-text-secondary in frontend/src/index.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (review current theming)
2. Complete Phase 2: Foundational (define brown tokens)
3. Complete Phase 3: User Story 1 (apply + verify brown background)
4. **STOP and VALIDATE**: Open app in browser, verify brown background renders correctly in light and dark modes
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Brown tokens defined
2. Add User Story 1 → Visually verify → Deploy/Demo (MVP!)
3. Polish phase → Documentation and final regression check
4. Single-story feature — delivery is atomic

---

## Notes

- [P] tasks = different files or non-overlapping sections, no dependencies
- [US1] label maps task to the single user story for traceability
- All CSS changes are confined to `frontend/src/index.css` — minimal blast radius
- Note: `--color-bg` is the primary app background token; `--color-bg-secondary` is used as the `body` background (the outermost visible surface). Both must be updated to brown values.
- Brown color values: Light mode `#4E342E` (rich chocolate brown), Dark mode `#2C1A12` (deep brown)
- WCAG AA requires minimum 4.5:1 contrast ratio for normal text — white text (#FFFFFF) on #4E342E achieves ~11.3:1
- No new files are created — this is purely a CSS token value update
- Total tasks: 17
- Tasks in US1: 9 (T007–T015)
- Parallel opportunities: 4 sets of parallelizable tasks
- Suggested MVP scope: User Story 1 (Phase 3) — the entire feature is one story
