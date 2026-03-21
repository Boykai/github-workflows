# Implementation Plan: Optimistic Updates for Mutations

**Branch**: `001-optimistic-updates-mutations` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-optimistic-updates-mutations/spec.md`

## Summary

Add optimistic UI updates to the 4 mutations currently missing them (`useCreateAgent`, `useDeleteAgent`, `uploadTool` in `useToolsList`, and `useCreateProject`) and fix the paginated cache gap where existing optimistic updates only target flat array caches while the UI has migrated to `useInfiniteQuery`. The approach uses the existing `onMutate`/snapshot/rollback pattern already established in `useChores` and `useApps`, extended with a shared utility for paginated (`InfiniteData`) cache manipulation modelled after `useUndoableDelete.ts`'s `removeEntityFromCache`.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode)  
**Primary Dependencies**: TanStack React Query v5, React 18+, Sonner (toast notifications)  
**Storage**: N/A (client-side cache only — TanStack Query `QueryClient`)  
**Testing**: Vitest + React Testing Library (existing test files: `useAgents.test.tsx`, `useUndoableDelete.test.tsx`)  
**Target Platform**: Web (SPA, Vite-bundled)  
**Project Type**: Web application (frontend-only changes)  
**Performance Goals**: Optimistic updates reflected in UI within 100ms of user action (SC-001)  
**Constraints**: Zero duplicate entries after reconciliation (SC-004); rapid sequential mutations independently reversible (SC-006)  
**Scale/Scope**: 4 hooks modified, 1 shared utility introduced, ~8 existing hooks need paginated cache gap fix

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with prioritized user stories (P1/P2), Given-When-Then scenarios, edge cases |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Single-purpose plan agent producing well-defined outputs |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; existing test files cover hooks under modification |
| V. Simplicity and DRY | ✅ PASS | Shared utility for paginated cache ops avoids per-hook duplication; follows existing patterns |

**Post-Phase 1 Re-check**: ✅ All gates pass. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-optimistic-updates-mutations/
├── plan.md              # This file
├── research.md          # Phase 0 output — codebase research findings
├── data-model.md        # Phase 1 output — entity/cache models
├── quickstart.md        # Phase 1 output — developer quickstart
├── contracts/           # Phase 1 output — API contracts
│   └── optimistic-cache-contract.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/src/
├── hooks/
│   ├── useAgents.ts          # MODIFY: add onMutate to useCreateAgent, useDeleteAgent
│   ├── useTools.ts           # MODIFY: add onMutate + error toast to uploadMutation
│   ├── useProjects.ts        # MODIFY: add onMutate to useCreateProject
│   ├── useChores.ts          # MODIFY: extend onMutate handlers for paginated cache
│   ├── useApps.ts            # MODIFY: extend onMutate handlers for paginated cache
│   ├── useInfiniteList.ts    # READ-ONLY: reference for InfiniteData structure
│   └── useUndoableDelete.ts  # READ-ONLY: reference impl for paginated cache ops
├── services/
│   └── api.ts                # READ-ONLY: API types and endpoints
└── types/
    ├── index.ts              # READ-ONLY: PaginatedResponse, Project, AgentConfig types
    └── apps.ts               # READ-ONLY: CreateProjectRequest/Response types
```

**Structure Decision**: Frontend-only changes within the existing `solune/frontend/src/hooks/` directory. No new directories needed. The feature modifies existing hook files to add `onMutate` handlers and extends them for paginated cache awareness.

## Complexity Tracking

> No constitution violations detected. No complexity justification needed.
