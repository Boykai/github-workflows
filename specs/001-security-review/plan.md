# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across OWASP Top 10 categories in a phased approach. The audit covers authentication flow hardening (cookie-only session delivery), mandatory encryption/secrets enforcement at startup, non-root container execution, centralized project access authorization, HTTP security headers, rate limiting, and defense-in-depth configuration improvements. Changes span the FastAPI backend (`config.py`, `auth.py`, `dependencies.py`, `database.py`, nginx config, Dockerfiles), the React frontend (`useAuth.ts`, `useChatHistory.ts`, `IssueCard.tsx`), Docker Compose, and GitHub Actions workflows. Research confirms all 21 findings are addressable with the existing technology stack — no new frameworks or architectural changes are required.

## Technical Context

**Language/Version**: Python ≥3.12 (targets 3.14 in Docker), TypeScript ~5.9, Node.js 25-alpine  
**Primary Dependencies**: FastAPI ≥0.135.0, Uvicorn ≥0.42.0, Pydantic ≥2.12.0, React 19.2, Vite 8.0, slowapi ≥0.1.9, cryptography ≥46.0.5  
**Storage**: SQLite via aiosqlite ≥0.22.0 (async, file-based at `/var/lib/solune/data/settings.db`)  
**Testing**: Backend — pytest ≥9.0.0 (with pytest-asyncio, hypothesis, freezegun); Frontend — Vitest ≥4.0.18 (with @testing-library/react, happy-dom); E2E — Playwright ≥1.58.2  
**Target Platform**: Linux server (Docker containers), modern web browsers  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: Rate limits — chat 10/min, agents 5/min, workflow 10/min, OAuth callback 20/min per-IP  
**Constraints**: Zero credentials in URLs, startup fails if security config missing in production, all containers non-root, constant-time secret comparisons  
**Scale/Scope**: 21 findings across ~25 source files, 4 implementation phases by severity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gate (Before Phase 0)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First Development | ✅ PASS | `spec.md` contains 10 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` produces plan.md, research.md, data-model.md, quickstart.md, contracts/ — single-responsibility with explicit handoff to `speckit.tasks` |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated in spec; behavioral verification checklist (10 items) serves as acceptance criteria. Tests may be added during implementation if needed |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` dependency (not per-endpoint logic), existing `hmac.compare_digest` pattern replicated, `slowapi` already in pyproject.toml. One complexity exception: `repo` OAuth scope retained (see Complexity Tracking) |

**Gate Result**: ✅ All principles satisfied. Proceeding to Phase 0 research.

### Post-Design Gate (After Phase 1)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First Development | ✅ PASS | All 30 functional requirements (FR-001–FR-029) have corresponding contracts in `contracts/security-contracts.md` (C-001–C-020) |
| II. Template-Driven Workflow | ✅ PASS | All generated artifacts (research.md, data-model.md, quickstart.md, contracts/) follow template structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Phase 0 and Phase 1 outputs complete; explicit handoff boundary: `tasks.md` is produced by `speckit.tasks` (not this command) |
| IV. Test Optionality with Clarity | ✅ PASS | Behavioral verification checklist retained from spec; implementation may add targeted tests as needed |
| V. Simplicity and DRY | ✅ PASS | Research resolved all unknowns with simplest viable approaches. One justified complexity (OAuth `repo` scope) tracked below |

**Gate Result**: ✅ All principles satisfied. Ready for `speckit.tasks` phase.

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — 21 research decisions
├── data-model.md        # Phase 1 output — 5 security-relevant entities
├── quickstart.md        # Phase 1 output — phased implementation roadmap
├── contracts/           # Phase 1 output — behavioral contracts (C-001 through C-020)
│   └── security-contracts.md
├── checklists/          # Specification quality validation
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/                  # Endpoint handlers (auth.py, signal.py, webhooks.py, chat.py, etc.)
│   │   ├── config.py             # AppSettings — startup validation, encryption enforcement
│   │   ├── dependencies.py       # verify_project_access, session dependencies
│   │   ├── main.py               # Application entry, docs toggle
│   │   ├── models/               # Pydantic models (DevLoginRequest, etc.)
│   │   ├── services/
│   │   │   ├── database.py       # SQLite management, file permissions
│   │   │   └── github_projects/
│   │   │       └── service.py    # GraphQL error sanitization
│   │   └── middleware/           # Request middleware
│   ├── tests/
│   │   ├── unit/                 # Unit tests
│   │   ├── integration/          # Integration tests
│   │   └── property/            # Property-based tests
│   └── Dockerfile               # Backend container (already non-root)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/             # useAuth.ts — session handling
│   │   │   ├── board/            # IssueCard.tsx — avatar rendering
│   │   │   └── chat/             # useChatHistory.ts — chat storage
│   │   ├── hooks/                # Custom React hooks
│   │   └── services/             # API clients
│   ├── Dockerfile               # Frontend container — add non-root USER
│   └── nginx.conf               # Security headers, server_tokens
├── docker-compose.yml            # Port bindings, volume mounts
└── .github/workflows/
    └── branch-issue-link.yml     # Workflow permissions
```

**Structure Decision**: Web application layout (Option 2). The existing `solune/backend/` and `solune/frontend/` directories are the primary targets. Changes are scoped to existing files — no new directories or services are introduced. All changes modify existing behavior (security hardening) rather than adding new features.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (FR-013) | GitHub API returns misleading 404 errors for issue/PR creation operations without `repo` scope. The application creates issues, sub-issues, comments, labels, and PRs as core functionality. | Narrower scopes (`public_repo`, `project` only) tested and confirmed insufficient — write operations fail silently with 404. GitHub App installation tokens would provide fine-grained permissions but require a different authentication architecture (deferred). |
