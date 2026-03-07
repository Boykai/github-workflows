# Quickstart: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Feature**: 029-pipeline-ux-fixes | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 029-pipeline-ux-fixes
```

## Setup

### Backend

```bash
cd backend
pip install -e ".[dev]"
# Database migrations run automatically on startup
uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Files to Modify

### Backend

| File | Changes |
|------|---------|
| `backend/src/api/pipelines.py` | Remove `GET /models/available` endpoint (lines 38-43) |
| `backend/src/services/pipelines/service.py` | Remove `_AVAILABLE_MODELS` constant (lines 31-80) and `list_models()` static method (lines 512-514) |

### Frontend

| File | Changes |
|------|---------|
| `frontend/src/pages/AgentsPipelinePage.tsx` | Replace `usePipelineModels()` with `useModels()` hook; remove `onAddStage` prop; add `onCloneAgent` prop |
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Remove `onAddStage` prop and both "Add Stage" buttons; remove DnD for stages; add `onCloneAgent` pass-through |
| `frontend/src/components/pipeline/StageCard.tsx` | Disable `useSortable`; remove drag handle; add lock visual; add `onCloneAgent` prop |
| `frontend/src/components/pipeline/AgentNode.tsx` | Add `onClone` prop and Clone button (Copy icon) |
| `frontend/src/components/tools/ToolSelectorModal.tsx` | Increase z-index to `z-[9999]`; wrap render in `createPortal` to `document.body` |
| `frontend/src/hooks/usePipelineConfig.ts` | Add `cloneAgentInStage` action; remove `addStage` from return interface |
| `frontend/src/services/api.ts` | Remove `pipelinesApi.listModels()` method (lines 862-864) |

## Verification

### Fix 1: Dynamic Model List (FR-001–FR-004)

1. Start the backend and frontend
2. Log in with a GitHub account
3. Navigate to the Pipeline page
4. Click "New Pipeline" → observe stages auto-populated from board columns
5. Click "+ Add Agent" on any stage → select an agent
6. Open the "Select model" dropdown on the agent node
7. **Verify**: The dropdown shows models from your GitHub account (fetched dynamically), not the old static list of 6 models
8. **Verify**: The pipeline-level model dropdown (top of board) shows the same dynamic model list

### Fix 2: Tools Z-Index (FR-005)

1. On the pipeline board, add an agent to a stage
2. Click the "+ Tools" button on the agent node
3. **Verify**: The Tool Selector Modal renders fully visible above all other elements
4. **Verify**: No part of the modal is hidden or clipped by stage cards, headers, or overlays
5. Click outside the modal to close it — **Verify**: closes cleanly

### Fix 3: Tile Dragging (FR-006–FR-008)

1. On the pipeline board with multiple stages
2. Hover over a stage card header
3. **Verify**: No grab cursor appears (previously showed grab cursor on drag handle)
4. Attempt to click and drag a stage card
5. **Verify**: The stage does not move — no drag operation starts
6. **Verify**: Stages show a lock icon or fixed visual indicator
7. Agent nodes within stages remain interactive (add, remove, edit model, edit tools)

### Fix 4: Agent Clone (FR-009–FR-011)

1. Add an agent to a stage and configure it (select model, add tools)
2. **Verify**: A "Clone" button (Copy icon) appears on the agent node
3. Click the Clone button
4. **Verify**: A new agent node appears in the same stage with identical configuration
5. Modify the cloned agent's model
6. **Verify**: The original agent's model is unchanged (deep copy independence)
7. Click Clone multiple times rapidly
8. **Verify**: Each clone is independent with a unique ID

### Fix 5: Remove Add Stage (FR-012)

1. Create a new pipeline (stages auto-populated from board columns)
2. **Verify**: No "Add Stage" button appears anywhere on the pipeline board
3. **Verify**: The empty state (if no board columns) shows an informational message, not an "Add Stage" CTA
4. Inspect the entire pipeline creation UI
5. **Verify**: There is no way to manually add a stage

## Running Tests

### Frontend

```bash
cd frontend
npm run lint        # ESLint check
npm run build       # TypeScript compilation check
npm test            # Vitest unit tests
```

### Backend

```bash
cd backend
pytest              # All backend tests
pytest tests/unit/  # Unit tests only
```

## Key Implementation Notes

1. **Model data source**: The `useModels()` hook (from `@/hooks/useModels`) already handles caching (`staleTime: Infinity`), loading states, error handling, and manual refresh. It returns `models: AIModel[]` which is the same type expected by `PipelineBoard` and `PipelineModelDropdown`. The `modelsApi.list()` function maps the response to `{ id, name, provider }` — the `PipelineModelDropdown` only needs these three fields.

2. **ToolSelectorModal portaling**: The modal already uses `fixed inset-0` positioning. Wrapping in `createPortal(modal, document.body)` doesn't change its visual position — it only moves the DOM node out of the `StageCard`'s stacking context. Import `createPortal` from `react-dom` (already available in the bundle).

3. **@dnd-kit disabled**: The `useSortable({ id, disabled: true })` approach keeps the element in the `SortableContext` items list (preserving layout) but prevents it from being dragged or used as a drop target. The `attributes` and `listeners` returned by `useSortable` become no-ops when disabled.

4. **structuredClone**: Available in all target browsers (Chrome 98+, Firefox 94+, Safari 15.4+). No polyfill needed. Creates a true deep copy of plain objects, arrays, and primitives.

5. **generateId vs crypto.randomUUID**: The existing `usePipelineConfig` uses a `generateId()` helper for agent IDs. For the clone, `crypto.randomUUID()` is equivalent — both produce UUIDs. Use whichever is consistent with the existing codebase (if `generateId` wraps `crypto.randomUUID`, use `generateId` for consistency).
