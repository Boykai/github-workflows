# Tasks: GitHub Label-Based Agent Pipeline State Tracking

**Input**: Design documents from `/specs/034-label-pipeline-state/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Included — spec mandates unit tests for label utilities, write path, fast-path reconstruction, and validation (Constitution Check IV; Verification items 1–4).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing. US2 (label writes) precedes US1 (label reads) because the write path must exist for read-path labels to be present.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- **Backend tests**: `backend/tests/unit/`
- **Frontend types**: `frontend/src/types/index.ts`
- **Frontend services**: `frontend/src/services/api.ts`

---

## Phase 1: Setup (Label Constants & Utilities)

**Purpose**: Define pipeline label constants and pure-function utilities that all subsequent phases depend on. These are the foundation referenced by contracts/label-utilities.md.

- [x] T001 Add pipeline label constants (`PIPELINE_LABEL_PREFIX`, `AGENT_LABEL_PREFIX`, `ACTIVE_LABEL`, `STALLED_LABEL`) and color constants (`PIPELINE_LABEL_COLOR`, `AGENT_LABEL_COLOR`, `ACTIVE_LABEL_COLOR`, `STALLED_LABEL_COLOR`) to `backend/src/constants.py`, and append new label names to the existing `LABELS` allowlist
- [x] T002 Add label parsing and builder pure functions (`extract_pipeline_config()`, `extract_agent_slug()`, `build_pipeline_label()`, `build_agent_label()`) to `backend/src/constants.py` — must satisfy round-trip invariant per contracts/label-utilities.md
- [x] T003 Add label list query utilities (`find_pipeline_label()`, `find_agent_label()`, `has_stalled_label()`) accepting both `list[dict]` and `list[Label]` via duck-typing to `backend/src/constants.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Extend the Task model with labels, propagate label data from GraphQL responses, pre-create labels, and validate utilities with tests. MUST complete before any user story work.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T004 Add `labels: list[dict[str, str]] | None = None` field to the `Task` model in `backend/src/models/task.py` — use simple dict representation per research R-003 to avoid cross-model coupling
- [x] T005 Map label data from GraphQL response `content.labels.nodes` to `Task.labels` during construction in `backend/src/services/github_projects/projects.py` inside `get_project_items()`
- [x] T006 [P] Add `labels?: Array<{name: string; color: string}>` to the `Task` interface in `frontend/src/types/index.ts` and update `TaskListResponse` type
- [x] T007 [P] Update API response type handling in `frontend/src/services/api.ts` to include label data from task responses
- [x] T008 [P] Implement `ensure_pipeline_labels_exist()` async function in `backend/src/constants.py` that pre-creates `active` (green) and `stalled` (red) labels with correct colors via GitHub REST API, with local cache flag to avoid redundant creation and 422 handling for idempotency — per research R-005
- [x] T009 [P] Write unit tests for all label constants and utilities in `backend/tests/unit/test_label_constants.py` — cover: round-trip invariants for build/extract pairs, `find_*` with mixed label formats, edge cases (empty lists, missing name keys, non-matching prefixes), and `has_stalled_label` true/false paths

**Checkpoint**: Foundation ready — Task model includes labels, GraphQL data is propagated, utilities are tested. User story implementation can begin.

---

## Phase 3: User Story 2 — Automatic Label Application During Pipeline Lifecycle (Priority: P1) 🎯 MVP

**Goal**: Apply and swap labels at every pipeline transition point — issue creation, agent assignment, agent transition, and pipeline completion. Labels are written alongside existing tracking table updates for dual-source state tracking.

**Independent Test**: Run a single agent assignment and verify correct labels via the existing label management API. Simulate full pipeline lifecycle (create → assign → transition → complete) and verify label state at each step.

**Why US2 before US1**: The write path (US2) must exist before the read path (US1) has any labels to consume. Per spec: "Without label writes, the read-path (Story 1) has no labels to consume."

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T010 [US2] Write unit tests for label write path in `backend/tests/unit/test_label_write_path.py` — cover: `_build_labels()` with/without `pipeline_config_name`, agent label swap (old removed + new added in single operation), `active` label move between sub-issues, `agent:*` removal on pipeline completion, stalled label removal on re-assignment, and non-blocking error handling (label failure logged as warning, never raises)

### Implementation for User Story 2

- [x] T011 [US2] Extend `_build_labels()` static method to accept optional `pipeline_config_name: str | None = None` parameter and append `build_pipeline_label(pipeline_config_name)` when provided in `backend/src/services/workflow_orchestrator/orchestrator.py`
- [x] T012 [US2] Pass the pipeline config name to `_build_labels()` at parent issue creation call site in `backend/src/services/workflow_orchestrator/orchestrator.py` so new issues receive the `pipeline:<config>` label in their initial label set
- [x] T013 [US2] Add agent label swap logic in `assign_agent_for_status()` in `backend/src/services/workflow_orchestrator/orchestrator.py` — call `update_issue_state()` with `labels_add=[build_agent_label(new_slug)]` and `labels_remove=[build_agent_label(old_slug), STALLED_LABEL]` on the parent issue; wrap in try/except to ensure label failures are non-blocking (FR-017)
- [x] T014 [US2] Add `active` label move between sub-issues in `assign_agent_for_status()` in `backend/src/services/workflow_orchestrator/orchestrator.py` — remove `ACTIVE_LABEL` from previous sub-issue and add to new sub-issue via `update_issue_state()`; wrap in try/except for non-blocking failures
- [x] T015 [P] [US2] Remove `agent:*` label from parent issue on pipeline completion in `backend/src/services/copilot_polling/pipeline.py` — when all agents are done, call `update_issue_state(labels_remove=[current_agent_label])`; also remove `ACTIVE_LABEL` from the last sub-issue
- [x] T016 [US2] Call `ensure_pipeline_labels_exist()` at first pipeline use (before first issue creation) in `backend/src/services/workflow_orchestrator/orchestrator.py` to pre-create fixed labels with correct colors

**Checkpoint**: All pipeline transitions now apply, swap, or remove labels. Verify by running a pipeline lifecycle and checking labels on issues via GitHub API.

---

## Phase 4: User Story 1 — Instant Pipeline State Recovery After Restart (Priority: P1) 🎯 MVP

**Goal**: When the backend restarts or loses its cache, rebuild pipeline state from `pipeline:<config>` and `agent:<slug>` labels with zero additional GitHub API calls beyond the board query. Falls through to existing reconstruction chain when labels are absent.

**Independent Test**: Simulate a cache miss on a parent issue with both pipeline labels. Verify `PipelineState` is built from labels alone without fetching issue body or sub-issues. Verify identical state to what full reconstruction produces.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T017 [US1] Write unit tests for fast-path reconstruction in `backend/tests/unit/test_label_fast_path.py` — cover: `_build_pipeline_from_labels()` produces correct `PipelineState` (current_agent_index, agents list, completed_agents); fast-path returns None when agent slug not found in config; fallthrough to existing chain when labels absent; fallthrough when only one of two required labels present; multiple `agent:` labels selects first match; `labels` parameter is optional (None skips fast-path)

### Implementation for User Story 1

- [x] T018 [US1] Implement `_build_pipeline_from_labels()` helper function in `backend/src/services/copilot_polling/pipeline.py` — accepts issue_number, project_id, status, pipeline_config_name, agent_slug, and PipelineConfig; looks up agent index in config's agent list; builds and returns `PipelineState` or None if agent slug not found
- [x] T019 [US1] Add `labels: list[dict[str, str]] | None = None` parameter to `_get_or_reconstruct_pipeline()` and insert fast-path layer after cache check but before issue body fetch in `backend/src/services/copilot_polling/pipeline.py` — extract config name and agent slug from labels, look up pipeline config from database, call `_build_pipeline_from_labels()`, cache result on success, fall through on failure
- [x] T020 [US1] Propagate `task.labels` from polling loop through to `_get_or_reconstruct_pipeline()` calls in `backend/src/services/copilot_polling/polling_loop.py` — update all call sites that invoke pipeline reconstruction to pass the task's labels
- [x] T021 [P] [US1] Expose labels in task API responses by ensuring `labels` field is serialized in task endpoints in `backend/src/api/projects.py` — verify `TaskListResponse` includes label data for frontend consumption (FR-013)

**Checkpoint**: Pipeline state recovery from labels works with zero additional API calls. Issues without labels fall through to existing reconstruction chain. Verify by clearing cache and confirming fast-path builds correct PipelineState.

---

## Phase 5: User Story 3 — Stalled Issue Detection and Recovery via Labels (Priority: P2)

**Goal**: Apply `stalled` label when recovery detects an idle agent beyond the grace period. Use agent label presence to skip expensive reconciliation for demonstrably active pipelines. Remove `stalled` label on successful re-assignment (already implemented in T013).

**Independent Test**: Simulate a stalled pipeline by setting an agent idle beyond the grace period. Verify `stalled` label appears. Re-assign the agent and verify `stalled` label is removed. Verify active issues with valid agent labels skip reconciliation.

- [x] T022 [US3] Apply `stalled` label when `recover_stalled_issues()` detects an issue needing re-assignment in `backend/src/services/copilot_polling/recovery.py` — call `update_issue_state(labels_add=[STALLED_LABEL])` just before triggering re-assignment; wrap in try/except for non-blocking failure
- [x] T023 [US3] Add early-exit optimization in `recover_stalled_issues()` in `backend/src/services/copilot_polling/recovery.py` — when `task.labels` contains a valid `agent:<slug>` label and `has_stalled_label()` returns False, skip expensive issue body fetch and tracking table parsing for that issue (agent is assigned and not stalled)
- [x] T024 [P] [US3] Pass `task.labels` to recovery functions in `backend/src/services/copilot_polling/polling_loop.py` — ensure `recover_stalled_issues()` receives task objects with populated labels for the early-exit optimization

**Checkpoint**: Stalled issues are visually identifiable via label. Recovery skips unnecessary reconciliation for active issues. Verify by monitoring API call counts during recovery.

---

## Phase 6: User Story 4 — Label-Enriched Board Display (Priority: P2)

**Goal**: Display active agent, pipeline configuration, and stalled status on board cards using labels already fetched by the GraphQL board query. Add pipeline config filter for at-a-glance status without clicking into individual issues.

**Independent Test**: Load the project board with issues that have pipeline labels. Verify agent badge, pipeline config tag, and stalled indicator render on cards. Verify pipeline config filter shows only matching issues.

- [x] T025 [US4] Add pipeline label rendering to `IssueCard` in `frontend/src/components/board/IssueCard.tsx` — parse `agent:<slug>` labels into an active agent badge (purple), `pipeline:<config>` labels into a config tag (blue), and `stalled` label into a warning indicator (red); use existing badge/tag patterns from the component
- [x] T026 [P] [US4] Add pipeline config filter dropdown to `BoardToolbar` in `frontend/src/components/board/BoardToolbar.tsx` — extract unique `pipeline:<config>` values from board items; add a dedicated filter (separate from general label filter) that filters board cards to only show issues matching the selected pipeline config
- [x] T027 [US4] Update board data flow in `frontend/src/components/board/ProjectBoard.tsx` to propagate parsed pipeline label metadata (agent slug, config name, is-stalled) to `IssueCard` components, extracting from `item.labels` array

**Checkpoint**: Board cards display agent badges, pipeline tags, and stalled indicators. Pipeline config filter works. Verify by visual inspection on a board with pipeline-labeled issues.

---

## Phase 7: User Story 5 — Simplified Recovery with Label-Assisted Validation (Priority: P3)

**Goal**: Reduce API call overhead during recovery by using labels to skip unnecessary steps. Create a consolidated validation function that cross-checks labels against tracking tables and fixes the stale source. When `pipeline:<config>` is present, read agent list from config directly (skip sub-issues API). When `agent:<slug>` is present, start reconciliation from that agent's index.

**Independent Test**: Measure API call counts during recovery with vs. without labels. Verify label-assisted path uses fewer calls. Simulate label/tracking-table mismatch and verify correction to the stale source.

### Tests for User Story 5 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T028 [US5] Write unit tests for label validation in `backend/tests/unit/test_label_validation.py` — cover: labels match tracking table (no corrections), labels ahead of tracking table (label stale → fix label), tracking table ahead of labels (table stale → fix label), missing labels fallthrough, ground truth tiebreaker logic, idempotent re-validation, and WARNING-level logging of corrections

### Implementation for User Story 5

- [x] T029 [US5] Create `validate_pipeline_labels()` function in new file `backend/src/services/copilot_polling/state_validation.py` — compare label-derived agent state vs tracking-table-derived agent state; when they disagree, check GitHub ground truth (sub-issue state, assignment) and fix the stale source; return `(corrections_made: bool, correction_descriptions: list[str])`; log corrections at WARNING level
- [x] T030 [US5] Simplify `_self_heal_tracking_table()` using `pipeline:<config>` label for direct config lookup in `backend/src/services/copilot_polling/pipeline.py` — when pipeline config name is available from labels, read agent list from config directly instead of calling the sub-issues API (saves 1–2 API calls per self-heal)
- [x] T031 [US5] Optimize `_validate_and_reconcile_tracking_table()` start index using `agent:<slug>` label in `backend/src/services/copilot_polling/recovery.py` — when agent slug is available, find its index in the pipeline config and only validate agents from that index onward (skip already-completed agents)
- [x] T032 [US5] Integrate `validate_pipeline_labels()` into the polling cycle in `backend/src/services/copilot_polling/polling_loop.py` — call validation at most once per polling cycle per issue, after fast-path reconstruction but before recovery; ensure validation is non-blocking

**Checkpoint**: Recovery uses fewer API calls when labels are present. Label/tracking-table mismatches are detected and corrected. Verify by comparing API call counts before and after.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup across all modified files.

- [x] T033 [P] Run all quickstart.md validation scenarios end-to-end to verify label operations across the full pipeline lifecycle in `specs/034-label-pipeline-state/quickstart.md`
- [x] T034 Code review and cleanup across all modified backend and frontend files — verify consistent error handling (all label writes wrapped in try/except), verify FR-016 (at most one `agent:` label per parent issue), verify FR-015 (tracking table remains authoritative)
- [x] T035 [P] Verify all existing tests pass with new label fields — run `pytest backend/tests/` to confirm no regressions from Task model extension or function signature changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US2 (Phase 3)**: Depends on Phase 2 — write path must exist before read path
- **US1 (Phase 4)**: Depends on Phase 2 — can run in parallel with US2 for test/implementation, but integration requires US2 labels
- **US3 (Phase 5)**: Depends on Phase 2 — can start after Foundational; stalled removal logic is in US2's T013
- **US4 (Phase 6)**: Depends on Phase 2 (frontend types) — can proceed in parallel with backend stories once labels are in API responses
- **US5 (Phase 7)**: Depends on US1 (fast-path) and US2 (write path) — validation cross-checks both
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US2 (P1)**: Can start after Phase 2 — No dependencies on other stories. **Should be implemented first** as it produces the labels other stories consume.
- **US1 (P1)**: Can start after Phase 2 — Functionally independent (reads labels from any source), but benefits from US2 writing labels in production.
- **US3 (P2)**: Can start after Phase 2 — Stalled label removal already in US2's `assign_agent_for_status()` (T013). Only adds stalled label application.
- **US4 (P2)**: Can start after Phase 2 — Frontend-only, uses labels already in API responses. Independent of backend US3/US5.
- **US5 (P3)**: Depends on US1 + US2 — Cross-checks fast-path labels against tracking table, needs both to exist.

### Within Each User Story

- Tests MUST be written and FAIL before implementation (spec-mandated TDD)
- Constants/utilities before services
- Services before endpoints/UI
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 2**: T006, T007, T008, T009 can all run in parallel (different files)
- **Phase 3 (US2)**: T015 can run in parallel with T011–T014 (different file: pipeline.py vs orchestrator.py)
- **Phase 4 (US1)**: T021 can run in parallel with T018–T019 (different file: api/projects.py vs pipeline.py)
- **Phase 5 (US3)**: T024 can run in parallel with T022–T023 (different file: polling_loop.py vs recovery.py)
- **Phase 6 (US4)**: T026 can run in parallel with T025 (different files: BoardToolbar.tsx vs IssueCard.tsx)
- **Cross-story**: US4 (frontend) can proceed entirely in parallel with US3 (backend) once Phase 2 is complete

---

## Parallel Example: User Story 2

```text
# After Phase 2 is complete, launch US2 tests first:
Task T010: "Write unit tests for label write path in backend/tests/unit/test_label_write_path.py"

# Then implementation — T015 can run in parallel with T011-T014:
Parallel group A (orchestrator.py, sequential):
  Task T011: "Extend _build_labels() with pipeline_config_name"
  Task T012: "Apply pipeline:<config> label at issue creation"
  Task T013: "Add agent label swap in assign_agent_for_status()"
  Task T014: "Move active label between sub-issues"
  Task T016: "Call ensure_pipeline_labels_exist() at pipeline launch"

Parallel group B (pipeline.py):
  Task T015: "Remove agent:* label on pipeline completion"
```

## Parallel Example: User Story 1

```text
# Tests first:
Task T017: "Write unit tests for fast-path reconstruction"

# Then implementation — T021 can run in parallel with T018-T020:
Parallel group A (pipeline.py + polling_loop.py, sequential):
  Task T018: "Implement _build_pipeline_from_labels()"
  Task T019: "Add fast-path layer to _get_or_reconstruct_pipeline()"
  Task T020: "Propagate task.labels through polling loop"

Parallel group B (api/projects.py):
  Task T021: "Expose labels in task API responses"
```

## Parallel Example: Cross-Story Parallelism

```text
# Once Phase 2 (Foundational) is complete, these can proceed simultaneously:
Developer A (backend): US2 → US1 → US3 → US5 (sequential backend pipeline)
Developer B (frontend): US4 (independent frontend work)
```

---

## Implementation Strategy

### MVP First (US2 + US1 Only)

1. Complete Phase 1: Setup (label constants and utilities)
2. Complete Phase 2: Foundational (Task model, label propagation, pre-creation, utility tests)
3. Complete Phase 3: US2 — Label write path (pipeline transitions apply labels)
4. Complete Phase 4: US1 — Fast-path reconstruction (labels enable zero-API-call recovery)
5. **STOP and VALIDATE**: Test fast-path by clearing cache and verifying PipelineState builds from labels
6. Deploy/demo if ready — pipeline operates with label-assisted recovery

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US2 (label writes) → Test label application at transitions → **Labels now appear on issues**
3. Add US1 (fast-path reads) → Test zero-API-call recovery → **Deploy MVP!**
4. Add US3 (stalled detection) → Test stalled label lifecycle → **Recovery efficiency improved**
5. Add US4 (board display) → Test badge rendering → **Visual pipeline status on board**
6. Add US5 (label validation) → Test cross-check corrections → **Full label integrity**
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US2 → US1 → US3 → US5 (backend pipeline, sequential)
   - Developer B: US4 (frontend, fully independent after Phase 2)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- All label write operations MUST be wrapped in try/except — failures are logged at WARNING level but never block pipeline progression (FR-017)
- At most one `agent:` label per parent issue at any time (FR-016)
- Tracking table remains the authoritative audit trail — labels supplement but never replace it (FR-015)
- Issues created before this feature (no pipeline labels) gracefully fall through to existing reconstruction chain (FR-012)
- Label operations are idempotent — safe for concurrent polling cycles
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
