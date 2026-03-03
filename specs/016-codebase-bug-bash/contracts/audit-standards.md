# Audit Standards & Process Contracts

This document defines the standards, processes, and conventions for the Bug Bash code audit. These are internal contracts that ensure consistency across all reviewers and audit phases.

## 1. Bug Category Definitions

### 🔴 Security Vulnerabilities (Priority: P1)

**Scope**: Authentication bypasses, injection risks (SQL, XSS, command), exposed secrets/tokens, insecure defaults, improper input validation, CORS misconfiguration, cookie security, CSRF vulnerabilities.

**Fix criteria**: A security fix must:
- Address the specific vulnerability without introducing new attack surface
- Include a regression test that demonstrates the vulnerability was exploitable before the fix
- Not weaken existing security controls

**Escalation**: If a vulnerability is severe (authentication bypass, data exposure) and the fix is ambiguous, flag it AND notify via the summary report with `🔴 URGENT` prefix.

### 🟠 Runtime Errors (Priority: P1)

**Scope**: Unhandled exceptions, race conditions, null/None/undefined references, missing imports, type errors, resource leaks (file handles, DB connections, WebSocket connections), async context errors.

**Fix criteria**: A runtime error fix must:
- Handle the error path explicitly (try/except, null check, resource cleanup)
- Include a regression test that triggers the error condition
- Not mask the error silently (log or propagate appropriately)

### 🟡 Logic Bugs (Priority: P2)

**Scope**: Incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, incorrect return values, wrong comparison operators, incorrect boolean logic.

**Fix criteria**: A logic bug fix must:
- Correct the specific logic error without changing the overall algorithm
- Include a regression test that verifies the correct behavior
- Document what the expected behavior is (in the test name or commit message)

### 🔵 Test Gaps & Quality (Priority: P2)

**Scope**: Untested code paths, tests passing for wrong reasons, mock leaks (MagicMock objects in production paths), assertions that never fail, missing edge case coverage, incorrect test setup/teardown.

**Fix criteria**: A test fix must:
- Make the test actually validate the intended behavior
- Demonstrate that deliberately breaking the code under test causes the test to fail
- Not introduce flaky behavior (no timing-dependent assertions)

### ⚪ Code Quality (Priority: P3)

**Scope**: Dead code, unreachable branches, duplicated logic, hardcoded values that should be configurable, silent failures (empty except blocks), missing error messages, unused imports, unused variables.

**Fix criteria**: A code quality fix must:
- Remove only confirmed dead/unreachable code
- Not change any observable behavior (all tests pass unchanged)
- For silent failures: add logging or proper error handling

---

## 2. Fix Commit Convention

### Commit Message Format

```
fix(<category>): <brief description>

<What>: Describe what was changed
<Why>: Explain why the original code was a bug
<How>: Describe the approach taken to fix it

File(s): <list of changed files>
Regression test: <test file>::<test function>
```

**Category tags**: `security`, `runtime`, `logic`, `test-quality`, `code-quality`

### Example

```
fix(security): validate redirect URL against allowlist in OAuth callback

What: Added URL validation in auth.py to check redirect_uri against configured allowlist
Why: The original code accepted arbitrary redirect URLs, enabling open redirect attacks
How: Added a helper function that validates the URL scheme and host against ALLOWED_REDIRECT_ORIGINS

File(s): backend/src/api/auth.py
Regression test: backend/tests/unit/test_auth.py::test_rejects_external_redirect_url
```

---

## 3. Flag (TODO) Convention

### Comment Format

```python
# TODO(bug-bash): <Category> — <Brief description>
# Options: (a) <option 1>  (b) <option 2>
# Needs human decision because: <rationale>
```

### Example

```python
# TODO(bug-bash): Logic — session_cleanup_interval may be too long for high-traffic deployments
# Options: (a) Reduce default to 1800s  (b) Make it configurable per-deployment  (c) Keep as-is
# Needs human decision because: The optimal interval depends on deployment scale which varies by user
```

### Rules
- Place the comment at the exact line of the issue (not at the top of the file)
- Do NOT change any code when flagging — only add the comment
- The comment must be self-contained: a reader should understand the issue without additional context

---

## 4. Audit Process Contract

### Phase Execution Order

```
Phase 1: Security Audit (all files)
  └─ Backend → Frontend → Infrastructure
Phase 2: Runtime Error Audit (all files)
  └─ Backend → Frontend → Infrastructure
Phase 3: Logic Bug Audit (all files)
  └─ Backend → Frontend → Infrastructure
Phase 4: Test Gap Audit (all test files)
  └─ Backend tests → Frontend tests → E2E tests
Phase 5: Code Quality Audit (all files)
  └─ Backend → Frontend → Infrastructure
Phase 6: Summary Report Generation
  └─ Compile all findings → Verify test suite → Generate table
```

### Pre-Audit Checklist

Before starting the audit:
1. ✅ Ensure `main` branch is checked out and up to date
2. ✅ Run full test suite to establish baseline (all tests must pass)
3. ✅ Run linters to establish baseline (all checks must pass)
4. ✅ Note any pre-existing failures for exclusion from findings

### Post-Fix Verification

After each fix:
1. ✅ Run the specific regression test to confirm it passes
2. ✅ Run the full test suite for the affected area (backend or frontend)
3. ✅ Run linters for the affected area
4. ✅ Commit the fix with the standard commit message format

### Final Verification

After all fixes are applied:
1. ✅ Run `cd backend && pytest -v` — must exit 0
2. ✅ Run `cd backend && ruff check src tests && ruff format --check src tests` — must exit 0
3. ✅ Run `cd frontend && npm test` — must exit 0
4. ✅ Run `cd frontend && npm run lint && npm run type-check` — must exit 0
5. ✅ Verify every Fix has a corresponding entry in the Summary Report
6. ✅ Verify every Flag has a corresponding entry in the Summary Report
7. ✅ Verify the Summary Report category counts match actual findings

---

## 5. Scope Exclusions

The following are explicitly OUT of scope for this bug bash:

| Exclusion | Rationale |
|-----------|-----------|
| Architecture changes | Spec requirement: "without altering architecture" |
| Public API signature changes | Spec requirement: "no public API signature changes" |
| New third-party dependencies | Spec requirement: "no new third-party dependencies" |
| Large-scale refactors | Spec requirement: "each fix must be minimal and focused" |
| Auto-generated files | Bugs originate from source, not generated output |
| Performance optimizations | Not a bug category in the spec |
| Feature additions | Bug bash is fix-only, not feature development |
| Documentation content changes | Unless documenting a bug fix or TODO |
