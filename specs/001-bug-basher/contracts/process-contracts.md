# Process Contracts: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-26 | **Phase**: 1 (Design & Contracts)

> **Note**: This feature does not introduce API endpoints or external interfaces. The "contracts" here define the process interfaces — inputs, outputs, and quality gates that govern the bug bash workflow.

## Contract 1: File Audit Process

### Input
- **Source**: Repository file tree (`solune/backend/src/`, `solune/frontend/src/`, `.github/workflows/`, `solune/scripts/`, infrastructure configs)
- **Format**: Source code files (`.py`, `.ts`, `.tsx`, `.yml`, `.json`, `.toml`)
- **Scope**: Every file in the repository (FR-001, SC-001)

### Processing Rules
1. Files are reviewed in category priority order: Security (P1) → Runtime (P2) → Logic (P3) → Test Quality (P4) → Code Quality (P5) (FR-012)
2. Within each category, backend files are reviewed before frontend files
3. Each file is inspected once per category pass
4. Findings are recorded as Bug Report Entries (see data-model.md)

### Output
- **Bug fixes**: Modified source files with minimal, focused changes (FR-006)
- **Regression tests**: New test functions/files validating each fix (FR-002, FR-013)
- **TODO comments**: `TODO(bug-bash)` annotations for ambiguous issues (FR-003)
- **Commits**: One or more commits per category with descriptive messages (FR-007)

---

## Contract 2: Bug Fix Validation Gate

### Input
- **Source**: Modified source files and new test files from a fix
- **Trigger**: After each bug fix or batch of related fixes

### Validation Steps

#### Backend Validation
```bash
cd solune/backend
ruff check src tests                    # Lint check
ruff format --check src tests           # Format check
bandit -r src/ -ll -ii --skip B104,B608 # Security scan
pyright src                             # Type check
pytest --cov=src --cov-report=term-missing \
  --ignore=tests/property \
  --ignore=tests/fuzz \
  --ignore=tests/chaos \
  --ignore=tests/concurrency            # Test + coverage
```

#### Frontend Validation
```bash
cd solune/frontend
npm run lint        # ESLint
npm run type-check  # TypeScript strict check
npm run test        # Vitest unit tests
npm run build       # Production build
```

### Pass Criteria
- All commands exit with code 0 (FR-008, FR-009)
- No new lint warnings introduced
- Coverage does not drop below 75% (backend `fail_under = 75`)
- No type errors introduced

### Failure Handling
- If validation fails, the fix must be iterated until green
- Do not commit failing changes
- If a fix cannot be made green without violating constraints (FR-004, FR-005, FR-006), flag it as `TODO(bug-bash)` instead

---

## Contract 3: Summary Table Output

### Input
- **Source**: All Bug Report Entries collected during the review

### Format
```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description of bug | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description of ambiguity | ⚠️ Flagged (TODO) |
```

### Validation Rules
- Every identified bug appears in the table (FR-010, SC-006)
- Files with no bugs are omitted (FR-011)
- Entries are numbered sequentially starting from 1
- `✅ Fixed` entries have corresponding commits and regression tests (SC-002)
- `⚠️ Flagged (TODO)` entries have corresponding `TODO(bug-bash)` comments in the source (SC-005)
- The table covers all 5 bug categories (SC-001)

---

## Contract 4: Commit Message Format

### Format
```
fix(<category>): <what was wrong>

<Why it's a bug>: <detailed explanation>

<How the fix resolves it>: <description of the change>

Regression test: <test function/file path>
```

### Example
```
fix(security): sanitize webhook payload before logging

Webhook payloads were logged with raw user input, which could contain
sensitive data or injection payloads that pollute log aggregation.

Sanitize payload fields through the existing input validation layer
before passing to the activity logger.

Regression test: tests/unit/test_webhooks.py::test_webhook_payload_sanitized
```

### Rules
- Category must be one of: `security`, `runtime`, `logic`, `test-quality`, `code-quality`
- Commit must not include unrelated changes (FR-006)
- Related fixes within the same file/module may be grouped into a single commit

---

## Contract 5: TODO Flag Format

### Format (Python)
```python
# TODO(bug-bash): <brief description of the issue>
# Options: <option A> | <option B> [| <option C> ...]
# Rationale: <why this needs a human decision, not an automated fix>
```

### Format (TypeScript)
```typescript
// TODO(bug-bash): <brief description of the issue>
// Options: <option A> | <option B> [| <option C> ...]
// Rationale: <why this needs a human decision, not an automated fix>
```

### Rules
- Placed at the exact line(s) where the issue exists
- Must include at least two options for resolution
- Must explain why the agent did not make the change (e.g., "would require API surface change" or "behavior intent is ambiguous")
- Must appear in the summary table with status `⚠️ Flagged (TODO)`
