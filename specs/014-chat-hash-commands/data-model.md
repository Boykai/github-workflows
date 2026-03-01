# Data Model: Enhance Chat # Commands — App-Wide Settings Control & #help Command with Test Coverage

**Feature**: 014-chat-hash-commands | **Date**: 2026-02-28

## Entity: CommandDefinition

**Purpose**: A single entry in the command registry representing one user-invocable `#` command. This is the core building block of the command system — every command surface (help, autocomplete, execution) consumes this entity.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| name | string | Command name without `#` prefix (e.g., `"theme"`, `"help"`) | Required, lowercase, unique in registry, no whitespace |
| description | string | Human-readable description of what the command does | Required, non-empty, max 120 characters |
| syntax | string | Usage pattern (e.g., `"#theme <light\|dark\|system>"`) | Required, must include `#` prefix and parameter placeholders |
| handler | function | `(args: string, context: CommandContext) => CommandResult` | Required, must return CommandResult |
| parameterSchema | ParameterSchema \| null | Valid parameter definition for commands that accept arguments | Required for settings commands, null for `#help` |

**Validation Rules**:
- `name` must be a non-empty lowercase string with no whitespace
- `name` must be unique across the entire registry (enforced by Map key)
- `description` must be non-empty and concise (fits in autocomplete overlay)
- `syntax` must start with `#` followed by the command name
- `handler` must be a function that accepts `(args, context)` and returns `CommandResult`
- `parameterSchema` must list all valid values when present

---

## Entity: ParameterSchema

**Purpose**: Defines the valid parameters for a command that accepts arguments (settings commands).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| type | `"enum"` \| `"string"` \| `"boolean"` | Type of the parameter | Required |
| values | string[] | List of valid values (for enum type) | Required when type is `"enum"` |
| labels | Record<string, string> \| undefined | Human-readable labels for values | Optional |

**Validation Rules**:
- When `type` is `"enum"`, `values` must be a non-empty array
- Each value in `values` must be lowercase
- `labels` keys must be a subset of `values`

---

## Entity: CommandContext

**Purpose**: Runtime context passed to command handlers, providing access to app state and mutation functions.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| setTheme | function | `(theme: string) => void` — sets the UI theme | Required, from ThemeProvider |
| updateSettings | function | `(data: UserPreferencesUpdate) => Promise<void>` — updates user settings via API | Required, from useSettings mutation |
| currentSettings | object | Current user settings snapshot | Required, from useSettings query |
| currentTheme | string | Current theme value (`"light"`, `"dark"`, `"system"`) | Required, from useTheme |

**Validation Rules**:
- All fields must be provided when executing a command
- `setTheme` and `updateSettings` must be callable functions
- `currentSettings` may have undefined fields for settings not yet configured

---

## Entity: CommandResult

**Purpose**: The output of executing a command handler, consumed by the chat interface to display a system message.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| success | boolean | Whether the command executed successfully | Required |
| message | string | Display text for the system message (supports markdown-like formatting) | Required, non-empty |
| clearInput | boolean | Whether to clear the chat input after execution | Required; `true` for success, `false` for errors (FR-013) |

**Validation Rules**:
- `success: false` must always have `clearInput: false` (user keeps input to correct it)
- `message` must be non-empty and human-readable
- Error messages must include guidance (e.g., valid options or `#help` suggestion)

---

## Entity: ParsedCommand

**Purpose**: The result of parsing a user's chat input into command components.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| isCommand | boolean | Whether the input was recognized as a command attempt | Required |
| name | string \| null | Extracted command name (lowercase, trimmed) | Non-null when `isCommand` is true |
| args | string | Arguments string (whitespace-normalized, trimmed) | Empty string when no arguments provided |
| raw | string | Original input text | Required |

**Validation Rules**:
- When `isCommand` is `false`, `name` must be `null` and `args` must be empty
- When `isCommand` is `true`, `name` must be a non-empty lowercase string
- `args` must have internal whitespace normalized (multiple spaces → single space)

---

## Entity: SystemChatMessage

**Purpose**: A locally-generated chat message displayed in response to a command. Not persisted to the backend.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| message_id | string (UUID) | Unique identifier for the message | Required, generated client-side |
| session_id | string (UUID) | Current chat session ID | Required, from active session |
| sender_type | `"system"` | Always `"system"` for command responses | Required, literal value |
| content | string | The command result message text | Required, from CommandResult.message |
| action_type | null | No action associated with system messages | Always null |
| action_data | null | No action data | Always null |
| timestamp | string (ISO 8601) | When the message was created | Required, client-side timestamp |

**Validation Rules**:
- Must conform to the existing `ChatMessage` interface for seamless rendering
- `sender_type` is always `"system"` — never `"user"` or `"assistant"`
- `message_id` must be unique (UUID v4 generated client-side)

---

## Relationships

```
CommandRegistry 1──* CommandDefinition       (registry contains all commands)
CommandDefinition 1──0..1 ParameterSchema    (settings commands have schemas; help does not)
CommandDefinition *──1 CommandHandler         (each command has one handler function)
CommandHandler *──1 CommandContext            (handlers receive runtime context)
CommandHandler 1──1 CommandResult             (handlers produce exactly one result)
ParsedCommand 1──0..1 CommandDefinition       (parsed name may or may not match a registry entry)
CommandResult 1──1 SystemChatMessage          (result is wrapped into a displayable message)
```

## State Transitions

### Command Processing Lifecycle
```
user input → [parse] → ParsedCommand
  isCommand: false → pass to AI chat (existing flow)
  isCommand: true  → [lookup in registry]
    found:     → [execute handler with context] → CommandResult → SystemChatMessage → display
    not found: → CommandResult(success: false, "Unknown command") → SystemChatMessage → display
```

### Autocomplete Lifecycle
```
idle → [user types '#'] → overlay open (show all commands)
  → [user types more characters] → filter commands by prefix
    matches found: → show filtered list
    no matches:    → hide overlay
  → [user presses Escape] → close overlay
  → [user presses Enter on highlighted item] → insert command name → close overlay
  → [user deletes '#'] → close overlay
  → [user submits message] → close overlay
```

### Settings Update Lifecycle
```
user submits settings command (e.g., "#theme dark")
  → [parse] → ParsedCommand(name: "theme", args: "dark")
  → [lookup "theme" in registry] → found
  → [validate "dark" against ParameterSchema] → valid
  → [read current value from context] → "light"
  → [call setTheme("dark") / updateSettings()] → success
  → CommandResult(success: true, "✓ Theme changed from light to dark")
  → SystemChatMessage → display in chat
```
