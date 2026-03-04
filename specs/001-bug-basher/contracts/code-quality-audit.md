# Review Contract: Code Quality Audit (P5)

**Category**: Code Quality Issues
**Priority**: P5 — Lowest
**Scope**: All files in `backend/src/`, `frontend/src/`, and test files

## Checklist

### Dead Code
- [ ] No unused imports
- [ ] No unreachable code after return/raise/break/continue
- [ ] No unused variables or function parameters
- [ ] No commented-out code blocks that serve no documentation purpose
- [ ] No unused utility functions or classes

### Unreachable Branches
- [ ] No conditions that always evaluate to True or False
- [ ] No exception handlers that can never trigger
- [ ] No type checks that are always satisfied
- [ ] No default cases in exhaustive switches that are dead

### Duplicated Logic
- [ ] No copy-pasted code blocks that should be extracted to shared functions
- [ ] No repeated validation logic that should use a decorator or middleware
- [ ] No repeated error handling patterns that should use the centralized utilities

### Hardcoded Values
- [ ] No magic numbers without constants or configuration
- [ ] No hardcoded URLs or paths that should be configurable
- [ ] No hardcoded timeouts or limits that should be settings
- [ ] Default values are documented and reasonable

### Silent Failures
- [ ] No empty `except: pass` blocks
- [ ] No error conditions that return None without logging
- [ ] No failed operations that proceed as if successful
- [ ] All catch blocks at minimum log the error

## Acceptance Criteria
- Dead code removal does not change application behavior (existing tests pass)
- Hardcoded values replaced with configurable settings include tests for both defaults and overrides
- Silent failures updated to provide appropriate logging
- All changes validated by `ruff check`, `eslint`, and full test suite
