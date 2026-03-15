# Code Quality Review Contract

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Version**: 1.0
**Priority**: P5 — Lowest priority, reviewed last

## Purpose

Defines the process for identifying and resolving code quality issues across the Solune codebase. This contract governs User Story 5 (Code Quality Cleanup) and covers: dead code, unreachable branches, duplicated logic, hardcoded values that should be configurable, missing error messages, and silent failures.

## Input: File Scope

All source files reviewed in order:

1. **Backend source**: All files in `solune/backend/src/` — dead code, duplication, silent failures
2. **Frontend source**: All files in `solune/frontend/src/` — dead code, duplication, silent failures
3. **Constants**: `solune/backend/src/constants.py`, `solune/frontend/src/constants/` — hardcoded values
4. **Configuration**: `solune/backend/src/config.py` — hardcoded values that should be configurable
5. **Prompt templates**: `solune/backend/src/prompts/` — dead templates, unused variables
6. **Utility files**: `solune/backend/src/utils.py`, `solune/frontend/src/utils/` — unused helpers

## Check Categories

### CQ1: Dead Code

**Pattern**: Functions, variables, imports, classes, or code blocks that are never called, referenced, or reachable.

**Detection**:
- Unused imports (ruff/eslint may catch some, but not all)
- Functions defined but never called (search for definition, then search for usage)
- Variables assigned but never read
- `if False:` blocks or always-false conditions
- Commented-out code blocks

**Fix pattern**: Remove the dead code. If unsure whether something is used (e.g., dynamically referenced), flag with `TODO(bug-bash)` instead of removing.

**Regression test**: Full test suite must still pass after removal, confirming the code was truly unused.

### CQ2: Unreachable Branches

**Pattern**: Code branches that can never execute due to preceding conditions, early returns, or always-true/false guards.

**Detection**:
- `else` blocks after `if` conditions that always evaluate to true
- Code after unconditional `return`, `raise`, `break`, or `continue`
- `except` handlers for exceptions that can never be raised in the try block
- TypeScript branches guarded by conditions that TypeScript's type system proves impossible

**Fix pattern**: Remove the unreachable branch. If the branch is intentional defensive programming, add a comment explaining why.

**Regression test**: Full test suite passes, confirming no behavior change.

### CQ3: Duplicated Logic

**Pattern**: Identical or near-identical code blocks appearing in multiple locations.

**Detection**:
- Functions with the same body in different files
- Copy-pasted code blocks with only variable name differences
- Repeated pattern of the same 5+ lines across multiple files

**Fix pattern**: If consolidation can be done without changing architecture or public API, extract to a shared utility. Otherwise, flag with `TODO(bug-bash)` explaining the duplication and the architectural consideration.

**Regression test**: All existing tests pass after consolidation.

### CQ4: Hardcoded Values

**Pattern**: Magic numbers, hardcoded strings, or literal values that should be configurable or defined as named constants.

**Detection**:
- Numeric literals in business logic (timeouts, limits, sizes)
- Hardcoded URLs, paths, or resource identifiers
- String literals that appear in multiple locations
- Values that vary by environment but are hardcoded

**Fix pattern**: Extract to named constants in the appropriate constants file. If the value should vary by environment, flag with `TODO(bug-bash)` as making it configurable may require API changes.

**Regression test**: Assert the named constant has the expected value; verify behavior is unchanged.

### CQ5: Silent Failures

**Pattern**: Error conditions that are caught and silently swallowed without logging, notification, or user feedback.

**Detection**:
- Empty `except:` or `except Exception: pass` blocks
- `.catch(() => {})` in TypeScript/JavaScript
- Error handlers that log at DEBUG level instead of WARNING/ERROR
- Functions that return `None` or default values on error without any indication
- Note: `StructuredJsonFormatter` only emits whitelisted extra fields (`operation`, `duration_ms`, `error_type`, `status_code`) — errors logged with other extra fields may be silently dropped

**Fix pattern**: Add appropriate error logging (at WARNING or ERROR level), user-facing error messages, or explicit error propagation.

**Regression test**: Trigger the error condition and assert that appropriate logging or error response occurs.

## Output

For each finding, produce:
- A BugReportEntry with `category: code-quality`
- A code fix (if obvious) or TodoComment (if ambiguous)
- An explanation of the cleanup (in commit message)
- A commit with `fix(code-quality): <description>` message format

## Completion Criteria

- All source files scanned for dead code and unused imports
- No unreachable branches remain (except intentional defensive code with comments)
- Duplicated logic identified and resolved where safe, flagged where architectural
- Magic numbers extracted to named constants where appropriate
- No silently swallowed errors in production code paths
