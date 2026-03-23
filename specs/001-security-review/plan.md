# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Comprehensive security audit covering 21 findings across OWASP Top 10 categories (3 Critical, 8 High, 9 Medium, 2 Low). The audit addresses session management, encryption enforcement, container security, authorization controls, HTTP hardening, rate limiting, data privacy, and configuration validation across the backend (FastAPI/Python), frontend (React/TypeScript), nginx reverse proxy, Docker containers, and CI/CD workflows. All findings are organized into four severity-based phases with clear dependency ordering and behavioral verification contracts.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9.0 (frontend)
**Primary Dependencies**: FastAPI ≥0.135.0, React 19.2, nginx 1.29, slowapi ≥0.1.9, cryptography ≥46.0.5
**Storage**: SQLite via aiosqlite ≥0.22.0 (encrypted at rest with Fernet)
**Testing**: pytest (backend unit/integration), vitest (frontend), Playwright (e2e)
**Target Platform**: Linux containers (Docker Compose), web browser clients
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limits — 10 req/min on chat/workflow, 5 req/min on agents, 20 req/min on OAuth callback
**Constraints**: All containers non-root, ports bound to 127.0.0.1 only, database dir 0700 / file 0600
**Scale/Scope**: 21 security findings across 4 severity phases, ~25 files modified

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` contains 10 prioritized user stories (P1–P4) with Given-When-Then acceptance scenarios, clear scope boundaries, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Work decomposed into speckit agents (specify → plan → tasks → implement) with clear handoffs |
| IV. Test Optionality with Clarity | ✅ PASS | Security audit mandates verification (behavior-based checks listed in spec); tests are included because the spec explicitly requires them for security validation |
| V. Simplicity and DRY | ✅ PASS | Changes favor existing patterns (e.g., `verify_project_access` shared dependency, `hmac.compare_digest` reuse). No premature abstractions introduced |

**Post-Design Re-check**: All principles remain satisfied. The `repo` OAuth scope retention is justified with a code comment explaining GitHub API requirements (see research.md Decision 8).

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research decisions for all 21 findings
├── data-model.md        # Phase 1 output — security-relevant entity model
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/
│   └── security-contracts.md  # Phase 1 output — behavioral contracts per finding
├── checklists/
│   └── requirements.md  # Quality checklist (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── Dockerfile               # FR-005: Non-root appuser (already non-root)
│   ├── src/
│   │   ├── api/
│   │   │   ├── auth.py          # FR-001/002/012: Secure OAuth, cookie-based sessions, POST dev-login
│   │   │   ├── agents.py        # FR-006/016: Project access + rate limiting
│   │   │   ├── chat.py          # FR-016: Rate limiting on chat endpoints
│   │   │   ├── pipelines.py     # FR-006: Project access verification
│   │   │   ├── projects.py      # FR-006: Project access verification
│   │   │   ├── settings.py      # FR-006: Project access verification
│   │   │   ├── signal.py        # FR-008: Constant-time secret comparison
│   │   │   ├── tasks.py         # FR-006: Project access verification
│   │   │   ├── webhooks.py      # FR-008/020: Webhook verification, no debug bypass
│   │   │   └── workflow.py      # FR-006/016: Project access + rate limiting
│   │   ├── config.py            # FR-003/004/014/019/023: Startup validation suite
│   │   ├── dependencies.py      # FR-007: Centralized verify_project_access
│   │   ├── main.py              # FR-021: ENABLE_DOCS gate
│   │   └── services/
│   │       ├── database.py      # FR-022: Directory/file permissions 0700/0600
│   │       ├── github_auth.py   # FR-013: OAuth scope management
│   │       └── github_projects/ # FR-027: Error sanitization
│   └── tests/
├── frontend/
│   ├── Dockerfile               # FR-005: Non-root nginx-app user
│   ├── nginx.conf               # FR-009/010/011: Security headers
│   └── src/
│       ├── hooks/
│       │   ├── useAuth.ts       # FR-002: No URL credential reading
│       │   └── useChatHistory.ts # FR-025/026: Memory-only chat, logout clear
│       └── components/
│           └── board/
│               └── IssueCard.tsx # FR-029: Avatar URL validation
├── docker-compose.yml           # FR-015/024: Port binding 127.0.0.1, volume at /var/lib/solune/data
└── .github/workflows/
    └── branch-issue-link.yml    # FR-028: Minimal workflow permissions
```

**Structure Decision**: Web application (backend + frontend). All security changes are scoped to existing files — no new directories or modules required. The `solune/` directory contains both `backend/` (FastAPI/Python) and `frontend/` (React/TypeScript with nginx) subdirectories.

## Complexity Tracking

> No constitution violations identified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| `repo` OAuth scope retained (FR-013) | GitHub API returns misleading 404s for issue/PR creation without `repo` scope | Narrower scopes (`public_repo`, `project`) were tested but do not support the core workflow (creating issues, sub-issues, comments, labels, and PRs). GitHub App migration deferred to future enhancement. |
