# Implementation Plan: Deep Security Review of GitHub Workflows App

**Branch**: `012-deep-security-review` | **Date**: 2026-02-28 | **Spec**: `specs/012-deep-security-review/spec.md`
**Input**: Feature specification from `/specs/012-deep-security-review/spec.md`

## Summary

Perform a comprehensive security audit of the GitHub Workflows application covering authentication/authorization, input handling, secrets management, dependency security, GitHub Actions hardening, CORS/HTTP headers, and security logic consolidation. The review follows the OWASP Top 10 and GitHub Actions security hardening guidelines. Identified vulnerabilities will be remediated, duplicated security logic consolidated into shared utilities, and a final security report produced.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.4 (frontend)
**Primary Dependencies**: FastAPI, Uvicorn, python-jose, Pydantic, aiosqlite (backend); React 18.3, Vite, Radix UI, TanStack Query (frontend)
**Storage**: SQLite via aiosqlite (`/app/data/settings.db`)
**Testing**: pytest + pytest-asyncio + pytest-cov (backend); Vitest + Playwright + @testing-library/react (frontend)
**Target Platform**: Linux server (Docker), web browser (frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: N/A — security review does not change performance targets
**Constraints**: All changes must maintain backward compatibility (FR-013); zero critical/high-severity vulnerabilities post-remediation (SC-001)
**Scale/Scope**: ~50 backend source files, ~80 frontend source files, 1 CI workflow file, 1 docker-compose config

### Security Landscape (from codebase analysis)

| Area | Current State | Risk Level |
|------|--------------|------------|
| **Authentication** | GitHub OAuth 2.0 with session cookies; dev-login bypass in debug mode | Medium |
| **Session Management** | DB-backed sessions with 8h TTL, lazy expiry | Low |
| **Encryption** | Fernet encryption for tokens — but **optional** (plaintext fallback) | **Critical** |
| **CORS** | Wildcard `allow_methods=["*"]`, `allow_headers=["*"]` with credentials | **High** |
| **GitHub Actions** | Single ci.yml — actions use floating version tags, no permissions block | **Critical** |
| **Webhook Security** | HMAC-SHA256 verification — bypassed in debug mode | Medium |
| **Rate Limiting** | RateLimitError handler exists but **no enforcement middleware** | **High** |
| **Secrets Management** | .env.example with placeholders; no hardcoded secrets detected in source | Low |
| **Dependencies** | Not yet audited for known CVEs | Unknown |
| **Input Validation** | Pydantic models for API; webhook payloads lack schema validation | Medium |
| **Admin Promotion** | First authenticated user auto-promoted to admin | **High** |
| **HTTP Security Headers** | No security headers middleware (CSP, HSTS, X-Frame-Options, etc.) | **High** |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I — Specification-First Development ✅ PASS
- Feature spec (`spec.md`) exists with 6 prioritized user stories (P1–P3)
- Given-When-Then acceptance scenarios defined for each story
- Edge cases documented

### Principle II — Template-Driven Workflow ✅ PASS
- Plan follows canonical `plan-template.md` structure
- All artifacts will be generated to the prescribed directory layout

### Principle III — Agent-Orchestrated Execution ✅ PASS
- This plan is produced by the `speckit.plan` agent with clear inputs/outputs
- Handoff to `speckit.tasks` for Phase 2 is defined

### Principle IV — Test Optionality with Clarity ✅ PASS
- Spec explicitly requires tests for shared security utilities (FR-014)
- Tests are mandated only where the spec requires them (security utility consolidation)
- No blanket test requirement imposed

### Principle V — Simplicity and DRY ✅ PASS
- Security logic consolidation (User Story 5) directly serves the DRY principle
- No premature abstractions; consolidation targets identified duplicated patterns only
- Complexity tracking section below is empty (no violations)

### Gate Result: **PASS** — Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/012-deep-security-review/
├── plan.md              # This file
├── research.md          # Phase 0: security research findings
├── data-model.md        # Phase 1: security entity definitions
├── quickstart.md        # Phase 1: getting started with security changes
├── contracts/           # Phase 1: API security contracts
│   └── security-api.yaml
├── checklists/          # Pre-existing requirement checklist
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── auth.py              # OAuth authentication endpoints
│   │   ├── webhooks.py          # GitHub webhook handlers
│   │   ├── projects.py          # Project CRUD
│   │   ├── tasks.py             # Task management
│   │   ├── chat.py              # Chat messaging
│   │   └── workflow.py          # Workflow recommendations
│   ├── middleware/
│   │   ├── request_id.py        # Request ID middleware
│   │   ├── rate_limit.py        # [NEW] Rate limiting middleware
│   │   └── security_headers.py  # [NEW] HTTP security headers
│   ├── services/
│   │   ├── encryption.py        # Token encryption service
│   │   ├── session_store.py     # Session management
│   │   ├── github_auth.py       # GitHub OAuth service
│   │   └── security/            # [NEW] Shared security utilities
│   │       ├── __init__.py
│   │       ├── input_sanitizer.py
│   │       ├── auth_helpers.py
│   │       └── validators.py
│   ├── config.py                # Application configuration
│   ├── dependencies.py          # FastAPI dependency injection
│   └── main.py                  # Application entry point + CORS
└── tests/
    ├── test_security/           # [NEW] Security utility tests
    │   ├── test_input_sanitizer.py
    │   ├── test_auth_helpers.py
    │   └── test_validators.py
    └── ...

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

.github/
└── workflows/
    └── ci.yml                   # CI pipeline (actions to be pinned)
```

**Structure Decision**: Web application structure (Option 2). Backend and frontend are separate projects under `backend/` and `frontend/` directories. New security utilities are added under `backend/src/services/security/`. New middleware components go in `backend/src/middleware/`. Security tests go in `backend/tests/test_security/`.

## Constitution Check — Post-Design Re-evaluation

*Re-check after Phase 1 design artifacts are complete.*

### Principle I — Specification-First Development ✅ PASS
- All design artifacts trace back to spec.md user stories and functional requirements
- Research findings (research.md) map to specific spec requirements (FR-001 through FR-014)

### Principle II — Template-Driven Workflow ✅ PASS
- plan.md follows canonical template structure
- research.md, data-model.md, contracts/, quickstart.md all generated per workflow

### Principle III — Agent-Orchestrated Execution ✅ PASS
- Phase 0 (research) and Phase 1 (design) complete
- Clear handoff to `speckit.tasks` for Phase 2 task decomposition

### Principle IV — Test Optionality with Clarity ✅ PASS
- Tests mandated only for shared security utilities (FR-014 from spec)
- Test structure defined in project structure (`backend/tests/test_security/`)
- No unnecessary test overhead for audit/documentation tasks

### Principle V — Simplicity and DRY ✅ PASS
- Security logic consolidation (User Story 5) directly serves DRY principle
- New middleware components (rate_limit.py, security_headers.py) are simple, single-purpose
- No premature abstractions; shared utilities target only verified duplicated patterns

### Post-Design Gate Result: **PASS** — Ready for Phase 2 (tasks generation)

## Complexity Tracking

> No constitution violations detected. This section is intentionally empty.
