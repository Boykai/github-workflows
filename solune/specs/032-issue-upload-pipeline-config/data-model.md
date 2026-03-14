# Data Model: Projects Page — Upload GitHub Parent Issue Description & Select Agent Pipeline Config

**Feature**: 032-issue-upload-pipeline-config | **Date**: 2026-03-10

## Backend Entities (Pydantic Models)

### PipelineIssueLaunchRequest (Existing)

Request model for the `POST /pipelines/{projectId}/launch` endpoint. Already exists in `backend/src/models/pipeline.py`. No modifications needed.

```python
class PipelineIssueLaunchRequest(BaseModel):
    """Request for launching pipeline with issue description."""
    issue_description: str = Field(..., min_length=1, max_length=65_536)
    pipeline_id: str = Field(..., min_length=1)
```

**Fields**:

- `issue_description` — The full text of the GitHub Parent Issue description. Min 1 character (non-empty after trimming), max 65,536 characters. Provided by the user via paste or file upload.
- `pipeline_id` — UUID of the selected Agent Pipeline Config. Must match an existing `pipeline_configs.id` for the project.

**Validation**:

- `issue_description`: Pydantic enforces `min_length=1` and `max_length=65_536`. Backend additionally normalizes whitespace via `_normalize_issue_description()` and validates against `GITHUB_ISSUE_BODY_MAX_LENGTH` after appending agent tracking metadata.
- `pipeline_id`: Pydantic enforces `min_length=1`. Backend fetches the pipeline from `pipeline_configs` and returns `404 NotFoundError` if not found.

### WorkflowResult (Existing)

Response model returned by the launch endpoint. Already exists in `backend/src/models/workflow.py`. No modifications needed.

```python
class WorkflowResult(BaseModel):
    """Result of a workflow execution."""
    success: bool
    issue_id: str | None = None
    issue_number: int | None = None
    issue_url: str | None = None
    project_item_id: str | None = None
    current_status: str | None = None
    message: str = ""
```

**Fields**:

- `success` — Whether the pipeline launch completed successfully.
- `issue_id` — GitHub node ID of the created parent issue.
- `issue_number` — GitHub issue number (e.g., `#42`).
- `issue_url` — Full URL to the created GitHub issue.
- `project_item_id` — GitHub project board item ID.
- `current_status` — Board column status (e.g., "Backlog").
- `message` — Human-readable result message.

### PipelineConfig (Existing)

The full pipeline configuration with stages and agents. Already exists in `backend/src/models/pipeline.py`. Referenced by the launch endpoint but not modified.

```python
class PipelineConfig(BaseModel):
    id: str
    project_id: str
    name: str
    description: str = ""
    stages: list[PipelineStage] = Field(default_factory=list)
    is_preset: bool = False
    preset_id: str = ""
    blocking: bool = False
    created_at: str
    updated_at: str
```

### PipelineConfigSummary (Existing)

Lightweight pipeline summary returned by the list endpoint, used to populate the dropdown. Already exists in `backend/src/models/pipeline.py`.

```python
class PipelineConfigSummary(BaseModel):
    id: str
    name: str
    description: str
    stage_count: int
    agent_count: int
    total_tool_count: int
    is_preset: bool
    preset_id: str
    stages: list[PipelineStage]
    blocking: bool
    updated_at: str
```

### ProjectPipelineAssignment (Existing)

Links a project to its assigned pipeline. Used internally by the launch endpoint to set the assignment. Already exists in `backend/src/models/pipeline.py`.

```python
class ProjectPipelineAssignment(BaseModel):
    project_id: str
    pipeline_id: str = ""
    blocking_override: bool | None = None
```

---

## Frontend Types (TypeScript)

### PipelineIssueLaunchRequest — Frontend (Existing)

Request payload type for `pipelinesApi.launch()`. Already exists in `frontend/src/types/index.ts`.

```typescript
export interface PipelineIssueLaunchRequest {
  issue_description: string;
  pipeline_id: string;
}
```

### WorkflowResult — Frontend (Existing)

Response type from `pipelinesApi.launch()`. Already exists in `frontend/src/types/index.ts`.

```typescript
export interface WorkflowResult {
  success: boolean;
  issue_id?: string;
  issue_number?: number;
  issue_url?: string;
  project_item_id?: string;
  current_status?: string;
  message: string;
}
```

### PipelineConfigSummary — Frontend (Existing)

Pipeline summary type used to populate the dropdown. Already exists in `frontend/src/types/index.ts`.

```typescript
export interface PipelineConfigSummary {
  id: string;
  name: string;
  description: string;
  stage_count: number;
  agent_count: number;
  total_tool_count: number;
  is_preset: boolean;
  preset_id: string;
  stages: PipelineStage[];
  blocking: boolean;
  updated_at: string;
}
```

### ProjectIssueLaunchPanelProps (New)

Component props interface for the new `ProjectIssueLaunchPanel` component.

```typescript
interface ProjectIssueLaunchPanelProps {
  projectId: string;
  projectName?: string;
  pipelines: PipelineConfigSummary[];
  isLoadingPipelines: boolean;
  pipelinesError?: string | null;
  onRetryPipelines: () => void;
  onLaunched?: (result: WorkflowResult) => void;
}
```

**Fields**:

- `projectId` — The selected project ID (required for the launch API call).
- `projectName` — Optional project display name (shown in success message context).
- `pipelines` — Array of available pipeline configs for the dropdown. Passed from parent's React Query data.
- `isLoadingPipelines` — Whether the pipeline list is still loading (shows loading state in dropdown).
- `pipelinesError` — Error message if pipeline fetch failed (shows error state with retry).
- `onRetryPipelines` — Callback to retry fetching pipelines (wired to React Query refetch).
- `onLaunched` — Callback invoked after successful launch (parent uses this to refresh the board).

### FormErrors (New, Internal)

Internal type for tracking per-field validation errors.

```typescript
interface FormErrors {
  issueDescription?: string;
  pipelineId?: string;
  file?: string;
}
```

---

## Database Schema (No Changes)

No new tables or columns are required. The feature reuses existing schema:

### pipeline_configs (Existing)

```sql
CREATE TABLE pipeline_configs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    stages TEXT NOT NULL,        -- JSON array of PipelineStage objects
    is_preset INTEGER DEFAULT 0,
    preset_id TEXT,
    blocking INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
```

### project_settings (Existing)

```sql
CREATE TABLE project_settings (
    github_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    assigned_pipeline_id TEXT,   -- Updated by launch endpoint (step 4)
    agent_pipeline_mappings TEXT,
    updated_at TEXT,
    PRIMARY KEY (github_user_id, project_id)
);
```

---

## State Flow Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                  Projects Page                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │         ProjectIssueLaunchPanel                       │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────┐                  │  │
│  │  │ <textarea>                      │ ← paste / edit   │  │
│  │  │ Issue Description               │                  │  │
│  │  └─────────────────────────────────┘                  │  │
│  │                                                       │  │
│  │  ┌──────────┐  ← File.text() reads .md/.txt          │  │
│  │  │ Upload   │     into textarea                       │  │
│  │  └──────────┘                                         │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────┐                  │  │
│  │  │ <select> Pipeline Config        │ ← populated from │  │
│  │  │ [▾ Full Review Pipeline     ]   │   pipelinesApi   │  │
│  │  └─────────────────────────────────┘   .list()        │  │
│  │                                                       │  │
│  │  ┌────────────┐                                       │  │
│  │  │ 🚀 Launch  │ → validates → calls                   │  │
│  │  └────────────┘   pipelinesApi.launch()               │  │
│  │                                                       │  │
│  │  formErrors{} ← inline error messages                 │  │
│  │  submissionResult ← WorkflowResult on success         │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ↓                                 │
│              POST /pipelines/{projectId}/launch              │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Backend Launch Flow:                                    ││
│  │ 1. Normalize issue description                          ││
│  │ 2. Resolve GitHub repository (owner/repo)               ││
│  │ 3. Fetch PipelineConfig from pipeline_configs           ││
│  │ 4. Set pipeline assignment in project_settings          ││
│  │ 5. Convert pipeline stages → agent_mappings             ││
│  │ 6. Append agent tracking to issue body                  ││
│  │ 7. Validate body length ≤ GITHUB_ISSUE_BODY_MAX_LENGTH ││
│  │ 8. Determine blocking mode                              ││
│  │ 9. Create GitHub Issue via API                          ││
│  │ 10. Add issue to project board                          ││
│  │ 11. Create per-agent sub-issues                         ││
│  │ 12. Enqueue for blocking (if applicable)                ││
│  │ 13. Return WorkflowResult                               ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                 │
│                            ↓                                 │
│  onLaunched(result) → ProjectsPage refreshes board           │
└─────────────────────────────────────────────────────────────┘
```

---

## Entity Relationships

```text
PipelineConfigSummary (1..n)     User Input
  │ (populated dropdown)          │ (paste / file upload)
  │                               │
  ↓                               ↓
pipeline_id (selected)     issue_description (text)
  │                               │
  └───────────┬───────────────────┘
              │
              ↓
   PipelineIssueLaunchRequest
   { issue_description, pipeline_id }
              │
              ↓
   POST /pipelines/{projectId}/launch
              │
              ├──→ pipeline_configs (fetch by pipeline_id)
              │         │
              │         ↓
              │    PipelineConfig.stages[]
              │         │
              │         ↓
              │    PipelineStage.agents[]  →  AgentAssignment (converted)
              │         │
              │         ↓
              │    WorkflowConfiguration.agent_mappings
              │
              ├──→ GitHub API: Create Issue
              │         │
              │         ↓
              │    GitHub Issue (number, url, node_id)
              │
              ├──→ GitHub Projects API: Add to Board
              │
              ├──→ Create Sub-Issues per Agent
              │
              └──→ WorkflowResult { success, issue_number, issue_url, ... }
```
