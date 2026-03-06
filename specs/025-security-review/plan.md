# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `025-security-review` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/025-security-review/spec.md`

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across OWASP Top 10 categories. Changes span the full stack: backend Python/FastAPI (session management, encryption enforcement, config validation, access control, rate limiting, webhook hardening), frontend React/TypeScript (credential handling, localStorage privacy, avatar validation), infrastructure (Dockerfile non-root, nginx headers, Docker Compose network binding), and CI (workflow permissions). Phased by severity — Critical fixes block deployment; High fixes ship within one week; Medium in the next sprint; Low in the backlog.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.9 (frontend), Node 22 (build)
**Primary Dependencies**: FastAPI ≥0.135.0, React 19, Vite 7, pydantic-settings, aiosqlite, Fernet (cryptography), slowapi (NEW — rate limiting)
**Storage**: SQLite via aiosqlite with WAL mode — sessions, settings, encrypted tokens
**Testing**: pytest + pytest-asyncio (backend, ~1411 tests), Vitest + Playwright (frontend)
**Target Platform**: Docker Compose (Linux containers), nginx reverse proxy
**Project Type**: Web application (backend/ + frontend/)
**Performance Goals**: Rate-limited endpoints must respond with 429 within 1 second of exceeding threshold; startup validation must complete within 5 seconds
**Constraints**: All existing tests must pass; zero breaking changes to API response shapes for non-security endpoints; migration path required for existing plaintext token rows
**Scale/Scope**: ~15 backend source files modified, ~5 frontend files modified, 3 infrastructure files modified, 1 CI workflow modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS
Feature work began with explicit specification (spec.md) containing 12 prioritized user stories (P1–P4), Given-When-Then acceptance scenarios for each, clear scope boundaries, edge cases, and out-of-scope declarations.

### II. Template-Driven Workflow — PASS
All artifacts follow canonical templates: spec.md from spec-template, plan.md from plan-template. No custom sections added.

### III. Agent-Orchestrated Execution — PASS
Workflow follows the specify → plan → tasks → implement sequence. Each phase produces specific outputs and hands off to the next agent.

### IV. Test Optionality with Clarity — PASS
The spec mandates behavior-based verification checks (10 items in the audit) and measurable success criteria. Existing test suites serve as regression gates. New tests are warranted for security-critical paths (startup validation, access control, rate limiting) as called for in the spec's acceptance scenarios.

### V. Simplicity and DRY — PASS
Changes are scoped to security remediation with minimal architectural impact. The centralized project authorization dependency (FR-007) follows DRY by replacing per-endpoint duplication. Rate limiting uses an existing library (slowapi) rather than custom implementation. No premature abstractions.

**GATE RESULT: ALL PASS — proceed to Phase 0.**

### Post-Design Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Spec complete; plan artifacts (research, data-model, contracts, quickstart) all generated |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | specify → plan → tasks → implement pipeline followed |
| IV. Test Optionality | ✅ PASS | New tests warranted for security-critical paths per spec acceptance scenarios |
| V. Simplicity and DRY | ✅ PASS | Centralized auth dependency eliminates per-endpoint duplication; slowapi reuses existing library pattern; config validation consolidates startup checks |

**Post-design gate result**: PASS — no violations or complexity additions to justify.

## Project Structure

### Documentation (this feature)

```text
specs/025-security-review/
├── plan.md              # This file
├── research.md          # Phase 0: security research & decisions
├── data-model.md        # Phase 1: security entity model
├── quickstart.md        # Phase 1: verification commands
├── contracts/           # Phase 1: config & API contracts
│   └── security-contracts.md
├── checklists/
│   └── requirements.md  # Quality checklist (completed)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml              # Add slowapi dependency
├── src/
│   ├── config.py               # Startup validation: ENCRYPTION_KEY, GITHUB_WEBHOOK_SECRET,
│   │                           #   SESSION_SECRET_KEY min-length, cookie_secure enforcement,
│   │                           #   CORS origins validation, ENABLE_DOCS env var
│   ├── main.py                 # ENABLE_DOCS gating (decouple from DEBUG)
│   ├── dependencies.py         # Centralized project authorization dependency
│   ├── api/
│   │   ├── auth.py             # Cookie-based session delivery (remove URL token),
│   │   │                       #   POST body for dev-login
│   │   ├── tasks.py            # Add project auth dependency
│   │   ├── projects.py         # Add project auth dependency
│   │   ├── settings.py         # Add project auth dependency
│   │   ├── workflow.py         # Add project auth dependency + rate limiting
│   │   ├── chat.py             # Rate limiting
│   │   ├── agents.py           # Rate limiting
│   │   ├── signal.py           # hmac.compare_digest for secret comparison
│   │   └── webhooks.py         # Remove debug-mode bypass for signature verification
│   └── services/
│       ├── encryption.py       # Remove plaintext fallback (mandatory encryption)
│       ├── database.py         # 0700 directory, 0600 file permissions
│       ├── github_auth.py      # Narrow OAuth scopes (remove repo)
│       └── github_projects/
│           └── service.py      # Sanitize GraphQL error messages
└── tests/                      # Regression gate + new security tests

frontend/
├── Dockerfile                  # Add non-root USER directive
├── nginx.conf                  # Add CSP, HSTS, Referrer-Policy, Permissions-Policy;
│                               #   remove X-XSS-Protection; add server_tokens off
├── src/
│   ├── hooks/
│   │   ├── useAuth.ts          # Remove URL token reading; cookie-only auth
│   │   └── useChatHistory.ts   # Store only message IDs with TTL; clear on logout
│   └── components/
│       └── board/
│           └── IssueCard.tsx   # Avatar URL domain validation + fallback

docker-compose.yml              # Bind to 127.0.0.1; move data volume outside /app

.github/
└── workflows/
    └── branch-issue-link.yml   # Scope permissions with justification comment
```

**Structure Decision**: Web application layout (backend/ + frontend/). No new directories created. All changes are in-place modifications to existing files. One new FastAPI dependency (slowapi) added for rate limiting. One new shared dependency function added to `dependencies.py` for project authorization.

## Complexity Tracking

> No constitution violations. No complexity justification needed.
