# Research: Add #help Command to User Chat for In-Chat Command Reference

**Feature**: 032-chat-help-command | **Date**: 2026-03-09

## R1: Command Parsing — Extending `parseCommand` for `#help` Detection

### Context

The spec requires the system to detect `#help` when submitted as a chat message, regardless of surrounding whitespace or casing (e.g., `#Help`, `#HELP`). The current `parseCommand` function in `frontend/src/lib/commands/registry.ts` explicitly excludes `#` as a command prefix — it is listed as a Markdown character that should NOT be treated as a command.

### Research Findings

**Current parsing rules (registry.ts lines 60–94):**

1. Input starting with `/` → command
2. `help` (exact, case-insensitive) → alias for `/help`
3. `#`, `*`, `-`, `` ` ``, `>` → NOT treated as commands (Markdown chars)

**The `#help` requirement conflicts with rule 3.** However, the issue is narrow: only `#help` (exact match after trimming, case-insensitive) needs to be recognized. General `#` prefix support is NOT required — `# Heading` must still be treated as Markdown, not as a command.

**Approaches evaluated:**

1. **Add `#help` as another exact-match alias** (like the existing `help` alias): Check if `trimmed.toLowerCase() === '#help'` and route to the help command. This is minimal, precise, and does not change the existing `#` exclusion for general Markdown.

2. **Add general `#` prefix support**: Treat `#` like `/` as a command prefix. This would break Markdown heading detection (`# Heading` would become a command). Requires complex disambiguation logic.

3. **Pre-process `#help` into `/help` before parsing**: Transform `#help` → `/help` before passing to `parseCommand`. Adds a layer of indirection; slightly harder to trace.

### Decision: Exact-match alias for `#help`

Add a case-insensitive check for `#help` (trimmed) as an alias, identical to the existing `help` alias pattern. This routes `#help`, `#HELP`, `#Help`, `  #help  ` all to the `help` command.

**Implementation:**

```typescript
// In parseCommand(), after the existing 'help' alias check:
if (trimmed.toLowerCase() === '#help') {
  return { isCommand: true, name: 'help', args: '', raw };
}
```

### Rationale

- Minimal change — adds 3 lines to `parseCommand()`.
- Follows the existing pattern (the `help` alias is already an exact-match special case).
- Does NOT break Markdown heading detection (`# Heading` ≠ `#help`).
- Case-insensitive and whitespace-tolerant per the spec requirement.
- No new dependencies, no architectural changes.

### Alternatives Considered

1. **General `#` prefix support**: Rejected — breaks Markdown heading detection; over-engineering for a single-command requirement.
2. **Pre-processing layer**: Rejected — adds indirection without benefit; the alias pattern is already established and simpler.
3. **Separate command parser for `#` commands**: Rejected — YAGNI; the spec only requires `#help`, not a general `#command` system.

---

## R2: Ephemeral System Message — Local-Only Response Pattern

### Context

The spec requires that the `#help` response is only visible to the user who invoked the command — not broadcast to other participants. It must not be persisted to the backend or sent to other users.

### Research Findings

**The existing command system already implements this pattern perfectly.** When a local command is executed in `useChat.ts` (lines 196–246):

1. `isCommand(content)` detects the command
2. `executeCommand(content)` runs the handler locally
3. If `result.passthrough` is false (local command):
   - A user message (`sender_type: 'user'`) is added to `localMessages`
   - A system message (`sender_type: 'system'`) is added to `localMessages`
   - Neither is sent to the backend API
4. `localMessages` are ephemeral — they exist only in React state and are lost on page refresh

**The `/help` command already uses this pattern.** The `helpHandler` returns `{ success: true, message: <formatted help text>, clearInput: true }`, which is displayed as a local system message via `SystemMessage` component.

### Decision: No changes needed for ephemeral message behavior

Since `#help` will be routed to the same `help` command handler via the alias in `parseCommand`, it will automatically use the existing ephemeral local message pattern. No changes to `useChat.ts`, `SystemMessage`, or any message handling code are needed.

### Rationale

- Zero additional code for the ephemeral requirement — the existing infrastructure handles it.
- The alias in `parseCommand` is sufficient; the entire downstream pipeline (command execution, local message injection, system message rendering) works as-is.

### Alternatives Considered

1. **Custom ephemeral message type**: Rejected — the existing `session_id: 'local'` pattern already distinguishes local from server messages.
2. **Backend-side filtering**: Rejected — local commands never reach the backend, so there's nothing to filter.

---

## R3: Help Output Format — Existing Format vs. Enhanced Formatting

### Context

The spec says the `#help` response should display command entries in a structured, scannable format (e.g., command keyword in bold or monospace font). The current `helpHandler` outputs plain text with spacing.

### Research Findings

**Current help output format (handlers/help.ts):**

```
Available Commands:
  /agent <description> [#status-column]  —  Create a custom agent for your project (admin only)
  /help  —  Show all available commands
  /language <en|es|fr|de|ja|zh>  —  Change the display language
  /notifications <on|off>  —  Toggle notifications on or off
  /theme <light|dark|system>  —  Change the UI theme
  /view <chat|board|settings>  —  Set the default view
```

**SystemMessage component rendering:** The `SystemMessage` component uses `whitespace-pre-wrap` CSS, which preserves the plain text formatting. It does NOT parse Markdown — literal `**` or `` ` `` characters would be displayed as-is.

**Assessment:** The current format is already structured and scannable. Each command is on its own line with consistent spacing. The `whitespace-pre-wrap` styling preserves the indentation.

### Decision: Keep existing plain text format with minor enhancement

The current plain text format is adequate and consistent with `SystemMessage`'s rendering capabilities. Add the `#help` alias to the help output text so users discover both invocation methods. Optionally add a brief header note mentioning the `#help` alias.

**Updated output (via helpHandler enhancement):**

```
Available Commands:
  /agent <description> [#status-column]  —  Create a custom agent for your project (admin only)
  /help (or #help)  —  Show all available commands
  /language <en|es|fr|de|ja|zh>  —  Change the display language
  /notifications <on|off>  —  Toggle notifications on or off
  /theme <light|dark|system>  —  Change the UI theme
  /view <chat|board|settings>  —  Set the default view
```

### Rationale

- No new rendering infrastructure needed — `SystemMessage` + `whitespace-pre-wrap` handles the format.
- Adding `(or #help)` to the help command line satisfies the requirement to include `#help` in the command reference.
- Minimal change to the existing handler.

### Alternatives Considered

1. **Markdown rendering in SystemMessage**: Rejected — would require adding a Markdown parser to `SystemMessage`; over-engineering for command help text.
2. **Rich HTML rendering**: Rejected — `SystemMessage` uses `text-sm text-foreground` with `whitespace-pre-wrap`; injecting HTML would require `dangerouslySetInnerHTML` which is a security concern.
3. **Separate HelpMessage component**: Rejected — YAGNI; the existing SystemMessage renders the help text clearly.

---

## R4: Command Registry — `#help` as a Discoverable Alias vs. Separate Command

### Context

The spec says the system MUST include `#help` in the command reference list. Should `#help` be a separate registered command, or an alias noted in the existing `/help` command's description?

### Research Findings

**Option A — Register `#help` as a separate command:**

```typescript
registerCommand({
  name: '#help',
  description: 'Show all available commands (alias for /help)',
  syntax: '#help',
  handler: helpHandler,
});
```

This would add a second entry to the registry. The help output would show both `/help` and `#help` as separate commands. However, this creates confusion — users might think they're different commands. It also means `getAllCommands()` returns a duplicate help entry.

**Option B — Note the alias in the existing `/help` command description:**

Update the help handler to append `(or #help)` to the `/help` syntax line. The `#help` alias is handled in `parseCommand` (routing), not in the registry (listing). This keeps the registry clean — one command, one entry.

### Decision: Option B — alias in help output, not a separate registration

The `#help` alias is a routing concern handled in `parseCommand`. The command registry stays clean with one `help` entry. The help output mentions the `#help` alias inline.

### Rationale

- Single source of truth — one `help` command in the registry.
- No duplicate entries in autocomplete or help output.
- The alias is discoverable via the `(or #help)` notation in the help text.
- Consistent with how the existing `help` keyword alias works — it routes to `/help` without being a separate registry entry.

### Alternatives Considered

1. **Separate `#help` command registration**: Rejected — creates duplicate entries, confuses users, bloats the command list.
2. **No mention of `#help` in help output**: Rejected — spec MUST include `#help` in the command reference; users need to discover the alias.
