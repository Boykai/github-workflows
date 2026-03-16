# Research: Pipeline Page Audit

**Feature**: `043-pipeline-page-audit` | **Date**: 2026-03-16

## R1: Celestial Design System Token Compliance

**Decision**: All Pipeline page components must exclusively use Celestial design tokens from `frontend/src/index.css` and Tailwind utility classes. No hardcoded colors, spacing, or typography values.

**Rationale**: The Celestial design system is the single source of truth for visual consistency across Project Solune. All other audited pages (Projects, Agents, Chores, Settings) have been aligned to this system. The Pipeline page must follow the same standard to ensure seamless theme switching (light/dark) and visual cohesion.

**Alternatives Considered**:
- CSS-in-JS with styled-components — rejected; project uses Tailwind CSS v4 exclusively
- CSS Modules — rejected; inconsistent with established codebase pattern
- Inline styles — rejected; violates codebase convention (`cn()` helper with Tailwind classes)

**Key Findings**:
- Design tokens are defined in `frontend/src/index.css` as CSS custom properties
- Custom utility classes: `.celestial-panel`, `.moonwell`, `.solar-chip`, `.nebula-glow`, `.celestial-focus`, `.glass-panel`
- The `cn()` helper from `frontend/src/lib/utils.ts` (clsx + tailwind-merge) is the standard for conditional classes
- Dark mode is handled via Tailwind `dark:` variants and CSS variable overrides
- Components must use `bg-card`, `text-card-foreground`, `border-border`, `bg-muted`, etc. — never raw color values like `#fff`, `bg-white`, or `text-gray-500`

---

## R2: Accessibility Best Practices for Pipeline Builder Interfaces

**Decision**: Follow WCAG AA compliance with focus on keyboard navigation, ARIA attributes for custom controls, focus trapping in dialogs, and non-color-dependent status indicators.

**Rationale**: The Pipeline page has complex interactive elements — inline stage name editing, drag-and-drop agent reordering, portal-based dropdowns (model selector, agent picker), execution mode toggles, and multi-step unsaved-changes dialogs. These are high-risk areas for accessibility gaps. WCAG AA is the minimum target consistent with the spec.

**Alternatives Considered**:
- WCAG AAA compliance — rejected; overly restrictive for a power-user workflow builder tool. AA is the established project standard
- No accessibility target — rejected; spec explicitly requires WCAG AA (FR-013 through FR-016)

**Key Findings**:
- All interactive elements must be reachable via Tab with visible `celestial-focus` or `focus-visible:` ring styles
- Dialogs (UnsavedChangesDialog, ConfirmationDialog) must trap focus, close on Escape, and return focus to trigger element — Radix UI primitives handle this when used correctly
- Saved workflow cards must be proper interactive elements (buttons/links), not styled `<div>` with `onClick` (FR-026)
- Status indicators (stage execution mode, pipeline save state, assignment status) must use icon + text, not color alone (FR-015)
- Form inputs (pipeline name, stage names) need `aria-label` or visible labels with `htmlFor` association
- The execution mode toggle must have `role="switch"` or equivalent with `aria-checked` state
- Screen reader text: decorative icons (Lucide) need `aria-hidden="true"`; meaningful icons need `aria-label`
- Error messages on validation (e.g., empty pipeline name) must be programmatically associated with the input via `aria-describedby`

---

## R3: Responsive Design Patterns for Multi-Panel Builder Pages

**Decision**: Use Tailwind responsive utilities with two breakpoints: desktop (1280px+) and tablet/laptop (768px–1279px). The Pipeline page is a power-user tool not expected to be functional below 768px.

**Rationale**: The spec explicitly scopes responsive behavior to 768px–1920px (Assumption 3). The Pipeline page has a complex multi-section layout (toolbar, stage board, saved workflows, analytics) that must reflow correctly. Below 768px, a simplified view or informational message is acceptable.

**Alternatives Considered**:
- Full mobile support — rejected; Pipeline builder is a power-user tool with drag-and-drop, multi-panel layout, and inline editing that doesn't translate to small screens
- Fixed desktop-only layout — rejected; many users access on laptop screens (1280px–1366px)

**Key Findings**:
- Desktop (1280px+): Full multi-column layout with stage board, saved workflows sidebar, and analytics visible simultaneously
- Tablet/Laptop (768px–1279px): Sections stack vertically or use collapsible panels; stage board adapts column count
- Tailwind breakpoints: `md:` (768px), `lg:` (1024px), `xl:` (1280px) — use these for responsive classes
- CSS Grid and Flexbox used for layout; avoid fixed pixel widths
- Pipeline flow graph visualization must scale with container width
- The saved workflows list may need to collapse to a dropdown or slide-out panel on narrower viewports

---

## R4: React Performance Optimization for Pipeline Board

**Decision**: Apply targeted memoization to frequently-rendered list items (StageCard, AgentNode, SavedWorkflowsList items). Use `useMemo` for derived computations (stage grouping, agent counting, model override mode). Avoid premature optimization.

**Rationale**: The Pipeline page renders potentially many stage cards, each with multiple execution groups and agent nodes. Additionally, the saved workflows list can contain 50+ items. Performance optimization should focus on preventing unnecessary re-renders in these list items.

**Alternatives Considered**:
- Virtualizing all lists with `react-window` — rejected for stage board (typically <10 stages); worth considering for saved workflows if >50 items
- No memoization — rejected; StageCard and AgentNode receive complex props that change identity on every render without memoization
- Global state management (Redux, Zustand) — rejected; existing React Query + useReducer pattern is well-established and sufficient

**Key Findings**:
- StageCard receives pipeline state and mutation callbacks — wrap in `React.memo` if not already
- AgentNode props include model info and tool config — stable references needed via `useCallback` for mutation handlers
- Saved workflows list items: use `key={pipeline.id}` (never index-based keys)
- Heavy computations: model override mode derivation (`usePipelineModelOverride`) already uses proper state derivation
- Pipeline flow graph visualization: canvas/SVG rendering should be memoized to prevent re-computation on unrelated state changes
- Analytics dashboard calculations should be wrapped in `useMemo`

---

## R5: State Management Patterns for Pipeline Editor

**Decision**: Maintain the existing architecture of `usePipelineConfig` as the orchestration hook composing sub-hooks (`usePipelineBoardMutations`, `usePipelineValidation`, `usePipelineModelOverride`) with `useReducer` for state machine. This follows established codebase patterns.

**Rationale**: The Pipeline page's state management is already well-structured with clear separation of concerns. The hooks follow the project convention of extracting complex logic from components. The audit should verify this architecture works correctly rather than restructuring it.

**Key Findings**:
- `usePipelineConfig` (232 lines) orchestrates all pipeline CRUD operations
- `usePipelineBoardMutations` (418 lines) handles stage/agent/group mutations — this is the largest hook and may benefit from further decomposition if individual functions exceed 15 lines
- `usePipelineReducer` (115 lines) manages state transitions with snapshot-based dirty tracking
- `usePipelineValidation` (38 lines) handles field validation — currently only validates name; may need extension
- `usePipelineModelOverride` (98 lines) derives model mode from agent configuration
- `useSelectedPipeline` provides pipeline selection context
- React Query is used for data fetching with `pipelineKeys` factory pattern
- Dual navigation guards: in-app (`useBlocker` from react-router) and browser (`beforeunload` event)
- Legacy backward compatibility: `syncLegacyAgents()` keeps `stage.agents[]` in sync with `stage.groups[].agents[]`

---

## R6: Error Handling and User Feedback Patterns

**Decision**: All API errors must be displayed as user-friendly messages following the format "Could not [action]. [Reason, if known]. [Suggested next step]." Rate limit errors get specific detection and messaging. All mutations provide success feedback.

**Rationale**: The spec has explicit requirements for error handling (FR-004, FR-005) and success feedback (FR-008). The codebase has existing utilities (`isRateLimitApiError()` in `utils/rateLimit.ts`) that must be used consistently.

**Alternatives Considered**:
- Global error boundary only — rejected; spec requires section-level error isolation (FR-006)
- Raw error forwarding — rejected; spec explicitly prohibits showing raw error codes or stack traces (FR-004)

**Key Findings**:
- `isRateLimitApiError()` from `@/utils/rateLimit` detects rate limit responses — must be used in all mutation `onError` handlers
- Toast notifications are the standard success feedback pattern in the application
- Pipeline name conflict errors (HTTP 409) need specific user-friendly messaging: "Could not save pipeline. The name '[name]' is already in use. Please try a different name."
- Section-level error isolation: pipeline list, pipeline assignment, and analytics should each handle their own error states independently
- The unsaved-changes dialog must handle save failures gracefully — if save fails during "Save and Continue", the dialog should remain open with an error message
- Mutation error handling pattern: `useMutation({ onError: (error) => { if (isRateLimitApiError(error)) { /* rate limit message */ } else { /* generic user-friendly message */ } } })`

---

## Research Summary

| Topic | Status | Key Finding |
|-------|--------|-------------|
| Design Token Compliance | ✅ Resolved | Use Celestial tokens exclusively; `cn()` for conditional classes; `dark:` variants for theme |
| Accessibility (a11y) | ✅ Resolved | WCAG AA; keyboard nav + ARIA + focus trapping; saved workflow cards must be interactive elements |
| Responsive Design | ✅ Resolved | 768px–1920px; Tailwind responsive utilities; sections stack on narrower viewports |
| Performance | ✅ Resolved | Targeted memoization for list items; `useMemo` for derived state; virtualization for 50+ saved workflows |
| State Management | ✅ Resolved | Maintain existing hook architecture; verify correctness; legacy sync compatibility |
| Error Handling | ✅ Resolved | User-friendly messages; rate limit detection; section-level error isolation; success feedback |
