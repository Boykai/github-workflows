# Tasks: Align Agent Pipeline Columns with Project Board Status & Enable Drag/Drop

**Input**: Design documents from `/specs/023-pipeline-dragdrop/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/component-contracts.md, quickstart.md

**Tests**: Not explicitly requested in spec. Existing tests must continue to pass (Constitution Check IV). New drag-and-drop tests are recommended but optional.

**Organization**: Tasks grouped by user story (P1–P5) for independent implementation and testing. Each story can be delivered as an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5)
- Exact file paths included in descriptions

## Path Conventions

- **Web app**: `frontend/src/` (React), `backend/src/` (FastAPI)
- All source changes are frontend-only; backend already supports persistence via `PUT /workflow/config`

---

## Phase 1: Setup

**Purpose**: Verify existing infrastructure and audit current implementation before making changes.

- [ ] T001 Verify @dnd-kit package versions (@dnd-kit/core ^6.3.1, @dnd-kit/sortable ^10.0.0, @dnd-kit/utilities ^3.2.2) in frontend/package.json
- [ ] T002 [P] Audit current per-column DndContext implementation and restrictToVerticalAxis modifier usage in frontend/src/components/board/AgentColumnCell.tsx

**Checkpoint**: Dependencies confirmed, current architecture understood. Ready for foundational changes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before cross-column drag-and-drop stories can be implemented.

**⚠️ CRITICAL**: US2–US5 cannot begin until this phase is complete.

- [ ] T003 Add `moveAgentToColumn(sourceStatus, targetStatus, agentId, targetIndex?)` method to useAgentConfig hook with case-insensitive key matching, splice-based removal from source, and index-clamped insertion into target in frontend/src/hooks/useAgentConfig.ts
- [ ] T004 [P] Create AgentDragOverlay component that renders a styled read-only AgentTile preview with semi-transparency and shadow in frontend/src/components/board/AgentDragOverlay.tsx

**Checkpoint**: Foundation ready — `moveAgentToColumn` available for cross-column moves, overlay component ready for visual feedback.

---

## Phase 3: User Story 1 — Consistent Column View Between Agent Pipeline and Project Board (Priority: P1) 🎯 MVP

**Goal**: Ensure the Agent Pipeline columns match the Project Board Status columns exactly in naming and order.

**Independent Test**: Open the Project Board and the Agent Pipeline side by side and verify that every status column appears in both views with identical names and in the same left-to-right order.

### Implementation for User Story 1

- [ ] T005 [US1] Verify that AgentConfigRow receives `columns={boardData.columns}` from the same data source as the Project Board in frontend/src/pages/ProjectBoardPage.tsx
- [ ] T006 [US1] Verify column iteration order in AgentConfigRow matches Project Board column rendering order in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T007 [US1] Add orphaned mapping cleanup during config load — remove agent_mappings keys that no longer match any current column name (case-insensitive) in frontend/src/hooks/useAgentConfig.ts

**Checkpoint**: Agent Pipeline columns match Project Board exactly. Orphaned mappings from deleted columns are cleaned up on load. US1 is fully functional and testable independently.

---

## Phase 4: User Story 2 — Drag Agent Titles Across Columns (Priority: P2)

**Goal**: Enable users to drag agent title cards horizontally from one status column to another to change the agent's workflow status.

**Independent Test**: Drag an agent card from one column (e.g., "Todo") to another column (e.g., "In Progress") and verify the card appears in the target column. Save and refresh to confirm persistence.

### Implementation for User Story 2

- [ ] T008 [US2] Lift DndContext from AgentColumnCell to AgentConfigRow — wrap all columns in a single DndContext with closestCenter collision detection in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T009 [US2] Remove internal DndContext, sensors, and restrictToVerticalAxis modifier from AgentColumnCell and add useDroppable registration with column status as droppable ID in frontend/src/components/board/AgentColumnCell.tsx
- [ ] T010 [US2] Configure PointerSensor (distance: 5) and KeyboardSensor (with sortableKeyboardCoordinates coordinate getter function from @dnd-kit/sortable) in the AgentConfigRow-level DndContext in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T011 [US2] Add activeAgent state and implement handleDragStart to record the dragged agent in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T012 [US2] Implement handleDragOver to detect cross-column boundary crossings and call moveAgentToColumn for live preview in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T013 [US2] Implement handleDragEnd to finalize drop position and clear activeAgent state in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T014 [US2] Implement handleDragCancel to revert any preview changes and clear activeAgent state (store localMappings snapshot on dragStart, restore on cancel) in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T015 [US2] Integrate DragOverlay with AgentDragOverlay component — render floating preview when activeAgent is set in frontend/src/components/board/AgentConfigRow.tsx

**Checkpoint**: Users can drag agent cards across columns. Cards move to the target column on drop. AgentSaveBar appears (isDirty). Save persists, Discard reverts. Drop outside valid zones cancels.

---

## Phase 5: User Story 3 — Reorder Agent Titles Within a Column (Priority: P3)

**Goal**: Preserve and enhance within-column vertical reordering after the DndContext lift from US2.

**Independent Test**: Drag an agent card up or down within the same column and verify the new ordering persists after Save and page refresh.

### Implementation for User Story 3

- [ ] T016 [US3] Retain SortableContext with verticalListSortingStrategy per column in AgentColumnCell — ensure each column's agent IDs are passed as items in frontend/src/components/board/AgentColumnCell.tsx
- [ ] T017 [US3] Handle same-column drops in handleDragEnd — detect when source and target columns match and call reorderAgents with arrayMove result in frontend/src/components/board/AgentConfigRow.tsx

**Checkpoint**: Within-column reordering works as before. Agents can be reprioritized by dragging up/down. Combined with US2, cards can be moved to a new column at a specific row position in a single gesture (FR-008).

---

## Phase 6: User Story 4 — Visual Feedback During Drag Operations (Priority: P4)

**Goal**: Provide clear visual cues during drag operations: ghost at source position, highlighted drop zones, insertion indicators, and smooth overlay animation.

**Independent Test**: Initiate a drag and verify: (1) source card shows ghost/placeholder, (2) target column highlights on hover, (3) insertion line appears between cards, (4) floating preview follows cursor.

### Implementation for User Story 4

- [ ] T018 [P] [US4] Update ghost styling on the source tile when isDragging is true — apply opacity-30 and border-dashed classes in frontend/src/components/board/AgentTile.tsx
- [ ] T019 [P] [US4] Add drop zone highlighting to column container when isOver is true — apply border-primary bg-primary/10 ring-2 ring-primary/30 classes in frontend/src/components/board/AgentColumnCell.tsx
- [ ] T020 [US4] Add insertion line indicator (2px bg-primary divider) between cards during drag-over to show drop position in frontend/src/components/board/AgentColumnCell.tsx
- [ ] T021 [US4] Style AgentDragOverlay with shadow-lg opacity-80 rotate-1 for visual distinction from in-place tiles in frontend/src/components/board/AgentDragOverlay.tsx

**Checkpoint**: Full visual feedback loop: ghost at source, highlighted column on hover, insertion line at target position, animated overlay following cursor. Drop animation handled by @dnd-kit transforms.

---

## Phase 7: User Story 5 — Keyboard and Touch Accessibility for Drag/Drop (Priority: P5)

**Goal**: Ensure drag-and-drop works via keyboard navigation and touch gestures, making the feature accessible to all users.

**Independent Test**: (1) Use keyboard only: Tab to tile → Space to activate → Arrow keys to move → Space to drop. (2) On touch device: long-press tile → drag to new position → release.

### Implementation for User Story 5

- [ ] T022 [US5] Add TouchSensor with activationConstraint (delay: 250ms, tolerance: 5px) alongside PointerSensor in the sensors configuration in frontend/src/components/board/AgentConfigRow.tsx
- [ ] T023 [US5] Add ARIA attributes to column containers (role="group", aria-label="{status} column, {count} agents") and agent tiles (aria-roledescription="sortable agent") in frontend/src/components/board/AgentColumnCell.tsx and frontend/src/components/board/AgentTile.tsx
- [ ] T024 [US5] Implement custom keyboard handler for cross-column movement — Left/Right arrow keys call moveAgentToColumn when in keyboard drag mode in frontend/src/components/board/AgentConfigRow.tsx

**Checkpoint**: All three input methods (mouse, touch, keyboard) can move agent cards between and within columns. Screen readers announce drag operations and drop targets.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validate all changes work together, ensure type safety, and verify no regressions.

- [ ] T025 Run existing frontend linting and type checking: `cd frontend && npx eslint . && npx tsc --noEmit`
- [ ] T026 [P] Run existing frontend tests: `cd frontend && npx vitest run` — all must pass without modification
- [ ] T027 [P] Run existing backend tests: `cd backend && python -m pytest tests/` — all must pass without modification
- [ ] T028 Run quickstart.md verification steps — verify all 8 test scenarios pass (column alignment, vertical reorder, cross-column move, visual feedback, save/discard, keyboard, touch, cancel)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS US2–US5
- **US1 (Phase 3)**: Can start after Setup (Phase 1) — independent of Foundational
- **US2 (Phase 4)**: Depends on Foundational (Phase 2) — the primary engineering effort
- **US3 (Phase 5)**: Depends on US2 completion (DndContext lift changes reorder architecture)
- **US4 (Phase 6)**: Depends on US2 completion (DragOverlay integration, column highlighting)
- **US5 (Phase 7)**: Depends on US2 completion (sensors configured at row level)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Setup — independent of all other stories. **MVP scope.**
- **US2 (P2)**: Depends on Foundational. Once complete, US3/US4/US5 can proceed.
- **US3 (P3)**: Depends on US2 (DndContext architecture change). Mostly preserving existing behavior.
- **US4 (P4)**: Can start after US2 (needs DragOverlay and drag state infrastructure). Tasks T018, T019, T021 are parallelizable.
- **US5 (P5)**: Can start after US2 (needs row-level sensor config). T022, T023 are parallelizable.

### Within Each User Story

- Foundational methods before component integration
- DndContext architecture before event handlers
- Event handlers before visual feedback
- Core implementation before accessibility enhancements

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel
- **Phase 2**: T003 and T004 can run in parallel (different files)
- **Phase 3**: T005 and T006 can run in parallel (read-only audit tasks)
- **Phase 4**: T008 must precede T009 (DndContext lift before removal); T011–T015 are sequential within AgentConfigRow.tsx
- **Phase 6**: T018, T019, and T021 modify different files and can run in parallel
- **Phase 7**: T022 and T023 can be started in parallel (different files)
- **Phase 8**: T025, T026, and T027 are independent verification tasks
- **US1 + US2**: US1 (column audit) can proceed in parallel with Foundational (Phase 2)

---

## Parallel Example: User Story 2

```bash
# After Foundational phase completes, T008 and T009 must be sequential:
Task T008: "Lift DndContext to AgentConfigRow" in AgentConfigRow.tsx (FIRST — parent context must exist)
Task T009: "Remove internal DndContext, add useDroppable" in AgentColumnCell.tsx (SECOND — depends on T008)

# Then sequentially within AgentConfigRow.tsx:
Task T010: "Configure sensors"
Task T011: "Implement handleDragStart"
Task T012: "Implement handleDragOver"
Task T013: "Implement handleDragEnd"
Task T014: "Implement handleDragCancel"
Task T015: "Integrate DragOverlay"
```

## Parallel Example: User Story 4

```bash
# These tasks modify different files and can run in parallel:
Task T018: "Ghost styling on dragged tile" in AgentTile.tsx
Task T019: "Drop zone highlighting" in AgentColumnCell.tsx
Task T021: "DragOverlay styling" in AgentDragOverlay.tsx

# Then sequentially (same file as T019):
Task T020: "Insertion line indicator" in AgentColumnCell.tsx
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify dependencies)
2. Complete Phase 3: User Story 1 (column alignment audit + orphaned mapping cleanup)
3. **STOP and VALIDATE**: Verify columns match between Project Board and Agent Pipeline
4. Deploy/demo if column alignment is the immediate priority

### Incremental Delivery

1. Complete Setup → Dependencies verified
2. Complete US1 → Column alignment confirmed → Deploy/Demo (MVP!)
3. Complete Foundational → moveAgentToColumn and DragOverlay ready
4. Complete US2 → Cross-column drag-and-drop working → Deploy/Demo
5. Complete US3 → Within-column reorder preserved → Deploy/Demo
6. Complete US4 → Visual feedback polished → Deploy/Demo
7. Complete US5 → Full accessibility support → Deploy/Demo
8. Complete Polish → All verifications pass → Final release

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Developer A: US1 (column alignment — independent, MVP)
3. Developer B: Foundational phase (moveAgentToColumn + DragOverlay)
4. Once Foundational is done:
   - Developer A: US2 (cross-column drag — primary effort)
   - Developer B: US4 visual tasks T018, T021 (file-independent)
5. After US2 completes:
   - Developer A: US3 (within-column reorder)
   - Developer B: US5 (accessibility)
6. Polish phase: All developers

---

## Summary

| Metric | Count |
|--------|-------|
| **Total tasks** | 28 |
| **Phase 1 — Setup** | 2 |
| **Phase 2 — Foundational** | 2 |
| **Phase 3 — US1 (Column Alignment)** | 3 |
| **Phase 4 — US2 (Cross-Column Drag)** | 8 |
| **Phase 5 — US3 (Within-Column Reorder)** | 2 |
| **Phase 6 — US4 (Visual Feedback)** | 4 |
| **Phase 7 — US5 (Accessibility)** | 3 |
| **Phase 8 — Polish** | 4 |
| **Parallelizable tasks [P]** | 10 |
| **Files modified** | 5 (4 existing + 1 new) |
| **Files created** | 1 (AgentDragOverlay.tsx) |
| **Backend changes** | 0 |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- The Agent Pipeline already shares `boardData.columns` with the Project Board (Research Task 1), so US1 is primarily verification + edge case handling
- @dnd-kit is already installed at compatible versions — no new packages required
- All state changes flow through `useAgentConfig` → `localMappings` → `isDirty` → AgentSaveBar → `PUT /workflow/config` — existing persistence path, no backend changes needed
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
