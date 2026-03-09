# Quickstart: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## What This Feature Does

Adds `#help` as an alias for the existing `/help` chat command. When a user types `#help` (case-insensitive, whitespace-tolerant) in the chat input, the system responds with the same inline help message as `/help` — a formatted list of all available commands. The response is ephemeral (local-only, not sent to backend or other users) and appears instantly as a system message.

## Quick Setup (for implementer)

### Prerequisites

- Node.js and npm (already configured in the frontend workspace)
- No new dependencies required
- No backend changes

### Implementation Steps

#### Step 1: Update parseCommand() in registry.ts

**File**: `frontend/src/lib/commands/registry.ts`

Add `#help` as an exact-match alias alongside the existing `help` alias. Locate the `parseCommand()` function and add the `#help` check:

```typescript
// In parseCommand(), after the existing 'help' alias check:
// Add '#help' to the condition
if (trimmed.toLowerCase() === 'help' || trimmed.toLowerCase() === '#help') {
  return { isCommand: true, name: 'help', args: '', raw: input };
}
```

This is a one-line change to the existing condition.

#### Step 2: Update help command syntax in registry.ts

**File**: `frontend/src/lib/commands/registry.ts`

Update the `syntax` field of the `help` command registration so the help output reflects the `#help` alias:

```typescript
// In the registerCommand() call for 'help':
registerCommand({
  name: 'help',
  description: 'Show all available commands and their descriptions',
  syntax: '/help (or #help)',  // Updated from '/help'
  handler: helpHandler,
});
```

### Verification

```bash
# Build frontend to verify no TypeScript errors
cd frontend && npm run build

# Run existing tests to verify no regressions
cd frontend && npx vitest run

# Manual checks:
# 1. Open the chat interface
# 2. Type '#help' and press Enter → verify help output appears as system message
# 3. Type '#Help' and press Enter → verify same help output (case-insensitive)
# 4. Type '#HELP' and press Enter → verify same help output
# 5. Type '  #help  ' and press Enter → verify same help output (whitespace-tolerant)
# 6. Type '/help' and press Enter → verify existing behavior unchanged
# 7. Type 'help' and press Enter → verify existing behavior unchanged
# 8. Type '#helpme' and press Enter → verify sent as regular message (NOT a command)
# 9. Type '#theme' and press Enter → verify sent as regular message (NOT a command)
# 10. Verify help output includes '/help (or #help)' in the command list
# 11. Verify help response appears instantly without page reload
# 12. Verify help response is only visible to the invoking user (local system message)
```

## Key Files

| File | Status | Purpose |
|------|--------|---------|
| `frontend/src/lib/commands/registry.ts` | MODIFIED | Add `#help` alias in `parseCommand()` and update help command syntax |
| `frontend/src/lib/commands/handlers/help.ts` | UNCHANGED | Auto-generates help output from registry — no changes needed |
| `frontend/src/hooks/useChat.ts` | UNCHANGED | Local message injection already handles command responses |
| `frontend/src/hooks/useCommands.ts` | UNCHANGED | Wraps registry — no interface changes |
| `frontend/src/lib/commands/types.ts` | UNCHANGED | No type changes needed |

## Spec Traceability

| Requirement | Implementation |
|------------|---------------|
| FR-001: Detect `#help` command (case-insensitive, whitespace-tolerant) | `parseCommand()` uses `trimmed.toLowerCase() === '#help'` — handles all casing and whitespace variants |
| FR-002: Respond with formatted command list | Existing `helpHandler` auto-generates from `getAllCommands()` — no changes needed |
| FR-003: Distinct system/bot-style message | Existing `SystemMessage` component renders command responses with muted styling — no changes needed |
| FR-004: Local-only visibility (not broadcast) | Existing `localMessages` mechanism in `useChat.ts` with `session_id: 'local'` — no changes needed |
| FR-005: Include `#help` in command reference | Updated `syntax` field: `/help (or #help)` appears in auto-generated help output |
| FR-006: Real-time rendering (no reload) | Existing React state injection via `setLocalMessages` — no changes needed |
| FR-007: Structured, scannable format | Existing help output format: `  /command  —  description` — no changes needed |
| FR-008: Graceful with minimal commands | Existing `helpHandler` works with any number of registered commands — no changes needed |

## Architecture Notes

The implementation follows the **alias pattern** already established for the `help` keyword. The `#help` alias is handled identically to the `help` alias — it's an exact-match condition in `parseCommand()` that routes to the same command handler. This approach:

1. **Minimizes change surface**: Only one file modified (`registry.ts`), with two small changes (one condition, one string).
2. **Preserves auto-generation**: The help output is always generated from the command registry — no manual maintenance.
3. **Avoids generalization**: `#` is NOT a general command prefix; only `#help` is recognized. This prevents unexpected behavior with Markdown-like input.
4. **Zero backend impact**: The entire change is in the frontend command parsing layer.
