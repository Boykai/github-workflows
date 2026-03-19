# Implementation Plan: Solune UX Improvements

**Branch**: `051-solune-ux-improvements` | **Date**: 2026-03-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/051-solune-ux-improvements/spec.md`

## Summary

Ten concrete UX improvements across the Solune frontend (React 19 / TypeScript 5.9 / Tailwind v4)
spanning five categories: mobile responsiveness, perceived performance, interaction consistency,
discoverability, and power-user features. All changes are frontend-only — no backend API changes
or new endpoints required.

The approach follows phased execution ordered by user impact: mobile responsiveness first (P1–P2:
ChatPopup bottom-sheet, sidebar auto-collapse, responsive modals and toolbar), then perceived
performance (P2–P3: skeleton loaders for 4 catalog pages, optimistic updates for drag-drop and
app start/stop), then interaction consistency (P3: standardize all mutation feedback to Sonner
toasts, add empty states for catalog pages), and finally discoverability/power-user features
(P4: board and catalog text search, extended onboarding tour, pipeline undo/redo).

Key technical decisions: use a single 768px breakpoint via `matchMedia` for all responsive
behaviors; reuse the existing `Skeleton` component (pulse/shimmer variants) without modification;
implement optimistic updates via TanStack Query `onMutate`/`onError` rollback pattern; implement
undo/redo as a state snapshot stack in `usePipelineConfig`; client-side search only (no new API).

## Technical Context

**Language/Version**: TypeScript ~5.9.0 (frontend only — no backend changes)
**Primary Dependencies**: React ^19.2.0, TanStack React Query ^5.91.0, Tailwind CSS ^4.2.0, @dnd-kit/core ^6.3.1, Sonner ^2.0.7, Vite ^8.0.0, Radix UI (popover, tooltip), Lucide React ^0.577.0, Zod ^4.3.6, react-hook-form ^7.71.2
**Storage**: N/A (frontend-only changes; existing API endpoints remain unchanged)
**Testing**: Vitest ^4.0.18 (unit, happy-dom), Playwright ^1.58.2 (E2E), Stryker ^9.6.0 (mutation), @testing-library/react ^16.3.2
**Target Platform**: Modern browsers (Chrome, Firefox, Safari, Edge); mobile viewports 320px–1024px+
**Project Type**: Web application (frontend monorepo under `solune/frontend/`)
**Performance Goals**: Drag-drop optimistic update visual feedback <100ms; search filtering <300ms for ≤500 items; undo/redo operations <200ms; skeleton-to-content transition with zero layout shift
**Constraints**: Single 768px breakpoint for all responsive behaviors; undo stack capped at 50 entries; client-side search only (no new API endpoints); no new dependencies — use existing libraries only
**Scale/Scope**: ~130 frontend test files, 10 E2E specs, 11 pages, 15+ hooks, 20+ components modified across 4 phases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature work began with explicit specification (`spec.md`)
- ✅ 11 prioritized user stories (P1–P4) with independent testing criteria
- ✅ Given-When-Then acceptance scenarios for each story (4+ scenarios per story)
- ✅ Clear scope boundaries (optimistic updates scoped to drag-drop/app actions only; undo/redo scoped to pipeline builder only; client-side search only)

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ All artifacts follow canonical templates from `.specify/templates/`
- ✅ Plan, research, data-model, contracts, quickstart generated per template structure
- ✅ No custom sections added without justification

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Plan phase produces well-defined outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md)
- ✅ Explicit handoff to subsequent phases (tasks generation via `/speckit.tasks`, implementation)
- ✅ Single-responsibility: this plan phase does not implement code changes

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests are expected per spec success criteria (SC-009: "Existing automated test suites pass after all improvements")
- ✅ Specific verification methods defined in spec (vitest, playwright, axe-core, manual viewport testing)
- ✅ Test types are appropriate to each target (unit for hooks/logic, component for UI, E2E for integration flows)

### Principle V: Simplicity and DRY ✅ PASS

- ✅ No new dependencies — uses existing libraries (Sonner, @dnd-kit, TanStack Query, Tailwind)
- ✅ Reuses existing `Skeleton` component without modification
- ✅ Single breakpoint (768px) for all responsive behaviors avoids complexity
- ✅ Follows YAGNI — optimistic updates scoped only to high-frequency mutations; undo/redo only for pipeline builder
- ✅ No premature abstraction — each improvement is self-contained

### Constitution Check: Post-Design Re-evaluation ✅ PASS

All five principles remain satisfied after Phase 1 design completion. No violations detected.

- ✅ **Principle I**: Specification-first workflow followed; all design artifacts trace back to spec user stories
- ✅ **Principle II**: All artifacts (plan, research, data-model, contracts, quickstart) follow canonical templates
- ✅ **Principle III**: Plan phase produces well-defined outputs; explicit handoff to `/speckit.tasks` for Phase 2
- ✅ **Principle IV**: Tests expected per spec (SC-009); verification commands documented in contracts
- ✅ **Principle V**: No new dependencies added; two new files (`useMediaQuery.ts`, `EmptyState.tsx`) are justified reusable utilities that avoid duplication across 4+ components; no premature abstractions

The feature operates entirely within the existing frontend project structure and tooling.
No complexity justifications needed.

## Project Structure

### Documentation (this feature)

```text
specs/051-solune-ux-improvements/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — quality contracts
│   ├── responsive-behavior.md       # Mobile breakpoint contracts
│   └── verification-commands.md     # Test and verification reference
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   └── ChatPopup.tsx              # US-1: Bottom-sheet mobile layout
│   │   ├── board/
│   │   │   ├── IssueDetailModal.tsx       # US-3: Full-screen modal on mobile
│   │   │   └── BoardToolbar.tsx           # US-4: Compact mobile toolbar; US-9: Text search
│   │   ├── onboarding/
│   │   │   └── SpotlightTour.tsx          # US-10: Extended tour steps
│   │   ├── common/
│   │   │   └── EmptyState.tsx             # US-8: Reusable empty state component (new)
│   │   └── ui/
│   │       └── skeleton.tsx               # Existing — reused for US-5
│   ├── pages/
│   │   ├── AgentsPage.tsx                 # US-5: Skeleton loaders; US-8: Empty states; US-9: Search
│   │   ├── ToolsPage.tsx                  # US-5: Skeleton loaders; US-8: Empty states; US-9: Search
│   │   ├── ChoresPage.tsx                 # US-5: Skeleton loaders; US-8: Empty states; US-9: Search
│   │   └── AppsPage.tsx                   # US-5: Skeleton loaders; US-7: Toast standardization
│   ├── hooks/
│   │   ├── useBoardDragDrop.ts            # US-6: Optimistic updates
│   │   ├── useApps.ts                     # US-6: Optimistic app start/stop; US-7: Toast standardization
│   │   ├── usePipelineBoardMutations.ts   # US-6: Optimistic pipeline saves
│   │   ├── usePipelineConfig.ts           # US-11: Undo/redo state stack
│   │   ├── useMediaQuery.ts              # New: Shared matchMedia hook for responsive behaviors
│   │   └── useOnboarding.tsx              # US-10: Updated total steps count
│   └── layout/
│       └── Sidebar.tsx                    # US-2: Auto-collapse on mobile
└── src/test/
    └── [test files for each modified component/hook]
```

**Structure Decision**: Web application structure (frontend monorepo under `solune/frontend/`).
All changes are in the existing `src/` directory tree. Two new files: `useMediaQuery.ts` (shared
responsive hook) and `EmptyState.tsx` (reusable empty state component). All other changes modify
existing files.

## Complexity Tracking

> No Constitution Check violations detected. No complexity justifications needed.

All improvements use existing libraries and patterns. The feature operates entirely within the
existing frontend project structure with no new abstractions beyond a shared `useMediaQuery` hook
(replacing duplicated `matchMedia` logic) and a reusable `EmptyState` component (replacing
per-page empty state markup).
