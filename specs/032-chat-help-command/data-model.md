# Data Model: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## Overview

This feature requires no new data entities, database tables, or API models. The change is entirely within the existing frontend command parsing layer. The "data model" documents the existing types that are relevant to the change and the minimal modifications to constant/configuration data.

## Entities

### ParsedCommand (existing — unchanged)

The output of `parseCommand()` in the command registry. No structural changes needed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isCommand` | `boolean` | Yes | Whether the input was recognized as a command |
| `name` | `string \| null` | Yes | The normalized command name (e.g., `'help'`), or `null` if not a command |
| `args` | `string` | Yes | The argument string after the command name |
| `raw` | `string` | Yes | The original unmodified input |

**TypeScript definition (existing):**

```typescript
interface ParsedCommand {
  isCommand: boolean;
  name: string | null;
  args: string;
  raw: string;
}
```

### CommandDefinition (existing — unchanged)

Registration entry for a command in the registry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Command name (e.g., `'help'`) |
| `description` | `string` | Yes | Human-readable description shown in help output |
| `syntax` | `string` | Yes | Usage syntax (e.g., `/help (or #help)`) |
| `handler` | `CommandHandler` | Yes | Function that executes the command |
| `parameterSchema` | `ParameterSchema` | No | Optional parameter validation schema |
| `passthrough` | `boolean` | No | If true, command is forwarded to backend |

### CommandResult (existing — unchanged)

Return value from command handlers.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | `boolean` | Yes | Whether the command executed successfully |
| `message` | `string` | Yes | Response message to display to the user |
| `clearInput` | `boolean` | Yes | Whether to clear the chat input after execution |
| `passthrough` | `boolean` | No | If true, forward the original message to backend |

### ChatMessage (existing — unchanged)

The message structure used for both server and local messages.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message_id` | `string` | Yes | Unique message identifier |
| `session_id` | `string` | Yes | `'local'` for ephemeral command responses |
| `sender_type` | `SenderType` | Yes | `'user'`, `'assistant'`, or `'system'` |
| `content` | `string` | Yes | Message text content |
| `timestamp` | `string` | Yes | ISO 8601 timestamp |
| `status` | `MessageStatus` | No | `'pending'`, `'sent'`, or `'failed'` |

## Constants / Configuration Changes

### Help Command Registration (modified)

The only constant change is the `syntax` field of the existing `help` command registration.

| Field | Before | After |
|-------|--------|-------|
| `syntax` | `/help` | `/help (or #help)` |

All other command registrations remain unchanged.

## State Transitions

N/A — the `#help` alias adds no new state to the application. The command execution follows the existing state flow:

```
User Input → parseCommand() → [isCommand?]
  ├─ No  → Send as regular message (backend)
  └─ Yes → getCommand(name)
           ├─ passthrough? → Send to backend
           └─ local?       → Execute handler → Inject into localMessages
```

The `#help` input enters at `parseCommand()` and exits as `{ isCommand: true, name: 'help' }` — identical to `/help` and `help` inputs. No new states, no new transitions.

## Validation Rules

| Rule | Applies To | Description |
|------|-----------|-------------|
| Case-insensitive match | `parseCommand()` input | `#help`, `#Help`, `#HELP` all resolve to the `help` command |
| Whitespace trimming | `parseCommand()` input | Leading/trailing whitespace is stripped before matching |
| Exact match only | `#help` alias | Only the exact string `#help` (after trim + lowercase) triggers the command; `#helpme`, `#help foo`, etc. do not match |

## Relationships

```
parseCommand() ──recognizes──▶ "#help" alias ──routes to──▶ helpHandler()
helpHandler()  ──reads──▶ getAllCommands() (includes updated syntax field)
helpHandler()  ──returns──▶ CommandResult { message: "Available Commands:\n..." }
useChat.ts     ──injects──▶ localMessages[] (ephemeral system message)
SystemMessage  ──renders──▶ Command response in chat UI
```
