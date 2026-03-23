# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across the Solune application, covering OWASP Top 10 categories A01–A09 plus supply-chain concerns. The audit spans the FastAPI backend, React frontend, nginx reverse proxy, Docker configuration, and GitHub Actions workflows. Findings are addressed in four severity-ordered phases: Critical fixes enforce cookie-only session delivery, mandatory encryption at startup, and non-root containers; High fixes add centralized project authorization, constant-time secret comparison, HTTP security headers, POST-only credential endpoints, OAuth scope documentation, session key entropy, and localhost-only port binding; Medium fixes introduce rate limiting, cookie-secure enforcement, debug-independent webhook verification, dedicated API docs toggle, restrictive database permissions, CORS validation, external data volume mounts, memory-only chat history, and GraphQL error sanitization; Low fixes scope GitHub Actions permissions and validate avatar URLs.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript/Node 25 (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, React 19, Vite 8, nginx (Alpine), slowapi ≥0.1.9, cryptography ≥46.0.5
**Storage**: SQLite via aiosqlite ≥0.22.0 (path: `/var/lib/solune/data/settings.db`)
**Testing**: pytest ≥9.0.0 + pytest-asyncio (backend), Vitest 4 + @testing-library/react (frontend), Playwright (e2e)
**Target Platform**: Linux server (Docker containers), browser clients
**Project Type**: Web application (backend + frontend)
**Performance Goals**: N/A — security hardening only, no performance-impacting changes expected
**Constraints**: All changes must be backward-compatible with existing deployments (migration path for encryption enforcement); OAuth scope change requires staging validation
**Scale/Scope**: 21 findings across ~30 source files, 4 Docker/compose files, 1 GitHub Actions workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Phase 0 Entry)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First Development | ✅ PASS | `spec.md` contains 10 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios, clear scope boundaries, and out-of-scope declarations |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/` |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.specify` → `speckit.plan` → `speckit.tasks` → `speckit.implement` pipeline followed |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated in spec; verification is behavior-based (code review, runtime checks, curl commands). Tests may be added during implementation if needed |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` dependency avoids per-endpoint duplication; startup validation collects all errors in a single pass; no premature abstractions introduced |

### Post-Design Gate (Phase 1 Completion)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First Development | ✅ PASS | All 30 functional requirements (FR-001–FR-029) traced to user stories and acceptance scenarios in spec.md |
| II. Template-Driven Workflow | ✅ PASS | research.md (21 decisions), data-model.md (5 entities), contracts/security-contracts.md (20 contracts), quickstart.md (4 phases) all generated per template |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase complete; handoff to `speckit.tasks` for task decomposition |
| IV. Test Optionality with Clarity | ✅ PASS | Behavioral verification checklist in quickstart.md covers all 10 verification criteria from spec; no test framework changes required |
| V. Simplicity and DRY | ⚠️ JUSTIFIED | `repo` OAuth scope retained (broader than ideal) — justified in Complexity Tracking below; all other decisions favor simplest viable approach |

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — 21 research decisions
├── data-model.md        # Phase 1 output — 5 entity definitions
├── quickstart.md        # Phase 1 output — 4-phase implementation guide
├── contracts/
│   └── security-contracts.md  # Phase 1 output — 20 behavioral contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── Dockerfile                    # Container security (non-root user)
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py               # OAuth callback, dev login (FR-001, FR-002, FR-012)
│   │   │   ├── agents.py             # Project access control (FR-006)
│   │   │   ├── chat.py               # Rate limiting (FR-016)
│   │   │   ├── pipelines.py          # Project access control (FR-006)
│   │   │   ├── projects.py           # Project access, error sanitization (FR-006, FR-027)
│   │   │   ├── settings.py           # Project access control (FR-006)
│   │   │   ├── signal.py             # Constant-time comparison (FR-008)
│   │   │   ├── tasks.py              # Project access control (FR-006)
│   │   │   ├── webhooks.py           # Debug bypass removal (FR-020)
│   │   │   └── workflow.py           # Project access, rate limiting (FR-006, FR-016)
│   │   ├── config.py                 # Startup validation (FR-003, FR-004, FR-014, FR-019, FR-023)
│   │   ├── dependencies.py           # verify_project_access (FR-007)
│   │   ├── main.py                   # API docs toggle (FR-021)
│   │   └── services/
│   │       ├── database.py           # File permissions (FR-022)
│   │       ├── encryption.py         # Encryption enforcement support
│   │       ├── github_auth.py        # OAuth scope documentation (FR-013)
│   │       └── github_projects/
│   │           └── service.py        # GraphQL error sanitization (FR-027)
│   └── tests/                        # Existing test suite
├── frontend/
│   ├── Dockerfile                    # Non-root container (FR-005)
│   ├── nginx.conf                    # Security headers (FR-009, FR-010, FR-011)
│   └── src/
│       ├── components/
│       │   ├── auth/
│       │   │   └── useAuth.ts        # Cookie-based session (FR-001, FR-002)
│       │   ├── board/
│       │   │   └── IssueCard.tsx     # Avatar URL validation (FR-029)
│       │   └── chat/
│       │       └── useChatHistory.ts # Memory-only chat history (FR-025, FR-026)
│       └── services/
└── docker-compose.yml                # Port binding, volume mounts (FR-015, FR-024)

.github/workflows/
└── branch-issue-link.yml             # Workflow permissions (FR-028)
```

**Structure Decision**: Web application (Option 2) — the Solune project uses a `backend/` + `frontend/` structure under `solune/`. All security changes modify existing files in-place; no new directories or structural changes are needed. Infrastructure files (`Dockerfile`, `docker-compose.yml`, `nginx.conf`, workflow YAML) are also modified in-place.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `repo` OAuth scope retained (FR-013) | GitHub API returns misleading 404 errors for issue/PR creation without `repo` scope. The application creates issues, sub-issues, comments, labels, and PRs as core functionality. | Narrower scopes (`public_repo`, `project` only) were tested and confirmed to fail for write operations. GitHub App installation tokens would provide fine-grained permissions but require significant architectural changes (deferred to future enhancement). Decision documented with code comment per research Decision 8. |
