# Feature Specification: Solune Frontend UX Improvements

**Feature Branch**: `050-frontend-ux-improvements`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Solune Frontend UX Improvements — six-phase plan covering toast notifications, chat markdown rendering, kanban drag-and-drop, skeleton loading states, global keyboard shortcuts, and independent quick wins"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Action Feedback via Toast Notifications (Priority: P1)

A user saves settings, adds an agent, deletes a workflow, or performs any mutation action in Solune. Today the action completes silently — there is no visual confirmation of success or failure. The user is left guessing whether their action took effect. With this improvement, every mutation surfaces a toast notification with the appropriate severity (success, error, warning, info) and auto-dismisses after a short duration. Toasts stack when multiple actions fire in quick succession, and they visually match the celestial theme.

**Why this priority**: Without action feedback, users cannot trust the application. Silent mutations erode confidence, increase support requests, and lead to redundant re-submissions. This is the single highest-impact UX gap because it affects every workflow in the app.

**Independent Test**: Trigger any mutation (e.g., save a setting, add an agent, delete a workflow) and verify a themed toast appears with correct severity, auto-dismisses, and stacks when multiple toasts fire rapidly.

**Acceptance Scenarios**:

1. **Given** a user is on the settings page, **When** the user saves a valid configuration, **Then** a success toast appears confirming the save, styled in the celestial theme, and auto-dismisses within 5 seconds.
2. **Given** a user triggers a mutation that fails (e.g., network error while deleting a workflow), **When** the failure response is received, **Then** an error toast appears with a user-friendly message describing the failure.
3. **Given** a user performs three rapid actions (e.g., deleting three items in succession), **When** all three complete, **Then** three toasts stack vertically without overlapping content or controls.
4. **Given** a user is navigating any page in the app, **When** a toast is visible, **Then** the toast is accessible via screen reader announcements and can be dismissed with keyboard interaction.

---

### User Story 2 — Chat Markdown and Code Block Rendering (Priority: P2)

A user interacts with the AI chat assistant and receives a response containing markdown — code snippets, bold text, links, bullet lists, or tables. Today the response renders as raw text, making code unreadable and links non-clickable. With this improvement, AI messages render through a markdown processor with GitHub Flavored Markdown (GFM) support, code blocks display with syntax highlighting and a copy-to-clipboard button, and users can copy entire AI messages via a hover action.

**Why this priority**: Chat is the primary interaction surface for AI-assisted workflows. Unreadable AI responses directly reduce user productivity and trust in the AI assistant. The required libraries (`react-markdown`, `remark-gfm`) are already installed — only wiring is needed.

**Independent Test**: Send a chat message that triggers an AI response containing markdown with a fenced code block. Verify the response renders formatted text, the code block has a copy button, and the hover "Copy message" action works.

**Acceptance Scenarios**:

1. **Given** a user sends a question to the AI assistant, **When** the AI responds with markdown containing bold text, links, and a bullet list, **Then** the response renders with proper formatting — bold text is visually bold, links are clickable, and lists are indented.
2. **Given** an AI response contains a fenced code block, **When** the message renders, **Then** the code block displays in a distinct styled container with a visible "Copy" button.
3. **Given** a user clicks the "Copy" button on a code block, **When** the clipboard write completes, **Then** the code content is copied to the clipboard and the button shows a brief "Copied!" confirmation.
4. **Given** a user hovers over an AI message, **When** the hover action area appears, **Then** a "Copy message" button is visible, and clicking it copies the full raw markdown content to the clipboard.
5. **Given** a user message (not AI), **When** it renders, **Then** it continues to display as plain text without markdown processing.

---

### User Story 3 — Kanban Board Drag-and-Drop (Priority: P3)

A user views the project board and wants to move an issue card from one status column to another (e.g., "To Do" → "In Progress"). Today the board is a static grid with no drag-and-drop capability. With this improvement, users can drag issue cards between columns, the system updates the issue status via the backend API with an optimistic UI update, and visual feedback (column highlighting, ghost card overlay) guides the interaction.

**Why this priority**: The project board is central to issue management. Manual status changes require opening individual issues, which breaks flow. Drag-and-drop is an expected interaction pattern for kanban boards. The `dnd-kit` library is already installed and used in the pipeline builder — the pattern exists and can be reused.

**Independent Test**: Drag an issue card from one column to a different column. Verify the card moves immediately (optimistic), the backend API is called, and the column highlights during the drag.

**Acceptance Scenarios**:

1. **Given** a user is on the project board with issues in multiple columns, **When** the user starts dragging an issue card, **Then** a ghost card overlay appears following the cursor and the source card dims.
2. **Given** a user is dragging a card over a valid target column, **When** the card enters the column boundary, **Then** the target column visually highlights to indicate it is a valid drop target.
3. **Given** a user drops a card on a different column, **When** the drop completes, **Then** the card immediately appears in the target column (optimistic update), the backend API is called to update the issue status, and a success toast confirms the move.
4. **Given** the backend API returns an error after a drop, **When** the error is received, **Then** the card rolls back to its original column and an error toast notifies the user.
5. **Given** a user is using keyboard navigation, **When** the user activates drag mode on a card, **Then** they can use arrow keys to move between columns and Enter/Space to drop.

---

### User Story 4 — Skeleton Loading States (Priority: P4)

A user navigates to a page that requires data loading (project board, agent list, chat history). Today all loading states show a generic spinning `CelestialLoader`. With this improvement, content-shaped skeleton placeholders appear in place of the actual content during loading, reducing perceived load time and eliminating layout shift when data arrives.

**Why this priority**: Skeleton states are a proven UX pattern that reduce perceived wait time by 30–40%. They also prevent jarring layout shifts. This is a quality-of-life improvement that applies across the entire app. The existing `celestial-shimmer` keyframe can be reused for the sweep animation.

**Independent Test**: Throttle the network to slow loading. Navigate to the project board. Verify content-shaped skeletons appear instead of the spinner, and when data loads, content replaces skeletons without layout shift.

**Acceptance Scenarios**:

1. **Given** a user navigates to the project board while data is loading, **When** the page renders during the loading state, **Then** skeleton placeholders shaped like board columns and issue cards appear instead of a generic spinner.
2. **Given** skeletons are displaying, **When** data finishes loading, **Then** content replaces skeletons smoothly without visible layout shift (content dimensions match skeleton dimensions).
3. **Given** the chat interface is loading message history, **When** the loading state renders, **Then** message-shaped skeletons appear in the chat pane.
4. **Given** a route-level page transition occurs, **When** the entire page is loading via React Suspense, **Then** the `CelestialLoader` spinner is used (not skeletons).
5. **Given** a user with a screen reader navigates during loading, **When** skeletons are visible, **Then** an appropriate ARIA live region announces that content is loading.

---

### User Story 5 — Global Keyboard Shortcuts (Priority: P5)

A power user wants to navigate the application efficiently without reaching for the mouse. Today there are no global keyboard shortcuts. With this improvement, users can press `?` to view a shortcut help modal, `Ctrl+K` to focus the chat input, number keys `1–5` to navigate between major sections, and `Escape` to close any open modal. Sidebar nav items and toolbar buttons display shortcut hints in their tooltips.

**Why this priority**: Keyboard shortcuts are a quality-of-life feature for power users that increase efficiency and make the app feel professional. This builds on the existing command system (`/help`, `/theme`, etc.) and tooltip infrastructure.

**Independent Test**: Press `?` on any page. Verify a shortcut help modal opens. Press `Ctrl+K` and verify the chat input receives focus.

**Acceptance Scenarios**:

1. **Given** a user is on any page and no text input is focused, **When** the user presses `?`, **Then** a keyboard shortcut help modal appears listing all available shortcuts.
2. **Given** a user is on any page, **When** the user presses `Ctrl+K` (or `Cmd+K` on macOS), **Then** the chat input receives focus regardless of the current page.
3. **Given** a user is on any page, **When** the user presses a number key `1` through `5`, **Then** the app navigates to the corresponding section (e.g., 1 = Dashboard, 2 = Board, 3 = Agents, 4 = Pipeline, 5 = Settings).
4. **Given** a modal or popover is open, **When** the user presses `Escape`, **Then** the topmost modal closes.
5. **Given** a user hovers over a sidebar nav item, **When** the tooltip appears, **Then** it includes the keyboard shortcut hint (e.g., "Board (2)").
6. **Given** a user has focus in a text input or textarea, **When** the user presses `?` or a number key, **Then** the shortcut is NOT triggered (keys behave normally for text entry).

---

### User Story 6 — Quick Wins: Board Filtering, Tour Progress, Chat Polish, and Visual Enhancements (Priority: P6)

A collection of independent, low-to-medium impact improvements that polish the overall UX: board filtering/sorting by assignee, label, and priority; onboarding tour step progress indicator ("Step X of 9"); chat date separators between messages from different days; notification bell pulse animation when unread count is greater than zero; empty state enrichment with celestial illustrations and suggested next steps; and `Ctrl+Enter` to send messages in chat.

**Why this priority**: Each item is small and independent. They collectively raise the polish level but none is individually critical. They can be implemented in any order or cherry-picked as time allows.

**Independent Test**: Each sub-improvement can be tested independently: filter the board by a label and verify results; check tour shows "Step 2 of 9"; send messages across two days and verify a date separator appears; trigger unread notifications and verify bell animates; view an empty board column and verify an illustration and suggestion appear; press `Ctrl+Enter` in chat and verify the message sends.

**Acceptance Scenarios**:

1. **Given** a user is on the project board with issues, **When** the user selects a filter (assignee, label, or priority) from the board toolbar, **Then** only matching issues display and the filter selection is visually indicated.
2. **Given** a user is in the onboarding tour, **When** a spotlight tooltip is displayed, **Then** a progress indicator shows "Step X of 9" (where X is the current step and 9 is the total).
3. **Given** a chat conversation spans multiple days, **When** messages from different calendar days are visible, **Then** a date separator line with the date label appears between them.
4. **Given** a user has unread notifications, **When** the notification bell renders with an unread count greater than zero, **Then** the bell icon displays a pulse animation to draw attention.
5. **Given** a board column has zero issues, **When** the empty column renders, **Then** it displays a celestial-themed illustration and a suggested next step (e.g., "Create your first issue").
6. **Given** a user is typing in the chat input, **When** the user presses `Ctrl+Enter`, **Then** the message sends immediately (same behavior as clicking the send button).

---

### Edge Cases

- What happens when toast notifications exceed the maximum visible stack? Oldest toasts should auto-dismiss to maintain a maximum of 3 visible toasts.
- How does markdown rendering handle malicious or deeply nested HTML in AI responses? HTML in markdown should be sanitized — raw HTML tags must not execute.
- What happens when a user drops a card on the same column it started in? The drop should be treated as a no-op — no API call, no toast.
- What happens when the backend API is unreachable during a card drag? An error toast should appear and the card should return to its original position.
- How do keyboard shortcuts behave when multiple modals are stacked? Only the topmost modal should respond to `Escape`. Shortcuts that open new UI elements should be suppressed while a modal is open.
- What happens when skeleton loading extends beyond 10 seconds? A subtle message or retry affordance should appear to prevent the user from assuming the app is frozen.
- How does `Ctrl+K` behave when the chat panel is closed? The chat panel should open and the input should receive focus.
- What happens when board filtering returns zero results? A friendly empty state should display indicating no matches and offer a "Clear filters" action.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display toast notifications for all mutation outcomes (success, error, warning) across settings, agent configuration, pipeline configuration, chore management, and board operations.
- **FR-002**: Toasts MUST auto-dismiss after a configurable duration (default 5 seconds for success, persistent until dismissed for errors).
- **FR-003**: Toasts MUST stack vertically when multiple notifications fire simultaneously, with a maximum of 3 visible at once.
- **FR-004**: Toasts MUST be accessible — announced by screen readers and dismissible via keyboard.
- **FR-005**: Toast styling MUST match the celestial theme of the application.
- **FR-006**: AI chat messages MUST render through a markdown processor supporting GitHub Flavored Markdown (bold, italic, links, lists, tables, strikethrough).
- **FR-007**: Fenced code blocks in AI messages MUST display in a visually distinct container with a "Copy" button.
- **FR-008**: Users MUST be able to copy an entire AI message's raw markdown content via a hover action.
- **FR-009**: User-sent messages MUST continue rendering as plain text (no markdown processing).
- **FR-010**: HTML within AI markdown responses MUST be sanitized to prevent injection.
- **FR-011**: Project board issue cards MUST be draggable between status columns.
- **FR-012**: Dropping a card on a new column MUST trigger a backend API call to update the issue status.
- **FR-013**: Card moves MUST use optimistic updates — the UI reflects the change immediately before the API responds.
- **FR-014**: Failed API calls after a drop MUST roll back the card to its original column and display an error toast.
- **FR-015**: Drag interactions MUST provide visual feedback: target column highlighting and a ghost card overlay.
- **FR-016**: Dropping a card on the same column it originated from MUST be treated as a no-op.
- **FR-017**: Drag-and-drop MUST be operable via keyboard (activate with Enter/Space, navigate with arrow keys, drop with Enter).
- **FR-018**: Data-loading states for board columns, issue cards, agent cards, and chat messages MUST display content-shaped skeleton placeholders instead of a generic spinner.
- **FR-019**: Skeleton placeholders MUST match the approximate dimensions of the content they represent to prevent layout shift.
- **FR-020**: Route-level Suspense boundaries MUST continue using the `CelestialLoader` spinner.
- **FR-021**: Skeleton animations MUST use the existing `celestial-shimmer` keyframe for visual consistency.
- **FR-022**: Users MUST be able to press `?` (when no text input is focused) to open a keyboard shortcut help modal.
- **FR-023**: Users MUST be able to press `Ctrl+K` / `Cmd+K` to focus the chat input from any page.
- **FR-024**: Users MUST be able to press number keys `1–5` (when no text input is focused) to navigate to major app sections.
- **FR-025**: The `Escape` key MUST close the topmost open modal or popover.
- **FR-026**: Keyboard shortcuts MUST NOT fire when a text input, textarea, or contenteditable element has focus (except `Escape` and `Ctrl+K`).
- **FR-027**: Sidebar nav items and toolbar buttons MUST display shortcut hints in their tooltips.
- **FR-028**: The board toolbar MUST support filtering issues by assignee, label, and priority.
- **FR-029**: The onboarding tour MUST display a step progress indicator ("Step X of N").
- **FR-030**: Chat messages from different calendar days MUST be separated by a date label.
- **FR-031**: The notification bell MUST display a pulse animation when the unread notification count is greater than zero.
- **FR-032**: Empty board columns MUST display a themed illustration and a suggested next step.
- **FR-033**: Users MUST be able to press `Ctrl+Enter` in the chat input to send a message.

### Key Entities

- **Toast Notification**: Represents a transient feedback message. Attributes: message text, severity (success, error, warning, info), duration, dismissible flag, optional action link.
- **Rendered Message**: A chat message that has been processed for display. AI messages pass through markdown rendering; user messages render as plain text. Includes metadata for copy-to-clipboard interactions.
- **Board Card**: An issue card on the project board. Has a status (mapped to a column), position within a column, and supports drag-and-drop state (idle, dragging, dropping, rolling back).
- **Skeleton Placeholder**: A loading-state placeholder shaped to match a specific content type (column, card, message, agent tile). Has dimensions, animation style, and an ARIA loading announcement.
- **Keyboard Shortcut**: A global key binding mapped to an action. Has a key combination, description, category (navigation, action, help), and a guard condition (e.g., "not when input is focused").

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of user-initiated mutations surface a toast notification with the correct severity — verified by performing each mutation type (save, delete, add, update) and confirming a toast appears.
- **SC-002**: Users can identify whether an action succeeded or failed within 1 second of the action completing, without needing to refresh or navigate away.
- **SC-003**: AI chat responses containing markdown render with visible formatting (bold, links, lists, code blocks) — verified by sending at least 5 different markdown patterns and confirming correct rendering.
- **SC-004**: Users can copy a code block from an AI response in a single click — verified by the clipboard containing the exact code content after clicking the copy button.
- **SC-005**: Users can move an issue between board columns via drag-and-drop in under 2 seconds — verified by timing the drag-drop-confirm cycle.
- **SC-006**: Failed board moves roll back within 1 second and display an error notification — verified by simulating a backend error during a drag-drop.
- **SC-007**: Content-loading pages display shaped skeletons instead of generic spinners — verified by throttling the network and observing the loading state on at least 3 pages (board, chat, agents).
- **SC-008**: Loaded content replaces skeletons with zero visible layout shift — verified by recording the loading transition and confirming no content jump.
- **SC-009**: Power users can open the shortcut modal, navigate to any major section, and focus the chat input using only the keyboard in under 3 seconds total — verified by timed keyboard-only navigation test.
- **SC-010**: Board filtering reduces visible issues to only those matching the selected criteria — verified by applying each filter type and confirming accurate results.
- **SC-011**: All new interactive elements meet WCAG 2.1 AA accessibility standards — verified by screen reader testing and keyboard-only navigation of new features.
