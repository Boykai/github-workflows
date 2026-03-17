# Implementation Plan: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/050-solune-v010-release/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Ship a public-ready v0.1.0 of Solune covering 49 functional requirements across 10 user stories in 9 implementation phases. The release addresses critical data integrity (pipeline state persistence to SQLite), security hardening (cookie flags, encryption enforcement, access control), code quality refactoring (God class split, complexity reduction), core feature delivery (visual pipeline builder, parallel agents, chat enhancements), accessibility compliance (WCAG AA), documentation refresh, test coverage closure (≥80% backend, ≥70% frontend with mutation testing), and release engineering (Docker Compose deployment). The existing web application architecture (Python/FastAPI backend + React/Vite frontend + SQLite) is retained with no new infrastructure dependencies.

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

## Constitution Check — Post-Design Re-Evaluation

*GATE: Re-evaluated after Phase 1 design artifacts are complete.*

### I. Specification-First Development — ✅ PASS

All Phase 1 design artifacts directly trace back to spec requirements:
- `data-model.md` entities map to Key Entities in spec (Pipeline Run, Stage Group, Onboarding Tour State, etc.)
- `contracts/rest-api.md` endpoints map to functional requirements (FR-001→FR-003, FR-015→FR-017, FR-038, FR-021, FR-022)
- `contracts/events.md` internal events derive from pipeline state lifecycle in spec (US-1, US-4, US-5)
- No design artifacts introduce requirements not traceable to the spec

### II. Template-Driven Workflow — ✅ PASS

All generated artifacts follow the canonical structure:
- `plan.md` follows `plan-template.md` with all required sections filled
- `research.md` uses Decision/Rationale/Alternatives format for each research item
- `data-model.md` uses structured Entity/Fields/Validation/Indexes format
- `contracts/` documents follow REST API and event contract conventions

### III. Agent-Orchestrated Execution — ✅ PASS

Phase 0 (research.md) and Phase 1 (data-model.md, contracts/, quickstart.md) artifacts are complete. This plan is ready for handoff to `speckit.tasks` for Phase 2 task decomposition. All inputs are explicit and documented.

### IV. Test Optionality with Clarity — ✅ PASS

Tests remain spec-mandated (FR-041 through FR-044, FR-050 through FR-052). The design artifacts (data model, API contracts) provide clear contract surfaces for test generation. Mutation testing requirements (FR-050: ≥75% backend, FR-051: ≥60% frontend) and flaky test limits (FR-052: max 5 quarantined) are incorporated into the verification plan.

### V. Simplicity and DRY — ⚠️ PASS WITH JUSTIFICATION (unchanged)

No new complexity was introduced during the design phase. The data model adds 4 new tables (pipeline_runs, pipeline_stage_states, stage_groups, onboarding_tour_state) and extends 2 existing tables — the minimum needed to satisfy FR-001 through FR-003 and FR-038. The API contracts add 12 new endpoints and modify 3 existing ones, each directly mapped to a functional requirement.

## Generated Artifacts

| Artifact | Path | Phase | Description |
|----------|------|-------|-------------|
| Research | [research.md](./research.md) | Phase 0 | 10 research items resolving all technical unknowns |
| Data Model | [data-model.md](./data-model.md) | Phase 1 | 8 entities, relationships, state transitions, migration plan |
| REST API Contracts | [contracts/rest-api.md](./contracts/rest-api.md) | Phase 1 | 12 new + 3 modified endpoints with request/response schemas |
| Event Contracts | [contracts/events.md](./contracts/events.md) | Phase 1 | Pipeline state events, WebSocket messages, GitHub label format |
| Quickstart | [quickstart.md](./quickstart.md) | Phase 1 | Local dev setup, test commands, Docker build, release checklist |
| Requirements Checklist | [checklists/requirements.md](./checklists/requirements.md) | Pre-existing | FR verification checklist from speckit.specify |

## Execution Phases Overview

The implementation follows a strict phase ordering based on criticality and dependency:

```text
Phase A: Foundation & Critical Path (P1 — Release Blockers)
├── Step 1: Setup & Repo Validation (T001–T005) — no dependencies
├── Step 2: Pipeline State Persistence (US-1, T006–T016) — depends on Step 1
└── Step 3: Security Hardening (US-2, T017–T026) — parallel with Step 2

Phase B: Code Quality & Features (P2)
├── Step 4: God Class Split (US-3, T027–T048) — depends on Phase A
├── Step 5: Visual Pipeline Builder (US-4, T049–T068) — depends on Step 4
├── Step 6: Agent Orchestration (US-5, T069–T074) — depends on Step 4, parallel with Step 5
└── Step 7: Remove Blocking Feature (T126–T129) — depends on Step 4, parallel with Steps 5–6

Phase C: Polish (P3)
├── Step 8: Chat & Voice Enhancements (US-7, T075–T081) — depends on Phase B
├── Step 9: Performance Optimization (US-9, T093–T102) — depends on Phase B
├── Step 10: Accessibility & Visual Polish (US-6, T103–T111) — depends on Phase B
└── Step 11: Documentation & Onboarding (US-8, T112–T125) — depends on Phase B

Phase D: Test Coverage (Parallel Track — runs alongside Phases B & C)
├── Step 12: Backend 71% → ≥80% (T130–T140)
├── Step 13: Frontend 49% → ≥70% (T141–T149)
└── Step 14: Mutation & Flaky Management

Phase E: Release Engineering (Final Gate — US-10, T150–T161)
├── Step 15: Version & Docker Consistency
├── Step 16: Startup Validation
└── Step 17: Release Verification Checklist
```

### Critical Path

The critical path to release runs through:
1. **Phase A** → Pipeline persistence + security (release blockers)
2. **Phase B Step 4** → God class split (highest-risk refactor, unblocks all P2 features)
3. **Phase D** → Test coverage closure (starts in parallel with Phase A, must complete before Phase E)
4. **Phase E** → Release verification (final gate)

### Risk Mitigations

| Risk | Mitigation | Fallback |
|------|-----------|----------|
| Frontend coverage gap (49% → 70%) | Start Phase D immediately alongside Phase A | Ship at 60% with tracked post-release commitment |
| God class split regressions | Complete early in Phase B for maximum regression discovery time | Incremental extraction (one domain at a time) |
| Prior feature validation (037–042) | Phase 1 Step 1 explicitly verifies merge status | Block Phase B until confirmed |
