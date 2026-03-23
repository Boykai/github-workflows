# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Comprehensive security hardening across 21 findings spanning OWASP Top 10 categories (3 Critical, 8 High, 9 Medium, 2 Low). The implementation modifies existing behavior rather than introducing new features — securing the OAuth flow with HttpOnly cookies, enforcing encryption/secrets at startup, running containers as non-root, centralizing project authorization, adding HTTP security headers, implementing rate limiting, and improving data privacy. The phased approach (Critical → High → Medium → Low) ensures the most dangerous vulnerabilities are resolved first.

## Technical Context

**Language/Version**: Python ≥3.12 (backend, targeting 3.13), TypeScript/React (frontend)
**Primary Dependencies**: FastAPI, uvicorn, Pydantic, slowapi, cryptography (backend); React, Vite, TanStack Query, Tailwind CSS (frontend); nginx (reverse proxy/static serving)
**Storage**: SQLite via aiosqlite (async), encrypted at rest with Fernet (cryptography library)
**Testing**: pytest (backend unit/integration/property/fuzz), Vitest (frontend unit), Playwright (E2E)
**Target Platform**: Linux server (Docker containers), web browser (SPA frontend)
**Project Type**: Web application (backend + frontend + Docker Compose orchestration)
**Performance Goals**: Rate limiting thresholds — chat 10/min, agents 5/min, workflow 10/min, OAuth 20/min per-IP
**Constraints**: Non-root container execution, HTTPS-only cookies in production, 64-char minimum session key, 0700/0600 database permissions
**Scale/Scope**: Single-instance deployment, SQLite storage, 21 security findings across ~25 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md contains 10 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates: spec.md, plan.md, research.md, data-model.md, quickstart.md, contracts/ |
| III. Agent-Orchestrated Execution | ✅ PASS | speckit.plan generates plan artifacts; speckit.tasks will decompose into executable tasks; speckit.implement will execute |
| IV. Test Optionality with Clarity | ✅ PASS | Spec does not mandate TDD; behavioral verification checklist is sufficient. Tests are optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Changes modify existing code patterns rather than introducing new abstractions. Centralized `verify_project_access` follows existing dependency injection pattern. One justified complexity: retaining `repo` OAuth scope (documented in Complexity Tracking) |

**Post-Phase 1 Re-check**: ✅ All gates still pass. Research confirmed all decisions align with existing codebase patterns. No new abstractions beyond `verify_project_access` dependency (which follows the established FastAPI `Depends()` pattern).

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── security-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── Dockerfile              # Already non-root (appuser)
│   ├── pyproject.toml          # slowapi already listed as dependency
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py         # Findings 1, 7: OAuth cookie delivery, dev login POST body
│   │   │   ├── agents.py       # Finding 4, 11: project access, rate limiting
│   │   │   ├── chat.py         # Finding 11: rate limiting
│   │   │   ├── projects.py     # Finding 4, 19: project access, error sanitization
│   │   │   ├── settings.py     # Finding 4: project access
│   │   │   ├── signal.py       # Finding 5: constant-time comparison
│   │   │   ├── webhooks.py     # Finding 13: debug bypass removal
│   │   │   └── workflow.py     # Finding 4, 11: project access, rate limiting
│   │   ├── config.py           # Findings 2, 9, 12, 16: startup validation
│   │   ├── dependencies.py     # Finding 4: verify_project_access
│   │   ├── main.py             # Finding 14: ENABLE_DOCS toggle
│   │   ├── models/
│   │   │   └── database.py     # Finding 15: file permissions
│   │   └── services/
│   │       ├── encryption.py   # Finding 2: encryption enforcement
│   │       ├── github_auth.py  # Finding 8: OAuth scopes
│   │       └── github/
│   │           └── service.py  # Finding 19: GraphQL error sanitization
│   └── tests/
│       ├── unit/
│       └── integration/
├── frontend/
│   ├── Dockerfile              # Finding 3: non-root user (nginx-app)
│   ├── nginx.conf              # Finding 6: security headers
│   └── src/
│       ├── hooks/
│       │   ├── useAuth.ts      # Finding 1: cookie-based auth
│       │   └── useChatHistory.ts  # Finding 18: memory-only chat
│       └── components/
│           └── board/
│               └── IssueCard.tsx  # Finding 21: avatar URL validation
├── docker-compose.yml          # Findings 10, 17: port binding, volume mount
└── .github/
    └── workflows/
        └── branch-issue-link.yml  # Finding 20: workflow permissions
```

**Structure Decision**: Web application with backend (Python/FastAPI) and frontend (TypeScript/React/Vite) served via nginx. Docker Compose orchestrates both services plus a Signal API container. All security changes modify existing files — no new directories or modules required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `repo` OAuth scope retained (broader than minimum) | GitHub API returns 404 errors for issue/PR creation operations without `repo` scope. Core workflow depends on creating issues, sub-issues, comments, labels, and PRs | Narrower scopes (`public_repo`, `project` only) tested and confirmed insufficient. GitHub App migration deferred as architectural change |
| Encryption enforcement is a breaking change | Existing deployments without ENCRYPTION_KEY will fail to start after upgrade | Warning-only mode defeats the purpose of enforcement. Migration path documented: generate key + run migration script for plaintext rows |
