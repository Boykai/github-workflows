# Quickstart: Bug Bash — Full Codebase Review & Fix

**Feature Branch**: `025-bug-basher`

## Pre-Audit Baseline

Before making any changes, establish a passing baseline to distinguish pre-existing issues from regressions introduced by bug fixes.

### Backend Baseline

```bash
cd backend

# 1. Install dependencies
pip install -e ".[dev]"

# 2. Lint baseline (record any pre-existing issues)
ruff check src/              # Should be zero violations
ruff format --check src/     # Should be zero violations

# 3. Type check baseline
pyright src/                 # Should be zero errors

# 4. Test baseline (run in batches to avoid timeout)
ls tests/unit/*.py | head -24 | xargs pytest -x
ls tests/unit/*.py | tail -27 | xargs pytest -x
pytest tests/integration/ -x

# Record: total tests passing, any skipped, any xfail
```

### Frontend Baseline

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Lint baseline
npx eslint .                 # Should be zero errors
npx tsc --noEmit             # Should be zero errors

# 3. Test baseline
npm run test                 # Vitest run, record total passing
```

## During Audit: Per-Fix Verification

After each bug fix, verify the fix doesn't introduce regressions.

### Single File Verification (Backend)

```bash
cd backend

# Run tests for the affected module only
pytest tests/unit/test_<module>.py -x -v

# Quick lint check on changed file
ruff check src/path/to/changed_file.py
ruff format --check src/path/to/changed_file.py
```

### Single File Verification (Frontend)

```bash
cd frontend

# Run tests for the affected component/hook
npx vitest run src/path/to/file.test.tsx

# Type check
npx tsc --noEmit
```

## Post-Audit: Full Validation

After all fixes are applied, run the complete validation suite.

### Backend Full Validation

```bash
cd backend

# 1. Lint — zero violations
ruff check src/
ruff format --check src/

# 2. Type check — zero errors
pyright src/

# 3. Full test suite — all pass (batch to avoid timeout)
ls tests/unit/*.py | head -24 | xargs pytest
ls tests/unit/*.py | tail -27 | xargs pytest
pytest tests/integration/

# 4. Verify regression test count
# Count new test functions added (should match number of ✅ Fixed entries)
git diff --name-only | grep test_ | wc -l
```

### Frontend Full Validation

```bash
cd frontend

# 1. Lint — zero errors
npx eslint .
npx tsc --noEmit

# 2. Full test suite — all pass
npm run test

# 3. Production build — succeeds
npm run build
```

### Summary Table Verification

```bash
cd ..  # Repository root

# 1. Verify all TODO(bug-bash) comments have corresponding table entries
grep -rn "TODO(bug-bash)" backend/src/ frontend/src/ | wc -l
# This count should match the number of ⚠️ Flagged entries in the summary table

# 2. Verify no TODO(bug-bash) comments in test files (they should only be in source)
grep -rn "TODO(bug-bash)" backend/tests/ frontend/src/**/*.test.* | wc -l
# This should be zero

# 3. Verify commit messages follow the contract
git log --oneline --no-merges | grep -E "^[a-f0-9]+ fix\((security|runtime|logic|test|quality)\):"
```

## Checklist

- [ ] Backend lint passes with zero violations
- [ ] Backend type check passes with zero errors
- [ ] All ~1,411 backend tests pass (including new regression tests)
- [ ] Frontend lint passes with zero errors
- [ ] Frontend type check passes with zero errors
- [ ] All frontend unit tests pass (including new regression tests)
- [ ] Frontend production build succeeds
- [ ] Every ✅ Fixed entry has at least one regression test
- [ ] Every ⚠️ Flagged entry has a corresponding `TODO(bug-bash)` comment in source
- [ ] Summary table is complete and follows the output contract format
- [ ] No pre-existing passing tests were broken by fixes
