# Data Model: Audit & Polish Projects Page for Visual Cohesion and UX Quality

**Feature Branch**: `034-projects-page-audit`
**Date**: 2026-03-11

## Overview

This document describes the key entities rendered on the Projects page and their relationships. Since this is an audit-and-polish feature (no new entities), the data model captures the **existing** entities that components interact with, their validation rules, and state transitions. This serves as a reference for auditing component correctness.

## Entity Diagram

```text
┌─────────────────────┐
│   BoardProject      │
│   (project_id, name,│
│    owner_login,     │
│    status_field)    │
└────────┬────────────┘
         │ 1
         │
         │ has many
         ▼
┌─────────────────────┐
│   BoardColumn       │──────────────────┐
│   (status, items[], │                  │
│    item_count,      │                  │ each column has
│    estimate_total)  │                  │ a status option
└────────┬────────────┘                  │
         │ contains                       ▼
         │                       ┌──────────────────┐
         ▼                       │ BoardStatusOption │
┌─────────────────────┐          │ (option_id, name, │
│   BoardItem         │          │  color, desc)     │
│   (item_id, title,  │          └──────────────────┘
│    number, status,  │
│    assignees[],     │
│    labels[],        │
│    priority,        │
│    sub_issues[],    │
│    linked_prs[])    │
└────────┬────────────┘
         │
    ┌────┴─────┬──────────┬──────────┐
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐
│Assignee│ │ Label  │ │SubIssue│ │LinkedPR │
└────────┘ └────────┘ └────────┘ └─────────┘
```

## Entities

### BoardProject

The top-level entity representing a GitHub Project V2.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id` | string | ✅ | Unique GitHub Project node ID |
| `name` | string | ✅ | Project display name |
| `description` | string | ❌ | Optional project description |
| `url` | string | ✅ | GitHub URL to the project |
| `owner_login` | string | ✅ | GitHub org/user login that owns the project |
| `status_field` | BoardStatusField | ✅ | Status field configuration with available options |

**Validation Rules**:

- `project_id` must be a non-empty string
- `name` must be a non-empty string
- `status_field.options` must contain at least one option

**UI Rendering Notes**:

- Displayed in the project selector button as `name` with `owner_login` subtitle
- First character of `name` shown as avatar initial in the selector
- Full `owner_login/name` shown in the hero badge

---

### BoardColumn

A status column in the Kanban board, representing one status option.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | BoardStatusOption | ✅ | The status this column represents |
| `items` | BoardItem[] | ✅ | Items currently in this status (may be empty) |
| `item_count` | number | ✅ | Total count of items (may differ from items.length if paginated) |
| `estimate_total` | number | ✅ | Sum of estimate values for items in this column |

**Validation Rules**:

- `items` may be an empty array (valid empty column)
- `item_count >= 0`
- `estimate_total >= 0`

**UI Rendering Notes**:

- Rendered as a vertical column in `BoardColumn.tsx`
- Column header shows status name, color dot, item count, and estimate total
- Empty columns display normally (no special empty state — the board-level empty state handles all-empty)
- Pipeline stage cards show the same columns with assigned agents

**State Transitions**:

Columns are read-only in the UI; items move between columns via GitHub Project status changes.

---

### BoardItem

An individual item (issue, draft issue, or PR) on the board.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | string | ✅ | GitHub Project item node ID |
| `content_id` | string | ❌ | GitHub content node ID (issue/PR) |
| `content_type` | `'issue' \| 'draft_issue' \| 'pull_request'` | ✅ | Type of content |
| `title` | string | ✅ | Item title |
| `number` | number | ❌ | Issue/PR number (absent for draft issues) |
| `repository` | BoardRepository | ❌ | Repository info (owner + name) |
| `url` | string | ❌ | GitHub URL |
| `body` | string | ❌ | Markdown body content |
| `status` | string | ✅ | Current status name |
| `status_option_id` | string | ✅ | Status option ID |
| `assignees` | BoardAssignee[] | ✅ | Assigned users (may be empty) |
| `priority` | BoardCustomFieldValue | ❌ | Priority field (P0–P3) |
| `size` | BoardCustomFieldValue | ❌ | Size/effort field |
| `estimate` | number | ❌ | Numeric estimate value |
| `linked_prs` | LinkedPR[] | ✅ | Associated pull requests |
| `sub_issues` | SubIssue[] | ✅ | Child issues |
| `labels` | BoardLabel[] | ✅ | Applied labels |
| `created_at` | string (ISO 8601) | ❌ | Creation timestamp |
| `updated_at` | string (ISO 8601) | ❌ | Last update timestamp |
| `milestone` | string | ❌ | Milestone name |

**Validation Rules**:

- `title` must be a non-empty string
- `content_type` must be one of the three allowed values
- `assignees`, `linked_prs`, `sub_issues`, `labels` default to empty arrays
- `priority.name` when present should match pattern `P[0-3]` for correct color mapping

**UI Rendering Notes**:

- Rendered as `IssueCard.tsx` in board columns
- Priority shown with color-coded badge using `--priority-p0` through `--priority-p3` tokens
- Assignee avatars displayed in a stack
- Labels shown as colored chips
- Blocking status indicated via `BlockingIssuePill` overlay
- Click opens `IssueDetailModal` with full details

---

### BoardAssignee

A user assigned to a board item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `login` | string | ✅ | GitHub username |
| `avatar_url` | string | ✅ | Avatar image URL |

**UI Rendering Notes**: Displayed as circular avatar images (stacked when multiple).

---

### BoardLabel

A label applied to a board item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Label ID |
| `name` | string | ✅ | Label display name |
| `color` | string | ✅ | Hex color code (without #) |

**UI Rendering Notes**: Rendered as colored chips. The `color` field is used for background with computed foreground for contrast.

---

### RateLimitInfo

GitHub API rate limit state, surfaced in banners and the global top bar.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | number | ✅ | Maximum requests per window |
| `remaining` | number | ✅ | Remaining requests |
| `reset_at` | number | ✅ | Unix timestamp when limit resets |
| `used` | number | ✅ | Requests used in current window |

**UI Rendering Notes**:

- Rate limit low: Warning banner when `remaining` drops below threshold
- Rate limit reached: Error banner with countdown to `reset_at`
- Published to global context for TopBar display

---

### Pipeline (from pipelinesApi)

Agent pipeline configuration associated with a project.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ | Pipeline UUID |
| `name` | string | ✅ | Pipeline display name |
| `stages` | PipelineStage[] | ✅ | Ordered pipeline stages with agent assignments |
| `blocking` | boolean | ✅ | Whether pipeline enforces blocking queue |

**UI Rendering Notes**:

- Selected via pipeline dropdown in the Pipeline Stages section
- Stages mapped to board columns by name (case-insensitive)
- Blocking toggle shows override state with amber indicator

---

### PipelineAssignment

Links a project to its active pipeline.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pipeline_id` | string | ❌ | Assigned pipeline ID (null = no pipeline) |
| `blocking_override` | boolean | ❌ | Project-level blocking override (null = use pipeline default) |

**UI Rendering Notes**:

- Pipeline selector shows current assignment
- Blocking toggle reflects effective state: `blocking_override ?? pipeline.blocking`

---

## State Transitions

### Page-Level States

```text
┌──────────────┐    project selected    ┌──────────────┐
│  No Project  │ ─────────────────────► │   Loading    │
│  Selected    │                        │   Board      │
└──────────────┘                        └──────┬───────┘
                                               │
                                    ┌──────────┼──────────┐
                                    ▼          ▼          ▼
                              ┌──────────┐ ┌────────┐ ┌───────┐
                              │ Populated│ │ Empty  │ │ Error │
                              │  Board   │ │ Board  │ │       │
                              └──────────┘ └────────┘ └───────┘
                                    │                     │
                                    │    rate limit       │
                                    ▼                     │
                              ┌──────────┐                │
                              │Rate Limit│ ◄──────────────┘
                              │ Banner   │
                              └──────────┘
```

### Sync Status States

```text
disconnected ──► connecting ──► connected
     ▲                │              │
     │                ▼              │
     │           polling ◄───────────┘ (WebSocket failure)
     │                │
     └────────────────┘ (all retries exhausted)
```

### Pipeline Selector States

```text
closed ──► open (click/keyboard)
  ▲           │
  │           ├── option selected → assignment mutation → closed
  │           ├── outside click → closed
  │           └── Escape key → closed
  └───────────┘
```
