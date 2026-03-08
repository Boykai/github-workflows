# Component Contracts: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Feature**: 030-chat-pipeline-config | **Date**: 2026-03-08

## New Components

### PipelineWarningBanner

**Location**: `frontend/src/components/chat/PipelineWarningBanner.tsx`
**Purpose**: Inline warning banner shown in the chat area when no Agent Pipeline is assigned to the current project.

```typescript
interface PipelineWarningBannerProps {
  projectId: string;
}
```

**Behavior**:

- Uses `useSelectedPipeline(projectId)` hook to check assignment state
- Renders an amber/yellow warning banner when `hasAssignment === false` and `isLoading === false`
- Displays text: "⚠ No Agent Pipeline selected — issues will use the default pipeline. Select one on the Project page."
- Automatically hides when a pipeline is assigned (React Query cache update)
- Renders nothing when loading or when a pipeline is assigned
- Styling follows existing warning patterns: `bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-3 text-xs`

**Accessibility**:

- `role="alert"` for screen reader announcement
- Warning icon has `aria-hidden="true"`

---

## New Hooks

### useSelectedPipeline

**Location**: `frontend/src/hooks/useSelectedPipeline.ts`
**Purpose**: Shared hook for reading the current project's pipeline assignment. Used by both the chat (for `PipelineWarningBanner`) and optionally by `ProjectsPage` for DRY refactoring.

```typescript
function useSelectedPipeline(projectId: string | null): SelectedPipelineState;

interface SelectedPipelineState {
  pipelineId: string;       // "" = none selected, UUID = specific pipeline
  pipelineName: string;     // "" = none, display name if selected
  isLoading: boolean;       // Combined loading state (assignment + pipeline list)
  hasAssignment: boolean;   // Convenience: pipelineId !== ""
}
```

**Behavior**:

- Wraps two React Query calls:
  1. `pipelinesApi.getAssignment(projectId)` — gets `{ pipeline_id }` (query key: `['pipelines', 'assignment', projectId]`)
  2. `pipelinesApi.list(projectId)` — gets pipeline list to resolve name (query key: `['pipelines', projectId]`, reuses existing cache)
- Returns `isLoading: true` while either query is loading
- Returns `pipelineName` by finding the matching pipeline in the list by ID
- Returns `hasAssignment: false` when `pipeline_id` is empty string
- `staleTime: 60_000` (1 minute) — matches existing pipeline query staleness
- Enabled only when `projectId` is non-null
- Handles edge case: assigned pipeline deleted (ID exists but not in list) → `hasAssignment: true` but `pipelineName: "Unknown Pipeline"`

---

## Modified Components

### TaskPreview (Modified)

**Location**: `frontend/src/components/chat/TaskPreview.tsx`
**Purpose**: Shows the created issue details after proposal confirmation. Extended to display the applied Agent Pipeline name.

**Changes**:

- After successful confirmation (when `proposal.status === "confirmed"`), display pipeline info:
  - If `proposal.pipeline_name` exists: show badge `"Agent Pipeline: {pipeline_name}"`
  - If `proposal.pipeline_source === "default"`: show badge `"Agent Pipeline: Default"`
  - If `proposal.pipeline_source === "user"`: show badge `"Agent Pipeline: Custom Mappings"`
- Badge styling: `inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[10px] text-muted-foreground`
- Uses a small pipeline icon from `lucide-react` (e.g., `GitBranch` or `Workflow`)

### ChatInterface (Modified)

**Location**: `frontend/src/components/chat/ChatInterface.tsx`
**Purpose**: Main chat container. Extended to show `PipelineWarningBanner`.

**Changes**:

- Import and render `PipelineWarningBanner` when a project is selected
- Position: above the chat input area, below messages
- Conditionally rendered: only when `projectId` is available
- No changes to existing chat logic or message handling

### ProjectsPage (Optional Refactor)

**Location**: `frontend/src/pages/ProjectsPage.tsx`
**Purpose**: Could optionally use `useSelectedPipeline` hook for DRY, but this is a low-priority refactor since the page already works correctly.

**Changes** (optional):

- Replace inline `useQuery` for `pipelineAssignment` with `useSelectedPipeline` hook
- This is a cosmetic/DRY improvement and not required for the feature to work

---

## Modified Types

### AITaskProposal (Modified)

**Location**: `frontend/src/types/index.ts`

```typescript
export interface AITaskProposal {
  // ... existing fields unchanged ...
  
  // NEW
  pipeline_name?: string;    // Name of the applied Agent Pipeline
  pipeline_source?: string;  // "pipeline" | "user" | "default"
}
```

---

## Backend Functions

### resolve_project_pipeline_mappings (New)

**Location**: `backend/src/services/workflow_orchestrator/config.py`
**Purpose**: Top-level resolution function implementing the three-tier fallback chain.

```python
async def resolve_project_pipeline_mappings(
    project_id: str,
    github_user_id: str,
) -> PipelineResolutionResult:
    """Resolve agent pipeline mappings for issue creation.
    
    Three-tier fallback:
    1. Project-level pipeline assignment (assigned_pipeline_id)
    2. User-specific agent mappings (agent_pipeline_mappings)
    3. System default agent mappings
    
    Returns a PipelineResolutionResult with the resolved mappings and metadata.
    """
```

### load_pipeline_as_agent_mappings (New)

**Location**: `backend/src/services/workflow_orchestrator/config.py`
**Purpose**: Converts a `PipelineConfig` to `agent_mappings` format.

```python
async def load_pipeline_as_agent_mappings(
    project_id: str,
    pipeline_id: str,
) -> tuple[dict[str, list[AgentAssignment]], str] | None:
    """Load a pipeline config and convert its stages to agent_mappings.
    
    Returns (agent_mappings, pipeline_name) or None if pipeline not found.
    """
```
