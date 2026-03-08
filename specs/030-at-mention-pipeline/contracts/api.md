# API Contracts: @ Mention in Chat to Select Agent Pipeline Configuration

**Feature**: 030-at-mention-pipeline | **Date**: 2026-03-08

## Modified Endpoint

### Send Chat Message (Modified)

```text
POST /chat/messages
```

**Description**: Send a chat message and get AI response. **Modified** to accept an optional `pipeline_id` for pipeline-aware issue creation.

**Request Body** (updated):

```json
{
  "content": "Create a code review workflow using @Code Review Pipeline for the frontend module",
  "ai_enhance": true,
  "file_urls": [],
  "pipeline_id": "uuid-1234"
}
```

**New Field**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `pipeline_id` | `string \| null` | No | `null` | Pipeline configuration ID from @mention selection. When provided, overrides the project's default pipeline assignment for this submission. |

**Validation**:

- When `pipeline_id` is provided and non-null, the backend MUST validate that a `pipeline_configs` record with that ID exists for the current project.
- If the pipeline does not exist, the backend returns `400 Bad Request` with error message: `"Pipeline not found: {pipeline_id}"`.
- When `pipeline_id` is `null` or omitted, existing behavior is preserved — the project's default pipeline assignment is used (FR-013).

**Response**: Unchanged — returns `ChatMessage` as before.

**Error Responses** (new):

- `400 Bad Request` — Pipeline ID provided but not found in the project's saved pipelines.

**Backward Compatibility**: Existing clients that do not send `pipeline_id` are unaffected. The field defaults to `null`, preserving current behavior.

---

## Unchanged Endpoints (Used by Feature)

### List Pipelines

```text
GET /pipelines/{project_id}
```

**Usage in this feature**: The `MentionAutocomplete` dropdown fetches pipeline names and IDs from this existing endpoint. The response's `PipelineConfigSummary[]` provides `id`, `name`, `description`, `stage_count`, `agent_count`, and `updated_at` for display in the autocomplete dropdown (FR-014).

**No changes required** — endpoint already returns all data needed for the autocomplete.

---

## Frontend API Client Changes

### Modified in `frontend/src/services/api.ts`

The `sendMessage` method in the chat API client is updated to include the optional `pipeline_id` field:

```typescript
// Existing method signature (in chatApi or similar namespace)
sendMessage(data: ChatMessageRequest): Promise<ChatMessage> {
  return request<ChatMessage>('/chat/messages', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

The `ChatMessageRequest` type is updated to include `pipeline_id?: string` (see data-model.md). No changes to the `sendMessage` implementation are needed — `JSON.stringify` automatically includes the new field when present.

### No changes to `pipelinesApi`

The existing `pipelinesApi.list(projectId)` is used as-is for fetching pipeline data for the autocomplete dropdown.

---

## Query Keys (TanStack Query)

| Key | Endpoint | staleTime | Usage |
|-----|----------|-----------|-------|
| `['pipelines', projectId]` | `GET /pipelines/{projectId}` | 30s (existing) | Autocomplete dropdown pipeline list |

No new query keys are introduced. The autocomplete reuses the existing pipeline list query.
