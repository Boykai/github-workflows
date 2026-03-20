# Data Model: Optimistic UI Updates for Mutations

**Feature**: `054-optimistic-ui-updates` | **Date**: 2026-03-20

## Entities

### BoardItem (existing — no changes)

Represents a single item on the project board. Participates in drag-and-drop status changes.

| Field | Type | Description |
|-------|------|-------------|
| `item_id` | `string` | Unique project item node ID |
| `content_id` | `string?` | GitHub content node ID |
| `content_type` | `ContentType` | `ISSUE`, `DRAFT_ISSUE`, or `PULL_REQUEST` |
| `title` | `string` | Item title |
| `number` | `number?` | Issue/PR number |
| `status` | `string` | Current status name (e.g., "In Progress", "Done") |
| `status_option_id` | `string` | Internal status option ID |
| `assignees` | `BoardAssignee[]` | Assigned users |
| `priority` | `BoardCustomFieldValue?` | Priority field value |
| `size` | `BoardCustomFieldValue?` | Size/estimate field value |
| `estimate` | `number?` | Numeric estimate |
| `linked_prs` | `LinkedPR[]` | Associated pull requests |
| `sub_issues` | `SubIssue[]` | Child issues |
| `labels` | `BoardLabel[]` | Issue labels |
| `issue_type` | `string?` | Issue type classification |
| `created_at` | `string?` | Creation timestamp |
| `updated_at` | `string?` | Last update timestamp |
| `milestone` | `string?` | Milestone name |
| `queued` | `boolean?` | Whether item is in pipeline queue |

**Source**: `solune/frontend/src/types/index.ts` (lines 723–746)

### BoardColumn (existing — no changes)

Groups board items by status. Optimistic board updates move items between column `items` arrays.

| Field | Type | Description |
|-------|------|-------------|
| `status` | `BoardStatusOption` | Column status metadata (`name`, `color`, `option_id`) |
| `items` | `BoardItem[]` | Ordered list of items in this column |
| `item_count` | `number` | Total item count (may exceed `items.length` with pagination) |
| `estimate_total` | `number` | Sum of estimates in column |
| `next_cursor` | `string \| null` | Pagination cursor for loading more items |
| `has_more` | `boolean?` | Whether more items exist beyond current page |

**Source**: `solune/frontend/src/types/index.ts` (lines 748–755)

### BoardDataResponse (existing — no changes)

Complete board view. This is the primary cache entry optimistically updated for board status changes.

| Field | Type | Description |
|-------|------|-------------|
| `project` | `BoardProject` | Project metadata |
| `columns` | `BoardColumn[]` | All status columns with their items |
| `rate_limit` | `RateLimitInfo \| null` | GitHub API rate limit status |

**Cache Key**: `['board', 'data', projectId]`
**Source**: `solune/frontend/src/types/index.ts` (lines 782–785)

### Chore (existing — no changes)

Task item subject to create, update, inline-update, and delete mutations.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique chore ID |
| `project_id` | `string` | Parent project ID |
| `name` | `string` | Chore name |
| `template_path` | `string` | Template file path |
| `template_content` | `string` | Template content |
| `schedule_type` | `ScheduleType \| null` | Scheduling type |
| `schedule_value` | `number \| null` | Schedule interval |
| `status` | `ChoreStatus` | Current status |
| `last_triggered_at` | `string \| null` | Last trigger timestamp |
| `last_triggered_count` | `number` | Trigger count |
| `current_issue_number` | `number \| null` | Active issue number |
| `current_issue_node_id` | `string \| null` | Active issue node ID |
| `pr_number` | `number \| null` | Associated PR number |
| `pr_url` | `string \| null` | Associated PR URL |
| `tracking_issue_number` | `number \| null` | Tracking issue number |
| `execution_count` | `number` | Total execution count |
| `ai_enhance_enabled` | `boolean` | AI enhancement flag |
| `agent_pipeline_id` | `string` | Agent pipeline ID |
| `is_preset` | `boolean` | Whether chore is from a preset |
| `preset_id` | `string` | Source preset ID |
| `created_at` | `string` | Creation timestamp |
| `updated_at` | `string` | Last update timestamp |

**Cache Key**: `choreKeys.list(projectId)` → `['chores', 'list', projectId]`
**Source**: `solune/frontend/src/types/index.ts` (lines 899–922)

### App (existing — no changes)

Application entry subject to create, update, delete, start, and stop mutations.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Unique app identifier |
| `display_name` | `string` | Human-readable name |
| `description` | `string` | App description |
| `directory_path` | `string` | File system path |
| `associated_pipeline_id` | `string \| null` | Linked pipeline ID |
| `status` | `AppStatus` | `'creating' \| 'active' \| 'stopped' \| 'error'` |
| `repo_type` | `RepoType` | Repository type |
| `external_repo_url` | `string \| null` | External repo URL |
| `github_repo_url` | `string \| null` | GitHub repo URL |
| `github_project_url` | `string \| null` | GitHub project URL |
| `github_project_id` | `string \| null` | GitHub project ID |
| `parent_issue_number` | `number \| null` | Parent issue number |
| `parent_issue_url` | `string \| null` | Parent issue URL |
| `port` | `number \| null` | Running port |
| `error_message` | `string \| null` | Error details |
| `created_at` | `string` | Creation timestamp |
| `updated_at` | `string` | Last update timestamp |
| `warnings` | `string[] \| null` | Warning messages |

**Cache Key**: `appKeys.list()` → `['apps', 'list']`, `appKeys.detail(name)` → `['apps', 'detail', name]`
**Source**: `solune/frontend/src/types/apps.ts` (lines 6–26)

### McpToolConfig (existing — no changes)

Tool configuration entry subject to delete mutations.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique tool ID |
| `name` | `string` | Tool name |
| `description` | `string` | Tool description |
| `endpoint_url` | `string` | Tool endpoint |
| `config_content` | `string` | Configuration JSON |
| `sync_status` | `McpToolSyncStatus` | Sync state |
| `sync_error` | `string` | Error message from last sync |
| `synced_at` | `string \| null` | Last sync timestamp |
| `github_repo_target` | `string` | Target repository |
| `is_active` | `boolean` | Active flag |
| `created_at` | `string` | Creation timestamp |
| `updated_at` | `string` | Last update timestamp |

**Cache Key**: `toolKeys.list(projectId)` → `['tools', 'list', projectId]`
**Source**: `solune/frontend/src/types/index.ts` (lines 1204–1217)

### PipelineConfig (existing — no changes)

Pipeline configuration entry subject to delete mutations.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique pipeline ID |
| `project_id` | `string` | Parent project ID |
| `name` | `string` | Pipeline name |
| `description` | `string` | Pipeline description |
| `stages` | `PipelineStage[]` | Ordered stage definitions |
| `is_preset` | `boolean` | Whether from a preset |
| `preset_id` | `string` | Source preset ID |
| `created_at` | `string` | Creation timestamp |
| `updated_at` | `string` | Last update timestamp |

**Cache Key**: `pipelineKeys.list(projectId)` → `['pipelines', 'list', projectId]`
**Source**: `solune/frontend/src/types/index.ts` (lines 1104–1114)

### StatusUpdateRequest (new — backend only)

Pydantic request model for the board status update endpoint.

| Field | Type | Validation | Description |
|-------|------|------------|-------------|
| `status` | `str` | Required, non-empty | Target status name (case-insensitive match) |

**Source**: To be added to `solune/backend/src/models/board.py`

### StatusUpdateResponse (new — backend only)

Pydantic response model for the board status update endpoint.

| Field | Type | Description |
|-------|------|-------------|
| `success` | `bool` | Whether the status update was applied |

**Source**: To be added to `solune/backend/src/models/board.py`

## Relationships

```text
BoardDataResponse
  └── columns: BoardColumn[]
        ├── status: BoardStatusOption
        └── items: BoardItem[]

Chore → belongs to Project (via project_id)
App → standalone (identified by name)
McpToolConfig → belongs to Project (via API path)
PipelineConfig → belongs to Project (via project_id)
```

## Cache Key Reference

| Entity | Query Key Factory | Cache Shape |
|--------|------------------|-------------|
| Board data | `['board', 'data', projectId]` | `BoardDataResponse` |
| Board projects | `['board', 'projects']` | `BoardProjectListResponse` |
| Chores list | `choreKeys.list(projectId)` → `['chores', 'list', projectId]` | `Chore[]` or `PaginatedResponse<Chore>` |
| Apps list | `appKeys.list()` → `['apps', 'list']` | `App[]` or `PaginatedResponse<App>` |
| App detail | `appKeys.detail(name)` → `['apps', 'detail', name]` | `App` |
| Tools list | `toolKeys.list(projectId)` → `['tools', 'list', projectId]` | `McpToolConfig[]` or `PaginatedResponse<McpToolConfig>` |
| Pipelines list | `pipelineKeys.list(projectId)` → `['pipelines', 'list', projectId]` | `PipelineConfig[]` or `PaginatedResponse<PipelineConfig>` |

## State Transitions

### Board Item Status (optimistic)

```text
[Current Column] --drag--> [Target Column]
  onMutate: remove from source column items[], add to target column items[]
  onError:  restore from snapshot (item back in source column)
  onSettled: invalidate ['board', 'data', projectId]
```

### App Status (optimistic)

```text
stopped --start--> active
active  --stop-->  stopped
  onMutate: flip status field in cache
  onError:  restore from snapshot
  onSettled: invalidate appKeys.list() + appKeys.detail(name)
```

### Chore/App/Tool/Pipeline List (optimistic create/delete)

```text
[List] --create--> [List + placeholder with _optimistic: true]
[List] --delete--> [List - removed item]
  onMutate: snapshot list, apply modification
  onError:  restore from snapshot
  onSettled: invalidate list query key
```
