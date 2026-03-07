# Component Contracts: Pipeline Page — CRUD for Agent Pipeline Configurations

**Feature**: 026-pipeline-crud | **Date**: 2026-03-07

## New Components

### PipelineBoard

**Location**: `frontend/src/components/pipeline/PipelineBoard.tsx`
**Purpose**: Main board canvas that renders pipeline stages with agents. Supports drag-and-drop stage reordering via @dnd-kit.

```typescript
interface PipelineBoardProps {
  stages: PipelineStage[];
  availableAgents: AvailableAgent[];
  isEditMode: boolean;
  pipelineName: string;
  onStagesChange: (stages: PipelineStage[]) => void;
  onNameChange: (name: string) => void;
  onAddStage: () => void;
  onRemoveStage: (stageId: string) => void;
}
```

**Behavior**:
- Renders stages horizontally or vertically as cards within a `SortableContext`
- Shows pipeline name as an editable inline field (FR-016)
- Displays "Edit Mode" banner when `isEditMode` is true (FR-014)
- Shows empty state with "Add your first stage" CTA when `stages` is empty (FR-021)
- Handles drag-and-drop stage reordering via @dnd-kit `useSortable` (FR-015)
- Calls `onStagesChange` after reorder completes

---

### PipelineToolbar

**Location**: `frontend/src/components/pipeline/PipelineToolbar.tsx`
**Purpose**: Persistent action bar with Create/Save/Delete/Discard buttons.

```typescript
interface PipelineToolbarProps {
  boardState: 'empty' | 'creating' | 'editing';
  isDirty: boolean;
  isSaving: boolean;
  onNewPipeline: () => void;
  onSave: () => void;
  onDelete: () => void;
  onDiscard: () => void;
}
```

**Behavior**:
- Button enabled/disabled states follow the Toolbar Button States matrix from data-model.md (FR-017)
- "Save" shows loading spinner while `isSaving` is true
- "Delete" triggers `onDelete` which should show confirmation dialog externally
- All buttons use existing `Button` component from `components/ui/button.tsx`

---

### StageCard

**Location**: `frontend/src/components/pipeline/StageCard.tsx`
**Purpose**: Represents a single stage within the pipeline board. Contains agent nodes and supports inline renaming.

```typescript
interface StageCardProps {
  stage: PipelineStage;
  availableAgents: AvailableAgent[];
  onUpdate: (updatedStage: PipelineStage) => void;
  onRemove: () => void;
  onAddAgent: (agentSlug: string) => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  isDragging?: boolean;
}
```

**Behavior**:
- Displays stage name as clickable/editable text (FR-016)
- Click on name → inline text input; Enter or blur confirms rename
- Renders contained `AgentNode` components for each agent in the stage
- Shows "Add Agent" button/popover to assign agents from `availableAgents`
- Provides drag handle for @dnd-kit sortable integration
- Shows visual feedback when `isDragging` (reduced opacity, elevated shadow)
- Uses `Card` component from `components/ui/card.tsx`

---

### AgentNode

**Location**: `frontend/src/components/pipeline/AgentNode.tsx`
**Purpose**: Represents an agent assigned to a stage, showing the agent name and selected model.

```typescript
interface AgentNodeProps {
  agentNode: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
}
```

**Behavior**:
- Displays agent display name and current model selection (FR-010)
- Shows "Select model" prompt if no model selected
- Shows model name and provider badge when model is selected (FR-004 from spec)
- Click on model area opens `ModelSelector` popover
- Remove button (X icon) to detach agent from stage
- Uses compact card layout within the `StageCard`

---

### ModelSelector

**Location**: `frontend/src/components/pipeline/ModelSelector.tsx`
**Purpose**: Reusable model picker popover that displays available models grouped by provider.

```typescript
interface ModelSelectorProps {
  selectedModelId: string | null;
  onSelect: (modelId: string, modelName: string) => void;
  trigger?: React.ReactNode;  // Custom trigger element (defaults to button)
}
```

**Behavior**:
- Renders as a popover/dropdown anchored to the trigger element
- Groups models by `provider` with section headers (FR-008)
- Each model entry shows: name, context window size (formatted), cost tier badge (FR-008)
- "Recent" group pinned at top showing last 3 used models in this session (FR-009)
- Selected model highlighted with checkmark
- Search/filter input at top for quick lookup when model list is long
- Closes on selection, calling `onSelect` with model ID and name
- Fetches models via `useModels` hook (cached)

---

### SavedWorkflowsList

**Location**: `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
**Purpose**: Displays saved pipeline configurations at the bottom of the pipeline page.

```typescript
interface SavedWorkflowsListProps {
  pipelines: PipelineConfigSummary[];
  activePipelineId: string | null;
  isLoading: boolean;
  onSelect: (pipelineId: string) => void;
}
```

**Behavior**:
- Renders pipeline summaries as cards or compact rows (FR-011)
- Each card shows: name, last modified date (relative), stage count, agent count (FR-012)
- Active/selected pipeline highlighted with visual indicator
- Empty state: "No saved pipelines yet. Create your first pipeline above!" with CTA (FR-022)
- Loading skeleton when `isLoading` is true
- Cards are clickable; click triggers `onSelect` (FR-013)
- Uses `Card` component from `components/ui/card.tsx`

---

### UnsavedChangesDialog

**Location**: `frontend/src/components/pipeline/UnsavedChangesDialog.tsx`
**Purpose**: Confirmation dialog shown when user has unsaved changes and attempts a destructive action.

```typescript
interface UnsavedChangesDialogProps {
  isOpen: boolean;
  onSave: () => void;
  onDiscard: () => void;
  onCancel: () => void;
  actionDescription?: string;  // e.g., "load a different workflow"
}
```

**Behavior**:
- Modal overlay with three action buttons: Save, Discard, Cancel (FR-018)
- Clear messaging explaining unsaved changes will be lost
- "Save" triggers save then proceeds with pending action
- "Discard" proceeds without saving
- "Cancel" closes dialog, no action taken
- Uses existing UI components (Button, Card for dialog container)

---

## New Hooks

### usePipelineConfig

**Location**: `frontend/src/hooks/usePipelineConfig.ts`
**Purpose**: Core state management hook for pipeline CRUD operations.

```typescript
interface UsePipelineConfigReturn {
  // State
  boardState: 'empty' | 'creating' | 'editing';
  pipeline: PipelineConfig | null;
  editingPipelineId: string | null;
  isDirty: boolean;
  isSaving: boolean;
  saveError: string | null;

  // Pipeline actions
  newPipeline: () => void;
  loadPipeline: (pipelineId: string) => Promise<void>;
  savePipeline: () => Promise<void>;
  deletePipeline: () => Promise<void>;
  discardChanges: () => void;

  // Board mutations
  setPipelineName: (name: string) => void;
  setPipelineDescription: (description: string) => void;
  addStage: (name?: string) => void;
  removeStage: (stageId: string) => void;
  updateStage: (stageId: string, updates: Partial<PipelineStage>) => void;
  reorderStages: (newOrder: PipelineStage[]) => void;
  addAgentToStage: (stageId: string, agent: AvailableAgent) => void;
  removeAgentFromStage: (stageId: string, agentNodeId: string) => void;
  updateAgentInStage: (stageId: string, agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
}

function usePipelineConfig(projectId: string): UsePipelineConfigReturn;
```

**Implementation Notes**:
- Uses `useState` for local board state (working copy)
- Uses TanStack Query mutations for save/delete operations
- `isDirty` computed by deep comparison of working copy vs. last saved state
- `savePipeline` debounces rapid clicks (FR-020)
- After successful save, invalidates `['pipelines', 'list']` query
- After successful delete, resets board to 'empty' state

### useModels

**Location**: `frontend/src/hooks/useModels.ts`
**Purpose**: Fetches and caches the available AI models list.

```typescript
interface UseModelsReturn {
  models: AIModel[];
  modelsByProvider: ModelGroup[];
  isLoading: boolean;
  error: string | null;
}

function useModels(): UseModelsReturn;
```

**Implementation Notes**:
- Uses TanStack Query with `queryKey: ['models']` and `staleTime: 300_000` (5 min)
- `modelsByProvider` is a derived grouping computed from the flat `models` array
- Follows the pattern of `useAvailableAgents` for data fetching

---

## Modified Components

### AgentsPipelinePage

**Location**: `frontend/src/pages/AgentsPipelinePage.tsx`
**Purpose**: Existing page — modified to compose new pipeline CRUD components.

**Changes**:
- Import and render `PipelineToolbar` at the top
- Import and render `PipelineBoard` as the main content area
- Import and render `SavedWorkflowsList` at the bottom
- Wire `usePipelineConfig` hook for state management
- Add `UnsavedChangesDialog` with `useBlocker` for navigation protection (FR-019)
- Add `window.onbeforeunload` handler when `isDirty` (FR-019)
- Retain existing agent config row and workflow status sections as secondary content

### api.ts

**Location**: `frontend/src/services/api.ts`
**Purpose**: Existing API client — add pipeline and models API methods.

**Changes**:
- Add `pipelines` namespace with `list`, `get`, `create`, `update`, `delete` methods
- Add `models` namespace with `list` method
- Follow existing patterns (e.g., `workflowApi`, `agentApi`)

### types/index.ts

**Location**: `frontend/src/types/index.ts`
**Purpose**: Existing type definitions — add pipeline-related types.

**Changes**:
- Add `PipelineConfig`, `PipelineStage`, `PipelineAgentNode` interfaces
- Add `PipelineConfigSummary`, `PipelineConfigCreate`, `PipelineConfigUpdate` interfaces
- Add `AIModel`, `ModelGroup` interfaces
- Add `PipelineBoardState` interface
