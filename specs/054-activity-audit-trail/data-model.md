# Data Model: Activity Log / Audit Trail

**Feature**: `054-activity-audit-trail` | **Date**: 2026-03-20
**Input**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### ActivityEvent

The core entity representing a single recorded action in the system. Immutable once created.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| `id` | TEXT | PK, UUID | Unique event identifier |
| `event_type` | TEXT | NOT NULL, CHECK | Category of action (see Event Types enum) |
| `entity_type` | TEXT | NOT NULL, CHECK | Type of affected resource (see Entity Types enum) |
| `entity_id` | TEXT | NOT NULL | Identifier of the affected resource |
| `project_id` | TEXT | NOT NULL | Project scope for feed queries |
| `actor` | TEXT | NOT NULL | User identifier or "system" |
| `action` | TEXT | NOT NULL, CHECK | Verb describing what happened (see Actions enum) |
| `summary` | TEXT | NOT NULL | Human-readable one-liner (e.g., "Pipeline 'deploy-prod' completed successfully") |
| `detail` | TEXT | NULL, JSON | Structured metadata blob (old/new values, error messages, stage data) |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | ISO 8601 timestamp of when the event occurred |

**Indexes**:
- `idx_activity_project_time` on `(project_id, created_at DESC)` — Primary feed query
- `idx_activity_entity` on `(entity_type, entity_id)` — Entity-scoped history query

**Validation rules**:
- `event_type` must be one of the defined event types
- `entity_type` must be one of the defined entity types
- `action` must be one of the defined actions
- `summary` must be non-empty
- `detail` must be valid JSON when present

---

### Enums

#### Event Types

```
pipeline_run      — Pipeline execution lifecycle (created, started, completed, failed, cancelled)
pipeline_stage    — Individual pipeline stage completion or failure
chore_trigger     — Chore trigger evaluation and execution
chore_crud        — Chore create, update, or delete operation
agent_crud        — Agent create, update, or delete operation
agent_execution   — Agent task execution lifecycle
cleanup           — Cleanup operation (branch/PR pruning)
app_crud          — App create, update, or delete operation
tool_crud         — Tool create, update, or delete operation
status_change     — Workflow/issue status transition
webhook           — Inbound GitHub webhook event
```

#### Entity Types

```
pipeline   — Pipeline configuration or run
chore      — Scheduled/triggered chore
agent      — AI agent assignment
app        — Installed application
tool       — MCP tool
issue       — GitHub issue (for status changes, webhooks)
```

#### Actions

```
created     — Resource was created
updated     — Resource was modified
deleted     — Resource was removed
triggered   — Chore or pipeline was triggered
started     — Execution began
completed   — Execution finished successfully
failed      — Execution finished with error
cancelled   — Execution was cancelled
moved       — Issue/item changed status column
```

---

## Relationships

```
ActivityEvent
  ├── project_id → scopes to a project (logical FK, not enforced)
  ├── entity_type + entity_id → references the affected resource (polymorphic)
  └── actor → identifies the user or "system" (no FK to users table)
```

- **Project scoping**: Every event belongs to exactly one project. The feed is always scoped to a `project_id`.
- **Polymorphic entity reference**: `entity_type` + `entity_id` together identify the resource. No foreign key constraint because the referenced entity may be deleted (edge case: deleted entity events still display with summary text).
- **Actor**: String identifier — either a GitHub username or "system" for automated actions. No FK to a users table (the app doesn't have a persistent users table beyond sessions).

---

## State Transitions

ActivityEvent is **immutable** — once created, it is never updated or deleted (in v1). There are no state transitions on the event itself.

The events *describe* state transitions of other entities:

```
Pipeline Run Lifecycle:
  [none] → created → started → completed | failed | cancelled

Chore Trigger Lifecycle:
  [none] → triggered → completed | failed

CRUD Operations:
  [none] → created | updated | deleted  (single event, no lifecycle)

Cleanup Operation:
  [none] → started → completed

Workflow Status Change:
  [none] → moved  (captures from_status → to_status in detail)
```

---

## Backend Models (Pydantic)

### ActivityEvent (response model)

```python
class ActivityEvent(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    project_id: str
    actor: str
    action: str
    summary: str
    detail: dict[str, Any] | None = None
    created_at: str
```

### ActivityEventCreate (internal model for log_event)

```python
class ActivityEventCreate(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str
    project_id: str
    actor: str
    action: str
    summary: str
    detail: dict[str, Any] | None = None
```

Note: `id` is generated server-side (UUID), `created_at` is set by database default.

---

## Frontend Types (TypeScript)

### ActivityEvent

```typescript
export interface ActivityEvent {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  project_id: string;
  actor: string;
  action: string;
  summary: string;
  detail?: Record<string, unknown>;
  created_at: string;
}
```

### Notification (existing type — extended mapping)

The existing `Notification` interface is reused for the notification bell. Activity events are mapped to notifications:

```typescript
// Existing type (no changes needed):
export interface Notification {
  id: string;
  type: 'agent' | 'chore';
  title: string;
  timestamp: string;
  read: boolean;
  source?: string;
}

// Mapping: ActivityEvent → Notification
// event.id → notification.id
// event.event_type → notification.type (mapped: pipeline_run/agent_* → 'agent', chore_* → 'chore')
// event.summary → notification.title
// event.created_at → notification.timestamp
// readIds.has(event.id) → notification.read
// event.entity_type → notification.source
```

---

## Detail Payload Schemas (by event type)

The `detail` field contains structured metadata specific to the event type. Examples:

### Pipeline Run Events

```json
{
  "pipeline_name": "deploy-prod",
  "run_id": "run-abc-123",
  "status": "completed",
  "duration_ms": 45200,
  "stages_completed": 3,
  "stages_total": 3
}
```

### Pipeline Stage Events

```json
{
  "pipeline_name": "deploy-prod",
  "stage_name": "code-review",
  "agent_slug": "code-reviewer",
  "status": "completed",
  "duration_ms": 12300
}
```

### Workflow Status Change Events

```json
{
  "from_status": "In Progress",
  "to_status": "Done",
  "triggered_by": "agent",
  "issue_number": 42
}
```

### CRUD Events

```json
{
  "entity_name": "nightly-cleanup",
  "changes": {
    "schedule_type": { "old": "interval", "new": "cron" }
  }
}
```

### Chore Trigger Events

```json
{
  "chore_name": "nightly-cleanup",
  "trigger_type": "cron",
  "result_count": 5
}
```

### Webhook Events

```json
{
  "webhook_type": "pull_request",
  "action": "opened",
  "sender": "octocat",
  "repository": "owner/repo"
}
```

### Cleanup Events

```json
{
  "branches_deleted": 3,
  "prs_closed": 1,
  "duration_ms": 2100
}
```
