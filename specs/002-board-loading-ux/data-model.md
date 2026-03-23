# Data Model: Board Loading UX — Skeleton, Stale-While-Revalidate, Refetch Indicator

**Feature**: 002-board-loading-ux
**Date**: 2026-03-23
**Status**: Complete

## Overview

This feature is entirely frontend and does not introduce new data entities, database tables, or API endpoints. The data model describes the **query state shape** and **component props** that drive the board loading UX.

## Entities

### 1. Board Query State (extended from `useProjectBoard`)

The existing `useProjectBoard` hook returns a state object. This feature extends it with one new field.

| Field | Type | Source | New? | Description |
|-------|------|--------|------|-------------|
| `projects` | `BoardProject[]` | projects query | No | List of available projects |
| `projectsLoading` | `boolean` | projects query | No | Projects list loading state |
| `projectsError` | `Error \| null` | projects query | No | Projects list error |
| `projectsRateLimitInfo` | `RateLimitInfo \| null` | projects query | No | Rate limit metadata |
| `selectedProjectId` | `string \| null` | local state | No | Currently selected project |
| `boardData` | `BoardDataResponse \| null` | board query | No | Board columns and items |
| `boardLoading` | `boolean` | board query (`isLoading`) | No | True on initial load only |
| `isFetching` | `boolean` | board query | No | True during any fetch (initial or background) |
| `boardError` | `Error \| null` | board query | No | Board data fetch error |
| `lastUpdated` | `Date \| null` | local state | No | Timestamp of last successful fetch |
| `selectProject` | `(id: string) => void` | local state | No | Project selection handler |
| `pollingState` | `AdaptivePollingState` | adaptive polling hook | No | Current polling state |
| **`isPlaceholderData`** | **`boolean`** | **board query** | **Yes** | **True when displaying cached data from a different query key (e.g., previous project)** |

### 2. Board Rendering State (derived)

The rendering state is derived from query state flags — no new stored state is introduced.

| State | Derived From | Description |
|-------|-------------|-------------|
| Initial Load | `boardLoading && !boardData` | First load, no cache — show skeleton |
| Fresh | `boardData && !isFetching && !isPlaceholderData` | Fresh data displayed — full opacity |
| Stale/Refreshing | `boardData && (isFetching \|\| isPlaceholderData)` | Background refresh or stale placeholder — dimmed with indicator |
| Error (initial) | `boardError && !boardData` | First load failed — show error state |
| Error (background) | `boardError && boardData` | Background refresh failed — toast, keep board |

### 3. BoardSkeleton Props (new component)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `columnCount` | `number` | `5` | Number of skeleton columns to render |

**Note**: The component has minimal props by design — it mirrors the board's default 5-column layout. The column count is not configurable from outside in the initial implementation (per YAGNI), but is parameterized internally for testability.

## Relationships

```text
ProjectsPage.tsx
  ├── uses useProjectBoard() hook
  │     ├── returns boardLoading, boardData, isFetching, isPlaceholderData, boardError
  │     └── query config: placeholderData: keepPreviousData
  │
  ├── renders BoardSkeleton (when: initial load)
  │     └── renders 5x BoardColumnSkeleton
  │           └── renders 3x IssueCardSkeleton (each)
  │
  ├── renders ProjectBoard (when: data available)
  │     └── columns from boardData.columns
  │
  └── renders "Updating…" indicator (when: stale/refreshing)
        └── opacity-60 overlay on board container
```

## Validation Rules

- `columnCount` in `BoardSkeleton` must be a positive integer (default 5)
- `isPlaceholderData` is read-only — derived from TanStack Query internal state
- Background error toast must only fire when `boardData` is already present (to distinguish from initial load errors)

## State Transitions

```text
                    ┌─────────────┐
                    │   No Data   │ (initial state)
                    └──────┬──────┘
                           │ navigate to project
                           ▼
                    ┌─────────────┐
                    │   Skeleton  │ (boardLoading && !boardData)
                    └──────┬──────┘
                           │ data arrives
                           ▼
                    ┌─────────────┐
              ┌────▶│    Fresh    │◀───── data arrives (from refetch)
              │     └──────┬──────┘
              │            │ staleTime expires / project switch
              │            ▼
              │     ┌─────────────┐
              │     │  Refreshing │ (isFetching || isPlaceholderData)
              │     └──────┬──────┘
              │            │
              │     ┌──────┴──────┐
              │     ▼             ▼
              │  success       failure
              │     │             │
              └─────┘      ┌──────┴──────┐
                           │ Toast Error │ (board stays visible)
                           └─────────────┘
```
