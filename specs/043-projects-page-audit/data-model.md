# Data Model: Projects Page Audit

**Feature**: `043-projects-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Entities

### Project

Represents a GitHub Project linked to the application. This is an existing entity — documented here for audit reference.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | `string` | Required, unique | Unique identifier for the project |
| `owner` | `string` | Required | GitHub owner (organization or user) |
| `name` | `string` | Required | Project display name |
| `type` | `ProjectType` | Required, enum: `'organization' \| 'user' \| 'repository'` | Project ownership type |
| `url` | `string` | Required, valid URL | GitHub Project URL |
| `description` | `string \| null` | Optional | Project description |
| `status_columns` | `StatusColumn[]` | Required | Available status columns for the board |
| `item_count` | `number` | Required, ≥0 | Total number of items in the project |

**Validation Rules**:
- `project_id` must be a non-empty string matching the GitHub Project node ID format.
- `name` must be non-empty. Long names (>40 chars) should be truncated in the UI with a tooltip showing the full name (FR-027).
- `description` is nullable — UI must handle `null` gracefully by showing no description rather than "null" text.
- `status_columns` may be empty for newly created projects — the board should show an empty state.

**State Transitions**: N/A — projects are read-only from the application's perspective (managed on GitHub).

---

### BoardProject

Represents a project as displayed in the board context. Extends Project with board-specific metadata.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | `string` | Required, unique | Unique identifier |
| `owner` | `string` | Required | GitHub owner |
| `name` | `string` | Required | Project display name |
| `type` | `ProjectType` | Required | Project ownership type |
| `url` | `string` | Required | GitHub Project URL |
| `status_field` | `BoardStatusField` | Required | Status field configuration |
| `item_count` | `number` | Required, ≥0 | Total items |

**Relationships**:
- Has many `BoardColumn` (derived from `status_field.options`)
- Has zero or one `PipelineAssignment`

---

### BoardColumn

Represents a status-based column in the Kanban board view.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `status` | `BoardStatusOption` | Required | Status option defining this column |
| `items` | `BoardItem[]` | Default: `[]` | Ordered list of items in this column |

**Validation Rules**:
- `items` may be empty — the column should render with its header and an empty body.
- The order of items within `items` determines their display order in the column.

**State Transitions**:
- Items move between columns via drag-and-drop (handled by `useBoardControls`).
- Items may be added to a column via issue creation (handled by `ProjectIssueLaunchPanel`).

---

### BoardStatusOption

Represents a single status option with its visual properties.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `option_id` | `string` | Required, unique within project | Status option identifier |
| `name` | `string` | Required | Display name (e.g., "To Do", "In Progress", "Done") |
| `color` | `string` | Required | Status color identifier from GitHub API |
| `description` | `string \| null` | Optional | Status description |

**Validation Rules**:
- `color` is a GitHub-defined color name (e.g., "GREEN", "YELLOW", "RED"), not a CSS color value. The `statusColorToCSS()` utility maps these to CSS values.
- `name` should not be empty. Long status names should be truncated with a tooltip.

---

### BoardItem

Represents an individual issue or pull request displayed on the board.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `string` | Required, unique | Item identifier (used as React key) |
| `title` | `string` | Required | Issue/PR title |
| `number` | `number \| null` | Optional | Issue/PR number (e.g., #42) |
| `repository` | `string \| null` | Optional | Repository name |
| `status` | `string \| null` | Optional | Current status value |
| `assignees` | `string[]` | Default: `[]` | List of assignee usernames |
| `labels` | `Array<{ name: string; color: string }>` | Default: `[]` | Issue labels with colors |
| `priority` | `string \| null` | Optional | Priority field value |
| `size` | `string \| null` | Optional | Size/estimate field value |
| `linked_prs` | `Array<{ number: number; title: string; state: string }>` | Default: `[]` | Linked pull requests |
| `url` | `string \| null` | Optional | GitHub issue/PR URL |
| `created_at` | `string` | Required, ISO 8601 | Creation timestamp |
| `updated_at` | `string` | Required, ISO 8601 | Last update timestamp |

**Validation Rules**:
- `id` must be used as the React `key` in list renders — never array index (FR-032).
- `title` must never be empty. Long titles (>60 chars) should be truncated with a tooltip (FR-027).
- `number`, `repository`, `status`, `priority`, `size`, `url` are all nullable — the UI must handle `null` by omitting the field display, not showing "null" or "undefined".
- `assignees` and `labels` may be empty arrays — no special empty state needed, just omit the section.
- `created_at` and `updated_at` should be formatted with `formatTimeAgo()` for recent timestamps and absolute format for older ones (FR-027 implied).

**State Transitions**:
- Status changes when item is dragged to a different column.
- Item may be opened in `IssueDetailModal` for full details.

---

### PipelineConfiguration

Represents a reusable agent pipeline that can be assigned to a project.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `string` | Required, unique | Pipeline identifier |
| `name` | `string` | Required | Pipeline display name |
| `description` | `string \| null` | Optional | Pipeline description |
| `stages` | `PipelineStage[]` | Required | Ordered list of pipeline stages |
| `created_at` | `string` | Required, ISO 8601 | Creation timestamp |
| `updated_at` | `string` | Required, ISO 8601 | Last update timestamp |

**Validation Rules**:
- `name` is unique per project. Long names should be truncated with a tooltip (FR-027).
- Pipeline selection uses `<ConfirmationDialog>` if the action would override an existing assignment (FR-024).

---

### PipelineAssignment

Represents the link between a project and its active pipeline.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | `string` | Required, unique | Assignment identifier |
| `pipeline_id` | `string` | Required, FK → PipelineConfiguration | Assigned pipeline |
| `project_id` | `string` | Required, FK → Project | Target project |
| `agent_mappings` | `ProjectAgentMapping[]` | Default: `[]` | Per-column agent assignments |
| `created_at` | `string` | Required, ISO 8601 | Assignment timestamp |

**State Transitions**:
- Created when user assigns a pipeline to a project (mutation with success feedback — FR-025).
- Updated when user changes agent mappings per column.
- Deleted when user unassigns a pipeline (destructive action — requires confirmation per FR-024).

---

### RateLimitInfo

Represents GitHub API rate limit state.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `limit` | `number` | Required, ≥0 | Maximum allowed requests |
| `remaining` | `number` | Required, ≥0 | Remaining requests in window |
| `reset` | `number` | Required, Unix timestamp | When the rate limit resets |
| `used` | `number` | Required, ≥0 | Requests used in current window |

**Validation Rules**:
- When `remaining` is 0, the rate limit banner must be displayed (FR-011).
- `reset` timestamp should be displayed using `formatTimeUntil()` to show countdown.
- Rate limit state is global (shared via `RateLimitContext`) — changes on the Projects page are visible in the TopBar.

---

### PageDecompositionTarget

Not a runtime entity — represents the target structure after the page decomposition refactor.

| Component | Max Lines | Responsibility | Props Received |
|-----------|-----------|---------------|----------------|
| `ProjectsPage.tsx` | ≤250 | Orchestrator — composes sub-components, manages top-level state | None (route component) |
| `ProjectSelector.tsx` | ~120 | Project list dropdown with search | `projects`, `selectedProject`, `onSelect`, `isLoading` |
| `PipelineSelector.tsx` | ~150 | Pipeline assignment dropdown with grid | `projectId`, `pipelines`, `activePipeline`, `onAssign` |
| `BoardHeader.tsx` | ~80 | Title bar with sync status, refresh, timestamp | `project`, `syncStatus`, `lastUpdated`, `onRefresh`, `isRefreshing` |
| `RateLimitBanner.tsx` | ~50 | Rate limit warning with reset countdown | `rateLimitInfo`, `isLow` |

## Entity Relationships

```text
Project (list view)
  └─── Selected by user ──→ BoardProject (board context)
       ├─── Has many ──→ BoardColumn
       │    └─── Has many ──→ BoardItem
       │         ├─── Has many ──→ Label
       │         ├─── Has many ──→ Assignee
       │         └─── Has many ──→ LinkedPR
       └─── Has zero or one ──→ PipelineAssignment
            └─── References ──→ PipelineConfiguration
                 └─── Has many ──→ PipelineStage

RateLimitInfo (global)
  └─── Displayed by ──→ RateLimitBanner (component)
  └─── Tracked by ──→ RateLimitContext (React context)

PageDecompositionTarget
  └─── ProjectsPage orchestrates ──→ ProjectSelector
  └─── ProjectsPage orchestrates ──→ BoardHeader
  └─── ProjectsPage orchestrates ──→ RateLimitBanner
  └─── ProjectsPage orchestrates ──→ PipelineSelector
  └─── ProjectsPage orchestrates ──→ ProjectBoard (existing)
  └─── ProjectsPage orchestrates ──→ BoardToolbar (existing)
  └─── ProjectsPage orchestrates ──→ IssueDetailModal (existing)
```
