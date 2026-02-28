# Data Model: Deep Security Review of GitHub Workflows App

**Feature**: 012-deep-security-review
**Date**: 2026-02-28

## Overview

This security review does not introduce new persistent data entities. Instead, it defines **security-relevant domain concepts** that guide the audit and remediation work, and documents the existing data model elements that have security implications.

## Security Entities

### Security Finding

Represents a discovered vulnerability or security weakness during the audit.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | string | Unique identifier (e.g., `SF-001`) | Format: `SF-NNN` |
| `title` | string | Short description of the finding | Required, max 200 chars |
| `severity` | enum | Risk classification | `critical`, `high`, `medium`, `low` |
| `category` | string | OWASP category or security domain | Required |
| `location` | string | File path and line numbers | Required |
| `description` | string | Detailed explanation of the vulnerability | Required |
| `remediation_status` | enum | Current fix status | `open`, `in_progress`, `remediated`, `accepted_risk` |
| `remediation_steps` | string | Actions taken or recommended | Required when status ≠ `open` |

**Note**: Security findings are tracked in the security review report document, not in a database.

---

### Shared Security Utility

Represents a reusable security module created by consolidating duplicated logic.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `module_name` | string | Python module name | Valid Python identifier |
| `location` | string | File path | Under `backend/src/services/security/` |
| `functions` | list[string] | Exported function names | At least one function |
| `replaces` | list[string] | Locations of duplicated code being replaced | At least one location |
| `test_file` | string | Path to test file | Under `backend/tests/test_security/` |

---

## Existing Data Model — Security Implications

### Session (in `session_store.py`)

| Field | Security Concern | Recommendation |
|-------|-----------------|----------------|
| `session_id` | Primary authentication token; stored as cookie | Ensure `httponly`, `secure`, `samesite` flags |
| `github_token` | GitHub API access token | **Must be encrypted** (currently optional) |
| `user_data` | JSON blob with user profile | Avoid storing sensitive fields beyond what's needed |
| `expires_at` | Session expiry timestamp | Enforce max 8-hour TTL; no indefinite sessions |

### Encryption Key (in `config.py`)

| Field | Security Concern | Recommendation |
|-------|-----------------|----------------|
| `ENCRYPTION_KEY` | Fernet key for token encryption | **Must be mandatory** in production (currently optional) |
| `SESSION_SECRET_KEY` | Cookie signing key | Must be cryptographically random; no default value |

### OAuth State (in `github_auth.py`)

| Field | Security Concern | Recommendation |
|-------|-----------------|----------------|
| `_pending_states` | In-memory CSRF protection for OAuth flow | 10-minute TTL is appropriate; bounded to 1000 entries ✓ |

---

## State Transitions

### Security Finding Lifecycle

```
[open] → [in_progress] → [remediated]
  │                           │
  └──→ [accepted_risk] ←─────┘
```

- **open**: Finding documented but not yet addressed
- **in_progress**: Remediation work underway
- **remediated**: Fix applied and verified
- **accepted_risk**: Finding acknowledged with documented justification for not fixing

### Session Security States

```
[created] → [active] → [expired] → [purged]
                │
                └──→ [revoked] → [purged]
```

- Tokens must be encrypted at every state except `purged`
- Session purge cleans both session record and associated encrypted tokens

## Relationships

```
Session ──has── EncryptedGitHubToken (1:1)
Session ──belongs_to── User (N:1)
User ──has── AdminRole (0..1)
WorkflowFile ──references── GitHubAction (1:N)
GitHubAction ──pinned_to── SHA (1:1, target state)
```
