# Data Model: Housekeeping Issue Templates with Configurable Triggers

**Feature**: 014-housekeeping-triggers | **Date**: 2026-02-28

## Entity: Issue Template

**Purpose**: Reusable GitHub Issue template that defines the title pattern and body content for parent issues created by housekeeping tasks.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string (UUID) | Unique identifier | Primary key, auto-generated |
| name | string | Display name for the template | Required, unique, max 200 chars |
| title_pattern | string | Title pattern for generated issues (supports `{date}`, `{task_name}` placeholders) | Required, max 500 chars |
| body_content | text | Markdown body content for generated issues | Required |
| category | enum | `built-in` \| `custom` | Required, default `custom` |
| created_at | datetime (ISO 8601) | Creation timestamp | Required, auto-set |
| updated_at | datetime (ISO 8601) | Last update timestamp | Required, auto-updated |

**Validation Rules**:
- `name` must be unique across all templates in the project
- `built-in` templates cannot be deleted (only duplicated)
- `title_pattern` must contain valid placeholder syntax
- `body_content` must be valid markdown

---

## Entity: Housekeeping Task

**Purpose**: A named, recurring maintenance task definition with trigger configuration and state tracking.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string (UUID) | Unique identifier | Primary key, auto-generated |
| name | string | Display name for the task | Required, unique, max 200 chars |
| description | string | Optional description of the task purpose | Optional, max 1000 chars |
| template_id | string (UUID) | Reference to the issue template used | Required, FK → Issue Template.id |
| sub_issue_config | JSON | Agent pipeline sub-issue configuration | Optional, defaults to Spec Kit DEFAULT_AGENT_MAPPINGS |
| trigger_type | enum | `time` \| `count` | Required, mutually exclusive |
| trigger_value | string | Cron expression (for `time`) or integer threshold string (for `count`) | Required |
| last_triggered_at | datetime (ISO 8601) | Timestamp of last successful trigger | Nullable, null if never triggered |
| last_triggered_issue_count | integer | Parent issue count baseline at last trigger | Default 0 |
| enabled | boolean | Whether the task's automatic triggers are active | Required, default true |
| cooldown_minutes | integer | Minimum minutes between triggers (idempotency guard) | Required, default 5 |
| project_id | string | GitHub Project node ID this task belongs to | Required |
| created_at | datetime (ISO 8601) | Creation timestamp | Required, auto-set |
| updated_at | datetime (ISO 8601) | Last update timestamp | Required, auto-updated |

**Validation Rules**:
- `name` must be unique within the same `project_id`
- `template_id` must reference an existing Issue Template
- When `trigger_type` is `time`, `trigger_value` must be a valid cron expression or named preset (daily, weekly, monthly)
- When `trigger_type` is `count`, `trigger_value` must be a positive integer string
- `trigger_type` and `trigger_value` are mutually consistent (no cron for count, no integer for time)
- `cooldown_minutes` must be ≥ 1
- `sub_issue_config` when provided must be a valid agent pipeline mapping structure

---

## Entity: Trigger Event (History)

**Purpose**: Immutable historical record of a housekeeping task execution, providing auditability and troubleshooting.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | string (UUID) | Unique identifier | Primary key, auto-generated |
| task_id | string (UUID) | Reference to the housekeeping task | Required, FK → Housekeeping Task.id |
| timestamp | datetime (ISO 8601) | When the trigger fired | Required, auto-set |
| trigger_type | enum | `scheduled` \| `count-based` \| `manual` | Required |
| issue_url | string (URL) | URL of the created GitHub Issue | Nullable (null if creation failed) |
| issue_number | integer | GitHub Issue number | Nullable (null if creation failed) |
| status | enum | `success` \| `failure` | Required |
| error_details | text | Error description if status is `failure` | Nullable, populated on failure |
| sub_issues_created | integer | Number of sub issues successfully created | Default 0 |

**Validation Rules**:
- `task_id` must reference an existing Housekeeping Task
- When `status` is `success`, `issue_url` and `issue_number` must be non-null
- When `status` is `failure`, `error_details` should be non-empty
- Records are append-only (no updates or deletes)

---

## Entity: Agent Pipeline Configuration (Reference)

**Purpose**: The project board's sub-issue generation mapping. This entity already exists in the system (`DEFAULT_AGENT_MAPPINGS` in `constants.py` and `WorkflowConfiguration` in `models/workflow.py`). Housekeeping tasks reference it, not define it.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| status_column | string | Workflow status column name | One of: Backlog, Ready, In Progress, In Review |
| agents | list[string] | Agent slugs assigned to this status | Valid agent identifiers from AGENT_DISPLAY_NAMES |

**Default (Spec Kit pipeline)**: From `constants.DEFAULT_AGENT_MAPPINGS`:
- Backlog → `speckit.specify`
- Ready → `speckit.plan`, `speckit.tasks`
- In Progress → `speckit.implement`
- In Review → `copilot-review`

---

## Relationships

```
Issue Template 1──* Housekeeping Task     (one template can be used by many tasks)
Housekeeping Task 1──* Trigger Event      (one task has many historical trigger events)
Housekeeping Task *──1 Agent Pipeline     (task references pipeline config, defaults to Spec Kit)
```

## State Transitions

### Housekeeping Task Lifecycle
```
created (enabled=true) → [trigger condition met] → evaluating
evaluating → [cooldown check passes] → executing
evaluating → [cooldown check fails] → skipped (no history entry)
executing → [issue created successfully] → triggered (history: success)
executing → [API error] → failed (history: failure)
triggered → [next trigger condition] → evaluating (cycle repeats)

enabled → [user disables] → disabled (triggers stop, config preserved)
disabled → [user enables] → enabled (triggers resume from current state)
disabled → [manual "Run Now"] → executing (manual override bypasses enabled check)
```

### Template Lifecycle
```
created → [referenced by tasks] → in-use
in-use → [edit] → updated (future triggers use new content)
in-use → [delete attempted] → warning (active tasks reference this template)
in-use → [delete confirmed] → deleted (referencing tasks become invalid)
not-referenced → [delete] → deleted (no warning needed)
built-in → [delete attempted] → blocked (built-in templates cannot be deleted)
built-in → [duplicate] → new custom template created from built-in content
```

### Trigger Evaluation Flow
```
[time-based] GitHub Actions cron fires → backend /api/v1/housekeeping/evaluate-triggers
  → for each enabled time-based task:
    → parse cron expression
    → compare with last_triggered_at
    → if due AND outside cooldown → execute
    → else → skip

[count-based] Webhook: issues.opened event → backend webhook handler
  → increment global parent issue count
  → for each enabled count-based task:
    → current_count - last_triggered_issue_count >= trigger_value?
    → if yes AND outside cooldown → execute
    → else → skip

[manual] User clicks "Run Now" → backend /api/v1/housekeeping/tasks/{id}/run
  → cooldown warning if within window (user can confirm)
  → execute regardless of enabled/disabled state
```

## SQLite Schema

```sql
-- Migration: 006_housekeeping.sql

CREATE TABLE IF NOT EXISTS housekeeping_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    title_pattern TEXT NOT NULL,
    body_content TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'custom' CHECK(category IN ('built-in', 'custom')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS housekeeping_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    template_id TEXT NOT NULL REFERENCES housekeeping_templates(id),
    sub_issue_config TEXT,  -- JSON, NULL means use default agent pipeline
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('time', 'count')),
    trigger_value TEXT NOT NULL,
    last_triggered_at TEXT,
    last_triggered_issue_count INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1,
    cooldown_minutes INTEGER NOT NULL DEFAULT 5,
    project_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, project_id)
);

CREATE TABLE IF NOT EXISTS housekeeping_trigger_history (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES housekeeping_tasks(id),
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    trigger_type TEXT NOT NULL CHECK(trigger_type IN ('scheduled', 'count-based', 'manual')),
    issue_url TEXT,
    issue_number INTEGER,
    status TEXT NOT NULL CHECK(status IN ('success', 'failure')),
    error_details TEXT,
    sub_issues_created INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_trigger_history_task_id ON housekeeping_trigger_history(task_id);
CREATE INDEX IF NOT EXISTS idx_trigger_history_timestamp ON housekeeping_trigger_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_housekeeping_tasks_project ON housekeeping_tasks(project_id);
```
