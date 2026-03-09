# Component Contracts: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## New Modules

None. This feature does not introduce any new files or modules. All changes are modifications to existing files.

## Modified Components

### registry.ts

**Location**: `frontend/src/lib/commands/registry.ts`
**Change summary**: Add `#help` as an exact-match alias in `parseCommand()` and update the `help` command syntax to reflect the alias.

**parseCommand() change:**

```typescript
// BEFORE
export function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();

  // 'help' keyword alias (case-insensitive, exact match)
  if (trimmed.toLowerCase() === 'help') {
    return { isCommand: true, name: 'help', args: '', raw: input };
  }

  // Check for '/' prefix
  if (!trimmed.startsWith('/')) {
    return { isCommand: false, name: null, args: '', raw: input };
  }
  // ... rest of parsing
}

// AFTER
export function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();

  // 'help' and '#help' keyword aliases (case-insensitive, exact match)
  if (trimmed.toLowerCase() === 'help' || trimmed.toLowerCase() === '#help') {
    return { isCommand: true, name: 'help', args: '', raw: input };
  }

  // Check for '/' prefix
  if (!trimmed.startsWith('/')) {
    return { isCommand: false, name: null, args: '', raw: input };
  }
  // ... rest of parsing
}
```

**Help command registration change:**

```typescript
// BEFORE
registerCommand({
  name: 'help',
  description: 'Show all available commands and their descriptions',
  syntax: '/help',
  handler: helpHandler,
});

// AFTER
registerCommand({
  name: 'help',
  description: 'Show all available commands and their descriptions',
  syntax: '/help (or #help)',
  handler: helpHandler,
});
```

**Traces to**: FR-001 (detect `#help`), FR-002 (respond with command list), FR-005 (include `#help` in reference), FR-006 (real-time, no reload)

### helpHandler (handlers/help.ts)

**Location**: `frontend/src/lib/commands/handlers/help.ts`
**Change summary**: No code changes. The handler auto-generates output from `getAllCommands()`, which will automatically include the updated syntax field showing `(or #help)`.

**Current behavior (preserved):**

```typescript
export function helpHandler(_args: string, _context: CommandContext): CommandResult {
  const commands = getAllCommands();
  const lines = commands.map((cmd) => `  ${cmd.syntax}  —  ${cmd.description}`);
  const message = `Available Commands:\n${lines.join('\n')}`;
  return { success: true, message, clearInput: true };
}
```

**Output after change:**
```
Available Commands:
  /agent <description> [#status-column]  —  Create a custom agent from a description
  /help (or #help)  —  Show all available commands and their descriptions
  /language <en|es|fr|de|ja|zh>  —  Change the display language
  /notifications <on|off>  —  Toggle notification preferences
  /theme <light|dark|system>  —  Change the UI theme
  /view <chat|board|settings>  —  Set the default view
```

**Traces to**: FR-002 (formatted list), FR-005 (`#help` in list), FR-007 (structured format), FR-008 (graceful even if only command)

## Unchanged Components

| Component | Reason |
|-----------|--------|
| `useChat.ts` | Command execution flow unchanged — `parseCommand()` returning `{ isCommand: true, name: 'help' }` triggers the existing local message injection path |
| `useCommands.ts` | Wraps registry functions — no interface changes needed |
| `types.ts` | No type changes — `ParsedCommand`, `CommandResult`, `CommandDefinition` interfaces unchanged |
| `handlers/settings.ts` | Theme, language, notifications, view handlers unaffected |
| `handlers/agent.ts` | Agent handler unaffected |
| `ChatInterface.tsx` | Message rendering unchanged — `SystemMessage` already handles command responses |
| `SystemMessage.tsx` | Visual styling unchanged — already provides distinct bot-style rendering |
| `MessageBubble.tsx` | User/assistant message display unaffected |
| `CommandAutocomplete.tsx` | Autocomplete only triggers on `/` prefix — `#` does not activate autocomplete (by design: `#help` is a shortcut, not a discoverable prefix) |
| `MentionInput.tsx` | Input handling unchanged |

## Dependency Impact

| Dependency | Change | Version Impact |
|-----------|--------|----------------|
| None | No new dependencies | N/A |

This feature is entirely a logic change within the existing command parsing module. Zero new packages, zero API changes, zero backend changes.

## Behavioral Contracts

### Input → Output Mapping

| Input | Parsed As | Result |
|-------|-----------|--------|
| `#help` | `{ isCommand: true, name: 'help' }` | Help output (local system message) |
| `#Help` | `{ isCommand: true, name: 'help' }` | Help output (local system message) |
| `#HELP` | `{ isCommand: true, name: 'help' }` | Help output (local system message) |
| ` #help ` | `{ isCommand: true, name: 'help' }` | Help output (local system message) |
| `/help` | `{ isCommand: true, name: 'help' }` | Help output (unchanged) |
| `help` | `{ isCommand: true, name: 'help' }` | Help output (unchanged) |
| `#helpme` | `{ isCommand: false }` | Sent as regular message |
| `#help foo` | `{ isCommand: false }` | Sent as regular message |
| `#theme` | `{ isCommand: false }` | Sent as regular message |
| `# help` | `{ isCommand: false }` | Sent as regular message |

### Invariants

1. **Only `#help` is aliased** — no other `#` prefixed commands are recognized.
2. **Exact match after trim + lowercase** — partial matches like `#helpme` are NOT commands.
3. **Local-only response** — `#help` response is never sent to the backend or broadcast to other users.
4. **No page reload required** — response is injected into React state instantly.
5. **Existing command behavior preserved** — all `/` prefixed commands and the `help` alias continue to work identically.
