# Security Audit Contracts

**Feature**: `012-deep-security-review`
**Date**: 2026-02-28

## Overview

This feature is a security audit and hardening effort — not an API feature. There are no new API endpoints, no new database tables, and no new user-facing contracts. Instead, the "contracts" for this feature define the **security invariants** that the codebase must satisfy after the review is complete.

## Contract 1: GitHub Actions Workflow Security

**Applies to**: `.github/workflows/ci.yml`

### Invariants

1. **Action SHA Pinning**: Every `uses:` directive referencing a third-party action MUST specify a full 40-character commit SHA.
   ```yaml
   # REQUIRED format:
   uses: actions/checkout@<40-char-sha>  # vX.Y.Z
   
   # PROHIBITED format:
   uses: actions/checkout@v4
   ```

2. **Explicit Permissions**: Every workflow MUST have a top-level `permissions` block. Every job MAY have a job-level `permissions` block that further restricts the workflow-level permissions.
   ```yaml
   permissions:
     contents: read
   ```

3. **No Insecure Triggers**: No workflow MUST use `pull_request_target` with `actions/checkout` of the PR head ref.

## Contract 2: API Error Response Safety

**Applies to**: All HTTP error responses from `backend/src/api/`

### Invariants

1. **No Exception Details in Responses**: HTTP error responses (`4xx`, `5xx`) MUST NOT contain raw exception messages, stack traces, internal file paths, or database error details.
   ```python
   # REQUIRED:
   raise HTTPException(status_code=400, detail="Authentication failed")
   
   # PROHIBITED:
   raise HTTPException(status_code=400, detail=str(e))
   ```

2. **Logging of Original Errors**: When sanitizing error responses, the original exception MUST be logged at WARNING or ERROR level for debugging purposes.

## Contract 3: Secrets Management

**Applies to**: All files in the repository

### Invariants

1. **No Hardcoded Secrets**: Zero real credentials, API keys, tokens, passwords, or private keys MUST exist in any committed file.
2. **Placeholder-Only Examples**: `.env.example` and configuration templates MUST use clearly labeled placeholder values.
3. **Gitignore Protection**: `.env`, `.env.local`, and similar files MUST be excluded via `.gitignore`.

## Contract 4: Dependency Security

**Applies to**: `backend/pyproject.toml`, `frontend/package.json`, `frontend/package-lock.json`

### Invariants

1. **No Critical/High CVEs**: Zero critical or high-severity known vulnerabilities MUST remain in the dependency tree without a documented accepted-risk justification.
2. **Audit Trail**: All dependency changes MUST be documented in the security findings report.

## Contract 5: Session and Cookie Security

**Applies to**: `backend/src/api/auth.py`, `backend/src/config.py`

### Invariants

1. **Cookie Flags**: All session cookies MUST be set with `httponly=True` and `samesite="lax"`. The `secure` flag MUST be configurable and documented.
2. **Session Expiration**: Sessions MUST expire after the configured `session_expire_hours` (default: 8 hours).
3. **Startup Warnings**: The application MUST log a warning when optional security features (encryption key, secure cookies) are not configured.
