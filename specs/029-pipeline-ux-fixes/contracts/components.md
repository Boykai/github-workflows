# Component Contracts: Pipeline Page — Fix Model List, Tools Z-Index, Tile Dragging, Agent Clone, and Remove Add Stage

**Feature**: 029-pipeline-ux-fixes | **Date**: 2026-03-07

## Modified Components

### AgentsPipelinePage (MODIFIED)

**Location**: `frontend/src/pages/AgentsPipelinePage.tsx`
**Changes**: Replace `usePipelineModels()` with `useModels()` hook; remove `onAddStage` prop; add `onCloneAgent` prop to `PipelineBoard`.

```typescript
// BEFORE
import { usePipelineModels } from './usePipelineModels'; // local hook
const availableModels = usePipelineModels();

// AFTER
import { useModels } from '@/hooks/useModels';
const { models: availableModels } = useModels();
```

**Removed**: `usePipelineModels()` function definition (lines 27-35).
**Removed**: `onAddStage={() => pipelineConfig.addStage()}` prop (line 220).
**Added**: `onCloneAgent={(stageId, agentNodeId) => pipelineConfig.cloneAgentInStage(stageId, agentNodeId)}` prop.

**FR mapping**: FR-001 (dynamic model list), FR-012 (remove Add Stage), FR-009/FR-010 (clone agent)

---

### PipelineBoard (MODIFIED)

**Location**: `frontend/src/components/pipeline/PipelineBoard.tsx`

**Changes**:
1. Remove `onAddStage` prop and both "Add Stage" buttons (empty state + normal state)
2. Disable stage drag-and-drop (remove `DndContext` + `SortableContext` or set all stages as non-draggable)
3. Pass `onCloneAgent` through to `StageCard`

```typescript
interface PipelineBoardProps {
  // REMOVED
  // onAddStage: () => void;

  // ADDED
  onCloneAgent: (stageId: string, agentNodeId: string) => void;

  // ... all other props unchanged ...
  columnCount: number;
  stages: PipelineStage[];
  availableAgents: AvailableAgent[];
  availableModels: AIModel[];
  isEditMode: boolean;
  pipelineName: string;
  projectId: string;
  modelOverride: PipelineModelOverride;
  validationErrors: PipelineValidationErrors;
  onStagesChange: (stages: PipelineStage[]) => void;
  onNameChange: (name: string) => void;
  onModelOverrideChange: (override: PipelineModelOverride) => void;
  onClearValidationError: (field: string) => void;
  onRemoveStage: (stageId: string) => void;
  onAddAgent: (stageId: string, agentSlug: string) => void;
  onRemoveAgent: (stageId: string, agentNodeId: string) => void;
  onUpdateAgent: (stageId: string, agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  onUpdateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
}
```

**Behavioral changes**:
- Empty state (0 stages): Shows a message indicating stages are derived from board columns, not an "Add Stage" CTA
- Normal state: The "Add Stage" button at the bottom of the board is removed
- Stage cards no longer have drag-and-drop — the `DndContext`/`SortableContext` wrapper can be simplified or removed
- The `handleDragEnd` callback for stage reordering becomes unused (can be removed)

**FR mapping**: FR-006 (disable stage drag), FR-012 (remove Add Stage), FR-009 (pass clone)

---

### StageCard (MODIFIED)

**Location**: `frontend/src/components/pipeline/StageCard.tsx`

**Changes**:
1. Disable `useSortable` by passing `disabled: true`
2. Remove the drag handle (GripVertical icon button)
3. Add a lock icon or visual indicator that the stage is fixed
4. Add `onCloneAgent` prop and pass to `AgentNode`

```typescript
interface StageCardProps {
  stage: PipelineStage;
  availableAgents: AvailableAgent[];
  projectId: string;
  onUpdate: (updatedStage: PipelineStage) => void;
  onRemove: () => void;
  onAddAgent: (agentSlug: string) => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  onCloneAgent: (agentNodeId: string) => void;  // NEW: FR-009
}
```

**Behavioral changes**:
- `useSortable({ id: stage.id, disabled: true })` — prevents drag initiation
- Drag handle button removed — no GripVertical icon, no `cursor-grab` styling
- Optional: Add a `Lock` icon (from lucide-react) in the header to visually indicate the stage is fixed (FR-008)
- Stage still supports inline name editing, agent management (add/remove/update), and tool selection
- The `style` object from `useSortable` (transform/transition) can be simplified since dragging is disabled

**FR mapping**: FR-006 (disable drag), FR-008 (visual differentiation), FR-009 (pass clone)

---

### AgentNode (MODIFIED)

**Location**: `frontend/src/components/pipeline/AgentNode.tsx`

**Changes**:
1. Add `onClone` callback prop
2. Add a "Clone" button (Copy icon from lucide-react) in the agent node UI

```typescript
interface AgentNodeProps {
  agentNode: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
  onToolsClick?: () => void;
  onClone: () => void;  // NEW: FR-009
}
```

**New UI element**: A clone button positioned next to the remove button:

```tsx
<button
  type="button"
  onClick={onClone}
  className="shrink-0 rounded-md p-1 text-muted-foreground/60 transition-colors hover:bg-primary/10 hover:text-primary"
  title="Clone agent"
>
  <Copy className="h-3.5 w-3.5" />
</button>
```

**Visual layout**: The clone button uses the `Copy` icon from lucide-react, styled consistently with the existing remove button. It appears to the left of the remove button in the agent node's action area.

**FR mapping**: FR-009 (clone button), FR-010 (triggers deep copy)

---

### ToolSelectorModal (MODIFIED)

**Location**: `frontend/src/components/tools/ToolSelectorModal.tsx`

**Changes**: Fix z-index stacking by increasing the overlay z-index and ensuring it renders above all pipeline canvas elements.

```typescript
// BEFORE (line 75)
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" ...>

// AFTER
<div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50" ...>
```

**Note**: The `ToolSelectorModal` is rendered inside the `StageCard` component tree. The `StageCard` applies a CSS `transform` from `@dnd-kit/sortable` which creates a new stacking context. Even with `position: fixed` and `z-50`, the modal is constrained within that stacking context. The fix has two parts:

1. Increase z-index to `z-[9999]` (higher than any other element)
2. Wrap the modal render in `createPortal(modal, document.body)` to escape the stacking context entirely

Since the modal is already a full-screen overlay (`fixed inset-0`), portaling to `document.body` doesn't change its visual position — it only changes its DOM position to escape the stacking context.

**FR mapping**: FR-005 (tools module z-index)

---

### usePipelineConfig Hook (MODIFIED)

**Location**: `frontend/src/hooks/usePipelineConfig.ts`

**Changes**:
1. Add `cloneAgentInStage` action
2. Remove `addStage` from the return interface (retain internal implementation if `newPipeline` depends on `buildStage`)

```typescript
interface UsePipelineConfigReturn {
  // REMOVED from return
  // addStage: (name?: string) => void;

  // ADDED
  cloneAgentInStage: (stageId: string, agentNodeId: string) => void;

  // ... all other fields unchanged ...
}
```

**New action implementation**:
```typescript
const cloneAgentInStage = useCallback((stageId: string, agentNodeId: string) => {
  setPipeline((prev) => {
    if (!prev) return null;
    const stage = prev.stages.find((s) => s.id === stageId);
    if (!stage) return prev;
    const sourceAgent = stage.agents.find((a) => a.id === agentNodeId);
    if (!sourceAgent) return prev;

    const clonedAgent: PipelineAgentNode = {
      ...structuredClone(sourceAgent),
      id: crypto.randomUUID(),
    };

    return {
      ...prev,
      stages: prev.stages.map((s) =>
        s.id === stageId
          ? { ...s, agents: [...s.agents, clonedAgent] }
          : s,
      ),
    };
  });
}, []);
```

**FR mapping**: FR-010 (deep copy), FR-011 (independent editing)

## Removed Components/Functions

### usePipelineModels (REMOVED)

**Location**: `frontend/src/pages/AgentsPipelinePage.tsx` (lines 27-35)
**Reason**: This inline hook called `pipelinesApi.listModels()` which fetched a static model list from the backend. Replaced by the existing `useModels()` hook.

### pipelinesApi.listModels (REMOVED)

**Location**: `frontend/src/services/api.ts` (lines 862-864)
**Reason**: Called `GET /pipelines/models/available` which returned a static list. No longer needed since the frontend uses `modelsApi.list()` instead.

## Unchanged Components

The following pipeline components are **not modified** by this feature:

| Component | File | Reason |
|-----------|------|--------|
| `ModelSelector` | `pipeline/ModelSelector.tsx` | Already uses `useModels()` — no changes needed |
| `PipelineModelDropdown` | `pipeline/PipelineModelDropdown.tsx` | Receives `models` via props — data source change is transparent |
| `PipelineToolbar` | `pipeline/PipelineToolbar.tsx` | No changes to toolbar actions |
| `PipelineFlowGraph` | `pipeline/PipelineFlowGraph.tsx` | Read-only visualization — unchanged |
| `SavedWorkflowsList` | `pipeline/SavedWorkflowsList.tsx` | Pipeline list display — unchanged |
| `UnsavedChangesDialog` | `pipeline/UnsavedChangesDialog.tsx` | Dialog behavior — unchanged |
| `PresetBadge` | `pipeline/PresetBadge.tsx` | Preset indicator — unchanged |
