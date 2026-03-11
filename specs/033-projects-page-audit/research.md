# Research: Audit & Polish the Projects Page for Quality and Consistency

**Feature Branch**: `033-projects-page-audit`
**Date**: 2026-03-10

## Research Tasks

### R1: Celestial Design System Token Compliance

**Decision**: All Projects page components must exclusively use CSS custom properties defined in `frontend/src/index.css` via the Tailwind v4 `@theme` block and custom utility classes. No hardcoded hex/rgb/hsl values should appear in component code.

**Rationale**: The Celestial design system defines a comprehensive token set covering colors (`--color-background`, `--color-primary`, `--color-muted-foreground`, etc.), spacing (Tailwind's default scale), typography (`--font-display`, `--font-sans`), shadows (`--shadow-sm` through `--shadow-lg`), radii (`--radius-sm`, `--radius-md`, `--radius-lg`), and motion (`--transition-cosmic-*`). Both light and dark themes are supported via `@media (prefers-color-scheme: dark)` with HSL-based token overrides. Using these tokens ensures visual consistency across pages and automatic theme switching support.

**Alternatives Considered**:

- Creating a separate design token JSON file — Rejected because Tailwind v4's native `@theme` block already serves this purpose and is the established convention
- Using CSS-in-JS for theming — Rejected because the project uses Tailwind CSS exclusively with utility classes and the `cn()` helper

**Key Tokens to Audit Against**:

- Colors: `primary`, `secondary`, `muted`, `accent`, `destructive`, `background`, `foreground`, `border`, `card`, `panel`, `popover`, `glow`, `gold`, `night`
- Priority colors: `--priority-p0` (red), `--priority-p1` (orange), `--priority-p2` (blue), `--priority-p3` (green)
- Custom CSS classes: `.celestial-panel`, `.celestial-fade-in`, `.moonwell`, `.solar-chip`, `.solar-chip-*`, `.project-pipeline-select`, `.project-pipeline-option`, `.project-board-column`, `.project-board-card`

---

### R2: Accessibility Best Practices for Kanban Boards

**Decision**: Follow WAI-ARIA Authoring Practices for composite widgets, ensuring keyboard navigability, screen reader announcements, and proper focus management. The Projects page already has partial ARIA support that should be completed.

**Rationale**: WCAG AA requires that all interactive content be operable via keyboard (2.1.1), has visible focus indicators (2.4.7), has appropriate names and roles (4.1.2), and meets contrast ratios (1.4.3 normal text 4.5:1, 1.4.11 UI components 3:1). The Projects page already uses `aria-haspopup`, `aria-expanded`, `role="listbox"`, `role="option"`, `role="switch"`, and `role="region"`. Areas to audit include: focus trap in IssueDetailModal, keyboard navigation through board cards, focus indicators on all interactive elements, and screen reader announcements for dynamic state changes.

**Alternatives Considered**:

- Using a dedicated accessibility testing library like axe-core during development — Recommended as a supplementary tool; the project already has `jest-axe` in devDependencies
- Implementing full WAI-ARIA grid pattern for the Kanban board — Rejected as overly complex; the board uses a simpler list-of-columns pattern with cards as clickable items

**Key Accessibility Audit Points**:

1. **Focus management**: IssueDetailModal must trap focus and return focus on close; pipeline selector dropdown must manage focus
2. **Keyboard navigation**: All buttons, links, and interactive elements must be reachable via Tab; dropdowns must support Escape to close
3. **ARIA labels**: Custom dropdowns (project selector, pipeline selector) need complete ARIA labeling; status indicators need accessible text
4. **Contrast ratios**: Verify all `text-muted-foreground`, `text-muted-foreground/80`, and `text-muted-foreground/60` meet minimum 4.5:1 against their backgrounds
5. **Focus indicators**: Ensure `focus-visible:ring-*` classes are present on all interactive elements
6. **Live regions**: Dynamic updates (rate limit banners, sync status changes) should use `aria-live` for screen reader announcement

---

### R3: Responsive Design Patterns for Board Layouts

**Decision**: Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`) to adapt the Projects page layout across three breakpoints: desktop (1280px+), tablet (768px–1279px), and mobile (below 768px). The Kanban board should scroll horizontally on smaller screens rather than stacking columns.

**Rationale**: The Projects page already uses some responsive classes (e.g., `sm:p-6`, `sm:flex-row`). However, the board grid uses a dynamic `gridTemplateColumns` style that may not adapt well to smaller screens. The pipeline stages grid similarly uses a dynamic column count. Both need responsive overrides. Touch targets must be at minimum 44×44px on touch screens per WCAG 2.5.5.

**Alternatives Considered**:

- Stacking columns vertically on mobile — Rejected because users need to see column context; horizontal scrolling is the standard Kanban pattern
- Using a different layout entirely for mobile (e.g., list view) — Deferred as a future enhancement; the audit focuses on ensuring the current layout doesn't break

**Key Responsive Audit Points**:

1. **Page shell**: Already responsive with `p-4 sm:p-6` and `rounded-[1.5rem] sm:rounded-[1.75rem]`
2. **Header**: Already wraps with `flex-col sm:flex-row`
3. **Board grid**: Needs `overflow-x-auto` wrapper and minimum column widths that work on mobile
4. **Pipeline stages grid**: Uses dynamic `gridTemplateColumns` — needs responsive handling
5. **Modals**: IssueDetailModal and launch panel must be full-width on mobile
6. **Touch targets**: All buttons and interactive elements need minimum 44×44px on touch screens

---

### R4: React Performance Optimization Patterns

**Decision**: Use React's built-in optimization tools (`useMemo`, `useCallback`, `React.memo`) strategically where profiling identifies unnecessary re-renders. TanStack Query's built-in caching and stale-time management handles data-fetching performance.

**Rationale**: The Projects page already uses `useMemo` for derived data (e.g., `assignedPipeline`, `assignedStageMap`, `blockingIssueNumbers`), `useCallback` for event handlers, and TanStack Query with appropriate `staleTime` values. The `useBoardControls` hook computes `transformedData` with memoization. The primary areas to audit are: whether child components that receive stable references still re-render unnecessarily, whether the `statusColorToCSS` utility in the column map causes re-renders, and whether the pipeline selector dropdown creates unnecessary renders when closed.

**Alternatives Considered**:

- Virtualizing the board for large datasets — Deferred; the spec mentions 100+ items as a target, which is manageable without virtualization. Can be revisited if profiling shows issues
- Using React Compiler (React 19 feature) — Not yet adopted in this project; could be a future improvement
- Moving to signals or external state — Rejected; TanStack Query is the established pattern and works well

**Key Performance Audit Points**:

1. **Board column rendering**: Each column maps items — ensure stable keys and avoid inline object creation in props
2. **IssueCard**: Most frequently rendered component — verify it doesn't re-render when sibling cards change
3. **Pipeline selector**: Dropdown state changes should not trigger board re-renders
4. **Rate limit banner**: Updates to rate limit info should not cause full page re-renders
5. **Data fetching**: Verify no duplicate requests during normal navigation; confirm `staleTime` values are appropriate

---

### R5: Component State Management Patterns

**Decision**: Existing state management using a combination of React local state, TanStack Query for server state, and localStorage persistence (via `useBoardControls`) is appropriate for the Projects page. No new state management layer is needed.

**Rationale**: The Projects page uses:

- **TanStack Query**: For all server-fetched data (projects list, board data, pipelines, blocking queue, pipeline assignments). Provides caching, refetch intervals, and error states.
- **Local state (`useState`)**: For UI-only concerns (selected item, selector open/closed states).
- **Custom hooks**: Encapsulate complex logic (board controls with localStorage, real-time sync with WebSocket/polling fallback, refresh with rate limit tracking).
- **Context**: `useRateLimitStatus` for global rate limit display; `useAuth` for authentication.

This architecture cleanly separates server state from UI state and follows established React patterns. No consolidation or migration is needed.

**Alternatives Considered**:

- Adding Zustand or Jotai for shared UI state — Rejected; current patterns are sufficient and adding a state library increases complexity without clear benefit
- Moving board controls to URL search params — Deferred as a future enhancement; localStorage persistence is acceptable for now

---

### R6: Error Handling and Edge Case Patterns

**Decision**: The Projects page already handles most error states but should be audited for completeness. Each error state should display a consistent banner with a retry action where appropriate.

**Rationale**: Current error handling covers:

- ✅ Rate limit errors (429) with countdown display
- ✅ Rate limit low warning banner
- ✅ Refresh failure banner
- ✅ Projects loading failure with API error details
- ✅ Board data loading failure with retry button
- ✅ Empty board state (no items)
- ✅ Empty board state (filters applied, no matches)
- ✅ No project selected state

Areas to audit:

- Pipeline loading errors (handled in `ProjectIssueLaunchPanel` — verify)
- Session expiry (should redirect to login — verify)
- WebSocket disconnection (shows status indicator — verify graceful degradation)
- Rapid project switching (verify request cancellation)

**Alternatives Considered**:

- Implementing a global error boundary — Already exists at the app level; the page-level error handling is appropriate
- Using toast notifications instead of banners — Rejected; inline banners provide persistent visibility and are the established pattern

---

## Research Summary

| Topic | Status | Key Finding |
|-------|--------|-------------|
| Design system tokens | ✅ Resolved | Comprehensive Celestial token set in `index.css`; audit for hardcoded values |
| Accessibility (WCAG AA) | ✅ Resolved | Partial ARIA support exists; focus trap, contrast, and keyboard nav need audit |
| Responsive design | ✅ Resolved | Three breakpoints; board needs horizontal scroll on mobile; touch targets need validation |
| React performance | ✅ Resolved | Good memoization already; audit for unnecessary re-renders in board columns |
| State management | ✅ Resolved | TanStack Query + local state is appropriate; no new libraries needed |
| Error handling | ✅ Resolved | Most states covered; verify pipeline errors, session expiry, WebSocket degradation |

All NEEDS CLARIFICATION items have been resolved through codebase analysis. No external research dependencies remain.
