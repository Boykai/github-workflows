# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `037-security-review` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/037-security-review/spec.md`

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across the OWASP Top 10 categories. The audit spans the full-stack application: Python/FastAPI backend, React/TypeScript frontend, nginx reverse proxy, Docker deployment, and GitHub Actions CI/CD. Changes are phased by severity — Critical fixes (credential leakage, encryption enforcement, non-root containers) land first, followed by access control and header hardening (High), then defense-in-depth measures (Medium), and finally supply-chain/cosmetic fixes (Low). Each finding maps to specific files and has a behavior-based verification check defined in the specification.

## Technical Context

**Language/Version**: Python 3.13 (backend, floor ≥3.12), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, httpx, slowapi (backend); React 19.2, TanStack React Query 5.90 (frontend); nginx (reverse proxy)
**Storage**: aiosqlite (SQLite with application-level encryption via `encryption.py`)
**Testing**: pytest (backend, 1736+ unit tests), Vitest 4.0 (frontend, 644+ tests)
**Target Platform**: Linux server (backend API + nginx), browser (frontend SPA), Docker containers
**Project Type**: Web application (frontend + backend)
**Performance Goals**: No performance regressions from security hardening; rate limiting thresholds tuned to observed usage patterns
**Constraints**: Must not break existing OAuth flows during scope narrowing; encryption enforcement requires migration path for existing plaintext data; CSP headers must not break existing frontend behavior
**Scale/Scope**: 21 findings across ~25 files; 25 functional requirements (FR-001–FR-025); 10 behavior-based verification checks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Full spec exists at `specs/037-security-review/spec.md` with 10 prioritized user stories (P1–P4), Given-When-Then acceptance scenarios, 25 functional requirements, and 10 measurable success criteria. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates. Plan follows `plan-template.md`. Spec follows `spec-template.md`. Checklist validated. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | `speckit.plan` agent produces this plan with well-defined inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are included where the spec mandates behavior-based verification (SC-001–SC-010). Security hardening changes to config validation, access control, and rate limiting require tests to prevent regression. Test-free changes include Dockerfile USER directive, nginx headers, and docker-compose bind address updates. |
| **V. Simplicity and DRY** | ✅ PASS | Project-ownership check is centralized as a single FastAPI dependency (FR-007). Rate limiting uses the existing `slowapi` pattern. Config validation consolidates all startup checks in `config.py`. No premature abstractions introduced. |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/037-security-review/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── security-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── config.py                          # Modified: add startup validation for ENCRYPTION_KEY,
│   │                                      #   GITHUB_WEBHOOK_SECRET, SESSION_SECRET_KEY length,
│   │                                      #   cookie_secure enforcement, CORS origin validation
│   ├── main.py                            # Modified: gate API docs on ENABLE_DOCS env var
│   ├── dependencies.py                    # Modified: add verify_project_ownership dependency
│   ├── api/
│   │   ├── auth.py                        # Modified: cookie-based session delivery, POST-body
│   │   │                                  #   dev login, remove URL token param
│   │   ├── tasks.py                       # Modified: add project ownership check dependency
│   │   ├── projects.py                    # Modified: add project ownership check dependency
│   │   ├── settings.py                    # Modified: add project ownership check dependency
│   │   ├── workflow.py                    # Modified: add project ownership check dependency
│   │   ├── chat.py                        # Modified: add rate limiting decorator
│   │   ├── agents.py                      # Modified: add rate limiting decorator
│   │   ├── signal.py                      # Modified: constant-time secret comparison
│   │   └── webhooks.py                    # Modified: remove debug-conditional signature bypass
│   ├── middleware/
│   │   └── rate_limit.py                  # Modified: configure slowapi rate limiter
│   ├── services/
│   │   ├── database.py                    # Modified: 0700 dir / 0600 file permissions
│   │   ├── encryption.py                  # Modified: mandatory key enforcement
│   │   ├── github_auth.py                 # Modified: narrow OAuth scopes
│   │   ├── websocket.py                   # Modified: project ownership check on WS connect
│   │   └── github_projects/
│   │       └── service.py                 # Modified: sanitize GraphQL error messages
│   └── migrations/                        # NEW: migration for encrypting existing plaintext rows
│       └── 0XX_encrypt_existing_tokens.sql
└── tests/
    └── unit/
        ├── test_config_validation.py      # NEW: startup validation tests
        ├── test_project_ownership.py      # NEW: access control tests
        └── test_rate_limiting.py          # NEW: rate limit threshold tests

frontend/
├── src/
│   ├── hooks/
│   │   ├── useAuth.ts                     # Modified: remove URL token reading, use cookie auth
│   │   └── useChatHistory.ts              # Modified: store only message IDs, add TTL, clear on logout
│   └── components/
│       └── board/
│           └── IssueCard.tsx              # Modified: validate avatar URLs against allowed domains
└── Dockerfile                             # Modified: add USER directive for non-root nginx

docker-compose.yml                         # Modified: bind to 127.0.0.1, move data volume
frontend/nginx.conf                        # Modified: add security headers, remove X-XSS-Protection,
                                           #   server_tokens off
.github/workflows/
    └── branch-issue-link.yml              # Modified: minimize permissions, add justification comment
```

**Structure Decision**: Web application structure. Changes span `backend/`, `frontend/`, Docker configuration, nginx config, and CI/CD workflows. No new top-level directories. The majority of changes are modifications to existing files, with a few new test files and one database migration.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
