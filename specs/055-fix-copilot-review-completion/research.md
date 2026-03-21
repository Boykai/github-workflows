# Research: Fix Premature Copilot Review Completion in Agent Pipeline

**Feature**: `055-fix-copilot-review-completion` | **Date**: 2026-03-21

## R1: Pipeline-Position Guard Pattern in _check_copilot_review_done()

**Decision**: Add an optional `pipeline` parameter to `_check_copilot_review_done()`. When provided, if `pipeline.current_agent != "copilot-review"`, return `False` immediately before any API calls.

**Rationale**: The function currently performs expensive operations (fetching issue comments, discovering PRs, checking reviews) before determining that the result is irrelevant because copilot-review isn't the active agent. The guard is the innermost defense — even if all upstream callers incorrectly invoke the function, it short-circuits safely. The existing `_pipeline_allows_copilot_review_request()` in `completion.py` (line 1249) already validates pipeline position for *requesting* reviews. This guard adds the same check for *detecting completion*.

The guard must be optional (`pipeline: "object | None" = None`) to preserve backward compatibility for any call sites that don't have pipeline context. When `pipeline` is `None`, the function proceeds with its existing logic (no guard applied).

**Alternatives Considered**:
- **Guard only in callers**: Rejected — defense-in-depth requires the innermost function to self-protect; callers can be added or modified without remembering to add the guard
- **Mandatory pipeline parameter**: Rejected — would break any existing call sites that don't have pipeline context; optional preserves backward compatibility
- **Decorator-based guard**: Rejected — adds abstraction for a single check; inline `if` is simpler and more readable

## R2: Passing Pipeline Through _check_agent_done_on_sub_or_parent()

**Decision**: In `_check_agent_done_on_sub_or_parent()`, pass the existing `pipeline` parameter to `_check_copilot_review_done()` when calling for the `copilot-review` agent.

**Rationale**: The function already accepts a `pipeline` parameter (line 168: `pipeline: "object | None" = None`) but doesn't pass it through to `_check_copilot_review_done()` at line 195. This is the exact gap that allows the guard bypass. The fix is a single-line change — adding `pipeline=pipeline` to the call.

The `pipeline` parameter is already available at the call site because `_check_agent_done_on_sub_or_parent()` receives it from `_process_pipeline_completion()` which always has the pipeline object.

**Alternatives Considered**:
- **Look up pipeline from cache inside `_check_copilot_review_done()`**: Rejected — requires knowing the issue number-to-pipeline mapping, adds coupling to cache internals, and the pipeline is already available in the caller
- **Pass only `current_agent` string instead of full pipeline**: Rejected — the full pipeline provides future extensibility (e.g., group-aware checks) without additional parameters

## R3: Pipeline-Position Guard in check_in_review_issues()

**Decision**: In `check_in_review_issues()`, after pipeline retrieval, if the pipeline exists and its `current_agent` is not `copilot-review`, log a warning and let `_process_pipeline_completion()` handle the current agent naturally.

**Rationale**: The function iterates all "In Review" issues and checks for copilot-review completion. When the board shows "In Review" but the pipeline's current agent is still an earlier agent (e.g., `speckit.implement`), the function should not process copilot-review completion. The existing code at lines 2322–2348 already handles the case where the pipeline status disagrees with the board status — it adjusts `effective_from_status` and `effective_to_status`. However, it still proceeds to call `_process_pipeline_completion()`, which may invoke `_check_agent_done_on_sub_or_parent()` for copilot-review. The Phase 1 guard in `_check_copilot_review_done()` (R1) is the innermost defense here. The `check_in_review_issues()` guard provides an additional outer layer that logs the mismatch and avoids unnecessary work.

**Alternatives Considered**:
- **Skip the issue entirely**: Rejected — the issue may have a non-copilot-review agent that needs advancement; `_process_pipeline_completion()` should handle that
- **Only rely on the inner guard**: Rejected — defense-in-depth; the outer guard reduces unnecessary API calls for issues that can't possibly complete copilot-review

## R4: Webhook Pipeline Validation Guard

**Decision**: In `update_issue_status_for_copilot_pr()`, before calling `update_item_status_by_name("In Review")`, check if a pipeline exists for the issue. If a pipeline exists and its `current_agent != "copilot-review"`, skip the status move and return a "skipped" result.

**Rationale**: The webhook fires whenever ANY Copilot PR becomes ready for review — including PRs from `speckit.implement` or other coding agents. The webhook should only move the issue to "In Review" when it's actually time for copilot-review. For non-pipeline issues (backward compatibility), the webhook continues to move status as before.

The pipeline state is accessed via `_cp.get_pipeline_state(issue_number)` which is an in-memory cache lookup — zero API calls. If no pipeline is cached (e.g., non-pipeline issue or after restart), the webhook proceeds with its default behavior.

**Alternatives Considered**:
- **Guard in `handle_pull_request_event()` instead**: Rejected — `handle_pull_request_event()` doesn't have easy access to the issue number before calling `update_issue_status_for_copilot_pr()`; the guard is more natural inside the function that performs the status update
- **Always block webhook status moves for pipeline issues**: Rejected — when copilot-review IS the current agent, the webhook should still move the issue to "In Review" (this is the correct behavior)
- **Remove webhook status move entirely**: Rejected — breaks backward compatibility for non-pipeline issues

## R5: SQLite Durable Timestamp Storage

**Decision**: Create a `copilot_review_requests` table in SQLite with columns `issue_number` (PK), `requested_at` (TEXT, ISO 8601), and `project_id` (TEXT). Persist timestamps on write; recover from DB when in-memory cache misses.

**Rationale**: The current in-memory `_copilot_review_requested_at` (a `BoundedDict` with max 200 entries) is lost on server restart. The existing recovery mechanism parses HTML comments from the issue body, which is unreliable (comments can be edited, body format can change). SQLite provides a durable, reliable recovery path.

The table uses `INSERT OR REPLACE` semantics (SQLite's `REPLACE` behavior) to handle re-requests without requiring UPDATE logic. The `project_id` column enables future multi-project support and aids debugging.

The recovery priority is: in-memory dict → SQLite query → HTML comment parsing (existing fallback preserved).

**Alternatives Considered**:
- **Redis/external cache**: Rejected — adds external dependency; SQLite is already used for other durable state (migrations 023–032)
- **File-based persistence**: Rejected — SQLite provides ACID guarantees, concurrent access safety, and is already used in the project
- **Remove HTML comment fallback**: Rejected — HTML comments may contain timestamps from before the migration; keeping the fallback ensures continuity during the transition
- **Store in the tracking table (issue body)**: Rejected — this is the current approach and it's unreliable; SQLite is the fix for this exact problem

## R6: Pipeline Reconstruction Safety for "In Review" Status

**Decision**: Verify that the existing tracking-table guard in `_get_or_reconstruct_pipeline()` correctly handles the "In Progress agents pending but board says In Review" scenario. Add test coverage but no code changes.

**Rationale**: The code at lines 404–451 of `pipeline.py` already implements this guard:
1. It parses the tracking table from the issue body (line 387)
2. Finds the first incomplete (Pending/Active) step (line 406)
3. If that step is in a different (earlier) status than the board claims, it checks for incomplete agents in the earlier status (lines 415–420)
4. If found, it reconstructs the pipeline for the earlier status (lines 427–451)

This logic correctly prevents the false `current_agent="copilot-review"` assignment described in the issue. The fix in Phase 1 (guards in `_check_copilot_review_done()`) provides defense-in-depth even if reconstruction fails.

**Alternatives Considered**:
- **Rewrite reconstruction logic**: Rejected — the existing logic is correct; adding guards upstream is simpler and less risky
- **Add a separate "reconstruction validation" step**: Rejected — would duplicate the existing tracking-table check
