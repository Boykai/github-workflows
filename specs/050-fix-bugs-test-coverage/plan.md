# Implementation Plan: Find/Fix Bugs & Increase Test Coverage

**Branch**: `050-fix-bugs-test-coverage` | **Date**: 2026-03-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/050-fix-bugs-test-coverage/spec.md`

## Summary

Systematic bug-hunting and coverage improvement across the Solune monorepo backend (Python/FastAPI,
currently 75% coverage threshold, 151+ test files) and frontend (React/TypeScript, currently 51%
statement coverage, 130+ test files, 10 E2E specs). The approach follows a strict sequence: static
analysis → runtime error discovery → fix known bugs → expand coverage strategically → harden with
mutation testing and CI gates.

Four critical bugs are identified for immediate fix: mutmut trampoline name-resolution (blocks all
mutation testing), cache leakage between test suites, AsyncMock deprecation warnings in integration
tests, and pipeline "stuck in In Progress" state transition bug. After fixes, coverage expands via
risk-first targeting of high-complexity modules, followed by threshold ratcheting and chaos testing.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI 0.135+, React 18+, Pydantic 2.12+, Vitest, Playwright
**Storage**: SQLite via aiosqlite (existing — no changes in this feature)
**Testing**: pytest + pytest-asyncio + Hypothesis (backend), Vitest + Playwright (frontend), mutmut (backend mutation), Stryker (frontend mutation)
**Target Platform**: Linux server (backend), modern browsers (frontend)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: Pre-commit hooks complete in <30 seconds on changed files; mutation testing shards complete within CI timeout
**Constraints**: No DRY refactoring in this plan — characterization tests only; thresholds only ratchet upward
**Scale/Scope**: ~151 backend test files, ~130 frontend test files, 10 E2E specs, 27+ service modules, 5 mutation shards

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development ✅ PASS

- ✅ Feature work began with explicit specification (`spec.md`)
- ✅ Prioritized user stories (P1–P5) with independent testing criteria
- ✅ Given-When-Then acceptance scenarios for each story
- ✅ Clear scope boundaries (DRY refactoring explicitly excluded)

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
- ✅ Testing phases follow clear ordering (fix infrastructure → expand coverage → harden)
- ✅ Test types are appropriate to each target (unit, integration, property-based, E2E, chaos)

### Principle V: Simplicity and DRY ✅ PASS

- ✅ No new abstractions introduced — working within existing test infrastructure
- ✅ DRY refactoring explicitly deferred (characterization tests first)
- ✅ Uses existing tools (pytest, vitest, mutmut, stryker) — no new tool adoption
- ✅ Pre-commit hooks already exist — only verification needed, not creation

### Constitution Check: Post-Design Re-evaluation ✅ PASS

All five principles remain satisfied after Phase 1 design completion. No violations detected.
The feature operates entirely within existing project structure and tooling. No complexity
justifications needed.

## Project Structure

### Documentation (this feature)

```text
specs/050-fix-bugs-test-coverage/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — quality gate contracts
│   ├── quality-gates.md         # Coverage and quality thresholds
│   └── verification-commands.md # Verification command reference
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
│   │   │   ├── copilot_polling/   # Pipeline polling (BUG-004 fix target)
│   │   │   │   ├── pipeline.py
│   │   │   │   ├── state_validation.py
│   │   │   │   └── recovery.py    # High-risk: coverage target
│   │   │   ├── workflow_orchestrator/
│   │   │   │   └── transitions.py # High-risk: coverage target
│   │   │   ├── cache.py           # BUG-002 fix target
│   │   │   ├── guard_service.py   # High-risk: coverage target
│   │   │   ├── signal_bridge.py   # High-risk: coverage target
│   │   │   └── signal_delivery.py # High-risk: coverage target
│   │   └── utils.py
│   ├── tests/
│   │   ├── conftest.py            # BUG-002 fix target (cache clearing fixture)
│   │   ├── unit/                  # ~151 test files — expand here
│   │   ├── integration/           # Integration tests — add API route tests
│   │   │   └── conftest.py        # BUG-003 fix target (AsyncMock → stubs)
│   │   ├── property/             # Hypothesis tests — add state machine tests
│   │   ├── chaos/                # Chaos tests — add concurrency scenarios
│   │   └── concurrency/          # Concurrency tests — expand
│   ├── scripts/
│   │   ├── run_mutmut_shard.py   # BUG-001 fix target (trampoline)
│   │   └── detect_flaky.py       # Flaky test detection
│   └── pyproject.toml            # Coverage threshold (75 → 80), mutmut config
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # 0% coverage — primary target
│   │   ├── components/
│   │   │   └── board/            # Partial coverage — interaction tests
│   │   ├── hooks/                # 44% branch coverage — expand
│   │   ├── lib/                  # Mutation testing target
│   │   └── __tests__/            # Component tests — add App.test.tsx
│   ├── e2e/                      # 10 specs → expand to 14+
│   ├── vitest.config.ts          # Coverage thresholds (50/44/41 → 55/50/45)
│   ├── stryker.config.mjs        # Mutation testing config
│   └── playwright.config.ts      # E2E config
└── scripts/
    └── pre-commit                # Pre-commit hooks (verify coverage)
```

**Structure Decision**: Web application structure (Option 2 — backend + frontend). The feature
operates entirely within the existing `solune/` monorepo layout. No new directories or projects
are created. Test files are added to existing test directories. Configuration changes are made
to existing config files (`pyproject.toml`, `vitest.config.ts`).

## Phases

### Phase 1: Static Analysis & Error Discovery (P2 — User Story 2)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 1 | Run backend lint + type-check sweep | — | Report output |
| 2 | Run all test suites and capture failures | — | `results.xml` |
| 3 | Run flaky test detection (5+ runs) | Step 2 | Flaky test report |

**Parallelism**: Steps 1 and 2 can run simultaneously. Step 3 depends on Step 2.

### Phase 2: Fix Known Bugs (P1 — User Story 1)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 4 | Fix mutmut trampoline name-resolution | Phase 1 | `scripts/run_mutmut_shard.py`, `pyproject.toml` |
| 5 | Fix cache leakage between tests | Phase 1 | `tests/conftest.py`, `src/services/cache.py` |
| 6 | Fix AsyncMock warnings | Phase 1 | `tests/integration/conftest.py` |
| 7 | Fix pipeline "stuck in In Progress" | Phase 1 | `src/services/copilot_polling/state_validation.py`, `pipeline.py` |

**Parallelism**: Steps 4–7 can be developed in parallel (independent bugs). Each must be
individually verified before Phase 3.

### Phase 3: Backend Coverage Expansion (P3 — User Story 3)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 8 | Add API route integration tests | Phase 2 | `tests/integration/` |
| 9 | Cover high-risk service modules | Phase 2 | `tests/unit/`, `tests/property/` |
| 10 | Expand mutation testing targets | Phase 2 | `scripts/run_mutmut_shard.py` |
| 11 | Add characterization tests for DRY candidates | Phase 2 | `tests/unit/test_regression_bugfixes.py` |

**Parallelism**: Steps 8–11 can be developed in parallel across developers.

### Phase 4: Frontend Coverage Expansion (P4 — User Story 4)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 12 | Cover App.tsx | Phase 2 | `src/__tests__/App.test.tsx` |
| 13 | Cover board components | Phase 2 | `src/components/board/` tests |
| 14 | Increase branch coverage in hooks | Phase 2 | `src/hooks/` tests |
| 15 | Expand E2E suite (10 → 14 specs) | Phase 2 | `e2e/` new specs |
| 16 | Run Stryker and kill survivors | Steps 12–14 | Targeted assertions |

**Parallelism**: Steps 12–15 can be developed in parallel. Step 16 depends on 12–14.

### Phase 5: Hardening & CI Gates (P5 — User Story 5)

| Step | Task | Depends On | Files |
|------|------|-----------|-------|
| 17 | Ratchet coverage thresholds | Phases 3–4 | `pyproject.toml`, `vitest.config.ts` |
| 18 | Verify pre-commit hooks | Phases 3–4 | `scripts/pre-commit` |
| 19 | Add chaos/concurrency test scenarios | Phases 3–4 | `tests/chaos/`, `tests/concurrency/` |

**Parallelism**: Steps 17–19 can be developed in parallel.

## Dependency Graph

```
Phase 1 (Static Analysis)
  ├── Step 1: Lint + type-check ──┐
  ├── Step 2: Run test suites ────┤
  └── Step 3: Flaky detection ────┘ (depends on Step 2)
                │
                ▼
Phase 2 (Bug Fixes) ──── All 4 bugs can be fixed in parallel
  ├── Step 4: Mutmut trampoline
  ├── Step 5: Cache leakage
  ├── Step 6: AsyncMock warnings
  └── Step 7: Pipeline transitions
                │
          ┌─────┴─────┐
          ▼           ▼
Phase 3 (Backend)  Phase 4 (Frontend) ──── Can run in parallel
  ├── Step 8         ├── Step 12
  ├── Step 9         ├── Step 13
  ├── Step 10        ├── Step 14
  └── Step 11        ├── Step 15
                     └── Step 16 (depends on 12–14)
          │               │
          └───────┬───────┘
                  ▼
Phase 5 (Hardening)
  ├── Step 17: Ratchet thresholds
  ├── Step 18: Verify pre-commit
  └── Step 19: Chaos/concurrency tests
```

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| Mutmut trampoline fix is more complex than expected | High | Medium | Fall back to PYTHONPATH normalization; pin known-good version |
| Coverage targets not achievable with current test effort | Medium | Low | Ratchet incrementally (75→77→80) rather than in one jump |
| E2E tests flaky in CI environment | Medium | Medium | Use retry logic in Playwright config; distinguish env failures |
| Mutation testing CI timeout | Medium | Medium | Sharding already in place; reduce shard sizes if needed |
| Pre-commit hooks slow developer workflow | Low | Low | Already scoped to changed files only; monitor timing |

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
