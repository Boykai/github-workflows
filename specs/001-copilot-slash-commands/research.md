# Research: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Feature**: 001-copilot-slash-commands | **Date**: 2026-03-27

## Research Tasks

### R1: Frontend Passthrough Pattern — How `/agent` and `/plan` work

**Decision**: Reuse the identical passthrough pattern used by `/agent` and `/plan`.

**Rationale**: The existing pattern is proven, minimal, and well-tested. When a command has `passthrough: true` in the registry, `useChat` forwards the raw message to the backend POST `/chat/messages` endpoint instead of executing the handler locally. The handler function (`agentHandler()` in `handlers/agent.ts`) is a stub returning `{ success: true, message: '', clearInput: true, passthrough: true }` — it only runs as a fallback. This approach requires zero frontend-side AI logic.

**Alternatives considered**:
- **Frontend-side Copilot SDK calls**: Rejected — would require exposing GitHub tokens to the browser and duplicating completion provider logic.
- **New dedicated `/copilot` REST endpoint**: Rejected — unnecessary; the existing `POST /chat/messages` endpoint already handles all command routing via the priority dispatcher.

**Source files examined**:
- `solune/frontend/src/lib/commands/handlers/agent.ts` (19 lines — stub handler pattern)
- `solune/frontend/src/lib/commands/registry.ts` (line 141–147 — agent registration with `passthrough: true`)

---

### R2: Backend Dispatch Chain — Priority insertion point for Copilot commands

**Decision**: Insert `_handle_copilot_command()` at priority 0.1, between the agent handler (priority 0.0) and the `/plan` prefix strip + transcript handler (priority 0.5).

**Rationale**: The dispatch chain in `send_message()` (chat.py lines 1050–1114) is a linear cascade: each handler returns `ChatMessage | None` — if non-None, the message is returned immediately. Priority 0.1 ensures Copilot commands are intercepted before the `/plan` prefix strip (line 1066) and before feature-request detection (priority 1), which could misroute `/explain` or `/new` as feature descriptions. The agent handler at priority 0.0 must remain first because it checks for active agent sessions.

**Alternatives considered**:
- **Priority 0 (same as agent)**: Rejected — agent handler must stay first to avoid intercepting ongoing agent sessions.
- **Priority 0.5 or later**: Rejected — `/plan` prefix strip at line 1066 would consume Copilot commands like `/plan` does; feature-request detection at priority 1 could misinterpret Copilot content as feature requests.

**Source files examined**:
- `solune/backend/src/api/chat.py` (lines 300–352 — `_handle_agent_command()`, lines 1050–1114 — dispatch chain)

---

### R3: CopilotCompletionProvider.complete() — Message format and usage

**Decision**: Call `CopilotCompletionProvider.complete()` with a `messages` list containing one `{"role": "system", "content": <prompt>}` and one `{"role": "user", "content": <args>}` dict. Pass `github_token=session.access_token`.

**Rationale**: The `complete()` method (completion_providers.py lines 154–230) iterates over messages extracting `system` and `user` content. It creates a Copilot SDK session with the system message and sends the user content. The method accepts `github_token` as a required parameter and uses the shared `CopilotClientPool` for client lifecycle management. This is the same pattern used by the AI agent service.

**Alternatives considered**:
- **Direct Copilot SDK usage**: Rejected — would bypass the existing client pool and session management.
- **AIAgentService wrapper**: Rejected — AIAgentService adds feature-detection and task-generation logic not needed for passthrough commands.

**Source files examined**:
- `solune/backend/src/services/completion_providers.py` (lines 138–230 — CopilotCompletionProvider class, lines 335–359 — factory)

---

### R4: Command Detection — Matching logic for `/new` vs `/newNotebook`

**Decision**: Sort commands by length (longest first) when matching, so `/newNotebook` is checked before `/new`. Match only when the command name is followed by a space or end of input.

**Rationale**: The spec explicitly calls out the `/new` vs `/newNotebook` prefix collision (edge case in spec.md line 89). Longest-match-first ensures `/newNotebook data analysis` matches `/newNotebook` (not `/new` with args `Notebook data analysis`). The match boundary (space or end-of-input) ensures `/newtest` does not match `/new`.

**Alternatives considered**:
- **Exact word-boundary regex (`\b`)**: Rejected — `\b` would match at camelCase boundaries, which is correct here but fragile for future command names.
- **Simple startswith without length sorting**: Rejected — would incorrectly match `/new` when the user typed `/newNotebook`.

**Source files examined**:
- `specs/001-copilot-slash-commands/spec.md` (lines 88–89 — edge cases for `/new` and `/newNotebook`)

---

### R5: Error Handling Pattern — Copilot command failures

**Decision**: Use try/except in `_handle_copilot_command()` with a generic error message pattern matching `_handle_agent_command()`. Log the full exception server-side; return a safe message to the user.

**Rationale**: The agent handler (chat.py lines 339–343) catches all exceptions, logs via `logger.error()`, and returns a generic error string. The `handle_service_error()` utility (logging_utils.py:224–267) is available but raises exceptions rather than returning error messages — not suitable for the dispatch chain which expects `ChatMessage | None` return values. The agent handler's inline try/except is the correct pattern.

**Alternatives considered**:
- **`handle_service_error()` utility**: Rejected — it raises exceptions, which would propagate up through the dispatch chain instead of returning a user-friendly ChatMessage.
- **No error handling (let exceptions bubble)**: Rejected — would expose internal details to the user.

**Source files examined**:
- `solune/backend/src/api/chat.py` (lines 339–343 — agent handler error pattern)
- `solune/backend/src/logging_utils.py` (lines 224–267 — `handle_service_error()`)

---

### R6: Frontend Category Grouping — CommandAutocomplete.tsx design

**Decision**: Add an optional `category?: 'solune' | 'copilot'` field to `CommandDefinition`. In `CommandAutocomplete.tsx`, group commands by category and render section headers before each group. Default untagged commands to `'solune'`.

**Rationale**: The current `CommandAutocomplete.tsx` (72 lines) renders a flat `<ul>` of commands. Adding category headers requires grouping the input `commands` array. The simplest approach: sort commands into `solune` and `copilot` arrays, render each group with a header `<li>` that has `role="presentation"` (not selectable). The highlighted index calculation must account for header items being non-interactive.

**Alternatives considered**:
- **Separate `<ul>` per category**: Rejected — would break the single `role="listbox"` accessibility pattern and keyboard navigation.
- **CSS-only visual separator**: Rejected — spec explicitly requires section header text ("Solune" and "GitHub Copilot").

**Source files examined**:
- `solune/frontend/src/components/chat/CommandAutocomplete.tsx` (72 lines — current flat list)
- `solune/frontend/src/lib/commands/types.ts` (lines 40–50 — CommandDefinition interface)

---

### R7: Test Strategy — Frontend and backend test coverage

**Decision**: Frontend tests go in `solune/frontend/src/lib/commands/registry.test.ts` (extending existing file). Backend tests go in `solune/backend/tests/unit/test_copilot_commands.py` (new file).

**Rationale**: Frontend tests are colocated with implementation (`.test.ts` alongside `.ts`), not in `__tests__/` directories. The existing `registry.test.ts` (246 lines) covers command registration, parsing, and filtering — extending it with Copilot command assertions is the DRY approach. Backend tests follow the `tests/unit/` convention used by `test_api_chat.py` (1064 lines). The spec requires: (FR-012) frontend tests for registry presence + parseCommand + handler shape; (FR-013) backend tests for detection + rejection + system prompt verification with mocks.

**Alternatives considered**:
- **Separate `copilot-commands.test.ts` file**: Viable but less DRY — would duplicate registry setup/teardown and import patterns already in `registry.test.ts`.
- **Integration tests only**: Rejected — spec explicitly requires unit tests with mocks (FR-013).

**Source files examined**:
- `solune/frontend/src/lib/commands/registry.test.ts` (246 lines — existing test structure)
- `solune/backend/tests/unit/test_api_chat.py` (1064 lines — backend test patterns)

---

## Summary of Resolved Clarifications

All technical context items from the plan are resolved:

| Item | Resolution |
|------|-----------|
| Passthrough pattern | Identical to `/agent` — stub handler + `passthrough: true` in registry |
| Dispatch priority | 0.1 — between agent (0.0) and transcript/plan (0.5) |
| Provider message format | `[{"role": "system", ...}, {"role": "user", ...}]` with `github_token` param |
| Command matching | Longest-first sort, match on space-or-EOI boundary |
| Error handling | Inline try/except in dispatcher (agent handler pattern) |
| Category UI | Optional `category` field, group-and-header rendering in `CommandAutocomplete.tsx` |
| Test placement | Colocated frontend (registry.test.ts), `tests/unit/` backend (new file) |
