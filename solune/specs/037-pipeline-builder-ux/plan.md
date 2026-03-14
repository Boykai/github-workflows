# Implementation Plan: Reinvent Agent Pipeline Creation UX

**Branch**: `037-pipeline-builder-ux` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-pipeline-builder-ux/spec.md`

## Summary

Replace the current fixed-column, single-group-per-stage pipeline builder with a kanban-style builder supporting **multiple execution groups per column**, **cross-column drag-and-drop**, and **per-group series/parallel toggle**. The implementation introduces an `ExecutionGroup` entity into the data model (frontend types, backend Pydantic models, and SQLite persistence), refactors the `@dnd-kit` drag-and-drop from stage-scoped `SortableContext` to a board-level `DndContext` enabling cross-column agent movement, and adds backward-compatible migration logic to convert legacy flat-agent-list pipelines into the new group-based format at load time. See [research.md](./research.md) for technology decisions.

## Technical Context

**Language/Version**: TypeScript ~5.9.0 (frontend), Python ≥3.12 (backend)
**Primary Dependencies**: React 19.2, @dnd-kit/core 6.3 + @dnd-kit/sortable 10.0, Tailwind CSS 4.2, Radix UI, TanStack React Query 5.90, FastAPI ≥0.135, Pydantic v2, aiosqlite
**Storage**: SQLite via aiosqlite with JSON-serialised pipeline stages (existing pattern)
**Testing**: Vitest + happy-dom (frontend, ~644 tests), pytest (backend, ~1736 tests)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: All drag-and-drop operations respond in <200ms; pipelines with up to 50 agent nodes render without perceptible lag (SC-006)
**Constraints**: Backward-compatible with all existing saved pipelines; no data loss on migration (SC-004); keyboard-accessible DnD (SC-005)
**Scale/Scope**: Up to 10 stages × 5 groups × 10 agents = 50 agents per pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md contains 6 prioritised user stories with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan produced by `speckit.plan` agent; tasks will be produced by `speckit.tasks` agent |
| IV. Test Optionality with Clarity | ✅ PASS | Tests are included where they exist already (6 pipeline test files); new tests will be added for new components per existing patterns |
| V. Simplicity and DRY | ✅ PASS | Extends existing `PipelineStage` type with a `groups` array rather than introducing a new abstraction layer; migration is a thin load-time transform; no new libraries required |

**Post-Phase 1 Re-check**: ✅ PASS — No complexity violations introduced. The `ExecutionGroup` type is a natural sub-entity of `PipelineStage` and does not add unnecessary abstraction. See Complexity Tracking below.

## Project Structure

### Documentation (this feature)

```text
specs/037-pipeline-builder-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── data-model.md        # Phase 1 output — entity definitions & relationships
├── quickstart.md        # Phase 1 output — developer onboarding guide
├── contracts/           # Phase 1 output — API contract changes
│   └── pipeline-api.md  # Updated REST API contract for group-based pipelines
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── pipeline.py              # Add ExecutionGroup model; update PipelineStage
│   ├── services/
│   │   └── pipelines/
│   │       └── service.py           # Update presets, add migration logic, update normalization
│   ├── api/
│   │   └── pipelines.py             # No route changes (existing CRUD handles new shape)
│   └── migrations/
│       └── 023_pipeline_groups.sql  # Schema note (JSON blob — no DDL needed)
└── tests/
    └── unit/
        └── test_pipeline_groups.py  # Migration + normalization tests

frontend/
├── src/
│   ├── types/
│   │   └── index.ts                 # Add ExecutionGroup type; update PipelineStage
│   ├── components/
│   │   └── pipeline/
│   │       ├── PipelineBoard.tsx     # Lift DndContext to board level for cross-stage DnD
│   │       ├── StageCard.tsx         # Render multiple ExecutionGroups per stage
│   │       ├── ExecutionGroupCard.tsx # NEW — group container with mode toggle
│   │       ├── ParallelStageGroup.tsx # Refactor into ExecutionGroupCard or remove
│   │       └── AgentNode.tsx         # Minor: add drag overlay support
│   ├── hooks/
│   │   ├── usePipelineConfig.ts     # Add group-level mutations
│   │   ├── usePipelineBoardMutations.ts # Add cross-stage move, group CRUD
│   │   └── usePipelineMigration.ts  # NEW — load-time migration hook
│   └── lib/
│       └── pipelineMigration.ts     # NEW — pure migration function
└── src/
    └── __tests__/ or co-located
        ├── ExecutionGroupCard.test.tsx
        ├── PipelineBoard.test.tsx     # Update existing tests
        └── pipelineMigration.test.ts  # Migration function tests
```

**Structure Decision**: Web application (Option 2). The feature modifies existing files in both `backend/` and `frontend/` directories. Two new frontend components (`ExecutionGroupCard`, `usePipelineMigration`) and one new utility (`pipelineMigration.ts`) are introduced. Backend changes are confined to the existing pipeline models and service.

## Complexity Tracking

> No Constitution Check violations. Table included for completeness.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | — | — |
