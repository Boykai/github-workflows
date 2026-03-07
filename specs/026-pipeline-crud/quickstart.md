# Quickstart: Pipeline Page — CRUD for Agent Pipeline Configurations

**Feature**: 026-pipeline-crud | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 026-pipeline-crud
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

## New Files to Create

### Backend

| File | Purpose |
|------|---------|
| `backend/src/migrations/013_pipeline_configs.sql` | New table for pipeline configurations |
| `backend/src/models/pipeline.py` | Pydantic models: PipelineConfig, PipelineStage, PipelineAgentNode, AIModel |
| `backend/src/services/pipelines/__init__.py` | Service re-exports |
| `backend/src/services/pipelines/service.py` | PipelineService: CRUD operations against SQLite |
| `backend/src/api/pipelines.py` | FastAPI router: GET/POST/PUT/DELETE /pipelines, GET /models |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Main board canvas with stage rendering and drag-and-drop |
| `frontend/src/components/pipeline/PipelineToolbar.tsx` | Action bar: New, Save, Delete, Discard |
| `frontend/src/components/pipeline/StageCard.tsx` | Stage container with inline rename and agent list |
| `frontend/src/components/pipeline/AgentNode.tsx` | Agent card with model display and selection |
| `frontend/src/components/pipeline/ModelSelector.tsx` | Reusable model picker popover grouped by provider |
| `frontend/src/components/pipeline/SavedWorkflowsList.tsx` | Saved pipelines list with summary cards |
| `frontend/src/components/pipeline/UnsavedChangesDialog.tsx` | Confirmation dialog for unsaved changes |
| `frontend/src/hooks/usePipelineConfig.ts` | Pipeline CRUD state management hook |
| `frontend/src/hooks/useModels.ts` | Model list fetching and caching hook |

### Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/pages/AgentsPipelinePage.tsx` | Compose new pipeline components, wire hooks |
| `frontend/src/services/api.ts` | Add `pipelines` and `models` API client methods |
| `frontend/src/types/index.ts` | Add pipeline and model TypeScript interfaces |
| `backend/src/main.py` | Register new `pipelines` router |

## Implementation Order

### Phase 1: Backend Foundation

1. **Migration** (`013_pipeline_configs.sql`)
   - Create `pipeline_configs` table with JSON stages column
   - Add indexes on `project_id` and `updated_at`

2. **Models** (`models/pipeline.py`)
   - Define Pydantic models: `PipelineConfig`, `PipelineStage`, `PipelineAgentNode`, `AIModel`
   - Define request/response models: `PipelineConfigCreate`, `PipelineConfigUpdate`, `PipelineConfigListResponse`

3. **Service** (`services/pipelines/service.py`)
   - Implement CRUD methods: `list_pipelines`, `get_pipeline`, `create_pipeline`, `update_pipeline`, `delete_pipeline`
   - Implement `list_models` (static/config-based)
   - Follow pattern from `services/chores/service.py`

4. **API Router** (`api/pipelines.py`)
   - Wire endpoints to service methods
   - Follow pattern from `api/workflow.py` for session dependency injection

### Phase 2: Frontend Types and API

5. **Types** (`types/index.ts`)
   - Add all pipeline and model interfaces

6. **API Client** (`services/api.ts`)
   - Add `pipelinesApi` and `modelsApi` objects with fetch methods

### Phase 3: Frontend Hooks

7. **useModels** hook
   - Fetch and cache models list
   - Derive `modelsByProvider` grouping

8. **usePipelineConfig** hook
   - Pipeline CRUD state management
   - Board state tracking (empty/creating/editing)
   - Dirty state detection and save debouncing

### Phase 4: Frontend Components

9. **ModelSelector** component (reusable, no external dependencies)
10. **AgentNode** component (depends on ModelSelector)
11. **StageCard** component (depends on AgentNode)
12. **PipelineToolbar** component (standalone)
13. **SavedWorkflowsList** component (standalone)
14. **UnsavedChangesDialog** component (standalone)
15. **PipelineBoard** component (depends on StageCard, uses @dnd-kit)

### Phase 5: Integration

16. **AgentsPipelinePage** modifications
    - Compose all new components
    - Wire usePipelineConfig hook
    - Add navigation guards (useBlocker, beforeunload)

## Key Patterns to Follow

### API Client Pattern (from existing `api.ts`)

```typescript
const pipelinesApi = {
  list: async (): Promise<PipelineConfigListResponse> => {
    const response = await fetch(`${API_BASE}/pipelines`, {
      headers: getAuthHeaders(),
    });
    return response.json();
  },
  // ... other methods
};
```

### Hook Pattern (from existing `useAgentConfig.ts`)

```typescript
function usePipelineConfig(projectId: string) {
  const queryClient = useQueryClient();
  const [localState, setLocalState] = useState<PipelineConfig | null>(null);
  const [savedState, setSavedState] = useState<PipelineConfig | null>(null);
  const isDirty = useMemo(() => /* deep compare */, [localState, savedState]);

  const saveMutation = useMutation({
    mutationFn: (config) => pipelinesApi.create(config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines', 'list'] });
    },
  });
  // ...
}
```

### Service Pattern (from existing `services/chores/service.py`)

```python
class PipelineService:
    def __init__(self):
        pass

    async def list_pipelines(self, project_id: str) -> list[PipelineConfig]:
        db = get_db()
        cursor = await db.execute(
            "SELECT * FROM pipeline_configs WHERE project_id = ? ORDER BY updated_at DESC",
            (project_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_pipeline(row) for row in rows]
```

## Verification

After implementation, verify:

1. **Create**: Click "New Pipeline" → name it → add stage → add agent → select model → save → appears in Saved Workflows list
2. **Read**: Refresh page → saved workflows still listed with correct metadata
3. **Update**: Click saved workflow → modify stage → save → changes persist
4. **Delete**: Select saved workflow → click Delete → confirm → removed from list
5. **Model Selection**: Open model picker → models grouped by provider → select → agent card updates
6. **Unsaved Changes**: Make change → click different workflow → confirmation dialog appears
7. **Stage Reordering**: Drag stage to new position → save → order persists
