# Tasks: Performance Review

**Workspace note**: Treat `/home/runner/work/github-workflows/github-workflows` as `REPO_ROOT`; for example, `/home/runner/work/github-workflows/github-workflows/backend/src/api/board.py` maps to `REPO_ROOT/backend/src/api/board.py` if the repository is checked out elsewhere.

**Input**: Design documents from `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/`
**Prerequisites**: `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/plan.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/spec.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/research.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/data-model.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md`

**Tests**: Tests are required for this feature because the specification explicitly requires regression coverage and before/after verification across backend cache behavior, polling/WebSocket refresh logic, and frontend rerender behavior.

**Organization**: Tasks are grouped by user story so each story can be implemented, measured, and validated independently while reusing a small shared setup and foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel when the listed files do not overlap with incomplete work
- **[Story]**: Present only for user story tasks (`[US1]` ... `[US6]`)
- Every task below includes exact repository file paths

## Path Conventions

- **Repository root**: `/home/runner/work/github-workflows/github-workflows`
- **Backend code/tests**: `/home/runner/work/github-workflows/github-workflows/backend/src/` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/`
- **Frontend code/tests**: `/home/runner/work/github-workflows/github-workflows/frontend/src/`
- **Feature docs/artifacts**: `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/`

---

## Phase 1: Setup

**Purpose**: Create the shared measurement and verification artifacts that every optimization story will reference.

- [ ] T001 Create the baseline workbook in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` and link it from `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md`
- [ ] T002 [P] Add the representative-board capture workflow and command matrix to `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md`
- [ ] T003 [P] Record contract-to-code traceability notes in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/research.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/cache-behavior.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/refresh-policy.md`, and `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/render-behavior.md`

**Checkpoint**: A shared measurement workbook, execution guide, and contract mapping exist before code or baseline work begins.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish reusable hash/fixture plumbing and verification scaffolding that every story depends on.

**⚠️ CRITICAL**: Complete this phase before starting any user story implementation.

- [ ] T004 Add shared cache/hash helpers needed by the refresh-policy and cache-behavior contracts in `/home/runner/work/github-workflows/github-workflows/backend/src/services/cache.py` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useProjectBoard.ts`
- [ ] T005 [P] Add backend warm-cache, stale-cache, and unchanged-data fixtures in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_cache.py`, `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_board.py`, and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_projects.py`
- [ ] T006 [P] Add frontend query-client and refresh-path harness coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.test.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useBoardRefresh.test.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useProjectBoard.test.tsx`
- [ ] T007 Define the before/after metric table and pass/fail checklist in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` and `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md`

**Checkpoint**: Shared helpers and regression harnesses are ready, so story work can proceed without redefining fixtures or success metrics.

---

## Phase 3: User Story 1 - Establish Performance Baselines (Priority: P1) 🎯

**Goal**: Capture backend and frontend baseline measurements in a consistent format before optimization work changes behavior.

**Independent Test**: Follow `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md` on a representative board and confirm `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` records:

- idle API and warm-cache baselines
- board-load, rerender, and network baselines
- the mapped regression suites that will validate later optimization work

### Tests for User Story 1

- [ ] T008 [P] [US1] Add the baseline measurement schema and capture checklist to `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` and `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md`
- [ ] T009 [P] [US1] Map each baseline metric to regression suites in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_cache.py`, `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_board.py`, `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.test.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useBoardRefresh.test.tsx`

### Implementation for User Story 1

- [ ] T010 [US1] Capture backend idle-call, endpoint-frequency, and warm-cache baselines in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` using `/home/runner/work/github-workflows/github-workflows/backend/src/api/board.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/api/projects.py`, and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/polling_loop.py`
- [ ] T011 [US1] Capture frontend board-load, rerender-count, and network-volume baselines in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` using `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/ProjectsPage.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/ProjectBoard.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.ts`

**Checkpoint**: Baselines are recorded and the feature has an objective before/after comparison point for all later stories.

---

## Phase 4: User Story 2 - Reduce Backend API Consumption During Idle Board Viewing (Priority: P1)

**Goal**: Reuse warm caches and suppress unchanged refresh work so idle boards stop burning GitHub API budget.

**Independent Test**: Leave a board idle for 5 minutes and verify the documented baseline comparison shows no unnecessary full refreshes, fewer warm-cache GitHub calls, and unchanged data paths skipped by backend tests.

### Tests for User Story 2

- [ ] T012 [P] [US2] Add warm sub-issue cache reuse regression coverage in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_cache.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_board.py`
- [ ] T013 [P] [US2] Add unchanged-subscription and idle-polling regression coverage in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_projects.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 2

- [ ] T014 [US2] Reuse warm sub-issue caches during non-manual board loads in `/home/runner/work/github-workflows/github-workflows/backend/src/api/board.py`
- [ ] T015 [US2] Skip unchanged WebSocket refresh work while preserving stale-fallback behavior in `/home/runner/work/github-workflows/github-workflows/backend/src/api/projects.py`
- [ ] T016 [US2] Tighten idle polling cache reuse, inflight request coalescing, and shared repository-resolution reuse in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/polling_loop.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/github_projects/service.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/utils.py`, and `/home/runner/work/github-workflows/github-workflows/backend/src/api/workflow.py`

**Checkpoint**: Backend refresh paths avoid redundant GitHub traffic when board data and sub-issue data are already warm or unchanged.

---

## Phase 5: User Story 3 - Decouple Frontend Refresh Paths (Priority: P1)

**Goal**: Keep task-level real-time updates lightweight so they do not invalidate or reload the full board query unless the user explicitly requests it.

**Independent Test**: Trigger WebSocket and fallback-polling updates on an open board and verify only `['projects', projectId, 'tasks']` is invalidated; then trigger manual refresh and confirm the full board query reloads exactly once.

### Tests for User Story 3

- [ ] T017 [P] [US3] Add task-query-only invalidation coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.test.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useProjectBoard.test.tsx`
- [ ] T018 [P] [US3] Add debounce and manual-refresh precedence coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useBoardRefresh.test.tsx`

### Implementation for User Story 3

- [ ] T019 [US3] Apply hash-aware polling fallback and message-type refresh routing in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.ts`
- [ ] T020 [US3] Enforce the manual-vs-auto board reload contract in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useBoardRefresh.ts`
- [ ] T021 [US3] Keep board queries isolated from task refreshes in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useProjectBoard.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: WebSocket and polling updates stay lightweight, while manual refresh remains the only path that forces a full board reload.

---

## Phase 6: User Story 4 - Optimize Frontend Board Rendering (Priority: P2)

**Goal**: Reduce rerenders and expensive derived work so large boards stay responsive during common interactions.

**Independent Test**: On a board with 20+ items, update one card and confirm rerender coverage shows only the affected card/column update while memoized callbacks and RAF-gated listeners remain stable.

### Tests for User Story 4

- [ ] T022 [P] [US4] Add rerender-scope regression coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/BoardColumn.test.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/IssueCard.test.tsx`
- [ ] T023 [P] [US4] Add callback-stability and board-orchestration coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/ProjectsPage.test.tsx`

### Implementation for User Story 4

- [ ] T024 [US4] Stabilize board-level callbacks and derived board data in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/ProjectsPage.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/ProjectBoard.tsx`
- [ ] T025 [US4] Memoize column grouping and derived computations in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/BoardColumn.tsx`
- [ ] T026 [US4] Preserve card-level memo boundaries and RAF-gated interaction handlers in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/IssueCard.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/AddAgentPopover.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/chat/ChatPopup.tsx`

**Checkpoint**: Single-card updates stop cascading through the whole board, and high-frequency UI handlers remain throttled and well-scoped.

---

## Phase 7: User Story 5 - Verify Improvements and Prevent Regressions (Priority: P2)

**Goal**: Prove the optimizations are real and durable with automated coverage plus a documented manual comparison against the recorded baselines.

**Independent Test**: Run the targeted backend/frontend suites, repeat the manual profiling pass, and confirm the after-state in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` shows measurable improvement against the baseline workbook.

### Tests for User Story 5

- [ ] T027 [P] [US5] Run and extend backend regression coverage in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_cache.py`, `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_board.py`, `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_projects.py`, and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`
- [ ] T028 [P] [US5] Run and extend frontend regression coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.test.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useBoardRefresh.test.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/BoardColumn.test.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/IssueCard.test.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/ProjectsPage.test.tsx`

### Implementation for User Story 5

- [ ] T029 [US5] Record post-optimization measurements and before/after deltas in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md`
- [ ] T030 [US5] Update the manual verification walkthrough and success-criteria checklist in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md`

**Checkpoint**: The feature has both automated regression coverage and documented evidence that the performance targets improved versus baseline.

---

## Phase 8: User Story 6 - Confirm Backend State Against Existing Spec (Priority: P2)

**Goal**: Audit Spec 022 behaviors so remaining backend work is limited to genuine gaps rather than re-implementing completed protections.

**Independent Test**: Review the Spec 022 audit artifact, then run the cache/WebSocket/manual-refresh tests and confirm each acceptance area is marked implemented, partial, or missing with any residual backend gap closed.

### Tests for User Story 6

- [ ] T031 [P] [US6] Add TTL-alignment and manual-refresh invalidation assertions in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_board.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_cache.py`
- [ ] T032 [P] [US6] Add unchanged-subscription and stale-fallback assertions in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_projects.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 6

- [ ] T033 [US6] Create the Spec 022 audit matrix and gap notes in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/spec-022-audit.md` and `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/research.md`
- [ ] T034 [US6] Close any remaining Spec 022 cache/change-detection gaps in `/home/runner/work/github-workflows/github-workflows/backend/src/api/board.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/api/projects.py`, and `/home/runner/work/github-workflows/github-workflows/backend/src/services/cache.py`

**Checkpoint**: Spec 022 status is explicit, verified, and any remaining backend gaps have been resolved or documented.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Reconcile the shipped implementation with the design artifacts and run the final validation commands.

- [ ] T035 [P] Reconcile shipped behavior with `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/cache-behavior.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/refresh-policy.md`, and `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/contracts/render-behavior.md`
- [ ] T036 [P] Run the quickstart scenarios and capture final notes in `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/quickstart.md` and `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md`
- [ ] T037 [P] Run backend validation commands from `/home/runner/work/github-workflows/github-workflows/backend/pyproject.toml` against `/home/runner/work/github-workflows/github-workflows/backend/src/api/board.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/api/projects.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/polling_loop.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/github_projects/service.py`, and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/`
- [ ] T038 [P] Run frontend validation commands from `/home/runner/work/github-workflows/github-workflows/frontend/package.json` against `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useRealTimeSync.ts`, `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useBoardRefresh.ts`, `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/useProjectBoard.ts`, `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/ProjectsPage.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/board/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories
- **US1 (Phase 3)**: Depends on Foundational; establishes the baseline required by optimization stories
- **US2-US5 (Phases 4-7)**: Depend on US1 baseline capture and Foundational scaffolding
- **US6 (Phase 8)**: Depends on Foundational and the shared measurement checklist; can proceed in parallel with baseline capture once Phase 2 is complete
- **Polish (Phase 9)**: Depends on all stories targeted for release

### User Story Dependency Graph

```text
Setup -> Foundational -> US1
Foundational -> US6
US1 -> US2 -> US5
US1 -> US3 -> US4 -> US5
US6 -> US5
US5 -> Polish
```

### User Story Dependencies

- **US1**: Must finish before any optimization claims are valid because it defines the baseline workbook and regression mapping
- **US2**: Depends on US1 baseline data and Foundational cache/hash fixtures
- **US3**: Depends on US1 baseline data and Foundational frontend refresh harnesses
- **US4**: Depends on US3 so rerender measurements are not polluted by unnecessary board reloads
- **US5**: Depends on US2, US3, US4, and US6 because it validates the final optimized behavior
- **US6**: Depends on the backend fixture work and measurement checklist in Phase 2; it does not depend on US2 and can run in parallel with US1/US2 once the checklist exists

### Within Each User Story

- Write or extend the listed tests before implementation changes in the same story
- Complete cache/hash/helper changes before behavior changes that rely on them
- Record baseline or post-change measurements immediately after the corresponding behavior lands
- Do not mark a story complete until its independent test and artifact updates pass

### Parallel Opportunities

- **Setup**: T002 and T003 can run together after T001 creates the shared measurement artifact
- **Foundational**: T005 and T006 can run together after T004 defines the shared helper direction
- **US1**: T008 and T009 can run together; T010 and T011 can then be measured in parallel in separate backend/frontend sessions
- **US2**: T012 and T013 can run together before T014-T016
- **US3**: T017 and T018 can run together before T019-T021
- **US4**: T022 and T023 can run together before T024-T026
- **US5**: T027 and T028 can run together before T029-T030
- **US6**: T031 and T032 can run together before T033-T034
- **Polish**: T035-T038 can be split across documentation, backend validation, and frontend validation owners

---

## Parallel Execution Examples

- **US1**: Run `T008` and `T009` together, then capture backend measurements in `T010` while a second session captures frontend measurements in `T011`.
- **US2**: Run `T012` and `T013` together, then split `T014` and `T015` across separate backend files while `T016` follows once the refresh behavior is stable.
- **US3**: Run `T017` and `T018` together, then implement `T019` and `T020` sequentially before wiring `T021`.
- **US4**: Run `T022` and `T023` together, then divide `T024`, `T025`, and `T026` by page, column, and card/listener surfaces.
- **US5**: Run `T027` and `T028` together, then assign one owner to `T029` measurement capture while another updates `T030` verification steps.
- **US6**: Run `T031` and `T032` together, then complete the audit artifact in `T033` before closing any residual backend gap in `T034`.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2
2. Complete **US1** to lock the baseline workbook
3. **Stop and validate** the baseline package before starting optimization stories
4. Use **US2** as the first optimization slice once the baseline confirms backend idle refresh work is still the top-value gap

### Incremental Delivery

1. Baseline and audit scaffolding first (`Setup` + `Foundational` + `US1`)
2. Ship backend idle-call reductions (`US2`)
3. Ship coherent frontend refresh-path behavior (`US3`)
4. Ship rerender reductions (`US4`)
5. Run the Spec 022 audit in parallel with backend/frontend optimization work once the checklist exists, then finish broad verification (`US6` + `US5`)
6. Run final polish and validation commands

### Parallel Team Strategy

1. One owner handles measurement/docs artifacts (`T001-T011`)
2. One owner handles backend cache/change-detection work (`T012-T016`, `T031-T034`)
3. One owner handles frontend refresh/render work (`T017-T026`)
4. Rejoin for regression proof and polish (`T027-T038`)

---

## Notes

- `[P]` marks tasks that touch separate files and can be executed independently
- Each user story phase is independently testable using the listed files and the quickstart workflow
- `/home/runner/work/github-workflows/github-workflows/specs/039-performance-review/measurements.md` is the canonical before/after evidence artifact for this feature
- Keep all work within the existing backend/frontend modules named in `plan.md`; no new runtime dependencies are needed
