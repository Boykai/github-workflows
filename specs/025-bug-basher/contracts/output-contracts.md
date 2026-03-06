# Output Contracts: Bug Bash — Full Codebase Review & Fix

**Feature Branch**: `025-bug-basher`

## Summary Table Contract (FR-023)

The final output of the bug bash is a markdown summary table. This table MUST be included as the last section of the implementation output.

### Format

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

### Column Specifications

| Column | Type | Format | Required |
|--------|------|--------|----------|
| `#` | integer | Sequential, 1-based | Yes |
| `File` | string | Relative path from repo root, wrapped in backticks | Yes |
| `Line(s)` | string | Single line `N` or range `N-M` | Yes |
| `Category` | enum | One of: `Security`, `Runtime`, `Logic`, `Test`, `Quality` | Yes |
| `Description` | string | Brief, actionable description (<100 chars) | Yes |
| `Status` | enum | `✅ Fixed` or `⚠️ Flagged (TODO)` | Yes |

### Ordering Rules

1. Entries MUST be grouped by category in priority order: Security → Runtime → Logic → Test → Quality
2. Within each category, entries MUST be ordered by file path (alphabetical)
3. Within the same file, entries MUST be ordered by line number (ascending)

### Inclusion Rules

- **Include**: Only files where a bug was found and either fixed or flagged
- **Exclude**: Files with no bugs (spec constraint: "If a file has no bugs, skip it — don't mention it in the summary")
- **Include**: Every `# TODO(bug-bash):` comment must have a corresponding `⚠️ Flagged (TODO)` entry
- **Include**: Every new regression test must correspond to a `✅ Fixed` entry

### Status Definitions

- **✅ Fixed**: Bug was resolved in source code, at least one regression test was added, and the full test suite passes including the new test.
- **⚠️ Flagged (TODO)**: Ambiguous issue was left as a `# TODO(bug-bash):` comment in the source code for human review. No code change was made. The comment describes the issue, options, and why human judgment is needed.

## Commit Message Contract

Each commit MUST follow this format:

```
fix(<category>): <concise description>

What: <what the bug was>
Why: <why it's a bug>
How: <how the fix resolves it>

Affects: <file1>, <file2>, ...
Tests: <new test names>
```

### Category Tags

| Tag | Bug Category |
|-----|-------------|
| `security` | Security Vulnerabilities (Category 1) |
| `runtime` | Runtime Errors (Category 2) |
| `logic` | Logic Bugs (Category 3) |
| `test` | Test Gaps & Test Quality (Category 4) |
| `quality` | Code Quality Issues (Category 5) |

## TODO Comment Contract (FR-022)

### Python Format
```python
# TODO(bug-bash): <Category> — <description>.
# Options: (A) <option A>, (B) <option B>.
# Needs human review because: <reason>.
```

### TypeScript Format
```typescript
// TODO(bug-bash): <Category> — <description>.
// Options: (A) <option A>, (B) <option B>.
// Needs human review because: <reason>.
```

### Rules
- The marker `TODO(bug-bash)` MUST be searchable (no variations like `TODO(bugbash)` or `TODO (bug-bash)`)
- Each TODO MUST include all three lines: description, options, and rationale
- Category MUST match one of: Security, Runtime, Logic, Test, Quality

## Regression Test Contract (FR-013)

### Naming Convention

**Python**: `test_<module>_<bug_short_description>`
**TypeScript**: `it('should <expected behavior after fix>')`

### Structure Requirements

1. Each regression test MUST have a docstring/comment explaining what bug it prevents
2. Each regression test MUST assert the **correct** behavior (not just absence of error)
3. Each regression test MUST be added to the existing test file for the module, or create a new file following the existing naming convention if no test file exists
4. Test placement MUST follow existing project conventions:
   - Backend: `backend/tests/unit/test_<module>.py` or `backend/tests/integration/test_<module>.py`
   - Frontend: colocated `<component>.test.tsx` or in `__tests__/` directory

### Validation

After all tests are added:
```bash
# Backend
cd backend && pytest tests/ -x  # Stop on first failure

# Frontend
cd frontend && npm run test     # Vitest run
```
