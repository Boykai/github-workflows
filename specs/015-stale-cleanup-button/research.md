# Research: Add 'Clean Up' Button to Delete Stale Branches and PRs

**Feature**: 015-stale-cleanup-button  
**Date**: 2026-03-01  
**Status**: Complete

## R1: Branch-to-Issue Cross-Referencing Strategy

**Decision**: Use a three-layer cross-referencing approach to determine if a branch is linked to an open issue on the project board:
1. **Branch naming convention**: Match patterns like `issue-{number}`, `{number}-feature-name`, `copilot/fix-{number}` against open issue numbers.
2. **PR body references**: Parse PR bodies for issue references (`Closes #N`, `Fixes #N`, `Resolves #N`, `#N`).
3. **GitHub timeline events API**: Query issue timeline events for `CONNECTED_EVENT` and `CROSS_REFERENCED_EVENT` to find linked branches/PRs.

**Rationale**: The spec (FR-005, FR-006) requires resolving branch-to-issue and PR-to-issue associations. No single method is 100% reliable — branch naming conventions may not always be followed, PR body references can be missing, and timeline events may not capture all linkages. The existing codebase already uses timeline events in `get_linked_pull_requests()` (service.py:2394) and REST search in `_search_open_prs_for_issue_rest()` (service.py:2152). Combining all three maximizes accuracy (SC-002: 100% accurate categorization).

**Alternatives considered**:
- Branch naming only: Too fragile; many branches don't follow naming conventions (e.g., `copilot/add-clean-up-button`).
- Timeline events only: Misses branches that are linked by convention but not through GitHub's linking UI.
- GitHub Search API: Rate-limited separately and returns results with a delay; not suitable for real-time preflight.

## R2: API Architecture — Preflight vs. Execute Split

**Decision**: Implement two backend endpoints:
1. `POST /api/v1/cleanup/preflight` — Fetches all branches, PRs, and project board issues; computes and returns deletion/preservation lists without performing any mutations.
2. `POST /api/v1/cleanup/execute` — Accepts the confirmed deletion list and performs the deletions sequentially, returning a single JSON response once execution is complete (no streamed progress events).

**Rationale**: The spec (FR-002, FR-003) requires the confirmation modal to be populated from a preflight fetch, not at button render time. Separating preflight from execution ensures the user reviews an accurate, up-to-date list before any destructive action. For execution, the current implementation performs the whole batch and then returns a single JSON result, while the frontend shows an indeterminate spinner during the operation. This keeps the implementation simple and consistent with existing JSON-based task flows, while still satisfying the core requirement that the user can initiate cleanup and be notified when it finishes. POST is used instead of GET for preflight because the request may include project board context and the response can be large.

**Alternatives considered**:
- Single endpoint with confirmation token: Simpler but conflates data retrieval with mutation intent; harder to retry preflight independently.
- SSE-based streaming progress for `/cleanup/execute`: Initially explored to provide fine-grained progress updates (FR-009), but deferred to keep the backend and frontend implementation aligned with the existing single-response pattern.
- WebSocket for progress: More complex to implement and operate; not necessary given the current indeterminate-progress UX.
- Polling for progress: Would require additional state management to track job IDs and introduces extra API surface area for limited UX benefit in this feature.

## R3: PR Closure Strategy

**Decision**: Close PRs by patching their state to `closed` via `PATCH /repos/{owner}/{repo}/pulls/{pull_number}` with `{"state": "closed"}`, rather than deleting the PR.

**Rationale**: GitHub does not support deleting PRs via API — only closing them. The spec (FR-008) says "delete all pull requests" but the technical notes clarify to use `PATCH` with `state=closed`. Closing preserves the PR history for auditability. When the associated branch is deleted, the PR will show as having a deleted head branch, which is the standard GitHub behavior.

**Alternatives considered**:
- Delete PR (not supported): GitHub API does not provide a DELETE endpoint for pull requests.
- Close PR and delete branch separately: This is what we do — close the PR first, then delete the branch (if not already scheduled for separate deletion).

## R4: Rate Limit Handling During Batch Deletions

**Decision**: Execute deletions sequentially with a configurable delay between operations (default: 200ms). Use the existing `_request_with_retry()` method for exponential backoff on 429/403 rate-limit responses. Batch size of 1 (sequential) by default.

**Rationale**: GitHub's secondary rate limit penalizes bursts of mutation requests. The existing codebase (service.py:92-176) has a battle-tested retry mechanism with exponential backoff (1s initial, 30s max, 3 retries). Sequential execution with small delays is the safest approach for destructive operations — it's predictable, debuggable, and avoids concurrent deletion race conditions. The spec (FR-014) explicitly requires sequential or batched execution.

**Alternatives considered**:
- Parallel deletions with semaphore: Faster but risks triggering secondary rate limits; harder to provide accurate progress updates.
- Client-side batching: Moves rate-limit awareness to the frontend, which has no visibility into GitHub API headers.
- Queue-based async processing: Overengineered for a user-initiated, interactive operation.

## R5: Permission Verification Approach

**Decision**: Verify permissions during the preflight phase by attempting a lightweight GitHub API call that requires the `repo` scope (e.g., listing repository collaborator permissions for the authenticated user via `GET /repos/{owner}/{repo}/collaborators/{username}/permission`). If the user lacks `push` access or higher, return a clear 403 error before showing the confirmation modal.

**Rationale**: The spec (FR-011, SC-006) requires permission verification before attempting any deletions, with a clear error if permissions are lacking. Checking the user's permission level during preflight — rather than waiting for a deletion to fail — provides a fast, clear failure mode (within 3 seconds per SC-006). The `repo` scope is needed for branch deletion; `push` access is the minimum required permission.

**Alternatives considered**:
- Check OAuth scopes via token introspection: GitHub doesn't expose scope details via a standard API; scopes are returned in the OAuth response but may not reflect repository-level permissions.
- Try a deletion and catch the 403: Wastes time and may partially execute before the first failure; poor UX.
- Check permissions client-side: Not reliable; permissions must be verified server-side.

## R6: Audit Trail Storage

**Decision**: Store audit trail entries in a new `cleanup_audit_logs` SQLite table. Each cleanup operation creates one summary row. Detailed per-item results are stored as a JSON blob in a `details` column on the summary row.

**Rationale**: The spec (FR-013, SC-008) requires a detailed audit trail of deleted and preserved items. The existing codebase uses SQLite for all persistent data. A single table with a JSON details column is simple and avoids the complexity of a normalized per-item table. The audit log is primarily for human review (not querying individual items), so a JSON blob is appropriate. The next available migration number is 008.

**Alternatives considered**:
- Normalized per-item table: More SQL-queryable but adds complexity for a feature that's primarily about displaying a log to the user. Violates YAGNI.
- File-based logging: Harder to query and associate with user sessions; not persistent across container restarts.
- No persistent storage (summary only): Loses the audit trail once the browser session ends; spec requires post-operation review capability.

## R7: Frontend Component Architecture

**Decision**: Create three new components:
1. `CleanUpButton.tsx` — Button with tooltip, triggers preflight on click.
2. `CleanUpConfirmModal.tsx` — Modal displaying deletion/preservation lists with confirm/cancel actions.
3. `CleanUpSummary.tsx` — Post-operation summary with audit trail details.

Use a `useCleanup` hook to manage the full workflow state (idle → loading → confirming → executing → summary → idle).

**Rationale**: The existing codebase separates concerns into focused components (`IssueDetailModal`, `AddAgentPopover`, etc.). The three-component split maps directly to the three phases of the user workflow: initiation, confirmation, and results. The `useCleanup` hook follows the existing pattern of custom hooks for async state (`useMcpSettings`, etc.). The modal follows the pattern established by `IssueDetailModal.tsx` (backdrop click, escape key, body scroll lock, `role="dialog"`).

**Alternatives considered**:
- Single monolithic component: Harder to test and maintain; violates the existing component granularity pattern.
- Separate page for cleanup: Breaks the flow; the user should stay on the board page.
- Context provider for state: Overkill for a single-feature workflow; a hook is sufficient.

## R8: Project Board Issue Resolution

**Decision**: Use the GitHub Projects v2 GraphQL API to fetch all open issues on the linked project board. The existing `get_project_items()` method (service.py) already fetches project items with cursor-based pagination. Filter items by status (open issues only) and extract issue numbers for cross-referencing.

**Rationale**: The spec requires preservation based on the project board, not just any open issue in the repository. The existing codebase has robust Projects v2 GraphQL integration including `get_board_data()` and `get_project_items()`. Reusing these methods avoids duplicating pagination and field-parsing logic.

**Alternatives considered**:
- REST Issues API (`GET /repos/{owner}/{repo}/issues`): Returns all open issues, not just those on the project board. Would over-preserve branches.
- Classic Projects API: Out of scope per spec assumptions (Projects v2 only).
- Repository-level issue query: Doesn't filter by project board membership.
