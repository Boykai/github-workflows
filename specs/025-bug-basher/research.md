# Research: Bug Bash — Full Codebase Review & Fix

**Feature Branch**: `025-bug-basher`
**Date**: 2026-03-06
**Status**: Complete — all NEEDS CLARIFICATION resolved

## Findings

### 1. Audit Methodology — Manual Code Review vs. Static Analysis Tools

- **Decision**: Combine manual code review with existing tooling (ruff, pyright, eslint, tsc) — no new tools
- **Rationale**: The spec explicitly prohibits adding new dependencies (FR-025). The project already has comprehensive linting (ruff with FURB, PTH, PERF, RUF rules), type checking (pyright basic mode, tsc), and test frameworks (pytest, vitest). Manual review is required for semantic bugs (logic errors, test quality issues) that no static analysis tool can catch. Existing tools catch syntax-level issues that should already be clean.
- **Alternatives considered**: Adding bandit (Python security scanner), semgrep, or CodeQL locally — rejected because the spec prohibits new dependencies and these tools would need to be added to dev dependencies. CodeQL is available via GitHub Actions (already in CI) and will run on the PR.
- **Impact**: Audit relies on file-by-file manual review augmented by grep/search for common anti-patterns.

### 2. Python Security Audit Patterns

- **Decision**: Search for the following patterns as indicators of security issues
- **Rationale**: These are the most common Python web security vulnerabilities in FastAPI applications.
- **Patterns to search**:
  - `os.environ.get` without default vs. hardcoded secrets in source
  - `eval(`, `exec(`, `__import__` — code injection
  - Raw SQL strings or string formatting in database queries
  - Missing `Depends()` on endpoints that should require auth
  - `CORS` configuration with wildcard origins
  - Exception handlers that leak internal details to API responses
  - `pickle.loads`, `yaml.unsafe_load` — deserialization attacks
  - Missing webhook signature verification
  - Token/secret values logged at DEBUG/INFO level
  - `cryptography` usage without proper key management

### 3. TypeScript/React Security Audit Patterns

- **Decision**: Search for the following patterns as indicators of frontend security issues
- **Rationale**: These are the most common React/TypeScript web security vulnerabilities.
- **Patterns to search**:
  - `dangerouslySetInnerHTML` — XSS risk
  - `window.location` manipulation without sanitization — open redirect
  - Storing tokens in `localStorage` vs. httpOnly cookies
  - Missing CSRF protection on state-changing requests
  - Unvalidated URL parameters used in API calls
  - Missing `rel="noopener noreferrer"` on external links

### 4. Runtime Error Patterns

- **Decision**: Search for common Python async runtime error patterns
- **Rationale**: The backend is async-first (FastAPI + aiosqlite + websockets). Async code has unique runtime error patterns.
- **Patterns to search**:
  - `await` outside async context or missing `await` on coroutines
  - Bare `except:` or `except Exception:` without logging
  - File/DB connections opened without context managers (`async with`)
  - Race conditions in shared mutable state (global variables, class attributes)
  - `asyncio.create_task` without exception handling (fire-and-forget)
  - Missing `None` checks before attribute access
  - `dict[]` access without `.get()` on user-supplied data

### 5. Test Quality Anti-Patterns

- **Decision**: Search for the following test quality anti-patterns
- **Rationale**: The spec specifically calls out mock leaks (FR-014), meaningless assertions (FR-015), and untested critical paths (FR-016).
- **Patterns to search**:
  - `MagicMock()` used as path/URL/config value that reaches production code
  - `assert mock_obj` — always truthy, meaningless assertion
  - `assert True` — unconditional pass
  - `assert result is not None` when result is a MagicMock (always truthy)
  - Test functions with no assertions (test runs but verifies nothing)
  - `@pytest.mark.skip` with no explanation
  - Mocked return values that don't match real API shapes
  - Tests that catch exceptions too broadly (`pytest.raises(Exception)`)

### 6. Backend Test Execution Strategy

- **Decision**: Run tests in batches to avoid timeout issues, then full suite for final validation
- **Rationale**: Repository memory notes that "Backend tests (1411 total) timeout when run all at once but pass when split in batches." Batching by file prefix ensures reliability.
- **Execution plan**:
  1. Run modified test files individually after each fix
  2. Run batch validation: `ls tests/unit/*.py | head -24 | xargs pytest` then `ls tests/unit/*.py | tail -27 | xargs pytest`
  3. Final full-suite run: `pytest` (may need timeout increase)
- **Alternatives considered**: Running all 1,411 tests at once — rejected per repository memory about timeouts.

### 7. Frontend Test Execution Strategy

- **Decision**: Use `npm run test` (Vitest) for unit tests, skip Playwright E2E (requires running server)
- **Rationale**: Unit tests validate component behavior and hook logic. E2E tests require a running backend and frontend server which is not practical during the audit. The spec focuses on code-level bugs, not E2E integration issues.
- **Execution plan**:
  1. Run modified test files individually: `npx vitest run src/path/to/file.test.tsx`
  2. Run full unit suite: `npm run test`
  3. Lint: `npm run lint` + `npx tsc --noEmit`
- **Alternatives considered**: Running Playwright E2E — deferred to CI pipeline.

### 8. Fix-to-Commit Strategy

- **Decision**: Group fixes by category within logical file groups, commit per category
- **Rationale**: The spec requires clear commit messages explaining "what the bug was, why it's a bug, and how the fix resolves it." Grouping by category keeps commits focused and reviewable. Individual fixes within a category may be combined when they affect the same file.
- **Commit pattern**:
  - `fix(security): <description>` — Category 1 fixes
  - `fix(runtime): <description>` — Category 2 fixes
  - `fix(logic): <description>` — Category 3 fixes
  - `fix(test): <description>` — Category 4 fixes
  - `fix(quality): <description>` — Category 5 fixes
- **Alternatives considered**: One commit per individual bug fix — rejected as too granular for 10+ potential fixes; per-file commits — rejected because related fixes across files should be atomic.

### 9. Ambiguity Threshold

- **Decision**: Flag as `TODO(bug-bash)` when any of these conditions apply
- **Rationale**: The spec distinguishes between "obvious/clear bugs" and "ambiguous or trade-off situations." Clear criteria prevent over-fixing or under-flagging.
- **Flag conditions**:
  1. Fix would change the public API surface (response shape, status codes, endpoint paths)
  2. Fix has multiple valid approaches with different trade-offs
  3. Fix could break downstream consumers or integrations
  4. Fix for a single file causes >2 previously passing tests to fail (spec edge case)
  5. Removal of dead code when dynamic dispatch (`getattr`, string lookups) cannot be ruled out (spec edge case)
  6. Performance trade-off (e.g., adding validation that could slow a hot path)
- **Comment format**: `# TODO(bug-bash): <category> — <description>. Options: <A> vs <B>. Needs human review because: <reason>.`
