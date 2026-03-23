# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Remediate 21 security findings across OWASP Top 10 categories (3 Critical, 8 High, 9 Medium, 2 Low) in the Solune web application. The audit covers authentication flow hardening (cookie-based session delivery replacing URL tokens), mandatory encryption and secrets enforcement at startup, container privilege reduction, centralized project access authorization, HTTP security headers, rate limiting, and privacy-preserving chat history storage. Changes span the Python/FastAPI backend, React/TypeScript frontend, nginx configuration, Dockerfiles, and Docker Compose orchestration. Implementation follows a phased approach ordered by severity, with each phase independently deployable.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, React 19.2.0, nginx (frontend reverse proxy), slowapi ≥0.1.9 (rate limiting), Cryptography ≥46.0.5 (encryption)
**Storage**: SQLite via aiosqlite (session and settings storage, encrypted at rest with Fernet)
**Testing**: pytest + pytest-asyncio (backend), Vitest 4.0.18 + Playwright 1.58.2 (frontend)
**Target Platform**: Linux server (Docker containers), modern web browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limiting thresholds: chat 10/min, agents 5/min, workflow 10/min, OAuth callback 20/min per-IP
**Constraints**: Zero credentials in URLs; all containers non-root; database permissions 0700/0600; startup fails on missing security config in production
**Scale/Scope**: 21 security findings across ~30 source files; 4 implementation phases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Phase 0 Entry)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` contains 10 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md, research.md, data-model.md, quickstart.md, contracts/; hands off to `speckit.tasks` for task decomposition |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated in spec; behavioral verification checklist provided as acceptance criteria. Tests may be added during implementation if warranted |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` dependency avoids per-endpoint authorization duplication; startup validation collects all errors in single pass. One justified complexity: retaining `repo` OAuth scope (documented below) |

### Post-Design Gate (Phase 1 Exit) — Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All 30 functional requirements (FR-001–FR-029) have corresponding contracts in `contracts/security-contracts.md` |
| II. Template-Driven Workflow | ✅ PASS | All generated artifacts (research.md, data-model.md, quickstart.md, contracts/) follow template structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Phase outputs are immutable and ready for handoff to `speckit.tasks` |
| IV. Test Optionality with Clarity | ✅ PASS | Behavioral verification checklist in quickstart.md provides 10 manual verification steps; no test code generation required at this phase |
| V. Simplicity and DRY | ⚠️ JUSTIFIED | OAuth `repo` scope retained (broader than ideal) because GitHub API returns 404 for issue/PR operations without it. Documented in Complexity Tracking below |

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
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/            # Endpoint modules: auth.py, tasks.py, projects.py, settings.py,
│   │   │                   #   workflow.py, agents.py, pipelines.py, signal.py, webhooks.py, chat.py
│   │   ├── middleware/     # Request middleware
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   │   ├── github_projects/  # GitHub API integration: service.py, github_auth.py
│   │   │   └── ...
│   │   ├── config.py       # AppSettings with startup validation
│   │   ├── dependencies.py # Shared dependencies: verify_project_access
│   │   ├── database.py     # SQLite database setup and permissions
│   │   ├── encryption.py   # Fernet encryption for tokens
│   │   └── main.py         # FastAPI application entry point
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── architecture/
│   │   └── ...
│   ├── Dockerfile          # Backend container (already non-root)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/     # UI components: board/IssueCard.tsx
│   │   ├── hooks/          # React hooks: useAuth.ts, useChatHistory.ts
│   │   ├── pages/          # Page components
│   │   └── ...
│   ├── nginx.conf          # Frontend reverse proxy config
│   ├── Dockerfile          # Frontend container (needs non-root USER)
│   └── package.json
├── docker-compose.yml      # Service orchestration
└── .github/workflows/
    └── branch-issue-link.yml  # GitHub Actions workflow
```

**Structure Decision**: Web application layout (Option 2). The repository uses a monorepo structure under `solune/` with separate `backend/` and `frontend/` directories. Infrastructure files (`docker-compose.yml`, Dockerfiles, `nginx.conf`) are co-located with their respective services. The security audit modifies existing files across both services — no new directories or projects are introduced.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Retaining `repo` OAuth scope (FR-013) | GitHub API returns 404 errors for issue/PR creation without `repo` scope; the application creates issues, sub-issues, comments, labels, and PRs as core workflow | Narrower scopes (`public_repo`, `project` only) were tested and confirmed insufficient; GitHub App installation tokens would provide fine-grained permissions but require significant architectural changes — deferred to future enhancement |
