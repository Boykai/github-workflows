# Feature Specification: Optimistic UI Updates for Mutations

**Feature Branch**: `054-optimistic-ui-updates`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "Plan: Optimistic UI Updates for Mutations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Board Drag-and-Drop Feels Instant (Priority: P1)

A user managing their project board drags a card from one status column (e.g., "In Progress") to another (e.g., "Done"). The card visually moves to the target column the moment the user drops it, without waiting for a network round-trip. If the server rejects the change or the network is down, the card smoothly snaps back to its original column and the user sees a clear error notification.

**Why this priority**: Board drag-and-drop is the highest-visibility, most frequently used interaction. The current delay between dropping a card and seeing it move creates a sluggish, unresponsive feel that undermines user confidence in the interface.

**Independent Test**: Can be fully tested by dragging any board card between columns and observing instant visual movement. Delivers immediate perceived-performance value even if no other optimistic updates are implemented.

**Acceptance Scenarios**:

1. **Given** a project board is displayed with cards in columns, **When** the user drags a card from column A to column B, **Then** the card appears in column B instantly (before any server response).
2. **Given** a card was just dragged to a new column, **When** the server confirms the status change, **Then** the card remains in the new column and all data refreshes to match server state.
3. **Given** a card was just dragged to a new column, **When** the server rejects the status change (error response), **Then** the card returns to its original column and an error toast is displayed.
4. **Given** the network is unavailable, **When** the user drags a card, **Then** the card moves momentarily but snaps back with an error toast once the request fails.

---

### User Story 2 - Chore CRUD Operations Are Responsive (Priority: P2)

A user creates, updates, or deletes chores on their project. When they add a new chore, it appears in the list immediately with placeholder data. When they edit a chore's fields inline or via a form, the change appears instantly. When they delete a chore, it disappears from the list immediately. Any server failure causes the change to revert cleanly with a notification.

**Why this priority**: Chore management is the most frequently used CRUD workflow. Users perform multiple create/update/delete actions in rapid succession, and waiting for each server response before seeing the result significantly disrupts their flow.

**Independent Test**: Can be fully tested by performing chore CRUD operations and verifying instant UI feedback. Each operation (create, update, delete, inline edit) can be tested in isolation.

**Acceptance Scenarios**:

1. **Given** a list of chores is displayed, **When** the user creates a new chore, **Then** the chore appears in the list immediately with a temporary placeholder appearance.
2. **Given** a chore is displayed, **When** the user edits its title or other fields, **Then** the changes appear in the UI immediately without a loading spinner.
3. **Given** a chore is displayed, **When** the user deletes it, **Then** the chore disappears from the list immediately.
4. **Given** a new chore was optimistically added, **When** the server confirms creation, **Then** placeholder data is replaced with server-confirmed data (real ID, timestamps).
5. **Given** any chore operation was performed optimistically, **When** the server returns an error, **Then** the UI reverts to its previous state and an error toast is shown.

---

### User Story 3 - App Status Changes Feel Immediate (Priority: P3)

A user starts or stops an app from the apps list. The status badge toggles instantly (e.g., from "stopped" to "running") without waiting for the server. If the server fails to process the request, the badge reverts and the user is notified. Similarly, app create, update, and delete operations show instant UI feedback.

**Why this priority**: App status toggling is a common action where the delay between clicking start/stop and seeing the status change creates uncertainty about whether the action registered.

**Independent Test**: Can be tested by toggling app status and observing the instant badge change. CRUD operations can also be verified independently.

**Acceptance Scenarios**:

1. **Given** an app is displayed with status "stopped", **When** the user clicks start, **Then** the status badge immediately shows "running".
2. **Given** an app's status was optimistically changed, **When** the server confirms the change, **Then** the status remains as shown and data is refreshed.
3. **Given** an app's status was optimistically changed, **When** the server rejects the change, **Then** the badge reverts to its previous state and an error toast is displayed.
4. **Given** a list of apps is displayed, **When** the user creates/updates/deletes an app, **Then** the change appears immediately in the list.

---

### User Story 4 - Tool and Pipeline Deletions Are Instant (Priority: P4)

A user deletes a tool or pipeline from their respective lists. The deleted item disappears from the list immediately, without waiting for server confirmation. If the server fails, the item reappears and an error notification is shown.

**Why this priority**: While less frequent than chore or app operations, delete operations benefit meaningfully from optimistic updates because the current pattern of waiting for a response before removing the item feels slow and uncertain.

**Independent Test**: Can be tested by deleting a tool or pipeline and verifying it disappears from the list immediately.

**Acceptance Scenarios**:

1. **Given** a list of tools is displayed, **When** the user deletes a tool, **Then** the tool disappears from the list immediately.
2. **Given** a list of pipelines is displayed, **When** the user deletes a pipeline, **Then** the pipeline disappears from the list immediately.
3. **Given** a tool or pipeline was optimistically removed, **When** the server confirms deletion, **Then** the item remains removed and the list refreshes from the server.
4. **Given** a tool or pipeline was optimistically removed, **When** the server rejects deletion, **Then** the item reappears in the list and an error toast is shown.

---

### User Story 5 - Graceful Error Recovery Across All Mutations (Priority: P1)

Across all optimistic mutations, when the server returns an error or the network is unavailable, the UI state reverts cleanly to the last known-good state. The user always sees a clear error notification explaining what went wrong. No data is lost or corrupted due to optimistic updates.

**Why this priority**: Error recovery is fundamental to the reliability of optimistic updates. Without robust rollback, optimistic updates would create data inconsistencies and erode user trust. This is co-prioritized with P1 because it must accompany the board drag-and-drop feature.

**Independent Test**: Can be tested by simulating network failures and server errors during any mutation and verifying clean rollback behavior.

**Acceptance Scenarios**:

1. **Given** any optimistic mutation is in flight, **When** the server returns a 4xx or 5xx error, **Then** the UI reverts to its previous state and an error toast is shown.
2. **Given** any optimistic mutation is in flight, **When** the network connection is lost, **Then** the UI reverts to its previous state and an error toast is shown.
3. **Given** multiple optimistic mutations are in flight simultaneously, **When** one fails, **Then** only the failed mutation's changes revert; other mutations remain unaffected.
4. **Given** an optimistic mutation successfully completes, **When** the server response arrives, **Then** the UI state is reconciled with server data to ensure consistency.

---

### Edge Cases

- What happens when a user drags a board card while a previous drag-and-drop mutation is still in flight? The new drag should be queued or the previous mutation's optimistic state should be used as the baseline for the next snapshot.
- What happens when a user rapidly creates multiple chores before the first creation has been confirmed by the server? Each creation should generate its own snapshot and temporary entry; all should resolve independently.
- What happens when a user deletes an item that has already been deleted by another user (concurrent modification)? The reconciliation phase (re-fetch) will reflect the server state; the optimistic removal remains visually consistent.
- What happens when the server returns a success response but with data that conflicts with the optimistic update (e.g., server modifies additional fields)? The settled-phase re-fetch replaces all optimistic data with server truth, resolving any conflicts.
- What happens when the user navigates away from the page while an optimistic mutation is still settling? Standard cache invalidation behavior applies; the mutation completes in the background and the cache is updated for when the user returns.
- What happens when the cache is empty or stale at the time an optimistic update is attempted? The mutation should still proceed; if no cached data exists to snapshot, the optimistic update should be skipped and the mutation should fall back to the standard fire-and-wait pattern.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST update the UI immediately (before server response) when a user performs any supported mutation (board status change, chore CRUD, app CRUD, app start/stop, tool delete, pipeline delete).
- **FR-002**: The system MUST revert the UI to its previous state when a mutation fails (server error or network failure).
- **FR-003**: The system MUST display an error notification to the user when any mutation fails, with a human-readable error message.
- **FR-004**: The system MUST reconcile the UI with server-confirmed data after each mutation settles (success or failure), replacing any temporary or placeholder data.
- **FR-005**: The system MUST support a board status change operation that updates an item's status, requiring a new backend endpoint to process these requests.
- **FR-006**: The system MUST handle concurrent optimistic mutations independently, so that the failure of one mutation does not affect the state of other in-flight mutations.
- **FR-007**: The system MUST use a snapshot-and-restore approach, capturing the current UI state before each mutation and restoring it on failure.
- **FR-008**: Optimistically created items (e.g., new chores, new apps) MUST be visually distinguishable from server-confirmed items during the pending period (e.g., reduced opacity or a subtle pending indicator).
- **FR-009**: Optimistic updates for update and delete operations SHOULD NOT require visual distinction from confirmed state, as the change is small and brief.
- **FR-010**: The system MUST NOT apply optimistic updates to excluded operations: chat mutations, trigger polling, pipeline save (which already uses a different loading-state mechanism), and long-running server operations (e.g., createWithAutoMerge).
- **FR-011**: The board status change endpoint MUST accept a status name and item identifier, resolve the status to the appropriate internal identifier, and return a minimal success/error response.
- **FR-012**: The system MUST invalidate and re-fetch relevant cached data after each mutation settles (success or failure) to ensure the UI is synchronized with the server.

### Key Entities

- **BoardItem**: Represents a single item on the project board. Key attributes include item identifier, title, current status, assignees, priority, and size. Participates in drag-and-drop status changes.
- **BoardColumn**: Represents a column on the project board, grouping items by status. Contains a status label and an ordered list of board items.
- **BoardDataResponse**: The complete board view including project metadata, all columns with their items, and rate-limit information. This is the primary data shape cached and optimistically updated for board operations.
- **Chore**: A task item with title, description, status, and timestamps. Subject to create, update, inline-update, and delete mutations.
- **App**: An application entry with name, description, status (running/stopped), and configuration. Subject to create, update, delete, start, and stop mutations.
- **Tool**: A tool entry with name, description, and configuration. Subject to delete mutations.
- **Pipeline**: A pipeline configuration entry. Subject to delete mutations.
- **Mutation Snapshot**: A transient in-memory copy of the cached data taken immediately before an optimistic update. Used exclusively for rollback if the mutation fails. Not persisted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users perceive board drag-and-drop status changes as instant — the card visually moves to the target column within 100 milliseconds of being dropped, regardless of network latency.
- **SC-002**: All 14 supported mutation operations (1 board status, 4 chore, 5 app, 1 tool delete, 1 pipeline delete, plus inline chore update and board wiring) reflect changes in the UI before the server responds.
- **SC-003**: 100% of failed mutations (server error or network failure) revert the UI cleanly to the previous state with no orphaned or inconsistent data visible to the user.
- **SC-004**: 100% of failed mutations display a user-facing error notification within 2 seconds of the failure.
- **SC-005**: After every successful mutation, the UI data matches the server-confirmed state once reconciliation completes — no stale placeholder data remains.
- **SC-006**: Existing automated test suites (unit and end-to-end) continue to pass with no regressions introduced by the optimistic update changes.
- **SC-007**: Rapid sequential mutations (e.g., creating 5 chores in quick succession) all resolve correctly — each item appears optimistically and is reconciled individually.
- **SC-008**: Users can perform optimistic actions with zero additional page loads or full-page refreshes compared to the current behavior.

## Assumptions

- The existing cache management library (TanStack Query) supports the snapshot-restore pattern natively via `onMutate`, `onError`, and `onSettled` callbacks, and no additional libraries are needed.
- The existing backend service function for updating item status by name is functional and can be reused by the new endpoint without modification.
- Error toasts are already implemented in the application (the current mutation hooks use `toast.error()`) and can be reused for optimistic rollback notifications.
- The board status change endpoint will return a minimal response (success/error) rather than the full board data, since the settled-phase re-fetch handles data reconciliation.
- Optimistic update logic will reside in the mutation hook callbacks (not in separate state management), keeping the architecture consistent with the existing pattern.
- Pipeline save and createWithAutoMerge are explicitly excluded because they already have dedicated loading-state handling via `useReducer` and long-running operation patterns, respectively.
- Chat mutations are excluded because they have different real-time update patterns that would conflict with optimistic updates.

## Scope Boundaries

### In Scope

- All user-initiated CRUD and status-change mutations across chores, apps, tools, pipelines, and the board (14 mutations total)
- One new backend endpoint for board item status changes
- One new frontend API method for the board status endpoint
- Snapshot-and-restore rollback pattern for all mutations
- Error notification on mutation failure
- Data reconciliation (re-fetch) on mutation settlement
- Visual pending indicator for newly created items

### Out of Scope

- Chat mutations (different real-time pattern)
- Trigger polling operations
- Pipeline save (already uses `useReducer`-based loading state)
- `createWithAutoMerge` (long-running server operation)
- Offline-first or queue-based mutation strategies
- Retry logic for failed mutations (users can manually retry)
- Changes to the drag-and-drop hook itself (it already calls the status update callback)

## Dependencies

- The board drag-and-drop hook (`useBoardDragDrop`) already invokes a status update callback on drag end — this specification assumes that contract remains stable.
- The existing backend function `update_item_status_by_name()` resolves status names to internal identifiers — the new endpoint depends on this function.
- Toast notification infrastructure is already in place across all mutation hooks.
- Cache key patterns for board data, chores, apps, tools, and pipelines are already established and will be reused.
