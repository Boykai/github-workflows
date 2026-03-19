# Responsive Behavior Contracts: Solune UX Improvements

**Feature Branch**: `051-solune-ux-improvements`
**Date**: 2026-03-19
**Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

## Breakpoint Definition

All responsive behaviors use a single breakpoint:

| Breakpoint | Value | CSS Media Query | Hook Value |
|------------|-------|-----------------|------------|
| Mobile | < 768px | `(max-width: 767px)` | `useMediaQuery` → `true` |
| Desktop | ≥ 768px | `(min-width: 768px)` | `useMediaQuery` → `false` |

## Component Behavior Contracts

### ChatPopup (US-1)

| Viewport | Layout | Width | Height | Resize | Close |
|----------|--------|-------|--------|--------|-------|
| Desktop (≥ 768px) | Floating panel | 300–800px (user resizable) | 350–900px (user resizable) | Drag corners/edges | Close button |
| Mobile (< 768px) | Full-screen overlay | 100vw | 100vh | Disabled | Close button |

**Transition**: When viewport crosses 768px while chat is open, layout switches immediately.
Chat content (messages, input) and state are preserved during transition.

### Sidebar (US-2)

| Viewport | Default State | Expanded Behavior | Collapse Triggers |
|----------|---------------|-------------------|-------------------|
| Desktop (≥ 768px) | User's last preference | Pushes content (inline) | Toggle button only |
| Mobile (< 768px) | Collapsed (icon-only) | Overlay with backdrop (z-40) | Toggle, outside click, nav item click |

**Transition**: When viewport crosses below 768px, sidebar auto-collapses. When crossing above
768px, restores user's last desktop preference.

### IssueDetailModal (US-3)

| Viewport | Sizing | Header | Content |
|----------|--------|--------|---------|
| Desktop (≥ 768px) | Max-width centered dialog | Inline with content | Scrollable within dialog |
| Mobile (< 768px) | Full viewport (100vw × ≥95vh) | Fixed at top | Scrollable body area |

### BoardToolbar (US-4)

| Viewport | Layout | Button Style | Dropdown Behavior |
|----------|--------|-------------|-------------------|
| Desktop (≥ 768px) | Horizontal row | Text + icon | Popover below button |
| Mobile (< 768px) | Compact (icon-only or overflow menu) | Icon-only | Full-width panel or bottom-aligned |

**Active filter indicator**: Badge count or highlighted icon visible in both layouts.

## Optimistic Update Contracts (US-6)

### Board Drag-Drop

| Event | UI Update | Timing | Rollback |
|-------|-----------|--------|----------|
| Drop card on new column | Card appears in target column | Immediate (<100ms) | Card animates back to source column |
| Server confirms | No visible change | On response | N/A |
| Server rejects | Card returns to source | On error response | Error toast: "Failed to move issue" |

### App Start/Stop

| Event | UI Update | Timing | Rollback |
|-------|-----------|--------|----------|
| Click "Start" | Status changes to "Starting" | Immediate | Status reverts to previous state |
| Click "Stop" | Status changes to "Stopping" | Immediate | Status reverts to previous state |
| Server confirms | Status updates to final state | On response | N/A |
| Server rejects | Status reverts | On error response | Error toast with error description |

## Toast Notification Contracts (US-7)

| Operation | Success Toast | Error Toast | Duration |
|-----------|---------------|-------------|----------|
| Create resource | "✓ {Resource} created" | Error message from server | Success: 3–5s auto-dismiss; Error: persist until dismissed |
| Update resource | "✓ {Resource} updated" | Error message from server | Same |
| Delete resource | "✓ {Resource} deleted" | Error message from server | Same |
| Move issue (drag-drop) | "Issue moved" | "Failed to move issue" | Same |
| Start/stop app | "App started"/"App stopped" | Error message from server | Same |

**Stacking**: Toasts stack vertically. Maximum visible follows Sonner defaults. Oldest auto-dismiss
first to prevent screen clutter.

## Skeleton Loader Contracts (US-5)

| Page | Skeleton Layout | Item Count | Variant | Transition |
|------|----------------|------------|---------|------------|
| AgentsPage | List rows (avatar + name + description placeholders) | 6 | shimmer | Fade to content, zero layout shift |
| ToolsPage | List rows (icon + name + description placeholders) | 6 | shimmer | Fade to content, zero layout shift |
| ChoresPage | List rows (icon + name + schedule placeholders) | 4 | shimmer | Fade to content, zero layout shift |
| AppsPage | Card grid (2×2 card placeholders) | 4 | shimmer | Fade to content, zero layout shift |

**Error transition**: If data fetch fails while skeletons are showing, transition to error state
with retry button (not infinite skeleton).

## Undo/Redo Contracts (US-11)

| Action | Keyboard Shortcut | Effect | Stack Behavior |
|--------|-------------------|--------|----------------|
| Undo | Ctrl+Z / Cmd+Z | Revert to previous pipeline state | Pop from undoStack, push current to redoStack |
| Redo | Ctrl+Shift+Z / Cmd+Shift+Z | Reapply undone change | Pop from redoStack, push current to undoStack |
| New action after undo | N/A | Clears redo stack | Standard fork behavior |
| Pipeline load/discard | N/A | Clears both stacks | Fresh start |
| Stack overflow | N/A | Drop oldest undo entry | Max 50 entries |

## Search Filter Contracts (US-9)

| Context | Search Target | Match Fields | Debounce | Empty Results |
|---------|--------------|-------------|----------|---------------|
| Board | Issues | `title`, `description` | 150ms | "No results found" message |
| AgentsPage | Agents | `name`, `description` | 150ms | "No results found" message |
| ToolsPage | Tools | `name`, `description` | 150ms | "No results found" message |
| ChoresPage | Chores | `name`, `description` | 150ms | "No results found" message |

**Matching**: Case-insensitive substring match via `String.toLowerCase().includes()`.
**Clear**: Clearing the search input restores all items immediately (no debounce on clear).
