# Feature Specification: Enhance #help and General # Commands with Robust, Best-Practice Chat UX

**Feature Branch**: `018-help-commands-ux`  
**Created**: 2026-03-04  
**Status**: Draft  
**Input**: User description: "Update to provide more robust chat #help and general # commands details for a better user experience. Use best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover All Available Commands via #help (Priority: P1)

As a chat user, I want to type `#help` and receive a well-structured, categorized list of every available # command so that I can quickly scan and discover what actions are available without memorizing them.

**Why this priority**: Command discovery is the primary entry point for all users. Without a clear, categorized help output, users cannot effectively use any other commands. This is the foundation for all command interactions.

**Independent Test**: Can be fully tested by typing `#help` in the chat input and verifying the response contains all registered commands organized into logical categories with names, descriptions, and usage examples.

**Acceptance Scenarios**:

1. **Given** a user is in the chat interface, **When** they type `#help` and press enter, **Then** the system displays a categorized list of all available # commands grouped by function (e.g., General, Settings, Workflow).
2. **Given** the #help output is displayed, **When** the user reads any command entry, **Then** each entry shows the command name, a one-line description, and the usage syntax with required and optional parameters clearly distinguished.
3. **Given** the #help output is displayed, **When** a new command has been registered in the system, **Then** it automatically appears in the #help output under the appropriate category without manual updates to the help text.
4. **Given** the user is on a narrow viewport or mobile device, **When** they view the #help output, **Then** the content remains readable without requiring horizontal scrolling.

---

### User Story 2 - Receive Context-Sensitive Error Guidance (Priority: P2)

As a chat user, I want to receive clear, actionable usage hints when I mistype a command or omit required arguments so that I can correct my input immediately without needing to consult #help.

**Why this priority**: Inline error guidance is the second most impactful improvement. Users who already know commands exist but make mistakes need immediate, targeted feedback rather than generic errors or silent failures.

**Independent Test**: Can be fully tested by invoking commands with missing arguments (e.g., `#theme` without a value), incorrect arguments (e.g., `#theme purple`), and misspelled command names (e.g., `#hep`), then verifying each returns a specific, helpful error message.

**Acceptance Scenarios**:

1. **Given** a user types a command with required arguments missing (e.g., `#theme`), **When** the command is executed, **Then** the system displays a usage hint showing the correct syntax and lists the valid parameter options.
2. **Given** a user types a command with an invalid argument (e.g., `#theme purple`), **When** the command is executed, **Then** the system indicates the argument is invalid, shows the valid options, and displays the correct syntax.
3. **Given** a user types a command name that is close to a registered command (e.g., `#hep` or `#theam`), **When** the command is executed, **Then** the system suggests the closest matching command(s) as a "Did you mean?" hint alongside the standard unknown-command message.
4. **Given** a user types just `#` with no command name, **When** they press enter, **Then** the system displays a brief prompt directing them to type `#help` for available commands, consistent with current behavior.

---

### User Story 3 - Consistent and Accessible Response Formatting (Priority: P3)

As a chat user, I want all # command responses to follow a consistent visual style so that I can quickly scan and understand outputs regardless of which command I used.

**Why this priority**: Consistent formatting builds user trust and reduces cognitive load. While the system works without it, polished formatting significantly improves the day-to-day experience.

**Independent Test**: Can be tested by executing multiple different commands and verifying that success messages, error messages, and informational outputs all follow the same structural pattern (header, content, contextual hints).

**Acceptance Scenarios**:

1. **Given** a user successfully executes any # command, **When** the response is displayed, **Then** it uses a consistent structure: a brief summary line followed by detail (if any), using the same visual conventions across all commands.
2. **Given** a user triggers an error on any # command, **When** the error response is displayed, **Then** it follows the same error format: what went wrong, how to fix it, and where to get more help.
3. **Given** a user views command responses, **When** inspecting the output, **Then** meaning is conveyed through text and structure (not color alone), command syntax is visually distinct from descriptive text, and the output does not rely on emoji as the sole indicator of status.

---

### User Story 4 - Quick Help for a Specific Command (Priority: P4)

As a chat user who already knows the command name but has forgotten its syntax, I want to type `#help <command>` to see detailed usage for just that one command so that I do not need to scan the full help listing.

**Why this priority**: This is a convenience enhancement for returning users. The full #help output already provides the information, but targeted help reduces friction for power users.

**Independent Test**: Can be tested by typing `#help theme` and verifying the output shows only the #theme command's description, full syntax, valid parameters, and a usage example — without listing other commands.

**Acceptance Scenarios**:

1. **Given** a user types `#help theme`, **When** the command is executed, **Then** the system displays detailed information about the #theme command only, including its description, syntax, valid parameter values, and a usage example.
2. **Given** a user types `#help nonexistent`, **When** the command is executed, **Then** the system indicates the command was not found and suggests typing `#help` for the full list.
3. **Given** a user types `#help` with no argument, **When** the command is executed, **Then** the system displays the full categorized command listing (same as User Story 1).

---

### Edge Cases

- What happens when a command is registered without a category? It should appear under a "General" or "Other" default category in the #help output.
- What happens when the user types `#help #theme` (with the hash prefix on the argument)? The system should strip the leading `#` from the argument and still show help for the `theme` command.
- What happens when the user types multiple spaces between `#help` and an argument (e.g., `#help   theme`)? The system should normalize whitespace and handle this correctly (current parsing already normalizes whitespace).
- How does the system handle very long or unusual command arguments in error messages? Error messages should truncate or sanitize displayed user input to prevent layout issues.
- What happens if there are no commands registered (e.g., during testing teardown)? The #help output should display a message indicating no commands are available.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `#help` command that returns a complete list of all registered # commands, organized into named categories (e.g., General, Settings, Workflow).
- **FR-002**: System MUST display each command in the #help output with: the command name, a concise one-line description, and the usage syntax with required parameters shown as `<param>` and optional parameters shown as `[param]`.
- **FR-003**: System MUST support a `#help <command>` variant that displays detailed information for a single specified command, including its description, full syntax, valid parameter values, and an example.
- **FR-004**: System MUST show context-sensitive usage hints when a # command is invoked with missing required arguments, displaying the correct syntax and listing valid parameter values for that command.
- **FR-005**: System MUST show context-sensitive error messages when a # command is invoked with an invalid argument value, indicating which value was rejected and what values are accepted.
- **FR-006**: System MUST suggest the closest matching command name(s) when a user types an unrecognized command that is similar to a registered command (e.g., "Did you mean #help?" when user types `#hep`).
- **FR-007**: System MUST ensure all # command responses (success, error, informational) follow a consistent structural format so users can predict where to find key information.
- **FR-008**: System MUST ensure all command responses remain readable without horizontal scrolling on narrow viewports (320px minimum width).
- **FR-009**: System MUST NOT rely solely on color or emoji to convey meaning in command responses; all critical information must be communicated through text.
- **FR-010**: System MUST assign every registered command a category. Commands without an explicit category default to "General".
- **FR-011**: System MUST dynamically generate the #help output from the command registry so that newly registered commands automatically appear without changes to the help handler.
- **FR-012**: System SHOULD support the bare word `help` (without `#`) as an alias for `#help`, consistent with current behavior.

### Key Entities

- **CommandDefinition**: A registered command entry containing name, description, syntax, handler, optional parameter schema, optional passthrough flag, and category. Category is a new attribute that groups commands in the #help output.
- **CommandCategory**: A logical grouping label (e.g., "General", "Settings", "Workflow") used to organize commands in the #help listing. Each category has a display name and sort order.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify the correct command for their task within 10 seconds of reading the #help output (categorized listing reduces scanning time compared to a flat list).
- **SC-002**: 100% of commands that accept required parameters display a specific usage hint (including valid values) when invoked without those parameters — zero silent failures.
- **SC-003**: 100% of commands that accept enumerated parameter values display the valid options when invoked with an invalid value.
- **SC-004**: Users who mistype a command name receive a "Did you mean?" suggestion at least 80% of the time when the typo is within 2 characters of a registered command name.
- **SC-005**: All # command responses render without horizontal scrolling on viewports as narrow as 320px.
- **SC-006**: The #help output automatically includes any newly registered command without requiring changes to the help handler code.

## Assumptions

- The chat interface renders plain text (not Markdown), so formatting will use whitespace, indentation, and line breaks rather than Markdown syntax. This is consistent with the existing help handler comment: "chat messages are rendered without a Markdown parser."
- The existing `CommandDefinition` type will be extended with an optional `category` field. Commands that do not specify a category will default to "General."
- The "Did you mean?" suggestion feature will use a simple string-distance comparison (e.g., Levenshtein distance) to find close matches among registered command names. A threshold of 2 edits or fewer is a reasonable default.
- The shorthand variant `#help <command>` reuses the existing argument parsing in the help handler; the `_args` parameter (currently ignored) will be used to detect single-command help requests.
- The existing test suite (vitest, happy-dom) and test patterns will be extended — not replaced — to cover the new behaviors.
- Current behavior for bare `#` (returning "Type #help to see available commands.") is preserved unchanged.
