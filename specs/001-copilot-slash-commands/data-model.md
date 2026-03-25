# Data Model: Add GitHub Copilot Slash Commands to Solune Chat

**Feature Branch**: `001-copilot-slash-commands`
**Date**: 2026-03-25
**Status**: Complete

## Entity Definitions

### 1. CommandDefinition (Existing — Extended)

**Location**: `solune/frontend/src/lib/commands/types.ts`

The central entity representing a registered slash command. Already exists; no schema changes required for new commands.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Unique command name (lowercase, no `/` prefix) |
| `description` | `string` | Yes | Human-readable description shown in `/help` and HelpPage |
| `syntax` | `string` | Yes | Usage syntax (e.g., `/model [MODEL]`) |
| `handler` | `CommandHandler` | Yes | Function `(args, context) => CommandResult` |
| `parameterSchema` | `ParameterSchema` | No | Validation schema for command arguments |
| `passthrough` | `boolean` | No | When true, forward to backend instead of executing locally |

**Validation Rules**:
- `name` must be unique in registry (enforced by Map key)
- `name` must be lowercase (enforced by `registerCommand`)
- `handler` must return `CommandResult` or `Promise<CommandResult>`

---

### 2. CommandResult (Existing — No Changes)

**Location**: `solune/frontend/src/lib/commands/types.ts`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | `boolean` | Yes | Whether the command executed successfully |
| `message` | `string` | Yes | User-facing result message (empty for passthrough) |
| `clearInput` | `boolean` | Yes | Whether to clear the chat input field |
| `passthrough` | `boolean` | No | Signal to forward message to backend API |

---

### 3. CommandContext (Existing — May Need Extension)

**Location**: `solune/frontend/src/lib/commands/types.ts`

Current fields plus potential extensions for new commands:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `setTheme` | `(theme: string) => void` | Yes | Theme setter (existing) |
| `updateSettings` | `(data) => Promise<unknown>` | Yes | Settings persistence (existing) |
| `currentSettings` | `EffectiveUserSettings` | Yes | Current user settings (existing) |
| `currentTheme` | `string` | Yes | Current theme value (existing) |
| `clearChat` | `() => Promise<void>` | New | Clear all messages and backend state (for `/clear`) |
| `messages` | `ChatMessage[]` | New | Current message list (for `/share` export) |

**State Transitions**:
- `/clear` handler calls `context.clearChat()` → messages cleared, backend state deleted
- `/experimental` handler stores the toggle in browser-managed storage → setting persisted locally for the current browser
- `/share` handler reads `context.messages` → generates Markdown → triggers download

---

### 4. ParsedCommand (Existing — No Changes)

**Location**: `solune/frontend/src/lib/commands/types.ts`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isCommand` | `boolean` | Yes | Whether input was recognized as a command |
| `name` | `string \| null` | Yes | Lowercased command name, or null for bare `/` |
| `args` | `string` | Yes | Whitespace-normalized arguments after command name |
| `raw` | `string` | Yes | Original unmodified input |

---

### 5. ChatMessage (Existing — No Changes)

**Location**: `solune/backend/src/models/chat.py`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | `UUID` | Yes | Unique message identifier |
| `session_id` | `UUID` | Yes | Parent session ID |
| `sender_type` | `SenderType` | Yes | `user`, `assistant`, or `system` |
| `content` | `str` | Yes | Message text content (max 100000 chars) |
| `action_type` | `ActionType \| None` | No | Associated action type |
| `action_data` | `dict \| None` | No | Action-specific payload |
| `timestamp` | `datetime` | Yes | Message timestamp |

**Relevance**: No changes needed. Passthrough commands send/receive messages using this model. `/share` exports messages in this format. `/clear` deletes messages of this type.

---

### 6. ChatMessageRequest (Existing — No Changes)

**Location**: `solune/backend/src/models/chat.py`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | `str` | Yes | Message content (includes `/command args` for passthrough) |
| `ai_enhance` | `bool` | Yes | AI enhancement flag (default: true) |
| `file_urls` | `list[str]` | Yes | Attached file URLs (default: []) |
| `pipeline_id` | `str \| None` | No | Optional pipeline override |

**Relevance**: Passthrough commands send messages through this model. The backend's `send_message` handler receives the full `/command args` content and routes accordingly.

---

## New Command Inventory

### Local Commands (execute on frontend)

| Command | Handler File | Args | Context Dependencies |
|---------|-------------|------|---------------------|
| `/clear` | `handlers/session.ts` | None | `clearChat` |
| `/feedback` | `handlers/monitoring.ts` | None | None |
| `/share` | `handlers/monitoring.ts` | None | `messages` |
| `/experimental` | `handlers/settings.ts` | `[on\|off]` | Browser-managed local persistence |

### Passthrough Commands (forward to backend)

| Command | Handler File | Args | Backend Behavior |
|---------|-------------|------|-----------------|
| `/model` | `handlers/advanced.ts` | `[MODEL]` | Show/switch AI model |
| `/compact` | `handlers/session.ts` | None | AI-summarize conversation |
| `/context` | `handlers/session.ts` | None | Return session stats |
| `/diff` | `handlers/monitoring.ts` | None | Return session change summary |
| `/usage` | `handlers/monitoring.ts` | None | Return session metrics |
| `/mcp` | `handlers/advanced.ts` | `[show\|add\|delete]` | Manage MCP configurations |
| `/plan` | `handlers/advanced.ts` | `[description]` | Create/show execution plan |

## Relationships

```
CommandRegistry (Map<string, CommandDefinition>)
  ├── has many → CommandDefinition
  │     ├── uses → CommandHandler (function)
  │     ├── validated by → ParameterSchema (optional)
  │     └── receives → CommandContext (runtime)
  │
  ├── consumed by → HelpPage (getAllCommands)
  ├── consumed by → useCommands hook (parseCommand, getCommand, filterCommands)
  └── consumed by → CommandAutocomplete (filterCommands)

useChat hook
  ├── uses → useCommands (isCommand, executeCommand)
  ├── sends → ChatMessageRequest (via chatApi.sendMessage for passthrough)
  ├── displays → ChatMessage[] (local results + server messages)
  └── clears → clearChatMutation (for /clear command)

Backend send_message endpoint
  ├── receives → ChatMessageRequest (passthrough command content)
  ├── routes → AI agent service (interprets /command content)
  └── returns → ChatMessage (AI response)
```

## Database Impact

**No new migrations required.** All new commands operate within existing data structures:
- `/clear` uses existing `DELETE /api/v1/chat/messages` endpoint and `chat_store.clear_messages()`
- Passthrough commands use existing `POST /api/v1/chat/messages` endpoint
- `/experimental` uses browser-local persistence managed by the frontend
- `/share` reads messages already in frontend state
- `/feedback` displays a static link — no persistence
