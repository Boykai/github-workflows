# Research: Auto Merge — Automatically Squash-Merge Parent PRs When Pipelines Complete

**Feature**: `001-auto-merge-pipelines` | **Date**: 2026-03-22 | **Plan**: [plan.md](./plan.md)

## Research Tasks

### R-001: Auto Merge Flag Persistence Pattern

**Context**: The `auto_merge` boolean needs to be stored at both the project and pipeline levels, following the same dual-storage pattern used by `queue_mode`.

**Decision**: Mirror the `queue_mode` implementation exactly.

**Rationale**:
- `queue_mode` is stored as `INTEGER NOT NULL DEFAULT 0` in the `project_settings` table (migration `031_queue_mode.sql`).
- The canonical value lives on the `__workflow__` row (`github_user_id = '__workflow__'`), which is the single source of truth for orchestrator reads.
- The API handler (`settings.py`) syncs `queue_mode` to both the user row and the `__workflow__` row on update, and invalidates the in-memory cache.
- `settings_store.py` exposes a helper (`is_queue_mode_enabled()`) with a 10-second TTL in-memory cache to avoid repeated DB reads.
- `ProjectBoardConfig` Pydantic model includes `queue_mode: bool = False`.

**Implementation**:
- Add `auto_merge INTEGER NOT NULL DEFAULT 0` to `project_settings` (new migration `034_auto_merge.sql`).
- Add `auto_merge` to `PROJECT_SETTINGS_COLUMNS` tuple in `settings_store.py`.
- Add `is_auto_merge_enabled()` with the same TTL cache pattern.
- Add `auto_merge: bool = False` to `ProjectBoardConfig` model.
- Update API handler to sync `auto_merge` to `__workflow__` row on update.
- For pipeline-level: add `auto_merge` field to `PipelineState` dataclass and serialize in metadata JSON via `pipeline_state_store.py`.

**Alternatives Considered**:
- Separate `auto_merge_settings` table: Rejected — unnecessary complexity for a single boolean; would diverge from the established pattern.
- Store only in `board_display_config` JSON: Rejected — the `queue_mode` pattern deliberately uses a dedicated column for reliable orchestrator reads without JSON parsing.

---

### R-002: Merge Decision Point — Retroactive Auto Merge

**Context**: When Auto Merge is toggled on for a project with active pipelines, the spec requires retroactive activation via lazy check rather than eager in-memory state updates.

**Decision**: Check `is_auto_merge_enabled()` at the `_transition_after_pipeline_complete()` merge decision point, not at pipeline creation.

**Rationale**:
- The existing `_transition_after_pipeline_complete()` function in `pipeline.py` is the natural merge decision point — it already handles status transitions, dequeue logic, and PR discovery.
- A lazy check avoids the complexity of iterating all active pipeline states on toggle change.
- The 10-second TTL cache ensures the setting is eventually consistent (same guarantee as `queue_mode`).
- Pipeline-level `auto_merge` is resolved at pipeline start via `execute_full_workflow()` and stored in `PipelineState.auto_merge`. The merge decision point checks `pipeline_state.auto_merge OR is_auto_merge_enabled(project_id)` — either being true activates the feature.

**Alternatives Considered**:
- Eager update of all pipeline states on toggle: Rejected — race conditions with concurrent pipeline advancement, unnecessary L1 cache churn.
- Store resolved flag only at pipeline start: Rejected — would miss retroactive activation for already-running pipelines.

---

### R-003: Human Agent Skip Mechanism

**Context**: When Auto Merge is active and the human agent is the last step in the pipeline, the human step must be skipped with an audit trail.

**Decision**: Intercept human agent assignment in `_advance_pipeline()` — when the next agent is `"human"` and it's the last step and auto_merge is active, mark it `AgentStepState.SKIPPED`, close the sub-issue, and proceed to pipeline completion.

**Rationale**:
- `AgentStepState.SKIPPED` already exists in the codebase (`models/agent.py`) with emoji ⏭.
- The `_advance_pipeline()` function in `pipeline.py` is where agent assignment happens. Adding a skip check before assignment is non-invasive.
- Sub-issue closure is already implemented for completed agents — the skip path just needs a different comment ("Skipped — Auto Merge enabled").
- The tracking table update already supports the SKIPPED state via markdown cell rendering.

**Alternatives Considered**:
- Remove human agent from pipeline configuration when auto_merge is enabled: Rejected — would alter the configured pipeline, making it impossible to audit what was skipped.
- Skip at pipeline start (precompute skip): Rejected — the auto_merge flag may change between pipeline start and human step (retroactive toggle).

---

### R-004: _attempt_auto_merge() Function Design

**Context**: A new function is needed to orchestrate the actual squash-merge after pipeline completion.

**Decision**: Create `backend/src/services/copilot_polling/auto_merge.py` with an `_attempt_auto_merge()` function that returns a structured result (`merged`, `devops_needed`, `merge_failed`).

**Rationale**:
- Separation into a dedicated module follows the existing service structure (compare `completion.py` for child PR merges, `recovery.py` for error recovery).
- The function reuses existing primitives:
  - `_discover_main_pr_for_review()` for PR discovery (multi-strategy).
  - `merge_pull_request()` GraphQL mutation (already defaults to SQUASH).
  - `mark_pr_ready_for_review()` for draft → ready conversion.
- New GitHub API helpers are needed:
  - `get_check_runs_for_ref()` — REST `GET /repos/{owner}/{repo}/commits/{ref}/check-runs`.
  - `get_pr_mergeable_state()` — GraphQL query for `PR.mergeable` field.

**Return Value Design**:
```python
@dataclass
class AutoMergeResult:
    status: Literal["merged", "devops_needed", "merge_failed"]
    pr_number: int | None = None
    merge_commit: str | None = None
    error: str | None = None
    context: dict | None = None  # CI failure details for devops dispatch
```

**Alternatives Considered**:
- Inline in `_transition_after_pipeline_complete()`: Rejected — function is already complex; separation enables unit testing.
- Use existing `_merge_child_pr_if_applicable()`: Rejected — that function merges child PRs into parent branches, not parent PRs into the default branch. Different merge targets and different pre-merge checks (CI status, mergeability).

---

### R-005: DevOps Agent Design

**Context**: A specialized repository agent for CI failure recovery, discoverable by the existing agent scanning mechanism.

**Decision**: Create `.github/agents/devops.agent.md` with YAML frontmatter matching the existing agent file format.

**Rationale**:
- The `list_available_agents()` function in `agents.py` automatically discovers `*.agent.md` files in `.github/agents/`.
- It parses YAML frontmatter for `name`, `description`, and `icon`/`icon_name` fields.
- The agent slug is derived from the filename: `devops.agent.md` → slug `devops`.
- No backend code changes are needed for discovery — this is the designed extensibility point.
- The system prompt should specialize the agent for: reading CI logs, identifying test failures, resolving merge conflicts, applying targeted fixes, and re-triggering checks.

**Alternatives Considered**:
- Built-in agent (hardcoded in `BUILTIN_AGENTS`): Rejected — requires backend code changes; repository agents are the designed extensibility mechanism.
- External service/webhook: Rejected — unnecessary infrastructure; Copilot dispatch handles agent execution.

---

### R-006: CI Failure Detection via Webhooks

**Context**: GitHub sends `check_run` and `check_suite` webhook events when CI checks complete. These must be routed to DevOps agent dispatch for auto_merge-enabled pipelines.

**Decision**: Add Pydantic models for `CheckRunEvent` and `CheckSuiteEvent` in `webhook_models.py`; add routing in `webhooks.py` for `check_run` (action=completed, conclusion=failure/timed_out) and `check_suite` (action=completed, conclusion=failure).

**Rationale**:
- The existing webhook handler (`POST /github`) already parses `x_github_event` header and routes to handlers by event type.
- Existing Pydantic models (`PullRequestEvent`, `IssuesEvent`) provide the pattern for new event models.
- The handler must:
  1. Parse the event and extract the PR association (via `check_run.pull_requests[]` or `check_suite.pull_requests[]`).
  2. Look up whether the PR belongs to an auto_merge-enabled pipeline (query pipeline state store).
  3. Check deduplication: skip if DevOps agent is already active on the pipeline.
  4. Dispatch the DevOps agent via standard Copilot dispatch.

**Alternatives Considered**:
- Poll CI status periodically: Rejected — wasteful API calls; webhooks are the designed event delivery mechanism.
- Use GitHub Actions workflow_run event: Rejected — more limited than check_run/check_suite; doesn't cover all CI systems.

---

### R-007: DevOps Retry Cap and Completion Detection

**Context**: DevOps agent retries must be capped at 2 per pipeline. Completion is detected via the "devops: Done!" marker.

**Decision**: Track attempts in `pipeline.metadata['devops_attempts']` (integer). On DevOps completion (detected via Done! marker in the polling loop), retry `_attempt_auto_merge()`. After 2nd failed attempt, mark pipeline ERROR and notify user.

**Rationale**:
- `PipelineState` already has a `metadata` dict for extensible key-value storage, serialized to JSON in `pipeline_state_store.py`.
- The existing agent completion detection (`_check_agent_done_on_sub_or_parent()` in `helpers.py`) already checks for `{agent}: Done!` markers.
- The retry cap prevents infinite loops — 2 attempts balance automated recovery with avoiding wasted compute.

**Alternatives Considered**:
- Separate retry counter table: Rejected — metadata dict is already designed for this purpose.
- Unlimited retries with backoff: Rejected — spec explicitly requires cap of 2.

---

### R-008: WebSocket Broadcast for Auto Merge Events

**Context**: Three new event types must be broadcast via the existing WebSocket infrastructure.

**Decision**: Use the existing `connection_manager.broadcast_to_project()` pattern with new event types: `auto_merge_completed`, `auto_merge_failed`, `devops_triggered`.

**Rationale**:
- The `ConnectionManager` class in `websocket.py` already supports arbitrary JSON payloads via `broadcast_to_project(project_id, message)`.
- Existing events (`agent_completed`, `agent_assigned`, `status_updated`) demonstrate the pattern.
- Frontend `useRealTimeSync.ts` handles WebSocket messages and can be extended to show toast notifications via sonner for the new event types.

**Event Payloads**:
```json
{
  "type": "auto_merge_completed",
  "issue_number": 42,
  "pr_number": 123,
  "merge_commit": "abc123",
  "timestamp": "2026-03-22T18:00:00Z"
}

{
  "type": "auto_merge_failed",
  "issue_number": 42,
  "pr_number": 123,
  "error": "Branch protection requires 2 reviews",
  "timestamp": "2026-03-22T18:00:00Z"
}

{
  "type": "devops_triggered",
  "issue_number": 42,
  "pr_number": 123,
  "attempt": 1,
  "reason": "CI check 'tests' failed",
  "timestamp": "2026-03-22T18:00:00Z"
}
```

**Alternatives Considered**:
- Separate notification service: Rejected — the existing broadcast infrastructure is sufficient.
- Email notifications: Rejected — spec requires real-time toast notifications in the UI.

---

### R-009: GitHub API Helpers for Merge Verification

**Context**: Two new GitHub API calls are needed for pre-merge verification.

**Decision**: Add `get_check_runs_for_ref()` and `get_pr_mergeable_state()` to `pull_requests.py` mixin.

**Implementation**:

1. **`get_check_runs_for_ref(ref)`**: REST `GET /repos/{owner}/{repo}/commits/{ref}/check-runs`
   - Uses existing `rest_request()` method on `GitHubProjectsService`.
   - Returns list of check runs with their `status` and `conclusion` fields.
   - Filters to only `completed` check runs; checks all have `conclusion` in (`success`, `neutral`, `skipped`).

2. **`get_pr_mergeable_state(pr_number)`**: GraphQL query for `pullRequest(number: N) { mergeable }`.
   - Uses existing `_graphql()` method.
   - Returns `MergeableState` enum: `MERGEABLE`, `CONFLICTING`, `UNKNOWN`.
   - `UNKNOWN` triggers a short wait and retry (GitHub computes mergeability asynchronously).

**Alternatives Considered**:
- Use REST API for mergeability: Rejected — REST `GET /repos/{owner}/{repo}/pulls/{number}` includes `mergeable` but it's nullable and less reliable than GraphQL.
- Skip CI check verification: Rejected — merge would fail anyway due to branch protection, but a pre-check gives better error messages.

---

### R-010: Concurrent DevOps Dispatch Serialization

**Context**: Multiple pipelines on the same project with simultaneous CI failures could cause competing DevOps agent invocations.

**Decision**: Use the existing `get_project_launch_lock(project_id)` pattern to serialize DevOps dispatches per project.

**Rationale**:
- The lock is already used for queue-mode pipeline launch serialization.
- DevOps dispatch is a similar per-project serialization need.
- A lightweight `_devops_active` flag in pipeline metadata serves as the deduplication check (FR-009).
- The lock scope covers: check dedup → dispatch → set flag (atomic window).

**Alternatives Considered**:
- Global DevOps dispatch lock: Rejected — too coarse; unrelated projects should not block each other.
- Separate `_devops_launch_locks` dict: Could work but unnecessary given the existing lock infrastructure serves the same purpose (per-project serialization).

---

### R-011: Retroactive Toggle UX — Confirmation Dialog

**Context**: When enabling Auto Merge on a project with active pipelines, the UI must show a confirmation dialog listing affected pipelines.

**Decision**: Before calling `updateSettings({ auto_merge: true })`, query active pipeline count and show a confirmation dialog if count > 0.

**Rationale**:
- The frontend already has access to pipeline states via the board data.
- Active pipelines can be counted from the existing `BoardItem` data (items with non-terminal statuses).
- The confirmation dialog follows standard React patterns (state-controlled modal with confirm/cancel).
- No new API endpoint needed — the active pipeline count is derivable from existing board data.

**Alternatives Considered**:
- Dedicated `/api/v1/projects/{id}/active-pipeline-count` endpoint: Rejected — the data is already available on the frontend via board items.
- Skip confirmation entirely: Rejected — spec explicitly requires it (FR-015, User Story 4, Scenario 3).
