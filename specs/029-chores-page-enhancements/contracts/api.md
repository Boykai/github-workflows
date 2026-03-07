# API Contracts: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Feature**: 029-chores-page-enhancements | **Date**: 2026-03-07

## Base URL

All endpoints are prefixed with `/api/v1` and require an authenticated session (same auth pattern as existing endpoints in `/api/v1/chores/*`).

---

## Modified Endpoints

### List Chores (MODIFIED)

```
GET /api/v1/chores/{project_id}
```

**Description**: List all Chores for the given project. Response now includes `execution_count`, `ai_enhance_enabled`, and `agent_pipeline_id` fields on each Chore.

**Response** (200 OK):
```json
[
  {
    "id": "uuid-1234",
    "project_id": "project-abc",
    "name": "Weekly Security Scan",
    "template_path": ".github/ISSUE_TEMPLATE/chore-weekly-security-scan.md",
    "template_content": "---\nname: Weekly Security Scan\n...",
    "schedule_type": "count",
    "schedule_value": 5,
    "status": "active",
    "last_triggered_at": "2026-03-05T10:00:00Z",
    "last_triggered_count": 42,
    "current_issue_number": null,
    "current_issue_node_id": null,
    "pr_number": 123,
    "pr_url": "https://github.com/owner/repo/pull/123",
    "tracking_issue_number": 120,
    "execution_count": 8,
    "ai_enhance_enabled": true,
    "agent_pipeline_id": "",
    "created_at": "2026-02-15T08:00:00Z",
    "updated_at": "2026-03-05T10:00:00Z"
  }
]
```

**Changes from initial implementation**:
- Response now includes `execution_count` (integer), `ai_enhance_enabled` (boolean), and `agent_pipeline_id` (string, empty = Auto).

---

### Create Chore (MODIFIED)

```
POST /api/v1/chores/{project_id}
```

**Description**: Create a new Chore. Now supports AI enhance preference, pipeline selection, and auto-merge flag.

**Request Body**:
```json
{
  "name": "Weekly Security Scan",
  "template_content": "---\nname: Weekly Security Scan\nabout: Run weekly security scans\ntitle: 'chore: weekly security scan'\nlabels: ['chore', 'security']\nassignees: []\n---\n\n## Tasks\n- Run dependency audit\n- Check for CVEs\n",
  "ai_enhance_enabled": true,
  "agent_pipeline_id": "",
  "auto_merge": true
}
```

**Validation**:
- `name`: Required, 1–200 characters, unique per project
- `template_content`: Required, non-empty
- `ai_enhance_enabled`: Optional, defaults to `true`
- `agent_pipeline_id`: Optional, defaults to `""` (Auto). If non-empty, should be a valid pipeline ID (advisory check — not blocking)
- `auto_merge`: Optional, defaults to `true`. If `true`, the PR will be automatically merged into main after creation

**Response** (201 Created):
```json
{
  "chore": {
    "id": "uuid-new",
    "project_id": "project-abc",
    "name": "Weekly Security Scan",
    "template_path": ".github/ISSUE_TEMPLATE/chore-weekly-security-scan.md",
    "template_content": "...",
    "schedule_type": null,
    "schedule_value": null,
    "status": "active",
    "last_triggered_at": null,
    "last_triggered_count": 0,
    "current_issue_number": null,
    "current_issue_node_id": null,
    "pr_number": 456,
    "pr_url": "https://github.com/owner/repo/pull/456",
    "tracking_issue_number": 455,
    "execution_count": 0,
    "ai_enhance_enabled": true,
    "agent_pipeline_id": "",
    "created_at": "2026-03-07T12:00:00Z",
    "updated_at": "2026-03-07T12:00:00Z"
  },
  "issue_number": 455,
  "pr_number": 456,
  "pr_url": "https://github.com/owner/repo/pull/456",
  "pr_merged": true,
  "merge_error": null
}
```

If auto-merge fails:
```json
{
  "chore": { "..." },
  "issue_number": 455,
  "pr_number": 456,
  "pr_url": "https://github.com/owner/repo/pull/456",
  "pr_merged": false,
  "merge_error": "Required status check 'ci' is expected"
}
```

**Changes from initial implementation**:
- Request body now accepts `ai_enhance_enabled`, `agent_pipeline_id`, `auto_merge`.
- Response changed from a flat `Chore` to a `ChoreCreateResponse` wrapper with PR merge status.
- When `auto_merge=true`, the endpoint creates the PR and attempts to merge it. Failure does not prevent Chore creation.

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `409 Conflict` — Chore with same name already exists for this project

---

### Update Chore (MODIFIED)

```
PATCH /api/v1/chores/{project_id}/{chore_id}
```

**Description**: Update a Chore's schedule, status, AI enhance preference, or pipeline assignment. Does NOT create a PR (use inline-update for that).

**Request Body**:
```json
{
  "schedule_type": "count",
  "schedule_value": 10,
  "ai_enhance_enabled": false,
  "agent_pipeline_id": "pipeline-uuid-123"
}
```

**Changes from initial implementation**:
- Request body now accepts optional `ai_enhance_enabled` and `agent_pipeline_id` fields.

---

### Chore Chat (MODIFIED)

```
POST /api/v1/chores/{project_id}/chat
```

**Description**: Send a chat message for Chore template refinement. Now supports AI Enhance toggle.

**Request Body**:
```json
{
  "content": "I want a chore that runs a security audit every 5 issues",
  "conversation_id": "conv-uuid-or-null",
  "ai_enhance": false
}
```

**New Field**:
- `ai_enhance` (boolean, default `true`): When `false`, the user's chat input is used verbatim as the template body. The Chat Agent generates only metadata (name, about, title, labels, assignees) without modifying the body content.

**Response** (200 OK) — when `ai_enhance=false` and template is ready:
```json
{
  "message": "I've generated the metadata for your template. Here's the result:",
  "conversation_id": "conv-uuid",
  "template_ready": true,
  "template_content": "---\nname: Security Audit\nabout: Run security audit on codebase\ntitle: 'chore: security audit'\nlabels: ['chore', 'security']\nassignees: []\n---\n\nI want a chore that runs a security audit every 5 issues",
  "template_name": "Security Audit"
}
```

Note: When `ai_enhance=false`, the body section after `---` is the user's exact input, unmodified.

**Changes from initial implementation**:
- Request body now accepts optional `ai_enhance` field.
- When `ai_enhance=false`, the response template body contains the user's verbatim input.

---

## New Endpoints

### Inline Update Chore (with PR Creation)

```
PUT /api/v1/chores/{project_id}/{chore_id}/inline-update
```

**Description**: Update a Chore's definition fields and create a Pull Request with the changes. Used for inline editing on the Chores page.

**Request Body**:
```json
{
  "name": "Updated Security Scan",
  "template_content": "---\nname: Updated Security Scan\n...\n---\n\n## Updated Tasks\n...",
  "schedule_type": "count",
  "schedule_value": 10,
  "ai_enhance_enabled": false,
  "agent_pipeline_id": "pipeline-uuid-123",
  "expected_sha": "abc123def456"
}
```

**Validation**:
- All fields optional — only changed fields need to be sent
- `name`: 1–200 characters if provided
- `template_content`: Non-empty if provided
- `schedule_value`: Must be > 0 if provided
- `expected_sha`: If provided, the endpoint checks the current file SHA against this value. If they differ, returns `409 Conflict`.

**Response** (200 OK):
```json
{
  "chore": {
    "id": "uuid-1234",
    "name": "Updated Security Scan",
    "...": "..."
  },
  "pr_number": 789,
  "pr_url": "https://github.com/owner/repo/pull/789",
  "pr_merged": false,
  "merge_error": null
}
```

**Behavior**:
- Updates the Chore record in the database.
- If `template_content` or `name` changed:
  - Creates a new branch `chore/update-{slug}-{timestamp}`
  - Commits the updated template file to the branch
  - Opens a PR with title `chore: update {chore_name}` and a description summarizing the changes
- If only metadata fields changed (schedule, pipeline, AI enhance): updates the database only, no PR created.
- The PR is NOT auto-merged for edits (only for new Chore creation).

**Error Responses**:
- `401 Unauthorized` — Missing or invalid session
- `404 Not Found` — Chore or project not found
- `409 Conflict` — Template file has been modified since the page was loaded (SHA mismatch). Response includes the current file content for manual resolution.

**409 Conflict Response**:
```json
{
  "detail": "File has been modified since page load",
  "current_sha": "xyz789abc",
  "current_content": "---\nname: ...\n---\n..."
}
```

---

## Unchanged Endpoints (Referenced)

These existing endpoints are used by the feature but not modified:

### List Templates

```
GET /api/v1/chores/{project_id}/templates
```

**Description**: List discovered Chore templates from the repository. Already implemented.

### Delete Chore

```
DELETE /api/v1/chores/{project_id}/{chore_id}
```

**Description**: Delete a Chore and close its open issue. Already implemented.

### Manual Trigger

```
POST /api/v1/chores/{project_id}/{chore_id}/trigger
```

**Description**: Manually trigger a Chore. Already implemented. Now benefits from `execution_count` increment and pipeline resolution.

### Evaluate Triggers (Cron)

```
POST /api/v1/chores/evaluate-triggers
```

**Description**: Evaluate all active Chore triggers. Already implemented. Now benefits from `execution_count` increment and pipeline resolution.

### List Pipelines

```
GET /api/v1/pipelines/{project_id}
```

**Description**: List saved pipeline configurations. Used to populate the `PipelineSelector` dropdown. Already implemented in spec 028.

---

## Frontend API Client Extensions

### New Methods in `choresApi`

```typescript
const choresApi = {
  // ... existing methods ...

  inlineUpdate: async (
    projectId: string,
    choreId: string,
    data: ChoreInlineUpdate
  ): Promise<ChoreInlineUpdateResponse> => {
    return request(`/chores/${projectId}/${choreId}/inline-update`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  createWithAutoMerge: async (
    projectId: string,
    data: ChoreCreateWithConfirmation
  ): Promise<ChoreCreateResponse> => {
    return request(`/chores/${projectId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
```

### Modified Methods in `choresApi`

```typescript
const choresApi = {
  // Existing chat method — now accepts ai_enhance parameter
  chat: async (
    projectId: string,
    data: ChoreChatMessage                     // Now includes ai_enhance?: boolean
  ): Promise<ChoreChatResponse> => {
    return request(`/chores/${projectId}/chat`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};
```

---

## TanStack Query Keys

```typescript
export const choreKeys = {
  all: ['chores'] as const,
  list: (projectId: string) => [...choreKeys.all, 'list', projectId] as const,
  templates: (projectId: string) => [...choreKeys.all, 'templates', projectId] as const,
  // No new query keys needed — inline update and create are mutations, not queries.
};
```
