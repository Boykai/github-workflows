# Feature Specification: Solune UX Improvements Plan

**Feature Branch**: `051-solune-ux-improvements`  
**Created**: 2026-03-19  
**Status**: Draft  
**Input**: User description: "Solune UX Improvements Plan — 10 concrete UX improvement areas spanning mobile responsiveness, perceived performance, interaction consistency, and discoverability for the Solune AI-powered agent orchestration platform."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Mobile Chat Experience (Priority: P1)

A user accesses Solune from a smartphone (screen width ≤ 480px) and opens the chat assistant. Today the chat popup has a fixed minimum width of 300px and a default width of 400px, which causes horizontal overflow or awkward layout on narrow screens. The user needs the chat to occupy the full screen as a bottom-sheet overlay so they can comfortably type prompts and read AI responses on mobile.

**Why this priority**: Chat is the primary interaction channel for an AI orchestration platform. If mobile users cannot use the chat, the entire product is unusable on phones — the highest-impact gap.

**Independent Test**: Can be fully tested by opening the chat on a 320px-wide viewport and verifying the chat fills the screen as a bottom-sheet without horizontal overflow, content truncation, or unusable controls.

**Acceptance Scenarios**:

1. **Given** a user is on a device with a viewport width below 768px, **When** they tap the chat toggle button, **Then** the chat opens as a full-screen overlay or bottom-sheet that covers the entire viewport width with no horizontal scrolling.
2. **Given** the chat is open in bottom-sheet mode on mobile, **When** the user types a message and submits, **Then** the message input, send button, and AI response are all fully visible and usable without zooming or horizontal scrolling.
3. **Given** the chat is open in bottom-sheet mode, **When** the user taps the close button or swipes down, **Then** the chat dismisses and the underlying page is fully visible again.
4. **Given** a user resizes the browser window from desktop (≥ 768px) to mobile width (< 768px) while the chat is open, **Then** the chat transitions smoothly from the floating popup to the bottom-sheet layout.

---

### User Story 2 — Sidebar Auto-Collapse on Mobile (Priority: P1)

A user navigates Solune on a tablet or phone. The sidebar currently does not auto-collapse and remains expanded, consuming valuable screen real estate and overlapping main content. The sidebar should automatically collapse on screens narrower than 768px, and users should be able to manually expand it via a toggle.

**Why this priority**: The sidebar occupies 240px when expanded — on a 375px phone that leaves only 135px for content, making the app completely unusable. This is a fundamental layout blocker for mobile use.

**Independent Test**: Can be fully tested by loading any page on a 375px viewport and verifying the sidebar is collapsed by default, showing only icons, and can be toggled.

**Acceptance Scenarios**:

1. **Given** a user opens Solune on a viewport narrower than 768px, **When** the page loads, **Then** the sidebar is in its collapsed (icon-only) state automatically.
2. **Given** the sidebar is auto-collapsed on mobile, **When** the user taps the expand toggle, **Then** the sidebar expands as an overlay on top of content (not pushing content off-screen).
3. **Given** the sidebar is expanded as an overlay on mobile, **When** the user taps outside the sidebar or selects a navigation item, **Then** the sidebar collapses back to its icon-only state.
4. **Given** a user is on a desktop viewport (≥ 768px), **When** the page loads, **Then** the sidebar remains in whatever state the user last set (expanded or collapsed), unaffected by mobile auto-collapse logic.

---

### User Story 3 — Responsive Issue Detail Modal (Priority: P2)

A user taps on an issue card on the project board while using a phone. The issue detail modal currently uses a fixed maximum width and does not expand to fill small viewports, making content cramped with tiny text and requiring excessive scrolling.

**Why this priority**: Viewing and managing issues is a core workflow. On mobile, the modal must be full-screen to show issue details (title, status, description, sub-issues, linked PRs) in a readable format.

**Independent Test**: Can be fully tested by tapping an issue card on a 375px viewport and verifying the modal fills the screen with readable content and a clear close action.

**Acceptance Scenarios**:

1. **Given** a user is on a viewport narrower than 768px, **When** they open an issue detail modal, **Then** the modal occupies the full viewport width and at least 95% of the viewport height with appropriate padding.
2. **Given** the issue detail modal is open full-screen on mobile, **When** the user scrolls the description section, **Then** only the description scrolls while the modal header (title, close button) remains fixed and visible.
3. **Given** the issue detail modal is open on mobile, **When** the user taps the close button or presses Escape, **Then** the modal closes and the board view is restored.

---

### User Story 4 — Mobile-Friendly Board Toolbar (Priority: P2)

A user accesses the project board on a phone and needs to filter, sort, or group issues. The toolbar currently shows all filter/sort/group controls in a horizontal row, which overflows or overlaps content on narrow screens.

**Why this priority**: Filtering and sorting are essential for managing boards with many issues. If these controls are unusable on mobile, productivity drops significantly.

**Independent Test**: Can be fully tested by opening the board toolbar on a 375px viewport and verifying all controls are accessible without horizontal overflow.

**Acceptance Scenarios**:

1. **Given** a user is on a viewport narrower than 768px, **When** they view the board toolbar, **Then** the toolbar controls are arranged in a compact layout (e.g., icon-only buttons, collapsible menu, or stacked layout) that fits within the viewport width without horizontal scrolling.
2. **Given** the toolbar is in mobile layout, **When** the user taps a filter/sort/group control, **Then** the dropdown panel opens in a way that does not overlap or obscure the toolbar close/navigation controls.
3. **Given** active filters are applied on mobile, **When** the user views the toolbar, **Then** a visible indicator shows that filters are active (e.g., badge count or highlighted icon).

---

### User Story 5 — Skeleton Loaders for Catalog Pages (Priority: P2)

A user navigates to the Agents, Tools, Chores, or Apps pages. Currently these pages show a centered spinning loader during data fetches, which provides no structural preview of incoming content and feels slower than it is. The user should see skeleton placeholders that mirror the page layout during loading, giving an immediate sense of progress and structure.

**Why this priority**: Perceived performance directly impacts user satisfaction. Skeleton loaders reduce perceived wait time by up to 30% compared to spinner-only loading states, improving the experience for all users on every page load.

**Independent Test**: Can be fully tested by throttling the network and loading each catalog page, verifying skeleton placeholders appear in the shape of the expected content before data arrives.

**Acceptance Scenarios**:

1. **Given** the Agents page is loading data, **When** the user navigates to the page, **Then** skeleton placeholders matching the layout of agent cards/rows appear immediately instead of a generic spinner.
2. **Given** the Tools page is loading data, **When** the user navigates to the page, **Then** skeleton placeholders matching the tools list layout appear.
3. **Given** the Chores page is loading data, **When** the user navigates to the page, **Then** skeleton placeholders matching the chores panel layout appear.
4. **Given** the Apps page is loading data, **When** the user navigates to the page, **Then** skeleton placeholders matching the apps card grid appear.
5. **Given** data has finished loading on any catalog page, **When** the skeletons are visible, **Then** they transition smoothly to the actual content without layout shift or flash of content.

---

### User Story 6 — Optimistic Updates for Drag-Drop and App Actions (Priority: P3)

A user drags an issue card from one board column to another, or starts/stops an application. Currently the UI waits for the server response before updating, causing a perceptible delay (200ms–2s depending on network) during which the card snaps back to its original position or the button shows no feedback. The user should see the change reflected instantly, with an automatic rollback and error notification if the server rejects the update.

**Why this priority**: High-frequency interactions (drag-drop is performed dozens of times per session) must feel instant. Delays in these interactions erode trust in the platform's responsiveness.

**Independent Test**: Can be fully tested by performing a drag-drop operation with simulated network delay and verifying the card moves immediately, then testing with a simulated server error to verify rollback.

**Acceptance Scenarios**:

1. **Given** a user drags an issue card to a new column, **When** they drop the card, **Then** the card appears in the new column immediately without waiting for a server response.
2. **Given** an issue was optimistically moved, **When** the server confirms the update, **Then** no visible change occurs (the UI already shows the correct state).
3. **Given** an issue was optimistically moved, **When** the server rejects the update, **Then** the card animates back to its original column and an error notification appears.
4. **Given** a user clicks "Start" on an application, **When** the button is clicked, **Then** the UI immediately shows the app as "Starting" without waiting for a server response.
5. **Given** an app start was optimistically updated, **When** the server rejects the request, **Then** the app status reverts to its previous state and an error notification appears.

---

### User Story 7 — Standardized Toast Notifications (Priority: P3)

A user performs create, update, or delete operations across the platform. Currently feedback is inconsistent — some actions show toast notifications, others use inline success/error messages that persist until dismissed. The user should receive consistent toast notifications for all mutation feedback across the entire application.

**Why this priority**: Inconsistent feedback patterns create cognitive load and confusion. Users should not have to learn different feedback mechanisms for different pages. Standardizing to toasts provides a predictable, non-blocking feedback pattern.

**Independent Test**: Can be fully tested by performing create/update/delete operations on agents, tools, chores, and apps, and verifying that each action produces a consistent toast notification.

**Acceptance Scenarios**:

1. **Given** a user creates, updates, or deletes any resource (agent, tool, chore, or app), **When** the operation succeeds, **Then** a success toast notification appears with a descriptive message and auto-dismisses after 3–5 seconds.
2. **Given** a user performs a mutation that fails, **When** the server returns an error, **Then** an error toast notification appears with a clear error description and persists until the user dismisses it.
3. **Given** multiple rapid operations are performed, **When** several toasts are triggered in quick succession, **Then** they stack visibly without overlapping and each can be independently dismissed.

---

### User Story 8 — Actionable Empty States for Catalog Pages (Priority: P3)

A user who has created a project but has not yet created any agents, tools, or chores navigates to the respective catalog page. Currently, empty lists show a minimal "no items" message. The user should see an inviting empty state with guidance on what the resource is, why it matters, and a prominent call-to-action button to create their first item.

**Why this priority**: First-use experience defines user activation. Actionable empty states reduce time-to-first-value by guiding new users through their first creation flow.

**Independent Test**: Can be fully tested by navigating to each catalog page with a project that has no agents/tools/chores, and verifying the empty state shows descriptive guidance and a working create button.

**Acceptance Scenarios**:

1. **Given** a user has a project selected but no agents exist, **When** they navigate to the Agents page, **Then** an empty state is displayed with an explanation of what agents do and a "Create your first agent" call-to-action button.
2. **Given** a user has a project selected but no tools exist, **When** they navigate to the Tools page, **Then** an empty state is displayed with an explanation of what tools do and a "Create your first tool" call-to-action button.
3. **Given** a user has a project selected but no chores exist, **When** they navigate to the Chores page, **Then** an empty state is displayed with an explanation of what chores do and a "Create your first chore" call-to-action button.
4. **Given** the user clicks the create call-to-action in any empty state, **When** the action completes, **Then** the empty state is replaced by the newly created item in the catalog list.

---

### User Story 9 — Text Search on Board and Catalog Pages (Priority: P4)

A user has a board with many issues or a catalog page with many items and wants to find a specific one quickly. Currently the board toolbar offers filter, sort, and group controls but no text search. The user should be able to type keywords to instantly filter issues or catalog items by title or description.

**Why this priority**: Search is the fastest way to find specific items in large lists. As users accumulate more issues and resources, text search becomes essential for productivity.

**Independent Test**: Can be fully tested by typing a search term into the search field on the board and verifying only matching issues are displayed.

**Acceptance Scenarios**:

1. **Given** the user is on the project board, **When** they type a search term into the board toolbar search field, **Then** only issues whose title or description contains the search term are displayed, with non-matching issues hidden.
2. **Given** the user is on a catalog page (Agents, Tools, or Chores), **When** they type a search term, **Then** only matching items are shown.
3. **Given** a search term is active, **When** the user clears the search field, **Then** all items are shown again.
4. **Given** a search term matches no items, **When** the results are empty, **Then** a "No results found" message is displayed with a suggestion to adjust the search term.

---

### User Story 10 — Extended Onboarding Tour (Priority: P4)

A new user completes the current onboarding tour but is not introduced to the Tools, Chores, Settings, or Apps pages. The user should experience a comprehensive tour that covers all major sections of the application so they understand the full breadth of Solune's capabilities.

**Why this priority**: The onboarding tour is a one-time investment that significantly impacts feature adoption. Covering more pages increases the chance that users discover and use advanced features.

**Independent Test**: Can be fully tested by triggering the onboarding tour and verifying it includes steps for all major pages, including Tools, Chores, Settings, and Apps.

**Acceptance Scenarios**:

1. **Given** a new user starts the onboarding tour, **When** the tour progresses past the existing steps, **Then** additional steps introduce the Tools, Chores, Settings, and Apps pages with brief descriptions of each.
2. **Given** the extended tour includes a step for a page, **When** that step is shown, **Then** the corresponding sidebar link is highlighted and the tooltip explains the page's purpose.
3. **Given** the user is on any tour step, **When** they press the skip button, **Then** the tour ends and is marked as completed (same behavior as today).
4. **Given** the user completes the full extended tour, **When** the last step finishes, **Then** the tour is marked completed and does not appear on subsequent visits.

---

### User Story 11 — Undo/Redo in Pipeline Builder (Priority: P4)

A user is configuring an agent pipeline and accidentally deletes a stage, removes an agent, or makes an unwanted change. Currently there is no way to undo the change — the user must manually recreate the lost configuration. The user should be able to press Ctrl+Z (Cmd+Z on Mac) to undo their last change and Ctrl+Shift+Z (Cmd+Shift+Z on Mac) to redo.

**Why this priority**: Pipeline configuration involves complex multi-step workflows where mistakes are costly. Undo/redo is a standard expectation in builder interfaces and significantly reduces configuration anxiety.

**Independent Test**: Can be fully tested by making changes to a pipeline configuration, pressing Ctrl+Z to undo, verifying the previous state is restored, and pressing Ctrl+Shift+Z to redo.

**Acceptance Scenarios**:

1. **Given** a user makes a change to a pipeline (add/remove/reorder stage, add/remove/update agent), **When** they press Ctrl+Z (or Cmd+Z), **Then** the pipeline reverts to the state before the last change.
2. **Given** a user has undone a change, **When** they press Ctrl+Shift+Z (or Cmd+Shift+Z), **Then** the undone change is reapplied.
3. **Given** a user has made multiple changes, **When** they press Ctrl+Z multiple times, **Then** each press reverts one change in reverse chronological order.
4. **Given** a user has undone changes and then makes a new change, **When** they try to redo, **Then** the redo history is cleared (standard undo/redo behavior — new changes fork the history).
5. **Given** a user loads a pipeline from the server or discards changes, **When** the pipeline state resets, **Then** the undo/redo history is cleared.

---

### Edge Cases

- What happens when a user rotates their device between portrait and landscape while the chat bottom-sheet is open? The layout should adapt without losing the current conversation or input text.
- How does the sidebar behave when the user resizes a desktop browser window below 768px? The sidebar should auto-collapse smoothly without jarring layout shifts.
- What happens when an optimistic update is in progress and the user performs another drag-drop on the same card? The system should queue or reject the second operation until the first resolves.
- What happens when a user with a slow connection performs rapid mutations that all require toast notifications? Toasts should stack without overflow and the oldest should auto-dismiss to prevent screen clutter (maximum 5 visible toasts).
- What happens when the undo stack exceeds a reasonable depth (e.g., 50 actions)? The oldest entries should be silently discarded to prevent excessive memory usage.
- What happens when skeleton loaders are shown and the data request fails? The skeleton should transition to an error state with a retry option, not remain indefinitely.
- What happens if the onboarding tour attempts to highlight a navigation item that has been removed or renamed? The tour step should be skipped automatically (existing behavior should be preserved).

## Requirements *(mandatory)*

### Functional Requirements

**Mobile Responsiveness**

- **FR-001**: The chat popup MUST display as a full-screen overlay or bottom-sheet on viewports narrower than 768px, occupying the full viewport width.
- **FR-002**: The chat bottom-sheet MUST include all functionality available in the desktop popup: message input, send button, message history, and close action.
- **FR-003**: The sidebar MUST automatically collapse to its icon-only state when the viewport width is below 768px on initial page load.
- **FR-004**: The sidebar MUST expand as an overlay (not pushing content) when manually toggled on mobile, and MUST collapse when the user taps outside it or selects a navigation item.
- **FR-005**: The issue detail modal MUST display in full-screen mode on viewports narrower than 768px, with a fixed header and scrollable content area.
- **FR-006**: The board toolbar MUST adapt its layout on viewports narrower than 768px to prevent horizontal overflow, using a compact arrangement such as icon-only buttons or a collapsible menu.
- **FR-007**: All mobile layout adaptations MUST transition smoothly when the viewport is resized across the 768px breakpoint.

**Perceived Performance**

- **FR-008**: The Agents, Tools, Chores, and Apps pages MUST display skeleton placeholders that reflect the expected content layout during data loading, replacing the current generic spinner.
- **FR-009**: Skeleton placeholders MUST transition to actual content without visible layout shift when data arrives.
- **FR-010**: Board drag-drop status changes MUST update the UI immediately (optimistic update) before the server response is received.
- **FR-011**: App start and stop actions MUST update the UI immediately (optimistic update) before the server response is received.
- **FR-012**: If the server rejects an optimistic update, the system MUST revert the UI to the previous state and display an error notification to the user.

**Interaction Consistency**

- **FR-013**: All create, update, and delete operations across agents, tools, chores, and apps MUST provide user feedback exclusively via toast notifications (not inline alerts or manual state messages).
- **FR-014**: Success toasts MUST auto-dismiss after 3–5 seconds. Error toasts MUST persist until the user dismisses them.
- **FR-015**: When a project is selected but the catalog list (agents, tools, or chores) is empty, the system MUST display an actionable empty state with a description of the resource type and a call-to-action button to create the first item.

**Discoverability & Power Users**

- **FR-016**: The board toolbar MUST include a text search field that filters displayed issues by matching against issue title and description content.
- **FR-017**: Catalog pages (Agents, Tools, Chores) MUST include a text search field that filters displayed items by name or description.
- **FR-018**: The search filter MUST be client-side, operating on already-loaded data without additional server requests.
- **FR-019**: The onboarding tour MUST include additional steps covering Tools, Chores, Settings, and Apps pages, extending the current 9-step tour.
- **FR-020**: Each new tour step MUST highlight the corresponding sidebar navigation item and display a tooltip explaining the page's purpose.
- **FR-021**: The pipeline builder MUST support undo (Ctrl+Z / Cmd+Z) and redo (Ctrl+Shift+Z / Cmd+Shift+Z) for all pipeline configuration changes.
- **FR-022**: The undo/redo history MUST be cleared when a pipeline is loaded from the server, discarded, or when a new pipeline is created.
- **FR-023**: The undo history MUST support at least 50 entries before silently discarding the oldest actions.

### Key Entities

- **Viewport Breakpoint**: A width threshold (768px) that determines whether the application renders in mobile or desktop layout mode. Affects sidebar, chat, modals, and toolbar behavior.
- **Skeleton Placeholder**: A visual placeholder matching the expected layout structure of a content area, displayed during data loading to communicate progress and reduce perceived wait time.
- **Optimistic Update**: A UI state change applied immediately upon user action, before server confirmation, with automatic rollback on server error.
- **Undo/Redo History Stack**: An ordered collection of pipeline state snapshots enabling users to reverse or reapply configuration changes. Maximum depth of 50 entries.
- **Toast Notification**: A brief, non-blocking message overlay used to communicate operation success or failure. Success toasts auto-dismiss; error toasts persist until dismissed.
- **Empty State**: A specialized view shown when a catalog list has no items, providing contextual guidance and a call-to-action to create the first resource.

## Assumptions

- The 768px breakpoint is the standard tablet/mobile boundary. All responsive behaviors use this single breakpoint for consistency.
- The chat bottom-sheet on mobile does not support drag-to-resize (resize is a desktop-only interaction).
- Optimistic updates are scoped to board drag-drop and app start/stop only — other mutations (create, update, delete for agents/tools/chores) will continue to wait for server confirmation as they are lower-frequency operations.
- Undo/redo is scoped to the pipeline builder only, not to board operations or other configuration surfaces.
- Board text search is client-side filtering of already-loaded issue data. No new server endpoints are needed.
- The existing skeleton component (with pulse and shimmer variants) is reusable for all catalog pages without modification.
- Toast notification stacking behavior (max visible toasts, positioning) follows the defaults of the existing toast library.
- The onboarding tour extension adds approximately 4 new steps (Tools, Chores, Settings, Apps), bringing the total from 9 to approximately 13 steps.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All core workflows (chat, board, issue detail, sidebar navigation) are fully usable on 320px, 375px, 768px, and 1024px viewport widths with no horizontal scrolling or content overflow.
- **SC-002**: Users can complete a board drag-drop operation with perceived instant feedback (visual update in under 100ms), regardless of server response time.
- **SC-003**: 100% of create, update, and delete mutations across all resource types (agents, tools, chores, apps) produce toast notifications with consistent timing and behavior.
- **SC-004**: All four catalog pages (Agents, Tools, Chores, Apps) display skeleton placeholders during loading, with zero layout shift when content replaces skeletons.
- **SC-005**: New users experience an onboarding tour that covers all major application sections, with tour completion rate remaining at or above the current baseline.
- **SC-006**: Pipeline builder users can undo at least 50 sequential changes and redo any undone changes, with each undo/redo operation completing in under 200ms.
- **SC-007**: Empty catalog pages display actionable empty states with create CTAs, and users who click the CTA successfully create their first resource at least 80% of the time.
- **SC-008**: Text search on board and catalog pages returns filtered results within 300ms of the last keystroke for datasets of up to 500 items.
- **SC-009**: Existing automated test suites (unit and end-to-end) pass after all improvements are implemented, with no regressions.
