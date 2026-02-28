# Data Model: Attach Parent Branch to GitHub Issue Upon Branch Creation

**Feature**: 014-attach-parent-branch-issue | **Date**: 2026-02-28

> This feature does not introduce new application data entities stored in a database. The "entities" below describe the conceptual data flowing through the GitHub Actions workflow.

## Entity: Branch Creation Event

**Purpose**: The trigger event received by the GitHub Actions workflow when a new branch is created.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| ref | string | The full branch name (e.g., `042-fix-navigation`, `feature/issue-15-add-search`) | Required, non-empty |
| ref_type | string | The type of Git ref created | Must be `branch` (tags are filtered out) |
| repository | string | Full repository name (`owner/repo`) | Required |
| repository_fork | boolean | Whether the repository is a fork | Required; workflow skips if `true` |
| actor | string | GitHub username who created the branch | Required |

**Validation Rules**:
- `ref_type` must equal `branch`; tag creation events are ignored
- `repository_fork` must be `false`; fork events are skipped (FR-010)

---

## Entity: Parsed Issue Reference

**Purpose**: The issue number extracted from the branch name after regex parsing.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| issue_number | integer | The extracted GitHub Issue number | Positive integer, ≥ 1 |
| branch_name | string | The original branch name | Required, non-empty |
| matched | boolean | Whether a valid issue number was found | Required |

**Derivation Rules**:
- Strip any path prefix (e.g., `feature/`, `bugfix/`) to get the base name
- Strip optional `issue-` prefix from the base name
- Extract the leading numeric segment and strip leading zeros
- If no numeric segment is found, `matched = false` (FR-005: log warning, no action)
- If multiple numbers exist (e.g., `42-fix-issue-15`), use the first number (FR-009)

**Examples**:
| Branch Name | Parsed issue_number | matched |
|---|---|---|
| `042-fix-navigation` | 42 | true |
| `feature/issue-15-add-search` | 15 | true |
| `100-implement-dashboard` | 100 | true |
| `007-feature` | 7 | true |
| `hotfix-urgent` | — | false |
| `42-fix-issue-15` | 42 | true |

---

## Entity: Issue State

**Purpose**: The state of the target GitHub Issue, fetched via the GitHub API before posting a comment.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| issue_number | integer | The GitHub Issue number | Positive integer |
| exists | boolean | Whether the issue exists in the repository | Required |
| state | enum | Issue state: `open`, `closed`, or `not_found` | Required |
| has_existing_link | boolean | Whether the branch is already linked (idempotency check) | Required |

**Validation Rules**:
- If `exists = false`: surface warning, do not attempt attachment (FR-006)
- If `state = closed`: surface warning, still proceed with attachment (FR-007)
- If `has_existing_link = true`: skip attachment, no duplicate created (FR-004)

---

## Entity: Branch Attachment Comment

**Purpose**: The comment posted on the GitHub Issue to link the branch.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| issue_number | integer | Target GitHub Issue number | Required, positive integer |
| branch_name | string | The branch being linked | Required, non-empty |
| marker | string | Hidden HTML comment for idempotency detection | Format: `<!-- branch-link: {branch_name} -->` |
| body | string | The full comment body (visible text + marker) | Required, non-empty |
| created_at | datetime | Timestamp when the comment was posted | Set by GitHub API |

**Comment Body Template**:
```
<!-- branch-link: {branch_name} -->
🔗 **Branch linked:** `{branch_name}`

This branch was automatically linked to this issue by the [branch-issue-link]({workflow_url}) workflow.
```

**Validation Rules**:
- The `marker` must be unique per branch name to enable idempotency checks
- The comment body must contain the marker as the first line
- The visible text must clearly identify the linked branch

---

## Relationships

```
Branch Creation Event 1──1 Parsed Issue Reference  (event triggers parsing)
Parsed Issue Reference 1──0..1 Issue State          (only if matched = true)
Issue State 1──0..1 Branch Attachment Comment       (only if exists = true AND has_existing_link = false)
```

## State Transitions

### Workflow Lifecycle
```
create event received
  → [filter: ref_type == branch AND fork == false]
  → parse branch name for issue number
  → [no match?] → log warning → exit success
  → [match found] → fetch issue state
  → [issue not found?] → log warning → exit success
  → [issue closed?] → log warning → continue
  → check for existing branch link comment
  → [already linked?] → log info (idempotent skip) → exit success
  → post branch attachment comment → exit success
```

### Retry Lifecycle (transient failures only)
```
API call fails (5xx, timeout, rate limit)
  → wait 2^attempt seconds (exponential backoff)
  → retry (up to 3 attempts)
  → [all retries exhausted] → log error warning → exit success (do not block)
```
