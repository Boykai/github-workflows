# Feature Specification: Activity Log / Audit Trail

**Feature Branch**: `054-activity-audit-trail`  
**Created**: 2026-03-20  
**Status**: Draft  
**Input**: User description: "The backend already persists pipeline runs and cleanup operations with GET endpoints, but the frontend has zero UI to view them. Workflow transitions are in-memory only. Chore triggers and agent executions have no history at all. The notification bell returns an empty array — it's a placeholder. The fix: add a unified activity events table in the backend, persist all trackable actions into it, expose a paginated API, and build an Activity page + feed component in the frontend."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Unified Activity Feed (Priority: P1)

A user wants to see what has been happening across their project in one place. Today, pipeline runs are stored but invisible in the UI, chore triggers have no history at all, and CRUD operations on agents, apps, and tools leave no trace. The user needs a single, chronological Activity page that shows all significant events — pipeline runs, chore triggers, entity changes, webhook events, and cleanup operations — so they can understand what happened, when, and why.

**Why this priority**: Without a central activity feed, users have no visibility into system behavior. This is the foundational capability that every other story depends on. A working activity feed with persisted events is the minimum viable product for this feature.

**Independent Test**: Can be fully tested by performing several actions (running a pipeline, creating a chore, deleting an agent, triggering a webhook), then navigating to the Activity page and verifying that all actions appear in reverse-chronological order with accurate summaries.

**Acceptance Scenarios**:

1. **Given** a project where the user has run a pipeline, created a chore, and deleted an agent, **When** the user navigates to the Activity page, **Then** all three events appear in reverse-chronological order with human-readable summaries (e.g., "Pipeline 'deploy-prod' completed successfully", "Chore 'nightly-cleanup' created", "Agent 'code-reviewer' deleted").
2. **Given** the Activity page is open, **When** a new action occurs in the project (e.g., a pipeline run completes), **Then** the new event appears in the feed within 30 seconds without the user needing to manually refresh the page.
3. **Given** the Activity page showing events, **When** the user clicks on an event, **Then** the event expands inline to show additional detail (such as old/new values for updates, error messages for failures, or metadata for triggered actions).
4. **Given** the Activity page, **When** no events exist for the project, **Then** the page displays a friendly empty state message explaining that activity will appear here as the user interacts with the project.
5. **Given** each event in the activity feed, **When** the user views the event row, **Then** the event displays an icon representing its type (pipeline, chore, agent, app, tool, webhook), a summary, and a relative timestamp (e.g., "5 minutes ago").

---

### User Story 2 — Filtered Activity Feed (Priority: P1)

A user has a busy project with dozens of events per day. They need to filter the activity feed by event type (e.g., only pipeline runs, only chore triggers) and by date range so they can quickly find the events they care about without scrolling through unrelated noise.

**Why this priority**: Without filtering, the activity feed becomes unusable at scale. Filtering is essential to the usability of the feed and is tightly coupled to the feed itself — it has minimal value without Story 1 but is critical for the feed to be practically useful.

**Independent Test**: Can be fully tested by generating 50+ events across multiple types, then using filter controls to narrow the feed to a single event type and verifying that only matching events appear.

**Acceptance Scenarios**:

1. **Given** the Activity page with events of multiple types, **When** the user selects a filter chip for "Pipeline" events, **Then** only pipeline-related events are shown and all other event types are hidden.
2. **Given** the Activity page with a filter applied, **When** the user selects additional filter chips (e.g., "Pipeline" and "Chore"), **Then** events matching any of the selected types are shown.
3. **Given** the Activity page with filters applied, **When** the user removes all filters, **Then** the full unfiltered feed is restored.
4. **Given** the Activity page, **When** the user selects a date range filter, **Then** only events within the selected date range are displayed.

---

### User Story 3 — Paginated Activity Feed with Infinite Scroll (Priority: P1)

A project accumulates hundreds or thousands of events over time. The activity feed must load efficiently by fetching events in pages rather than all at once, using infinite scroll to load more events as the user scrolls down.

**Why this priority**: Without pagination, the activity feed will degrade in performance as events accumulate. Cursor-based pagination is fundamental to the feed's viability and must be part of the initial implementation.

**Independent Test**: Can be fully tested by generating 100+ events, loading the Activity page, and verifying that only an initial batch appears, with more loading as the user scrolls down.

**Acceptance Scenarios**:

1. **Given** a project with 200 activity events, **When** the user opens the Activity page, **Then** only the most recent 50 events load initially.
2. **Given** the Activity page showing 50 events, **When** the user scrolls to the bottom of the list, **Then** the next batch of 50 events loads automatically and appends below the existing events.
3. **Given** the user has scrolled to load multiple batches, **When** new events are created in the project, **Then** loading the next page does not skip or duplicate any events (cursor-based consistency).
4. **Given** the Activity page has loaded all available events, **When** the user scrolls to the bottom, **Then** no further loading occurs and an "end of activity" indicator is shown.

---

### User Story 4 — Entity-Scoped Activity History (Priority: P2)

A user is viewing a specific entity (a pipeline, chore, agent, app, or tool) and wants to see only the history for that entity — what changed, when it was triggered, when it failed. This scoped view helps the user troubleshoot issues and understand the lifecycle of a specific resource without navigating to the full activity feed.

**Why this priority**: Entity-scoped history adds significant value for debugging and auditing individual resources. It depends on the activity logging infrastructure from Story 1 but provides a distinct, complementary user experience.

**Independent Test**: Can be fully tested by performing multiple actions on a single pipeline (create, run, complete, fail), then opening that pipeline's detail view and verifying that only events related to that pipeline appear in the history panel.

**Acceptance Scenarios**:

1. **Given** a pipeline that has been run 5 times with various outcomes (completed, failed, cancelled), **When** the user views that pipeline's detail page, **Then** a history section shows all 5 run events with their statuses and timestamps.
2. **Given** a chore that has been created, updated, and triggered several times, **When** the user views that chore's detail page, **Then** the history section shows creation, updates, and trigger events in reverse-chronological order.
3. **Given** an entity with no activity history, **When** the user views that entity's detail page, **Then** the history section shows a message indicating no activity has been recorded yet.
4. **Given** the entity history section, **When** the user clicks on an event, **Then** the event expands to show additional detail, consistent with the main activity feed experience.

---

### User Story 5 — Notification Bell with Real Activity (Priority: P2)

The notification bell in the application header currently shows nothing — it is a placeholder that returns an empty array. Users expect the bell to surface important, recent events — such as pipeline failures, completed runs, and chore triggers — so they are aware of significant happenings without visiting the Activity page.

**Why this priority**: The notification bell is already present in the UI as a placeholder. Wiring it to real activity data transforms a broken feature into a functional one, providing passive awareness of important events. It depends on the activity logging infrastructure but provides a distinct surface for high-signal events.

**Independent Test**: Can be fully tested by triggering a pipeline failure and a chore execution, then clicking the notification bell and verifying that both events appear as notifications with accurate summaries and timestamps.

**Acceptance Scenarios**:

1. **Given** a pipeline run has completed or failed, **When** the user clicks the notification bell, **Then** the event appears as a notification with a summary (e.g., "Pipeline 'deploy-prod' failed") and a relative timestamp.
2. **Given** the user has not viewed notifications recently, **When** new high-signal events occur (pipeline failures, chore triggers), **Then** the bell displays an unread badge indicating the count of new notifications.
3. **Given** the user clicks on a notification, **When** the notification dropdown is open, **Then** the notification is marked as read and the unread badge count decreases accordingly.
4. **Given** the notification dropdown is open, **When** the user clicks "View all", **Then** they are navigated to the Activity page.
5. **Given** the notification bell, **When** only low-signal events have occurred (e.g., routine CRUD operations), **Then** those events do not appear as notifications — only high-signal events (pipeline completions/failures, chore triggers, agent executions) are surfaced.

---

### User Story 6 — Pipeline Run History Panel (Priority: P3)

A user editing or viewing a pipeline configuration wants quick access to the history of past runs for that pipeline — statuses, durations, and stage breakdowns — without leaving the pipeline editor. This provides immediate context about how the pipeline has been performing.

**Why this priority**: Pipeline run history is a focused, secondary view that enriches the pipeline editor. The backend already persists run data, so this story primarily involves surfacing existing data in a convenient location. It depends on activity infrastructure but offers value through a specialized presentation.

**Independent Test**: Can be fully tested by running a pipeline 3 times (one success, one failure, one cancelled), then opening the pipeline editor and verifying that a "Run History" tab shows all 3 runs with status badges, durations, and stage breakdowns.

**Acceptance Scenarios**:

1. **Given** a pipeline with 10 past runs, **When** the user opens the pipeline editor, **Then** a "Run History" tab or panel is available showing past runs with status badges (success/failure/cancelled), durations, and timestamps.
2. **Given** the run history panel, **When** the user clicks on a specific run, **Then** the run expands to show a stage-by-stage breakdown with individual stage statuses and durations.
3. **Given** a pipeline with no past runs, **When** the user views the run history panel, **Then** a message indicates that no runs have been recorded yet.

---

### Edge Cases

- What happens when two events occur at the exact same timestamp? The system must ensure a stable sort order so events do not jump positions across page loads.
- What happens when activity logging fails (e.g., storage is temporarily unavailable)? The primary operation (pipeline run, chore trigger, CRUD) must succeed regardless — activity logging failures must never block or fail the user's action.
- What happens when the user applies a filter that matches zero events? The system must display a clear empty state specific to the filter (e.g., "No pipeline events found") rather than the generic empty state.
- What happens when the user views the Activity page while new events are being written concurrently? Cursor-based pagination must ensure consistency — no duplicated or skipped events.
- What happens when the activity feed grows very large (10,000+ events per project)? The system must remain performant, with page load times staying within defined success criteria.
- What happens when an entity referenced by an activity event has been deleted? The event should still display with its summary text intact, but entity links should gracefully indicate that the entity no longer exists.

## Requirements *(mandatory)*

### Functional Requirements

#### Activity Event Persistence

- **FR-001**: System MUST persist every significant user and system action as an activity event, including pipeline runs, stage transitions, chore triggers, CRUD operations on agents/apps/tools/chores, webhook events, and cleanup operations.
- **FR-002**: Each activity event MUST capture: the type of event, the type and identifier of the affected entity, the project it belongs to, who or what performed the action (user or system), what action was taken, a human-readable summary, and an optional detail payload with structured metadata.
- **FR-003**: Activity events MUST be recorded with a timestamp and stored in chronological order.
- **FR-004**: Activity logging MUST be fire-and-forget — a failure to record an activity event MUST NOT cause the primary operation (e.g., pipeline run, entity creation) to fail or be delayed.

#### Activity Feed

- **FR-005**: System MUST provide a paginated activity feed scoped to a project, returning events in reverse-chronological order.
- **FR-006**: The activity feed MUST support cursor-based pagination to ensure consistent results when new events are added between page requests.
- **FR-007**: The activity feed MUST support filtering by one or more event types (e.g., show only pipeline and chore events).
- **FR-008**: The activity feed MUST support a configurable page size, with a default of 50 events per page.

#### Entity-Scoped History

- **FR-009**: System MUST provide a history view for a specific entity (identified by entity type and entity identifier), returning all activity events related to that entity in reverse-chronological order.
- **FR-010**: Entity history MUST be accessible from the detail view of each supported entity type (pipelines, chores, agents, apps, tools).

#### Activity Page

- **FR-011**: System MUST provide a dedicated Activity page accessible from the application's main navigation.
- **FR-012**: The Activity page MUST display each event as a compact row with an icon (representing the event type), a summary, a relative timestamp, and a link to the related entity.
- **FR-013**: The Activity page MUST support expanding an event inline to reveal additional detail (old/new values, error messages, metadata).
- **FR-014**: The Activity page MUST display an appropriate empty state when no events exist for the current project or current filter.
- **FR-015**: The Activity page MUST support infinite scroll, automatically loading the next page of events as the user scrolls to the bottom of the list.

#### Notification Bell

- **FR-016**: The notification bell MUST display recent high-signal activity events (pipeline completions/failures, chore triggers, agent executions) as notifications.
- **FR-017**: The notification bell MUST show an unread badge with the count of notifications the user has not yet viewed.
- **FR-018**: Users MUST be able to mark notifications as read by viewing them, and unread tracking MUST persist across page navigations within the same session.
- **FR-019**: The notification bell MUST include a "View all" link that navigates the user to the Activity page.

#### Pipeline Run History

- **FR-020**: Users MUST be able to view past pipeline runs from within the pipeline editor view, showing run status, duration, and timestamp.
- **FR-021**: Users MUST be able to expand a pipeline run to see a stage-by-stage breakdown with individual stage statuses and durations.

#### Event Coverage

- **FR-022**: System MUST log activity events for pipeline run creation, status transitions (started, completed, failed, cancelled), and stage completions.
- **FR-023**: System MUST log activity events for workflow transitions, capturing the from-status, to-status, trigger source, success/failure, and any error message.
- **FR-024**: System MUST log activity events for chore triggers, capturing chore name, trigger type (cron or manual), and result count.
- **FR-025**: System MUST log activity events for create, update, and delete operations on chores, agents, apps, and tools, capturing entity name and actor.
- **FR-026**: System MUST log activity events for inbound webhook events, capturing the webhook type and a summary of the payload.
- **FR-027**: System MUST log activity events for cleanup operations, capturing start/completion and branch/PR counts.

### Key Entities

- **Activity Event**: A record of a significant action that occurred within a project. Key attributes: event type (categorizes the kind of action), entity type and identifier (what was affected), project scope, actor (who or what performed the action), action taken, human-readable summary, optional structured detail, and timestamp. An activity event is immutable once created.
- **Activity Feed**: A paginated, filterable, reverse-chronological stream of activity events scoped to a project. Supports cursor-based navigation and type-based filtering.
- **Entity History**: A scoped subset of the activity feed showing only events related to a specific entity, providing a lifecycle view of that resource.
- **Notification**: A high-signal activity event surfaced in the notification bell. Attributes include summary, timestamp, read/unread status, and source event reference.

## Assumptions

- The notification bell already exists in the UI as a placeholder component. This feature replaces the placeholder with real data rather than building a new notification system from scratch.
- Read/unread tracking for notifications uses browser-local storage (consistent with the existing pattern in the codebase). Notifications are not synced across devices or sessions.
- The activity feed uses light polling (refreshing every 30 seconds) rather than real-time push for v1. Real-time updates via existing broadcast infrastructure may be added as a follow-up.
- All event types share a single unified event structure rather than separate per-type storage. This simplifies the feed query and avoids complex joins at the cost of some denormalization.
- Chat messages and real-time WebSocket events are excluded from the activity log — they already have their own dedicated UI and storage.
- Login/session events are excluded from scope — the system does not currently track authentication events.
- No automatic retention/purge policy is implemented in v1. A time-based or count-based cleanup mechanism (e.g., retain last 90 days) is recommended as a follow-up if event volume becomes a concern.
- The "detail" field on activity events contains structured metadata (old/new values, error messages) rendered as key-value pairs in the UI. The exact schema of the detail payload varies by event type.
- Pipeline run history in the pipeline editor reuses existing backend endpoints that already persist and serve run data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All supported action types (pipeline runs, chore triggers, CRUD operations, webhook events, cleanup operations) appear in the activity feed within 30 seconds of occurring, with accurate summaries and timestamps.
- **SC-002**: The Activity page loads its initial batch of events in under 2 seconds, even when the project has 10,000+ total activity events.
- **SC-003**: Scrolling through the activity feed loads subsequent pages in under 1 second per page, with no duplicated or skipped events across pages.
- **SC-004**: Users can filter the activity feed by event type and see results update within 1 second.
- **SC-005**: The notification bell displays unread high-signal events (pipeline completions/failures, chore triggers) within 30 seconds of the event occurring.
- **SC-006**: Entity-scoped history panels load in under 1 second for entities with up to 100 associated events.
- **SC-007**: Activity logging adds no more than 50 milliseconds of latency to any primary operation (pipeline run, CRUD, webhook processing) — users experience no perceptible slowdown.
- **SC-008**: The pipeline run history panel displays past runs with status, duration, and stage breakdowns accurately matching the data persisted by existing run-tracking infrastructure.
