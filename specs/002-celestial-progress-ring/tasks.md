# Tasks: Celestial Loading Progress Ring

**Input**: Design documents from `/specs/002-celestial-progress-ring/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Tests are REQUIRED per FR-016 and FR-017 in the feature specification.

**Organization**: Tasks are grouped by user story. US1 (P1) and US4 (P1) are combined into a single phase because the time-based minimum progress animation (US4) is an integral internal feature of the core component created in US1 — they cannot be delivered or tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/frontend/src/` for frontend code
- **Tests**: Colocated with source files per project convention (e.g., `CelestialLoadingProgress.test.tsx` alongside `CelestialLoadingProgress.tsx`)

---

## Phase 1: Setup

**Purpose**: Add shared CSS utility class required by the new component

- [ ] T001 Add `.celestial-ring-glow` CSS utility class with gold drop-shadow filter (`filter: drop-shadow(0 0 6px hsl(var(--gold) / 0.4)) drop-shadow(0 0 14px hsl(var(--gold) / 0.15))`) after existing celestial animation classes (~line 1460) in `solune/frontend/src/index.css`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking foundational work required — this feature is entirely client-side with no database, API, or authentication dependencies.

**⚠️ NOTE**: Phase 1 (Setup) provides the only shared prerequisite (`.celestial-ring-glow` CSS class).

**Checkpoint**: Setup complete — user story implementation can begin.

---

## Phase 3: User Story 1 + User Story 4 — Core Component + Project Page Integration (Priority: P1) 🎯 MVP

**Goal**: Create the `CelestialLoadingProgress` component with time-based minimum progress animation (US4) and integrate it into `ProjectsPage`, replacing the static `CelestialLoader`. This delivers the highest-impact UX improvement on the primary long-loading screen.

**Independent Test**: Navigate to any project and confirm the gold ring fills through labeled phases with stars twinkling; confirm the ring moves immediately on mount (time-based fill) and jumps on phase completions.

### Tests for User Story 1 (FR-016, FR-017) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T002 [P] [US1] Create component test file with test cases: (a) renders initial phase label with zero completions, (b) updates ring progress as phases complete via `aria-valuenow`, (c) exposes `role='progressbar'` with correct `aria-valuenow`, (d) shows last phase label when all phases complete, (e) handles empty phases array gracefully — in `solune/frontend/src/components/common/CelestialLoadingProgress.test.tsx`

### Implementation for User Story 1 + User Story 4

- [ ] T003 [US1] Create `CelestialLoadingProgress` component implementing: `LoadingPhase` and `CelestialLoadingProgressProps` interfaces, `useEffect`-driven time-based minimum progress (`useState(0)` + `setInterval(100ms)`, 0→15% over 3s, cap at ~30%), progress computation as `max(minProgress, completedPhases/totalPhases)`, SVG circular progress ring (`viewBox="0 0 120 120"`, `r=52`, `stroke-dasharray`/`stroke-dashoffset` with `0.6s ease` CSS transition), `<linearGradient>` with `hsl(var(--gold))` → `hsl(var(--primary))`, embedded `CelestialLoader` centered via absolute positioning inside relative container, phase label `<p key={label}>` with `celestial-fade-in` class, 3–5 twinkling star `<span>` elements with `celestial-twinkle`/`celestial-twinkle-delayed` classes and `aria-hidden="true"`, `celestial-ring-glow` class on SVG, and `role="progressbar"` with `aria-valuenow`/`aria-valuemin={0}`/`aria-valuemax={100}`/`aria-label="Loading progress"` — in `solune/frontend/src/components/common/CelestialLoadingProgress.tsx`
- [ ] T004 [US1] Replace the `boardLoading && CelestialLoader` block (~line 455) with `CelestialLoadingProgress` wiring four phases: Phase 1 `'Connecting to GitHub…'` (`complete: !projectsLoading`), Phase 2 `'Loading project board…'` (`complete: !boardLoading`), Phase 3 `'Loading pipelines…'` (`complete: !savedPipelinesLoading`), Phase 4 `'Loading agents…'` (`complete: !!agents`) — update import from `CelestialLoader` to `CelestialLoadingProgress` — in `solune/frontend/src/pages/ProjectsPage.tsx`
- [ ] T005 [US1] Replace `CelestialLoader` mock with `CelestialLoadingProgress` mock (rendering phase label text from the first incomplete phase), update `'shows loading state when board is loading'` test assertion from `'Loading board…'` to the first phase label text `'Connecting to GitHub…'` — in `solune/frontend/src/pages/ProjectsPage.test.tsx`

**Checkpoint**: `CelestialLoadingProgress` component is fully functional with time-based minimum animation; Project page shows phased progress ring. Component tests and page tests pass. This is a shippable MVP.

---

## Phase 4: User Story 2 — Agents Pipeline and Settings Page Integration (Priority: P2)

**Goal**: Extend `CelestialLoadingProgress` to `AgentsPipelinePage` and `SettingsPage` with page-specific phase labels, ensuring consistent loading feedback across all long-loading screens.

**Independent Test**: Navigate to the Agents Pipeline page and the Settings page and confirm each displays the progress ring with page-specific phase labels; confirm ring behavior (time-based minimum, phase jumps, twinkling stars) is identical to the Project page.

### Implementation for User Story 2

- [ ] T006 [P] [US2] Replace `CelestialLoader` with `CelestialLoadingProgress` wiring three phases: Phase 1 `'Connecting to GitHub…'` (`complete: !projectsLoading`), Phase 2 `'Loading board data…'` (`complete: !boardLoading`), Phase 3 `'Loading agents…'` (`complete: !agentsLoading`) — update import from `CelestialLoader` to `CelestialLoadingProgress` — in `solune/frontend/src/pages/AgentsPipelinePage.tsx` (~line 155)
- [ ] T007 [P] [US2] Replace `CelestialLoader` loading block with `CelestialLoadingProgress` wiring two phases: Phase 1 `'Loading user settings…'` (`complete: !userLoading`), Phase 2 `'Loading global settings…'` (`complete: !globalLoading`) — update import from `CelestialLoader` to `CelestialLoadingProgress`, update loading condition to `(userLoading || globalLoading)` — in `solune/frontend/src/pages/SettingsPage.tsx` (~line 68)

**Checkpoint**: All three target pages (Project, Agents Pipeline, Settings) show consistent progress ring behavior with page-appropriate phase labels. Each page can be tested independently.

---

## Phase 5: User Story 3 — Accessibility and Dark Mode Verification (Priority: P2)

**Goal**: Ensure the progress ring is fully accessible to assistive technology and clearly visible in dark mode, with dedicated test coverage for all accessibility attributes.

**Independent Test**: Enable a screen reader and verify progress announcements; toggle dark mode to confirm visual clarity of the gold ring and twinkling stars against the dark background.

### Tests for User Story 3 ⚠️

- [ ] T008 [US3] Add accessibility-focused test assertions verifying: `aria-valuemin="0"`, `aria-valuemax="100"`, and `aria-label="Loading progress"` are all present on the `role="progressbar"` element — in `solune/frontend/src/components/common/CelestialLoadingProgress.test.tsx`
- [ ] T009 [US3] Add test assertion verifying twinkling star decorative elements have `aria-hidden="true"` attribute for screen reader exclusion — in `solune/frontend/src/components/common/CelestialLoadingProgress.test.tsx`

**Checkpoint**: All accessibility attributes verified by automated tests. Dark mode compatibility ensured via `hsl(var(--gold))` and `hsl(var(--primary))` design tokens (existing tokens already have dark-mode-aware values — verified in research.md).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all stories — ensure zero regressions, clean lint, and production-ready build

- [ ] T010 [P] Run component tests: `npx vitest run src/components/common/CelestialLoadingProgress.test.tsx`
- [ ] T011 [P] Run page tests: `npx vitest run src/pages/ProjectsPage.test.tsx`
- [ ] T012 Run full test suite with no regressions: `npm run test`
- [ ] T013 [P] Lint all modified files: `npx eslint src/components/common/CelestialLoadingProgress.tsx src/pages/ProjectsPage.tsx src/pages/AgentsPipelinePage.tsx src/pages/SettingsPage.tsx`
- [ ] T014 Run type check: `npm run type-check`
- [ ] T015 Run production build: `npm run build`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: No tasks — pass-through
- **US1+US4 (Phase 3)**: Depends on Phase 1 (`.celestial-ring-glow` CSS class must exist)
- **US2 (Phase 4)**: Depends on Phase 3 (`CelestialLoadingProgress` component must exist)
- **US3 (Phase 5)**: Depends on Phase 3 (test assertions extend existing test file from T002)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 + US4 (P1)**: Can start after Phase 1 — No dependency on other user stories
- **US2 (P2)**: Depends on US1 — Uses `CelestialLoadingProgress` component created in Phase 3
- **US3 (P2)**: Depends on US1 — Extends test file created in Phase 3 — Can run **in parallel** with US2

### Within Each User Story

- Tests (T002) written FIRST and expected to FAIL before implementation (T003)
- Component creation (T003) before page integration (T004)
- Page integration (T004) before test mock updates (T005)
- Story complete before moving to next priority

### Parallel Opportunities

- T001 (CSS class) and T002 (test file) can be written in parallel — different files
- T006 (AgentsPipelinePage) and T007 (SettingsPage) can run in parallel — different files, no shared dependencies
- T008 and T009 (US3 accessibility tests) can run in parallel with T006/T007 (US2 page integrations)
- T010, T011, T013 (verification commands) can run in parallel — independent targets
- US2 (Phase 4) and US3 (Phase 5) can be worked in parallel once US1+US4 (Phase 3) is complete

---

## Parallel Example: User Story 1 + User Story 4

```bash
# T001 and T002 can run in parallel (different files):
Task: "Add .celestial-ring-glow CSS class in solune/frontend/src/index.css"
Task: "Create CelestialLoadingProgress.test.tsx in solune/frontend/src/components/common/"

# After T003 (component), T004 and T005 are sequential:
Task: "Replace loader in ProjectsPage.tsx"          # T004 — depends on T003
Task: "Update mocks in ProjectsPage.test.tsx"       # T005 — depends on T004
```

## Parallel Example: User Story 2

```bash
# T006 and T007 can run in parallel (different page files):
Task: "Replace loader in AgentsPipelinePage.tsx"     # T006
Task: "Replace loader in SettingsPage.tsx"           # T007
```

## Parallel Example: US2 + US3 (after US1 complete)

```bash
# US2 and US3 can run in parallel:
Task: "T006 — AgentsPipelinePage integration"        # US2
Task: "T007 — SettingsPage integration"              # US2
Task: "T008 — Accessibility test assertions"         # US3 (parallel with US2)
Task: "T009 — Star aria-hidden test"                 # US3 (parallel with US2)
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 4 Only)

1. Complete Phase 1: Setup (T001 — `.celestial-ring-glow` CSS class)
2. Complete Phase 3: US1+US4 (T002–T005 — component + ProjectsPage + tests)
3. **STOP and VALIDATE**: Run `npx vitest run src/components/common/CelestialLoadingProgress.test.tsx` and `npx vitest run src/pages/ProjectsPage.test.tsx`
4. Deploy/demo if ready — Project page alone delivers the highest-impact UX improvement

### Incremental Delivery

1. Phase 1: Setup → CSS ready
2. Phase 3: US1+US4 → Core component + Project page → Test + Demo (**MVP!**)
3. Phase 4: US2 → Agents Pipeline + Settings pages consistent → Test + Demo
4. Phase 5: US3 → Full accessibility test coverage → Validate
5. Phase 6: Polish → Full suite green, lint clean, type-safe, production build passes
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 (single task — T001)
2. Once CSS class is committed:
   - Developer A: US1+US4 (T002–T005 — core component + ProjectsPage)
3. Once component exists:
   - Developer B: US2 (T006–T007 — AgentsPipelinePage + SettingsPage)
   - Developer C: US3 (T008–T009 — accessibility test coverage)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- US4 (Time-Based Minimum) is combined with US1 because it is an integral `useState`/`useEffect` inside the component — not a separately deliverable feature
- US3 (Accessibility/Dark Mode) implementation is embedded in the component (T003) but verified separately with dedicated tests in Phase 5
- `CelestialLoader.tsx` is NOT modified — only embedded inside the new component via absolute positioning
- Progress is derived from existing React Query hooks — no backend changes or new API endpoints needed
- Dark mode compatibility is inherent via `hsl(var(--gold))` and `hsl(var(--primary))` design tokens (verified in research.md Task 6)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 15 |
| **US1 + US4 tasks** | 4 (T002–T005) |
| **US2 tasks** | 2 (T006–T007) |
| **US3 tasks** | 2 (T008–T009) |
| **Setup tasks** | 1 (T001) |
| **Polish/validation tasks** | 6 (T010–T015) |
| **Parallel opportunities** | 6 tasks marked [P] |
| **Files created** | 2 (`CelestialLoadingProgress.tsx`, `CelestialLoadingProgress.test.tsx`) |
| **Files modified** | 5 (`index.css`, `ProjectsPage.tsx`, `ProjectsPage.test.tsx`, `AgentsPipelinePage.tsx`, `SettingsPage.tsx`) |
| **Suggested MVP scope** | Phase 1 + Phase 3 (US1+US4): 5 tasks |
| **Independent test criteria** | US1: Gold ring fills through phases on Project page; US2: Consistent ring on all 3 pages; US3: Screen reader + dark mode |
