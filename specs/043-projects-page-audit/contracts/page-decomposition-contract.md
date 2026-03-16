# Contract: Page Decomposition

**Feature**: `043-projects-page-audit` | **Date**: 2026-03-16 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the decomposition of `ProjectsPage.tsx` (630 lines) into a ≤250-line orchestrator and four focused sub-components. All extracted components are placed in `solune/frontend/src/components/board/` alongside existing board components.

## Component Contracts

### `ProjectsPage.tsx` (Orchestrator)

**Current**: 630 lines
**Target**: ≤250 lines

**Responsibilities**:
- Compose sub-components into the page layout
- Initialize hooks (`useProjectBoard`, `useProjects`, `useBoardControls`, `useBoardRefresh`, `useRealTimeSync`)
- Pass hook return values as props to sub-components
- Manage the `selectedItem` state for the issue detail modal
- Render conditional layout: loading → error → empty → board

**Must NOT contain**:
- Inline business logic (sorting, filtering, computation)
- Direct API calls (`useQuery`/`useMutation` in the page file) — delegate to hooks or extracted components
- More than 2 levels of prop passing to any child
- Inline `style={}` attributes (except documented dynamic color exceptions)

**Layout Structure**:
```tsx
export function ProjectsPage() {
  // 1. Hook initialization (~30 lines)
  // 2. Derived state / memoized values (~10 lines)
  // 3. Event handlers (~20 lines)
  // 4. Render:
  return (
    <div className="flex h-full flex-col">
      {/* Rate limit banner (conditional) */}
      <RateLimitBanner rateLimitInfo={rateLimitInfo} isLow={isRateLimitLow} />

      {/* Page header with project selector */}
      <CelestialCatalogHero title="Projects" icon={...}>
        <ProjectSelector ... />
      </CelestialCatalogHero>

      {/* Conditional content: loading / error / empty / board */}
      {isLoading ? (
        <CelestialLoader size="md" />
      ) : error ? (
        <ErrorState error={error} onRetry={retry} />
      ) : !selectedProject ? (
        <ProjectSelectionEmptyState />
      ) : (
        <>
          <BoardHeader ... />
          <BoardToolbar ... />
          <PipelineSelector ... />
          <ProjectBoard ... />
        </>
      )}

      {/* Issue detail modal (conditional) */}
      <IssueDetailModal ... />
    </div>
  );
}
```

---

### `ProjectSelector.tsx`

**Target**: ~120 lines
**Location**: `solune/frontend/src/components/board/ProjectSelector.tsx`

**Props Interface**:
```tsx
interface ProjectSelectorProps {
  /** List of available projects */
  projects: BoardProject[];
  /** Currently selected project (null if none) */
  selectedProject: BoardProject | null;
  /** Callback when user selects a project */
  onSelect: (projectId: string) => void;
  /** Whether the project list is loading */
  isLoading: boolean;
}
```

**Internal State**:
- `searchQuery: string` — for filtering the project list
- `isOpen: boolean` — dropdown open/closed state

**Behavior Contract**:

| Behavior | Specification |
|----------|--------------|
| Trigger | Click on the selector button |
| Keyboard | Enter/Space opens dropdown; Escape closes; Arrow keys navigate; Enter selects |
| Search | Filters projects by name (case-insensitive) as user types |
| Selection | Calls `onSelect(projectId)` and closes dropdown |
| Loading | Shows "Loading projects..." when `isLoading` is true |
| Empty list | Shows "No projects found" when filtered list is empty |
| ARIA | `role="combobox"`, `aria-expanded`, `aria-haspopup="listbox"` on trigger; `role="listbox"` on list; `role="option"` + `aria-selected` on items |
| Focus | Dropdown traps focus; close returns focus to trigger |

---

### `PipelineSelector.tsx`

**Target**: ~150 lines
**Location**: `solune/frontend/src/components/board/PipelineSelector.tsx`

**Props Interface**:
```tsx
interface PipelineSelectorProps {
  /** Active project ID for pipeline queries */
  projectId: string;
  /** Board data containing column information */
  boardData: BoardDataResponse | null;
  /** Available agents for the agent assignment grid */
  availableAgents: Agent[];
}
```

**Internal State/Queries**:
- `useQuery` for pipeline list (query key follows `pipelinesApi` convention)
- `useMutation` for pipeline assignment with `onSuccess` invalidation and toast feedback
- `isOpen: boolean` — selector dropdown state

**Behavior Contract**:

| Behavior | Specification |
|----------|--------------|
| Pipeline list | Fetches pipelines for the project; shows loading state while fetching |
| Selection | Assigning a pipeline triggers a mutation with success/error feedback |
| Grid display | Shows pipeline columns with status color dots and agent assignment indicators |
| Destructive action | Changing pipeline assignment shows `<ConfirmationDialog>` if overriding existing |
| Error handling | Mutation errors display user-friendly toast with format "Could not assign pipeline. [Reason]." |
| ARIA | Dropdown has `aria-label="Select pipeline"`, options have `role="option"` |

---

### `BoardHeader.tsx`

**Target**: ~80 lines
**Location**: `solune/frontend/src/components/board/BoardHeader.tsx`

**Props Interface**:
```tsx
interface BoardHeaderProps {
  /** Name of the selected project */
  projectName: string;
  /** Real-time sync connection status */
  syncStatus: 'connected' | 'disconnected' | 'syncing';
  /** When the board data was last updated */
  lastUpdated: Date | null;
  /** When the last real-time sync update was received */
  syncLastUpdate: Date | null;
  /** Callback to trigger a manual board refresh */
  onRefresh: () => void;
  /** Whether a refresh is currently in progress */
  isRefreshing: boolean;
}
```

**Behavior Contract**:

| Behavior | Specification |
|----------|--------------|
| Display | Shows project name, sync status badge, refresh button, last-updated time |
| Sync status | Visual indicator: green dot for connected, yellow for syncing, red for disconnected |
| Status not color-only | Status badge includes text label alongside color dot (FR-020) |
| Refresh | Delegates to `onRefresh` callback; shows spinner while `isRefreshing` |
| Timestamp | Uses `formatTimeAgo()` for relative time display |
| ARIA | Sync status has `aria-label` describing connection state |

---

### `RateLimitBanner.tsx`

**Target**: ~50 lines
**Location**: `solune/frontend/src/components/board/RateLimitBanner.tsx`

**Props Interface**:
```tsx
interface RateLimitBannerProps {
  /** Current rate limit information (null if not available) */
  rateLimitInfo: RateLimitInfo | null;
  /** Whether the rate limit is critically low */
  isLow: boolean;
}
```

**Behavior Contract**:

| Behavior | Specification |
|----------|--------------|
| Visibility | Renders only when `isLow` is true |
| Content | Warning icon + message + reset countdown |
| Reset time | Uses `formatTimeUntil()` to show "Resets in X minutes" |
| Role | `role="alert"` for screen reader announcement |
| Styling | Warning color scheme (`bg-warning/10 text-warning-foreground`), uses Tailwind only |
| No interaction | Pure display — no buttons or actions needed |

## Prop Flow Diagram

```text
ProjectsPage (orchestrator)
  ├── props to ProjectSelector: projects, selectedProject, onSelect, isLoading
  │   └── depth: 1 level ✅ (max 2 allowed)
  ├── props to BoardHeader: projectName, syncStatus, lastUpdated, syncLastUpdate, onRefresh, isRefreshing
  │   └── depth: 1 level ✅
  ├── props to RateLimitBanner: rateLimitInfo, isLow
  │   └── depth: 1 level ✅
  ├── props to PipelineSelector: projectId, boardData, availableAgents
  │   └── depth: 1 level ✅
  ├── props to BoardToolbar: (existing — verify ≤2 levels)
  │   └── depth: 1 level ✅
  └── props to ProjectBoard: (existing — verify ≤2 levels)
      └── depth: 1 level ✅ (ProjectBoard passes to BoardColumn → depth 2)
```

**Maximum prop depth**: 2 levels (ProjectsPage → ProjectBoard → BoardColumn). ✅ Meets FR-003.
