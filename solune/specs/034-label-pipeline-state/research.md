# Research: GitHub Label-Based Agent Pipeline State Tracking

**Branch**: `034-label-pipeline-state` | **Date**: 2026-03-11

## Research Tasks & Findings

### R-001: Existing Label Infrastructure and Gap Analysis

**Context**: FR-001 through FR-003 require label constants and parsing utilities. The codebase already has label handling spread across multiple files — need to understand what exists and what's missing.

**Findings**:
- `backend/src/constants.py` defines `BLOCKING_LABEL = "blocking"` and a `LABELS` list of 26 allowed labels. The `with_blocking_label()` helper adds the blocking label conditionally. No pipeline-specific label constants exist.
- `backend/src/services/workflow_orchestrator/orchestrator.py` has `_build_labels()` (static method) that constructs labels from `IssueRecommendation` metadata (ai-generated, priority, size, blocking). This is the only label builder in the codebase.
- `backend/src/services/github_projects/issues.py` provides `update_issue_state()` with `labels_add` and `labels_remove` parameters — this is the only label write API.
- `backend/src/models/board.py` defines `Label(BaseModel)` with `id`, `name`, `color` fields. `BoardItem` has `labels: list[Label]`.
- `backend/src/models/task.py` defines `Task(BaseModel)` with NO labels field. `get_project_items()` in `projects.py` creates `Task` objects without mapping labels from the underlying GraphQL data.
- `BOARD_GET_PROJECT_ITEMS_QUERY` (used for the board view) already fetches `labels(first: 20) { nodes { id name color } }` for each issue. However, `GET_PROJECT_ITEMS_QUERY` (used by `get_project_items()` for polling) does not currently include labels — it must be extended with the same `labels(first: 20)` selection to propagate label data to `Task` objects.

**Decision**: Add pipeline label constants (`PIPELINE_LABEL_PREFIX`, `AGENT_LABEL_PREFIX`, `ACTIVE_LABEL`, `STALLED_LABEL`) and pure-function utilities (`extract_pipeline_config()`, `extract_agent_slug()`, `build_agent_label()`, `build_pipeline_label()`) to `constants.py`. This keeps label logic centralized alongside existing constants.

**Rationale**: 
1. `constants.py` already houses `BLOCKING_LABEL`, `LABELS`, and `with_blocking_label()` — pipeline labels are the same category.
2. Pure functions (no I/O, no side effects) keep utilities testable without mocks.
3. A separate `label_utils.py` was considered but rejected — the utilities are small (4 functions, ~20 lines each) and don't justify a new module.

**Alternatives Considered**:
- **Separate `label_utils.py` module**: Rejected — adds import indirection for 4 small functions. Constants and their associated parsers belong together.
- **Label utilities on a class**: Rejected — no state to manage, pure functions are simpler and more composable.

---

### R-002: Label Write Path — Atomic Swap Strategy

**Context**: FR-006 requires swapping `agent:<slug>` labels atomically. `update_issue_state()` accepts both `labels_add` and `labels_remove` in a single call, but the GitHub REST API executes these as separate requests (POST for add, DELETE for remove). Need to determine if this is sufficient.

**Findings**:
- `update_issue_state()` in `issues.py` (lines 107–165) performs label additions first (`POST /repos/{owner}/{repo}/issues/{issue_number}/labels`), then removals (`DELETE .../{label}`). This is NOT a single atomic operation at the GitHub API level.
- However, both operations are within a single async function call, minimizing the window of inconsistency.
- GitHub label operations are idempotent: adding an existing label is a no-op; removing a non-existent label returns 404 (handled gracefully by the existing error handling).
- The polling cycle interval (default 60s) means any transient inconsistency (both old and new `agent:` labels present) is resolved within one cycle.

**Decision**: Use existing `update_issue_state()` with both `labels_add` and `labels_remove` for agent label swaps. Accept the non-atomic window as acceptable given polling-cycle reconciliation.

**Rationale**:
1. The existing function already handles the two-step GitHub API limitation.
2. Polling cycle ensures eventual consistency within 60 seconds.
3. The fast-path reader should handle the edge case of multiple `agent:` labels by selecting the first match (consistent with contracts/label-fast-path.md and the `find_agent_label()` implementation).
4. Building a custom atomic swap would require the GraphQL mutations API, adding complexity without meaningful benefit.

**Alternatives Considered**:
- **GraphQL `updateIssue` mutation**: Rejected — the mutation replaces all labels (not add/remove), risking race conditions with user-applied labels.
- **Custom lock mechanism**: Rejected — over-engineering for a self-healing system with polling-cycle reconciliation.

---

### R-003: Task Model Label Propagation Strategy

**Context**: FR-010 requires labels in the Task model. Currently, `get_project_items()` creates `Task` objects without labels, but the underlying GraphQL response includes label data in `BoardItem`. Need to determine the most minimal change.

**Findings**:
- `get_project_items()` in `projects.py` (lines 145–225) builds `Task` objects manually from raw GraphQL response data. It does NOT use `BoardItem` as an intermediate — it parses the raw JSON directly.
- `BoardItem` in `board.py` has `labels: list[Label]` but is used by the board API endpoint, not by `get_project_items()`.
- The GraphQL query used by `get_project_items()` fetches `labels(first: 20) { nodes { id name color } }` — the data is in the response but ignored during Task construction.
- The `Task` model uses simple types: `str`, `int`, `list[str]`, `datetime`. Adding `list[Label]` would introduce a dependency on `board.py`'s Label model.

**Decision**: Add `labels: list[dict[str, str]] | None = None` to the Task model using simple dict representation (`{"name": "...", "color": "..."}`) rather than importing the `Label` Pydantic model. Map label data from GraphQL response during Task construction in `get_project_items()`.

**Rationale**:
1. Simple dict avoids cross-model coupling between `task.py` and `board.py`.
2. Label consumers (fast-path, polling steps) only need the `name` field — a full Pydantic model is unnecessary overhead.
3. Matches existing Task model convention of using primitive types.
4. The `is_sub_issue()` helper already handles labels as dicts with `.get("name", "")` pattern (see `helpers.py` line 28).

**Alternatives Considered**:
- **Import `Label` from board.py**: Rejected — creates model-to-model dependency; Task model should remain self-contained.
- **Separate `TaskLabel` model**: Rejected — adds a model for what is effectively a name+color pair.
- **`labels: list[str]`**: Rejected — loses color information needed by frontend rendering (FR-013).

---

### R-004: Fast-Path Reconstruction Design

**Context**: FR-011 requires building `PipelineState` from labels alone when both `pipeline:<config>` and `agent:<slug>` are present. Need to determine exactly how to construct the state and where to insert the fast-path.

**Findings**:
- `_get_or_reconstruct_pipeline()` in `pipeline.py` (lines 130–298) is the single entry point for pipeline state retrieval. Current flow: cache check → fetch issue body → parse tracking table → self-heal from sub-issues → reconstruct.
- `PipelineState` (in `workflow_orchestrator/models.py`) is a dataclass with fields: `issue_number`, `project_id`, `status`, `agents`, `current_agent_index`, `completed_agents`, `started_at`, `agent_sub_issues`, `original_status`, `target_status`, `execution_mode`.
- To build from labels, we need: (a) `pipeline:<config>` → look up PipelineConfig → get ordered agent list; (b) `agent:<slug>` → find index in agent list → set `current_agent_index` and derive `completed_agents`.
- The pipeline config must be looked up from the database using the config name. This is already available via `_cp.get_workflow_config(project_id)` which returns pipeline configurations.

**Decision**: Insert the fast-path immediately after the cache check in `_get_or_reconstruct_pipeline()`. When labels are available: (1) extract `pipeline:<config>` to get config name, (2) look up pipeline config to get agent list, (3) extract `agent:<slug>` to find current agent index, (4) build PipelineState directly. Falls through to existing chain if any step fails.

**Rationale**:
1. After-cache placement preserves the fastest path (in-memory cache hit) while adding label-based reconstruction before any API calls.
2. Config lookup is local (database) — not a GitHub API call — so it's effectively zero additional API cost.
3. Graceful fallthrough means labels are purely additive; existing behavior is unchanged when labels are absent.

**Alternatives Considered**:
- **Before cache check**: Rejected — cache is faster than label parsing; labels are the fallback for cache misses.
- **Separate function**: Considered viable but rejected for this iteration — the fast-path is 15–20 lines of code and fits naturally in the existing function's flow.

---

### R-005: Label Pre-Creation Strategy

**Context**: FR-004 requires pre-creating pipeline labels with distinct colors. Need to determine when and how to create labels in the repository.

**Findings**:
- The GitHub REST API supports `POST /repos/{owner}/{repo}/labels` to create labels with `name`, `color`, and `description`.
- The existing codebase uses `create_issue()` which accepts a `labels` parameter — GitHub auto-creates labels that don't exist, but without colors.
- Label creation requires `repo` scope, which the app already has (per spec assumptions).
- Label colors in the spec: `pipeline:*` = blue (#0052cc), `agent:*` = purple (#7057ff), `active` = green (#0e8a16), `stalled` = red (#d73a4a).
- Labels need to be created per-repository, not per-project.

**Decision**: Add an `ensure_pipeline_labels_exist()` function to `constants.py` (or a thin wrapper in the orchestrator) that pre-creates labels with colors on first pipeline use. Use a local cache flag to avoid redundant creation attempts. Label creation is idempotent (creating an existing label is a 422 that can be caught).

**Rationale**:
1. Pre-creation ensures consistent colors and descriptions from the start.
2. Caching the "already created" flag per repository avoids repeated API calls.
3. 422 handling (label already exists) makes the operation safe to retry.

**Alternatives Considered**:
- **Lazy creation at first use**: Rejected — misses color assignment; GitHub auto-creates labels without color.
- **Project connect hook**: Preferred by spec, but the current codebase doesn't have a clear "project connect" event. Pipeline launch is the next best trigger point.

---

### R-006: Stalled Label Integration Points

**Context**: FR-009 requires applying `stalled` label during recovery and removing it on successful re-assignment. Need to determine exact integration points in recovery.py.

**Findings**:
- `recover_stalled_issues()` (recovery.py lines 232–736) iterates over non-terminal issues, validates tracking tables, and re-assigns agents when conditions A (Copilot assigned) or B (WIP PR exists) are unmet.
- The re-assignment happens via `assign_agent_for_status()` in the orchestrator.
- Current recovery cooldown is managed by `_should_skip_recovery()` using `RECOVERY_COOLDOWN_SECONDS`.
- There's no existing "stalled detection" flag — recovery simply re-assigns agents that appear stuck.

**Decision**: 
1. Apply `stalled` label when recovery identifies an issue needing re-assignment (just before calling `assign_agent_for_status()`).
2. Remove `stalled` label inside `assign_agent_for_status()` when a new agent is successfully assigned (alongside the `agent:<slug>` swap).
3. Use `stalled` label presence in the fast-path to skip expensive reconciliation for issues that are already known-stalled and within cooldown.

**Rationale**:
1. Applying `stalled` at detection and removing at re-assignment creates a clean state machine.
2. Removing inside `assign_agent_for_status()` ensures the label is cleared regardless of whether assignment is triggered by recovery or normal pipeline progression.

**Alternatives Considered**:
- **Separate stalled cleanup job**: Rejected — adds complexity; cleanup at re-assignment is sufficient.
- **Stalled label only for UI**: Considered but rejected — using it for fast-path detection adds recovery optimization value.

---

### R-007: Frontend Label Display Patterns

**Context**: FR-013 requires exposing labels in API responses for frontend consumption. Need to determine the minimal frontend changes.

**Findings**:
- `BoardToolbar.tsx` already has a label filter with `availableLabels: string[]` and `CheckboxList` component. Labels are already filterable.
- Board cards currently don't display individual label badges — only status column determines card appearance.
- The `TaskListResponse` and board API both return task data but without labels on the Task model.
- The frontend uses TanStack Query for data fetching with typed API responses in `api.ts`.

**Decision**: 
1. Add `labels` to Task API responses (backend change in `projects.py`).
2. Frontend: parse `agent:*`, `pipeline:*`, and `stalled` labels from task.labels to render badges.
3. Add a dedicated pipeline config filter dropdown to `BoardToolbar.tsx` (separate from the general label filter).
4. Use existing UI patterns (badges, warning indicators) rather than new components.

**Rationale**:
1. The backend already has label data — just needs to expose it through the Task model.
2. Frontend changes are rendering-only — no new API calls needed.
3. A dedicated pipeline config filter is more discoverable than relying on the general label filter.

**Alternatives Considered**:
- **Separate API endpoint for pipeline labels**: Rejected — labels are already on the task; no need for an additional fetch.
- **Backend pre-parsing of pipeline labels into separate fields**: Rejected — violates separation of concerns; frontend can parse label prefixes.

---

### R-008: Label Validation and Cross-Check Strategy

**Context**: FR-014 requires a consolidated validation function that cross-checks labels against the tracking table. Need to determine what "stale source correction" means in practice.

**Findings**:
- The tracking table (Markdown in issue body) is updated via `update_issue_body()` when agent states change.
- Labels are updated via `update_issue_state()` when agents are assigned/completed.
- Mismatch scenarios: (a) Label says `agent:speckit.plan` but table says `speckit.tasks` is active — could happen if label update failed; (b) Table says `speckit.plan` is active but no `agent:` label — could happen if labels were manually removed.
- Ground truth is determined by checking: sub-issue state (open/closed), Copilot assignment status, PR existence.
- `_validate_and_reconcile_tracking_table()` already validates tracking table against GitHub ground truth.

**Decision**: Create `backend/src/services/copilot_polling/state_validation.py` with a single `validate_pipeline_labels()` function that:
1. Compares label-derived state with tracking-table-derived state.
2. When they disagree, checks GitHub ground truth (sub-issue status, assignment).
3. Fixes the stale source: updates labels via `update_issue_state()` or updates tracking table via `update_issue_body()`.
4. Returns the reconciled state.

**Rationale**:
1. Single validation function consolidates what would otherwise be scattered checks across pipeline.py and recovery.py.
2. "Fix stale source" approach means both labels and tracking table converge to truth — neither is permanently authoritative.
3. Separate file (`state_validation.py`) keeps the validation logic focused and testable without inflating existing modules.

**Alternatives Considered**:
- **Labels always win**: Rejected — labels can be manually removed by users; tracking table is more reliable for audit.
- **Tracking table always wins**: Rejected — defeats the purpose of labels as fast-path; would require re-reading issue body.
- **Inline validation in pipeline.py**: Rejected — the validation logic is ~80–100 lines; merits its own module for clarity and testability.