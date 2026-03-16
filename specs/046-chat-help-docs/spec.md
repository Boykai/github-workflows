# Feature Specification: Update Chat Help & Help Page for Comprehensive Chat Commands & Features

**Feature Branch**: `046-chat-help-docs`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Update Chat Help & Help Page for Comprehensive Chat Commands & Features"

## User Scenarios & Testing *(mandatory)*

<!--
  User stories are prioritized as user journeys ordered by importance.
  Each story is independently testable and delivers standalone value.
-->

### User Story 1 — Expanded /help Chat Command Output (Priority: P1)

A user types `/help` (or `help` without the slash) in the chat input and sees not only the list of six slash commands but also a "Chat Features" section describing @pipeline mentions, file attachments, voice input, and AI Enhance, followed by a "Tips" section with guidance on command autocomplete, the `help` alias, message history navigation, and a pointer to the full Help page. This gives users immediate, in-context awareness of all chat capabilities without leaving the conversation.

**Why this priority**: The `/help` command is the primary in-app discovery mechanism. Most users will never visit the Help page — they type `/help` when stuck. Expanding this output is the single highest-impact change because it reaches every user at the moment they need guidance.

**Independent Test**: Can be fully tested by invoking the `/help` command handler and verifying the returned message string contains the expected "Chat Features" block (with @pipeline mentions, file attachments, voice input, AI Enhance lines) and the "Tips" block (with autocomplete hint, help alias, history navigation, Help page link).

**Acceptance Scenarios**:

1. **Given** a user is in the chat interface, **When** they type `/help` and submit, **Then** the response includes the standard six-command list followed by a "Chat Features" section with four feature descriptions and a "Tips" section with four tips.
2. **Given** a user types `help` (no slash) in the chat, **When** they submit, **Then** the response is identical to the `/help` output, including the Chat Features and Tips sections.
3. **Given** the `/help` output is rendered in the chat window, **When** the user reads it, **Then** all text is plain text (no Markdown syntax artifacts such as `**` or `#` visible in the message).
4. **Given** a new slash command is registered in the future, **When** the user types `/help`, **Then** the command list dynamically includes the new command while the Chat Features and Tips sections remain unchanged.

---

### User Story 2 — New Chat Features Section on the Help Page (Priority: P2)

A user visits the Help page and sees a new "Chat Features" section (positioned between the FAQ section and the Feature Guides section) containing seven feature cards: @Pipeline Mentions, File Attachments, Voice Input, AI Enhance, Task Proposals, Message History, and Keyboard Shortcuts. Each card has a title, icon, and descriptive text explaining the feature. This provides a comprehensive reference for all non-command chat capabilities.

**Why this priority**: The Help page is the long-form reference surface. After `/help` gives users a quick overview, the Help page provides the depth needed to understand each feature fully. Adding the Chat Features section fills the largest documentation gap identified in the codebase audit.

**Independent Test**: Can be fully tested by rendering the Help page and verifying that seven feature cards appear in the Chat Features section, each with the correct title and description content.

**Acceptance Scenarios**:

1. **Given** a user navigates to the Help page, **When** the page loads, **Then** a "Chat Features" section is visible between the FAQ section and the Feature Guides section.
2. **Given** the Chat Features section is rendered, **When** the user views it, **Then** it contains exactly seven feature cards: @Pipeline Mentions, File Attachments, Voice Input, AI Enhance, Task Proposals, Message History, and Keyboard Shortcuts.
3. **Given** the @Pipeline Mentions card is displayed, **When** the user reads it, **Then** it describes typing `@` followed by a pipeline name, the autocomplete dropdown, inline token badges, and validation on submit.
4. **Given** the File Attachments card is displayed, **When** the user reads it, **Then** it lists supported file formats, the 10 MB per-file limit, the toolbar attachment button, and preview chips with upload status.
5. **Given** the Voice Input card is displayed, **When** the user reads it, **Then** it mentions the microphone toolbar button, Chrome/Edge browser recommendation, live interim transcription, and auto-stop on speech end.
6. **Given** the AI Enhance card is displayed, **When** the user reads it, **Then** it describes the toolbar toggle, that it enriches messages before sending, defaults to ON, and persists across sessions.
7. **Given** the Task Proposals card is displayed, **When** the user reads it, **Then** it explains that AI proposes structured tasks from chat, users can confirm to create issues, and status change proposals are supported.
8. **Given** the Message History card is displayed, **When** the user reads it, **Then** it describes Arrow Up/Down navigation, draft preservation, and the history popover for quick recall.
9. **Given** the Keyboard Shortcuts card is displayed, **When** the user reads it, **Then** it lists Enter to send, Escape to dismiss autocomplete, Tab to select, and `/` and `@` as trigger keys.

---

### User Story 3 — Enriched Slash Commands Table on the Help Page (Priority: P3)

A user views the Slash Commands section on the Help page and sees an additional "Options" column in the commands table showing the valid parameter values for each command (e.g., light, dark, system for `/theme`). Below the table, a footer note reminds users they can type `/` in chat to autocomplete commands and that `help` without the slash also works. This eliminates guesswork about valid parameter values.

**Why this priority**: The existing commands table shows syntax but not what options are actually valid. Users must guess or experiment. Adding the Options column and footer note makes the documentation self-sufficient and reduces trial-and-error usage.

**Independent Test**: Can be fully tested by rendering the Help page Slash Commands section and verifying the table has four columns (Name, Syntax, Description, Options) with correct option values for each command, plus a footer note.

**Acceptance Scenarios**:

1. **Given** the Help page Slash Commands table is rendered, **When** the user views it, **Then** the table has four columns: Name, Syntax, Description, and Options.
2. **Given** the `/theme` row is displayed, **When** the user reads the Options column, **Then** it shows: light, dark, system.
3. **Given** the `/language` row is displayed, **When** the user reads the Options column, **Then** it shows: en (English), es (Spanish), fr (French), de (German), ja (Japanese), zh (Chinese).
4. **Given** the `/notifications` row is displayed, **When** the user reads the Options column, **Then** it shows: on, off.
5. **Given** the `/view` row is displayed, **When** the user reads the Options column, **Then** it shows: chat, board, settings.
6. **Given** the `/help` row is displayed, **When** the user reads the Options column, **Then** it shows no options (empty or a dash).
7. **Given** the `/agent` row is displayed, **When** the user reads the Options column, **Then** it shows the parameter format and an admin-only indicator.
8. **Given** the Slash Commands section is fully rendered, **When** the user scrolls below the table, **Then** a footer note reads: "Type `/` in chat to autocomplete commands. You can also type `help` without the slash."

---

### User Story 4 — Corrected FAQ Entries (Priority: P4)

A user browses the FAQ section on the Help page and finds accurate information. The entry about available slash commands no longer references the non-existent `/clear` command, and the entry about file attachments no longer claims drag-and-drop support that does not exist. This eliminates user confusion caused by documentation that contradicts actual application behavior.

**Why this priority**: Inaccurate FAQ content actively misleads users, causing failed attempts and eroding trust. While lower priority than adding new documentation (P1–P3), fixing factual errors is essential for documentation credibility.

**Independent Test**: Can be fully tested by rendering the Help page FAQ section and verifying that the `chat-voice-1` entry does not contain `/clear` and the `chat-voice-2` entry does not contain "drag-and-drop" or "drag and drop".

**Acceptance Scenarios**:

1. **Given** the FAQ entry `chat-voice-1` ("What slash commands are available?") is displayed, **When** the user reads the answer, **Then** it does not reference `/clear` and instead correctly lists `/agent` among the available commands.
2. **Given** the FAQ entry `chat-voice-2` ("Can I attach files to chat messages?") is displayed, **When** the user reads the answer, **Then** it does not mention "drag-and-drop" and instead instructs the user to click the attachment button in the chat toolbar.

---

### User Story 5 — Automated Tests for All Changes (Priority: P5)

A developer runs the test suite and all tests pass, confirming that the expanded `/help` output, the new Chat Features section, the enriched commands table, and the corrected FAQ entries are all verified by automated tests. This ensures changes are protected against regressions.

**Why this priority**: Tests are the safety net for all other user stories. Without them, future changes could silently break the documentation improvements. This is last in priority because it delivers value to developers, not directly to end users, but is mandatory for long-term quality.

**Independent Test**: Can be fully tested by running the help handler unit tests and the Help page component tests and verifying all assertions pass.

**Acceptance Scenarios**:

1. **Given** the help handler test suite runs, **When** the tests execute, **Then** assertions verify the output includes "Chat Features" and "Tips" section content.
2. **Given** the Help page test suite runs, **When** the tests execute, **Then** assertions verify the Chat Features section renders seven cards, the commands table has an Options column, and the FAQ entries contain corrected text.
3. **Given** all source files are type-checked, **When** the type checker runs, **Then** zero type errors are reported.

---

### Edge Cases

- What happens when the command registry is empty (no commands registered)? The `/help` output still shows the Chat Features and Tips sections even with an empty command list.
- What happens when a command has no `parameterSchema` defined? The Options column for that command shows an empty cell or dash, never an error.
- What happens when `parameterSchema` has `labels` defined (e.g., language codes with display names)? The Options column shows the label-enhanced format (e.g., "en (English)") rather than raw values.
- What happens when the Help page is viewed on a narrow mobile screen? The Chat Features card grid reflows to a single-column layout while maintaining readability.
- What happens when a FAQ entry ID is referenced that does not exist in the accordion data? The accordion gracefully renders only the entries that exist without errors.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1 — /help Command Output

- **FR-001**: The `/help` command handler MUST append a "Chat Features" block below the command list containing four lines: @Pipeline Mentions ("Type @ to invoke a pipeline by name"), File Attachments ("Use the attachment button to add files (images, PDF, code, up to 10 MB)"), Voice Input ("Use the microphone button for speech-to-text (Chrome/Edge recommended)"), and AI Enhance ("Toggle AI Enhance in the toolbar for smarter responses").
- **FR-002**: The `/help` command handler MUST append a "Tips" block below the Chat Features block containing four lines: "Type / to browse and autocomplete commands", "You can also type help without the slash", "Use Arrow Up/Down to browse previous messages", and "Visit the Help page for the full guide".
- **FR-003**: All `/help` output MUST be plain text with no Markdown formatting (no `**`, `#`, `*`, or other Markdown syntax).
- **FR-004**: The command list portion of the `/help` output MUST remain dynamically generated from the command registry (not hardcoded).

#### Phase 2 — Help Page Chat Features Section

- **FR-005**: The Help page MUST include a "Chat Features" section positioned between the FAQ section and the Feature Guides section.
- **FR-006**: The Chat Features section MUST contain exactly seven feature cards: @Pipeline Mentions, File Attachments, Voice Input, AI Enhance, Task Proposals, Message History, and Keyboard Shortcuts.
- **FR-007**: Each Chat Features card MUST have a title, an icon, and a description that accurately reflects the current application behavior as documented in the codebase audit.
- **FR-008**: The Chat Features card descriptions MUST match the following content:
  - @Pipeline Mentions: Type `@` followed by a pipeline name to trigger autocomplete; select from dropdown; inline token badges (blue for valid, red for invalid); validated on submit.
  - File Attachments: Supported formats include images (PNG, JPEG, GIF, WebP, SVG), documents (PDF, TXT, MD), and data files (CSV, JSON, YAML, ZIP); 10 MB per-file limit; use the toolbar attachment button; preview chips show filename, size, and upload status.
  - Voice Input: Microphone button in toolbar; Chrome/Edge recommended; interim transcription shown live; auto-stops on speech end; appends transcription to input.
  - AI Enhance: Toolbar toggle with ON/OFF indicator; enriches messages before sending; defaults to ON; persists across sessions.
  - Task Proposals: AI proposes structured tasks with title, description, and pipeline badge; confirm to create; status change proposals show current-to-target flow.
  - Message History: Arrow Up/Down keys to browse previously sent messages; current draft preserved when navigating; history popover for quick recall of recent messages.
  - Keyboard Shortcuts: Enter to send, Escape to dismiss autocomplete, Tab to select highlighted autocomplete option, `/` to trigger command autocomplete, `@` to trigger pipeline mention autocomplete.

#### Phase 3 — Enriched Commands Table

- **FR-009**: The Slash Commands table on the Help page MUST include an "Options" column showing the valid parameter values for each command.
- **FR-010**: The Options column MUST be dynamically driven by each command's `parameterSchema` property from the command registry.
- **FR-011**: For commands with `parameterSchema.type === 'enum'` and `parameterSchema.labels`, the Options column MUST display label-enhanced values (e.g., "en (English)").
- **FR-012**: For commands with `parameterSchema.type === 'enum'` and no labels, the Options column MUST display the raw values joined by commas.
- **FR-013**: For commands with no `parameterSchema`, the Options column MUST display an empty cell or a dash.
- **FR-014**: For the `/agent` command (passthrough), the Options column MUST show the parameter format and an admin-only indicator.
- **FR-015**: A footer note MUST appear below the commands table reading: "Type `/` in chat to autocomplete commands. You can also type `help` without the slash."

#### Phase 4 — FAQ Corrections

- **FR-016**: The FAQ entry `chat-voice-1` answer MUST NOT reference `/clear` and MUST instead correctly reference `/agent` among the available commands.
- **FR-017**: The FAQ entry `chat-voice-2` answer MUST NOT claim "drag-and-drop" file support and MUST instead instruct users to click the attachment button in the chat toolbar.

#### Phase 5 — Tests

- **FR-018**: Unit tests for the help handler MUST verify the output includes the "Chat Features" section content and the "Tips" section content.
- **FR-019**: Component tests for the Help page MUST verify the Chat Features section renders all seven cards.
- **FR-020**: Component tests for the Help page MUST verify the commands table includes an Options column with correct values.
- **FR-021**: Component tests for the Help page MUST verify the corrected FAQ entry text (no `/clear`, no "drag-and-drop").
- **FR-022**: All source files MUST pass type checking with zero errors.

### Key Entities

- **Command Definition**: A registered slash command with name, description, syntax, handler function, and optional parameter schema. The parameter schema specifies the type (enum, string, boolean), valid values, and optional display labels.
- **Chat Feature**: A non-command capability of the chat interface (e.g., @pipeline mentions, file attachments, voice input) that is documented but not invoked via a slash command.
- **FAQ Entry**: A question-and-answer pair displayed in the Help page FAQ accordion, categorized by topic (getting-started, agents-pipelines, chat-voice, settings-integration).
- **Feature Card**: A visual card component used on the Help page to describe a feature, consisting of a title, icon, description, and optional link.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users who type `/help` see a response that covers 100% of the six slash commands plus four chat features and four tips — up from only the six commands today.
- **SC-002**: The Help page Chat Features section displays all seven documented chat capabilities, increasing help page feature coverage from 0% to 100% of non-command features.
- **SC-003**: 100% of slash commands in the Help page table show their valid parameter options, eliminating guesswork for users.
- **SC-004**: Zero FAQ entries reference non-existent commands or unsupported features (currently two inaccuracies: `/clear` and "drag-and-drop").
- **SC-005**: All automated tests pass with zero failures, covering the expanded help output, chat features section, enriched table, and corrected FAQ text.
- **SC-006**: Users can discover all chat capabilities (commands, features, and tips) within 30 seconds by using either the `/help` command or the Help page, without needing to explore the UI by trial and error.
- **SC-007**: All source files pass type checking with zero type errors after changes are applied.

## Assumptions

- The chat interface does not render Markdown — all `/help` output must remain plain text.
- The existing `FeatureGuideCard` component (or a similar card component) can be reused for the Chat Features section cards on the Help page.
- The `parameterSchema` property is already defined on all command registrations that have parameters, and the `labels` property is used for language codes.
- The six slash commands documented in the issue are the complete set — no additional commands exist that are unregistered or hidden.
- The FAQ entry IDs `chat-voice-1` and `chat-voice-2` correspond to the entries documented in the issue and are stable identifiers.
- The Help page section order (Hero → Getting Started → FAQ → Chat Features → Feature Guides → Slash Commands) is the intended layout after changes.
- No new slash commands or chat features need to be created — this feature is documentation-only, describing existing capabilities.
- Mobile responsiveness follows the existing Help page grid patterns (single column on mobile, multi-column on desktop).
