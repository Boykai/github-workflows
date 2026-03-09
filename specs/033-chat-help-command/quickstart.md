# Quickstart: Add #help Command to User Chat

**Feature**: 033-chat-help-command | **Date**: 2026-03-09

---

## Prerequisites

- Node.js >= 20
- Frontend dev dependencies installed: `cd frontend && npm install`
- Existing tests passing: `cd frontend && npm test`

---

## Implementation Steps

### Step 1: Add #help Alias in parseCommand()

**File**: `frontend/src/lib/commands/registry.ts`

Update the JSDoc comment and add the `#help` exact-match alias:

```typescript
// BEFORE (line 52):
// * 2. 'help' (exact, case-insensitive after trim) is a help alias.

// AFTER:
// * 2. 'help' or '#help' (exact, case-insensitive after trim) is a help alias.
```

```typescript
// BEFORE (line 58):
// * Markdown characters (#, *, -, `, >) are NOT treated as commands.

// AFTER:
// * Markdown characters (#, *, -, `, >) are NOT treated as commands
// * (but '#help' is special-cased as an exact-match alias).
```

```typescript
// BEFORE (lines 64-66):
if (trimmed.toLowerCase() === 'help') {
  return { isCommand: true, name: 'help', args: '', raw };
}

// AFTER:
if (trimmed.toLowerCase() === 'help' || trimmed.toLowerCase() === '#help') {
  return { isCommand: true, name: 'help', args: '', raw };
}
```

### Step 2: Update Help Command Syntax

**File**: `frontend/src/lib/commands/registry.ts`

```typescript
// BEFORE (line 101):
syntax: '/help',

// AFTER:
syntax: '/help (or #help)',
```

### Step 3: Add Tests for #help Alias

**File**: `frontend/src/lib/commands/registry.test.ts`

Add test cases in the `parseCommand` describe block:

```typescript
it('treats "#help" (exact, case-insensitive) as help alias', () => {
  expect(parseCommand('#help').isCommand).toBe(true);
  expect(parseCommand('#help').name).toBe('help');
  expect(parseCommand('#HELP').isCommand).toBe(true);
  expect(parseCommand('#HELP').name).toBe('help');
  expect(parseCommand('#Help').isCommand).toBe(true);
  expect(parseCommand('#Help').name).toBe('help');
});

it('trims whitespace around #help', () => {
  const result = parseCommand('  #help  ');
  expect(result.isCommand).toBe(true);
  expect(result.name).toBe('help');
});

it('does not treat "# help" (Markdown heading) as a command', () => {
  const result = parseCommand('# help');
  expect(result.isCommand).toBe(false);
});

it('does not treat "#helpme" as a command', () => {
  const result = parseCommand('#helpme');
  expect(result.isCommand).toBe(false);
});
```

**File**: `frontend/src/lib/commands/handlers/help.test.ts`

Add test to verify `#help` alias appears in help output:

```typescript
it('output includes #help alias in syntax', () => {
  const result = helpHandler('', context);
  expect(result.message).toContain('#help');
});
```

---

## Verification

### Automated Tests

```bash
cd frontend
npm test -- --run src/lib/commands/registry.test.ts
npm test -- --run src/lib/commands/handlers/help.test.ts
npm test -- --run src/hooks/useCommands.test.tsx
npm test -- --run src/hooks/useChat.test.tsx
```

### Manual Testing Checklist

1. **Start the frontend dev server**: `cd frontend && npm run dev`
2. **Open the chat interface** in the browser
3. **Type `#help`** and send — verify system message appears with command list
4. **Type `#Help`** — verify case-insensitive handling
5. **Type `#HELP`** — verify uppercase handling
6. **Type `  #help  `** (with spaces) — verify whitespace trimming
7. **Type `# help`** (Markdown heading) — verify it is NOT treated as a command
8. **Type `/help`** — verify original command still works
9. **Type `help`** — verify keyword alias still works
10. **Verify** the help output includes `(or #help)` in the syntax for the help command

---

## Key Files

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/lib/commands/registry.ts` | MODIFY | Add `#help` alias in `parseCommand()`, update help syntax |
| `frontend/src/lib/commands/registry.test.ts` | MODIFY | Add `#help` test cases |
| `frontend/src/lib/commands/handlers/help.test.ts` | MODIFY | Verify `#help` appears in help output |

---

## Spec Traceability

| Requirement | Implementation |
|-------------|---------------|
| FR-001: Detect `#help` regardless of whitespace/casing | `parseCommand()` exact-match with `trim().toLowerCase()` |
| FR-002: Respond with formatted command list | Existing `helpHandler()` — no changes needed |
| FR-003: Distinct system message styling | Existing `sender_type: 'system'` rendering — no changes needed |
| FR-004: Only visible to invoking user | Existing `localMessages` path — no changes needed |
| FR-005: Include `#help` in command reference | Updated `syntax: '/help (or #help)'` in registration |
| FR-006: No page reload required | Existing reactive `localMessages` state — no changes needed |
| FR-007: Structured, scannable format | Existing help output format — no changes needed |
| FR-008: Graceful single-command handling | Existing `getAllCommands()` iteration — no changes needed |
