# Contract: Slash Command Context Switching

**Feature**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14
**Source**: FR-023, FR-024, FR-025, FR-026

## Overview

The slash command system enables users to switch the active application context via the chat interface. When a user types `/<app-name>`, the system changes the working scope for all subsequent agent operations to target that application's directory and configuration.

## Command Format

```text
/<app-name>       Switch to the named application context
/platform         Return to platform context (no active app)
```

## Frontend Behavior

### Command Detection

The chat input component detects messages beginning with `/` and provides autocomplete suggestions from the list of registered apps.

```typescript
// Pseudocode for command autocomplete
function onInputChange(text: string) {
  if (text.startsWith('/')) {
    const query = text.slice(1); // Remove leading slash
    const suggestions = apps
      .filter(app => app.name.startsWith(query))
      .map(app => ({
        label: `/${app.name}`,
        description: app.display_name,
        status: app.status
      }));
    showSuggestions(suggestions);
  }
}
```

### Context Indicator

A persistent indicator in the chat header shows the currently active app context:

```text
┌──────────────────────────────────────┐
│  Chat  │  Context: my-app (active)   │
├──────────────────────────────────────┤
│                                      │
│  Messages...                         │
│                                      │
├──────────────────────────────────────┤
│  / type a command...                 │
└──────────────────────────────────────┘
```

When no app is selected, the indicator shows "Platform" or is hidden.

## Backend Behavior

### Context Switch Endpoint

```
POST /api/v1/chat/context
```

**Request Body**:
```json
{
  "app_name": "my-app"
}
```

To return to platform context:
```json
{
  "app_name": null
}
```

**Response** `200 OK`:
```json
{
  "active_app": {
    "name": "my-app",
    "display_name": "My Application",
    "status": "active"
  },
  "message": "Context switched to my-app"
}
```

**Error Responses**:
- `404 Not Found`: App does not exist
  ```json
  {
    "detail": "App 'nonexistent' not found",
    "suggestions": ["my-app", "my-api", "my-web"]
  }
  ```

### Context Storage

The active app context is stored as a session-level attribute:
- Updated via the context switch endpoint
- Read by agent operation handlers to determine the working directory
- Persisted across page refreshes (session-based)
- Does NOT filter conversation history (FR-026)

### Agent Operation Routing

When an agent operation is dispatched:
1. Read `active_app_name` from the current session
2. If set, resolve the app's `directory_path` (e.g., `apps/my-app`)
3. Prepend the app directory to relative file paths in the operation
4. Pass through the guard middleware (which will allow `apps/**` paths)

```python
async def resolve_working_directory(session) -> str:
    """Resolve the working directory based on active app context."""
    if session.active_app_name:
        app = await get_app(session.active_app_name)
        return app.directory_path  # e.g., "apps/my-app"
    return "solune"  # Default: platform directory
```

## Conversation History

Context switches are recorded as system messages in the conversation:

```json
{
  "sender_type": "system",
  "content": "Context switched to my-app",
  "action_type": "context_switch",
  "action_data": {
    "from_app": null,
    "to_app": "my-app"
  }
}
```

All messages remain visible regardless of context switches (FR-026). The context switch message serves as a visual separator in the conversation.

## Autocomplete Integration

The existing `CommandAutocomplete` component in the chat interface is extended to include app names:

| Trigger | Source | Example |
|---------|--------|---------|
| `/@` | Agent mentions | `/@code-reviewer` |
| `/<app>` | Registered apps | `/my-app` |
| `/platform` | Built-in command | `/platform` |

App suggestions include the app's status as a visual badge (active = green, stopped = gray, error = red).
