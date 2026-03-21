# Data Model: ChoresPanel Pagination Migration

**Feature**: 057-chores-pagination-migration
**Date**: 2026-03-21

## Entities

### Chore (existing — no schema changes)

The core entity. No modifications to the database schema or model are needed. Filtering and sorting operate on the existing fields.

| Field | Type | Description | Filterable | Sortable |
|-------|------|-------------|:----------:|:--------:|
| `id` | string | Unique identifier (UUID) | — | — |
| `project_id` | string | Foreign key to project | — (path param) | — |
| `name` | string | Chore display name | ✅ (search) | ✅ (`name`) |
| `template_path` | string | Path to the chore template file | ✅ (search) | — |
| `template_content` | string | Template body content | — | — |
| `schedule_type` | `"time"` \| `"count"` \| `null` | Schedule type | ✅ (`schedule_type`) | — |
| `schedule_value` | int \| null | Schedule interval value | — | — |
| `status` | `"active"` \| `"paused"` | Chore status | ✅ (`status`) | — |
| `last_triggered_at` | string \| null | ISO timestamp of last trigger | — | — |
| `last_triggered_count` | int | Counter for trigger-based schedules | — | — |
| `current_issue_number` | int \| null | Currently open issue number | — | — (used in attention sort) |
| `current_issue_node_id` | string \| null | GraphQL node ID of current issue | — | — |
| `pr_number` | int \| null | Associated PR number | — | — |
| `pr_url` | string \| null | Associated PR URL | — | — |
| `tracking_issue_number` | int \| null | Parent tracking issue | — | — |
| `execution_count` | int | Total execution count | — | — |
| `ai_enhance_enabled` | bool | Whether AI enhancement is enabled | — | — |
| `agent_pipeline_id` | string | Pipeline configuration ID | — | — |
| `is_preset` | bool | Whether this is a preset chore | — | — |
| `preset_id` | string | Preset identifier (if preset) | — | — |
| `created_at` | string | ISO timestamp of creation | — | ✅ (`created_at`, default) |
| `updated_at` | string | ISO timestamp of last update | — | ✅ (`updated_at`) |

### PaginatedResponse\<T\> (existing — no changes)

Generic pagination wrapper returned by `apply_pagination()`.

| Field | Type | Description |
|-------|------|-------------|
| `items` | `list[T]` | Current page of results |
| `next_cursor` | string \| null | Opaque cursor for next page (base64-encoded item ID) |
| `has_more` | bool | Whether more pages exist |
| `total_count` | int | Total items matching the query (pre-pagination) |

### Filter Parameters (new — query string only, no persistence)

These are transient query parameters, not persisted entities. They control which chores are returned and in what order.

| Parameter | Type | Values | Default | Description |
|-----------|------|--------|---------|-------------|
| `status` | string \| null | `"active"`, `"paused"` | null (all) | Filter by chore status |
| `schedule_type` | string \| null | `"time"`, `"count"`, `"unscheduled"` | null (all) | Filter by schedule type; `"unscheduled"` matches null |
| `search` | string \| null | free text | null (no filter) | Case-insensitive substring match on `name` or `template_path` |
| `sort` | string \| null | `"name"`, `"updated_at"`, `"created_at"`, `"attention"` | `"created_at"` | Sort field |
| `order` | string \| null | `"asc"`, `"desc"` | `"asc"` | Sort direction |

## Relationships

```
Project 1──* Chore
  └── project_id (FK, path parameter)

Chore *──? Issue
  └── current_issue_number (nullable FK to GitHub issue)

Chore *──? PullRequest
  └── pr_number (nullable FK to GitHub PR)
```

No new relationships are introduced. The pagination migration does not alter entity relationships.

## Validation Rules

### Filter Parameter Validation (backend)

| Rule | Implementation |
|------|---------------|
| `status` must be a valid `ChoreStatus` value or omitted | FastAPI Query param with validation |
| `schedule_type` must be `"time"`, `"count"`, `"unscheduled"`, or omitted | FastAPI Query param with validation |
| `search` is free-form text, no length limit enforced | Stripped and lowercased for matching |
| `sort` must be one of the accepted sort fields or omitted | FastAPI Query param with validation |
| `order` must be `"asc"` or `"desc"` or omitted | FastAPI Query param with validation |
| `limit` must be 1–100 (existing) | Already enforced by FastAPI `Query(ge=1, le=100)` |
| `cursor` must be a valid base64 cursor or omitted (existing) | Already validated by `apply_pagination()` |

### State Transitions

No state transitions are introduced or modified. Chore status transitions (`active` ↔ `paused`) are unchanged and handled by separate endpoints (update chore).

## Frontend Type Additions

### ChoresFilterParams (new TypeScript interface)

```typescript
interface ChoresFilterParams {
  status?: string;
  scheduleType?: string;
  search?: string;
  sort?: string;
  order?: string;
}
```

This interface is used internally in the frontend to pass filter state from ChoresPanel → `useChoresListPaginated()` → `choresApi.listPaginated()`. It is not persisted or transmitted directly — values are serialized as individual query parameters in the URL.
