# Tasks: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Input**: Design documents from `/specs/029-pipeline-ux-fixes/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Existing tests must continue to pass.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup

**Purpose**: No project initialization needed — this is a modification-only feature targeting existing files. No new files, no new dependencies, no schema changes.

*(No tasks in this phase)*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend cleanup and state management changes that must be complete before user story implementation begins. Removes the static model list (enabling US1), adds the clone action (enabling US4), and removes the addStage action (enabling US5).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Remove static `_AVAILABLE_MODELS` list and `list_models()` static method from `backend/src/services/pipelines/service.py`
- [x] T002 [P] Remove `GET /models/available` endpoint handler from `backend/src/api/pipelines.py`
- [x] T003 [P] Remove `pipelinesApi.listModels()` method from `frontend/src/services/api.ts`
- [x] T004 Add `cloneAgentInStage(stageId, agentNodeId)` action using `structuredClone` + `crypto.randomUUID()` and remove `addStage` from return interface in `frontend/src/hooks/usePipelineConfig.ts`

**Checkpoint**: Backend static model endpoint removed; frontend API client cleaned up; state management hook updated with clone action and without addStage — user story implementation can now begin

---

## Phase 3: User Story 1 — Dynamic GitHub Model List (Priority: P1) 🎯 MVP

**Goal**: Replace the static/mismatched model list in the Pipeline Creation "Select model" dropdown with dynamically fetched per-user GitHub models via the existing `useModels()` hook.

**Independent Test**: Log in with a GitHub account that has a known set of available models, open Pipeline Creation → + Add Agent → Select model, verify the dropdown lists exactly the models available for that account (not the old static list of 6 models). Verify the pipeline-level model dropdown also shows the same dynamic list.

### Implementation for User Story 1

- [x] T005 [US1] Remove inline `usePipelineModels()` hook definition (which called `pipelinesApi.listModels()`) and replace with `useModels()` import from `@/hooks/useModels` in `frontend/src/pages/AgentsPipelinePage.tsx`
- [x] T006 [US1] Update `availableModels` binding from `usePipelineModels()` return value to `useModels()` destructured `{ models: availableModels, isLoading, error }` and pass to `PipelineBoard` in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: The "Select model" dropdown now shows per-user GitHub models fetched dynamically. Both the pipeline-level `PipelineModelDropdown` and per-agent `ModelSelector` use the same `useModels()` data source. Error and empty states are handled by the existing `useModels` hook (TanStack Query caching with `staleTime: Infinity`).

---

## Phase 4: User Story 2 — Tools Module Z-Index Fix (Priority: P1)

**Goal**: Ensure the Tools module rendered via "+ Add Agent → + Tools" is fully visible above all other pipeline canvas elements, never hidden or clipped by parent stacking contexts.

**Independent Test**: Open Pipeline Creation → add an agent to a stage → click "+ Tools" on the agent node. Verify the Tool Selector Modal renders fully visible above all cards, panels, and overlays. Click outside to close — verify clean dismissal.

### Implementation for User Story 2

- [x] T007 [P] [US2] Fix z-index stacking context in `frontend/src/components/tools/ToolSelectorModal.tsx`: increase backdrop z-index from `z-50` to `z-[9999]` and wrap modal render in `createPortal(modal, document.body)` to escape the `StageCard` DnD transform stacking context

**Checkpoint**: The ToolSelectorModal renders above all pipeline elements regardless of StageCard transforms or parent overflow. The portal approach is consistent with existing patterns (`ModelSelector` line 236, `StageCard` agent picker line 209).

---

## Phase 5: User Story 3 — Status Tiles Locked; Agent Tiles Remain Draggable (Priority: P1)

**Goal**: Stage cards (status tiles) are fixed in place with no drag interaction, no move cursor, and no drag events. Agent nodes within stages remain fully interactive (add, remove, edit, clone). Stages show a visual indicator (lock icon) that they are fixed.

**Independent Test**: Hover over a stage card header — verify no grab cursor appears. Attempt to drag a stage card — verify it does not move. Verify agent nodes within stages are still interactive (add agent, remove agent, select model, add tools). Confirm stages show a lock icon or fixed visual indicator.

### Implementation for User Story 3

- [x] T008 [US3] Disable stage drag in `frontend/src/components/pipeline/StageCard.tsx`: set `disabled: true` on `useSortable({ id, disabled: true })`, remove drag handle button (GripVertical icon), remove `cursor-grab` styling, and add a Lock icon (from lucide-react) in the stage header to visually indicate fixed position
- [x] T009 [US3] Simplify stage DnD handling in `frontend/src/components/pipeline/PipelineBoard.tsx`: remove or no-op the `handleDragEnd` callback for stage reordering since all stages are now non-draggable

**Checkpoint**: Stage cards are locked in place with a lock icon. No grab cursor, no drag events on stages. Agent nodes remain fully interactive within each stage. The `DndContext`/`SortableContext` wrapper is retained (as a no-op) to preserve the component tree structure for potential future use.

---

## Phase 6: User Story 4 — Clone Button on Agent Tiles (Priority: P2)

**Goal**: Each Agent tile displays a "Clone" button that creates a complete deep copy of the agent's configuration (model, tools, parameters) with a new unique ID, inserted into the same stage as an independently editable instance.

**Independent Test**: Add an agent to a stage, select a model, add tools. Click the Clone button on the agent tile. Verify a new agent tile appears in the same stage with identical configuration. Modify the clone's model — verify the original is unchanged (deep copy independence). Clone multiple times rapidly — verify each clone is independent.

### Implementation for User Story 4

- [x] T010 [P] [US4] Add `onClone` callback prop to `AgentNodeProps` interface and render a Clone button with Copy icon (from lucide-react) next to the remove button in `frontend/src/components/pipeline/AgentNode.tsx`
- [x] T011 [US4] Add `onCloneAgent(agentNodeId: string)` prop to `StageCardProps` and pass `() => onCloneAgent(agent.id)` as `onClone` to each `AgentNode` in `frontend/src/components/pipeline/StageCard.tsx`
- [x] T012 [US4] Add `onCloneAgent(stageId: string, agentNodeId: string)` prop to `PipelineBoardProps` and pass `(agentNodeId) => onCloneAgent(stage.id, agentNodeId)` to each `StageCard` in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T013 [US4] Wire `pipelineConfig.cloneAgentInStage` to `PipelineBoard` via `onCloneAgent={(stageId, agentNodeId) => pipelineConfig.cloneAgentInStage(stageId, agentNodeId)}` prop in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: Each agent tile shows a Clone button. Clicking Clone creates a deep copy with a new UUID, appended to the same stage. Editing the clone does not affect the original. The `cloneAgentInStage` action in `usePipelineConfig` triggers dirty state detection.

---

## Phase 7: User Story 5 — Remove Add Stage (Priority: P2)

**Goal**: Remove the "Add Stage" button and all associated stage-creation UI from the Pipeline Creation page. Stages are derived from board columns and should not be manually added.

**Independent Test**: Load Pipeline Creation page. Confirm no "Add Stage" button appears anywhere — not in the empty state, not at the bottom of the board, not in any menu. Verify stages are still auto-populated from board columns.

### Implementation for User Story 5

- [x] T014 [US5] Remove both "Add Stage" buttons (empty state at ~lines 165-172 and normal state at ~lines 253-260) and remove `onAddStage` prop from `PipelineBoardProps` interface in `frontend/src/components/pipeline/PipelineBoard.tsx`
- [x] T015 [US5] Remove `onAddStage={() => pipelineConfig.addStage()}` prop binding from `PipelineBoard` usage in `frontend/src/pages/AgentsPipelinePage.tsx`

**Checkpoint**: No "Add Stage" button visible anywhere in Pipeline Creation. The empty state shows an informational message about stages being derived from board columns. The `addStage` action has already been removed from the `usePipelineConfig` return interface (T004).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, build verification, and cross-story integration checks

- [x] T016 [P] Run frontend lint (`npm run lint`) and TypeScript build (`npm run build`) in `frontend/` to verify no type errors or lint violations across all modified files
- [x] T017 [P] Run backend tests (`pytest`) in `backend/` to verify endpoint removal does not break existing test suite
- [ ] T018 Run quickstart.md verification scenarios for all 5 fixes to confirm end-to-end correctness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — skip
- **Foundational (Phase 2)**: No dependencies — can start immediately. BLOCKS all user stories.
- **User Stories (Phases 3–7)**: All depend on Foundational (Phase 2) completion
  - US1 (Phase 3), US2 (Phase 4), US3 (Phase 5) are all P1 — can proceed in parallel or in priority order
  - US4 (Phase 6) and US5 (Phase 7) are P2 — can proceed after P1 stories or in parallel with them
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on T001–T003 (backend endpoint removal, frontend API cleanup). No dependencies on other stories.
- **US2 (P1)**: Independent of all other stories. Can start after Foundational phase.
- **US3 (P1)**: Independent of all other stories. Can start after Foundational phase.
- **US4 (P2)**: Depends on T004 (`cloneAgentInStage` action in hook). No dependencies on other stories.
- **US5 (P2)**: Depends on T004 (`addStage` removal from hook). No dependencies on other stories.

### Within Each User Story

- Backend changes before frontend changes (US1)
- Component changes bottom-up: leaf components first (AgentNode), then containers (StageCard, PipelineBoard), then page (AgentsPipelinePage) for US4
- Core implementation before integration

### Parallel Opportunities

- **Phase 2**: T001 sequential → T002 + T003 in parallel (different files/codebases), then T004
- **Phase 3–5**: US1, US2, US3 can all proceed in parallel (different files)
  - T007 (ToolSelectorModal) is fully independent — [P] marked
- **Phase 6**: T010 (AgentNode) is independent — [P] marked — can start while T009 completes
- **Phase 8**: T016 (frontend) + T017 (backend) in parallel (different codebases)

---

## Parallel Example: All P1 Stories Simultaneously

```text
# After Foundational (Phase 2) completes, launch all P1 stories in parallel:

# Developer A — US1: Dynamic Model List
Task T005: "Remove usePipelineModels, import useModels in AgentsPipelinePage.tsx"
Task T006: "Update availableModels binding in AgentsPipelinePage.tsx"

# Developer B — US2: Tools Z-Index Fix
Task T007: "Fix z-index and portal ToolSelectorModal.tsx"

# Developer C — US3: Tile Dragging Lock
Task T008: "Disable stage drag, remove handle, add lock in StageCard.tsx"
Task T009: "Simplify DnD handling in PipelineBoard.tsx"
```

---

## Parallel Example: P2 Stories After P1

```text
# After P1 stories complete (or in parallel if team capacity allows):

# Developer A — US4: Agent Clone (bottom-up)
Task T010: "Add onClone prop and Clone button in AgentNode.tsx"
Task T011: "Pass onCloneAgent through StageCard.tsx"
Task T012: "Pass onCloneAgent through PipelineBoard.tsx"
Task T013: "Wire cloneAgentInStage in AgentsPipelinePage.tsx"

# Developer B — US5: Remove Add Stage
Task T014: "Remove Add Stage buttons from PipelineBoard.tsx"
Task T015: "Remove onAddStage binding from AgentsPipelinePage.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 2: Foundational (T001–T004)
2. Complete Phase 3: User Story 1 — Dynamic Model List (T005–T006)
3. **STOP and VALIDATE**: Verify the "Select model" dropdown shows per-user GitHub models
4. Deploy/demo if ready — pipeline model list is now accurate

### Incremental Delivery

1. Complete Foundational → Backend and hooks ready
2. Add US1 (Dynamic Models) → Test independently → Deploy (MVP!)
3. Add US2 (Tools Z-Index) → Test independently → Deploy
4. Add US3 (Tile Dragging) → Test independently → Deploy
5. Add US4 (Agent Clone) → Test independently → Deploy
6. Add US5 (Remove Add Stage) → Test independently → Deploy
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Foundational together (T001–T004)
2. Once Foundational is done:
   - Developer A: US1 (Dynamic Models) + US4 (Agent Clone)
   - Developer B: US2 (Tools Z-Index) + US5 (Remove Add Stage)
   - Developer C: US3 (Tile Dragging)
3. Stories complete and integrate independently
4. Final validation pass (Phase 8)

---

## Summary

| Metric | Value |
|--------|-------|
| **Total tasks** | 18 |
| **Foundational tasks** | 4 (T001–T004) |
| **US1 tasks** (Dynamic Model List, P1) | 2 (T005–T006) |
| **US2 tasks** (Tools Z-Index, P1) | 1 (T007) |
| **US3 tasks** (Tile Dragging, P1) | 2 (T008–T009) |
| **US4 tasks** (Agent Clone, P2) | 4 (T010–T013) |
| **US5 tasks** (Remove Add Stage, P2) | 2 (T014–T015) |
| **Polish tasks** | 3 (T016–T018) |
| **Parallel opportunities** | 6 tasks marked [P] |
| **Files modified** | 7 frontend + 2 backend = 9 total |
| **Files created** | 0 |
| **Suggested MVP scope** | Phase 2 + Phase 3 (US1 only — 6 tasks) |

### Format Validation

✅ All 18 tasks follow the checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ All user story phase tasks include `[US#]` label
✅ Foundational and Polish phase tasks have no story label
✅ All tasks include exact file paths
✅ Task IDs are sequential (T001–T018)
✅ [P] markers applied only to tasks with no dependencies on incomplete same-file tasks

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No test tasks generated — tests not explicitly requested in specification
- Existing tests must continue to pass (verified in Phase 8)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
