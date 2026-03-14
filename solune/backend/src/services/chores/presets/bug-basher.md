---
name: Bug Basher
about: Recurring chore — Bug Basher
title: '[CHORE] Bug Basher'
labels: chore
assignees: ''
---

## Bug Bash: Full Codebase Review & Fix

### Objective
Perform a comprehensive bug bash code review of the **entire codebase**. Identify bugs, fix them, and ensure fixes are validated by tests.

### Scope — Review Categories
Audit every file in the repository for the following bug categories, in priority order:

1. **Security vulnerabilities** — auth bypasses, injection risks, secrets/tokens exposed in code or config, insecure defaults, improper input validation
2. **Runtime errors** — unhandled exceptions, race conditions, null/None references, missing imports, type errors, file handle leaks, database connection leaks
3. **Logic bugs** — incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values
4. **Test gaps & test quality** — untested code paths, tests that pass for the wrong reason, mock leaks (e.g., `MagicMock` objects leaking into production paths like database file paths), assertions that never fail, missing edge case coverage
5. **Code quality issues** — dead code, unreachable branches, duplicated logic, hardcoded values that should be configurable, missing error messages, silent failures

### Actions Required

**For obvious/clear bugs:**
- Fix the bug directly in the source code.
- Update any existing tests that are affected by the fix.
- Add at least one new regression test per bug to ensure it does not reoccur.
- Write a clear commit message explaining: what the bug was, why it's a bug, and how the fix resolves it.

**For ambiguous or trade-off situations:**
- Do NOT make the change.
- Instead, add a `# TODO(bug-bash):` comment at the relevant location describing the issue, the options, and why it needs a human decision.
- Include these in a summary (see Output below).

### Validation
After all fixes are applied:
1. Run `pytest` and ensure the full test suite passes (including all new regression tests).
2. Run any existing linting/formatting checks if configured (e.g., `flake8`, `black`, `ruff`).
3. Do not commit if tests fail — iterate on the fix until green.

### Output
At the end, provide a single summary comment with:

| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |

- **✅ Fixed** — bug was resolved, tests added, all passing
- **⚠️ Flagged (TODO)** — ambiguous issue left as `TODO(bug-bash)` comment for human review

### Constraints
- Do not change the project's architecture or public API surface.
- Do not add new dependencies.
- Preserve existing code style and patterns.
- Each fix should be minimal and focused — no drive-by refactors.
- If a file has no bugs, skip it — don't mention it in the summary.

