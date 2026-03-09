# Component Contracts: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## Modified Modules

### registry.ts — `parseCommand` function

**Location**: `frontend/src/lib/commands/registry.ts`
**Change summary**: Add `#help` exact-match alias in `parseCommand`, following the existing `help` keyword alias pattern.

```typescript
// BEFORE (lines 67-69)
// 'help' keyword alias (exact match, case-insensitive)
if (trimmed.toLowerCase() === 'help') {
  return { isCommand: true, name: 'help', args: '', raw };
}

// AFTER
// 'help' keyword alias (exact match, case-insensitive)
if (trimmed.toLowerCase() === 'help') {
  return { isCommand: true, name: 'help', args: '', raw };
}

// '#help' hash-command alias (exact match, case-insensitive)
if (trimmed.toLowerCase() === '#help') {
  return { isCommand: true, name: 'help', args: '', raw };
}
```

**Traces to**: FR-001 (detect `#help` regardless of whitespace/casing)

### help.ts — `helpHandler` function

**Location**: `frontend/src/lib/commands/handlers/help.ts`
**Change summary**: Update the help command's syntax line in the output to mention the `#help` alias, so users discover both invocation methods.

```typescript
// BEFORE
export function helpHandler(_args: string, _context: CommandContext): CommandResult {
  const commands = getAllCommands();
  const lines = commands.map((cmd) => `  ${cmd.syntax}  —  ${cmd.description}`);
  const message = `Available Commands:\n${lines.join('\n')}`;
  return { success: true, message, clearInput: true };
}

// AFTER
export function helpHandler(_args: string, _context: CommandContext): CommandResult {
  const commands = getAllCommands();
  const lines = commands.map((cmd) => {
    // Annotate the help command entry with the #help alias
    if (cmd.name === 'help') {
      return `  ${cmd.syntax} (or #help)  —  ${cmd.description}`;
    }
    return `  ${cmd.syntax}  —  ${cmd.description}`;
  });
  const message = `Available Commands:\n${lines.join('\n')}`;
  return { success: true, message, clearInput: true };
}
```

**Traces to**: FR-002 (inline formatted list), FR-005 (include `#help` in command reference)

---

## Unchanged Components

| Component | Reason |
|-----------|--------|
| `useChat.ts` | Command execution flow already handles local commands via `localMessages`; `#help` routes through the same path as `/help` |
| `useCommands.ts` | Delegates to `parseCommand` and `executeCommand` — no changes needed |
| `ChatInterface.tsx` | Uses `isCommand()` from `useCommands` which calls `parseCommand` — automatically picks up the alias |
| `SystemMessage.tsx` | Renders system message content with `whitespace-pre-wrap` — no changes needed for help text formatting |
| `MessageBubble.tsx` | User/assistant message rendering — not affected |
| `MentionInput.tsx` | Input component — not affected |
| `CommandAutocomplete.tsx` | Shows `/` command suggestions — `#help` is an alias, not a new autocomplete trigger |
| `types.ts` | No new types needed — existing `ParsedCommand`, `CommandResult`, `ChatMessage` are sufficient |

---

## New Modules

None. This feature requires zero new files.

---

## Test Updates

### registry.test.ts

**Location**: `frontend/src/lib/commands/registry.test.ts`
**Change summary**: Add test cases for `#help` alias detection in `parseCommand`.

```typescript
// New tests in the 'parseCommand' describe block:

it('parses #help as help command alias (case-insensitive)', () => {
  expect(parseCommand('#help').isCommand).toBe(true);
  expect(parseCommand('#help').name).toBe('help');
  expect(parseCommand('#HELP').name).toBe('help');
  expect(parseCommand('#Help').name).toBe('help');
});

it('trims whitespace around #help', () => {
  const result = parseCommand('  #help  ');
  expect(result.isCommand).toBe(true);
  expect(result.name).toBe('help');
});

it('#help preserves raw input', () => {
  const result = parseCommand('  #help  ');
  expect(result.raw).toBe('  #help  ');
});

it('# followed by other text is still NOT a command', () => {
  expect(parseCommand('# Heading').isCommand).toBe(false);
  expect(parseCommand('#nothelp').isCommand).toBe(false);
  expect(parseCommand('#help me').isCommand).toBe(false);
});
```

**Traces to**: FR-001, FR-008

### help.test.ts

**Location**: `frontend/src/lib/commands/handlers/help.test.ts`
**Change summary**: Add test verifying `#help` alias is mentioned in the help output.

```typescript
// New test in the 'helpHandler' describe block:

it('output mentions the #help alias for the help command', () => {
  const result = helpHandler('', context);
  expect(result.message).toContain('#help');
});
```

**Traces to**: FR-005

---

## Dependency Impact

| Dependency | Change | Version Impact |
|-----------|--------|----------------|
| None | No new dependencies | N/A |

This feature is entirely self-contained within the existing command system. Zero new npm packages, zero API changes, zero backend changes.
