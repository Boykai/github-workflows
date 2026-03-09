# Data Model: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## Overview

This feature has no new database entities, API models, or TypeScript interfaces. It extends the existing command parsing logic with a single alias and updates the existing help handler's output format. The "data model" documents the affected data structures and the parsing rule addition.

## Affected Entities

### ParsedCommand (existing — no changes)

The `ParsedCommand` interface in `frontend/src/lib/commands/types.ts` is unchanged. The `#help` alias produces the same output shape as the existing `help` keyword alias:

```typescript
// Output of parseCommand('#help'):
{
  isCommand: true,
  name: 'help',    // Routes to the same 'help' command
  args: '',
  raw: '#help'     // Preserves original input
}
```

### CommandDefinition (existing — description updated)

The existing `help` command registration in `frontend/src/lib/commands/registry.ts` is updated to mention the `#help` alias:

| Field | Before | After |
|-------|--------|-------|
| `name` | `'help'` | `'help'` (unchanged) |
| `description` | `'Show all available commands'` | `'Show all available commands'` (unchanged) |
| `syntax` | `'/help'` | `'/help'` or `'#help'` (reflected in help output, not registry) |

### ChatMessage (existing — no changes)

Ephemeral messages created for `#help` responses use the same `ChatMessage` shape as all other local commands:

```typescript
// User message (what the user typed)
{
  message_id: '<generated>',
  session_id: 'local',
  sender_type: 'user',
  content: '#help',
  timestamp: '<ISO 8601>'
}

// System response (help text)
{
  message_id: '<generated>',
  session_id: 'local',
  sender_type: 'system',
  content: 'Available Commands:\n  /agent ...  —  ...\n  /help (or #help)  —  ...\n  ...',
  timestamp: '<ISO 8601>'
}
```

## Parsing Rules

### Updated `parseCommand` flow

```
Input → trim → lowercase check

1. trimmed === '' or whitespace-only → { isCommand: false }
2. trimmed.toLowerCase() === 'help' → { isCommand: true, name: 'help' }
3. trimmed.toLowerCase() === '#help' → { isCommand: true, name: 'help' }  ← NEW
4. !trimmed.startsWith('/') → { isCommand: false }
5. trimmed.startsWith('/') → parse as /command with args
```

Rule 3 is the only addition. It follows the exact same pattern as rule 2 (exact-match alias).

## State Transitions

N/A — no new state machines or state transitions. The `#help` alias produces the same downstream behavior as `/help`:

1. User types `#help` → `parseCommand` returns `{ isCommand: true, name: 'help' }`
2. `useChat.sendMessage` detects `isCommand` → calls `executeCommand`
3. `executeCommand` looks up `help` in registry → calls `helpHandler`
4. `helpHandler` returns formatted command list
5. `useChat` injects user message + system response into `localMessages`
6. `SystemMessage` component renders the response

## Validation Rules

| Rule | Description |
|------|-------------|
| Case-insensitive matching | `#help`, `#HELP`, `#Help` all route to help command |
| Whitespace tolerance | `  #help  ` (with leading/trailing whitespace) is detected after `trim()` |
| Exact match only | `#helping`, `#help me`, `#helpdesk` are NOT treated as commands |
| Markdown disambiguation | `# Heading` is NOT affected — only exact `#help` matches |

## Relationships

```
parseCommand('#help') ──alias──▶ getCommand('help') ──handler──▶ helpHandler()
                                                                       │
                                                                       ▼
                                                          getAllCommands() ──formats──▶ help text output
                                                                                            │
                                                                                            ▼
                                                                              SystemMessage component
```
