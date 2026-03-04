# API Contracts: Enhance #help and General # Commands UX

**Feature**: 018-help-commands-ux | **Date**: 2026-03-04

> This feature is entirely frontend/client-side. There are no REST API endpoints
> to define. The "contracts" below describe the TypeScript module interfaces
> that consumers (hooks, components) depend on.

## Module: `frontend/src/lib/commands/types.ts`

### CommandDefinition (updated interface)

```typescript
export interface CommandDefinition {
  name: string;
  description: string;
  syntax: string;
  handler: CommandHandler;
  parameterSchema?: ParameterSchema;
  passthrough?: boolean;
  /** Category for #help grouping. Defaults to "General" when omitted. */
  category?: string;
}
```

## Module: `frontend/src/lib/commands/registry.ts`

### Existing functions (unchanged signatures)

```typescript
function registerCommand(command: CommandDefinition): void;
function unregisterCommand(name: string): void;
function getCommand(name: string): CommandDefinition | undefined;
function getAllCommands(): CommandDefinition[];
function filterCommands(prefix: string): CommandDefinition[];
function parseCommand(input: string): ParsedCommand;
```

### New function

```typescript
/**
 * Return all registered commands grouped by category.
 * "General" category is always first; others sorted alphabetically.
 * Commands within each category sorted alphabetically by name.
 */
function getCommandsByCategory(): Array<{ category: string; commands: CommandDefinition[] }>;
```

## Module: `frontend/src/lib/commands/helpers.ts` (new)

### levenshteinDistance

```typescript
/**
 * Compute the Levenshtein edit distance between two strings.
 * Used for "Did you mean?" suggestions on unknown commands.
 */
function levenshteinDistance(a: string, b: string): number;
```

### findClosestCommands

```typescript
/**
 * Find registered commands whose names are within `maxDistance` edits
 * of the given input. Returns matches sorted by distance (closest first).
 */
function findClosestCommands(input: string, maxDistance?: number): CommandDefinition[];
```

### truncateInput

```typescript
/**
 * Truncate user input for display in error messages.
 * Prevents layout breakage from very long strings.
 */
function truncateInput(input: string, maxLength?: number): string;
```

## Module: `frontend/src/lib/commands/handlers/help.ts`

### helpHandler (updated behavior)

```typescript
/**
 * Handler for the #help command.
 *
 * - When args is empty: display full categorized command listing
 * - When args is non-empty: display detailed help for the specified command
 *   (strips leading # from arg to handle "#help #theme")
 */
function helpHandler(args: string, context: CommandContext): CommandResult;
```

### Response format: Full help listing

```text
Available Commands:

General
  #help  —  Show all available commands
  #help <command>  —  Show detailed help for a specific command

Settings
  #language <en|es|fr|de|ja|zh>  —  Change the display language
  #notifications <on|off>  —  Toggle notifications on or off
  #theme <light|dark|system>  —  Change the UI theme
  #view <chat|board|settings>  —  Set the default view

Workflow
  #agent <description> [#status-column]  —  Create a custom agent for your project (admin only)
```

### Response format: Single-command help

```text
#theme — Change the UI theme

Usage: #theme <light|dark|system>
Options: light, dark, system

Example: #theme dark
```

### Response format: Command not found

```text
Command 'nonexistent' not found. Type #help to see all available commands.
```

## Module: `frontend/src/hooks/useCommands.ts`

### executeCommand (updated behavior for unknown commands)

```typescript
// When command is not found in registry:
// 1. Run findClosestCommands(name, 2)
// 2. If matches found: "Unknown command '<name>'. Did you mean #<match>?"
// 3. If no matches: "Unknown command '<name>'. Type #help to see available commands."
```
