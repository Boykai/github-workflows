# Data Model: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Feature**: 030-chat-pipeline-config | **Date**: 2026-03-08

## Backend Entities (Pydantic Models)

### PipelineResolutionResult (New)

Internal result object from pipeline resolution. Not serialized to API — used within `confirm_proposal` to carry resolution metadata.

```python
@dataclass
class PipelineResolutionResult:
    agent_mappings: dict[str, list[AgentAssignment]]  # Resolved status → agents
    source: str           # "pipeline" | "user" | "default"
    pipeline_name: str | None  # Name of the resolved pipeline (None if default/user)
    pipeline_id: str | None    # ID of the resolved pipeline (None if default/user)
```

**Fields**:

- `agent_mappings` — The resolved agent assignments keyed by status name (e.g., `{"Backlog": [...], "In Progress": [...]}`)
- `source` — Indicates which tier in the fallback chain was used: `"pipeline"` (project-level assignment), `"user"` (user-specific mappings), or `"default"` (system defaults)
- `pipeline_name` — Display name of the pipeline, for use in the chat confirmation message. `None` if using user or default mappings.
- `pipeline_id` — UUID of the resolved pipeline. `None` if not from a saved pipeline.

### AITaskProposal (Modified)

Existing response model extended with pipeline metadata.

```python
class AITaskProposal(BaseModel):
    # ... existing fields ...
    proposal_id: str
    proposed_title: str
    proposed_description: str
    status: str  # "pending" | "confirmed" | "rejected" | "expired"
    action_type: str
    created_at: datetime
    
    # NEW FIELDS
    pipeline_name: str | None = None    # Name of the applied Agent Pipeline (after confirm)
    pipeline_source: str | None = None  # "pipeline" | "user" | "default" (after confirm)
```

**Validation**:

- `pipeline_name` is optional; only populated after proposal confirmation.
- `pipeline_source` is optional; only populated after proposal confirmation.

### Existing Models (Unchanged)

The following existing models are referenced but not structurally modified:

- **ProjectPipelineAssignment** (`backend/src/models/pipeline.py`): `project_id`, `pipeline_id` — returned by `GET /pipelines/{projectId}/assignment`. Already exists and is used by the Projects page.
- **PipelineConfig** (`backend/src/models/pipeline.py`): `id`, `project_id`, `name`, `description`, `stages[]` — the full pipeline configuration with stages and agents. Read by `PipelineService.get_pipeline()`.
- **PipelineStage** (`backend/src/models/pipeline.py`): `id`, `name`, `agents[]` — a stage within a pipeline. The `name` field corresponds to a status column name (e.g., "Backlog").
- **PipelineAgentNode** (`backend/src/models/pipeline.py`): `id`, `slug`, `display_name`, `model_id`, `model_name`, `tool_ids[]` — an agent assigned to a stage. Maps to `AgentAssignment`.
- **WorkflowConfiguration** (`backend/src/models/workflow.py`): `project_id`, `agent_mappings`, `copilot_assignee`, etc. — the runtime configuration consumed by the workflow orchestrator.
- **AgentAssignment** (`backend/src/models/workflow.py`): `slug`, `display_name`, `model_id`, `model_name` — a single agent assignment within a status mapping.
- **ProposalConfirmRequest** (`backend/src/models/recommendation.py`): `edited_title`, `edited_description` — unchanged; no pipeline_id field needed (backend resolves pipeline).

---

## Frontend Types (TypeScript)

### useSelectedPipeline Hook Return Type (New)

```typescript
interface SelectedPipelineState {
  pipelineId: string;       // "" = none selected, UUID = specific pipeline
  pipelineName: string;     // "" = none, display name if selected
  isLoading: boolean;       // Query loading state
  hasAssignment: boolean;   // Convenience: pipelineId !== ""
}
```

### AITaskProposal — Frontend (Modified)

```typescript
export interface AITaskProposal {
  // ... existing fields ...
  proposal_id: string;
  proposed_title: string;
  proposed_description: string;
  status: string;
  action_type: string;
  created_at: string;
  
  // NEW FIELDS
  pipeline_name?: string;    // Name of the applied Agent Pipeline (after confirm)
  pipeline_source?: string;  // "pipeline" | "user" | "default" (after confirm)
}
```

### PipelineWarningBannerProps (New)

```typescript
interface PipelineWarningBannerProps {
  projectId: string;
}
```

---

## Database Schema (No Changes)

No new tables or columns are required. The feature reuses existing schema:

### project_settings (Existing)

```sql
CREATE TABLE project_settings (
    github_user_id TEXT NOT NULL,   -- "__workflow__" for project-level, user ID for user-level
    project_id TEXT NOT NULL,
    assigned_pipeline_id TEXT,       -- ← USED: Project-level pipeline assignment (set by Projects page)
    agent_pipeline_mappings TEXT,    -- ← USED: User-level agent mappings JSON (fallback)
    updated_at TEXT,
    PRIMARY KEY (github_user_id, project_id)
);
```

### pipeline_configs (Existing)

```sql
CREATE TABLE pipeline_configs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    stages TEXT NOT NULL,            -- ← USED: JSON array of PipelineStage objects
    is_preset INTEGER DEFAULT 0,
    preset_id TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

---

## State Flow Diagram

```text
┌─────────────────────────────────────┐
│         Projects Page               │
│  ┌─────────────────────────┐        │
│  │ Pipeline Selector       │        │
│  │ <select> dropdown       │──PUT──→│ /pipelines/{projectId}/assignment
│  └─────────────────────────┘        │       ↓
│                                     │ project_settings.assigned_pipeline_id
└─────────────────────────────────────┘       │
                                              │
┌─────────────────────────────────────┐       │
│         Chat Interface              │       │
│  ┌─────────────────────────┐        │       │
│  │ useSelectedPipeline()   │←─GET──←│ /pipelines/{projectId}/assignment
│  │ → PipelineWarningBanner │        │       │
│  └─────────────────────────┘        │       │
│  ┌─────────────────────────┐        │       │
│  │ confirmProposal()       │──POST─→│ /chat/proposals/{id}/confirm
│  │                         │        │       ↓
│  │                         │        │ resolve_project_pipeline_mappings()
│  │                         │        │   ├─ Tier 1: assigned_pipeline_id → pipeline_configs
│  │                         │        │   ├─ Tier 2: load_user_agent_mappings()
│  │                         │        │   └─ Tier 3: DEFAULT_AGENT_MAPPINGS
│  │                         │        │       ↓
│  │ ← pipeline_name in     │←─200──←│ agent_mappings applied to WorkflowConfig
│  │   response              │        │       ↓
│  │                         │        │ create_all_sub_issues()
│  └─────────────────────────┘        │
│  ┌─────────────────────────┐        │
│  │ TaskPreview shows:      │        │
│  │ "Pipeline: Alpha"       │        │
│  └─────────────────────────┘        │
└─────────────────────────────────────┘
```

---

## Entity Relationships

```text
ProjectPipelineAssignment (1) ──→ (0..1) PipelineConfig
       │                                      │
       │ project_id                           │ stages[]
       │                                      │
       ↓                                      ↓
project_settings                    PipelineStage (1..n)
  assigned_pipeline_id ──────→          │
                                        │ agents[]
                                        ↓
                              PipelineAgentNode (0..n)
                                        │
                                        │ slug, model_id
                                        ↓
                              AgentAssignment (converted)
                                        │
                                        ↓
                              WorkflowConfiguration.agent_mappings
                                {"Backlog": [AgentAssignment, ...],
                                 "In Progress": [...]}
```
