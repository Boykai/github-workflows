# Quickstart: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## What This Feature Does

Adds `#help` as an alias for the existing `/help` chat command. When a user types `#help` (case-insensitive, whitespace-tolerant) in the chat input, the system responds with an ephemeral, local-only system message listing all available chat commands. The `#help` alias is mentioned in the help output so users can discover both invocation methods.

## Quick Setup (for implementer)

### Prerequisites

- Node.js and npm (already configured in the frontend workspace)
- No new dependencies required
- No backend changes

### Implementation Steps

#### Step 1: Add `#help` alias in `parseCommand`

**File**: `frontend/src/lib/commands/registry.ts`

Add the following check after the existing `help` keyword alias (around line 70):

```typescript
// '#help' hash-command alias (exact match, case-insensitive)
if (trimmed.toLowerCase() === '#help') {
  return { isCommand: true, name: 'help', args: '', raw };
}
```

#### Step 2: Update help output to mention `#help`

**File**: `frontend/src/lib/commands/handlers/help.ts`

Update the `helpHandler` function to annotate the help command line with the `#help` alias:

```typescript
export function helpHandler(_args: string, _context: CommandContext): CommandResult {
  const commands = getAllCommands();
  const lines = commands.map((cmd) => {
    if (cmd.name === 'help') {
      return `  ${cmd.syntax} (or #help)  —  ${cmd.description}`;
    }
    return `  ${cmd.syntax}  —  ${cmd.description}`;
  });
  const message = `Available Commands:\n${lines.join('\n')}`;
  return { success: true, message, clearInput: true };
}
```

#### Step 3: Add tests for `#help` alias

**File**: `frontend/src/lib/commands/registry.test.ts`

Add test cases in the `parseCommand` describe block for `#help` detection, case-insensitivity, whitespace trimming, and non-matching `#` inputs.

**File**: `frontend/src/lib/commands/handlers/help.test.ts`

Add a test verifying the help output mentions `#help`.

### Verification

```bash
# Run the command system tests
cd frontend && npx vitest run src/lib/commands/

# Run full frontend tests to verify no regressions
cd frontend && npm test

# Build frontend to verify no TypeScript errors
cd frontend && npm run build

# Manual checks:
# 1. Open the chat popup
# 2. Type '#help' and press Enter → verify system message with command list appears
# 3. Type '#HELP' and press Enter → verify same behavior (case-insensitive)
# 4. Type '  #help  ' and press Enter → verify same behavior (whitespace-tolerant)
# 5. Type '# Heading' and press Enter → verify it is NOT treated as a command
# 6. Verify the help output includes "(or #help)" on the /help line
# 7. Verify the #help response appears as a system message (distinct styling)
# 8. Verify the response is local-only (refresh the page → the message disappears)
```

## Key Files

| File | Status | Purpose |
|------|--------|---------|
| `frontend/src/lib/commands/registry.ts` | MODIFIED | Add `#help` exact-match alias in `parseCommand` |
| `frontend/src/lib/commands/handlers/help.ts` | MODIFIED | Mention `#help` alias in help output |
| `frontend/src/lib/commands/registry.test.ts` | MODIFIED | Add tests for `#help` alias parsing |
| `frontend/src/lib/commands/handlers/help.test.ts` | MODIFIED | Add test for `#help` mention in output |

## Spec Traceability

| Requirement | Implementation |
|------------|---------------|
| FR-001: Detect `#help` case-insensitively | `parseCommand` exact-match alias with `trimmed.toLowerCase() === '#help'` |
| FR-002: Respond with formatted command list | Existing `helpHandler` output via `SystemMessage` component |
| FR-003: Distinct system/bot-style message | Existing `SystemMessage` component with `bg-background/56` styling |
| FR-004: Only visible to invoking user | Existing local command path — `localMessages` state, `session_id: 'local'`, not sent to backend |
| FR-005: Include `#help` in command reference | Help output annotates `/help` line with `(or #help)` |
| FR-006: No page reload needed | React state update via `setLocalMessages` — immediate UI update |
| FR-007: Structured, scannable format | Plain text with consistent spacing, one command per line, `whitespace-pre-wrap` rendering |
| FR-008: Handle as only command gracefully | `helpHandler` uses `getAllCommands()` dynamically — works with any number of commands |
