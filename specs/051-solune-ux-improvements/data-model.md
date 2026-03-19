# Data Model: Solune UX Improvements

**Feature Branch**: `051-solune-ux-improvements`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This feature is a frontend-only UX improvement effort — it does not introduce new backend data
models, database tables, or API endpoints. The entities below represent frontend-only state
structures, component prop interfaces, and conceptual objects managed during execution.

## Entities

### 1. Viewport Breakpoint State

Reactive state representing whether the current viewport is below the mobile threshold.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `isMobile` | boolean | Whether viewport width < 768px | Reactive via `matchMedia` |
| `query` | string | Media query string | `'(max-width: 767px)'` |

**Managed by**: `useMediaQuery` hook (new)
**Consumed by**: ChatPopup, Sidebar (via AppLayout), IssueDetailModal, BoardToolbar
**Relationships**: Drives conditional rendering for all mobile-responsive components.

---

### 2. Chat Layout Mode

Determines the ChatPopup rendering mode based on viewport.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `mode` | enum | Current layout mode | `'floating'` (desktop) or `'fullscreen'` (mobile) |
| `width` | number | Popup width in pixels | Desktop only: MIN_WIDTH(300)–MAX_WIDTH(800) |
| `height` | number | Popup height in pixels | Desktop only: MIN_HEIGHT(350)–MAX_HEIGHT(900) |
| `isOpen` | boolean | Whether chat is visible | Toggle via chat button |

**State transitions**:
- Desktop: `floating` → user can resize within bounds
- Mobile: `fullscreen` → fixed `inset-0`, resize disabled
- Viewport resize across 768px: automatic mode switch, preserving `isOpen` state

---

### 3. Sidebar State (Extended)

Extended sidebar state to support mobile overlay behavior.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `isCollapsed` | boolean | Whether sidebar is in icon-only mode | Existing prop |
| `isMobileOverlay` | boolean | Whether sidebar renders as overlay | `true` when mobile + expanded |
| `autoCollapsed` | boolean | Whether collapse was triggered by viewport | Internal state |

**State transitions**:
- Page load on mobile (< 768px): `isCollapsed = true`, `autoCollapsed = true`
- User expands on mobile: `isCollapsed = false`, `isMobileOverlay = true`
- User taps outside / selects nav item on mobile: `isCollapsed = true`, `isMobileOverlay = false`
- Viewport crosses above 768px: restore user's last desktop preference
- Viewport crosses below 768px: `isCollapsed = true`, `autoCollapsed = true`

---

### 4. Optimistic Update Context

State context passed through TanStack Query's `onMutate` → `onError` flow.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `previousData` | unknown | Snapshot of query data before optimistic change | Serializable query cache data |
| `queryKey` | QueryKey | The query key that was optimistically updated | Must match active query |

**Used in**:
- `useBoardDragDrop.ts` — Board column data snapshot for issue move rollback
- `useApps.ts` — App status snapshot for start/stop rollback

**State transitions**:
- `onMutate`: Capture `previousData` via `queryClient.getQueryData(queryKey)`, apply optimistic change via `queryClient.setQueryData(queryKey, newData)`
- `onError`: Restore via `queryClient.setQueryData(queryKey, context.previousData)`, show error toast
- `onSettled`: Invalidate via `queryClient.invalidateQueries({ queryKey })`

---

### 5. Undo/Redo History Stack

State snapshot stack for pipeline builder undo/redo.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `undoStack` | PipelineState[] | Stack of previous states | Max depth: 50 entries |
| `redoStack` | PipelineState[] | Stack of undone states | Cleared on new action |
| `current` | PipelineState | Current pipeline state | Managed by pipelineReducer |

**State transitions**:
- User action (add/remove/reorder stage, etc.): Push `current` to `undoStack`, clear `redoStack`, apply action
- Undo (Ctrl+Z): Pop from `undoStack` → push `current` to `redoStack` → set popped as `current`
- Redo (Ctrl+Shift+Z): Pop from `redoStack` → push `current` to `undoStack` → set popped as `current`
- Stack overflow (>50 entries): Drop oldest entry from `undoStack`
- Pipeline load/discard/create: Clear both stacks

**Validation rules**:
- Undo disabled when `undoStack` is empty
- Redo disabled when `redoStack` is empty
- New action after undo clears `redoStack` (fork behavior)

---

### 6. Skeleton Layout Configuration

Describes the skeleton placeholder structure for each catalog page.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `type` | enum | Layout pattern | `'card-grid'` (Apps), `'list-rows'` (Agents/Tools/Chores) |
| `itemCount` | number | Number of skeleton items to show | 3–8 depending on page |
| `variant` | enum | Skeleton animation style | `'pulse'` or `'shimmer'` |

**Per-page configurations**:
- AgentsPage: `list-rows`, 6 items, `shimmer`
- ToolsPage: `list-rows`, 6 items, `shimmer`
- ChoresPage: `list-rows`, 4 items, `shimmer`
- AppsPage: `card-grid`, 4 items, `shimmer`

---

### 7. Empty State Props

Props interface for the reusable EmptyState component.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `icon` | LucideIcon | Decorative icon for the empty state | Required |
| `title` | string | Heading text | Required, max ~50 chars |
| `description` | string | Explanatory paragraph | Required, 1–3 sentences |
| `actionLabel` | string | CTA button text | Required, e.g., "Create your first agent" |
| `onAction` | () => void | CTA button click handler | Required |

**Used in**: AgentsPage, ToolsPage, ChoresPage (when project selected but list empty)

---

### 8. Search Filter State

Client-side search state for board and catalog pages.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `searchTerm` | string | Current search input value | Local component state |
| `debouncedTerm` | string | Debounced search term for filtering | 150ms debounce delay |
| `matchCount` | number | Number of items matching the filter | Computed, ≥ 0 |

**Filtering logic**:
- Board: Filter issues where `title.toLowerCase().includes(term)` OR `description?.toLowerCase().includes(term)`
- Catalog: Filter items where `name.toLowerCase().includes(term)` OR `description?.toLowerCase().includes(term)`
- Empty search term shows all items
- No matches shows "No results found" message

---

### 9. Onboarding Tour Step

Existing entity extended with 4 new entries.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | number | Step sequence number | 1–13 (was 1–9) |
| `targetSelector` | string \| null | CSS selector for target element | null for welcome/finish steps |
| `title` | string | Step heading | Required |
| `description` | string | Step explanation | Required |
| `icon` | LucideIcon | Step icon component | Required |
| `placement` | string | Tooltip placement relative to target | `'top'`, `'right'`, `'bottom'`, `'left'` |

**New steps (10–13)**:
- Step 10: Tools page (targetSelector: `'sidebar-tools'`)
- Step 11: Chores page (targetSelector: `'sidebar-chores'`)
- Step 12: Settings page (targetSelector: `'sidebar-settings'`)
- Step 13: Apps page (targetSelector: `'sidebar-apps'`)

**Constant update**: `TOTAL_STEPS` changes from `9` to `13` in `useOnboarding.tsx`.

## Entity Relationship Diagram

```text
┌─────────────────────────┐     drives     ┌──────────────────────┐
│  Viewport Breakpoint    │ ──────────────▶ │  Chat Layout Mode    │
│  State (useMediaQuery)  │                 │  (ChatPopup)         │
│  isMobile: boolean      │     drives     ├──────────────────────┤
│                         │ ──────────────▶ │  Sidebar State       │
│                         │                 │  (AppLayout)         │
│                         │     drives     ├──────────────────────┤
│                         │ ──────────────▶ │  IssueDetailModal    │
│                         │                 │  (full-screen mode)  │
│                         │     drives     ├──────────────────────┤
│                         │ ──────────────▶ │  BoardToolbar        │
└─────────────────────────┘                 │  (compact layout)    │
                                            └──────────────────────┘

┌─────────────────────────┐  snapshot/     ┌──────────────────────┐
│  Optimistic Update      │  rollback      │  TanStack Query      │
│  Context                │ ◀────────────▶ │  Cache               │
│  previousData, queryKey │                │  (board, apps)       │
└─────────────────────────┘                └──────────────────────┘

┌─────────────────────────┐                ┌──────────────────────┐
│  Undo/Redo History      │  wraps         │  Pipeline Reducer    │
│  Stack                  │ ◀────────────▶ │  (useReducer)        │
│  undoStack[], redoStack │                │  state + dispatch    │
└─────────────────────────┘                └──────────────────────┘

┌─────────────────────────┐                ┌──────────────────────┐
│  Search Filter State    │  filters       │  Board/Catalog       │
│  searchTerm, debounced  │ ──────────────▶│  Item Lists          │
└─────────────────────────┘                └──────────────────────┘
```
