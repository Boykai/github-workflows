# Quickstart: Audit & Polish the Agents Page

**Feature Branch**: `035-audit-agents-page`
**Date**: 2026-03-11

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and `uv` (for backend, if running locally)
- A GitHub token configured in `.env` for API access

## Setup

```bash
# Clone and checkout
git checkout 035-audit-agents-page

# Install frontend dependencies
cd frontend
npm install

# Verify existing tests pass
npx vitest run
npm run lint
npm run type-check
```

## Development Workflow

### 1. Run the Frontend Dev Server

```bash
cd frontend
npm run dev
```

The Agents page is available at `http://localhost:5173/agents` (or the port shown in terminal).

### 2. Run the Backend (if testing with live data)

```bash
cd backend
uv run --extra dev uvicorn src.main:app --reload --port 8000
```

### 3. Audit Checklist

Work through the audit in priority order matching the spec:

#### P1: Visual Consistency (User Story 1)

- [ ] Compare typography (font family, sizes, weights, line heights) against other pages (Projects, Settings)
- [ ] Verify spacing follows Tailwind's standard scale — no arbitrary magic numbers
- [ ] Check all colors reference design tokens (no hardcoded hex/rgb/hsl in component files)
- [ ] Replace `border-emerald-300/40`, `bg-emerald-50/80` in AgentsPanel with design tokens
- [ ] Replace `text-green-700 dark:text-green-400` in AgentCard with design tokens
- [ ] Replace `bg-blue-100 dark:bg-blue-900/30`, `bg-green-100 dark:bg-green-900/30` in AddAgentPopover with design tokens
- [ ] Verify icons are from Lucide React and consistently sized
- [ ] Test light mode and dark mode switching — all elements render correctly
- [ ] Verify radial gradient overlays, border radii, and shadow values align with design system

#### P1: Bug-Free Page States (User Story 2)

- [ ] Test loading state — skeleton cards in AgentsPanel, CelestialLoader in assignments
- [ ] Test no-project-selected state — ProjectSelectionEmptyState renders correctly
- [ ] Test empty agent catalog — empty state with "Create the first agent" CTA
- [ ] Test populated catalog — featured agents, full grid, pending agents sections
- [ ] Test pending agents — status badges (Pending PR, Pending Deletion) render correctly
- [ ] Test error state — error message with red error box
- [ ] Test no board columns — dashed border "No board columns available" message
- [ ] Add error handling for pipeline query failures (pipelineList, pipelineAssignment)

#### P2: Accessibility (User Story 3)

- [ ] Tab through all interactive elements — verify focus order and visible indicators
- [ ] Apply `.celestial-focus` to all interactive elements missing focus indicators
- [ ] Add `role="dialog"` and `aria-modal="true"` to AgentIconPickerModal (fix `role="presentation"`)
- [ ] Add `role="status" aria-live="polite"` to AgentSaveBar
- [ ] Add `role="region" aria-label` to AgentConfigRow
- [ ] Add `role="list"` to AgentColumnCell, `role="listitem"` to AgentTile
- [ ] Add `aria-expanded` to AddAgentPopover and AgentPresetSelector dropdown triggers
- [ ] Verify focus trap in AddAgentModal, AgentIconPickerModal, BulkModelUpdateDialog
- [ ] Verify focus restoration on modal/editor close
- [ ] Run contrast checker on muted text and reduced-opacity elements
- [ ] Test Escape key on all dropdowns and modals

#### P2: Responsive Layout (User Story 4)

- [ ] Test at 1280px+ (desktop) — two-panel layout side by side
- [ ] Test at 768px–1279px (tablet) — panels stack, card grid adjusts
- [ ] Test at below 768px (mobile) — single column, cards stack, all controls usable
- [ ] Verify Orbital Map grid has `overflow-x-auto` wrapper on small screens
- [ ] Verify touch targets are 44×44px minimum on mobile
- [ ] Test browser resize transitions — no broken intermediate states
- [ ] Test at 200% browser zoom — content readable, no horizontal scroll

#### P2: Interactive Elements (User Story 5)

- [ ] Test Add Agent button → modal open → form validation → save → success
- [ ] Test agent card edit button → inline editor opens → save/discard
- [ ] Test agent card delete button → confirmation dialog → confirm/cancel
- [ ] Test agent catalog search — real-time filtering, no lag
- [ ] Test sort toggle (name/usage)
- [ ] Test icon picker — open modal → select icon → save
- [ ] Test bulk model update — open dialog → select model → review → confirm
- [ ] Test column assignments — add agent via popover → drag reorder → save/discard
- [ ] Test preset selector — apply preset → confirmation → apply
- [ ] Test saved pipelines dropdown — open → select → apply
- [ ] Verify all buttons show hover/focus states and loading spinners during processing

#### P3: Performance & Code Quality (User Story 6)

- [ ] Review component boundaries for single responsibility
- [ ] Profile for unnecessary re-renders with React DevTools
- [ ] Verify no duplicate API requests during normal navigation
- [ ] Verify `staleTime` values are appropriate for agent queries
- [ ] Check `useMemo`/`useCallback` dependency arrays for correctness
- [ ] Verify `useDeferredValue` prevents layout shift during search

### 4. Running Tests

```bash
# All tests
cd frontend && npx vitest run

# Agent-specific tests only
npx vitest run --reporter=verbose AgentSaveBar AgentTile ThemedAgentIcon

# Type checking
npm run type-check

# Linting
npm run lint
```

### 5. Accessibility Scanning

```bash
# jest-axe is available — add axe tests to verify components
# Example in test:
# import { axe, toHaveNoViolations } from 'jest-axe'
# expect(await axe(container)).toHaveNoViolations()
```

## Key Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `pages/AgentsPage.tsx` | 251 | Main page — two-panel layout |
| `agents/AgentsPanel.tsx` | 561 | Catalog container — search, sort, featured, grid |
| `agents/AgentCard.tsx` | 259 | Individual agent card |
| `agents/AddAgentModal.tsx` | 520 | Agent create/edit modal |
| `agents/AgentInlineEditor.tsx` | 261 | Inline editor with imperative ref |
| `agents/AgentIconPickerModal.tsx` | 101 | Icon selection modal |
| `agents/AgentIconCatalog.tsx` | 70 | Icon selection grid |
| `agents/BulkModelUpdateDialog.tsx` | 165 | Bulk model update dialog |
| `agents/ToolsEditor.tsx` | 125 | Tool list editor |
| `board/AgentConfigRow.tsx` | 478 | DnD orchestrator + constellation |
| `board/AgentPresetSelector.tsx` | 536 | Preset buttons + saved pipelines |
| `board/AgentTile.tsx` | 295 | Sortable agent tile |
| `board/AgentColumnCell.tsx` | 168 | Droppable column container |
| `board/AddAgentPopover.tsx` | 295 | Agent add dropdown |
| `board/AgentDragOverlay.tsx` | 69 | Drag preview overlay |
| `board/AgentSaveBar.tsx` | 49 | Save/discard floating bar |

## PR Guidelines

- Reference the spec: `specs/035-audit-agents-page/spec.md`
- Organize commits by user story priority (P1 first, then P2, then P3)
- Each commit should address one component or one category of fix
- Run `npx vitest run` before each PR update to verify no regressions
- Include before/after screenshots for visual changes
