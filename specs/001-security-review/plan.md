# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across the Solune application stack. Changes span the Python/FastAPI backend, React/TypeScript frontend, nginx configuration, Dockerfiles, and CI workflows. The approach is phased by severity: Critical findings (cookie-based session delivery, mandatory encryption/secrets at startup, non-root containers) are addressed first, followed by High (centralized project authorization, constant-time comparisons, security headers, dev login POST, port binding), Medium (rate limiting, webhook hardening, CORS validation, chat privacy, error sanitization), and Low (workflow permissions, avatar URL validation). Research confirmed all 21 findings are actionable with decisions documented in [research.md](research.md).

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9 / React 19 (frontend)
**Primary Dependencies**: FastAPI ≥0.135, Uvicorn, Pydantic ≥2.12, aiosqlite, slowapi ≥0.1.9, httpx, githubkit (backend); Vite 8, react-router-dom 7, TanStack Query (frontend)
**Storage**: SQLite via aiosqlite (WAL mode, single persistent connection)
**Testing**: pytest ≥9.0 with pytest-asyncio, pytest-cov, hypothesis (backend); Vitest ≥4.0, Testing Library, Playwright (frontend)
**Target Platform**: Linux containers (Docker), nginx reverse proxy for frontend
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — security hardening, no performance-critical changes
**Constraints**: All changes must be backward-compatible in debug mode; encryption enforcement is a breaking change in production (migration path documented)
**Scale/Scope**: 21 findings across ~25 source files, 4 Docker/Compose files, 1 CI workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development — ✅ PASS

- Specification (`spec.md`) contains 10 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios
- 30 functional requirements (FR-001 through FR-030) with clear acceptance criteria
- Scope boundaries and out-of-scope items explicitly declared
- Edge cases documented (encryption migration, OAuth re-authorization, shared NAT rate limiting)

### Principle II: Template-Driven Workflow — ✅ PASS

- All artifacts follow canonical templates from `.specify/templates/`
- `spec.md` uses spec-template.md structure
- `plan.md` (this file) follows plan-template.md structure
- `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` generated per plan workflow

### Principle III: Agent-Orchestrated Execution — ✅ PASS

- `speckit.specify` produced spec.md → `speckit.plan` produces plan.md + Phase 0/1 artifacts → `speckit.tasks` will produce tasks.md
- Each agent operates on well-defined inputs from the previous phase
- Clear handoff: plan.md references spec.md; research.md references plan.md Technical Context

### Principle IV: Test Optionality with Clarity — ✅ PASS

- The specification does not mandate TDD; tests are not required by this plan
- Verification is behavior-based (10 behavioral checks defined in spec.md and quickstart.md)
- Tests may be added by `speckit.tasks` if the implementation phase determines them necessary

### Principle V: Simplicity and DRY — ✅ PASS (with justified complexity)

- Each finding has a single, direct fix — no over-engineering
- `verify_project_access` centralizes authorization (DRY) rather than duplicating logic per endpoint
- OAuth `repo` scope retention is justified in Complexity Tracking below (simpler scope breaks functionality)

**Gate Result**: All five principles satisfied. Proceeding to Phase 0 research.

### Post-Design Re-Check — ✅ PASS

- Research (Phase 0) resolved all Technical Context items — no NEEDS CLARIFICATION remains
- Data model (Phase 1) documents security-relevant entity modifications without introducing new entities
- Contracts (Phase 1) map directly to functional requirements FR-001 through FR-029
- Quickstart (Phase 1) provides phased verification commands for each finding
- No template deviations or unjustified complexity introduced during design

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — 21 decisions with rationale
├── data-model.md        # Phase 1 output — security-relevant entity attributes
├── quickstart.md        # Phase 1 output — phased implementation roadmap
├── contracts/
│   └── security-contracts.md  # Phase 1 output — 20 behavioral contracts (C-001 through C-020)
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/           # Route handlers: auth.py, tasks.py, projects.py, settings.py,
│   │   │                  #   workflow.py, agents.py, pipelines.py, signal.py, webhooks.py, chat.py
│   │   ├── models/        # Pydantic/DB models
│   │   ├── services/      # Business logic: github_projects/service.py
│   │   ├── middleware/     # Request middleware
│   │   ├── migrations/    # SQL migration scripts
│   │   ├── config.py      # AppSettings with startup validation
│   │   ├── dependencies.py # verify_project_access, session management
│   │   ├── main.py        # FastAPI app creation, docs toggle
│   │   ├── database.py    # SQLite connection, file permissions
│   │   └── encryption.py  # Fernet encryption for tokens
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # UI components: board/IssueCard.tsx
│   │   ├── hooks/         # Custom hooks: useAuth.ts, useChatHistory.ts
│   │   ├── pages/         # Page components
│   │   └── services/      # API client services
│   ├── nginx.conf         # Security headers, reverse proxy
│   └── Dockerfile         # Non-root user directive
├── docker-compose.yml     # Port bindings, volume mounts
└── .github/
    └── workflows/
        └── branch-issue-link.yml  # Workflow permissions
```

**Structure Decision**: Web application (Option 2) — the project has a dedicated `solune/backend/` (Python/FastAPI) and `solune/frontend/` (React/TypeScript) structure. All 21 security findings map to files within this structure. No new directories or projects are introduced; changes are modifications to existing files.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (FR-013) | GitHub API returns 404 for issue/PR creation without `repo` scope | Narrower scopes (`public_repo`, `project`) tested and confirmed insufficient for core write operations; GitHub App migration deferred as architectural change |
| Encryption key mandatory in production (FR-003) | Breaking change for existing deployments without encryption | Warning-only mode defeats the purpose; migration path documented with key generation command |
