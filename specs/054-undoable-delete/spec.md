# Feature Specification: Undo/Redo Support for Destructive Actions

**Feature Branch**: `054-undoable-delete`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "Undo/Redo Support for Destructive Actions — Destructive actions (delete agent, pipeline, chore, tool) use a confirmation dialog but offer no recovery after confirmation. Replace immediate hard-deletes with a soft-delete + undo toast pattern. During a grace window (~5s), the item is hidden from the UI but not yet deleted server-side. Clicking 'Undo' in the toast cancels the pending delete. If the timer expires, the real DELETE fires."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Undo Delete via Toast Notification (Priority: P1)

A user accidentally deletes an agent from their project. Today, once the user confirms deletion in the dialog, the item is permanently removed with no way to recover it. The user needs a brief grace period after confirming a delete during which they can undo the action and restore the item. When the user confirms a delete, the item disappears from the list immediately (optimistic removal), and a toast notification appears with an "Undo" button. Clicking "Undo" within the grace window restores the item to its original position. If the grace window expires without the user clicking "Undo," the permanent deletion proceeds automatically.

**Why this priority**: This is the core value proposition of the feature. Without the undo toast, users have no safety net after confirming a destructive action. Every other user story builds on top of this foundational undo mechanism.

**Independent Test**: Can be fully tested by deleting any entity (agent, tool, chore, pipeline), observing the undo toast, clicking "Undo" within the grace window, and verifying the item is restored to its original position in the list.

**Acceptance Scenarios**:

1. **Given** a user is viewing a list of agents, **When** they confirm deletion of an agent, **Then** the agent disappears from the list immediately and a toast notification appears containing the entity name, a message confirming the pending deletion, and an "Undo" button.
2. **Given** a deletion toast is visible, **When** the user clicks the "Undo" button within the grace window, **Then** the deleted item reappears in its original position in the list and a brief "Restored" confirmation toast appears.
3. **Given** a deletion toast is visible, **When** the grace window expires without the user clicking "Undo," **Then** the item is permanently deleted and the toast dismisses automatically.
4. **Given** a user has confirmed deletion and the toast is visible, **When** the user clicks "Undo," **Then** the item's data is fully intact — no attributes, relationships, or configuration are lost during the undo.
5. **Given** a deletion toast is visible, **When** the user manually dismisses the toast (e.g., by clicking a close button), **Then** the grace window continues and the deletion proceeds as normal when the timer expires.

---

### User Story 2 — Undo Delete Across All Entity Types (Priority: P1)

A user deletes different types of entities throughout their workflow — agents, tools, chores, and pipelines. The undo experience must be consistent regardless of which entity type is being deleted. The same toast pattern, grace window duration, and undo behavior must apply uniformly across all deletable entity types.

**Why this priority**: Users interact with multiple entity types in a single session. Inconsistent undo behavior across entity types would create confusion and erode trust. This story ensures the undo mechanism is not limited to a single entity type.

**Independent Test**: Can be fully tested by sequentially deleting one of each entity type (agent, tool, chore, pipeline), undoing each deletion via the toast, and verifying consistent behavior across all types.

**Acceptance Scenarios**:

1. **Given** a user deletes an agent, **When** the deletion toast appears, **Then** the toast displays the agent's name and the "Undo" button restores the agent when clicked.
2. **Given** a user deletes a tool, **When** the deletion toast appears, **Then** the toast displays the tool's name and the "Undo" button restores the tool when clicked.
3. **Given** a user deletes a chore, **When** the deletion toast appears, **Then** the toast displays the chore's name and the "Undo" button restores the chore when clicked.
4. **Given** a user deletes a pipeline, **When** the deletion toast appears, **Then** the toast displays the pipeline's name and the "Undo" button restores the pipeline when clicked.
5. **Given** two different entity types are deleted in quick succession, **When** both toasts are visible, **Then** each toast operates independently — undoing one does not affect the other.

---

### User Story 3 — Optimistic Removal and Visual Feedback (Priority: P2)

A user deletes an item and expects immediate visual feedback. The item should vanish from the list the instant the user confirms deletion, without waiting for a server response. The list should update smoothly — no empty gaps, no layout jumps. If the user undoes the deletion, the item should reappear smoothly in its original position.

**Why this priority**: Optimistic UI is essential for the undo pattern to feel responsive. If the item only disappears after the server round-trip completes, the grace window would either feel delayed or require the user to wait, defeating the purpose of the undo toast.

**Independent Test**: Can be fully tested by deleting an item and verifying the list immediately removes the item, then undoing and verifying the list immediately restores it — both without visible loading states or layout shifts.

**Acceptance Scenarios**:

1. **Given** a list of 10 agents, **When** the user confirms deletion of the 5th agent, **Then** the agent is removed from the list instantly (within 100ms) and the remaining 9 agents reflow without gaps or visual glitches.
2. **Given** an item has been optimistically removed, **When** the user clicks "Undo," **Then** the item reappears in its original position in the list instantly (within 100ms) and the list reflows smoothly.
3. **Given** an item has been optimistically removed and the deletion toast is visible, **When** the user navigates to a different page and returns, **Then** the item remains hidden (pending deletion continues in the background).

---

### User Story 4 — Multiple Concurrent Deletions (Priority: P2)

A user is cleaning up their project and deletes several items in rapid succession. Each deletion should produce its own undo toast, and each should be independently undoable. Undoing one deletion should not affect the pending deletions of other items.

**Why this priority**: Batch cleanup is a common workflow. If the system only supports one pending deletion at a time (overwriting the previous toast), the user loses the ability to undo earlier deletions, reducing the safety net's value.

**Independent Test**: Can be fully tested by deleting 3 items in quick succession, verifying all 3 toasts appear, undoing the second deletion, and confirming only the second item is restored while the first and third deletions proceed.

**Acceptance Scenarios**:

1. **Given** a user deletes Agent A, then Tool B, then Chore C within 3 seconds, **When** all three toasts are visible, **Then** each toast shows the correct entity name and type, and each "Undo" button is independently clickable.
2. **Given** three pending deletions are active, **When** the user clicks "Undo" on the second toast, **Then** only Tool B is restored; Agent A and Chore C remain pending and will be permanently deleted when their timers expire.
3. **Given** multiple deletion toasts are stacked, **When** the user does not click "Undo" on any of them, **Then** each deletion fires independently when its own timer expires.

---

### User Story 5 — Grace Window Cleanup on Navigation (Priority: P3)

A user deletes an item and then navigates away from the page or closes the browser tab before the grace window expires. The system must handle this gracefully — pending deletions should either complete or be safely abandoned without leaving the data in an inconsistent state.

**Why this priority**: While the primary flow is the user staying on the same page, navigation-during-delete is a real edge case that could leave orphaned pending operations if not handled. This story ensures data integrity in all scenarios.

**Independent Test**: Can be fully tested by deleting an item, immediately navigating away, returning to the original page, and verifying the item is either restored (if the deletion was cancelled) or permanently deleted (if it completed).

**Acceptance Scenarios**:

1. **Given** a user has a pending deletion with 3 seconds remaining, **When** they navigate to a different page within the application, **Then** the pending deletion is cancelled, the item is restored, and no permanent deletion occurs.
2. **Given** a user has a pending deletion, **When** the component displaying the toast unmounts due to navigation, **Then** any pending timers are cleaned up to prevent memory leaks or unintended side effects.

---

### Edge Cases

- What happens when the user deletes the same item type multiple times in rapid succession (e.g., deletes 10 agents)? The toast stack must not overwhelm the screen — toasts should stack cleanly and remain individually dismissible.
- What happens when the server returns an error during the permanent deletion after the grace window expires? The user should see an error notification, and the item should reappear in the list since the server-side deletion failed.
- What happens when another user deletes the same item concurrently? If User A deletes an item and User B also deletes it before User A's grace window expires, User A's "Undo" should handle the conflict gracefully — either by showing a message that the item no longer exists or by silently accepting the deletion.
- What happens when the user's network disconnects during the grace window? The pending deletion timer should continue, but the actual deletion request should retry or fail gracefully when the timer expires and the network is still unavailable.
- What happens when the user undoes a deletion but the list has been reordered or filtered in the meantime? The restored item should appear in the correct position according to the current sort/filter state, not necessarily in its original visual position.
- What happens when the grace window is active and the user tries to interact with the deleted item via another route (e.g., a direct link or search result)? The item should either be shown as "pending deletion" or be accessible as normal until the grace window completes.

## Requirements *(mandatory)*

### Functional Requirements

#### Undo Toast Mechanism

- **FR-001**: System MUST display a toast notification immediately upon user confirmation of a delete action, containing the entity's display name, a descriptive message, and an "Undo" action button.
- **FR-002**: System MUST provide a configurable grace window (defaulting to 5 seconds) during which the permanent deletion is deferred and the user may undo the action.
- **FR-003**: System MUST cancel the pending permanent deletion and restore the item to the list when the user clicks the "Undo" button within the grace window.
- **FR-004**: System MUST permanently delete the item when the grace window expires without the user clicking "Undo."
- **FR-005**: System MUST display a brief "Restored" confirmation toast when an item is successfully restored via undo.

#### Optimistic UI Behavior

- **FR-006**: System MUST optimistically remove the item from the displayed list immediately upon delete confirmation, before any server-side deletion occurs.
- **FR-007**: System MUST restore the item to its original position in the list when the user clicks "Undo," without requiring a page reload or server round-trip to refetch the data.
- **FR-008**: System MUST re-insert the restored item in the correct position according to the current sort and filter state of the list.

#### Multiple Concurrent Deletions

- **FR-009**: System MUST support multiple simultaneous pending deletions, each with its own independent grace window and undo toast.
- **FR-010**: Undoing one pending deletion MUST NOT affect the grace window or outcome of any other pending deletion.
- **FR-011**: System MUST ensure that toast notifications from multiple deletions stack cleanly without obstructing critical UI elements.

#### Entity Coverage

- **FR-012**: The undo delete mechanism MUST be available for agents.
- **FR-013**: The undo delete mechanism MUST be available for tools.
- **FR-014**: The undo delete mechanism MUST be available for chores.
- **FR-015**: The undo delete mechanism MUST be available for pipelines.

#### Cleanup and Lifecycle

- **FR-016**: System MUST cancel all pending deletion timers and restore items when the component managing the delete unmounts (e.g., due to page navigation).
- **FR-017**: System MUST clean up all internal state (timers, cached snapshots) associated with a deletion after the deletion completes or is undone, to prevent memory leaks.

#### Error Handling

- **FR-018**: When the permanent deletion fails after the grace window expires (e.g., due to a network error), the system MUST display an error notification to the user and restore the item to the list.
- **FR-019**: When the user attempts to undo a deletion but the item has already been permanently deleted by another process, the system MUST display a message indicating the item could not be restored.

### Key Entities

- **Pending Deletion**: Represents a delete action that has been confirmed by the user but not yet executed server-side. Characterized by the target entity's identifier, a cached snapshot of the entity data, the remaining grace time, and the associated undo callback.
- **Undo Toast**: A transient notification tied to a pending deletion, providing the user with contextual information about the deleted entity and an action to reverse the deletion.

## Assumptions

- The existing confirmation dialog for delete actions remains in place. The undo toast is an additional safety net that appears after the user has already confirmed the deletion — it does not replace the confirmation step.
- The grace window duration of 5 seconds is appropriate for most users. This value should be consistent across all entity types but may be adjusted based on user feedback.
- Optimistic removal relies on the existing cache management patterns already used in the application for mutations. The undo mechanism restores cached data rather than re-fetching from the server.
- Navigation away from the current page cancels pending deletions and restores items. This is the safest default — users who navigate away likely did not intend to complete the deletion and should not lose data unexpectedly.
- The undo mechanism is client-side only. No server-side "soft delete" or "trash" infrastructure is required — the item is simply not deleted on the server until the grace window expires.
- Toast stacking follows the application's existing toast system behavior. The maximum number of visible toasts is governed by the toast library's configuration, not by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can undo an accidental deletion within 5 seconds of confirming the action, with the item fully restored to its original state and position.
- **SC-002**: The undo toast appears within 200ms of the user confirming a deletion, with the deleted item visually removed from the list in the same time frame.
- **SC-003**: 100% of deletable entity types (agents, tools, chores, pipelines) support the undo toast mechanism with identical user-facing behavior.
- **SC-004**: Users can have at least 3 concurrent pending deletions active simultaneously, each independently undoable.
- **SC-005**: Zero data loss occurs from the undo mechanism — undone items retain all their original attributes, relationships, and configuration without exception.
- **SC-006**: No memory leaks or orphaned timers result from using the undo feature, including scenarios involving rapid sequential deletions, page navigation, and component unmounting.
- **SC-007**: When the permanent deletion fails after the grace window, the user is notified and the item is restored within 1 second of the failure.
- **SC-008**: The undo feature reduces irreversible accidental deletions to near-zero for users who interact with the undo toast.
