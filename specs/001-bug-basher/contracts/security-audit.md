# Review Contract: Security Audit (P1)

**Category**: Security Vulnerabilities
**Priority**: P1 — Highest
**Scope**: All files in `backend/src/` and `frontend/src/`

## Checklist

### Authentication & Authorization
- [ ] All API endpoints require proper authentication (verify `get_current_user` dependency)
- [ ] Admin-only endpoints enforce admin authorization checks
- [ ] OAuth state parameter is validated to prevent CSRF
- [ ] Token validation rejects expired, malformed, and revoked tokens
- [ ] No endpoints accessible without intended authentication

### Input Validation
- [ ] All user-supplied inputs are validated via Pydantic models
- [ ] Path parameters are validated against expected formats
- [ ] Query parameters have type constraints and reasonable limits
- [ ] File uploads (if any) validate content type and size
- [ ] No raw user input used in database queries, file paths, or shell commands

### Secrets & Configuration
- [ ] No hardcoded secrets, tokens, or API keys in source code
- [ ] `.env.example` contains only placeholder values, not real credentials
- [ ] Encryption keys are derived securely (not hardcoded)
- [ ] Sensitive configuration values are loaded from environment variables
- [ ] No secrets logged or exposed in error responses

### Injection Prevention
- [ ] SQL/NoSQL injection: parameterized queries or ORM usage throughout
- [ ] XSS: no `dangerouslySetInnerHTML` without sanitization in frontend
- [ ] Command injection: no `os.system()`, `subprocess.call(shell=True)`, or `eval()` with user input
- [ ] Path traversal: file paths validated against directory boundaries
- [ ] SSRF: external URL fetching validates/restricts target hosts

### Insecure Defaults
- [ ] CORS configuration does not use wildcard `*` in production
- [ ] Cookie security flags (httpOnly, secure, sameSite) are set correctly
- [ ] Debug mode is not enabled by default
- [ ] Default database paths do not use predictable/writable locations without validation

## Acceptance Criteria
- All identified security vulnerabilities are fixed with regression tests
- No `str(e)` in API error responses (use static messages, log server-side)
- All fixes validated by `pytest` and `ruff check`
