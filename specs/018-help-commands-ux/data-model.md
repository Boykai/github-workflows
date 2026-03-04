# Data Model: Enhance #help and General # Commands UX

**Feature**: 018-help-commands-ux | **Date**: 2026-03-04

## Entities

### CommandDefinition (extended)

Existing entity in `frontend/src/lib/commands/types.ts`. Extended with one new optional field.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Lowercase command name (e.g., "help", "theme") |
| description | string | Yes | One-line description shown in #help output |
| syntax | string | Yes | Usage syntax with `<required>` and `[optional]` params |
| handler | CommandHandler | Yes | Function that executes the command |
| parameterSchema | ParameterSchema | No | Valid parameter definition for validation |
| passthrough | boolean | No | When true, forwarded to backend instead of local execution |
| **category** | **string** | **No** | **NEW: Category name for #help grouping. Defaults to "General"** |

**Validation rules**:
- `name` must be non-empty, lowercase, no spaces
- `description` must be non-empty
- `syntax` must start with `#`
- `category`, when provided, must be non-empty string

**Default behavior**: Commands without an explicit `category` are assigned to `"General"` at display time (in the help handler), not at registration time. This avoids requiring changes to existing `registerCommand()` calls.

### CommandCategory (display-only)

Not a persisted entity — a runtime grouping concept used in #help output rendering.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Display name (e.g., "General", "Settings", "Workflow") |
| commands | CommandDefinition[] | Commands belonging to this category |
| sortOrder | number (implicit) | Alphabetical by category name, "General" always first |

**Ordering rules**:
1. "General" category always appears first in #help output
2. All other categories sorted alphabetically
3. Commands within each category sorted alphabetically by name

### ParameterSchema (unchanged)

Existing entity, no changes needed.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | 'enum' \| 'string' \| 'boolean' | Yes | Parameter type |
| values | string[] | No | Valid values for enum type |
| labels | Record<string, string> | No | Human-readable labels for values |

## Relationships

```text
CommandDefinition (1) ──category──> (1) CommandCategory (display-only grouping)
CommandDefinition (0..1) ──parameterSchema──> (1) ParameterSchema
```

## State Transitions

### Command Execution Flow

```text
User Input → parseCommand() → ParsedCommand
  │
  ├── isCommand: false → Not a command (pass to chat)
  │
  ├── name: null (bare #) → Error: "Type #help to see available commands."
  │
  ├── name: "help", args: "" → Full categorized help listing
  │
  ├── name: "help", args: "<cmd>" → Single-command detail view
  │   ├── Command found → Detailed help for that command
  │   └── Command not found → "Command not found. Type #help for full list."
  │
  ├── name: known command → Execute handler(args, context)
  │   ├── args valid → Success result
  │   ├── args missing → Usage hint with syntax and valid values
  │   └── args invalid → Error with valid options listed
  │
  └── name: unknown command → "Unknown command" + fuzzy match suggestions
      ├── Close match found (distance ≤ 2) → "Did you mean #<match>?"
      └── No close match → "Type #help to see available commands."
```
