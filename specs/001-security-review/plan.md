# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Remediate 21 OWASP-classified security findings (3 Critical, 8 High, 9 Medium, 2 Low) across backend, frontend, nginx, Docker, and CI/CD. Changes span cookie-based session delivery, mandatory encryption enforcement at startup, non-root containers, centralized project authorization, constant-time secret comparison, HTTP security headers, rate limiting, privacy-safe chat storage, and error sanitization. Implementation follows a phased approach ordered by severity, with each phase independently testable.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, React 19.2, Vite 8, slowapi ≥0.1.9, cryptography ≥46.0.5, httpx ≥0.28.0, pydantic ≥2.12.0, @tanstack/react-query 5.91
**Storage**: SQLite (aiosqlite ≥0.22.0), file-based at `/var/lib/solune/data/settings.db`
**Testing**: pytest ≥9.0 with 75% coverage minimum (backend), vitest 4.0 (frontend), Playwright (E2E)
**Target Platform**: Linux server (Docker Compose), web browser (SPA)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limiting at 5–20 req/min per endpoint category; no measurable latency impact from security changes
**Constraints**: No new infrastructure dependencies; backward-compatible except encryption key enforcement (documented migration path)
**Scale/Scope**: 21 findings across ~30 files; 4 implementation phases ordered by severity

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

- [x] Prioritized user stories (P1–P4) with independent testing criteria are present in spec.md
- [x] Given-When-Then acceptance scenarios defined for all 10 user stories
- [x] Clear scope boundaries and out-of-scope declarations documented

### II. Template-Driven Workflow — ✅ PASS

- [x] All artifacts follow canonical templates from `.specify/templates/`
- [x] No custom sections without justification

### III. Agent-Orchestrated Execution — ✅ PASS

- [x] Plan follows the speckit.plan workflow phases (0: Research, 1: Design, 2: Planning)
- [x] Each phase produces well-defined outputs (research.md, data-model.md, contracts/, quickstart.md)
- [x] Clear handoff to speckit.tasks for Phase 2 task generation

### IV. Test Optionality with Clarity — ✅ PASS

- [x] Tests are included: the spec explicitly requires behavioral verification (10 verification checks)
- [x] Testing approach uses existing pytest/vitest infrastructure — no new test frameworks
- [x] Tests verify security behavior (403 responses, startup failures, header presence)

### V. Simplicity and DRY — ✅ PASS (with 1 justified complexity)

- [x] Changes favor direct modifications to existing code over new abstractions
- [x] Centralized `verify_project_access` dependency prevents per-endpoint duplication (DRY)
- [x] OAuth `repo` scope retained despite being broader than ideal — justified in Complexity Tracking

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — all 21 findings researched
├── data-model.md        # Phase 1 output — security entity models
├── quickstart.md        # Phase 1 output — phased implementation guide
├── contracts/
│   └── security-contracts.md  # Phase 1 output — behavioral contracts C-001 through C-020
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py          # [Finding 1,7] Cookie session delivery, dev-login POST body
│   │   │   ├── signal.py        # [Finding 5] Constant-time secret comparison
│   │   │   ├── webhooks.py      # [Finding 13] Remove debug bypass for webhook verification
│   │   │   ├── tasks.py         # [Finding 4] Add verify_project_access dependency
│   │   │   ├── projects.py      # [Finding 4,19] Project access + error sanitization
│   │   │   ├── settings.py      # [Finding 4] Add verify_project_access dependency
│   │   │   ├── workflow.py      # [Finding 4,11] Project access + rate limiting
│   │   │   ├── agents.py        # [Finding 4,11] Project access + rate limiting
│   │   │   ├── pipelines.py     # [Finding 4] Add verify_project_access dependency
│   │   │   └── health.py        # No changes
│   │   ├── services/
│   │   │   ├── database.py      # [Finding 15] Database file permissions 0700/0600
│   │   │   └── github_projects/
│   │   │       └── service.py   # [Finding 19] GraphQL error sanitization
│   │   ├── config.py            # [Finding 2,9,12,14,16] Startup validation
│   │   ├── dependencies.py      # [Finding 4] verify_project_access dependency
│   │   ├── main.py              # [Finding 14] ENABLE_DOCS toggle
│   │   └── ...
│   ├── tests/
│   │   ├── unit/                # Security behavior unit tests
│   │   └── ...
│   ├── Dockerfile               # Backend already non-root
│   └── pyproject.toml           # slowapi already listed
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useAuth.ts       # [Finding 1] Cookie-based auth (no URL params)
│   │   │   └── useChatHistory.ts # [Finding 18] Memory-only chat history
│   │   ├── components/
│   │   │   └── board/
│   │   │       └── IssueCard.tsx # [Finding 21] Avatar URL validation
│   │   └── ...
│   ├── nginx.conf               # [Finding 6] Security headers
│   ├── Dockerfile               # [Finding 3] Non-root USER directive
│   └── ...
├── docker-compose.yml           # [Finding 10,17] Port binding + volume mount
└── ...

.github/workflows/
└── branch-issue-link.yml        # [Finding 20] Minimum permissions
```

**Structure Decision**: Web application (Option 2) — `solune/backend/` and `solune/frontend/` with shared Docker Compose orchestration. All changes modify existing files; no new directories or projects introduced.

## Complexity Tracking

> **Documents justified complexities that pass Constitution Check with explanation**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (broader than minimum) | GitHub API returns 404 for issue/PR creation without `repo` scope; core workflow (issues, sub-issues, comments, labels, PRs) requires it | Narrower scopes (`public_repo`, `project` only) were tested and confirmed insufficient — GitHub App migration deferred as separate feature |
| Encryption key now mandatory at startup | Breaking change for existing deployments without a key | Warning-only mode defeats enforcement purpose; migration path documented with key generation command in error message |
