# Quickstart: Use Selected Agent Pipeline Config from Project Page When Creating GitHub Issues via Chat

**Feature**: 030-chat-pipeline-config | **Date**: 2026-03-08

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+
- The repository cloned and on the feature branch

```bash
git checkout 030-chat-pipeline-config
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

### New Frontend Files

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useSelectedPipeline.ts` | NEW: Shared hook for reading project pipeline assignment |
| `frontend/src/components/chat/PipelineWarningBanner.tsx` | NEW: Inline warning when no pipeline selected |

### Files to Modify

| File | Changes |
|------|---------|
| `backend/src/api/chat.py` | Add pipeline resolution in `confirm_proposal` endpoint |
| `backend/src/services/workflow_orchestrator/config.py` | Add `resolve_project_pipeline_mappings()` and `load_pipeline_as_agent_mappings()` |
| `frontend/src/components/chat/TaskPreview.tsx` | Display applied pipeline name in confirmation |
| `frontend/src/components/chat/ChatInterface.tsx` | Render `PipelineWarningBanner` above input |
| `frontend/src/types/index.ts` | Extend `AITaskProposal` with `pipeline_name`, `pipeline_source` |

## Implementation Order

### Phase 1: Backend Pipeline Resolution (FR-001, FR-002, FR-003, FR-006)

1. **config.py** — Add `load_pipeline_as_agent_mappings()`
   - Fetch `PipelineConfig` by ID from `pipeline_configs` table
   - Convert `stages[].agents[]` to `dict[str, list[AgentAssignment]]`
   - Map each stage's `name` to its agents' `slug`, `display_name`, `model_id`, `model_name`
   - Return `(agent_mappings, pipeline_name)` or `None` if pipeline deleted

2. **config.py** — Add `resolve_project_pipeline_mappings()`
   - Tier 1: Read `assigned_pipeline_id` from `project_settings` → call `load_pipeline_as_agent_mappings()`
   - Tier 2: Call existing `load_user_agent_mappings(github_user_id, project_id)`
   - Tier 3: Return `DEFAULT_AGENT_MAPPINGS`
   - Return `PipelineResolutionResult` with `agent_mappings`, `source`, `pipeline_name`

3. **chat.py** — Integrate pipeline resolution in `confirm_proposal`
   - Replace direct `load_user_agent_mappings()` call with `resolve_project_pipeline_mappings()`
   - Apply resolved `agent_mappings` to `WorkflowConfiguration`
   - Add `pipeline_name` and `pipeline_source` to the response

**Verify**: Create an issue via chat with a pipeline selected on the Project page → check that sub-issues match the pipeline's agents. Create without a pipeline → check that defaults are used.

### Phase 2: Frontend Warning Banner (FR-004, FR-005)

1. **useSelectedPipeline.ts** (new)
   - Wrap `pipelinesApi.getAssignment()` and `pipelinesApi.list()` queries
   - Return `{ pipelineId, pipelineName, isLoading, hasAssignment }`
   - Use React Query cache (same query keys as ProjectsPage)

2. **PipelineWarningBanner.tsx** (new)
   - Consume `useSelectedPipeline(projectId)`
   - Render amber warning when `!hasAssignment`
   - Render nothing when loading or when pipeline assigned

3. **ChatInterface.tsx** — Render banner
   - Import `PipelineWarningBanner`
   - Render above chat input area when `projectId` is available

**Verify**: Open chat with no pipeline selected → see warning. Select a pipeline on Project page → warning disappears (may need to refocus tab).

### Phase 3: Pipeline Confirmation Display (FR-007)

1. **types/index.ts** — Extend `AITaskProposal`
   - Add `pipeline_name?: string` and `pipeline_source?: string`

2. **TaskPreview.tsx** — Show pipeline badge
   - After successful confirmation, render badge: "Agent Pipeline: {name}"
   - Handle all source types: pipeline, user, default

**Verify**: Create an issue via chat with "Full Review Pipeline" selected → confirmation shows "Agent Pipeline: Full Review Pipeline". Create with no pipeline → shows "Agent Pipeline: Default".

### Phase 4: Deleted Pipeline Handling (FR-008)

1. **config.py** — Auto-cleanup in `resolve_project_pipeline_mappings()`
   - If `assigned_pipeline_id` exists but pipeline is deleted, clear the stale ID
   - Log warning for observability
   - Fall through to Tier 2/3

**Verify**: Select a pipeline, then delete it, then create an issue via chat → system falls back to user/default mappings and the Project page shows no pipeline selected.

## Testing Strategy

No new test files required. Existing tests should continue to pass:

```bash
# Backend
cd backend && python -m pytest tests/ -v

# Frontend
cd frontend && npx vitest run
```

Manual verification covers all acceptance scenarios in the spec.

## Key Architecture Decisions

1. **Backend resolves pipeline** — avoids stale-state bugs from frontend-side resolution
2. **Three-tier fallback** — project pipeline → user mappings → defaults (backward compatible)
3. **Reuses existing APIs** — no new endpoints for pipeline assignment (GET/PUT already exist)
4. **React Query sync** — cache invalidation keeps chat and Project page in sync within staleTime
5. **Auto-cleanup of deleted pipelines** — backend clears stale references lazily at issue-creation time
