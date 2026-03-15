# Research: Audit & Polish the Agents Page for Quality and Consistency

**Feature Branch**: `035-audit-agents-page`
**Date**: 2026-03-11

## Research Tasks

### R1: Celestial Design System Token Compliance

**Decision**: All Agents page components must exclusively use CSS custom properties defined in `frontend/src/index.css` via the Tailwind v4 `@theme` block and custom utility classes. No hardcoded hex/rgb/hsl values should appear in component code.

**Rationale**: The Celestial design system defines a comprehensive token set covering colors (`--background`, `--foreground`, `--primary`, `--muted-foreground`, `--glow`, `--gold`, `--night`, `--star`, `--star-soft`, etc.), spacing (Tailwind's default scale), typography (`font-display`, `font-sans`), shadows, radii, and motion. Both light and dark themes are supported via `@media (prefers-color-scheme: dark)` with HSL-based token overrides. Using these tokens ensures visual consistency across pages and automatic theme switching support.

**Alternatives Considered**:

- Creating a separate design token JSON file — Rejected because Tailwind v4's native `@theme` block already serves this purpose and is the established convention
- Using CSS-in-JS for theming — Rejected because the project uses Tailwind CSS exclusively with utility classes and the `cn()` helper

**Key Tokens to Audit Against**:

- Colors: `primary`, `secondary`, `muted`, `accent`, `destructive`, `background`, `foreground`, `border`, `card`, `panel`, `popover`, `glow`, `gold`, `night`, `star`, `star-soft`
- Sync colors: `--sync-connected`, `--sync-polling`, `--sync-connecting`, `--sync-disconnected`
- Custom CSS classes: `.celestial-panel`, `.celestial-shell`, `.celestial-fade-in`, `.celestial-focus`, `.celestial-orbit`, `.celestial-sigil`, `.celestial-pulse-glow`, `.moonwell`, `.solar-chip`, `.solar-chip-*`, `.solar-action`, `.solar-action-danger`, `.ritual-stage`, `.constellation-grid`

**Hardcoded Values Found in Agents Page Components** (to be replaced during audit):

| Component | Line(s) | Hardcoded Value | Replacement |
|-----------|---------|-----------------|-------------|
| AgentsPanel.tsx | Badge styling | `border-emerald-300/40`, `bg-emerald-50/80` | Design token equivalent (e.g., `solar-chip-success`) |
| AgentCard.tsx | Success message | `text-green-700 dark:text-green-400` | Design token or `text-emerald-*` via design system |
| AddAgentPopover.tsx | Source badges | `bg-blue-100 dark:bg-blue-900/30`, `bg-green-100 dark:bg-green-900/30` | Design token badges |
| AgentTile.tsx | SVG circles | Inline `hsl(var(--gold))`, `hsl(var(--glow))` with magic opacity | CSS custom properties via Tailwind |
| AgentDragOverlay.tsx | Width constraints | `min-w-[280px] max-w-[340px]` | Consistent with design scale |
| Various | Z-index values | `z-[120]`, `z-[140]`, `z-[9999]`, `z-50` | Standardized z-layer system |

---

### R2: Accessibility Best Practices for Agent Management Interfaces

**Decision**: Follow WAI-ARIA Authoring Practices for composite widgets, ensuring keyboard navigability, screen reader announcements, and proper focus management. The Agents page has partial ARIA support that must be completed to meet WCAG AA.

**Rationale**: WCAG AA requires that all interactive content be operable via keyboard (2.1.1), has visible focus indicators (2.4.7), has appropriate names and roles (4.1.2), and meets contrast ratios (1.4.3 normal text 4.5:1, 1.4.11 UI components 3:1). The project defines a `.celestial-focus` class (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background`) that should be consistently applied but is currently underused on the Agents page.

**Alternatives Considered**:

- Using a dedicated focus-trap library (e.g., `focus-trap-react`) — The project's existing modal patterns (AddAgentModal, ConfirmationDialog) already implement focus management; consistency with existing patterns is preferred
- Implementing full WAI-ARIA combobox pattern for agent search — Rejected as overly complex; the search field is a simple text filter, not a selection widget

**Key Accessibility Audit Points**:

1. **Focus management**: AddAgentModal, AgentIconPickerModal, BulkModelUpdateDialog must trap focus and return focus on close; AgentPresetSelector confirmation dialogs must do the same
2. **Keyboard navigation**: All buttons, links, and interactive elements must be reachable via Tab; dropdowns (AddAgentPopover, preset selector) must support Escape to close; @dnd-kit KeyboardSensor already handles keyboard drag-and-drop
3. **ARIA labels**: Agent cards need accessible descriptions; custom dropdowns (AddAgentPopover, AgentPresetSelector) need complete ARIA labeling; status badges need accessible text
4. **Contrast ratios**: Verify all `text-muted-foreground`, opacity-reduced text, and badge colors meet minimum 4.5:1 against their backgrounds
5. **Focus indicators**: Ensure `.celestial-focus` or equivalent `focus-visible:ring-*` classes are present on ALL interactive elements across agents and board components
6. **Live regions**: Dynamic updates (save success/failure, delete confirmation results) should use `aria-live` for screen reader announcement
7. **Semantic roles**: AgentColumnCell needs `role="list"`, AgentTile needs `role="listitem"`, AgentSaveBar needs `role="status" aria-live="polite"`

**Current ARIA Coverage vs Gaps**:

| Component | Has ARIA | Missing |
|-----------|----------|---------|
| AddAgentModal | `role="dialog"`, `aria-modal`, `aria-label`, `role="switch"` | Focus trap completeness |
| AgentIconPickerModal | `role="presentation"`, `aria-label` on close | `role="dialog"`, `aria-modal` on modal content |
| AgentsPanel | `aria-label` on search, sort | None critical |
| AgentCard | `aria-label` on icon/edit/delete buttons | Missing card-level accessible description |
| AgentInlineEditor | `htmlFor` bindings | Focus restoration on close |
| AgentSaveBar | None | `role="status"`, `aria-live="polite"` |
| AgentConfigRow | None | `role="region"`, `aria-label` |
| AgentColumnCell | None | `role="list"` |
| AgentTile | None | `role="listitem"`, focus indicator |
| AgentPresetSelector | None | Focus trap in confirmations, `aria-expanded` on dropdown |
| AddAgentPopover | None | `role="listbox"` on options, focus trap, `aria-expanded` |

---

### R3: Responsive Design Patterns for Two-Panel Agent Layout

**Decision**: Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`) to adapt the Agents page layout across three breakpoints: desktop (1280px+), tablet (768px–1279px), and mobile (below 768px). The two-panel layout (Agent Catalog + Orbital Map) should stack vertically on narrower screens.

**Rationale**: The Agents page uses a CSS Grid layout with `xl:grid-cols-[minmax(0,1fr)_22rem]` for the two-panel split. This already collapses to single-column below `xl` (1280px). However, individual components within each panel need responsive verification: the agent card grid (`md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-3`), the Orbital Map grid (`gridTemplateColumns: repeat(${columnCount}, minmax(...))`), modals, and the inline editor layout.

**Alternatives Considered**:

- Hiding the Orbital Map on mobile and providing a separate view — Deferred; the audit focuses on ensuring the current layout doesn't break
- Using a tab-based layout switching on mobile — Deferred as a future enhancement beyond audit scope

**Key Responsive Audit Points**:

1. **Page shell**: Already responsive with `p-3 sm:p-4` and `rounded-[1.5rem]`
2. **Two-panel grid**: `xl:grid-cols-[minmax(0,1fr)_22rem]` — stacks below xl ✓
3. **Agent card grid**: `md:grid-cols-2 xl:grid-cols-3` — verify no overflow at each breakpoint
4. **Orbital Map grid**: Dynamic `gridTemplateColumns` — needs `overflow-x-auto` wrapper and minimum column widths
5. **Modals**: AddAgentModal, IconPickerModal, BulkModelUpdateDialog must be full-width on mobile
6. **Inline editor**: Uses `xl:grid-cols-[minmax(0,1.2fr)_minmax(20rem,0.8fr)]` — verify collapse behavior
7. **Touch targets**: All buttons and interactive elements need minimum 44×44px on touch screens
8. **AgentPresetSelector**: Dropdown positioning must not go off-screen on narrow viewports

---

### R4: React Performance Optimization Patterns

**Decision**: Use React's built-in optimization tools (`useMemo`, `useCallback`, `React.memo`) strategically where profiling identifies unnecessary re-renders. TanStack Query's built-in caching and stale-time management handles data-fetching performance.

**Rationale**: The Agents page already uses `useMemo` for derived data (e.g., spotlight agents, sorted catalog, pipeline mappings), `useCallback` for event handlers, and TanStack Query with `staleTime` values. The `useDeferredValue` hook handles search input debouncing. The @dnd-kit library handles drag-and-drop performance. Primary areas to audit are: whether child components that receive stable references still re-render unnecessarily, and whether the Orbital Map constellation SVG calculation is efficiently memoized.

**Alternatives Considered**:

- Virtualizing the agent catalog for large datasets — Deferred; the spec mentions 50+ agents as a target, and 100+ as edge case, which is manageable without virtualization
- Using React Compiler (React 19 feature) — Not yet adopted in this project; could be a future improvement
- Moving to signals or external state — Rejected; TanStack Query is the established pattern

**Key Performance Audit Points**:

1. **AgentCard rendering**: Most frequently rendered component — verify it doesn't re-render when sibling cards change
2. **AgentConfigRow constellation SVG**: `useMemo` for coordinate computation — verify dependency arrays are correct
3. **AgentPresetSelector**: Dropdown state changes should not trigger grid re-renders
4. **Search filtering**: `useDeferredValue` in AgentsPanel — verify no layout shift during deferred update
5. **Data fetching**: Verify no duplicate requests during normal navigation; confirm `staleTime` values are appropriate

---

### R5: Component State Management Patterns

**Decision**: Existing state management using a combination of React local state, TanStack Query for server state, and custom hooks (`useAgentConfig` for dirty tracking, `useUnsavedChanges` for route blocking) is appropriate for the Agents page. No new state management layer is needed.

**Rationale**: The Agents page uses:

- **TanStack Query**: For all server-fetched data (agent lists, pending agents, pipelines, models, available agents). Provides caching, refetch intervals, error states.
- **Local state (`useState`)**: For UI-only concerns (search filter, sort mode, modal visibility, editor state, icon picker).
- **Custom hooks**: `useAgentConfig` encapsulates column-to-agent mappings with add/remove/clone/reorder operations and dirty state tracking. `useConfirmation` standardizes confirmation dialogs. `useUnsavedChanges` blocks navigation on pending changes.
- **Imperative refs**: `AgentInlineEditor` uses `forwardRef` + `useImperativeHandle` for save/discard control from parent.

This architecture cleanly separates server state from UI state and follows established React patterns.

**Alternatives Considered**:

- Adding Zustand or Jotai for shared UI state — Rejected; current patterns are sufficient
- Centralizing all agent state in a context provider — Rejected; components are already well-scoped

---

### R6: Error Handling and Edge Case Patterns

**Decision**: The Agents page already handles most error states but should be audited for completeness and consistency. Each error state should display a consistent banner or message with a retry action where appropriate.

**Rationale**: Current error handling covers:

- ✅ Loading state: Skeleton grid in AgentsPanel, CelestialLoader in assignments
- ✅ No project selected: ProjectSelectionEmptyState
- ✅ Empty catalog: Empty state with CTA to create first agent
- ✅ Agent deletion: Confirmation dialog via useConfirmation
- ✅ Delete error/success: Inline messages on AgentCard
- ✅ Pending agents: Separate section with status badges
- ✅ Unsaved inline editor: UnsavedChanges dialog blocking navigation
- ✅ Save bar: Error display + saving state + discard option
- ✅ AddAgentPopover: Loading, error with retry, empty state, duplicate detection

Areas to audit for completeness:

- Pipeline queries in AgentsPage: No error handling if `pipelineList` or `pipelineAssignment` queries fail
- AgentPresetSelector: savedPipelines query loading state not displayed; error stays visible without dismiss
- BulkModelUpdateDialog: Error handling for mutation failure needs verification
- AgentIconPickerModal: No error handling if onSave rejects
- AgentInlineEditor: No form submission pattern (manual button save, no `<form onSubmit>`)
- Session expiry: Should redirect to login — needs verification
- Rapid project switching: Verify TanStack Query handles request cancellation

**Alternatives Considered**:

- Implementing a global error boundary for the Agents page — Already exists at app level; component-level error handling is appropriate
- Using toast notifications instead of inline messages — Rejected; inline messages provide persistent visibility and are the established pattern

---

## Research Summary

| Topic | Status | Key Finding |
|-------|--------|-------------|
| Design system tokens | ✅ Resolved | Comprehensive Celestial token set in `index.css`; ~6 components have hardcoded values to replace |
| Accessibility (WCAG AA) | ✅ Resolved | `.celestial-focus` class exists but is underused; 10+ components need ARIA improvements |
| Responsive design | ✅ Resolved | Three breakpoints; two-panel layout stacks at xl; Orbital Map grid needs responsive handling |
| React performance | ✅ Resolved | Good memoization already in place; audit for constellation SVG and card re-renders |
| State management | ✅ Resolved | TanStack Query + local state + custom hooks is appropriate; no new libraries needed |
| Error handling | ✅ Resolved | Most states covered; pipeline query errors and modal error dismissal need attention |
