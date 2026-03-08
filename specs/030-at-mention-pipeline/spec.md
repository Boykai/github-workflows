# Feature Specification: @ Mention in Chat to Select Agent Pipeline Configuration

**Feature Branch**: `030-at-mention-pipeline`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Support @ Mention in Chat to Select Agent Pipeline Configuration for GitHub Issue Creation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — @ Mention Autocomplete for Pipeline Selection (Priority: P1)

As a user composing a chat input description, I want to type "@" in the chat input field to trigger an autocomplete dropdown listing all saved Agent Pipeline configurations by name, so that I can quickly find and select the pipeline I want to use for GitHub Issue creation without memorizing exact names.

**Why this priority**: This is the foundational interaction for the entire feature. Without the ability to discover and select a pipeline via @mention, no other functionality (validation, visual indicators, issue creation) can work. This delivers the core value of pipeline-aware issue creation.

**Independent Test**: Can be fully tested by typing "@" in the chat input, verifying the autocomplete dropdown appears with pipeline names, typing additional characters to filter results, and selecting a pipeline via keyboard or mouse. Delivers immediate value by enabling users to reference pipelines directly in chat.

**Acceptance Scenarios**:

1. **Given** the user is focused on the chat input field and saved Agent Pipeline configurations exist, **When** they type "@", **Then** an autocomplete dropdown appears listing all saved Agent Pipeline configurations by name.
2. **Given** the autocomplete dropdown is visible, **When** the user types additional characters after "@", **Then** the dropdown filters in real-time to show only pipelines whose names match the typed text (case-insensitive).
3. **Given** the autocomplete dropdown is visible with filtered results, **When** the user navigates using arrow keys and presses Enter, **Then** the selected pipeline is inserted into the chat input as a visually distinct @mention token (chip/tag).
4. **Given** the autocomplete dropdown is visible, **When** the user clicks on a pipeline name, **Then** the selected pipeline is inserted into the chat input as a visually distinct @mention token.
5. **Given** the user has typed "@" and the autocomplete is visible, **When** they press Escape or click outside the dropdown, **Then** the dropdown closes and the "@" character remains as plain text.
6. **Given** there are no saved Agent Pipeline configurations, **When** the user types "@", **Then** the dropdown appears with an empty state message indicating no pipelines are available.

---

### User Story 2 — Pipeline-Aware GitHub Issue Creation (Priority: P1)

As a user submitting a chat input that contains an @mentioned pipeline, I want the system to automatically use the referenced Agent Pipeline configuration when creating GitHub Issues from my chat input, so that the correct AI agent workflow handles the issue creation with the settings I intended.

**Why this priority**: This is the core value delivery — connecting the @mention selection to the actual issue creation workflow. Without this, the @mention is purely cosmetic and provides no functional benefit.

**Independent Test**: Can be tested by composing a chat message with an @mentioned pipeline, submitting it, and verifying that the GitHub Issues created use the referenced pipeline's configuration. Delivers the primary business value of targeted pipeline-driven issue creation.

**Acceptance Scenarios**:

1. **Given** the user has composed a chat input containing a valid @mentioned pipeline, **When** they submit the chat input, **Then** the system uses the Agent Pipeline configuration associated with the @mentioned pipeline for GitHub Issue creation.
2. **Given** the user submits a chat input with a valid @mention, **When** the issue creation completes successfully, **Then** the created issues reflect the settings defined in the referenced pipeline configuration.
3. **Given** the user submits a chat input containing no @mention, **When** the submission is processed, **Then** the system uses the default pipeline configuration (current behavior is preserved).
4. **Given** the user submits a chat input with an @mention referencing a pipeline that has been deleted since it was mentioned, **When** the submission is processed, **Then** the system displays a clear error message indicating the pipeline cannot be found and prevents issue creation, allowing the user to correct the reference.

---

### User Story 3 — Active Pipeline Visual Indicator (Priority: P2)

As a user who has selected a pipeline via @mention, I want to see a clear visual indicator near the submit action showing which pipeline configuration is active, so that I can confirm my selection before submitting.

**Why this priority**: Visual confirmation reduces user errors and builds confidence in the pipeline selection. While not strictly required for functionality, it significantly improves the user experience and prevents accidental submissions with the wrong pipeline.

**Independent Test**: Can be tested by inserting an @mention token into the chat input and verifying a contextual indicator (badge or label) appears near the submit button displaying the active pipeline name. The indicator should update or disappear when the @mention is removed.

**Acceptance Scenarios**:

1. **Given** the user has inserted a valid @mention token in the chat input, **When** they view the area near the submit button, **Then** a contextual indicator displays the text "Using pipeline: [pipeline name]" (or similar).
2. **Given** the user removes the @mention token from the chat input, **When** the input is updated, **Then** the active pipeline indicator disappears.
3. **Given** the user replaces one @mention with a different pipeline, **When** the replacement is complete, **Then** the indicator updates to reflect the newly selected pipeline name.

---

### User Story 4 — Invalid Pipeline Warning State (Priority: P2)

As a user who has typed an @mention that does not match any existing pipeline, I want to see a warning state on the mention, so that I know the reference is invalid before I attempt to submit.

**Why this priority**: Proactive validation prevents wasted time from failed submissions and provides a smoother user experience. It is an important usability enhancement but not blocking for core functionality.

**Independent Test**: Can be tested by manually typing "@nonexistent-pipeline" in the chat input (without selecting from the dropdown) and verifying a warning visual state appears on the text, and that attempting to submit surfaces a validation error.

**Acceptance Scenarios**:

1. **Given** the user has typed an @mention that does not correspond to any saved pipeline, **When** the input loses focus or the user finishes typing, **Then** the unresolved @mention text renders with a warning visual state (e.g., different color, underline, or icon).
2. **Given** the user attempts to submit a chat input containing an unresolved @mention, **When** the submission is triggered, **Then** the system prevents submission and displays a clear error message indicating the pipeline name is not recognized.
3. **Given** an @mention token references a pipeline that existed at selection time but was subsequently deleted, **When** the user views the chat input, **Then** the token updates to show a warning state indicating the pipeline is no longer available.

---

### User Story 5 — Multiple @Mention Handling (Priority: P3)

As a user who has accidentally included multiple @mentions in a single chat input, I want the system to handle this gracefully, so that I am not confused about which pipeline will be used.

**Why this priority**: Edge case handling that improves robustness. Most users will only use one @mention, but handling multiples prevents confusing behavior.

**Independent Test**: Can be tested by inserting two different @mention tokens into the chat input and verifying the system either uses the last valid mention with a clear indicator or surfaces a validation message asking the user to keep only one.

**Acceptance Scenarios**:

1. **Given** the user has inserted multiple valid @mention tokens in the chat input, **When** the system evaluates the input, **Then** it uses the last valid @mention as the active pipeline and displays a notification informing the user that only one pipeline can be active per submission.
2. **Given** the user has multiple @mentions and one is invalid, **When** the system evaluates the input, **Then** the invalid mention shows a warning state and the last valid mention is used as the active pipeline.

---

### Edge Cases

- What happens when the user types "@" at the very beginning of the chat input? The autocomplete should trigger normally regardless of cursor position within the input field.
- What happens when the user types "@" inside a word (e.g., "email@pipeline")? The autocomplete should only trigger when "@" is preceded by a space, newline, or is at the start of the input to avoid false triggers on email addresses or other patterns.
- How does the system handle rapid typing after "@" with many saved pipelines? The autocomplete filtering should be responsive with debounced lookups to avoid excessive processing on rapid keystrokes.
- What happens if the pipeline list is very long (50+ pipelines)? The autocomplete dropdown should be scrollable and show a limited number of results at a time (e.g., 10 visible items) with the ability to scroll for more.
- What happens when the user pastes text containing "@pipeline-name" from an external source? The system should attempt to resolve the pasted @mention against saved pipelines and render it as a token if valid, or as plain warning text if unrecognized.
- What happens when the user deletes part of an @mention token (e.g., backspaces into it)? The entire token should be removed as a single unit rather than allowing partial deletion.
- How does the system behave when there is no network connectivity and the user types "@"? The dropdown should show a helpful error state (e.g., "Unable to load pipelines") rather than silently failing.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect when the user types "@" in the chat input field (preceded by a space, newline, or at the start of the input) and display an autocomplete dropdown listing all saved Agent Pipeline configurations.
- **FR-002**: System MUST filter the autocomplete dropdown in real-time as the user types characters after "@", matching against pipeline names case-insensitively.
- **FR-003**: System MUST allow the user to select a pipeline from the autocomplete dropdown via keyboard navigation (arrow keys + Enter) or mouse click.
- **FR-004**: System MUST insert the selected pipeline as a visually distinct @mention token (chip or styled tag) inline in the chat input, clearly differentiating it from plain text.
- **FR-005**: System MUST store the pipeline's unique identifier internally within the @mention token (not just the display name) to guard against pipeline rename edge cases.
- **FR-006**: System MUST use the Agent Pipeline configuration associated with the @mentioned pipeline as the active configuration when the user submits the chat input for GitHub Issue creation.
- **FR-007**: System MUST support only one active @mention per chat submission; if multiple @mentions are present, the system MUST use the last valid one and notify the user.
- **FR-008**: System MUST validate that the @mentioned pipeline name corresponds to an existing saved Agent Pipeline configuration at submission time and MUST prevent issue creation with a clear error message if the pipeline cannot be resolved.
- **FR-009**: System MUST display a contextual indicator near the submit action (e.g., a badge or label reading "Using pipeline: [name]") when a valid @mention is present in the chat input.
- **FR-010**: System MUST render unresolved or invalid @mentions with a warning visual state (e.g., different color or underline) to alert the user before submission.
- **FR-011**: System MUST remove the @mention token as a complete unit when the user presses backspace/delete into it (no partial token deletion).
- **FR-012**: System MUST close the autocomplete dropdown when the user presses Escape or clicks outside of it.
- **FR-013**: System MUST preserve existing chat submission behavior (using the default or currently selected pipeline) when no @mention is present in the input.
- **FR-014**: System SHOULD show each pipeline's name and optionally a short description or last-modified date in the autocomplete dropdown to help distinguish configurations.
- **FR-015**: System SHOULD limit the visible autocomplete dropdown to a scrollable list when many pipelines exist, showing a reasonable number of results at a time.
- **FR-016**: System SHOULD handle the case where a previously valid pipeline is deleted or renamed after being mentioned, surfacing a recoverable warning with guidance to re-select a valid pipeline.
- **FR-017**: System SHOULD debounce autocomplete lookups to avoid excessive processing on rapid keystrokes.

### Key Entities

- **Agent Pipeline Configuration**: A saved configuration that defines an AI agent workflow for GitHub Issue creation. Each configuration has a unique identifier, a display name, an optional description, and associated pipeline settings. This is the entity referenced by @mentions.
- **@Mention Token**: An inline, interactive element within the chat input that represents a reference to a specific Agent Pipeline Configuration. Stores the pipeline's unique identifier internally and renders the pipeline's display name as a styled chip/tag. Can be in a valid (resolved) or invalid (unresolved/warning) state.
- **Chat Input**: The text composition area where users type their descriptions for GitHub Issue creation. Supports both plain text and @mention tokens as part of its content.
- **Autocomplete Dropdown**: A floating UI element triggered by typing "@" that displays a filterable list of available Agent Pipeline Configurations for selection.

## Assumptions

- Saved Agent Pipeline configurations already exist as a feature in the system and can be queried/listed.
- Each Agent Pipeline configuration has a unique identifier and a human-readable display name.
- The chat input field already exists and is used for composing descriptions that drive GitHub Issue creation.
- The GitHub Issue creation workflow already accepts a pipeline configuration parameter to determine which agent workflow is used.
- Standard session-based authentication is in place; no additional authentication is needed to query pipeline configurations.
- The autocomplete dropdown follows existing UI patterns in the application (if any typeahead/mention components exist).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can type "@", see the autocomplete dropdown, select a pipeline, and have the @mention token inserted in under 3 seconds from the first keystroke.
- **SC-002**: The autocomplete dropdown filters results within 300 milliseconds of each keystroke, providing a responsive real-time search experience.
- **SC-003**: 100% of chat submissions with a valid @mention use the referenced pipeline configuration for issue creation (zero misrouted submissions).
- **SC-004**: 100% of submissions with an invalid or deleted @mention are blocked with a clear error message before any issues are created.
- **SC-005**: 90% of users can successfully select a pipeline via @mention and submit a chat input on their first attempt without external guidance.
- **SC-006**: The active pipeline indicator correctly reflects the selected pipeline 100% of the time when a valid @mention is present, and disappears when no @mention is present.
- **SC-007**: The system gracefully handles up to 100 saved pipeline configurations in the autocomplete dropdown without noticeable performance degradation.
