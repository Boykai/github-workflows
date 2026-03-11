# Feature Specification: Enforce Blocking Queue in Polling Loop & Fix Branch Ancestry

**Feature Branch**: `035-blocking-queue-guard`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Plan: Enforce Blocking Queue in Polling Loop & Fix Branch Ancestry"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Blocked Issues Stay Blocked During Polling (Priority: P1)

When an issue is PENDING in the blocking queue (waiting on a predecessor issue), the polling loop must not start an agent pipeline for it. Currently, polling check functions (`check_backlog_issues`, `check_ready_issues`, `check_in_progress_issues`) process all issues without consulting the blocking queue, causing blocked issues to receive agent assignments prematurely.

**Why this priority**: This is the root cause bug. Blocked parent issues are getting agent pipelines started, leading to race conditions, wasted compute, and incorrect work. Without this fix, the blocking queue is effectively bypassed during normal polling.

**Independent Test**: Can be fully tested by creating two issues in a blocking relationship (A blocks B), verifying B stays PENDING and is skipped by every polling check function until A completes.

**Acceptance Scenarios**:

1. **Given** issue B is PENDING in the blocking queue (blocked by issue A), **When** `check_backlog_issues()` encounters issue B in the backlog, **Then** issue B is skipped and no pipeline is started for it.
2. **Given** issue B is PENDING in the blocking queue, **When** `check_ready_issues()` encounters issue B in the ready list, **Then** issue B is skipped and no pipeline is started for it.
3. **Given** issue B is PENDING in the blocking queue, **When** `check_in_progress_issues()` encounters issue B, **Then** issue B is skipped and no pipeline is started for it.
4. **Given** the blocking queue service is temporarily unavailable, **When** any polling check function attempts to determine if an issue is PENDING, **Then** the system fails open — the issue is allowed to proceed (not blocked), preserving backward compatibility for non-blocking-queue users.
5. **Given** issue A is ACTIVE (not PENDING) in the blocking queue, **When** any polling check function encounters issue A, **Then** issue A is processed normally and a pipeline may be started.

---

### User Story 2 - Recovery Fails Closed When Blocking Queue Is Unavailable (Priority: P1)

When the blocking queue service is temporarily unavailable during recovery, the system must skip recovery for that issue rather than allow a potentially incorrect agent assignment. Currently, the exception handler in `_should_skip_recovery()` falls through with `False` (allow recovery), which risks assigning agents to blocked issues during outages.

**Why this priority**: Tied with Story 1 as a critical safety fix. A false agent assignment during recovery can cause conflicting work and data corruption. Skipping a recovery is always safer than a false assignment.

**Independent Test**: Can be fully tested by simulating a blocking queue service exception during recovery and verifying the issue is skipped.

**Acceptance Scenarios**:

1. **Given** the blocking queue service raises an exception during `_should_skip_recovery()`, **When** recovery evaluates whether to skip the issue, **Then** the system returns `True` (skip recovery) instead of `False` (allow recovery).
2. **Given** the blocking queue service is healthy, **When** `_should_skip_recovery()` checks a non-blocked issue, **Then** recovery proceeds normally.

---

### User Story 3 - Sweep Dispatches Agents for Newly Activated Entries (Priority: P2)

When `sweep_stale_entries()` marks stale entries as completed and activates the next queued issue, the system must dispatch an agent for each newly activated entry. Currently, `sweep_stale_entries()` activates entries in the database but the calling code in `_step_sweep_blocking_queue()` never dispatches agents, leaving activated issues stranded.

**Why this priority**: Without dispatch after sweep, activated issues sit idle until the next polling cycle happens to pick them up — or they may never be picked up at all. This creates a reliability gap in the blocking queue lifecycle.

**Independent Test**: Can be fully tested by creating a stale blocking queue entry, triggering a sweep, and verifying both that the entry is swept and that the newly activated issue receives an agent dispatch.

**Acceptance Scenarios**:

1. **Given** a stale entry exists in the blocking queue and a next queued issue is waiting, **When** `sweep_stale_entries()` marks the stale entry as completed, **Then** the return value includes both the swept issue numbers and the activated entries.
2. **Given** `_step_sweep_blocking_queue()` receives activated entries from the sweep, **When** it processes the sweep results, **Then** it calls `_activate_queued_issue()` for each activated entry, matching the existing dispatch pattern.
3. **Given** a sweep completes with no newly activated entries, **When** `_step_sweep_blocking_queue()` processes the results, **Then** no agent dispatch occurs and the system continues normally.

---

### User Story 4 - Branch Ancestry Uses Issue-Specific Blocking Source (Priority: P2)

When determining the base branch reference for a blocked issue, the system must use the specific `blocking_source_issue` from the issue's own queue entry rather than the global oldest blocker. Currently, `_determine_base_ref()` uses the global oldest blocker, which can produce incorrect branch ancestry when multiple blocking relationships exist.

**Why this priority**: Incorrect branch ancestry causes issues to branch from `main` instead of from their actual blocking predecessor's branch, leading to merge conflicts and lost work when the predecessor's changes aren't inherited.

**Independent Test**: Can be fully tested by creating a chain A → B → C where B blocks C, and verifying C's base branch is resolved to B's branch (not A's or `main`).

**Acceptance Scenarios**:

1. **Given** issue C has a queue entry with `blocking_source_issue` pointing to issue B, **When** `_determine_base_ref()` resolves the base branch for issue C, **Then** the base branch is issue B's branch, not the global oldest blocker's branch.
2. **Given** issue C has a queue entry but the `blocking_source_issue` lookup fails, **When** `_determine_base_ref()` resolves the base branch, **Then** the system falls back to the existing `get_base_ref_for_issue()` behavior.
3. **Given** issue C has no queue entry (not in the blocking queue), **When** `_determine_base_ref()` resolves the base branch, **Then** the system uses the existing logic without any blocking queue lookup.

---

### User Story 5 - Recovery Logs Deferred Dispatch Explicitly (Priority: P3)

When `recover_all_repos()` activates entries in the blocking queue during recovery, it must log an explicit message noting that agent dispatch is deferred to the polling loop, since recovery lacks the `access_token` needed to dispatch agents directly.

**Why this priority**: This is an observability improvement. The Phase 1 guards prevent double-assignment, but without explicit logging, operators cannot distinguish between "dispatch happened" and "dispatch deferred" when troubleshooting.

**Independent Test**: Can be fully tested by triggering recovery with blocking queue entries and verifying the log output contains the deferred dispatch message.

**Acceptance Scenarios**:

1. **Given** `recover_all_repos()` activates an entry in the blocking queue, **When** the activation completes, **Then** an explicit log message states "agent dispatch deferred to polling loop" (or equivalent).
2. **Given** `recover_all_repos()` runs with no blocking queue entries to activate, **When** recovery completes, **Then** no deferred dispatch log message is emitted.

---

### Edge Cases

- What happens when the same issue is encountered by multiple polling check functions in the same cycle? Each function independently checks the blocking queue, so the issue is skipped by all of them — no double-processing risk.
- What happens when a blocking queue entry is marked completed between the guard check and the pipeline start? The pipeline start itself is idempotent; the worst case is a no-op pipeline reconstruction.
- What happens when `sweep_stale_entries()` activates an entry but `_activate_queued_issue()` fails? The entry remains in ACTIVE state in the database and will be picked up by the next polling cycle.
- What happens when the `blocking_source_issue` in a queue entry points to an issue that has been deleted? The `get_base_ref_for_entry()` function falls back to `get_base_ref_for_issue()`, which uses the existing fallback chain.
- What happens when multiple issues are activated in a single sweep? Each activated entry is dispatched independently; failures in one do not block dispatch of others.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a shared guard function that checks whether a given issue is PENDING in the blocking queue for a given repository.
- **FR-002**: The shared guard function MUST fail open on exception — returning `False` (not pending) when the blocking queue service is unavailable — to avoid breaking non-blocking-queue users.
- **FR-003**: The `check_backlog_issues()` polling function MUST skip any issue that is PENDING in the blocking queue before attempting pipeline reconstruction.
- **FR-004**: The `check_ready_issues()` polling function MUST skip any issue that is PENDING in the blocking queue before attempting pipeline processing.
- **FR-005**: The `check_in_progress_issues()` polling function MUST skip any issue that is PENDING in the blocking queue before attempting pipeline processing.
- **FR-006**: The `_should_skip_recovery()` exception handler MUST fail closed — returning `True` (skip recovery) when the blocking queue service raises an exception — to prevent false agent assignments.
- **FR-007**: The `sweep_stale_entries()` function MUST return activated entries alongside swept issue numbers so callers can dispatch agents.
- **FR-008**: The `_step_sweep_blocking_queue()` function MUST iterate over activated entries returned by the sweep and dispatch agents for each using the existing `_activate_queued_issue()` pattern.
- **FR-009**: The `recover_all_repos()` function MUST log an explicit message noting that agent dispatch is deferred to the polling loop when it activates blocking queue entries.
- **FR-010**: The `_determine_base_ref()` function MUST look up the issue's own `blocking_source_issue` from its queue entry and use that specific issue's branch for ancestry resolution.
- **FR-011**: System MUST provide a `get_base_ref_for_entry()` function that resolves the base branch from an issue's queue entry via the `blocking_source_issue`, falling back to the existing `get_base_ref_for_issue()` when the lookup fails.

### Key Entities

- **Blocking Queue Entry**: Represents an issue's position in the blocking queue; has a status (PENDING, ACTIVE, COMPLETED) and a `blocking_source_issue` reference pointing to the predecessor issue.
- **Polling Check Functions**: Three functions (`check_backlog_issues`, `check_ready_issues`, `check_in_progress_issues`) that iterate over issues and decide whether to start or continue agent pipelines.
- **Recovery Handler**: The `_should_skip_recovery()` function that decides whether to skip recovery for an issue based on its blocking queue state.
- **Sweep Process**: The `sweep_stale_entries()` function that cleans up stale blocking queue entries and activates the next queued issue.
- **Branch Ancestry Resolver**: The `_determine_base_ref()` function that determines which branch a new issue's work should be based on.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: No PENDING issue in the blocking queue receives an agent pipeline start during normal polling — 100% of PENDING issues are skipped by all three polling check functions.
- **SC-002**: When the blocking queue service is unavailable during polling, issues proceed normally (fail-open) — zero additional pipeline failures caused by blocking queue outages.
- **SC-003**: When the blocking queue service is unavailable during recovery, issues are skipped (fail-closed) — zero false agent assignments occur during blocking queue outages.
- **SC-004**: Every issue activated by `sweep_stale_entries()` receives an agent dispatch within the same sweep cycle — zero activated issues are left stranded without dispatch.
- **SC-005**: Issues with blocking predecessors branch from their specific predecessor's branch, not the global oldest blocker — branch ancestry is correct for 100% of chained blocking relationships.
- **SC-006**: All deferred dispatch events during recovery are logged with an explicit message — operators can distinguish deferred dispatch from actual dispatch in 100% of recovery scenarios.
- **SC-007**: The full existing test suite continues to pass with all changes applied — zero regressions introduced.

## Assumptions

- The existing blocking queue data model (PENDING, ACTIVE, COMPLETED statuses; `blocking_source_issue` field) is sufficient and does not require schema changes.
- The existing `mark_in_review()` and `mark_completed()` logic is already correct and does not need modification.
- The frontend UI already displays blocking state correctly and does not need changes.
- The `_activate_queued_issue()` function is the correct dispatch pattern to reuse in `_step_sweep_blocking_queue()`.
- Recovery lacks an `access_token` by design, so deferring agent dispatch to the polling loop is the correct architectural choice rather than threading tokens through recovery.

## Scope Boundaries

### In Scope

- Adding blocking queue guards to all three polling check functions
- Fixing the recovery exception handler fail-through direction
- Fixing `sweep_stale_entries()` return value to include activated entries
- Adding agent dispatch in `_step_sweep_blocking_queue()` for activated entries
- Adding deferred dispatch logging in `recover_all_repos()`
- Hardening `_determine_base_ref()` to use issue-specific blocking source
- Adding `get_base_ref_for_entry()` helper function

### Out of Scope

- Frontend changes (UI already displays blocking state correctly)
- Database schema changes (model is sufficient)
- Core `mark_in_review()` / `mark_completed()` logic changes (already correct)
- `access_token` threading through recovery paths
