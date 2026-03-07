# Data Model: Pipeline Page — CRUD for Agent Pipeline Configurations

**Feature**: 026-pipeline-crud | **Date**: 2026-03-07

## Backend Entities (Pydantic Models)

### PipelineConfig

The primary entity representing a saved pipeline configuration.

```python
class PipelineConfig(BaseModel):
    id: str                              # UUID, primary key
    project_id: str                      # Scoping to project
    name: str                            # User-defined pipeline name (1–100 chars)
    description: str = ""                # Optional description (0–500 chars)
    stages: list[PipelineStage]          # Ordered list of stages
    created_at: str                      # ISO 8601 datetime
    updated_at: str                      # ISO 8601 datetime
```

**Relationships**: Owns 0..N `PipelineStage` objects (embedded, not normalized).

### PipelineStage

A named step within a pipeline containing agents.

```python
class PipelineStage(BaseModel):
    id: str                              # UUID, unique within pipeline
    name: str                            # User-defined stage name (1–100 chars)
    order: int                           # Display order (0-indexed)
    agents: list[PipelineAgentNode]      # Agents assigned to this stage
```

**Relationships**: Belongs to one `PipelineConfig`. Owns 0..N `PipelineAgentNode` objects.

### PipelineAgentNode

An agent placed within a stage, configured with a specific model.

```python
class PipelineAgentNode(BaseModel):
    id: str                              # UUID, unique within stage
    agent_slug: str                      # Reference to AvailableAgent.slug
    agent_display_name: str = ""         # Cached display name
    model_id: str = ""                   # Selected model identifier
    model_name: str = ""                 # Cached model display name
    config: dict = {}                    # Reserved for future agent-specific config
```

**Relationships**: Belongs to one `PipelineStage`. References an `AvailableAgent` by slug and an `AIModel` by model_id.

### PipelineConfigCreate

Request body for creating a new pipeline.

```python
class PipelineConfigCreate(BaseModel):
    name: str                            # Required, 1–100 chars
    description: str = ""                # Optional, 0–500 chars
    stages: list[PipelineStage] = []     # Initial stages (can be empty)
```

**Validation Rules**:
- `name` must be non-empty (1–100 characters)
- `description` max 500 characters
- Each stage must have a non-empty `name`

### PipelineConfigUpdate

Request body for updating an existing pipeline.

```python
class PipelineConfigUpdate(BaseModel):
    name: str | None = None              # Optional name update
    description: str | None = None       # Optional description update
    stages: list[PipelineStage] | None = None  # Full stage replacement
```

**Validation Rules**: Same as `PipelineConfigCreate` for any provided field.

### AIModel

Represents an available AI model for agent assignment.

```python
class AIModel(BaseModel):
    id: str                              # Unique model identifier (e.g., "gpt-4o")
    name: str                            # Display name (e.g., "GPT-4o")
    provider: str                        # Provider name (e.g., "OpenAI")
    context_window_size: int             # Context window in tokens (e.g., 128000)
    cost_tier: str                       # "economy" | "standard" | "premium"
    capability_category: str = ""        # Optional grouping (e.g., "general", "coding")
```

### PipelineConfigListResponse

Response for the list endpoint.

```python
class PipelineConfigListResponse(BaseModel):
    pipelines: list[PipelineConfigSummary]
    total: int

class PipelineConfigSummary(BaseModel):
    id: str
    name: str
    description: str
    stage_count: int
    agent_count: int
    updated_at: str
```

---

## Frontend Types (TypeScript)

### Pipeline Types

```typescript
interface PipelineConfig {
  id: string;
  projectId: string;
  name: string;
  description: string;
  stages: PipelineStage[];
  createdAt: string;
  updatedAt: string;
}

interface PipelineStage {
  id: string;
  name: string;
  order: number;
  agents: PipelineAgentNode[];
}

interface PipelineAgentNode {
  id: string;
  agentSlug: string;
  agentDisplayName: string;
  modelId: string;
  modelName: string;
  config: Record<string, unknown>;
}

interface PipelineConfigSummary {
  id: string;
  name: string;
  description: string;
  stageCount: number;
  agentCount: number;
  updatedAt: string;
}
```

### Model Types

```typescript
interface AIModel {
  id: string;
  name: string;
  provider: string;
  contextWindowSize: number;
  costTier: 'economy' | 'standard' | 'premium';
  capabilityCategory: string;
}

interface ModelGroup {
  provider: string;
  models: AIModel[];
}
```

### Board State Types

```typescript
interface PipelineBoardState {
  pipeline: PipelineConfig | null;       // Current working copy
  editingPipelineId: string | null;      // null = new mode, string = edit mode
  isDirty: boolean;                      // Unsaved changes exist
  isSaving: boolean;                     // Save operation in progress
  saveError: string | null;              // Last save error message
}
```

---

## Database Schema

### pipeline_configs Table (Migration 013)

```sql
CREATE TABLE IF NOT EXISTS pipeline_configs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    stages TEXT NOT NULL DEFAULT '[]',    -- JSON-serialized PipelineStage[]
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, project_id)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_configs_project_id
    ON pipeline_configs(project_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_configs_updated_at
    ON pipeline_configs(updated_at DESC);
```

**Storage Notes**:
- `stages` column stores the full stage/agent hierarchy as a JSON string, following the pattern used by `workflow_config` in `project_settings` and `tools` in `agent_configs`.
- `UNIQUE(name, project_id)` prevents duplicate pipeline names within a project while allowing same names across projects.
- `updated_at` index supports efficient sorting for the Saved Workflows list (most recently modified first).

---

## State Machines

### Pipeline Board Mode

```
                    ┌──────────────┐
                    │    EMPTY     │  (No pipeline loaded)
                    │  Board blank │
                    └──────┬───────┘
                           │ Click "New Pipeline"
                           ▼
                    ┌──────────────┐
                    │   CREATING   │  (New pipeline, no ID yet)
                    │ editingId=null│
                    └──────┬───────┘
                           │ Click "Save" (first time)
                           ▼
                    ┌──────────────┐
         ┌─────────│   EDITING    │◄────────────┐
         │         │ editingId=id │              │
         │         └──────┬───────┘              │
         │                │                      │
    Click "Delete"   Click "New"          Click saved workflow
    (confirmed)      Pipeline              (from list)
         │                │                      │
         ▼                ▼                      │
    ┌──────────┐   ┌──────────────┐              │
    │  EMPTY   │   │  CREATING    │    ┌─────────┴──────┐
    │          │   │              │    │ LOADING FROM   │
    └──────────┘   └──────────────┘    │ SAVED WORKFLOW │
                                       └────────────────┘
```

### Unsaved Changes Guard

```
User action (load different workflow / navigate away)
    │
    ▼
  isDirty?
    │
    ├─ No  → Proceed with action
    │
    └─ Yes → Show UnsavedChangesDialog
                │
                ├─ "Save"    → Save current → Proceed with action
                ├─ "Discard" → Reset board  → Proceed with action
                └─ "Cancel"  → No-op, stay on current pipeline
```

### Toolbar Button States

| Board State | New Pipeline | Save | Discard | Delete |
|-------------|-------------|------|---------|--------|
| EMPTY (no pipeline) | ✅ Enabled | ❌ Disabled | ❌ Disabled | ❌ Disabled |
| CREATING (new, no changes) | ❌ Disabled | ❌ Disabled | ❌ Disabled | ❌ Disabled |
| CREATING (new, with changes) | ❌ Disabled | ✅ Enabled | ✅ Enabled | ❌ Disabled |
| EDITING (saved, no changes) | ✅ Enabled | ❌ Disabled | ❌ Disabled | ✅ Enabled |
| EDITING (saved, with changes) | ✅ Enabled | ✅ Enabled | ✅ Enabled | ✅ Enabled |

---

## Existing Entities (Unchanged)

The following existing entities are referenced but not modified:

- **AvailableAgent** (`backend/src/models/agent.py`): `slug`, `display_name`, `description`, `source` — used to populate agent selection in pipeline stages.
- **AgentAssignment** (`backend/src/models/agent.py`): `id`, `slug`, `display_name`, `config` — existing pattern that `PipelineAgentNode` extends with `model_id`.
- **WorkflowConfiguration** (`backend/src/models/workflow.py`): Existing workflow config — pipeline configs are a separate, parallel concept.
