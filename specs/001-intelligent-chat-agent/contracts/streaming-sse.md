# API Contract: SSE Streaming Endpoint

**Feature**: 001-intelligent-chat-agent | **Date**: 2026-04-07

## Endpoint

```
POST /api/v1/chat/messages/stream
```

## Description

Sends a chat message and streams the agent's response as Server-Sent Events (SSE). The response is delivered progressively, token by token, allowing the frontend to render partial responses in real time.

This endpoint is **additive** — the existing `POST /api/v1/chat/messages` endpoint remains unchanged and continues to return complete responses synchronously (FR-007).

## Request

### Headers

| Header | Value | Required |
|--------|-------|----------|
| Content-Type | application/json | Yes |
| Cookie | session_id=\<session-cookie\> | Yes (authentication) |

### Body

Same as existing `POST /chat/messages`:

```json
{
  "content": "Create a task for fixing the login bug",
  "ai_enhance": true,
  "pipeline_id": "optional-pipeline-uuid",
  "file_urls": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | User's message text (max 100,000 chars) |
| ai_enhance | boolean | No | Default true. When false, bypasses agent (FR-012) |
| pipeline_id | string (UUID) | No | Optional pipeline context |
| file_urls | string[] | No | Previously uploaded file URLs |

## Response

### Content-Type

```
text/event-stream; charset=utf-8
```

### SSE Event Format

Each event follows the standard SSE protocol:

#### Token event (progressive content)

```
data: {"type": "token", "content": "Here"}

data: {"type": "token", "content": " is"}

data: {"type": "token", "content": " a task"}
```

#### Action event (tool invocation result)

Sent when the agent invokes a tool that produces an actionable result:

```
data: {"type": "action", "action_type": "task_create", "action_data": {"proposal_id": "uuid", "proposed_title": "Fix login bug", "proposed_description": "..."}}
```

#### Done event (stream complete)

```
data: {"type": "done", "message_id": "uuid"}
```

#### Error event

```
data: {"type": "error", "message": "Agent temporarily unavailable. Please try again."}
```

### Event Schema

```json
{
  "oneOf": [
    {
      "type": "object",
      "properties": {
        "type": { "const": "token" },
        "content": { "type": "string" }
      },
      "required": ["type", "content"]
    },
    {
      "type": "object",
      "properties": {
        "type": { "const": "action" },
        "action_type": { "type": "string", "enum": ["task_create", "status_update", "issue_create"] },
        "action_data": { "type": "object" }
      },
      "required": ["type", "action_type", "action_data"]
    },
    {
      "type": "object",
      "properties": {
        "type": { "const": "done" },
        "message_id": { "type": "string", "format": "uuid" }
      },
      "required": ["type", "message_id"]
    },
    {
      "type": "object",
      "properties": {
        "type": { "const": "error" },
        "message": { "type": "string" }
      },
      "required": ["type", "message"]
    }
  ]
}
```

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 401 | No valid session cookie | `{"detail": "Not authenticated"}` |
| 403 | No project selected | `{"detail": "No project selected"}` |
| 422 | Invalid request body | Standard FastAPI validation error |
| 500 | Agent initialization failure | SSE error event, then stream closes |

## Behavior Notes

1. **User message persistence**: The user's message is persisted to SQLite *before* streaming begins, same as the non-streaming endpoint.
2. **Assistant message persistence**: The complete assistant message (accumulated from all token events + action events) is persisted to SQLite after the stream completes (after `done` event).
3. **Connection drop**: If the client disconnects mid-stream, the server cancels the agent generation and persists whatever content was generated up to that point.
4. **Bypass mode**: When `ai_enhance=false`, the endpoint returns a single `token` event with the simple title-only response followed by `done`, effectively behaving like a non-streaming call.
5. **Rate limiting**: Same rate limits as the non-streaming endpoint apply.

## Frontend Integration

```typescript
// api.ts
async sendMessageStream(
  data: ChatMessageRequest,
  onToken: (content: string) => void,
  onAction: (actionType: string, actionData: Record<string, unknown>) => void,
  onDone: (messageId: string) => void,
  onError: (message: string) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/chat/messages/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  });

  if (!response.ok || !response.body) {
    onError('Failed to connect to streaming endpoint');
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      const event = JSON.parse(line.slice(6));

      switch (event.type) {
        case 'token': onToken(event.content); break;
        case 'action': onAction(event.action_type, event.action_data); break;
        case 'done': onDone(event.message_id); break;
        case 'error': onError(event.message); break;
      }
    }
  }
}
```

## Traceability

| Requirement | Coverage |
|-------------|----------|
| FR-008 | Streaming endpoint delivers progressive tokens |
| FR-009 | Frontend consumes SSE with fallback |
| FR-012 | ai_enhance=false bypass |
| SC-005 | First token within 2 seconds |
