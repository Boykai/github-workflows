# Data Model: Add #help Command to User Chat

**Feature**: 033-chat-help-command | **Date**: 2026-03-09

---

## Overview

This feature introduces no new entities, types, or state. It adds a single alias (`#help`) to the existing command parsing logic. All data structures remain unchanged. This document describes the existing entities that participate in the `#help` flow for traceability.

---

## Existing Entities (No Changes)

### ParsedCommand

The output of `parseCommand()` — unchanged by this feature.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isCommand` | `boolean` | Yes | Whether the input was recognized as a command |
| `name` | `string \| null` | Yes | Lowercase command name, or `null` for bare `/` |
| `args` | `string` | Yes | Whitespace-normalized arguments after the command name |
| `raw` | `string` | Yes | Original unmodified input |

```typescript
// frontend/src/lib/commands/types.ts (UNCHANGED)
export interface ParsedCommand {
  isCommand: boolean;
  name: string | null;
  args: string;
  raw: string;
}
```

**Usage**: `parseCommand('#help')` returns `{ isCommand: true, name: 'help', args: '', raw: '#help' }` — identical to `parseCommand('/help')` except for the `raw` field.

### CommandDefinition

Registry entry for each command — the `syntax` field is the only value updated.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `string` | Yes | Lowercase command identifier |
| `description` | `string` | Yes | Human-readable description |
| `syntax` | `string` | Yes | Display syntax (e.g., `/help (or #help)`) |
| `handler` | `CommandHandler` | Yes | Function to execute the command |
| `parameterSchema` | `ParameterSchema` | No | Optional parameter validation |
| `passthrough` | `boolean` | No | If true, forwarded to backend API |

```typescript
// frontend/src/lib/commands/types.ts (UNCHANGED)
export interface CommandDefinition {
  name: string;
  description: string;
  syntax: string;
  handler: CommandHandler;
  parameterSchema?: ParameterSchema;
  passthrough?: boolean;
}
```

### CommandResult

Handler output — unchanged.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `success` | `boolean` | Yes | Whether the command executed successfully |
| `message` | `string` | Yes | Response text to display |
| `clearInput` | `boolean` | Yes | Whether to clear the chat input field |
| `passthrough` | `boolean` | No | Signal to forward to backend |

### ChatMessage (local command response)

The system message injected into `localMessages` — unchanged.

| Field | Type | Value for #help |
|-------|------|-----------------|
| `message_id` | `string` | Generated via `generateId()` |
| `session_id` | `string` | `'local'` |
| `sender_type` | `string` | `'system'` |
| `content` | `string` | Help output text |
| `timestamp` | `string` | ISO 8601 current time |

---

## Command Alias Resolution Flow

```text
User Input          parseCommand()           Command Lookup
─────────────       ──────────────           ──────────────
"/help"         →   name: "help"         →   helpHandler()
"help"          →   name: "help"         →   helpHandler()
"#help"  [NEW]  →   name: "help"         →   helpHandler()
"#Help"  [NEW]  →   name: "help"         →   helpHandler()
"#HELP"  [NEW]  →   name: "help"         →   helpHandler()
" #help " [NEW] →   name: "help"         →   helpHandler()
"# help"        →   isCommand: false     →   (regular message — Markdown heading)
"#hashtag"      →   isCommand: false     →   (regular message)
```

All three aliases (`/help`, `help`, `#help`) resolve to the same `name: 'help'` and execute the same `helpHandler()`. The rest of the pipeline (command execution, local message injection, system message rendering) is unchanged.

---

## Validation Rules

| Rule | Value | Source |
|------|-------|--------|
| `#help` matching | Exact match after `trim().toLowerCase()` | FR-001 |
| No Markdown collision | `# help` (with space) is NOT matched | R1 research |
| No hashtag collision | `#hashtag` (other words) is NOT matched | Exact-match constraint |
| Case insensitivity | `#help`, `#Help`, `#HELP` all match | FR-001 |
| Whitespace tolerance | Leading/trailing whitespace trimmed | FR-001 |

---

## State Transitions

No new state transitions. The `#help` alias follows the existing local command lifecycle:

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  User types  │ ──→ │ parseCommand │ ──→ │ executeCommand  │ ──→ │ localMessages    │
│  "#help"     │     │ name:"help"  │     │ helpHandler()   │     │ [user, system]   │
└─────────────┘     └──────────────┘     └─────────────────┘     └──────────────────┘
                                                                        │
                                                                        ▼
                                                                  ┌──────────────────┐
                                                                  │ UI renders system │
                                                                  │ message bubble    │
                                                                  └──────────────────┘
```

---

## Relationships

```text
parseCommand() ──produces──→ ParsedCommand { name: "help" }
                                    │
                                    ▼
getCommand("help") ──returns──→ CommandDefinition { handler: helpHandler }
                                    │
                                    ▼
helpHandler() ──returns──→ CommandResult { message: "Available Commands:..." }
                                    │
                                    ▼
useChat.sendMessage() ──injects──→ ChatMessage { sender_type: "system" }
                                    │
                                    ▼
localMessages state ──renders──→ MessageBubble (system styling)
```
