# Tasks: Undo/Redo Support for Destructive Actions

**Input**: Design documents from `/specs/054-undoable-delete/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/useUndoableDelete.ts ✓, quickstart.md ✓

**Tests**: Not requested in specification. Tests are NOT included per Constitution IV (Test Optionality).

**Organization**: Tasks grouped by user story. 5 user stories (2×P1, 2×P2, 1×P3). Single new file plus modifications to existing entity hooks and component delete handlers.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- File paths are relative to repository root

## Path Conventions

- **Project root**: `solune/frontend/src/` (frontend-only feature, no backend changes)
- **Hooks**: `solune/frontend/src/hooks/`
- **Components**: `solune/frontend/src/components/`
- **Pages**: `solune/frontend/src/pages/`
- **Layout**: `solune/frontend/src/layout/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing Toaster configuration supports undo toast stacking

- [ ] T001 Verify Toaster configuration in solune/frontend/src/layout/AppLayout.tsx confirms visibleToasts ≥ 3, default duration 5000ms, position bottom-right, and sonner `action` API support — no code changes expected, document any gaps

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the generic `useUndoableDelete` hook that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Create `useUndoableDelete` hook in solune/frontend/src/hooks/useUndoableDelete.ts implementing the interface contract from specs/054-undoable-delete/contracts/useUndoableDelete.ts and reference implementation from specs/054-undoable-delete/quickstart.md — must include: `UseUndoableDeleteOptions` input (queryKey, undoTimeoutMs defaulting to 5000), `UndoableDeleteParams` per-call input (id, entityLabel, onDelete callback), optimistic cache removal via `queryClient.setQueryData` filtering by entity id, sonner toast with `action: { label: 'Undo', onClick }` and unique `id: undo-delete-${entityId}`, `setTimeout`-based deferred deletion that fires `onDelete()` then `invalidateQueries` on success, undo handler that clears timeout + restores cache snapshot via `setQueryData` + shows "Restored" success toast, `pendingIds` Set state for consumer-side tracking, `useRef<Map>` for per-deletion state (timeoutId, toastId, snapshot, onDelete, queryKey), re-deletion of same entity resets existing timer and replaces toast, error recovery that restores cache snapshot and shows error toast when API delete fails after grace window, and `useEffect` cleanup on unmount that iterates all pending entries clearing timeouts and restoring snapshots

**Checkpoint**: Foundation ready — `useUndoableDelete` hook exists with full API. Entity integration can begin.

---

## Phase 3: User Story 1 — Undo Delete via Toast Notification (Priority: P1) 🎯 MVP

**Goal**: Users can undo an accidental agent deletion within 5 seconds via an undo toast notification that appears immediately after confirming the delete

**Independent Test**: Delete an agent → agent disappears from list instantly → undo toast appears with agent name → click "Undo" within 5s → agent restored to list with "Restored" toast; OR let timer expire → agent permanently deleted (verify via page refresh)

### Implementation for User Story 1

- [ ] T003 [US1] Add `useUndoableDeleteAgent` function in solune/frontend/src/hooks/useAgents.ts that instantiates `useUndoableDelete` with `queryKey: agentKeys.list(projectId)` and returns `{ deleteAgent: (agentId: string, agentName: string) => void, pendingIds: Set<string> }` where `deleteAgent` calls `undoableDelete({ id: agentId, entityLabel: \`Agent: ${agentName}\`, onDelete: () => agentsApi.delete(projectId!, agentId) })`
- [ ] T004 [US1] Update delete handler in solune/frontend/src/components/agents/AgentCard.tsx to use `useUndoableDeleteAgent` — after confirmation dialog, call `deleteAgent(agent.id, displayName)` instead of `deleteMutation.mutate(agent.id)`, replacing the existing `useDeleteAgent` usage for the delete flow

**Checkpoint**: Agent deletion is undoable via toast. Core undo mechanism proven with one entity type. This is the MVP — deployable independently.

---

## Phase 4: User Story 2 — Undo Delete Across All Entity Types (Priority: P1)

**Goal**: Consistent undo delete experience across all 4 deletable entity types (agents, tools, chores, pipelines) using the same toast pattern, grace window duration, and undo behavior

**Independent Test**: Sequentially delete one of each entity type (agent, tool, chore, pipeline), undo each via its toast, verify identical behavior — same toast format, same 5s grace window, same "Restored" feedback, same data integrity on restore

### Implementation for User Story 2

- [ ] T005 [P] [US2] Add `useUndoableDeleteChore` function in solune/frontend/src/hooks/useChores.ts that instantiates `useUndoableDelete` with `queryKey: choreKeys.list(projectId)` and returns `{ deleteChore: (choreId: string, choreName: string) => void, pendingIds: Set<string> }` where `deleteChore` calls `undoableDelete({ id: choreId, entityLabel: \`Chore: ${choreName}\`, onDelete: () => choresApi.delete(projectId!, choreId) })`
- [ ] T006 [P] [US2] Update delete handler in solune/frontend/src/components/chores/ChoreCard.tsx to use `useUndoableDeleteChore` — after confirmation dialog, call `deleteChore(chore.id, chore.name)` instead of `deleteMutation.mutate(chore.id)`
- [ ] T007 [P] [US2] Add `useUndoableDeleteTool` function in solune/frontend/src/hooks/useTools.ts that instantiates `useUndoableDelete` with `queryKey: toolKeys.list(projectId)` and returns `{ deleteTool: (toolId: string, toolName: string) => void, pendingIds: Set<string> }` where `deleteTool` calls `undoableDelete({ id: toolId, entityLabel: \`Tool: ${toolName}\`, onDelete: () => toolsApi.delete(projectId!, toolId, true) })` — note: uses `confirm=true` to force-delete since the undoable pattern replaces the two-step dependency check flow
- [ ] T008 [P] [US2] Update delete handler in solune/frontend/src/components/tools/ToolsPanel.tsx to use `useUndoableDeleteTool` — after confirmation dialog (retain affected-agents warning), call `deleteTool(toolId, tool.name)` instead of the existing two-step `deleteTool({ toolId, confirm })` mutation flow
- [ ] T009 [P] [US2] Add `useUndoableDeleteApp` function in solune/frontend/src/hooks/useApps.ts that instantiates `useUndoableDelete` with `queryKey: appKeys.list()` (no projectId — apps are global) and returns `{ deleteApp: (appName: string, displayName: string, force?: boolean) => void, pendingIds: Set<string> }` where `deleteApp` calls `undoableDelete({ id: appName, entityLabel: \`App: ${displayName}\`, onDelete: () => appsApi.delete(appName, force) })`
- [ ] T010 [P] [US2] Update delete handler in solune/frontend/src/components/apps/AppDetailView.tsx to use `useUndoableDeleteApp` — after confirmation dialog, call `deleteApp(appName, app.display_name)` then `onBack()` to navigate to list; the undo toast remains visible globally (rendered in AppLayout.tsx Toaster) so the user can undo from the list view
- [ ] T011 [US2] Wire undoable pipeline delete in solune/frontend/src/hooks/useUnsavedPipelineGuard.ts — instantiate `useUndoableDelete` with `queryKey: pipelineKeys.list(projectId)` and modify `handleDelete` to call `undoableDelete({ id: pipelineConfig.editingPipelineId, entityLabel: \`Pipeline: ${pipelineName}\`, onDelete: () => pipelineConfig.deletePipeline() })` after the existing confirmation dialog instead of calling `pipelineConfig.deletePipeline()` directly; requires adding `projectId` and `pipelineName` to the hook's interface/options
- [ ] T012 [US2] Modify `deletePipeline` in solune/frontend/src/hooks/usePipelineConfig.ts to remove its `toast.success('Pipeline deleted')` call (the undo toast from `useUndoableDelete` replaces it) and ensure `clearUndoRedo()`, `resetPending()`, and `dispatch({ type: 'DELETE_SUCCESS' })` execute as part of the deletion (they fire when the grace timer expires via the `onDelete` callback, not immediately on delete trigger)

**Checkpoint**: All 4 entity types (agents, chores, tools, pipelines) support undo delete with identical toast behavior. Each entity's delete handler goes through confirmation dialog → undoable delete → undo toast.

---

## Phase 5: User Story 3 — Optimistic Removal and Visual Feedback (Priority: P2)

**Goal**: Deleted items vanish instantly from rendered lists (within 100ms of confirmation) and reappear instantly on undo without layout shifts, loading states, or server round-trips

**Independent Test**: Delete an item from a list of 10+ items → verify instant removal with smooth list reflow (no empty gaps) → click Undo → verify instant restoration to correct position with smooth reflow — both without any visible loading spinner or layout jump

### Implementation for User Story 3

- [ ] T013 [US3] Ensure `useUndoableDelete` cache updater in solune/frontend/src/hooks/useUndoableDelete.ts handles paginated query data structures — if entity list queries use `useInfiniteQuery` (pages array structure `{ pages: T[], pageParams: unknown[] }`), the `setQueryData` filter must iterate `pages` and filter within each page; verify against actual query data shapes used by `agentKeys.list`, `choreKeys.list`, `toolKeys.list`, `appKeys.list`, and `pipelineKeys.list`
- [ ] T014 [US3] Verify snapshot restoration in solune/frontend/src/hooks/useUndoableDelete.ts restores the complete cache snapshot (not a re-insert), ensuring items return to their correct position per the sort/filter state at deletion time — the hook's `restoreItem` function must call `queryClient.setQueryData(queryKey, snapshot)` with the full pre-deletion snapshot

**Checkpoint**: Optimistic removal and restoration feel instantaneous with no visual glitches or layout shifts.

---

## Phase 6: User Story 4 — Multiple Concurrent Deletions (Priority: P2)

**Goal**: Users can delete ≥3 items in rapid succession with each deletion producing an independent undo toast, and undoing one does not affect the others

**Independent Test**: Delete Agent A, then Tool B, then Chore C within 3 seconds → verify all 3 toasts visible and stacked → click Undo on second toast (Tool B) → verify only Tool B is restored while Agent A and Chore C deletions proceed normally

### Implementation for User Story 4

- [ ] T015 [US4] Verify `useUndoableDelete` concurrent deletion support in solune/frontend/src/hooks/useUndoableDelete.ts — confirm `pendingIds` Set correctly tracks multiple in-flight deletions, each toast has unique `id` format `undo-delete-${entityId}` for independent lifecycle, the `pendingRef` Map stores separate entries per entity, and `restoreItem` only affects the targeted entity without side effects on other pending entries

**Checkpoint**: ≥3 concurrent deletions each independently undoable via stacked toasts.

---

## Phase 7: User Story 5 — Grace Window Cleanup on Navigation (Priority: P3)

**Goal**: Pending deletions are safely cancelled and items restored when the user navigates away from the page, with no memory leaks or orphaned timers

**Independent Test**: Delete an item → immediately navigate to a different page → return to original page → verify the item is restored (pending delete was cancelled on navigation)

### Implementation for User Story 5

- [ ] T016 [US5] Verify `useEffect` cleanup in solune/frontend/src/hooks/useUndoableDelete.ts correctly handles unmount during pending deletions — cleanup must iterate `pendingRef.current` Map, call `clearTimeout` on each entry's `timeoutId`, restore each entry's `snapshot` via `queryClient.setQueryData`, and clear the Map; must NOT show toasts during cleanup (component is already unmounted); verify no React state-update-after-unmount warnings by using refs for cleanup-path data access

**Checkpoint**: No orphaned timers or memory leaks. Items safely restored on navigation away. Data integrity maintained in all lifecycle scenarios.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T017 [P] Update confirmation dialog descriptions to remove "This cannot be undone" / "This action cannot be undone" messaging in solune/frontend/src/components/agents/AgentCard.tsx, solune/frontend/src/components/chores/ChoreCard.tsx, solune/frontend/src/components/tools/ToolsPanel.tsx, solune/frontend/src/components/apps/AppDetailView.tsx, and solune/frontend/src/hooks/useUnsavedPipelineGuard.ts — the undo toast now provides recovery, so the "cannot be undone" language is misleading
- [ ] T018 Verify error handling in solune/frontend/src/hooks/useUndoableDelete.ts for failed API deletes after grace window expiry — on catch: restore cache snapshot via `setQueryData`, show error toast with `toast.error(\`Failed to delete ${entityLabel}\`, { duration: Infinity })`, remove entry from `pendingRef` and `pendingIds` (FR-018)
- [ ] T019 Run quickstart.md validation scenarios per specs/054-undoable-delete/quickstart.md verification checklist — execute all 6 verification steps: (1) delete entity → undo toast appears, (2) click Undo → item restored + "Restored" toast, (3) let timer expire → permanent delete verified via refresh, (4) delete 3 items → 3 toasts independently undoable, (5) delete + navigate away → item restored on return, (6) delete + network error → error toast + item restored

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup verification — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — proves core mechanism with agents (MVP)
- **User Story 2 (Phase 4)**: Depends on US1 pattern — extends to all entity types
- **User Story 3 (Phase 5)**: Depends on Foundational — refines hook cache handling for edge cases
- **User Story 4 (Phase 6)**: Depends on Foundational — verifies concurrent deletion support
- **User Story 5 (Phase 7)**: Depends on Foundational — verifies cleanup behavior
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories. Delivers MVP with agents only.
- **US2 (P1)**: Depends on US1 for the proven integration pattern. Can start after US1 is complete. Tasks within US2 can run in parallel (different entity files).
- **US3 (P2)**: Can start after Foundational — Independent of US1/US2. Focuses on hook cache data structure handling.
- **US4 (P2)**: Can start after Foundational — Independent of US1/US2. Verifies hook concurrent behavior.
- **US5 (P3)**: Can start after Foundational — Independent of other stories. Verifies hook cleanup on unmount.

### Within Each User Story

- Hook wrapper function before component handler updates
- Core integration before edge case refinement
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

### Parallel Opportunities

- T005, T006, T007, T008, T009, T010 can all run in parallel (different entity files, no cross-dependencies)
- T013, T014 can run in parallel with US2 entity integrations (different concerns on same file)
- T015, T016 can run in parallel with US2/US3 work (verification tasks)
- T017 can run in parallel with T018 (different files)

---

## Parallel Example: User Story 2

```text
# All entity hook wrappers can proceed in parallel (different files):
Task T005: "Add useUndoableDeleteChore in useChores.ts"
Task T007: "Add useUndoableDeleteTool in useTools.ts"
Task T009: "Add useUndoableDeleteApp in useApps.ts"

# Then update corresponding components in parallel (different files):
Task T006: "Update ChoreCard.tsx delete handler"
Task T008: "Update ToolsPanel.tsx delete handler"
Task T010: "Update AppDetailView.tsx delete handler"

# Pipeline integration is sequential (cross-file dependency):
Task T011: "Wire undoable pipeline delete in useUnsavedPipelineGuard.ts"
Task T012: "Modify deletePipeline in usePipelineConfig.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify Toaster config (T001)
2. Complete Phase 2: Create `useUndoableDelete` hook (T002)
3. Complete Phase 3: Wire agents with undo delete (T003, T004)
4. **STOP and VALIDATE**: Delete an agent, verify undo toast, click Undo, verify restoration
5. Deploy/demo if ready — undo works for agents

### Incremental Delivery

1. Complete Setup + Foundational → Hook ready
2. Add US1 (agents) → Test independently → **MVP!**
3. Add US2 (all entities) → Test each type → Full entity coverage
4. Add US3 (cache edge cases) → Verify optimistic UI → Robust removal/restore
5. Add US4/US5 (concurrent + cleanup) → Verify edge cases → Production ready
6. Polish → Update dialog copy, verify error handling → **Ship**

### Parallel Team Strategy

With multiple developers:

1. All complete Setup + Foundational together (T001, T002)
2. Once Foundational is done:
   - Developer A: US1 agents (T003–T004) → then US3 cache handling (T013–T014)
   - Developer B: US2 chores+tools (T005–T008) → then US4 concurrent (T015)
   - Developer C: US2 apps+pipeline (T009–T012) → then US5 cleanup (T016)
3. All: Polish (T017–T019)

---

## Notes

- **[P]** tasks = different files, no dependencies on other in-progress tasks
- **[Story]** label maps task to specific user story for traceability
- No backend changes required — feature is entirely client-side
- No new dependencies — uses existing sonner ^2.0.7 and @tanstack/react-query ^5.91.0
- Hook contract defined in `specs/054-undoable-delete/contracts/useUndoableDelete.ts`
- Reference implementation in `specs/054-undoable-delete/quickstart.md`
- Entity-specific query keys documented in `specs/054-undoable-delete/data-model.md`
- Existing confirmation dialogs remain — undo toast is an additional safety net AFTER confirmation
- Pipeline uses `useCallback` + `useReducer` pattern, not `useMutation` — integration at consumer level via `useUnsavedPipelineGuard.ts`
- App delete navigates back on confirmation — undo toast remains visible globally via `AppLayout.tsx` Toaster
- Tool delete simplifies from two-step (dependency check → force delete) to single-step (confirmation → undoable force delete) to enable the undo pattern
