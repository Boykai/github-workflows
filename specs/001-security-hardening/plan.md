# Implementation Plan: Phase 4 — Security Hardening

**Branch**: `001-security-hardening` | **Date**: 2026-03-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-security-hardening/spec.md`

## Summary

Harden the Solune application's security posture across five areas: make token encryption mandatory with key rotation support (MultiFernet), add session revocation API with immediate invalidation, implement TTL-based webhook deduplication (60-minute window), validate OAuth scopes at login, and upgrade the CSRF cookie from SameSite=Lax to Strict.

## Technical Context

**Language/Version**: Python 3.13 (target), ≥3.12 (minimum) — backend; TypeScript/React 19 — frontend  
**Primary Dependencies**: FastAPI, Pydantic, cryptography (Fernet/MultiFernet), aiosqlite, githubkit  
**Storage**: SQLite via aiosqlite (single-instance architecture)  
**Testing**: pytest (asyncio mode), Vitest (frontend)  
**Target Platform**: Linux server (Docker), single-instance deployment  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: API responses <1s; session revocation effective within 1s  
**Constraints**: Single-instance (no Redis/external cache); SQLite-only; no breaking changes to existing OAuth flow  
**Scale/Scope**: Single-tenant, <100 concurrent users; 5 security hardening items in this phase

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ Pass | spec.md completed with 5 prioritized user stories, GWT scenarios, edge cases |
| II. Template-Driven | ✅ Pass | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ Pass | speckit.specify → speckit.plan → speckit.tasks pipeline |
| IV. Test Optionality | ✅ Pass | Tests not explicitly mandated in spec; existing test suite covers security patterns |
| V. Simplicity & DRY | ✅ Pass | Uses existing libraries (MultiFernet, BoundedDict), extends existing patterns; no new abstractions beyond what's needed |

**Post-Phase-1 Re-check**:

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ Pass | All design decisions traced to spec requirements (FR-001–FR-022) |
| II. Template-Driven | ✅ Pass | research.md, data-model.md, contracts/, quickstart.md follow patterns |
| III. Agent-Orchestrated | ✅ Pass | Clear handoff artifacts for speckit.tasks |
| IV. Test Optionality | ✅ Pass | No test mandate; existing tests provide regression safety |
| V. Simplicity & DRY | ✅ Pass | Reuses MultiFernet (no custom crypto), extends existing BoundedDict (no new data structures), adds column to existing table (no new tables) |

## Project Structure

### Documentation (this feature)

```text
specs/001-security-hardening/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file
├── research.md          # Phase 0 output — technical decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — verification guide
├── contracts/
│   └── api.md           # Phase 1 output — API contract changes
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py              # Modified: session revocation endpoints, scope error redirect
│   │   │   └── webhooks.py          # Modified: TTL-based deduplication
│   │   ├── middleware/
│   │   │   └── csrf.py              # Modified: SameSite=Strict on CSRF cookie
│   │   ├── services/
│   │   │   ├── encryption.py        # Modified: MultiFernet, remove passthrough
│   │   │   ├── session_store.py     # Modified: revocation check, revoke functions
│   │   │   └── github_auth.py       # Modified: scope validation post-token-exchange
│   │   ├── models/
│   │   │   └── user.py              # Unchanged (UserSession model)
│   │   ├── migrations/
│   │   │   └── 034_session_revocation.sql  # New: revoked_at column + index
│   │   ├── config.py                # Modified: encryption_key mandatory
│   │   └── utils.py                 # Potentially extended: TTLBoundedDict
│   └── tests/
│       └── unit/
│           ├── test_token_encryption.py   # Existing: update for MultiFernet
│           ├── test_session_store.py      # Existing: add revocation tests
│           ├── test_webhooks.py           # Existing: add TTL dedup tests
│           ├── test_auth_security.py      # Existing: add scope validation tests
│           └── test_csrf.py              # Existing: verify Strict attribute
└── frontend/
    └── src/
        ├── pages/                    # Modified: handle scope error on /auth/callback
        └── components/auth/          # Modified: display scope error message
```

**Structure Decision**: Web application — existing `solune/backend/` and `solune/frontend/` structure. No new directories or projects needed; all changes are modifications to existing files plus one new migration file.

## Complexity Tracking

No constitution violations — no complexity justification needed.

| Item | Approach | Why Simple |
|------|----------|------------|
| 4.1 Encryption | MultiFernet (stdlib pattern) | Built-in to `cryptography` library; replaces custom code |
| 4.2 Revocation | Column on existing table | No new tables, no JOINs, single-query check |
| 4.3 Dedup | In-memory dict with TTL | Matches existing `BoundedSet` pattern; no external deps |
| 4.5 Scopes | String set comparison | 5-line validation after existing token exchange |
| 4.7 CSRF | One-line cookie attribute change | `"lax"` → `"strict"` |
