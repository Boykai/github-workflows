# Implementation Plan: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Branch**: `051-fix-bugs-test-coverage` | **Date**: 2026-03-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/051-fix-bugs-test-coverage/spec.md`
**Predecessor**: `050-fix-bugs-test-coverage` (42% complete — all 4 critical bugs fixed, infrastructure established)

## Summary

Phase 2 of the systematic test coverage and quality improvement effort across the Solune monorepo.
Phase 1 (spec 050) completed static analysis at ~50%, fixed all 4 critical bugs (mutmut trampoline,
cache leakage, AsyncMock warnings, pipeline stuck state), and established infrastructure. This phase
finishes the static analysis sweep, expands test coverage to meet ratcheted thresholds, verifies
mutation kill rates, and locks in CI enforcement.

**Key targets**: Backend line coverage 75% → 80%, frontend statement/branch/function coverage
51%/44%/41% → 55%/50%/45%, mutation kill rates verified across all shards, zero flaky tests,
zero lint/type-check violations.

## Technical Context

**Language/Version**: Python 3.12+/3.13 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI 0.135+, React 19, Pydantic 2.12+, Vite 8, TanStack Query v5, Tailwind CSS 4
**Storage**: SQLite via aiosqlite (existing — no changes in this feature)
**Testing**: pytest + pytest-asyncio + Hypothesis (backend), Vitest + @testing-library/react (frontend), Playwright (E2E), mutmut (backend mutation), Stryker (frontend mutation)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: Pre-commit hooks complete in <30 seconds on changed files; mutation testing shards complete within CI timeout
**Constraints**: No DRY refactoring — characterization tests only; thresholds only ratchet upward
**Scale/Scope**: ~151 backend test files, ~130 frontend test files, 10 E2E specs, 27+ service modules, 4 mutation shards

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature work began with explicit specification (`spec.md`)
- ✅ Prioritized user stories (P1–P5) with independent testing criteria
- ✅ Given-When-Then acceptance scenarios for each story
- ✅ Clear scope boundaries (DRY refactoring explicitly excluded)
- ✅ Predecessor spec (050) baseline documented

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
specs/051-fix-bugs-test-coverage/
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
solune/
├── backend/
│   ├── src/
│   │   ├── api/                    # FastAPI route handlers (mutation target: expand)
│   │   ├── middleware/             # Request middleware (mutation target: expand)
│   │   ├── models/                # Pydantic data models
│   │   ├── services/              # Core business logic (mutation target: current)
│   │   │   ├── copilot_polling/   # Pipeline polling (already fixed in 050)
│   │   │   │   ├── pipeline.py
│   │   │   │   ├── state_validation.py
│   │   │   │   └── recovery.py    # High-risk: coverage target
│   │   │   ├── workflow_orchestrator/
│   │   │   │   └── transitions.py # High-risk: coverage target
│   │   │   ├── cache.py           # Already fixed in 050
│   │   │   ├── guard_service.py   # High-risk: coverage target
│   │   │   ├── signal_bridge.py   # High-risk: coverage target
│   │   │   └── signal_delivery.py # High-risk: coverage target
│   │   ├── dependencies.py        # Coverage target: orphan file
│   │   └── utils.py
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── unit/                  # ~151 test files — expand here
│   │   ├── integration/           # Integration tests — add API route tests
│   │   ├── property/             # Hypothesis tests — add state machine tests
│   │   ├── chaos/                # Chaos tests
│   │   └── concurrency/          # Concurrency tests
│   ├── scripts/
│   │   ├── run_mutmut_shard.py   # Mutation shard runner
│   │   └── detect_flaky.py       # Flaky test detection
│   └── pyproject.toml            # Coverage threshold (75 → 80), mutmut config
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Coverage target
│   │   ├── components/
│   │   │   └── board/            # 14 untested components — primary target
│   │   ├── hooks/                # 3 untested hooks — branch coverage target
│   │   ├── lib/                  # Utility modules — mutation testing target
│   │   │   ├── commands/         # Coverage target
│   │   │   ├── lazyWithRetry.ts  # Coverage target
│   │   │   ├── formatAgentName.ts# Coverage target
│   │   │   └── generateId.ts    # Coverage target
│   │   └── __tests__/            # Component tests
│   ├── e2e/                      # 10 E2E specs
│   ├── vitest.config.ts          # Coverage thresholds (→ 55/50/45)
│   ├── stryker.config.mjs        # Mutation testing config
│   └── playwright.config.ts      # E2E config
└── scripts/
    └── pre-commit                # Pre-commit hooks
```

**Structure Decision**: Web application structure (Option 2 — backend + frontend). The feature
operates entirely within the existing `solune/` monorepo layout. No new directories or projects
are created. Test files are added to existing test directories. Configuration changes are made
to existing config files (`pyproject.toml`, `vitest.config.ts`).

## Phases

### Phase A: Static Analysis Completion (P1 — User Story 1)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 1 | Run frontend lint sweep and triage all violations | — | Report output |
| 2 | Fix all violations triaged as fix-now | Step 1 | Frontend source files |
| 3 | Run frontend type-check in strict mode and fix errors | — | Frontend source files |
| 4 | Run backend lint (ruff) and fix violations | — | Backend source files |
| 5 | Run backend type-check (pyright) and fix errors | — | Backend source files |
| 6 | Run backend security scan (bandit) and fix issues | — | Backend source files |
| 7 | Run flaky test detection (5 runs each) for backend | Steps 4–6 | `scripts/detect_flaky.py` |
| 8 | Run flaky test detection (5 runs each) for frontend | Step 3 | Test output |
| 9 | Quarantine any confirmed flaky tests with root cause | Steps 7, 8 | Test files |
| 10 | Resolve all test warnings in frontend suite | Step 3 | Test files |

**Parallelism**: Steps 1 and 3 can run simultaneously. Steps 4, 5, 6 can run simultaneously. Steps 7 and 8 depend on their respective analysis steps.

### Phase B: Backend Coverage Expansion (P2 — User Story 2)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 11 | Add integration tests for auth callback route | Phase A | `tests/integration/` |
| 12 | Add integration tests for webhook dispatch route | Phase A | `tests/integration/` |
| 13 | Add integration tests for pipeline launch route | Phase A | `tests/integration/` |
| 14 | Add integration tests for chat confirm route | Phase A | `tests/integration/` |
| 15 | Add unit tests for dependency injection module | Phase A | `tests/unit/` |
| 16 | Add unit tests for request ID middleware | Phase A | `tests/unit/` |
| 17 | Add edge-case tests for recovery logic | Phase A | `tests/unit/` |
| 18 | Add edge-case tests for state validation boundaries | Phase A | `tests/unit/` |
| 19 | Add edge-case tests for signal bridge error propagation | Phase A | `tests/unit/` |
| 20 | Add property-based tests for pipeline state machine | Phase A | `tests/property/` |
| 21 | Add property-based tests for markdown parser | Phase A | `tests/property/` |
| 22 | Expand mutation testing to include API routes | Steps 11–14 | `scripts/run_mutmut_shard.py` |
| 23 | Expand mutation testing to include middleware | Step 16 | `pyproject.toml` |
| 24 | Verify backend line coverage ≥ 80% | Steps 11–23 | Coverage report |

**Parallelism**: Steps 11–21 can all run in parallel. Steps 22–23 depend on the tests they cover.

### Phase C: Frontend Coverage Expansion (P3 — User Story 3)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 25 | Add tests for ProjectBoard component | Phase A | `src/components/board/__tests__/` |
| 26 | Add tests for BoardToolbar component | Phase A | `src/components/board/__tests__/` |
| 27 | Add tests for CleanUpConfirmModal component | Phase A | `src/components/board/__tests__/` |
| 28 | Add tests for AgentColumnCell component | Phase A | `src/components/board/__tests__/` |
| 29 | Add tests for BoardDragOverlay component | Phase A | `src/components/board/__tests__/` |
| 30 | Add tests for useBoardDragDrop hook | Phase A | `src/hooks/__tests__/` |
| 31 | Add tests for useConfirmation hook | Phase A | `src/hooks/__tests__/` |
| 32 | Add tests for useUnsavedPipelineGuard hook | Phase A | `src/hooks/__tests__/` |
| 33 | Add tests for lazyWithRetry utility | Phase A | `src/lib/__tests__/` |
| 34 | Add tests for commands directory | Phase A | `src/lib/__tests__/` |
| 35 | Add tests for formatAgentName utility | Phase A | `src/lib/__tests__/` |
| 36 | Add tests for generateId utility | Phase A | `src/lib/__tests__/` |
| 37 | Add branch coverage tests for hooks (error/loading/empty) | Steps 30–32 | `src/hooks/__tests__/` |
| 38 | Verify frontend coverage ≥ 55/50/45 | Steps 25–37 | Coverage report |

**Parallelism**: Steps 25–36 can all run in parallel. Step 37 depends on hook tests. Step 38 is the verification gate.

### Phase D: Mutation Verification (P4 — User Story 4)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 39 | Execute backend mutation shard: auth-and-projects | Phase B | mutmut output |
| 40 | Execute backend mutation shard: orchestration | Phase B | mutmut output |
| 41 | Execute backend mutation shard: app-and-data | Phase B | mutmut output |
| 42 | Execute backend mutation shard: agents-and-integrations | Phase B | mutmut output |
| 43 | Execute frontend mutation testing (Stryker) | Phase C | Stryker output |
| 44 | Review and document surviving mutants | Steps 39–43 | Documentation |
| 45 | Write targeted assertions to kill survivor mutants | Step 44 | Test files |

**Parallelism**: Steps 39–43 can all run in parallel. Steps 44–45 are sequential.

### Phase E: Final Verification and CI Enforcement (P5 — User Story 5)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 46 | Enforce coverage thresholds in CI configuration | Phase D | `pyproject.toml`, `vitest.config.ts` |
| 47 | Run final flaky test detection (5 runs each suite) | Phase D | Test output |
| 48 | Verify zero AsyncMock deprecation warnings | Phase D | Test output |
| 49 | Verify pre-commit hooks complete in <30 seconds | Phase D | `scripts/pre-commit` |
| 50 | Document emergency hotfix override process | Phase D | Documentation |
| 51 | Generate final coverage and mutation reports | Steps 46–50 | Reports |

**Parallelism**: Steps 46–50 can run in parallel. Step 51 is the final gate.

## Constitution Check: Post-Design Re-evaluation

*Re-check after Phase 1 design completion.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I: Specification-First Development | ✅ PASS | Full spec with 5 user stories, 25 FRs, 15 SCs. Predecessor documented. |
| II: Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates. No custom sections. |
| III: Agent-Orchestrated Execution | ✅ PASS | Well-defined phase outputs. Explicit handoffs. Single-responsibility. |
| IV: Test Optionality with Clarity | ✅ PASS | Tests are primary deliverable. Ordered by dependency. Appropriate types. |
| V: Simplicity and DRY | ✅ PASS | No new abstractions. Existing tools only. DRY deferred. |

All five principles remain satisfied after Phase 1 design completion. No violations detected.

## Complexity Tracking

No new abstractions or patterns introduced. This feature operates entirely within the existing
project structure, test infrastructure, and CI pipeline. All changes are additive (new test files,
threshold adjustments) with no structural modifications.

| Item | Justification | Status |
|------|---------------|--------|
| (none) | No complexity justifications needed | N/A |
