# Feature Specification: Optimistic Updates for Mutations

**Feature Branch**: `001-optimistic-updates-mutations`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Add optimistic UI updates to the 4 mutations missing them, and fix the paginated cache gap where existing optimistic updates only target flat array caches while the UI has migrated to useInfiniteQuery."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Instant Feedback on Agent Creation (Priority: P1)

A user creates a new agent from the agents list page. Today, after clicking "Create", the user sees no change in the list until the server responds, which can take several seconds. With this feature, the new agent appears immediately in the agents list as soon as the user submits the creation form, providing instant visual confirmation that their action was received.

**Why this priority**: Agent creation is one of the four mutations completely missing optimistic updates. Agents are a core entity, and the lack of immediate feedback creates a perceived performance gap compared to other entity types (chores, apps) that already have optimistic behavior.

**Independent Test**: Can be fully tested by creating an agent and verifying it appears in the list instantly before the server confirms, and delivers immediate visual feedback to the user.

**Acceptance Scenarios**:

1. **Given** a user is viewing the agents list, **When** they submit the create agent form, **Then** the new agent appears in the list immediately without waiting for the server response.
2. **Given** a user creates an agent and the server confirms success, **When** the server response arrives, **Then** the list reflects the server-confirmed data (e.g., server-assigned ID) without any visual flicker or duplication.
3. **Given** a user creates an agent but the server returns an error, **When** the error is received, **Then** the optimistically added agent is removed from the list, the list reverts to its previous state, and the user sees an error notification.

---

### User Story 2 - Instant Feedback on Agent Deletion (Priority: P1)

A user deletes an agent from the agents list. Today, the agent remains visible in the list until the server confirms deletion. With this feature, the agent disappears from the list immediately when the user confirms deletion, providing instant feedback.

**Why this priority**: Agent deletion is another mutation missing optimistic updates entirely. Paired with agent creation, completing both ensures the full agent lifecycle has consistent instant-feedback behavior.

**Independent Test**: Can be fully tested by deleting an agent and verifying it disappears from the list instantly, and delivers immediate visual feedback confirming the deletion action.

**Acceptance Scenarios**:

1. **Given** a user is viewing the agents list with multiple agents, **When** they confirm deletion of an agent, **Then** the agent is removed from the list immediately without waiting for server confirmation.
2. **Given** a user deletes an agent and the server confirms success, **When** the server response arrives, **Then** the list remains in its current state with no visual disruption.
3. **Given** a user deletes an agent but the server returns an error, **When** the error is received, **Then** the deleted agent reappears in the list at its original position and the user sees an error notification.

---

### User Story 3 - Instant Feedback on Tool Upload (Priority: P1)

A user uploads a new tool from the tools page. Today, after uploading, there is no immediate feedback — the tool does not appear in the list and no error notification is shown if the upload fails. With this feature, the uploaded tool appears in the tools list immediately and the user is notified if an error occurs.

**Why this priority**: Tool upload is missing both optimistic updates and error notifications, making it the most incomplete mutation in terms of user feedback. Users currently have no way of knowing whether their upload succeeded or failed without manually refreshing.

**Independent Test**: Can be fully tested by uploading a tool and verifying it appears in the tools list instantly, and that an error toast is displayed if the upload fails.

**Acceptance Scenarios**:

1. **Given** a user is viewing the tools list, **When** they upload a new tool, **Then** the tool appears in the list immediately with a placeholder or pending indicator.
2. **Given** a user uploads a tool and the server confirms success, **When** the server response arrives, **Then** the list updates with the server-confirmed tool data seamlessly.
3. **Given** a user uploads a tool but the server returns an error, **When** the error is received, **Then** the optimistically added tool is removed from the list, the list reverts to its previous state, and the user sees an error notification toast.

---

### User Story 4 - Instant Feedback on Project Creation (Priority: P1)

A user creates a new project. Today, the project does not appear in the projects list until the server responds. With this feature, the new project appears immediately in the list upon creation.

**Why this priority**: Project creation completes the set of four mutations missing optimistic updates. Consistent instant-feedback behavior across all entity creation flows is important for a cohesive user experience.

**Independent Test**: Can be fully tested by creating a project and verifying it appears in the projects list instantly before server confirmation.

**Acceptance Scenarios**:

1. **Given** a user is viewing the projects list, **When** they submit the create project form, **Then** the new project appears in the list immediately without waiting for server response.
2. **Given** a user creates a project and the server confirms success, **When** the server response arrives, **Then** the list reflects server-confirmed data without visual flicker or duplication.
3. **Given** a user creates a project but the server returns an error, **When** the error is received, **Then** the optimistically added project is removed from the list, the list reverts to its previous state, and the user sees an error notification.

---

### User Story 5 - Paginated List Consistency (Priority: P2)

A user is browsing a paginated list of entities (agents, chores, apps, tools, or projects) and performs a create, update, or delete action. Today, existing optimistic updates only modify a flat array cache, but the UI has migrated to paginated (infinite scroll) queries. This means optimistic updates may not reflect correctly in the visible list — users might not see their change until they scroll or refresh. With this feature, all optimistic updates correctly target the paginated cache structure so that changes are immediately visible regardless of which page the user is viewing.

**Why this priority**: This is a systemic issue affecting all existing optimistic updates, not just the four new ones. Without fixing the paginated cache gap, even the new optimistic updates added in Stories 1–4 would not display correctly in paginated views. However, it is P2 because the four missing mutations (P1) represent a complete absence of feedback, whereas the paginated gap is a degradation of existing functionality.

**Independent Test**: Can be fully tested by performing a mutation (e.g., creating a chore) while viewing a paginated list and verifying the change appears in the currently visible page without scrolling or refreshing.

**Acceptance Scenarios**:

1. **Given** a user is viewing page 1 of a paginated entity list, **When** they create a new entity, **Then** the new entity appears on the appropriate page (typically the first page or last page depending on sort order) immediately.
2. **Given** a user is viewing page 2 of a paginated entity list, **When** they delete an entity from page 2, **Then** the entity disappears from page 2 immediately without requiring a page refresh or scroll.
3. **Given** a user performs a mutation on a paginated list and the server confirms, **When** the server response arrives, **Then** the paginated cache is reconciled correctly — no duplicate entries, no missing entries, and correct page boundaries.
4. **Given** a user performs a mutation on a paginated list but the server returns an error, **When** the error is received, **Then** the paginated cache reverts to its pre-mutation state across all loaded pages.

---

### Edge Cases

- What happens when a user creates an entity while the list is still loading its initial data?
- What happens when a user performs multiple rapid mutations (e.g., creating three agents in quick succession) before any server responses return?
- What happens when the user creates an entity and immediately navigates away from the list page before the server responds?
- What happens when the server response for a mutation returns data that significantly differs from the optimistic placeholder (e.g., server modifies the entity name)?
- How does the system handle optimistic updates when the user's session has expired or the network is disconnected?
- What happens when a user deletes the last entity on a paginated page — does the page collapse correctly?
- What happens when an optimistic create triggers a new page to be needed in the paginated cache?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display newly created agents in the agents list immediately upon form submission, before server confirmation.
- **FR-002**: System MUST remove deleted agents from the agents list immediately upon deletion confirmation, before server confirmation.
- **FR-003**: System MUST display newly uploaded tools in the tools list immediately upon upload initiation, before server confirmation.
- **FR-004**: System MUST display an error notification toast when a tool upload fails.
- **FR-005**: System MUST display newly created projects in the projects list immediately upon form submission, before server confirmation.
- **FR-006**: System MUST revert the list to its previous state when any optimistic mutation fails (server error, network error, or timeout).
- **FR-007**: System MUST reconcile optimistic data with server-confirmed data upon successful server response, replacing temporary/placeholder values with server-assigned values (e.g., IDs, timestamps).
- **FR-008**: System MUST correctly update paginated (infinite scroll) cache structures for all optimistic mutations — including both the four new mutations and all pre-existing optimistic mutations.
- **FR-009**: System MUST ensure no duplicate entries appear in any list after optimistic data is reconciled with server-confirmed data.
- **FR-010**: System MUST preserve scroll position and visible page state when optimistic updates are applied to paginated lists.
- **FR-011**: System MUST handle rapid sequential mutations correctly — each optimistic update must be independently reversible without affecting other pending mutations.
- **FR-012**: System MUST display error notifications for failed mutations on agent creation, agent deletion, tool upload, and project creation, consistent with existing error notification patterns used for other entity mutations.

### Key Entities

- **Agent**: A configurable AI agent entity. Users can create and delete agents. Agents appear in a paginated list view.
- **Tool**: An uploadable utility/plugin. Users can upload new tools. Tools appear in a paginated list view. Currently missing error feedback on upload failure.
- **Project**: A workspace container for organizing work. Users can create projects. Projects appear in a paginated list view.
- **Paginated Cache**: The client-side data structure (infinite query pages) that stores entity lists across multiple pages. Must be updated atomically during optimistic mutations.

## Assumptions

- Optimistic updates for agent creation and deletion will follow the same patterns already established by chore and app create/update/delete mutations.
- The paginated cache structure follows a standard pages-based infinite query pattern where each page contains an array of entities.
- Error notifications will use the same toast/notification system already in use for other mutation errors.
- Temporary/placeholder data used during optimistic creates will include enough information to render the entity in the list (e.g., user-provided name, a temporary ID).
- The undoable delete pattern already handling paginated cache correctly can serve as a reference implementation for the paginated cache update logic.
- Sort order for new entities follows the existing default sort behavior of each list (e.g., newest first or alphabetical).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four previously missing mutations (agent create, agent delete, tool upload, project create) provide instant visual feedback — the entity list updates within 100 milliseconds of user action, before server response.
- **SC-002**: 100% of optimistic mutations correctly revert on server error — no stale or phantom entries remain in any list after a failed mutation.
- **SC-003**: All entity list views using paginated/infinite scroll correctly reflect optimistic updates — users see changes on the current page without needing to scroll, refresh, or navigate away and back.
- **SC-004**: Zero duplicate entries appear in any entity list after optimistic data is reconciled with server-confirmed data.
- **SC-005**: Users receive an error notification for every failed mutation across all entity types, including the previously missing error toast for tool upload failures.
- **SC-006**: Rapid sequential mutations (3 or more within 2 seconds) are handled correctly — each mutation is independently reflected and independently reversible.
