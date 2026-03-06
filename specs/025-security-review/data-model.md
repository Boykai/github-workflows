# Data Model: Security, Privacy & Vulnerability Audit

**Branch**: `025-security-review` | **Date**: 2026-03-06

## Overview

This feature does not introduce new database tables or fundamentally change the data architecture. It modifies how existing entities are secured, validated, and accessed. This document maps the security-relevant entities and their changed behaviors.

## Entity: Session (Modified)

**What it represents**: An authenticated user's session, now delivered exclusively via HttpOnly cookie (previously also via URL parameter).

**Current state**:
- Created in `auth.py` OAuth callback
- Delivered via both URL query parameter AND cookie
- Cookie attributes: HttpOnly=true, Secure=effective_cookie_secure, SameSite=lax

**Target state**:
- Delivered exclusively via HttpOnly cookie on the callback response
- Cookie attributes: HttpOnly=true, Secure=true (enforced), SameSite=strict
- No credentials in redirect URLs

**Validation rules**:
- SESSION_SECRET_KEY must be ≥64 characters (startup enforcement)
- cookie_secure must be true in non-debug mode (startup enforcement)

**State transitions**:
- `OAuth callback` → cookie set on redirect response → `Authenticated`
- `Logout` → cookie cleared → `Unauthenticated`
- `Session expired` (8h TTL) → `Unauthenticated`

## Entity: Configuration (Modified)

**What it represents**: The set of environment variables validated at startup. Gains mandatory security checks.

**New validation rules (non-debug mode)**:

| Field | Validation | Error on Failure |
|-------|-----------|-----------------|
| `ENCRYPTION_KEY` | Must be set and non-empty | Startup refuses with explicit error |
| `GITHUB_WEBHOOK_SECRET` | Must be set and non-empty | Startup refuses with explicit error |
| `SESSION_SECRET_KEY` | Must be ≥64 characters | Startup refuses with length error |
| `cookie_secure` / `effective_cookie_secure` | Must be true | Startup refuses with config error |
| `CORS_ORIGINS` | Each origin must be well-formed URL with scheme + hostname | Startup refuses identifying invalid origin |
| `ENABLE_DOCS` | New field (bool, default=false) | Controls Swagger/ReDoc independently of DEBUG |

**State transitions**:
- `Environment loaded` → validators run → `Valid` (app starts) or `Invalid` (app exits with error)

## Entity: Project Authorization (New Dependency)

**What it represents**: A centralized FastAPI dependency that verifies the authenticated user has access to the target project before any operation.

**Key attributes**:
- Input: `project_id` (from path/query/body), `session` (from auth middleware)
- Output: Verified project context or 403 Forbidden

**Relationships**:
- Injected into: `tasks.py`, `projects.py`, `settings.py`, `workflow.py` endpoint handlers
- Depends on: Session middleware (provides authenticated user identity)
- Depends on: GitHub API (verifies user has access to the project)

**Validation rules**:
- Authenticated user must own or have been granted access to the project
- Check runs before any endpoint logic executes
- WebSocket connections validated before any data is sent

## Entity: Rate Limit State (New)

**What it represents**: Per-user and per-IP counters for rate-limited endpoints.

**Key attributes**:
- `key`: User ID (for per-user limits) or IP address (for per-IP limits)
- `endpoint`: The rate-limited endpoint path
- `count`: Number of requests in the current window
- `window`: Sliding time window (e.g., 1 minute)
- `limit`: Maximum allowed requests per window

**Storage**: In-memory via slowapi's default storage (sufficient for single-instance deployment).

**Relationships**:
- Applied to: `chat.py`, `agents.py`, `workflow.py` (per-user), `auth.py` OAuth callback (per-IP)

**State transitions**:
- `Request received` → counter incremented → `Under limit` (request proceeds) or `Over limit` (429 returned)
- `Window expires` → counter resets → `Under limit`

**Note**: Rate limit state is lost on application restart. This is acceptable per the spec's edge case acknowledgment — rate limits reset on restart.

## Entity: Chat Reference (Modified)

**What it represents**: A lightweight local storage entry replacing full message content storage in the browser.

**Current state**:
- localStorage key: `chat-message-history`
- Value: Array of full message content strings (up to 100)
- Lifetime: Indefinite (survives logout)

**Target state**:
- localStorage key: `chat-message-history`
- Value: Array of `{ id: string, timestamp: number }` references
- TTL: Configurable (e.g., 24 hours); entries pruned on access
- Lifetime: Cleared on logout

**Validation rules**:
- Only message IDs stored locally, never full content
- Content loaded on-demand from backend API
- All entries cleared when user logs out
- Expired entries (past TTL) pruned automatically

## Entity: Encryption Service (Modified)

**What it represents**: The Fernet-based encryption/decryption service for OAuth tokens at rest.

**Current state**:
- ENCRYPTION_KEY optional; plaintext passthrough when absent
- Legacy plaintext detection by token prefix (`gho_`, `ghp_`, etc.)

**Target state**:
- ENCRYPTION_KEY mandatory in non-debug mode (enforced at startup)
- Plaintext passthrough removed from encrypt() path
- Legacy plaintext detection retained in decrypt() for migration of existing rows
- One-time migration: startup or manual script encrypts any remaining plaintext rows

**State transitions**:
- `Startup (non-debug)` → ENCRYPTION_KEY validated → `Ready`
- `Startup (debug)` → ENCRYPTION_KEY optional (warning if absent) → `Ready (degraded)`
- `encrypt(token)` → always returns Fernet-encrypted ciphertext
- `decrypt(ciphertext)` → detects legacy plaintext → returns plaintext (logs migration warning)
