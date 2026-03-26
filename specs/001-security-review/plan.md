# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Comprehensive security audit addressing 21 findings across OWASP Top 10 categories (3 Critical, 7 High, 9 Medium, 2 Low). Codebase analysis reveals **17 of 21 findings are already remediated** in the current codebase. The remaining work focuses on: documenting the justified OAuth scope exception, verifying completeness of rate-limiting coverage across all sensitive endpoints, and ensuring end-to-end behavioral verification of all security controls.

## Technical Context

**Language/Version**: Python ≥3.12 (pyright target 3.13) (backend), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI, slowapi, aiosqlite, cryptography (Fernet), React 19.2, nginx (Alpine)
**Storage**: SQLite via aiosqlite with Fernet encryption at rest
**Testing**: pytest (3575 unit tests), Vitest (frontend), ruff/pyright/bandit (linting)
**Target Platform**: Linux containers (Docker Compose), nginx reverse proxy
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limiting at 10 req/min on AI/chat endpoints; sub-200ms p95 on auth flows
**Constraints**: All containers non-root; mandatory encryption in production; localhost-only port binding
**Scale/Scope**: ~132 backend source files, ~413 frontend TS/TSX files, 33 services, 21 API routes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Specification-First** | ✅ PASS | `spec.md` contains 15 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Single-responsibility: speckit.specify → speckit.plan → speckit.tasks → speckit.implement |
| **IV. Test Optionality** | ✅ PASS | Tests not mandated by spec; behavioral verification checklist provided instead (code review + integration inspection) |
| **V. Simplicity / DRY** | ✅ PASS | Security fixes target existing code patterns; no new abstractions introduced. `verify_project_access` is already centralized as a shared dependency |

**Gate Result**: ✅ ALL PASS — Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file
├── research.md          # Phase 0: Codebase audit findings and remediation status
├── data-model.md        # Phase 1: Security-relevant entities and state transitions
├── quickstart.md        # Phase 1: Verification guide for all security controls
├── contracts/           # Phase 1: Security-hardened API contract amendments
│   └── security-headers.md
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py            # FR-001, FR-002, FR-013: OAuth flow, session cookies, dev-login
│   │   │   ├── chat.py            # FR-017: Rate-limited AI chat endpoint
│   │   │   ├── agents.py          # FR-017: Rate-limited agent invocation
│   │   │   ├── tasks.py           # FR-006: Project-scoped task creation
│   │   │   ├── projects.py        # FR-006: Project access control
│   │   │   ├── settings.py        # FR-006: Project-scoped settings
│   │   │   ├── workflow.py        # FR-006, FR-017: Project-scoped, rate-limited workflows
│   │   │   ├── signal.py          # FR-009: Constant-time webhook secret comparison
│   │   │   └── webhooks.py        # FR-009, FR-020: Webhook verification (no debug bypass)
│   │   ├── services/
│   │   │   ├── github_auth.py     # FR-014: OAuth scopes configuration
│   │   │   ├── encryption.py      # FR-003: Fernet encryption with mandatory key
│   │   │   ├── database.py        # FR-022: Directory/file permissions (0700/0600)
│   │   │   └── service.py         # FR-028: Error sanitization
│   │   ├── middleware/
│   │   │   ├── rate_limit.py      # FR-017, FR-018: slowapi rate limiter
│   │   │   └── csrf.py            # CSRF double-submit cookie protection
│   │   ├── config.py              # FR-003, FR-004, FR-015, FR-019, FR-023: Production validation
│   │   ├── dependencies.py        # FR-006, FR-007: Centralized verify_project_access
│   │   └── main.py                # FR-021: ENABLE_DOCS independent of DEBUG
│   └── tests/
│       ├── unit/                  # 144 unit test files
│       └── integration/           # 15 integration test files
├── frontend/
│   ├── Dockerfile                 # FR-005: Non-root nginx-app user
│   ├── nginx.conf                 # FR-010, FR-011, FR-012: Security headers
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useAuth.ts         # FR-002: No credential reading from URL params
│   │   │   └── useChatHistory.ts  # FR-025, FR-026, FR-027: Memory-only chat, logout cleanup
│   │   └── components/
│   │       └── IssueCard.tsx      # FR-030: Avatar URL validation (HTTPS + allowlist)
│   └── tests/                     # 152 test files
├── docker-compose.yml             # FR-016, FR-024: Localhost binding, external data volume
└── .github/workflows/
    └── branch-issue-link.yml      # FR-029: Scoped permissions with justification
```

**Structure Decision**: Existing web application structure (backend + frontend) with changes scoped to existing files. No new directories or architectural changes required.

## Complexity Tracking

> No constitution violations detected. All changes target existing code and patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *None* | — | — |
