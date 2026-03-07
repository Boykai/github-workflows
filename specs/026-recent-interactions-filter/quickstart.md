# Quickstart: Recent Interactions Filter

**Feature Branch**: `026-recent-interactions-filter`
**Date**: 2026-03-07

## Prerequisites

- Node.js 18+ (check with `node --version`)
- Git (on branch `026-recent-interactions-filter` or development branch)
- Backend running at `localhost:8000` (for API proxy and board data)
- At least one GitHub project board with issues configured

## Setup

```bash
# Switch to feature branch
git checkout 026-recent-interactions-filter

# Install dependencies (no new deps — all existing)
cd frontend
npm install

# Start dev server
npm run dev
```

The app is available at `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

## Verification Steps

### 1. Parent Issue Filtering

After the hook changes are applied:

1. Open the app at `http://localhost:5173/`
2. Select a project from the bottom-left project selector
3. Look at the "Recent Interactions" section in the sidebar
4. Verify that ONLY parent issues appear (no sub-issues, no PRs, no draft issues)
5. Cross-check: items shown should have `content_type: 'issue'` and should NOT appear in any other issue's sub-issues list on the project board

### 2. Status Color Accent

1. With a project selected, observe the Recent Interactions entries
2. Each entry should have a colored left border accent
3. The color should match the item's project board column color:
   - Items in a "Todo" column → gray border
   - Items in an "In Progress" column → blue border
   - Items in a "Done" column → green border
   - etc. (colors come from the actual project board configuration)
4. Move an issue to a different column on the project board
5. After the board data refreshes (automatic polling), the sidebar entry's border color should update

### 3. Deleted Item Removal

1. Note which issues appear in the Recent Interactions sidebar
2. Delete or archive one of those issues from GitHub
3. Wait for the board data to refresh (or manually trigger by navigating away and back to `/projects`)
4. The deleted issue should no longer appear in the Recent Interactions list

### 4. Empty State

1. If no valid parent issues exist in the board data (e.g., project is empty or all items are sub-issues/PRs):
2. The sidebar should show: "No recent parent issues" instead of a blank space

## Files to Modify

| File | Change Summary |
|------|----------------|
| `frontend/src/types/index.ts` | Add `status: string` and `statusColor: StatusColor` to `RecentInteraction` interface |
| `frontend/src/hooks/useRecentParentIssues.ts` | Add content_type filter, sub-issue exclusion, status color capture |
| `frontend/src/layout/Sidebar.tsx` | Add `border-l-2` with status color, update empty state text, import `statusColorToCSS` |

## Running Tests

```bash
cd frontend

# Type checking
npx tsc --noEmit

# Unit tests
npm run test

# Lint
npm run lint
```

## Design Reference

- Status colors use the existing `StatusColor` system from `colorUtils.ts`
- Left border accent style: `border-l-2` with inline `borderLeftColor`
- Colors align with GitHub Projects V2 color scheme (GRAY, BLUE, GREEN, YELLOW, ORANGE, RED, PINK, PURPLE)
- Fallback color: GRAY (for unknown/unavailable status)
- Empty state text: "No recent parent issues" (consistent with sidebar typography)
