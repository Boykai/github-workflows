# Data Model: Remove Blocking Feature Entirely from Application

**Branch**: `035-remove-blocking-feature` | **Date**: 2026-03-12 | **Plan**: [plan.md](./plan.md)

## Entities Being Removed

This document describes the data model entities that will be removed as part of the blocking feature removal. No new entities are being created.

---

### Entity: BlockingQueue (TABLE — to be dropped)

**Database table**: `blocking_queue`
**Created by**: Migration 017 (`017_blocking_queue.sql`)
**Status**: Table exists in schema but service code was never implemented

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Auto-increment row ID |
| `repo_key` | TEXT | NOT NULL | Repository identifier (owner/repo format) |
| `issue_number` | INTEGER | NOT NULL | GitHub issue number |
| `project_id` | TEXT | NOT NULL | GitHub project ID |
| `is_blocking` | INTEGER | NOT NULL DEFAULT 0 | Whether issue was marked as blocking |
| `queue_status` | TEXT | NOT NULL DEFAULT 'pending' | One of: pending, active, in_review, completed |
| `parent_branch` | TEXT | | Base branch for the blocking issue |
| `blocking_source_issue` | INTEGER | | Issue number of the blocking dependency |
| `created_at` | TEXT | NOT NULL DEFAULT datetime('now') | Timestamp of queue entry creation |
| `activated_at` | TEXT | | Timestamp when issue was activated |
| `completed_at` | TEXT | | Timestamp when issue was completed |

**Indexes to drop**:
- `idx_blocking_queue_repo_status` on `(repo_key, queue_status)`
- `idx_blocking_queue_repo_blocking` on `(repo_key, is_blocking, queue_status)`

**Unique constraint**: `UNIQUE(repo_key, issue_number)`

**Relationships**: None (self-contained table, no foreign keys to/from other tables)

---

### Entity: BlockingQueueStatus (ENUM — never implemented)

**Expected location**: `backend/src/models/blocking.py` (file never created)
**Referenced by**: `recovery.py`, `test_api_board.py`

| Value | Description |
|-------|-------------|
| `PENDING` | Issue queued, waiting for activation |
| `ACTIVE` | Issue currently active in the pipeline |
| `IN_REVIEW` | Issue in review stage |
| `COMPLETED` | Issue completed and dequeued |

**Action**: No file to delete since it was never created. Remove all import references.

---

### Entity: BlockingQueueEntry (MODEL — never implemented)

**Expected location**: `backend/src/models/blocking.py` (file never created)
**Referenced by**: `test_api_board.py`

Would have been a Pydantic model mirroring the `blocking_queue` table schema.

**Action**: No file to delete since it was never created. Remove all import references.

---

### Column Removals from Existing Tables

#### pipeline_configs.blocking

| Field | Type | Default | Added by |
|-------|------|---------|----------|
| `blocking` | INTEGER | NOT NULL DEFAULT 0 | Migration 017 |

**Purpose**: Flag to indicate whether a pipeline config creates blocking issues by default.
**Action**: Drop column via Migration 019.

#### chores.blocking

| Field | Type | Default | Added by |
|-------|------|---------|----------|
| `blocking` | INTEGER | NOT NULL DEFAULT 0 | Migration 017 |

**Purpose**: Flag to indicate whether a chore creates blocking issues.
**Action**: Drop column via Migration 019. Also remove from chore preset definitions and `_CHORE_UPDATABLE_COLUMNS`.

#### project_settings.pipeline_blocking_override

| Field | Type | Default | Added by |
|-------|------|---------|----------|
| `pipeline_blocking_override` | INTEGER | NULL | Migration 018 |

**Purpose**: Project-level override for pipeline blocking behavior (NULL=inherit, 0=force OFF, 1=force ON).
**Action**: Drop column via Migration 019.

---

### Fields Never Added to Models (references only)

These fields are referenced in code but were never added to the actual Pydantic models:

| Model | Field | Referenced in |
|-------|-------|---------------|
| `AITaskProposal` | `is_blocking: bool` | `api/chat.py:763` |
| `IssueRecommendation` | `is_blocking: bool` | `api/workflow.py:269`, `signal_chat.py:389` |
| `ProjectPipelineAssignment` | `blocking_override` | `chores/service.py:548-549` |

**Action**: Remove the code that accesses these non-existent fields.

---

## State Transitions (being removed)

The blocking queue had a planned state machine:

```
pending → active → in_review → completed
                       ↓
                   completed
```

- **pending**: Issue enqueued, waiting for previous blocking issues to complete
- **active**: Issue activated, agent assignment proceeds
- **in_review**: Issue has open PRs in review
- **completed**: Issue done, next pending issue activated

This entire state machine is removed. Issues will proceed directly through the pipeline without any queue gating.
