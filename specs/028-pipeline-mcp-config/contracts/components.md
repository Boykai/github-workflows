# Component Contracts: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Feature**: 028-pipeline-mcp-config | **Date**: 2026-03-07

## New Components

### PipelineFlowGraph

**Location**: `frontend/src/components/pipeline/PipelineFlowGraph.tsx`
**Purpose**: Compact SVG visualization of pipeline stage execution order for card display. Renders a horizontal node-edge diagram within a constrained space.

```typescript
interface PipelineFlowGraphProps {
  stages: PipelineStage[];
  width?: number;                        // Default: 200
  height?: number;                       // Default: 48
  className?: string;
}
```

**Behavior**:
- Renders each stage as a rounded rectangle node arranged left-to-right
- Connects nodes with arrow edges (SVG `<line>` or `<path>` elements)
- Each node displays the stage name (truncated) and agent count
- Scales nodes to fit within `width × height` bounds
- Handles edge cases: 0 stages (empty state), 1 stage (single node, no edges), 5+ stages (smaller nodes)
- Memoized with `React.memo` to prevent re-renders when card list updates
- No interactivity (read-only visualization per FR-009)
- Uses Tailwind colors for nodes (e.g., `stroke-border`, `fill-card`) to match theme

---

### PipelineModelDropdown

**Location**: `frontend/src/components/pipeline/PipelineModelDropdown.tsx`
**Purpose**: Pipeline-level model selection dropdown with "Auto" option. Batch-updates all agents in the pipeline when a model is selected.

```typescript
interface PipelineModelDropdownProps {
  models: AIModel[];
  currentOverride: PipelineModelOverride;  // { mode, modelId, modelName }
  onModelChange: (override: PipelineModelOverride) => void;
  disabled?: boolean;
}
```

**Behavior**:
- Renders a dropdown/select at the top of the pipeline builder form
- First option: "Auto" (each agent uses its saved stamp model)
- Remaining options: all available models from `useModels()`, grouped by provider
- When "Auto" is selected: calls `onModelChange({ mode: 'auto', modelId: '', modelName: '' })`
- When a specific model is selected: calls `onModelChange({ mode: 'specific', modelId, modelName })`
- If agents have mixed models (some overridden individually), dropdown displays "Mixed" as the current value
- Uses existing `Select` or `Popover` UI components from `components/ui/`

---

### PresetBadge

**Location**: `frontend/src/components/pipeline/PresetBadge.tsx`
**Purpose**: Visual indicator for system preset pipelines in the Saved Workflows list.

```typescript
interface PresetBadgeProps {
  presetId: string;                      // "spec-kit" | "github-copilot"
  className?: string;
}
```

**Behavior**:
- Renders a small badge with a lock icon and the preset name
- "spec-kit" → "Spec Kit" badge with a blue/purple accent
- "github-copilot" → "GitHub Copilot" badge with a green accent
- Uses existing `Badge` component from `components/ui/badge.tsx`
- Includes `lucide-react` `Lock` icon to indicate non-editable status

---

## Modified Components

### AgentNode (MODIFIED)

**Location**: `frontend/src/components/pipeline/AgentNode.tsx`
**Changes**: Add tool count badge and tool selector trigger.

```typescript
interface AgentNodeProps {
  agentNode: PipelineAgentNode;
  onModelSelect: (modelId: string, modelName: string) => void;
  onRemove: () => void;
  onToolsChange: (toolIds: string[]) => void;  // NEW: Tool selection callback
}
```

**New Behavior**:
- Displays a tool count badge next to the model name (e.g., "3 tools") per FR-003
- Badge shows `agentNode.toolCount` value; clicking it opens `ToolSelectorModal`
- If `toolCount === 0`, shows "+ Tools" as a subtle action link
- `onToolsChange` is called when the `ToolSelectorModal` confirms a selection
- The modal receives `agentNode.toolIds` as initial selection and available tools from `useTools()`

---

### StageCard (MODIFIED)

**Location**: `frontend/src/components/pipeline/StageCard.tsx`
**Changes**: Wire tool selector flyout per agent.

```typescript
interface StageCardProps {
  stage: PipelineStage;
  availableAgents: AvailableAgent[];
  availableTools: McpToolConfig[];           // NEW: For tool selector modal
  onUpdate: (updatedStage: PipelineStage) => void;
  onRemove: () => void;
  onAddAgent: (agentSlug: string) => void;
  onRemoveAgent: (agentNodeId: string) => void;
  onUpdateAgent: (agentNodeId: string, updates: Partial<PipelineAgentNode>) => void;
  isDragging?: boolean;
}
```

**New Behavior**:
- Passes `availableTools` to child `AgentNode` components
- Manages the `ToolSelectorModal` open/close state for the currently selected agent
- When `ToolSelectorModal` confirms, calls `onUpdateAgent(agentNodeId, { toolIds, toolCount })` to update the agent node

---

### PipelineBoard (MODIFIED)

**Location**: `frontend/src/components/pipeline/PipelineBoard.tsx`
**Changes**: Add pipeline-level model dropdown and pass tool data through.

```typescript
interface PipelineBoardProps {
  stages: PipelineStage[];
  availableAgents: AvailableAgent[];
  availableTools: McpToolConfig[];           // NEW: Tool list for agent tool selection
  isEditMode: boolean;
  pipelineName: string;
  pipelineDescription: string;
  modelOverride: PipelineModelOverride;      // NEW: Pipeline-level model state
  validationErrors: PipelineValidationErrors; // NEW: Inline validation state
  onStagesChange: (stages: PipelineStage[]) => void;
  onNameChange: (name: string) => void;
  onDescriptionChange: (description: string) => void;
  onModelOverrideChange: (override: PipelineModelOverride) => void;  // NEW
  onAddStage: () => void;
  onRemoveStage: (stageId: string) => void;
}
```

**New Behavior**:
- Renders `PipelineModelDropdown` at the top of the form, below the pipeline name field
- Passes `availableTools` to `StageCard` components
- When `modelOverride` changes:
  - If `mode === 'specific'`: iterates all agents in all stages and sets their `modelId`/`modelName`
  - If `mode === 'auto'`: iterates all agents and clears `modelId`/`modelName`
  - Calls `onStagesChange()` with the updated stages
- Renders `validationErrors` on the pipeline name input (red border + helper text when `validationErrors.name` is set)
- Clears validation error for a field on first edit after error

---

### PipelineToolbar (MODIFIED)

**Location**: `frontend/src/components/pipeline/PipelineToolbar.tsx`
**Changes**: Save is always enabled; validation errors displayed inline.

```typescript
interface PipelineToolbarProps {
  boardState: 'empty' | 'creating' | 'editing';
  isDirty: boolean;
  isSaving: boolean;
  isPreset: boolean;                         // NEW: Prevents save on presets
  validationErrors: PipelineValidationErrors; // NEW: Validation state
  onNewPipeline: () => void;
  onSave: () => void;
  onSaveAsCopy: () => void;                  // NEW: For preset "Save as Copy"
  onDelete: () => void;
  onDiscard: () => void;
}
```

**New Behavior**:
- "Save" button is ALWAYS enabled when `boardState !== 'empty'` (FR-007)
- Clicking Save calls `onSave()` which triggers validation in the parent hook
- If `isPreset` is true and user has made changes, shows "Save as Copy" instead of "Save"
- `onSaveAsCopy` opens a name input dialog before saving as a new user pipeline
- Validation error count badge shown on Save button when errors exist

---

### SavedWorkflowsList (MODIFIED)

**Location**: `frontend/src/components/pipeline/SavedWorkflowsList.tsx`
**Changes**: Enriched cards with agent details, tool counts, flow graph, and preset badge.

```typescript
interface SavedWorkflowsListProps {
  pipelines: PipelineConfigSummary[];
  activePipelineId: string | null;
  assignedPipelineId: string;                // NEW: Project's assigned pipeline
  onSelect: (pipelineId: string) => void;
  onAssign: (pipelineId: string) => void;    // NEW: Pipeline assignment callback
}
```

**New Behavior**:
- Each card now displays (FR-008):
  - Pipeline name + description
  - `PresetBadge` component (if `isPreset`)
  - `PipelineFlowGraph` component showing stage execution order (FR-009)
  - Expandable/visible list of stages with agents per stage
  - Per-agent: model name and tool count (e.g., "GPT-4o · 3 tools")
  - Total tool count across all agents
- Cards for assigned pipeline show a checkmark/highlight indicator
- Each card has an "Assign to Project" action (calls `onAssign`)
- Preset cards are visually distinguished (FR-012) with the `PresetBadge` and a subtle background color difference

---

### ToolSelectorModal (MODIFIED)

**Location**: `frontend/src/components/tools/ToolSelectorModal.tsx`
**Changes**: Accept pipeline context for scoped selection.

```typescript
interface ToolSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableTools: McpToolConfig[];
  selectedToolIds: string[];                 // Pre-selected tool IDs
  onConfirm: (selectedToolIds: string[]) => void;
  title?: string;                            // NEW: Customizable title (default: "Select Tools")
  context?: 'agent' | 'pipeline';            // NEW: Visual context hint
}
```

**New Behavior**:
- When `context === 'pipeline'`, the modal title shows "Select Tools for {agentName}" (if title is provided)
- Pre-selects tools matching `selectedToolIds` on open
- Emits updated `selectedToolIds` on confirm
- No changes to the core tile grid selection logic — reused as-is

---

## New Hook Extensions

### usePipelineConfig (MODIFIED)

**New Return Fields**:

```typescript
interface UsePipelineConfigReturn {
  // ... existing fields from spec 026 ...

  // NEW: Model override
  modelOverride: PipelineModelOverride;
  setModelOverride: (override: PipelineModelOverride) => void;

  // NEW: Validation
  validationErrors: PipelineValidationErrors;
  validatePipeline: () => boolean;           // Returns true if valid
  clearValidationError: (field: string) => void;

  // NEW: Tool management
  updateAgentTools: (stageId: string, agentNodeId: string, toolIds: string[]) => void;

  // NEW: Preset handling
  isPreset: boolean;
  saveAsCopy: (newName: string) => Promise<void>;

  // NEW: Pipeline assignment
  assignedPipelineId: string;
  assignPipeline: (pipelineId: string) => Promise<void>;
}
```

**New Behavior**:
- `setModelOverride`: When mode changes, batch-updates all agents' model fields. Tracks override state for dropdown display.
- `validatePipeline`: Called on save click. Checks pipeline name, returns false and sets `validationErrors` if invalid.
- `clearValidationError`: Called on field edit to remove error for that field.
- `updateAgentTools`: Updates `tool_ids` and `tool_count` for a specific agent node in the local working copy.
- `saveAsCopy`: Creates a new pipeline from the current working copy with a new name and `is_preset: false`.
- `assignPipeline`: Calls `pipelinesApi.setAssignment()` and invalidates the assignment query.

---

## Modified Page

### AgentsPipelinePage (MODIFIED)

**Location**: `frontend/src/pages/AgentsPipelinePage.tsx`
**Changes**: Compose new components, wire validation and tool data.

**New Behavior**:
- Fetches tool list via `useTools()` hook (already available)
- Passes tools to `PipelineBoard` → `StageCard` → `AgentNode` → `ToolSelectorModal`
- On mount, calls `pipelinesApi.seedPresets(projectId)` to ensure presets exist (idempotent)
- Renders `PipelineModelDropdown` within `PipelineBoard`
- Handles pipeline assignment dropdown (delegates to `usePipelineConfig`)
- Save button always enabled; validation errors shown inline on board
