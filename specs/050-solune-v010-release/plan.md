# Implementation Plan: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/050-solune-v010-release/spec.md`

## Summary

Ship a public-ready v0.1.0 of Solune covering 49 functional requirements across 9 phases. The release addresses critical data integrity (pipeline state persistence to SQLite), security hardening (cookie flags, encryption enforcement, access control), code quality refactoring (God class split, complexity reduction), core feature delivery (visual pipeline builder, parallel agents, chat enhancements), accessibility compliance (WCAG AA), documentation refresh, test coverage closure (80% backend, 70% frontend), and release engineering (Docker Compose deployment). The existing web application architecture (Python/FastAPI backend + React/Vite frontend + SQLite) is retained with no new infrastructure dependencies.

## Technical Context

**Language/Version**: Python 3.13 (backend runtime, 3.12 CI), TypeScript ~5.9 (frontend)
**Primary Dependencies**: FastAPI >=0.135, React 19.2, Vite 7.3, TanStack Query 5.90, Tailwind CSS 4.2, @dnd-kit (drag-and-drop), Pydantic 2.12, aiosqlite, cryptography 46
**Storage**: SQLite via aiosqlite (async), SQL-based migrations in `backend/src/migrations/`
**Testing**: pytest 9 (backend, 71% → 80% target), Vitest 4 (frontend, 50% → 70% target), Playwright 1.58 (E2E), Stryker/mutmut (mutation), Hypothesis (property-based)
**Target Platform**: Linux server (Docker Compose), modern browsers (Chrome, Firefox, Edge, Safari)
**Project Type**: web (frontend + backend)
**Performance Goals**: Sub-2s page loads, 100ms interaction response, 60fps scroll, ≥50% idle API call reduction, ≥30% cache hit improvement
**Constraints**: Docker Compose only (no cloud), SQLite only (no external DB), OAuth via GitHub, WCAG AA compliance
**Scale/Scope**: Single-user to small-team local deployment, ~15 pages/views, ~30 API endpoints, 3 Docker services (backend, frontend, signal-api)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature spec (`spec.md`) contains 10 prioritized user stories (P1/P2/P3), each with Given-When-Then acceptance scenarios, independent test criteria, and clear priority justification. 49 functional requirements are enumerated with measurable success criteria (SC-001 through SC-015). Scope boundaries are explicitly declared (Docker Compose only, no cloud deployment, excluded specs listed).

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. The spec follows `spec-template.md`. The checklist in `checklists/requirements.md` follows `checklist-template.md`. No custom sections are introduced without justification.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent with single responsibility: generate implementation plan artifacts. It consumes the spec (previous phase output) and produces plan.md, research.md, data-model.md, contracts/, and quickstart.md. The next handoff is to `speckit.tasks` for task decomposition.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are explicitly required by the spec: FR-041 (80% backend coverage), FR-042 (70% frontend coverage), FR-043 (E2E flows), FR-044 (accessibility assertions). The spec mandates test coverage as a release gate. Phase 8 is dedicated to test coverage gap closure. This is not opt-in — it is spec-mandated.

### V. Simplicity and DRY — ⚠️ PASS WITH JUSTIFICATION

The release scope (24 specs, 49 FRs, 9 phases) is inherently complex. However, this is a coordinated release plan, not a single feature. Each phase is independently scoped with clear dependencies. Complexity is justified by the release scope and tracked below.

## Project Structure

### Documentation (this feature)

```text
specs/050-solune-v010-release/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── rest-api.md      # REST API contracts for new/modified endpoints
│   └── events.md        # Internal event contracts (pipeline state, webhooks)
├── checklists/          # Existing checklist from speckit.specify
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI route handlers (agents, apps, auth, board, chat, pipelines, etc.)
│   │   ├── models/           # Pydantic models and domain types
│   │   ├── services/         # Business logic layer
│   │   │   ├── copilot_polling/   # Pipeline state persistence, polling, recovery
│   │   │   ├── github_projects/   # GitHub Projects integration (God class target)
│   │   │   │   └── service.py     # 5,338-line God class → split into issues, PR, branches services
│   │   │   ├── agents/            # Agent orchestration services
│   │   │   └── chores/            # Chore management services
│   │   ├── middleware/       # CSRF, CSP, rate limiting, admin guard, request ID
│   │   ├── migrations/       # SQL migration files (023–028+)
│   │   ├── prompts/          # AI prompt templates
│   │   ├── main.py           # FastAPI app entry, middleware registration, startup
│   │   ├── config.py         # Pydantic settings (env var management)
│   │   └── dependencies.py   # FastAPI dependency injection
│   ├── tests/
│   │   ├── unit/             # Unit tests
│   │   ├── property/         # Hypothesis property-based tests
│   │   ├── fuzz/             # Fuzz tests
│   │   ├── chaos/            # Chaos tests
│   │   └── concurrency/      # Concurrency tests
│   ├── Dockerfile            # python:3.13-slim, non-root appuser
│   └── pyproject.toml        # Python project config, dependencies, tool settings
├── frontend/
│   ├── src/
│   │   ├── components/       # React components (agents/, apps/, board/, chat/, settings/, etc.)
│   │   ├── pages/            # Page-level components
│   │   ├── hooks/            # Custom React hooks (usePipelineConfig 616 lines → split target)
│   │   ├── services/         # API client layer
│   │   ├── context/          # React context providers
│   │   ├── utils/            # Utility functions
│   │   ├── types/            # TypeScript type definitions
│   │   ├── constants.ts      # App constants (stale times, query keys)
│   │   └── App.tsx           # Root component with routing
│   ├── tests/                # Vitest unit/component tests
│   ├── e2e/                  # Playwright E2E tests
│   ├── Dockerfile            # Multi-stage: node:22-alpine build → nginx:1.27-alpine serve
│   ├── package.json          # npm dependencies and scripts
│   └── playwright.config.ts  # E2E test configuration
├── docs/                     # Documentation (setup, config, API, architecture)
├── docker-compose.yml        # 3 services: backend, frontend, signal-api
├── .env.example              # Environment variable template
└── scripts/                  # Utility scripts (diagrams, contracts validation)
```

**Structure Decision**: Existing web application structure is retained. No new top-level directories or services are introduced. All changes occur within the existing `solune/backend/` and `solune/frontend/` directories. The God class split (step 6) creates new files within `solune/backend/src/services/github_projects/` but does not change the directory hierarchy. Frontend decomposition (step 7) splits existing files into sub-modules within their current directories.

## Complexity Tracking

> Justified violations of Constitution Principle V (Simplicity and DRY).

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 49 functional requirements in single spec | This is a coordinated release encompassing 24 sub-specs across 9 phases. Each FR maps to a specific, independently verifiable capability. | Splitting into 24 separate specs would lose release-level coordination, dependency tracking, and unified success criteria. The parent issue already manages sub-spec decomposition. |
| 9-phase execution with complex dependency graph | Phases are ordered by criticality (security first) and dependency (refactoring before features). Parallelism is maximized within constraints. | A flat task list would miss critical ordering (e.g., pipeline persistence before label-based state) and allow unsafe parallelism (e.g., features before security fixes). |
| God class split producing 3+ new service files | The current 5,338-line `service.py` violates FR-009 (1,500-line limit) and is the primary contributor to maintenance burden. | Leaving the God class intact contradicts FR-009 and blocks the code quality user story (US-3). Partial splits would create inconsistent module boundaries. |
