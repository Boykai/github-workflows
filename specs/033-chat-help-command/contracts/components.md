# Component Contracts: Add #help Command to User Chat

**Feature**: 033-chat-help-command | **Date**: 2026-03-09

---

## Modified Modules

### 1. `parseCommand()` — Command Parser

**Location**: `frontend/src/lib/commands/registry.ts`

**Change Summary**: Add `#help` as an exact-match alias for the `help` command, immediately after the existing `help` keyword alias check.

**BEFORE** (lines 60-72):

```typescript
export function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();
  const raw = input;

  // 'help' keyword alias (exact match, case-insensitive)
  if (trimmed.toLowerCase() === 'help') {
    return { isCommand: true, name: 'help', args: '', raw };
  }

  // Must start with '/'
  if (!trimmed.startsWith('/')) {
    return { isCommand: false, name: null, args: '', raw };
  }
```

**AFTER**:

```typescript
export function parseCommand(input: string): ParsedCommand {
  const trimmed = input.trim();
  const raw = input;

  // 'help' and '#help' keyword aliases (exact match, case-insensitive)
  if (trimmed.toLowerCase() === 'help' || trimmed.toLowerCase() === '#help') {
    return { isCommand: true, name: 'help', args: '', raw };
  }

  // Must start with '/'
  if (!trimmed.startsWith('/')) {
    return { isCommand: false, name: null, args: '', raw };
  }
```

**Rationale**: Exact-match alias prevents Markdown false positives. The `||` pattern keeps both aliases in a single check for readability. Traces to: FR-001, FR-002.

### 2. Help Command Registration — Syntax Annotation

**Location**: `frontend/src/lib/commands/registry.ts`

**Change Summary**: Update the `syntax` field of the help command registration to include the `#help` alias.

**BEFORE** (lines 98-103):

```typescript
registerCommand({
  name: 'help',
  description: 'Show all available commands',
  syntax: '/help',
  handler: helpHandler,
});
```

**AFTER**:

```typescript
registerCommand({
  name: 'help',
  description: 'Show all available commands',
  syntax: '/help (or #help)',
  handler: helpHandler,
});
```

**Rationale**: The `syntax` field is used by `helpHandler` to generate the command list. Including `#help` in the syntax ensures users see both invocation methods. Traces to: FR-005, FR-007.

### 3. JSDoc Comment — Parser Documentation

**Location**: `frontend/src/lib/commands/registry.ts`

**Change Summary**: Update the `parseCommand` JSDoc to document the `#help` alias rule.

**BEFORE** (lines 48-58):

```typescript
/**
 * Parse user input into a ParsedCommand.
 *
 * Rules:
 * 1. Input starting with '/' (after trim) is a command.
 * 2. 'help' (exact, case-insensitive after trim) is a help alias.
 * 3. Command name is the first word after '/', lowercased.
 * 4. Arguments are everything after the command name, whitespace-normalized.
 * 5. Bare '/' results in isCommand:true with name:null.
 *
 * Markdown characters (#, *, -, `, >) are NOT treated as commands.
 */
```

**AFTER**:

```typescript
/**
 * Parse user input into a ParsedCommand.
 *
 * Rules:
 * 1. Input starting with '/' (after trim) is a command.
 * 2. 'help' or '#help' (exact, case-insensitive after trim) is a help alias.
 * 3. Command name is the first word after '/', lowercased.
 * 4. Arguments are everything after the command name, whitespace-normalized.
 * 5. Bare '/' results in isCommand:true with name:null.
 *
 * Markdown characters (#, *, -, `, >) are NOT treated as commands
 * (but '#help' is special-cased as an exact-match alias).
 */
```

**Rationale**: Keeps documentation accurate with code behavior. Traces to: FR-001.

---

## Unchanged Components

The following components are **NOT modified** by this feature:

| Component | Location | Reason |
|-----------|----------|--------|
| `helpHandler` | `frontend/src/lib/commands/handlers/help.ts` | Output is auto-generated from registry — no code changes needed |
| `useCommands` hook | `frontend/src/hooks/useCommands.ts` | Delegates to `parseCommand()` — changes propagate automatically |
| `useChat` hook | `frontend/src/hooks/useChat.ts` | Command execution flow unchanged — `#help` routes through existing path |
| `ChatInterface` | `frontend/src/components/chat/ChatInterface.tsx` | Renders `localMessages` as-is — system message styling is automatic |
| `MessageBubble` | `frontend/src/components/chat/MessageBubble.tsx` | System message styling already applied based on `sender_type` |
| Backend API | `backend/src/api/chat.py` | No backend changes — `#help` is local-only |

---

## Behavioral Contracts

### parseCommand('#help') Contract

**Preconditions**: Input string contains `#help` (with optional surrounding whitespace, any casing)

**Postconditions**:
- Returns `{ isCommand: true, name: 'help', args: '', raw: <original input> }`
- Functionally identical to `parseCommand('/help')` (except `raw` field)

**Invariants**:
- `# help` (with space) is NOT matched — remains a regular message (Markdown heading)
- `#anything-else` is NOT matched — only exact `#help` is special-cased
- `#helpme` is NOT matched — exact match only, no prefix matching

### Command Execution Contract (unchanged)

**Preconditions**: `parseCommand` returns `isCommand: true, name: 'help'`

**Postconditions**:
- `helpHandler` executes synchronously
- Returns `CommandResult` with `success: true`, formatted command list, `clearInput: true`
- Result is injected into `localMessages` as a `sender_type: 'system'` message
- No backend API call is made
- No WebSocket broadcast occurs

---

## Dependency Impact

No new dependencies. No version changes. No configuration changes.
