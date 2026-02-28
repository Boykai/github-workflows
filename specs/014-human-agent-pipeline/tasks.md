# Tasks: Add 'Human' Agent Type to Agent Pipeline

**Input**: Design documents from `/specs/014-human-agent-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are omitted per Constitution IV (Test Optionality).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Register the Human agent as a builtin constant so it is discoverable by the API and available in all pipelines

- [x] T001 Add `"human"` entry to `AGENT_DISPLAY_NAMES` dict in `backend/src/constants.py` with value `"Human"`
- [x] T002 Verify `"human"` is NOT added to `DEFAULT_AGENT_MAPPINGS` in `backend/src/constants.py` (Human is user-added, not default)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend orchestrator and pipeline changes that all user stories depend on — sub-issue creation assignment, agent assignment skip, and completion detection

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Extend `create_all_sub_issues()` in `backend/src/services/workflow_orchestrator/orchestrator.py` to detect `"human"` slug and resolve parent issue creator via `issue.user.login` for sub-issue assignee
- [x] T004 Add fallback handling in `create_all_sub_issues()` in `backend/src/services/workflow_orchestrator/orchestrator.py` — if creator cannot be resolved, create sub-issue unassigned and post warning comment on parent issue
- [x] T005 Modify agent assignment logic in `backend/src/services/copilot_polling/pipeline.py` to skip Copilot workspace/PR assignment when active agent slug is `"human"` and instead mark step as active (🔄)
- [x] T006 Extend `_check_agent_done_on_sub_or_parent()` in `backend/src/services/copilot_polling/helpers.py` to check Human sub-issue state (`closed`) via GitHub API as a completion signal
- [x] T007 Extend comment-checking logic in `backend/src/services/agent_tracking.py` to support Human `Done!` pattern — exact `^Done!$` match with no agent prefix, authorized only from the sub-issue assignee

**Checkpoint**: Foundation ready — Human agent appears in API, sub-issues are created and assigned correctly, completion detection works for both signals

---

## Phase 3: User Story 1 — Add a Human Step to a Pipeline (Priority: P1) 🎯 MVP

**Goal**: Pipeline creators can see 'Human' in the '+ Add Agent' dropdown in any pipeline column and add it. The Human card is visually distinct with a person icon and 'Human' label.

**Independent Test**: Open any Agent Pipeline, click '+ Add Agent' in any column, select 'Human', verify card appears with person icon and 'Human' label. Also verify existing pipelines and new pipelines both show the option.

### Implementation for User Story 1

- [x] T008 [US1] Add conditional rendering in `frontend/src/components/board/AgentTile.tsx` to display a person icon (User SVG from lucide-react) when agent slug is `"human"` instead of the default letter avatar
- [x] T009 [US1] Add 'Human' label styling in `frontend/src/components/board/AgentTile.tsx` to visually distinguish the Human agent card from automated agent cards (e.g., different badge color or icon treatment)

**Checkpoint**: User Story 1 complete — Human step is visible and visually distinct in all pipeline columns. This is the MVP.

---

## Phase 4: User Story 2 — Human Step Triggers Sub-Issue Creation and Assignment (Priority: P1)

**Goal**: When a pipeline with a Human step is triggered, the system creates a GitHub Sub Issue assigned to the parent issue creator using the same creation mechanism as automated agents.

**Independent Test**: Create a pipeline with a Human step, trigger it via a GitHub Issue, verify a Sub Issue is created with title `[human] <parent title>` and is assigned to the issue creator. Test the unresolved-creator fallback.

### Implementation for User Story 2

- [x] T010 [US2] Add Human-specific sub-issue body template in `backend/src/services/workflow_orchestrator/orchestrator.py` — body should instruct the human to close the sub-issue or comment 'Done!' on the parent issue
- [x] T011 [US2] Wire the issue creator assignment into `assign_issue()` call within `create_all_sub_issues()` in `backend/src/services/workflow_orchestrator/orchestrator.py` so the sub-issue is assigned at creation time
- [x] T012 [US2] Add warning comment logic in `backend/src/services/workflow_orchestrator/orchestrator.py` — when creator cannot be resolved, post `⚠️ Could not resolve issue creator for Human step assignment` on the parent issue

**Checkpoint**: User Story 2 complete — Human sub-issues are created and correctly assigned to the issue creator, with proper fallback handling.

---

## Phase 5: User Story 3 — Human Step Completion Advances the Pipeline (Priority: P1)

**Goal**: The pipeline automatically continues when the human closes the Sub Issue or comments exactly 'Done!' on the parent issue. Both signals are idempotent.

**Independent Test**: Trigger a pipeline with a Human step, then (a) close the Sub Issue and verify the pipeline advances, or (b) comment 'Done!' as the assigned user and verify the pipeline advances. Test that non-assigned user comments and wrong casing are ignored.

### Implementation for User Story 3

- [x] T013 [US3] Add sub-issue state polling in `backend/src/services/copilot_polling/helpers.py` — on each polling cycle, fetch Human sub-issue state via GitHub API and trigger `_advance_pipeline()` if state is `closed`
- [x] T014 [US3] Add `Done!` comment author validation in `backend/src/services/copilot_polling/helpers.py` — compare comment author with Human sub-issue assignee before accepting as completion signal
- [x] T015 [US3] Verify idempotent advancement in `backend/src/services/copilot_polling/pipeline.py` — ensure `_advance_pipeline()` checks `pipeline.current_agent == "human"` before advancing so duplicate signals are no-ops

**Checkpoint**: User Story 3 complete — pipeline correctly advances on either completion signal, with authorization and idempotency enforced.

---

## Phase 6: User Story 4 — Human Step Works in Any Pipeline Position (Priority: P2)

**Goal**: The Human step behaves correctly regardless of position — first, middle, or last step in any pipeline column.

**Independent Test**: Create three pipelines with the Human step at beginning, middle, and end positions. Trigger each and verify the Human step activates at the correct time and downstream steps wait.

### Implementation for User Story 4

- [x] T016 [US4] Verify and adjust ordering logic in `backend/src/services/copilot_polling/pipeline.py` to ensure Human steps at any position (first, middle, last) correctly block downstream steps and advance when complete
- [x] T017 [US4] Verify pipeline column completion logic in `backend/src/services/copilot_polling/pipeline.py` — column should not be marked complete until a Human step at the last position finishes

**Checkpoint**: User Story 4 complete — Human steps work in all pipeline positions with correct blocking and advancement behavior.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [x] T018 [P] Update `specs/014-human-agent-pipeline/checklists/requirements.md` to track FR-001 through FR-012 completion status
- [ ] T019 Run `specs/014-human-agent-pipeline/quickstart.md` validation test cases (all 13 scenarios) end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (Phase 1) completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Setup (Phase 1) — frontend-only, can start in parallel with Phase 2
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) — requires orchestrator changes from T003, T004
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) — requires completion detection from T006, T007
- **User Story 4 (Phase 6)**: Depends on User Stories 2 and 3 — positional testing requires sub-issue creation and completion to work
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1) — No backend dependencies (frontend-only changes)
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) — May overlap with US2 if orchestrator changes are committed
- **User Story 4 (P2)**: Depends on US2 and US3 being complete — positional verification requires full pipeline flow

### Within Each User Story

- Models/constants before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 + Phase 3**: T001/T002 (backend constants) and T008/T009 (frontend) touch different codebases — can run in parallel
- **Phase 2**: T005 (pipeline.py), T006 (helpers.py), T007 (agent_tracking.py) modify different files — can run in parallel after T003/T004
- **Phase 4**: T010, T011, T012 all modify orchestrator.py — must run sequentially
- **Phase 5**: T013 (helpers.py) and T015 (pipeline.py) modify different files — can run in parallel; T014 depends on T013
- **Phase 3 vs Phase 4/5**: Frontend work (US1) is independent of backend orchestrator/pipeline work (US2, US3) — can proceed in parallel

---

## Parallel Example: User Story 1

```bash
# Frontend changes can start immediately after Phase 1 Setup:
Task: T008 "Add person icon for Human agent in frontend/src/components/board/AgentTile.tsx"
Task: T009 "Add Human label styling in frontend/src/components/board/AgentTile.tsx"
# T009 depends on T008 (same file), so these run sequentially
```

## Parallel Example: Phase 2 (Foundational)

```bash
# After T003/T004 (orchestrator changes), these can run in parallel:
Task: T005 "Skip Copilot assignment for Human in backend/src/services/copilot_polling/pipeline.py"
Task: T006 "Add sub-issue closed check in backend/src/services/copilot_polling/helpers.py"
Task: T007 "Add Human Done! pattern in backend/src/services/agent_tracking.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002) — Human agent registered as builtin
2. Complete Phase 3: User Story 1 (T008–T009) — Human visible in UI
3. **STOP and VALIDATE**: Verify Human appears in '+ Add Agent' dropdown with person icon
4. Deploy/demo if ready — users can see the Human option even before backend pipeline support

### Incremental Delivery

1. Setup (Phase 1) + US1 (Phase 3) → Human visible in UI → Demo (MVP!)
2. Foundational (Phase 2) → Backend infrastructure ready
3. US2 (Phase 4) → Sub-issues created and assigned → Demo
4. US3 (Phase 5) → Completion detection works → Demo
5. US4 (Phase 6) → Positional flexibility verified → Demo
6. Polish (Phase 7) → Checklists updated, end-to-end validated

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup (Phase 1) together
2. Once Setup is done:
   - Developer A: User Story 1 (frontend — T008, T009)
   - Developer B: Foundational Phase 2 (backend — T003–T007)
3. After Foundational completes:
   - Developer A: User Story 4 verification (T016, T017)
   - Developer B: User Story 2 (T010–T012) → User Story 3 (T013–T015)
4. Polish phase after all stories complete

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- No new database tables or migrations required (data-model.md confirms this)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
