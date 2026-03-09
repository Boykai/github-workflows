# Research: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## R1: Command Prefix Strategy — Supporting `#` Alongside `/`

### Context

The spec requires `#help` to be recognized as a chat command, but the existing command system uses `/` as the command prefix (e.g., `/help`, `/theme`, `/agent`). The `help` keyword (no prefix) is also supported as an exact-match alias. We need to determine the safest way to add `#help` support without disrupting existing command parsing or opening the `#` prefix to arbitrary commands.

### Research Findings

**Current `parseCommand()` logic in `registry.ts`:**

1. Trim input → check if exact match for `help` (case-insensitive) → treat as `/help`
2. Check if input starts with `/` → extract command name and args
3. Otherwise → not a command (`isCommand: false`)

**Key observations:**
- `#` is currently treated as regular text — it passes through as a normal message.
- The `#` character has no special meaning in the existing command system.
- Making `#` a general command prefix (like `/`) would require supporting `#theme`, `#agent`, etc., which is not specified and could cause confusion with Markdown headings.
- The spec specifically requests only `#help` — not a general `#` prefix.
- The spec requires case-insensitive matching and whitespace trimming.

### Decision: Add `#help` as a specific exact-match alias (not a general `#` prefix)

Add `#help` as another exact-match alias in `parseCommand()`, alongside the existing `help` alias. This means:
- `#help`, `#Help`, `#HELP` → all resolve to the `help` command
- `#theme`, `#agent`, etc. → remain regular text (not commands)
- The `#` prefix is NOT generalized as a command prefix

### Rationale
- Minimal change — one additional condition in `parseCommand()`.
- No risk of breaking existing behavior — `#` was already regular text.
- Aligns with spec requirement: only `#help` is requested, not a general `#` prefix.
- Future-proof: if more `#` commands are needed later, the alias pattern can be extended individually.

### Alternatives Considered
1. **General `#` prefix support**: Rejected — would require supporting `#theme`, `#agent`, etc., which is not specified and conflicts with Markdown heading syntax.
2. **Regex-based matching**: Rejected — over-engineering for a single alias; exact-match string comparison is simpler and faster.
3. **Modifying the command registry to accept multiple prefixes per command**: Rejected — adds unnecessary abstraction; the alias approach is simpler and already established.

---

## R2: Ephemeral Message Handling — Local-Only Command Response

### Context

The spec requires the `#help` response to be visible only to the invoking user — not broadcast to other participants and not persisted to the backend. We need to verify the existing local message mechanism can handle this correctly.

### Research Findings

**Current local message flow in `useChat.ts`:**

1. User submits a message → `handleSendMessage()` is called.
2. `parseCommand()` checks if input is a command.
3. If command is local (no `passthrough`), the handler executes and returns a `CommandResult`.
4. Two local messages are added to `localMessages` state:
   - A `sender_type: 'user'` message showing what the user typed
   - A `sender_type: 'system'` message showing the command response
5. These messages have `session_id: 'local'` — they are never sent to the backend API.
6. Local messages are merged with server messages for display: `[...serverMessages, ...localMessages]`.

**Key observations:**
- The existing mechanism already satisfies the ephemeral/local-only requirement.
- `#help` will follow the exact same path as `/help` — both route to `helpHandler`.
- No backend changes are needed.
- The `SystemMessage` component renders system messages with distinct visual styling (muted background, left-aligned, no avatar).

### Decision: No changes needed to the ephemeral message system

The existing `localMessages` mechanism in `useChat.ts` already provides:
- Local-only visibility (not sent to backend)
- Not broadcast to other users
- Distinct system message styling via `SystemMessage` component
- Real-time rendering without page reload

### Rationale
- The `#help` command, once parsed, routes to the same `helpHandler` as `/help`.
- `helpHandler` returns `{ success: true, message: ..., clearInput: true }` — no `passthrough`.
- `useChat.ts` handles non-passthrough commands by injecting into `localMessages`.
- The entire chain is already built and tested.

### Alternatives Considered
1. **Custom ephemeral message type**: Rejected — the existing `sender_type: 'system'` with `session_id: 'local'` already achieves ephemeral behavior.
2. **Backend-side command interception**: Rejected — contradicts the spec requirement of local-only visibility; would add unnecessary network round-trip.

---

## R3: Help Output Self-Inclusion — Ensuring `#help` Appears in Command List

### Context

The spec requires that the `#help` command itself appears in the help output with a description. Currently, the `helpHandler` lists all registered commands from `getAllCommands()`. We need to ensure the help output mentions both `/help` and the `#help` alias.

### Research Findings

**Current `helpHandler` output format:**
```
Available Commands:
  /agent <description> [#status-column]  —  Create a custom agent from a description
  /help  —  Show all available commands and their descriptions
  /language <en|es|fr|de|ja|zh>  —  Change the display language
  /notifications <on|off>  —  Toggle notification preferences
  /theme <light|dark|system>  —  Change the UI theme
  /view <chat|board|settings>  —  Set the default view
```

**Observations:**
- The `help` command is already registered with syntax `/help` and description "Show all available commands and their descriptions".
- The `#help` alias is NOT reflected in the syntax field.
- Users discovering commands via `#help` should learn that `/help` (and `#help`) are available.

### Decision: Update the `help` command's syntax field to include the `#help` alias

Modify the help command registration in `registry.ts` to show `#help` as an alias:
- **Syntax**: `/help` → `/help (or #help)`
- **Description**: remains "Show all available commands and their descriptions"

This ensures the auto-generated help output from `getAllCommands()` includes the `#help` alias without any changes to `helpHandler` itself.

### Rationale
- Single point of change — the command registration entry.
- `helpHandler` already auto-generates output from `getAllCommands()` — no handler changes needed.
- Users see both command forms in the help output.

### Alternatives Considered
1. **Register `#help` as a separate command**: Rejected — would create a duplicate entry in the help list; confusing UX.
2. **Add alias metadata to `CommandDefinition` type**: Rejected — over-engineering; only one command has an alias currently.
3. **Custom formatting in `helpHandler`**: Rejected — breaks the auto-generation pattern; would require manual maintenance.

---

## R4: Case-Insensitive and Whitespace-Robust Matching

### Context

The spec requires `#help` matching to be case-insensitive and whitespace-tolerant. We need to verify the existing parsing handles this correctly.

### Research Findings

**Current `parseCommand()` behavior:**
- Input is trimmed with `.trim()` before any matching.
- The `help` alias check uses `.toLowerCase() === 'help'` — case-insensitive.
- The `/` prefix check extracts the command name and uses case-insensitive lookup via `getCommand()`.

**For `#help` alias:**
- Trimming is already applied at the top of `parseCommand()`.
- Adding `trimmed.toLowerCase() === '#help'` follows the same pattern as the `help` alias.
- This handles: `#help`, `#Help`, `#HELP`, ` #help `, `  #HELP  `.

### Decision: Use the same `.trim().toLowerCase()` pattern for `#help`

The existing pattern is sufficient. No additional whitespace or casing logic is needed.

### Rationale
- Consistent with existing `help` alias implementation.
- `.trim()` handles surrounding whitespace.
- `.toLowerCase()` handles case variations.
- Simple string equality check — no regex needed.

### Alternatives Considered
1. **Regex matching**: Rejected — over-engineering for a single exact-match alias; regex is slower and harder to read.
2. **Normalize function**: Rejected — the existing `trim().toLowerCase()` chain is the standard approach in this codebase.
