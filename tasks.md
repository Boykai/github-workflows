# Tasks: GitHub Label-Based Agent Pipeline State Tracking

**Feature**: `034-label-pipeline-state` | **Spec**: [spec.md](specs/034-label-pipeline-state/spec.md) | **Plan**: [plan.md](specs/034-label-pipeline-state/plan.md)

---

## Phase 1: Label Constants & Utilities

### Task 1.1 — Add Pipeline Label Constants

**File**: `backend/src/constants.py`

**Description**: Add label prefix constants, color codes, and description mappings for pipeline state labels.

**Input**: Spec data-model.md § New Constants

**Changes**:
1. Add `PIPELINE_LABEL_PREFIX = "pipeline:"`
2. Add `AGENT_LABEL_PREFIX = "agent:"`
3. Add `ACTIVE_LABEL = "active"`
4. Add `STALLED_LABEL = "stalled"`
5. Add color constants: `PIPELINE_LABEL_COLOR = "0052cc"`, `AGENT_LABEL_COLOR = "7057ff"`, `ACTIVE_LABEL_COLOR = "0e8a16"`, `STALLED_LABEL_COLOR = "d73a4a"`
6. Add `PIPELINE_LABEL_DESCRIPTIONS` dict mapping `ACTIVE_LABEL` and `STALLED_LABEL` to their descriptions

**Output**: Four string constants, four color constants, one dict — all importable from `constants.py`.

**Acceptance Criteria**:
- Constants are defined at module level in `backend/src/constants.py` after the existing label definitions.
- All values match the data-model.md exactly.
- No existing constants or functions are modified.
- `python -c "from backend.src.constants import PIPELINE_LABEL_PREFIX, AGENT_LABEL_PREFIX, ACTIVE_LABEL, STALLED_LABEL"` succeeds.

---

### Task 1.2 — Add Label Parsing Utilities (`extract_*`)

**File**: `backend/src/constants.py`

**Description**: Add two pure functions that extract the value portion from prefixed label strings.

**Input**: Contract `label-utilities.md` § Interface — Parsing functions

**Changes**:
1. Add `extract_pipeline_config(label_name: str) -> str | None` — returns the config name after `pipeline:` prefix, or `None` if label doesn't match.
2. Add `extract_agent_slug(label_name: str) -> str | None` — returns the agent slug after `agent:` prefix, or `None` if label doesn't match.

**Output**: Two pure functions in `constants.py`.

**Acceptance Criteria**:
- `extract_pipeline_config("pipeline:speckit-full")` returns `"speckit-full"`.
- `extract_pipeline_config("agent:speckit.plan")` returns `None`.
- `extract_pipeline_config("")` returns `None`.
- `extract_agent_slug("agent:speckit.plan")` returns `"speckit.plan"`.
- `extract_agent_slug("pipeline:speckit-full")` returns `None`.
- `extract_agent_slug("")` returns `None`.
- Functions never raise exceptions.
- Functions are pure — no I/O, no side effects.

---

### Task 1.3 — Add Label Builder Utilities (`build_*`)

**File**: `backend/src/constants.py`

**Description**: Add two pure functions that construct prefixed label strings from values.

**Input**: Contract `label-utilities.md` § Interface — Building functions

**Changes**:
1. Add `build_pipeline_label(config_name: str) -> str` — returns `f"{PIPELINE_LABEL_PREFIX}{config_name}"`.
2. Add `build_agent_label(agent_slug: str) -> str` — returns `f"{AGENT_LABEL_PREFIX}{agent_slug}"`.

**Output**: Two pure functions in `constants.py`.

**Acceptance Criteria**:
- `build_pipeline_label("speckit-full")` returns `"pipeline:speckit-full"`.
- `build_agent_label("speckit.plan")` returns `"agent:speckit.plan"`.
- Round-trip invariants hold: `extract_pipeline_config(build_pipeline_label("x")) == "x"` and `extract_agent_slug(build_agent_label("x")) == "x"`.

---

### Task 1.4 — Add Label Query Utilities (`find_*`, `has_*`)

**File**: `backend/src/constants.py`

**Description**: Add three functions that scan label lists to extract pipeline state information.

**Input**: Contract `label-utilities.md` § Interface — Querying functions; data-model.md § Label Parsing Utilities

**Changes**:
1. Add `find_pipeline_label(labels: list[dict[str, str]] | list) -> str | None` — scans for first `pipeline:*` match, returns config name or `None`.
2. Add `find_agent_label(labels: list[dict[str, str]] | list) -> str | None` — scans for first `agent:*` match, returns agent slug or `None`.
3. Add `has_stalled_label(labels: list[dict[str, str]] | list) -> bool` — returns `True` if `stalled` label present.

**Output**: Three functions in `constants.py`.

**Acceptance Criteria**:
- Functions accept both `list[dict]` (with `"name"` key) and objects with `.name` attribute (duck-typed via `isinstance` check).
- `find_pipeline_label([{"name": "pipeline:speckit-full"}, {"name": "bug"}])` returns `"speckit-full"`.
- `find_pipeline_label([{"name": "bug"}])` returns `None`.
- `find_pipeline_label([])` returns `None`.
- `find_agent_label([{"name": "agent:speckit.plan"}, {"name": "bug"}])` returns `"speckit.plan"`.
- `has_stalled_label([{"name": "stalled"}])` returns `True`.
- `has_stalled_label([{"name": "bug"}])` returns `False`.
- When multiple `agent:` labels exist (transient inconsistency), the first match is returned.

---

### Task 1.5 — Update `build_parent_labels()` for Pipeline Config

**File**: `backend/src/constants.py`

**Description**: Extend the existing `build_parent_labels()` (or the label-building function used at issue creation) to accept an optional `pipeline_config_name` parameter and include the `pipeline:<config>` label when provided.

**Input**: Plan Step 3; contract `label-write-path.md` § Issue Creation

**Changes**:
1. Add optional `pipeline_config_name: str | None = None` parameter to the label builder.
2. When `pipeline_config_name` is provided and non-empty, append `build_pipeline_label(pipeline_config_name)` to the returned label list.

**Output**: Modified function signature with backward-compatible optional parameter.

**Acceptance Criteria**:
- Calling without `pipeline_config_name` produces identical output to the current behavior (backward compatible).
- Calling with `pipeline_config_name="speckit-full"` includes `"pipeline:speckit-full"` in the returned labels.
- Existing tests remain green.

---

### Task 1.6 — Add `ensure_pipeline_labels_exist()` for Repo Pre-Creation

**File**: `backend/src/constants.py` (or a new utility in `backend/src/services/github_projects/`)

**Description**: Add an async function that pre-creates the `active` and `stalled` labels in a repository with correct colors and descriptions. Pipeline-specific (`pipeline:*`) and agent-specific (`agent:*`) labels are created dynamically at first use.

**Input**: Contract `label-write-path.md` § Label Pre-Creation; data-model.md § Pipeline Label Constants

**Changes**:
1. Add `async def ensure_pipeline_labels_exist(access_token: str, owner: str, repo: str) -> None`.
2. For each label in `[ACTIVE_LABEL, STALLED_LABEL]`, call the GitHub REST API `POST /repos/{owner}/{repo}/labels` with name, color, and description.
3. Handle 422 (already exists) gracefully — log info, do not raise.
4. Handle other errors gracefully — log warning, do not raise.

**Output**: One async function that idempotently creates labels.

**Acceptance Criteria**:
- Function creates `active` (color `0e8a16`) and `stalled` (color `d73a4a`) labels.
- 422 response (label already exists) is handled silently — no error raised.
- Network errors are logged at WARNING level — no error raised.
- Function is idempotent — safe to call multiple times.

---

### Task 1.7 — Unit Tests for Label Utilities

**File**: `backend/tests/unit/test_label_constants.py` (new)

**Description**: Write unit tests for all label parsing, building, and querying utilities added in Tasks 1.1–1.4.

**Input**: Contract `label-utilities.md` § Invariants; data-model.md § New Pure Functions

**Changes**:
1. Test `extract_pipeline_config()` — matching, non-matching, empty string, just-prefix cases.
2. Test `extract_agent_slug()` — matching, non-matching, empty string, just-prefix cases.
3. Test `build_pipeline_label()` — normal case, round-trip with `extract_*`.
4. Test `build_agent_label()` — normal case, round-trip with `extract_*`.
5. Test `find_pipeline_label()` — with dict labels, with object labels, empty list, multiple matches (first wins).
6. Test `find_agent_label()` — same variations.
7. Test `has_stalled_label()` — present, absent, empty list.

**Output**: Test file with ≥15 test cases covering all utility functions.

**Acceptance Criteria**:
- `cd backend && python -m pytest tests/unit/test_label_constants.py -x -q` passes.
- All round-trip invariants from the contract are tested.
- Both `dict` and object-with-attribute label formats are tested for `find_*` functions.
- Edge cases (empty list, empty string, prefix-only) are covered.

---

## Phase 2: Label Write Path

*Depends on: Phase 1 (Tasks 1.1–1.6)*

### Task 2.1 — Apply `pipeline:<config>` Label at Issue Creation

**File**: `backend/src/services/workflow_orchestrator/orchestrator.py`

**Description**: When creating a new pipeline issue via `create_issue_from_recommendation()`, include the `pipeline:<config>` label in the issue's initial label set.

**Input**: Contract `label-write-path.md` § Issue Creation; Task 1.5 output

**Changes**:
1. Import `build_pipeline_label` from `constants.py`.
2. In `create_issue_from_recommendation()` (or `_build_labels()`), determine the `pipeline_config_name` from the pipeline configuration context.
3. Pass `pipeline_config_name` to the label builder so `pipeline:<config>` is included in the created issue's labels.

**Output**: Issues created by the orchestrator now carry a `pipeline:<config>` label from creation.

**Acceptance Criteria**:
- A newly created pipeline issue has a `pipeline:<config>` label matching the pipeline configuration name.
- The `pipeline:<config>` label is set once and never modified after creation.
- Issues created without a pipeline configuration (e.g., standalone issues) do not receive a `pipeline:` label.
- Existing issue creation behavior is preserved — all other labels still applied.

---

### Task 2.2 — Swap `agent:<slug>` Label on Agent Assignment

**File**: `backend/src/services/workflow_orchestrator/orchestrator.py`

**Description**: When assigning a new agent via `assign_agent_for_status()`, atomically swap the `agent:<slug>` label — remove the old agent label (if any) and add the new one in a single `update_issue_state()` call.

**Input**: Contract `label-write-path.md` § Agent Assignment; existing `update_issue_state()` API

**Changes**:
1. Import `build_agent_label`, `find_agent_label` from `constants.py`.
2. In `assign_agent_for_status()`, after determining the new agent slug:
   a. Read current labels from the task/issue to find existing `agent:*` label.
   b. Call `update_issue_state(labels_add=[build_agent_label(new_slug)], labels_remove=[old_agent_label])` if old label exists, or just `labels_add` if no old label.
3. Label swap failure is non-blocking — log warning but continue with pipeline progression.

**Output**: Parent issue always has exactly one `agent:<slug>` label reflecting the currently active agent.

**Acceptance Criteria**:
- After assignment, the parent issue has exactly one `agent:` label matching the new agent.
- If no previous `agent:` label existed (first agent), only an add is performed.
- If a previous `agent:` label existed, it is removed and the new one is added.
- Label swap failure does not prevent agent assignment from completing.
- `update_issue_state()` is called at most once for the swap (both add and remove in same call).

---

### Task 2.3 — Move `active` Label Between Sub-Issues

**File**: `backend/src/services/workflow_orchestrator/orchestrator.py`

**Description**: When transitioning between agents, move the `active` label from the previous agent's sub-issue to the new agent's sub-issue.

**Input**: Contract `label-write-path.md` § Agent Assignment; `ACTIVE_LABEL` constant

**Changes**:
1. Import `ACTIVE_LABEL` from `constants.py`.
2. In `assign_agent_for_status()`, after resolving the new sub-issue:
   a. Add `active` label to the new agent's sub-issue via `update_issue_state(labels_add=["active"])`.
   b. Remove `active` label from the previous agent's sub-issue via `update_issue_state(labels_remove=["active"])` (if a previous sub-issue is known).
3. Both operations are non-blocking — logged on failure.

**Output**: At most one sub-issue has the `active` label at any time.

**Acceptance Criteria**:
- New sub-issue receives the `active` label.
- Previous sub-issue has the `active` label removed (if known).
- First agent assignment (no previous sub-issue) only adds — no removal attempted.
- Failure to add/remove `active` label does not prevent agent assignment.

---

### Task 2.4 — Remove `stalled` Label on Successful Assignment

**File**: `backend/src/services/workflow_orchestrator/orchestrator.py`

**Description**: When `assign_agent_for_status()` successfully assigns an agent, remove the `stalled` label from the parent issue if present.

**Input**: Contract `label-write-path.md` § Agent Assignment; `STALLED_LABEL` constant

**Changes**:
1. Import `STALLED_LABEL` from `constants.py`.
2. In `assign_agent_for_status()`, include `STALLED_LABEL` in the `labels_remove` list of the `update_issue_state()` call (same call as the agent label swap from Task 2.2).

**Output**: Stalled label is removed whenever a successful agent assignment occurs.

**Acceptance Criteria**:
- If `stalled` label was present, it is removed after successful assignment.
- If `stalled` label was not present, removal is a no-op (handled gracefully by `update_issue_state()`).
- Removal failure does not prevent agent assignment.

---

### Task 2.5 — Remove `agent:*` Label on Pipeline Completion

**File**: `backend/src/services/copilot_polling/pipeline.py`

**Description**: When a pipeline completes (all agents done), remove the `agent:*` label from the parent issue to signal completion.

**Input**: Contract `label-write-path.md` § Pipeline Completion; `_process_pipeline_completion()` function

**Changes**:
1. Import `find_agent_label`, `build_agent_label` from `constants.py`.
2. In `_process_pipeline_completion()`, after marking the pipeline complete:
   a. Determine the last agent's label from the current labels or the pipeline state.
   b. Call `update_issue_state(labels_remove=[last_agent_label])` to remove it.
3. Non-blocking — log warning on failure.

**Output**: Completed pipeline issues have no `agent:*` label.

**Acceptance Criteria**:
- After pipeline completion, the parent issue has no `agent:` label.
- If no `agent:` label existed at completion time, operation is a no-op.
- Also removes `active` label from the last sub-issue.
- Failure to remove label does not prevent pipeline completion processing.

---

### Task 2.6 — Apply `stalled` Label in Recovery

**File**: `backend/src/services/copilot_polling/recovery.py`

**Description**: When `recover_stalled_issues()` detects an idle agent that exceeds the grace period, apply the `stalled` label to the parent issue.

**Input**: Contract `label-write-path.md` § Stalled Detection; `STALLED_LABEL` constant

**Changes**:
1. Import `STALLED_LABEL` from `constants.py`.
2. In `recover_stalled_issues()`, when a stalled issue is detected (before re-assignment attempt):
   a. Call `update_issue_state(labels_add=[STALLED_LABEL])` on the parent issue.
3. Non-blocking — log warning on failure.

**Output**: Stalled issues are visually marked with the `stalled` label on GitHub.

**Acceptance Criteria**:
- Issues detected as stalled receive the `stalled` label.
- If `stalled` label already exists (re-detection), add is a no-op.
- Stalled label is eventually removed by `assign_agent_for_status()` (Task 2.4) upon successful re-assignment.
- Label application failure does not prevent recovery processing.

---

### Task 2.7 — Unit Tests for Label Write Path

**File**: `backend/tests/unit/test_label_write_path.py` (new)

**Description**: Write unit tests that mock `update_issue_state()` and verify correct label operations at each pipeline transition point.

**Input**: Contract `label-write-path.md` § Invariants; Tasks 2.1–2.6 outputs

**Changes**:
1. Test issue creation includes `pipeline:<config>` label.
2. Test agent swap: old `agent:*` removed, new `agent:*` added in same call.
3. Test first agent (no old label): only add, no remove.
4. Test `active` label moved between sub-issues.
5. Test `stalled` label removed on assignment.
6. Test `stalled` label applied on recovery detection.
7. Test `agent:*` label removed on pipeline completion.
8. Test non-blocking: label API failures do not raise exceptions.

**Output**: Test file with ≥10 test cases using mocked GitHub API calls.

**Acceptance Criteria**:
- `cd backend && python -m pytest tests/unit/test_label_write_path.py -x -q` passes.
- All transition points (creation, assignment, completion, stalled) are covered.
- Both success and failure (API error) paths are tested.
- Mock assertions verify exact `labels_add` and `labels_remove` arguments.

---

## Phase 3: Label Read Path — Fast-Path Detection

*Depends on: Phase 2 (Tasks 2.1–2.6)*

### Task 3.1 — Add `labels` Field to Task Model

**File**: `backend/src/models/task.py`

**Description**: Add an optional `labels` field to the `Task` Pydantic model so label data from the GraphQL board query can be propagated through the polling pipeline.

**Input**: Data-model.md § Modified Models — Task Model Extension; contract `label-fast-path.md` § Task Model Extension

**Changes**:
1. Add `labels: list[dict[str, str]] | None = None` field to the `Task` class.

**Output**: Task model accepts label data; serializes labels in API responses automatically.

**Acceptance Criteria**:
- `Task(labels=[{"name": "pipeline:speckit-full", "color": "0052cc"}], ...)` succeeds.
- `Task(labels=None, ...)` succeeds (backward compatible).
- `Task(...)` without labels argument defaults to `None`.
- Existing code that creates `Task` objects without labels is unaffected.

---

### Task 3.2 — Propagate Labels from Board Query to Task Objects

**File**: `backend/src/services/github_projects/projects.py` (or wherever `BoardItem` → `Task` conversion happens)

**Description**: Pass the already-parsed `labels` from `BoardItem` into `Task` objects during the board-to-task conversion.

**Input**: `board.py` already parses `labels(first: 20)` into `BoardItem.labels`; Task model now has `labels` field (Task 3.1)

**Changes**:
1. In the function that converts `BoardItem` to `Task`, map `BoardItem.labels` to `Task.labels`.
2. Convert `Label` objects to `dict[str, str]` format: `{"name": label.name, "color": label.color}`.

**Output**: `Task.labels` is populated from GraphQL data with zero additional API calls.

**Acceptance Criteria**:
- Tasks returned by `get_project_items()` have their `labels` field populated.
- Label data includes at least `name` and `color` for each label.
- Tasks for issues without labels have `labels` as empty list or `None`.
- No additional API calls are made — labels come from the existing GraphQL board query.

---

### Task 3.3 — Pass Labels Through Polling Steps

**File**: `backend/src/services/copilot_polling/polling_loop.py`

**Description**: Ensure label data is available to polling steps (especially pipeline reconstruction) by passing `Task.labels` through the polling step invocations.

**Input**: Contract `label-fast-path.md` § Polling Loop Integration; Tasks 3.1–3.2 outputs

**Changes**:
1. Where polling steps call `_get_or_reconstruct_pipeline()`, pass `task.labels` as the new `labels` parameter.
2. Verify that parent task filtering and sub-issue detection can optionally use labels.

**Output**: Pipeline reconstruction and polling steps have access to label data.

**Acceptance Criteria**:
- Polling steps that invoke pipeline reconstruction pass `task.labels` to `_get_or_reconstruct_pipeline()`.
- Steps receiving tasks without labels (legacy) continue to work — `labels=None` triggers existing code paths.
- No behavioral change for existing pipelines without labels.

---

### Task 3.4 — Implement Label Fast-Path in `_get_or_reconstruct_pipeline()`

**File**: `backend/src/services/copilot_polling/pipeline.py`

**Description**: Insert a zero-API-call fast-path layer into the pipeline state reconstruction chain. When both `pipeline:<config>` and `agent:<slug>` labels are present, build `PipelineState` directly from labels + config without fetching the issue body or sub-issues.

**Input**: Contract `label-fast-path.md` § Fast-Path Layer; data-model.md § Data Flow

**Changes**:
1. Add `labels: list[dict[str, str]] | None = None` parameter to `_get_or_reconstruct_pipeline()`.
2. After cache hit check and before issue-body fetch, add fast-path:
   a. Call `find_pipeline_label(labels)` → `pipeline_config_name`.
   b. Call `find_agent_label(labels)` → `agent_slug`.
   c. If both are present, look up `PipelineConfig` by name.
   d. Find the agent's index in the config's agent list.
   e. Build `PipelineState` with correct `current_agent_index` and `agents`.
   f. Cache and return the built state.
3. If fast-path fails (missing label, unknown config, unknown agent), fall through to existing chain.

**Output**: New reconstruction path that builds `PipelineState` with zero GitHub API calls.

**Acceptance Criteria**:
- With both `pipeline:` and `agent:` labels present, `PipelineState` is built without issue-body or sub-issue API calls.
- Fast-path produces identical `PipelineState` fields (`current_agent_index`, `agents`, `completed_agents`) as full reconstruction for the same state.
- Fast-path failure (missing labels, unknown config/agent) gracefully falls through to existing reconstruction.
- `labels=None` skips the fast-path entirely (backward compatible).
- Built state is cached in the in-memory cache.

---

### Task 3.5 — Implement `_build_pipeline_from_labels()` Helper

**File**: `backend/src/services/copilot_polling/pipeline.py`

**Description**: Create an internal helper function that constructs a `PipelineState` object from label-extracted data and pipeline configuration.

**Input**: Contract `label-fast-path.md` § Fast-Path Builder

**Changes**:
1. Add `_build_pipeline_from_labels(issue_number, project_id, status, pipeline_config_name, agent_slug, pipeline_config) -> PipelineState | None`.
2. Look up the agent slug in the pipeline config's agent list to determine the index.
3. Build `PipelineState` with agents marked as DONE before the current index, ACTIVE at the current index, and PENDING after.
4. Return `None` if the agent slug is not found in the config (triggers fallthrough).

**Output**: Internal helper function for fast-path construction.

**Acceptance Criteria**:
- Returns valid `PipelineState` when agent slug is found in config.
- Returns `None` when agent slug is not in the config's agent list.
- `current_agent_index` matches the agent's position in the config.
- Agents before the current index are marked as completed.
- Agents at and after the current index are marked appropriately.

---

### Task 3.6 — Label-Based Parent-Issue Filter

**File**: `backend/src/services/copilot_polling/polling_loop.py` (or `helpers.py`)

**Description**: Add a label-based check to `is_sub_issue()` as an additional fast-path for filtering sub-issues. Sub-issues have a `sub-issue` label; parent issues may have a `parent` label.

**Input**: Plan Step 14; existing `is_sub_issue()` in helpers.py

**Changes**:
1. In `is_sub_issue()` or the polling loop's parent-task filter, check for the `sub-issue` label first (O(1) label scan) before falling back to title-pattern matching.
2. Existing title-pattern matching remains as fallback for issues without labels.

**Output**: Faster parent/sub-issue filtering using label data when available.

**Acceptance Criteria**:
- Issues with `sub-issue` label are correctly identified as sub-issues without title parsing.
- Issues without labels fall through to existing title-pattern detection.
- No false positives or false negatives compared to current detection.

---

### Task 3.7 — Unit Tests for Label Fast-Path

**File**: `backend/tests/unit/test_label_fast_path.py` (new)

**Description**: Write unit tests for the fast-path reconstruction layer and `_build_pipeline_from_labels()` helper.

**Input**: Contract `label-fast-path.md` § Invariants; Tasks 3.4–3.5 outputs

**Changes**:
1. Test fast-path builds correct `PipelineState` from labels + config (zero API calls).
2. Test fast-path fallthrough when `pipeline:` label missing.
3. Test fast-path fallthrough when `agent:` label missing.
4. Test fast-path fallthrough when agent slug not in config.
5. Test fast-path fallthrough when pipeline config not found.
6. Test `_build_pipeline_from_labels()` with valid inputs — correct agent index and state.
7. Test `_build_pipeline_from_labels()` returns `None` for unknown agent.
8. Test `labels=None` skips fast-path entirely.
9. Test that fast-path result matches full reconstruction result for the same state.

**Output**: Test file with ≥10 test cases verifying fast-path behavior.

**Acceptance Criteria**:
- `cd backend && python -m pytest tests/unit/test_label_fast_path.py -x -q` passes.
- Zero-API-call reconstruction is verified (mock API not called during fast-path).
- All fallthrough scenarios tested.
- State equivalence between fast-path and full reconstruction tested.

---

## Phase 4: Recovery Consolidation

*Depends on: Phase 3 (Tasks 3.1–3.6)*

### Task 4.1 — Create `state_validation.py` with `validate_pipeline_labels()`

**File**: `backend/src/services/copilot_polling/state_validation.py` (new)

**Description**: Create a consolidated validation function that cross-checks pipeline labels against the Markdown tracking table and corrects whichever source is stale.

**Input**: Contract `label-validation.md` § Interface; data-model.md § New Module

**Changes**:
1. Create `state_validation.py` with `validate_pipeline_labels()`.
2. Comparison logic:
   a. Extract `agent:<slug>` from labels → `label_agent`.
   b. Find active agent from `tracking_steps` → `table_agent`.
   c. If both match → consistent, no corrections.
   d. If mismatch → check GitHub ground truth (sub-issue state) → fix stale source.
3. Return `(corrections_made: bool, correction_descriptions: list[str])`.
4. Log all corrections at WARNING level.

**Output**: New module with a single public function for label/table cross-validation.

**Acceptance Criteria**:
- Function detects consistency between labels and tracking table.
- When labels are stale, labels are updated via `update_issue_state()`.
- When tracking table is stale, table is updated via `update_issue_body()`.
- Ambiguous cases default to trusting the tracking table.
- Function is idempotent — running twice produces no additional changes.
- All corrections are logged at WARNING level.
- Validation is non-blocking — errors are caught and logged, never raised.

---

### Task 4.2 — Simplify `_self_heal_tracking_table()` with `pipeline:` Label

**File**: `backend/src/services/agent_tracking.py`

**Description**: When the `pipeline:<config>` label is present, use it to look up the agent list from the pipeline configuration directly — skipping the `get_sub_issues()` API call.

**Input**: Plan Step 16; contract `label-validation.md` § Simplified Recovery Functions

**Changes**:
1. Accept optional `pipeline_config_name: str | None = None` parameter (or extract from labels).
2. If `pipeline_config_name` is available, load the `PipelineConfig` from the database and get the agent list directly.
3. Skip the `get_sub_issues()` API call when the config provides sufficient information.
4. Fall back to existing sub-issue fetching if no `pipeline:` label is present.

**Output**: Self-heal saves 1–2 API calls per invocation when `pipeline:` label exists.

**Acceptance Criteria**:
- When `pipeline:<config>` label is present, `get_sub_issues()` is not called.
- Agent list derived from config matches what `get_sub_issues()` would return.
- When `pipeline:<config>` label is absent, existing behavior is preserved.
- Self-heal produces the same tracking table result regardless of which path is taken.

---

### Task 4.3 — Simplify `_validate_and_reconcile_tracking_table()` with `agent:` Label

**File**: `backend/src/services/copilot_polling/recovery.py`

**Description**: Use the `agent:<slug>` label as a cursor into the agent list — only validate agents from that index onward, skipping "Done!" checks for agents that completed before the current one.

**Input**: Plan Step 17; contract `label-validation.md` § Simplified Recovery Functions

**Changes**:
1. Accept optional `agent_slug: str | None = None` parameter (or extract from labels).
2. If `agent_slug` is available, find its index in the agent list.
3. Skip "Done!" comment checks for agents before that index (they are already complete).
4. Only validate the current agent and subsequent agents.
5. Fall back to full validation if no `agent:` label is present.

**Output**: Reconciliation saves N-1 "Done!" checks for completed agents.

**Acceptance Criteria**:
- When `agent:<slug>` label is present, agents before that index are not validated.
- Current agent and subsequent agents are still fully validated.
- When `agent:<slug>` label is absent, existing full validation is preserved.
- Results are identical to full validation for consistent states.

---

### Task 4.4 — Simplify `_reconstruct_pipeline_state()` with Labels

**File**: `backend/src/services/copilot_polling/pipeline.py`

**Description**: When labels provide the current agent index, only verify the current agent's status (1 API call) instead of checking all N agents.

**Input**: Plan Step 18; contract `label-validation.md` § Simplified Recovery Functions

**Changes**:
1. Accept optional label data in `_reconstruct_pipeline_state()`.
2. If `agent:<slug>` label provides the current agent index, skip verification of agents before that index.
3. Only verify the CURRENT agent's status (1 API call instead of N).
4. Fall back to full reconstruction if labels are unavailable.

**Output**: Reconstruction saves N-1 API calls for completed agents.

**Acceptance Criteria**:
- With `agent:` label, only 1 API call is made (current agent verification).
- Without `agent:` label, existing N-call reconstruction is preserved.
- Reconstructed state matches full reconstruction for consistent states.

---

### Task 4.5 — Integrate `validate_pipeline_labels()` into Polling Cycle

**File**: `backend/src/services/copilot_polling/polling_loop.py` or `recovery.py`

**Description**: Call `validate_pipeline_labels()` at most once per polling cycle per issue to ensure label/table consistency.

**Input**: Contract `label-validation.md` § Invariants; Task 4.1 output

**Changes**:
1. In the appropriate polling step (e.g., after successful pipeline state retrieval), call `validate_pipeline_labels()` with the current labels and tracking steps.
2. Ensure it runs at most once per polling cycle per issue.
3. Log any corrections made.

**Output**: Label/table consistency is validated periodically.

**Acceptance Criteria**:
- Validation runs at most once per polling cycle per issue.
- Corrections are applied and logged.
- Validation failure does not block polling.

---

### Task 4.6 — Unit Tests for Label Validation

**File**: `backend/tests/unit/test_label_validation.py` (new)

**Description**: Write unit tests for `validate_pipeline_labels()` covering consistency, mismatch, and edge cases.

**Input**: Contract `label-validation.md` § Invariants; Task 4.1 output

**Changes**:
1. Test consistent state (labels match tracking table) → no corrections.
2. Test label is stale (label says agent A, table says agent B) → label updated.
3. Test table is stale (table says agent A, label says agent B) → table updated.
4. Test ambiguous mismatch → tracking table wins.
5. Test missing `agent:` label → validation skipped gracefully.
6. Test missing tracking steps → validation skipped gracefully.
7. Test idempotency — running twice produces no additional corrections.
8. Test non-blocking — API errors caught and logged.

**Output**: Test file with ≥8 test cases covering validation logic.

**Acceptance Criteria**:
- `cd backend && python -m pytest tests/unit/test_label_validation.py -x -q` passes.
- All mismatch scenarios and edge cases are covered.
- Mock assertions verify correct label/table updates.

---

## Phase 5: Frontend Enhancements

*Parallel with Phase 4; depends on Phases 2–3*

### Task 5.1 — Expose Labels in Task/Board API Responses

**File**: `backend/src/api/projects.py`

**Description**: Ensure that the `labels` field added to the `Task` model (Task 3.1) is serialized in the API responses for board and task endpoints.

**Input**: Plan Step 19; Task 3.1 (Task model has `labels` field)

**Changes**:
1. Verify that Pydantic serialization automatically includes `labels` in API responses.
2. If any response model or serializer explicitly excludes fields, add `labels` to the included set.
3. Verify with a test request that labels appear in the JSON response.

**Output**: API responses include label data for board cards.

**Acceptance Criteria**:
- `GET /api/projects/{id}/board` response includes `labels` in each task item.
- Labels include at least `name` and `color` for each label.
- Tasks without labels return `labels: null` or `labels: []`.
- No breaking changes to existing API consumers.

---

### Task 5.2 — Show Active Agent Badge on Board Cards

**File**: `frontend/src/components/board/BoardCard.tsx` (or equivalent card component)

**Description**: Parse the `agent:*` label from the task's label list and display it as a colored badge on board cards.

**Input**: Plan Step 20; `AGENT_LABEL_COLOR = "7057ff"` (purple)

**Changes**:
1. Extract agent slug from labels using a frontend utility: `labels.find(l => l.name.startsWith("agent:"))`.
2. Display as a small purple badge showing the agent name (e.g., "speckit.plan").
3. Only show when `agent:` label is present.

**Output**: Board cards display the currently active agent as a badge.

**Acceptance Criteria**:
- Cards with `agent:` label show a purple badge with the agent slug.
- Cards without `agent:` label show no badge.
- Badge is styled consistently with existing card labels.

---

### Task 5.3 — Show Pipeline Config Tag on Issue Cards

**File**: `frontend/src/components/board/BoardCard.tsx` (or equivalent)

**Description**: Parse the `pipeline:*` label from the task's label list and display it as a colored tag.

**Input**: Plan Step 21; `PIPELINE_LABEL_COLOR = "0052cc"` (blue)

**Changes**:
1. Extract pipeline config name from labels: `labels.find(l => l.name.startsWith("pipeline:"))`.
2. Display as a small blue tag showing the config name.
3. Only show when `pipeline:` label is present.

**Output**: Board cards show the pipeline configuration as a tag.

**Acceptance Criteria**:
- Cards with `pipeline:` label show a blue tag with the config name.
- Cards without `pipeline:` label show no tag.

---

### Task 5.4 — Show Stalled Warning Indicator

**File**: `frontend/src/components/board/BoardCard.tsx` (or equivalent)

**Description**: Check for the `stalled` label and display a visual warning indicator on the card.

**Input**: Plan Step 22; `STALLED_LABEL_COLOR = "d73a4a"` (red)

**Changes**:
1. Check `labels.some(l => l.name === "stalled")`.
2. Display a red warning icon or border highlight when stalled.
3. Optionally show tooltip: "This pipeline agent is stalled and may need recovery."

**Output**: Stalled issues are visually distinct on the board.

**Acceptance Criteria**:
- Cards with `stalled` label show a red warning indicator.
- Cards without `stalled` label show no indicator.
- Warning is visually prominent but not disruptive.

---

### Task 5.5 — Add Pipeline Config Filter to BoardToolbar

**File**: `frontend/src/components/board/BoardToolbar.tsx`

**Description**: Add a filter option in the board toolbar that allows filtering cards by `pipeline:*` label, showing only issues belonging to a specific pipeline configuration.

**Input**: Plan Step 23; existing filter infrastructure in `BoardToolbar.tsx`

**Changes**:
1. Extract unique pipeline config names from tasks' labels.
2. Add a filter dropdown/checkbox list for pipeline configs (following existing filter patterns).
3. Apply filter to board card display.

**Output**: Users can filter the board by pipeline configuration.

**Acceptance Criteria**:
- Toolbar shows a "Pipeline" filter option when pipeline labels exist.
- Selecting a pipeline config filters cards to only show matching issues.
- Clearing the filter shows all issues again.
- Filter follows existing toolbar patterns (consistent UI).

---

## Verification & Integration

### Task V.1 — Full Backend Test Suite Regression Check

**Description**: Run the complete backend unit test suite to verify no regressions.

**Command**: `cd backend && python -m pytest tests/unit/ -x -q`

**Acceptance Criteria**:
- All existing tests pass.
- All new test files pass.
- No test warnings related to label changes.

---

### Task V.2 — Integration Test: Full Pipeline Lifecycle with Labels

**Description**: Create or extend an integration test that verifies labels at each pipeline transition point: issue creation → agent assignment → agent completion → next agent → pipeline completion.

**Acceptance Criteria**:
- Pipeline issue created with `pipeline:<config>` label.
- First agent assigned → `agent:<slug>` label added, `active` label on sub-issue.
- Agent completes → `agent:` label swapped to next agent, `active` label moved.
- Pipeline completes → `agent:` label removed, `active` label removed.
- At each step, label state matches expected state.

---

### Task V.3 — Integration Test: Fast-Path Recovery After Restart

**Description**: Verify that after a simulated container restart (cleared in-memory cache), the fast-path reconstructs pipeline state from labels without full reconstruction API calls.

**Acceptance Criteria**:
- Clear in-memory pipeline cache.
- Call `_get_or_reconstruct_pipeline()` with labels containing `pipeline:` and `agent:`.
- Verify `PipelineState` is built from labels (zero API calls for issue body / sub-issues).
- Verify state matches what full reconstruction would produce.

---

### Task V.4 — API Call Count Comparison

**Description**: Measure and document the reduction in API calls for stalled issue recovery: expected drop from ~15–25 calls to ~3–5.

**Acceptance Criteria**:
- Document before/after API call counts for: recovery of a stalled 5-agent pipeline.
- Before: ~15–25 calls (fetch issue body + N sub-issue checks + N "Done!" comment checks).
- After: ~3–5 calls (label read from board query + 1 current agent verification + label/tracking update).
- Reduction is ≥ 60% for a 5-agent pipeline.

---

## Dependency Graph

```
Phase 1 (Tasks 1.1–1.7)
  ↓
Phase 2 (Tasks 2.1–2.7) — depends on Phase 1
  ↓
Phase 3 (Tasks 3.1–3.7) — depends on Phase 2
  ↓
Phase 4 (Tasks 4.1–4.6) — depends on Phase 3
  ↓
Phase 5 (Tasks 5.1–5.5) — parallel with Phase 4, depends on Phases 2–3
  ↓
Verification (Tasks V.1–V.4) — depends on all phases
```

## Summary

| Phase | Tasks | New Files | Modified Files |
|-------|-------|-----------|----------------|
| Phase 1: Constants & Utilities | 7 | 1 test file | `constants.py` |
| Phase 2: Label Write Path | 7 | 1 test file | `orchestrator.py`, `pipeline.py`, `recovery.py` |
| Phase 3: Label Read Path | 7 | 1 test file | `task.py`, `projects.py`, `polling_loop.py`, `pipeline.py` |
| Phase 4: Recovery Consolidation | 6 | `state_validation.py` + 1 test | `agent_tracking.py`, `recovery.py`, `pipeline.py` |
| Phase 5: Frontend Enhancements | 5 | — | `BoardCard.tsx`, `BoardToolbar.tsx`, `projects.py` |
| Verification | 4 | — | — |
| **Total** | **36** | **6** | **~12** |
