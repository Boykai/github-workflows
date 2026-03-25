# Research: Add GitHub Copilot Slash Commands to Solune Chat

**Feature Branch**: `001-copilot-slash-commands`
**Date**: 2026-03-25
**Status**: Complete

## Resolved Unknowns

### 1. /plan Command — Full Syntax and Behavior

**Context**: The `/plan` command description was truncated in the original issue (FR-019 in spec.md notes "NEEDS CLARIFICATION").

**Decision**: `/plan` is a passthrough command with syntax `/plan [description]`.
- `/plan` (no args): Display the current execution plan for the active task context, if one exists.
- `/plan [description]`: Create a new execution plan based on the provided description and current task context.

**Rationale**: This mirrors GitHub Copilot CLI's `/plan` behavior which creates/shows execution plans. The backend AI service already has task context (proposals, pipelines) and can generate structured plans. Keeping it passthrough aligns with the pattern for all AI-dependent commands.

**Alternatives Considered**:
- Local-only plan display: Rejected because plan generation requires AI reasoning about task dependencies.
- Separate `/plan show` and `/plan create` subcommands: Rejected for simplicity; the presence/absence of arguments naturally disambiguates.

---

### 2. /theme Command Enhancements (FR-024)

**Context**: FR-024 states "/theme command MUST be enhanced with additional capabilities" but the spec notes "NEEDS CLARIFICATION: What specific enhancements are planned?"

**Decision**: Defer `/theme` enhancements to a follow-up feature. The current `/theme <light|dark|system>` behavior is sufficient and functional. No changes to `/theme` in this feature.

**Rationale**: The original issue lists `/theme` under "enhance" but provides no concrete enhancement details. Implementing speculative enhancements violates the Simplicity principle (Constitution §V). The existing theme handler already supports all three standard modes.

**Alternatives Considered**:
- Adding custom theme colors: Rejected — no user story or acceptance criteria defined.
- Adding per-component theming: Rejected — scope creep with no requirements.

---

### 3. Command Type Classification

**Context**: Each new command needs to be classified as Local or Passthrough to determine execution path.

**Decision**: Classification based on whether the command requires AI reasoning or backend data:

| Command | Type | Rationale |
|---------|------|-----------|
| `/clear` | Local + API | Clears UI state locally, calls existing `DELETE /api/v1/chat/messages` endpoint |
| `/model` | Passthrough | Requires backend to list/switch AI models |
| `/compact` | Passthrough | Requires AI to summarize conversation |
| `/context` | Passthrough | Requires backend session statistics (proposals, pipelines) |
| `/diff` | Passthrough | Requires backend task/issue change history |
| `/feedback` | Local | Displays a static feedback link — no backend needed |
| `/experimental` | Local | Toggles a browser-local experimental preference without requiring a backend route |
| `/usage` | Passthrough | Requires backend metrics (token consumption, timestamps) |
| `/share` | Local | Generates Markdown from frontend message state, triggers browser download |
| `/mcp` | Passthrough | Requires backend MCP configuration management |
| `/plan` | Passthrough | Requires AI reasoning for plan generation |

**Rationale**: This matches the original issue's type assignments and follows the established pattern where `/agent` is passthrough and `/theme`, `/notifications`, `/view` are local.

---

### 4. Handler File Organization

**Context**: Currently 3 handler files exist: `help.ts`, `settings.ts`, `agent.ts`. Adding 14 commands to one file would create bloat.

**Decision**: Group new handlers into 3 domain-specific files:
- `handlers/session.ts` — `/clear`, `/compact`, `/context` (session management)
- `handlers/monitoring.ts` — `/diff`, `/usage`, `/share`, `/feedback` (monitoring & export)
- `handlers/advanced.ts` — `/mcp`, `/plan`, `/model` (advanced configuration)
- `handlers/settings.ts` — Add `/experimental` to existing settings file (it's a settings toggle)

**Rationale**: Groups of 3-4 related commands per file maintains readability. The `/experimental` command fits naturally in `settings.ts` alongside `/theme`, `/language`, `/notifications`, and `/view` since it's a user preference toggle.

**Alternatives Considered**:
- One file per command (14 files): Rejected — excessive file count for simple stub handlers.
- All commands in one file: Rejected — 20+ handlers in one file hurts maintainability.

---

### 5. /clear Command Implementation Strategy

**Context**: `/clear` is classified as "Local + API call" — it needs both frontend state clearing and backend API call.

**Decision**: The `/clear` handler calls the existing `clearChat` function from `useChat.ts`, which already:
1. Calls `chatApi.clearMessages()` (DELETE /api/v1/chat/messages)
2. Clears proposals via `proposals.clearProposals()`
3. Resets `localMessages` to `[]`
4. Invalidates the `['chat', 'messages']` query cache

The `/clear` command handler needs access to this `clearChat` function through the `CommandContext`.

**Rationale**: Reusing the existing `clearChat` mutation avoids duplicating backend communication logic and ensures consistent behavior with any other "clear" UI triggers.

**Alternatives Considered**:
- Calling the API directly in the handler: Rejected — duplicates mutation logic and misses cache invalidation.
- Making `/clear` a passthrough command: Rejected — the clear action is primarily a frontend state operation with a backend side-effect, and the existing `clearChatMutation` already handles this.

---

### 6. /share Markdown Export Format

**Context**: The spec says `/share` generates "a Markdown-formatted file" and triggers a browser download.

**Decision**: Use a simple Markdown format with metadata header:
```markdown
# Solune Chat Export
**Exported**: {ISO timestamp}
**Messages**: {count}

---

## Conversation

**User** ({timestamp}):
{message content}

**Assistant** ({timestamp}):
{message content}
```

**Rationale**: Standard Markdown that renders well in any viewer. No custom templates needed (per spec assumption). The `react-markdown` dependency already in the project validates Markdown as the standard format.

**Alternatives Considered**:
- JSON export: Rejected — less human-readable, spec explicitly says Markdown.
- HTML export: Rejected — spec explicitly says Markdown.
- Including proposals/metadata: Rejected — scope creep; spec says "conversation" export.

---

### 7. /experimental Feature Toggle Persistence

**Context**: The spec says experimental features should be "persisted" (FR-009, FR-010).

**Decision**: Persist the experimental flag locally in the browser for this feature using frontend-managed storage. The command remains local and does not require a dedicated backend settings schema.

**Rationale**: The current shared settings types and update payloads do not define an `experimental` field, so documenting a backend settings mutation would be misleading for the current scope. Browser-local persistence still satisfies the local-command requirement without introducing unsupported schema changes.

**Alternatives Considered**:
- Persist via existing settings API: Rejected — the current `EffectiveUserSettings` and `UserPreferencesUpdate` schemas do not expose an `experimental` field.
- Separate API endpoint: Rejected — out of scope for this frontend-first command increment.

---

### 8. Backend Passthrough Command Handling

**Context**: Passthrough commands forward to the backend via the existing `send_message` endpoint. How does the backend differentiate slash commands from regular messages?

**Decision**: The backend's `send_message` endpoint already receives the full message content including the `/` prefix. The AI agent service (github-copilot-sdk / OpenAI) processes slash commands contextually. No special backend routing is needed — the AI interprets `/model`, `/compact`, etc., as instructions within the conversation.

**Rationale**: The existing `/agent` passthrough command works this way — the backend receives `/agent <description>` as message content and routes it to `_handle_agent_command()`. New passthrough commands follow the same pattern where the AI service understands the command intent from the message content.

**Alternatives Considered**:
- Add explicit command routing in backend: Rejected for initial implementation — adds complexity when the AI service can interpret commands naturally. Can be added later if precision is needed.
- Add a `command` field to ChatMessageRequest: Rejected — would require backend model changes and breaks the simple passthrough pattern.

---

### 9. Case-Insensitive Command Input (FR-023)

**Context**: The spec requires case-insensitive command handling (e.g., `/Clear` and `/clear` should behave identically).

**Decision**: Already handled by the existing `parseCommand()` function which lowercases the command name (`afterSlash.slice(0, spaceIndex).toLowerCase()`). No additional work needed.

**Rationale**: The registry lookup uses `registry.get(name.toLowerCase())` and the parser outputs lowercased names. This handles `/Clear`, `/CLEAR`, `/cLeAr` etc. identically.

---

### 10. Unknown Command Error (FR-003)

**Context**: The spec requires displaying an error with `/help` suggestion for unrecognized commands.

**Decision**: Already handled by the existing `executeCommand()` in `useCommands.ts` which returns `"Unknown command '${parsed.name}'. Type /help to see available commands."` for unregistered command names. No additional work needed.

**Rationale**: The existing error handling in `useCommands.ts` lines 65-70 already provides this exact behavior.

## Technology Best Practices

### TypeScript Command Handler Pattern
- Handlers should be pure functions (or async functions for I/O) accepting `(args: string, context: CommandContext)` and returning `CommandResult`
- Validate args before execution; return `{ success: false, message: '...' }` for invalid input
- Use `clearInput: true` to clear the chat input after successful execution
- Use `passthrough: true` to signal backend forwarding

### Frontend File Download (for /share)
- Use `Blob` + `URL.createObjectURL` + programmatic `<a>` click pattern
- Clean up object URLs with `URL.revokeObjectURL` to prevent memory leaks
- Standard browser API — no additional dependencies needed

### Settings Persistence Pattern (for /experimental)
- Store the current experimental flag in browser-managed storage
- Return the current status when called without arguments
- Treat repeated `on`/`off` calls as successful no-ops with a status message
