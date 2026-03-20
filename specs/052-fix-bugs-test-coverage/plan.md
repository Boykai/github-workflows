# Implementation Plan: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Branch**: `052-fix-bugs-test-coverage` | **Date**: 2026-03-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/052-fix-bugs-test-coverage/spec.md`
**Predecessor**: `050-fix-bugs-test-coverage` (42% complete — 4 critical bugs fixed, infrastructure established) and `051-fix-bugs-test-coverage` (planning completed with 67 tasks across 5 user stories).

## Summary

Phase 2 of the systematic test coverage and quality improvement effort across the Solune monorepo. Phase 1 (050) fixed all 4 critical bugs (mutmut trampoline, cache leakage, AsyncMock warnings, pipeline stuck state) and established infrastructure. This phase completes the static analysis sweep, expands test coverage to meet ratcheted thresholds, verifies mutation kill rates, and locks in CI enforcement.

**Key targets**: Backend line coverage 75% → 80%, frontend statement/branch/function coverage 50%/44%/41% → 55%/50%/45%, mutation kill rates verified across all 5 shards, zero flaky tests, zero lint/type-check violations.

## Technical Context

**Language/Version**: Python ≥3.12 (backend, pyright targets 3.13), TypeScript ~5.9.0 (frontend)
**Primary Dependencies**: FastAPI ≥0.135 (backend), React 19.2 (frontend), Pydantic ≥2.12 (backend), Vite 8 (frontend), TanStack Query v5.91 (frontend), Tailwind CSS 4.2 (frontend), @dnd-kit (frontend drag-drop)
**Storage**: SQLite via aiosqlite ≥0.22 (existing — no changes in this feature)
**Testing**: pytest ≥9.0 + pytest-asyncio ≥1.3 + Hypothesis ≥6.131 (backend), Vitest ≥4.0.18 + @testing-library/react 16.3 (frontend), Playwright ≥1.58 (E2E), mutmut ≥3.2 (backend mutation, 5 shards), Stryker ≥9.6 (frontend mutation)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend monorepo under `apps/solune/`)
**Performance Goals**: Pre-commit hooks complete in <30 seconds on changed files; mutation testing shards complete within CI timeout
**Constraints**: No DRY refactoring — characterization tests only; thresholds only ratchet upward; no existing tests removed or modified to meet thresholds
**Scale/Scope**: ~87 backend unit test files + 9 integration + 5 property + 3 fuzz + 9 chaos/concurrency, ~134 frontend test files + 17 E2E specs, 27+ service modules, 5 mutation shards (4 backend services + 1 api-and-middleware)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature work began with explicit specification (`spec.md`)
- ✅ Prioritized user stories (P1–P5) with independent testing criteria
- ✅ Given-When-Then acceptance scenarios for each story
- ✅ Clear scope boundaries (DRY refactoring explicitly excluded)
- ✅ Predecessor specs (050, 051) baseline documented

### Principle II: Template-Driven Workflow ✅ PASS

- ✅ All artifacts follow canonical templates from `.specify/templates/`
- ✅ Plan, research, data-model, contracts, quickstart generated per template structure
- ✅ No custom sections added without justification

### Principle III: Agent-Orchestrated Execution ✅ PASS

- ✅ Plan phase produces well-defined outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md)
- ✅ Explicit handoff to subsequent phases (tasks generation, implementation)
- ✅ Single-responsibility: this plan phase does not implement code changes

### Principle IV: Test Optionality with Clarity ✅ PASS

- ✅ Tests are the *primary deliverable* of this feature — explicitly requested in spec
- ✅ Testing phases follow clear ordering (static analysis → coverage expansion → mutation → enforcement)
- ✅ Test types are appropriate to each target (unit, integration, property-based, component)

### Principle V: Simplicity and DRY ✅ PASS

- ✅ No new abstractions introduced — working within existing test infrastructure
- ✅ DRY refactoring explicitly deferred (characterization tests first)
- ✅ Uses existing tools (pytest, vitest, mutmut, stryker) — no new tool adoption
- ✅ Pre-commit hooks already exist — only verification needed, not creation

## Project Structure

### Documentation (this feature)

```text
specs/052-fix-bugs-test-coverage/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation guide
├── spec.md              # Feature specification (/speckit.specify output)
├── contracts/           # Phase 1 output — quality gate contracts
│   ├── quality-gates.md         # Coverage and quality thresholds
│   └── verification-commands.md # Verification command reference
├── checklists/
│   └── requirements.md         # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
apps/solune/
├── backend/
│   ├── src/
│   │   ├── api/                    # 19 route modules: auth, board, chat, agents, apps, chores,
│   │   │                           #   cleanup, health, mcp, metadata, onboarding, pipelines,
│   │   │                           #   projects, settings, signal, tasks, tools, webhooks, workflow
│   │   ├── middleware/             # 5 modules: admin_guard, csp, rate_limit, request_id, session
│   │   ├── models/                 # 22 Pydantic data models
│   │   ├── services/               # 27+ service modules (mutation target: current + expand)
│   │   │   ├── copilot_polling/    # pipeline, polling_loop, label_manager, recovery,
│   │   │   │                       #   state_validation (fixed in 050, edge-case targets)
│   │   │   ├── workflow_orchestrator/  # orchestrator, config, models, transitions
│   │   │   ├── github_projects/    # agents, board, issues, projects, pull_requests,
│   │   │   │                       #   graphql, copilot, branches, identities, repository, service
│   │   │   ├── agents/             # Agent service modules
│   │   │   ├── chores/             # Chore scheduling and execution
│   │   │   ├── tools/              # Tool registry
│   │   │   ├── pipelines/          # Pipeline management
│   │   │   ├── cache.py            # Fixed in 050
│   │   │   ├── guard_service.py    # High-risk: coverage target
│   │   │   ├── signal_bridge.py    # High-risk: coverage target
│   │   │   └── signal_delivery.py  # High-risk: coverage target
│   │   ├── dependencies.py         # Orphan file: coverage target
│   │   ├── prompts/                # Prompt templates (indirect coverage only)
│   │   └── utils.py
│   ├── tests/
│   │   ├── conftest.py             # 400+ lines of shared fixtures
│   │   ├── helpers/                # assertions.py, factories.py
│   │   ├── unit/                   # ~87 test files — expand here
│   │   ├── integration/            # 9 test files — add API route tests
│   │   ├── property/               # 5 test files — add state machine + parser tests
│   │   ├── fuzz/                   # 3 test files
│   │   ├── chaos/                  # 5 test files
│   │   ├── concurrency/            # 4 test files
│   │   └── test_api_e2e.py         # End-to-end API tests
│   ├── scripts/
│   │   ├── run_mutmut_shard.py     # 5 shards: auth-and-projects, orchestration,
│   │   │                           #   app-and-data, agents-and-integrations, api-and-middleware
│   │   └── detect_flaky.py         # 5-run JUnit XML diff-based flaky detection
│   └── pyproject.toml              # Coverage (fail_under=75→80), mutmut, ruff, pyright, bandit
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── board/              # 32 components; 14 untested — primary target
│   │   │       # Targets: ProjectBoard, BoardToolbar, CleanUpConfirmModal,
│   │   │       #          AgentColumnCell, BoardDragOverlay
│   │   ├── hooks/                  # ~50 hooks; 3 untested — branch coverage target
│   │   │   # Targets: useBoardDragDrop, useConfirmation, useUnsavedPipelineGuard
│   │   ├── lib/                    # Utility modules — mutation + coverage target
│   │   │   # Targets: lazyWithRetry, commands/, formatAgentName, generateId
│   │   ├── services/               # api.ts — only 1 test file exists
│   │   ├── pages/                  # 12 pages (all have tests)
│   │   └── utils/                  # Formatting, helpers (10+ files)
│   ├── e2e/                        # 17 E2E specs
│   ├── vitest.config.ts            # Thresholds: 50/44/41/50 → 55/50/45/55
│   ├── stryker.config.mjs          # Mutation: hooks/ + lib/ (thresholds: high=80, low=60)
│   └── playwright.config.ts        # Chromium + Firefox
└── scripts/
    └── pre-commit                  # Pre-commit hooks
```

**Structure Decision**: Web application structure — backend + frontend monorepo under `apps/solune/`. This feature operates entirely within the existing layout. No new directories or projects are created. Test files are added to existing test directories. Configuration changes are made to existing config files (`pyproject.toml`, `vitest.config.ts`).

## Phases

### Phase A: Static Analysis Completion (P1 — User Story 1)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 1 | Run frontend lint sweep (`eslint .`) and triage all violations as fix-now/fix-later/false-positive | — | Frontend `src/` |
| 2 | Fix all violations triaged as fix-now | Step 1 | Frontend source files |
| 3 | Run frontend type-check (`tsc --noEmit`) in strict mode and fix all errors | — | Frontend source files |
| 4 | Run backend lint (`ruff check src/`) and fix all violations | — | Backend `src/` |
| 5 | Run backend type-check (`pyright`) and fix all errors | — | Backend `src/` |
| 6 | Run backend security scan (`bandit -r src/ -s B104,B608`) and fix issues | — | Backend `src/` |
| 7 | Run flaky test detection (`python scripts/detect_flaky.py`, 5 runs) for backend | Steps 4–6 | `scripts/detect_flaky.py`, JUnit XML outputs |
| 8 | Run flaky test detection (`vitest run` ×5, diff results) for frontend | Steps 2–3 | Vitest output |
| 9 | Quarantine confirmed flaky tests with root cause and file tracked issues | Steps 7, 8 | Test files |
| 10 | Resolve all test warnings (AsyncMock deprecation, other deprecations) | Steps 7, 8 | Test files, `conftest.py` |

**Parallelism**: Steps 1+3 run simultaneously. Steps 4+5+6 run simultaneously. Steps 7+8 depend on their respective analysis steps.

### Phase B: Backend Coverage Expansion (P2 — User Story 2)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 11 | Add integration tests for auth callback route | Phase A | `tests/integration/test_auth_callback.py` |
| 12 | Add integration tests for webhook dispatch route | Phase A | `tests/integration/test_webhook_dispatch.py` |
| 13 | Add integration tests for pipeline launch route | Phase A | `tests/integration/test_pipeline_launch.py` |
| 14 | Add integration tests for chat confirm route | Phase A | `tests/integration/test_chat_confirm.py` |
| 15 | Add unit tests for dependency injection module | Phase A | `tests/unit/test_dependencies.py` |
| 16 | Add unit tests for request ID middleware | Phase A | `tests/unit/test_request_id_middleware.py` |
| 17 | Add edge-case tests for recovery logic | Phase A | `tests/unit/test_recovery_edge_cases.py` |
| 18 | Add edge-case tests for state validation boundaries | Phase A | `tests/unit/test_state_validation_edge_cases.py` |
| 19 | Add edge-case tests for signal bridge error propagation | Phase A | `tests/unit/test_signal_bridge_edge_cases.py` |
| 20 | Add edge-case tests for guard service + signal delivery | Phase A | `tests/unit/test_guard_signal_edge_cases.py` |
| 21 | Add property-based tests for pipeline state machine | Phase A | `tests/property/test_pipeline_state_machine.py` |
| 22 | Add property-based tests for markdown parser | Phase A | `tests/property/test_markdown_parser_roundtrips.py` |
| 23 | Verify mutation shard config includes api-and-middleware targets | Steps 11–16 | `scripts/run_mutmut_shard.py` |
| 24 | Verify backend line coverage ≥ 80% | Steps 11–23 | Coverage report |

**Parallelism**: Steps 11–22 can all run in parallel. Steps 23–24 are sequential verification gates.

### Phase C: Frontend Coverage Expansion (P3 — User Story 3)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 25 | Add tests for ProjectBoard component | Phase A | `src/components/board/__tests__/ProjectBoard.test.tsx` |
| 26 | Add tests for BoardToolbar component | Phase A | `src/components/board/__tests__/BoardToolbar.test.tsx` |
| 27 | Add tests for CleanUpConfirmModal component | Phase A | `src/components/board/__tests__/CleanUpConfirmModal.test.tsx` |
| 28 | Add tests for AgentColumnCell component | Phase A | `src/components/board/__tests__/AgentColumnCell.test.tsx` |
| 29 | Add tests for BoardDragOverlay component | Phase A | `src/components/board/__tests__/BoardDragOverlay.test.tsx` |
| 30 | Add tests for useBoardDragDrop hook (5 branch paths) | Phase A | `src/hooks/__tests__/useBoardDragDrop.test.ts` |
| 31 | Add tests for useConfirmation hook (5 branch paths) | Phase A | `src/hooks/__tests__/useConfirmation.test.ts` |
| 32 | Add tests for useUnsavedPipelineGuard hook (5 branch paths) | Phase A | `src/hooks/__tests__/useUnsavedPipelineGuard.test.ts` |
| 33 | Add tests for lazyWithRetry utility | Phase A | `src/lib/__tests__/lazyWithRetry.test.ts` |
| 34 | Add tests for commands directory | Phase A | `src/lib/__tests__/commands.test.ts` |
| 35 | Add tests for formatAgentName utility | Phase A | `src/lib/__tests__/formatAgentName.test.ts` |
| 36 | Add tests for generateId utility | Phase A | `src/lib/__tests__/generateId.test.ts` |
| 37 | Add service layer tests (error handling, retry, response parsing) | Phase A | `src/services/__tests__/api-errors.test.ts` |
| 38 | Add branch coverage tests for hooks (error/loading/empty states) | Steps 30–32 | Hook test files |
| 39 | Verify frontend coverage ≥ 55/50/45/55 | Steps 25–38 | Coverage report |

**Parallelism**: Steps 25–37 can all run in parallel. Step 38 depends on hook tests. Step 39 is the verification gate.

### Phase D: Mutation Verification (P4 — User Story 4)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 40 | Execute backend mutation shard: auth-and-projects | Phase B | mutmut output |
| 41 | Execute backend mutation shard: orchestration | Phase B | mutmut output |
| 42 | Execute backend mutation shard: app-and-data | Phase B | mutmut output |
| 43 | Execute backend mutation shard: agents-and-integrations | Phase B | mutmut output |
| 44 | Execute backend mutation shard: api-and-middleware | Phase B | mutmut output |
| 45 | Execute frontend mutation testing (Stryker) | Phase C | Stryker output |
| 46 | Review and classify surviving mutants (killable/equivalent/non-killable) | Steps 40–45 | Documentation |
| 47 | Write targeted assertions to kill survivor mutants | Step 46 | Test files |

**Parallelism**: Steps 40–45 can all run in parallel. Steps 46–47 are sequential.

### Phase E: Final Verification and CI Enforcement (P5 — User Story 5)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 48 | Ratchet backend coverage threshold: `fail_under = 80` | Phase D | `pyproject.toml` |
| 49 | Ratchet frontend coverage thresholds: 55/50/45/55 | Phase D | `vitest.config.ts` |
| 50 | Run final flaky test detection (5 runs each suite) | Phase D | Test output |
| 51 | Verify zero AsyncMock deprecation warnings | Phase D | Test output |
| 52 | Verify pre-commit hooks complete in <30 seconds | Phase D | `scripts/pre-commit` |
| 53 | Document emergency hotfix override process | Phase D | Documentation |
| 54 | Generate final coverage and mutation reports | Steps 48–53 | Reports |

**Parallelism**: Steps 48–53 can run in parallel. Step 54 is the final gate.

## Constitution Check: Post-Design Re-evaluation

*Re-check after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I: Specification-First Development | ✅ PASS | Full spec with 5 user stories, 27 FRs, 11 SCs. Predecessors documented. |
| II: Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates. No custom sections. |
| III: Agent-Orchestrated Execution | ✅ PASS | Well-defined phase outputs. Explicit handoffs. Single-responsibility. |
| IV: Test Optionality with Clarity | ✅ PASS | Tests are primary deliverable. Ordered by dependency. Appropriate types. |
| V: Simplicity and DRY | ✅ PASS | No new abstractions. Existing tools only. DRY deferred. |

All five principles remain satisfied after Phase 1 design completion. No violations detected.

## Complexity Tracking

No new abstractions or patterns introduced. This feature operates entirely within the existing project structure, test infrastructure, and CI pipeline. All changes are additive (new test files, threshold adjustments) with no structural modifications.

| Item | Justification | Status |
|------|---------------|--------|
| (none) | No complexity justifications needed | N/A |
