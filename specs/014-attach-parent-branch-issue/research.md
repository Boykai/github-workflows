# Research: Attach Parent Branch to GitHub Issue Upon Branch Creation

**Feature**: 014-attach-parent-branch-issue | **Date**: 2026-02-28

## Research Task 1: GitHub Actions `create` Event for Branch Detection

### Decision
Use the GitHub Actions `create` event with `ref_type == 'branch'` filter to detect new branch creation in real time. This is the standard, first-party mechanism for reacting to branch creation within a repository.

### Rationale
- The `create` event fires whenever a Git ref (branch or tag) is created. Filtering on `github.event.ref_type == 'branch'` ensures only branch creations are processed.
- This is a native GitHub Actions trigger — no external webhooks, third-party services, or additional infrastructure required.
- The event provides `github.event.ref` (the branch name), `github.repository`, and `github.actor` as context, which is all the information needed to parse the issue number and make API calls.
- Near real-time: workflow runs are typically queued within seconds of the event.

### Alternatives Considered
- **GitHub Webhooks (external)**: Requires hosting an HTTP endpoint, managing secrets, and handling retries manually. Over-engineered for this use case since GitHub Actions is already available.
- **GitHub Apps**: More powerful but requires app registration, installation, and hosting. Unnecessary complexity for a single-repo workflow.
- **Polling-based approach**: Periodically checking for new branches. Introduces latency and wastes API quota. Rejected.

---

## Research Task 2: Branch Name Parsing Strategy for Issue Number Extraction

### Decision
Use a regex-based extraction strategy that prioritizes the **leading numeric segment** of the branch name (after stripping any path prefix like `feature/`). The primary pattern is `/^(?:.*\/)?(?:issue-)?0*(\d+)/` which handles:
- `042-fix-navigation` → Issue #42
- `feature/issue-15-add-search` → Issue #15
- `100-implement-dashboard` → Issue #100
- `007-feature` → Issue #7

### Rationale
- The spec explicitly requires (FR-009) that the leading numeric segment be used when multiple numbers appear in the branch name (e.g., `42-fix-issue-15` → Issue #42).
- Leading zeros must be stripped (edge case in spec: `007-feature` → Issue #7).
- The existing speckit workflow already uses `NNN-feature-name` format (constitution: Branch and Directory Naming), so this pattern is consistent with existing conventions.
- The regex is implemented in bash using `sed` and shell parameter expansion, avoiding external dependencies.

### Alternatives Considered
- **Strict `NNN-` only**: Would miss `feature/issue-NNN-description` patterns required by the spec (FR-002). Too restrictive.
- **Multiple regex patterns with priority**: More complex with no clear benefit — a single flexible pattern covers all documented conventions.
- **Configuration file for custom patterns**: YAGNI — the spec does not require user-configurable patterns. Can be added later if needed.

---

## Research Task 3: Branch-to-Issue Attachment Mechanism

### Decision
Use **GitHub Issue comments** via the REST API (`POST /repos/{owner}/{repo}/issues/{issue_number}/comments`) as the attachment mechanism. The comment includes a standardized marker to enable idempotency checks.

### Rationale
- Issue comments are universally available across all GitHub plan tiers (Free, Team, Enterprise).
- Comments are visible, searchable, and provide an audit trail.
- A unique marker string (e.g., `<!-- branch-link: {branch_name} -->`) embedded in the comment body enables idempotency: before posting, the workflow checks existing comments for this marker and skips if found (FR-004).
- The `gh` CLI (`gh issue comment`) provides a convenient wrapper and is pre-installed on GitHub Actions runners.

### Alternatives Considered
- **GitHub GraphQL `linkedBranches` API**: The most elegant solution, but requires GitHub Enterprise or specific plan tier features. Not universally available. Would create a formal branch-issue link in the UI sidebar.
- **Issue labels**: Too noisy and not designed for branch tracking. Labels have character limits and would pollute the label namespace.
- **Issue body editing**: Risky — modifying the issue body could cause conflicts with other automation or manual edits.
- **GitHub Projects metadata**: Requires Projects V2 setup, adds complexity, and is not available in all repositories.

---

## Research Task 4: Idempotency Implementation

### Decision
Before posting a comment, list existing issue comments (via `gh issue view` or `GET /repos/{owner}/{repo}/issues/{issue_number}/comments`) and search for the HTML comment marker `<!-- branch-link: {branch_name} -->`. If found, skip posting. This ensures the operation is idempotent.

### Rationale
- HTML comments are invisible to users but machine-readable, making them ideal as idempotency markers.
- The `gh` CLI supports `gh issue view {number} --json comments` to retrieve all comments efficiently.
- Using the branch name as the marker key (rather than a UUID or timestamp) means that even if a branch is deleted and recreated, the same marker is found and no duplicate is created — matching the spec requirement (User Story 2, Scenario 2: "the issue shows exactly one active branch reference").
- The check-then-act pattern is safe here because GitHub Actions workflows are serialized per repository (with concurrency controls), and the window for race conditions is negligible.

### Alternatives Considered
- **GitHub API search for existing comments**: The search API has rate limits and eventual consistency. Listing comments on a specific issue is more reliable and direct.
- **External state store**: Storing which branches have been linked in a file, database, or artifact. Over-engineered — the comments themselves are the source of truth.
- **No idempotency check (post always)**: Would create duplicates on workflow re-runs or retries. Violates FR-004.

---

## Research Task 5: Error Handling and Retry Strategy

### Decision
Use GitHub Actions' built-in retry mechanisms via `continue-on-error` for non-critical warnings, and implement a simple retry loop (up to 3 attempts with exponential backoff) for transient API failures using shell scripting.

### Rationale
- FR-008 requires retry logic for transient failures (rate limits, network timeouts).
- The `gh` CLI returns appropriate exit codes for failures, enabling simple retry logic in bash.
- Exponential backoff (2s, 4s, 8s) prevents hammering the API during rate limiting.
- For non-existent issues (404) or closed issues, the workflow should warn but not retry — these are permanent conditions, not transient failures.
- The workflow should always exit with code 0 (success) to avoid blocking other CI workflows triggered by the same event. Warnings are surfaced via `echo "::warning::..."` annotations.

### Alternatives Considered
- **GitHub Actions retry action (`nick-fields/retry`)**: Adds a third-party dependency for something achievable in 5 lines of bash. Violates simplicity principle.
- **No retry**: Would miss branch attachments during transient GitHub outages. Violates FR-008.
- **Webhook-based retry with queue**: Requires external infrastructure. Massive over-engineering.

---

## Research Task 6: Authentication and Permissions

### Decision
Use the built-in `GITHUB_TOKEN` (via `${{ secrets.GITHUB_TOKEN }}`) with `issues: write` permission. This is the standard, zero-configuration approach for GitHub Actions workflows that need to interact with issues in the same repository.

### Rationale
- `GITHUB_TOKEN` is automatically provisioned for every workflow run — no secret management needed.
- The `issues: write` permission is the minimum required to post comments on issues.
- `contents: read` is needed to access the repository context (already default).
- The workflow explicitly declares minimal permissions following the principle of least privilege, consistent with the existing `ci.yml` which also uses scoped permissions.

### Alternatives Considered
- **Personal Access Token (PAT)**: Requires manual secret creation, rotation, and grants broader access than needed. Only necessary for cross-repository operations, which are out of scope.
- **GitHub App token**: More secure than PATs but requires app registration and installation. Over-engineered for a single workflow in a single repository.
- **Fine-grained PAT**: Better than classic PATs but still requires manual management. `GITHUB_TOKEN` is simpler and sufficient.

---

## Research Task 7: Fork Handling

### Decision
Add a condition `if: github.event.repository.fork == false` to the workflow job to skip execution for forked repositories. This satisfies FR-010.

### Rationale
- The `create` event fires for branches in forks as well as the main repository.
- Forked repositories should not trigger the parent repo's issue linking workflow.
- The `github.event.repository.fork` context variable is `true` when the event comes from a fork.
- This is a simple, declarative check at the job level — no custom logic needed.

### Alternatives Considered
- **Checking `github.repository` against a hardcoded value**: Fragile and not portable across repositories. The fork flag is the standard approach.
- **Ignoring forks entirely (no check)**: Risky — could cause unexpected behavior if the workflow is somehow triggered in a fork context.

---

## Research Task 8: Workflow Concurrency and Race Conditions

### Decision
Use GitHub Actions `concurrency` with `group: branch-issue-link-${{ github.event.ref }}` and `cancel-in-progress: true` to prevent duplicate workflow runs for the same branch.

### Rationale
- If a branch is rapidly deleted and recreated, multiple `create` events could fire in quick succession.
- The concurrency group keyed on the branch ref ensures only the latest run completes, preventing wasted API calls.
- `cancel-in-progress: true` cancels any in-flight run for the same branch, ensuring only one attachment attempt succeeds.
- Combined with the idempotency check (Research Task 4), this provides defense in depth against duplicates.

### Alternatives Considered
- **No concurrency control**: Relies entirely on idempotency checks. Works but wastes runner minutes on redundant runs.
- **Global concurrency group**: Would serialize all branch creation events across the entire repository. Too restrictive — different branches should be processed in parallel.
