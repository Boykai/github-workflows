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

## Constitution Re-Check (Post-Design)

*Re-evaluated after Phase 1 design artifacts (research.md, data-model.md, contracts/, quickstart.md) are complete.*

### I. Specification-First Development — ✅ PASS

All design artifacts trace back to the spec's 49 FRs and 10 user stories. The data model entities (pipeline_runs, pipeline_stage_states, stage_groups, onboarding_tour_state) map directly to spec Key Entities. REST API contracts cover all spec-required endpoints. No scope creep introduced during design.

### II. Template-Driven Workflow — ✅ PASS

All generated artifacts follow canonical templates. Plan, research, data-model, contracts, and quickstart documents use the `.specify/templates/` structure. No custom sections were added without justification.

### III. Agent-Orchestrated Execution — ✅ PASS

The `speckit.plan` agent produced all Phase 0 and Phase 1 artifacts. The handoff to `speckit.tasks` is defined (tasks.md already exists from parallel agent work). Agent context file updated via `update-agent-context.sh copilot`.

### IV. Test Optionality with Clarity — ✅ PASS

Test requirements remain explicitly spec-mandated (FR-041 through FR-044). The quickstart documents all test commands. Phase D (parallel test coverage track) is scoped in the implementation phases below.

### V. Simplicity and DRY — ⚠️ PASS WITH JUSTIFICATION

Design artifacts introduce 4 new SQLite tables and 16 API endpoints. All are directly required by functional requirements — no speculative abstractions. The event system (pipeline state changes, MCP propagation) uses Python dataclasses rather than a heavyweight event bus. Complexity is tracked in the table above.

---

## Implementation Phases

The 49 functional requirements are organized into 9 implementation phases plus a parallel test coverage track. Phases are ordered by criticality (P1 release blockers first) and dependency (infrastructure before features). Within each phase, tasks can run in parallel where marked.

### Phase 1: Setup (T001–T005)

**Purpose**: Verify current state and prepare for phased delivery.
**Dependencies**: None.
**Duration estimate**: 1 day.

| Step | Task | Verification |
|------|------|-------------|
| 1.1 | Verify monorepo structure and "Solune" rebrand completeness | Directory tree matches Project Structure section above |
| 1.2 | Verify backend deps current (`pyproject.toml`) | `pip install -e ".[dev]"` succeeds |
| 1.3 | Verify frontend deps current (`package.json`) | `npm ci` succeeds |
| 1.4 | Verify CI pipeline passes | `ruff check`, `pyright`, `pytest`, `eslint`, `tsc`, `vitest` all green |
| 1.5 | Confirm migration chain integrity (023–028) | Backend starts with clean DB, no migration errors |

**Gate**: All 5 steps pass before proceeding.

---

### Phase 2: Security & Data Integrity — Release Blockers (T006–T026)

**Purpose**: Core security and pipeline state persistence. No feature work until complete.
**Dependencies**: Phase 1 complete.
**Duration estimate**: 5–7 days.
**User Stories**: US-1 (Pipeline Persistence, P1), US-2 (Security, P1).

#### Track A: Pipeline State Persistence (US-1, FR-001 through FR-003)

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 2A.1 | Create migration `029_pipeline_state_persistence.sql` | `backend/src/migrations/029_pipeline_state_persistence.sql` | Migration applies cleanly on fresh DB |
| 2A.2 | Add `access_control_enabled`, `visual_identifier`, `display_order` columns | Same migration file | Columns visible in schema |
| 2A.3 | Create Pydantic models for PipelineRun, PipelineStageState, StageGroup | `backend/src/models/pipeline_run.py`, `pipeline_stage_state.py`, `stage_group.py` | Models validate correctly |
| 2A.4 | Create PipelineStateService | `backend/src/services/copilot_polling/pipeline_state_service.py` | Pipeline runs persist to SQLite |
| 2A.5 | Startup state rebuild from DB | Same service file | Restart preserves pipeline state |
| 2A.6 | SQLite PRAGMA integrity_check on startup | Same service file | Corrupted DB falls back to in-memory |
| 2A.7 | Remove 500-entry cap | `backend/src/services/copilot_polling/` | 500+ runs accessible |
| 2A.8 | Transactional writes for concurrent updates | Same service file | No data races under concurrent writes |
| 2A.9 | Wire into FastAPI DI | `backend/src/dependencies.py` | Service injectable |

#### Track B: Security Critical Fixes (US-2, FR-004 through FR-008) — Parallel with Track A

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 2B.1 | HttpOnly + SameSite=Strict on session cookies | `backend/src/api/auth.py` | Cookie flags verified in browser |
| 2B.2 | Startup validation: ENCRYPTION_KEY | `backend/src/main.py` | Missing key → startup refused |
| 2B.3 | Startup validation: SESSION_SECRET_KEY | `backend/src/main.py` | Missing key → startup refused |
| 2B.4 | Startup validation: GITHUB_CLIENT_ID/SECRET | `backend/src/main.py` | Missing vars → startup refused |
| 2B.5 | Enumerate ALL missing vars in single error | `backend/src/main.py` | All missing vars listed at once |
| 2B.6 | Project-level access control middleware (403) | `backend/src/middleware/project_access.py` | Unauthorized → 403 |
| 2B.7 | Wire access control middleware | `backend/src/main.py` | Middleware active |
| 2B.8 | Audit for hardcoded secrets | All source files | `bandit -r src/` clean |
| 2B.9 | Pydantic validation at all API boundaries | `backend/src/api/` | Invalid input → 422 |
| 2B.10 | File upload sanitization | `backend/src/api/chat.py` | Path traversal blocked |

**Gate**: Pipeline state persists across restarts. Application refuses insecure config. All security checks pass.

---

### Phase 3: Code Quality — Clean Codebase (T027–T048)

**Purpose**: Refactor God class, reduce complexity, eliminate dead code, decompose frontend modules.
**Dependencies**: Phase 2 complete (avoids merge conflicts with security changes).
**Duration estimate**: 5–7 days.
**User Story**: US-3 (Clean Codebase, P2).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 3.1 | Remove dead code and unused artifacts | `backend/src/`, `frontend/src/` | No unused exports |
| 3.2 | Extract `resolve_repository()` utility | `backend/src/services/github_projects/utils.py` | One location, no duplicates |
| 3.3 | Decompose high-complexity functions (CC ≤25) | `backend/src/services/github_projects/service.py` | `ruff check --select C901` clean |
| 3.4 | Replace emoji state with typed enums | `backend/src/services/` | No emoji in business logic |
| 3.5 | Extract GitHubIssuesService | `backend/src/services/github_projects/issues_service.py` | Tests pass, file < 1,500 lines |
| 3.6 | Extract GitHubPRService | `backend/src/services/github_projects/pr_service.py` | Tests pass, file < 1,500 lines |
| 3.7 | Extract GitHubBranchesService | `backend/src/services/github_projects/branches_service.py` | Tests pass, file < 1,500 lines |
| 3.8 | Slim coordinator to < 1,500 lines | `backend/src/services/github_projects/service.py` | `wc -l` < 1,500 |
| 3.9 | Update imports and DI wiring | `backend/src/dependencies.py` | All services resolve |
| 3.10 | Split `usePipelineConfig` hook (616 lines) | `frontend/src/hooks/pipeline/` | Each hook < 200 lines |
| 3.11 | Split `GlobalSettings` component (380 lines) | `frontend/src/components/settings/` | Each component < 200 lines |
| 3.12 | Pin Docker base image digests | `backend/Dockerfile`, `frontend/Dockerfile` | Images pinned by SHA |
| 3.13 | Full static analysis pass | All source | `ruff`, `pyright`, `eslint`, `tsc` zero errors |

**Gate**: All backend files < 1,500 lines. All functions CC ≤ 25. All frontend modules < 200 lines. Zero static analysis errors.

---

### Phase 4: Pipeline Features — Label State & Run API (T049–T059)

**Purpose**: Label-based state tracking and pipeline run REST endpoints.
**Dependencies**: Phase 2 (pipeline persistence) + Phase 3 (God class split).
**Duration estimate**: 5 days.
**User Story**: US-1 (Pipeline Persistence, P1) — feature track.

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 4.1 | GitHub label manager for pipeline state | `backend/src/services/copilot_polling/label_manager.py` | Labels created/updated on GitHub |
| 4.2 | Label lifecycle (create/update/query) | Same file | Format: `solune:pipeline:{run_id}:stage:{stage_id}:{status}` |
| 4.3 | Recovery protocol (query labels on startup) | Same file | ~60% fewer API calls on recovery |
| 4.4 | Pipeline state change event dataclasses | `backend/src/models/pipeline_events.py` | Events emit correctly |
| 4.5 | Wire label manager as event consumer | `backend/src/services/copilot_polling/` | Labels sync with state |
| 4.6 | `POST /pipelines/{id}/runs` | `backend/src/api/pipelines.py` | 201 on create |
| 4.7 | `GET /pipelines/{id}/runs` | Same file | Paginated list, no cap |
| 4.8 | `GET /pipelines/{id}/runs/{run_id}` | Same file | Full state with stages/groups |
| 4.9 | `POST .../cancel` | Same file | 200 on cancel, 409 if terminal |
| 4.10 | `POST .../recover` | Same file | Resumes from last success |
| 4.11 | WebSocket pipeline state push | Same file | Frontend receives real-time updates |

**Gate**: Pipeline state fully persistent. Label-based recovery functional. All run endpoints pass contract tests.

---

### Phase 5: Visual Pipeline Builder & Groups (T060–T068)

**Purpose**: Drag-and-drop pipeline builder with sequential/parallel group execution.
**Dependencies**: Phase 4 (pipeline run API + label-based state).
**Duration estimate**: 5 days.
**User Story**: US-4 (Pipeline Builder, P2).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 5.1 | Group execution orchestrator | `backend/src/services/copilot_polling/group_executor.py` | Sequential groups block, parallel groups run simultaneously |
| 5.2 | `GET /pipelines/{id}/groups` | `backend/src/api/pipelines.py` | Lists groups with stage counts |
| 5.3 | `PUT /pipelines/{id}/groups` | Same file | Atomic group create/update |
| 5.4 | PipelineBuilder page component | `frontend/src/components/pipelines/PipelineBuilder.tsx` | Drag-drop stages into groups |
| 5.5 | StageGroup component | `frontend/src/components/pipelines/StageGroup.tsx` | Sequential/parallel toggle |
| 5.6 | DraggableStage component | `frontend/src/components/pipelines/DraggableStage.tsx` | Individual stage drag |
| 5.7 | `usePipelineGroups` hook | `frontend/src/hooks/pipeline/usePipelineGroups.ts` | Group CRUD via TanStack Query |
| 5.8 | Route + navigation | `frontend/src/App.tsx` | Builder accessible |
| 5.9 | Large pipeline handling (50+ stages) | PipelineBuilder component | Virtualized, zoom/pan (edge case #4) |

**Gate**: Users can create, configure, and run grouped pipelines via visual builder.

---

### Phase 6: Agent Orchestration & Parallel Layout (T069–T074)

**Purpose**: Side-by-side agent display and MCP tool synchronization.
**Dependencies**: Phase 3 (frontend decomposition). Parallel with Phase 5.
**Duration estimate**: 3 days.
**User Story**: US-5 (Agent Orchestration, P2).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 6.1 | ParallelAgentLayout component | `frontend/src/components/agents/ParallelAgentLayout.tsx` | Side-by-side display |
| 6.2 | AgentCard with visual identifiers | `frontend/src/components/agents/AgentCard.tsx` | Color/icon differentiation |
| 6.3 | `useParallelAgents` hook | `frontend/src/hooks/useParallelAgents.ts` | Agent state management |
| 6.4 | MCP config propagation on save | `backend/src/services/agents/` | Agent files updated |
| 6.5 | `PUT /projects/{id}/mcp-config` response update | `backend/src/api/` | Returns `agents_updated` count |

**Gate**: Two agents display side-by-side. MCP config propagates to all agent files.

---

### Phase 7: Remove Blocking Feature (T126–T129)

**Purpose**: Remove deprecated blocking/queue feature.
**Dependencies**: Phase 3 (God class split). Parallel with Phases 5–6.
**Duration estimate**: 1–2 days.

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 7.1 | Remove blocking UI components | `frontend/src/components/` | No blocking UI references |
| 7.2 | Remove blocking backend logic | `backend/src/services/`, `backend/src/api/` | No blocking endpoints |
| 7.3 | Remove blocking data/migration | `backend/src/migrations/` | Clean schema |
| 7.4 | Verify no dead references | Full codebase grep | Zero references to blocking/queue |

**Gate**: Blocking feature fully removed. No orphaned code.

---

### Phase 8: Chat & Voice Enhancements (T075–T081)

**Purpose**: Fix voice input cross-browser, file attachments, issue paste.
**Dependencies**: Phase 3 complete (code quality baseline).
**Duration estimate**: 3 days.
**User Story**: US-7 (Chat & Voice, P3).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 8.1 | Fix voice input for Firefox | `frontend/src/components/chat/` | Speech recognized in Firefox |
| 8.2 | Fix voice input for Chrome | Same directory | Speech recognized in Chrome |
| 8.3 | Unsupported browser message | Same directory | Clear message shown (edge case #5) |
| 8.4 | File attachment upload to GitHub | `backend/src/api/chat.py`, `frontend/src/components/chat/` | File appears on GitHub issue |
| 8.5 | Failed attachment error handling | Same files | Message sent, attachment error inline (edge case #7) |
| 8.6 | Issue description paste + pipeline config | `backend/src/api/`, `frontend/src/` | Issue created with config association |

**Gate**: Voice works in Chrome + Firefox. Attachments upload to GitHub. Issue paste functional.

---

### Phase 9: Performance Optimization (T093–T102)

**Purpose**: Reduce idle API calls, improve caching, optimize rendering.
**Dependencies**: Phase 5 complete (features stabilized before optimization).
**Duration estimate**: 3–4 days.
**User Story**: US-9 (Performance, P3).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 9.1 | Establish baseline metrics | Measurement script | Idle req/min, load times, render counts recorded |
| 9.2 | Backend Cache-Control + ETag headers | `backend/src/api/`, `backend/src/middleware/` | 304 Not Modified for unchanged data |
| 9.3 | Frontend staleTime tuning | `frontend/src/constants.ts`, hooks | Fewer refetches for stable data |
| 9.4 | Disable refetch on window focus for non-critical | Query configurations | Reduced idle calls |
| 9.5 | React.memo + useMemo for expensive renders | `frontend/src/components/` | Profiler shows targeted rerenders |
| 9.6 | Virtualized lists for 50+ pipeline runs | `frontend/src/components/pipelines/` | Smooth scroll at 60fps |
| 9.7 | Measure post-optimization metrics | Same measurement script | ≥50% idle reduction, ≥30% cache improvement |

**Gate**: ≥50% idle API call reduction. ≤2s page loads. 60fps scrolling.

---

### Phase 10: Accessibility & Visual Polish (T103–T111)

**Purpose**: WCAG AA compliance, keyboard navigation, responsive layouts.
**Dependencies**: Phase 5 complete (visual features finalized).
**Duration estimate**: 3–4 days.
**User Story**: US-6 (Accessibility, P3).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 10.1 | Run contrast audit | `npm run audit:theme-contrast` | Baseline established |
| 10.2 | Replace hardcoded colors with theme tokens | `frontend/src/` | `npm run audit:theme-colors` clean |
| 10.3 | Fix contrast ratio violations (4.5:1 / 3:1) | Theme files, components | Audit passes WCAG AA |
| 10.4 | Add `focus-visible:ring-2` to all interactive elements | `frontend/src/components/` | Keyboard focus visible |
| 10.5 | Full keyboard navigation audit | All pages | Tab order correct, all actions reachable |
| 10.6 | Responsive layout fixes (320px–1920px) | `frontend/src/` | No overflow/overlap at breakpoints |
| 10.7 | Theme switching with modals open (edge case #8) | Theme provider | Immediate theme application |

**Gate**: WCAG AA contrast passes. Full keyboard navigation. Responsive at all breakpoints.

---

### Phase 11: Documentation & Onboarding (T112–T125)

**Purpose**: Fresh docs, interactive tour, Help page, API docs.
**Dependencies**: Phase 5 complete (features documented match actual behavior).
**Duration estimate**: 4 days.
**User Story**: US-8 (Documentation, P3).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| 11.1 | Audit all docs against current behavior | `solune/docs/` | All docs accurate |
| 11.2 | Update setup guide (≤30 min first-time) | `solune/docs/setup.md` | Fresh install succeeds within 30 min |
| 11.3 | 9-step onboarding tour implementation | `frontend/src/components/onboarding/` | Tour completes all 9 steps |
| 11.4 | Onboarding state API endpoints | `backend/src/api/` | GET/PUT onboarding state |
| 11.5 | Tour dismiss/resume/restart (edge case #6) | Same files | State persists, restart from Help page |
| 11.6 | Help page with FAQ | `frontend/src/pages/HelpPage.tsx` | 10 most common questions answered |
| 11.7 | Export OpenAPI docs | `backend/src/main.py` | `/openapi.json` includes all endpoints |
| 11.8 | Architecture diagrams refresh | `solune/docs/` | Diagrams reflect current architecture |

**Gate**: Setup guide works from scratch. Tour completes. FAQ covers top 10 questions.

---

### Phase D: Test Coverage (Parallel Track — runs alongside Phases 3–11)

**Purpose**: Close coverage gaps to meet release gates.
**Dependencies**: Phase 2 complete (code under test must be stable enough to test).
**Duration estimate**: Continuous, 10–14 days total.
**User Stories**: Cross-cutting (FR-041 through FR-044).

#### Backend: 71% → ≥80% (T130–T140)

| Step | Task | Verification |
|------|------|-------------|
| D.1 | Parameterized API tests (200, 401, 403, 404, 422, 429, 500) | Each status code covered |
| D.2 | Property-based tests (Hypothesis) for pipeline state | Hypothesis finds no failures |
| D.3 | Fuzz testing (webhook payloads, chat injection) | No crashes on malformed input |
| D.4 | Pipeline state persistence tests | State survives restart |
| D.5 | Security middleware tests | Auth, CSRF, rate limiting verified |
| D.6 | CI coverage ratchet — blocks on decrease | Coverage never drops |

#### Frontend: 49% → ≥70% (T141–T149)

| Step | Task | Verification |
|------|------|-------------|
| D.7 | Component tests (Testing Library) for pipeline builder | All interactions covered |
| D.8 | Hook tests for split pipeline hooks | Each hook tested independently |
| D.9 | Playwright E2E: 10+ new specs | Full user flows pass |
| D.10 | Visual regression (3 viewports × light/dark = 42 snapshots) | No unexpected visual changes |
| D.11 | Contract testing with schemathesis | API responses match contracts |
| D.12 | Accessibility assertions in E2E | `axe-core` passes on every page |

#### Mutation & Flaky Management (T150+)

| Step | Task | Verification |
|------|------|-------------|
| D.13 | Backend mutation score ≥75% (mutmut) | `mutmut run` by shard passes |
| D.14 | Frontend mutation score ≥60% (Stryker) | `npm run test:mutate` passes |
| D.15 | Nightly flaky detection | Max 5 quarantined tests |

**Gate**: ≥80% backend coverage. ≥70% frontend coverage. ≥75%/60% mutation scores.

---

### Phase E: Release Engineering — Final Gate (T150–T161)

**Purpose**: Version consistency, Docker hardening, startup validation, release checklist.
**Dependencies**: All previous phases complete.
**Duration estimate**: 2–3 days.
**User Story**: US-10 (Production Release, P1).

| Step | Task | Files | Verification |
|------|------|-------|-------------|
| E.1 | Verify `0.1.0` in all configs | `pyproject.toml`, `package.json`, `CHANGELOG.md` | `grep -r "0.1.0"` consistent |
| E.2 | Verify Docker base images remain pinned (done in Phase 3, step 3.12) | All Dockerfiles | SHA256 pinned, no floating tags |
| E.3 | Non-root container verification | Dockerfiles | Processes run as non-root |
| E.4 | `.env.example` completeness | `solune/.env.example` | All required vars documented |
| E.5 | Fail-fast on missing/invalid env vars | `backend/src/main.py` | Startup lists all failures at once |
| E.6 | `GET /api/v1/health` includes startup state | `backend/src/api/` | Health response per contracts/rest-api.md |
| E.7 | `docker compose up --build` → 3 healthy | `solune/docker-compose.yml` | All services healthy in ≤120s |
| E.8 | Full E2E pass | Playwright suite | All specs pass |
| E.9 | Security scans clean | `bandit`, `npm audit` | Zero critical/high |
| E.10 | CHANGELOG finalized | `solune/CHANGELOG.md` | v0.1.0 entry complete |
| E.11 | Git tag `v0.1.0` | Repository | Tag created |

**Gate**: Zero open P1/P2 bugs. All verification checks pass. Ready for release.

---

## Dependency Graph

```text
Phase 1 (Setup)
    │
    ├──► Phase 2A (Pipeline Persistence) ──┐
    │                                       ├──► Phase 3 (Code Quality) ──┬──► Phase 4 (Label State + Run API)
    └──► Phase 2B (Security) ─────────────┘                              │       │
                                                                          │       └──► Phase 5 (Pipeline Builder)
                                                                          │
                                                                          ├──► Phase 6 (Agent Orchestration) [parallel w/ Phase 5]
                                                                          ├──► Phase 7 (Remove Blocking) [parallel w/ Phases 5-6]
                                                                          │
                                                                          └──► Phase D (Test Coverage) [parallel track, continuous]
                                                                          
    Phase 5 complete ──► Phase 8 (Chat & Voice)
                    ──► Phase 9 (Performance)
                    ──► Phase 10 (Accessibility)
                    ──► Phase 11 (Documentation)
                    
    All phases complete ──► Phase E (Release Engineering)
```

## Risk Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Frontend coverage gap (49% → 70%) | Highest risk — 21-point gap in limited time | Start Phase D immediately alongside Phase 2. Fallback: ship at 60% with tracked post-release commitment |
| God class split (5,338 lines → 3 services) | Highest regression risk refactor | Complete early in Phase 3 for maximum regression detection time. Incremental extraction, one service at a time |
| Prior feature validation (037–042) | Merge conflicts if features incomplete | Verify completeness in Phase 1 setup before starting any work |
| Pipeline state migration | Data integrity risk on schema change | Migration is additive (new tables only). No existing table modifications except adding nullable columns |
| Performance baselines after feature work | Measurements may miss optimization opportunities | Establish rough baselines during Phase 3, formal baselines in Phase 9 |

## Verification Summary

| Check | Command | Gate | Phase |
|-------|---------|------|-------|
| Backend tests | `pytest tests/ -v --tb=short` | Zero regressions | Each phase |
| Frontend tests | `npx vitest run` | Zero regressions | Each phase |
| Backend coverage | `pytest --cov --cov-branch` | ≥80% | Phase D |
| Frontend coverage | `npm run test:coverage` | ≥70% | Phase D |
| Backend mutation | `mutmut run` (by shard) | ≥75% | Phase D |
| Frontend mutation | `npm run test:mutate` | ≥60% | Phase D |
| Security | `bandit -r src/` + `npm audit` | Zero critical/high | Phase E |
| Type checking | `pyright src` + `npm run type-check` | Zero errors | Phase 3, E |
| Docker health | `docker compose up --build` | All healthy in ≤120s | Phase E |
| E2E | `npx playwright test` | All specs pass | Phase E |
