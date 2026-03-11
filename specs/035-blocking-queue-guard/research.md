# Research: Enforce Blocking Queue in Polling Loop & Fix Branch Ancestry

**Branch**: `035-blocking-queue-guard` | **Date**: 2026-03-11

## Research Tasks & Findings

### R-001: Blocking Queue Store API and Entry Lifecycle

**Context**: The shared guard function needs to look up an issue's blocking queue status. Need to confirm the store API, status enum values, and whether lookups are synchronous (in-memory) or require I/O.

**Findings**:
- `backend/src/services/blocking_queue.py:10-16`: `BlockingQueueStatus` is a `StrEnum` with values `PENDING`, `ACTIVE`, `IN_REVIEW`, `COMPLETED`.
- `backend/src/services/blocking_queue.py:49`: `get_entry(repo_key, issue_number) -> BlockingQueueEntry | None` delegates to `store.get_by_issue()` — an async function backed by aiosqlite.
- `backend/src/services/blocking_queue.py:19-33`: `BlockingQueueEntry` is a Pydantic `BaseModel` with fields `id`, `repo_key`, `issue_number`, `project_id`, `is_blocking`, `queue_status`, `parent_branch`, `blocking_source_issue`, `created_at`, `activated_at`, `completed_at`.
- The store is initialized once at app startup; lookups go through aiosqlite which keeps the DB in memory with WAL mode — effectively an in-memory lookup with async wrapper.

**Decision**: Use `get_entry()` as the lookup API for the guard function. Check `entry.queue_status == BlockingQueueStatus.PENDING` to determine if the issue should be skipped.

**Rationale**:
1. `get_entry()` is the canonical public API — avoids coupling to store internals.
2. The async overhead is negligible since aiosqlite runs in-memory with WAL mode.
3. Checking for PENDING specifically (rather than "not ACTIVE") ensures only truly blocked issues are skipped.

**Alternatives Considered**:
- **Direct store access**: Rejected — violates the service layer abstraction; `get_entry()` already wraps the store call cleanly.
- **Batch lookup**: Rejected — polling functions iterate one task at a time; batch would require restructuring all three functions for minimal gain.

---

### R-002: Existing Polling Loop Guard Patterns

**Context**: Need to understand how the three polling check functions currently iterate over tasks and where the guard should be inserted, to ensure consistency with existing patterns.

**Findings**:
- `backend/src/services/copilot_polling/pipeline.py:544`: `check_backlog_issues()` iterates `for task in backlog_tasks:` (line ~594), filtering by status field. Guard insertion point is before `_get_or_reconstruct_pipeline()` call.
- `backend/src/services/copilot_polling/pipeline.py:643`: `check_ready_issues()` follows the same pattern — iterate, filter, reconstruct pipeline.
- `backend/src/services/copilot_polling/pipeline.py:1860`: `check_in_progress_issues()` follows the same pattern with a different status filter.
- All three functions already have early `continue` statements for various skip conditions (e.g., missing issue number, wrong status). The blocking queue guard fits naturally as another early `continue`.
- The `repo_key` format is consistently `f"{owner}/{repo}"` across the codebase (confirmed in `blocking_queue.py`, `recovery.py`, `orchestrator.py`).

**Decision**: Insert the guard as an early `continue` inside each function's task iteration loop, immediately after existing skip conditions and before `_get_or_reconstruct_pipeline()`. Use a shared `_is_pending_in_blocking_queue(repo_key, issue_number)` helper to avoid duplication.

**Rationale**:
1. Matches the existing skip-condition pattern used in all three functions.
2. A shared helper keeps the check DRY across three call sites.
3. Placing it before pipeline reconstruction avoids wasted I/O for blocked issues.

**Alternatives Considered**:
- **Inline check in each function**: Rejected — three identical try/except blocks would violate DRY; a shared helper is cleaner.
- **Decorator-based guard**: Rejected — overengineered for a simple boolean check; functions have different signatures and loop structures.

---

### R-003: Fail-Open vs Fail-Closed Semantics in Existing Codebase

**Context**: The spec mandates fail-open for polling guards and fail-closed for recovery. Need to verify that these semantics align with existing codebase conventions and understand the rationale.

**Findings**:
- `backend/src/services/copilot_polling/recovery.py:136-143`: The `_should_skip_recovery()` exception handler currently returns `True` (skip) on blocking queue exceptions — this is the fail-closed behavior already implemented in the current branch.
- `backend/src/services/copilot_polling/pipeline.py:601-604`: The guard in `check_backlog_issues()` uses a try/except that logs and continues (fail-open) — consistent with the spec.
- The codebase convention is: polling paths fail open (avoid breaking existing non-blocking-queue workflows), recovery paths fail closed (a skipped recovery is safer than a false agent assignment).

**Decision**: Maintain the established convention. Polling guard: catch all exceptions, log at debug level, return `False` (not pending = allow processing). Recovery handler: catch all exceptions, log at debug level, return `True` (skip recovery).

**Rationale**:
1. Polling is the hot path — blocking queue outages should not cascade into breaking all pipeline processing for repositories that don't use the blocking queue.
2. Recovery is a cold path — missing one recovery cycle is low-cost; a false agent assignment during an outage is high-cost (conflicting work, data corruption).
3. Both patterns are already established in the current codebase, so this is consistent behavior.

**Alternatives Considered**:
- **Fail-closed everywhere**: Rejected — would break all non-blocking-queue users during any blocking queue service issue.
- **Fail-open everywhere**: Rejected — recovery without blocking queue checks risks assigning agents to blocked issues during outages.

---

### R-004: Sweep Return Value and Dispatch Pattern

**Context**: `sweep_stale_entries()` needs to return activated entries so `_step_sweep_blocking_queue()` can dispatch agents. Need to understand the current return type, how `mark_completed()` returns data, and the dispatch pattern in `_activate_queued_issue()`.

**Findings**:
- `backend/src/services/blocking_queue.py:472`: `sweep_stale_entries()` already returns `tuple[list[int], list[BlockingQueueEntry]]` — swept issue numbers and activated entries.
- `backend/src/services/blocking_queue.py:304`: `mark_completed()` returns `list[BlockingQueueEntry]` — the newly activated entries after marking one completed.
- `backend/src/services/copilot_polling/pipeline.py:2277`: `_activate_queued_issue()` takes `(access_token, project_id, owner, repo, issue_number)` and calls `orchestrator.assign_agent_for_status()` with backlog_status and agent_index=0.
- `backend/src/services/copilot_polling/polling_loop.py:253-276`: `_step_sweep_blocking_queue()` already destructures the sweep result into `(swept, activated)` and iterates over activated entries calling `_activate_queued_issue()`.

**Decision**: The sweep return type and dispatch pattern are already correctly implemented in the current branch. The contract documents the expected interface for validation.

**Rationale**:
1. `mark_completed()` already returns activated entries — sweep collects them naturally.
2. The `_activate_queued_issue()` function encapsulates the full dispatch logic including context setup and orchestrator call.
3. Per-entry error handling in the dispatch loop prevents one failure from blocking others.

**Alternatives Considered**:
- **Returning just issue numbers from sweep**: Rejected — callers would need to re-query the store for entry details needed by `_activate_queued_issue()`.
- **Dispatch inside `sweep_stale_entries()`**: Rejected — sweep is a service-layer function that lacks `access_token`; dispatch requires polling-loop context.

---

### R-005: Branch Ancestry Resolution and blocking_source_issue

**Context**: `_determine_base_ref()` needs to use the issue-specific `blocking_source_issue` rather than the global oldest blocker. Need to understand the current resolution chain and where `get_base_ref_for_entry()` fits.

**Findings**:
- `backend/src/services/workflow_orchestrator/orchestrator.py:879`: `_determine_base_ref()` returns `tuple[str, str, dict | None]` — (base_ref, current_head_sha, existing_pr).
- `backend/src/services/workflow_orchestrator/orchestrator.py:902-918`: Already calls `bq_service.get_base_ref_for_entry()` with the issue's own `repo_key` and `issue_number`. Falls back gracefully on exception.
- `backend/src/services/blocking_queue.py:367`: `get_base_ref_for_entry()` already exists — looks up the issue's entry, reads `blocking_source_issue`, resolves that source issue's branch. Falls back to `get_base_ref_for_issue()` when no entry or no source issue.
- `backend/src/services/blocking_queue.py:356`: `get_base_ref_for_issue()` uses the global oldest open blocking issue — the less specific fallback.

**Decision**: The entry-specific lookup via `get_base_ref_for_entry()` is already implemented. The contract documents the expected chain: entry lookup → source issue branch → fallback to global → fallback to "main".

**Rationale**:
1. Issue-specific lookup eliminates the race condition where multiple blocking chains exist and the global oldest blocker may not be the issue's actual predecessor.
2. The fallback chain ensures graceful degradation: entry-specific → global → "main".
3. Exception handling in `_determine_base_ref()` ensures blocking queue failures don't prevent branch creation.

**Alternatives Considered**:
- **Walking the full blocking chain**: Rejected — unnecessary complexity. The immediate `blocking_source_issue` is sufficient; chains resolve transitively as each predecessor completes.
- **Caching resolved branches**: Rejected — branches change infrequently and the lookup is fast; caching adds staleness risk.

---

### R-006: Recovery Dispatch Deferral and Logging

**Context**: `recover_all_repos()` activates entries but cannot dispatch agents because it lacks `access_token`. Need to confirm this is by design and that explicit logging is the correct approach.

**Findings**:
- `backend/src/services/blocking_queue.py:405-429`: `recover_all_repos()` calls `try_activate_next()` for each repo with non-completed entries. It has no access to `access_token` — it runs during app startup or periodic maintenance.
- The Phase 1 polling guards ensure that activated entries will be picked up by the next polling cycle — the guard skips PENDING issues but allows ACTIVE issues through.
- Agent dispatch requires `access_token` (needed for GitHub API calls to create branches, assign issues, etc.), which is only available in the polling loop context.

**Decision**: Add an explicit log message in `recover_all_repos()` when entries are activated, noting that agent dispatch is deferred to the polling loop. Use `logger.info()` level for visibility.

**Rationale**:
1. Operators troubleshooting "why didn't this issue get an agent?" need to distinguish between "dispatch happened" and "dispatch deferred".
2. The polling loop will pick up activated entries in the next cycle — the deferral is by design, not a bug.
3. `logger.info()` is appropriate for operational visibility without flooding debug logs.

**Alternatives Considered**:
- **Threading access_token into recovery**: Rejected — significant architectural change for a cold path; Phase 1 guards already handle the gap.
- **No logging (rely on polling logs)**: Rejected — creates a gap in the audit trail where activated-but-not-dispatched entries are invisible.
