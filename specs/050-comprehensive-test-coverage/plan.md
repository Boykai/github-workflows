# Implementation Plan: Comprehensive Test Coverage to 90%+

**Branch**: `050-comprehensive-test-coverage` | **Date**: 2026-03-17 | **Spec**: `specs/050-test-coverage-90/spec.md`
**Input**: Feature specification from `/specs/050-test-coverage-90/spec.md`

## Summary

Raise backend test coverage from 71% → 90%+ lines and frontend from 49% statements / 44% branches → 90% statements / 85% branches using a phased, ratchet-enforced approach. The plan implements a CI coverage ratchet (Phase 1) that prevents any metric from decreasing, then systematically fills test gaps across backend services/API (Phase 2), frontend hooks/components (Phase 3), mutation testing (Phase 4), property/fuzz testing (Phase 5), E2E/visual regression (Phase 6), and contract/integration testing (Phase 7), culminating in final threshold lock-down (Phase 8). Phases 2–7 execute in parallel after Phase 1 completes.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript + React (frontend)
**Primary Dependencies**: FastAPI, pytest, pytest-cov, mutmut, Hypothesis (backend); Vitest, Playwright, Stryker, fast-check (frontend)
**Storage**: SQLite (backend, with in-memory mock for tests)
**Testing**: pytest with pytest-cov (backend), Vitest with v8 provider (frontend), Playwright (E2E)
**Target Platform**: Linux CI (GitHub Actions), Node.js 22+, Python 3.12+
**Project Type**: Web application (backend + frontend)
**Performance Goals**: CI pipeline completes in <15 minutes for standard tests; mutation testing runs weekly
**Constraints**: Coverage thresholds are monotonically increasing (ratchet); maximum 5 quarantined flaky tests; `pragma: no cover` restricted to `__main__`, `TYPE_CHECKING`, platform-specific code
**Scale/Scope**: ~18 API endpoints, ~30+ service modules, ~44 hook test files, ~30 untested components, 14→24 E2E specs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

The feature specification (`specs/050-test-coverage-90/spec.md`) contains 8 prioritized user stories (P1–P3) with independent testing criteria and Given-When-Then acceptance scenarios. Scope boundaries and out-of-scope declarations are explicit.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md`. Research, data model, contracts, and quickstart documents are generated per the template structure.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to `speckit.tasks` for Phase 2 task generation is explicit.

### IV. Test Optionality with Clarity — ✅ PASS (with note)

This feature is inherently about testing. Tests are explicitly requested in the feature specification across all user stories. TDD is not mandated but the phased approach (write tests → bump thresholds) follows Red-Green-Refactor principles at the phase level.

### V. Simplicity and DRY — ✅ PASS

The plan favors extending existing infrastructure (pytest-cov, Vitest, Playwright, mutmut, Stryker) over introducing new tools. The only new tools are diff-cover and schemathesis, both purpose-built for specific gaps. The coverage ratchet uses a simple JSON baseline rather than a complex plugin system.

### Post-Design Re-evaluation — ✅ PASS

After Phase 1 design, all principles remain satisfied. The data model introduces only essential entities (Coverage Baseline, Quarantined Test, Mutation Score Report, Visual Snapshot Baseline). No unnecessary abstractions or complexity is added.

## Project Structure

### Documentation (this feature)

```text
specs/050-comprehensive-test-coverage/
├── plan.md              # This file (speckit.plan output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── coverage-baseline-schema.md
│   ├── ci-pipeline-steps.md
│   └── test-conventions.md
└── tasks.md             # Phase 2 output (speckit.tasks — NOT created by speckit.plan)
```

### Source Code (repository root)

```text
# Web application structure (existing)
solune/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI endpoints (18 modules)
│   │   ├── middleware/     # Custom middleware
│   │   ├── models/        # Pydantic models
│   │   └── services/      # 30+ service modules
│   ├── tests/
│   │   ├── unit/          # Unit tests (expand: service gap fill, API error matrix)
│   │   ├── integration/   # Integration tests (expand: pipeline, chat, webhook, DB, WS)
│   │   ├── property/      # Hypothesis tests (expand: GraphQL, state machines, round-trips)
│   │   ├── fuzz/          # Fuzz tests (expand: webhook, chat injection, upload)
│   │   ├── chaos/         # Chaos engineering tests (existing)
│   │   ├── concurrency/   # Concurrency tests (existing)
│   │   ├── architecture/  # Architecture tests (existing)
│   │   ├── helpers/       # Test utilities (existing)
│   │   └── conftest.py    # Shared fixtures (extend with new service mocks)
│   ├── scripts/
│   │   ├── run_mutmut_shard.py   # Mutation sharding (extend: 3 new shards)
│   │   └── detect_flaky.py       # NEW: Flaky test detection
│   └── pyproject.toml            # Coverage config (bump fail_under: 71→75→85→90)
├── frontend/
│   ├── src/
│   │   ├── hooks/         # Custom hooks (expand test coverage)
│   │   ├── components/    # React components (add ~30 new test files)
│   │   ├── services/      # API client (expand tests)
│   │   ├── lib/schemas/   # Zod schemas (add negative tests)
│   │   └── test/          # Test utilities (extend factories)
│   ├── e2e/               # Playwright E2E (add 10 new spec files)
│   ├── vitest.config.ts   # Coverage thresholds (bump: 49→80→90)
│   └── stryker.config.mjs # Mutation config (expand scope, add break threshold)
├── scripts/
│   ├── update-coverage-baseline.sh  # NEW: Baseline bump script
│   └── validate-contracts.sh        # Enhance with response body validation
├── .github/workflows/
│   ├── ci.yml             # Add ratchet + diff-cover steps
│   └── mutation.yml       # Expand shards (4→7)
└── .coverage-baseline.json # NEW: Coverage ratchet baseline
```

**Structure Decision**: Extends existing web application structure. No new top-level directories needed. All new files are placed within established directory conventions (tests alongside source for frontend, in `tests/` hierarchy for backend).

## Phase Breakdown

### Phase 1 — Foundation & CI Ratchet

**Goal**: Establish regression protection before adding tests.
**Dependencies**: None (foundation phase).
**User Stories**: US-1 (CI Coverage Ratchet)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 1.1 | Create `.coverage-baseline.json` with current metrics | `.coverage-baseline.json` | FR-001 |
| 1.2 | Add CI ratchet step (backend) comparing coverage.xml against baseline | `.github/workflows/ci.yml` | FR-002 |
| 1.3 | Add CI ratchet step (frontend) comparing coverage-summary.json against baseline | `.github/workflows/ci.yml` | FR-002 |
| 1.4 | Create `update-coverage-baseline.sh` script | `solune/scripts/update-coverage-baseline.sh` | FR-003 |
| 1.5 | Add diff-cover step for backend PRs | `.github/workflows/ci.yml` | FR-004 |
| 1.6 | Add diff-cover step for frontend PRs | `.github/workflows/ci.yml` | FR-004 |
| 1.7 | Bump backend `fail_under` from 71 to 75 | `solune/backend/pyproject.toml` | FR-005 |
| 1.8 | Bump frontend thresholds to current-minus-1% | `solune/frontend/vitest.config.ts` | FR-006 |
| 1.9 | Create `detect_flaky.py` script | `solune/backend/scripts/detect_flaky.py` | FR-027 |
| 1.10 | Add nightly flaky detection workflow | `.github/workflows/flaky-detection.yml` | FR-027 |
| 1.11 | Configure `@pytest.mark.flaky` marker in pytest | `solune/backend/pyproject.toml` | FR-027 |

**Acceptance**: PR that removes a test → CI fails. `update-coverage-baseline.sh` runs successfully.

---

### Phase 2 — Backend Services & API Layer

**Goal**: Fill backend coverage gaps systematically.
**Dependencies**: Phase 1 complete.
**User Stories**: US-2 (Backend Coverage 90%+)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 2.1 | Create test file for `github_commit_workflow.py` | `tests/unit/test_github_commit_workflow.py` | FR-007 |
| 2.2 | Create test file for `signal_bridge.py` | `tests/unit/test_signal_bridge.py` | FR-007 |
| 2.3 | Create test file for `signal_chat.py` | `tests/unit/test_signal_chat.py` | FR-007 |
| 2.4 | Create test file for `signal_delivery.py` | `tests/unit/test_signal_delivery.py` | FR-007 |
| 2.5 | Expand `ai_agent.py` tests (provider paths, streaming errors) | `tests/unit/test_ai_agent.py` | FR-007 |
| 2.6 | Expand `tools/service.py` tests | `tests/unit/test_tools_service.py` | FR-007 |
| 2.7 | Expand `workflow_orchestrator/` tests (all state transitions) | `tests/unit/test_workflow_orchestrator.py` | FR-007 |
| 2.8 | API error-path matrix: parameterized tests for all endpoints | `tests/unit/test_api_*.py` | FR-008 |
| 2.9 | Integration test: pipeline lifecycle | `tests/integration/test_pipeline_lifecycle.py` | FR-009 |
| 2.10 | Integration test: chat flow | `tests/integration/test_chat_flow.py` | FR-009 |
| 2.11 | Integration test: webhook processing | `tests/integration/test_webhook_processing.py` | FR-009 |
| 2.12 | Bump `fail_under` to 85 | `solune/backend/pyproject.toml` | FR-005 |

**Acceptance**: `pytest --cov=src` reports ≥85%. Every API test file covers ≥6 of 7 status codes.

---

### Phase 3 — Frontend Hooks & Components

**Goal**: Fill frontend coverage gaps systematically.
**Dependencies**: Phase 1 complete. Parallel with Phase 2.
**User Stories**: US-3 (Frontend Coverage 90%+)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 3.1 | Hook branch expansion: error states for all 44 hooks | `src/hooks/*.test.tsx` | FR-010 |
| 3.2 | Hook branch expansion: loading states | `src/hooks/*.test.tsx` | FR-010 |
| 3.3 | Hook branch expansion: empty/null edge cases | `src/hooks/*.test.tsx` | FR-010 |
| 3.4 | Hook branch expansion: cache invalidation | `src/hooks/*.test.tsx` | FR-010 |
| 3.5 | Priority hooks deep coverage: `useChat`, `useWorkflow`, `usePipelineConfig`, `useAgentConfig`, `useApps` | `src/hooks/*.test.tsx` | FR-010 |
| 3.6 | Component tests: High priority (TopBar, Sidebar, AppLayout, ProjectSelector, ChatInterface, ChatToolbar, BoardToolbar, CleanUpConfirmModal, settings sub-components) | `src/components/*.test.tsx` | FR-011 |
| 3.7 | Component tests: Medium priority (ChoreCard, ChoreInlineEditor, AgentPresetSelector, RateLimitBar) | `src/components/*.test.tsx` | FR-011 |
| 3.8 | Accessibility validation for all component tests | `src/components/*.test.tsx` | FR-011 |
| 3.9 | Expand `api.test.ts` to cover every export | `src/services/api.test.ts` | FR-012 |
| 3.10 | Schema negative tests (malformed, missing, coercion) | `src/lib/schemas/*.test.ts` | FR-012 |
| 3.11 | Bump frontend thresholds to 80/75/70/80 | `solune/frontend/vitest.config.ts` | FR-006 |

**Acceptance**: `npx vitest run --coverage` reports ≥80% statements, ≥75% branches. Every component test includes `expectNoA11yViolations()`.

---

### Phase 4 — Mutation Testing Expansion

**Goal**: Validate test quality beyond coverage metrics.
**Dependencies**: Phases 2 and 3 complete.
**User Stories**: US-4 (Mutation Testing)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 4.1 | Add 3 new mutmut shards: `api-endpoints`, `middleware`, `models` | `scripts/run_mutmut_shard.py` | FR-013 |
| 4.2 | Update mutation.yml matrix to include new shards | `.github/workflows/mutation.yml` | FR-013 |
| 4.3 | Expand Stryker mutate scope: add `src/services/**`, `src/utils/**` | `solune/frontend/stryker.config.mjs` | FR-014 |
| 4.4 | Set Stryker `thresholds.break: 60` | `solune/frontend/stryker.config.mjs` | FR-016 |
| 4.5 | Verify backend mutation score ≥75% per shard | CI verification | FR-015 |
| 4.6 | File issues for surviving mutant batches | GitHub Issues | FR-015 |

**Acceptance**: `mutmut run` per shard → ≥75% mutation score. `npx stryker run` → ≥60% mutation score.

---

### Phase 5 — Property-Based & Fuzz Testing

**Goal**: Discover edge cases that example-based tests miss.
**Dependencies**: Phase 1 complete. Parallel with Phases 2-3.
**User Stories**: US-5 (Property & Fuzz Testing)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 5.1 | Backend property tests: GraphQL query invariants | `tests/property/test_graphql_invariants.py` | FR-017 |
| 5.2 | Backend property tests: state machine transitions | `tests/property/test_state_machines.py` | FR-017 |
| 5.3 | Backend property tests: Pydantic model round-trips | `tests/property/test_model_roundtrips.py` | FR-017 |
| 5.4 | Backend property tests: encryption round-trip | `tests/property/test_encryption_roundtrip.py` | FR-017 |
| 5.5 | Backend property tests: pipeline config validation | `tests/property/test_pipeline_config.py` | FR-017 |
| 5.6 | Frontend property tests: URL construction invariants | `src/services/api.property.test.ts` | FR-018 |
| 5.7 | Frontend property tests: pipeline reducer invariants | `src/hooks/usePipelineConfig.property.test.ts` | FR-018 |
| 5.8 | Frontend property tests: Zod schema round-trips | `src/lib/schemas/*.property.test.ts` | FR-018 |
| 5.9 | Frontend property tests: pipeline migration idempotency | `src/lib/pipeline-migration.property.test.ts` | FR-018 |
| 5.10 | Backend fuzz: webhook payloads | `tests/fuzz/test_webhook_fuzz.py` | FR-019 |
| 5.11 | Backend fuzz: chat message injection | `tests/fuzz/test_chat_injection.py` | FR-019 |
| 5.12 | Backend fuzz: file upload path traversal | `tests/fuzz/test_upload_fuzz.py` | FR-019 |
| 5.13 | Frontend fuzz: paste events, nested JSON, emoji | `src/test/fuzz/*.test.ts` | FR-020 |

**Acceptance**: All property tests pass with 100+ generated examples. All fuzz tests pass without crashes.

---

### Phase 6 — E2E & Visual Regression

**Goal**: Expand end-to-end coverage and add visual regression baselines.
**Dependencies**: Phase 1 complete. Parallel with Phases 2-3.
**User Stories**: US-6 (E2E & Visual Regression)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 6.1 | E2E: pipeline-builder.spec.ts | `e2e/pipeline-builder.spec.ts` | FR-021 |
| 6.2 | E2E: agent-management.spec.ts | `e2e/agent-management.spec.ts` | FR-021 |
| 6.3 | E2E: apps-page.spec.ts | `e2e/apps-page.spec.ts` | FR-021 |
| 6.4 | E2E: chores-workflow.spec.ts | `e2e/chores-workflow.spec.ts` | FR-021 |
| 6.5 | E2E: projects-page.spec.ts | `e2e/projects-page.spec.ts` | FR-021 |
| 6.6 | E2E: tools-page.spec.ts | `e2e/tools-page.spec.ts` | FR-021 |
| 6.7 | E2E: help-page.spec.ts | `e2e/help-page.spec.ts` | FR-021 |
| 6.8 | E2E: keyboard-navigation.spec.ts | `e2e/keyboard-navigation.spec.ts` | FR-021 |
| 6.9 | E2E: dark-mode.spec.ts | `e2e/dark-mode.spec.ts` | FR-021 |
| 6.10 | E2E: error-recovery.spec.ts | `e2e/error-recovery.spec.ts` | FR-021 |
| 6.11 | Extend `fixtures.ts` with mock routes for new pages | `e2e/fixtures.ts` | FR-021 |
| 6.12 | Visual regression: toHaveScreenshot at 3 viewports × 2 modes | `e2e/*.spec.ts` | FR-022 |
| 6.13 | Stabilize E2E (track 2-week window) | CI monitoring | FR-023 |
| 6.14 | Make E2E blocking (remove `continue-on-error: true`) | `.github/workflows/ci.yml` | FR-023 |

**Acceptance**: `npx playwright test` → all specs pass (68+ tests). Screenshots match baselines.

---

### Phase 7 — Contract & Integration Testing

**Goal**: Validate system boundaries and API schema compliance.
**Dependencies**: Phase 1 complete. Parallel with Phases 2-3.
**User Stories**: US-7 (Contract & Integration Testing)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 7.1 | Integrate schemathesis for auto-generated API tests | CI configuration | FR-024 |
| 7.2 | Integration test: database migration correctness | `tests/integration/test_db_migrations.py` | FR-025 |
| 7.3 | Integration test: WebSocket lifecycle | `tests/integration/test_websocket_lifecycle.py` | FR-025 |
| 7.4 | Integration test: rate limiting end-to-end | `tests/integration/test_rate_limiting.py` | FR-025 |
| 7.5 | Integration test: guard config validation | `tests/integration/test_guard_config.py` | FR-025 |
| 7.6 | Integration test: chore scheduling cycle | `tests/integration/test_chore_scheduling.py` | FR-025 |
| 7.7 | Enhance `validate-contracts.sh` with response body validation | `solune/scripts/validate-contracts.sh` | FR-026 |

**Acceptance**: `bash solune/scripts/validate-contracts.sh` passes with schemathesis. All integration tests pass.

---

### Phase 8 — Coverage Ceiling & Maintenance

**Goal**: Lock final thresholds and establish maintenance processes.
**Dependencies**: All prior phases complete.
**User Stories**: US-1 (final lock), US-8 (Flaky Test Management)

| Step | Description | Key Files | FR |
|------|-------------|-----------|-----|
| 8.1 | Run `--cov-report=term-missing`, fill remaining gaps | Various test files | FR-029 |
| 8.2 | Justify all `# pragma: no cover` annotations | PR documentation | FR-033 |
| 8.3 | Lock backend `fail_under: 90` | `solune/backend/pyproject.toml` | FR-029 |
| 8.4 | Lock frontend thresholds: 90/85/85/90 | `solune/frontend/vitest.config.ts` | FR-030 |
| 8.5 | Update `.coverage-baseline.json` to final values | `.coverage-baseline.json` | FR-001 |
| 8.6 | Add PR template checklist for test coverage | `.github/pull_request_template.md` | FR-031 |
| 8.7 | Create monthly per-file audit script | `solune/scripts/audit-coverage.sh` | FR-032 |
| 8.8 | Verify max 5 quarantined flaky tests | CI/monitoring | FR-028 |

**Acceptance**: `pytest --cov=src` → ≥90%. `npx vitest run --coverage` → ≥90/85/85/90. All verification commands from spec pass.

---

## Dependency Graph

```
Phase 1 (Foundation & CI Ratchet)
    │
    ├──→ Phase 2 (Backend Services & API)  ──┐
    ├──→ Phase 3 (Frontend Hooks & Comps)  ──┤──→ Phase 4 (Mutation Testing)
    ├──→ Phase 5 (Property & Fuzz Testing)   │
    ├──→ Phase 6 (E2E & Visual Regression)   │
    └──→ Phase 7 (Contract & Integration)    │
                                              │
                                              └──→ Phase 8 (Coverage Ceiling)
```

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flaky E2E tests block transition to blocking mode | Medium | Quarantine process + 2-week stability window |
| Mutation testing takes too long in CI | Medium | Named shards enable parallelism; weekly schedule, not per-PR |
| Coverage targets unreachable for some modules | Low | `pragma: no cover` budget with justification; 90% not 100% |
| Fast-check / schemathesis integration issues | Low | Both are mature libraries; fallback to example-based tests |
| Existing tests break during refactoring | Medium | Ratchet prevents regression; run full suite before threshold bumps |

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |
