# Quickstart: Parallel Agent Layout in Pipelines

**Feature Branch**: `033-parallel-agent-layout`
**Date**: 2026-03-10

## Overview

This guide covers the implementation approach for adding parallel (side-by-side) Agent execution to the pipeline canvas. After reading this, a developer should understand the key changes, where they go, and how to verify them.

## Prerequisites

- Python 3.11+ with `uv` for backend development
- Node.js 18+ with `npm` for frontend development
- Familiarity with the existing pipeline codebase:
  - Backend: `backend/src/models/pipeline.py`, `backend/src/services/pipelines/service.py`
  - Frontend: `frontend/src/components/pipeline/StageCard.tsx`, `frontend/src/components/pipeline/PipelineBoard.tsx`
  - Types: `frontend/src/types/index.ts`

## Step 1: Backend Data Model (estimated: 1h)

Add `execution_mode` field to `PipelineStage` model in `backend/src/models/pipeline.py`:

```python
class PipelineStage(BaseModel):
    """A named step within a pipeline containing agents."""

    id: str
    name: str = Field(..., min_length=1, max_length=100)
    order: int
    agents: list[PipelineAgentNode] = Field(default_factory=list)
    execution_mode: str = Field(default="sequential")  # NEW: "sequential" | "parallel"
```

Add a Pydantic validator to enforce the enum constraint:

```python
from pydantic import field_validator

@field_validator("execution_mode")
@classmethod
def validate_execution_mode(cls, v: str) -> str:
    if v not in ("sequential", "parallel"):
        raise ValueError("execution_mode must be 'sequential' or 'parallel'")
    return v
```

No SQL migration is needed — `stages` is stored as JSON. Verify with:

```bash
cd backend && uv run --extra dev pytest tests/unit/ -x -k "pipeline"
```

## Step 2: Frontend Type Update (estimated: 15min)

Add `execution_mode` to the TypeScript `PipelineStage` interface in `frontend/src/types/index.ts`:

```typescript
export interface PipelineStage {
  id: string;
  name: string;
  order: number;
  agents: PipelineAgentNode[];
  execution_mode?: 'sequential' | 'parallel';  // NEW — defaults to 'sequential'
}
```

Verify with: `cd frontend && npm run type-check`

## Step 3: State Management Hook (estimated: 2h)

Add `toggleStageExecutionMode` and `setStageExecutionMode` mutations to `usePipelineConfig` in `frontend/src/hooks/usePipelineConfig.ts`:

- `setStageExecutionMode(stageId: string, mode: 'sequential' | 'parallel')` — explicitly sets mode
- When adding a second agent to a stage via `addAgentToStage`, auto-prompt or auto-set to `"parallel"` if user used the parallel affordance
- When removing an agent from a parallel stage leaving only 1, auto-revert to `"sequential"`

Verify with: `cd frontend && npm run type-check && npm run test`

## Step 4: Stage Card Parallel Layout (estimated: 4h)

Update `StageCard` in `frontend/src/components/pipeline/StageCard.tsx` to render agents horizontally when `execution_mode === "parallel"`:

1. **Layout direction**: When parallel, use `flex-row` instead of `flex-col` for agent container
2. **Sorting strategy**: Use `rectSortingStrategy` (already imported) for parallel stages; keep `verticalListSortingStrategy` for sequential
3. **Visual container**: Add a border/background wrapper with "Runs in Parallel" label and a `GitBranch` icon when in parallel mode
4. **"Add Parallel Agent" button**: Render a `+` button to the side of agent cards that triggers `onAddAgent` and sets `execution_mode` to `"parallel"`
5. **Connector lines**: No horizontal connectors between parallel agents (they share the stage container)

Visual structure comparison:

```text
Sequential stage:         Parallel stage:
┌─────────────────┐       ┌────────────────────────────────┐
│ Stage: Specify   │       │ Stage: Design & Review          │
│ ┌─────────────┐ │       │ ⑂ Runs in Parallel              │
│ │ Agent A     │ │       │ ┌──────────┐ ┌──────────────┐  │
│ └─────────────┘ │       │ │ Designer │ │ QA           │  │
│ ┌─────────────┐ │       │ └──────────┘ └──────────────┘  │
│ │ Agent B     │ │       │ [+ Add Parallel Agent]          │
│ └─────────────┘ │       └────────────────────────────────┘
│ [+ Add Agent]   │
└─────────────────┘
```

Verify with: `cd frontend && npm run type-check && npm run lint`

Then visually inspect in the browser: navigate to the Pipelines page, create a new pipeline, and add two agents to the same stage using the parallel button.

## Step 5: Pipeline Execution Engine (estimated: 4h)

Extend the pipeline execution logic in `backend/src/services/copilot_polling/pipeline.py` to dispatch parallel-stage agents concurrently:

1. Check stage's `execution_mode` from the pipeline config
2. If `"parallel"`: create all sub-issues simultaneously, assign all agents at once
3. Track per-agent completion using `PipelineState.parallel_agent_statuses`
4. Implement barrier: only advance when all parallel agents report complete
5. Handle partial failure: if any agent fails, mark stage as failed and halt

Add fields to `PipelineState` in `backend/src/services/workflow_orchestrator/models.py`:

```python
execution_mode: str = "sequential"
parallel_agent_statuses: dict[str, str] = field(default_factory=dict)
failed_agents: list[str] = field(default_factory=list)
```

Verify with: `cd backend && uv run --extra dev pytest tests/unit/ -x`

## Step 6: Visual Differentiation and Tooltips (estimated: 2h)

Add distinct visual styling for parallel stages and hover tooltips in `StageCard.tsx` and `AgentNode.tsx`:

1. Parallel stage container gets a dashed border and accent background color
2. "Runs in Parallel" badge with icon in the stage header area
3. Tooltips on agent hover: parallel shows "These agents run at the same time", sequential shows "This agent runs after the previous completes"

Verify by visual inspection in the browser.

## Step 7: Status Indicators (estimated: 2h, P3)

Show per-agent running/completed/failed indicators during pipeline execution in `frontend/src/components/pipeline/AgentNode.tsx`. Add optional `status` prop and render spinner/checkmark/X icons accordingly. This is P3 and can be deferred.

## Build and Test Commands

```bash
# Backend
cd backend
uv run --extra dev ruff check src/        # Lint
uv run --extra dev pytest tests/unit/ -x  # Unit tests

# Frontend
cd frontend
npm run lint                               # ESLint
npm run type-check                         # TypeScript
npm run test                               # Vitest
npm run build                              # Production build
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `backend/src/models/pipeline.py` | Add `execution_mode` to `PipelineStage` |
| `backend/src/services/pipelines/service.py` | Validation, normalization |
| `backend/src/services/copilot_polling/pipeline.py` | Parallel dispatch logic |
| `backend/src/services/workflow_orchestrator/models.py` | `PipelineState` extensions |
| `frontend/src/types/index.ts` | TypeScript type update |
| `frontend/src/hooks/usePipelineConfig.ts` | State mutations |
| `frontend/src/components/pipeline/StageCard.tsx` | Parallel layout rendering |
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Board-level layout |
| `frontend/src/components/pipeline/AgentNode.tsx` | Status indicators |
