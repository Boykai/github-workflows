# Tasks: Group-Aware Pipeline Execution & Tracking Table

**Input**: Design documents from `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/`
**Prerequisites**: `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/plan.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/spec.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/research.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/data-model.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/contracts/internal-interfaces.md`, `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/quickstart.md`

**Tests**: Tests are required for this feature because the specification and implementation plan explicitly require coverage updates for sequential groups, parallel groups, tracking-table parsing/rendering, backward compatibility, and partial failure handling.

**Organization**: Tasks are grouped by user story so each increment can be implemented, verified, and demonstrated independently after a small shared setup/foundational phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete tasks)
- **[Story]**: Required only for user story phases (`[US1]`, `[US2]`, etc.)
- **Every task includes exact absolute file paths**

## Path Conventions

- **Repository root**: `/home/runner/work/github-workflows/github-workflows`
- **Backend source**: `/home/runner/work/github-workflows/github-workflows/backend/src/`
- **Backend tests**: `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/`
- **Feature docs**: `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/`

---

## Phase 1: Setup

**Purpose**: Establish the shared workflow, runtime, and tracking-table data contracts for group-aware execution.

- [ ] T001 Add the `ExecutionGroupMapping` schema and execution-mode validation in `/home/runner/work/github-workflows/github-workflows/backend/src/models/workflow.py`
- [ ] T002 Add the `WorkflowConfiguration.group_mappings` field and serialization defaults in `/home/runner/work/github-workflows/github-workflows/backend/src/models/workflow.py`
- [ ] T003 [P] Add `PipelineGroupInfo` plus group-aware `PipelineState` fields and properties in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/models.py`
- [ ] T004 [P] Extend `AgentStep` with backward-compatible defaulted `group_label`, `group_order`, and `group_execution_mode` metadata in `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`

**Checkpoint**: Shared models can represent `ExecutionGroupMapping`, `PipelineGroupInfo`, and tracking-table group metadata without breaking existing serialization defaults.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Preserve execution-group data from pipeline config through workflow configuration and shared tracking entry points before story-specific orchestration begins.

**⚠️ CRITICAL**: No user story work should begin until execution-group mappings can be loaded, stored, and forwarded consistently.

- [ ] T005 Add shared regression coverage for `ExecutionGroupMapping`, `WorkflowConfiguration.group_mappings`, and `PipelineResolutionResult.group_mappings` in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_models.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator_config.py`
- [ ] T006 Update `load_pipeline_as_agent_mappings()` to iterate `PipelineStage.groups` from `/home/runner/work/github-workflows/github-workflows/backend/src/models/pipeline.py` and build ordered `group_mappings` plus flat fallback in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py`
- [ ] T007 [P] Update `PipelineResolutionResult`, `resolve_project_pipeline_mappings()`, and `_prepare_workflow_config()` to accept and persist the 4-tuple group payload in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/api/pipelines.py`
- [ ] T008 [P] Thread optional `group_mappings` through shared tracking entry points in `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py`

**Checkpoint**: `PipelineConfig -> WorkflowConfiguration` preserves ordered groups, callers accept the new internal contract, and shared helpers can receive group-aware mappings.

---

## Phase 3: User Story 1 - Sequential Group Execution (Priority: P1) 🎯 MVP

**Goal**: Execute agents one-by-one inside a configured sequential group while preserving group boundaries through orchestration.

**Independent Test**: Create a stage with one sequential group containing 2–3 agents, enter the stage, and verify agents are assigned and advanced strictly in order with no overlap.

### Tests for User Story 1

- [ ] T009 [P] [US1] Add sequential-group orchestration and stage-entry regression tests in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 1

- [ ] T010 [US1] Initialize `PipelineState.groups`, `current_group_index`, and `current_agent_index_in_group` for sequential groups in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T011 [US1] Implement sequential-group agent selection in `assign_agent_for_status()` in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T012 [US1] Advance exactly one agent at a time inside the active sequential group in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py`
- [ ] T013 [US1] Preserve active sequential-group context while updating tracking state in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`

**Checkpoint**: A single sequential execution group behaves deterministically and is independently testable as the MVP slice.

---

## Phase 4: User Story 2 - Parallel Group Execution (Priority: P1)

**Goal**: Assign all agents in a parallel group within the stagger window and keep the stage open until every grouped agent finishes.

**Independent Test**: Create a stage with one parallel group of 3 agents, enter the stage, verify all 3 assignments happen within the configured stagger window, and confirm the stage does not advance until all three finish.

### Tests for User Story 2

- [ ] T014 [P] [US2] Add parallel-group assignment and completion tests in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 2

- [ ] T015 [US2] Add 2-second staggered assignment for all agents in the active parallel group in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T016 [US2] Initialize and update per-agent parallel group statuses for active assignments in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py`
- [ ] T017 [US2] Hold stage advancement until every agent in the active parallel group reaches a terminal state in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py`

**Checkpoint**: Parallel groups launch as a coordinated batch, track each agent independently, and complete only when the whole group finishes.

---

## Phase 5: User Story 3 - Mixed Group Ordering Within a Stage (Priority: P2)

**Goal**: Respect configured group order so sequential and parallel groups can coexist within the same stage.

**Independent Test**: Create a stage with Group 1 sequential (`A -> B`) and Group 2 parallel (`C, D, E`), run an issue through it, and verify Group 2 starts only after Group 1 fully completes.

### Tests for User Story 3

- [ ] T018 [P] [US3] Add mixed-group ordering and empty-group skip coverage in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py`

### Implementation for User Story 3

- [ ] T019 [US3] Sort and materialize ordered `ExecutionGroupMapping` entries per status in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T020 [US3] Move between `current_group_index` values only after the active group completes in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py`
- [ ] T021 [US3] Transition to the next pipeline status only after the final group in the current status completes in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`

**Checkpoint**: Stages with multiple ordered groups execute end-to-end in the configured sequence and skip empty groups without error.

---

## Phase 6: User Story 4 - Tracking Table Displays Group Information (Priority: P2)

**Goal**: Show and preserve group membership in the GitHub issue tracking table so operators can inspect and reconstruct grouped execution state.

**Independent Test**: Trigger a grouped pipeline, inspect the issue body for a 6-column table with a Group column, then re-parse and re-render the table and verify the same group labels remain intact.

### Tests for User Story 4

- [ ] T022 [P] [US4] Add 6-column tracking-table render, parse, and re-render preservation tests in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_agent_tracking.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 4

- [ ] T023 [US4] Build per-step group labels (`G{n} (series)` for sequential groups and `G{n} (parallel)` for parallel groups) from `group_mappings` in `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`
- [ ] T024 [US4] Render the 6-column tracking markdown and preserve group metadata through `append_tracking_to_body()` and `update_agent_state()` in `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`
- [ ] T025 [US4] Reconstruct `PipelineGroupInfo` from tracking-table group rows during polling recovery in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py`

**Checkpoint**: The issue body visibly shows group structure, and polling recovery can rebuild grouped runtime state from the Group column.

---

## Phase 7: User Story 5 - Backward Compatibility with Legacy Pipelines (Priority: P2)

**Goal**: Keep legacy pipelines and historical tracking tables working unchanged while new grouped pipelines use the new behavior only when group data is present.

**Independent Test**: Run a legacy pipeline with no explicit groups and confirm it still executes sequentially with the 5-column table; separately parse saved 5-column and 4-column issue bodies without errors.

### Tests for User Story 5

- [ ] T026 [P] [US5] Add legacy pipeline fallback and 6-column/5-column/4-column parser coverage in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_agent_tracking.py`, `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator_config.py`, and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`

### Implementation for User Story 5

- [ ] T027 [US5] Implement 6-column -> 5-column -> 4-column tracking-table parser fallback in `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`
- [ ] T028 [US5] Apply `if group_mappings and group_mappings.get(status)` guard paths with unchanged flat fallback in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py`, and `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py`
- [ ] T029 [US5] Keep legacy pipelines and new pipelines without explicit groups on implicit sequential execution and 5-column tracking output in `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`

**Checkpoint**: Existing pipelines remain unaffected, historical issue bodies still parse, and grouped behavior activates only when grouped data is actually present.

---

## Phase 8: User Story 6 - Parallel Group Partial Failure Handling (Priority: P3)

**Goal**: Allow a parallel group to continue running after one agent fails, record failed agents, and advance only after all group members finish.

**Independent Test**: Simulate one failed agent and two successful agents in a parallel group, verify the remaining agents still complete, and confirm the pipeline records the failure before moving on.

### Tests for User Story 6

- [ ] T030 [P] [US6] Add partial-failure continuation and failed-agent recording tests in `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py` and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py`

### Implementation for User Story 6

- [ ] T031 [US6] Record failed agents without canceling remaining parallel-group work in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] T032 [P] [US6] Reflect completed versus failed outcomes per agent row during partial-failure updates in `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py`
- [ ] T033 [US6] Advance from a partially failed parallel group only after every member reaches `completed` or `failed` in `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py`

**Checkpoint**: Parallel groups tolerate individual agent failure, record failure detail, and move forward only after all grouped agents finish.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Validate the end-to-end grouped execution flow, confirm backward compatibility, and run the scoped quality gates.

- [ ] T034 [P] Validate sequential, parallel, mixed-group, backward-compatibility, and partial-failure scenarios in `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/quickstart.md` against `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py` and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py`
- [ ] T035 [P] Run targeted backend tests from `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/quickstart.md` against `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_agent_tracking.py`, `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py`, and `/home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py`
- [ ] T036 [P] Run backend lint and format validation from `/home/runner/work/github-workflows/github-workflows/backend/pyproject.toml` against `/home/runner/work/github-workflows/github-workflows/backend/src/models/workflow.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/`, and `/home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/`
- [ ] T037 Review cleanup for group-aware orchestration, backward-compatibility guards, and contract alignment in `/home/runner/work/github-workflows/github-workflows/backend/src/api/pipelines.py`, `/home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py`, and `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/contracts/internal-interfaces.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 — establishes the MVP sequential-group runtime.
- **Phase 4 (US2)**: Depends on Phase 3 — parallel execution builds on group-aware runtime initialization.
- **Phase 5 (US3)**: Depends on Phases 3-4 — mixed ordering requires both sequential and parallel group behavior.
- **Phase 6 (US4)**: Depends on Phase 2 — tracking-table rendering/parsing can proceed once shared group mappings exist, and it must complete before Phase 7 starts or any grouped release ships.
- **Phase 7 (US5)**: Depends on Phases 2 and 6 — backward-compatible parser and guard logic rely on the new tracking-table path being in place.
- **Phase 8 (US6)**: Depends on Phases 4 and 6 — partial failure handling needs parallel execution and per-agent grouped tracking.
- **Phase 9 (Polish)**: Depends on all stories intended for release.

### User Story Dependency Graph

```text
Setup -> Foundational -> US1 -> US2 -> US3
Foundational -> US4 -> US5
US2 -> US6
US4 -> US6
{US3, US5, US6} -> Polish
```

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational — no dependency on other user stories and is the recommended MVP scope.
- **US2 (P1)**: Depends on US1’s grouped runtime initialization so parallel assignment has valid group state to manage.
- **US3 (P2)**: Depends on US1 and US2 because mixed ordering requires both sequential and parallel group semantics.
- **US4 (P2)**: Depends on Foundational shared mappings and should complete before US5 so the new 6-column format is available for compatibility fallback tests.
- **US5 (P2)**: Depends on US4 plus Foundational guard plumbing because it validates both new grouped tables and legacy formats.
- **US6 (P3)**: Depends on US2 and US4 because partial failure handling relies on parallel-group state plus grouped tracking visibility.

### Within Each User Story

- Write the story’s tests first and confirm they fail before implementing the story.
- Update shared models/configuration before orchestration logic that consumes them.
- Update orchestration before polling recovery or tracking-table reconciliation that depends on runtime state.
- Complete each checkpoint before moving to the next story in the release plan.

### Parallel Opportunities

- **Phase 1**: T003 and T004 can run in parallel after T001-T002 define the workflow-layer group schema.
- **Phase 2**: T007 and T008 can run in parallel after T006 defines the new group-mapping contract.
- **US1**: T009 can run while T013 is prepared, but T010 -> T011 -> T012 should remain sequential because they touch the same orchestration flow.
- **US2**: T014 can start first; T016 and T017 can be split once T015 establishes the staggered assignment path.
- **US3**: T018 can run in parallel with design review of T019, but T019 -> T020 -> T021 should execute in order.
- **US4**: T022 can run before implementation; T023 and T025 can proceed in parallel once the group-label format is fixed because they touch different files.
- **US5**: T026 can run before implementation; T028 and T029 can proceed in parallel once T027 defines parser fallback behavior.
- **US6**: T030 can run before implementation; T032 can proceed in parallel with T031 after the failure-recording contract is settled.

---

## Parallel Example: User Story 1

```text
After Phase 2 completes:
1. Start T009 in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py.
2. In parallel, prepare T013 in /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py and /home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py.
3. Then execute T010 -> T011 -> T012 sequentially in the orchestration flow.
```

## Parallel Example: User Story 2

```text
After US1 passes:
1. Start T014 in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py.
2. Implement T015 in /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py.
3. Split follow-up work so T016 updates runtime statuses while T017 updates completion checks in /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/.
```

## Parallel Example: User Story 3

```text
After US2 passes:
1. Start T018 in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py.
2. Implement T019 in /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py and /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py.
3. Follow with T020 -> T021 in /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py.
```

## Parallel Example: User Story 4

```text
After Phase 2 completes:
1. Start T022 in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_agent_tracking.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py.
2. Implement T023/T024 in /home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py.
3. In parallel, implement T025 in /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py and /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py.
```

## Parallel Example: User Story 5

```text
After US4 passes:
1. Start T026 across /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_agent_tracking.py, /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator_config.py, and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py.
2. Implement T027 in /home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py.
3. In parallel, implement T028 in /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py, /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py, and /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/config.py, and implement T029 in /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py and /home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py.
```

## Parallel Example: User Story 6

```text
After US2 and US4 pass:
1. Start T030 in /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_copilot_polling.py and /home/runner/work/github-workflows/github-workflows/backend/tests/unit/test_workflow_orchestrator.py.
2. Implement T031 in /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/pipeline.py and /home/runner/work/github-workflows/github-workflows/backend/src/services/workflow_orchestrator/orchestrator.py.
3. In parallel, implement T032 in /home/runner/work/github-workflows/github-workflows/backend/src/services/agent_tracking.py and /home/runner/work/github-workflows/github-workflows/backend/src/services/copilot_polling/helpers.py before finishing T033.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: US1 sequential-group execution.
4. Validate the independent US1 test scenario from `/home/runner/work/github-workflows/github-workflows/specs/039-group-pipeline-execution/spec.md`.
5. Pause for review before adding parallel execution.

### Incremental Delivery

1. Ship Setup + Foundational to preserve `ExecutionGroupMapping` and `PipelineGroupInfo` through the workflow stack.
2. Add US1 to deliver deterministic grouped sequential execution.
3. Add US2 to unlock staggered parallel execution.
4. Add US3 to support ordered mixed groups within a stage.
5. Add US4 to expose group metadata in the tracking table and recovery path.
6. Add US5 to lock in backward compatibility for legacy pipelines and 5-column/4-column issue bodies.
7. Add US6 to harden parallel groups with partial failure handling.

### Suggested Release Slices

- **Slice 1 (MVP)**: Phases 1-3 (`ExecutionGroupMapping`, `PipelineGroupInfo`, sequential grouped execution).
- **Slice 2**: Phase 4 (`PipelineGroupInfo.agent_statuses`, staggered parallel assignment).
- **Slice 3**: Phases 5-7 (mixed ordering, tracking-table Group column, backward compatibility).
- **Slice 4**: Phase 8 plus Phase 9 (partial failure handling and final validation).

---

## Notes

- Keep task descriptions granular so an implementation agent can execute them without reopening the planning documents.
- Preserve backward compatibility by defaulting every new group-aware field to an empty or legacy-safe value.
- Treat the tracking table as the persisted recovery surface: new grouped pipelines render 6 columns, while legacy issues must continue parsing from 5-column and 4-column tables.
- Prefer small, reviewable commits at each checkpoint so sequential, parallel, mixed-group, compatibility, and failure-handling behavior can be validated independently.
