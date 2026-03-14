# Tasks: Parallel Agent Layout in Pipelines

**Input**: Design documents from `/specs/033-parallel-agent-layout/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pipeline-api.yaml, quickstart.md

**Tests**: The feature specification does not request a TDD workflow, so no dedicated test-writing tasks are included. Existing backend and frontend validation commands plus the quickstart scenarios must pass after implementation.

**Organization**: Tasks are grouped by user story so each story can be implemented, validated, and demonstrated independently. User Story 1 delivers the editing MVP; User Story 2 completes the core runtime contract.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React/TypeScript), `backend/src/` (Python/FastAPI)
- **Backend models/services**: `backend/src/models/`, `backend/src/services/`, `backend/src/api/`
- **Frontend pipeline UI**: `frontend/src/components/pipeline/`, `frontend/src/hooks/`, `frontend/src/pages/`, `frontend/src/types/`
- **Feature docs**: `specs/033-parallel-agent-layout/`

---

## Phase 1: Setup

**Purpose**: Establish the shared stage-execution contract and seed data every later story depends on.

- [x] T001 Add the `execution_mode` field and validation for `PipelineStage` in `backend/src/models/pipeline.py`
- [x] T002 [P] Mirror `PipelineStage.execution_mode` in `frontend/src/types/index.ts`
- [x] T003 [P] Add explicit sequential `execution_mode` values for built-in pipeline stage definitions in `backend/src/services/pipelines/service.py` and `frontend/src/data/preset-pipelines.ts`

**Checkpoint**: Backend and frontend agree on the stage shape used by saved pipelines, preset pipelines, and future runtime updates.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared normalization and state-management plumbing required before any user story work can land safely.

**⚠️ CRITICAL**: No user story work should begin until create/edit flows, runtime state, and stage-mode normalization all understand sequential vs. parallel stages.

- [x] T004 Normalize missing, invalid, or single-agent `execution_mode` values during pipeline load/save in `backend/src/services/pipelines/service.py`
- [x] T005 [P] Extend stage-to-status mapping and runtime pipeline state for parallel metadata in `backend/src/services/workflow_orchestrator/config.py` and `backend/src/services/workflow_orchestrator/models.py`
- [x] T006 [P] Add stage-mode setters, add/remove-agent normalization, and save-ready transforms in `frontend/src/hooks/usePipelineConfig.ts`
- [x] T007 [P] Thread stage-level execution-mode state through `frontend/src/pages/AgentsPipelinePage.tsx` and `frontend/src/components/pipeline/PipelineBoard.tsx`

**Checkpoint**: The application can store, normalize, and propagate stage execution mode without changing user-visible behavior yet.

---

## Phase 3: User Story 1 - Add Parallel Agents to a Pipeline Stage (Priority: P1) 🎯 MVP

**Goal**: Let pipeline builders place multiple agents into one stage while creating or editing a pipeline and persist that grouping.

**Independent Test**: Open the Create or Edit pipeline flow, add two agents into the same stage using the side-by-side affordance, save, and confirm the reopened pipeline still shows those agents grouped in one stage.

### Implementation for User Story 1

- [x] T008 [US1] Add an "Add Parallel Agent" affordance and same-stage grouping interactions in `frontend/src/components/pipeline/StageCard.tsx`
- [x] T009 [P] [US1] Create `frontend/src/components/pipeline/ParallelStageGroup.tsx` to render multiple agents inside one shared stage container
- [x] T010 [US1] Persist grouped-stage create/edit saves and reloads in `frontend/src/pages/AgentsPipelinePage.tsx` and `frontend/src/hooks/usePipelineConfig.ts`

**Checkpoint**: Users can configure and save a parallel stage from the pipeline editor. This is the editing MVP.

---

## Phase 4: User Story 2 - Parallel Agents Execute Simultaneously at Runtime (Priority: P1)

**Goal**: Fan out all agents in a parallel stage at the same time and block the next stage until every parallel agent finishes.

**Independent Test**: Launch a pipeline whose second stage contains two parallel agents followed by a sequential third stage, then verify both parallel agents start together and the third stage waits for both completions.

### Implementation for User Story 2

- [x] T011 [US2] Dispatch agents in `execution_mode == "parallel"` stages concurrently with a barrier join in `backend/src/services/copilot_polling/pipeline.py`
- [x] T012 [US2] Preserve existing sequential execution for default and single-agent stages while mapping multi-agent stages correctly in `backend/src/services/copilot_polling/pipeline.py` and `backend/src/services/workflow_orchestrator/config.py`
- [x] T013 [US2] Ensure parallel stage definitions round-trip through pipeline launch and CRUD surfaces in `backend/src/services/pipelines/service.py` and `backend/src/api/pipelines.py`

**Checkpoint**: Parallel stages now have real runtime meaning and remain backward-compatible with sequential pipelines.

---

## Phase 5: User Story 3 - Visual Differentiation of Parallel vs. Sequential Stages (Priority: P2)

**Goal**: Make parallel stages visually distinct so builders can recognize stage boundaries and execution mode at a glance.

**Independent Test**: Create a pipeline with sequential and parallel stages, then verify parallel siblings sit inside a labeled shared container and connectors only appear between stage groups.

### Implementation for User Story 3

- [x] T014 [US3] Add shared parallel-stage styling, label, and icon treatment in `frontend/src/components/pipeline/ParallelStageGroup.tsx` and `frontend/src/components/pipeline/StageCard.tsx`
- [x] T015 [P] [US3] Render connector lines only between stage groups in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T016 [P] [US3] Add sequential-vs-parallel hover copy and tooltip wiring in `frontend/src/components/pipeline/AgentNode.tsx` and `frontend/src/components/pipeline/StageCard.tsx`

**Checkpoint**: Builders can visually distinguish parallel and sequential execution without opening additional controls.

---

## Phase 6: User Story 4 - Parallel Stage Failure Handling (Priority: P2)

**Goal**: Halt the pipeline cleanly when any parallel agent fails and make it obvious which agent(s) failed.

**Independent Test**: Run a pipeline whose parallel stage has one failing agent and confirm the pipeline stops, the stage is marked failed, and the failed agent is identifiable in the UI.

### Implementation for User Story 4

- [x] T017 [US4] Track per-agent running/completed/failed outcomes and failed agent IDs for parallel stages in `backend/src/services/copilot_polling/pipeline.py` and `backend/src/services/workflow_orchestrator/models.py`
- [x] T018 [US4] Stop pipeline advancement and mark the stage failed whenever any parallel agent fails in `backend/src/services/copilot_polling/pipeline.py`
- [x] T019 [US4] Surface failed parallel stages and highlight failed sibling agents in `frontend/src/components/pipeline/AgentNode.tsx` and `frontend/src/components/pipeline/PipelineBoard.tsx`

**Checkpoint**: Parallel failures are deterministic, visible, and do not allow later stages to start.

---

## Phase 7: User Story 5 - Remove Agent from Parallel Stage (Priority: P3)

**Goal**: Let builders remove one agent from a parallel group without corrupting the rest of the stage structure.

**Independent Test**: Start with a three-agent parallel stage, remove one agent, and confirm the remaining agents stay grouped; then remove another and confirm the last agent reverts to a normal sequential stage.

### Implementation for User Story 5

- [x] T020 [US5] Auto-revert parallel stages to sequential when removals leave fewer than two agents in `frontend/src/hooks/usePipelineConfig.ts`
- [x] T021 [US5] Add remove and move-out controls for parallel siblings, including empty-stage cleanup, in `frontend/src/components/pipeline/StageCard.tsx` and `frontend/src/components/pipeline/ParallelStageGroup.tsx`

**Checkpoint**: Users can safely undo parallel grouping from the editor without rebuilding the whole pipeline.

---

## Phase 8: User Story 6 - Reorder Agents and Stages via Drag-and-Drop (Priority: P3)

**Goal**: Support drag-and-drop reordering inside a parallel stage and across stage groups without breaking group membership.

**Independent Test**: Reorder agents left-to-right inside one parallel stage and then drag that entire stage ahead of or behind another stage, confirming the saved pipeline preserves both order changes.

### Implementation for User Story 6

- [x] T022 [US6] Enable left-to-right sorting for parallel siblings with `rectSortingStrategy` in `frontend/src/components/pipeline/StageCard.tsx`
- [x] T023 [US6] Update stage drag-and-drop to move sequential stages and whole parallel groups as units in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T024 [US6] Persist reordered stage order and parallel sibling order in `frontend/src/hooks/usePipelineConfig.ts` and `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: Builders can restructure mixed pipelines without losing stage grouping semantics.

---

## Phase 9: User Story 7 - Real-Time Status Indicators for Parallel Agents (Priority: P3)

**Goal**: Show each parallel agent's live running/completed/failed state while a pipeline is executing.

**Independent Test**: Watch a running pipeline with a parallel stage and confirm each sibling agent shows live status changes independently as the stage progresses.

### Implementation for User Story 7

- [x] T025 [US7] Emit per-agent parallel status updates from the runtime pipeline flow in `backend/src/services/copilot_polling/pipeline.py` and `backend/src/services/workflow_orchestrator/models.py`
- [x] T026 [P] [US7] Thread parallel agent status payloads through `frontend/src/types/index.ts` and `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T027 [US7] Render running, completed, and failed indicators for parallel agents in `frontend/src/components/pipeline/AgentNode.tsx`

**Checkpoint**: Monitoring users can see which agents in a parallel stage are still running and which have already completed or failed.

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Validate the full mixed-execution experience, preserve backward compatibility, and run existing quality gates.

- [x] T028 [P] Validate the create/edit, runtime, failure, removal, reorder, and status scenarios from `specs/033-parallel-agent-layout/quickstart.md` against `frontend/src/pages/AgentsPipelinePage.tsx` and the backend pipeline services
- [x] T029 [P] Run `uv run --extra dev ruff check src/` and `uv run --extra dev pytest tests/unit/ -x` in `backend/`, plus `npm run lint`, `npm run type-check`, `npm run test`, and `npm run build` in `frontend/` after the pipeline changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story phases (Phases 3-9)**: Depend on Foundational completion
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependency Graph

```text
Setup -> Foundational -> US1 -> US2 -> {US4, US7}
                          ├-> US3 -> US6
                          └-> US5
US5 -> US6
{US3, US4, US6, US7} -> Polish
```

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — establishes the create/edit interaction and persistence needed to configure any parallel stage
- **US2 (P1)**: Depends on US1's saved stage structure so runtime execution can consume real parallel-stage definitions
- **US3 (P2)**: Depends on US1's grouped-stage UI so styling, tooltips, and connector changes apply to the finished editor surface
- **US4 (P2)**: Depends on US2's parallel runtime orchestration so failure states can be detected and surfaced accurately
- **US5 (P3)**: Depends on US1's grouping model so removals can dissolve or preserve groups correctly
- **US6 (P3)**: Depends on US3's grouped-stage presentation and US5's removal normalization to keep drag-and-drop behavior stable
- **US7 (P3)**: Depends on US2's runtime barrier logic and US4's per-agent outcome tracking so live indicators have accurate source data

### Within Each User Story

- Shared model/state updates before editor or runtime UI changes
- Stage grouping before styling and connector polish
- Runtime concurrency before failure handling and live status indicators
- Removal normalization before reorder persistence
- Finish each story's checkpoint before moving into later polish work

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 defines the backend contract
- **Phase 2**: T005, T006, and T007 can run in parallel after T004 establishes normalization rules
- **US1**: T009 can run in parallel with the interaction work in T008 before both converge in T010
- **US3**: T015 and T016 can run in parallel once T014 defines the shared parallel-stage container
- **US7**: T026 can start once T025 defines the runtime payload shape
- **Phase 10**: T028 and T029 can run in parallel after feature work is complete

---

## Parallel Execution Examples

### User Story 1

```text
Task T008: Add an "Add Parallel Agent" affordance in frontend/src/components/pipeline/StageCard.tsx
Task T009: Create frontend/src/components/pipeline/ParallelStageGroup.tsx
Task T010: Persist grouped-stage saves in frontend/src/pages/AgentsPipelinePage.tsx and frontend/src/hooks/usePipelineConfig.ts
```

### User Story 2

```text
No safe same-story parallel split is recommended.
T011-T013 all change the backend execution flow and should land sequentially.
```

### User Story 3

```text
Task T014: Add shared parallel-stage styling in frontend/src/components/pipeline/ParallelStageGroup.tsx and frontend/src/components/pipeline/StageCard.tsx
Task T015: Update group-level connector rendering in frontend/src/components/pipeline/PipelineBoard.tsx
Task T016: Add execution-mode tooltips in frontend/src/components/pipeline/AgentNode.tsx and frontend/src/components/pipeline/StageCard.tsx
```

### User Story 4

```text
No safe same-story parallel split is recommended.
T017-T019 depend on one another's runtime state contract and failure presentation.
```

### User Story 5

```text
No safe same-story parallel split is recommended.
T020 should establish dissolve-to-sequential behavior before T021 adds the editor controls that rely on it.
```

### User Story 6

```text
No safe same-story parallel split is recommended.
T022-T024 all share drag-and-drop ordering state and should be completed in order.
```

### User Story 7

```text
Task T025: Emit per-agent runtime status updates in backend/src/services/copilot_polling/pipeline.py and backend/src/services/workflow_orchestrator/models.py
Task T026: Thread status payloads through frontend/src/types/index.ts and frontend/src/components/pipeline/PipelineBoard.tsx
Task T027: Render per-agent indicators in frontend/src/components/pipeline/AgentNode.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Save and reopen a pipeline containing a side-by-side stage
5. Demo the editor MVP before starting runtime changes

### Incremental Delivery

1. Complete Setup + Foundational so stage execution mode is stable across backend and frontend
2. Add User Story 1 to unlock parallel-stage authoring (**editing MVP**)
3. Add User Story 2 to make parallel stages execute concurrently (**runtime MVP complete**)
4. Add User Story 3 and User Story 4 to make grouped stages understandable and safe in failure cases
5. Add User Stories 5-7 for editing ergonomics and live observability
6. Finish with Phase 10 validation and existing-command quality gates

### Parallel Team Strategy

With multiple developers:

1. Complete Setup + Foundational together
2. Then split work by surface area:
   - Developer A: US1 + US3 editor layout work in `frontend/src/components/pipeline/`
   - Developer B: US2 + US4 backend runtime orchestration in `backend/src/services/`
   - Developer C: US5 + US6 editor-state and drag/drop persistence in `frontend/src/hooks/` and `frontend/src/pages/`
   - Developer D: US7 live-status wiring once US2 and US4 stabilize

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 29 |
| **Setup tasks** | 3 (T001-T003) |
| **Foundational tasks** | 4 (T004-T007) |
| **US1 tasks** | 3 (T008-T010) |
| **US2 tasks** | 3 (T011-T013) |
| **US3 tasks** | 3 (T014-T016) |
| **US4 tasks** | 3 (T017-T019) |
| **US5 tasks** | 2 (T020-T021) |
| **US6 tasks** | 3 (T022-T024) |
| **US7 tasks** | 3 (T025-T027) |
| **Polish tasks** | 2 (T028-T029) |
| **Parallel opportunities** | 11 tasks marked `[P]` across setup, foundational plumbing, UI styling, live-status wiring, and final validation |
| **MVP scope** | Phases 1-3 (T001-T010) for editor support; add Phase 4 (T011-T013) to complete the runtime contract |
| **Independent test criteria** | Each user story phase includes a standalone manual validation scenario derived from `spec.md` |
| **Format validation** | Every task uses the required `- [ ] T### [P?] [US?] Description with file path` checklist structure |

---

## Notes

- [P] tasks touch different files or can proceed once the task immediately before them establishes the shared contract
- No dedicated automated-test authoring tasks are included because the specification did not request TDD; validation is captured in Phase 10 instead
- `execution_mode` must remain backward-compatible by defaulting old stages to sequential behavior during load and save
- A stage with fewer than two agents should normalize back to sequential mode when pipelines are saved or edited
- Parallel runtime work must wait for all siblings to finish before advancing and must stop the pipeline when any sibling fails
