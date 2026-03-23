# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

A comprehensive security audit addressing 21 findings across the OWASP Top 10, organized into 4 severity phases (3 Critical, 8 High, 9 Medium, 2 Low). The implementation hardens the Solune application's authentication flow (cookie-based session delivery), enforces encryption and secrets at startup, locks down container execution to non-root users, adds centralized project access authorization, introduces HTTP security headers, rate limiting, and privacy-respecting client-side data handling. Technical approach uses FastAPI's dependency injection for authorization, `slowapi` for rate limiting, nginx configuration for security headers, Pydantic settings validation for startup enforcement, and React state for privacy-safe chat history.

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript ~5.9 / Node 25 (frontend)
**Primary Dependencies**: FastAPI 0.135+, React 19.2, Vite 8, nginx 1.29-alpine, pydantic-settings, aiosqlite, cryptography 46, slowapi 0.1.9+
**Storage**: SQLite via aiosqlite at `/var/lib/solune/data/settings.db`
**Testing**: pytest + pytest-asyncio (backend), vitest + Playwright (frontend)
**Target Platform**: Linux containers (Docker Compose), served via nginx reverse proxy
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limiting thresholds: chat 10/min, agents 5/min, workflow 10/min, OAuth callback 20/min per-IP
**Constraints**: Zero credentials in URLs after login; containers must run non-root; encryption mandatory in production; per-user rate limiting preferred over per-IP
**Scale/Scope**: 21 security findings across 4 phases; ~25 files modified across backend, frontend, Docker, and CI

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` complete with 10 prioritized user stories (P1–P4), Given-When-Then acceptance scenarios, clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/` |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` generates plan artifacts; `speckit.tasks` will generate `tasks.md` (not created by this phase) |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated in spec; behavioral verification checklist provided for manual/integration testing |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` dependency avoids per-endpoint duplication; startup validation collects all errors in single pass; one Complexity Tracking entry for OAuth scope retention |

**Post-Phase 1 Re-check**:

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All 30 functional requirements (FR-001–FR-029) traced to contracts (C-001–C-020) |
| II. Template-Driven Workflow | ✅ PASS | All plan phase artifacts generated per template structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Phase 0 (research) and Phase 1 (design) artifacts complete; handoff to `speckit.tasks` ready |
| IV. Test Optionality with Clarity | ✅ PASS | No tests mandated; behavioral verification checklist in quickstart.md covers all acceptance scenarios |
| V. Simplicity and DRY | ✅ PASS | OAuth `repo` scope retention documented in Complexity Tracking with justification |

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
│   ├── Dockerfile                        # Container user hardening (Finding 3)
│   ├── src/
│   │   ├── config.py                     # Startup validation (Findings 2, 9, 12, 16)
│   │   ├── main.py                       # API docs toggle (Finding 14)
│   │   ├── dependencies.py               # Centralized verify_project_access (Finding 4)
│   │   ├── middleware/                    # Rate limiting setup (Finding 11)
│   │   ├── models/
│   │   ├── services/
│   │   │   ├── database.py               # File permissions (Finding 15)
│   │   │   ├── encryption.py             # Encryption enforcement (Finding 2)
│   │   │   └── github_projects/
│   │   │       └── service.py            # GraphQL error sanitization (Finding 19)
│   │   └── api/
│   │       ├── auth.py                   # OAuth cookie delivery, dev login (Findings 1, 7)
│   │       ├── signal.py                 # Constant-time comparison (Finding 5)
│   │       ├── webhooks.py               # Debug bypass removal (Finding 13)
│   │       ├── chat.py                   # Rate limiting (Finding 11)
│   │       ├── agents.py                 # Rate limiting, project access (Findings 4, 11)
│   │       ├── workflow.py               # Rate limiting, project access (Findings 4, 11)
│   │       ├── tasks.py                  # Project access (Finding 4)
│   │       ├── projects.py               # Project access, error sanitization (Findings 4, 19)
│   │       ├── settings.py               # Project access (Finding 4)
│   │       └── pipelines.py              # Project access (Finding 4)
│   └── tests/
├── frontend/
│   ├── Dockerfile                        # Non-root user (Finding 3)
│   ├── nginx.conf                        # Security headers (Finding 6)
│   └── src/
│       ├── components/
│       │   ├── auth/
│       │   │   └── useAuth.ts            # Cookie-based auth (Finding 1)
│       │   ├── board/
│       │   │   └── IssueCard.tsx          # Avatar URL validation (Finding 21)
│       │   └── chat/
│       │       └── useChatHistory.ts      # Memory-only chat history (Finding 18)
│       └── hooks/
├── docker-compose.yml                    # Port binding, volume mount (Findings 10, 17)
└── .github/
    └── workflows/
        └── branch-issue-link.yml         # Permission minimization (Finding 20)
```

**Structure Decision**: Web application structure (backend + frontend) — matches the existing repository layout. All changes modify existing files; no new directories or modules are introduced beyond the centralized `verify_project_access` dependency.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (Finding 8) | GitHub API returns 404 errors for issue/PR creation without `repo` scope; narrower scopes (`public_repo`, `project`) do not support required write operations | Narrower scopes tested and confirmed insufficient; GitHub App tokens would provide fine-grained permissions but require architectural changes deferred to future enhancement |
