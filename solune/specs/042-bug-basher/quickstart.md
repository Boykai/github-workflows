# Quickstart: Bug Basher — Full Codebase Review & Fix

**Feature**: 042-bug-basher
**Date**: 2026-03-15

## Prerequisites

- Full repository clone (not shallow — run `git fetch --unshallow origin` if needed)
- Python 3.11+ with the backend dependencies installed (`cd solune/backend && pip install -e ".[dev]"`)
- Node.js 18+ with frontend dependencies installed (`cd solune/frontend && npm install`)
- Ability to run `pytest`, `vitest`, `ruff`, and `eslint`

## Verify Tools Before Starting

```bash
# Backend tests
cd solune/backend && python -m pytest tests/ -v --co  # list tests without running
cd solune/backend && python -m ruff check src/         # lint check

# Frontend tests
cd solune/frontend && npx vitest run                   # run tests
cd solune/frontend && npm run lint                      # lint check
```

All four commands must succeed before beginning the review.

## Review Workflow

### Phase 1: Security Vulnerabilities (P1)

**Time estimate**: 2–3 hours

```bash
# 1. Search for hardcoded secrets
grep -rn "password\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
grep -rn "token\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
grep -rn "secret\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
grep -rn "api_key\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/

# 2. Check auth on all API routes
# For each file in solune/backend/src/api/*.py:
#   - Verify sensitive routes include auth dependency
#   - Check for missing input validation on request bodies

# 3. Review config files for insecure defaults
# Files: config.py, docker-compose.yml, .env.example, guard-config.yml

# 4. Check for injection risks
grep -rn "subprocess\|os\.system\|os\.popen" solune/backend/src/
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" solune/backend/src/
```

For each finding:
- **Obvious fix**: Fix it, add regression test, commit with `fix(security): <description>`
- **Ambiguous**: Add `# TODO(bug-bash):` comment, don't change the code

```bash
# Verify after each fix
cd solune/backend && python -m pytest tests/ -v && python -m ruff check src/
```

### Phase 2: Runtime Errors (P2)

**Time estimate**: 2–3 hours

```bash
# 1. Check for resource leaks
grep -rn "open(" solune/backend/src/ | grep -v "with "  # file handles without context manager
grep -rn "\.connect(" solune/backend/src/               # DB connections

# 2. Check for unhandled exceptions
# Review each service file for try/except coverage on I/O operations

# 3. Check for null/None references
grep -rn "\.get(" solune/backend/src/ | head -20        # check for safe access patterns
grep -rn "\[\"" solune/backend/src/                     # check for unsafe dict access

# 4. Check datetime parsing (known issue with Z suffix)
grep -rn "fromisoformat" solune/backend/src/

# 5. Check frontend hooks for cleanup
grep -rn "useEffect" solune/frontend/src/hooks/ | head -20
```

For each finding:
- Fix obvious bugs (missing cleanup, unhandled exceptions)
- Add regression test per fix
- Commit with `fix(runtime): <description>`

```bash
# Verify after each fix
cd solune/backend && python -m pytest tests/ -v && python -m ruff check src/
cd solune/frontend && npx vitest run && npm run lint
```

### Phase 3: Logic Bugs (P3)

**Time estimate**: 2–3 hours

```bash
# 1. Check enum/status mismatches
grep -rn "status" solune/backend/src/models/            # find all status enums
# Cross-reference with database schema in migrations/

# 2. Check pagination logic
grep -rn "offset\|limit\|page" solune/backend/src/api/

# 3. Check return values
# Review each service method for correct return types
# Check API route handlers return correct HTTP status codes

# 4. Check control flow
# Look for unreachable code after early returns
# Check boolean logic in conditionals
```

For each finding:
- Fix obvious logic errors
- Add regression test covering the edge case
- Commit with `fix(logic): <description>`

### Phase 4: Test Quality (P4)

**Time estimate**: 1–2 hours

```bash
# 1. Check for mock leaks
grep -rn "MagicMock\|Mock(" solune/backend/tests/
# Verify each Mock usage is properly scoped (with statement or decorator)

# 2. Check for empty or weak assertions
grep -rn "assert True\|assert.*is not None" solune/backend/tests/
grep -rn "expect.*toBeTruthy\|expect.*toBeDefined" solune/frontend/src/

# 3. Check for tests with no assertions
# Review each test function for at least one meaningful assert/expect
```

For each finding:
- Fix directly in the test file
- Explain why the original test was incorrect in commit message
- Commit with `fix(test-quality): <description>`

### Phase 5: Code Quality (P5)

**Time estimate**: 1–2 hours

```bash
# 1. Check for dead code (ruff catches some)
cd solune/backend && python -m ruff check src/ --select F841,F401
# F841 = unused variables, F401 = unused imports

# 2. Check for silent failures
grep -rn "except.*pass\|except:$" solune/backend/src/
grep -rn "\.catch.*{.*}" solune/frontend/src/ | grep -v "test"

# 3. Check for hardcoded values
grep -rn "timeout\s*=\s*[0-9]" solune/backend/src/
grep -rn "limit\s*=\s*[0-9]" solune/backend/src/
```

For each finding:
- Remove dead code, add error logging to silent failures
- Flag architectural cleanup with `TODO(bug-bash)`
- Commit with `fix(code-quality): <description>`

## Final Validation

After all phases are complete:

```bash
# 1. Full backend test suite
cd solune/backend && python -m pytest tests/ -v

# 2. Full frontend test suite
cd solune/frontend && npx vitest run

# 3. Full linting
cd solune/backend && python -m ruff check src/
cd solune/frontend && npm run lint

# 4. Verify no architecture or API changes
git diff --stat HEAD~N  # review scope of all changes
```

All four checks must pass with zero failures and zero new violations.

## Generate Summary Table

After final validation, compile the summary table:

```markdown
| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
```

Rules:
- Number entries sequentially across all categories
- Only include files where bugs were found
- Use `✅ Fixed` for resolved bugs with tests
- Use `⚠️ Flagged (TODO)` for deferred issues
- Order by discovery sequence (approximately by category priority)

## Commit Strategy

Each commit should:
1. Fix one or a small group of related bugs in the same category
2. Include the regression test(s) in the same commit
3. Leave the full test suite passing
4. Use the format: `fix(<category>): <short description>`

Example:
```bash
git commit -m "fix(security): Remove hardcoded API token from config defaults

What: config.py contained a default API token value 'dev-token-123'
Why: Hardcoded tokens in source code can be extracted from version history
How: Replaced with os.environ.get('API_TOKEN') requiring explicit configuration

Bug-bash: #1"
```
