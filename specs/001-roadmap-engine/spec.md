# Feature Specification: Self-Evolving Roadmap Engine

**Feature Branch**: `001-roadmap-engine`  
**Created**: 2026-03-27  
**Status**: Draft  
**Input**: User description: "As a product owner, I want the system to automatically analyze the codebase and repo metrics against my seed vision to generate and launch the next batch of feature issues when the pipeline is idle, so that development momentum is maintained continuously without manual roadmap grooming."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Roadmap Settings (Priority: P1)

As a product owner, I want to enable the roadmap engine and configure my seed vision, batch size, and target pipeline from the project settings page, so that the system knows what direction to generate features toward and how many to produce per cycle.

**Why this priority**: Without configuration, no other roadmap functionality can operate. This is the foundational entry point that gates every subsequent capability.

**Independent Test**: Can be fully tested by navigating to the project settings page, filling out the Roadmap section (toggle, seed vision, batch size, pipeline selector, auto-launch toggle), saving, refreshing the page, and verifying all values persist correctly.

**Acceptance Scenarios**:

1. **Given** a project with no roadmap configuration, **When** the product owner opens Settings and enables the Roadmap toggle, enters a seed vision, sets batch size to 5, selects a pipeline, and saves, **Then** all five fields are persisted and restored on page reload.
2. **Given** a saved roadmap configuration, **When** the product owner changes the batch size from 5 to 2 and saves, **Then** only the batch size updates; all other fields remain unchanged.
3. **Given** the Roadmap toggle is disabled, **When** the product owner saves settings, **Then** all roadmap fields are preserved but no automatic generation occurs.
4. **Given** the product owner enters a batch size outside the 1–10 range, **When** they attempt to save, **Then** the system rejects the input with a clear validation message.

---

### User Story 2 - Manually Generate a Roadmap Batch (Priority: P2)

As a product owner, I want to manually trigger generation of a roadmap batch so that I can review AI-proposed feature issues before they enter the pipeline, giving me control over what gets queued.

**Why this priority**: Manual generation is the core value proposition—translating a seed vision into actionable feature issues via AI. It must work before auto-launch can be trusted.

**Independent Test**: Can be fully tested by configuring roadmap settings, clicking a "Generate" button (or calling the generate endpoint), and verifying that a batch of feature items appears in the roadmap activity feed with titles, rationale, priority, and size.

**Acceptance Scenarios**:

1. **Given** a configured roadmap with a seed vision and batch size of 3, **When** the product owner triggers manual generation, **Then** the system produces exactly 3 roadmap items, each with a title, full issue body, rationale, priority, and size estimate.
2. **Given** a previous cycle generated items with titles "Feature A" and "Feature B," **When** the product owner triggers a new generation cycle, **Then** none of the new items duplicate previously generated titles.
3. **Given** the AI service is temporarily unavailable, **When** the product owner triggers generation, **Then** the system displays a clear error message and no partial items are created.
4. **Given** a seed vision is empty or missing, **When** the product owner triggers generation, **Then** the system rejects the request with a message indicating that a seed vision is required.

---

### User Story 3 - Review and Veto Roadmap Items (Priority: P3)

As a product owner, I want to review generated roadmap items in an activity feed and veto (skip) individual items before they are launched, so that I maintain editorial control over which features enter the development pipeline.

**Why this priority**: Veto capability is essential for trust in the system. Without it, product owners cannot prevent undesirable features from being launched. However, it depends on generation working first (P2).

**Independent Test**: Can be fully tested by generating a batch, viewing the activity feed with expandable cards, clicking the veto button on one item, and verifying it is skipped and does not appear in the pipeline queue.

**Acceptance Scenarios**:

1. **Given** a generated batch with 3 items displayed in the activity feed, **When** the product owner clicks the veto button on item 2, **Then** item 2 is marked as skipped and will not be launched into the pipeline.
2. **Given** a generated batch is displayed, **When** the product owner expands a card, **Then** they see the item's title, rationale, priority, and a veto button.
3. **Given** a vetoed item, **When** the product owner views roadmap history, **Then** the vetoed item appears with a "skipped" status in the cycle log.

---

### User Story 4 - Auto-Launch on Idle Pipeline (Priority: P4)

As a product owner, I want the system to automatically generate and launch a roadmap batch when the pipeline queue is empty and auto-launch is enabled, so that development momentum is maintained without manual intervention.

**Why this priority**: Auto-launch is the "self-evolving" promise of the feature. It depends on generation (P2) and veto (P3) being solid first, as it removes human-in-the-loop oversight for triggering.

**Independent Test**: Can be fully tested by enabling auto-launch, clearing the pipeline queue, waiting for the idle debounce period, and verifying that a new batch is generated and items appear in the pipeline queue.

**Acceptance Scenarios**:

1. **Given** roadmap is enabled with auto-launch on and the pipeline queue is empty, **When** 5 minutes pass with no new queue activity, **Then** the system triggers a roadmap generation cycle and launches the resulting items into the pipeline.
2. **Given** auto-launch is enabled and 10 auto-cycles have already occurred today, **When** the pipeline becomes idle again, **Then** no further auto-cycles are triggered until the next calendar day (UTC).
3. **Given** auto-launch is enabled but the pipeline queue has items, **When** the queue is checked, **Then** no roadmap cycle is triggered.
4. **Given** auto-launch is enabled and a cycle was triggered 2 minutes ago, **When** the pipeline becomes idle again, **Then** no new cycle is triggered until the 5-minute debounce window expires.

---

### User Story 5 - Receive Notifications and Veto via Signal (Priority: P5)

As a product owner, I want to receive a Signal notification when a roadmap cycle completes, listing the queued items and allowing me to veto items by replying, so that I can maintain oversight even when not actively using the web interface.

**Why this priority**: Notifications are an important convenience layer but not essential for core functionality. The system is fully usable via the web interface without notifications.

**Independent Test**: Can be fully tested by triggering a generation cycle, verifying a Signal notification is sent in the correct format, replying with "SKIP 2" and verifying item 2 is vetoed.

**Acceptance Scenarios**:

1. **Given** a roadmap cycle generates 3 items, **When** the cycle completes, **Then** a Signal notification is sent in the format: "🗺️ Roadmap: 3 items queued — Title A, Title B, Title C. Reply SKIP {number} to veto."
2. **Given** a notification was sent for a cycle, **When** the product owner replies "SKIP 2," **Then** item 2 is vetoed and does not launch into the pipeline.
3. **Given** roadmap_grace_minutes is set to 15, **When** a cycle completes, **Then** items are held in a queued-but-not-launched state for 15 minutes before launching, allowing time for veto via notification.

---

### User Story 6 - View Roadmap Cycle History (Priority: P6)

As a product owner, I want to view the history of all roadmap generation cycles, including which items were generated, launched, or vetoed in each cycle, so that I can audit past decisions and understand the system's behavior over time.

**Why this priority**: History and auditability are important for long-term trust but not required for the core generation-and-launch loop.

**Independent Test**: Can be fully tested by running multiple generation cycles, navigating to the history endpoint or activity feed, and verifying that each cycle shows its timestamp, items, statuses, and outcomes.

**Acceptance Scenarios**:

1. **Given** 3 roadmap cycles have been completed, **When** the product owner queries roadmap history, **Then** all 3 cycles are listed in reverse chronological order with their batch details and statuses.
2. **Given** a cycle where 1 of 3 items was vetoed, **When** the product owner views that cycle in history, **Then** the vetoed item shows "skipped" and the other 2 show "launched."

---

### Edge Cases

- What happens when the AI returns malformed JSON that cannot be parsed into a RoadmapBatch? The system must reject the response, log the error, record the cycle as "failed," and not create any partial items.
- What happens when the pipeline referenced by roadmap_pipeline_id is deleted or reconfigured? The system must detect the invalid pipeline reference and surface an error to the product owner rather than silently failing.
- What happens when two auto-launch triggers race concurrently (e.g., two queue-empty events within milliseconds)? The debounce guard must ensure only one cycle is triggered; the second must be suppressed.
- What happens when the daily auto-cycle cap is reached mid-batch? The current cycle completes fully, but no additional cycles are triggered until the next day.
- What happens when the seed vision is extremely long (e.g., 50,000 characters)? The system must enforce a reasonable maximum length and reject or truncate inputs that exceed it.
- What happens when there are no completed cycles for deduplication? The system must proceed with generation using an empty deduplication list.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extend ProjectBoardConfig with `roadmap_enabled` (boolean, default false), `roadmap_seed` (text), `roadmap_batch_size` (integer 1–10, default 3), `roadmap_pipeline_id` (reference to existing pipeline), and `roadmap_auto_launch` (boolean, default false) fields, persisted as JSON in the existing project_settings table without requiring a schema migration.
- **FR-002**: System MUST provide RoadmapItem, RoadmapBatch, and RoadmapCycleLog data models that validate generated roadmap data, where each RoadmapItem includes a title, full issue body, rationale, priority, and size estimate.
- **FR-003**: System MUST persist cycle audit records (cycle ID, project ID, user ID, batch contents, status, and creation timestamp) to enable history queries and deduplication.
- **FR-004**: System MUST implement a roadmap batch generation capability that: gathers codebase context signals and repository metrics (coverage, dependencies), retrieves recent completed cycle titles for deduplication, constructs a structured prompt combining the seed vision with a duplicate-avoidance list, sends the prompt to the AI completion provider, and parses the response into a validated RoadmapBatch.
- **FR-005**: System MUST implement a roadmap launcher that iterates over RoadmapBatch items and delegates each to the existing pipeline launch mechanism, with zero new issue-creation logic.
- **FR-006**: System MUST hook into the pipeline dequeue mechanism so that when the queue is empty AND `roadmap_enabled` AND `roadmap_auto_launch` are both true, a roadmap cycle is triggered with a 5-minute debounce guard to prevent rapid re-triggering.
- **FR-007**: System MUST enforce a hard cap of 10 auto-triggered cycles per calendar day (UTC) per project to prevent runaway cost.
- **FR-008**: System MUST expose endpoints for: retrieving roadmap configuration, updating roadmap configuration, manually triggering a generation cycle, retrieving cycle history, and vetoing (skipping) individual roadmap items.
- **FR-009**: System MUST send a Signal notification on each completed cycle in the format: "🗺️ Roadmap: N items queued — {titles}. Reply SKIP {number} to veto."
- **FR-010**: System MUST support a configurable `roadmap_grace_minutes` window (integer, default 0) that, when greater than zero, holds generated items in a queued-but-not-launched state for the specified duration before launching, allowing time for veto.
- **FR-011**: System MUST validate that the referenced pipeline exists and is active before attempting generation or launch, and surface a clear error if the pipeline is invalid.
- **FR-012**: System MUST handle AI response parsing failures gracefully by logging the error, recording the cycle as "failed," and not creating any partial items.
- **FR-013**: System MUST prevent duplicate titles across cycles by including recent cycle titles in the generation prompt as a deduplication signal (title-based dedup in V1).
- **FR-014**: System MUST validate `roadmap_seed` is non-empty before allowing generation, and enforce a maximum length to prevent excessively large prompts.
- **FR-015**: System MUST display a compact board badge near the queue mode toggle reflecting live roadmap state: "Active," "Idle," or "Generating…"

### Key Entities

- **RoadmapItem**: Represents a single AI-generated feature proposal. Attributes: title, full issue body text, rationale explaining why this feature was suggested, priority level, and size estimate.
- **RoadmapBatch**: Represents a collection of RoadmapItems generated in a single cycle. Attributes: list of RoadmapItems, generation timestamp, associated project, and requesting user.
- **RoadmapCycleLog**: Represents the audit record of a generation cycle. Attributes: unique cycle ID, project reference, user reference, serialized batch contents, cycle status (pending, completed, failed, partial), and creation timestamp.
- **RoadmapConfig**: Represents the per-project roadmap configuration. Attributes: enabled flag, seed vision text, batch size, target pipeline reference, auto-launch flag, grace minutes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Product owners can configure all roadmap settings (toggle, seed vision, batch size, pipeline, auto-launch) and have them persist correctly across page reloads with 100% fidelity.
- **SC-002**: Manual generation produces a valid batch of feature proposals matching the configured batch size within 60 seconds of triggering.
- **SC-003**: Generated items contain meaningful, non-duplicate titles that align with the seed vision, with zero exact-title duplicates across the last 30 cycles.
- **SC-004**: Product owners can veto any individual item within 3 clicks (expand card → click veto → confirm), and vetoed items never enter the pipeline.
- **SC-005**: Auto-launch triggers within 6 minutes of the pipeline becoming idle (5-minute debounce + 1-minute tolerance) and does not exceed 10 cycles per day per project.
- **SC-006**: Signal notifications are delivered within 30 seconds of cycle completion and contain accurate item titles and veto instructions.
- **SC-007**: Cycle history displays all past cycles with correct status, item details, and outcomes, loading within 2 seconds for up to 100 cycles.
- **SC-008**: The system degrades gracefully under AI service failures—no partial items are created, errors are surfaced to the user, and the system recovers on the next trigger without manual intervention.

## Assumptions

- The existing `project_settings` table supports arbitrary JSON fields, so no schema migration is needed for roadmap configuration storage.
- The existing `execute_pipeline_launch()` function handles all issue creation logic; the roadmap launcher only needs to invoke it.
- The existing blocking-queue skip mechanism can be reused for roadmap item veto without modification.
- Signal notification infrastructure is already in place and can be extended with new message formats.
- The AI completion provider (CompletionProvider.complete()) supports structured JSON output parsing.
- Title-based deduplication (V1) is sufficient; embedding-based similarity is deferred to V2.
- AI-driven seed evolution is deferred to V2; V1 uses static user-managed seed text.
- The dedicated /roadmap page with funnel visualization is a stretch goal and out of core scope for V1.
- The `roadmap_grace_minutes` default of 0 means items are launched immediately by default; behavior when greater than 0 is to hold items for the specified window before auto-launching.
- Cost model assumes batch size default of 3 with approximately 5 agent assignments per item, yielding roughly 15 agent assignments per cycle; the 10-cycle daily cap limits maximum spend.
