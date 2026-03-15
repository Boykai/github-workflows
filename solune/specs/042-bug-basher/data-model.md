# Data Model: Bug Basher — Full Codebase Review & Fix

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Status**: Complete

## Overview

This feature is a code review process, not a runtime application feature. It does not introduce persistent database entities or API endpoints. The entities below describe the conceptual data structures used to organize, track, and report the bug bash results — stored as inline code comments, commit messages, test files, and a markdown summary table.

## Entities

### 1. BugReportEntry

**Description**: A single discovered bug in the codebase. Each entry represents one discrete issue found during the review, tracked from discovery through resolution. Maps directly to the spec's "Bug Report Entry" key entity and one row in the final summary table (FR-013).

| Field | Type | Description |
|-------|------|-------------|
| number | integer | Sequential identifier (1, 2, 3, ...) across all categories |
| file_path | string | Relative path from repository root (e.g., `solune/backend/src/api/chat.py`) |
| line_range | string | Line number(s) affected (e.g., `42`, `42-45`) |
| category | enum | `security` \| `runtime` \| `logic` \| `test-quality` \| `code-quality` |
| description | string | Human-readable explanation of the bug (1–2 sentences) |
| status | enum | `fixed` \| `flagged` |
| commit_sha | string \| null | SHA of the commit containing the fix (null if flagged) |

**Validation Rules**:

- `number` must be unique and sequential starting from 1
- `file_path` must reference an existing file in the repository
- `line_range` must reference valid lines within the file
- `category` must be one of the five defined categories
- `status` = `fixed` requires a non-null `commit_sha` and at least one associated RegressionTest
- `status` = `flagged` requires an associated TodoComment in the source code

**Relationships**:

- One BugReportEntry → one or more RegressionTest (when status = `fixed`)
- One BugReportEntry → one TodoComment (when status = `flagged`)
- One BugReportEntry → one Commit (when status = `fixed`)
- Many BugReportEntry → one SummaryTable

---

### 2. RegressionTest

**Description**: A test added specifically to guard against reintroduction of a fixed bug. Each regression test is linked to a specific BugReportEntry and designed to fail if the original bug is reintroduced (FR-003).

| Field | Type | Description |
|-------|------|-------------|
| test_file | string | Path to the test file (e.g., `solune/backend/tests/unit/test_chat_store.py`) |
| test_name | string | Test function name (e.g., `test_timestamp_z_suffix_parsing`) |
| bug_entry_number | integer | Reference to the BugReportEntry this test guards |
| test_framework | enum | `pytest` \| `vitest` |
| assertion_type | string | What the test asserts (e.g., "validates Z suffix is parsed correctly") |

**Validation Rules**:

- `test_file` must exist and be within the appropriate test directory (`solune/backend/tests/` or `solune/frontend/src/`)
- `test_name` must follow framework conventions: `test_*` for pytest, `it()/test()` for vitest
- `bug_entry_number` must reference a valid BugReportEntry with status = `fixed`
- The test must fail when the bug is manually reintroduced (mutation testing principle)

**Placement Rules**:

- Backend unit tests: `solune/backend/tests/unit/test_<module>.py`
- Backend integration tests: `solune/backend/tests/integration/test_<feature>.py`
- Frontend tests: co-located as `<component>.test.tsx` or `<utility>.test.ts`

**Relationships**:

- Many RegressionTest → one BugReportEntry
- Contained within: existing test directories (no new test directories created)

---

### 3. TodoComment

**Description**: An inline code comment marking an ambiguous issue deferred for human decision. Placed at the exact location of the potential bug in source code (FR-005).

| Field | Type | Description |
|-------|------|-------------|
| file_path | string | Path to the file containing the comment |
| line_number | integer | Line where the comment is placed |
| marker | string | Always `# TODO(bug-bash):` (Python) or `// TODO(bug-bash):` (TypeScript) |
| issue_description | string | What the potential bug is |
| options | string[] | Available resolution approaches |
| deferral_reason | string | Why this needs human judgment |
| bug_entry_number | integer | Reference to the associated BugReportEntry |

**Validation Rules**:

- `marker` must use the exact prefix `TODO(bug-bash):` — no variations
- The comment must be placed at or immediately before the problematic code
- `options` must include at least two alternatives
- `deferral_reason` must explain why automated resolution is inappropriate

**Format Examples**:

```python
# TODO(bug-bash): The CORS origin list includes '*' in dev mode but there's no
# env check to restrict this in production. Options: (1) add explicit production
# origin list, (2) remove wildcard entirely, (3) add runtime env detection.
# Needs human review: changing CORS could break existing integrations.
```

```typescript
// TODO(bug-bash): This useEffect has no cleanup function but subscribes to
// a WebSocket. Options: (1) add cleanup to close connection, (2) move to
// a context provider with lifecycle management. Needs human review: option 2
// is an architectural change that exceeds bug-bash scope.
```

**Relationships**:

- One TodoComment → one BugReportEntry (with status = `flagged`)

---

### 4. Commit

**Description**: A version control unit containing one or more related bug fixes. Each commit message must follow the format specified in FR-008.

| Field | Type | Description |
|-------|------|-------------|
| sha | string | Git commit hash |
| message | string | Structured commit message |
| files_changed | string[] | List of modified files |
| bug_entry_numbers | integer[] | BugReportEntry numbers addressed in this commit |
| tests_added | string[] | Test files added or modified |

**Commit Message Format**:

```text
fix(<category>): <short description>

What: <what the bug was>
Why: <why it is a bug — impact on users/system>
How: <how the fix resolves it>

Bug-bash: #<number>[, #<number>...]
```

**Validation Rules**:

- Message must contain all three sections: What, Why, How
- `category` must match the BugReportEntry category
- Every commit must leave the full test suite passing (FR-006)
- Every commit must leave linting passing (FR-007)
- Files changed should be minimal — only lines necessary for the fix (FR-012)

**Grouping Rules**:

- Related fixes in the same file and same category may be grouped in one commit
- Fixes across different categories should be in separate commits
- Test additions are included in the same commit as their corresponding fix

**Relationships**:

- One Commit → one or more BugReportEntry
- One Commit → one or more RegressionTest (always paired)

---

### 5. SummaryTable

**Description**: The consolidated output artifact listing all BugReportEntry items with metadata and resolution status. Produced at the conclusion of the review (FR-013, FR-014).

| Field | Type | Description |
|-------|------|-------------|
| entries | BugReportEntry[] | All discovered bugs, ordered by sequential number |
| total_fixed | integer | Count of entries with status = `fixed` |
| total_flagged | integer | Count of entries with status = `flagged` |
| categories_covered | string[] | All five categories must appear if bugs were found |
| generated_date | string | ISO 8601 timestamp of summary generation |

**Table Format**:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

**Validation Rules**:

- Every BugReportEntry must appear in the table (completeness)
- Entries are numbered sequentially (no gaps)
- Only files with bugs appear — clean files are omitted (FR-014)
- Status must use exact markers: `✅ Fixed` or `⚠️ Flagged (TODO)`
- Table must be valid markdown that renders correctly

**Relationships**:

- Contains: all BugReportEntry instances
- Produced after: all Commit and TodoComment entities are finalized

## Entity Relationships

```text
BugReportEntry ──[status=fixed]──▶ RegressionTest (1:N)
      │                                    │
      │                                    ▼
      ├──[status=fixed]──▶ Commit ◀── contains ── RegressionTest
      │
      ├──[status=flagged]──▶ TodoComment (1:1)
      │
      ▼
SummaryTable ◀── aggregates ── BugReportEntry (N:1)
```

1. Each **BugReportEntry** is either fixed (linked to a **Commit** + **RegressionTest**) or flagged (linked to a **TodoComment**)
2. A **Commit** groups one or more related fixes with their regression tests
3. All **BugReportEntry** items are aggregated into the final **SummaryTable**
4. The process is strictly sequential: discovery → fix/flag → test → commit → summarize

## Review File Scope

The following file groups define the review scope, organized by review priority:

### Priority 1 — Security-Critical Files

| File Group | Path Pattern | Review Focus |
|------------|-------------|--------------|
| API routes | `solune/backend/src/api/*.py` | Auth injection, input validation |
| Middleware | `solune/backend/src/middleware/*.py` | Security headers, guard logic |
| Config | `solune/backend/src/config.py` | Exposed secrets, insecure defaults |
| Guard config | `solune/guard-config.yml` | Path protection rules |
| Docker configs | `docker-compose.yml`, `solune/docker-compose.yml` | Exposed ports, secrets in env |
| Env template | `solune/.env.example` | Secret patterns |
| Encryption service | `solune/backend/src/services/encryption.py` | Cryptographic correctness |

### Priority 2 — Runtime-Critical Files

| File Group | Path Pattern | Review Focus |
|------------|-------------|--------------|
| Services | `solune/backend/src/services/**/*.py` | Resource leaks, error handling |
| Database | `solune/backend/src/services/database.py` | Connection management |
| WebSocket | `solune/backend/src/services/websocket.py` | Connection lifecycle |
| React hooks | `solune/frontend/src/hooks/*.ts` | Cleanup, race conditions |
| Main entry | `solune/backend/src/main.py` | Startup errors |

### Priority 3 — Logic-Critical Files

| File Group | Path Pattern | Review Focus |
|------------|-------------|--------------|
| Models | `solune/backend/src/models/*.py` | Validation, enum values |
| Service logic | `solune/backend/src/services/**/*.py` | State transitions, data flow |
| Frontend services | `solune/frontend/src/services/*.ts` | API contract adherence |
| Utilities | `solune/backend/src/utils.py`, `solune/frontend/src/utils/*.ts` | Edge cases |

### Priority 4 — Test Files

| File Group | Path Pattern | Review Focus |
|------------|-------------|--------------|
| Backend tests | `solune/backend/tests/**/*.py` | Mock leaks, assertion quality |
| Frontend tests | `solune/frontend/src/**/*.test.{ts,tsx}` | Mock scoping, meaningful assertions |
| Test utilities | `solune/frontend/src/test/**/*` | Shared mock correctness |
| Conftest | `solune/backend/tests/conftest.py` | Fixture quality |

### Priority 5 — Code Quality Files

| File Group | Path Pattern | Review Focus |
|------------|-------------|--------------|
| All source files | `solune/backend/src/**/*.py` | Dead code, duplication |
| All source files | `solune/frontend/src/**/*.{ts,tsx}` | Dead code, duplication |
| Constants | `solune/backend/src/constants.py` | Hardcoded values |
| Prompt templates | `solune/backend/src/prompts/*.py` | Dead code |
