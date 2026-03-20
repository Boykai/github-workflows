# Implementation Plan: Global Search / Command Palette

**Branch**: `053-global-command-palette` | **Date**: 2026-03-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/053-global-command-palette/spec.md`

## Summary

Implement a global search / command palette accessible via Ctrl+K (Cmd+K on macOS) that replaces
the current "focus chat" shortcut. The palette provides instant client-side search across all
navigation pages, agents, pipelines, tools, chores, and apps. It also exposes quick actions
(Toggle Theme, Focus Chat) and supports full keyboard-driven navigation (arrow keys, Enter,
Escape). A clickable UI trigger in the top bar ensures mobile accessibility. The feature is
entirely frontend — no backend changes required. The existing "Focus Chat" functionality is
preserved as a quick action within the palette.

## Technical Context

**Language/Version**: TypeScript 5.9 (frontend only)
**Primary Dependencies**: React 19, React Router v7, TanStack Query v5, Tailwind CSS 4, Lucide React, Radix UI
**Storage**: N/A (client-side search against already-loaded or cached entity data)
**Testing**: Vitest + @testing-library/react (frontend component/hook tests)
**Target Platform**: Modern browsers (desktop + mobile)
**Project Type**: Web application (frontend module within `solune/` monorepo)
**Performance Goals**: Search results returned within 200ms of typing, no UI jank or flicker
**Constraints**: <200ms result update, client-side only, max 15 visible results, no new backend endpoints
**Scale/Scope**: 8 navigation routes, 5 entity types (agents, pipelines, tools, chores, apps), ~5 quick actions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature work began with explicit specification (`spec.md`)
- ✅ Prioritized user stories (P1–P3) with independent testing criteria
- ✅ Given-When-Then acceptance scenarios for each story (15 scenarios across 4 stories)
- ✅ Clear scope boundaries (client-side only, no backend, no full-text search)
- ✅ Edge cases documented (modal conflicts, mobile access, rapid typing)

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ All artifacts follow canonical templates from `.specify/templates/`
- ✅ Plan, research, data-model, contracts, quickstart generated per template structure
- ✅ No custom sections added without justification

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Plan phase produces well-defined outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md)
- ✅ Explicit handoff to subsequent phases (tasks generation, implementation)
- ✅ Single-responsibility: this plan phase does not implement code changes

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests not explicitly mandated in the feature spec — test optionality respected
- ✅ If tests are included during implementation, they follow standard patterns (Vitest + @testing-library/react)
- ✅ No TDD mandate — tests are additive, not blocking

### Principle V: Simplicity and DRY ✅ PASS

- ✅ No new external libraries required — built with existing React, Radix UI, Tailwind, Lucide
- ✅ Reuses existing hooks (useAgentsList, useApps, useChoresList, useToolsList, usePipelineConfig)
- ✅ Reuses existing constants (NAV_ROUTES for navigation items)
- ✅ Simple substring matching — no complex search algorithms
- ✅ Single new component (CommandPalette) + single new hook (useCommandPalette)

## Project Structure

### Documentation (this feature)

```text
specs/053-global-command-palette/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation guide
├── spec.md              # Feature specification (/speckit.specify output)
├── contracts/           # Phase 1 output — component interface contracts
│   └── command-palette-interface.md  # Component props, hook API, event contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/src/
├── components/
│   └── command-palette/
│       └── CommandPalette.tsx       # Main command palette overlay component
├── hooks/
│   ├── useCommandPalette.ts         # Search logic, result aggregation, state management
│   └── useGlobalShortcuts.ts        # Modified: Ctrl+K opens palette instead of focusing chat
├── layout/
│   ├── AppLayout.tsx                # Modified: renders CommandPalette, passes open state
│   └── TopBar.tsx                   # Modified: adds clickable search trigger button
├── constants.ts                     # Existing: NAV_ROUTES used as navigation search source
└── components/ui/
    └── keyboard-shortcut-modal.tsx  # Modified: update Ctrl+K description
```

**Structure Decision**: Web application structure (frontend module only). This feature adds one
new component directory (`components/command-palette/`), one new hook file (`useCommandPalette.ts`),
and modifies four existing files. No new directories or projects are created. All changes are
within the existing `solune/frontend/src/` layout.

## Phases

### Phase A: Foundation — Command Palette Hook and Component (P1 — User Stories 1 & 4)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 1 | Create `useCommandPalette` hook with search state, result aggregation, and keyboard navigation | — | `src/hooks/useCommandPalette.ts` |
| 2 | Create `CommandPalette` component with overlay, search input, categorized results list | Step 1 | `src/components/command-palette/CommandPalette.tsx` |
| 3 | Modify `useGlobalShortcuts` to dispatch palette open event instead of focus-chat event on Ctrl+K | — | `src/hooks/useGlobalShortcuts.ts` |
| 4 | Integrate `CommandPalette` into `AppLayout` — render globally, wire open/close state | Steps 2, 3 | `src/layout/AppLayout.tsx` |
| 5 | Verify: Ctrl+K opens palette, Escape closes, arrow keys navigate results, Enter selects | Steps 1–4 | Manual verification |

**Parallelism**: Steps 1 and 3 can run simultaneously. Step 2 depends on Step 1. Step 4 depends on Steps 2 and 3.

### Phase B: Entity Search — Cross-Entity Result Aggregation (P2 — User Story 2)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 6 | Add agent search source to `useCommandPalette` using `useAgentsList` data | Phase A | `src/hooks/useCommandPalette.ts` |
| 7 | Add pipeline search source using `usePipelineConfig` data | Phase A | `src/hooks/useCommandPalette.ts` |
| 8 | Add tools search source using `useToolsList` data | Phase A | `src/hooks/useCommandPalette.ts` |
| 9 | Add chores search source using `useChoresList` data | Phase A | `src/hooks/useCommandPalette.ts` |
| 10 | Add apps search source using `useApps` data | Phase A | `src/hooks/useCommandPalette.ts` |
| 11 | Display categorized results with category headers and entity-type icons | Steps 6–10 | `src/components/command-palette/CommandPalette.tsx` |
| 12 | Display "No results found" message for empty search results | Step 11 | `src/components/command-palette/CommandPalette.tsx` |
| 13 | Display loading indicator while entity data is loading | Step 11 | `src/components/command-palette/CommandPalette.tsx` |
| 14 | Verify: search across entities returns categorized results, navigation works | Steps 6–13 | Manual verification |

**Parallelism**: Steps 6–10 can all run in parallel. Steps 11–13 can run in parallel after entity sources are wired.

### Phase C: Quick Actions and UI Trigger (P3 — User Story 3 + FR-013)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 15 | Add quick actions to `useCommandPalette`: Toggle Theme, Focus Chat | Phase A | `src/hooks/useCommandPalette.ts` |
| 16 | Add clickable search trigger button to `TopBar` for mobile/non-keyboard access | Phase A | `src/layout/TopBar.tsx` |
| 17 | Update `keyboard-shortcut-modal.tsx` to reflect new Ctrl+K behavior (command palette) | Phase A | `src/components/ui/keyboard-shortcut-modal.tsx` |
| 18 | Verify: quick actions execute correctly, UI trigger opens palette, shortcut modal is accurate | Steps 15–17 | Manual verification |

**Parallelism**: Steps 15, 16, and 17 can all run in parallel.

### Phase D: Polish and Edge Cases (All Stories)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 19 | Prevent palette from opening when a modal dialog is already active (FR-012) | Phase A | `src/hooks/useGlobalShortcuts.ts` |
| 20 | Restore focus to previously focused element on palette close (FR-009) | Phase A | `src/hooks/useCommandPalette.ts` |
| 21 | Cap visible results at 15, add scrolling for overflow | Phase B | `src/components/command-palette/CommandPalette.tsx` |
| 22 | Handle rapid typing with debounce/requestAnimationFrame for smooth result updates | Phase B | `src/hooks/useCommandPalette.ts` |
| 23 | Verify all edge cases from spec: modal conflict, re-open, long queries, loading state, mobile trigger | Steps 19–22 | Manual verification |

**Parallelism**: Steps 19–22 can all run in parallel.

## Constitution Check: Post-Design Re-evaluation

*Re-check after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I: Specification-First Development | ✅ PASS | Full spec with 4 user stories, 15 FRs, 7 SCs. Scenarios cover all major flows. |
| II: Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates. No custom sections. |
| III: Agent-Orchestrated Execution | ✅ PASS | Well-defined phase outputs. Explicit handoffs. Single-responsibility. |
| IV: Test Optionality with Clarity | ✅ PASS | Tests optional per spec. Standard test patterns documented if added. |
| V: Simplicity and DRY | ✅ PASS | One new component, one new hook. Reuses existing data hooks and constants. No new libraries. Simple substring search. |

All five principles remain satisfied after Phase 1 design completion. No violations detected.

## Complexity Tracking

No new abstractions or patterns introduced beyond standard React component + hook architecture.
All changes are additive and follow existing project conventions.

| Item | Justification | Status |
|------|---------------|--------|
| (none) | No complexity justifications needed | N/A |
