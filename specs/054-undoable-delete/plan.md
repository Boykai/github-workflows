# Implementation Plan: Undo/Redo Support for Destructive Actions

**Branch**: `054-undoable-delete` | **Date**: 2026-03-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/054-undoable-delete/spec.md`

## Summary

Replace immediate hard-deletes with a soft-delete + undo toast pattern for all destructive actions (agents, tools, chores, pipelines). On delete confirmation, the item is optimistically hidden from the UI and a sonner toast with an "Undo" button appears. During a ~5-second grace window, clicking "Undo" cancels the pending delete and restores the item from a cached snapshot. If the timer expires, the real API DELETE fires. The implementation introduces a single generic `useUndoableDelete` React hook that wraps existing TanStack Query v5 mutations with setTimeout-based deferred execution, optimistic cache removal/restoration, and cleanup on unmount. No backend changes are required — the mechanism is entirely client-side.

## Technical Context

**Language/Version**: TypeScript ~5.9.0, React ^19.2.0
**Primary Dependencies**: @tanstack/react-query ^5.91.0 (mutations, query cache), sonner ^2.0.7 (toast notifications), React hooks (useState, useRef, useCallback, useEffect)
**Storage**: N/A — client-side only; leverages TanStack Query cache for optimistic state
**Testing**: Vitest ^4.0.18, @testing-library/react, happy-dom
**Target Platform**: Web browser (Vite ^8.0.0 build)
**Project Type**: Web application (frontend-only change)
**Performance Goals**: Toast appears within 200ms of delete confirmation (SC-002); item removal/restoration within 100ms (FR-006, FR-007)
**Constraints**: No backend API changes; client-side grace window only; maximum 3 visible toasts (existing Toaster config); cleanup on unmount to prevent memory leaks (FR-017)
**Scale/Scope**: 4 entity types (agents, tools, chores, pipelines); supports ≥3 concurrent pending deletions (SC-004)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Gate

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 5 prioritized user stories, Given-When-Then scenarios, 19 FRs, 8 SCs |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates; no custom sections required |
| III. Agent-Orchestrated | ✅ PASS | Planning phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Spec does not mandate tests; tests optional per constitution. Hook is testable in isolation if needed |
| V. Simplicity and DRY | ✅ PASS | Single generic hook replaces 4+ duplicate delete patterns; no premature abstraction — hook directly wraps existing mutation + toast patterns |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0

### Post-Phase 1 Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All design artifacts (data-model, contracts, quickstart) trace directly to spec requirements |
| II. Template-Driven | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, contracts/ all follow template structure |
| III. Agent-Orchestrated | ✅ PASS | Phase 0 + Phase 1 complete; outputs are well-defined inputs for Phase 2 (tasks) |
| IV. Test Optionality | ✅ PASS | No tests mandated; hook contract is testable if future task requires it |
| V. Simplicity and DRY | ✅ PASS | Design introduces 1 new file (useUndoableDelete.ts) with a single generic pattern. No new dependencies. No premature abstractions. Cache management reuses existing TanStack Query patterns |

**Post-Design Gate Result**: ✅ ALL PASS — Ready for Phase 2 (tasks)

## Project Structure

### Documentation (this feature)

```text
specs/054-undoable-delete/
├── plan.md              # This file
├── research.md          # Phase 0: Technology research and decisions
├── data-model.md        # Phase 1: Entity model and state transitions
├── quickstart.md        # Phase 1: Implementation quickstart guide
├── contracts/           # Phase 1: Hook interface contracts
│   └── useUndoableDelete.ts   # TypeScript interface specification
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/src/
├── hooks/
│   ├── useUndoableDelete.ts       # NEW — Generic undoable delete hook
│   ├── useAgents.ts               # MODIFY — Wire useDeleteAgent to useUndoableDelete
│   ├── useApps.ts                 # MODIFY — Wire useDeleteApp to useUndoableDelete
│   ├── useChores.ts               # MODIFY — Wire useDeleteChore to useUndoableDelete
│   ├── useTools.ts                # MODIFY — Wire deleteMutation to useUndoableDelete
│   └── usePipelineConfig.ts       # MODIFY — Wire deletePipeline to useUndoableDelete
├── components/
│   └── agents/                    # MODIFY — Update delete handlers to use undoable pattern
│   └── chores/                    # MODIFY — Update delete handlers
│   └── tools/                     # MODIFY — Update delete handlers
│   └── pipeline/                  # MODIFY — Update delete handlers
├── layout/
│   └── AppLayout.tsx              # VERIFY — Toaster config already supports stacking
└── services/
    └── api.ts                     # NO CHANGE — API layer untouched
```

**Structure Decision**: Web application (Option 2). This feature is frontend-only. All changes live under `solune/frontend/src/`. The single new file is `hooks/useUndoableDelete.ts`. Remaining changes are modifications to existing entity hooks to integrate the new undoable pattern. No backend changes required.

## Complexity Tracking

> No constitution violations detected. Table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
