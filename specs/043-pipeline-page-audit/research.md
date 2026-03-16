# Research: Pipeline Page Audit

**Feature Branch**: `043-pipeline-page-audit`
**Date**: 2026-03-16

## Research Tasks

### R1: Celestial Design System Token Compliance

**Decision**: All Pipeline page components must exclusively use CSS custom properties defined in `frontend/src/index.css` via the Tailwind v4 `@theme` block and custom utility classes. No hardcoded hex/rgb/hsl values should appear in component code.

**Rationale**: The Celestial design system defines a comprehensive token set covering colors (`--background`, `--foreground`, `--primary`, `--muted-foreground`, `--glow`, `--gold`, `--night`, `--star`, `--star-soft`, etc.), spacing (Tailwind's default scale), typography (`font-display`, `font-sans`), shadows, radii, and motion. Both light and dark themes are supported via `@media (prefers-color-scheme: dark)` with HSL-based token overrides. Using these tokens ensures visual consistency across pages and automatic theme switching support.

**Alternatives Considered**:

- Creating a separate design token JSON file — Rejected because Tailwind v4's native `@theme` block already serves this purpose and is the established convention
- Using CSS-in-JS for theming — Rejected because the project uses Tailwind CSS exclusively with utility classes and the `cn()` helper

**Key Tokens to Audit Against**:

- Colors: `primary`, `secondary`, `muted`, `accent`, `destructive`, `background`, `foreground`, `border`, `card`, `panel`, `popover`, `glow`, `gold`, `night`, `star`, `star-soft`
- Sync colors: `--sync-connected`, `--sync-polling`, `--sync-connecting`, `--sync-disconnected`
- Custom CSS classes: `.celestial-panel`, `.celestial-shell`, `.celestial-fade-in`, `.celestial-focus`, `.celestial-orbit`, `.celestial-sigil`, `.celestial-pulse-glow`, `.moonwell`, `.solar-chip`, `.solar-chip-*`, `.solar-action`, `.solar-action-danger`, `.ritual-stage`, `.constellation-grid`

**Hardcoded Values Found in Pipeline Components** (to be replaced during audit):

| Component | Line(s) | Hardcoded Value | Replacement |
|-----------|---------|-----------------|-------------|
| PipelineToolbar.tsx | Notification badge | `text-white`, `bg-red-500` | Design token equivalents (e.g., `text-destructive-foreground`, `bg-destructive`) |

**Token Usage Audit Summary**:

The Pipeline page components are in strong compliance with the design system. The vast majority of classes use CSS variable-based tokens (`bg-background/*`, `text-muted-foreground/*`, `border-border/*`, `border-primary/*`, `border-destructive/*`), HSL variable references (`hsl(var(--night)/...)`, `hsl(var(--panel)/...)`, `hsl(var(--glow)/...)`), and custom Celestial classes (`celestial-panel`, `celestial-fade-in`, `celestial-focus`). Only the PipelineToolbar notification badge uses non-token values (`text-white`, `bg-red-500`).

---

### R2: Accessibility Best Practices for Pipeline Builder Interfaces

**Decision**: Follow WAI-ARIA Authoring Practices for composite widgets, ensuring keyboard navigability, screen reader announcements, and proper focus management. The Pipeline page has partial ARIA support that must be completed to meet WCAG AA.

**Rationale**: WCAG AA requires that all interactive content be operable via keyboard (2.1.1), has visible focus indicators (2.4.7), has appropriate names and roles (4.1.2), and meets contrast ratios (1.4.3 normal text 4.5:1, 1.4.11 UI components 3:1). The project defines a `.celestial-focus` class (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background`) that should be consistently applied. The Pipeline page includes complex interactive elements — inline stage name editing, agent picker portals, model selection dropdowns, execution mode toggles — that require careful ARIA treatment.

**Alternatives Considered**:

- Using a dedicated focus-trap library (e.g., `focus-trap-react`) — The project's existing dialog patterns (UnsavedChangesDialog, ConfirmationDialog) already implement focus management; consistency with existing patterns is preferred
- Implementing full WAI-ARIA grid pattern for the pipeline board — Rejected as overly complex; the board is a visual layout tool, not a data grid

**Key Accessibility Audit Points**:

1. **Focus management**: UnsavedChangesDialog must trap focus and return focus on close; PipelineToolbar copy dialog must do the same; all dropdown menus (ModelSelector, PipelineModelDropdown) must trap focus
2. **Keyboard navigation**: All buttons, inputs, and interactive elements must be reachable via Tab; dropdowns must support Escape to close; inline stage name editing must support Enter to confirm and Escape to cancel
3. **ARIA labels**: Pipeline name input has `aria-label`, `aria-invalid`, `aria-describedby` ✓; saved workflow cards need complete accessible descriptions; execution mode toggles have `aria-label` ✓; agent action buttons have `aria-label` ✓
4. **Contrast ratios**: Verify all `text-muted-foreground` with opacity reductions (e.g., `/50`, `/60`) meet minimum 4.5:1 against their backgrounds
5. **Focus indicators**: Ensure `.celestial-focus` or equivalent `focus-visible:ring-*` classes are present on ALL interactive elements
6. **Live regions**: Dynamic updates (save success/failure, pipeline operations) should use `aria-live` for screen reader announcements
7. **Semantic roles**: Saved workflows list entries use `role="button"` ✓; UnsavedChangesDialog uses `role="button"` on close ✓

**Current ARIA Coverage vs Gaps**:

| Component | Has ARIA | Missing |
|-----------|----------|---------|
| AgentsPipelinePage | Pipeline name: `aria-label`, `aria-invalid`, `aria-describedby` | None critical at page level |
| PipelineBoard | `aria-label="Pipeline name"`, validation attributes | Stage area could use `role="region"` with label |
| PipelineToolbar | `role="presentation"`, copy dialog: `role="dialog"`, `aria-modal`, `aria-labelledby` | Save/delete/discard buttons: confirm `aria-label` or text content |
| SavedWorkflowsList | `aria-labelledby="saved-pipelines-title"`, `role="button"` on cards | Card-level accessible description (pipeline stage/agent counts) |
| StageCard | `role="img"` on lock icon, `aria-hidden` on decorative elements, `role="button"` on agent picker trigger, `aria-label` on remove | Inline stage name edit: `aria-label` on input field |
| ExecutionGroupCard | `aria-label` on mode toggle, `aria-label` on remove button | Group-level region label |
| AgentNode | `aria-label` on tools/clone/remove buttons | Agent description for screen readers |
| ModelSelector | None found | `aria-expanded` on trigger, `aria-label` on dropdown, `role="listbox"` on options |
| PipelineModelDropdown | Uses `.celestial-focus` class | `aria-expanded` on trigger, `role="listbox"` on options |
| PipelineAnalytics | None found | `role="region"` with label, heading hierarchy |
| PipelineFlowGraph | None found | `role="img"` with `aria-label` describing the flow, or `aria-hidden` if decorative |
| UnsavedChangesDialog | `role="button"` on close, `aria-label="Close dialog"` | Focus trap verification, `role="alertdialog"` consideration |

---

### R3: Responsive Design Patterns for Pipeline Builder

**Decision**: Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`) to adapt the Pipeline page layout across supported breakpoints: desktop (1280px+) and tablet/laptop (768px–1279px). The Pipeline page is a power-user tool and is not expected to be fully functional below 768px.

**Rationale**: The Pipeline page uses a flexible layout with multiple sections (toolbar, board, saved workflows, analytics) that must adapt to different viewport widths. The stage board uses a horizontal scroll pattern for multiple stages. The saved workflows list and analytics dashboard are secondary sections that should stack below the board on narrower screens.

**Alternatives Considered**:

- Hiding the analytics dashboard on mobile and providing a separate view — Deferred; the audit focuses on ensuring the current layout doesn't break at supported widths
- Using a collapsible sidebar pattern for saved workflows — Deferred as a future enhancement beyond audit scope

**Key Responsive Audit Points**:

1. **Page shell**: Verify padding, margins, and max-width constraints work at 768px minimum
2. **Pipeline board**: Stage cards should scroll horizontally when there are more stages than fit the viewport; no content should be clipped or inaccessible
3. **Stage cards**: Should maintain minimum width for readability; agent nodes should stack vertically within groups
4. **Saved workflows list**: Should adapt width; cards should remain readable at narrow widths
5. **Analytics dashboard**: Metrics cards should reflow from horizontal to stacked layout at narrow widths
6. **Toolbar**: Save/delete/copy buttons should remain accessible; consider icon-only mode at narrow widths
7. **Dialogs**: UnsavedChangesDialog, copy dialog should be responsive and centered
8. **Pipeline flow graph**: SVG visualization should scale proportionally

---

### R4: React Performance Optimization Patterns

**Decision**: Use React's built-in optimization tools (`useMemo`, `useCallback`, `React.memo`) strategically where profiling identifies unnecessary re-renders. TanStack Query's built-in caching and stale-time management handles data-fetching performance.

**Rationale**: The Pipeline page already uses `useMemo` for derived data, `useCallback` for event handlers, and TanStack Query for server state. The `usePipelineConfig` hook composes multiple sub-hooks (`usePipelineBoardMutations`, `usePipelineReducer`, `usePipelineModelOverride`, `usePipelineValidation`) creating a comprehensive state management layer. Primary areas to audit are: whether child components re-render unnecessarily when sibling state changes, and whether the pipeline flow graph SVG calculation is efficiently memoized.

**Alternatives Considered**:

- Virtualizing the saved workflows list for large datasets — Deferred; spec targets 50+ pipelines which is manageable without virtualization, but should be monitored
- Using React Compiler (React 19 feature) — Not yet adopted in this project; could be a future improvement
- Moving to signals or external state — Rejected; TanStack Query + useReducer is the established pattern

**Key Performance Audit Points**:

1. **StageCard rendering**: Most frequently rendered component (one per stage) — verify it doesn't re-render when other stages change
2. **AgentNode rendering**: Multiple per stage — verify stable keys and minimal re-renders
3. **PipelineFlowGraph SVG**: Computed visualization — verify `useMemo` wraps the computation with correct dependencies
4. **PipelineAnalytics**: Independent data section — should not re-render when board state changes
5. **SavedWorkflowsList**: List rendering — verify stable `key={pipeline.id}` usage
6. **Model selection cascades**: Changing the pipeline-level model override should efficiently propagate to agent nodes without full board re-render
7. **Data fetching**: Verify no duplicate requests for pipeline list and assignment during normal page usage; confirm `staleTime` values are appropriate

---

### R5: Component State Management Patterns

**Decision**: Existing state management using a combination of `useReducer` (via `usePipelineReducer`), TanStack Query for server state, and custom hooks (`usePipelineConfig` for orchestration, `usePipelineBoardMutations` for CRUD, `usePipelineValidation` for validation) is appropriate for the Pipeline page. No new state management layer is needed.

**Rationale**: The Pipeline page uses a well-structured state architecture:

- **TanStack Query**: For all server-fetched data (pipeline list, pipeline detail, pipeline assignment). Uses `pipelineKeys` factory for consistent query keys. Provides caching, error states, loading states.
- **useReducer (`usePipelineReducer`)**: For complex local pipeline editing state. Reducer handles actions: `SET_PIPELINE`, `UPDATE_PIPELINE`, `CLEAR_PIPELINE`, `SET_SAVING`, `SET_ERROR`, `SET_DIRTY`. This is appropriate for the interrelated state updates during editing.
- **Custom hooks**: `usePipelineConfig` orchestrates all sub-hooks and exposes a unified API. `usePipelineBoardMutations` provides 20+ granular mutation functions for stage/agent/group CRUD. `usePipelineValidation` manages field-level validation errors. `usePipelineModelOverride` derives model override state.
- **Navigation guard**: `useBlocker` from react-router-dom blocks navigation when `isDirty` is true. Combined with `useConfirmation` for the unsaved changes dialog.

This architecture cleanly separates server state from editing state and follows established React patterns.

**Alternatives Considered**:

- Adding Zustand or Jotai for shared pipeline state — Rejected; the reducer + hooks pattern is sufficient and already well-tested
- Centralizing all pipeline state in a context provider — Rejected; the hook composition pattern avoids unnecessary context re-renders

---

### R6: Error Handling and Edge Case Patterns

**Decision**: The Pipeline page already handles most error states but should be audited for completeness and consistency. Each error state should display a consistent message with a retry action where appropriate.

**Rationale**: Current error handling covers:

- ✅ Loading state: CelestialLoader while data fetches (AgentsPipelinePage line 1, conditional rendering)
- ✅ No project selected: ProjectSelectionEmptyState
- ✅ Empty pipeline board: Empty state when `boardState === 'empty'` with "Create Pipeline" CTA
- ✅ Save errors: `saveError` state surfaced in PipelineBoard validation display
- ✅ Pipeline name validation: `validationErrors.name` with `aria-invalid` and `aria-describedby`
- ✅ Unsaved changes: UnsavedChangesDialog with save/discard/cancel options
- ✅ Browser tab close: `beforeunload` event via `useBlocker`
- ✅ Pipeline deletion: Confirmation before delete

Areas to audit for completeness:

- **Rate limit detection**: Verify `isRateLimitApiError()` is used for API error differentiation
- **Partial section failures**: Pipeline list, pipeline assignment, and analytics are independent data sources — verify each has independent error handling
- **Deleted pipeline fallback**: If a selected pipeline is deleted externally, the page should handle the 404 gracefully
- **Rapid save clicks**: Verify save button is disabled during `isSaving` to prevent duplicate submissions
- **Name conflict on save**: Verify user-friendly error when pipeline name conflicts with existing pipeline
- **Stage name inline edit**: Verify validation and error display for empty stage names
- **Copy pipeline naming**: When copying a pipeline whose name already has "(Copy)" suffix, verify non-conflicting name generation
- **Session expiry**: Should redirect to login — needs verification

**Alternatives Considered**:

- Implementing a global error boundary for the Pipeline page — Already exists at app level; component-level error handling is appropriate
- Using toast notifications for all errors — Current inline error pattern provides persistent visibility and is the established convention

---

## Research Summary

| Topic | Status | Key Finding |
|-------|--------|-------------|
| Design system tokens | ✅ Resolved | Excellent compliance; only 2 hardcoded values in PipelineToolbar.tsx notification badge (`text-white`, `bg-red-500`) |
| Accessibility (WCAG AA) | ✅ Resolved | Good foundation with ARIA on key elements; ModelSelector, PipelineModelDropdown, PipelineAnalytics, PipelineFlowGraph need ARIA additions |
| Responsive design | ✅ Resolved | Two supported breakpoints (768px+, 1280px+); horizontal scroll for stages; audit overflow and minimum widths |
| React performance | ✅ Resolved | Good memoization in hooks; audit flow graph SVG computation and model override cascades |
| State management | ✅ Resolved | Well-structured useReducer + TanStack Query + hook composition; no changes needed |
| Error handling | ✅ Resolved | Most states covered; rate limit detection, partial section failures, and edge cases need verification |
