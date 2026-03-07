# Feature Specification: Fix #help Command Auto-Repeat Bug & Add Optimistic Message Rendering in Chat UI

**Feature Branch**: `026-chat-help-optimistic-render`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Debug chat. I entered #help once and now it keeps sending it automatically as a reply to the chat agent. Also, when a user sends a chat message, it should be displayed immediately in the chat UI, then the chat agent can 'think' if processing time is needed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Send a Command Without Auto-Repeat (Priority: P1)

A Solune chat user opens the chat popup, types `#help` (or any hash/slash command), and presses send. The command is dispatched once and the chat displays the appropriate help response. When the user types and sends a normal follow-up message, the follow-up is sent on its own — the `#help` command is not re-injected, appended, or replayed in any way. The input field is clean, there is no lingering command text, and the reply context carries no residual command state.

**Why this priority**: This is a critical bug fix. The auto-repeat behavior makes the chat unusable — every subsequent message triggers the command again, creating an infinite loop of unwanted responses. Fixing this is the highest priority because it blocks normal chat functionality.

**Independent Test**: Can be fully tested by sending `#help` in the chat, then sending a follow-up plain-text message and verifying only the plain-text message is dispatched without any command re-injection.

**Acceptance Scenarios**:

1. **Given** the user has an open chat session, **When** they type `#help` and press send, **Then** the command is dispatched exactly once and the appropriate help response is displayed.
2. **Given** the user just sent the `#help` command and received a response, **When** they type a new plain-text message and press send, **Then** only the plain-text message is sent — no `#help` command is included in the outgoing payload.
3. **Given** the user sent `#help` in a previous session and reopens the chat, **When** they type a new message and press send, **Then** no prior command state leaks into the new message.
4. **Given** the user types `#help` and sends it, **When** the command is dispatched, **Then** the input field is fully cleared with no residual command text.
5. **Given** the user sends any hash/slash command (e.g., `#help`, `#status`, `/clear`), **When** the next message is composed, **Then** the reply-to context and message queue contain no reference to the prior command.

---

### User Story 2 — See Sent Messages Instantly (Priority: P1)

A Solune chat user types a message and presses send. The message immediately appears in the conversation thread as a sent message, the input field clears, and the conversation scrolls to show the new message. The user does not wait for any server acknowledgment before seeing their own message in the chat — the experience feels instant and responsive.

**Why this priority**: Optimistic message rendering is essential for a responsive chat experience. Without it, users are left staring at a blank input area wondering whether their message was received, especially when agent processing takes several seconds.

**Independent Test**: Can be fully tested by sending a message and verifying it appears in the conversation thread within 100 milliseconds of pressing send, before any server response arrives.

**Acceptance Scenarios**:

1. **Given** the user has an open chat session, **When** they type a message and press send, **Then** the message appears in the conversation thread immediately (within 100ms) as a visually distinct "sent" message.
2. **Given** the user sends a message, **When** the message appears optimistically, **Then** the input field is cleared and the conversation auto-scrolls to the new message.
3. **Given** the user sends a message that is still pending server confirmation, **When** they look at their message in the thread, **Then** it is visually indistinguishable from a confirmed message (no jarring status indicator during normal flow).
4. **Given** the server confirms the message was received, **When** the confirmation arrives, **Then** the optimistic message is seamlessly reconciled with the server-confirmed message without duplication or layout shift.

---

### User Story 3 — See a Thinking Indicator While the Agent Processes (Priority: P1)

After the user sends a message and it appears in the chat, a visual "thinking" indicator (such as an animated typing bubble or pulsing ellipsis) appears below the user's message. This indicator persists until the agent's response is ready. Once the response arrives, the thinking indicator is replaced by the agent's actual reply without any layout shift or flicker.

**Why this priority**: The thinking indicator closes the feedback loop — the user knows the system received their message and is actively processing. Without it, there is no visual distinction between "processing" and "broken."

**Independent Test**: Can be fully tested by sending a message, observing the thinking indicator appears after the sent message, and verifying it is replaced by the agent's response when processing completes.

**Acceptance Scenarios**:

1. **Given** the user sends a message and it appears in the thread, **When** the agent begins processing, **Then** a thinking indicator appears below the user's message within 200ms.
2. **Given** the thinking indicator is visible, **When** the agent's response is received, **Then** the indicator is replaced by the agent's reply without layout shift, flicker, or duplicate content.
3. **Given** the thinking indicator is visible, **When** the user scrolls up and then scrolls back down, **Then** the thinking indicator is still visible at the bottom of the conversation.
4. **Given** the agent takes more than 5 seconds to respond, **When** the user views the chat, **Then** the thinking indicator continues to animate, providing ongoing feedback that processing is active.

---

### User Story 4 — Handle Failed Messages Gracefully (Priority: P2)

A user sends a message that fails to deliver (due to a network error, server timeout, or other transient failure). Instead of the message silently disappearing, the optimistically rendered message remains in the conversation thread but is visually marked as "failed" (e.g., with a red accent or error icon). A retry option is available so the user can resend without retyping.

**Why this priority**: This is a defensive UX enhancement. While message failures are uncommon, silently dropping messages erodes trust. Providing clear failure indication and a retry path prevents data loss and frustration.

**Independent Test**: Can be fully tested by simulating a network failure during message send, verifying the message is marked as failed, and confirming the retry button resends the message.

**Acceptance Scenarios**:

1. **Given** the user sends a message and the server is unreachable, **When** the send operation fails, **Then** the optimistic message remains in the thread but is visually marked as failed (distinct styling such as red border or error icon).
2. **Given** a message is marked as failed, **When** the user clicks the retry option, **Then** the message is resent and the failed indicator is removed upon successful delivery.
3. **Given** a message is marked as failed, **When** the user sends a new message, **Then** the new message is sent independently — the failed message does not block or interfere with subsequent sends.
4. **Given** a message fails to send, **When** the user views the failed message, **Then** the original message text is preserved and visible — no content is lost.

---

### User Story 5 — Regression Protection for Command State Leaking (Priority: P2)

The development team has automated test coverage that specifically validates command state (such as `#help`) does not leak across message sends. These tests catch any future regressions where command state persists beyond its single-use lifecycle.

**Why this priority**: The auto-repeat bug indicates a systemic issue with state management. Without regression tests, a future code change could easily reintroduce the problem.

**Independent Test**: Can be fully tested by running the automated test suite and verifying all command-state-isolation tests pass.

**Acceptance Scenarios**:

1. **Given** the test suite is executed, **When** a test sends `#help` followed by a normal message, **Then** the test asserts the normal message payload contains no command references.
2. **Given** the test suite is executed, **When** a test sends multiple different commands in sequence, **Then** the test asserts each command is dispatched independently with no cross-contamination.
3. **Given** the test suite is executed, **When** a test checks the input field state after a command is sent, **Then** the test asserts the input field, reply context, and message queue are fully cleared.

---

### Edge Cases

- What happens when the user sends multiple commands in rapid succession (e.g., `#help` then `#status` within 1 second)? Each command is dispatched independently in order; neither is duplicated or lost.
- What happens when the user sends a message containing a command-like string in the middle of normal text (e.g., "I typed #help and it broke")? The message is treated as plain text — commands are only recognized when the entire message matches the command pattern.
- What happens when the thinking indicator is visible and the user sends another message? The pending thinking indicator for the previous message is preserved, the new user message appears below it, and a new thinking indicator appears for the new message.
- What happens when the network connection drops while the thinking indicator is showing? The thinking indicator transitions to an error/timeout state after a reasonable timeout (e.g., 30 seconds), providing the user an option to retry.
- What happens when the user refreshes the browser while a message is in "pending" optimistic state? The pending message is not persisted — only server-confirmed messages appear after refresh. This is acceptable because the message was never confirmed.
- What happens when the chat popup is closed and reopened while a message is being processed? The thinking indicator is restored based on the current processing state — if the agent is still processing, the indicator reappears.

## Requirements *(mandatory)*

### Functional Requirements

#### Command State Management

- **FR-001**: System MUST clear all stored command state (including `#help` and all hash/slash commands) from the input field, reply context, message queue, and any pending-command store immediately after the command is dispatched.
- **FR-002**: System MUST ensure that no command reference persists in any state store, context payload, or message queue after the command has been successfully dispatched.
- **FR-003**: System MUST treat hash/slash commands as one-time actions — they are dispatched once and their state is completely purged, never carried forward to subsequent messages.
- **FR-004**: System MUST reset the chat input field to an empty state after any message (command or plain text) is successfully dispatched.
- **FR-005**: System MUST ensure the reply-to context of any subsequent message contains no reference to a previously dispatched command.

#### Optimistic Message Rendering

- **FR-006**: System MUST append the user's message to the local chat conversation state immediately upon submission, before any server response is received.
- **FR-007**: System MUST assign a unique temporary identifier to each optimistic message to enable reconciliation with the server-confirmed message.
- **FR-008**: System MUST update the optimistic message status from "pending" to "sent" upon server acknowledgment, without creating duplicate messages or causing layout shifts.
- **FR-009**: System MUST auto-scroll the conversation to the newly appended optimistic message so it is visible to the user.

#### Thinking Indicator

- **FR-010**: System MUST display a visual thinking indicator (e.g., animated typing bubble or pulsing ellipsis) below the user's last sent message after the optimistic message is rendered and before the agent's response arrives.
- **FR-011**: System MUST remove the thinking indicator and render the agent's response in its place once processing is complete, without layout shift or content flicker.
- **FR-012**: System MUST continue animating the thinking indicator for the full duration of agent processing, regardless of processing time.

#### Failure Handling

- **FR-013**: System SHOULD visually mark an optimistic message as "failed" if the send operation encounters an error, displaying a distinct visual treatment (e.g., error icon or red accent).
- **FR-014**: System SHOULD provide a retry action on failed messages that resends the original message content without requiring the user to retype it.
- **FR-015**: System MUST NOT silently discard a failed message — the user must be informed of the failure.

#### Regression Protection

- **FR-016**: System SHOULD include automated tests that verify command state (e.g., `#help`) does not leak into subsequent messages after dispatch.
- **FR-017**: System SHOULD include automated tests that verify the input field, reply context, and message queue are fully cleared after command dispatch.

### Key Entities

- **Chat Message**: A message in the conversation thread. Has content (text), a sender (user or agent), a status (pending, sent, failed), and optionally a temporary ID for optimistic rendering. Commands are a subtype that carry no persistent state beyond dispatch.
- **Command**: A special message prefixed with `#` or `/` (e.g., `#help`, `#status`, `/clear`). Dispatched as a one-time action with no state retention after execution.
- **Thinking Indicator**: A transient UI element displayed while the agent processes a request. Occupies the position where the agent's response will appear. Removed when the response arrives.
- **Reply Context**: Metadata attached to an outgoing message that references prior conversation context. Must be scrubbed of any command references after command dispatch.
- **Message Queue**: The internal queue of messages pending dispatch. Must not retain command entries after they have been sent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After sending `#help` (or any command), 100% of subsequent messages are dispatched without any command re-injection — zero occurrences of auto-repeat.
- **SC-002**: User-sent messages appear in the conversation thread within 100 milliseconds of pressing send, before any server response.
- **SC-003**: The thinking indicator appears within 200 milliseconds of the optimistic message rendering and persists until the agent response arrives.
- **SC-004**: Agent responses replace the thinking indicator without visible layout shift (zero pixels of content jumping).
- **SC-005**: Failed messages display a visible error state and retry option within 2 seconds of the failure occurring.
- **SC-006**: 100% of automated regression tests for command state isolation pass on every build.
- **SC-007**: The chat input field is empty and contains no residual command text within 50 milliseconds of any message dispatch.
- **SC-008**: Users can send 10 consecutive messages (mix of commands and plain text) without any state leakage between them.

## Assumptions

- The existing chat backend API and agent processing pipeline remain unchanged; this feature addresses frontend chat state management and UI rendering only.
- The chat popup is already globally accessible from all pages (per the Solune UI redesign). This feature enhances its internal behavior.
- Hash/slash commands (e.g., `#help`, `#status`, `/clear`) are recognized by a single prefix character (`#` or `/`) at the start of the message, matching the existing command parsing behavior.
- The chat state is managed on the frontend (local state or state manager); no backend changes are required to fix the command replay bug.
- Optimistic message rendering uses local state only — pending messages are not persisted to local storage or the server until confirmed.
- The thinking indicator is a purely visual element with no backend state dependency.

## Scope Exclusions

- Backend API changes or new endpoints
- Changes to agent processing logic or response generation
- Modifications to non-chat UI components (sidebar, board, pipeline, etc.)
- Offline message queuing or sync (beyond basic retry on failure)
- Message editing or deletion after send
- Rich text formatting or media attachments in chat messages
- Changes to the command set itself (no new commands are added)

## Decisions

- **Optimistic rendering over wait-for-confirmation**: Displaying messages immediately provides a responsive experience aligned with modern chat UX expectations. The tradeoff of showing unconfirmed messages is mitigated by failure indicators and retry.
- **Temporary ID for reconciliation**: Using a client-generated temporary ID to match optimistic messages with server-confirmed messages avoids duplication without requiring the server to echo the client's message back.
- **Commands as stateless one-time actions**: Commands are treated as fire-and-forget — they are dispatched and their state is immediately purged. This is the simplest model that prevents replay and aligns with user expectations.
- **Thinking indicator replaces in-place**: The thinking indicator occupies the exact space where the agent's response will render, preventing layout shift when the response arrives.
- **Failed messages remain visible**: Rather than removing failed messages (which could confuse the user), they remain in the thread with clear error styling and a retry path.
