# Data Model: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Feature**: 030-blocking-queue | **Date**: 2026-03-08

## Backend Entities (Pydantic Models)

### BlockingQueueStatus

Enum representing the lifecycle states of a blocking queue entry.

```python
class BlockingQueueStatus(StrEnum):
    PENDING = "pending"          # Waiting for activation
    ACTIVE = "active"            # Agents are working on this issue
    IN_REVIEW = "in_review"      # Issue is in review, agents finished
    COMPLETED = "completed"      # Issue is done
```

### BlockingQueueEntry

The primary entity representing an issue's position and state in a repository's blocking queue.

```python
class BlockingQueueEntry(BaseModel):
    id: int                                    # Auto-increment primary key
    repo_key: str                              # Repository identifier (owner/repo)
    issue_number: int                          # GitHub issue number
    project_id: str                            # Project ID for WebSocket scoping
    is_blocking: bool                          # Whether this issue enforces serial activation
    queue_status: BlockingQueueStatus          # Current state in the queue
    parent_branch: str | None = None           # Branch this issue targets as base_ref
    blocking_source_issue: int | None = None   # Which blocking issue provided the parent branch
    created_at: str                            # ISO 8601 datetime
    activated_at: str | None = None            # When the issue was activated
    completed_at: str | None = None            # When the issue completed
```

**Relationships**: Belongs to a repository (by `repo_key`). References a project (by `project_id`). Optionally references another issue (by `blocking_source_issue`).
**Constraints**: UNIQUE(repo_key, issue_number) — each issue appears at most once in a repo's queue.

### Chore (Modified)

Add `blocking` field to existing Chore model.

```python
# In backend/src/models/chores.py — additions only
class Chore(BaseModel):
    # ... existing fields ...
    blocking: bool = False                     # NEW: Whether triggered issues are blocking

class ChoreCreate(BaseModel):
    # ... existing fields ...
    blocking: bool = False                     # NEW: Blocking flag for new chores

class ChoreUpdate(BaseModel):
    # ... existing fields ...
    blocking: bool | None = None               # NEW: Optional blocking flag update
```

### PipelineConfig (Modified)

Add `blocking` field to existing PipelineConfig model.

```python
# In backend/src/models/pipeline.py — additions only
class PipelineConfig(BaseModel):
    # ... existing fields ...
    blocking: bool = False                     # NEW: ALL issues from this pipeline are blocking

class PipelineConfigUpdate(BaseModel):
    # ... existing fields ...
    blocking: bool | None = None               # NEW: Optional blocking flag update
```

---

## Frontend Types (TypeScript)

### Blocking Queue Types

```typescript
type BlockingQueueStatus = 'pending' | 'active' | 'in_review' | 'completed';

interface BlockingQueueEntry {
  id: number;
  repoKey: string;
  issueNumber: number;
  projectId: string;
  isBlocking: boolean;
  queueStatus: BlockingQueueStatus;
  parentBranch: string | null;
  blockingSourceIssue: number | null;
  createdAt: string;
  activatedAt: string | null;
  completedAt: string | null;
}
```

### Modified Types

```typescript
// In frontend/src/types/index.ts — additions to existing interfaces

interface Chore {
  // ... existing fields ...
  blocking: boolean;                           // NEW
}

interface ChoreUpdate {
  // ... existing fields ...
  blocking?: boolean;                          // NEW
}

interface PipelineConfig {
  // ... existing fields ...
  blocking: boolean;                           // NEW
}

interface PipelineConfigUpdate {
  // ... existing fields ...
  blocking?: boolean;                          // NEW
}
```

### Chat Types

```typescript
// Addition to existing chat message send options
interface ChatMessageOptions {
  // ... existing fields ...
  isBlocking?: boolean;                        // NEW: Set when #block detected
}
```

### WebSocket Event Types

```typescript
interface BlockingQueueUpdatedEvent {
  type: 'blocking_queue_updated';
  repoKey: string;
  activatedIssues: number[];
  completedIssues: number[];
  currentBaseBranch: string;
}
```

---

## Database Schema

### blocking_queue Table (Migration 017)

```sql
CREATE TABLE IF NOT EXISTS blocking_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_key TEXT NOT NULL,                     -- formatted as 'owner/repo'
    issue_number INTEGER NOT NULL,
    project_id TEXT NOT NULL,
    is_blocking INTEGER NOT NULL DEFAULT 0,
    queue_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (queue_status IN ('pending', 'active', 'in_review', 'completed')),
    parent_branch TEXT,                         -- branch this issue targets as base_ref
    blocking_source_issue INTEGER,              -- which blocking issue provided the parent branch
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    activated_at TEXT,
    completed_at TEXT,
    UNIQUE(repo_key, issue_number)
);

CREATE INDEX IF NOT EXISTS idx_blocking_queue_repo_status
    ON blocking_queue(repo_key, queue_status);

CREATE INDEX IF NOT EXISTS idx_blocking_queue_repo_blocking
    ON blocking_queue(repo_key, is_blocking, queue_status);
```

### ALTER TABLE Additions (Migration 017)

```sql
-- Add blocking column to pipeline_configs
ALTER TABLE pipeline_configs ADD COLUMN blocking INTEGER NOT NULL DEFAULT 0;

-- Add blocking column to chores
ALTER TABLE chores ADD COLUMN blocking INTEGER NOT NULL DEFAULT 0;
```

**Storage Notes**:

- `queue_status` uses a CHECK constraint to enforce valid states, matching the `BlockingQueueStatus` enum.
- `is_blocking` is stored as INTEGER (0/1) following SQLite's boolean convention used throughout the project.
- `idx_blocking_queue_repo_status` supports the most frequent query: "get all non-completed entries for a repo."
- `idx_blocking_queue_repo_blocking` supports the "get oldest open blocking issue" query.
- `UNIQUE(repo_key, issue_number)` prevents duplicate entries per issue within a repo.
- `parent_branch` and `blocking_source_issue` are populated when an issue activates, providing traceability (FR-020).
- `ALTER TABLE ADD COLUMN` with `DEFAULT 0` is safe for existing rows — all current chores and pipelines become non-blocking.

---

## State Machines

### Blocking Queue Entry Lifecycle

```text
                    ┌──────────────┐
                    │   PENDING    │  Issue created, waiting for activation
                    │              │
                    └──────┬───────┘
                           │ try_activate_next() determines
                           │ this issue should activate
                           ▼
                    ┌──────────────┐
                    │    ACTIVE    │  Agents assigned, work in progress
                    │              │
                    └──────┬───────┘
                           │ Issue status changes to "In review"
                           │ (detected by polling)
                           ▼
                    ┌──────────────┐
                    │  IN_REVIEW   │  PR created, awaiting merge/approval
                    │              │  → triggers try_activate_next()
                    └──────┬───────┘
                           │ Issue completed/closed
                           │ (detected by polling)
                           ▼
                    ┌──────────────┐
                    │  COMPLETED   │  Terminal state
                    │              │  → triggers try_activate_next()
                    └──────────────┘
```

### Activation Decision Logic (try_activate_next)

```text
try_activate_next(repo_key):
    │
    ├─ Get all pending entries (ordered by created_at ASC)
    │  └─ No pending entries? → Return (nothing to activate)
    │
    ├─ Get all active/in_review entries
    │  └─ Any active (not in_review) entries? → Return (wait for them to finish or move to review)
    │
    ├─ Any open blocking issues (active or in_review)?
    │  │
    │  ├─ YES → Serial mode:
    │  │        Get next pending entry
    │  │        ├─ Blocking entry? → Activate it alone
    │  │        └─ Non-blocking entry? → Activate it and all consecutive
    │  │           non-blocking entries (up to next blocking entry)
    │  │
    │  └─ NO → Concurrent mode:
    │          Look at pending entries
    │          ├─ First pending is non-blocking? → Activate all consecutive
    │          │   non-blocking entries (up to next blocking entry)
    │          └─ First pending is blocking? → Activate it alone
    │              (this starts serial mode)
    │
    └─ For each activated entry:
       ├─ Determine base branch (oldest open blocking issue's branch, or "main")
       ├─ Call mark_active(repo_key, issue_number, parent_branch)
       └─ Return list of activated issues for agent assignment
```

### Base Branch Resolution

```text
get_base_ref_for_issue(repo_key, issue_number):
    │
    ├─ Find oldest open blocking issue (active or in_review)
    │  WHERE repo_key = ? AND is_blocking = 1
    │  AND queue_status IN ('active', 'in_review')
    │  ORDER BY created_at ASC LIMIT 1
    │
    ├─ Found? → Return that issue's parent_branch
    │           Record blocking_source_issue on the requesting entry
    │
    └─ Not found? → Return "main"
```

### 8-Issue Example Walkthrough

This validates the activation rules using the scenario from the spec (SC-009):

```text
Queue (creation order):
  1. Issue #1 — blocking
  2. Issue #2 — non-blocking
  3. Issue #3 — non-blocking
  4. Issue #4 — blocking
  5. Issue #5 — non-blocking
  6. Issue #6 — blocking
  7. Issue #7 — non-blocking
  8. Issue #8 — non-blocking

Step 1: Issue #1 created (blocking)
  → No open blocking issues → activate immediately
  → Branches from "main"
  Queue: [#1=active, #2-#8 not yet created]

Step 2: Issues #2-#8 created while #1 is active
  → #1 is active blocking → all enter "pending"
  Queue: [#1=active, #2=pending, #3=pending, ..., #8=pending]

Step 3: Issue #1 → "in review"
  → mark_in_review(#1)
  → try_activate_next(): #1 is in_review (blocking, still open)
  → Serial mode: next pending is #2 (non-blocking)
  → Activate #2 AND #3 (consecutive non-blocking, stop at #4 which is blocking)
  → #2 and #3 branch from #1's branch (oldest open blocking)
  Queue: [#1=in_review, #2=active, #3=active, #4=pending, ..., #8=pending]

Step 4: Issues #2 and #3 → "in review"
  → try_activate_next(): still have #1 in_review (blocking, open)
  → No active entries, next pending is #4 (blocking)
  → Activate #4 alone (blocking entries activate alone)
  → #4 branches from #1's branch (oldest open blocking)
  Queue: [#1=in_review, #2=in_review, #3=in_review, #4=active, #5=pending, ..., #8=pending]

Step 5: Issue #1 → "completed"
  → mark_completed(#1)
  → try_activate_next(): #4 is active (blocking)
  → Can't activate more while blocking issue is active
  Queue: [#1=completed, #2=in_review, #3=in_review, #4=active, #5=pending, ..., #8=pending]

Step 6: Issues #2, #3 → "completed", #4 → "in review"
  → try_activate_next(): #4 is in_review (blocking, still open)
  → Next pending is #5 (non-blocking)
  → Activate #5 alone (only one non-blocking before #6 which is blocking)
  → #5 branches from #4's branch (oldest open blocking)
  Queue: [#1-#3=completed, #4=in_review, #5=active, #6=pending, #7=pending, #8=pending]

Step 7: #5 → "in review"
  → try_activate_next(): #4 still in_review (blocking, open)
  → Next pending is #6 (blocking)
  → Activate #6 alone (blocking entries activate alone)
  → #6 branches from #4's branch (oldest open blocking)
  Queue: [#1-#3=completed, #4=in_review, #5=in_review, #6=active, #7=pending, #8=pending]

Step 8: #4 → "completed"
  → try_activate_next(): #6 is active (blocking)
  → Can't activate more while blocking issue is active
  Queue: [#1-#4=completed, #5=in_review, #6=active, #7=pending, #8=pending]

Step 9: #5 → "completed", #6 → "in review"
  → try_activate_next(): #6 is in_review (blocking, still open)
  → Next pending is #7 (non-blocking)
  → Activate #7 AND #8 (consecutive non-blocking, no more entries)
  → #7 and #8 branch from #6's branch (oldest open blocking)
  Queue: [#1-#5=completed, #6=in_review, #7=active, #8=active]

Step 10: #6, #7, #8 → "completed"
  → All completed. No open blocking issues.
  → Future issues branch from "main"
```

---

## Existing Entities (Unchanged — Referenced Only)

The following existing entities are referenced but not structurally modified:

- **ConnectionManager** (`backend/src/services/websocket.py`): Used to broadcast `blocking_queue_updated` events to project WebSocket connections.
- **WorkflowResult** (`backend/src/models/workflow.py`): Orchestrator return type — a new `pending` status variant is needed for blocked issues.
- **BoardItem** (`backend/src/models/board.py`): Frontend issue card model — `labels` field used to display blocking indicators.
