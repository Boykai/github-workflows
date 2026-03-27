# Feature Specification: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Feature Branch**: `001-copilot-slash-commands`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "Add 9 GitHub Copilot Slash Commands to Solune Chat (Frontend + Backend + Tests)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invoke a Copilot Command from Chat Input (Priority: P1)

As a Solune chat user, I want to type a GitHub Copilot slash command (e.g., `/explain What is a closure?`) directly in the chat input so that I receive an AI-powered coding assistance response without leaving the Solune interface.

**Why this priority**: This is the core value proposition — enabling users to access Copilot capabilities inside Solune. Without this, none of the other stories deliver value.

**Independent Test**: Can be fully tested by typing `/explain What is a closure?` in the chat input, submitting, and verifying that a Copilot-generated explanation appears as an assistant message in the conversation.

**Acceptance Scenarios**:

1. **Given** a user is on the Solune chat page with a valid GitHub token, **When** they type `/explain What is a closure?` and press Enter, **Then** the backend routes the message to the Copilot completion provider with the explain-specific system prompt and the assistant response appears in the chat.
2. **Given** a user submits `/fix const x = [1,2,3]; x.map(i => i +)`, **When** the backend processes the command, **Then** the response contains corrected code with an explanation of the fix.
3. **Given** a user submits `/tests function add(a, b) { return a + b; }`, **When** the backend processes the command, **Then** the response contains generated unit tests covering normal inputs and edge cases.
4. **Given** a user submits a Copilot command, **When** the backend returns the response, **Then** the chat input field is cleared.
5. **Given** the Copilot completion provider is unreachable, **When** a user submits any Copilot command, **Then** the user receives a user-friendly error message without exposing internal details.

---

### User Story 2 - Discover Copilot Commands via Autocomplete Dropdown (Priority: P2)

As a Solune chat user, I want to see all available Copilot commands in the autocomplete dropdown (grouped under a "GitHub Copilot" header) when I type `/` so that I can discover and select the right command without memorizing them.

**Why this priority**: Discoverability is critical for adoption — users need to know which commands are available. This story depends on the commands existing (P1) but is independently testable through the UI.

**Independent Test**: Can be fully tested by typing `/` in the chat input and verifying the dropdown shows two category sections: "Solune" (with /help, /agent, /plan, /clear) and "GitHub Copilot" (with all 9 new commands).

**Acceptance Scenarios**:

1. **Given** a user is on the Solune chat page, **When** they type `/` in the chat input, **Then** the autocomplete dropdown displays commands grouped under "Solune" and "GitHub Copilot" section headers.
2. **Given** the autocomplete dropdown is open, **When** the user views the "GitHub Copilot" section, **Then** all 9 commands are listed: /explain, /fix, /doc, /tests, /setupTests, /new, /newNotebook, /search, and /startDebugging.
3. **Given** the autocomplete dropdown is open, **When** the user views the "Solune" section, **Then** the existing commands (/help, /agent, /plan, /clear) remain visually and functionally unchanged.
4. **Given** the user types `/ex`, **When** the autocomplete filters the list, **Then** `/explain` appears in the filtered results under the "GitHub Copilot" section.
5. **Given** the user selects a Copilot command from the dropdown, **When** the command is inserted into the input, **Then** it functions identically to manually typing the command.

---

### User Story 3 - Each Copilot Command Produces Intent-Specific Responses (Priority: P3)

As a Solune chat user, I want each of the 9 Copilot commands to produce responses tailored to their specific intent (explaining, fixing, documenting, testing, etc.) so that the AI output matches what I asked for.

**Why this priority**: Command-specific prompts ensure each command delivers differentiated value. Without distinct prompts, all commands would behave identically, undermining the purpose of having separate commands.

**Independent Test**: Can be tested by submitting the same code snippet to `/explain`, `/fix`, and `/doc` and verifying that each produces a qualitatively different response matching its stated intent.

**Acceptance Scenarios**:

1. **Given** a user submits `/doc function add(a, b) { return a + b; }`, **When** the backend processes the command, **Then** the response contains idiomatic documentation comments (e.g., JSDoc, docstring) for the function.
2. **Given** a user submits `/setupTests I'm using a Python FastAPI project`, **When** the backend processes the command, **Then** the response recommends a test framework (e.g., pytest) and provides configuration steps.
3. **Given** a user submits `/new Create a React app with TypeScript`, **When** the backend processes the command, **Then** the response contains a project scaffold with directory structure.
4. **Given** a user submits `/newNotebook Data analysis with pandas`, **When** the backend processes the command, **Then** the response contains a Jupyter notebook outline with cell descriptions.
5. **Given** a user submits `/search memory leak in event listeners`, **When** the backend processes the command, **Then** the response contains effective code search queries and patterns.
6. **Given** a user submits `/startDebugging Node.js Express app`, **When** the backend processes the command, **Then** the response contains a debug launch.json configuration.

---

### User Story 4 - Existing Commands Remain Unaffected (Priority: P1)

As a Solune chat user, I want my existing commands (/help, /agent, /plan, /clear) to continue working exactly as before so that this new feature does not break my existing workflow.

**Why this priority**: Backward compatibility is essential — any regression in existing functionality would undermine user trust. This is P1 because it is a hard constraint.

**Independent Test**: Can be tested by exercising each existing command (/help, /agent, /plan, /clear) and verifying their output and behavior are identical to the pre-change baseline.

**Acceptance Scenarios**:

1. **Given** a user types `/help`, **When** the command is processed, **Then** the help output displays exactly as before the change.
2. **Given** a user types `/agent How do I deploy?`, **When** the command is processed, **Then** the agent handler responds as it did before the change.
3. **Given** a user types `/plan`, **When** the command is processed, **Then** the plan handler responds as it did before the change.
4. **Given** a user types `/clear`, **When** the command is processed, **Then** the chat is cleared as it did before the change.
5. **Given** a user types a non-command message (e.g., "Hello"), **When** the message is processed, **Then** it is routed to the default handler without interference from the Copilot command handler.

---

### Edge Cases

- What happens when a user submits a Copilot command with no arguments (e.g., `/explain` with no code)? The system should pass the empty argument to Copilot and return whatever response the provider generates.
- What happens when the GitHub token is missing or expired? The system should return a user-friendly error indicating authentication is required, without exposing token details.
- What happens when a user types a command that starts like a Copilot command but is not one (e.g., `/explains`)? The system should not match it as a Copilot command; it should fall through to the default handler.
- What happens when a user types `/new` (shortest Copilot command name) followed immediately by other text without a space (e.g., `/newtest`)? The system should only match `/new` if it is followed by a space or end of input, and `/newNotebook` should match exactly.
- What happens when two commands share a prefix (e.g., `/new` and `/newNotebook`)? The system should match the longest matching command first to avoid ambiguity.
- How does the system handle very long arguments (e.g., 10,000+ characters of code)? The system should pass the full argument to the provider, relying on the provider's own token limits.
- What happens when the Copilot completion provider returns an error? The system should surface a generic error message to the user without leaking internal error details.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST register 9 new slash commands (/explain, /fix, /doc, /tests, /setupTests, /new, /newNotebook, /search, /startDebugging) in the frontend command registry, each with `passthrough: true` so that raw content is forwarded to the backend without frontend-side processing.
- **FR-002**: System MUST add an optional `category` field to the command definition type, accepting values of `'solune'` or `'copilot'`, and tag all existing commands as `'solune'` and all 9 new commands as `'copilot'`.
- **FR-003**: System MUST implement a Copilot passthrough handler function that returns `{ success: true, message: '', clearInput: true, passthrough: true }`, following the same pattern as the existing agent handler.
- **FR-004**: System MUST render category section headers ("Solune" and "GitHub Copilot") in the command autocomplete dropdown to visually group commands by category when the autocomplete list is displayed.
- **FR-005**: System MUST create a backend service containing: a set of the 9 Copilot command names, a dictionary mapping each command to a tailored system prompt, a detection function that identifies Copilot commands and extracts arguments, and an execution function that builds messages and calls the existing Copilot completion provider.
- **FR-006**: System MUST add a Copilot command handler in the chat dispatcher at a priority between the agent handler and the plan/transcript handler, to prevent misrouting Copilot commands to feature detection or other handlers.
- **FR-007**: System MUST provide 9 distinct, intent-specific system prompts: /explain (explain code/concepts with examples), /fix (identify issues and provide corrected code with explanation), /doc (generate idiomatic documentation comments), /tests (generate comprehensive unit tests with edge cases), /setupTests (recommend test framework and provide setup steps/config), /new (generate project scaffold with directory structure), /newNotebook (generate Jupyter notebook outline with cells), /search (generate effective code search queries/patterns), /startDebugging (generate debug launch.json config for the user's setup).
- **FR-008**: System MUST NOT require changes to the existing Copilot completion provider — the existing provider and its client pool MUST be reused as-is with no new API clients or authentication flows introduced.
- **FR-009**: System MUST clear the chat input field after a Copilot command is submitted (clearInput: true).
- **FR-010**: System MUST NOT match partial command names as Copilot commands — only exact command-name matches (followed by a space or end of input) are valid. When multiple valid Copilot commands share a common prefix (e.g., `/new` and `/newNotebook`), the system MUST resolve the input using the longest matching command name first (e.g., `/newNotebook` MUST be parsed as `/newNotebook`, not `/new`).
- **FR-011**: System MUST ensure that commands /clear, /compact, /fork, /yolo, init, /agents, and /create-* are explicitly excluded and not affected by this implementation.
- **FR-012**: Frontend MUST include tests verifying all 9 commands exist in the registry, that parseCommand works correctly for Copilot commands, and that the handler returns the expected passthrough shape.
- **FR-013**: Backend MUST include tests verifying the detection function correctly parses all 9 commands, rejects non-Copilot input, and the execution function calls the completion provider with the correct system prompt.

### Key Entities

- **CopilotCommand**: Represents one of the 9 supported Copilot slash commands. Key attributes: command name (string), system prompt (string), category ("copilot").
- **CommandDefinition**: Extended frontend type that now includes an optional category field (`'solune' | 'copilot'`) for grouping commands in the UI.
- **ChatMessage**: Existing entity representing a message in the chat conversation. Used to store both the user's Copilot command input and the assistant's generated response.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can invoke any of the 9 Copilot commands and receive a relevant AI-generated response within the same timeframe as existing agent commands.
- **SC-002**: All 9 Copilot commands appear in the autocomplete dropdown under a clearly labeled "GitHub Copilot" section header when a user types `/`.
- **SC-003**: Existing commands (/help, /agent, /plan, /clear) continue to function identically to their pre-change behavior with zero regressions.
- **SC-004**: All automated frontend checks in the standard CI pipeline pass, including coverage for the 9 Copilot command registrations, parseCommand behavior, and handler return shape.
- **SC-005**: All automated backend checks in the standard CI pipeline pass, including coverage for command detection, argument extraction, rejection of non-Copilot input, and correct system prompt usage.
- **SC-006**: No regressions are detected in existing backend automated test suites when the Copilot command functionality is enabled.
- **SC-007**: No regressions are detected in existing frontend automated test suites and the frontend build pipeline when the Copilot command functionality is enabled.
- **SC-008**: Each of the 9 commands produces a response that is qualitatively distinct and aligned with its stated intent (e.g., /explain produces explanations, /fix produces corrections).
- **SC-009**: No new API clients, authentication flows, or changes to the existing Copilot completion provider are required.

## Assumptions

- The existing Copilot completion provider (`CopilotCompletionProvider.complete()`) is functional and accessible from the backend, requiring only a GitHub token and message payload.
- Users already have valid GitHub tokens available through the existing authentication/passthrough mechanism — no new auth flow is needed.
- The 9 command names (/explain, /fix, /doc, /tests, /setupTests, /new, /newNotebook, /search, /startDebugging) are final and will not change during implementation.
- The passthrough pattern (frontend sends raw input → backend builds prompt → calls provider) is the confirmed architecture, matching the existing /agent command pattern.
- The priority ordering in the chat dispatcher (agent=0.0, copilot=0.1, plan/transcript=0.5) is correct and sufficient to prevent misrouting.
- Copilot commands with empty arguments are valid — the system passes them through and returns whatever the provider generates.
- Error handling for Copilot commands reuses the existing standard service error-handling approach used elsewhere in the system, surfacing user-friendly messages without leaking internal details.
