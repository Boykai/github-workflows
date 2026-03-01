# Data Model: Add 'Clean Up' Button to Delete Stale Branches and PRs

**Feature**: 015-stale-cleanup-button  
**Date**: 2026-03-01  
**Depends on**: research.md (R1, R2, R6)

## Entities

### Branch

Represents a git branch in the repository as evaluated during the preflight phase.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | NOT NULL | Branch name (e.g., `main`, `015-stale-cleanup-button`) |
| `is_protected` | boolean | NOT NULL | Whether this branch is unconditionally protected (`main`) |
| `linked_issue_number` | number \| null | — | Issue number this branch is linked to (if any) |
| `linked_issue_title` | string \| null | — | Title of the linked issue (for display in modal) |
| `linking_method` | string \| null | — | How the link was determined: `naming_convention`, `pr_reference`, `timeline_event` |
| `eligible_for_deletion` | boolean | NOT NULL | Whether this branch is scheduled for deletion |
| `preservation_reason` | string \| null | — | Human-readable reason for preservation (e.g., "Main branch", "Linked to open issue #42") |

### Pull Request

Represents an open pull request in the repository as evaluated during the preflight phase.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | number | NOT NULL | PR number |
| `title` | string | NOT NULL | PR title |
| `head_branch` | string | NOT NULL | Source branch name |
| `referenced_issues` | number[] | — | Issue numbers referenced in PR body or timeline |
| `eligible_for_deletion` | boolean | NOT NULL | Whether this PR is scheduled for closure |
| `preservation_reason` | string \| null | — | Human-readable reason for preservation |

### Open Project Board Issue

Represents an open issue on the associated GitHub Projects v2 board, used as the preservation criteria.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `number` | number | NOT NULL | Issue number |
| `title` | string | NOT NULL | Issue title |
| `linked_branches` | string[] | — | Branch names linked to this issue |
| `linked_prs` | number[] | — | PR numbers linked to this issue |

### Cleanup Operation (Audit Log)

Represents a single execution of the cleanup process, persisted in SQLite.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PRIMARY KEY | Unique identifier for this operation |
| `github_user_id` | TEXT | NOT NULL | Authenticated user who initiated the cleanup |
| `owner` | TEXT | NOT NULL | Repository owner |
| `repo` | TEXT | NOT NULL | Repository name |
| `project_id` | TEXT | NOT NULL | Project board ID used for issue resolution |
| `started_at` | TEXT | NOT NULL | ISO 8601 timestamp of operation start |
| `completed_at` | TEXT | NULL | ISO 8601 timestamp of operation completion |
| `status` | TEXT | NOT NULL, DEFAULT 'in_progress' | `in_progress`, `completed`, `failed` |
| `branches_deleted` | INTEGER | NOT NULL, DEFAULT 0 | Count of branches successfully deleted |
| `branches_preserved` | INTEGER | NOT NULL, DEFAULT 0 | Count of branches preserved |
| `prs_closed` | INTEGER | NOT NULL, DEFAULT 0 | Count of PRs successfully closed |
| `prs_preserved` | INTEGER | NOT NULL, DEFAULT 0 | Count of PRs preserved |
| `errors_count` | INTEGER | NOT NULL, DEFAULT 0 | Count of failed operations |
| `details` | TEXT | NOT NULL, DEFAULT '{}' | JSON blob with per-item results |

### Relationships

```
GitHub Repository
  ├── 1:N ── Branch (fetched via REST API)
  ├── 1:N ── Pull Request (fetched via REST API)
  └── 1:1 ── Project Board
               └── 1:N ── Open Issue (fetched via GraphQL)
                            ├── linked to 0:N Branches
                            └── linked to 0:N Pull Requests

Cleanup Operation (audit log)
  └── N:1 ── User (github_user_id)
```

### Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `idx_cleanup_audit_user` | `github_user_id` | Fast lookup of cleanup history per user |
| `idx_cleanup_audit_repo` | `owner, repo` | Fast lookup of cleanup history per repository |

### Validation Rules

| Rule | Field(s) | Enforcement |
|------|----------|-------------|
| Main branch always protected | `name` | Hard-coded check in preflight logic; never included in deletion list |
| Linked to open project board issue | `linked_issue_number` | Cross-referenced during preflight via 3-layer strategy (R1) |
| Valid repository context | `owner`, `repo` | Required path parameters, validated at API layer |
| User has push access | — | Permission check during preflight (R5) |

### State Transitions

Cleanup operation lifecycle:

```
[Idle] → Click "Clean Up" → [Preflight Loading]
[Preflight Loading] → API returns → [Confirming] (modal shown)
[Confirming] → User clicks "Cancel" → [Idle]
[Confirming] → User clicks "Confirm" → [Executing] (progress shown)
[Executing] → All operations complete → [Summary] (report shown)
[Executing] → Fatal error → [Summary] (with error details)
[Summary] → User dismisses → [Idle]
```

Audit log status transitions:

```
[Not Exists] → POST /cleanup/execute → [in_progress]
[in_progress] → All operations complete → [completed]
[in_progress] → Fatal error → [failed]
```

## Migration SQL

File: `backend/src/migrations/008_cleanup_audit_logs.sql`

```sql
-- Migration 008: Add cleanup audit logs table for branch/PR cleanup operations

CREATE TABLE IF NOT EXISTS cleanup_audit_logs (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    project_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'in_progress',
    branches_deleted INTEGER NOT NULL DEFAULT 0,
    branches_preserved INTEGER NOT NULL DEFAULT 0,
    prs_closed INTEGER NOT NULL DEFAULT 0,
    prs_preserved INTEGER NOT NULL DEFAULT 0,
    errors_count INTEGER NOT NULL DEFAULT 0,
    details TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_cleanup_audit_user ON cleanup_audit_logs(github_user_id);
CREATE INDEX IF NOT EXISTS idx_cleanup_audit_repo ON cleanup_audit_logs(owner, repo);
```

## Backend Models (Pydantic)

### Request Models

```python
class CleanupPreflightRequest(BaseModel):
    """Request body for the preflight check."""
    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    project_id: str = Field(min_length=1)


class CleanupExecuteRequest(BaseModel):
    """Request body to execute the cleanup operation."""
    owner: str = Field(min_length=1)
    repo: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    branches_to_delete: list[str]
    prs_to_close: list[int]
```

### Response Models

```python
class BranchInfo(BaseModel):
    """Branch details for preflight response."""
    name: str
    eligible_for_deletion: bool
    linked_issue_number: int | None = None
    linked_issue_title: str | None = None
    linking_method: str | None = None
    preservation_reason: str | None = None


class PullRequestInfo(BaseModel):
    """PR details for preflight response."""
    number: int
    title: str
    head_branch: str
    referenced_issues: list[int] = []
    eligible_for_deletion: bool
    preservation_reason: str | None = None


class CleanupPreflightResponse(BaseModel):
    """Response from preflight endpoint."""
    branches_to_delete: list[BranchInfo]
    branches_to_preserve: list[BranchInfo]
    prs_to_close: list[PullRequestInfo]
    prs_to_preserve: list[PullRequestInfo]
    open_issues_on_board: int
    has_permission: bool
    permission_error: str | None = None


class CleanupItemResult(BaseModel):
    """Result of a single deletion/close operation."""
    item_type: str  # "branch" or "pr"
    identifier: str  # branch name or PR number
    action: str  # "deleted", "closed", "preserved", "failed"
    reason: str | None = None
    error: str | None = None


class CleanupExecuteResponse(BaseModel):
    """Final summary response from execute endpoint."""
    operation_id: str
    branches_deleted: int
    branches_preserved: int
    prs_closed: int
    prs_preserved: int
    errors: list[CleanupItemResult]
    results: list[CleanupItemResult]
```

### Database Row Model

```python
class CleanupAuditLogRow(BaseModel):
    """Represents a cleanup_audit_logs database row."""
    id: str
    github_user_id: str
    owner: str
    repo: str
    project_id: str
    started_at: str
    completed_at: str | None
    status: str
    branches_deleted: int
    branches_preserved: int
    prs_closed: int
    prs_preserved: int
    errors_count: int
    details: str  # JSON string
```

## Frontend Types

```typescript
export interface BranchInfo {
  name: string;
  eligible_for_deletion: boolean;
  linked_issue_number: number | null;
  linked_issue_title: string | null;
  linking_method: string | null;
  preservation_reason: string | null;
}

export interface PullRequestInfo {
  number: number;
  title: string;
  head_branch: string;
  referenced_issues: number[];
  eligible_for_deletion: boolean;
  preservation_reason: string | null;
}

export interface CleanupPreflightResponse {
  branches_to_delete: BranchInfo[];
  branches_to_preserve: BranchInfo[];
  prs_to_close: PullRequestInfo[];
  prs_to_preserve: PullRequestInfo[];
  open_issues_on_board: number;
  has_permission: boolean;
  permission_error: string | null;
}

export interface CleanupItemResult {
  item_type: 'branch' | 'pr';
  identifier: string;
  action: 'deleted' | 'closed' | 'preserved' | 'failed';
  reason: string | null;
  error: string | null;
}

export interface CleanupExecuteResponse {
  operation_id: string;
  branches_deleted: number;
  branches_preserved: number;
  prs_closed: number;
  prs_preserved: number;
  errors: CleanupItemResult[];
  results: CleanupItemResult[];
}

export interface CleanupExecuteRequest {
  owner: string;
  repo: string;
  project_id: string;
  branches_to_delete: string[];
  prs_to_close: number[];
}
```
