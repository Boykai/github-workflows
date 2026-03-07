# Quickstart: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Feature**: 028-pipeline-mcp-config | **Date**: 2026-03-07

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 028-pipeline-mcp-config
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
| `backend/src/migrations/015_pipeline_mcp_presets.sql` | Add preset columns to pipeline_configs + project pipeline assignment |

### Frontend

| File | Purpose |
|------|---------|
| `frontend/src/components/pipeline/PipelineFlowGraph.tsx` | Compact SVG flow graph for card display |
| `frontend/src/components/pipeline/PipelineModelDropdown.tsx` | Pipeline-level model override dropdown |
| `frontend/src/components/pipeline/PresetBadge.tsx` | Visual badge for preset pipelines |
| `frontend/src/data/preset-pipelines.ts` | Static preset pipeline definitions (Spec Kit, GitHub Copilot) |

### Files to Modify

| File | Changes |
|------|---------|
| `backend/src/models/pipeline.py` | Add `tool_ids`, `tool_count` to PipelineAgentNode; add `is_preset`, `preset_id` to PipelineConfig |
| `backend/src/services/pipelines/service.py` | Add preset seeding, assignment CRUD, tool count computation |
| `backend/src/api/pipelines.py` | Add seed-presets endpoint, assignment endpoints, preset protection on update |
| `backend/src/services/github_projects/service.py` | Inject pipeline metadata on issue creation |
| `frontend/src/types/index.ts` | Add `toolIds`, `toolCount`, `isPreset`, `presetId` to pipeline types; add new types |
| `frontend/src/services/api.ts` | Add `seedPresets`, `getAssignment`, `setAssignment` to pipelinesApi |
| `frontend/src/hooks/usePipelineConfig.ts` | Add model override, validation, tool management, preset handling |
| `frontend/src/components/pipeline/AgentNode.tsx` | Add tool count badge and tool selector trigger |
| `frontend/src/components/pipeline/StageCard.tsx` | Wire tool selector flyout per agent |
| `frontend/src/components/pipeline/PipelineBoard.tsx` | Add model dropdown, validation display, tool data pass-through |
| `frontend/src/components/pipeline/PipelineToolbar.tsx` | Always-enabled Save, Save as Copy for presets |
| `frontend/src/components/pipeline/SavedWorkflowsList.tsx` | Enriched cards with agent details, flow graph, preset badge |
| `frontend/src/components/tools/ToolSelectorModal.tsx` | Accept pipeline context (title, context prop) |
| `frontend/src/pages/AgentsPipelinePage.tsx` | Wire new components, seed presets on mount |

## Implementation Order

### Phase 1: Backend Schema & Models

1. **Migration** (`015_pipeline_mcp_presets.sql`)
   - Add `is_preset` and `preset_id` columns to `pipeline_configs`
   - Add unique index on `(preset_id, project_id)` for non-empty preset_id
   - Add `assigned_pipeline_id` column to `project_settings`

2. **Models** (`models/pipeline.py`)
   - Add `tool_ids: list[str]` and `tool_count: int` to `PipelineAgentNode`
   - Add `is_preset: bool` and `preset_id: str` to `PipelineConfig`
   - Add `total_tool_count`, `is_preset`, `preset_id`, `stages` to `PipelineConfigSummary`
   - Add `ProjectPipelineAssignment` and `ProjectPipelineAssignmentUpdate` models

3. **Service** (`services/pipelines/service.py`)
   - Add `seed_presets(project_id)` method — inserts preset pipelines idempotently
   - Add `get_assignment(project_id)` and `set_assignment(project_id, pipeline_id)` methods
   - Modify `create_pipeline` and `update_pipeline` to compute `tool_count` from `tool_ids`
   - Modify `update_pipeline` to reject updates to preset pipelines
   - Modify `list_pipelines` to return enriched summaries with full stages

4. **API** (`api/pipelines.py`)
   - Add `POST /{project_id}/seed-presets` endpoint
   - Add `GET /{project_id}/assignment` and `PUT /{project_id}/assignment` endpoints
   - Modify `PUT /{project_id}/{pipeline_id}` to return 403 for preset updates

### Phase 2: Frontend Types & API

5. **Types** (`types/index.ts`)
   - Extend `PipelineAgentNode` with `toolIds`, `toolCount`
   - Extend `PipelineConfig` with `isPreset`, `presetId`
   - Extend `PipelineConfigSummary` with `totalToolCount`, `isPreset`, `presetId`, `stages`
   - Add `PipelineModelOverride`, `PipelineValidationErrors`, `ProjectPipelineAssignment`, `PresetPipelineDefinition`

6. **API Client** (`services/api.ts`)
   - Add `seedPresets`, `getAssignment`, `setAssignment` to `pipelinesApi`

7. **Preset Data** (`data/preset-pipelines.ts`)
   - Define "Spec Kit" preset: stages = [Specify, Plan, Tasks, Implement, Analyze] with corresponding agent slugs
   - Define "GitHub Copilot" preset: single stage with GitHub Copilot agent

### Phase 3: Frontend Hooks

8. **usePipelineConfig** hook extensions
   - Add `modelOverride` state and `setModelOverride` handler (batch-updates agents)
   - Add `validationErrors` state and `validatePipeline` / `clearValidationError` methods
   - Add `updateAgentTools` method for pipeline-scoped tool assignment
   - Add `isPreset` check and `saveAsCopy` method
   - Add `assignedPipelineId` and `assignPipeline` from assignment endpoint
   - Modify `savePipeline` to call `validatePipeline` first, block save on errors

### Phase 4: Frontend Components

9. **PipelineFlowGraph** (new, standalone)
   - Horizontal SVG node-edge diagram
   - Responsive sizing, memoized rendering

10. **PresetBadge** (new, standalone)
    - Badge with lock icon for preset identification

11. **PipelineModelDropdown** (new, depends on useModels)
    - "Auto" + model list dropdown
    - "Mixed" state detection

12. **AgentNode** (modified)
    - Add tool count badge display
    - Add tool selector trigger (opens ToolSelectorModal)

13. **StageCard** (modified)
    - Wire ToolSelectorModal per agent
    - Pass availableTools prop

14. **ToolSelectorModal** (modified)
    - Add optional `title` and `context` props

15. **PipelineBoard** (modified)
    - Add PipelineModelDropdown
    - Add validation error display on name field
    - Pass tool data through to stages

16. **PipelineToolbar** (modified)
    - Always-enabled Save
    - Save as Copy for presets

17. **SavedWorkflowsList** (modified)
    - Enriched cards with PipelineFlowGraph, PresetBadge, agent details
    - Pipeline assignment action per card

### Phase 5: Integration

18. **AgentsPipelinePage** (modified)
    - Fetch tools via useTools()
    - Seed presets on mount (idempotent)
    - Wire model override, validation, tool selection
    - Add pipeline assignment dropdown

19. **Issue creation hook** (`github_projects/service.py`)
    - On issue creation, read `project_settings.assigned_pipeline_id`
    - If set, inject pipeline metadata into issue

## Key Patterns to Follow

### Tool Selection in Pipeline Context (reusing ToolSelectorModal)

```typescript
// In StageCard or AgentNode:
const [toolSelectorOpen, setToolSelectorOpen] = useState(false);
const [selectedAgentNodeId, setSelectedAgentNodeId] = useState<string | null>(null);

// Open for specific agent
const handleToolsClick = (agentNodeId: string) => {
  setSelectedAgentNodeId(agentNodeId);
  setToolSelectorOpen(true);
};

// On confirm
const handleToolsConfirm = (toolIds: string[]) => {
  if (selectedAgentNodeId) {
    onUpdateAgent(selectedAgentNodeId, {
      toolIds,
      toolCount: toolIds.length,
    });
  }
  setToolSelectorOpen(false);
};

<ToolSelectorModal
  isOpen={toolSelectorOpen}
  onClose={() => setToolSelectorOpen(false)}
  availableTools={availableTools}
  selectedToolIds={currentAgent?.toolIds ?? []}
  onConfirm={handleToolsConfirm}
  title={`Select Tools for ${currentAgent?.agentDisplayName}`}
  context="pipeline"
/>
```

### Pipeline-Level Model Override Pattern

```typescript
const handleModelOverrideChange = (override: PipelineModelOverride) => {
  setModelOverride(override);

  const updatedStages = stages.map(stage => ({
    ...stage,
    agents: stage.agents.map(agent => ({
      ...agent,
      modelId: override.mode === 'auto' ? '' : override.modelId,
      modelName: override.mode === 'auto' ? '' : override.modelName,
    })),
  }));

  setStages(updatedStages);
};
```

### Inline Validation Pattern

```typescript
const validatePipeline = (): boolean => {
  const errors: PipelineValidationErrors = {};

  if (!pipeline?.name?.trim()) {
    errors.name = 'Pipeline name is required';
  }

  setValidationErrors(errors);
  return Object.keys(errors).length === 0;
};

const handleSave = async () => {
  if (!validatePipeline()) return;
  await saveMutation.mutateAsync(pipeline);
};
```

### Flow Graph SVG Pattern

```typescript
const PipelineFlowGraph: React.FC<PipelineFlowGraphProps> = ({ stages, width = 200, height = 48 }) => {
  const nodeWidth = Math.min(40, (width - 20) / Math.max(stages.length, 1));
  const nodeHeight = 24;
  const gap = (width - nodeWidth * stages.length) / Math.max(stages.length - 1, 1);

  return (
    <svg width={width} height={height} className="overflow-visible">
      {stages.map((stage, i) => {
        const x = i * (nodeWidth + gap);
        const y = (height - nodeHeight) / 2;
        return (
          <g key={stage.id}>
            {i > 0 && (
              <line
                x1={x - gap + 2} y1={height / 2}
                x2={x - 2} y2={height / 2}
                stroke="currentColor" strokeWidth={1.5} opacity={0.4}
              />
            )}
            <rect x={x} y={y} width={nodeWidth} height={nodeHeight} rx={4}
              className="fill-muted stroke-border" strokeWidth={1} />
            <text x={x + nodeWidth / 2} y={height / 2 + 4}
              textAnchor="middle" className="fill-foreground text-[8px]">
              {stage.agents.length}
            </text>
          </g>
        );
      })}
    </svg>
  );
};
```

## Verification

After implementation, verify:

1. **MCP Tool Selection**: Add agent to pipeline → click tool icon → ToolSelectorModal opens → select tools → confirm → agent card shows tool count badge (e.g., "3 tools")
2. **Agent Stamp Isolation**: Create pipeline with model/tool overrides → save → navigate to Agents page → verify source agents unchanged
3. **Pipeline-Level Model Override**: Select "GPT-4o" from pipeline dropdown → all agents show "GPT-4o" → select "Auto" → agents revert to stamp models
4. **Always-Available Save**: Click Save on empty form → pipeline name highlighted red with "Pipeline name is required" → fill in name → click Save → saves successfully
5. **Enhanced Saved Workflows**: Save pipeline with multiple stages/agents → view Saved Workflows → card shows stages, agents, models, tool counts, and flow graph
6. **Preset Pipelines**: Visit Saved Workflows → "Spec Kit" and "GitHub Copilot" presets visible with badge → click preset → loaded in builder → edit → "Save as Copy" prompt
7. **Project Assignment**: Select pipeline from assignment dropdown → create new GitHub Issue → verify issue has pipeline metadata
8. **Flow Graph**: Saved Workflow card shows horizontal node-edge diagram matching stage order
9. **Mixed Model State**: Override pipeline model → individually change one agent's model → pipeline dropdown shows "Mixed"
