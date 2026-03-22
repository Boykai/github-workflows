# Feature Specification: Phase 8 Feature Enhancements — Polling, UX, Board Projection, Concurrency, Collision Fix, Undo/Redo

**Feature Branch**: `001-phase8-enhancements`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "As a platform engineer and board user, I want adaptive polling, concurrent pipeline execution, lazy-loaded board data, label-driven state recovery, MCP collision resolution, and consistent undo/redo for destructive actions so that the system is more efficient, resilient, and intuitive across all entity management workflows."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Adaptive Polling (Priority: P1)

As a board user viewing a project board, I want the system to poll for updates at a frequency that adapts to how active the board is, so that I see near-real-time changes when work is happening and the system conserves resources when activity is low.

When a board is actively receiving updates (items moving, labels changing, pipelines running), polling should increase in frequency so users see fresh data quickly. When no changes are detected over a sustained period, polling should slow down to reduce unnecessary load. If a user navigates away and returns, polling should resume at an appropriate pace based on current activity.

**Why this priority**: Polling is the foundation for all real-time data freshness across the platform. Inefficient polling causes either stale data (users see outdated board state) or wasted resources (excessive requests with no new data). Fixing this first improves every subsequent feature's perceived responsiveness.

**Independent Test**: Can be fully tested by observing polling behavior on a board with varying levels of activity. Delivers value by ensuring users always see timely data without overloading the system.

**Acceptance Scenarios**:

1. **Given** a board with active pipeline runs, **When** items are being updated frequently, **Then** the polling interval decreases so users see changes within a short window (target: updates visible within 5 seconds of occurrence).
2. **Given** a board with no recent changes for several minutes, **When** the system detects inactivity, **Then** the polling interval increases gradually to conserve resources.
3. **Given** a user returns to a previously idle board tab, **When** the tab regains focus, **Then** the system immediately performs a fresh poll and resets the adaptive interval based on current activity.
4. **Given** the polling subsystem encounters transient network errors, **When** a poll request fails, **Then** the system retries with exponential backoff and does not flood the server with rapid retries.

---

### User Story 2 — Concurrent Pipeline Execution (Priority: P1)

As a platform engineer, I want to execute multiple pipelines concurrently for the same project so that independent workflows do not block each other and total processing time is reduced.

Currently, pipelines may execute sequentially even when they have no dependencies on one another. Concurrent execution allows independent pipelines (e.g., label sync, field updates, status transitions) to run in parallel, reducing end-to-end wait times for users watching board state converge.

**Why this priority**: Sequential pipeline execution is a throughput bottleneck. Enabling concurrency directly reduces the time between a user action and the board reaching its final state, which improves overall user satisfaction and system efficiency.

**Independent Test**: Can be fully tested by triggering two or more independent pipelines for the same project and verifying they run simultaneously rather than waiting for each other. Delivers value by reducing total pipeline processing time.

**Acceptance Scenarios**:

1. **Given** a project with two independent pipelines configured, **When** both are triggered at the same time, **Then** both pipelines begin execution concurrently rather than one waiting for the other to finish.
2. **Given** two pipelines are running concurrently, **When** one pipeline fails, **Then** the other pipeline continues to completion unaffected.
3. **Given** concurrent pipelines modify different entities, **When** both complete, **Then** all changes are applied correctly and the board reflects the combined results.
4. **Given** a project has a queue-mode setting enabled, **When** pipelines are triggered, **Then** the system respects the queue-mode serialization constraint and does not run them concurrently (backward compatibility).

---

### User Story 3 — Board Projection with Lazy Loading (Priority: P2)

As a board user working with a large project board (hundreds of items), I want the board to load only the data I need to see initially and fetch additional data as I scroll or interact, so that the board loads quickly and remains responsive.

Large boards currently load all data upfront, leading to slow initial render times. Lazy loading (board projection) means the system first delivers a lightweight view of visible items and loads details, off-screen items, and historical data on demand.

**Why this priority**: Initial load performance directly impacts user satisfaction. Users with large boards experience the most friction, and lazy loading delivers a dramatic improvement in perceived speed without requiring changes to the underlying data model.

**Independent Test**: Can be fully tested by loading a board with a large number of items and measuring initial load time versus full data availability over time. Delivers value by making large boards usable within seconds.

**Acceptance Scenarios**:

1. **Given** a project board with hundreds of items, **When** a user opens the board, **Then** the initial visible set of items renders within 2 seconds.
2. **Given** a board is displaying its initial projection, **When** the user scrolls to view additional items, **Then** those items load seamlessly without a noticeable loading delay (target: under 500 milliseconds per batch).
3. **Given** a board using lazy loading, **When** a user applies a filter or search, **Then** the system queries the full dataset (not just the loaded projection) and returns accurate results.
4. **Given** a board with lazy-loaded data, **When** the user navigates away and returns, **Then** previously loaded data is served from a local cache and only deltas are fetched.

---

### User Story 4 — Pipeline Config Filter in Board Toolbar (Priority: P2)

As a board user managing multiple pipeline configurations, I want a filter dropdown in the board toolbar that lets me filter the board view by pipeline configuration, so that I can focus on items relevant to a specific workflow.

The board toolbar should include a pipeline config filter dropdown that enables client-side filtering. When a pipeline is selected, only items associated with that pipeline are displayed. Selecting "All Pipelines" (the default) shows everything.

**Why this priority**: Users managing multiple pipelines on a single board waste time scanning irrelevant items. A simple filter control significantly improves focus and task efficiency without requiring backend changes.

**Independent Test**: Can be fully tested by opening a board with multiple pipeline configurations, using the dropdown to select different pipelines, and verifying that the board view updates accordingly. Delivers value by letting users focus on one workflow at a time.

**Acceptance Scenarios**:

1. **Given** a board with multiple pipeline configurations, **When** the user opens the board toolbar, **Then** a pipeline config filter dropdown is visible and lists all available pipeline configurations plus an "All Pipelines" option.
2. **Given** the filter dropdown is set to a specific pipeline, **When** the user selects it, **Then** only board items associated with that pipeline are displayed and items from other pipelines are hidden.
3. **Given** the filter is set to a specific pipeline, **When** the user selects "All Pipelines," **Then** all items across all pipelines are displayed.
4. **Given** the user has selected a pipeline filter, **When** the board receives new data via polling, **Then** the filter remains applied and only relevant new items appear.

---

### User Story 5 — Label-Driven State Recovery (Priority: P2)

As a platform engineer, I want the system to recover the last known pipeline state from item labels when the system restarts or encounters data loss, so that workflows resume correctly without requiring manual re-configuration.

Labels on board items encode the current pipeline state (e.g., stage, status). If the system's internal state is lost (due to a restart, cache eviction, or data corruption), the system should be able to read labels from the source of truth (the project board) and reconstruct its internal state accordingly.

**Why this priority**: System resilience is critical. Without state recovery, any restart or data loss forces manual intervention to re-align the system with the actual board state. Label-driven recovery automates this, reducing downtime and operational burden.

**Independent Test**: Can be fully tested by simulating a system restart, clearing internal state, and verifying that the system reconstructs its state from labels on board items. Delivers value by eliminating manual recovery steps after system disruptions.

**Acceptance Scenarios**:

1. **Given** the system's internal pipeline state has been lost (e.g., after a restart), **When** the system starts up, **Then** it reads labels from all project board items and reconstructs the pipeline state for each item.
2. **Given** an item has labels reflecting a mid-pipeline state, **When** state recovery runs, **Then** the item is placed at the correct stage in the pipeline and the pipeline can resume from that point.
3. **Given** an item has conflicting or missing labels, **When** state recovery encounters ambiguity, **Then** the system logs a warning, marks the item for manual review, and does not apply an incorrect state.
4. **Given** state recovery has completed, **When** the system resumes normal polling and pipeline execution, **Then** no duplicate actions are performed on items whose state was recovered.

---

### User Story 6 — MCP Collision Resolution (Priority: P3)

As a platform engineer, I want the system to detect and resolve collisions when multiple MCP (Model Context Protocol) operations attempt to modify the same entity simultaneously, so that data integrity is preserved and users are not left with conflicting or corrupted state.

When concurrent operations target the same entity (e.g., two pipelines trying to move the same item, or a user action conflicting with an automated pipeline action), the system must detect the collision and apply a deterministic resolution strategy rather than silently overwriting or producing an error.

**Why this priority**: Collisions are rare in single-pipeline setups but become increasingly likely with concurrent execution (Story 2). Resolving them gracefully is essential for data integrity but is a lower priority than enabling concurrency itself, since initial deployment can use conservative locking.

**Independent Test**: Can be fully tested by triggering two concurrent operations that target the same entity and verifying that the system detects the conflict and applies the correct resolution. Delivers value by preventing data corruption in concurrent scenarios.

**Acceptance Scenarios**:

1. **Given** two concurrent operations attempt to modify the same board item, **When** the system detects a collision, **Then** it applies a deterministic resolution (last-write-wins with timestamp, or operation priority rules) and the final item state is consistent.
2. **Given** a collision is detected and resolved, **When** the resolution completes, **Then** the system logs the collision event including both operations and the resolution outcome for auditability.
3. **Given** a collision occurs between a user-initiated action and an automated pipeline action, **When** the system resolves it, **Then** the user-initiated action takes precedence by default (user intent over automation).
4. **Given** a collision cannot be automatically resolved (e.g., contradictory state transitions), **When** automatic resolution fails, **Then** the system marks the item as requiring manual review and notifies the relevant user.

---

### User Story 7 — Undo/Redo for Destructive Actions (Priority: P3)

As a board user, I want to undo destructive actions (such as deleting items, removing labels, or archiving cards) and redo them if I change my mind, so that I can recover from mistakes without needing administrative intervention.

Destructive actions should be reversible for a reasonable window of time. The system should maintain an undo stack for the current session, allowing users to reverse their most recent destructive actions. A redo capability allows re-applying a previously undone action.

**Why this priority**: Undo/redo is a standard UX expectation for destructive operations. While important for user confidence, it is lower priority than system resilience and performance features because workarounds exist (manual re-creation, admin recovery).

**Independent Test**: Can be fully tested by performing a destructive action, undoing it, verifying the item is restored, and then redoing it to verify it is removed again. Delivers value by giving users confidence to take actions without fear of irreversible mistakes.

**Acceptance Scenarios**:

1. **Given** a user performs a destructive action (e.g., archives a board item), **When** the user clicks "Undo" within the undo window, **Then** the action is reversed and the item is restored to its previous state.
2. **Given** a user has undone a destructive action, **When** the user clicks "Redo," **Then** the destructive action is re-applied.
3. **Given** a user performs multiple destructive actions in sequence, **When** the user clicks "Undo" multiple times, **Then** each action is reversed in reverse chronological order (last action undone first).
4. **Given** a user performs a destructive action and the undo window expires, **When** the user attempts to undo, **Then** the system informs the user that the undo window has passed and provides guidance on alternative recovery options.
5. **Given** a user performs a destructive action and then performs a new non-undo action, **When** the user checks the redo stack, **Then** the redo stack is cleared (standard undo/redo behavior).

---

### Edge Cases

- What happens when the system transitions from high-activity to low-activity polling and a burst of updates arrives during the transition? The system should detect the burst and re-accelerate polling immediately.
- How does lazy loading behave when a user rapidly scrolls through hundreds of items? The system should debounce scroll events and prioritize loading the final scroll position.
- What happens when two users simultaneously trigger conflicting pipeline filter selections? Since filtering is client-side, each user's filter is independent; no server-side conflict exists.
- What happens when label-driven state recovery encounters labels from an older, incompatible pipeline configuration version? The system should detect version mismatches, skip incompatible labels, and log a warning.
- What happens when a user undoes an action that was already superseded by an automated pipeline update? The undo should restore the user's intended state and log a note that the automated update was overridden.
- How does the undo window interact with polling updates? Undo actions operate on the user's action stack and are independent of server-side polling updates; however, if the server state has diverged significantly, the undo should warn the user.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST adjust polling frequency dynamically based on detected activity levels on the board (higher frequency during active periods, lower during idle periods).
- **FR-002**: The system MUST resume an immediate poll and reset the adaptive interval when the user's browser tab regains focus after being backgrounded.
- **FR-003**: The system MUST apply exponential backoff when poll requests fail due to transient errors, preventing rapid retry floods.
- **FR-004**: The system MUST support concurrent execution of independent pipelines for the same project, so that non-dependent pipelines run in parallel.
- **FR-005**: The system MUST continue running unaffected pipelines when a concurrent pipeline fails (fault isolation).
- **FR-006**: The system MUST respect queue-mode settings; when queue mode is enabled for a project, pipelines MUST execute sequentially (backward compatibility).
- **FR-007**: The system MUST deliver an initial board projection (visible items) within 2 seconds for boards with up to 500 items.
- **FR-008**: The system MUST load additional board items on demand as the user scrolls, with each batch loading in under 500 milliseconds.
- **FR-009**: The system MUST apply filters and search queries against the full dataset, not just the currently loaded projection.
- **FR-010**: The board toolbar MUST include a pipeline configuration filter dropdown listing all available pipeline configurations and an "All Pipelines" default option.
- **FR-011**: Selecting a pipeline in the filter MUST hide items not associated with that pipeline (client-side filtering).
- **FR-012**: The selected pipeline filter MUST persist across polling updates within the same session.
- **FR-013**: The system MUST reconstruct internal pipeline state from item labels on startup when internal state is unavailable or corrupted.
- **FR-014**: State recovery MUST place each item at the correct pipeline stage based on its labels, enabling the pipeline to resume without re-processing.
- **FR-015**: When state recovery encounters ambiguous or conflicting labels, the system MUST log a warning and mark the item for manual review rather than applying an incorrect state.
- **FR-016**: After state recovery completes, the system MUST NOT perform duplicate actions on recovered items.
- **FR-017**: The system MUST detect collisions when concurrent operations target the same entity and apply a deterministic resolution strategy.
- **FR-018**: Collision resolution MUST prioritize user-initiated actions over automated pipeline actions by default.
- **FR-019**: All collision events MUST be logged with details of both operations and the resolution outcome.
- **FR-020**: When automatic collision resolution fails, the system MUST mark the entity for manual review and notify the responsible user.
- **FR-021**: The system MUST support undo for destructive actions (archive, delete, label removal) within a configurable time window.
- **FR-022**: The system MUST support redo to re-apply a previously undone destructive action.
- **FR-023**: Multiple undo operations MUST reverse actions in reverse chronological order (LIFO stack behavior).
- **FR-024**: Performing a new action after an undo MUST clear the redo stack (standard undo/redo semantics).
- **FR-025**: When the undo window expires, the system MUST inform the user and provide guidance on alternative recovery options.

### Key Entities

- **Polling Session**: Represents the adaptive polling state for a board view, including current interval, activity score, last poll timestamp, and backoff state.
- **Pipeline Execution**: Represents an individual pipeline run, including pipeline configuration reference, execution status, start time, and fault isolation boundary.
- **Board Projection**: Represents the lazily loaded subset of board data currently available in the client, including loaded item ranges, cache state, and pending fetch requests.
- **Pipeline Config Filter**: Represents the user's currently selected pipeline filter in the board toolbar, stored client-side per session.
- **Recovery State**: Represents the outcome of label-driven state recovery for an item, including source labels, reconstructed pipeline stage, confidence level, and any ambiguity flags.
- **Collision Event**: Represents a detected collision between concurrent operations, including the conflicting operations, target entity, resolution strategy applied, and outcome.
- **Action History Entry**: Represents a single entry in the undo/redo stack, including the action type, affected entity, previous state snapshot, new state, and timestamp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Board data freshness — users see updates within 5 seconds of occurrence during active periods, and polling resource usage decreases by at least 50% during idle periods compared to fixed-interval polling.
- **SC-002**: Total pipeline processing time for projects with 3+ independent pipelines decreases by at least 40% compared to sequential execution.
- **SC-003**: Initial board load time for boards with 500+ items is under 2 seconds (time to first meaningful content visible to the user).
- **SC-004**: Users can filter board items by pipeline configuration in under 2 interactions (open dropdown, select pipeline).
- **SC-005**: After a system restart with cleared internal state, 95% of items have their pipeline state correctly recovered from labels within 30 seconds of startup.
- **SC-006**: Zero data corruption incidents caused by concurrent operations over a 30-day observation period after launch.
- **SC-007**: Users can undo a destructive action within the configured time window with a 100% success rate (action fully reversed).
- **SC-008**: User-reported "accidental destructive action" support tickets decrease by at least 60% after undo/redo is available.

## Assumptions

- The existing polling infrastructure can be extended to support adaptive intervals without requiring a full architectural rewrite.
- Pipeline configurations already contain enough metadata to determine independence (no implicit dependencies that would prevent concurrent execution).
- Board items already carry labels that encode pipeline state information, and the label format is consistent enough to support automated state recovery.
- The board frontend supports virtualized or paginated rendering, enabling lazy loading without a complete UI rewrite.
- MCP operations already have identifiable timestamps or sequence numbers that can be used for collision detection.
- The undo time window defaults to 30 seconds, which balances recoverability with system complexity. This is configurable per deployment.
- Client-side pipeline filtering does not require backend changes; the board already receives pipeline configuration metadata with item data.
