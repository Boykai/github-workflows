# Feature Specification: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Feature Branch**: `030-blocking-queue`
**Created**: 2026-03-08
**Status**: Draft
**Input**: User description: "Blocking Queue — Serial Issue Activation & Branch Ancestry Control via Chores, Pipelines, and #block Chat Command"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Blocking Queue Core: Serial Issue Activation (Priority: P1)

As a developer orchestrating multi-agent GitHub workflows, I want the system to serialize issue activation when blocking issues exist in a repository — so that only one blocking issue runs agents at a time, preventing conflicting concurrent changes and ensuring dependent work completes in order.

When I create a blocking issue (via a blocking Chore, a blocking Pipeline, or the `#block` chat command), the system enqueues it in a per-repository blocking queue. If no other blocking issues are currently active, it activates immediately and agents begin work. If a blocking issue is already active, the new issue waits in "pending" status until the active issue transitions to "in review" or completes. Non-blocking issues submitted while no blocking issues are open continue to activate immediately and concurrently, preserving current behavior.

**Why this priority**: This is the fundamental value proposition — without serial activation, the entire blocking queue concept has no effect. It is the engine that all other stories depend on.

**Independent Test**: Can be fully tested by creating multiple issues with blocking flags in sequence, verifying that only one activates at a time, and that pending issues activate in order when the active issue transitions. Delivers immediate value by preventing conflicting concurrent agent work on dependent changes.

**Acceptance Scenarios**:

1. **Given** a repository with no open blocking issues, **When** a non-blocking issue is created, **Then** it activates immediately and agents are assigned (current behavior preserved).
2. **Given** a repository with no open blocking issues, **When** a blocking issue (Issue A) is created, **Then** Issue A activates immediately and agents are assigned.
3. **Given** a repository with one active blocking issue (Issue A), **When** a second blocking issue (Issue B) is created, **Then** Issue B enters "pending" status and no agents are assigned to it.
4. **Given** a repository with one active blocking issue (Issue A) and one pending blocking issue (Issue B), **When** Issue A transitions to "in review," **Then** Issue B activates and agents are assigned to it.
5. **Given** a repository with one active blocking issue (Issue A) and one pending non-blocking issue (Issue C) followed by a pending blocking issue (Issue D), **When** Issue A transitions to "in review," **Then** Issue C activates (non-blocking issues activate together up to the next blocking entry), but Issue D remains pending.
6. **Given** a repository with active issues in review, **When** the active blocking issue completes, **Then** the next pending issue(s) activate per the batch activation rules.
7. **Given** a blocking issue transitions to "in review" and a batch of non-blocking issues activates, **When** all those non-blocking issues also complete or move to "in review," **Then** the next blocking issue in the queue activates.

---

### User Story 2 — Branch Ancestry Control from Blocking Issues (Priority: P1)

As a developer, I want issues that activate while blocking issues are open to automatically branch from the oldest open blocking issue's branch (instead of `main`), so that dependent changes are layered correctly in Git history and each new issue builds on top of the most foundational in-progress blocking work.

**Why this priority**: Branch ancestry is tightly coupled with serial activation — without correct branching, serialized issues would still create isolated branches off `main`, defeating the purpose of ordered, dependent changes.

**Independent Test**: Can be tested by creating a blocking issue, verifying its branch is created from `main`, then creating a second issue while the first is active, and verifying the second issue's branch is created from the first blocking issue's branch. When all blocking issues complete, verify new issues branch from `main` again.

**Acceptance Scenarios**:

1. **Given** a repository with no open blocking issues, **When** a new issue activates, **Then** its branch is created from `main` (default behavior).
2. **Given** a repository with one open blocking issue (Issue A, branch `030-blocking-queue`), **When** a second issue (Issue B) activates, **Then** Issue B's branch is created from Issue A's branch (`030-blocking-queue`), not from `main`.
3. **Given** a repository with multiple open blocking issues, **When** a new issue activates, **Then** it branches from the **oldest** open blocking issue's branch (not chained — all branch from the same base).
4. **Given** a repository where a blocking issue completes and no other blocking issues remain, **When** the next issue activates, **Then** it branches from `main`.
5. **Given** a repository where the oldest blocking issue completes but other blocking issues remain open, **When** the base branch is recalculated, **Then** it shifts to the next oldest open blocking issue's branch.

---

### User Story 3 — Chore Blocking Toggle (Priority: P2)

As a user configuring Chores, I want a "Blocking" toggle on each Chore so that when triggered, the resulting issue is enqueued as a blocking issue in the repository's blocking queue, ensuring it runs serially and controls branch ancestry.

**Why this priority**: Chores are a primary entry point for creating issues. Enabling blocking on Chores allows scheduled or manual task triggers to participate in the blocking queue, which is essential for planned workflows.

**Independent Test**: Can be tested by enabling the blocking toggle on a Chore, triggering it, and verifying the resulting issue is enqueued with `is_blocking=true` and follows the blocking queue activation rules.

**Acceptance Scenarios**:

1. **Given** a user is viewing a Chore's configuration, **When** they toggle "Blocking" on, **Then** the `blocking` flag is persisted immediately and reflected in the UI.
2. **Given** a Chore has `blocking=true`, **When** the Chore is triggered, **Then** the resulting issue is created with `is_blocking=true` and enqueued in the blocking queue.
3. **Given** a Chore has `blocking=false` but is assigned to a Pipeline with `blocking=true`, **When** the Chore is triggered, **Then** the resulting issue inherits the Pipeline's blocking flag and is created as blocking.
4. **Given** a user toggles "Blocking" off on a Chore, **When** the toggle is saved, **Then** the `blocking` flag is updated to `false` and future triggers create non-blocking issues.

---

### User Story 4 — Pipeline-Level Blocking Toggle (Priority: P2)

As a user configuring Pipelines, I want a "Blocking" toggle on each Pipeline configuration so that ALL issues created by that Pipeline are automatically marked as blocking, simplifying configuration when an entire pipeline's output should be serialized.

**Why this priority**: Pipeline-level blocking is a convenience that avoids configuring each Chore individually. It ensures consistent behavior for all issues from a given Pipeline.

**Independent Test**: Can be tested by enabling the blocking toggle on a Pipeline, creating issues through that Pipeline, and verifying all resulting issues are enqueued as blocking.

**Acceptance Scenarios**:

1. **Given** a user is editing a Pipeline configuration, **When** they toggle "Blocking" on, **Then** the `blocking` flag is persisted immediately and reflected in the UI.
2. **Given** a Pipeline has `blocking=true`, **When** any issue is created through this Pipeline, **Then** the issue is enqueued with `is_blocking=true`.
3. **Given** a Pipeline has `blocking=true` and a Chore assigned to it has `blocking=false`, **When** the Chore is triggered, **Then** the Pipeline's blocking flag takes precedence and the issue is created as blocking.
4. **Given** a user views the Pipeline configuration form, **When** the "Blocking" toggle is visible, **Then** a tooltip explains that enabling it marks every issue the Pipeline creates as blocking.

---

### User Story 5 — Chat `#block` Command (Priority: P2)

As a user interacting via chat, I want to include `#block` anywhere in my message so that the resulting issue is marked as blocking and enters the blocking queue, without changing the rest of my message's intent or processing.

**Why this priority**: Chat is a key interaction point for ad-hoc issue creation. The `#block` command provides a lightweight, inline way to make any chat-created issue blocking without navigating to configuration screens.

**Independent Test**: Can be tested by sending a chat message containing `#block` (e.g., "Fix the login page #block"), verifying the `#block` text is stripped from the message before intent processing, and confirming the resulting issue is enqueued as blocking.

**Acceptance Scenarios**:

1. **Given** a user types a chat message containing `#block` (e.g., "Add dark mode support #block"), **When** the message is sent, **Then** `#block` is detected and stripped from the message content before downstream intent processing.
2. **Given** a chat message contains `#block`, **When** the resulting issue is created, **Then** it is enqueued with `is_blocking=true` in the blocking queue.
3. **Given** a chat message does NOT contain `#block`, **When** the resulting issue is created, **Then** it is enqueued with `is_blocking=false` (default behavior unchanged).
4. **Given** a user is typing a chat message, **When** they type `#block`, **Then** it appears in the command autocomplete suggestions, and a visual badge/indicator appears on the message composer showing the issue will be blocking.

---

### User Story 6 — Blocking Queue UI Indicators and Notifications (Priority: P3)

As a user viewing the Kanban/issue board, I want to see visual indicators for blocking issues (🔒 icon or "Blocking" badge), "Pending (blocked)" status labels for queued issues, and receive real-time toast notifications when pending issues activate, so that I understand the current state of the blocking queue at a glance.

**Why this priority**: Visual indicators and notifications are important for user awareness but are not functionally blocking. The core queue behavior works without them; they add polish and transparency.

**Independent Test**: Can be tested by creating blocking and pending issues, verifying the correct visual indicators appear on issue cards, and confirming a toast notification is displayed when a pending issue activates.

**Acceptance Scenarios**:

1. **Given** an issue is marked as blocking, **When** the issue card is displayed on the board, **Then** a 🔒 icon or "Blocking" badge is visible on the card.
2. **Given** an issue is in "pending" status in the blocking queue, **When** the issue card is displayed, **Then** it shows a "Pending (blocked)" status label.
3. **Given** a previously pending issue activates (agents start), **When** the activation occurs, **Then** a toast notification appears reading "Issue #X is now active — agents starting."
4. **Given** a user views the board for a repository with an active blocking queue, **When** they inspect the blocking chain (via tooltip or sidebar), **Then** they see the ordered queue, the current base branch, and which issue is next in line.

---

### User Story 7 — Container Restart Recovery (Priority: P3)

As a system administrator, I want the blocking queue to survive container restarts and automatically recover any missed activations on startup, so that issues are never permanently stuck in "pending" status due to infrastructure events.

**Why this priority**: Resilience is critical for a production system, but it is a background concern — the queue must first work correctly before we worry about restart recovery.

**Independent Test**: Can be tested by creating pending issues in the queue, restarting the container/polling loop, and verifying that the system automatically attempts to activate pending issues on startup for all repos with non-completed queue entries.

**Acceptance Scenarios**:

1. **Given** the system has pending issues in the blocking queue, **When** the container restarts, **Then** the system automatically attempts to activate the next eligible pending issue(s) for all repositories with non-completed queue entries.
2. **Given** a blocking issue transitioned to "in review" during downtime but the next issue was not activated, **When** the system recovers on startup, **Then** the next issue in the queue is activated and agents are assigned.
3. **Given** the blocking queue data is persisted in the database, **When** the container restarts, **Then** all queue entries (pending, active, in_review, completed) are intact and the queue resumes from its last known state.

---

### Edge Cases

- What happens when a blocking issue is manually closed or deleted outside the system? The system should detect the closure during the next polling cycle, mark it as completed, and attempt to activate the next pending issue(s) to unblock the queue.
- What happens if two issues transition simultaneously (race condition)? The system must use per-repository locking and database transactions to ensure only one activation decision is made at a time, preventing double-activation.
- What happens when the oldest open blocking issue's branch is deleted from the remote? The system should fall back to `main` when the target branch is not found and log a warning.
- What happens if a non-blocking issue is submitted while a blocking issue is active? It enters "pending" status and waits, since any open blocking issue enforces serial activation for all issues.
- What happens when all blocking issues complete but non-blocking issues are still pending? Pending non-blocking issues should activate immediately and concurrently, as no blocking constraint remains.
- What happens if the `#block` keyword appears multiple times in a chat message? The system should detect and strip all occurrences, setting `is_blocking=true` once — multiple occurrences have no additional effect.
- What happens if a Chore's pipeline is deleted after the Chore is configured with `blocking=false` and relied on pipeline inheritance? The Chore should fall back to its own `blocking` flag (false), and the issue is created as non-blocking.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a per-repository blocking queue that tracks issues through the states: pending, active, in_review, and completed.
- **FR-002**: System MUST activate non-blocking issues immediately and concurrently when no blocking issues are open in the repository (preserving current behavior).
- **FR-003**: System MUST enforce serial activation when any blocking issue is open — only one blocking issue may be active at a time.
- **FR-004**: System MUST activate pending issues in batch when the active issue transitions to "in review": non-blocking issues activate together up to the next blocking entry; blocking entries activate alone.
- **FR-005**: System MUST determine the base branch for newly activated issues as follows: if any blocking issue is open, use the oldest open blocking issue's branch; otherwise, use `main`.
- **FR-006**: System MUST recalculate the base branch when a blocking issue completes — shifting to the next oldest open blocking issue's branch, or reverting to `main` if none remain.
- **FR-007**: System MUST provide a "Blocking" toggle on each Chore configuration that persists immediately when changed.
- **FR-008**: System MUST provide a "Blocking" toggle on each Pipeline configuration that persists immediately when changed and marks ALL issues created by that Pipeline as blocking.
- **FR-009**: System MUST detect `#block` anywhere in a chat message (not just as a prefix), strip it before downstream intent processing, and set `is_blocking=true` on the resulting issue.
- **FR-010**: System MUST inherit the blocking flag from the assigned Pipeline when a Chore's own blocking flag is not set.
- **FR-011**: System MUST persist the blocking queue in the database so that queue state survives container restarts.
- **FR-012**: System MUST use per-repository locking and database transactions to prevent double-activation race conditions during concurrent state transitions.
- **FR-013**: System MUST attempt to activate the next pending issue(s) for all repositories with non-completed queue entries on container/polling-loop startup to recover missed activations.
- **FR-014**: System MUST broadcast a real-time event when issues activate or complete, including the repository identifier, list of activated issues, list of completed issues, and the current base branch.
- **FR-015**: System MUST display a 🔒 icon or "Blocking" badge on issue cards that are blocking.
- **FR-016**: System MUST display a "Pending (blocked)" status label on issue cards that are in the pending state of the blocking queue.
- **FR-017**: System MUST display a toast notification reading "Issue #X is now active — agents starting" when a previously pending issue activates.
- **FR-018**: System MUST add `#block` to the chat command autocomplete suggestions and display a visual indicator on the message composer when `#block` is detected in the typed text.
- **FR-019**: System MUST return a pending status (skipping agent assignment) when an issue cannot activate immediately due to blocking queue constraints.
- **FR-020**: System MUST record which blocking issue provided the parent branch for each activated issue for traceability.

### Key Entities

- **Blocking Queue Entry**: Represents an issue's position and state in a repository's blocking queue. Key attributes: repository identifier, issue number, project identifier, whether the issue is blocking, queue status (pending/active/in_review/completed), parent branch, source blocking issue number, timestamps for creation, activation, and completion. Unique per repository-issue pair.
- **Chore**: An existing entity representing a schedulable or manually triggered task. Enhanced with a `blocking` boolean flag that determines whether triggered issues enter the blocking queue as blocking.
- **Pipeline Configuration**: An existing entity representing a workflow pipeline configuration. Enhanced with a `blocking` boolean flag that propagates to ALL issues created by the pipeline.

## Assumptions

- The system already has a concept of issue activation and agent assignment, and the blocking queue integrates as a pre-activation gating layer.
- Issues transition through statuses (e.g., active → in review → completed) as part of the existing polling and workflow orchestration.
- The existing branching logic uses a deterministic base reference (currently `main`) that can be overridden by the blocking queue service.
- Chores and Pipelines already have CRUD operations and UI configuration forms that can be extended with the new `blocking` field.
- The chat interface already supports magic-word/command detection (e.g., `#agent`) and the `#block` command follows the same parsing pattern.
- Real-time event broadcasting infrastructure (WebSocket) already exists and can be extended with a new event type.
- The "8-issue scenario" referenced in requirements describes: a mix of blocking and non-blocking issues created in sequence, where activation order, batching, and branch ancestry are validated end-to-end.

## Scope Boundaries

- **Included**: Blocking toggle for Chores and Pipelines; `#block` chat command; serial activation; branch ancestry from blocking issues; per-repository queue; real-time notifications; container restart recovery; queue state persistence.
- **Excluded**: UI for reordering the blocking queue; blocking across repositories; retroactive blocking of existing open issues; blocking for draft items (only full issues); admin override to force-activate a blocked issue.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When a blocking issue is active, 100% of subsequently created issues enter "pending" status and do not receive agent assignments until the blocking issue transitions.
- **SC-002**: 100% of issues activated while blocking issues are open branch from the oldest open blocking issue's branch, not from `main`.
- **SC-003**: When all blocking issues complete, 100% of subsequently created issues branch from `main` (default behavior restored).
- **SC-004**: The blocking toggle on Chores and Pipelines persists within 2 seconds of user interaction and is reflected in the next API response.
- **SC-005**: The `#block` chat command is correctly detected, stripped, and propagated in 100% of messages containing it, with no impact on the remaining message content or intent processing.
- **SC-006**: Users can identify blocking issues and pending (blocked) issues at a glance on the board, with 100% of blocking issues displaying the appropriate visual indicator.
- **SC-007**: Pending issues that activate after a blocking issue transitions trigger a user-facing notification within 5 seconds of activation.
- **SC-008**: The blocking queue state survives container restarts with zero data loss, and missed activations are recovered within 30 seconds of startup.
- **SC-009**: An 8-issue mixed scenario (blocking and non-blocking) completes with correct activation order, correct batching, and correct branch ancestry for every issue in the sequence.
