# Implementation Plan: Align Agent Pipeline Columns with Project Board Status & Enable Drag/Drop

**Branch**: `023-pipeline-dragdrop` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/023-pipeline-dragdrop/spec.md`

## Summary

Align the Agent Pipeline columns with the Project Board Status columns and enable cross-column and within-column drag-and-drop for agent title cards. The Agent Pipeline already shares the same column source (`boardData.columns`) as the Project Board, so column alignment is structurally ensured — the work focuses on verifying naming/order consistency and surfacing any drift. The primary engineering effort is extending the existing `@dnd-kit` vertical-only reordering in `AgentColumnCell` to support cross-column drag-and-drop of agent tiles, including visual feedback, keyboard/touch accessibility, optimistic updates with rollback on failure, and persisting changes through the existing `useAgentConfig` → `PUT /workflow/config` → `agent_mappings` pipeline.

## Technical Context

**Language/Version**: TypeScript ~5.8 (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 18, @dnd-kit/core ^6.3.1, @dnd-kit/sortable ^10.0.0, @dnd-kit/modifiers ^9.0.0, @dnd-kit/utilities ^3.2.2, TanStack Query v5, Tailwind CSS
**Storage**: SQLite with WAL mode (aiosqlite) — workflow config stored via `set_workflow_config`
**Testing**: Vitest + React Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Web browser (desktop + mobile), Linux server (Docker)
**Project Type**: Web application (React frontend + FastAPI backend)
**Performance Goals**: Drag-and-drop grab-to-drop under 2 seconds (SC-002, SC-003); revert on failure within 1 second (SC-004)
**Constraints**: Must not break existing vertical reordering; must work across mouse, touch, and keyboard inputs
**Scale/Scope**: ~5 frontend files modified/created, 0-1 backend files modified; existing @dnd-kit already installed

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P5), Given-When-Then acceptance scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | Following canonical plan template structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Following specify → plan → tasks → implement pipeline |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass; new tests for drag-and-drop behavior recommended but optional |
| V. Simplicity and DRY | ✅ PASS | Extending existing @dnd-kit setup rather than adding new library; reusing existing `useAgentConfig` state management and `PUT /workflow/config` persistence path |

**Gate result**: PASS — no violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/023-pipeline-dragdrop/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0 output: @dnd-kit cross-column patterns
├── data-model.md        # Phase 1 output: Entity definitions
├── quickstart.md        # Phase 1 output: Implementation quickstart
├── contracts/           # Phase 1 output: Updated component interfaces
│   └── component-contracts.md
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── board/
│   │       ├── AgentConfigRow.tsx      # Modified: Lift DndContext to row level for cross-column DnD
│   │       ├── AgentColumnCell.tsx      # Modified: Remove per-column DndContext, use Droppable zones
│   │       ├── AgentTile.tsx            # Modified: Add drag overlay styling, keyboard movable mode
│   │       └── AgentDragOverlay.tsx     # New: Drag overlay component for visual preview
│   ├── hooks/
│   │   └── useAgentConfig.ts           # Modified: Add moveAgentToColumn() method
│   └── types/
│       └── index.ts                    # No changes expected (AgentAssignment type sufficient)
└── tests/
    └── (optional drag-and-drop tests)
```

**Structure Decision**: Existing web application layout. This feature primarily modifies the frontend `components/board/` layer and the `useAgentConfig` hook. The backend already supports the required persistence via `PUT /workflow/config` with `agent_mappings`. No new backend endpoints needed.

## Complexity Tracking

> No constitution violations to justify. The implementation extends existing patterns.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Lift DndContext to AgentConfigRow | Required for cross-column drag-and-drop; single DndContext must wrap all droppable zones | Keep per-column DndContext (rejected: cannot detect cross-column drops) |
| Use @dnd-kit (existing) | Already installed and used for vertical reordering; supports cross-container DnD natively | react-beautiful-dnd (rejected: maintenance mode, already have @dnd-kit) |
| Optimistic updates via useAgentConfig | Reuses existing dirty-state tracking and save/discard workflow | Direct API calls per drag (rejected: adds complexity, loses batch-save UX pattern) |
