# Data Model: Bug Bash — Full Codebase Review & Fix

## Overview

This bug bash does not modify database schema or introduce new persistent entities. The data model describes the audit-specific entities used to track, document, and report findings throughout the review process. These entities exist as structured comments in code and as rows in the summary report — not as database tables.

## Entities

### 1. Finding

**Type**: Audit tracking entity (documented in summary report)
**Purpose**: Represents a single identified issue in the codebase.

| Attribute | Type | Description |
|-----------|------|-------------|
| `file_path` | `string` | Relative path from repo root (e.g., `backend/src/api/auth.py`) |
| `line_numbers` | `string` | Line range or specific line (e.g., `42-45` or `42`) |
| `category` | `enum` | One of: `Security`, `Runtime`, `Logic`, `Test Quality`, `Code Quality` |
| `severity` | `enum` | Priority indicator: 🔴 (P1), 🟠 (P1), 🟡 (P2), 🔵 (P2), ⚪ (P3) |
| `description` | `string` | Brief description of the identified issue |
| `status` | `enum` | `✅ Fixed` or `⚠️ Flagged` |

**Validation rules**:
- `file_path` must be a valid path to an existing file in the repository
- `category` must map to one of the five defined audit categories
- `severity` is determined by category (Security/Runtime → P1, Logic/Test → P2, Quality → P3)
- Every Finding must have a status — no "unresolved" findings allowed at completion

### 2. Fix

**Type**: Code change entity (realized as a git commit)
**Purpose**: Represents a minimal code change that resolves a confirmed Finding.

| Attribute | Type | Description |
|-----------|------|-------------|
| `finding_ref` | `Finding` | The Finding this Fix resolves |
| `commit_sha` | `string` | Git commit hash containing the fix |
| `commit_message` | `string` | Descriptive message: what/why/how |
| `changed_files` | `list[string]` | Files modified by this fix |
| `regression_tests` | `list[string]` | Test file(s) and function(s) added |

**Validation rules**:
- Each Fix must reference exactly one Finding
- Each Fix must include at least one regression test (`len(regression_tests) >= 1`)
- The commit must contain only the fix and its regression test — no unrelated changes
- The commit message must explain: what was fixed, why it was a bug, how it was resolved
- All existing tests must continue to pass after applying the Fix

**State transitions**:
```
Finding (identified) → Fix (applied) → Verified (tests pass)
```

### 3. Flag

**Type**: Inline code annotation (realized as a `TODO(bug-bash)` comment)
**Purpose**: Marks an ambiguous Finding that requires human judgment to resolve.

| Attribute | Type | Description |
|-----------|------|-------------|
| `finding_ref` | `Finding` | The Finding this Flag documents |
| `location` | `string` | File and line where the comment is placed |
| `issue_description` | `string` | What the potential issue is |
| `options` | `list[string]` | Available resolution approaches |
| `rationale` | `string` | Why a human decision is needed |

**Validation rules**:
- Each Flag must be placed at the exact code location of the issue
- The comment must follow the format: `# TODO(bug-bash): <Category> — <Description>`
- Options and rationale must be included on subsequent comment lines
- No code changes accompany a Flag — only the comment is added

**Comment format**:
```python
# TODO(bug-bash): <Category> — <Brief description>
# Options: (a) <option 1>  (b) <option 2>
# Needs human decision because: <rationale>
```

### 4. Summary Report

**Type**: Deliverable document (realized as a section in the PR description or a separate markdown file)
**Purpose**: Consolidated listing of all Findings with their resolution status.

| Attribute | Type | Description |
|-----------|------|-------------|
| `findings` | `list[Finding]` | All identified issues |
| `category_counts` | `dict[str, int]` | Count of findings per category |
| `fixed_count` | `int` | Number of findings with `✅ Fixed` status |
| `flagged_count` | `int` | Number of findings with `⚠️ Flagged` status |
| `test_suite_status` | `enum` | `PASS` or `FAIL` — full pytest + vitest result |
| `lint_status` | `enum` | `PASS` or `FAIL` — Ruff + ESLint result |

**Validation rules**:
- Every Fix and Flag must have a corresponding entry in the Summary Report
- Every entry in the Summary Report must have a corresponding Fix or Flag in the codebase
- `test_suite_status` must be `PASS` before the bug bash is considered complete
- Category counts must match the actual number of findings per category

## Relationships

```
Finding 1──1 Fix    (confirmed bugs: one Fix per Finding)
Finding 1──1 Flag   (ambiguous issues: one Flag per Finding)
Finding *──1 Summary Report (all Findings appear in exactly one Summary)
Fix     1──* Regression Test (each Fix has ≥1 regression test)
```

## Non-Entities (Audit Infrastructure)

### Audit Checklist

**Type**: Process tracking artifact (not persisted)
**Purpose**: Tracks which files have been audited and in which categories.

Each file in the repository is tracked against all five categories:
```
file_path → { security: ✅/❌, runtime: ✅/❌, logic: ✅/❌, test_quality: ✅/❌, code_quality: ✅/❌ }
```

### Test Suite State

**Type**: Validation checkpoint (not persisted)
**Purpose**: Confirms all tests pass after each Fix is applied.

```
After each Fix:
  1. Run `cd backend && pytest -v` → must exit 0
  2. Run `cd frontend && npm test` → must exit 0
  3. Run `cd backend && ruff check src tests` → must exit 0
  4. Run `cd frontend && npm run lint` → must exit 0
```
