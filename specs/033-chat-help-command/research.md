# Research: Add #help Command to User Chat

**Feature**: 033-chat-help-command | **Date**: 2026-03-09

---

## R1: #help Alias Integration in parseCommand()

**Context**: The `parseCommand()` function in `registry.ts` currently recognizes two input patterns as commands: (1) inputs starting with `/` after trimming, and (2) the exact keyword `help` (case-insensitive). The `#` character is explicitly excluded from command parsing because it is also the Markdown heading character (`# Heading`). The requirement is to add `#help` as a third alias without breaking Markdown input.

**Research Findings**:

The current code at `registry.ts:60-94` has this flow:

```
Input → trim → check "help" exact match → check "/" prefix → not a command
```

The `#` prefix is intentionally NOT treated as a command prefix (per the JSDoc: "Markdown characters (#, *, -, `, >) are NOT treated as commands"). However, `#help` as an **exact match** (like the existing `help` alias) is safe because:

1. `#help` is not valid Markdown — `# help` (with space) is a heading, `#help` (no space) is not
2. Exact matching prevents false positives on `# Heading`, `## Section`, `#hashtag text`, etc.
3. The existing `help` alias uses the same exact-match pattern, so the approach is proven

**Decision**: Add `#help` as an exact-match alias in `parseCommand()`, immediately after the existing `help` alias check. Use `trimmed.toLowerCase() === '#help'` for matching.

**Rationale**: Exact matching is the simplest and safest approach. It perfectly mirrors the existing `help` alias pattern. No regex needed. No risk of Markdown false positives. The implementation is a single conditional check.

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| Treat `#` as a general command prefix (like `/`) | Would break Markdown input (`# Heading`, `## Section`, etc.) |
| Use regex to match `#` + any command name | Over-engineered for a single alias; introduces unnecessary complexity |
| Handle in `useCommands` hook instead of `parseCommand` | Would bypass the centralized parsing layer; violates DRY since all aliases belong in `parseCommand` |

---

## R2: Case-Insensitive and Whitespace-Tolerant Matching

**Context**: FR requires `#help` to work regardless of casing (`#Help`, `#HELP`) or surrounding whitespace (`  #help  `).

**Research Findings**:

The existing `parseCommand()` already applies `input.trim()` and uses `.toLowerCase()` for the `help` alias check. The same pattern applies directly:

```typescript
// Existing pattern (line 64-66):
if (trimmed.toLowerCase() === 'help') {
  return { isCommand: true, name: 'help', args: '', raw };
}

// New pattern (identical structure):
if (trimmed.toLowerCase() === '#help') {
  return { isCommand: true, name: 'help', args: '', raw };
}
```

Both checks produce `name: 'help'`, routing to the same `helpHandler`. This ensures `#help` is functionally identical to `/help` and `help`.

**Decision**: Use `trimmed.toLowerCase() === '#help'` — directly mirrors existing pattern. No additional normalization needed beyond what `parseCommand` already does.

**Rationale**: Reuses proven code patterns. Zero risk of regression. Handles all specified cases: `#help`, `#Help`, `#HELP`, `  #help  `.

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| Separate whitespace normalization step | Unnecessary — `trim()` already handles leading/trailing whitespace |
| Case-preserving match with manual lowering | Over-complex; `.toLowerCase()` is standard and sufficient |

---

## R3: Help Output Annotation

**Context**: FR-005 requires the `#help` command itself to appear in the command reference list. Currently, the `/help` command is registered with `syntax: '/help'`. Users who discover commands via `#help` should see that `#help` is also a valid way to invoke help.

**Research Findings**:

The `helpHandler` in `handlers/help.ts` auto-generates output from `getAllCommands()`:

```typescript
const commands = getAllCommands();
const lines = commands.map((cmd) => `  ${cmd.syntax}  —  ${cmd.description}`);
const message = `Available Commands:\n${lines.join('\n')}`;
```

The help command is registered with `syntax: '/help'`. To indicate that `#help` is also valid, the simplest approach is to update the registered syntax string to `'/help (or #help)'`.

**Decision**: Update the help command registration in `registry.ts` to use `syntax: '/help (or #help)'`. This automatically propagates to the help output and autocomplete.

**Rationale**: Single point of change. The registry is the source of truth for command metadata. Updating `syntax` ensures all consumers (help output, autocomplete tooltips) reflect the alias without any code changes in the handler.

**Alternatives Considered**:

| Alternative | Why Rejected |
|------------|--------------|
| Modify `helpHandler` to append a note about `#help` | Harder to maintain; puts alias knowledge outside the registry |
| Add a separate `aliases` field to `CommandDefinition` | Over-engineered for a single alias; would require type changes across the codebase |
| Add `#help` as a separate registered command | Would create duplicate entries in help output; violates DRY |

---

## R4: Ephemeral Local-Only Response

**Context**: FR-004 requires the `#help` response to be visible only to the invoking user, not broadcast to other participants.

**Research Findings**:

The existing command execution flow in `useChat.ts` (lines 196-246) already handles this correctly:

1. `isCommand(content)` detects the input as a command
2. `executeCommand(content)` runs the handler locally
3. If `result.passthrough` is false (which it is for `/help`), the response is injected into `localMessages` state
4. `localMessages` are client-side only — never sent to the backend API or WebSocket

Since `#help` routes to the same `help` command (via `parseCommand` returning `name: 'help'`), it automatically inherits the ephemeral local-only behavior. No changes needed in `useChat.ts`.

**Decision**: No changes to `useChat.ts` or the message handling flow. The existing local command path handles ephemeral responses correctly for all aliases.

**Rationale**: The architecture already supports this requirement. Adding the alias in `parseCommand` is sufficient — the rest of the pipeline works unchanged.

**Alternatives Considered**: None — the existing architecture handles this requirement perfectly.

---

## R5: Visual Differentiation of System Messages

**Context**: FR-003 requires the `#help` response to appear as a distinct system/bot-style message.

**Research Findings**:

The existing command response flow creates messages with `sender_type: 'system'` (see `useChat.ts:215`). The `MessageBubble` component already renders system messages with distinct styling (different background color, no avatar, system label). This applies to all local command responses including `/help`.

Since `#help` produces the same `CommandResult` and follows the same `localMessages` injection path, it automatically receives system message styling.

**Decision**: No changes needed. The existing system message styling applies to `#help` responses automatically.

**Rationale**: The visual differentiation is handled at the message rendering layer based on `sender_type: 'system'`, not at the command parsing layer.

**Alternatives Considered**: None — existing styling is sufficient.
