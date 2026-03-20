# Implementation Plan: Optimistic UI Updates for Mutations

**Branch**: `054-optimistic-ui-updates` | **Date**: 2026-03-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/054-optimistic-ui-updates/spec.md`

## Summary

All 14+ user-facing mutations across chores, apps, tools, pipelines, and the project board currently use a "fire-and-wait" pattern — call API, wait for response, invalidate queries, then re-render. This creates a sluggish user experience, especially for high-frequency interactions like board drag-and-drop and chore CRUD.

This plan adds TanStack Query v5's optimistic update pattern (`onMutate` → snapshot → `onError` → rollback → `onSettled` → invalidate) to every in-scope mutation. It also introduces one new backend endpoint (`PATCH /board/projects/{project_id}/items/{item_id}/status`) to support board status changes, plus a corresponding frontend API method. Optimistically created items will display a visual pending indicator; updates and deletes will not.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.x + React 19.2 (frontend)
**Primary Dependencies**: FastAPI (backend), TanStack Query v5.91 + React 19 (frontend), Sonner v2 (toasts)
**Storage**: SQLite with aiosqlite (backend local state), GitHub Projects GraphQL API (board data source)
**Testing**: Vitest + happy-dom + @testing-library/react (frontend), ruff + pyright (backend linting)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (separate `solune/backend/` and `solune/frontend/` trees)
**Performance Goals**: Optimistic UI updates must appear within 100ms of user action (perceived instant); rollback on error within 2 seconds
**Constraints**: No additional libraries; TanStack Query's built-in `onMutate`/`onError`/`onSettled` callbacks are sufficient. No offline-first queue or retry logic.
**Scale/Scope**: 14 mutations across 8 files (4 chore, 5 app, 1 tool delete, 1 pipeline delete, 1 board status, 2 board wiring)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` includes 5 prioritized user stories with Given-When-Then acceptance criteria, scope boundaries, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`; tasks deferred to `/speckit.tasks` |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not mandated by spec; existing Vitest + Playwright suites validate no regressions. Tests optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Uses TanStack Query's built-in optimistic pattern — no new state management, no new libraries, no custom abstractions. Each mutation hook adds 3 callbacks inline |

**Gate Result**: ✅ ALL GATES PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/054-optimistic-ui-updates/
├── plan.md              # This file
├── research.md          # Phase 0 — research findings
├── data-model.md        # Phase 1 — entity model
├── quickstart.md        # Phase 1 — implementation quickstart
├── contracts/           # Phase 1 — API contracts
│   └── board-status-update.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   └── src/
│       ├── api/
│       │   └── board.py              # ADD: PATCH status endpoint
│       ├── models/
│       │   └── board.py              # ADD: StatusUpdateRequest model
│       └── services/
│           └── github_projects/
│               └── projects.py       # REUSE: update_item_status_by_name()
└── frontend/
    └── src/
        ├── hooks/
        │   ├── useChores.ts          # MODIFY: add optimistic callbacks to 4 mutations
        │   ├── useApps.ts            # MODIFY: add optimistic callbacks to 5 mutations
        │   ├── useTools.ts           # MODIFY: add optimistic delete
        │   ├── usePipelineConfig.ts  # MODIFY: add optimistic delete
        │   ├── useProjectBoard.ts    # REFERENCE: query keys
        │   └── useBoardDragDrop.ts   # NO CHANGES: already calls onStatusUpdate
        ├── pages/
        │   └── ProjectsPage.tsx      # MODIFY: wire board status mutation
        ├── services/
        │   └── api.ts                # ADD: boardApi.updateItemStatus()
        └── types/
            └── index.ts              # REFERENCE: BoardItem, BoardColumn, BoardDataResponse
```

**Structure Decision**: Web application structure with separate `solune/backend/` and `solune/frontend/` trees. All changes are modifications to existing files; no new files are created outside the contracts directory.

## Implementation Phases

### Phase 1 — Board Drag-and-Drop (Highest Impact, P1)

Sequential dependency chain:

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 1.1 | `backend/src/models/board.py` | Add `StatusUpdateRequest` Pydantic model: `{ status: str }` | — |
| 1.2 | `backend/src/api/board.py` | Add `PATCH /projects/{project_id}/items/{item_id}/status` endpoint. Accepts `StatusUpdateRequest`, calls `update_item_status_by_name()`, returns `{ success: bool }` | 1.1 |
| 1.3 | `frontend/src/services/api.ts` | Add `boardApi.updateItemStatus(projectId, itemId, status)` — PATCH call to new endpoint | 1.2 |
| 1.4 | `frontend/src/pages/ProjectsPage.tsx` | Wire `useMutation` with full optimistic pattern: `onMutate` snapshots `['board', 'data', projectId]` and moves `BoardItem` between `BoardColumn` arrays; `onError` rolls back; `onSettled` invalidates. Pass callback as `onStatusUpdate` prop to `ProjectBoard` | 1.3 |

### Phase 2 — Chore Mutations (P2)

All 4 steps can be done in parallel:

| Step | File | Mutation | onMutate Pattern |
|------|------|----------|------------------|
| 2.1 | `useChores.ts` | `useCreateChore` | Generate temp ID, insert placeholder `Chore` into `choreKeys.list(projectId)` cache |
| 2.2 | `useChores.ts` | `useUpdateChore` | Snapshot list, apply field updates in-place via `setQueryData` |
| 2.3 | `useChores.ts` | `useDeleteChore` | Snapshot list, filter out deleted chore |
| 2.4 | `useChores.ts` | `useInlineUpdateChore` | Same pattern as 2.2, applied to inline update mutation |

Common pattern for all: `onError` → rollback to snapshot; `onSettled` → `invalidateQueries({ queryKey: choreKeys.list(projectId) })`

### Phase 3 — App Mutations (P3)

All 5 steps can be done in parallel with Phase 2:

| Step | File | Mutation | onMutate Pattern |
|------|------|----------|------------------|
| 3.1 | `useApps.ts` | `useCreateApp` | Generate temp name, insert placeholder `App` into `appKeys.list()` cache |
| 3.2 | `useApps.ts` | `useUpdateApp` | Snapshot list + detail, apply field patches in-place |
| 3.3 | `useApps.ts` | `useDeleteApp` | Snapshot list, filter out deleted app |
| 3.4 | `useApps.ts` | `useStartApp` | Snapshot, flip `status` to `"active"` in cache instantly |
| 3.5 | `useApps.ts` | `useStopApp` | Snapshot, flip `status` to `"stopped"` in cache instantly |

Common pattern: `onError` → rollback; `onSettled` → invalidate `appKeys.list()` and `appKeys.detail(name)` where applicable.

### Phase 4 — Tool & Pipeline Mutations (P4)

Both steps can be done in parallel with Phases 2 and 3:

| Step | File | Mutation | onMutate Pattern |
|------|------|----------|------------------|
| 4.1 | `useTools.ts` | `deleteMutation` | Snapshot `toolKeys.list(projectId)`, filter out deleted tool |
| 4.2 | `usePipelineConfig.ts` | `deletePipeline` | Snapshot `pipelineKeys.list(projectId)`, filter out deleted pipeline |

Common pattern: `onError` → rollback; `onSettled` → invalidate list query.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Optimistic pattern | TanStack Query `onMutate`/`onError`/`onSettled` | Native support in v5, no external state needed, consistent with existing hook architecture |
| New endpoint response | Minimal `{ success: bool }` | `onSettled` re-fetches full data anyway; minimal response reduces payload and endpoint complexity |
| Visual pending indicator | Reduced opacity on optimistically created items only | Creates clear signal for creates (temp ID visible); updates/deletes are brief enough not to need it (FR-008, FR-009) |
| Cache key strategy | Reuse existing key factories (`choreKeys`, `appKeys`, `toolKeys`, `pipelineKeys`, `['board', 'data', projectId]`) | Already established; no new key patterns needed |
| Excluded mutations | Chat, trigger polling, pipeline save, `createWithAutoMerge` | Each has distinct state management patterns that would conflict with optimistic updates |
| Concurrent mutations | Independent snapshots per mutation | TanStack Query v5 handles concurrent mutations naturally via separate context objects |
| Empty cache handling | Skip optimistic update, fall back to fire-and-wait | If no cached data exists to snapshot, optimistic update has no baseline to modify (edge case from spec) |

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
