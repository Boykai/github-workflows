# Tasks: Performance Review

**Input**: Design documents from `specs/001-performance-review/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/refresh-contract.md`

**Tests**: Tests are required — `spec.md` mandates regression coverage (FR-016) and manual before/after verification (FR-017).

**Organization**: Tasks are grouped by user story so each increment can be implemented and verified independently.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies)
- **[Story]**: User story label for story-specific work (`[US1]`–`[US4]`)
- Setup, Foundational, and Polish tasks do **not** include story labels

---

## Phase 1: Setup (Performance Review Workspace)

**Purpose**: Create the feature-local artifacts needed to capture measurements and run the performance pass consistently.

- [ ] T001 Create the before/after measurement workbook in `specs/001-performance-review/baseline.md`
- [ ] T002 Update the execution checklist and local verification commands in `specs/001-performance-review/quickstart.md`

**Checkpoint**: The feature has a dedicated baseline artifact and an executable quickstart for local verification.

---

## Phase 2: Foundational (Shared Guardrails and Contract)

**Purpose**: Lock the shared rules that all implementation stories must preserve before code changes begin.

**⚠️ CRITICAL**: No user story implementation should start until these guardrails are explicit.

- [ ] T003 Align refresh-source, scope, deduplication, and warm-state rules across `specs/001-performance-review/contracts/refresh-contract.md` and `specs/001-performance-review/data-model.md`
- [ ] T004 Document the already-correct protections to preserve (300s TTL, stale fallback, sub-issue invalidation, manual refresh bypass) in `specs/001-performance-review/research.md` and `specs/001-performance-review/baseline.md`

**Checkpoint**: The refresh contract and preservation rules are frozen, so implementation can focus on measured gaps only.

---

## Phase 3: User Story 1 — Team Establishes a Trusted Performance Baseline (Priority: P1) 🎯 MVP

**Goal**: Capture a reproducible before/after baseline package that blocks anecdotal optimization work and reuses the existing regression suite as guardrails.

**Independent Test**: Follow `specs/001-performance-review/quickstart.md`, record baseline data in `specs/001-performance-review/baseline.md`, and verify the documented guardrail suites are the exact suites reused after implementation.

### Tests for User Story 1

- [ ] T005 [P] [US1] Add the backend/frontend guardrail checklist in `specs/001-performance-review/baseline.md` for `backend/tests/unit/test_cache.py`, `backend/tests/unit/test_api_board.py`, `backend/tests/unit/test_copilot_polling.py`, `frontend/src/hooks/useRealTimeSync.test.tsx`, and `frontend/src/hooks/useBoardRefresh.test.tsx`
- [ ] T006 [P] [US1] Add the manual network/profiler verification steps in `specs/001-performance-review/quickstart.md` for `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/chat/ChatPopup.tsx`, and `frontend/src/components/board/AddAgentPopover.tsx`

### Implementation for User Story 1

- [ ] T007 [US1] Record the before/after measurement table, success-criteria rubric, and follow-on recommendation gate in `specs/001-performance-review/baseline.md`

**Checkpoint**: Baseline capture is reproducible, guardrails are explicit, and optimization work is blocked until the baseline artifact exists.

---

## Phase 4: User Story 2 — Idle Board Viewing Stops Wasting Upstream Request Budget (Priority: P1)

**Goal**: Suppress unchanged automatic board refreshes, lower warm-refresh upstream cost, and preserve manual refresh as a full fresh load.

**Independent Test**: Run the targeted backend regression suites, observe an unchanged board over the fixed interval, and confirm warm refreshes reuse cached board/sub-issue state while manual refresh still bypasses cache.

### Tests for User Story 2

- [ ] T008 [P] [US2] Extend unchanged-refresh and manual-refresh regression coverage in `backend/tests/unit/test_api_board.py`
- [ ] T009 [P] [US2] Extend WebSocket refresh-suppression and polling guard coverage in `backend/tests/unit/test_api_projects.py` and `backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 2

- [ ] T010 [US2] Add board cache hash and warm-state metadata handling in `backend/src/services/cache.py` and `backend/src/api/board.py`
- [ ] T011 [US2] Suppress unchanged-state WebSocket `refresh` broadcasts and keep canonical repository-resolution usage in `backend/src/api/projects.py` and `backend/src/utils.py`
- [ ] T012 [US2] Reuse warm board and sub-issue cache paths during repeated board refreshes in `backend/src/api/board.py` and `backend/src/services/github_projects/service.py`

**Checkpoint**: Idle unchanged viewing stops triggering repeated full refreshes, warm refreshes are cheaper, and manual refresh remains a forced full reload.

---

## Phase 5: User Story 3 — Live Updates Stay Responsive Without Recreating the Polling Storm (Priority: P1)

**Goal**: Enforce one refresh contract across WebSocket, fallback polling, auto-refresh, and manual refresh so task updates stay lightweight and board reloads are deduplicated.

**Independent Test**: Simulate live updates, WebSocket outages, fallback polling, auto-refresh, and manual refresh; verify task freshness remains timely while full board reloads only happen for manual refresh or confirmed board-level changes.

### Tests for User Story 3

- [ ] T013 [P] [US3] Extend live-update and fallback polling contract coverage in `frontend/src/hooks/useRealTimeSync.test.tsx`
- [ ] T014 [P] [US3] Extend board-reload deduplication and manual-refresh precedence coverage in `frontend/src/hooks/useBoardRefresh.test.tsx` and `frontend/src/hooks/useProjectBoard.test.tsx`

### Implementation for User Story 3

- [ ] T015 [US3] Encode lightweight-vs-full refresh handling and fallback coordination in `frontend/src/hooks/useRealTimeSync.ts`
- [ ] T016 [US3] Add full-board reload debouncing, manual-refresh precedence, and fallback-aware timer resets in `frontend/src/hooks/useBoardRefresh.ts`
- [ ] T017 [US3] Align board query ownership and contract-driven reload triggers in `frontend/src/hooks/useProjectBoard.ts` and `frontend/src/pages/ProjectsPage.tsx`

**Checkpoint**: Live updates remain fast, fallback stays lightweight, and all board reload paths follow one documented policy.

---

## Phase 6: User Story 4 — Large Board Interactions Feel Smoother During the First Pass (Priority: P2)

**Goal**: Reduce unnecessary render work and bound hot listener activity for representative board, chat, and popover interactions without architectural rewrites.

**Independent Test**: Profile the representative board before and after the changes, repeat card updates, drag-resize, chat movement, and popover interactions, and confirm unchanged board surfaces avoid extra render/listener work.

### Tests for User Story 4

- [ ] T018 [P] [US4] Add representative board interaction regression assertions in `frontend/src/pages/ProjectsPage.test.tsx`
- [ ] T019 [P] [US4] Add render-stability and listener-bounding coverage in `frontend/src/hooks/useBoardControls.test.tsx` and `frontend/src/hooks/useProjectBoard.test.tsx`

### Implementation for User Story 4

- [ ] T020 [US4] Stabilize memo-sensitive derived state and callback props in `frontend/src/pages/ProjectsPage.tsx`, `frontend/src/components/board/BoardColumn.tsx`, and `frontend/src/components/board/IssueCard.tsx`
- [ ] T021 [US4] Bound drag-resize update frequency in `frontend/src/components/chat/ChatPopup.tsx`
- [ ] T022 [US4] Bound popover reposition work in `frontend/src/components/board/AddAgentPopover.tsx`

**Checkpoint**: In-scope board and chat interactions are smoother without broad rerender storms or unbounded continuous listeners.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Re-run the documented guardrails, compare results against the baseline, and either defer broader work or record the next structural step.

- [ ] T023 [P] Re-run backend regression suites in `backend/tests/unit/test_cache.py`, `backend/tests/unit/test_api_board.py`, `backend/tests/unit/test_api_projects.py`, and `backend/tests/unit/test_copilot_polling.py`; record results in `specs/001-performance-review/baseline.md`
- [ ] T024 [P] Re-run frontend regression suites in `frontend/src/hooks/useRealTimeSync.test.tsx`, `frontend/src/hooks/useBoardRefresh.test.tsx`, `frontend/src/hooks/useProjectBoard.test.tsx`, and `frontend/src/pages/ProjectsPage.test.tsx`; record results in `specs/001-performance-review/baseline.md`
- [ ] T025 Perform the final before/after network-and-profiler comparison and update `specs/001-performance-review/baseline.md` with SC-001 through SC-007 results
- [ ] T026 Document the explicit defer/follow-on decision for broader structural work in `specs/001-performance-review/research.md` using the measured outcome recorded in `specs/001-performance-review/baseline.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** — no dependencies; start immediately.
- **Phase 2: Foundational** — depends on Phase 1; blocks implementation so the refresh contract and preservation rules are fixed before code changes.
- **Phase 3: US1** — depends on Phase 2; establishes the trusted baseline package and is the MVP gate for the whole feature.
- **Phase 4: US2** — depends on US1 baseline capture and Phase 2 contract alignment.
- **Phase 5: US3** — depends on Phase 2 and should follow US2 backend change-detection work so the frontend contract consumes the final backend signal behavior.
- **Phase 6: US4** — depends on Phase 2; can begin after US3 if you want render profiling to reflect the final refresh contract.
- **Phase 7: Polish** — depends on all targeted user stories being complete.

### User Story Dependencies

- **US1 (P1)**: No dependency on other user stories; this is the measurement gate and recommended MVP scope.
- **US2 (P1)**: Depends on US1 baseline artifacts so request-reduction results can be compared against the recorded before-state.
- **US3 (P1)**: Depends on US2’s backend refresh suppression semantics to keep frontend refresh policy coherent.
- **US4 (P2)**: Depends on US1 baseline artifacts; should preferably land after US3 so responsiveness is measured against the final refresh behavior.

### Within Each User Story

- Write or extend the listed regression tests before implementation tasks in the same story.
- Finish backend change-detection before validating frontend refresh-contract behavior.
- Complete implementation tasks before recording final measurements for that story.
- Re-run the story’s independent test before moving to the next priority increment.

---

## Parallel Opportunities

- **Setup**: T001 and T002 can run in parallel because they touch different feature-doc files.
- **Foundational**: T003 and T004 can run in parallel once the feature baseline artifact exists.
- **US1**: T005 and T006 can run in parallel; both feed T007.
- **US2**: T008 and T009 can run in parallel; T010 can start after their expected assertions are defined, while T011 and T012 should proceed sequentially after T010.
- **US3**: T013 and T014 can run in parallel; T015 and T016 can proceed in parallel if the query-key contract in T017 is finished last.
- **US4**: T018 and T019 can run in parallel; T021 and T022 can run in parallel after T020 establishes the memo-sensitive render boundaries.
- **Polish**: T023 and T024 can run in parallel before T025 and T026.

---

## Parallel Example(s)

### User Story 1

```bash
# Write the guardrail checklist while manual verification steps are documented
Task: "T005 Add guardrail checklist in specs/001-performance-review/baseline.md"
Task: "T006 Add manual network/profiler script in specs/001-performance-review/quickstart.md"
```

### User Story 2

```bash
# Define backend regression expectations in parallel before changing refresh behavior
Task: "T008 Extend backend/tests/unit/test_api_board.py"
Task: "T009 Extend backend/tests/unit/test_api_projects.py and backend/tests/unit/test_copilot_polling.py"
```

### User Story 3

```bash
# Cover both halves of the refresh contract before wiring implementation
Task: "T013 Extend frontend/src/hooks/useRealTimeSync.test.tsx"
Task: "T014 Extend frontend/src/hooks/useBoardRefresh.test.tsx and frontend/src/hooks/useProjectBoard.test.tsx"
```

### User Story 4

```bash
# Profile-facing regression work can be split before implementation begins
Task: "T018 Extend frontend/src/pages/ProjectsPage.test.tsx"
Task: "T019 Extend frontend/src/hooks/useBoardControls.test.tsx and frontend/src/hooks/useProjectBoard.test.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2 to create the baseline artifact and freeze the contract.
2. Complete Phase 3 (US1) and capture the before-state measurements.
3. **Stop and validate**: confirm `specs/001-performance-review/baseline.md` is reproducible and complete before code changes proceed.

### Incremental Delivery

1. Finish Setup + Foundational work.
2. Deliver **US1** to establish the measurement gate.
3. Deliver **US2** to cut backend request waste and re-run the backend guardrails.
4. Deliver **US3** to align frontend refresh behavior with the backend contract.
5. Deliver **US4** to smooth the highest-value UI interactions.
6. Finish with Phase 7 verification and the defer/follow-on decision.

### Suggested Team Strategy

- **Engineer A**: US2 backend request-reduction work in `backend/src/` and `backend/tests/unit/`
- **Engineer B**: US3 frontend refresh-contract work in `frontend/src/hooks/` and `frontend/src/pages/`
- **Engineer C**: US4 render/listener optimization in `frontend/src/components/` once US1 baseline capture is complete

---

## Notes

- All checklist items use executable, repository-relative file paths.
- `[P]` markers are only applied where file conflicts and unmet dependencies are not expected.
- User story labels appear only on story phases.
- The recommended MVP scope is **User Story 1** because every later optimization depends on its baseline artifact.
