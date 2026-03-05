# Feature Specification: Chat Message History Navigation with Up Arrow Key

**Feature Branch**: `018-chat-history-navigation`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Update app chat experience with useful chat features, like saved chat history - if the user hits the up arrow button, it should step through previously sent messages so the user can easily send the same messages without retyping."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recall Previous Messages with Up Arrow (Priority: P1)

As a chat user, I want to press the up arrow key while focused in the chat input field to cycle backwards through my previously sent messages (most recent first), so that I can quickly recall a past message without retyping it.

**Why this priority**: This is the core value of the feature. Without the ability to recall previous messages via the up arrow key, no other history navigation functionality is meaningful.

**Independent Test**: Can be fully tested by sending 3+ messages, then pressing the up arrow key repeatedly and verifying the input field is populated with each previous message in reverse chronological order.

**Acceptance Scenarios**:

1. **Given** a user has sent at least one message and the chat input field is focused and empty, **When** the user presses the up arrow key, **Then** the input field is populated with the most recently sent message.
2. **Given** a user is viewing a recalled message in the input field, **When** the user presses the up arrow key again, **Then** the input field is populated with the next older message in history.
3. **Given** a user has navigated to the oldest message in history, **When** the user presses the up arrow key again, **Then** the input field remains on the oldest message (no wrap-around).
4. **Given** a user has no previously sent messages, **When** the user presses the up arrow key, **Then** nothing happens and the input field remains unchanged.
5. **Given** a user recalls a historical message and sends it, **When** the message is sent, **Then** the sent message is added as a new entry at the end of the history list, and the input field is cleared.

---

### User Story 2 - Navigate Forward with Down Arrow and Restore Draft (Priority: P1)

As a chat user navigating through my message history, I want to press the down arrow key to step forward toward more recent messages and restore any draft I was typing before I started navigating, so that I don't lose my in-progress message.

**Why this priority**: Down arrow navigation and draft preservation are essential complements to up arrow navigation. Without them, users risk losing their in-progress message when they accidentally press up arrow, making the core feature frustrating rather than helpful.

**Independent Test**: Can be fully tested by typing a draft message, pressing up arrow to enter history navigation, then pressing down arrow until the draft is restored in the input field.

**Acceptance Scenarios**:

1. **Given** a user has typed a partial message (draft) and then pressed the up arrow to enter history navigation, **When** the user presses the down arrow key past the most recent message, **Then** the input field is restored to the original draft text.
2. **Given** a user is viewing a recalled message in the input field, **When** the user presses the down arrow key, **Then** the input field is populated with the next more recent message in history.
3. **Given** the user has not entered history navigation mode, **When** the user presses the down arrow key in the input field, **Then** nothing happens (default behavior is preserved).
4. **Given** a user's input field was empty before entering history navigation, **When** the user presses down arrow past the most recent message, **Then** the input field is restored to empty.

---

### User Story 3 - Persist Chat History Across Sessions (Priority: P2)

As a chat user, I want my sent message history to be saved and available even after I refresh the page or close and reopen the browser, so that I can recall past messages across sessions.

**Why this priority**: Session persistence elevates the feature from a convenience within a single session to a durable productivity tool. However, the core up/down navigation delivers value even without persistence.

**Independent Test**: Can be fully tested by sending several messages, refreshing the page, then pressing the up arrow key and verifying that previously sent messages are still available.

**Acceptance Scenarios**:

1. **Given** a user has sent messages in a previous session, **When** the user returns to the chat page in a new session (page refresh or new browser tab), **Then** pressing the up arrow key recalls messages from the previous session.
2. **Given** the stored history exceeds 100 messages, **When** a new message is sent, **Then** the oldest message is discarded to maintain a maximum of 100 stored messages.
3. **Given** the user clears their browser storage, **When** the user returns to the chat, **Then** the history is empty and up arrow navigation has no effect.

---

### User Story 4 - Cursor Positioning on Recalled Messages (Priority: P2)

As a chat user who has recalled a historical message, I want the text cursor to be placed at the end of the recalled message text, so that I can immediately begin editing or appending to the message.

**Why this priority**: Correct cursor positioning is a polish detail that significantly impacts usability. Without it, users must manually click to reposition the cursor every time they recall a message, adding friction.

**Independent Test**: Can be fully tested by pressing the up arrow to recall a message and verifying the cursor (caret) is positioned at the very end of the text in the input field.

**Acceptance Scenarios**:

1. **Given** a user presses the up arrow key and a historical message is loaded into the input field, **When** the message appears, **Then** the text cursor is positioned at the end of the message text.
2. **Given** a user navigates through multiple history entries using up/down arrows, **When** each message is loaded, **Then** the cursor is repositioned to the end of the newly loaded message each time.

---

### User Story 5 - Visual Feedback During History Navigation (Priority: P2)

As a chat user navigating through my message history, I want a subtle visual indicator on the chat input field when I am in history-navigation mode, so that I can clearly distinguish between typing a new message and browsing recalled messages.

**Why this priority**: Visual feedback prevents user confusion — without it, users may not realize they are browsing history rather than composing a new message, leading to accidental sends of old messages or unexpected input field content.

**Independent Test**: Can be fully tested by pressing the up arrow to enter history navigation mode and verifying a visual indicator (e.g., subtle highlight or border change) appears on the input field, then pressing down past the most recent message to exit history mode and verifying the indicator disappears.

**Acceptance Scenarios**:

1. **Given** a user presses the up arrow key and enters history-navigation mode, **When** a historical message is loaded into the input field, **Then** a subtle visual indicator (e.g., highlight, border change, or icon) is displayed on or near the input field.
2. **Given** a user is in history-navigation mode and presses down arrow past the most recent message (exiting history mode), **When** the draft is restored, **Then** the visual indicator is removed.
3. **Given** a user is in history-navigation mode and sends a recalled message, **When** the message is sent and the input field is cleared, **Then** the visual indicator is removed.

---

### User Story 6 - Mobile/Touch-Friendly History Access (Priority: P3)

As a mobile or touch-device user, I want an alternative way to access my chat message history (such as a history button), so that I can recall past messages even without a physical keyboard with arrow keys.

**Why this priority**: This extends the feature to mobile and touch-only users. Desktop keyboard users already have full functionality, so this is an accessibility enhancement that broadens the audience.

**Independent Test**: Can be fully tested on a touch device by tapping a history button (or using a defined gesture) and verifying that past messages can be browsed and selected for insertion into the input field.

**Acceptance Scenarios**:

1. **Given** a user is on a mobile or touch-only device, **When** the chat input is visible, **Then** an accessible alternative (e.g., a history button) is available near the input field.
2. **Given** a user taps the history access control, **When** the history list is displayed, **Then** the user can browse and select a past message to populate the input field.
3. **Given** no messages have been sent yet, **When** the user attempts to access history via the alternative control, **Then** a helpful empty-state message is shown indicating no history is available.

---

### Edge Cases

- What happens when the user presses up arrow in a multi-line input and the cursor is NOT on the first line? The system must allow the default cursor movement (moving the cursor up a line) instead of triggering history navigation.
- What happens when the user modifies a recalled message and then navigates away with up/down arrow? The modification is discarded; the original history entry is not changed. If the user sends the modified message, it is added as a new entry.
- What happens when the user pastes a very long message that exceeds typical input length? The message is stored in history as-is (up to the history cap of 100 entries).
- What happens when storage is full or unavailable (e.g., private browsing mode with storage restrictions)? The system gracefully degrades — history navigation still works for the current session but does not persist.
- What happens when two browser tabs are open to the same chat? Each tab loads history on startup; new messages sent in one tab are not automatically reflected in the other tab's in-memory history until the next page load.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST capture and store each message sent by the user in an ordered chat history list, appended in chronological order.
- **FR-002**: System MUST respond to the up arrow key press inside the focused chat input field by replacing the current input content with the most recently sent message, and each subsequent up arrow press MUST step to the next older message in history.
- **FR-003**: System MUST respond to the down arrow key press while in history-navigation mode by stepping forward toward more recent messages, and upon reaching the end of history MUST restore any unsaved draft the user had typed before navigation began.
- **FR-004**: System MUST persist chat message history across page refreshes and sessions using client-side storage.
- **FR-005**: System MUST position the text cursor at the end of the input field content when a historical message is recalled via arrow key navigation.
- **FR-006**: System SHOULD cap the stored history at a maximum of 100 most recent messages, discarding the oldest entries when the limit is exceeded.
- **FR-007**: System MUST only intercept up/down arrow keys for history navigation when the chat input field is focused.
- **FR-008**: System MUST NOT trigger history navigation via the up arrow key when the cursor is not on the first line of a multi-line input; default cursor movement must be preserved in that case.
- **FR-009**: System SHOULD display a subtle visual indicator on the chat input field when the user is in history-navigation mode, and remove the indicator when the user exits history-navigation mode (by navigating past the most recent message or sending a message).
- **FR-010**: System SHOULD provide an accessible alternative to keyboard-based history navigation (e.g., a history button or touch-friendly control) for users on mobile or touch-only devices.
- **FR-011**: System MUST treat each sent message as a new, separate history entry, even if the content is identical to a previously sent message.
- **FR-012**: System MUST NOT modify existing history entries when the user edits a recalled message. The edited version is only added to history if it is sent.
- **FR-013**: System MUST gracefully handle scenarios where client-side storage is unavailable or full by providing in-session history navigation without persistence.

### Key Entities

- **Message History**: An ordered list of previously sent messages, stored in reverse chronological order for navigation. Key attributes: message text, chronological position. Maximum size: 100 entries.
- **Draft Buffer**: A temporary store for any in-progress (unsent) text the user had typed before initiating history navigation. Allows restoration when the user navigates back past the most recent message.
- **History Index**: A pointer tracking the user's current position in the message history during navigation. When not navigating, the pointer is in a neutral state (no history selected).

## Assumptions

- The chat input field is a single, identifiable text input element where users type and send messages.
- "Sending a message" is a clearly defined user action (e.g., pressing Enter or clicking a Send button) that already exists in the application.
- The application has a single chat context per page (history is not scoped per conversation or per user). If multi-conversation support is needed in the future, history scoping can be added as an enhancement.
- Standard web keyboard events are available in the runtime environment (the chat is a web-based application).
- Client-side storage (such as localStorage) is the appropriate persistence mechanism for this feature; server-side storage of input history is out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can recall any of their last 100 sent messages in under 2 seconds using repeated up arrow key presses.
- **SC-002**: 95% of users who begin history navigation (press up arrow) successfully find and resend or edit a past message without retyping it manually.
- **SC-003**: Users who begin typing a draft and accidentally enter history navigation can restore their draft with a single down arrow press 100% of the time.
- **SC-004**: Chat message history survives page refresh and is available in the next session with no user action required.
- **SC-005**: The history navigation feature does not interfere with normal text editing — users can move the cursor within a multi-line message using arrow keys without unintended history navigation.
- **SC-006**: On mobile or touch devices, users can access their message history through an alternative control without requiring a physical keyboard.
