# Data Model: Pipeline Page — MCP Tool Selection, Model Override, Flow Graph Cards, Preset Configs & Agent Stamp Isolation

**Feature**: 028-pipeline-mcp-config | **Date**: 2026-03-07

## Backend Entities (Pydantic Models)

### PipelineAgentNode (MODIFIED)

Extended with pipeline-scoped MCP tool selections.

```python
class PipelineAgentNode(BaseModel):
    """An agent placed within a stage, configured with pipeline-scoped model and tool overrides."""

    id: str                              # UUID, unique within stage
    agent_slug: str                      # Reference to AvailableAgent.slug
    agent_display_name: str = ""         # Cached display name
    model_id: str = ""                   # Pipeline-scoped model override (empty = use agent stamp default)
    model_name: str = ""                 # Cached model display name
    tool_ids: list[str] = []             # Pipeline-scoped MCP tool IDs (0-to-many)
    tool_count: int = 0                  # Denormalized count for card display
    config: dict = {}                    # Reserved for future agent-specific config
```

**New Fields**:
- `tool_ids`: List of MCP tool IDs selected for this agent within this pipeline. References `mcp_configurations.id`. Empty list means no tools selected. These are pipeline-scoped and do NOT modify `agent_tool_associations`.
- `tool_count`: Denormalized count of `tool_ids` for efficient card rendering. Computed on save (`len(tool_ids)`).

**Validation Rules**:
- `tool_ids` entries must be valid UUIDs (format check; existence check is advisory — tools may be deleted after pipeline save)
- `tool_count` must equal `len(tool_ids)` (enforced on save, not on input)

### PipelineConfig (MODIFIED)

Extended with preset identification.

```python
class PipelineConfig(BaseModel):
    """Full pipeline configuration record."""

    id: str                              # UUID, primary key
    project_id: str                      # Scoping to project
    name: str                            # User-defined pipeline name (1–100 chars)
    description: str = ""                # Optional description (0–500 chars)
    stages: list[PipelineStage]          # Ordered list of stages (with extended agent nodes)
    is_preset: bool = False              # True for system-seeded presets
    preset_id: str = ""                  # Unique preset identifier (e.g., "spec-kit", "github-copilot")
    created_at: str                      # ISO 8601 datetime
    updated_at: str                      # ISO 8601 datetime
```

**New Fields**:
- `is_preset`: Boolean flag distinguishing system presets from user-created pipelines. Used for visual differentiation (FR-012) and to trigger "Save as Copy" behavior on edit.
- `preset_id`: Stable identifier for preset pipelines. Used for idempotent seeding (`INSERT OR IGNORE` keyed on `preset_id + project_id`). Empty string for user-created pipelines.

### PipelineConfigCreate (MODIFIED)

```python
class PipelineConfigCreate(BaseModel):
    """Request body for creating a new pipeline."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    stages: list[PipelineStage] = Field(default_factory=list)
    # Note: is_preset and preset_id are NOT in the create model.
    # Presets are seeded internally, not created via API.
```

### PipelineConfigSummary (MODIFIED)

Extended for enriched card rendering.

```python
class PipelineConfigSummary(BaseModel):
    """Summary of a pipeline for the list endpoint — enriched with card data."""

    id: str
    name: str
    description: str
    stage_count: int
    agent_count: int
    total_tool_count: int                # Sum of all agents' tool_counts across stages
    is_preset: bool                      # For badge rendering
    preset_id: str                       # For preset identification
    stages: list[PipelineStage]          # Full stages for flow graph + detail rendering
    updated_at: str
```

**New Fields**:
- `total_tool_count`: Aggregate tool count across all agents in all stages. Convenience field for card display.
- `is_preset`, `preset_id`: Passed through for frontend badge rendering.
- `stages`: Full stage data included in summary to enable flow graph rendering and per-agent detail display without a separate detail fetch.

### ProjectPipelineAssignment (NEW)

```python
class ProjectPipelineAssignment(BaseModel):
    """Links a project to a saved pipeline for auto-assignment to new issues."""

    project_id: str                      # Project identifier
    pipeline_id: str                     # ID of the assigned pipeline (or "" for no assignment)
```

### ProjectPipelineAssignmentUpdate (NEW)

```python
class ProjectPipelineAssignmentUpdate(BaseModel):
    """Request body for setting/clearing pipeline assignment."""

    pipeline_id: str = ""                # Empty string to clear assignment
```

---

## Frontend Types (TypeScript)

### Pipeline Types (MODIFIED)

```typescript
// Extended PipelineAgentNode with tool support
interface PipelineAgentNode {
  id: string;
  agentSlug: string;
  agentDisplayName: string;
  modelId: string;
  modelName: string;
  toolIds: string[];           // NEW: Pipeline-scoped MCP tool IDs
  toolCount: number;           // NEW: Denormalized tool count
  config: Record<string, unknown>;
}

// Extended PipelineConfig with preset support
interface PipelineConfig {
  id: string;
  projectId: string;
  name: string;
  description: string;
  stages: PipelineStage[];
  isPreset: boolean;           // NEW: System preset flag
  presetId: string;            // NEW: Preset identifier
  createdAt: string;
  updatedAt: string;
}

// Extended PipelineConfigSummary for enriched cards
interface PipelineConfigSummary {
  id: string;
  name: string;
  description: string;
  stageCount: number;
  agentCount: number;
  totalToolCount: number;      // NEW: Aggregate tool count
  isPreset: boolean;           // NEW
  presetId: string;            // NEW
  stages: PipelineStage[];     // NEW: Full stages for flow graph
  updatedAt: string;
}

// Extended PipelineConfigListResponse
interface PipelineConfigListResponse {
  pipelines: PipelineConfigSummary[];
  total: number;
}
```

### New Types

```typescript
// Pipeline model override state
interface PipelineModelOverride {
  mode: 'auto' | 'specific';
  modelId: string;              // Empty when mode is 'auto'
  modelName: string;            // Empty when mode is 'auto'
}

// Validation errors for inline Save feedback
interface PipelineValidationErrors {
  name?: string;                // e.g., "Pipeline name is required"
  stages?: string;              // e.g., "Pipeline has no agents" (warning level)
  [key: string]: string | undefined;
}

// Project pipeline assignment
interface ProjectPipelineAssignment {
  projectId: string;
  pipelineId: string;           // Empty string = no assignment
}

// Preset pipeline definition (static frontend data)
interface PresetPipelineDefinition {
  presetId: string;             // "spec-kit" | "github-copilot"
  name: string;
  description: string;
  stages: PipelineStage[];
}

// Flow graph node for SVG rendering
interface FlowGraphNode {
  id: string;
  label: string;                // Stage name
  agentCount: number;
  x: number;                    // Computed SVG x position
  y: number;                    // Computed SVG y position
}
```

### PipelineStage, AIModel (UNCHANGED)

```typescript
// These types are unchanged from spec 026
interface PipelineStage {
  id: string;
  name: string;
  order: number;
  agents: PipelineAgentNode[];
}

interface AIModel {
  id: string;
  name: string;
  provider: string;
  contextWindowSize: number;
  costTier: 'economy' | 'standard' | 'premium';
  capabilityCategory: string;
}
```

---

## Database Schema

### Migration 015: Pipeline MCP Presets & Project Assignment

```sql
-- 015_pipeline_mcp_presets.sql
-- Extends pipeline_configs with preset identification and project pipeline assignment.

-- Add preset columns to pipeline_configs
ALTER TABLE pipeline_configs ADD COLUMN is_preset INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pipeline_configs ADD COLUMN preset_id TEXT NOT NULL DEFAULT '';

-- Unique constraint for preset seeding (one preset per project)
CREATE UNIQUE INDEX IF NOT EXISTS idx_pipeline_configs_preset
    ON pipeline_configs(preset_id, project_id)
    WHERE preset_id != '';

-- Add assigned pipeline column to project_settings
ALTER TABLE project_settings ADD COLUMN assigned_pipeline_id TEXT NOT NULL DEFAULT '';
```

**Notes**:
- `is_preset`: SQLite boolean (0/1). `DEFAULT 0` ensures existing pipelines remain non-preset.
- `preset_id`: Empty string for user-created pipelines. Non-empty for system presets. Partial unique index ensures at most one instance of each preset per project.
- `assigned_pipeline_id`: References `pipeline_configs.id`. Empty string means no assignment. Not a foreign key constraint — allows graceful handling if assigned pipeline is deleted.
- The `stages` JSON column already accommodates the extended `PipelineAgentNode` with `tool_ids` and `tool_count` — no column changes needed for tool storage (it's within the JSON).

---

## State Machines

### Pipeline Model Override Flow

```
User opens pipeline builder
    │
    ▼
Pipeline-level model dropdown shows "Auto" (default)
    │
    ├─ User selects specific model (e.g., "GPT-4o")
    │   │
    │   ▼
    │  All agents' modelId/modelName updated to selected model
    │  Dropdown shows "GPT-4o"
    │   │
    │   ├─ User overrides single agent's model → "Mixed" indicator on dropdown
    │   ├─ User selects another model → All agents updated again
    │   └─ User selects "Auto" → All agents' modelId/modelName cleared
    │
    └─ User leaves as "Auto"
        │
        ▼
       Each agent uses its own saved stamp model
       (modelId = "" → runtime resolves from agent_configs)
```

### Tool Selection Flow (Per Agent)

```
User clicks tool icon/badge on agent card
    │
    ▼
ToolSelectorModal opens
├── Shows all available MCP tools (from useTools())
├── Pre-selects tools matching agent's current tool_ids
│
├─ User toggles tool selections (click to select/deselect)
│
├─ User clicks "Confirm"
│   │
│   ▼
│  PipelineAgentNode.tool_ids updated in local working copy
│  Agent card updates tool count badge
│  Pipeline marked as dirty
│
└─ User clicks "Cancel"
    │
    ▼
   No changes; modal closes
```

### Save Validation Flow

```
User clicks "Save" (always enabled)
    │
    ▼
Client-side validation runs:
    │
    ├─ Pipeline name empty?
    │   └─ YES → validationErrors.name = "Pipeline name is required"
    │            Name input shows red border + helper text
    │
    ├─ Pipeline has no agents?
    │   └─ YES → Show warning toast (non-blocking)
    │            Proceed with save anyway (spec edge case)
    │
    └─ All validations pass?
        │
        ├─ YES → Execute save mutation
        │         └─ On success: clear validationErrors, update board state
        │         └─ On error: show API error toast
        │
        └─ NO → Scroll to first error field, focus it
                 Do NOT execute save mutation
```

### Preset Pipeline Interaction Flow

```
User views Saved Workflows list
    │
    ▼
Cards rendered with preset badge for "Spec Kit" / "GitHub Copilot"
    │
    ├─ User clicks preset card
    │   │
    │   ▼
    │  Pipeline loaded into builder (read-only indicator shown)
    │   │
    │   ├─ User makes changes
    │   │   │
    │   │   ▼
    │   │  "Save as Copy" dialog shown (cannot overwrite preset)
    │   │  User enters new name → saved as new user pipeline
    │   │
    │   └─ User views without changes → No save prompt
    │
    └─ User clicks user-created pipeline card
        │
        ▼
       Pipeline loaded in normal edit mode (spec 026 behavior)
```

### Project Pipeline Assignment Flow

```
User navigates to pipeline assignment dropdown
    │
    ▼
Dropdown shows saved pipelines (including presets)
+ "None" option to clear assignment
    │
    ├─ User selects a pipeline
    │   │
    │   ▼
    │  PUT /api/v1/pipelines/{project_id}/assignment
    │  { "pipeline_id": "selected-id" }
    │  Project settings updated
    │
    └─ User selects "None"
        │
        ▼
       PUT /api/v1/pipelines/{project_id}/assignment
       { "pipeline_id": "" }
       Assignment cleared

Subsequently:
New GitHub Issue created in project
    │
    ▼
Backend reads project_settings.assigned_pipeline_id
    │
    ├─ Non-empty → Inject pipeline_config_id as issue metadata
    └─ Empty → No pipeline metadata added to issue
```

---

## Existing Entities (Referenced, Not Modified)

The following existing entities are referenced but their database tables/schemas are NOT modified:

- **Agent / agent_configs** (`backend/src/models/agents.py`, `backend/src/migrations/007_agent_configs.sql`): Source agent stamps. Referenced by `PipelineAgentNode.agent_slug`. Never mutated by pipeline operations (FR-006).
- **McpToolConfig / mcp_configurations** (`backend/src/models/tools.py`, `backend/src/migrations/014_extend_mcp_tools.sql`): MCP tool registry. Referenced by `PipelineAgentNode.tool_ids`. Tool metadata resolved at render time via `useTools()`.
- **AgentToolAssociation / agent_tool_associations** (`backend/src/migrations/014_extend_mcp_tools.sql`): Global agent-tool links on the Agents page. NOT used for pipeline-scoped tool assignments.
- **PipelineStage** (`backend/src/models/pipeline.py`): Unchanged from spec 026. Contains `agents: list[PipelineAgentNode]` which now includes extended fields.
- **AIModel** (`backend/src/models/pipeline.py`): Unchanged from spec 026. Used in the model dropdown.
