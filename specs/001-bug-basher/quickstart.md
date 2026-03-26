# Quickstart: Bug Basher

**Feature**: 001-bug-basher | **Date**: 2026-03-24

## Prerequisites

- Python ≥3.12 (backend)
- Node.js 25+ (frontend)
- Git
- Access to the repository

## Setup

### 1. Clone and checkout the feature branch

```bash
git checkout copilot/bug-bash-full-codebase-review
```

### 2. Install backend dependencies

```bash
cd solune/backend
pip install -e ".[dev]"
```

### 3. Install frontend dependencies

```bash
cd solune/frontend
npm ci
```

## Execution Workflow

### Phase 1: Security Audit (P1)

Audit all source files for security vulnerabilities in priority order:

```bash
# Run existing security scanners first
cd solune/backend
bandit -r src/ -ll -ii --skip B104,B608

# Then manual review of:
# - Auth flows (src/api/auth.py, src/dependencies.py)
# - Session management (src/services/session_store.py)
# - Middleware (src/middleware/)
# - Config validation (src/config.py)
# - Input handling (src/api/*.py)
```

### Phase 2: Runtime Errors (P2)

```bash
# Run type checkers to catch type errors
cd solune/backend && pyright src/
cd solune/frontend && npm run type-check

# Manual review for:
# - Unhandled exceptions
# - Resource leaks (file handles, DB connections)
# - Null/None references
# - Missing imports
```

### Phase 3: Logic Bugs (P3)

```bash
# Run full test suites to identify logic failures
cd solune/backend && pytest -q --tb=short
cd solune/frontend && npm test
```

### Phase 4: Test Quality (P4)

```bash
# Check coverage to find untested code paths
cd solune/backend && pytest --cov=src --cov-report=term-missing
cd solune/frontend && npm run test:coverage
```

### Phase 5: Code Quality (P5)

```bash
# Run linters for code quality
cd solune/backend && ruff check src/ tests/
cd solune/frontend && npm run lint
```

## Validation

After all fixes are applied, run the full validation suite:

### Backend

```bash
cd solune/backend
ruff check src/ tests/              # Linting
ruff format --check src/ tests/     # Formatting
pyright src/                         # Type checking
pytest -q --tb=short                 # Full test suite
```

### Frontend

```bash
cd solune/frontend
npm run lint                         # ESLint
npm run type-check                   # TypeScript
npm run test                         # Vitest
npm run build                        # Build verification
```

## Output

The bug bash produces:

1. **Fixed bugs**: Direct source code fixes with regression tests
2. **Flagged issues**: `# TODO(bug-bash):` comments for ambiguous findings
3. **Summary report**: Markdown table listing all findings with file, lines, category, description, and status

## Constraints Checklist

Before committing, verify:

- [ ] No new dependencies added
- [ ] No public API surface changes
- [ ] No architecture changes
- [ ] Each fix is minimal and focused
- [ ] All regression tests pass
- [ ] All linting checks pass
- [ ] Summary report is complete
