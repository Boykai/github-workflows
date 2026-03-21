# Tasks: Fix Premature Copilot Review Completion in Agent Pipeline

**Input**: Design documents from `/specs/055-fix-copilot-review-completion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Tasks below focus on implementation only. The spec notes "unit tests optional per constitution."

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. User stories map directly to the phased implementation plan.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app backend**: `solune/backend/src/` (all changes are backend-only)
- **Migrations**: `solune/backend/src/migrations/`
- **Key files**:
  - `solune/backend/src/services/copilot_polling/helpers.py`
  - `solune/backend/src/services/copilot_polling/pipeline.py`
  - `solune/backend/src/services/copilot_polling/state.py`
  - `solune/backend/src/api/webhooks.py`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project setup needed — all changes modify existing files within `solune/backend/`. This phase covers the one new file that must exist before other phases.

- [x] T001 Create SQLite migration file `solune/backend/src/migrations/033_copilot_review_requests.sql` with `copilot_review_requests` table (columns: `issue_number INTEGER PRIMARY KEY`, `requested_at TEXT NOT NULL`, `project_id TEXT`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add pipeline-position guard to the innermost completion-detection function. This is the core defense-in-depth guard that MUST be in place before any other guard can be effective.

**⚠️ CRITICAL**: Phases 3 and 4 depend on this phase being complete. The guard in `_check_copilot_review_done()` is the innermost defense — even if all upstream guards fail, this prevents false completion.

- [x] T002 Add optional `pipeline` parameter (`pipeline: "object | None" = None`) to `_check_copilot_review_done()` function signature in `solune/backend/src/services/copilot_polling/helpers.py`
- [x] T003 Add pipeline-position guard at the top of `_check_copilot_review_done()` body in `solune/backend/src/services/copilot_polling/helpers.py` — if `pipeline` is provided and `pipeline.current_agent != "copilot-review"`, return `False` immediately with a warning log before any API calls
- [x] T004 Pass `pipeline=pipeline` kwarg from `_check_agent_done_on_sub_or_parent()` to `_check_copilot_review_done()` at the copilot-review branch (~line 194) in `solune/backend/src/services/copilot_polling/helpers.py`

**Checkpoint**: The innermost guard is in place. `_check_copilot_review_done()` now short-circuits when copilot-review is not the current agent. All callers that have pipeline context pass it through.

---

## Phase 3: User Story 1 — Pipeline Correctly Sequences Agent Completion (Priority: P1) 🎯 MVP

**Goal**: Ensure the system only marks the copilot-review step as complete when it is genuinely the current active agent. When earlier agents (such as speckit.implement) finish, copilot-review must NOT be falsely marked done.

**Independent Test**: Run a pipeline where speckit.implement completes and verify that copilot-review is NOT marked as done until the pipeline has actually advanced to the copilot-review step.

**Depends on**: Phase 2 (foundational guards in `_check_copilot_review_done()`)

### Implementation for User Story 1

- [x] T005 [US1] Add pipeline-position guard to `check_in_review_issues()` in `solune/backend/src/services/copilot_polling/pipeline.py` — after pipeline retrieval (~line 2328), if `pipeline.current_agent != "copilot-review"` and the pipeline status is earlier than "In Review", log a warning and let `_process_pipeline_completion()` handle advancing the current (non-copilot-review) agent only
- [x] T006 [US1] Add warning log message in `check_in_review_issues()` guard in `solune/backend/src/services/copilot_polling/pipeline.py` — include current agent name and issue number in the log for debugging

**Checkpoint**: User Story 1 is complete. The completion-detection function (`_check_copilot_review_done`) and the poller (`check_in_review_issues`) both guard against false copilot-review completion when it is not the current agent. Verify by confirming: (1) `_check_copilot_review_done(pipeline=pipeline_with_implement)` returns `False` without API calls, (2) `check_in_review_issues()` skips copilot-review processing when current agent is not copilot-review.

---

## Phase 4: User Story 2 — Webhook Does Not Prematurely Move Issues to "In Review" (Priority: P1)

**Goal**: Webhook-triggered status changes respect the pipeline's current position. An issue is not moved to "In Review" on the project board before the pipeline has reached the copilot-review step.

**Independent Test**: Simulate a webhook "ready_for_review" event while the pipeline's current agent is speckit.implement and verify the issue status is NOT changed to "In Review".

**Depends on**: Phase 2 (foundational guards)

### Implementation for User Story 2

- [x] T007 [US2] Add pipeline-position guard to `update_issue_status_for_copilot_pr()` in `solune/backend/src/api/webhooks.py` — before the `update_item_status_by_name("In Review")` call (~line 557), retrieve the pipeline state for the issue number
- [x] T008 [US2] Implement guard logic in `update_issue_status_for_copilot_pr()` in `solune/backend/src/api/webhooks.py` — if pipeline exists AND `pipeline.current_agent != "copilot-review"`, skip the status move, log a warning with current agent name, and return a "skipped" result dict (with keys: `status`, `event`, `pr_number`, `issue_number`, `reason`, `current_agent`, `message`)
- [x] T009 [US2] Ensure backward compatibility in `update_issue_status_for_copilot_pr()` in `solune/backend/src/api/webhooks.py` — if no pipeline is cached for the issue, proceed with the status move as normal (non-pipeline issues continue to work)

**Checkpoint**: User Story 2 is complete. Webhooks no longer prematurely move pipeline-tracked issues to "In Review". Verify: (1) webhook fires with current_agent="speckit.implement" → status NOT moved, (2) webhook fires with current_agent="copilot-review" → status moved normally, (3) webhook fires with no pipeline → status moved normally (backward compat).

---

## Phase 5: User Story 3 — Review-Request Timestamp Survives Server Restart (Priority: P2)

**Goal**: The review-request timestamp is durably stored in SQLite so that a server restart does not lose the record. Recovery priority: in-memory → SQLite → HTML comment (existing fallback preserved).

**Independent Test**: Record a review-request timestamp, clear the in-memory store (simulating restart), and verify the system recovers the timestamp from SQLite.

**Depends on**: Phase 1 (migration file T001)

### Implementation for User Story 3

- [x] T010 [US3] Add SQLite write to `_record_copilot_review_request_timestamp()` in `solune/backend/src/services/copilot_polling/helpers.py` — after storing in the in-memory `_copilot_review_requested_at` dict, INSERT OR REPLACE into `copilot_review_requests` table with `issue_number`, `requested_at` (ISO 8601), and `project_id`
- [x] T011 [US3] Add error handling around the SQLite write in `_record_copilot_review_request_timestamp()` in `solune/backend/src/services/copilot_polling/helpers.py` — wrap in try/except, log warning on failure, never crash the caller
- [x] T012 [US3] Add SQLite recovery to `_check_copilot_review_done()` in `solune/backend/src/services/copilot_polling/helpers.py` — when `_copilot_review_requested_at.get(parent_issue_number)` returns `None`, query `copilot_review_requests` table before falling back to HTML comment parsing
- [x] T013 [US3] Cache recovered timestamp in `_check_copilot_review_done()` in `solune/backend/src/services/copilot_polling/helpers.py` — when SQLite recovery succeeds, store the recovered timestamp back into `_copilot_review_requested_at` for subsequent fast access
- [x] T014 [US3] Add error handling around the SQLite read in `_check_copilot_review_done()` in `solune/backend/src/services/copilot_polling/helpers.py` — wrap in try/except, log warning on failure, fall through to existing HTML comment fallback

**Checkpoint**: User Story 3 is complete. Timestamps survive server restarts via SQLite persistence. Verify: (1) record a timestamp → check SQLite table has the row, (2) clear in-memory dict → completion check recovers from SQLite, (3) SQLite unavailable → falls back to HTML comment parsing.

---

## Phase 6: User Story 4 — Pipeline Reconstruction Does Not Falsely Set Current Agent (Priority: P2)

**Goal**: Pipeline reconstruction correctly determines the current agent even when the board status says "In Review" but earlier agents are still pending.

**Independent Test**: Call `_get_or_reconstruct_pipeline()` with status="In Review" while agents marked "In Progress" are still pending and verify it reconstructs the pipeline with the correct current agent.

**Depends on**: Phase 2 (foundational guards provide defense-in-depth even if reconstruction has edge cases)

### Implementation for User Story 4

- [x] T015 [US4] Verify the existing tracking-table guard in `_get_or_reconstruct_pipeline()` (~lines 404–451) in `solune/backend/src/services/copilot_polling/pipeline.py` correctly handles the scenario where the board says "In Review" but tracking data shows agents still "In Progress" — confirm the `first_incomplete` check detects pending agents and reconstructs for the earlier status
- [x] T016 [US4] Add a clarifying code comment in `_get_or_reconstruct_pipeline()` in `solune/backend/src/services/copilot_polling/pipeline.py` at the tracking-table guard section documenting the specific scenario this guard protects against (board says "In Review" due to webhook bug, but speckit.implement is still pending)

**Checkpoint**: User Story 4 is complete. Pipeline reconstruction correctly handles status disagreements between the board and tracking data. Combined with the Phase 2 guards, even if reconstruction has a failure mode, false completion is prevented.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup across all guard layers

- [x] T017 Run backend linter (`ruff check src/`) from `solune/backend/` to validate all modified files pass linting
- [x] T018 Run quickstart.md validation steps (lint + type check) to confirm no regressions
- [x] T019 Review all warning log messages across guards (T003, T006, T008, T015) for consistency in format and detail level

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately (migration file)
- **Foundational (Phase 2)**: No dependencies — can start immediately (parallel with Phase 1)
- **US1 (Phase 3)**: Depends on Phase 2 (foundational guards must exist)
- **US2 (Phase 4)**: Depends on Phase 2 (foundational guards must exist); parallel with Phase 3
- **US3 (Phase 5)**: Depends on Phase 1 (migration file must exist); parallel with Phases 3 & 4
- **US4 (Phase 6)**: Depends on Phase 2 (foundational guards provide defense-in-depth); parallel with Phases 3–5
- **Polish (Phase 7)**: Depends on all previous phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Depends on Phase 2 — no dependencies on other stories
- **User Story 2 (P1)**: Depends on Phase 2 — no dependencies on other stories (parallel with US1)
- **User Story 3 (P2)**: Depends on Phase 1 — no dependencies on other stories (parallel with US1/US2)
- **User Story 4 (P2)**: Depends on Phase 2 — no dependencies on other stories (parallel with US1/US2/US3)

### Within Each User Story

- Guard logic before logging
- Core implementation before error handling
- All changes within a story target specific, named functions in specific files

### Parallel Opportunities

- **Phase 1 + Phase 2**: Can run in parallel (migration file vs. helpers.py guard)
- **T002 + T003**: Sequential (signature change before guard logic)
- **T005 + T006**: Sequential (guard before log message in same function)
- **T007 + T008 + T009**: Sequential (all in same function in webhooks.py)
- **T010 + T011**: Sequential (write before error handling in same function)
- **T012 + T013 + T014**: Sequential (read + cache + error handling in same function)
- **US1 + US2**: Can run in parallel after Phase 2 (different files: pipeline.py vs. webhooks.py)
- **US3**: Can run in parallel with US1/US2 after Phase 1 (same file helpers.py but different functions)
- **US4**: Can run in parallel with US1/US2/US3 (different section of pipeline.py)

---

## Parallel Example: After Foundational Phase

```bash
# Once Phase 2 (Foundational) is complete, these can run in parallel:

# Developer A — User Story 1 (pipeline.py: check_in_review_issues)
Task T005: Add pipeline-position guard to check_in_review_issues() in pipeline.py
Task T006: Add warning log message in check_in_review_issues() guard in pipeline.py

# Developer B — User Story 2 (webhooks.py: update_issue_status_for_copilot_pr)
Task T007: Add pipeline-position guard to update_issue_status_for_copilot_pr() in webhooks.py
Task T008: Implement guard logic with skipped result in webhooks.py
Task T009: Ensure backward compatibility for non-pipeline issues in webhooks.py

# Developer C — User Story 3 (helpers.py: timestamp persistence)
Task T010: Add SQLite write to _record_copilot_review_request_timestamp() in helpers.py
Task T011: Add error handling around SQLite write in helpers.py
Task T012: Add SQLite recovery to _check_copilot_review_done() in helpers.py
Task T013: Cache recovered timestamp in _check_copilot_review_done() in helpers.py
Task T014: Add error handling around SQLite read in helpers.py

# Developer D — User Story 4 (pipeline.py: _get_or_reconstruct_pipeline)
Task T015: Verify tracking-table guard in _get_or_reconstruct_pipeline() in pipeline.py
Task T016: Add clarifying code comment in _get_or_reconstruct_pipeline() in pipeline.py
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 — both P1)

1. Complete Phase 1: Migration file (T001)
2. Complete Phase 2: Foundational guards in `_check_copilot_review_done()` (T002–T004)
3. Complete Phase 3: User Story 1 — poller guard in `check_in_review_issues()` (T005–T006)
4. Complete Phase 4: User Story 2 — webhook guard in `update_issue_status_for_copilot_pr()` (T007–T009)
5. **STOP and VALIDATE**: The core bug is fixed — copilot-review can no longer be falsely marked done, and webhooks no longer prematurely move issues to "In Review"

### Incremental Delivery

1. Complete Setup + Foundational → Guards are in place (T001–T004)
2. Add User Story 1 → Poller guards active (T005–T006) → **Core bug prevented**
3. Add User Story 2 → Webhook guards active (T007–T009) → **Board state correct**
4. Add User Story 3 → Durable timestamps (T010–T014) → **Restart resilience**
5. Add User Story 4 → Reconstruction verified (T015–T016) → **Full defense-in-depth**
6. Polish → Lint, validate, review (T017–T019) → **Production ready**

---

## Notes

- All changes are backend-only — no frontend modifications needed
- No new dependencies — aiosqlite and SQLite are already used in the project
- Guards are inline `if` checks with early returns — no new abstractions
- Zero-cost when guard passes — guard checks are in-memory pipeline cache lookups; no API calls
- Backward compatible — all guards are optional (skip when no pipeline context available)
- Defense-in-depth — three independent guard layers prevent false completion even if one fails
- Total tasks: 19
- Task count per user story: US1=2, US2=3, US3=5, US4=2, Setup=1, Foundational=3, Polish=3
- Suggested MVP scope: Phases 1–4 (Setup + Foundational + US1 + US2) = 10 tasks
