# Research: Chores Page — Counter Fixes, Featured Rituals Panel, Inline Editing, AI Enhance Toggle, Agent Pipeline Config & Auto-Merge PR Flow

**Feature**: 029-chores-page-enhancements | **Date**: 2026-03-07

## R1: Per-Chore Issue Counter Query Strategy

**Task**: Determine how to accurately count GitHub Parent Issues created since each Chore's last execution, scoping the count per-Chore rather than using the global `parent_issue_count` passed to `evaluate_triggers()`.

**Decision**: Continue using the existing global `parent_issue_count` for count-based trigger evaluation, but fix the counter display to show `schedule_value - (current_count - last_triggered_count)` as the "remaining" count on each tile. Add an `execution_count` column to the `chores` table for the "Most Run" ranking. The existing `last_triggered_count` field already stores the parent issue count at last trigger — the delta `current_count - last_triggered_count` gives the per-Chore scoped count.

**Rationale**: The existing `counter.py` already computes `issues_since = current_count - chore.last_triggered_count`, which IS a per-Chore scoped count (it measures issues since that specific Chore last fired). The tile display simply needs to show `schedule_value - issues_since` as the remaining count. The global `parent_issue_count` is the total count of Parent Issues in the project; each Chore's `last_triggered_count` snapshots this global count at trigger time, making the delta per-Chore. No new GitHub API query is needed — the existing mechanism is correct, only the display was wrong. Adding `execution_count` (incremented on each trigger) enables the "Most Run" Featured Rituals card without expensive history queries.

**Alternatives Considered**:
- **Per-Chore timestamp-bounded GitHub API query**: Rejected — requires N API calls per page load (one per Chore), adds latency and rate limit pressure. The existing snapshot-delta approach achieves the same accuracy with zero API calls.
- **Store individual issue references per Chore**: Rejected — over-engineered; the count is sufficient for the counter display and trigger evaluation. No need to track which specific issues were counted.

---

## R2: Featured Rituals Panel Data Derivation

**Task**: Determine how to compute the three Featured Rituals rankings (Next Run, Most Recently Run, Most Run) without adding new database tables or expensive queries.

**Decision**: Compute all three rankings client-side from the existing `useChoresList()` data. The Chore list already contains `schedule_type`, `schedule_value`, `last_triggered_count`, `last_triggered_at`, and the new `execution_count` field. The frontend computes:
- **Next Run**: For count-based Chores, sort by `(schedule_value - (currentParentIssueCount - last_triggered_count))` ascending; pick the lowest remaining. For time-based, sort by `(schedule_value - daysSince(last_triggered_at))` ascending.
- **Most Recently Run**: Sort by `last_triggered_at` descending, pick first non-null.
- **Most Run**: Sort by `execution_count` descending, pick highest.

**Rationale**: The Chore list is small (typically < 50 per project) and already fetched for the main grid. Computing rankings client-side avoids a dedicated backend endpoint and additional round-trips. The `currentParentIssueCount` is already available in the frontend from the board data (via `useRecentParentIssues` or a dedicated counter endpoint). All required fields exist or are being added (`execution_count`) on the Chore model.

**Alternatives Considered**:
- **Dedicated backend endpoint for Featured Rituals**: Rejected — adds a new API route for data already available on the client. The computation is trivial (three sorts on a small list). YAGNI.
- **Materialized view in database**: Rejected — the ranking changes on every page load (depends on current parent issue count and current time). A materialized view would need constant refresh, adding complexity for no benefit.

---

## R3: Inline Chore Definition Editing Architecture

**Task**: Determine how to make Chore definition fields editable inline while preserving dirty-state tracking and generating PRs on save.

**Decision**: Convert `ChoreCard` to a "view/edit" mode component. In edit mode, fields (`name`, `template_content`, `schedule_type`, `schedule_value`, `status`) render as `<input>` and `<textarea>` elements instead of read-only text. A parent-level `editState` map in `ChoresPanel` tracks original values vs. current values per Chore. The Save button calls a new `PUT /api/v1/chores/{project_id}/{chore_id}/inline-update` endpoint that accepts the updated fields, commits the changed template file via `commit_files_workflow`, and creates a PR.

**Rationale**: The spec requires (FR-005) that fields render as editable inputs/textareas, not that a separate edit page or modal is used. The view/edit mode pattern is standard for inline editing. Tracking dirty state in the parent (`ChoresPanel`) allows a single "Save All" button and a unified navigation guard. The `commit_files_workflow` is already used by `template_builder.py` for initial Chore creation — extending it to handle updates requires only passing the existing file path instead of generating a new one. Creating a dedicated endpoint (rather than reusing `PATCH`) keeps the inline update flow (which includes PR creation) separate from the simple schedule/status updates.

**Alternatives Considered**:
- **Separate edit page**: Rejected — spec explicitly says "inline" editing on the Chores page. A separate page would require navigation and lose the grid context.
- **Modal-based editing**: Rejected — spec says "fields render as editable inputs/textareas" (FR-005), implying in-place editing, not a modal overlay.
- **Reuse existing `PATCH` endpoint**: Rejected — the existing `PATCH` updates schedule/status without creating a PR. Inline editing of the template content requires PR creation, which is a different workflow. Overloading `PATCH` would create confusing behavior.

---

## R4: Unsaved Changes Navigation Guard

**Task**: Determine how to implement the "You have unsaved changes" confirmation dialog when navigating away from the Chores page.

**Decision**: Create a `useUnsavedChanges(isDirty: boolean)` custom hook that uses the browser's `beforeunload` event for hard navigations and `react-router-dom`'s `useBlocker` (or `unstable_useBlocker` in v7) for client-side route transitions. When `isDirty` is true and the user attempts to navigate, a confirmation dialog is shown. The hook is generic and reusable.

**Rationale**: The spec requires (FR-006) a confirmation dialog on navigation away with unsaved edits. The `beforeunload` event handles browser close/refresh/external navigation. React Router's blocker API handles SPA route changes. Both are needed for complete coverage. The hook is generic (takes a boolean) so it can be reused by other pages if needed. React Router v7 provides `useBlocker` which returns a blocker state that can drive a custom modal (matching the app's design system) rather than the browser's default `confirm()` dialog.

**Alternatives Considered**:
- **Browser-only `beforeunload`**: Rejected — doesn't catch SPA route transitions (clicking links within the app). The user can navigate away without warning.
- **`window.confirm()` only**: Rejected — doesn't match the app's design system. A custom modal with "Discard" / "Stay" buttons is more consistent.
- **Third-party library (e.g., `react-beforeunload`)**: Rejected — adds a dependency for 10 lines of code. YAGNI.

---

## R5: AI Enhance Toggle for Chore Template Generation

**Task**: Determine how to implement the AI Enhance OFF path where the user's exact chat input is used as the Issue Template body while the Chat Agent still generates metadata.

**Decision**: Modify the existing `chores/chat.py` to accept an `ai_enhance` parameter. When `ai_enhance=false`:
1. The system prompt changes to instruct the AI to generate ONLY metadata fields (name, about, title, labels, assignees) in the YAML front matter.
2. The user's raw input is injected as a pre-filled body section below the YAML front matter.
3. The Chat Agent is called with a modified prompt: "Generate YAML front matter metadata for a GitHub Issue Template. The body content is provided by the user and must not be modified."
4. The final template is assembled by combining AI-generated YAML front matter + user's verbatim body.

On the frontend, add the same toggle pattern used in `ChatToolbar.tsx` (Sparkles icon + ON/OFF badge) to both `AddChoreModal` and `ChoreCard` (edit mode). The toggle state is passed to the `choresApi.chat()` call.

**Rationale**: The spec requires (FR-009) that when AI Enhance is OFF, "the user's exact chat input MUST be used verbatim as the GitHub Issue Template body." The simplest approach is to separate the template into two parts: AI-generated front matter and user-provided body. The Chat Agent already knows how to generate YAML front matter (it's part of the `SYSTEM_PROMPT` in `chores/chat.py`). Restricting it to metadata-only is a prompt change, not a code change. The frontend toggle reuses the proven `ChatToolbar` pattern for consistency (FR-008 says "co-located with the flow controls similarly to the '+ Add Agent' pop-out on the Agents page").

**Alternatives Considered**:
- **Post-process AI output to strip body changes**: Rejected — fragile; the AI might interleave metadata and body content. Separating generation is cleaner.
- **Two separate AI calls (one for metadata, one for body)**: Rejected — unnecessary when one call with a restricted prompt can generate metadata only. Reduces latency and token usage.
- **Client-side template assembly without AI**: Rejected — the spec says "the Chat Agent is still invoked to generate all template metadata" (FR-009). Metadata generation must use the AI.

---

## R6: Per-Chore Agent Pipeline Selection & Resolution

**Task**: Determine how to store and resolve per-Chore Agent Pipeline configuration, including the "Auto" option.

**Decision**: Add an `agent_pipeline_id` text column to the `chores` table. This stores the ID of a saved `pipeline_configs` record, or an empty string (`""`) for "Auto". On the frontend, the `PipelineSelector` dropdown lists all saved pipelines from `usePipelinesList(projectId)` plus a hardcoded "Auto" option. At execution time (in `trigger_chore()`):
- If `agent_pipeline_id` is non-empty, use that pipeline config directly.
- If empty ("Auto"), read `project_settings.assigned_pipeline_id` for the project and use that. If no project pipeline is assigned, fall back to the default workflow orchestrator behavior (no pipeline override).

**Rationale**: The spec requires (FR-012) that "Auto" resolves at runtime. Storing just the ID (not the config) ensures the Chore always picks up the latest pipeline version. Reading `project_settings.assigned_pipeline_id` at trigger time follows the same pattern already established in spec 028 for project-level pipeline assignment. An empty string for "Auto" is consistent with how `assigned_pipeline_id` uses empty string for "no assignment" — the pattern is established.

**Alternatives Considered**:
- **Separate `chore_pipeline_assignments` table**: Rejected — overkill for a single FK. A column on the Chore record is simpler.
- **Store full pipeline config JSON on the Chore**: Rejected — goes stale if the pipeline is updated. The FK ensures freshness.
- **Enum value "auto" in the column**: Rejected — using empty string is already the established convention in `project_settings.assigned_pipeline_id`. Mixing an enum value with UUID strings in the same column is error-prone.

---

## R7: Two-Step Confirmation Modal Design

**Task**: Design the two-step confirmation UX for new Chore creation that warns the user about automatic repository commits before proceeding.

**Decision**: Implement a single `ConfirmChoreModal` component with an internal `step` state (1 or 2). Step 1 shows an informational message: "This will automatically add a Chore file to your repository's `.github/ISSUE_TEMPLATE/` directory. A Pull Request will be created and auto-merged into main." with "Cancel" and "I Understand, Continue" buttons. Step 2 shows a final confirmation: "Create this Chore? This action will create a GitHub Issue, open a PR, and merge it into main." with "Back" and "Yes, Create Chore" buttons. Both steps share the same modal overlay — only the content changes.

**Rationale**: The spec requires (FR-013) a two-step confirmation modal. A single component with step state is simpler than coordinating two separate modals (see Complexity Tracking in plan.md). The first step is informational (awareness), the second is confirmatory (action). This mirrors common patterns in destructive action UIs (e.g., GitHub's "delete repository" flow). The "Back" button on step 2 allows users to reconsider without losing context.

**Alternatives Considered**:
- **Two separate modal components**: Rejected — requires coordination logic (close first, open second, handle dismiss of either). A single modal with state is simpler.
- **Single confirmation with extra warning text**: Rejected — spec explicitly requires "two-step" (FR-013). A single step doesn't meet the requirement.
- **Inline confirmation in the form**: Rejected — the spec says "modal," implying a dialog overlay, not inline buttons.

---

## R8: Auto-Merge PR Strategy

**Task**: Determine the best approach for automatically merging the PR created for new Chore definitions.

**Decision**: After creating the PR via `commit_files_workflow`, call the GitHub merge PR API (`PUT /repos/{owner}/{repo}/pulls/{pr_number}/merge`) with merge method `squash` (keeping the commit history clean). The merge call is wrapped in a try/except:
- On success: return success status, close the tracking issue if applicable, show success toast on frontend.
- On failure (merge conflict, CI failure, branch protection): surface the error as an actionable message to the user, leave the PR open for manual resolution, and still persist the Chore record locally. The frontend shows a warning toast with a link to the open PR.

Use the existing `githubkit` client (or direct GitHub REST API via `httpx`) for the merge call, as the GraphQL `mergePullRequest` mutation is also available. Prefer the REST API for simplicity since it's a single call.

**Rationale**: The spec requires (FR-014) sequential Issue → PR → auto-merge. Using squash merge keeps the main branch clean with a single descriptive commit per Chore. Error handling is critical — the spec explicitly requires (FR-016) graceful failure handling with user notification. Persisting the Chore locally even on merge failure ensures the user's work isn't lost (they can retry or merge manually).

**Alternatives Considered**:
- **GitHub auto-merge API (enable auto-merge on PR creation)**: Rejected — requires branch protection rules with required status checks to be configured. Not all repos have this. Direct merge is more reliable.
- **GraphQL `mergePullRequest` mutation**: Viable alternative, but the REST API is simpler for a single merge call and doesn't require constructing a GraphQL document.
- **Wait for CI then merge**: Rejected — the spec says "automatically merge" (FR-014), not "wait for CI then merge." If the user wants CI gating, they should configure branch protection rules, which would cause the direct merge to fail gracefully (handled by error path).

---

## R9: Counter Display Calculation on Frontend

**Task**: Determine how to calculate and display the "remaining issues" counter on each Chore tile, given that the current parent issue count may change between page loads.

**Decision**: Add a new lightweight endpoint `GET /api/v1/chores/{project_id}/counters` that returns the current parent issue count for the project alongside each Chore's computed remaining count. The response includes `{ chores: [{ chore_id, remaining, total_threshold, issues_since_last_run }], parent_issue_count: number }`. The frontend calls this endpoint on page load (alongside the Chore list) and uses `remaining` directly for tile display.

Alternatively, if the parent issue count is already available via the board data (which it is — `useProjectBoard` fetches all items), compute it client-side: iterate board items, filter `content_type === 'issue'`, exclude sub-issues, count them, and compute `remaining = schedule_value - (parent_issue_count - last_triggered_count)` per Chore.

**Decision (final)**: Use client-side computation from board data. The parent issue count is already available via `useProjectBoard()` → `boardData.items`. Filter to parent issues (same logic as `useRecentParentIssues.ts`), count them, and compute remaining per Chore. No new endpoint needed.

**Rationale**: The board data is already fetched for the project page. Reusing it avoids an extra API call. The computation is trivial (one subtraction per Chore). The existing `useRecentParentIssues` hook already filters board items to parent issues — the same filter logic can be extracted into a shared utility.

**Alternatives Considered**:
- **New dedicated counter endpoint**: Rejected (initially considered) — adds API surface for data already on the client. YAGNI.
- **WebSocket real-time counter updates**: Rejected — over-engineered for a counter that changes when issues are created (which happens infrequently). Page refresh is sufficient per spec ("updating in real time or on page refresh").

---

## R10: Inline Edit PR Title and Description Generation

**Task**: Determine how to generate meaningful PR titles and descriptions when a user saves inline edits to a Chore definition.

**Decision**: Generate the PR title as `chore: update {chore_name}` and the description as a markdown summary listing the changed fields. The backend's inline update endpoint receives the full updated Chore data and the original data (or just the changed fields). It computes a diff summary:
- "Updated name from '{old}' to '{new}'"
- "Updated template content"
- "Changed schedule from 'Every 5 issues' to 'Every 10 issues'"

This is assembled into the PR description. The branch name follows the existing pattern: `chore/update-{slug}-{timestamp}`.

**Rationale**: Meaningful PR descriptions help reviewers understand what changed without reading the full diff. The existing `commit_files_workflow` already accepts `pr_title` and `pr_body` parameters — this decision just defines how to compute them. Using a structured diff summary (rather than the raw content) keeps descriptions concise. The branch naming pattern matches the existing `chore/create-{slug}` pattern from `template_builder.py`.

**Alternatives Considered**:
- **AI-generated PR description**: Rejected — adds latency and token cost for a simple field-level diff. The structured format is sufficient and deterministic.
- **No description, just title**: Rejected — a bare title doesn't help reviewers. The diff summary is low-cost to generate.

---

## R11: Handling Deleted Pipeline References

**Task**: Determine how to handle the case where a saved Agent Pipeline referenced by a Chore is deleted.

**Decision**: On the frontend, when rendering the `PipelineSelector`, query the pipeline list and check if the Chore's `agent_pipeline_id` exists in the list. If not, show a warning indicator ("Pipeline no longer available") and auto-select "Auto" in the dropdown. On the backend, during `trigger_chore()`, if the `agent_pipeline_id` is non-empty but the pipeline doesn't exist in `pipeline_configs`, log a warning, fall back to "Auto" behavior, and optionally clear the stale reference on the Chore record.

**Rationale**: The spec requires (FR-017) fallback to "Auto" and user notification. Checking on the frontend provides immediate visual feedback. Checking on the backend ensures correct behavior even if the frontend check is bypassed (e.g., cron trigger evaluation). Clearing the stale reference is optional but prevents repeated warnings.

**Alternatives Considered**:
- **Foreign key constraint with CASCADE delete**: Rejected — CASCADE would silently null out the field without notification. The spec requires explicit notification.
- **Prevent pipeline deletion if referenced by Chores**: Rejected — blocks legitimate cleanup. Graceful fallback is more user-friendly.

---

## R12: Chore Edit Conflict Detection

**Task**: Determine how to handle the edge case where a Chore's underlying file has been modified by another user since the page loaded.

**Decision**: On the inline edit save endpoint, before committing changes, fetch the current file SHA from the repository (via GitHub API `GET /repos/{owner}/{repo}/contents/{path}`). Compare it with the SHA stored when the page loaded (passed as `expected_sha` in the request). If they differ, return a `409 Conflict` response with the updated content, allowing the user to resolve the conflict manually. The frontend shows a conflict warning modal with the option to overwrite or reload.

**Rationale**: This is a standard optimistic concurrency check (compare-and-swap on the file SHA). The GitHub API returns the file SHA on content reads, and the `commit_files_workflow` already uses the SHA for commits (to avoid clobbering changes). Passing `expected_sha` from the frontend makes the check explicit. A `409 Conflict` response follows HTTP semantics for concurrency conflicts.

**Alternatives Considered**:
- **Always overwrite**: Rejected — silently loses other users' changes. The spec mentions this as an edge case that should be handled.
- **Three-way merge**: Rejected — overly complex for template files. The user can manually resolve by reloading and re-applying their changes.
- **Lock file while editing**: Rejected — distributed locks are complex and can leave orphaned locks. Optimistic concurrency is simpler and well-established.
