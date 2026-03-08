# Quickstart: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Feature**: 030-blocking-queue | **Date**: 2026-03-08

## Prerequisites

- Python 3.12+
- Node.js 20+ and npm
- The repository cloned and on the feature branch

```bash
git checkout 030-blocking-queue
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

### Backend

| File | Purpose |
|------|---------|
| `backend/src/migrations/017_blocking_queue.sql` | New table + ALTER TABLE additions for blocking columns |
| `backend/src/models/blocking.py` | Pydantic models: BlockingQueueEntry, BlockingQueueStatus |
| `backend/src/services/blocking_queue.py` | Core blocking queue state machine (enqueue, activate, transition) |
| `backend/src/services/blocking_queue_store.py` | SQLite persistence layer (CRUD for blocking_queue table) |

### Tests

| File | Purpose |
|------|---------|
| `backend/tests/unit/test_blocking_queue.py` | State machine unit tests (8-issue scenario, edge cases) |

## Files to Modify

### Backend

| File | Changes |
|------|---------|
| `backend/src/models/chores.py` | Add `blocking: bool = False` to Chore, ChoreCreate, ChoreUpdate |
| `backend/src/models/pipeline.py` | Add `blocking: bool = False` to PipelineConfig, PipelineConfigUpdate |
| `backend/src/api/chat.py` | Add `#block` detection and stripping (Priority 0.5) |
| `backend/src/api/chores.py` | Pass blocking flag on chore trigger |
| `backend/src/api/pipelines.py` | Include blocking field in CRUD responses |
| `backend/src/services/chores/service.py` | Read blocking from chore/pipeline, pass to orchestrator; add `blocking` to `_CHORE_UPDATABLE_COLUMNS` |
| `backend/src/services/pipelines/service.py` | Add `blocking` to `_PIPELINE_COLUMNS` allowlist |
| `backend/src/services/workflow_orchestrator/orchestrator.py` | Integrate `enqueue_issue()` + `get_base_ref_for_issue()` |
| `backend/src/services/copilot_polling/pipeline.py` | Add `mark_in_review()` + activation cascade on status transition |
| `backend/src/services/copilot_polling/completion.py` | Add `mark_completed()` + activation cascade on issue completion |

### Frontend

| File | Changes |
|------|---------|
| `frontend/src/types/index.ts` | Add BlockingQueueEntry type, blocking fields to Chore/Pipeline types |
| `frontend/src/hooks/useChores.ts` | Include `blocking` in ChoreUpdate type and mutation |
| `frontend/src/hooks/usePipelineConfig.ts` | Include `blocking` in PipelineConfigUpdate type and mutation |
| `frontend/src/components/chores/ChoreCard.tsx` | Add "Blocking" toggle switch |
| `frontend/src/components/pipeline/SavedWorkflowsList.tsx` | Add pipeline "Blocking" toggle |
| `frontend/src/components/chat/ChatInterface.tsx` | Add `#block` autocomplete + visual indicator |
| Board components (various) | Add 🔒 blocking badge, "Pending (blocked)" label |

## Implementation Order

### Phase 1: Database & Models

1. **Migration** (`017_blocking_queue.sql`)
   - Create `blocking_queue` table with all columns and constraints
   - Add `blocking` column to `pipeline_configs` and `chores` tables
   - Add indexes for repo+status and repo+blocking queries

2. **Models** (`models/blocking.py`)
   - Define `BlockingQueueStatus` StrEnum (pending, active, in_review, completed)
   - Define `BlockingQueueEntry` Pydantic model mirroring DB columns

3. **Existing Models** (`models/chores.py`, `models/pipeline.py`)
   - Add `blocking: bool = False` to Chore, ChoreCreate, ChoreUpdate
   - Add `blocking: bool = False` to PipelineConfig, PipelineConfigUpdate

### Phase 2: Blocking Queue Service (Core Engine)

4. **Store** (`services/blocking_queue_store.py`)
   - Implement CRUD: insert, update_status, get_by_repo, get_by_issue, get_pending, get_open_blocking
   - Follow existing `get_db()` async pattern

5. **Service** (`services/blocking_queue.py`)
   - Implement: enqueue_issue, get_base_ref_for_issue, mark_active, mark_in_review, mark_completed
   - Implement core `try_activate_next()` with batch activation rules
   - Implement per-repo asyncio.Lock for concurrency control
   - Implement: get_current_base_branch, has_open_blocking_issues

### Phase 3: Backend Integration

6. **Pipeline/Chore CRUD** (`services/pipelines/service.py`, `services/chores/service.py`)
   - Add `blocking` to `_PIPELINE_COLUMNS` and `_CHORE_UPDATABLE_COLUMNS` allowlists
   - Update row-to-model conversion to include blocking field

7. **Chat** (`api/chat.py`)
   - Add `#block` detection regex at Priority 0.5
   - Strip `#block` from message content
   - Propagate `is_blocking` through confirm_proposal → execute_full_workflow

8. **Orchestrator** (`services/workflow_orchestrator/orchestrator.py`)
   - In `execute_full_workflow()`: call `enqueue_issue()` after issue creation
   - If not activated: return pending WorkflowResult, skip agent assignment
   - In base_ref resolution: use `get_base_ref_for_issue()` for first agent assignment

9. **Polling** (`services/copilot_polling/pipeline.py`, `completion.py`)
   - On "in review" transition: call `mark_in_review()` + activate next
   - On completion: call `mark_completed()` + activate next
   - On startup: call `try_activate_next()` for all repos with non-completed entries

10. **WebSocket** (integrated in blocking_queue.py)
    - After activation cascade: broadcast `blocking_queue_updated` event via `connection_manager`

### Phase 4: Frontend Integration

11. **Types** (`types/index.ts`)
    - Add `BlockingQueueEntry`, `BlockingQueueStatus` types
    - Add `blocking` to existing Chore and PipelineConfig types

12. **Hooks** (`useChores.ts`, `usePipelineConfig.ts`)
    - Include `blocking` in update mutation payloads

13. **Components**
    - ChoreCard: Add "Blocking" toggle (follow `ai_enhance_enabled` pattern)
    - SavedWorkflowsList: Add pipeline "Blocking" toggle
    - ChatInterface: Add `#block` autocomplete + badge indicator
    - Board cards: Add blocking/pending visual indicators

14. **WebSocket Handler**
    - Listen for `blocking_queue_updated` events
    - Display toast notifications for newly activated issues

## Key Patterns to Follow

### Service Pattern (from existing `services/chores/service.py`)

```python
from src.services.database import get_db

async def insert_queue_entry(entry_data: dict) -> dict:
    db = get_db()
    cursor = await db.execute(
        """INSERT INTO blocking_queue (repo_key, issue_number, project_id, is_blocking)
           VALUES (?, ?, ?, ?)""",
        (entry_data["repo_key"], entry_data["issue_number"],
         entry_data["project_id"], int(entry_data["is_blocking"]))
    )
    await db.commit()
    return await get_by_id(cursor.lastrowid)
```

### Column Allowlist Pattern (from `_CHORE_UPDATABLE_COLUMNS`)

```python
# In services/chores/service.py — add to existing frozenset:
_CHORE_UPDATABLE_COLUMNS = frozenset({
    "schedule_type", "schedule_value", "status",
    "ai_enhance_enabled", "agent_pipeline_id",
    "blocking",  # NEW
})

# In services/pipelines/service.py — add to existing frozenset:
_PIPELINE_COLUMNS = frozenset({
    "name", "description", "stages", "updated_at",
    "blocking",  # NEW
})
```

### Toggle Pattern (from ChoreCard `ai_enhance_enabled`)

```tsx
// Follow the existing toggle pattern in ChoreCard.tsx
<div className="flex items-center justify-between">
  <label className="text-sm text-muted-foreground">Blocking</label>
  <Switch
    checked={chore.blocking}
    onCheckedChange={(checked) =>
      updateChore({ blocking: checked })
    }
  />
</div>
```

### WebSocket Broadcast Pattern (from `websocket.py`)

```python
from src.services.websocket import connection_manager

await connection_manager.broadcast_to_project(
    project_id,
    {
        "type": "blocking_queue_updated",
        "repo_key": repo_key,
        "activated_issues": activated_issue_numbers,
        "completed_issues": completed_issue_numbers,
        "current_base_branch": current_base_branch,
    }
)
```

## Verification

After implementation, verify:

1. **Toggle persistence**: Enable blocking on a Chore → refresh page → toggle state persists
2. **Pipeline toggle**: Enable blocking on a Pipeline → refresh → toggle state persists
3. **Chat #block**: Send "Fix bug #block" → `#block` stripped → issue created as blocking
4. **Serial activation**: Create blocking issue A → create issue B → B enters "pending" → A moves to "in review" → B activates
5. **Branch ancestry**: Issue B's branch is created from Issue A's branch, not from `main`
6. **Concurrent non-blocking**: With no blocking issues → create two issues → both activate concurrently
7. **8-issue scenario**: Run full 8-issue mixed scenario → verify activation order and branch ancestry matches the walkthrough in data-model.md
8. **Restart recovery**: Create pending issues → restart backend → pending issues activate automatically
9. **Toast notification**: Issue activates → toast appears: "Issue #X is now active — agents starting"
10. **Blocking indicators**: Blocking issue card shows 🔒 badge; pending issue shows "Pending (blocked)"
