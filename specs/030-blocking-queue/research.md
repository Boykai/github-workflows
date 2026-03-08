# Research: Blocking Queue — Serial Issue Activation & Branch Ancestry Control

**Feature**: 030-blocking-queue | **Date**: 2026-03-08

## R1: Blocking Queue State Machine Design

**Task**: Determine the state machine for the blocking queue that supports serial activation, batch rules, and correct transitions.

**Decision**: Use a linear state machine with four states: `pending → active → in_review → completed`. Transitions are triggered by external events (enqueue, agent assignment, status change, issue closure). The `try_activate_next()` function is the central dispatcher called on every state transition that may unblock pending issues.

**Rationale**: The spec defines four queue statuses (FR-001) with clear transition triggers. A linear state machine is the simplest model that captures all required behavior. The `try_activate_next()` function consolidates all activation logic into a single entry point, making it easy to test (8-issue scenario) and reason about. Activation rules are:

- No open blocking issues → activate all pending non-blocking issues immediately
- Open blocking issue exists → serial activation: blocking issues activate alone, non-blocking issues activate together up to the next blocking entry
- On `in_review` or `completed` transitions → call `try_activate_next()` to evaluate the next batch

**Alternatives Considered**:

- **Event-driven pub/sub**: Rejected — adds infrastructure complexity (message broker) for what is a synchronous, single-process decision. The blocking queue is local to one container.
- **Priority queue with numeric weights**: Rejected — the spec uses creation order (FIFO), not priority-based ordering. YAGNI per Constitution Principle V.

---

## R2: Concurrency Control Strategy

**Task**: Determine how to prevent double-activation race conditions when multiple status transitions happen concurrently for the same repo.

**Decision**: Use an `asyncio.Lock` per `repo_key`, stored in a `dict[str, asyncio.Lock]` within the blocking queue service. All state-changing operations (`enqueue_issue`, `mark_active`, `mark_in_review`, `mark_completed`, `try_activate_next`) acquire the repo-specific lock before executing. SQLite transactions (`BEGIN IMMEDIATE`) are used for atomicity within the database layer.

**Rationale**: The system runs as a single Python process (FastAPI + uvicorn). `asyncio.Lock` is the correct concurrency primitive for async Python — it prevents two coroutines from executing the activation logic simultaneously for the same repo. Per-repo locks ensure that operations on different repos do not contend, preserving throughput. SQLite `BEGIN IMMEDIATE` prevents write conflicts at the database level, complementing the application-layer lock. This matches the spec's requirement for "per-repository locking and database transactions" (FR-012).

**Alternatives Considered**:

- **Global lock**: Rejected — blocks all repos when any repo's queue is being processed. Poor throughput for multi-repo deployments.
- **Database-only locking (EXCLUSIVE transactions)**: Rejected — SQLite in WAL mode allows concurrent readers but only one writer; EXCLUSIVE blocks all reads too. The application-layer lock is lighter and sufficient for single-process.
- **Distributed lock (Redis/file-based)**: Rejected — system is single-process; distributed locking adds unnecessary complexity.

---

## R3: Branch Ancestry Resolution Strategy

**Task**: Determine how the system decides which branch a newly activated issue should use as its base.

**Decision**: When activating an issue, query the blocking queue for the oldest open (active or in_review) blocking issue. If one exists, use that issue's `parent_branch` (the branch created for it). If no open blocking issues exist, return `"main"`. This is implemented in `get_base_ref_for_issue()` and called by the orchestrator during first agent assignment.

**Rationale**: The spec requires "all branch from the oldest open blocking issue's branch" (not chained) — see User Story 2, Acceptance Scenario 3. This flat ancestry model is simpler than chaining (where each issue branches from the previous) because:

- No cascading merge dependencies when intermediate issues complete
- A single query (`ORDER BY created_at ASC LIMIT 1`) resolves the base branch
- When the oldest blocking issue completes, the base simply shifts to the next oldest, or reverts to `main`

**Alternatives Considered**:

- **Chained branching (each from previous)**: Rejected — creates merge dependency chains; if issue #3 completes before issue #2, the merge target is unclear. Spec explicitly says "not chained."
- **Always branch from main, rebase later**: Rejected — defeats the purpose of branch ancestry control; rebasing is error-prone and not part of the spec.

---

## R4: `#block` Chat Command Detection and Stripping

**Task**: Determine how to detect and strip `#block` from chat messages without disrupting downstream intent processing.

**Decision**: Add a pre-processing step in `chat.py` at Priority 0.5 (between `#agent` detection and feature-request handling). Use a case-insensitive regex `r'\s*#block\b'` to detect `#block` anywhere in the message. Strip all occurrences before passing to downstream processing. Set an `is_blocking=True` flag that propagates through `confirm_proposal()` → `execute_full_workflow()`.

**Rationale**: The spec requires detection "anywhere in message content (not just prefix)" (FR-009). A regex-based approach handles edge cases: `#block` at the beginning, middle, or end of a message, with or without surrounding whitespace. Case-insensitive matching handles `#Block`, `#BLOCK`, etc. Stripping before downstream processing ensures the `#block` text doesn't confuse intent detection (e.g., being interpreted as part of a feature request). The existing chat processing pipeline already has a priority-based command detection pattern (`#agent` is highest priority); inserting `#block` at Priority 0.5 fits naturally.

**Alternatives Considered**:

- **Prefix-only detection (`message.startswith('#block')`)**: Rejected — spec explicitly says "anywhere in message content."
- **Separate `#block` command (not inline)**: Rejected — spec says `#block` should be detectable alongside other message content (e.g., "Fix the login page #block"), not as a standalone command.
- **Frontend-only detection (strip before sending)**: Rejected — backend must be the source of truth for is_blocking; frontend detection is supplementary for UI indicators only.

---

## R5: Blocking Flag Inheritance (Chore ← Pipeline)

**Task**: Determine how blocking flags propagate when a Chore is assigned to a Pipeline, and which takes precedence.

**Decision**: When triggering a Chore, the effective blocking flag is `chore.blocking OR pipeline.blocking`. If the Chore's own `blocking` flag is `True`, it's blocking regardless of pipeline. If the Chore's flag is `False`, check the assigned pipeline's `blocking` flag. If the pipeline is blocking, the issue inherits it. This is implemented in `trigger_chore()` in the chores service.

**Rationale**: The spec says "inherit the blocking flag from the assigned Pipeline when a Chore's own blocking flag is not set" (FR-010). User Story 3, Acceptance Scenario 3 confirms: "Chore has blocking=false but is assigned to a Pipeline with blocking=true → Pipeline's blocking flag takes precedence." The OR logic is the simplest interpretation: if either the Chore or its Pipeline says blocking, the result is blocking. Edge case: if the Pipeline is deleted, the Chore falls back to its own flag (Edge Case 7 in spec).

**Alternatives Considered**:

- **Pipeline always overrides Chore**: Rejected — spec says Chore can be blocking independently of its pipeline.
- **Chore always overrides Pipeline**: Rejected — spec says pipeline blocking applies to ALL issues, which includes chore-triggered issues.
- **Explicit `inherit` value on Chore blocking field**: Rejected — adds complexity; the OR logic achieves the same result without a three-state field. YAGNI.

---

## R6: WebSocket Notification Design

**Task**: Determine the structure and delivery mechanism for real-time blocking queue updates.

**Decision**: Use the existing `connection_manager.broadcast_to_project()` from `websocket.py` to send a `blocking_queue_updated` event. The payload includes: `repo_key`, `activated_issues` (list of issue numbers), `completed_issues` (list of issue numbers), and `current_base_branch` (string). For toast notifications, the frontend listens for this event and displays "Issue #X is now active — agents starting" for each newly activated issue.

**Rationale**: The existing WebSocket infrastructure (`ConnectionManager` in `websocket.py`) already supports per-project broadcasting. The blocking queue operates at the repo level, but projects map to repos, so broadcasting to the project associated with the repo is the correct delivery path. The payload matches the spec's requirement (FR-014). The toast notification (FR-017) is triggered on the frontend by filtering `activated_issues` for issues that were previously pending.

**Alternatives Considered**:

- **Server-Sent Events (SSE)**: Rejected — WebSocket infrastructure already exists and is used for other real-time updates. Adding SSE would be a second real-time channel, adding complexity.
- **Polling-based updates**: Rejected — adds latency; spec requires near-real-time notification (SC-007: within 5 seconds).
- **Per-issue WebSocket events**: Rejected — one event per queue change is more efficient than separate events per issue; the frontend can batch-process the list.

---

## R7: Restart Recovery Strategy

**Task**: Determine how the system recovers from container restarts where activation cascades may have been missed.

**Decision**: On polling loop startup (in `copilot_polling/pipeline.py`), query all repositories that have non-completed queue entries and call `try_activate_next(repo_key)` for each. This catches any pending issues that should have been activated during downtime (e.g., an issue transitioned to "in review" but the activation cascade didn't fire because the container was down).

**Rationale**: The queue state is fully persisted in SQLite (FR-011). The `try_activate_next()` function is idempotent — calling it when no pending issues need activation is a no-op. Running it on startup for all repos with active queues is safe and ensures no issues are stuck in "pending" forever. The spec requires recovery "within 30 seconds of startup" (SC-008), which is achievable with a simple sequential scan.

**Alternatives Considered**:

- **Background recovery task on a timer**: Rejected — startup-time recovery is simpler and sufficient; a periodic timer adds complexity for the same outcome (idempotent activation check).
- **Write-ahead log for pending activations**: Rejected — the SQLite table itself is the log; re-running `try_activate_next()` achieves the same recovery without additional infrastructure.

---

## R8: Migration Strategy for Existing Tables

**Task**: Determine how to add the `blocking` column to existing `pipeline_configs` and `chores` tables without data loss.

**Decision**: Use `ALTER TABLE ... ADD COLUMN` statements in the new migration (`017_blocking_queue.sql`). Both columns use `INTEGER NOT NULL DEFAULT 0`, which is safe for existing rows — all existing chores and pipelines will default to non-blocking. The migration also creates the new `blocking_queue` table.

**Rationale**: SQLite supports `ALTER TABLE ADD COLUMN` with default values, which is applied instantly without rewriting the table. Existing rows automatically get the default value (0 = false). This is the standard migration pattern used throughout the project (e.g., `016_chores_enhancements.sql` adds columns to the chores table). No data migration is needed because the feature is additive — existing chores and pipelines are non-blocking by default.

**Alternatives Considered**:

- **Create new tables and migrate data**: Rejected — unnecessary for adding a single column with a default value.
- **Store blocking flag in a separate table**: Rejected — adds JOIN complexity for every chore/pipeline read; a column on the existing table is simpler and follows the established pattern.
