# Render Contract: Frontend Component Rendering Rules

**Feature**: 039-performance-review
**Date**: 2026-03-13
**Version**: 1.0

## Purpose

Defines the rendering behavior expectations for board-related components, ensuring that optimizations are consistent, measurable, and resistant to regression.

## Component Rendering Rules

### BoardColumn (memoized)

| Rule | Description |
|------|-------------|
| Memo boundary | `React.memo()` wraps the entire component |
| Rerender trigger | Only when column props change (status, items array reference, callbacks) |
| Item change isolation | A change to one item's data MUST NOT cause sibling items to rerender |
| Callback stability | All callback props MUST be stable references (wrapped in `useCallback` by parent) |

### IssueCard (memoized)

| Rule | Description |
|------|-------------|
| Memo boundary | `React.memo()` wraps the entire component |
| Rerender trigger | Only when the card's own data changes (item prop reference) |
| Sub-issue expansion | Expansion state is local; toggling sub-issues does NOT trigger parent rerender |
| Avatar validation | URL validation (HTTPS-only, GitHub-whitelist) runs once per render, not per interaction |

### SubIssueRow (memoized)

| Rule | Description |
|------|-------------|
| Memo boundary | `React.memo()` wraps the entire component |
| Rerender trigger | Only when the sub-issue data changes |
| Parent isolation | SubIssueRow changes do NOT propagate to IssueCard or BoardColumn |

### ProjectsPage (orchestrator)

| Rule | Description |
|------|-------------|
| Derived data | All derived state (sorting, grouping, aggregation) MUST be wrapped in `useMemo` with correct dependency arrays |
| Computation frequency | Derived data recomputes only when source data changes, not on every render cycle |
| Callback stability | All callbacks passed to memoized children MUST use `useCallback` |
| Rate limit aggregation | Priority-ordered fallback chain MUST be memoized |

## Event Listener Rules

### Drag Interactions (@dnd-kit)

| Rule | Description |
|------|-------------|
| Scope | Drag listeners MUST be registered only during active drag operations |
| Throttle | Position updates MUST use `requestAnimationFrame` gating |
| Cleanup | All listeners MUST be removed on drag end and component unmount |

### Resize Handlers (ChatPopup)

| Rule | Description |
|------|-------------|
| Scope | `mousemove`/`mouseup` listeners registered ONLY during active resize |
| Throttle | Position updates use `requestAnimationFrame` |
| Cleanup | Listeners removed on `mouseup` and component unmount |

### Popover Positioning (AddAgentPopover)

| Rule | Description |
|------|-------------|
| Scope | Scroll/resize listeners registered ONLY when popover is open |
| Passive | Scroll listeners MUST use `{ passive: true, capture: true }` |
| Throttle | Repositioning uses `requestAnimationFrame` |
| Cleanup | Listeners removed on close, Escape key, and component unmount |

### Window Resize

| Rule | Description |
|------|-------------|
| Throttle | Any window resize handler MUST be throttled (RAF or debounce) |
| Component scope | Handlers MUST be cleaned up on unmount |

## Rerender Budget

Target rerender counts for common interactions on a board with 20+ tasks:

| Interaction | Maximum Rerenders |
|-------------|-------------------|
| Single task status change (WebSocket) | 1 card + 2 columns (source + destination) |
| Drag card between columns | Dragged card + 2 columns |
| Open task detail panel | Detail panel only; board does not rerender |
| Single task data update | 1 card only |
| Manual refresh (full reload) | All columns + all cards (acceptable) |
| Auto-refresh (background) | All columns + all cards if data changed; zero if unchanged |
| Popover open/close | Popover only; board does not rerender |

## Non-Goals

- This contract does NOT define pixel-level rendering behavior.
- This contract does NOT define animation frame budgets (e.g., 16ms per frame).
- This contract does NOT mandate virtualization for large boards (deferred to second pass).
- This contract does NOT define server-side rendering behavior.
