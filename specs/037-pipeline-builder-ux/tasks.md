# Tasks: Reinvent Agent Pipeline Creation UX

**Input**: Design documents from `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/`
**Prerequisites**: `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/plan.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/spec.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/research.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/data-model.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/contracts/pipeline-api.md`, `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/quickstart.md`

**Tests**: Tests are required for this feature because the specification includes mandatory user-story testing scenarios and the implementation plan calls out existing frontend and backend pipeline test suites that must be extended.

**Organization**: Tasks are grouped by user story so each story can be implemented, verified, and demonstrated independently while preserving a small shared setup/foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Required only for user story phases (`[US1]`, `[US2]`, etc.)
- Every task includes one or more exact file paths

## Path Conventions

- **Repository root**: `/home/runner/work/github-workflows/github-workflows`
- **Backend**: `/home/runner/work/github-workflows/github-workflows/backend/src/` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/`
- **Frontend**: `/home/runner/work/github-workflows/github-workflows/frontend/src/`
- **Feature docs**: `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/`

---

## Phase 1: Setup

**Purpose**: Establish the shared grouped-pipeline contract and seed data that every story depends on.

- [ ] T001 Add the `ExecutionGroup` schema and grouped `PipelineStage` fields in `/home/runner/work/github-workflows/github-workflows/backend/src/models/pipeline.py`
- [ ] T002 [P] Mirror `ExecutionGroup` and grouped `PipelineStage` TypeScript types in `/home/runner/work/github-workflows/github-workflows/frontend/src/types/index.ts`
- [ ] T003 [P] Update preset pipeline fixtures to the grouped shape in `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py` and `/home/runner/work/github-workflows/github-workflows/frontend/src/data/preset-pipelines.ts`

**Checkpoint**: Backend models, frontend types, and preset data all share the same group-based pipeline vocabulary.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared migration, normalization, and mutation plumbing that blocks every user story.

**⚠️ CRITICAL**: No user story work should start until grouped pipeline data can be loaded, mutated, and saved consistently.

- [ ] T004 Create the legacy-to-group migration utility in `/home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.ts`
- [ ] T005 [P] Apply load/save migration plumbing in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineMigration.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T006 [P] Normalize grouped and legacy pipeline payloads on backend write paths in `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/api/pipelines.py`
- [ ] T007 [P] Extend board mutation APIs for group CRUD, agent moves, and order reindexing in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts`

**Checkpoint**: The application can ingest old and new pipeline shapes, expose group-level mutations, and persist grouped data without user-facing UX changes yet.

---

## Phase 3: User Story 1 - Compose Mixed Execution Groups Within a Stage (Priority: P1) 🎯 MVP

**Goal**: Let pipeline authors build one stage with multiple ordered execution groups, each with its own agent list and persisted structure.

**Independent Test**: Create a new pipeline, add one stage, add multiple execution groups with different modes, assign agents to each group, save, and verify the reopened pipeline preserves the group order, modes, and assignments.

### Tests for User Story 1

- [ ] T008 [P] [US1] Add grouped-stage migration and persistence tests in `/home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.test.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.test.tsx`
- [ ] T009 [P] [US1] Add grouped-stage model and API regression tests in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_models.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_pipelines.py`

### Implementation for User Story 1

- [ ] T010 [US1] Create the execution-group container component in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx`
- [ ] T011 [US1] Render multiple ordered groups and the “Add Group” affordance inside `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.tsx`
- [ ] T012 [P] [US1] Add group create/remove/reorder mutations and default empty-group behavior in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T013 [US1] Persist ordered group structures through the editor flow in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/AgentsPipelinePage.tsx` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py`

**Checkpoint**: A single stage can contain multiple vertically ordered execution groups, and that structure survives save/reload.

---

## Phase 4: User Story 2 - Drag and Drop Agents Across Stages (Priority: P2)

**Goal**: Allow a user to move an agent card between execution groups in different stage columns in one gesture while preserving model and tool settings.

**Independent Test**: Create a pipeline with two stages, drag an agent from a group in Stage 1 to a group in Stage 2, and confirm the agent appears in the new group with its original model selection and tool configuration intact.

### Tests for User Story 2

- [ ] T014 [P] [US2] Add cross-stage drag-and-drop coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.test.tsx`
- [ ] T015 [P] [US2] Add drag-cancel, drop-indicator, and preserved-agent-settings coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.test.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/AgentNode.test.tsx`

### Implementation for User Story 2

- [ ] T016 [US2] Lift drag-and-drop orchestration to a board-level `DndContext` in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx`
- [ ] T017 [P] [US2] Register each execution group as a drop target and render hover feedback in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx`
- [ ] T018 [US2] Move agents across groups and stages without losing model or tool data in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T019 [US2] Add drag-cancel recovery, empty-source-group prompts, and keyboard-sensor support in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/AgentNode.tsx`

**Checkpoint**: Agents can move across stage columns in one gesture, valid drop targets are visible, invalid drops revert cleanly, and keyboard drag support remains intact.

---

## Phase 5: User Story 3 - Reorder Agents Within and Between Groups (Priority: P3)

**Goal**: Support agent reordering inside a group and moving agents between groups within the same stage while preserving the intended execution order.

**Independent Test**: Build a stage with two groups, reorder agents inside one group, move an agent from the first group into the second group, and confirm the saved order matches the user’s final arrangement.

### Tests for User Story 3

- [ ] T020 [P] [US3] Add intra-group and inter-group reorder tests in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.test.tsx`
- [ ] T021 [P] [US3] Add group-mutation ordering coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.test.tsx`

### Implementation for User Story 3

- [ ] T022 [US3] Support series and parallel sortable strategies per group in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx`
- [ ] T023 [US3] Implement within-stage moves, insertion indexes, and stable order reindexing in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts`
- [ ] T024 [US3] Add execution-group reorder controls and stage-level sequencing updates in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx`

**Checkpoint**: Authors can reorder agents within a group, move agents between groups in the same stage, and reorder the groups themselves to change top-to-bottom execution.

---

## Phase 6: User Story 4 - Toggle Execution Mode Per Group (Priority: P4)

**Goal**: Let authors switch each execution group between series and parallel modes with an immediate layout update and persisted mode state.

**Independent Test**: Create a group with two agents, toggle it between series and parallel, and verify the layout, badge text, and saved configuration all update correctly.

### Tests for User Story 4

- [ ] T025 [P] [US4] Add execution-mode toggle and layout tests in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.test.tsx`
- [ ] T026 [P] [US4] Add grouped execution-mode validation coverage in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_models.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_pipelines.py`

### Implementation for User Story 4

- [ ] T027 [US4] Add the single-interaction series/parallel toggle and mode badge in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx`
- [ ] T028 [P] [US4] Switch group rendering between vertical-list and side-by-side-grid layouts in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/AgentNode.tsx`
- [ ] T029 [US4] Persist per-group `execution_mode` updates through `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py`

**Checkpoint**: Each execution group exposes its own mode toggle, visual indicator, responsive layout, and durable saved mode.

---

## Phase 7: User Story 5 - Manage Stage Columns (Priority: P5)

**Goal**: Keep stage add/remove/reorder flows working with the new group model, including safe removal of populated stages.

**Independent Test**: Add and reorder stages, remove a stage containing assigned agents, confirm the removal prompt lists affected agents, and verify the saved pipeline reflects the remaining grouped stages in the expected order.

### Tests for User Story 5

- [ ] T030 [P] [US5] Add grouped stage CRUD and confirmation-dialog coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/AgentsPipelinePage.test.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.test.tsx`
- [ ] T031 [P] [US5] Add default-empty-group stage lifecycle coverage in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.test.tsx`

### Implementation for User Story 5

- [ ] T032 [US5] Ensure every newly added stage starts with one empty execution group in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts`
- [ ] T033 [US5] Add populated-stage removal confirmation with agent summaries in `/home/runner/work/github-workflows/github-workflows/frontend/src/pages/AgentsPipelinePage.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/ui/confirmation-dialog.tsx`
- [ ] T034 [US5] Preserve grouped agent assignments during stage reorder and removal flows in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts`

**Checkpoint**: Stage columns remain fully manageable without silently dropping grouped agent assignments or leaving invalid empty-stage structures.

---

## Phase 8: User Story 6 - Backward-Compatible Pipeline Loading (Priority: P6)

**Goal**: Load old single-group-per-stage pipelines into the new builder automatically and save them back in the grouped format without data loss.

**Independent Test**: Load a legacy pipeline payload with flat stage agents and a stage-level execution mode, verify the builder renders one migrated group per stage with the original agents and settings, then save and confirm the payload is persisted in grouped form.

### Tests for User Story 6

- [ ] T035 [P] [US6] Add legacy-pipeline migration unit tests in `/home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.test.ts`
- [ ] T036 [P] [US6] Add legacy payload normalization regression tests in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_pipelines.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_pipeline_groups.py`

### Implementation for User Story 6

- [ ] T037 [US6] Finalize `migratePipelineToGroupFormat` edge cases for empty stages and preserved agent metadata in `/home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.ts`
- [ ] T038 [P] [US6] Apply migration on pipeline load and save hydration in `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineMigration.ts` and `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts`
- [ ] T039 [US6] Persist legacy payloads in grouped form on backend create/update flows in `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/models/pipeline.py`
- [ ] T040 [US6] Keep migrated presets and loaded pipelines visually consistent in `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py` and `/home/runner/work/github-workflows/github-workflows/frontend/src/data/preset-pipelines.ts`

**Checkpoint**: Existing saved pipelines open without data loss, render in the new grouped UI, and save back using the canonical grouped structure.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Validate the full workflow, cover accessibility/performance checks, and run the existing project quality gates after implementation.

- [ ] T041 [P] Validate the scenarios in `/home/runner/work/github-workflows/github-workflows/specs/037-pipeline-builder-ux/quickstart.md` against `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx` and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx`
- [ ] T042 [P] Run frontend validation commands from `/home/runner/work/github-workflows/github-workflows/frontend/package.json` against `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/`, `/home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.ts`
- [ ] T043 [P] Run backend validation commands from `/home/runner/work/github-workflows/github-workflows/backend/pyproject.toml` against `/home/runner/work/github-workflows/github-workflows/backend/src/models/pipeline.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/pipelines/service.py`, and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_pipeline_groups.py`
- [ ] T044 [P] Verify keyboard-only drag-and-drop and empty-state accessibility behaviors in `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx`, `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.tsx`, and `/home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — blocks all user stories
- **User Story phases (Phases 3-8)**: Depend on Foundational completion
- **Polish (Phase 9)**: Depends on all completed user stories that will ship

### User Story Dependency Graph

```text
Setup -> Foundational -> US1 -> US2 -> US3
                       ├-> US4
                       ├-> US5
                       └-> US6
{US2, US3, US4, US5, US6} -> Polish
```

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — establishes grouped stage rendering, mutation, and persistence needed for every later story
- **US2 (P2)**: Depends on US1’s execution-group containers and group-aware mutations so cross-stage dragging has valid source/target structures
- **US3 (P3)**: Depends on US2’s board-level drag-and-drop plumbing so within-stage and inter-group reordering can reuse the same mechanics
- **US4 (P4)**: Depends on US1’s per-group data model and rendering surface so execution mode can move from the stage to the group level
- **US5 (P5)**: Depends on US1’s default-group behavior and US2’s board updates so stage add/remove/reorder flows preserve grouped assignments safely
- **US6 (P6)**: Depends only on Foundational migration/normalization work and can proceed in parallel with later stories, but must be complete before release to protect existing saved pipelines

### Within Each User Story

- Test tasks should fail before implementation tasks begin
- Shared model and migration updates come before UI interactions that rely on them
- State-mutation work comes before persistence wiring and visual polish
- Each story’s checkpoint should be manually validated before moving to the next phase

### Parallel Opportunities

- **Phase 1**: T002 and T003 can run in parallel after T001 defines the grouped backend contract
- **Phase 2**: T005, T006, and T007 can run in parallel after T004 defines the migration shape
- **US1**: T008 and T009 can run in parallel; T012 can start once T010/T011 define the component surfaces
- **US2**: T014 and T015 can run in parallel; T017 can proceed alongside T016 once the board-level DnD contract is set
- **US3**: T020 and T021 can run in parallel before T022-T024
- **US4**: T025 and T026 can run in parallel; T028 can run in parallel with T029 after T027 introduces the toggle contract
- **US5**: T030 and T031 can run in parallel before T032-T034
- **US6**: T035 and T036 can run in parallel; T038 and T040 can run in parallel after T037 defines migration edge cases
- **Phase 9**: T041-T044 can run in parallel after implementation stabilizes

---

## Parallel Execution Examples

### User Story 1

```text
Task T008: Add grouped-stage migration and persistence tests in /home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.test.ts and /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.test.tsx
Task T009: Add grouped-stage model and API regression tests in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_models.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_pipelines.py
Task T010: Create /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx
Task T011: Render multiple ordered groups in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.tsx
```

### User Story 2

```text
Task T014: Add cross-stage drag-and-drop coverage in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.test.tsx
Task T015: Add drag-cancel and preserved-settings coverage in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/StageCard.test.tsx and /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/AgentNode.test.tsx
Task T017: Register group drop targets in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx and /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.tsx
```

### User Story 3

```text
Task T020: Add reorder tests in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.test.tsx
Task T021: Add mutation ordering coverage in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.test.tsx
Task T023: Implement insertion-index and order reindexing in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineBoardMutations.ts
```

### User Story 4

```text
Task T025: Add execution-mode toggle tests in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.test.tsx
Task T026: Add grouped execution-mode validation coverage in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_models.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_pipelines.py
Task T028: Switch between list and grid layouts in /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/ExecutionGroupCard.tsx and /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/AgentNode.tsx
```

### User Story 5

```text
Task T030: Add grouped stage CRUD coverage in /home/runner/work/github-workflows/github-workflows/frontend/src/pages/AgentsPipelinePage.test.tsx and /home/runner/work/github-workflows/github-workflows/frontend/src/components/pipeline/PipelineBoard.test.tsx
Task T031: Add default-empty-group stage lifecycle coverage in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.test.tsx
Task T033: Add populated-stage removal confirmation in /home/runner/work/github-workflows/github-workflows/frontend/src/pages/AgentsPipelinePage.tsx and /home/runner/work/github-workflows/github-workflows/frontend/src/components/ui/confirmation-dialog.tsx
```

### User Story 6

```text
Task T035: Add legacy-pipeline migration unit tests in /home/runner/work/github-workflows/github-workflows/frontend/src/lib/pipelineMigration.test.ts
Task T036: Add backend legacy normalization tests in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_api_pipelines.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_pipeline_groups.py
Task T038: Apply load-time migration in /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineMigration.ts and /home/runner/work/github-workflows/github-workflows/frontend/src/hooks/usePipelineConfig.ts
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate grouped stage creation, ordering, and persistence independently before expanding scope

### Incremental Delivery

1. Setup + Foundational establish the grouped pipeline contract and migration safety net
2. Deliver **US1** to unlock mixed execution groups within a stage (recommended MVP scope)
3. Deliver **US2** and **US3** to complete the cross-stage and cross-group drag-and-drop experience
4. Deliver **US4** to make per-group execution mode editing fully interactive
5. Deliver **US5** to harden stage management around the new group model
6. Deliver **US6** before release to guarantee backward compatibility for existing saved pipelines
7. Finish with Phase 9 validation and accessibility/performance checks

### Parallel Team Strategy

1. One developer completes Setup + Foundational
2. After Foundational, parallel work can split across:
   - Developer A: US1 / US4
   - Developer B: US2 / US3
   - Developer C: US5 / US6
3. Rejoin for cross-cutting validation in Phase 9

---

## Notes

- All tasks follow the required checklist format: checkbox, task ID, optional `[P]`, required story label for story phases, and exact file paths
- The generated plan intentionally references both existing files and new files that will need to be created during implementation
- Backward compatibility is scheduled as User Story 6 to match the specification priority, but it remains release-critical for protecting existing saved pipelines
