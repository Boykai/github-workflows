# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across OWASP Top 10 categories. The audit spans a FastAPI + React web application with SQLite storage served via nginx. Changes are phased by severity: Critical fixes first (cookie-based session delivery, mandatory encryption enforcement, non-root containers), followed by High (centralized project authorization, constant-time secret comparison, HTTP security headers, Docker hardening), Medium (rate limiting, webhook verification hardening, CORS validation, chat privacy, error sanitization), and Low (workflow permissions, avatar URL validation). Research confirms all findings are addressable with the current stack — no new major dependencies required beyond `slowapi` (already present in pyproject.toml).

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13, Docker 3.14-slim) · TypeScript ~5.9.0 (React 19.2, Node 25)
**Primary Dependencies**: FastAPI ≥0.135.0, Pydantic ≥2.12.0, Uvicorn ≥0.42.0, aiosqlite ≥0.22.0, cryptography ≥46.0.5 (Fernet), slowapi ≥0.1.9, httpx ≥0.28.0, githubkit ≥0.14.6 · React 19.2, Vite 8, TanStack Query 5.91, Tailwind CSS 4.2, Radix UI, react-hook-form + zod 4.3
**Storage**: SQLite via aiosqlite (WAL mode, persistent connection, 32 SQL migrations) · Fernet encryption at rest
**Testing**: Backend: pytest ≥9.0.0, pytest-asyncio, pytest-cov (75% threshold), hypothesis · Frontend: Vitest 4.0, @testing-library/react, Playwright 1.58, Stryker 9.6
**Target Platform**: Linux server (Docker: python:3.14-slim + nginx:1.29-alpine) · Web browser (SPA)
**Project Type**: Web application (separate backend + frontend)
**Performance Goals**: No explicit SLA; async patterns throughout, SQLite WAL for concurrent reads, 75% test coverage minimum
**Constraints**: Single-server SQLite (no connection pooling), per-user rate limiting preferred over per-IP, `repo` OAuth scope retained (GitHub API limitation)
**Scale/Scope**: Single-deployment web application, 21 security findings across 30+ files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` includes 10 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/`) follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.specify` → `speckit.plan` → `speckit.tasks` → `speckit.implement` pipeline followed; each agent has single responsibility |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; verification is behavior-based (code review, `curl`, `docker exec`, browser devtools). Existing test infrastructure (pytest, Vitest) available if tests are added during implementation |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` dependency avoids per-endpoint authorization duplication. OAuth scope retained with justification (see Complexity Tracking). Memory-only chat history is simplest privacy solution |

**Gate Result**: PASS — all principles satisfied. One complexity justification required (OAuth scope retention).

### Post-Design Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All 30 functional requirements (FR-001–FR-029) mapped to behavioral contracts (C-001–C-020) in `contracts/security-contracts.md` |
| II. Template-Driven Workflow | ✅ PASS | All Phase 0 and Phase 1 artifacts generated per template structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase complete; handoff to `speckit.tasks` for task decomposition |
| IV. Test Optionality | ✅ PASS | Verification remains behavior-based per spec. Test tasks can be added in `tasks.md` if requested |
| V. Simplicity and DRY | ✅ PASS | No unnecessary abstractions introduced. Each fix is a targeted, surgical change |

**Post-Design Gate Result**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — 21 decisions documented
├── data-model.md        # Phase 1 output — 5 entities, relationships, permission model
├── quickstart.md        # Phase 1 output — phased implementation roadmap
├── contracts/
│   └── security-contracts.md  # Phase 1 output — 20 behavioral contracts (C-001–C-020)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/                 # Route handlers (auth.py, tasks.py, projects.py, settings.py,
│   │   │                        #   workflow.py, agents.py, pipelines.py, chat.py, signal.py,
│   │   │                        #   webhooks.py)
│   │   ├── services/            # Business logic (database.py, github_auth.py, service.py)
│   │   ├── models/              # Pydantic models
│   │   ├── middleware/          # Request middleware
│   │   ├── migrations/          # SQL migrations (001–032)
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # AppSettings with validation
│   │   ├── dependencies.py      # Shared dependencies (verify_project_access)
│   │   └── encryption.py        # Fernet encryption utilities
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── Dockerfile               # Multi-stage build, non-root appuser
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components (board/IssueCard.tsx)
│   │   ├── pages/               # Route pages
│   │   ├── hooks/               # React hooks (useAuth.ts, useChatHistory.ts)
│   │   ├── services/            # HTTP client (api.ts)
│   │   └── types/               # TypeScript types
│   ├── e2e/                     # Playwright E2E tests
│   ├── Dockerfile               # Multi-stage build, non-root nginx-app
│   ├── nginx.conf               # nginx configuration with security headers
│   └── package.json
│
├── docker-compose.yml           # 3 services: backend, frontend, signal-api
└── .github/
    └── workflows/
        └── branch-issue-link.yml  # GitHub Actions workflow
```

**Structure Decision**: Web application with separate backend (FastAPI) and frontend (React/nginx). All security changes modify existing files within this structure — no new directories or services required.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (FR-013) | GitHub API returns 404 errors for issue/PR creation operations without `repo` scope. The application creates issues, sub-issues, comments, labels, and PRs as core workflow | Narrower scopes (`public_repo`, `project` only) were tested and confirmed insufficient for write operations. GitHub App installation tokens would provide fine-grained permissions but require a different authentication model (deferred to future enhancement) |
