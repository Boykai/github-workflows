# Feature Specification: Align Agent Pipeline Columns with Project Board Status & Enable Drag/Drop

**Feature Branch**: `023-pipeline-dragdrop`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Update the Agent Pipeline view to ensure its columns align with the Project Board Status columns for consistency. Additionally, enhance the user experience by enabling drag-and-drop functionality for Agent titles across both rows and columns within the Agent Pipeline."

## Assumptions

- The Agent Pipeline view currently displays agent workflow stages as columns, but these columns do not match the Project Board Status columns in naming, ordering, or count.
- The Project Board Status columns are the authoritative source of truth for status definitions; the Agent Pipeline must conform to them, not the reverse.
- Agent titles (cards) currently support click-based status changes but do not support drag-and-drop repositioning.
- Each agent title card belongs to exactly one column (status) and has a position (row order) within that column.
- Drag-and-drop interactions should persist immediately; optimistic updates are acceptable with rollback on failure.
- The Agent Pipeline is accessed by authenticated users who have permission to manage agent workflows.
- Visual feedback during drag operations follows standard conventions: a ghost/preview of the dragged item, highlighted drop zones, and cursor changes.
- Both mouse and touch-based drag interactions should be supported for accessibility across devices.
- Column definitions are managed centrally and any change to the Project Board Status columns should automatically propagate to the Agent Pipeline.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Column View Between Agent Pipeline and Project Board (Priority: P1)

As a project manager, I want the Agent Pipeline columns to match the Project Board Status columns exactly so that I see a consistent workflow regardless of which view I use, avoiding confusion about where an agent stands in the pipeline.

**Why this priority**: Column alignment is the foundational requirement. Without matching columns, the two views present conflicting information about agent workflow status, leading to confusion and process errors. This must be resolved before drag-and-drop can work correctly.

**Independent Test**: Can be fully tested by opening the Project Board and the Agent Pipeline side by side and verifying that every status column appears in both views with identical names and in the same left-to-right order.

**Acceptance Scenarios**:

1. **Given** the Project Board has status columns defined (e.g., "Backlog", "Todo", "In Progress", "In Review", "Done"), **When** a user opens the Agent Pipeline view, **Then** the Agent Pipeline displays the same columns in the same order with the same names.
2. **Given** an administrator updates the name of a Project Board Status column, **When** a user refreshes the Agent Pipeline view, **Then** the renamed column appears with the updated name in the Agent Pipeline.
3. **Given** a new status column is added to the Project Board, **When** a user opens the Agent Pipeline, **Then** the new column appears in the correct position within the Agent Pipeline.
4. **Given** a status column is removed from the Project Board, **When** a user opens the Agent Pipeline, **Then** the removed column no longer appears and any agents formerly in that column are handled gracefully (e.g., moved to a default column or flagged for reassignment).

---

### User Story 2 - Drag Agent Titles Across Columns (Priority: P2)

As a team lead, I want to drag an agent title card from one status column to another within the Agent Pipeline so that I can quickly update an agent's workflow status without navigating through menus or detail pages.

**Why this priority**: Horizontal drag-and-drop across columns is the primary interaction improvement requested. It directly enhances workflow efficiency by replacing multi-click status updates with a single drag gesture, covering the most common use case.

**Independent Test**: Can be tested by dragging an agent card from one column to a different column and verifying the card appears in the target column with the correct updated status.

**Acceptance Scenarios**:

1. **Given** an agent title card is in the "Todo" column, **When** a user drags it to the "In Progress" column, **Then** the card moves to the "In Progress" column and the agent's status is updated to "In Progress".
2. **Given** a user starts dragging an agent title card, **When** the card is held over a valid drop column, **Then** the target column visually highlights to indicate it is a valid drop zone.
3. **Given** a user is dragging an agent title card, **When** the user releases the card outside any valid column, **Then** the card returns to its original column and position with no status change.
4. **Given** a user drags an agent card to a new column, **When** the status update fails (e.g., due to a network error), **Then** the card reverts to its original column and position and the user sees a notification explaining the failure.

---

### User Story 3 - Reorder Agent Titles Within a Column (Priority: P3)

As a team lead, I want to drag agent title cards up and down within the same column so that I can prioritize agents by their visual order, making it clear which agents should be addressed first.

**Why this priority**: Vertical reordering within a column enables priority management. While less critical than cross-column status changes, it allows teams to express and communicate task priority visually, enhancing daily workflow coordination.

**Independent Test**: Can be tested by dragging an agent card to a different row position within the same column and verifying the new ordering persists after page refresh.

**Acceptance Scenarios**:

1. **Given** a column contains three agent title cards (Agent A at row 1, Agent B at row 2, Agent C at row 3), **When** a user drags Agent C above Agent A, **Then** the column displays Agent C at row 1, Agent A at row 2, Agent B at row 3.
2. **Given** a user reorders agents within a column, **When** the user refreshes the page, **Then** the new order is preserved.
3. **Given** a user is dragging an agent card within a column, **When** the card passes over other cards, **Then** the other cards shift to indicate where the dragged card will land upon release.
4. **Given** a user attempts to reorder agents but the save fails, **When** the error occurs, **Then** the agent cards revert to their previous positions and the user is notified of the failure.

---

### User Story 4 - Visual Feedback During Drag Operations (Priority: P4)

As a user, I want clear visual cues while dragging agent title cards so that I understand what I am doing, where I can drop, and what will happen when I release the card.

**Why this priority**: Without proper visual feedback, drag-and-drop becomes confusing and error-prone. While the feature technically works without polished feedback, a poor drag experience leads to accidental drops and user frustration, reducing adoption.

**Independent Test**: Can be tested by initiating a drag operation and observing visual indicators: the dragged card should appear as a ghost/preview, valid drop targets should be highlighted, and invalid areas should show a "not allowed" indicator.

**Acceptance Scenarios**:

1. **Given** a user clicks and holds an agent title card, **When** the drag threshold is exceeded (slight movement), **Then** a semi-transparent preview of the card follows the cursor and the original card's position shows a placeholder.
2. **Given** a user is dragging a card, **When** the cursor hovers over a valid drop target (another column or row position), **Then** the drop target displays a visual indicator such as a highlighted border or insertion line.
3. **Given** a user is dragging a card, **When** the cursor hovers over an area that is not a valid drop target, **Then** no drop indicator appears and the cursor changes to indicate the drop is not allowed.
4. **Given** a user drops a card on a valid target, **When** the drop completes, **Then** the card animates smoothly into its new position rather than teleporting abruptly.

---

### User Story 5 - Keyboard and Touch Accessibility for Drag/Drop (Priority: P5)

As a user on a touch device or relying on keyboard navigation, I want to be able to reorder and move agent title cards without a mouse so that the drag-and-drop functionality is accessible to all users.

**Why this priority**: Accessibility ensures the feature works for all users regardless of input method. While the majority of users will use mouse-based drag, supporting touch and keyboard interactions ensures compliance with accessibility standards and broadens the user base.

**Independent Test**: Can be tested by using only keyboard controls (e.g., arrow keys and Enter/Space) to move an agent card to a different column or row position, and by using touch gestures on a mobile or tablet device.

**Acceptance Scenarios**:

1. **Given** a user focuses on an agent title card using keyboard navigation, **When** the user activates the card (e.g., Enter or Space), **Then** the card enters a "movable" mode with visual indication and the user can use arrow keys to change its position.
2. **Given** a user is in "movable" mode with a card selected, **When** the user presses the left or right arrow key, **Then** the card moves to the adjacent column.
3. **Given** a user is in "movable" mode with a card selected, **When** the user presses the up or down arrow key, **Then** the card moves up or down within the current column.
4. **Given** a user on a touch device, **When** the user long-presses an agent title card, **Then** the card enters drag mode and can be repositioned by touch-dragging.

---

### Edge Cases

- What happens when a user drags an agent card to a column that is at maximum capacity (if a limit exists)? The system should either allow the drop (if no capacity limit is enforced) or reject it with a clear message.
- What happens when two users simultaneously drag the same agent card? The first completed action should take precedence and the second user should see the updated state with a notification that the card was moved by another user.
- What happens when the Project Board Status columns are changed while a user has the Agent Pipeline open? The view should update on the next data refresh without losing unsaved drag operations in progress.
- What happens when an agent card is dragged during a slow network connection? The system should show a loading indicator after the drop and either confirm the change or revert with a notification.
- What happens when the Agent Pipeline contains no agent cards in any column? The empty state should display a helpful message or prompt, and columns should still render correctly.
- What happens when a column is renamed while a card is being dragged to it? The drag operation should complete based on the column's identity (not its label), and the updated name should appear after the operation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Agent Pipeline MUST display the same status columns as the Project Board, with identical names, in the same left-to-right order.
- **FR-002**: Column definitions in the Agent Pipeline MUST derive from the Project Board Status configuration so that changes to the Project Board automatically propagate.
- **FR-003**: Users MUST be able to drag an agent title card horizontally from one column to another to change the agent's status.
- **FR-004**: Users MUST be able to drag an agent title card vertically within a column to change its row position (priority ordering).
- **FR-005**: The system MUST apply status changes (column moves) and ordering changes (row moves) to local state immediately after a successful drop, and present a Save/Discard bar so the user can persist or revert all pending changes as a batch.
- **FR-006**: If a batch save fails, the system MUST display an error notification to the user and keep the local changes intact so the user can retry or discard.
- **FR-007**: The system MUST provide visual feedback during drag operations, including a preview of the dragged card, highlighted drop zones, insertion indicators, and a placeholder at the original position.
- **FR-008**: The system MUST support combined drag operations where a card is moved to a different column and placed at a specific row position within that column in a single gesture.
- **FR-009**: The system MUST support keyboard-based card movement as an accessible alternative to mouse-based drag-and-drop.
- **FR-010**: The system MUST support touch-based drag-and-drop on mobile and tablet devices.
- **FR-011**: The system MUST handle concurrent edits gracefully—if another user moves a card while the current user is viewing or dragging, the view should update without data corruption.

### Key Entities

- **Agent Title Card**: Represents an individual agent within the pipeline. Key attributes: agent name, current status (column), position within the column (row order), and metadata (e.g., assigned user, last updated timestamp).
- **Pipeline Column**: Represents a workflow status stage. Key attributes: column name, display order, and mapping to the corresponding Project Board Status.
- **Project Board Status**: The authoritative definition of workflow stages. Key attributes: status name and display order. Serves as the single source of truth for column definitions in both the Project Board and Agent Pipeline views.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Project Board Status columns appear in the Agent Pipeline with matching names and order, verified by visual comparison.
- **SC-002**: Users can move an agent card from one column to another via drag-and-drop in under 2 seconds (from grab to successful drop).
- **SC-003**: Users can reorder agent cards within a column via drag-and-drop in under 2 seconds (from grab to successful drop).
- **SC-004**: Failed batch saves display a visible error notification within 1 second, and the user can retry or discard pending changes.
- **SC-005**: 90% of users can successfully move an agent card to a target column on their first attempt without needing instructions.
- **SC-006**: Drag-and-drop operations complete correctly on touch devices and via keyboard navigation, covering all three input methods (mouse, touch, keyboard).
- **SC-007**: The Agent Pipeline renders correctly with zero layout shifts when columns are added, removed, or renamed in the Project Board.
