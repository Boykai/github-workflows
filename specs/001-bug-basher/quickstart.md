# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 001-bug-basher | **Date**: 2026-03-22

## Prerequisites

- Python 3.11+ with `pip`
- Node.js 20+ with `npm`
- Git

## Setup

### 1. Install Backend Dependencies

```bash
cd solune/backend
pip install -e ".[dev]"
```

### 2. Install Frontend Dependencies

```bash
cd solune/frontend
npm install
```

### 3. Verify Baseline Tests Pass

Run both test suites to establish the baseline before making any changes:

```bash
# Backend tests
cd solune/backend
pytest --timeout=60

# Frontend tests
cd solune/frontend
npm run test
```

### 4. Verify Linters Pass

```bash
# Backend linting
cd solune/backend
ruff check src tests
ruff format --check src tests

# Frontend linting
cd solune/frontend
npm run lint
npm run type-check
```

## Execution Workflow

### Phase 1: Security Vulnerabilities (P1)

```bash
# Run security scanner first for automated findings
cd solune/backend
bandit -r src/ -f json -o /tmp/bandit-report.json

# Review findings, fix confirmed bugs, add regression tests
# After fixes:
pytest --timeout=60
ruff check src tests
```

### Phase 2: Runtime Errors (P2)

```bash
# Run type checker for automated findings
cd solune/backend
pyright src

# Review type errors, fix null refs and unhandled exceptions
# After fixes:
pytest --timeout=60
```

### Phase 3: Logic Bugs (P3)

```bash
# Manual review of state machines, control flow, return values
# Fix confirmed logic bugs, add regression tests
# After fixes:
cd solune/backend && pytest --timeout=60
cd solune/frontend && npm run test
```

### Phase 4: Test Gaps & Quality (P4)

```bash
# Check coverage gaps
cd solune/backend
pytest --cov=src --cov-report=term-missing --timeout=60

cd solune/frontend
npm run test:coverage

# Fix mock leaks, dead assertions, add missing tests
```

### Phase 5: Code Quality Issues (P5)

```bash
# Ruff catches many quality issues
cd solune/backend
ruff check src tests --select F401,F841,E711,E712,W

cd solune/frontend
npm run lint

# Fix dead code, silent failures, hardcoded values
```

## Validation

After all phases complete:

```bash
# Full backend validation
cd solune/backend
ruff check src tests
ruff format --check src tests
pyright src
bandit -r src/
pytest --timeout=60

# Full frontend validation
cd solune/frontend
npm run lint
npm run type-check
npm run test
npm run build
```

## Commit Convention

Each fix uses a structured commit message:

```text
fix(<category>): <what was wrong>

<why it's a bug and how the fix resolves it>

Regression test: <test file>::<test name>
```

Example:

```text
fix(security): remove hardcoded API token from config defaults

The default value for GITHUB_TOKEN in config.py contained a placeholder
that could be mistaken for a real token. Replaced with empty string and
added validation that the token is set before use.

Regression test: tests/unit/test_config.py::test_no_hardcoded_secrets
```

## Output

Generate the summary table as the final deliverable:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `path/to/file.py` | 42-45 | Security | Description | ✅ Fixed |
| 2 | `path/to/file.py` | 100 | Logic | Description | ⚠️ Flagged (TODO) |
```
