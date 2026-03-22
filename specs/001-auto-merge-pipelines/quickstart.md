# Quickstart: Auto Merge — Automatically Squash-Merge Parent PRs When Pipelines Complete

**Feature**: `001-auto-merge-pipelines` | **Date**: 2026-03-22 | **Plan**: [plan.md](./plan.md)

## Overview

This guide covers how to implement the Auto Merge feature, which automatically squash-merges parent PRs when pipeline steps complete successfully. The feature follows the same patterns as the existing Queue Mode toggle.

## Prerequisites

- Python 3.11+ with FastAPI, aiosqlite
- Node.js 18+ with React, TypeScript
- SQLite database (existing `solune.db`)
- Familiarity with the existing `queue_mode` implementation

## Implementation Phases

### Phase 1: Data Model & Storage (Blocks all other phases)

**Files to modify**:

1. **Database Migration** — `solune/backend/src/migrations/034_auto_merge.sql`
   ```sql
   ALTER TABLE project_settings ADD COLUMN auto_merge INTEGER NOT NULL DEFAULT 0;
   ```

2. **Backend Model** — `solune/backend/src/models/settings.py`
   ```python
   class ProjectBoardConfig(BaseModel):
       # ... existing fields ...
       auto_merge: bool = False  # Add this field
   ```

3. **Settings Store** — `solune/backend/src/services/settings_store.py`
   - Add `"auto_merge"` to `PROJECT_SETTINGS_COLUMNS` tuple.
   - Add `is_auto_merge_enabled()` function (mirror `is_queue_mode_enabled()`).
   - Add `_auto_merge_cache` with 10-second TTL.
   - Update `_merge_settings_rows()` to merge `auto_merge` into `ProjectBoardConfig`.

4. **API Handler** — `solune/backend/src/api/settings.py`
   - Handle `auto_merge` in `update_project_settings_endpoint()` (same pattern as `queue_mode`).
   - Sync to `__workflow__` canonical row.
   - Invalidate `_auto_merge_cache`.

5. **Pipeline State** — `solune/backend/src/services/workflow_orchestrator/models.py`
   ```python
   @dataclass
   class PipelineState:
       # ... existing fields ...
       auto_merge: bool = False  # Add this field
   ```

6. **Frontend Types** — `solune/frontend/src/types/index.ts`
   ```typescript
   export interface ProjectBoardConfig {
     // ... existing fields ...
     auto_merge: boolean;  // Add this field
   }
   ```

### Phase 2: DevOps Agent (Parallel with Phase 3)

**Files to create**:

1. **DevOps Agent** — `.github/agents/devops.agent.md`
   - YAML frontmatter: `name: DevOps`, `description: ...`, `icon: wrench`
   - System prompt specialized for CI failure diagnosis and resolution

### Phase 3: Backend Logic (Parallel with Phase 2)

**Files to create/modify**:

1. **Auto Merge Function** — `solune/backend/src/services/copilot_polling/auto_merge.py` (NEW)
   - `_attempt_auto_merge()` — main merge orchestration function
   - Returns `AutoMergeResult` dataclass

2. **Pipeline Advancement** — `solune/backend/src/services/copilot_polling/pipeline.py` (MODIFY)
   - Add human agent skip logic in `_advance_pipeline()`
   - Add auto-merge trigger in `_transition_after_pipeline_complete()`

3. **Pipeline State Store** — `solune/backend/src/services/pipeline_state_store.py` (MODIFY)
   - Serialize `auto_merge` in metadata JSON

### Phase 4: Webhook CI Detection (Depends on Phase 1)

**Files to modify**:

1. **Webhook Models** — `solune/backend/src/api/webhook_models.py`
   - Add `CheckRunEvent`, `CheckSuiteEvent`, `CheckRunData`, `CheckSuiteData` Pydantic models

2. **Webhook Router** — `solune/backend/src/api/webhooks.py`
   - Route `check_run` and `check_suite` events to `dispatch_devops_agent()`

### Phase 5: Frontend (Depends on Phase 1)

**Files to modify**:

1. **Icons** — `solune/frontend/src/lib/icons.ts`
   - Export `GitMerge` from lucide-react

2. **Projects Page** — `solune/frontend/src/pages/ProjectsPage.tsx`
   - Add Auto Merge toggle (mirror Queue Mode toggle pattern)

3. **Pipeline Config** — Pipeline configuration panel
   - Add Auto Merge toggle

4. **WebSocket Hook** — `solune/frontend/src/hooks/useRealTimeSync.ts`
   - Handle `auto_merge_completed`, `auto_merge_failed`, `devops_triggered` events
   - Show toast notifications via sonner

### Phase 6: GitHub API Helpers (Depends on Phase 3)

**Files to modify**:

1. **Pull Requests Mixin** — `solune/backend/src/services/github_projects/pull_requests.py`
   - Add `get_check_runs_for_ref()` — REST call
   - Add `get_pr_mergeable_state()` — GraphQL query

## Key Patterns to Follow

### Settings Toggle Pattern (from Queue Mode)

```python
# 1. Model: Add field to ProjectBoardConfig
auto_merge: bool = False

# 2. Migration: Add column to project_settings
ALTER TABLE project_settings ADD COLUMN auto_merge INTEGER NOT NULL DEFAULT 0;

# 3. Settings Store: Add to columns tuple
PROJECT_SETTINGS_COLUMNS = (..., "auto_merge")

# 4. Settings Store: Add cached reader
_auto_merge_cache: dict[str, tuple[bool, float]] = {}

async def is_auto_merge_enabled(db, project_id) -> bool:
    # Same pattern as is_queue_mode_enabled() with 10s TTL

# 5. API: Handle in PUT /settings/project/{id}
if "auto_merge" in updates:
    workflow_updates["auto_merge"] = updates["auto_merge"]
    _auto_merge_cache.pop(project_id, None)

# 6. Frontend: Toggle in ProjectsPage
const isAutoMerge = settings?.project?.board_display_config?.auto_merge ?? false;
await updateSettings({ auto_merge: !isAutoMerge });
```

### Agent Dispatch Pattern

```python
# Standard Copilot dispatch (from helpers.py patterns)
await github_projects_service.dispatch_copilot_agent(
    access_token=access_token,
    owner=owner,
    repo=repo,
    agent_slug="devops",
    issue_number=sub_issue_number,
)
```

### WebSocket Broadcast Pattern

```python
# From existing pipeline.py patterns
await connection_manager.broadcast_to_project(
    project_id,
    {
        "type": "auto_merge_completed",
        "issue_number": issue_number,
        "pr_number": pr_number,
        "merge_commit": merge_commit,
        "timestamp": utcnow().isoformat(),
    }
)
```

## Testing Strategy

### Unit Tests (pytest)

| Test | File | Validates |
|------|------|-----------|
| `test_attempt_auto_merge_success` | `test_auto_merge.py` | Merge succeeds when CI passes and PR is mergeable |
| `test_attempt_auto_merge_ci_failure` | `test_auto_merge.py` | Returns `devops_needed` on CI failure |
| `test_attempt_auto_merge_conflict` | `test_auto_merge.py` | Returns `devops_needed` on CONFLICTING state |
| `test_human_skip_when_auto_merge` | `test_auto_merge.py` | Human step marked SKIPPED when auto_merge active |
| `test_human_not_skipped_when_disabled` | `test_auto_merge.py` | Human step runs normally when auto_merge off |
| `test_flag_resolution_or_logic` | `test_settings_auto_merge.py` | Either project OR pipeline true → active |
| `test_devops_retry_cap` | `test_auto_merge.py` | No more than 2 DevOps dispatch attempts |
| `test_devops_deduplication` | `test_auto_merge.py` | No duplicate dispatch when DevOps active |
| `test_webhook_check_run_routing` | `test_webhook_ci.py` | check_run failure routed to dispatch |
| `test_webhook_check_suite_routing` | `test_webhook_ci.py` | check_suite failure routed to dispatch |
| `test_settings_persistence` | `test_settings_auto_merge.py` | auto_merge persists across restart |

### Frontend Tests (Vitest)

| Test | Validates |
|------|-----------|
| Toggle renders adjacent to Queue Mode | FR-013 |
| Toggle persists setting on click | FR-001 |
| Confirmation dialog on retroactive enable | FR-015 |
| Toast notifications for WS events | FR-016 |

## Verification Checklist

- [ ] `auto_merge` column exists in `project_settings` table after migration
- [ ] Toggle in ProjectsPage reads/writes `auto_merge` setting
- [ ] Pipeline with auto_merge skips human agent (last step)
- [ ] Successful pipeline triggers squash-merge of parent PR
- [ ] CI failure dispatches DevOps agent (max 2 attempts)
- [ ] DevOps agent discoverable via `list_available_agents()`
- [ ] WebSocket notifications arrive for merge events
- [ ] Retroactive toggle applies at next merge decision point
