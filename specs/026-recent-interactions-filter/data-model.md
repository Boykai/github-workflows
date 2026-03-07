# Data Model: Recent Interactions — Filter Deleted Items & Display Only Parent Issues with Project Board Status Colors

**Feature Branch**: `026-recent-interactions-filter`
**Date**: 2026-03-07

> This feature is frontend-only. No new backend entities are created. This document describes the **frontend data model** changes — type modifications, hook contract updates, and state transitions.

## Existing Entities (Preserved — No Changes)

These types from `frontend/src/types/index.ts` are used as-is:

| Entity | Key Fields | Used By |
|---|---|---|
| `BoardItem` | item_id, content_type, title, number, status, status_option_id, sub_issues | useRecentParentIssues (filtering) |
| `BoardColumn` | status (BoardStatusOption), items (BoardItem[]) | useRecentParentIssues (color mapping) |
| `BoardStatusOption` | option_id, name, color (StatusColor) | Status color source |
| `BoardDataResponse` | project, columns (BoardColumn[]) | Input to useRecentParentIssues |
| `SubIssue` | id, number, title, state | Cross-reference for parent detection |
| `StatusColor` | GRAY \| BLUE \| GREEN \| YELLOW \| ORANGE \| RED \| PINK \| PURPLE | Color enum values |
| `ContentType` | 'issue' \| 'draft_issue' \| 'pull_request' | Content type filter |

## Modified Types

### RecentInteraction (Extended)

**Location**: `frontend/src/types/index.ts`

Current definition:
```typescript
export interface RecentInteraction {
  item_id: string;
  title: string;
  number?: number;
  repository?: {
    owner: string;
    name: string;
  };
  updatedAt: string;
}
```

Updated definition — adds `status` and `statusColor` fields:
```typescript
export interface RecentInteraction {
  item_id: string;
  title: string;
  number?: number;
  repository?: {
    owner: string;
    name: string;
  };
  updatedAt: string;
  status: string;              // NEW: Project board status name (e.g., "In Progress", "Done")
  statusColor: StatusColor;    // NEW: StatusColor enum value from the board column
}
```

**Field descriptions**:
- `status`: The display name of the project board status column the issue belongs to (e.g., "Todo", "In Progress", "Done"). Sourced from `BoardColumn.status.name`.
- `statusColor`: The `StatusColor` enum value from the board column's `BoardStatusOption.color`. Used by `statusColorToCSS()` and `statusColorToBg()` in `colorUtils.ts` for rendering.

**Migration impact**: The `Sidebar` component reads `recentInteractions` prop — it will now have access to `status` and `statusColor` on each entry. The `AppLayout` component passes `recentInteractions` from the hook — no prop changes needed since the array type is inferred.

## Hook Contract Changes

### useRecentParentIssues (Modified)

**Location**: `frontend/src/hooks/useRecentParentIssues.ts`

Current signature:
```typescript
function useRecentParentIssues(boardData: BoardDataResponse | null): RecentInteraction[]
```

Updated signature (unchanged — only internal logic changes):
```typescript
function useRecentParentIssues(boardData: BoardDataResponse | null): RecentInteraction[]
```

**Behavioral changes**:

1. **Content type filter**: Only include items where `item.content_type === 'issue'`. This excludes `draft_issue` and `pull_request` content types (FR-004).

2. **Sub-issue exclusion**: Build a `Set<number>` of all sub-issue numbers from all board items' `sub_issues` arrays. Exclude any item whose `number` is in this set (FR-005).

3. **Status color capture**: When iterating columns, capture `column.status.name` and `column.status.color` for each item, populating the new `status` and `statusColor` fields on `RecentInteraction` (FR-006, FR-007).

4. **Implicit deletion filtering**: Items not in `BoardDataResponse` are already excluded since the hook derives its list from board data (FR-001, FR-002, FR-003).

5. **Fallback color**: If a column's status color is undefined (unlikely but defensive), default to `'GRAY'` (FR-010).

**Algorithm**:
```
Input: BoardDataResponse (columns with items)
Output: RecentInteraction[] (max 8, parent issues only, with status colors)

1. If boardData is null → return []
2. Collect all sub-issue numbers into subIssueNumbers: Set<number>
   For each column in boardData.columns:
     For each item in column.items:
       For each si in item.sub_issues:
         subIssueNumbers.add(si.number)
3. Collect parent issues with status colors:
   For each column in boardData.columns:
     For each item in column.items:
       Skip if item.content_type !== 'issue'
       Skip if item.number is in subIssueNumbers
       Skip if already seen (dedup by item_id)
       Add to result with:
         status = column.status.name
         statusColor = column.status.color ?? 'GRAY'
       Stop if result.length >= MAX_RECENT (8)
4. Return result
```

## Component Props (No Structural Changes)

### Sidebar

The `SidebarProps` interface is unchanged:
```typescript
interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  selectedProject?: { project_id: string; name: string; owner_login: string };
  recentInteractions: RecentInteraction[];  // Now includes status + statusColor fields
  projects: Project[];
  projectsLoading: boolean;
  onSelectProject: (projectId: string) => void;
}
```

The component's rendering of recent interactions changes to include a status color accent. See `contracts/components.md` for the updated rendering contract.

## State Transitions

### Recent Interactions Panel States

```
┌─────────────┐
│   Loading    │ ← boardData is null (initial load)
│  (no panel)  │
└──────┬───────┘
       │ boardData received
       ▼
┌─────────────────┐    ┌────────────────────┐
│  Has Parent      │    │   Empty State       │
│  Issues          │    │   "No recent parent │
│  (colored list)  │    │    issues"          │
└─────────┬───────┘    └────────────────────┘
          │                      ▲
          │ All items deleted/   │
          │ filtered out         │
          └──────────────────────┘
          │
          │ Board data refreshes
          │ (polling / manual)
          ▼
┌─────────────────┐
│  Updated List    │ ← Colors/items update automatically
│  (re-rendered)   │
└─────────────────┘
```

### Status Color Update Flow

```
BoardDataResponse refreshed (polling via useBoardRefresh)
  → useRecentParentIssues recomputes (useMemo dependency: [boardData])
    → New RecentInteraction[] with updated statusColor values
      → Sidebar re-renders with new border colors
        → User sees updated status colors (within one render cycle, FR-008)
```

## Validation Rules

| Rule | Source | Enforcement |
|------|--------|-------------|
| Only `content_type === 'issue'` items pass | FR-004 | `useRecentParentIssues` filter |
| Items in any `sub_issues` array are excluded | FR-005 | `useRecentParentIssues` cross-reference |
| Max 8 items displayed | Existing behavior | `MAX_RECENT` constant |
| Deduplication by `item_id` | Existing behavior | `Set<string>` check |
| Fallback to GRAY for unknown status color | FR-010 | Nullish coalescing in hook |
| Empty state when 0 valid items | FR-009 | Conditional render in Sidebar |
