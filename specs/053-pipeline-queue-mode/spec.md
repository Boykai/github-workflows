# Feature Specification: Pipeline Queue Mode Toggle

**Feature Branch**: `053-pipeline-queue-mode`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "Add a per-project Queue Mode toggle to the Project Board toolbar that enforces sequential pipeline execution — only one parent issue's agent pipeline runs at a time. When ON, newly launched pipelines create the issue and sub-issues on the board but hold in Backlog without assigning any agent. When the active pipeline's parent issue reaches In Review or Done/Closed (whichever comes first), the next queued issue's pipeline automatically starts."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enable Queue Mode on a Project (Priority: P1)

A project manager opens their Project Board and toggles "Queue Mode" ON in the toolbar. From this point forward, only one pipeline runs at a time for that project. When a new pipeline is launched while another is already active, the new pipeline's issue and sub-issues appear on the board in the Backlog column, but no agent is assigned. The board visually indicates that the pipeline is queued.

**Why this priority**: This is the core interaction — without the ability to turn queue mode on, no other functionality works. It establishes the fundamental constraint that only one pipeline runs concurrently per project.

**Independent Test**: Can be fully tested by toggling the setting ON in the toolbar and verifying the setting is persisted. Delivers the foundation for all queue behavior.

**Acceptance Scenarios**:

1. **Given** a Project Board with Queue Mode OFF, **When** the user clicks the Queue Mode toggle in the toolbar, **Then** the toggle switches to ON, the setting is persisted to the project's configuration, and a tooltip confirms "Only one pipeline runs at a time — next starts when active reaches In Review or Done."
2. **Given** Queue Mode is ON, **When** the user clicks the Queue Mode toggle again, **Then** the toggle switches to OFF and the setting is persisted. Any currently queued pipelines remain in their current state.
3. **Given** Queue Mode is ON, **When** the user navigates away and returns to the project, **Then** the toggle reflects the persisted ON state.

---

### User Story 2 - Automatic Pipeline Queueing (Priority: P1)

A user has Queue Mode enabled and launches a pipeline while another pipeline is already active. The system creates the new issue and its sub-issues on the board in the Backlog column but does not assign an agent. The pipeline is held in a "Queued" state. The user sees a "Queued" badge on the issue card and a toast notification indicating the pipeline's queue position.

**Why this priority**: This is the primary functional behavior of queue mode — without queueing, the toggle is meaningless. Users must see clear feedback that their pipeline is queued, not lost.

**Independent Test**: Can be tested by enabling Queue Mode, launching one pipeline (which starts immediately), then launching a second pipeline and verifying it appears in Backlog with no agent and a "Queued" badge. The launch toast should display the queue position.

**Acceptance Scenarios**:

1. **Given** Queue Mode is ON and no pipeline is currently active, **When** the user launches a new pipeline, **Then** the pipeline starts immediately with an agent assigned (identical to current behavior).
2. **Given** Queue Mode is ON and one pipeline is already active, **When** the user launches a second pipeline, **Then** the second pipeline's issue and sub-issues are created on the board in Backlog, no agent is assigned, the pipeline state is marked as queued, and a "Queued" badge appears on the issue card.
3. **Given** Queue Mode is ON and one pipeline is active, **When** the user launches a second pipeline, **Then** a toast notification displays "Pipeline queued — position #N" indicating the queue position.
4. **Given** Queue Mode is ON and multiple pipelines are queued, **When** the user launches another pipeline, **Then** it is placed at the end of the queue with the correct position number.

---

### User Story 3 - Automatic Pipeline Dequeuing (Priority: P1)

When the active pipeline's parent issue reaches "In Review" or "Done/Closed" (whichever comes first), the system automatically starts the next queued pipeline in FIFO order by assigning an agent and beginning polling.

**Why this priority**: Dequeuing completes the queue lifecycle. Without automatic dequeuing, users would need to manually trigger each pipeline, negating the value of the feature.

**Independent Test**: Can be tested by enabling Queue Mode, launching two pipelines (first starts, second queues), then completing the first pipeline (moving it to In Review or Done). Verify the second pipeline automatically starts with an agent assigned.

**Acceptance Scenarios**:

1. **Given** Queue Mode is ON, one pipeline is active, and one pipeline is queued, **When** the active pipeline's parent issue reaches "In Review," **Then** the queued pipeline automatically starts — an agent is assigned and polling begins.
2. **Given** Queue Mode is ON, one pipeline is active, and one pipeline is queued, **When** the active pipeline's parent issue reaches "Done/Closed," **Then** the queued pipeline automatically starts.
3. **Given** Queue Mode is ON and multiple pipelines are queued, **When** the active pipeline completes, **Then** the oldest queued pipeline (by launch time, FIFO) starts next.
4. **Given** Queue Mode is ON and the active pipeline completes, **When** there are no queued pipelines, **Then** no action is taken and the system returns to an idle state.

---

### User Story 4 - Queue Mode OFF Preserves Existing Behavior (Priority: P2)

When Queue Mode is OFF (the default), all pipelines launch immediately with agents assigned, exactly as the system works today. Toggling Queue Mode OFF does not affect currently queued or active pipelines.

**Why this priority**: Backward compatibility is essential. Existing users who do not use Queue Mode must experience no change in behavior.

**Independent Test**: Can be tested by verifying that with Queue Mode OFF (default), launching multiple pipelines all start immediately with agents assigned, matching current behavior.

**Acceptance Scenarios**:

1. **Given** Queue Mode is OFF (default), **When** the user launches multiple pipelines, **Then** all pipelines start immediately with agents assigned (existing behavior).
2. **Given** Queue Mode is ON with queued pipelines, **When** the user toggles Queue Mode OFF, **Then** the queued pipelines remain in their current state (they do not auto-start or get removed).

---

### User Story 5 - Visual Queue Status on Board (Priority: P2)

Users can see at a glance which issue cards on the board represent queued pipelines. A distinct "Queued" badge with a clock/queue icon appears on issue cards whose pipeline is in the queued state.

**Why this priority**: Visual feedback is important for usability but is secondary to the core queueing mechanics. Users need to distinguish queued pipelines from active or unrelated issues.

**Independent Test**: Can be tested by enabling Queue Mode, launching a pipeline while another is active, and verifying the queued pipeline's issue card displays the "Queued" badge.

**Acceptance Scenarios**:

1. **Given** an issue card on the board whose pipeline is in the queued state, **When** the board renders, **Then** the issue card displays a "Queued" badge with a clock or queue icon.
2. **Given** a queued pipeline that transitions to active (agent assigned), **When** the board re-renders, **Then** the "Queued" badge is removed from the issue card.

---

### Edge Cases

- What happens when Queue Mode is toggled OFF while pipelines are queued? — Queued pipelines remain in their current state; they do not auto-start or get removed. Users can manually manage them.
- What happens if the active pipeline errors out or stalls indefinitely? — The slot is released when the pipeline's parent issue reaches "In Review" or "Done/Closed." If neither status is reached, the queue remains blocked. Future enhancements may add timeout-based release, but this is out of scope for the initial release.
- What happens if two pipelines reach "In Review" or "Done" simultaneously in a race condition? — The dequeue operation processes one pipeline at a time. The first to trigger the dequeue check wins; subsequent triggers are no-ops if no queued pipelines remain.
- What happens if a queued pipeline's issue is manually deleted or moved? — The pipeline state is cleaned up as part of normal issue lifecycle handling. The next queued pipeline (if any) is promoted.
- What if a project has queue mode enabled but only one pipeline is launched? — It starts immediately, identical to behavior without queue mode.
- What happens when Queue Mode is enabled on a project with no pipelines? — The toggle persists the setting. No pipelines are affected until the next launch.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a per-project toggle labeled "Queue Mode" in the Project Board toolbar that persists the setting across sessions.
- **FR-002**: System MUST enforce that only one pipeline runs at a time per project when Queue Mode is enabled.
- **FR-003**: When Queue Mode is ON and a pipeline is launched while another is active, the system MUST create the new issue and sub-issues on the board in the Backlog column without assigning an agent.
- **FR-004**: When Queue Mode is ON and a pipeline is queued, the system MUST mark the pipeline state as "queued" and display a "Queued" badge on the corresponding issue card.
- **FR-005**: When the active pipeline's parent issue reaches "In Review" or "Done/Closed" (whichever comes first), the system MUST automatically start the next queued pipeline in FIFO order by assigning an agent and beginning the polling cycle.
- **FR-006**: System MUST display a toast notification with the queue position (e.g., "Pipeline queued — position #N") when a pipeline is queued.
- **FR-007**: System MUST default Queue Mode to OFF for all projects, preserving existing immediate-launch behavior.
- **FR-008**: System MUST remove the "Queued" badge from an issue card when its pipeline transitions from queued to active.
- **FR-009**: Toggling Queue Mode OFF MUST NOT affect currently queued or active pipelines; they remain in their current state.
- **FR-010**: The Queue Mode toggle MUST display a tooltip explaining the behavior: "Only one pipeline runs at a time — next starts when active reaches In Review or Done."
- **FR-011**: The Queue Mode setting MUST be scoped per project — each project maintains its own independent queue mode state.

### Key Entities *(include if feature involves data)*

- **Project Settings**: The existing project configuration entity, extended with a queue mode flag (on/off). Scoped per project. Determines whether sequential pipeline execution is enforced.
- **Pipeline State**: The existing entity tracking an active pipeline's lifecycle, extended with a queued status. Indicates whether the pipeline is actively running or waiting in the queue.
- **Queue Position**: A derived concept (not a stored entity) representing a pipeline's order in the queue, calculated from the launch timestamp using FIFO ordering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can enable or disable Queue Mode for a project in under 2 seconds via a single click on the toolbar toggle.
- **SC-002**: When Queue Mode is ON, only one pipeline per project has an assigned agent at any given time.
- **SC-003**: Queued pipelines automatically start within 30 seconds of the active pipeline's parent issue reaching "In Review" or "Done/Closed."
- **SC-004**: Users can identify queued pipelines at a glance via the "Queued" badge on issue cards, achieving 100% visual accuracy (badge present on all queued pipelines, absent on all non-queued items).
- **SC-005**: Existing behavior is fully preserved when Queue Mode is OFF — no regressions in pipeline launch speed or agent assignment.
- **SC-006**: Queue position is accurately communicated to users via toast notification at launch time.
- **SC-007**: The Queue Mode setting persists across page refreshes and browser sessions with 100% reliability.

### Assumptions

- The existing `project_settings` storage is suitable for persisting the queue mode flag without schema changes beyond adding a column.
- The existing pipeline state tracking mechanism can accommodate a "queued" boolean flag.
- The polling loop that detects "In Review" and "Done/Closed" statuses is the appropriate place to trigger dequeue operations.
- FIFO ordering by launch timestamp provides sufficient fairness for queue ordering.
- The initial release does not include timeout-based queue release for stalled pipelines; this may be addressed in a future iteration.
- Race conditions during dequeue are handled by the existing single-threaded or serialized pipeline processing model.
