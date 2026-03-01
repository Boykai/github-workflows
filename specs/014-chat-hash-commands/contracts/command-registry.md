# Command Registry Contract: 014-chat-hash-commands

**Date**: 2026-02-28

> This feature does not introduce new backend API endpoints. All command processing occurs client-side. This document defines the **command registry contract** — the interface and behavioral contracts that all command definitions must follow, and the integration contracts between the command system and the existing chat/settings infrastructure.

## Command Registry Interface Contract

### Registration Contract

Every command MUST be registered in the central registry (`frontend/src/lib/commands/registry.ts`) with a `CommandDefinition` object. The registry is the **single source of truth** — no command behavior exists outside the registry.

```typescript
interface CommandDefinition {
  name: string;            // Lowercase, no whitespace, no '#' prefix
  description: string;     // ≤120 chars, shown in autocomplete and #help
  syntax: string;          // Usage pattern: "#name <param>" or "#name"
  handler: CommandHandler; // (args: string, context: CommandContext) => CommandResult
  parameterSchema?: ParameterSchema; // Validation rules for arguments
}

type CommandHandler = (args: string, context: CommandContext) => CommandResult | Promise<CommandResult>;

interface ParameterSchema {
  type: "enum" | "string" | "boolean";
  values?: string[];       // Required for enum type
  labels?: Record<string, string>; // Optional human-readable labels
}
```

### Adding a New Command

To add a new command, only ONE change is required:

```typescript
// In registry.ts or a handler module:
registry.set("newcommand", {
  name: "newcommand",
  description: "Does something useful",
  syntax: "#newcommand <value>",
  handler: newCommandHandler,
  parameterSchema: { type: "enum", values: ["a", "b", "c"] },
});
```

This automatically:
- ✅ Appears in `#help` output
- ✅ Appears in autocomplete suggestions
- ✅ Is executable via `#newcommand` in chat

### Command Lookup Contract

```typescript
function getCommand(name: string): CommandDefinition | undefined;
function getAllCommands(): CommandDefinition[];
function filterCommands(prefix: string): CommandDefinition[];
```

- `getCommand` performs case-insensitive lookup: `getCommand("THEME")` returns the `theme` command
- `getAllCommands` returns all registered commands sorted alphabetically by name
- `filterCommands` returns commands whose names start with the given prefix (case-insensitive)

## Command Parsing Contract

### Input Classification Rules

| Input Pattern | Classification | Action |
|--------------|----------------|--------|
| `#<name> <args>` | Command with arguments | Parse and execute |
| `#<name>` | Command without arguments | Parse and execute |
| `#` (bare) | Incomplete command | Show "type #help" message |
| `help` (exact, case-insensitive) | Help alias | Execute #help |
| `<anything else>` | Regular message | Pass to AI chat |

### Parsing Output

```typescript
interface ParsedCommand {
  isCommand: boolean;
  name: string | null;   // Lowercase, trimmed
  args: string;          // Whitespace-normalized
  raw: string;           // Original input
}
```

### Parsing Rules

1. Leading/trailing whitespace is trimmed before classification
2. `#` must be the first non-whitespace character for command classification
3. Command name is the first whitespace-delimited token after `#`, lowercased
4. Arguments are everything after the command name, with internal whitespace collapsed
5. `help` (without `#`) is a special case: `parseCommand("help")` → `{ isCommand: true, name: "help", args: "" }`
6. Case-insensitive: `#HELP`, `#Help`, `#help`, `HELP` all resolve to `{ name: "help" }`

## Command Execution Contract

### Handler Contract

Every handler function MUST:
1. Return a `CommandResult` (or `Promise<CommandResult>`)
2. Never throw exceptions — errors are returned as `CommandResult(success: false, ...)`
3. Not mutate the `CommandContext` object directly — use the provided functions (`setTheme`, `updateSettings`)

```typescript
interface CommandResult {
  success: boolean;
  message: string;      // Displayed as system message in chat
  clearInput: boolean;  // true on success, false on error
}
```

### Settings Handler Contract

Settings command handlers MUST:
1. Validate the argument against `parameterSchema.values`
2. Read the current value from `context.currentSettings` or `context.currentTheme`
3. Apply the change via `context.setTheme()` or `context.updateSettings()`
4. Return a confirmation message with old and new values: `"✓ Theme changed from light to dark"`
5. Return an error message listing valid options if the value is invalid: `"Invalid value 'rainbow' for theme. Valid options: light, dark, system"`

### Error Response Contract

| Error Condition | Message Format |
|----------------|----------------|
| Unknown command | `"Unknown command '<name>'. Type #help to see available commands."` |
| Missing argument | `"Missing value for #<name>. Usage: <syntax>"` |
| Invalid argument | `"Invalid value '<value>' for <name>. Valid options: <comma-separated values>"` |
| Bare `#` | `"Type #help to see available commands."` |

## Chat Integration Contract

### Message Interception

The `useCommands` hook (or equivalent) provides an `isCommand(input: string): boolean` function. The chat submission flow MUST check this **before** calling `chatApi.sendMessage()`:

```
if isCommand(input):
  result = executeCommand(input, context)
  addSystemMessage(result.message)
  if result.clearInput: clearInput()
else:
  chatApi.sendMessage({ content: input })  // existing AI flow
```

### System Message Format

System messages generated by commands use the existing `ChatMessage` interface:

```typescript
{
  message_id: crypto.randomUUID(),
  session_id: currentSessionId,
  sender_type: "system",
  content: commandResult.message,
  action_type: null,
  action_data: null,
  timestamp: new Date().toISOString(),
}
```

## Autocomplete Overlay Contract

### Trigger and Dismiss Rules

| Event | Overlay Behavior |
|-------|-----------------|
| User types `#` as first character | Open overlay, show all commands |
| User types additional chars after `#` | Filter commands by prefix |
| No commands match prefix | Close overlay |
| User presses Escape | Close overlay, keep input |
| User presses Enter with item highlighted | Insert command name, close overlay |
| User clicks a suggestion | Insert command name, close overlay |
| User presses ArrowDown/ArrowUp | Navigate suggestions |
| User deletes `#` character | Close overlay |
| User submits message | Close overlay |

### Keyboard Navigation

- **ArrowDown**: Move highlight to next item (wrap to first if at end)
- **ArrowUp**: Move highlight to previous item (wrap to last if at top)
- **Enter**: Select highlighted item (insert command name into input)
- **Escape**: Dismiss overlay without selection
- **Tab**: Select highlighted item (same as Enter)

### Suggestion Display Format

Each suggestion shows:
- Command name with `#` prefix (e.g., `#theme`)
- Brief description (from `CommandDefinition.description`)

## Initial Command Definitions

| Command | Description | Syntax | Valid Values |
|---------|-------------|--------|-------------|
| `help` | Show all available commands | `#help` | (none) |
| `theme` | Change the UI theme | `#theme <light\|dark\|system>` | `light`, `dark`, `system` |
| `language` | Change the display language | `#language <code>` | `en`, `es`, `fr`, `de`, `ja`, `zh` |
| `notifications` | Toggle notifications | `#notifications <on\|off>` | `on`, `off` |
| `view` | Set the default view | `#view <chat\|board\|settings>` | `chat`, `board`, `settings` |

## Test Contract

### Required Test Coverage

All command system tests MUST use Vitest + React Testing Library (consistent with existing test suite).

| Test Category | Test File | Minimum Scenarios |
|--------------|-----------|-------------------|
| Registry | `registry.test.ts` | Registration, lookup, filtering, unknown command, case insensitivity |
| Parser | `registry.test.ts` or `useCommands.test.tsx` | `#command args`, bare `#`, `help` alias, case insensitivity, whitespace normalization, mid-sentence `#`, non-command messages |
| Help handler | `help.test.ts` | Output contains all registered commands, format includes name/syntax/description |
| Settings handlers | `settings.test.ts` | Valid value applies, invalid value returns error with options, missing value returns usage |
| useCommands hook | `useCommands.test.tsx` | Command interception, system message creation, autocomplete filtering |
| Autocomplete | `CommandAutocomplete.test.tsx` | Render on `#`, filter on typing, keyboard navigation, selection, dismissal |
| Integration | `ChatInterface.test.tsx` | Full command flow: type → autocomplete → submit → system message; non-command passes to AI |

### Test Naming Convention

```typescript
describe("CommandRegistry", () => {
  it("returns command definition for registered command name", () => { ... });
  it("returns undefined for unregistered command name", () => { ... });
  it("performs case-insensitive lookup", () => { ... });
});
```

Follow the existing `describe`/`it` pattern with descriptive names that communicate intent.
