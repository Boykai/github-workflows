# Implementation Plan: Increase Test Coverage to Surface Unknown Bugs

**Branch**: `049-increase-test-coverage` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/049-increase-test-coverage/spec.md`

## Summary

Systematically raise backend line coverage from 71% to 80% and frontend coverage from ~50/45/42/51% to 60/55/52/60% through a phased approach. Phase 1 promotes existing local-only advanced tests (property, fuzz, chaos, concurrency) into CI with zero new test code. Phases 2–4 fill high-ROI coverage gaps in untested backend modules (GitHub integration, Copilot polling, chores, API routes) and frontend modules (Zod schemas, 24 hooks, 53 components). Phase 5 adds mutation-hardened tests targeting surviving mutants. Phase 6 introduces production-parity and time-controlled testing for 15+ temporal behaviors. Phase 7 adds architecture fitness functions to prevent regression. The approach follows a ratchet strategy — CI thresholds are bumped only after each phase merges, set 2% below actual to absorb fluctuation.

## Technical Context

**Language/Version**: Python ≥3.12 (target 3.13) backend; TypeScript ~5.9 / React 19.2 frontend
**Primary Dependencies**: FastAPI ≥0.135, githubkit, Pydantic 2.12, aiosqlite (backend); Vite 7.3, @tanstack/react-query 5.90, Zod 4.3, react-hook-form 7.71 (frontend)
**Storage**: SQLite via aiosqlite (async), in-memory SQLite for test fixtures
**Testing**: pytest + pytest-asyncio + pytest-cov + hypothesis + mutmut (backend); Vitest 4.0 + @testing-library/react + @vitest/coverage-v8 + @stryker-mutator (frontend); Playwright 1.58 (E2E)
**Target Platform**: GitHub Actions CI (Ubuntu), Node 22, Python 3.12
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: Total backend test suite increase ≤90s; total frontend test suite increase ≤60s (SC-010)
**Constraints**: All new tests must use existing fixture patterns; no new external service dependencies; advanced tests must respect 120s per-test timeout in CI
**Scale/Scope**: Backend: 9 untested priority modules → fully tested; Frontend: 6 schema files + 24 hooks + 53 components → tested

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md per workflow |
| **IV. Test Optionality** | ✅ PASS | This feature explicitly requests tests — the entire specification is about test coverage. Tests are the deliverable, not optional overhead |
| **V. Simplicity & DRY** | ✅ PASS | All new tests follow existing template patterns (no new abstractions). Test structure mirrors established conventions. Only one new dependency (`freezegun`, single-purpose time-freezing library) |

**Gate result**: ALL PASS — proceed to Phase 0.

### Post-Design Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All plan phases trace back to spec user stories and functional requirements |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, quickstart.md, contracts/ all follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Clear phase handoffs: plan → tasks → implement |
| **IV. Test Optionality** | ✅ PASS | Tests are the explicit deliverable per specification |
| **V. Simplicity & DRY** | ✅ PASS | No new abstractions introduced. Reuses existing fixtures, factories, and patterns. Architecture tests use stdlib `ast` instead of adding dependencies |

**Post-design gate result**: ALL PASS.

## Project Structure

### Documentation (this feature)

```text
specs/049-increase-test-coverage/
├── plan.md                          # This file
├── research.md                      # Phase 0: Research findings
├── data-model.md                    # Phase 1: Coverage entity model
├── quickstart.md                    # Phase 1: Quick-start guide for contributors
├── contracts/                       # Phase 1: CI contract definitions
│   ├── ci-advanced-tests.md         # Advanced test + flaky detection job contract
│   ├── ci-mutation.md               # Mutation testing workflow contract
│   └── ci-coverage-enforcement.md   # Coverage ratchet + architecture enforcement contract
├── checklists/
│   └── requirements.md              # Pre-existing from specify phase
└── tasks.md                         # Phase 2 output (speckit.tasks — NOT created here)
```

### Source Code (repository root)

```text
solune/backend/
├── pyproject.toml                   # MODIFIED: fail_under ratchet (71 → 76 → 80), freezegun dep
├── src/
│   ├── api/                         # Route handlers — untested: agents.py, health.py, webhook_models.py
│   ├── models/                      # Pydantic models
│   └── services/
│       ├── github_projects/         # Untested: agents.py
│       ├── copilot_polling/         # Untested: helpers.py, pipeline.py
│       └── chores/                  # Untested: chat.py, template_builder.py
└── tests/
    ├── unit/                        # ~50 existing + 8 new test files (Phase 2)
    ├── integration/                 # 8 existing + test_production_mode.py (Phase 6)
    ├── property/                    # 5 existing (promoted to CI in Phase 1)
    ├── fuzz/                        # 2 existing (promoted to CI in Phase 1)
    ├── chaos/                       # 3 existing (promoted to CI in Phase 1)
    ├── concurrency/                 # 3 existing (promoted to CI in Phase 1)
    ├── architecture/                # NEW: Import direction enforcement (Phase 7)
    └── conftest.py                  # Shared fixtures (mock_db, client, etc.)

solune/frontend/
├── vitest.config.ts                 # MODIFIED: Coverage thresholds ratchet
├── stryker.config.mjs               # Mutation testing scope (hooks + lib)
├── src/
│   ├── __tests__/fuzz/              # 2 existing fuzz tests (verify CI inclusion)
│   ├── __tests__/architecture/      # NEW: Import boundary tests (Phase 7)
│   ├── components/                  # ~53 untested components → tested (Phase 4)
│   │   ├── settings/                # 14 untested → tested
│   │   ├── board/                   # 11 untested → tested
│   │   ├── pipeline/                # 9 untested → tested
│   │   └── ...                      # ~19 remaining (chat, chores, tools, agents)
│   ├── hooks/                       # 24 untested hooks → tested (Phase 3)
│   └── services/
│       └── schemas/                 # 6 Zod schema files → 100% coverage (Phase 3)
├── src/test/
│   ├── setup.ts                     # createMockApi() factory
│   ├── test-utils.tsx               # renderWithProviders() helper
│   ├── a11y-helpers.ts              # expectNoA11yViolations() assertions
│   └── factories/index.ts           # Data factories
└── package.json                     # Scripts: test, test:coverage, test:mutate

.github/workflows/
├── ci.yml                           # MODIFIED: Advanced test job, flaky detection
└── mutation.yml                     # NEW: Scheduled weekly mutation testing
```

**Structure Decision**: Existing web application structure (`solune/backend/` + `solune/frontend/`) is used as-is. New test files are added within the existing `tests/` hierarchies following established naming conventions. One new test directory (`tests/architecture/`) is added for fitness function tests. One new CI workflow file (`.github/workflows/mutation.yml`) is added. The CI workflow (`.github/workflows/ci.yml`) is extended with additional jobs for advanced tests and flaky detection.

## Implementation Phases

### Phase 1: Promote Existing Advanced Tests to CI (Foundation)
*Tests exist locally but don't run in CI — this unblocks everything else.*
*Maps to: User Story 1 (P1), User Story 6 (P3), FR-001 through FR-005*

1. **Wire backend advanced tests into CI** — Add a CI job in `.github/workflows/ci.yml` running `tests/property/`, `tests/fuzz/`, `tests/chaos/`, `tests/concurrency/` with 120s timeout per test. Set `HYPOTHESIS_PROFILE=ci` for property tests. Mark non-blocking initially (continue-on-error).
2. **Wire frontend fuzz tests into CI** — Verify `src/__tests__/fuzz/` is picked up by the Vitest CI run via existing glob pattern. No config change expected.
3. **Schedule mutation testing** — Create `.github/workflows/mutation.yml` with weekly schedule (Monday 03:00 UTC). Backend uses `mutmut` with 4 shards via `scripts/run_mutmut_shard.py`. Frontend uses Stryker (hooks + lib scope). Upload reports as artifacts.
4. **Add flaky test detection** — Add a scheduled CI job that runs the backend suite 3× and flags tests with inconsistent results. Report the 20 slowest tests.

**Acceptance**: CI logs show property/fuzz/chaos/concurrency tests executing on every PR. Mutation workflow runs weekly. Flaky detection runs on schedule.

---

### Phase 2: Backend Coverage Growth — High-ROI Gaps (71% → 76%)
*Target 9 untested modules with highest business risk. Steps 5–8 can run in parallel.*
*Maps to: User Story 2 (P1), FR-006 through FR-010*

5. **GitHub integration layer** — Write tests for `src/services/github_projects/agents.py`. Mock GitHub API via `mock_github_service` fixture. Verify request construction, error paths (429 rate-limit, timeout, 404 not-found). Follow `tests/unit/test_issues.py` as template.
6. **Copilot polling subsystem** — Write tests for `src/services/copilot_polling/helpers.py` and `pipeline.py`. Test rate-limit tier logic (boundary values: 50/51, 100/101), adaptive polling interval calculations. Follow `tests/unit/test_polling_loop.py` as template.
7. **Chores subsystem** — Write tests for `src/services/chores/chat.py` and `template_builder.py`. Test message construction and template rendering. Follow `tests/unit/test_chores_service.py` as template.
8. **API route coverage** — Write tests for `src/api/agents.py`, `src/api/health.py`, `src/api/webhook_models.py`. Follow `tests/unit/test_api_apps.py` (test client pattern). Verify status codes, response shapes, input validation, error handling.
9. **Ratchet threshold** — Bump `fail_under` in `pyproject.toml` from 71 → 76.

**Acceptance**: `pytest --cov=src --cov-report=term-missing` shows ≥76% line coverage. CI enforces 76% threshold.

---

### Phase 3: Frontend Coverage Growth — Hooks & Services (→ 53/48/45/54%)
*Highest ROI: hooks contain business logic, validators are trivial to test. Steps 10–11 parallel.*
*Maps to: User Story 3 (P1), FR-011 through FR-013*

10. **Schema validation files** — Test all 6 Zod schema files under `src/services/schemas/`. Pure input/output testing with zero mocking. Validate correct inputs, reject invalid inputs, verify default values and transformations. Target 100% coverage on these files.
11. **24 untested hooks** — Write tests prioritized by risk:
    - **P1 (business-critical):** `useSettings`, `useAgents`, `useChores`, `useTools`, `useApps`, `useChatProposals`, `usePipelineValidation`, `usePipelineBoardMutations`
    - **P2 (UI state):** `useAgentConfig`, `useAgentTools`, `useMcpSettings`, `useMcpPresets`, `useMetadata`, `useModels`, `useNotifications`, `useRecentParentIssues`, `useRepoMcpConfig`
    - **P3 (simple):** `useAppTheme`, `useCleanup`, `useMentionAutocomplete`, `usePipelineModelOverride`, `useSidebarState`, `useUnsavedChanges`
    - Pattern: `renderHook()` with `createMockApi()`, assert query keys, mutation calls, error states
12. **Ratchet thresholds** — Update `vitest.config.ts` to 53/48/45/54%.

**Acceptance**: `npm run test:coverage` shows ≥53/48/45/54% (stmt/branch/func/lines). CI enforces thresholds.

---

### Phase 4: Frontend Coverage Growth — Components (→ 60/55/52/60%)
*Depends on Phase 3 for hook test infrastructure. Steps 13–16 can run in parallel.*
*Maps to: User Story 3 (P1), FR-014 through FR-018*

13. **Settings components** (14 untested) — `GlobalSettings`, `AIPreferences`, `McpSettings`, `ProjectSettings`, etc. Follow `SettingsSection.test.tsx` as template.
14. **Board components** (11 untested) — `ProjectBoard`, `BoardToolbar`, `CleanUpButton`, cleanup modals. Follow `BoardColumn.test.tsx` as template.
15. **Pipeline components** (9 untested) — `PipelineToolbar`, `ModelSelector`, `ExecutionGroupCard`, `ParallelStageGroup`.
16. **Chat, Chores, Tools, Agents** — Remaining ~19 untested components. Use `renderWithProviders()` + `expectNoA11yViolations()`.
17. **Ratchet thresholds** — Update `vitest.config.ts` to 60/55/52/60%.

**Acceptance**: `npm run test:coverage` shows ≥60/55/52/60% (stmt/branch/func/lines). CI enforces thresholds.

---

### Phase 5: Mutation-Hardened Tests (Quality over Quantity)
*Depends on Phases 2–4 for baseline coverage. Steps 18–19 parallel.*
*Maps to: User Story 2 (P1), User Story 3 (P1), FR-019, FR-020*

18. **Backend mutation kills** — Run `mutmut`, identify top 20 surviving mutants. Write targeted tests focusing on: boundary conditions (rate-limit tiers: 50/51, 100/101), boolean negation (guard/auth checks), arithmetic mutations (polling intervals, backoff formulas). Kill ≥10 survivors. Bump `fail_under` to 80.
19. **Frontend mutation kills** — Run Stryker, identify top 20 surviving mutants. Strengthen assertions on return values, conditional branches, error paths. Kill ≥10 survivors.

**Acceptance**: Mutation reports show ≥10 previously-surviving mutants killed per platform. Backend coverage ≥80%.

---

### Phase 6: Production-Parity & Time-Controlled Tests (Surface Hidden Bugs)
*Can start in parallel with Phase 5.*
*Maps to: User Story 4 (P2), FR-021 through FR-023*

20. **Production-parity tests** — Run tests with production config: encryption on (`ENCRYPTION_KEY=<Fernet>`), webhook secrets set (`GITHUB_WEBHOOK_SECRET=<hex>`), CSRF enabled, `TESTING=false`. Exercise auth flow, webhook verification, rate limiting. Test invalid env combinations. Place in `tests/integration/test_production_mode.py`.
21. **Time-controlled tests** — Add `freezegun` as dev dependency. Use `@freeze_time` for 15+ temporal behaviors: session expiry boundaries (±1s), token refresh timing, rate-limit window resets, polling backoff formulas, reconnection delays, cache TTL, debounce timers.
22. **WebSocket lifecycle test** — Full connect → receive → disconnect → polling fallback → reconnect → data freshness verification using Playwright WebSocket interception.

**Acceptance**: Production-parity tests surface ≥1 behavior difference vs test mode. Time-controlled tests cover all 15 temporal behaviors.

---

### Phase 7: Architecture Fitness & Structural Guards (Prevent Regression)
*Can start in parallel with Phases 5–6.*
*Maps to: User Story 5 (P2), FR-024 through FR-026*

23. **Backend import boundaries** — AST-based tests in `tests/architecture/test_import_rules.py`: `services/` never imports `api/`, `api/` never imports stores directly, `models/` never imports `services/`. Known-violations allowlist for pre-existing exceptions.
24. **Frontend import boundaries** — Test in `src/__tests__/architecture/import-rules.test.ts`: `pages/` never imports other pages, `hooks/` never imports components, `utils/` never imports hooks or components.
25. **Contract validation** — Verify `createMockApi()` types align with `openapi.json` schemas using `solune/scripts/validate-contracts.sh` on every CI run.

**Acceptance**: Architecture tests catch violations; contract validation exits 0. No new violations in allowlist.

## Complexity Tracking

> No constitution violations — table intentionally left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
