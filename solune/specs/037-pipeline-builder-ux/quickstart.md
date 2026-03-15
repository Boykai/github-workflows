# Quickstart: Reinvent Agent Pipeline Creation UX

**Feature Branch**: `037-pipeline-builder-ux`
**Date**: 2026-03-12

## Prerequisites

- Node.js (for frontend)
- Python ≥3.12 (for backend)
- Git

## Setup

```bash
# Clone and checkout feature branch
git checkout 037-pipeline-builder-ux

# Backend setup
cd backend
pip install -e ".[dev]"

# Frontend setup
cd ../frontend
npm install
```

## Running Locally

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn src.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

## Running Tests

```bash
# Backend tests (pipeline-related)
cd backend
python -m pytest tests/unit/test_pipeline_groups.py -v

# Frontend tests (pipeline-related)
cd frontend
npx vitest run src/components/pipeline/
npx vitest run src/hooks/usePipelineConfig.test.tsx
npx vitest run src/lib/pipelineMigration.test.ts

# Full test suites
cd backend && python -m pytest tests/unit/ -v
cd frontend && npx vitest run
```

## Key Files to Understand

### Data Model

| File | What It Does |
|------|-------------|
| `frontend/src/types/index.ts` | TypeScript type definitions — `ExecutionGroup`, `PipelineStage`, `PipelineAgentNode` |
| `backend/src/models/pipeline.py` | Python Pydantic models — `ExecutionGroup`, `PipelineStage` |

### Frontend Components

| File | What It Does |
|------|-------------|
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Board-level canvas; hosts the top-level `DndContext` for cross-stage drag-and-drop |
| `frontend/src/components/pipeline/StageCard.tsx` | Stage column; renders execution groups vertically |
| `frontend/src/components/pipeline/ExecutionGroupCard.tsx` | **(NEW)** Group container with mode toggle and agent list |
| `frontend/src/components/pipeline/AgentNode.tsx` | Individual agent card within a group |
| `frontend/src/components/pipeline/ParallelStageGroup.tsx` | **Refactored/replaced** by `ExecutionGroupCard` |

### State Management

| File | What It Does |
|------|-------------|
| `frontend/src/hooks/usePipelineConfig.ts` | Pipeline state and persistence; group-level mutations added here |
| `frontend/src/hooks/usePipelineBoardMutations.ts` | Board-level mutation callbacks for stages, groups, and agents |
| `frontend/src/hooks/usePipelineMigration.ts` | **(NEW)** Hook that applies migration at load time |

### Migration

| File | What It Does |
|------|-------------|
| `frontend/src/lib/pipelineMigration.ts` | **(NEW)** Pure function to convert legacy pipelines to group format |

### Backend

| File | What It Does |
|------|-------------|
| `backend/src/services/pipelines/service.py` | Pipeline CRUD service; normalization and preset definitions |
| `backend/src/api/pipelines.py` | REST API routes (no changes needed) |

## Architecture Overview

```
User interacts with PipelineBoard
        │
        ├── DndContext (board-level, handles cross-stage DnD)
        │     ├── StageCard (one per stage column)
        │     │     ├── ExecutionGroupCard (one per group)
        │     │     │     ├── SortableContext (scoped to group's agents)
        │     │     │     │     └── AgentNode (draggable agent cards)
        │     │     │     └── Mode Toggle (series ↔ parallel)
        │     │     └── "Add Group" button
        │     └── DragOverlay (visual clone of dragged agent)
        │
        ├── usePipelineBoardMutations (state updates)
        │     ├── addGroupToStage()
        │     ├── removeGroupFromStage()
        │     ├── reorderGroupsInStage()
        │     ├── setGroupExecutionMode()
        │     ├── moveAgentBetweenGroups()
        │     └── ... existing stage/agent mutations
        │
        └── usePipelineConfig (persistence)
              ├── loadPipeline() → migratePipelineToGroupFormat()
              └── savePipeline() → API POST/PUT
```

## Drag-and-Drop Flow

1. **User picks up agent card** → `onDragStart` stores active agent ID and source group/stage
2. **User drags over a group** → `onDragOver` fires; if target group differs from source, agent ID is moved between SortableContext items arrays for live visual feedback
3. **User drops agent** → `onDragEnd` commits the move via `moveAgentBetweenGroups()` or `reorderAgentsInGroup()` mutation
4. **User drops outside valid target** → `onDragCancel` reverts to pre-drag state

## Common Development Tasks

### Add a new execution group to a stage
1. Click "Add Group" button below the last group in a stage column
2. A new group appears with default mode "sequential" and an empty agent slot
3. Drag agents into the group or use the agent picker

### Toggle group execution mode
1. Click the series/parallel toggle icon on the group header
2. Layout switches between vertical list (series) and side-by-side grid (parallel)

### Move an agent across stages
1. Pick up the agent card from any group
2. Drag it to a group in another stage column
3. Drop it — the agent appears in the target group with its model and tool settings preserved

### Test backward compatibility
1. Create a pipeline using the old UI (or craft a JSON payload without `groups`)
2. Load it in the new builder
3. Verify: each stage shows one group with the original agents and execution mode

## Linting and Type Checking

```bash
# Frontend
cd frontend
npm run type-check    # TypeScript strict checks
npm run lint          # ESLint

# Backend
cd backend
python -m ruff check src/
```
