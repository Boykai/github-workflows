# Workflow Contract: Branch-Issue Link

**Feature**: 014-attach-parent-branch-issue | **Date**: 2026-02-28

> This feature does not introduce REST or GraphQL API endpoints. Instead, it introduces a GitHub Actions workflow. This document defines the workflow contract: trigger, inputs, outputs, and behavior.

## Workflow: `branch-issue-link.yml`

**Location**: `.github/workflows/branch-issue-link.yml`

### Trigger

| Property | Value |
|----------|-------|
| Event | `create` |
| Filter | `github.event.ref_type == 'branch'` |
| Fork filter | `github.event.repository.fork == false` |

### Permissions

| Scope | Level | Reason |
|-------|-------|--------|
| `issues` | `write` | Post comments on issues |
| `contents` | `read` | Access repository context |

### Concurrency

| Property | Value |
|----------|-------|
| Group | `branch-issue-link-${{ github.event.ref }}` |
| Cancel in-progress | `true` |

### Environment Variables / Inputs

| Variable | Source | Description |
|----------|--------|-------------|
| `BRANCH_NAME` | `${{ github.event.ref }}` | The newly created branch name |
| `GH_TOKEN` | `${{ secrets.GITHUB_TOKEN }}` | Authentication token for GitHub CLI (`gh`) |
| `GITHUB_REPOSITORY` | Built-in | `owner/repo` format |

### Workflow Steps

#### Step 1: Parse Branch Name

**Input**: `BRANCH_NAME`
**Output**: `ISSUE_NUMBER` (or empty if no match)

| Scenario | Branch Name | Extracted Issue # | Action |
|----------|-------------|-------------------|--------|
| Standard prefix | `042-fix-navigation` | `42` | Continue |
| Path prefix with issue keyword | `feature/issue-15-add-search` | `15` | Continue |
| Simple numeric prefix | `100-implement-dashboard` | `100` | Continue |
| Leading zeros | `007-feature` | `7` | Continue |
| No issue number | `hotfix-urgent` | — | Warn + exit |
| Multiple numbers (use first) | `42-fix-issue-15` | `42` | Continue |

**Regex logic** (bash):
```bash
# Strip path prefix (feature/, bugfix/, etc.)
base_name="${BRANCH_NAME##*/}"
# Try to match: optional "issue-" prefix followed by digits
if [[ "$base_name" =~ ^(issue-)?0*([0-9]+) ]]; then
  ISSUE_NUMBER="${BASH_REMATCH[2]}"
fi
```

#### Step 2: Check Issue Existence

**Input**: `ISSUE_NUMBER`
**Output**: Issue state (`open`, `closed`, `not_found`)

| API Call | Method |
|----------|--------|
| Check issue | `gh issue view $ISSUE_NUMBER --json state,number` |

| Scenario | Response | Action |
|----------|----------|--------|
| Issue exists and is open | `{"state": "OPEN"}` | Continue to Step 3 |
| Issue exists but is closed | `{"state": "CLOSED"}` | Warn (issue is closed), continue to Step 3 |
| Issue does not exist | Exit code non-zero | Warn (issue not found), exit success |

#### Step 3: Check Idempotency

**Input**: `ISSUE_NUMBER`, `BRANCH_NAME`
**Output**: `ALREADY_LINKED` (boolean)

| API Call | Method |
|----------|--------|
| List issue comments | `gh issue view $ISSUE_NUMBER --json comments` |
| Search for marker | grep for `<!-- branch-link: {BRANCH_NAME} -->` |

| Scenario | Action |
|----------|--------|
| Marker found | Log info (already linked), exit success |
| Marker not found | Continue to Step 4 |

#### Step 4: Post Branch Attachment Comment

**Input**: `ISSUE_NUMBER`, `BRANCH_NAME`
**Output**: Comment posted on the issue

| API Call | Method |
|----------|--------|
| Post comment | `gh issue comment $ISSUE_NUMBER --body "$COMMENT_BODY"` |

**Comment body**:
```markdown
<!-- branch-link: {BRANCH_NAME} -->
🔗 **Branch linked:** `{BRANCH_NAME}`

This branch was automatically linked to this issue by the [branch-issue-link]({RUN_URL}) workflow.
```

### Error Handling

| Error Type | HTTP Status / Exit Code | Action |
|-----------|-------------------------|--------|
| Issue not found | 404 / non-zero exit | `::warning::` annotation, exit 0 |
| Issue closed | 200 (state=CLOSED) | `::warning::` annotation, continue |
| API rate limit | 403 / 429 | Retry with exponential backoff (max 3 attempts) |
| Network timeout | Non-zero exit | Retry with exponential backoff (max 3 attempts) |
| All retries exhausted | — | `::warning::` annotation, exit 0 |
| No issue number in branch | — | `::notice::` annotation, exit 0 |

### Exit Codes

The workflow always exits with code 0 to avoid blocking other workflows or branch creation. All failures are surfaced as GitHub Actions annotations (`::warning::` or `::notice::`).

### Success Criteria Mapping

| Success Criterion | How Verified |
|-------------------|-------------|
| SC-001: Auto-update within 2 min | Workflow triggers on `create` event; typical execution < 30 seconds |
| SC-002: Zero duplicates | Idempotency check in Step 3 + concurrency group |
| SC-003: Warning for unrecognized branches | Step 1 outputs `::notice::` when no issue number found |
| SC-004: Warning for non-existent/closed issues | Step 2 outputs `::warning::` for these cases |
| SC-005: Zero manual effort | Entire workflow is automatic; no developer action required |
| SC-006: Retry for transient failures | Exponential backoff retry loop (max 3 attempts) |
