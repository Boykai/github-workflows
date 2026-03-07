# Component Interface Contracts: Recent Interactions Filter

**Feature Branch**: `026-recent-interactions-filter`
**Date**: 2026-03-07

> This feature modifies existing components only. No new components are created.
> No backend API changes. All data comes from existing `BoardDataResponse`.

## Modified Components

### useRecentParentIssues (Hook)

**Location**: `frontend/src/hooks/useRecentParentIssues.ts`

```typescript
/**
 * Derives recent parent issues from board data with status colors.
 * Filters to content_type 'issue' only, excludes sub-issues,
 * and captures project board status color per item.
 *
 * @param boardData - The current board data response (null during loading)
 * @returns Up to 8 RecentInteraction items, parent issues only, with status colors
 */
function useRecentParentIssues(boardData: BoardDataResponse | null): RecentInteraction[]
```

**Input contract**: Accepts `BoardDataResponse | null`. When null, returns empty array.

**Output contract**: Returns `RecentInteraction[]` where:
- Every item has `content_type === 'issue'` (excludes draft_issue, pull_request)
- No item's `number` appears in any board item's `sub_issues[*].number`
- Each item has `status` (string) and `statusColor` (StatusColor) populated
- Maximum 8 items (existing `MAX_RECENT` constant)
- Deduplicated by `item_id`
- Items with unknown status color default to `'GRAY'`

**Dependency**: `useMemo` with `[boardData]` dependency — recomputes only when board data changes.

### Sidebar (Component — Recent Interactions Section)

**Location**: `frontend/src/layout/Sidebar.tsx`

```typescript
interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
  selectedProject?: { project_id: string; name: string; owner_login: string };
  recentInteractions: RecentInteraction[];  // Now includes status + statusColor
  projects: Project[];
  projectsLoading: boolean;
  onSelectProject: (projectId: string) => void;
}
```

**Rendering contract for Recent Interactions section**:

Each recent interaction entry renders with:
1. A left border accent (`border-l-2`) colored by `statusColorToCSS(item.statusColor)`
2. Issue number prefix (`#{item.number}`) if available
3. Truncated title text
4. Status name in `title` attribute for hover tooltip (e.g., "Issue Title — In Progress")
5. Click navigates to `/projects` (existing behavior preserved)

**Empty state**: When `recentInteractions.length === 0`, renders:
```tsx
<p className="px-3 text-xs text-muted-foreground/60">No recent parent issues</p>
```

**Import additions**:
```typescript
import { statusColorToCSS } from '@/components/board/colorUtils';
import type { StatusColor } from '@/types';  // Only if needed for explicit typing
```

### AppLayout (No Interface Changes)

**Location**: `frontend/src/layout/AppLayout.tsx`

No prop or hook call changes needed. The `useRecentParentIssues` hook is already called with `boardData` and the result is passed to `Sidebar` as `recentInteractions`. The updated `RecentInteraction[]` type with status/statusColor fields flows through automatically.

```typescript
// Existing code (unchanged):
const { boardData } = useProjectBoard({ selectedProjectId: selectedProject?.project_id ?? null });
const recentInteractions = useRecentParentIssues(boardData);
// ... passed to Sidebar as recentInteractions={recentInteractions}
```

## Existing Utilities (Reused — No Changes)

### colorUtils.ts

**Location**: `frontend/src/components/board/colorUtils.ts`

```typescript
// Used by Sidebar to convert StatusColor to CSS hex for border-left color:
function statusColorToCSS(color: StatusColor): string
// Returns hex color string, defaults to GRAY if unknown

// Optionally used for background accent:
function statusColorToBg(color: StatusColor): string
// Returns rgba color string with 18% opacity
```

## Backend API Contract (Unchanged)

No backend changes. The existing endpoint provides all required data:

| Endpoint | Method | Response |
|----------|--------|----------|
| `GET /api/v1/board/projects/{projectId}` | GET | `BoardDataResponse` with `columns[*].status.color` and `columns[*].items[*].content_type`, `columns[*].items[*].sub_issues` |

The frontend already fetches this data via `useProjectBoard` hook with automatic polling via `useBoardRefresh`.
