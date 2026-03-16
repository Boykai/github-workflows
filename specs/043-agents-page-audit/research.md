# Research: Agents Page Audit

**Feature Branch**: `043-agents-page-audit`
**Date**: 2026-03-16

## Research Tasks

### R1: Component Decomposition Strategy for Oversized Files

**Decision**: Decompose oversized components (AgentsPanel 565 lines, AddAgentModal 520 lines, AgentConfigRow 480 lines, AgentPresetSelector 519 lines, AgentTile 308 lines, AgentCard 286 lines, AgentInlineEditor 272 lines) by extracting logically self-contained UI sections and complex state into dedicated sub-components and hooks. Target: ≤250 lines per file.

**Rationale**: The spec mandates FR-001 (≤250 lines per component) and FR-002 (state logic >15 lines extracted to hooks). The existing codebase already follows this pattern for smaller components (AgentSaveBar at 55 lines, AgentIconCatalog at 70 lines, AgentDragOverlay at 69 lines). The reference audit (035-audit-agents-page) validated this approach. Decomposition should follow natural UI boundaries (search section, sort controls, card actions, form sections) rather than arbitrary line-count splits.

**Alternatives Considered**:

- Splitting by render phase (data prep vs. JSX) — Rejected because it creates artificial boundaries that harm readability; better to split by feature/section
- Using render props or HOCs for composition — Rejected in favor of simpler component extraction which aligns with React 19 patterns and the existing codebase conventions
- Leaving components as-is with inline documentation — Rejected because it violates FR-001 and makes testing difficult

**Decomposition Plan**:

| Component | Current Lines | Extraction Targets | Estimated Post-Split Lines |
|-----------|--------------|-------------------|---------------------------|
| AgentsPanel (565) | Search, sort, spotlight, grid, pending sections | AgentSearch, AgentSortControls, SpotlightSection, AgentGrid, PendingAgentsSection | ~180–220 |
| AddAgentModal (520) | Form sections, validation, AI enhance | AgentFormFields, AgentFormActions, useAgentForm hook | ~180–220 |
| AgentConfigRow (480) | DnD context, preset selector, constellation SVG, column grid | useAgentDnd hook, ConstellationSvg, ColumnGrid | ~180–220 |
| AgentPresetSelector (519) | Preset buttons, saved pipelines dropdown, confirmation dialogs | PresetButtonGroup, SavedPipelinesDropdown, usePresetSelector hook | ~180–220 |
| AgentTile (308) | Tile layout, action buttons, model display, drag handle | AgentTileActions, AgentTileContent | ~200–240 |
| AgentCard (286) | Card layout, action buttons, metadata display, status badges | AgentCardActions, AgentCardMeta | ~200–240 |
| AgentInlineEditor (272) | Editor form, tool list, model selector | AgentEditorForm, useAgentEditor hook | ~200–240 |

---

### R2: Celestial Design System Token Compliance

**Decision**: All Agents page components must exclusively use CSS custom properties defined in `solune/frontend/src/index.css` via the Tailwind v4 `@theme` block and custom utility classes. No hardcoded hex/rgb/hsl values should appear in component code.

**Rationale**: The Celestial design system defines a comprehensive token set covering colors (`--background`, `--foreground`, `--primary`, `--muted-foreground`, `--glow`, `--gold`, `--night`, `--star`, `--star-soft`), spacing (Tailwind's default scale), typography (`font-display`, `font-sans`), shadows, radii, and motion. Both light and dark themes are supported via `@media (prefers-color-scheme: dark)` with HSL-based token overrides. Using these tokens ensures visual consistency across pages and automatic theme switching.

**Alternatives Considered**:

- Creating a separate design token JSON file — Rejected because Tailwind v4's native `@theme` block already serves this purpose and is the established convention
- Using CSS-in-JS for theming — Rejected because the project uses Tailwind CSS exclusively with utility classes and the `cn()` helper

**Key Tokens to Audit Against**:

- Colors: `primary`, `secondary`, `muted`, `accent`, `destructive`, `background`, `foreground`, `border`, `card`, `panel`, `popover`, `glow`, `gold`, `night`, `star`, `star-soft`
- Sync colors: `--sync-connected`, `--sync-polling`, `--sync-connecting`, `--sync-disconnected`
- Custom CSS classes: `.celestial-panel`, `.celestial-shell`, `.celestial-fade-in`, `.celestial-focus`, `.celestial-orbit`, `.celestial-sigil`, `.celestial-pulse-glow`, `.moonwell`, `.solar-chip`, `.solar-chip-*`, `.solar-action`, `.solar-action-danger`, `.ritual-stage`, `.constellation-grid`

**Hardcoded Values to Replace**:

| Component | Issue | Replacement |
|-----------|-------|-------------|
| AgentsPanel.tsx | `border-emerald-300/40`, `bg-emerald-50/80` | `solar-chip-success` design token |
| AgentCard.tsx | `text-green-700 dark:text-green-400` | Design token or `solar-chip-success` text |
| AddAgentPopover.tsx | `bg-blue-100 dark:bg-blue-900/30`, `bg-green-100 dark:bg-green-900/30` | Design token badges |
| AgentTile.tsx | Inline SVG `hsl(var(--gold))`, `hsl(var(--glow))` with magic opacity | CSS custom properties via Tailwind classes |
| AgentDragOverlay.tsx | `min-w-[280px] max-w-[340px]` | Consistent design scale values |
| Various | Z-index values `z-[120]`, `z-[140]`, `z-[9999]`, `z-50` | Standardized z-layer system |

---

### R3: Accessibility Best Practices for Agent Management Interfaces

**Decision**: Follow WAI-ARIA Authoring Practices for composite widgets, ensuring keyboard navigability, screen reader announcements, and proper focus management. Achieve WCAG AA compliance across all Agents page components.

**Rationale**: WCAG AA requires that all interactive content be operable via keyboard (2.1.1), has visible focus indicators (2.4.7), has appropriate names and roles (4.1.2), and meets contrast ratios (1.4.3 normal text 4.5:1, 1.4.11 UI components 3:1). The project defines a `.celestial-focus` class (`focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background`) that should be consistently applied.

**Alternatives Considered**:

- Using a dedicated focus-trap library (`focus-trap-react`) — Existing modal patterns already implement focus management via Radix UI Dialog; consistency with existing patterns preferred
- Implementing full WAI-ARIA combobox for agent search — Rejected as overly complex; the search field is a simple text filter

**Current ARIA Coverage vs. Gaps**:

| Component | Has ARIA | Missing |
|-----------|----------|---------|
| AddAgentModal | `role="dialog"`, `aria-modal`, `aria-label`, `role="switch"` | Focus trap completeness verification |
| AgentIconPickerModal | `role="presentation"`, `aria-label` on close | Needs `role="dialog"`, `aria-modal` on modal content |
| AgentsPanel | `aria-label` on search, sort | None critical |
| AgentCard | `aria-label` on icon/edit/delete buttons | Missing card-level accessible description |
| AgentInlineEditor | `htmlFor` bindings | Focus restoration on close |
| AgentSaveBar | None | `role="status"`, `aria-live="polite"` |
| AgentConfigRow | None | `role="region"`, `aria-label` |
| AgentColumnCell | None | `role="list"` |
| AgentTile | None | `role="listitem"`, focus indicator |
| AgentPresetSelector | None | `aria-expanded` on dropdown, focus trap in confirmations |
| AddAgentPopover | None | `role="listbox"` on options, `aria-expanded`, focus trap |

---

### R4: Responsive Design Patterns for Two-Panel Agent Layout

**Decision**: Use Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`, `xl:`) to verify and fix the Agents page layout across breakpoints: desktop (1280px+), tablet (768px–1279px), and mobile (below 768px, out of scope per spec but should not break). The two-panel layout (Agent Catalog + Orbital Map) already collapses to single-column below `xl`.

**Rationale**: The Agents page uses a CSS Grid layout with `xl:grid-cols-[minmax(0,1fr)_22rem]` for the two-panel split. Individual components need responsive verification: the agent card grid (`md:grid-cols-2 xl:grid-cols-3`), modals, the inline editor layout, and the Orbital Map column grid.

**Alternatives Considered**:

- Hiding the Orbital Map on mobile with a separate view — Deferred; audit focuses on ensuring the current layout doesn't break
- Tab-based layout switching on mobile — Deferred as a future enhancement beyond audit scope

**Key Responsive Audit Points**:

1. Page shell: Already responsive with `p-3 sm:p-4` and `rounded-[1.5rem]`
2. Two-panel grid: `xl:grid-cols-[minmax(0,1fr)_22rem]` — stacks below xl ✓
3. Agent card grid: `md:grid-cols-2 xl:grid-cols-3` — verify no overflow at each breakpoint
4. Orbital Map grid: Dynamic `gridTemplateColumns` — needs `overflow-x-auto` wrapper and minimum column widths
5. Modals: Must be full-width on smaller viewports
6. Touch targets: All buttons need minimum 44×44px on touch screens

---

### R5: React Query Patterns and Cache Management

**Decision**: Verify all agent-related hooks follow the established query key factory pattern (`agentKeys.all`, `agentKeys.list(id)`, etc.) and configure appropriate `staleTime`. Mutations must use `invalidateQueries` on success and provide `onError` feedback.

**Rationale**: The codebase uses TanStack React Query as the standard data fetching library. Existing patterns (`pipelineKeys`, `appKeys`) establish the key factory convention. The `useAgents.ts` hook already uses React Query but needs verification that staleTime, error handling, and cache invalidation follow best practices per FR-023 and FR-024.

**Alternatives Considered**:

- Moving to SWR — Rejected; TanStack Query is the established pattern with deeper adoption across the codebase
- Using React 19 `use()` with Suspense — Deferred; the project hasn't adopted Suspense boundaries for data fetching yet

**Key Patterns to Verify**:

1. Query key factory exists and follows `[feature].all / .list(id) / .detail(id)` pattern
2. `staleTime` configured appropriately (30s for agent lists, 60s for settings-like data)
3. No raw `useEffect` + `fetch` patterns remain
4. All `useMutation` calls have `onError` that surfaces user-visible feedback (toast or inline)
5. Successful mutations call `invalidateQueries` with the correct keys
6. No duplicate API calls between parent and child components

---

### R6: Test Coverage Strategy

**Decision**: Add hook tests via `renderHook()` for `useAgents`, `useAgentConfig`, and `useAgentTools`. Add component interaction tests for key components. Follow existing test conventions: `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`.

**Rationale**: FR-019 requires hook test coverage and FR-020 requires component interaction tests. Existing tests (AgentsPanel.test.tsx, AddAgentModal.test.tsx, AgentSaveBar.test.tsx, AgentTile.test.tsx) provide the pattern. Edge cases per FR spec: empty state, error state, loading state, rate limit error, long strings, null/missing data.

**Alternatives Considered**:

- Snapshot tests — Rejected per FR specification; all assertions must be explicit and behavioral
- E2E tests with Playwright — Out of scope; the audit focuses on unit and integration testing patterns already established in the codebase

**Test Coverage Matrix**:

| Target | Current Coverage | Required Coverage |
|--------|-----------------|-------------------|
| useAgents hook | None | Happy path, error, loading, rate limit |
| useAgentConfig hook | None | State mutations, dirty tracking, save/discard |
| useAgentTools hook | None | Tool list, add/remove |
| AgentsPanel | ✅ Exists (406 lines) | Verify edge cases covered |
| AddAgentModal | ✅ Exists (102 lines) | Verify interaction coverage |
| AgentCard | None | Click actions, status rendering |
| AgentSaveBar | ✅ Exists (57 lines) | Verify state transitions |
| AgentTile | ✅ Exists (117 lines) | Verify drag interactions |

---

### R7: Code Hygiene and Type Safety

**Decision**: Eliminate all `any` types, type assertions (`as`), dead code, `console.log` statements, and relative imports. Ensure all imports use the `@/` alias. Run ESLint to zero warnings.

**Rationale**: FR-018 mandates zero `any` types and zero type assertions. FR-021 mandates zero ESLint warnings. FR-022 mandates no dead code, no console.log, and `@/` alias imports. These are measurable, binary pass/fail criteria.

**Alternatives Considered**:

- Suppressing warnings with ESLint disable comments — Rejected; the spec explicitly requires zero warnings
- Using `unknown` as a replacement for `any` — Acceptable when combined with type narrowing/guards

**Audit Steps**:

1. Run `npx eslint` on all agent-related files — capture baseline warnings
2. Run `npx tsc --noEmit` — capture baseline type errors
3. Search for `any` types, `as` assertions, `console.log`, and relative imports
4. Fix all findings
5. Re-run lint and type-check to confirm zero issues
