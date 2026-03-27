# Feature Specification: Add 9 GitHub Copilot Slash Commands to Solune Chat

**Feature Branch**: `001-copilot-slash-commands`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "Add 9 GitHub Copilot Slash Commands to Solune Chat (Frontend + Backend + Tests)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Invoke Copilot Commands from Chat Input (Priority: P1)

As a Solune chat user, I want to type a slash command (e.g., `/explain`, `/fix`, `/tests`) in the chat input and receive an AI-powered coding response so that I can get explanations, fixes, documentation, tests, and more without leaving the Solune interface.

**Why this priority**: This is the core value proposition — without the ability to invoke commands and receive responses, no other feature matters. It delivers immediate, standalone value for every user interaction.

**Independent Test**: Can be fully tested by typing `/explain What is a closure?` in the chat input, submitting, and verifying an AI-generated explanation appears in the chat thread. Delivers direct coding assistance value.

**Acceptance Scenarios**:

1. **Given** a user is in the Solune chat interface with a valid session, **When** they type `/explain What is a closure?` and press Enter, **Then** the system sends the message to the backend, processes it through the Copilot completion provider, and displays an AI-generated explanation in the chat thread.
2. **Given** a user is in the Solune chat interface, **When** they type `/fix const x = [1,2,3; console.log(x)` and submit, **Then** the system returns an AI-generated response identifying the syntax error and providing corrected code with an explanation.
3. **Given** a user submits `/doc function add(a, b) { return a + b; }`, **Then** the system returns idiomatic documentation comments for the provided function.
4. **Given** a user submits `/tests function multiply(a, b) { return a * b; }`, **Then** the system returns comprehensive unit tests including edge cases for the provided function.
5. **Given** a user submits any of the 9 supported Copilot commands (`/explain`, `/fix`, `/doc`, `/tests`, `/setupTests`, `/new`, `/newNotebook`, `/search`, `/startDebugging`) with accompanying text, **Then** each command produces a contextually appropriate AI response tailored to that command's intent.
6. **Given** a user submits a Copilot command, **Then** the chat input field is cleared after submission.
7. **Given** a user submits a Copilot command, **Then** the system uses the user's existing authentication token transparently — no additional login or authorization is required.

---

### User Story 2 - Discover Copilot Commands via Autocomplete (Priority: P2)

As a Solune chat user, I want to see all available Copilot commands in an organized autocomplete dropdown when I type `/` so that I can discover and select the right command without memorizing them.

**Why this priority**: Discoverability directly impacts adoption. Without visible commands in the autocomplete, users must know command names by heart, severely limiting usage. This story makes the commands accessible but depends on the commands existing (P1).

**Independent Test**: Can be fully tested by typing `/` in the chat input and verifying the autocomplete dropdown appears with two labeled sections — one for existing Solune commands and one for the 9 new Copilot commands. Delivers navigation and discovery value.

**Acceptance Scenarios**:

1. **Given** a user types `/` in the chat input, **When** the autocomplete dropdown appears, **Then** it displays commands organized under two distinct section headers: "Solune" (for `/help`, `/agent`, `/plan`, `/clear`) and "GitHub Copilot" (for the 9 new commands).
2. **Given** a user types `/ex` in the chat input, **When** the autocomplete dropdown filters results, **Then** the `/explain` command appears under the "GitHub Copilot" header.
3. **Given** a user types `/` in the chat input, **When** the autocomplete dropdown is visible, **Then** the Copilot commands are visually separated from Solune commands via distinct category headers.
4. **Given** a user selects a Copilot command from the autocomplete dropdown, **Then** the command is inserted into the chat input and the user can append arguments before submitting.

---

### User Story 3 - Existing Commands Remain Unaffected (Priority: P1)

As a Solune chat user, I want my existing slash commands (`/help`, `/agent`, `/plan`, `/clear`) to continue working exactly as before so that the addition of new Copilot commands does not disrupt my current workflow.

**Why this priority**: Backward compatibility is critical. Existing users rely on current commands for daily workflows. Regressions would erode trust and block adoption of the new Copilot commands. This shares P1 because breaking existing commands is unacceptable.

**Independent Test**: Can be fully tested by invoking each existing command (`/help`, `/agent`, `/plan`, `/clear`) and verifying the behavior matches pre-change expectations. Delivers confidence in system stability.

**Acceptance Scenarios**:

1. **Given** a user types `/help` and submits, **Then** the help response is identical to the behavior before Copilot commands were added.
2. **Given** a user types `/agent` with arguments and submits, **Then** the agent handler processes the request as before with no change in routing or behavior.
3. **Given** a user types `/plan` with arguments and submits, **Then** the plan handler processes the request as before.
4. **Given** a user types `/clear` and submits, **Then** the chat is cleared as before.
5. **Given** a user types `/help` in the autocomplete, **Then** the command appears under the "Solune" section header, not under "GitHub Copilot."

---

### User Story 4 - Tailored Responses per Command Intent (Priority: P2)

As a Solune chat user, I want each Copilot command to produce a response specifically tailored to that command's purpose (e.g., `/doc` generates documentation, `/setupTests` recommends test frameworks) so that I get focused, actionable results rather than generic AI output.

**Why this priority**: Differentiated responses are what make individual commands valuable beyond a generic "ask AI" input. Without tailored prompts, there would be no reason to have 9 separate commands. This depends on the base command infrastructure (P1).

**Independent Test**: Can be tested by submitting the same code snippet to two different commands (e.g., `/doc function add(a,b) { return a+b }` vs. `/tests function add(a,b) { return a+b }`) and verifying the responses differ meaningfully — one produces documentation comments, the other produces unit tests.

**Acceptance Scenarios**:

1. **Given** a user submits `/explain` with a code snippet, **Then** the response explains the code logic, concepts, and provides examples — it does not generate tests or documentation.
2. **Given** a user submits `/fix` with broken code, **Then** the response identifies specific issues, provides corrected code, and explains each fix.
3. **Given** a user submits `/doc` with a function, **Then** the response generates idiomatic documentation comments appropriate to the language detected.
4. **Given** a user submits `/tests` with a function, **Then** the response generates comprehensive unit tests including edge cases and boundary conditions.
5. **Given** a user submits `/setupTests` with a project description, **Then** the response recommends a test framework and provides setup steps and configuration.
6. **Given** a user submits `/new` with a project idea, **Then** the response generates a project scaffold with a directory structure and boilerplate files.
7. **Given** a user submits `/newNotebook` with a topic, **Then** the response generates a Jupyter notebook outline with markdown and code cells.
8. **Given** a user submits `/search` with a description of what they are looking for, **Then** the response generates effective code search queries and regex patterns.
9. **Given** a user submits `/startDebugging` with a project/language description, **Then** the response generates a debug configuration appropriate for the user's setup.

---

### User Story 5 - Automated Test Coverage for Copilot Commands (Priority: P3)

As a developer maintaining Solune, I want comprehensive automated tests for the new Copilot command feature — covering command registration, parsing, handler behavior, backend routing, and prompt correctness — so that regressions are caught before they reach production.

**Why this priority**: Tests protect the feature long-term but are not user-facing. The feature must work first (P1, P2) before tests provide regression safety. Still important for ongoing maintenance confidence.

**Independent Test**: Can be tested by running the frontend and backend test suites and verifying all new tests pass. Delivers development confidence and regression safety.

**Acceptance Scenarios**:

1. **Given** the frontend test suite is run, **Then** tests confirm all 9 Copilot commands are registered in the command registry.
2. **Given** the frontend test suite is run, **Then** tests confirm the command parser correctly extracts command names and arguments for each Copilot command.
3. **Given** the frontend test suite is run, **Then** tests confirm the Copilot passthrough handler returns the expected shape (success, clearInput, passthrough).
4. **Given** the backend test suite is run, **Then** tests confirm command detection correctly identifies all 9 Copilot commands and extracts arguments.
5. **Given** the backend test suite is run, **Then** tests confirm command detection rejects non-Copilot input (e.g., `/help`, `/agent`, plain text).
6. **Given** the backend test suite is run, **Then** tests confirm each command is dispatched with the correct intent-specific prompt.
7. **Given** the full backend test suite is run, **Then** no existing tests are broken by the addition of Copilot command handling.
8. **Given** the full frontend test suite is run, **Then** no existing tests are broken by the addition of Copilot commands to the registry.

---

### Edge Cases

- What happens when a user submits a Copilot command with no arguments (e.g., just `/explain` with no text)? The system should still forward the command to the backend, which returns a helpful prompt asking the user to provide input.
- What happens when the Copilot completion provider is unreachable or returns an error? The system should display a user-friendly error message in the chat thread rather than failing silently or crashing.
- What happens when a user types a command that partially matches a Copilot command (e.g., `/exp`)? The autocomplete should filter and show matching commands; if submitted without selecting from autocomplete, the system should treat it as plain text (not a recognized command).
- What happens when a user types a command that does not exist (e.g., `/foobar`)? The system should treat it as regular chat input and not route it to the Copilot handler.
- What happens when the user's authentication token is expired or invalid? The system should propagate the error from the completion provider and display a meaningful message to the user.
- What happens when a Copilot command is submitted with extremely long input text? The system should forward it as-is and let the completion provider handle token limits, returning an appropriate response or error.
- What happens when multiple Copilot commands are submitted in rapid succession? Each command should be processed independently and responses should appear in the correct order in the chat thread.

## Requirements *(mandatory)*

### Functional Requirements

**Command Registration & Frontend**

- **FR-001**: System MUST register 9 new slash commands (`/explain`, `/fix`, `/doc`, `/tests`, `/setupTests`, `/new`, `/newNotebook`, `/search`, `/startDebugging`) in the frontend command registry, each marked as passthrough so that raw content is forwarded to the backend without frontend-side processing.
- **FR-002**: System MUST add a category field to command definitions that distinguishes between "solune" and "copilot" command types, with all existing commands tagged as "solune" and all 9 new commands tagged as "copilot."
- **FR-003**: System MUST implement a Copilot passthrough handler that returns a standardized response indicating success with input clearing and passthrough enabled, following the same pattern used by the existing agent command handler.
- **FR-004**: System MUST render category section headers ("Solune" and "GitHub Copilot") in the command autocomplete dropdown to visually group commands by their category when the user triggers the autocomplete.

**Backend Command Processing**

- **FR-005**: System MUST detect incoming Copilot commands by matching message content against the set of 9 recognized command names and extract the command arguments from the remainder of the message.
- **FR-006**: System MUST process detected Copilot commands at a priority level that falls after agent command handling but before plan prefix handling and transcript processing, ensuring Copilot commands are not misrouted to other handlers.
- **FR-007**: System MUST execute each Copilot command by constructing a message with the appropriate intent-specific prompt and forwarding it to the existing completion provider using the user's authentication token.
- **FR-008**: System MUST store the Copilot command response as an assistant message in the chat thread, following the same pattern used for agent command responses.

**Intent-Specific Prompts**

- **FR-009**: System MUST provide 9 distinct, intent-specific prompts — one for each Copilot command — that direct the AI to produce responses tailored to the command's purpose:
  - `/explain`: Explain code or concepts with clear examples and step-by-step breakdowns
  - `/fix`: Identify issues in provided code and return corrected code with explanation of each fix
  - `/doc`: Generate idiomatic documentation comments appropriate for the detected language
  - `/tests`: Generate comprehensive unit tests including edge cases and boundary conditions
  - `/setupTests`: Recommend a test framework and provide setup steps and configuration for the user's project
  - `/new`: Generate a project scaffold with directory structure and boilerplate files
  - `/newNotebook`: Generate a Jupyter notebook outline with markdown and code cells
  - `/search`: Generate effective code search queries, regex patterns, and search strategies
  - `/startDebugging`: Generate a debug launch configuration appropriate for the user's project and language

**Constraints**

- **FR-010**: System MUST NOT introduce new authentication flows or provider clients — all Copilot commands MUST use the existing completion provider and the user's existing token.
- **FR-011**: System MUST NOT alter the behavior of existing commands (`/help`, `/agent`, `/plan`, `/clear`) in any way — routing, response format, and user experience must remain identical.
- **FR-012**: System MUST clear the chat input field after a Copilot command is submitted.
- **FR-013**: System MUST NOT implement any of the explicitly excluded commands (`/clear`, `/compact`, `/fork`, `/yolo`, `init`, `/agents`, `/create-*`) as part of this feature.

**Testing**

- **FR-014**: System MUST include frontend tests verifying all 9 commands exist in the registry, command parsing works correctly for each command, and the handler returns the expected passthrough response shape.
- **FR-015**: System MUST include backend tests verifying command detection correctly identifies all 9 Copilot commands, extracts arguments, rejects non-Copilot input, and dispatches each command with the correct intent-specific prompt.
- **FR-016**: System MUST include backend tests verifying that the full existing test suite passes without regressions after Copilot command handling is added.

### Key Entities

- **Copilot Command**: A slash command (one of 9 defined commands) that a user types in the chat input. Attributes: command name, arguments (user-provided text), category ("copilot"), passthrough flag. Relationship: maps to a specific intent prompt.
- **Intent Prompt**: A tailored system-level instruction associated with each Copilot command that directs the AI completion provider to generate a response matching the command's purpose. Attributes: command name, prompt text. Relationship: one-to-one with a Copilot Command.
- **Command Category**: A classification label ("solune" or "copilot") applied to each command definition to enable grouped display in the autocomplete dropdown. Relationship: one category per command, many commands per category.

### Assumptions

- The existing completion provider is capable of handling the volume and type of requests generated by the 9 new Copilot commands without requiring scaling changes.
- The user's existing authentication token has sufficient permissions to invoke the completion provider for all 9 command types.
- The autocomplete dropdown's current rendering approach can accommodate additional section headers without requiring a redesign of the dropdown component.
- Error responses from the completion provider are already handled by the existing error-handling infrastructure and will surface user-friendly messages without additional work specific to Copilot commands.
- The 9 command names (`/explain`, `/fix`, `/doc`, `/tests`, `/setupTests`, `/new`, `/newNotebook`, `/search`, `/startDebugging`) do not conflict with any existing or planned command names in the system.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can invoke any of the 9 Copilot commands and receive a relevant AI-generated response within the same response time expectations as existing AI-powered commands.
- **SC-002**: 100% of the 9 Copilot commands appear in the autocomplete dropdown under the "GitHub Copilot" section header when a user types `/`.
- **SC-003**: All existing commands (`/help`, `/agent`, `/plan`, `/clear`) continue to function identically — zero behavioral regressions as verified by the existing test suite passing with no modifications.
- **SC-004**: Each Copilot command produces a response that is meaningfully differentiated from other commands when given the same input (e.g., `/doc` and `/tests` on the same function produce documentation vs. tests, respectively).
- **SC-005**: The chat input field is cleared after every Copilot command submission, ensuring a clean state for the next interaction.
- **SC-006**: No new authentication steps or prompts are required for users — Copilot commands work transparently with the user's existing session.
- **SC-007**: All new frontend tests pass, confirming command registration, parsing, and handler behavior for each of the 9 commands.
- **SC-008**: All new backend tests pass, confirming command detection, argument extraction, prompt mapping, and provider invocation for each of the 9 commands.
- **SC-009**: The full existing frontend and backend test suites pass without modification, confirming zero regressions.
