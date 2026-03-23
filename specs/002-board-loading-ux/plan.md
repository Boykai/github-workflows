# Implementation Plan: Board Loading UX — Skeleton, Stale-While-Revalidate, Refetch Indicator

**Branch**: `002-board-loading-ux` | **Date**: 2026-03-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-board-loading-ux/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Replace the full-screen CelestialLoader spinner with a three-tier loading UX for the project board: (1) use TanStack Query's `keepPreviousData` to instantly display cached board data on revisits (stale-while-revalidate), (2) show a skeleton board layout (5 columns of `BoardColumnSkeleton`) on first load instead of a centered spinner, and (3) add a subtle "Updating…" overlay with opacity dimming during background refetches plus toast notifications on refresh failures. All changes are frontend-only — modifications are scoped to `useProjectBoard.ts`, `ProjectsPage.tsx`, and a new `BoardSkeleton.tsx` component.

## Technical Context

**Language/Version**: TypeScript 5.x (React 18+ with Vite)
**Primary Dependencies**: @tanstack/react-query ^5.91.0, React 18, Tailwind CSS, sonner (toast), Shadcn/ui (Skeleton component)
**Storage**: N/A (client-side TanStack Query cache only — `staleTime: 60s` for board data)
**Testing**: Vitest + React Testing Library (`npm run test`)
**Target Platform**: Web browser (modern evergreen browsers)
**Project Type**: Web application (frontend-only changes for this feature)
**Performance Goals**: Cached board renders in <100ms; skeleton appears within 100ms of navigation; no user interaction blocking during background refresh
**Constraints**: No backend changes; no parallel fetching optimization; no ETag/conditional requests
**Scale/Scope**: Single page (`ProjectsPage.tsx`), one hook (`useProjectBoard.ts`), one new component (`BoardSkeleton.tsx`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` exists with prioritized user stories (P1–P3), Given-When-Then scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase generates well-defined inputs for subsequent task generation |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not mandated by spec; SC-008 requires existing tests pass (no new tests required) |
| V. Simplicity and DRY | ✅ PASS | Reuses existing `BoardColumnSkeleton` and `IssueCardSkeleton` components; uses built-in TanStack Query features (`keepPreviousData`); no new abstractions or patterns introduced |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/002-board-loading-ux/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── component-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       ├── ProjectBoard.tsx          # Existing — grid layout reference
│   │       ├── BoardColumnSkeleton.tsx   # Existing — unused skeleton column
│   │       ├── IssueCardSkeleton.tsx     # Existing — unused skeleton card
│   │       └── BoardSkeleton.tsx         # NEW — skeleton grid wrapper
│   ├── hooks/
│   │   └── useProjectBoard.ts           # MODIFY — add keepPreviousData, expose isPlaceholderData
│   └── pages/
│       └── ProjectsPage.tsx             # MODIFY — skeleton + refetch indicator rendering
```

**Structure Decision**: Frontend-only web application. All changes are within the existing `solune/frontend/src/` directory structure. No new directories needed — the new `BoardSkeleton.tsx` component slots into the existing `components/board/` directory alongside its sibling skeleton components.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
