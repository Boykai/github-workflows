# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `001-security-review` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-security-review/spec.md`

## Summary

Remediate 21 OWASP-mapped security findings (3 Critical, 8 High, 9 Medium, 2 Low) across the Solune web application. The audit covers authentication flow, encryption enforcement, container hardening, authorization, HTTP headers, rate limiting, data privacy, and configuration validation. Implementation follows a phased approach prioritized by severity: Critical fixes first (session token delivery, encryption enforcement, non-root containers), then High (project authorization, secret comparison, security headers, network binding), Medium (rate limiting, webhook hardening, error sanitization, data privacy), and Low (workflow permissions, avatar validation). Research confirmed all 21 findings are actionable with well-established remediation patterns — see [research.md](research.md) for decision rationale and alternatives considered.

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript/React (frontend), nginx (reverse proxy)
**Primary Dependencies**: FastAPI, Starlette, Pydantic, slowapi (rate limiting), cryptography (Fernet encryption)
**Storage**: SQLite via aiosqlite (encrypted at rest with Fernet)
**Testing**: pytest (backend), Vitest (frontend)
**Target Platform**: Linux server (Docker containers)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rate limits per endpoint (chat 10/min, agents 5/min, workflow 10/min, OAuth 20/min per-IP)
**Constraints**: Zero credentials in URLs, all containers non-root, all secrets mandatory in production
**Scale/Scope**: 21 security findings across ~25 files in backend and frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate (Initial)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | spec.md completed with 10 prioritized user stories, Given-When-Then scenarios, 30 functional requirements, scope boundaries |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated | ✅ PASS | speckit.plan produces plan.md, research.md, data-model.md, quickstart.md, contracts/; tasks.md deferred to speckit.tasks |
| IV. Test Optionality | ✅ PASS | Tests not explicitly mandated in spec; behavioral verification checklist provided for manual/automated validation |
| V. Simplicity and DRY | ✅ PASS | Centralized `verify_project_access` avoids per-endpoint duplication; startup validation collects all errors in one pass |

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All 21 findings map to functional requirements (FR-001 through FR-029); no scope creep beyond original audit |
| II. Template-Driven | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, contracts/ all follow template structure |
| III. Agent-Orchestrated | ✅ PASS | Phase outputs are well-defined; handoff to speckit.tasks is explicit |
| IV. Test Optionality | ✅ PASS | Behavioral verification checklist (10 checks) provided; formal test generation deferred unless requested |
| V. Simplicity and DRY | ⚠️ JUSTIFIED | OAuth `repo` scope retained (broader than ideal) — see Complexity Tracking below |

## Project Structure

### Documentation (this feature)

```text
specs/001-security-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — 21 research decisions with rationale
├── data-model.md        # Phase 1 output — 5 entities with security attributes
├── quickstart.md        # Phase 1 output — phased implementation roadmap
├── contracts/           # Phase 1 output — 20 behavioral security contracts
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
│   │   ├── config.py              # AppSettings, startup validation (Findings 2, 9, 12, 16)
│   │   ├── main.py                # FastAPI app creation, docs toggle (Finding 14)
│   │   ├── dependencies.py        # verify_project_access (Finding 4)
│   │   ├── api/
│   │   │   ├── auth.py            # OAuth callback, dev-login (Findings 1, 7)
│   │   │   ├── tasks.py           # Project-scoped endpoints (Finding 4)
│   │   │   ├── projects.py        # Project-scoped endpoints (Finding 4)
│   │   │   ├── settings.py        # Project-scoped endpoints (Finding 4)
│   │   │   ├── workflow.py        # Project-scoped + rate-limited (Findings 4, 11)
│   │   │   ├── chat.py            # Rate-limited endpoints (Finding 11)
│   │   │   ├── agents.py          # Rate-limited endpoints (Finding 11)
│   │   │   ├── signal.py          # Constant-time comparison (Finding 5)
│   │   │   ├── webhooks.py        # Debug bypass removal (Finding 13)
│   │   │   └── pipelines.py       # Project-scoped endpoints (Finding 4)
│   │   └── services/
│   │       ├── database.py        # File permissions (Finding 15)
│   │       ├── encryption.py      # Encryption enforcement (Finding 2)
│   │       └── github_projects/
│   │           ├── service.py     # GraphQL error sanitization (Finding 19)
│   │           └── ...
│   └── tests/
├── frontend/
│   ├── Dockerfile                 # Non-root user (Finding 3)
│   ├── nginx.conf                 # Security headers (Finding 6)
│   └── src/
│       ├── components/
│       │   ├── auth/              # useAuth hook (Finding 1)
│       │   ├── chat/              # useChatHistory (Finding 18)
│       │   └── board/
│       │       └── IssueCard.tsx  # Avatar validation (Finding 21)
│       └── ...
├── docker-compose.yml             # Port binding, volume mount (Findings 10, 17)
└── .github/workflows/
    └── branch-issue-link.yml      # Workflow permissions (Finding 20)
```

**Structure Decision**: Web application (Option 2) — existing `solune/backend/` and `solune/frontend/` structure. Security changes span both backend (Python/FastAPI) and frontend (TypeScript/React/nginx) with cross-cutting Docker and workflow configuration.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OAuth `repo` scope retained (FR-013) | GitHub API returns misleading 404 errors for issue/PR creation without `repo` scope — core workflow depends on these operations | Narrower scopes (`public_repo`, `project` only) tested and confirmed insufficient for private repo issue/PR write operations. GitHub App migration deferred as architectural change beyond audit scope. |
| Encryption enforcement is a breaking change | Existing deployments without `ENCRYPTION_KEY` will fail to start after upgrade | Warning-only mode defeats enforcement purpose. Migration path documented: generate key with `Fernet.generate_key()`, set env var, run one-time migration script for existing plaintext rows. |
