# Tasks: Optimistic Updates for Mutations

**Input**: Design documents from `/specs/001-optimistic-updates-mutations/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted per the Test Optionality principle (Constitution IV).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: No new project initialization needed. This feature modifies existing hook files in `solune/frontend/src/hooks/`. All infrastructure, types, query key factories, and the `onMutate`/snapshot/rollback pattern are already established.

(No setup tasks required — existing project structure is unchanged.)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No blocking prerequisites needed. All hooks, types, toast notifications (Sonner), and TanStack React Query v5 `useMutation` lifecycle callbacks are already in place.

(No foundational tasks required — all infrastructure exists.)

**Checkpoint**: Foundation ready — user story implementation can begin immediately.

---

## Phase 3: User Story 1 — Instant Feedback on Agent Creation (Priority: P1) 🎯 MVP

**Goal**: When a user creates a new agent, the agent appears in the agents list immediately without waiting for server response. On error, the list reverts and an error toast is shown.

**Independent Test**: Create an agent → verify it appears in the list instantly before the server responds. Simulate a server error → verify the agent is removed from the list and an error toast appears.

### Implementation for User Story 1

- [X] T001 [P] [US1] Add optimistic update lifecycle to `useCreateAgent` in `solune/frontend/src/hooks/useAgents.ts`
  - **`onMutate`**: Cancel in-flight queries for flat key (`agentKeys.list(projectId)`) and paginated key (`[...agentKeys.list(projectId), 'paginated']`). Snapshot both caches via `getQueryData`. Construct optimistic placeholder `AgentConfig` with `id: \`temp-${Date.now()}\``, user-provided `name`/`description`/`system_prompt`/`tools`, defaults `status: 'pending_pr'`, `source: 'local'`, ISO timestamps (see `data-model.md` for full shape). Prepend placeholder to flat array cache. Prepend to `pages[0].items` of paginated `InfiniteData` cache. Return `{ snapshot, queryKey, paginatedSnapshot, paginatedQueryKey }` context.
  - **`onError`**: Restore flat cache from `context.snapshot`, restore paginated cache from `context.paginatedSnapshot`, show `toast.error(error.message || 'Failed to create agent', { duration: Infinity })`.
  - **`onSettled`**: Invalidate `agentKeys.list(projectId)` queries to reconcile with server state.
  - **`onSuccess`**: Verify existing success toast is present (add if missing).
  - **Reference**: `useCreateChore` pattern in `useChores.ts:81–138`, contracts in `contracts/optimistic-cache-contract.md`.

**Checkpoint**: Agent creation provides instant visual feedback. Story is independently testable.

---

## Phase 4: User Story 2 — Instant Feedback on Agent Deletion (Priority: P1)

**Goal**: When a user deletes an agent, the agent disappears from the agents list immediately without waiting for server confirmation. On error, the agent reappears and an error toast is shown.

**Independent Test**: Delete an agent → verify it disappears from the list instantly. Simulate a server error → verify the agent reappears at its original position and an error toast appears.

### Implementation for User Story 2

- [X] T002 [US2] Add optimistic update lifecycle to `useDeleteAgent` in `solune/frontend/src/hooks/useAgents.ts`
  - **`onMutate`**: Cancel in-flight queries for both flat and paginated keys. Snapshot both caches. Filter deleted agent from flat array cache (`old?.filter(a => a.id !== agentId)`). Filter from all pages of paginated `InfiniteData` cache (`pages.map(page => ({ ...page, items: page.items.filter(...) }))`). Return context with both snapshots.
  - **`onError`**: Restore both caches from context, show `toast.error(error.message || 'Failed to delete agent', { duration: Infinity })`.
  - **`onSettled`**: Invalidate `agentKeys.list(projectId)` queries to reconcile with server state.
  - **Reference**: `useDeleteChore` pattern in `useChores.ts:181–213`, paginated delete contract in `contracts/optimistic-cache-contract.md`.

**Checkpoint**: Agent deletion provides instant visual feedback. Story is independently testable.

---

## Phase 5: User Story 3 — Instant Feedback on Tool Upload (Priority: P1)

**Goal**: When a user uploads a new tool, the tool appears in the tools list immediately. On error, the tool is removed and an error toast is shown (fixing the missing error notification).

**Independent Test**: Upload a tool → verify it appears in the tools list instantly. Simulate a server error → verify the tool is removed and an error toast appears.

### Implementation for User Story 3

- [X] T003 [P] [US3] Add optimistic update lifecycle to `uploadMutation` in `solune/frontend/src/hooks/useTools.ts`
  - **`onMutate`**: Cancel in-flight queries for wrapper object key (`toolKeys.list(projectId)`) and paginated key (`[...toolKeys.list(projectId), 'paginated']`). Snapshot both caches. Construct optimistic placeholder `McpToolConfig` with `id: \`temp-${Date.now()}\``, user-provided `name`/`command`/`description`, defaults `enabled: true`, ISO timestamps (see `data-model.md` for full shape). Prepend to wrapper cache (`{ ...old, tools: [placeholder, ...old.tools] }`). Prepend to `pages[0].items` of paginated `InfiniteData` cache. Return context with both snapshots.
  - **`onError`**: Restore wrapper cache and paginated cache from context, show `toast.error(error.message || 'Failed to upload tool', { duration: Infinity })` — this fixes FR-004 (missing error toast).
  - **`onSettled`**: Invalidate `toolKeys.list(projectId)` queries to reconcile with server state.
  - **Reference**: Wrapper object pattern from `research.md` Task 6, contracts in `contracts/optimistic-cache-contract.md`.

**Checkpoint**: Tool upload provides instant visual feedback and error notifications. Story is independently testable.

---

## Phase 6: User Story 4 — Instant Feedback on Project Creation (Priority: P1)

**Goal**: When a user creates a new project, the project appears in the projects list immediately. On error, the project is removed and an error toast is shown.

**Independent Test**: Create a project → verify it appears in the projects list instantly. Simulate a server error → verify it disappears and an error toast appears.

### Implementation for User Story 4

- [X] T004 [P] [US4] Add optimistic update lifecycle to `useCreateProject` in `solune/frontend/src/hooks/useProjects.ts`
  - **`onMutate`**: Cancel in-flight queries for projects key (`['projects']`). Snapshot wrapper cache (`{ projects: Project[] }`). Construct optimistic placeholder `Project` with `project_id: \`temp-${Date.now()}\``, `name` from `data.title`, `owner_login` from `data.owner`, defaults `type: 'ProjectV2'`, `status_columns: []`, `item_count: 0`, ISO timestamp for `cached_at` (see `data-model.md` for full shape). Prepend to wrapper cache (`{ ...old, projects: [placeholder, ...old.projects] }`). Return context with snapshot.
  - **Note**: Projects are NOT paginated per `research.md` Task 3 — no paginated cache handling needed.
  - **`onError`**: Restore wrapper cache from context, show `toast.error(error.message || 'Failed to create project', { duration: Infinity })`.
  - **`onSettled`**: Invalidate `['projects']` queries to reconcile with server state.
  - **Reference**: Wrapper object pattern from `research.md` Task 6.

**Checkpoint**: Project creation provides instant visual feedback. Story is independently testable.

---

## Phase 7: User Story 5 — Paginated List Consistency (Priority: P2)

**Goal**: All existing optimistic updates correctly target the paginated (`InfiniteData`) cache structure in addition to the flat array / wrapper object cache, so that changes are immediately visible in paginated/infinite scroll views.

**Independent Test**: Perform a create/update/delete mutation on a paginated entity list → verify the change appears on the current page without scrolling or refreshing.

### Implementation for User Story 5

#### Chore Hooks — `solune/frontend/src/hooks/useChores.ts`

- [X] T005 [P] [US5] Extend all chore mutation hooks for paginated cache awareness in `solune/frontend/src/hooks/useChores.ts`
  - For each of `useCreateChore`, `useUpdateChore`, `useDeleteChore`, and `useInlineUpdateChore`:
    1. Add `cancelQueries` for paginated key `[...choreKeys.list(projectId), 'paginated']` in `onMutate`.
    2. Snapshot paginated cache via `getQueryData`.
    3. Apply matching paginated update:
       - `useCreateChore`: prepend to `pages[0].items`.
       - `useUpdateChore` / `useInlineUpdateChore`: map across all `pages[].items` replacing matched chore.
       - `useDeleteChore`: filter from all `pages[].items`.
    4. Include `paginatedSnapshot` and `paginatedQueryKey` in returned context.
    5. Add paginated cache restore from `context.paginatedSnapshot` in `onError`.
  - **Reference**: Paginated contracts in `contracts/optimistic-cache-contract.md`, existing `removeEntityFromCache` in `useUndoableDelete.ts:74–125`.

#### App Hooks — `solune/frontend/src/hooks/useApps.ts`

- [X] T006 [P] [US5] Extend all app mutation hooks for paginated cache awareness in `solune/frontend/src/hooks/useApps.ts`
  - For each of `useCreateApp`, `useUpdateApp`, `useDeleteApp`, `useStartApp`, and `useStopApp`:
    1. Add `cancelQueries` for paginated key `[...appKeys.list(), 'paginated']` in `onMutate`.
    2. Snapshot paginated cache via `getQueryData`.
    3. Apply matching paginated update:
       - `useCreateApp`: prepend to `pages[0].items`.
       - `useUpdateApp` / `useStartApp` / `useStopApp`: map across all `pages[].items` replacing matched app.
       - `useDeleteApp`: filter from all `pages[].items`.
    4. Include `paginatedSnapshot` and `paginatedQueryKey` in returned context.
    5. Add paginated cache restore from `context.paginatedSnapshot` in `onError`.
  - **Reference**: Paginated contracts in `contracts/optimistic-cache-contract.md`.

#### Tool Delete Hook — `solune/frontend/src/hooks/useTools.ts`

- [X] T007 [US5] Extend tool delete mutation hook for paginated cache awareness in `solune/frontend/src/hooks/useTools.ts`
  - In existing delete `onMutate`:
    1. Add `cancelQueries` for paginated key `[...toolKeys.list(projectId), 'paginated']`.
    2. Snapshot paginated cache via `getQueryData`.
    3. Filter deleted tool from all `pages[].items` of paginated `InfiniteData` cache.
    4. Include `paginatedSnapshot` and `paginatedQueryKey` in returned context.
    5. Add paginated cache restore from `context.paginatedSnapshot` in `onError`.
  - **Reference**: Paginated delete contract in `contracts/optimistic-cache-contract.md`.

**Checkpoint**: All entity list views using paginated/infinite scroll correctly reflect optimistic updates.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and edge case hardening across all modified hooks

- [X] T008 Validate edge case guards across all modified hooks in `solune/frontend/src/hooks/` — Ensure each `onMutate` handler guards against empty/undefined cache (`if (!snapshot) return`), guards against missing `projectId` (`if (!projectId) return`), and that paginated updates guard against unloaded paginated cache (`if (!old?.pages?.length) return old`). Verify rapid sequential mutations produce independent snapshots (each `onMutate` snapshots current cache state including previous optimistic entries). Reference: edge cases in `contracts/optimistic-cache-contract.md` section "Edge Cases Handled by Contract"
- [X] T009 Run quickstart.md validation checklist against all 11 scenarios in `specs/001-optimistic-updates-mutations/quickstart.md` — verify agent create/delete, tool upload, project create all provide instant feedback, error rollback works for each, and paginated views correctly reflect mutations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No tasks — existing project
- **Foundational (Phase 2)**: No tasks — all infrastructure exists
- **User Stories (Phases 3–7)**: Can begin immediately
  - US1–US4 (P1): Can start in parallel where they modify different files
  - US5 (P2): Can start after US3 completes for `useTools.ts` tasks; chore and app tasks are independent
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)** — Agent Creation: No dependencies. Modifies `useAgents.ts`. Can start immediately.
- **US2 (P1)** — Agent Deletion: Depends on T001 completion (same file: `useAgents.ts`). Otherwise independent.
- **US3 (P1)** — Tool Upload: No dependencies on other stories. Modifies `useTools.ts`. Can start immediately.
- **US4 (P1)** — Project Creation: No dependencies. Modifies `useProjects.ts`. Can start immediately.
- **US5 (P2)** — Paginated Cache:
  - T005 (chores): Independent — `useChores.ts` not modified by US1–US4. Can start immediately.
  - T006 (apps): Independent — `useApps.ts` not modified by US1–US4. Can start immediately.
  - T007 (tools): Depends on T003 (US3) — same file `useTools.ts`. Must start after T003 completes.

### Within Each User Story

- Each task is a complete unit: `onMutate` + `onError` + `onSettled` (+ `onSuccess` verification)
- Core implementation before edge case validation
- Story complete before moving to polish

### Parallel Opportunities

- **T001 (US1)**, **T003 (US3)**, **T004 (US4)**: All [P] — different files, can run simultaneously
- **T005 (US5 chores)**, **T006 (US5 apps)**: Both [P] — different files, can run simultaneously
- **T002 (US2)**: Sequential after T001 — same file (`useAgents.ts`)
- **T007 (US5 tools)**: Sequential after T003 — same file (`useTools.ts`)

---

## Parallel Example: User Stories 1, 3, 4

```text
# These three tasks can launch simultaneously (different files):
T001 [P] [US1] — useAgents.ts (agent creation)
T003 [P] [US3] — useTools.ts (tool upload)
T004 [P] [US4] — useProjects.ts (project creation)

# After T001 completes:
T002 [US2] — useAgents.ts (agent deletion)

# After all P1 stories, launch paginated fixes in parallel:
T005 [P] [US5] — useChores.ts (chore hooks)
T006 [P] [US5] — useApps.ts (app hooks)

# After T003 completes:
T007 [US5] — useTools.ts (tool delete hook)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001: Add optimistic create to `useCreateAgent`
2. **STOP and VALIDATE**: Create an agent → verify instant feedback + error rollback
3. Deploy/demo if ready — single story delivers user value

### Incremental Delivery

1. T001 (US1 — agent create) → Validate → ✅ MVP
2. T002 (US2 — agent delete) → Validate → Full agent lifecycle optimistic
3. T003 (US3 — tool upload) → Validate → Tool feedback + error toast gap closed
4. T004 (US4 — project create) → Validate → All 4 missing mutations resolved (FR-001 through FR-005)
5. T005–T007 (US5 — paginated gap) → Validate → Complete cache consistency (FR-008 through FR-010)
6. T008–T009 (Polish) → Validate → All success criteria met (SC-001 through SC-006)

### Parallel Team Strategy

With multiple developers:

1. **Developer A**: T001 → T002 (agent creation + deletion in `useAgents.ts`)
2. **Developer B**: T003 → T007 (tool upload + tool delete paginated in `useTools.ts`)
3. **Developer C**: T004 (project creation in `useProjects.ts`)
4. **Developer D**: T005 (chore paginated in `useChores.ts`)
5. **Developer E**: T006 (app paginated in `useApps.ts`)
6. **All**: T008–T009 (polish after stories merge)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in same file
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No test tasks included (tests not requested in spec — Constitution IV: Test Optionality)
- Projects are NOT paginated (per `research.md` Task 3) — no paginated cache handling in US4
- Tools and Projects use wrapper object caches (`{ tools: T[] }`, `{ projects: T[] }`) — not raw arrays
- All `onError` handlers use `toast.error(msg, { duration: Infinity })` pattern per `research.md` Task 4
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
