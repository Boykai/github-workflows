# Security Review Contract

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Version**: 1.0
**Priority**: P1 — Highest priority, reviewed first

## Purpose

Defines the process for identifying and remediating security vulnerabilities across the Solune codebase. This contract governs User Story 1 (Security Vulnerability Remediation) and covers: authentication/authorization bypasses, injection risks, secrets/tokens in code or config, insecure defaults, and improper input validation.

## Input: File Scope

Security-critical files to review in order:

1. **Configuration files**: `solune/backend/src/config.py`, `solune/.env.example`, `docker-compose.yml`, `solune/docker-compose.yml`, `solune/guard-config.yml`
2. **Authentication/Authorization**: `solune/backend/src/api/auth.py`, `solune/backend/src/middleware/admin_guard.py`, `solune/backend/src/services/guard_service.py`, `solune/backend/src/services/session_store.py`
3. **API route handlers**: All files in `solune/backend/src/api/` — check each for auth dependency injection
4. **Input-accepting endpoints**: All API routes with request bodies or path parameters
5. **File system operations**: `solune/backend/src/services/app_service.py` (has `_safe_app_path` pattern), any file using `Path()`, `open()`, or `os.*` with user-influenced inputs
6. **Encryption/Secrets**: `solune/backend/src/services/encryption.py`
7. **Middleware**: `solune/backend/src/middleware/csp.py`, `solune/backend/src/middleware/rate_limit.py`
8. **Frontend auth**: `solune/frontend/src/components/auth/`, `solune/frontend/src/hooks/useAuth.ts`

## Check Categories

### S1: Hardcoded Secrets

**Pattern**: Search for hardcoded API keys, tokens, passwords, or secret strings in source code or configuration.

**Detection**:
```bash
# Search for common secret patterns
grep -rn "password\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
grep -rn "token\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
grep -rn "secret\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
grep -rn "api_key\s*=\s*['\"]" solune/backend/src/ solune/frontend/src/
```

**Fix pattern**: Replace with environment variable reference (`os.environ["KEY"]` or `config.KEY`).

**Regression test**: Assert the secret value is not present in source code; assert the configuration reads from environment.

### S2: Authentication Bypass

**Pattern**: API routes missing authentication dependency injection or guard checks.

**Detection**: Compare each route handler's dependencies against the auth patterns established in `api/auth.py`. Routes handling sensitive operations (CRUD, state changes) must include auth dependency.

**Fix pattern**: Add missing auth dependency to route handler parameters.

**Regression test**: Call the endpoint without auth credentials and assert 401/403 response.

### S3: Injection Risks

**Pattern**: User input concatenated into SQL queries, shell commands, or template strings without sanitization.

**Detection**:
- SQL: Search for f-strings or `.format()` containing SQL keywords near database operations
- Command: Search for `subprocess`, `os.system`, `os.popen` with variable arguments
- Template: Search for user input flowing into prompt templates without escaping

**Fix pattern**: Use parameterized queries (SQLAlchemy), `shlex.quote()` for commands, or explicit input sanitization.

**Regression test**: Pass malicious input (e.g., SQL injection string, shell metacharacters) and assert it's rejected or safely handled.

### S4: Insecure Defaults

**Pattern**: Debug mode, permissive CORS, disabled security checks, or overly broad permissions in configuration.

**Detection**: Review `config.py` for default values, `main.py` for middleware configuration, Docker files for exposed ports and debug flags.

**Fix pattern**: Change defaults to secure values; add environment-based toggling for development-only features.

**Regression test**: Assert production configuration uses secure defaults.

### S5: Input Validation

**Pattern**: API endpoints accepting user input without Pydantic model validation or explicit sanitization.

**Detection**: Review each API route for request body/parameter types. Endpoints accepting `str` or `dict` without Pydantic models are suspect.

**Fix pattern**: Add Pydantic model validation or explicit input validation.

**Regression test**: Pass malformed or oversized input and assert appropriate error response.

## Output

For each finding, produce:
- A BugReportEntry with `category: security`
- A code fix (if obvious) or TodoComment (if ambiguous)
- A regression test (if fixed)
- A commit with `fix(security): <description>` message format

## Completion Criteria

- All security-critical files reviewed
- No hardcoded secrets remain in source
- All sensitive routes have authentication checks
- No raw SQL concatenation or unescaped command injection vectors
- All configuration defaults are secure for production
- All input-accepting endpoints validate their inputs
