# Feature Specification: Solune Frontend UX Improvements

**Feature Branch**: `050-frontend-ux-improvements`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Plan: Solune Frontend UX Improvements"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Action Feedback via Toast Notifications (Priority: P1)

As a user performing actions in the Solune application (saving settings, adding agents, deleting workflows, managing configurations), I need immediate visual feedback confirming whether my action succeeded or failed. Currently, all mutations happen silently with no indication of success or failure, leaving me uncertain whether my changes were applied.

**Why this priority**: This is the most critical UX gap. Without action feedback, users cannot confirm whether their work was saved, leading to confusion, duplicate actions, and lost trust in the application. Every user on every page is affected by this gap. It is foundational — all other improvements build on the assumption that users receive feedback.

**Independent Test**: Can be fully tested by performing any mutation action (e.g., saving settings, adding an agent, deleting a workflow) and verifying that a toast notification appears with the correct severity (success, error, warning, info) and auto-dismisses after a set duration.

**Acceptance Scenarios**:

1. **Given** a user is on any page with a mutation action, **When** the user saves settings successfully, **Then** a success toast appears confirming the save and auto-dismisses after 4 seconds.
2. **Given** a user is on any page with a mutation action, **When** the action fails due to a network error, **Then** an error toast appears with a user-friendly error message and remains visible until dismissed.
3. **Given** a user triggers multiple actions in quick succession, **When** multiple toasts are generated, **Then** the toasts stack vertically without overlapping content or controls.
4. **Given** a user is navigating with a screen reader, **When** a toast appears, **Then** the toast content is announced via an ARIA live region.
5. **Given** a toast is displayed, **When** the user clicks the dismiss button or the auto-dismiss timer expires, **Then** the toast smoothly animates out and is removed from the screen.

---

### User Story 2 - Formatted Chat Messages with Markdown and Code Blocks (Priority: P2)

As a user chatting with the AI assistant, I need AI responses that contain markdown (bold, links, lists, headings) and code snippets to render properly formatted instead of as raw text. When the assistant provides code examples, I need a convenient way to copy them.

**Why this priority**: The chat interface is a primary interaction surface. Unformatted code and markdown severely degrade the usefulness of AI responses. Users who receive code snippets cannot easily read or copy them, directly reducing the value of the AI assistant feature.

**Independent Test**: Can be fully tested by sending a chat prompt that elicits an AI response containing markdown formatting (bold, links, lists) and code blocks, then verifying the response renders with proper formatting and copy functionality.

**Acceptance Scenarios**:

1. **Given** the AI assistant returns a message containing markdown (bold, italics, links, lists, headings), **When** the message is displayed in the chat, **Then** the markdown renders as formatted rich text.
2. **Given** the AI assistant returns a message containing a fenced code block, **When** the message is displayed, **Then** the code block renders with syntax highlighting and a visible "Copy" button.
3. **Given** a rendered code block with a "Copy" button, **When** the user clicks "Copy," **Then** the code content is copied to the clipboard and the button briefly changes to a "Copied" confirmation state.
4. **Given** a user hovers over an AI message, **When** the hover action is detected, **Then** a "Copy message" action appears allowing the user to copy the entire message content.
5. **Given** a user message (non-AI) is displayed, **When** the message renders, **Then** it continues to display as plain text without markdown processing.

---

### User Story 3 - Kanban Board Drag-and-Drop (Priority: P3)

As a user managing issues on the project board, I need to drag issue cards between status columns (e.g., To Do, In Progress, Done) to update their status visually. Currently, the board is a static grid and cards cannot be moved.

**Why this priority**: The project board is a core workflow management tool. Without drag-and-drop, users must navigate away to update issue statuses, breaking their flow. Drag-and-drop is the expected interaction pattern for Kanban boards and its absence makes the board feel incomplete.

**Independent Test**: Can be fully tested by dragging an issue card from one column to another on the project board, verifying the card moves visually, the backend status updates, and the change persists on page reload.

**Acceptance Scenarios**:

1. **Given** a user is viewing the project board with issue cards in columns, **When** the user picks up a card by clicking and holding, **Then** a drag overlay (ghost card) appears and the original card is visually dimmed.
2. **Given** a user is dragging a card, **When** the card hovers over a different column, **Then** the target column visually highlights to indicate it is a valid drop target.
3. **Given** a user drops a card into a new column, **When** the drop completes, **Then** the card immediately appears in the new column (optimistic update) and a request is sent to update the issue status on the backend.
4. **Given** a user drops a card and the backend status update fails, **When** the error response is received, **Then** the card reverts to its original column and an error toast notification is shown.
5. **Given** a user is using keyboard navigation, **When** the user activates a card and uses keyboard controls to move it, **Then** the card can be moved between columns via keyboard with appropriate announcements for screen readers.

---

### User Story 4 - Content-Shaped Skeleton Loading States (Priority: P4)

As a user navigating the application while data is loading, I need to see content-shaped skeleton placeholders instead of a generic spinner. This reduces perceived load time and prevents layout shift when content appears.

**Why this priority**: Skeleton loading states are a quality-of-life improvement. While the generic spinner works, skeleton placeholders make the app feel faster and more polished. They prevent jarring layout shifts and give users a preview of the content structure before it loads.

**Independent Test**: Can be fully tested by throttling network speed and navigating to any data-loaded page, verifying that content-shaped skeletons appear in place of the actual content and transition smoothly to real content without layout shift.

**Acceptance Scenarios**:

1. **Given** a user navigates to a page that loads data, **When** the data is being fetched, **Then** content-shaped skeleton placeholders are displayed matching the layout of the expected content (cards, columns, messages, etc.).
2. **Given** skeleton placeholders are displayed, **When** the data finishes loading, **Then** the skeletons transition smoothly to the real content without visible layout shift.
3. **Given** a user navigates between pages, **When** a page requires data loading, **Then** the skeletons for that page type appear (board skeletons for the board, chat skeletons for chat, card skeletons for agent cards).
4. **Given** the application performs a full route change (page-level navigation), **When** the route suspense boundary is triggered, **Then** the existing full-page loading indicator is used instead of skeleton placeholders.

---

### User Story 5 - Global Keyboard Shortcuts (Priority: P5)

As a power user of the Solune application, I need global keyboard shortcuts to quickly navigate between sections, access common actions, and manage modals without reaching for the mouse.

**Why this priority**: Keyboard shortcuts are an efficiency improvement for power users. While not required for basic functionality, they significantly improve navigation speed and accessibility for users who prefer keyboard-driven workflows.

**Independent Test**: Can be fully tested by pressing defined keyboard shortcuts on any page and verifying the expected action occurs (modal opens, input is focused, section navigates, etc.).

**Acceptance Scenarios**:

1. **Given** a user is on any page, **When** the user presses `?`, **Then** a keyboard shortcuts help modal opens listing all available shortcuts.
2. **Given** a user is on any page, **When** the user presses `Ctrl+K` (or `Cmd+K` on Mac), **Then** the chat input field receives focus.
3. **Given** a user is on any page, **When** the user presses a number key `1` through `5`, **Then** the application navigates to the corresponding sidebar section.
4. **Given** a modal or overlay is open, **When** the user presses `Escape`, **Then** the modal or overlay closes.
5. **Given** a user is typing in a text input or textarea, **When** the user presses a shortcut key, **Then** the shortcut is suppressed and the character is typed normally.

---

### User Story 6 - Quick Wins: Board Filtering, Tour Progress, Chat Dates, and More (Priority: P6)

As a user of the Solune application, I benefit from several smaller UX improvements that independently enhance specific workflows: filtering and sorting the project board, seeing onboarding progress, viewing date separators in chat, seeing notification animations, richer empty states, and using `Ctrl+Enter` to send chat messages.

**Why this priority**: These are low-to-medium impact improvements that are independent of each other and can be implemented at any time. Each provides incremental value but none is blocking for the overall experience.

**Independent Test**: Each quick win can be tested independently — filter the board by assignee, check tour progress indicator, verify date separators in chat, trigger notification pulse, view empty state content, or press `Ctrl+Enter` in chat.

**Acceptance Scenarios**:

1. **Given** a user is on the project board, **When** the user selects a filter (assignee, label, or priority), **Then** only matching cards are displayed.
2. **Given** a user is in the onboarding tour, **When** a tour step is displayed, **Then** a progress indicator shows "Step X of 9."
3. **Given** a user is viewing the chat history, **When** messages span multiple days, **Then** date separator labels appear between messages from different days.
4. **Given** a user has unread notifications, **When** the unread count is greater than zero, **Then** the notification bell icon animates with a pulse effect.
5. **Given** a user views a board column or content area with no items, **When** the empty state is displayed, **Then** a themed illustration and suggested next steps are shown.
6. **Given** a user is typing in the chat input, **When** the user presses `Ctrl+Enter`, **Then** the message is sent.

---

### Edge Cases

- What happens when a toast is triggered while the user is on a page that unmounts before the toast auto-dismisses? The toast should persist in the global toast container independent of page lifecycle.
- What happens when the AI returns malformed markdown or unsupported HTML tags? The chat renderer should gracefully degrade to plain text for malformed content and sanitize any raw HTML to prevent injection.
- What happens when a drag-and-drop operation is interrupted (e.g., user switches browser tabs mid-drag)? The drag operation should cancel cleanly, returning the card to its original position without triggering a backend update.
- What happens when the backend is unavailable during a card drag? The optimistic update should revert, the card should return to its original column, and an error toast should inform the user.
- What happens when skeleton loading states are shown but the data request fails? The skeleton should transition to an error state or empty state rather than persisting indefinitely.
- What happens when multiple keyboard shortcuts conflict with browser-native shortcuts? Application shortcuts should yield to browser-native shortcuts (e.g., `Ctrl+C`, `Ctrl+V`) and only intercept non-conflicting combinations.
- What happens when a user presses `Ctrl+Enter` in chat with an empty message? The send action should be suppressed and no empty message should be sent.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1: Toast/Snackbar Notifications**

- **FR-001**: System MUST display a toast notification whenever a mutation action succeeds (save, create, update, delete).
- **FR-002**: System MUST display an error toast notification whenever a mutation action fails, with a user-friendly error message.
- **FR-003**: Toast notifications MUST support severity levels: success, error, warning, and info.
- **FR-004**: Success and info toasts MUST auto-dismiss after 4 seconds. Error toasts MUST remain until manually dismissed.
- **FR-005**: Toast notifications MUST stack vertically when multiple toasts are active, without overlapping page content or interactive controls.
- **FR-006**: Toast notifications MUST be accessible, announced via ARIA live regions for screen reader users.
- **FR-007**: Toast notifications MUST be styled consistently with the application's celestial design theme.

**Phase 2: Chat Markdown & Code Blocks**

- **FR-008**: AI chat messages MUST render markdown content (bold, italics, links, lists, headings, tables) as formatted rich text.
- **FR-009**: AI chat messages MUST render fenced code blocks with syntax highlighting.
- **FR-010**: Each rendered code block MUST include a "Copy" button that copies the code content to the clipboard.
- **FR-011**: The "Copy" button MUST provide visual feedback (e.g., "Copied!" state) for 2 seconds after a successful copy.
- **FR-012**: AI messages MUST show a "Copy message" action on hover, allowing users to copy the entire message content.
- **FR-013**: User-sent messages MUST continue to render as plain text without markdown processing.
- **FR-014**: Markdown rendering MUST sanitize content to prevent script injection or rendering of unsafe HTML.

**Phase 3: Kanban Board Drag-and-Drop**

- **FR-015**: Users MUST be able to drag issue cards from one status column to another on the project board.
- **FR-016**: A drag overlay (ghost card) MUST be shown during the drag operation, with the original card visually dimmed.
- **FR-017**: Target columns MUST visually highlight when a dragged card hovers over them.
- **FR-018**: Card drops MUST trigger an optimistic UI update (card appears in new column immediately) followed by a backend status update.
- **FR-019**: If the backend status update fails, the card MUST revert to its original column and an error toast MUST be shown.
- **FR-020**: Drag-and-drop MUST be accessible via keyboard with appropriate announcements for screen reader users.

**Phase 4: Skeleton Loading States**

- **FR-021**: System MUST provide a reusable skeleton placeholder component with a shimmer animation effect.
- **FR-022**: Content-shaped composite skeletons MUST be available for: board columns, issue cards, agent cards, and chat messages.
- **FR-023**: Data-loading views MUST display content-shaped skeletons instead of a generic spinner.
- **FR-024**: The full-page loading indicator MUST be retained for route-level suspense boundaries only.
- **FR-025**: Skeleton placeholders MUST match the dimensions and layout of the real content to prevent layout shift.

**Phase 5: Global Keyboard Shortcuts**

- **FR-026**: System MUST support the following global keyboard shortcuts: `?` (help modal), `Ctrl/Cmd+K` (focus chat), `1–5` (navigate sections), `Escape` (close modals).
- **FR-027**: Keyboard shortcuts MUST be suppressed when the user is typing in a text input, textarea, or content-editable element.
- **FR-028**: A keyboard shortcuts help modal MUST list all available shortcuts with descriptions.
- **FR-029**: Sidebar navigation items and toolbar buttons MUST display shortcut hint tooltips.

**Phase 6: Quick Wins**

- **FR-030**: Users MUST be able to filter the project board by assignee, label, and priority.
- **FR-031**: Users MUST be able to sort the project board by specified criteria.
- **FR-032**: The onboarding tour MUST display a progress indicator showing the current step and total steps.
- **FR-033**: The chat interface MUST display date separator labels between messages from different days.
- **FR-034**: The notification bell MUST animate with a pulse effect when the unread notification count is greater than zero.
- **FR-035**: Empty content areas MUST display themed illustrations and suggested next steps.
- **FR-036**: Users MUST be able to send a chat message by pressing `Ctrl+Enter`.

### Key Entities

- **Toast Notification**: A transient, non-blocking feedback message. Attributes: severity (success, error, warning, info), message text, auto-dismiss duration, dismissible flag.
- **Chat Message**: A message in the AI conversation. Attributes: content (text or markdown), sender (user or AI), timestamp, copy state.
- **Issue Card**: A draggable representation of a project issue on the board. Attributes: issue title, status, assignee, labels, priority, column position.
- **Board Column**: A droppable status category on the project board. Attributes: status name, list of issue cards, highlight state.
- **Skeleton Placeholder**: A loading-state visual stand-in for content. Attributes: shape, dimensions, animation style, associated content type.
- **Keyboard Shortcut**: A global key binding mapped to an application action. Attributes: key combination, action description, active scope, suppression context.

### Assumptions

- The application uses a component-based frontend architecture with hooks for state management and side effects.
- Existing mutation hooks (for settings, pipeline config, agent config, chores, etc.) can be extended with callback handlers for success and error states.
- The project board backend supports status update operations that can be triggered from the frontend.
- The clipboard functionality is available in supported browsers for copy operations.
- The application's existing accessibility infrastructure (ARIA attributes, focus management) can be extended for new components.
- The existing celestial design theme provides color tokens, spacing variables, and animation keyframes that new components should reuse.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of user-initiated mutation actions (save, create, update, delete) produce a visible toast notification confirming the outcome within 500 milliseconds.
- **SC-002**: AI chat messages containing markdown and code blocks render as formatted rich text with 100% of fenced code blocks displaying a functional "Copy" button.
- **SC-003**: Users can drag an issue card from one column to another and see the status update reflected within 1 second (optimistic), with automatic rollback on failure.
- **SC-004**: All data-loading views display content-shaped skeleton placeholders that match the final layout dimensions, eliminating visible layout shift upon content load.
- **SC-005**: Power users can navigate to any major section of the application using only keyboard shortcuts, with an average of 2 or fewer keystrokes per navigation action.
- **SC-006**: All new interactive elements (toasts, copy buttons, drag handles, shortcuts) are fully accessible, meeting WCAG 2.1 AA standards for keyboard operability and screen reader compatibility.
- **SC-007**: 90% of users can successfully use the drag-and-drop board interaction on their first attempt without guidance.
- **SC-008**: The keyboard shortcuts help modal provides complete documentation of all available shortcuts, with zero discrepancies between documented and actual behavior.
