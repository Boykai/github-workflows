# Contract: State Management

**Feature**: `043-projects-page-audit` | **Date**: 2026-03-16 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the data flow and state management patterns for the Projects page after the audit refactoring. It documents how hooks, queries, and mutations are organized and how data flows between components.

## Hook Architecture

### Data Flow Diagram

```text
API Layer (services/api.ts)
  ├── boardApi.listProjects()     ──→ useProjectBoard.projectsQuery
  ├── boardApi.getBoardData()     ──→ useProjectBoard.boardQuery
  ├── projectsApi.list()          ──→ useProjects.projectsQuery
  ├── projectsApi.select()        ──→ useProjects.selectMutation
  ├── pipelinesApi.list()         ──→ PipelineSelector (internal query)
  ├── pipelinesApi.getAssignment()──→ PipelineSelector (assignment query)
  └── pipelinesApi.setAssignment()──→ PipelineSelector (assignment mutation)

Hook Layer
  ├── useProjects(selectedId)
  │   ├── Returns: projects, selectedProject, isLoading, selectProject
  │   └── Feeds: ProjectSelector component
  │
  ├── useProjectBoard({ selectedProjectId, onProjectSelect })
  │   ├── Returns: boardData, boardLoading, boardError, selectedProjectId, ...
  │   └── Feeds: ProjectBoard, BoardToolbar, PipelineSelector
  │
  ├── useBoardRefresh({ projectId, boardData })
  │   ├── Returns: refresh, isRefreshing, error, rateLimitInfo, isRateLimitLow, resetTimer
  │   └── Feeds: BoardHeader (refresh), RateLimitBanner (rate limit info)
  │
  ├── useRealTimeSync(selectedProjectId, { onRefreshTriggered })
  │   ├── Returns: status, lastUpdate
  │   └── Feeds: BoardHeader (sync status)
  │
  ├── useBoardControls({ boardData, projectId, ... })
  │   ├── Returns: drag handlers, filter/sort state, agent config actions
  │   └── Feeds: ProjectBoard, BoardToolbar
  │
  └── useAvailableAgents(selectedProjectId)
      ├── Returns: agents
      └── Feeds: PipelineSelector

Component Layer
  ProjectsPage ──→ orchestrates all components
    ├── ProjectSelector ←── useProjects
    ├── BoardHeader ←── useBoardRefresh + useRealTimeSync
    ├── RateLimitBanner ←── useBoardRefresh
    ├── PipelineSelector ←── useProjectBoard + useAvailableAgents (+ internal pipeline query)
    ├── BoardToolbar ←── useBoardControls
    ├── ProjectBoard ←── useProjectBoard + useBoardControls
    └── IssueDetailModal ←── selectedItem state
```

## Query Key Conventions

All queries follow the established key pattern used across the application:

| Query | Key Pattern | staleTime | Notes |
|-------|-------------|-----------|-------|
| Project list (board) | `['board', 'projects']` | `STALE_TIME_PROJECTS` (15 min) | Board-context project list |
| Board data | `['board', 'data', projectId]` | `STALE_TIME_SHORT` (60s) | Per-project board data |
| User projects | `['projects']` | `STALE_TIME_PROJECTS` (15 min) | Global project list |
| Project tasks | `['projects', projectId, 'tasks']` | `STALE_TIME_PROJECTS` (15 min) | Per-project task list |
| Pipeline list | `['pipelines', projectId]` | `STALE_TIME_PROJECTS` (15 min) | Per-project pipelines |
| Pipeline assignment | `['pipelines', 'assignment', projectId]` | `STALE_TIME_PROJECTS` (15 min) | Per-project pipeline assignment |

**Invariants**:
- No two components should independently fetch the same query key. All data flows through hooks.
- `staleTime` constants are imported from `@/constants` — never hardcoded.
- Board data refetches are coordinated through `useBoardRefresh` to avoid duplicate calls.

## Mutation Contracts

### Project Selection

| Property | Value |
|----------|-------|
| Hook | `useProjects` |
| API call | `projectsApi.select(projectId)` |
| On success | Invalidates `['projects']`; updates local state |
| On error | Toast: "Could not switch project. Please try again." |
| Optimistic | No — waits for server confirmation |

### Pipeline Assignment

| Property | Value |
|----------|-------|
| Hook | `PipelineSelector` (internal mutation) |
| API call | `pipelinesApi.setAssignment(projectId, pipelineId)` |
| On success | Invalidates `['pipelines', 'assignment', ...]`; toast: "Pipeline assigned successfully." |
| On error | Toast: "Could not assign pipeline. [Error message]. Please try again." |
| Confirmation | Required if overriding existing assignment (FR-024) |
| Optimistic | No — waits for server confirmation |

### Board Refresh

| Property | Value |
|----------|-------|
| Hook | `useBoardRefresh` |
| API call | `boardApi.getBoardData(projectId, refresh=true)` |
| On success | Updates board query cache; resets timer |
| On error | Inline error message with retry; rate limit banner if applicable |
| Rate limit | Detects via `isRateLimitApiError()`; shows `RateLimitBanner` with reset countdown |

## State Ownership Rules

| State | Owner | Shared Via |
|-------|-------|-----------|
| Selected project ID | `useProjects` hook | Props from ProjectsPage |
| Board data | `useProjectBoard` hook | Props from ProjectsPage |
| Board controls (filters, sort, drag) | `useBoardControls` hook | Props from ProjectsPage |
| Refresh state | `useBoardRefresh` hook | Props from ProjectsPage |
| Sync status | `useRealTimeSync` hook | Props from ProjectsPage |
| Selected board item | `ProjectsPage` local state (`useState`) | Props to IssueDetailModal |
| Pipeline selector open | `PipelineSelector` local state | Internal only |
| Project selector open | `ProjectSelector` local state | Internal only |
| Rate limit (global) | `RateLimitContext` | Context provider in AppLayout |

**Invariant**: Each piece of state has exactly one owner. No state is duplicated between hooks or components. The `ProjectsPage` orchestrator is the single coordination point between hooks and components.

## Error Handling Strategy

| Error Type | Detection | UI Response | Recovery |
|------------|-----------|-------------|----------|
| Network error | `error` from `useQuery` | Inline error message | Retry button triggers `refetch()` |
| API error (4xx/5xx) | `error` from `useQuery`/`useMutation` | User-friendly message (FR-026 format) | Retry button |
| Rate limit (429) | `isRateLimitApiError(error)` | `<RateLimitBanner>` with reset countdown | Auto-recovery after reset time |
| Mutation error | `onError` callback in `useMutation` | Toast notification with error details | User retries action manually |
| WebSocket disconnect | `syncStatus === 'disconnected'` | Status indicator in `<BoardHeader>` | Auto-reconnect; manual refresh available |

**Format for user-facing error messages** (FR-026):
```
"Could not [action]. [Reason, if known]. [Suggested next step]."
```

Examples:
- "Could not load board data. The server returned an unexpected error. Please try again."
- "Could not assign pipeline. The pipeline configuration was not found. Please refresh and try again."
- "Could not load projects. GitHub API rate limit exceeded. Resets in 12 minutes."
