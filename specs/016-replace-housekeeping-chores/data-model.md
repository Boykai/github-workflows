# Data Model: Replace Housekeeping with Chores

**Feature**: 016-replace-housekeeping-chores  
**Date**: 2026-03-02

## Entities

### Chore

A recurring maintenance task definition, belonging to a project.

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | TEXT (UUID) | No | Primary key |
| `project_id` | TEXT | No | Foreign key to associated GitHub Project (project node ID) |
| `name` | TEXT | No | Chore display name |
| `template_path` | TEXT | No | Path to `.md` template in repo (e.g., `.github/ISSUE_TEMPLATE/bug-bash.md`) |
| `template_content` | TEXT | No | Full cached template content (YAML front matter + markdown body) |
| `schedule_type` | TEXT | Yes | `'time'` or `'count'`; NULL if not yet configured |
| `schedule_value` | INTEGER | Yes | Days (time-based) or parent issue count (count-based); NULL if not yet configured |
| `status` | TEXT | No | `'active'` or `'paused'`; default `'active'` |
| `last_triggered_at` | TEXT (ISO 8601) | Yes | Datetime of last trigger; NULL if never triggered |
| `last_triggered_count` | INTEGER | No | Parent issue count at last trigger; default `0` |
| `current_issue_number` | INTEGER | Yes | GitHub issue number of currently open triggered issue; NULL if none |
| `current_issue_node_id` | TEXT | Yes | GraphQL node ID of currently open triggered issue; NULL if none |
| `pr_number` | INTEGER | Yes | PR number for the template commit; NULL if template was created without PR |
| `pr_url` | TEXT | Yes | URL of the template PR |
| `tracking_issue_number` | INTEGER | Yes | GitHub issue tracking the template review; NULL if N/A |
| `created_at` | TEXT (ISO 8601) | No | Creation timestamp |
| `updated_at` | TEXT (ISO 8601) | No | Last update timestamp |

**Constraints**:
- UNIQUE (`name`, `project_id`) — no duplicate chore names within a project
- CHECK (`schedule_type IN ('time', 'count')` OR `schedule_type IS NULL`)
- CHECK (`status IN ('active', 'paused')`)

**Indexes**:
- `idx_chores_project_id` ON `chores(project_id)` — fast lookup by project
- `idx_chores_status` ON `chores(status)` — filter active chores for trigger evaluation

### Relationships

```
Project (GitHub Project ID)
  └── has many → Chore
                   ├── references → GitHub Issue Template (.md file in repo)
                   ├── references → Current Open Issue (GitHub Issue number/node_id)
                   ├── references → Template PR (GitHub PR number)
                   └── references → Tracking Issue (GitHub Issue number)
```

### Validation Rules

1. `name` must be non-empty, max 200 characters
2. `template_path` must match pattern `.github/ISSUE_TEMPLATE/*.md`
3. `schedule_value` must be > 0 when `schedule_type` is set
4. `schedule_type` and `schedule_value` must both be set or both be NULL
5. `status` defaults to `'active'` on creation

### State Transitions

```
[Created] → active (default, schedule not yet configured)
    ↓
active ←→ paused (user toggles status)
    ↓
active + schedule configured → eligible for trigger evaluation
    ↓
trigger condition met + no open instance → TRIGGER
    ↓
[Triggered] → current_issue_number set, last_triggered_at/count reset
    ↓
open issue closed externally → current_issue_number cleared (detected on next eval)
    ↓
[Removed] → chore deleted from DB, open issue closed if exists
```

## SQL Schema

```sql
-- Migration 010_chores.sql

-- Drop housekeeping tables
DROP TABLE IF EXISTS housekeeping_trigger_history;
DROP TABLE IF EXISTS housekeeping_tasks;
DROP TABLE IF EXISTS housekeeping_templates;

-- Create chores table
CREATE TABLE IF NOT EXISTS chores (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    template_path TEXT NOT NULL,
    template_content TEXT NOT NULL,
    schedule_type TEXT CHECK(schedule_type IN ('time', 'count') OR schedule_type IS NULL),
    schedule_value INTEGER,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'paused')),
    last_triggered_at TEXT,
    last_triggered_count INTEGER NOT NULL DEFAULT 0,
    current_issue_number INTEGER,
    current_issue_node_id TEXT,
    pr_number INTEGER,
    pr_url TEXT,
    tracking_issue_number INTEGER,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(name, project_id),
    CHECK(
        (schedule_type IS NULL AND schedule_value IS NULL) OR
        (schedule_type IS NOT NULL AND schedule_value IS NOT NULL AND schedule_value > 0)
    )
);

CREATE INDEX IF NOT EXISTS idx_chores_project_id ON chores(project_id);
CREATE INDEX IF NOT EXISTS idx_chores_status ON chores(status);
```

## Pydantic Models

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class ScheduleType(str, Enum):
    TIME = "time"
    COUNT = "count"

class ChoreStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"

class Chore(BaseModel):
    id: str
    project_id: str
    name: str
    template_path: str
    template_content: str
    schedule_type: ScheduleType | None = None
    schedule_value: int | None = None
    status: ChoreStatus = ChoreStatus.ACTIVE
    last_triggered_at: datetime | None = None
    last_triggered_count: int = 0
    current_issue_number: int | None = None
    current_issue_node_id: str | None = None
    pr_number: int | None = None
    pr_url: str | None = None
    tracking_issue_number: int | None = None
    created_at: datetime
    updated_at: datetime

class ChoreCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    template_content: str = Field(..., min_length=1)

class ChoreUpdate(BaseModel):
    schedule_type: ScheduleType | None = None
    schedule_value: int | None = Field(None, gt=0)
    status: ChoreStatus | None = None

class ChoreTriggerResult(BaseModel):
    chore_id: str
    chore_name: str
    triggered: bool
    issue_number: int | None = None
    issue_url: str | None = None
    skip_reason: str | None = None

class EvaluateChoreTriggersResponse(BaseModel):
    evaluated: int
    triggered: int
    skipped: int
    results: list[ChoreTriggerResult]

class ChoreChatMessage(BaseModel):
    content: str
    conversation_id: str | None = None

class ChoreChatResponse(BaseModel):
    message: str
    conversation_id: str
    template_ready: bool = False
    template_content: str | None = None
    template_name: str | None = None
```
