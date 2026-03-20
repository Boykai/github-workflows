# Tasks: Optimistic UI Updates for Mutations

**Input**: Design documents from `/specs/054-optimistic-ui-updates/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested by the feature specification. Existing Vitest + Playwright suites validate no regressions.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Cross-Cutting Note**: User Story 5 (Graceful Error Recovery, P1) is delivered incrementally — every mutation task includes `onError` rollback + error toast + `onSettled` cache reconciliation as part of the optimistic pattern. US5 does not have a separate phase because it is inherent in every task's implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add backend request/response models needed by the new board status endpoint

- [ ] T001 Add `StatusUpdateRequest` and `StatusUpdateResponse` Pydantic models in `solune/backend/src/models/board.py`

---

## Phase 2: Foundational (Backend Endpoint + Frontend API)

**Purpose**: New backend endpoint and frontend API method required before board status optimistic updates can be wired

**⚠️ CRITICAL**: Phase 3 (US1 Board Drag-and-Drop) cannot begin until this phase is complete. Phases 4–6 (Chore/App/Tool/Pipeline mutations) have no dependency on this phase and can start immediately after Phase 1.

- [ ] T002 [P] Add `PATCH /projects/{project_id}/items/{item_id}/status` endpoint in `solune/backend/src/api/board.py` — accepts `StatusUpdateRequest`, calls `update_item_status_by_name()` from `services/github_projects/projects.py`, returns `StatusUpdateResponse`
- [ ] T003 [P] Add `boardApi.updateItemStatus(projectId, itemId, status)` method to the `boardApi` object in `solune/frontend/src/services/api.ts` — PATCH call to the new endpoint per `contracts/board-status-update.yaml`

**Checkpoint**: Backend endpoint deployed and frontend API method available — board optimistic wiring can now proceed

---

## Phase 3: User Story 1 — Board Drag-and-Drop Feels Instant (Priority: P1) 🎯 MVP

**Goal**: Dragging a board card between status columns updates the UI instantly; rolls back with error toast on failure

**Independent Test**: Drag any board card between columns and observe instant visual movement. Simulate network failure and verify the card snaps back with an error toast.

**US5 Error Recovery**: Built into `onError` — restores snapshot and displays toast on any server/network failure

### Implementation for User Story 1

- [ ] T004 [US1] Wire `useMutation` with full optimistic pattern in `solune/frontend/src/pages/ProjectsPage.tsx` — `onMutate`: cancel outgoing refetches for `['board', 'data', projectId]`, snapshot `BoardDataResponse`, move `BoardItem` from source `BoardColumn.items[]` to target `BoardColumn.items[]` via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: `invalidateQueries` to reconcile with server. Pass mutation callback as `onStatusUpdate` prop to `ProjectBoard`

**Checkpoint**: Board drag-and-drop is fully optimistic and independently testable — US1 complete

---

## Phase 4: User Story 2 — Chore CRUD Operations Are Responsive (Priority: P2)

**Goal**: Create, update, delete, and inline-edit chores show instant UI feedback; revert cleanly on failure

**Independent Test**: Create a chore and verify it appears immediately with pending visual indicator. Edit a chore inline and verify changes appear instantly. Delete a chore and verify it disappears immediately. Simulate network failure for each operation and verify rollback + error toast.

**US5 Error Recovery**: Built into each mutation's `onError` — restores snapshot and displays toast

**Note**: All 4 tasks modify the same file (`useChores.ts`) and should be implemented sequentially within this phase. However, this entire phase can run in parallel with Phases 5 and 6 (different files).

### Implementation for User Story 2

- [ ] T005 [US2] Add optimistic create callbacks to `useCreateChore` in `solune/frontend/src/hooks/useChores.ts` — `onMutate`: cancel queries for `choreKeys.list(projectId)`, snapshot list, generate temp ID, insert placeholder `Chore` with `_optimistic: true` flag at start of list via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate `choreKeys.list(projectId)` to replace placeholder with server data
- [ ] T006 [US2] Add optimistic update callbacks to `useUpdateChore` in `solune/frontend/src/hooks/useChores.ts` — `onMutate`: cancel queries, snapshot list, apply field updates in-place to matching chore via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate list
- [ ] T007 [US2] Add optimistic delete callbacks to `useDeleteChore` in `solune/frontend/src/hooks/useChores.ts` — `onMutate`: cancel queries, snapshot list, filter out deleted chore by ID via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate list
- [ ] T008 [US2] Add optimistic inline update callbacks to `useInlineUpdateChore` in `solune/frontend/src/hooks/useChores.ts` — `onMutate`: cancel queries, snapshot list, apply field update in-place (same pattern as T006); `onError`: restore snapshot, show error toast; `onSettled`: invalidate list

**Checkpoint**: All 4 chore mutations are optimistic — US2 complete and independently testable

---

## Phase 5: User Story 3 — App Status Changes Feel Immediate (Priority: P3)

**Goal**: App start/stop toggles status badge instantly; app create/update/delete show instant UI feedback; all revert on failure

**Independent Test**: Click start on a stopped app and verify status badge flips to "active" instantly. Click stop and verify it flips to "stopped". Create/update/delete an app and verify instant feedback. Simulate failures and verify rollback + toast for each operation.

**US5 Error Recovery**: Built into each mutation's `onError` — restores snapshot and displays toast

**Note**: All 5 tasks modify the same file (`useApps.ts`) and should be implemented sequentially within this phase. However, this entire phase can run in parallel with Phases 4 and 6 (different files).

### Implementation for User Story 3

- [ ] T009 [US3] Add optimistic create callbacks to `useCreateApp` in `solune/frontend/src/hooks/useApps.ts` — `onMutate`: cancel queries for `appKeys.list()`, snapshot list, generate temp name, insert placeholder `App` with `_optimistic: true` flag via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate `appKeys.list()`
- [ ] T010 [US3] Add optimistic update callbacks to `useUpdateApp` in `solune/frontend/src/hooks/useApps.ts` — `onMutate`: cancel queries for `appKeys.list()` and `appKeys.detail(name)`, snapshot both, apply field patches in-place via `setQueryData` on both cache entries; `onError`: restore both snapshots, show error toast; `onSettled`: invalidate `appKeys.list()` and `appKeys.detail(name)`
- [ ] T011 [US3] Add optimistic delete callbacks to `useDeleteApp` in `solune/frontend/src/hooks/useApps.ts` — `onMutate`: cancel queries for `appKeys.list()`, snapshot list, filter out deleted app by name via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate `appKeys.list()`
- [ ] T012 [US3] Add optimistic start callbacks to `useStartApp` in `solune/frontend/src/hooks/useApps.ts` — `onMutate`: cancel queries, snapshot list + detail, flip `status` to `"active"` for matching app via `setQueryData`; `onError`: restore snapshots, show error toast; `onSettled`: invalidate `appKeys.list()` and `appKeys.detail(name)`
- [ ] T013 [US3] Add optimistic stop callbacks to `useStopApp` in `solune/frontend/src/hooks/useApps.ts` — `onMutate`: cancel queries, snapshot list + detail, flip `status` to `"stopped"` for matching app via `setQueryData`; `onError`: restore snapshots, show error toast; `onSettled`: invalidate `appKeys.list()` and `appKeys.detail(name)`

**Checkpoint**: All 5 app mutations are optimistic — US3 complete and independently testable

---

## Phase 6: User Story 4 — Tool and Pipeline Deletions Are Instant (Priority: P4)

**Goal**: Deleting a tool or pipeline removes it from the list instantly; reverts with error toast on failure

**Independent Test**: Delete a tool and verify it disappears immediately. Delete a pipeline and verify it disappears immediately. Simulate failure and verify each reappears with an error toast.

**US5 Error Recovery**: Built into each mutation's `onError` — restores snapshot and displays toast

### Implementation for User Story 4

- [ ] T014 [P] [US4] Add optimistic delete callbacks to tool delete mutation in `solune/frontend/src/hooks/useTools.ts` — `onMutate`: cancel queries for `toolKeys.list(projectId)`, snapshot list, filter out deleted tool by ID via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate `toolKeys.list(projectId)`
- [ ] T015 [P] [US4] Add optimistic delete callbacks to pipeline delete mutation in `solune/frontend/src/hooks/usePipelineConfig.ts` — `onMutate`: cancel queries for `pipelineKeys.list(projectId)`, snapshot list, filter out deleted pipeline by ID via `setQueryData`; `onError`: restore snapshot, show error toast; `onSettled`: invalidate `pipelineKeys.list(projectId)`

**Checkpoint**: Tool and pipeline deletes are optimistic — US4 complete and independently testable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validation, lint, and verification across all stories

- [ ] T016 [P] Run backend lint (`ruff check src/ tests/`) and type-check (`pyright src/`) on `solune/backend/`
- [ ] T017 [P] Run frontend lint (`npm run lint`), type-check (`npm run type-check`), and test suite (`npm run test -- --run`) on `solune/frontend/`
- [ ] T018 Run `specs/054-optimistic-ui-updates/quickstart.md` validation scenarios — verify board drag-and-drop, chore CRUD, app start/stop, and tool/pipeline delete all demonstrate optimistic behavior with proper error rollback

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001 models) — T002 and T003 can run in parallel (different files)
- **US1 Board (Phase 3)**: Depends on Phase 2 (T002 endpoint + T003 API method)
- **US2 Chores (Phase 4)**: Depends on Phase 1 only — **NO dependency on Phase 2** — can start immediately after Setup
- **US3 Apps (Phase 5)**: Depends on Phase 1 only — **NO dependency on Phase 2** — can start immediately after Setup
- **US4 Tool/Pipeline (Phase 6)**: Depends on Phase 1 only — **NO dependency on Phase 2** — can start immediately after Setup
- **Polish (Phase 7)**: Depends on all prior phases being complete

### User Story Dependencies

- **US1 Board (P1)**: Requires Foundational phase (backend endpoint + frontend API). This is the MVP.
- **US2 Chores (P2)**: Independent of all other user stories. Can start after Setup.
- **US3 Apps (P3)**: Independent of all other user stories. Can start after Setup.
- **US4 Tool/Pipeline (P4)**: Independent of all other user stories. Can start after Setup.
- **US5 Error Recovery (P1)**: Cross-cutting — delivered incrementally through every task's `onError`/`onSettled` callbacks. Fully complete when all phases are done.

### Within Each User Story

- Each mutation follows the same pattern: `onMutate` → snapshot → apply → `onError` → rollback + toast → `onSettled` → invalidate
- Skip optimistic update if cache is empty (fall back to fire-and-wait per R9)
- Cancel outgoing refetches before snapshot to prevent overwrites
- Create operations include `_optimistic: true` flag for visual pending indicator (FR-008)
- Update/delete operations do NOT require visual distinction (FR-009)

### Parallel Opportunities

- **Phase 2**: T002 (backend endpoint) and T003 (frontend API) can run in parallel — different codebases
- **Phases 4, 5, 6**: All three user story phases can run in parallel after Setup — they modify different files (`useChores.ts`, `useApps.ts`, `useTools.ts`, `usePipelineConfig.ts`)
- **Phase 6**: T014 (useTools.ts) and T015 (usePipelineConfig.ts) can run in parallel — different files
- **Phase 7**: T016 (backend validation) and T017 (frontend validation) can run in parallel

---

## Parallel Example: Phases 4, 5, 6 (After Setup)

```bash
# These three phases can run simultaneously (different files):

# Developer A: Phase 4 — Chore Mutations (useChores.ts)
Task: "T005 [US2] Add optimistic create callbacks to useCreateChore"
Task: "T006 [US2] Add optimistic update callbacks to useUpdateChore"
Task: "T007 [US2] Add optimistic delete callbacks to useDeleteChore"
Task: "T008 [US2] Add optimistic inline update callbacks to useInlineUpdateChore"

# Developer B: Phase 5 — App Mutations (useApps.ts)
Task: "T009 [US3] Add optimistic create callbacks to useCreateApp"
Task: "T010 [US3] Add optimistic update callbacks to useUpdateApp"
Task: "T011 [US3] Add optimistic delete callbacks to useDeleteApp"
Task: "T012 [US3] Add optimistic start callbacks to useStartApp"
Task: "T013 [US3] Add optimistic stop callbacks to useStopApp"

# Developer C: Phase 6 — Tool/Pipeline Deletions (useTools.ts + usePipelineConfig.ts)
Task: "T014 [P] [US4] Add optimistic delete to useTools.ts"
Task: "T015 [P] [US4] Add optimistic delete to usePipelineConfig.ts"
```

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Backend and frontend can be developed simultaneously:
Task: "T002 [P] Add PATCH endpoint in solune/backend/src/api/board.py"
Task: "T003 [P] Add boardApi.updateItemStatus() in solune/frontend/src/services/api.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001 — backend models)
2. Complete Phase 2: Foundational (T002–T003 — endpoint + API method)
3. Complete Phase 3: US1 Board Drag-and-Drop (T004 — optimistic board mutation)
4. **STOP and VALIDATE**: Drag a card between columns — it should move instantly and snap back on error
5. Deploy/demo if ready — board drag-and-drop is the highest-impact improvement

### Incremental Delivery

1. Complete Setup + Foundational → Infrastructure ready
2. Add US1 Board → Test independently → Deploy/Demo (**MVP!**)
3. Add US2 Chores → Test independently → Deploy/Demo
4. Add US3 Apps → Test independently → Deploy/Demo
5. Add US4 Tool/Pipeline → Test independently → Deploy/Demo
6. Each story adds optimistic UX to another domain without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. All: Complete Phase 1 Setup together (1 task)
2. Split:
   - Developer A: Phase 2 Foundational (backend) → Phase 3 US1 Board
   - Developer B: Phase 4 US2 Chores (no dependency on Phase 2)
   - Developer C: Phase 5 US3 Apps + Phase 6 US4 Tool/Pipeline
3. All: Phase 7 Polish (validation across all changes)

---

## Reference: Key Files & Cache Keys

| File | Cache Key | Entity |
|------|-----------|--------|
| `solune/frontend/src/pages/ProjectsPage.tsx` | `['board', 'data', projectId]` | `BoardDataResponse` |
| `solune/frontend/src/hooks/useChores.ts` | `choreKeys.list(projectId)` → `['chores', 'list', projectId]` | `Chore[]` |
| `solune/frontend/src/hooks/useApps.ts` | `appKeys.list()` → `['apps', 'list']` | `App[]` |
| `solune/frontend/src/hooks/useApps.ts` | `appKeys.detail(name)` → `['apps', 'detail', name]` | `App` |
| `solune/frontend/src/hooks/useTools.ts` | `toolKeys.list(projectId)` → `['tools', 'list', projectId]` | `McpToolConfig[]` |
| `solune/frontend/src/hooks/usePipelineConfig.ts` | `pipelineKeys.list(projectId)` → `['pipelines', 'list', projectId]` | `PipelineConfig[]` |

## Reference: Optimistic Pattern per Mutation Type

| Pattern | Mutations | `onMutate` Action |
|---------|-----------|-------------------|
| **Move** | Board status (T004) | Remove item from source column, add to target column |
| **Create** | Chore create (T005), App create (T009) | Insert placeholder with temp ID + `_optimistic: true` |
| **Update** | Chore update (T006), Chore inline (T008), App update (T010) | Map over list, merge updated fields in-place |
| **Delete** | Chore delete (T007), App delete (T011), Tool delete (T014), Pipeline delete (T015) | Filter item out by ID |
| **Status flip** | App start (T012), App stop (T013) | Map over list, update `status` field for matching item |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- US5 (Graceful Error Recovery) is cross-cutting and delivered through every task — no separate phase needed
- All mutations skip optimistic update if cache is empty (edge case from research.md R9 — fall back to fire-and-wait)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No new libraries required — uses TanStack Query v5 built-in `onMutate`/`onError`/`onSettled`
- No new files created — all changes are additions/modifications to existing files
