# Research: Agents Page Audit

**Feature**: 043-agents-page-audit | **Date**: 2026-03-16

## R1: Component Decomposition Strategy

**Task**: Research best practices for decomposing oversized React components (7 files exceed 250-line limit) while maintaining state coherence and minimizing prop drilling.

**Decision**: Extract sub-components into `src/components/agents/` following the existing feature-folder pattern. Complex state logic extracted into dedicated hooks. Use composition over prop drilling (>2 levels uses context or hook extraction).

**Rationale**: The codebase already follows this pattern — `src/components/board/` has 7+ sub-components composed from larger orchestrators. The existing `useAgentConfig` hook (349 lines) demonstrates the hook-extraction pattern. React composition (children, render props) avoids the need for new Context providers.

**Alternatives Considered**:
- **Context API for shared state**: Rejected — current hook-based approach is simpler and sufficient. Context adds indirection without measurable benefit for this page's component tree depth.
- **Compound component pattern**: Rejected — adds API complexity for components that are only used in one place. Simple extraction into sibling files is more maintainable.
- **State management library (Zustand/Jotai)**: Rejected — TanStack React Query + local state + custom hooks already covers all state management needs per Principle V (Simplicity & DRY).

**Decomposition Plan**:

| Component (Current) | Lines | Extracted Sub-Components |
|---------------------|-------|--------------------------|
| AgentsPanel.tsx (565) | ≤250 | AgentSearch, AgentSortControls, SpotlightSection, AgentList, PendingAgentsSection |
| AddAgentModal.tsx (520) | ≤250 | AgentForm (shared create/edit), AgentFormFields, AgentToolsSection |
| AgentPresetSelector.tsx (519) | ≤250 | PresetButtons, SavedPipelinesDropdown, PresetConfirmDialog |
| AgentConfigRow.tsx (480) | ≤250 | ColumnMappingGrid, DnDOrchestrator |
| AgentTile.tsx (295) | ≤250 | ConstellationSVG, TileActions |
| AgentCard.tsx (286) | ≤250 | AgentCardActions, AgentCardMetadata |
| AgentInlineEditor.tsx (272) | ≤250 | AgentEditForm (fields + validation) |

---

## R2: Design Token Compliance

**Task**: Research hardcoded color usage in agent components and identify replacements using the Celestial design system tokens.

**Decision**: Replace all hardcoded color values with Tailwind CSS custom properties from the Celestial design system. Use `dark:` variants consistently.

**Rationale**: The project uses Tailwind CSS 4.2 with a custom theme configuration. Design tokens are already defined as CSS custom properties and consumed via Tailwind utility classes throughout other pages. Agent components have ~6 instances of hardcoded colors that deviate from this pattern.

**Alternatives Considered**:
- **CSS-in-JS with theme provider**: Rejected — project uses Tailwind exclusively. Adding CSS-in-JS would violate the styling convention.
- **Inline style overrides**: Rejected — FR-017 explicitly prohibits inline `style={}` attributes.

**Hardcoded Colors to Replace**:

| Component | Current Value | Replacement Token |
|-----------|---------------|-------------------|
| AgentsPanel.tsx | `border-emerald-300/40`, `bg-emerald-50/80` | Celestial panel border/background tokens |
| AgentCard.tsx | `text-green-700 dark:text-green-400` | Status indicator design token |
| AddAgentPopover.tsx | `bg-blue-100`, `bg-green-100` | Source badge design tokens |
| AgentTile.tsx | Hardcoded SVG fill/stroke colors | CSS custom properties for constellation SVG |
| Various | `text-amber-*`, `bg-amber-*` for warnings | Warning design token |

---

## R3: Accessibility (WCAG AA) Patterns

**Task**: Research WCAG AA compliance gaps in the Agents page components and identify required ARIA patterns for custom interactive elements.

**Decision**: Follow WAI-ARIA Authoring Practices 1.2 for all custom controls. Use the existing `.celestial-focus` class for focus indicators. Implement focus trapping in all modals/dialogs.

**Rationale**: The project already has `.celestial-focus` defined but it's underused in agent components. Radix UI Dialog (used by ConfirmationDialog) handles focus trapping automatically, but custom modals (AgentIconPickerModal, AddAgentModal) need manual focus management.

**Alternatives Considered**:
- **Third-party focus trap library**: Rejected — Radix UI already provides `FocusTrap` component. Custom implementations use existing Radix primitives.
- **Skip accessibility for P3**: Rejected — spec explicitly includes accessibility as P2 (User Story 3) with 7 acceptance scenarios.

**Required ARIA Improvements**:

| Component | Issue | Fix |
|-----------|-------|-----|
| AgentIconPickerModal | `role="presentation"` incorrect | Change to `role="dialog"` + `aria-modal="true"` |
| AgentSaveBar | No live region for status updates | Add `role="status" aria-live="polite"` |
| AgentConfigRow | No region landmark | Add `role="region" aria-label="Column assignments"` |
| AgentColumnCell | List semantics missing | Add `role="list"` container, `role="listitem"` on tiles |
| AgentPresetSelector | Dropdown state not announced | Add `aria-expanded` on trigger button |
| AddAgentPopover | Options not announced | Add `role="listbox"` + `role="option"` on items |
| All interactive elements | Inconsistent focus indicators | Apply `.celestial-focus` or `focus-visible:ring-*` consistently |
| All form fields | Some missing labels | Add `aria-label` or visible `<label>` to all inputs |

---

## R4: React Query Patterns and Cache Strategy

**Task**: Research current React Query usage in agent hooks and identify gaps in query key conventions, staleTime configuration, and mutation error handling.

**Decision**: Standardize on the existing `agentKeys` factory pattern. Configure `staleTime: 30_000` for agent lists, `staleTime: 60_000` for configuration data. All mutations must have `onError` with user-visible toast feedback.

**Rationale**: The codebase already has `agentKeys` (in `useAgents.ts`) and `pipelineKeys` as reference patterns. Current agent queries lack explicit `staleTime` configuration, defaulting to 0 (always stale). This causes unnecessary refetches.

**Alternatives Considered**:
- **Global staleTime configuration**: Rejected — different data types have different freshness requirements. Per-query configuration is more precise.
- **Optimistic updates for all mutations**: Rejected — agent CRUD operations are not latency-sensitive enough to justify the complexity. `invalidateQueries` on success is sufficient per Principle V.

**Query Configuration Standards**:

| Query | Key Pattern | staleTime | Notes |
|-------|-------------|-----------|-------|
| Agent list | `agentKeys.list(projectId)` | 30s | Refreshes on window focus |
| Pending agents | `agentKeys.pending(projectId)` | 30s | May change frequently |
| Pipeline list | `['pipelines', 'list', projectId]` | 30s | Cross-referenced for usage counts |
| Workflow config | `['workflow', projectId]` | 60s | Rarely changes |

---

## R5: Error Handling Patterns

**Task**: Research consistent error handling patterns for the Agents page, including rate limit detection, user-friendly messages, and retry mechanisms.

**Decision**: Use the existing `isRateLimitApiError()` utility for rate limit detection. Error messages follow the format: "Could not [action]. [Reason, if known]. [Suggested next step]." All mutations use toast notifications for error feedback.

**Rationale**: The project already has `isRateLimitApiError()` and toast infrastructure. The error message format is specified in FR-014. The pattern is consistent with other pages in the application.

**Alternatives Considered**:
- **Global error boundary for all API errors**: Rejected — per FR-006, each data source should handle errors independently. A global handler would mask the source of failures.
- **Retry with exponential backoff**: Rejected for mutations — user-initiated retries are more appropriate for destructive actions. Read queries use React Query's built-in retry (3 attempts).

**Error Handling Matrix**:

| Scenario | Detection | User Message | Action |
|----------|-----------|-------------|--------|
| API error (non-rate-limit) | HTTP status >= 400 | "Could not [action]. Please try again." | Retry button |
| Rate limit error | `isRateLimitApiError(error)` | "Rate limit reached. Please wait a moment and try again." | Auto-retry after delay |
| Network error | `error.message` contains network-related text | "Connection error. Check your network and try again." | Retry button |
| Rendering error | ErrorBoundary catches | "Something went wrong. Try refreshing the page." | Refresh button |
| Empty state (no agents) | `data.length === 0` | Meaningful empty state with CTA | "Create Agent" button |

---

## R6: Responsive Design Strategy

**Task**: Research responsive behavior requirements for the Agents page across viewport widths 768px–1920px.

**Decision**: Three breakpoints: xl (≥1280px) two-panel layout, md (768–1279px) stacked layout, and base (<768px) single-column. Use Tailwind responsive prefixes. No new CSS breakpoints needed.

**Rationale**: The project already uses Tailwind's responsive prefixes (`md:`, `lg:`, `xl:`) throughout other pages. The Agents page has a two-panel layout (catalog + Orbital Map) that naturally stacks on smaller screens.

**Alternatives Considered**:
- **Container queries**: Rejected — browser support is adequate but adds complexity without clear benefit for this layout. Tailwind responsive prefixes are the established pattern.
- **Separate mobile/desktop components**: Rejected — a single responsive component tree with Tailwind variants is simpler and more maintainable.

**Breakpoint Behavior**:

| Viewport | Layout | Catalog | Orbital Map |
|----------|--------|---------|-------------|
| ≥1280px (xl) | Side-by-side | Left panel, full width | Right panel, full width |
| 768–1279px (md) | Stacked | Full width, above | Full width, below |
| <768px | Single column | Full width, stacked | Hidden or collapsed accordion |

**Touch Targets**: All interactive elements must be ≥44×44px on viewports <1280px per WCAG 2.5.5.
