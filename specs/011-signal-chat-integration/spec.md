# Feature Specification: Signal Messaging Integration

**Feature Branch**: `011-signal-chat-integration`  
**Created**: 2026-02-27  
**Status**: Draft  
**Input**: User description: "Add support for a user to connect Signal messaging app for the core app's chat UX"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect Signal Account (Priority: P1)

A user navigates to the app's Settings view and links their Signal account so that chat messages exchanged in the app can also be sent and received through Signal. The user initiates the connection, authenticates with Signal, and sees a confirmation that the link is active.

**Why this priority**: Without a working connection flow, no other Signal functionality is possible. This is the foundational capability that everything else depends on.

**Independent Test**: Can be fully tested by navigating to Settings, initiating Signal linking, completing authentication, and verifying a "Connected" indicator appears. Delivers the core value of establishing the bridge between the app and Signal.

**Acceptance Scenarios**:

1. **Given** a logged-in user with no Signal account linked, **When** they open Settings and select "Connect Signal", **Then** the app displays a QR code that the user scans from their Signal client, and upon successful scan, the UI shows a "Connected" status with their Signal identifier.
2. **Given** a user is in the Signal linking flow, **When** authentication fails or is cancelled, **Then** the UI displays a clear error message and the account remains unlinked.
3. **Given** a user already has a linked Signal account, **When** they open Settings, **Then** they see the current connection status and an option to disconnect.

---

### User Story 2 - Receive App Chat Messages via Signal (Priority: P2)

When the AI assistant or the system sends a chat message inside the app (e.g., a task proposal, status update confirmation, or general reply), the user also receives that message on their linked Signal account so they can stay informed without having the app open.

**Why this priority**: Outbound notifications to Signal are the highest-value use case after connection is established—users can monitor project activity from their phone without switching apps.

**Independent Test**: Can be tested by sending a chat message in the app and verifying the same content arrives as a Signal message on the user's device within the expected delivery window.

**Acceptance Scenarios**:

1. **Given** a user has a linked Signal account and receives an assistant message in the app, **When** the message is delivered, **Then** a corresponding Signal message is sent to the user's linked account within 30 seconds.
2. **Given** a user has a linked Signal account and receives an action-bearing message (task proposal, status change), **When** the message is delivered via Signal, **Then** it includes a text summary of the action with a link back to the app to take action.
3. **Given** a user has disconnected their Signal account, **When** an assistant message is delivered in the app, **Then** no Signal message is sent and no errors appear in the app.

---

### User Story 3 - Send Messages from Signal to App Chat (Priority: P3)

A user sends a text message from Signal to the app's dedicated Signal number/contact, and that message appears as a user message inside the app's chat interface, triggering the same AI-assisted workflow (task creation, status changes, feature requests) as if typed directly in the app.

**Why this priority**: Bidirectional messaging completes the integration, but is more complex and less critical than outbound notifications. Users can still use the web UI to send messages; Signal input is a convenience enhancement.

**Independent Test**: Can be tested by sending a Signal message to the app's Signal contact and verifying it appears in the app's chat as a user message, with the AI assistant responding as normal.

**Acceptance Scenarios**:

1. **Given** a user has a linked Signal account, **When** they send a text message from Signal to the app's Signal contact, **Then** that message appears in the app's chat interface as a user message within 30 seconds.
2. **Given** a user sends a Signal message that describes a feature request, **When** the message is processed by the app, **Then** the AI assistant generates an issue recommendation just as it would for an in-app message.
3. **Given** a user sends a Signal message but their Signal account is not linked to any app account, **When** the message is received, **Then** it is discarded and an auto-reply is sent via Signal explaining the account is not linked.

---

### User Story 4 - Manage Signal Notification Preferences (Priority: P4)

A user configures which types of chat messages are forwarded to Signal (e.g., all messages, only action-bearing messages, only system confirmations) so they can control notification volume and avoid being overwhelmed.

**Why this priority**: Notification control is important for usability but is an enhancement on top of the core send/receive capability.

**Independent Test**: Can be tested by changing notification preferences in Settings and verifying that only the selected categories of messages are forwarded to Signal.

**Acceptance Scenarios**:

1. **Given** a user has a linked Signal account, **When** they open Signal notification preferences in Settings, **Then** they see toggles for message categories: All Messages, Action Proposals Only, System Confirmations Only.
2. **Given** a user has set preferences to "Action Proposals Only", **When** a general assistant reply is sent in the app, **Then** no Signal message is sent; **When** a task proposal is sent, **Then** a Signal message is delivered.

---

### Edge Cases

- What happens when the Signal service is temporarily unavailable? The app chat must continue to function normally; Signal delivery failures are logged and retried, not surfaced as chat errors.
- What happens when a user's Signal account is deactivated or their phone number changes? The connection should gracefully degrade—outbound messages fail silently (with a logged warning), and the user sees a "Connection issue" indicator in Settings prompting re-linking.
- What happens if a user sends a Signal message that exceeds the app's maximum message length (100,000 characters)? The message is truncated to the limit with a notice appended.
- What happens if multiple app users link the same Signal phone number? Each app account maintains its own independent connection; messages from that Signal number are routed to the most recently linked app account, and older links are automatically deactivated. The previously-linked user sees a dismissible in-app banner the next time they open chat or Settings, informing them their Signal connection was severed.
- How are media attachments (images, files) sent via Signal handled? For the initial release, only text messages are supported. Media attachments receive an auto-reply stating that only text is currently supported.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a Signal account linking flow accessible from the Settings view that displays a QR code; the user scans the QR code from their Signal client to authenticate and establish a persistent connection.
- **FR-002**: System MUST display the current Signal connection status (Connected / Not Connected / Error) in the Settings view, including the linked Signal identifier.
- **FR-003**: System MUST allow users to disconnect their Signal account from the Settings view, immediately stopping all Signal message delivery.
- **FR-004**: System MUST forward chat messages from the app (assistant and system messages) to the user's linked Signal account within 30 seconds of delivery.
- **FR-005**: Action-bearing messages (task proposals, status changes, issue recommendations) forwarded to Signal MUST include a text summary and a deep link back to the app.
- **FR-006**: System MUST receive inbound text messages from Signal and route them to the correct user's chat session within their most recently active project, processing them through the same AI workflow as in-app messages.
- **FR-013**: System MUST allow Signal users to override the target project by including `#<project-name>` anywhere in the message text; when present, the message is routed to the matching project and that project becomes the new default for subsequent messages.
- **FR-007**: System MUST allow users to configure notification preferences controlling which message categories are forwarded to Signal.
- **FR-008**: System MUST handle Signal service outages gracefully—app chat functionality MUST remain unaffected. Failed Signal deliveries MUST be retried up to 3 times with exponential backoff (30 seconds, 2 minutes, 8 minutes); after 3 failures the message is dropped and the failure is logged.
- **FR-009**: System MUST validate that an inbound Signal message originates from a linked account before processing; unlinked senders MUST receive an auto-reply explaining how to connect.
- **FR-010**: System MUST support only text-based messages for the initial release; media attachments MUST receive an informative auto-reply.
- **FR-011**: System MUST log all Signal message delivery attempts (successes and failures) for observability.
- **FR-012**: System MUST ensure that the AI assistant's response to a Signal-originated message is delivered both in the app chat and back to Signal.
- **FR-014**: System MUST encrypt Signal phone numbers at rest and MUST delete them immediately upon account disconnection; no PII may be retained after the user unlinks their Signal account.
- **FR-015**: When a Signal phone number conflict causes an existing link to be severed, the system MUST display a dismissible in-app banner to the affected user the next time they open chat or Settings, informing them their Signal connection was deactivated.

### Key Entities

- **Signal Connection**: Represents the link between an app user account and a Signal identity. Key attributes: user ID, Signal identifier (phone number, encrypted at rest), connection status, linked timestamp, notification preferences. Upon disconnection, the Signal identifier is permanently deleted.
- **Signal Message**: Represents a message sent or received via Signal. Key attributes: direction (inbound/outbound), associated chat message ID, delivery status, retry count, timestamp.
- **Notification Preference**: Represents a user's Signal notification configuration. Key attributes: user ID, enabled message categories, active/inactive flag.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the Signal account linking flow in under 2 minutes from initiating connection to seeing "Connected" status.
- **SC-002**: 95% of outbound Signal messages are delivered within 30 seconds of the corresponding in-app message.
- **SC-003**: Inbound Signal messages appear in the app chat within 30 seconds of being sent from the user's Signal client.
- **SC-004**: App chat functionality experiences zero degradation when the Signal service is unavailable—all existing chat features continue to work normally.
- **SC-005**: 90% of users who initiate the Signal linking flow complete it successfully on their first attempt.
- **SC-006**: Users can disconnect their Signal account in under 30 seconds, with immediate cessation of Signal message delivery.
- **SC-007**: Notification preference changes take effect within 60 seconds of being saved by the user.

## Clarifications

### Session 2026-02-27

- Q: How should inbound Signal messages be routed to a project? → A: Route to the user's most recently active project by default; user can override by including `#<project-name>` anywhere in the message text.
- Q: What retry behavior for failed outbound Signal deliveries? → A: Retry up to 3 times with exponential backoff (30s, 2min, 8min), then drop.
- Q: How should the app verify ownership of a Signal phone number during linking? → A: QR code displayed in the app that the user scans from their Signal client to establish the link.
- Q: How should Signal phone numbers be stored and handled after disconnection? → A: Encrypt phone numbers at rest; delete immediately upon disconnection.
- Q: When a phone number conflict is detected, should the previously-linked user be notified in-app? → A: Yes — show a dismissible in-app banner the next time the affected user opens chat or Settings.

## Assumptions

- Signal provides or will provide a supported programmatic messaging interface (e.g., Signal Bot API, signal-cli, or a registered business number) that the system can use for sending and receiving messages. The specific integration mechanism is an implementation detail.
- Users have an existing Signal account with a valid phone number before attempting to link.
- The app already has session-based authentication, and the Signal connection is scoped to the authenticated user's account.
- Message delivery to Signal is best-effort; the app does not guarantee Signal delivery and treats it as a supplementary notification channel.
- Signal's terms of service permit this type of automated messaging integration for the intended use case.
