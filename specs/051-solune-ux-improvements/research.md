# Research: Solune UX Improvements

**Feature Branch**: `051-solune-ux-improvements`
**Date**: 2026-03-19
**Spec**: [spec.md](./spec.md)

## Research Tasks

### RT-001: Mobile Responsive Breakpoint Strategy

**Context**: The spec defines a single 768px breakpoint for all responsive behaviors (ChatPopup,
Sidebar, IssueDetailModal, BoardToolbar). Need to determine the best approach for detecting
viewport width in React — CSS media queries, JavaScript `matchMedia`, or Tailwind responsive
prefixes.

**Decision**: Use a shared `useMediaQuery` hook wrapping `window.matchMedia('(max-width: 767px)')`.
This provides a reactive boolean `isMobile` that components can use for conditional rendering and
layout decisions. Tailwind responsive prefixes (`md:`, `lg:`) are used for CSS-only responsive
changes (padding, font sizes), while `useMediaQuery` handles structural layout changes that
require different JSX (e.g., bottom-sheet vs floating popup).

**Rationale**: A shared hook avoids duplicating `matchMedia` setup across 4+ components. The
`matchMedia` API is well-supported across all modern browsers, fires synchronously on mount, and
handles resize events efficiently via the `change` event listener. Tailwind's `md:` breakpoint
maps to `min-width: 768px`, which is the inverse of our mobile detection.

**Alternatives considered**:
- Tailwind-only (responsive prefixes for everything) — Insufficient for structural layout changes
  that require different JSX trees (e.g., ChatPopup as bottom-sheet vs floating panel).
- CSS Container Queries — More semantic but limited browser support for `@container` queries,
  and the components need JavaScript-level conditionals for layout switching.
- `resize` event listener — More verbose than `matchMedia`, fires on every pixel change (needs
  debouncing), and doesn't provide the media query matching semantics.

---

### RT-002: ChatPopup Bottom-Sheet Pattern on Mobile

**Context**: ChatPopup currently uses fixed dimensions (MIN_WIDTH=300, DEFAULT_WIDTH=400) with
drag-to-resize. On mobile, this must transform into a full-screen bottom-sheet overlay.

**Decision**: When `isMobile` is true (viewport < 768px), render the ChatPopup with fixed
positioning (`fixed inset-0 z-50`), full viewport width and height, and disable the drag-to-resize
behavior. The close button remains in the header. No swipe-to-dismiss gesture (per spec assumption:
"tap the close button" for dismissal). The transition between desktop and mobile layouts is handled
by the `useMediaQuery` hook — when the viewport crosses 768px, the component re-renders in the
appropriate layout.

**Rationale**: A full-screen overlay is the simplest mobile chat pattern and matches the spec
requirement. The existing ChatPopup already has a close button and all the chat functionality
(ChatInterface component) is layout-independent. Avoiding swipe gestures keeps the implementation
simple (YAGNI) and avoids conflicts with scroll behavior inside the chat.

**Alternatives considered**:
- Bottom-sheet with drag handle (like Google Maps) — More complex, requires touch gesture handling
  library, and conflicts with message scrolling inside the chat.
- Sheet/drawer component from Radix UI — Not currently in the project's Radix dependencies, and
  adding it for one component violates the "no new dependencies" constraint.
- CSS-only responsive layout — Cannot easily switch between floating positioned element and
  full-screen fixed overlay using only CSS.

---

### RT-003: Sidebar Auto-Collapse on Mobile

**Context**: Sidebar accepts `isCollapsed` and `onToggle` props from parent. It transitions
between `w-60` (expanded) and `w-16` (collapsed) with a 300ms CSS transition. On mobile, it
should auto-collapse on load and expand as an overlay (not pushing content).

**Decision**: Use the shared `useMediaQuery` hook in the parent layout component (AppLayout) to
detect mobile viewport. On mobile, force `isCollapsed = true` on initial load and when the
viewport crosses below 768px. When the sidebar is expanded on mobile, render it as a fixed overlay
(`fixed inset-y-0 left-0 z-40`) with a backdrop. Clicking outside the sidebar or selecting a nav
item auto-collapses it. The parent manages the mobile-specific state alongside the existing
`isCollapsed` state.

**Rationale**: Keeping the mobile auto-collapse logic in the parent (AppLayout) avoids adding
internal state to the Sidebar component, which is currently a controlled component. The overlay
approach matches mobile navigation patterns (Material Design, iOS). The existing `onToggle`
callback handles expand/collapse transitions without modification.

**Alternatives considered**:
- Move collapse state inside Sidebar — Breaks the controlled component pattern and requires
  refactoring all Sidebar consumers.
- Use a separate MobileSidebar component — Violates DRY (duplicates navigation items, project
  selector, theme toggle).
- CSS-only hide/show — Cannot implement the overlay + backdrop dismissal pattern with CSS alone.

---

### RT-004: Optimistic Updates with TanStack Query

**Context**: Board drag-drop (`useBoardDragDrop.ts`), app start/stop (`useApps.ts`), and pipeline
saves (`usePipelineBoardMutations.ts`) currently wait for server response before updating UI. The
spec requires instant visual feedback with automatic rollback on error.

**Decision**: Use TanStack Query's `onMutate` callback to snapshot the current query data, apply
the optimistic change to the query cache, and return the snapshot as context. On `onError`, restore
the snapshot from context and show an error toast. On `onSettled`, invalidate the relevant queries
to re-sync with the server. This is the canonical TanStack Query optimistic update pattern.

For drag-drop specifically:
- `onMutate`: Snapshot board columns, move the card to the target column in the cache
- `onError`: Restore the snapshot, show `toast.error('Failed to move issue')`
- `onSettled`: `queryClient.invalidateQueries({ queryKey: boardKeys.detail(...) })`

For app start/stop:
- `onMutate`: Snapshot app status, set to 'starting'/'stopping' in cache
- `onError`: Restore snapshot, show error toast
- `onSettled`: Invalidate app queries

**Rationale**: TanStack Query's optimistic update pattern is well-documented, handles race
conditions (multiple rapid mutations), and integrates cleanly with the existing mutation hooks.
The rollback mechanism is automatic via the context return value.

**Alternatives considered**:
- Local React state for optimistic UI — Duplicates server state, creates sync bugs, and doesn't
  integrate with TanStack Query's cache invalidation.
- Debounced mutations — Still shows delay; doesn't solve the perceived performance problem.
- WebSocket push for instant sync — Overkill for this use case; the server already has REST
  endpoints for these operations.

---

### RT-005: Skeleton Loader Patterns for Catalog Pages

**Context**: The existing `Skeleton` component supports `pulse` and `shimmer` variants. It's
currently used in 4 places. Need to add skeleton layouts to AgentsPage, ToolsPage, ChoresPage,
and AppsPage that match the expected content layout.

**Decision**: Create page-specific skeleton layouts as inline JSX within each page component's
loading branch. Each skeleton layout mirrors the actual content structure (card grid for Apps,
list rows for Agents/Tools/Chores) using the existing `Skeleton` component with appropriate
dimensions. Use the `shimmer` variant for consistency with the celestial design system.

**Rationale**: Inline skeleton layouts (not separate components) keep the code co-located with
the content it represents, making it easy to keep skeletons in sync with layout changes. The
existing `Skeleton` component's API (`className`, `variant`) is sufficient — no modifications
needed.

**Alternatives considered**:
- Auto-generated skeleton from component tree — Complex, fragile, and produces inconsistent
  results. Manual skeleton layouts are more reliable.
- Shared `SkeletonPage` component — Each page has a different layout structure (cards vs rows vs
  panels), so a shared component would need too many configuration props.
- Content-aware skeleton (e.g., react-loading-skeleton) — New dependency; the existing `Skeleton`
  component already provides what's needed.

---

### RT-006: Toast Notification Standardization

**Context**: `AppsPage.tsx` uses manual `successMessage`/`actionError` state with ref-based
timers. Other hooks (`useApps.ts`, `useBoardDragDrop.ts`) already use Sonner `toast.success()`
and `toast.error()`. Need to unify all mutation feedback to Sonner toasts.

**Decision**: Remove the manual `successMessage`/`actionError` state from `AppsPage.tsx` and
replace with Sonner toast calls in the mutation hooks. All mutation hooks (`useApps`, `useAgents`,
`useTools`, `useChores`) should follow the same pattern: `onSuccess → toast.success(message)`,
`onError → toast.error(message, { duration: Infinity })`. This matches the existing pattern in
`useBoardDragDrop.ts`.

**Rationale**: Sonner is already installed and configured (Toaster rendered in AppLayout). The
hook-level toast pattern is already established in the codebase. Moving toast calls to hooks
(not pages) ensures consistency regardless of which page triggers the mutation.

**Alternatives considered**:
- Custom notification context — Unnecessary when Sonner already provides a global notification
  system with stacking, auto-dismiss, and manual dismiss.
- Keep manual state for some pages — Creates inconsistency; the spec explicitly requires
  unification (FR-013).

---

### RT-007: Empty States for Catalog Pages

**Context**: Current catalog pages show minimal "no items" messages when lists are empty. The
spec requires actionable empty states with descriptions and CTAs.

**Decision**: Create a reusable `EmptyState` component in `components/common/` that accepts
`icon`, `title`, `description`, and `actionLabel`/`onAction` props. Each catalog page renders
this component when the list is empty (but a project is selected). The component uses the
celestial design tokens for consistent styling.

**Rationale**: A shared component avoids duplicating empty state markup across 3+ pages. The
prop-based API keeps it flexible for different resource types (agents, tools, chores) while
ensuring visual consistency.

**Alternatives considered**:
- Inline empty states per page — Duplicates layout and styling code.
- Empty state as part of each Panel component — Couples empty state logic to the data display
  component, making it harder to customize CTAs per context.

---

### RT-008: Client-Side Text Search

**Context**: The spec requires text search on the board (issues by title/description) and
catalog pages (agents/tools/chores by name/description). Search is client-side only — data is
already loaded.

**Decision**: Add a search input to `BoardToolbar` and each catalog page. Filter items using
`String.prototype.toLowerCase().includes()` for case-insensitive substring matching. Debounce
the search input by 150ms to avoid re-rendering on every keystroke. The search state is managed
as local component state (not URL params or global state).

**Rationale**: Client-side filtering is the simplest approach and matches the spec decision
("Board search is client-side filtering, data already loaded, not a new API endpoint"). The
`includes()` method is sufficient for substring matching — fuzzy search (e.g., Fuse.js) is not
required by the spec and would add a dependency.

**Alternatives considered**:
- Fuzzy search (Fuse.js) — Adds a dependency for marginal benefit; substring matching is
  sufficient for typical searches.
- URL-based search params — Adds complexity for state synchronization; search is ephemeral
  and doesn't need to survive page navigation.
- Server-side search — The spec explicitly scopes search to client-side only.

---

### RT-009: Pipeline Undo/Redo Architecture

**Context**: `usePipelineConfig` uses `useReducer` with `pipelineReducer` for local state
management. The spec requires undo/redo via Ctrl+Z / Ctrl+Shift+Z with a 50-entry stack.

**Decision**: Implement an undo/redo wrapper around the existing `pipelineReducer`. Before each
state-changing dispatch, push the current state snapshot onto an undo stack. Redo is implemented
as a separate stack that captures undone states. When a new action is dispatched after an undo,
the redo stack is cleared (standard fork behavior). The undo stack is capped at 50 entries
(oldest entries are dropped). Clear both stacks when a pipeline is loaded from server, discarded,
or created fresh.

Use a `useUndoReducer` wrapper hook that wraps the existing `useReducer` call in
`usePipelineConfig`. The keyboard shortcuts (Ctrl+Z, Ctrl+Shift+Z) are registered in the
pipeline builder component using `useEffect` with a `keydown` event listener.

**Rationale**: Wrapping the existing reducer preserves all current functionality without
modifying the reducer logic. State snapshots via `computeSnapshot()` (already used in the
codebase) provide clean serializable states for the undo stack. The 50-entry cap prevents
memory issues for long editing sessions.

**Alternatives considered**:
- Command pattern (individual reversible operations) — More complex to implement, requires
  defining inverse operations for each mutation type.
- Immutable state library (Immer) — Already available via TanStack Query but not used in the
  reducer; introducing it for undo/redo adds unnecessary complexity.
- Browser history API — Intended for URL navigation, not application state management.

---

### RT-010: Extended Onboarding Tour

**Context**: `SpotlightTour.tsx` defines 9 `TOUR_STEPS` with `targetSelector`, `title`,
`description`, `icon`, and `placement`. `useOnboarding.tsx` has `TOTAL_STEPS = 9` and manages
state via React Context + localStorage.

**Decision**: Add 4 new steps to the `TOUR_STEPS` array in `SpotlightTour.tsx` covering Tools,
Chores, Settings, and Apps pages. Each step targets the corresponding sidebar navigation item
via its CSS selector. Update `TOTAL_STEPS` from 9 to 13 in `useOnboarding.tsx`. The new steps
follow the exact same format as existing steps (icon, title, description, placement).

Add a sidebar auto-expand trigger for the new steps (same pattern as existing steps that need
the sidebar visible). Ensure the tour marks completion correctly with the updated total.

**Rationale**: Minimal change — extending an existing array and updating a constant. The
`SpotlightTour` component already handles arbitrary step counts, target element detection, and
keyboard navigation. No architectural changes needed.

**Alternatives considered**:
- Separate tour for new pages — Fragments the onboarding experience; users would need to
  trigger multiple tours.
- Dynamic step loading — Over-engineered for adding 4 static steps.
- Video/walkthrough instead of interactive tour — Different UX pattern; the spec explicitly
  extends the existing spotlight tour.
