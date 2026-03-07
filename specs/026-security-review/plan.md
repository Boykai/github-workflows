# Implementation Plan: Security, Privacy & Vulnerability Audit

**Branch**: `026-security-review` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-security-review/spec.md`

## Summary

Remediate 21 security findings (3 Critical, 8 High, 9 Medium, 2 Low) across OWASP Top 10 categories in a phased approach. Changes span the FastAPI backend (auth, config, webhooks, database, API endpoints), React frontend (auth hook, chat history, avatar validation), nginx configuration (security headers), Docker infrastructure (non-root containers, port bindings, volume mounts), and GitHub Actions (workflow permissions). Each phase is independently deployable with behavior-based verification checks.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.9 (frontend), Node 22 (build)
**Primary Dependencies**: FastAPI, githubkit, pydantic 2.x, aiosqlite, cryptography/Fernet, React 19.2, TanStack Query, Vite 7.3, slowapi (new — rate limiting)
**Storage**: SQLite with WAL mode (aiosqlite) — sessions, settings, encrypted OAuth tokens
**Testing**: pytest + pytest-asyncio (backend), Vitest (frontend)
**Target Platform**: Docker Compose (Linux containers), nginx reverse proxy
**Project Type**: Web application (FastAPI backend + React frontend)
**Performance Goals**: Rate limiting must not degrade normal usage; per-user limits preferred over per-IP to avoid shared-NAT penalties
**Constraints**: Zero feature regressions; existing deployments without ENCRYPTION_KEY need migration path; OAuth scope change requires user re-authorization
**Scale/Scope**: ~15 backend files, ~5 frontend files, 2 Dockerfiles, 1 nginx.conf, 1 docker-compose.yml, 1 GitHub Actions workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS

Feature work began with explicit specification (spec.md) containing 10 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios for each, clear scope boundaries (out of scope: GitHub API security, MCP internals, network infrastructure), and edge case analysis.

### II. Template-Driven Workflow — PASS

All artifacts follow canonical templates: spec.md from spec-template, plan.md from plan-template. No custom sections added without justification.

### III. Agent-Orchestrated Execution — PASS

Workflow follows the specify → plan → tasks → implement sequence. Each phase produces specific outputs and hands off to the next agent.

### IV. Test Optionality with Clarity — PASS

The spec defines 12 measurable success criteria (SC-001 through SC-012), most verified via behavior-based checks (startup rejection, HTTP header inspection, filesystem permissions, API response codes). New unit tests are not mandated — existing tests serve as regression gates. Tests may be added during implementation for critical paths (auth, authorization) at implementer discretion.

### V. Simplicity and DRY — PASS

Changes are strictly scoped to security remediation. No architectural refactoring beyond what is required to fix the findings. New abstractions are limited to: (1) centralized project ownership check (FR-007 — required by spec), (2) rate limiting middleware via slowapi (FR-017/018 — single library, no custom framework). Both justified by security requirements, not premature abstraction.

**GATE RESULT: ALL PASS — proceed to Phase 0.**

### Post-Phase 1 Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All 30 FRs traced to design artifacts |
| II. Template-Driven | ✅ PASS | All plan artifacts follow templates |
| III. Agent-Orchestrated | ✅ PASS | Plan → tasks → implement pipeline maintained |
| IV. Test Optionality | ✅ PASS | Behavior-based verification; no unnecessary test mandates |
| V. Simplicity/DRY | ✅ PASS | One new dependency (slowapi); one new shared dependency (project auth); no over-engineering |

## Project Structure

### Documentation (this feature)

```text
specs/026-security-review/
├── plan.md              # This file
├── spec.md              # Feature specification (complete)
├── research.md          # Phase 0: Security remediation research
├── data-model.md        # Phase 1: Entity definitions (Session, RateLimit, ChatMessageRef)
├── quickstart.md        # Phase 1: Verification commands
├── contracts/           # Phase 1: Config and API contracts
│   ├── config-contracts.md
│   └── nginx-contracts.md
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── auth.py              # FR-001,002,013: Cookie-based auth, POST dev-login
│   │   ├── signal.py            # FR-009: Constant-time secret comparison
│   │   ├── webhooks.py          # FR-021: Remove debug bypass
│   │   ├── tasks.py             # FR-006,007: Project ownership check
│   │   ├── projects.py          # FR-006,007,008: Project ownership + WebSocket auth
│   │   ├── settings.py          # FR-006,007: Project ownership check
│   │   ├── workflow.py          # FR-006,007: Project ownership check
│   │   ├── chat.py              # FR-017: Rate limiting
│   │   └── agents.py            # FR-017: Rate limiting
│   ├── services/
│   │   ├── github_auth.py       # FR-001,014: Cookie-based session, OAuth scopes
│   │   ├── encryption.py        # FR-003: Mandatory encryption key
│   │   ├── database.py          # FR-023: Restricted directory/file permissions
│   │   └── github_projects/
│   │       └── service.py       # FR-028: Sanitized GraphQL errors
│   ├── middleware/
│   │   └── rate_limit.py        # FR-017,018,019: Rate limiting middleware (new)
│   ├── config.py                # FR-003,004,015,020,022,024: Startup validation
│   ├── main.py                  # FR-022: ENABLE_DOCS toggle
│   └── dependencies.py          # FR-007: Centralized project auth dependency
├── Dockerfile                   # Already non-root (appuser)
└── tests/                       # Regression gate

frontend/
├── src/
│   ├── hooks/
│   │   ├── useAuth.ts           # FR-002: Remove URL token reading
│   │   └── useChatHistory.ts    # FR-026,027: Lightweight refs, logout clear
│   └── components/
│       └── board/
│           └── IssueCard.tsx    # FR-030: Avatar URL validation
├── nginx.conf                   # FR-010,011,012: Security headers
└── Dockerfile                   # FR-005: Non-root nginx user

docker-compose.yml               # FR-016,025: Localhost binding, external volume mount

.github/workflows/
└── branch-issue-link.yml        # FR-029: Scoped permissions with comments
```

**Structure Decision**: Existing web application layout (backend/ + frontend/). No new directories except `backend/src/middleware/` for rate limiting (if not already present). All changes are in-place modifications to existing files.

## Complexity Tracking

> No constitution violations. No complexity justification needed.
>
> The centralized project ownership dependency (FR-007) and rate limiting middleware (FR-017/018) are new abstractions, but both are explicitly required by the security specification and follow standard FastAPI patterns (Depends injection, middleware). They represent minimum viable security infrastructure, not premature abstraction.
