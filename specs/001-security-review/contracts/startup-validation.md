# Contract: Startup Validation

**Feature**: 001-security-review | **Date**: 2026-03-11

## Overview

Defines the validation contract for application startup in production (non-debug) mode. All checks run during Pydantic `Settings` instantiation before the FastAPI application begins accepting requests.

## Validation Rules

### Rule 1: Encryption Key Required

- **Condition**: `debug == False` AND `encryption_key is None`
- **Action**: Raise `ValueError` with message including `"ENCRYPTION_KEY is required in production mode"`
- **FR Reference**: FR-003

### Rule 2: Webhook Secret Required

- **Condition**: `debug == False` AND `github_webhook_secret` is empty or None
- **Action**: Raise `ValueError` with message including `"GITHUB_WEBHOOK_SECRET is required in production mode"`
- **FR Reference**: FR-003

### Rule 3: Session Secret Minimum Length

- **Condition**: `debug == False` AND `len(session_secret_key) < 64`
- **Action**: Raise `ValueError` with message including `"SESSION_SECRET_KEY must be at least 64 characters"`
- **FR Reference**: FR-004

### Rule 4: Cookie Secure Flag

- **Condition**: `debug == False` AND `cookie_secure == False`
- **Action**: Raise `ValueError` with message including `"COOKIE_SECURE must be True in production mode"`
- **FR Reference**: FR-005

### Rule 5: CORS Origins Format

- **Condition**: `debug == False` AND any origin in `cors_origins` lacks a valid scheme (`http://` or `https://`) or hostname
- **Action**: Raise `ValueError` identifying the malformed origin
- **FR Reference**: FR-015

## Behavior in Debug Mode

- All validation rules are skipped when `debug == True`
- Warnings are logged for missing values to aid local development
- This allows developers to run the application with minimal configuration

## Error Format

When multiple violations exist, they are combined into a single `ValueError`:

```text
Production security validation failed:

  - ENCRYPTION_KEY is required in production mode
  - SESSION_SECRET_KEY must be at least 64 characters (got 32)
  - COOKIE_SECURE must be True in production mode
```

## Test Contract

| # | Input | Expected |
|---|-------|----------|
| 1 | `debug=False`, `encryption_key=None` | Startup fails with encryption key error |
| 2 | `debug=False`, `session_secret_key="short"` | Startup fails with key length error |
| 3 | `debug=False`, `cookie_secure=False` | Startup fails with cookie secure error |
| 4 | `debug=False`, `cors_origins="not-a-url"` | Startup fails with CORS format error |
| 5 | `debug=False`, all values valid | Startup succeeds |
| 6 | `debug=True`, `encryption_key=None` | Startup succeeds (debug mode skips checks) |
| 7 | `debug=False`, multiple violations | Error message lists all violations |
