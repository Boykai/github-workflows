# Feature Specification: Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues

**Feature Branch**: `030-fix-chore-issue-counter`  
**Created**: 2026-03-08  
**Status**: Draft  
**Input**: User description: "Fix 'Every X Issues' Chore Counter to Only Count GitHub Parent Issues (Excluding Chores and Sub-Issues)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Counter Displays Accurate Count of Qualifying Parent Issues (Priority: P1)

As a project maintainer with a Chore configured to trigger "Every X issues," I want the counter on the Chore tile to show only the number of GitHub Parent Issues (excluding Chores and Sub-Issues) created since that Chore last ran, so that I can trust the displayed countdown is accurate and know exactly when the Chore will fire.

**Why this priority**: The counter is the primary user-facing feedback mechanism. If it displays an inflated number (due to counting Chores or Sub-Issues), users lose trust in the system and cannot predict when their Chores will trigger. This is the core of the reported bug.

**Independent Test**: Can be fully tested by setting up a Chore with "Every 5 issues" trigger, creating a mix of Parent Issues, Sub-Issues, and Chore-generated issues, and verifying the tile counter increments only for qualifying Parent Issues.

**Acceptance Scenarios**:

1. **Given** a Chore configured with "Every 5 issues" that last ran 2 qualifying Parent Issues ago, **When** the user views the Chores page, **Then** the tile counter displays a count of 2 (reflecting only the 2 qualifying Parent Issues created since the last run).
2. **Given** a Chore configured with "Every 5 issues" and 3 qualifying Parent Issues have been created since last run, **When** a new Sub-Issue is created under an existing Parent Issue, **Then** the tile counter remains at 3 and does not increment.
3. **Given** a Chore configured with "Every 5 issues" and 3 qualifying Parent Issues have been created since last run, **When** another Chore creates a GitHub Issue (a Chore-generated issue), **Then** the tile counter remains at 3 and does not increment.
4. **Given** a Chore configured with "Every 5 issues" and 4 qualifying Parent Issues exist since last run, **When** a new qualifying Parent Issue is created (reaching 5), **Then** the tile counter updates to 5, indicating the threshold is met.

---

### User Story 2 — Trigger Evaluation Uses Same Filtered Count as Tile Display (Priority: P1)

As a project maintainer, I want the internal trigger evaluation that decides when to fire the Chore to use the exact same filtered issue count as what is displayed on the tile, so that there is no discrepancy between what I see and when the Chore actually fires.

**Why this priority**: If the tile shows one number but the trigger evaluates a different number, users will experience confusing behavior where Chores fire too early or too late relative to what the counter shows. Consistency between display and trigger is essential.

**Independent Test**: Can be fully tested by configuring a Chore with "Every 3 issues," creating exactly 3 qualifying Parent Issues (plus several Sub-Issues and Chore issues that should not count), and verifying that the Chore fires when the counter reaches 3 — not before or after.

**Acceptance Scenarios**:

1. **Given** a Chore with "Every 3 issues" and 2 qualifying Parent Issues since last run (plus 5 Sub-Issues and 2 Chore issues), **When** the trigger evaluation runs, **Then** the trigger does not fire because the qualifying count is 2, not 9.
2. **Given** a Chore with "Every 3 issues" and the tile displays a count of 3, **When** the trigger evaluation runs, **Then** the Chore fires because the qualifying count matches the threshold.
3. **Given** a Chore with "Every 3 issues" that just fired, **When** the trigger evaluation runs again immediately after, **Then** the qualifying count is 0 and the Chore does not fire again.

---

### User Story 3 — Independent Per-Chore Counter Scoping (Priority: P1)

As a project maintainer managing multiple Chores with "Every X issues" triggers, I want each Chore's counter to be scoped independently to its own last-run timestamp, so that one Chore's execution does not affect another Chore's counter or cause it to reset.

**Why this priority**: Without independent scoping, running one Chore could inadvertently reset or alter another Chore's counter, leading to unpredictable trigger behavior across the entire Chores system.

**Independent Test**: Can be fully tested by creating two Chores with different "Every X issues" thresholds, running one of them, and verifying the other Chore's counter is unaffected.

**Acceptance Scenarios**:

1. **Given** Chore A ("Every 3 issues," last ran 2 hours ago with 2 qualifying issues since) and Chore B ("Every 5 issues," last ran 4 hours ago with 4 qualifying issues since), **When** Chore A triggers and executes, **Then** Chore B's counter remains at 4 and is unaffected by Chore A's reset.
2. **Given** Chore A and Chore B both track "Every 5 issues" but last ran at different times, **When** the user views the Chores page, **Then** each tile shows a different counter reflecting its own last-run baseline.
3. **Given** a new qualifying Parent Issue is created, **When** multiple Chores exist with "Every X issues" triggers, **Then** each Chore independently evaluates the new issue against its own last-run timestamp and increments its own counter accordingly.

---

### User Story 4 — Counter Reset After Chore Execution (Priority: P2)

As a project maintainer, I want a Chore's qualifying issue counter to reset to zero immediately after it successfully executes, so that the counter starts fresh from that point and accurately tracks progress toward the next trigger.

**Why this priority**: Counter reset is fundamental to the trigger cycle but is a downstream behavior that depends on the filtering fix. Once filtering is correct, reset behavior ensures ongoing accuracy.

**Independent Test**: Can be fully tested by letting a Chore reach its threshold and fire, then verifying the counter resets to 0 and begins accumulating again from only new qualifying Parent Issues created after the execution.

**Acceptance Scenarios**:

1. **Given** a Chore with "Every 5 issues" has reached its threshold and fires, **When** the execution completes successfully, **Then** the tile counter resets to 0.
2. **Given** a Chore has just reset after execution, **When** 2 new qualifying Parent Issues are created, **Then** the tile counter shows 2 (counting only issues created after the most recent execution).
3. **Given** a Chore fires and resets, **When** the user views the Chores page, **Then** the counter reflects only issues created after the reset timestamp, not any issues counted in the previous cycle.

---

### Edge Cases

- What happens when a Chore has never been executed and has no last-run timestamp? The system should count all qualifying Parent Issues created since the Chore's own creation date as the baseline.
- What happens when multiple qualifying Parent Issues are created simultaneously (e.g., bulk creation)? All qualifying issues created after the last-run timestamp must be counted, regardless of how closely their creation times overlap.
- What happens when a Chore's threshold is set to 1? The Chore should trigger on the very next qualifying Parent Issue, and the counter should briefly show 1 before the Chore fires and resets.
- What happens when a Parent Issue is reclassified as a Sub-Issue after it was already counted? The counter should reflect the current state of issue relationships at the time of evaluation — if an issue is now a Sub-Issue, it should not count.
- What happens when a GitHub Issue has no explicit parent-child metadata? Issues without parent-child linkage should be treated as top-level Parent Issues (qualifying) unless they are tagged or classified as Chores.
- What happens when a Chore-generated issue is later edited to remove its Chore classification? The system should evaluate classification at the time of counter evaluation — if the issue is no longer classified as a Chore, it would qualify as a Parent Issue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST count only GitHub Parent Issues created after the last-run timestamp of a given Chore when evaluating the "Every X Issues" trigger condition.
- **FR-002**: System MUST exclude all issues tagged or classified as Chores from the "Every X Issues" counter, regardless of whether they are parent or child issues.
- **FR-003**: System MUST exclude all Sub-Issues (GitHub child/sub-issues identified by parent-child relationship metadata) from the "Every X Issues" counter — only top-level, non-Chore GitHub issues qualify.
- **FR-004**: System MUST use the same filtered issue count for both the visual counter displayed on the Chore tile and the internal trigger evaluation logic, ensuring consistency between what the user sees and when the Chore fires.
- **FR-005**: System MUST scope the counter independently per Chore — each Chore tracks its own count from its own last-run timestamp, so one Chore's execution does not affect another Chore's counter.
- **FR-006**: System MUST reset the qualifying issue counter for a Chore to zero (re-anchoring the baseline timestamp to the current time) immediately after that Chore successfully executes.
- **FR-007**: System SHOULD identify Sub-Issues using GitHub's issue relationship metadata (parent/child linkage via sub-issue relationships or tracked-in relationships) to reliably exclude them from the count.
- **FR-008**: System MUST treat issues without any parent-child relationship metadata as top-level Parent Issues (qualifying), unless they are classified as Chores.
- **FR-009**: For a Chore that has never been executed, the system MUST use the Chore's creation timestamp as the baseline for counting qualifying Parent Issues.
- **FR-010**: System MUST evaluate issue classification (Chore status, Sub-Issue status) at the time of counter evaluation, reflecting the current state of each issue.

### Key Entities

- **Chore**: A recurring task configuration with a trigger condition (e.g., "Every X issues"), a last-run timestamp, an execution count, and a creation timestamp. Each Chore independently tracks its own qualifying issue count.
- **Qualifying Parent Issue**: A GitHub issue that (1) is not classified or tagged as a Chore, (2) is not a Sub-Issue (has no parent issue relationship), and (3) was created after the relevant Chore's last-run timestamp (or creation timestamp if never run).
- **Counter**: A derived value representing the number of Qualifying Parent Issues since a specific Chore's last run. Used for both tile display and trigger evaluation. Not stored separately — computed from the filtered issue set each time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Chore tile counter displays only the count of qualifying Parent Issues (excluding Chores and Sub-Issues) created since that Chore last ran, with 100% accuracy across all Chore tiles on the page.
- **SC-002**: The trigger evaluation fires a Chore at exactly the configured threshold based on qualifying Parent Issues only — never early (due to inflated counts from Chores or Sub-Issues) and never late (due to missed qualifying issues).
- **SC-003**: Creating a Sub-Issue or a Chore-generated issue does not increment any Chore's "Every X Issues" counter, verified by the counter remaining unchanged before and after such issue creation.
- **SC-004**: Each Chore's counter operates independently — executing one Chore does not alter the counter value of any other Chore on the page.
- **SC-005**: After a Chore successfully executes, its counter resets to 0 and begins accumulating from only new qualifying Parent Issues created after the execution timestamp.
- **SC-006**: The counter displayed on the tile and the value used for trigger evaluation are always identical for any given Chore at any point in time.

## Assumptions

- GitHub's issue relationship metadata (parent/child linkage, sub-issue relationships) is accessible and reliable for determining whether an issue is a Sub-Issue.
- Chores are identifiable by a consistent classification mechanism (label, type, or metadata field) that can be used to filter them out of the qualifying issue set.
- The existing Chore data model already stores a last-run timestamp (or equivalent) per Chore, and a creation timestamp for Chores that have never been executed.
- The counter is computed dynamically (not stored as a separate persisted value) to ensure it always reflects the current state of issues and their classifications.
- The development base branch is `copilot/fix-chores-page-counters` as indicated in the parent issue metadata.
