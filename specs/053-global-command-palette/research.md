# Research: Global Search / Command Palette

**Feature Branch**: `053-global-command-palette`
**Date**: 2026-03-20
**Spec**: [spec.md](./spec.md)

## Research Tasks

### RT-001: Command Palette Implementation Approach (Build vs. Library)

**Context**: The feature requires a command palette overlay with search input, categorized results,
keyboard navigation, and action execution. The project could use a library like `cmdk` or build
a custom component with existing primitives (Radix UI Dialog, custom hooks).

**Decision**: Build a custom command palette component using existing project primitives — React
state management, Radix-style patterns (already used for Popover, Tooltip, HoverCard), Tailwind
CSS styling, and Lucide icons. No new library dependency is needed.

**Rationale**: The project already has all the building blocks: modal/dialog patterns
(`keyboard-shortcut-modal.tsx`, `confirmation-dialog.tsx`), keyboard event handling
(`useGlobalShortcuts`), and data hooks for all entity types. Adding `cmdk` would introduce a new
dependency for a component that is straightforward to build with existing patterns. The custom
approach gives full control over styling (celestial theme), behavior (modal conflict detection),
and integration with existing hooks. Constitution Principle V (Simplicity) favors using existing
tools over adding new ones.

**Alternatives considered**:
- `cmdk` (npm package) — well-designed but adds a dependency for functionality achievable with
  existing primitives. Would need custom styling to match celestial theme. Adds ~15KB.
- `@radix-ui/react-dialog` — could wrap the palette in a dialog primitive, but the project
  already uses a custom modal pattern (focus trap, backdrop click, Escape close) that is simpler.
- `kbar` — heavier than `cmdk`, more opinionated about keyboard shortcut handling, conflicts
  with existing `useGlobalShortcuts`.

---

### RT-002: Search Algorithm — Substring vs. Fuzzy Matching

**Context**: The spec states "simple substring/fuzzy matching" and result ranking is out of scope
for the initial version. Need to decide on the matching strategy for filtering results.

**Decision**: Use case-insensitive substring matching (`item.name.toLowerCase().includes(query)`)
for the initial implementation. This is the simplest approach that meets all acceptance criteria.

**Rationale**: Substring matching is predictable, fast (O(n) per item), and sufficient for the
scale of data (typically <100 total items across all entity types). Users expect "set" to match
"Settings" — substring matching handles this naturally. Fuzzy matching (e.g., Fuse.js, Levenshtein)
adds complexity with marginal benefit at this scale. The spec explicitly marks advanced search as
out of scope.

**Alternatives considered**:
- Fuse.js — fuzzy matching library (~15KB), handles typos and partial matches. Overkill for <100
  items and adds a dependency. Can be added later if user feedback demands it.
- Custom fuzzy matcher (character-by-character scoring) — more complex, harder to debug,
  marginal benefit at this scale.
- `String.prototype.match()` with regex — risk of regex injection from user input, more complex
  than `includes()`.

---

### RT-003: State Management — Where to Hold Palette Open/Close State

**Context**: The command palette needs open/close state that is controlled by both keyboard
shortcuts (Ctrl+K, Escape) and UI interactions (click trigger, backdrop click, result selection).
Multiple components need to read/write this state.

**Decision**: Use a React state hook (`useState`) in `AppLayout` and pass `isOpen` / `setIsOpen`
as props to the `CommandPalette` component. The `useGlobalShortcuts` hook dispatches a custom
event (`solune:open-command-palette`) that `AppLayout` listens for to toggle the state.

**Rationale**: This matches the existing pattern used for the keyboard shortcut modal
(`showShortcutModal` state in `AppLayout`). The palette is rendered once at the app layout level,
so lifting state to `AppLayout` is the natural location. Custom events are already used in the
project (`solune:focus-chat`) for cross-component communication. No new context provider or
global state library is needed.

**Alternatives considered**:
- React Context — adds boilerplate (provider, consumer, context file) for a single boolean.
  Overkill when props suffice for a single component rendered in one place.
- Zustand/Jotai — the project doesn't use external state management libraries. Adding one for
  a single boolean violates Principle V (Simplicity).
- URL-based state (query parameter) — palette is ephemeral UI, not navigation state. Would
  pollute browser history.

---

### RT-004: Focus Management — Saving and Restoring Focus on Palette Close

**Context**: FR-009 requires focus to return to the previously focused element when the palette
closes. This is a common accessibility pattern for modal dialogs.

**Decision**: Capture `document.activeElement` when the palette opens and restore focus to that
element when it closes. Use a `useRef` to store the previously focused element. On close, call
`previousElement.focus()` if the element still exists in the DOM.

**Rationale**: This is the standard WAI-ARIA modal focus management pattern. The existing
`keyboard-shortcut-modal.tsx` already implements focus restore on close (line: stores
`previouslyFocusedElement` in useRef). Replicating this proven pattern ensures consistency.

**Alternatives considered**:
- No focus restore — violates FR-009 and accessibility best practices. Screen reader users
  would lose their place in the page.
- Focus the body element on close — generic but doesn't restore the user's context.
- Use `@radix-ui/react-focus-scope` — adds a Radix dependency for a pattern already implemented
  in the project.

---

### RT-005: Modal Conflict Detection

**Context**: FR-012 requires the command palette to not open when a modal dialog is already
active. The existing `useGlobalShortcuts` already has an `isModalOpen()` function that checks
for `[role="dialog"][aria-modal="true"]` elements.

**Decision**: Reuse the existing `isModalOpen()` function from `useGlobalShortcuts` to suppress
the palette open event when another modal is active. The command palette itself will also use
`role="dialog" aria-modal="true"`, so it will be detected by other components that check for
open modals.

**Rationale**: The `isModalOpen()` utility is already tested and proven in the codebase. It uses
the semantic DOM query approach (`[role="dialog"][aria-modal="true"]`) which works with all
existing dialogs (confirmation dialog, keyboard shortcut modal). No changes needed to the
detection logic — only the Ctrl+K handler needs to check it before opening the palette.

**Alternatives considered**:
- Track modal state in a context provider — requires all modal components to opt in. More
  complex and fragile than DOM-based detection.
- Use a global counter of open modals — requires coordination across unrelated components.
- Disable Ctrl+K via CSS pointer-events — doesn't prevent keyboard shortcuts.

---

### RT-006: Entity Data Access Pattern

**Context**: The command palette needs to search across agents, pipelines, tools, chores, and
apps. Each entity type has its own TanStack Query hook that fetches data from the backend API.
The hooks require a `projectId` parameter.

**Decision**: The `useCommandPalette` hook will accept the current `projectId` and call each
entity hook internally. Since TanStack Query caches responses, no additional API calls are
made when the palette opens — it uses already-cached data from the hooks that are also used by
the entity pages. The palette searches against whatever data is currently cached.

**Rationale**: TanStack Query's cache-first architecture means entity data loaded on any page
(Agents, Tools, Chores, etc.) is immediately available to the command palette without additional
network requests. For entities the user hasn't visited yet, the palette will trigger a fetch
on first open — but these hooks have long stale times (5–15 minutes), so subsequent opens
are instant. This approach requires zero new API endpoints or backend changes.

**Alternatives considered**:
- Dedicated search endpoint — adds backend complexity, latency, and a new API contract.
  The spec explicitly states client-side search.
- Pre-fetch all entities on app load — increases initial load time for data the user may
  never search. TanStack Query's lazy fetching is more efficient.
- Service worker with IndexedDB cache — massive over-engineering for <100 items.

---

### RT-007: Clickable UI Trigger Placement

**Context**: FR-013 requires a clickable UI trigger for opening the command palette (for mobile
and non-keyboard users). Need to decide where to place this trigger.

**Decision**: Add a search icon button to the `TopBar` component, positioned near the existing
theme toggle and notifications area. The button uses the `Search` Lucide icon and includes a
tooltip showing the keyboard shortcut (Ctrl+K / Cmd+K). On click, it dispatches the same
`solune:open-command-palette` custom event.

**Rationale**: The `TopBar` is visible on all authenticated pages and already contains global
action buttons (theme toggle, notifications). Placing the search trigger there follows
established UI patterns (VS Code, GitHub, Slack all place search triggers in the top bar).
The tooltip educates users about the keyboard shortcut, encouraging adoption of the faster
interaction method.

**Alternatives considered**:
- Sidebar search button — the sidebar collapses on mobile and in collapsed mode, reducing
  discoverability. Would need special handling for collapsed vs. expanded states.
- Floating action button (FAB) — not part of the celestial design system. Would feel out of
  place with the existing UI patterns.
- Browser address bar integration — not possible for web applications.

## Summary of Decisions

| # | Topic | Decision | Risk |
|---|-------|----------|------|
| RT-001 | Implementation approach | Custom component with existing primitives | Low — proven patterns in codebase |
| RT-002 | Search algorithm | Case-insensitive substring matching | Low — simple, sufficient at scale |
| RT-003 | State management | useState in AppLayout + custom event | Low — matches existing patterns |
| RT-004 | Focus management | useRef to save/restore activeElement | Low — standard WAI-ARIA pattern |
| RT-005 | Modal conflict detection | Reuse existing isModalOpen() DOM query | Low — already proven |
| RT-006 | Entity data access | TanStack Query cache via existing hooks | Low — zero new API calls |
| RT-007 | UI trigger placement | Search icon button in TopBar | Low — follows established patterns |
