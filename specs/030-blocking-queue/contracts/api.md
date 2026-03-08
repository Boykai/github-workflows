# API Contracts: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Feature**: 030-blocking-queue | **Date**: 2026-03-08

## Overview

This document defines the API contracts for the blocking queue feature. All endpoints use the existing authentication mechanism (session-based, `get_session_dep`). No new API routes are created for the blocking queue itself — it is an internal service integrated into existing workflows. Changes are to existing endpoints (pipeline CRUD, chore CRUD, chat) and internal service interfaces.

---

## Modified Endpoints

### Pipeline Config — Add `blocking` field

**Existing endpoints** in `backend/src/api/pipelines.py`:

#### `POST /api/v1/pipelines/{project_id}` — Create Pipeline

**Request body** (additions to `PipelineConfigCreate`):

```json
{
  "name": "My Pipeline",
  "description": "Pipeline description",
  "stages": [],
  "blocking": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `blocking` | `boolean` | No | `false` | When true, ALL issues created by this pipeline are blocking |

**Response** (additions to `PipelineConfig`):

```json
{
  "id": "uuid-string",
  "project_id": "project-id",
  "name": "My Pipeline",
  "description": "Pipeline description",
  "stages": [],
  "blocking": true,
  "created_at": "2026-03-08T12:00:00",
  "updated_at": "2026-03-08T12:00:00"
}
```

#### `PUT /api/v1/pipelines/{project_id}/{pipeline_id}` — Update Pipeline

**Request body** (additions to `PipelineConfigUpdate`):

```json
{
  "blocking": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `blocking` | `boolean` | No | Update the pipeline's blocking flag |

**Response**: Same as create, with updated `blocking` value.

#### `GET /api/v1/pipelines/{project_id}` — List Pipelines

**Response**: Each pipeline in the list includes `blocking: boolean`.

#### `GET /api/v1/pipelines/{project_id}/{pipeline_id}` — Get Pipeline

**Response**: Includes `blocking: boolean`.

---

### Chore — Add `blocking` field

**Existing endpoints** in `backend/src/api/chores.py`:

#### `POST /api/v1/chores/{project_id}` — Create Chore

**Request body** (additions to `ChoreCreate`):

```json
{
  "name": "My Chore",
  "template_content": "...",
  "blocking": true
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `blocking` | `boolean` | No | `false` | When true, triggered issues are blocking |

**Response** (additions to `Chore`):

```json
{
  "id": "chore-id",
  "blocking": true
}
```

#### `PATCH /api/v1/chores/{project_id}/{chore_id}` — Update Chore

**Request body** (additions to `ChoreUpdate`):

```json
{
  "blocking": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `blocking` | `boolean` | No | Update the chore's blocking flag |

**Response**: Full `Chore` object with updated `blocking` value.

#### `GET /api/v1/chores/{project_id}` — List Chores

**Response**: Each chore includes `blocking: boolean`.

#### `POST /api/v1/chores/{project_id}/{chore_id}/trigger` — Trigger Chore

**Behavior change**: When triggered, the effective blocking flag is `chore.blocking OR pipeline.blocking` (where `pipeline` is the chore's assigned pipeline, if any). This flag is passed to `execute_full_workflow()`.

**Response** (additions to `ChoreTriggerResult`): No response changes — blocking is transparent to the trigger response.

---

### Chat — `#block` Detection

**Existing endpoint** in `backend/src/api/chat.py`:

#### `POST /api/v1/chat/{project_id}` — Send Chat Message

**Behavior change**: The message content is scanned for `#block` (case-insensitive, anywhere in content). If found:
1. All occurrences of `#block` are stripped from the message
2. `is_blocking=True` is set on the resulting issue/task proposal
3. The cleaned message proceeds through normal intent processing

**Request body**: No changes to the request schema — `#block` is detected from the existing `content` field.

**Response**: No changes to the response schema — the blocking flag is applied internally to the workflow.

---

## Internal Service Interfaces

### BlockingQueueService (`backend/src/services/blocking_queue.py`)

These are internal Python interfaces, not HTTP endpoints.

#### `enqueue_issue(repo_key, issue_number, project_id, is_blocking) → BlockingQueueEntry`

Inserts a new entry into the blocking queue. Determines if the issue should activate immediately based on current queue state.

| Parameter | Type | Description |
|-----------|------|-------------|
| `repo_key` | `str` | Repository identifier (`owner/repo`) |
| `issue_number` | `int` | GitHub issue number |
| `project_id` | `str` | Project ID for WebSocket scoping |
| `is_blocking` | `bool` | Whether this issue is blocking |

**Returns**: The created `BlockingQueueEntry` (with `queue_status` set to either `pending` or `active`).

#### `get_base_ref_for_issue(repo_key, issue_number) → str`

Returns the branch that a newly activated issue should use as its base reference.

| Parameter | Type | Description |
|-----------|------|-------------|
| `repo_key` | `str` | Repository identifier |
| `issue_number` | `int` | GitHub issue number |

**Returns**: Branch name string — either the oldest open blocking issue's `parent_branch`, or `"main"`.

#### `mark_active(repo_key, issue_number, parent_branch) → None`

Transitions an entry to `active` status, recording the parent branch and activation timestamp.

#### `mark_in_review(repo_key, issue_number) → list[int]`

Transitions an entry to `in_review` status and triggers activation cascade.

**Returns**: List of issue numbers that were newly activated.

#### `mark_completed(repo_key, issue_number) → list[int]`

Transitions an entry to `completed` status, records completion timestamp, and triggers activation cascade.

**Returns**: List of issue numbers that were newly activated.

#### `try_activate_next(repo_key) → list[int]`

Core activation logic. Evaluates pending entries and activates the next eligible batch.

**Returns**: List of issue numbers that were newly activated.

#### `get_current_base_branch(repo_key) → str`

Returns the current base branch for the repo (oldest open blocking issue's branch, or `"main"`).

#### `has_open_blocking_issues(repo_key) → bool`

Quick boolean check for whether any blocking issues are open (active or in_review).

---

### BlockingQueueStore (`backend/src/services/blocking_queue_store.py`)

SQLite persistence layer following the existing `get_db()` pattern.

#### `insert(entry: BlockingQueueEntry) → BlockingQueueEntry`

Insert a new queue entry. Returns the entry with the auto-generated `id`.

#### `update_status(repo_key, issue_number, status, **kwargs) → None`

Update the queue status and any additional fields (e.g., `parent_branch`, `activated_at`, `completed_at`).

#### `get_by_repo(repo_key, statuses=None) → list[BlockingQueueEntry]`

Get all entries for a repo, optionally filtered by status(es). Ordered by `created_at ASC`.

#### `get_by_issue(repo_key, issue_number) → BlockingQueueEntry | None`

Get a single entry by repo and issue number.

#### `get_pending(repo_key) → list[BlockingQueueEntry]`

Get all pending entries for a repo, ordered by `created_at ASC`.

#### `get_open_blocking(repo_key) → list[BlockingQueueEntry]`

Get all open (active or in_review) blocking entries for a repo, ordered by `created_at ASC`.

---

## WebSocket Events

### `blocking_queue_updated`

Broadcast to all WebSocket connections for the relevant project when issues activate or complete.

```json
{
  "type": "blocking_queue_updated",
  "repo_key": "owner/repo",
  "activated_issues": [42, 43],
  "completed_issues": [41],
  "current_base_branch": "issue-41-branch-name"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | `string` | Always `"blocking_queue_updated"` |
| `repo_key` | `string` | Repository identifier |
| `activated_issues` | `number[]` | Issue numbers that were just activated |
| `completed_issues` | `number[]` | Issue numbers that just completed |
| `current_base_branch` | `string` | Current base branch for the repo (`"main"` if no blocking issues) |

---

## Frontend API Client Methods

### Pipeline API (modifications to existing)

```typescript
// In frontend/src/services/api.ts — additions to existing pipelinesApi

// Create pipeline — request body now includes optional `blocking`
pipelinesApi.create(projectId: string, body: PipelineConfigCreate): Promise<PipelineConfig>

// Update pipeline — request body now includes optional `blocking`
pipelinesApi.update(projectId: string, pipelineId: string, body: PipelineConfigUpdate): Promise<PipelineConfig>
```

### Chore API (modifications to existing)

```typescript
// In frontend/src/services/api.ts — additions to existing choresApi

// Update chore — request body now includes optional `blocking`
choresApi.update(projectId: string, choreId: string, body: ChoreUpdate): Promise<Chore>
```

No new API client methods are needed — the blocking queue is fully managed by the backend and communicated via WebSocket events.

---

## Error Responses

No new error codes are introduced. Existing error handling applies:

| Scenario | HTTP Status | Error |
|----------|------------|-------|
| Issue already in queue | 409 Conflict | `"Issue #X already exists in blocking queue for repo"` |
| Issue not found in queue | 404 Not Found | `"No blocking queue entry for issue #X in repo"` |
| Invalid status transition | 422 Validation Error | `"Cannot transition from {current} to {target}"` |

These errors are internal (service-to-service); they do not surface to the frontend as new API errors.
