# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Remediate 21 OWASP-mapped security findings (3 Critical, 8 High, 9 Medium, 2 Low) across the Solune web application. Changes span backend (Python/FastAPI), frontend (React/TypeScript), nginx configuration, Dockerfiles, and Docker Compose. The approach follows a phased severity ordering — Critical fixes first (cookie-based session delivery, mandatory encryption at startup, non-root containers), then High (centralized project authorization, constant-time secret comparison, security headers, Docker port binding), then Medium (rate limiting, webhook verification, database permissions, CORS validation, chat privacy, error sanitization), and finally Low (workflow permissions, avatar URL validation). Research confirms all 21 findings are addressable with existing libraries and patterns already present in the codebase.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9 with React 19 (frontend)
**Primary Dependencies**: FastAPI, Pydantic, aiosqlite, cryptography, slowapi, githubkit (backend); Vite, React, TanStack Query (frontend); nginx (reverse proxy)
**Storage**: SQLite via aiosqlite (encrypted at rest with Fernet from `cryptography`)
**Testing**: pytest with asyncio_mode=auto (backend), Vitest + Playwright (frontend)
**Target Platform**: Linux server (Docker containers), modern web browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limiting thresholds: chat 10/min, agents 5/min, workflow 10/min, OAuth 20/min per-IP
**Constraints**: No new infrastructure dependencies; all fixes use existing libraries; backward-compatible except encryption enforcement (breaking change with migration path)
**Scale/Scope**: 21 security findings across ~20 source files, 4 configuration files, 2 Dockerfiles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md contains 10 prioritized user stories with acceptance scenarios |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | speckit.plan produces plan.md, research.md, data-model.md, quickstart.md, contracts/ |
| IV. Test Optionality | ✅ PASS | Tests not mandated by spec; behavioral verification checklist provided instead |
| V. Simplicity and DRY | ⚠️ NOTE | OAuth `repo` scope retained — justified in Complexity Tracking |

### Post-Design Gate (After Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All 30 functional requirements (FR-001–FR-029) have acceptance scenarios |
| II. Template-Driven | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, contracts/ all generated |
| III. Agent-Orchestrated | ✅ PASS | Artifacts handed off for speckit.tasks |
| IV. Test Optionality | ✅ PASS | Behavioral verification checklist in quickstart.md; no test code mandated |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` dependency avoids per-endpoint duplication; `repo` scope justified |

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — 21 research decisions
├── data-model.md        # Phase 1 output — entity definitions with security attributes
├── quickstart.md        # Phase 1 output — phased implementation roadmap
├── contracts/           # Phase 1 output — behavioral contracts (C-001 through C-020)
│   └── security-contracts.md
├── checklists/          # Specification quality checklist
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/               # Route handlers (auth.py, chat.py, agents.py, workflow.py, etc.)
│   │   ├── config.py          # AppSettings with startup validation
│   │   ├── dependencies.py    # Shared dependencies (verify_project_access)
│   │   ├── main.py            # FastAPI app creation (docs toggle)
│   │   ├── models/            # Pydantic models and DB schemas
│   │   ├── services/          # Business logic (encryption.py, cache.py, etc.)
│   │   └── middleware/        # Middleware (rate limiting, etc.)
│   ├── tests/                 # pytest test suite
│   └── Dockerfile             # Backend container (already non-root)
├── frontend/
│   ├── src/
│   │   ├── components/        # UI components (board/IssueCard.tsx, etc.)
│   │   ├── hooks/             # React hooks (useAuth.ts, useChatHistory.ts, etc.)
│   │   ├── pages/             # Page components
│   │   └── services/          # API client services
│   ├── nginx.conf             # Reverse proxy config (security headers)
│   └── Dockerfile             # Frontend container (needs non-root user)
├── docker-compose.yml         # Service orchestration (port bindings, volumes)
└── .github/workflows/
    └── branch-issue-link.yml  # GitHub Actions (permissions scoping)
```

**Structure Decision**: Web application structure (Option 2). The repository uses `solune/backend/` and `solune/frontend/` under a `solune/` monorepo root. Security changes touch both backend and frontend source code, configuration files, Dockerfiles, and Docker Compose — spanning the full stack.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (FR-013) | GitHub API returns 404 errors for issue/PR creation without `repo` scope; app creates issues, sub-issues, comments, labels, and PRs as core workflow | Narrower scopes (`public_repo`, `project` only) tested and confirmed insufficient; GitHub App migration deferred as architectural change |
| Encryption enforcement is a breaking change | Production must not run without encryption; existing plaintext deployments will fail on upgrade | Warning-only mode defeats the purpose; migration path documented with key generation command |
