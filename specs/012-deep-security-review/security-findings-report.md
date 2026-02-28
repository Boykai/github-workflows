# Security Findings Report

**Project**: Agent Projects (github-workflows)
**Date**: 2026-02-28
**Reviewer**: Automated Security Audit
**Scope**: Full-stack web application — Python/FastAPI backend, React/TypeScript frontend, GitHub Actions CI, Docker configuration
**Standards**: OWASP Top 10 (2021), GitHub Actions Security Hardening Guide

---

## Methodology

1. **Static Analysis**: Manual code review of all source files, configuration files, and workflow definitions
2. **Dependency Audit**: `pip-audit` (backend), `npm audit` (frontend) against known CVE databases
3. **Secrets Scan**: Pattern-based scan across entire repository for hardcoded credentials, API keys, tokens
4. **Configuration Review**: Inspection of CI workflows, Docker files, environment templates, and CORS settings
5. **Authentication Flow Review**: Analysis of OAuth state management, session handling, cookie flags, and admin authorization

## Severity Classification

| Severity | Definition |
|----------|-----------|
| **Critical** | Actively exploitable, immediate data breach risk |
| **High** | Significant security weakness, exploitation likely without mitigation |
| **Medium** | Security concern with limited exploitability or impact |
| **Low** | Minor issue, defense-in-depth improvement |
| **Info** | Observation or recommendation, no immediate risk |

---

## Findings

### SEC-001: GitHub Actions Using Mutable Version Tags (High)

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Supply Chain Security |
| **Affected Component** | `.github/workflows/ci.yml` |
| **OWASP** | A08:2021 — Software and Data Integrity Failures |
| **Status** | ✅ Remediated |

**Description**: All third-party GitHub Actions (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`) were referenced using mutable version tags. Tags can be force-pushed by upstream maintainers, meaning a compromised action repository could inject malicious code into CI runs without any visible change to the workflow file.

**Remediation**: Pinned all action references to full 40-character commit SHAs:
- `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5` (v4)
- `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065` (v5)
- `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020` (v4)

Human-readable version comments are preserved inline.

---

### SEC-002: Missing Explicit Permissions in GitHub Workflows (High)

| Field | Value |
|-------|-------|
| **Severity** | High |
| **Category** | Least Privilege Violation |
| **Affected Component** | `.github/workflows/ci.yml` |
| **OWASP** | A01:2021 — Broken Access Control |
| **Status** | ✅ Remediated |

**Description**: The CI workflow lacked explicit `permissions` blocks, inheriting the repository's default token permissions. This grants CI jobs broader access than needed (potentially `contents: write`, `issues: write`, etc.) when they only require `contents: read`.

**Remediation**: Added top-level `permissions: {}` (deny-all default) and per-job `permissions: { contents: read }` to all three jobs (backend, frontend, docker).

---

### SEC-003: Error Message Information Leakage in OAuth Callback (Medium)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Information Disclosure |
| **Affected Component** | `backend/src/api/auth.py` — `github_callback()` |
| **OWASP** | A02:2021 — Cryptographic Failures / Sensitive Data Exposure |
| **Status** | ✅ Remediated |

**Description**: The OAuth callback error handler used `detail=str(e)` which exposed internal `ValueError` messages from the token exchange flow. These messages could contain OAuth service URLs, error codes, or internal state information.

**Remediation**: Replaced with generic `detail="Authentication failed"` message. Original exception details are now logged at WARNING level for debugging: `logger.warning("OAuth token exchange failed: %s", e)`.

---

### SEC-004: Error Message Information Leakage in Dev-Login Endpoint (Medium)

| Field | Value |
|-------|-------|
| **Severity** | Medium |
| **Category** | Information Disclosure |
| **Affected Component** | `backend/src/api/auth.py` — `dev_login()` |
| **OWASP** | A02:2021 — Cryptographic Failures / Sensitive Data Exposure |
| **Status** | ✅ Remediated |

**Description**: The dev-login error handler used `detail=f"Invalid GitHub token: {e}"` which exposed raw `httpx` exception details including request URLs, timeout values, and connection errors.

**Remediation**: Replaced with generic `detail="Authentication failed"` message. Original exception details are now logged at WARNING level: `logger.warning("Dev login failed: %s", e)`.

---

### SEC-005: Duplicated Cookie-Setting Logic (Low)

| Field | Value |
|-------|-------|
| **Severity** | Low |
| **Category** | Code Quality / DRY Principle |
| **Affected Component** | `backend/src/api/auth.py` |
| **OWASP** | N/A — Maintenance risk |
| **Status** | ✅ Remediated |

**Description**: Session cookie configuration (HttpOnly, SameSite, Secure, max_age, path) was duplicated in three locations: OAuth login callback, set_session_cookie endpoint, and dev-login endpoint. Divergence between instances could lead to inconsistent security posture.

**Remediation**: Extracted `_set_session_cookie()` shared helper function. All three endpoints now delegate to this single canonical implementation.

---

### SEC-006: Moderate Vulnerability in esbuild (Dev Dependency) (Low)

| Field | Value |
|-------|-------|
| **Severity** | Low (moderate per npm, but dev-only) |
| **Category** | Dependency Vulnerability |
| **Affected Component** | `frontend/package.json` — esbuild (via vite) |
| **Advisory** | GHSA-67mh-4wv8-2f99 |
| **Status** | ⚠️ Accepted Risk |

**Description**: esbuild <=0.24.2 has a moderate-severity vulnerability where any website can send requests to the development server and read the response. This only affects the Vite dev server (`npm run dev`), not production builds.

**Justification**: This is a development-only dependency that is never shipped to production. The vulnerability only impacts local development servers. The fix requires upgrading to vite@7.x (major breaking change). Risk is acceptable given the dev-only scope.

**Mitigation**: Developers should not expose the Vite dev server to untrusted networks.

---

### SEC-007: System-Level Python Package Vulnerabilities (Info)

| Field | Value |
|-------|-------|
| **Severity** | Info |
| **Category** | Dependency Vulnerability |
| **Affected Component** | System Python packages (not project dependencies) |
| **Status** | ℹ️ Not Applicable |

**Description**: `pip-audit` reported vulnerabilities in system-level packages (jinja2, pip, requests, setuptools, urllib3, wheel) installed in the CI runner environment. These are not direct or transitive dependencies of the project's `pyproject.toml`.

**Justification**: These packages are part of the CI runner's system Python installation, not the application's dependency tree. The application runs in Docker containers with a controlled dependency set defined in `pyproject.toml`. No action required.

---

## Verified Controls (No Issues Found)

The following areas were audited and found to be secure:

| Control | Status | Details |
|---------|--------|---------|
| **OAuth State Validation** | ✅ Strong | `secrets.token_urlsafe(32)`, 10-minute TTL, single-use `pop()`, `BoundedDict(maxlen=1000)` prevents memory exhaustion |
| **Session Cookies** | ✅ Good | `HttpOnly`, `SameSite=lax`, configurable `Secure`, 8-hour `max_age` |
| **Token Encryption at Rest** | ✅ Good | Fernet (AEAD) encryption via `EncryptionService`, startup warning when key not configured (FR-013) |
| **Admin Authorization** | ✅ Adequate | `require_admin()` dependency injection, first-user auto-promotion pattern |
| **Session Cleanup** | ✅ Good | Background task purges expired sessions every hour |
| **Webhook HMAC Verification** | ✅ Strong | `hmac.compare_digest()` timing-safe comparison |
| **Generic Exception Handler** | ✅ Good | Returns `"Internal server error"` without leaking details |
| **SQL Injection Protection** | ✅ Safe | All queries use parameterized `?` placeholders via aiosqlite |
| **XSS Prevention** | ✅ Safe | React JSX auto-escaping; no `dangerouslySetInnerHTML` usage |
| **Command Injection** | ✅ Safe | No `os.system()`, `subprocess`, or shell invocations in app code |
| **Log Sanitization** | ✅ Good | Logger uses `%s` formatting (no f-strings with user data); no credentials in log patterns |
| **Secrets Management** | ✅ Clean | `.gitignore` excludes `.env`/`.env.local`; `.env.example` has placeholders only; `docker-compose.yml` uses `${VAR}` substitution; config via `pydantic-settings` |
| **Test Fixtures** | ✅ Safe | All auth test data uses dummy values (`test-token`, `test-client-id`) |
| **Insecure Triggers** | ✅ Clean | No `pull_request_target` with head checkout patterns found |

---

## Summary

| Severity | Found | Remediated | Accepted Risk | Not Applicable |
|----------|-------|------------|---------------|----------------|
| **Critical** | 0 | 0 | 0 | 0 |
| **High** | 2 | 2 | 0 | 0 |
| **Medium** | 2 | 2 | 0 | 0 |
| **Low** | 2 | 1 | 1 | 0 |
| **Info** | 1 | 0 | 0 | 1 |
| **Total** | **7** | **5** | **1** | **1** |

**Overall Assessment**: All critical and high-severity findings have been remediated. The single accepted risk (SEC-006) is a moderate-severity vulnerability in a development-only dependency with no production impact.

---

## Recommendations for Future Enhancements

1. **Automated Secrets Scanning in CI**: Add `gitleaks` or `truffleHog` as a CI step to prevent accidental secret commits.
2. **Dependabot for SHA-Pinned Actions**: Configure Dependabot to automatically update SHA-pinned action references when new versions are released.
3. **Rate Limiting**: Add rate limiting middleware to authentication endpoints to protect against brute-force attacks.
4. **Content Security Policy**: Add CSP headers to the frontend to provide additional XSS defense-in-depth.
5. **Dependency Update Automation**: Enable Dependabot or Renovate for both Python and npm dependencies to receive automated security update PRs.
