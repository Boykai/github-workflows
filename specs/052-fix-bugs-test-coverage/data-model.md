# Data Model: Find & Fix Bugs, Increase Test Coverage (Phase 2)

**Feature**: `052-fix-bugs-test-coverage`
**Date**: 2026-03-19

## Overview

This feature does not introduce new data entities to the application. It operates on existing source code, test infrastructure, and CI configuration. The "entities" below represent the conceptual data model used for tracking and verification throughout the implementation.

## Entities

### CoverageThreshold

Represents a minimum coverage percentage enforced by tooling configuration.

| Field | Type | Description |
|-------|------|-------------|
| metric | enum: line, statement, branch, function | The coverage metric being measured |
| value | integer (0–100) | The minimum percentage required |
| scope | enum: backend, frontend | Which codebase the threshold applies to |
| config_file | string | Path to the configuration file where the threshold is defined |
| enforced | boolean | Whether CI rejects commits below this threshold |

**Current state → Target state:**

| Scope | Metric | Current | Target |
|-------|--------|---------|--------|
| Backend | line | 75 | 80 |
| Frontend | statement | 50 | 55 |
| Frontend | branch | 44 | 50 |
| Frontend | function | 41 | 45 |
| Frontend | line | 50 | 55 |

**Validation rules:**
- Thresholds only ratchet upward (target ≥ current)
- Thresholds are enforced only after verification passes (Phase E)

---

### MutationShard

Represents a partitioned subset of source modules targeted for mutation testing.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Shard identifier (e.g., "auth-and-projects") |
| targets | list[string] | Source file/directory paths included in this shard |
| kill_rate | float (0.0–1.0) | Percentage of mutants killed by the test suite |
| status | enum: pending, executed, triaged | Execution progress |

**Instances:**

| Shard | Targets | Kill Rate Target |
|-------|---------|-----------------|
| auth-and-projects | github_auth, completion_providers, model_fetcher, github_projects/ | >60% |
| orchestration | workflow_orchestrator/, pipelines/, copilot_polling/, task_registry, pipeline_state_store, agent_tracking | >60% |
| app-and-data | app_service, guard_service, metadata_service, cache, database, stores (5), cleanup, encryption, websocket | >60% |
| agents-and-integrations | ai_agent, agent_creator, github_commit_workflow, signal_bridge/chat/delivery, tools/, agents/, chores/ | >60% |
| api-and-middleware | api/ (19 modules), middleware/ (5 modules), utils | >60% |

**Stryker (frontend):**
- Scope: `src/hooks/**/*.ts`, `src/lib/**/*.ts`
- Kill rate target: >60%

---

### FlakyTest

Represents a test that produces inconsistent results across identical runs.

| Field | Type | Description |
|-------|------|-------------|
| test_id | string | Fully qualified test name (e.g., `tests/unit/test_foo.py::TestFoo::test_bar`) |
| suite | enum: backend, frontend | Which test suite the test belongs to |
| root_cause | string | Documented reason for flakiness |
| issue_url | string | URL of the tracked issue |
| quarantine_marker | string | The skip marker applied (e.g., `@pytest.mark.skip(reason="flaky: ...")`) |
| detection_run | integer | Which iteration (1–5) first detected the failure |

**Validation rules:**
- Every FlakyTest must have a non-empty root_cause
- Every FlakyTest must have a corresponding tracked issue

---

### SurvivingMutant

Represents a code mutation that no test detects.

| Field | Type | Description |
|-------|------|-------------|
| shard | string | Which mutation shard produced this mutant |
| location | string | File path + line number of the mutation |
| mutation_type | string | Type of mutation (e.g., "changed == to !=") |
| classification | enum: killable, equivalent, non-killable | Triage result |
| justification | string | Why the mutant was classified this way (required for equivalent/non-killable) |
| resolution | string | Test file + assertion added (required for killable) |

**Validation rules:**
- killable mutants must have a resolution (targeted assertion)
- equivalent/non-killable mutants must have a justification

---

### QualityGate

Represents a verification checkpoint that must pass before proceeding.

| Field | Type | Description |
|-------|------|-------------|
| gate_id | string | Unique identifier (e.g., "static-analysis-clean") |
| phase | enum: A, B, C, D, E | Which implementation phase owns this gate |
| verification_command | string | The command to run to check the gate |
| expected_exit_code | integer | Expected exit code (0 = pass) |
| status | enum: pending, passed, failed | Current gate status |

**Instances:**

| Gate | Phase | Command |
|------|-------|---------|
| frontend-lint-clean | A | `eslint .` |
| frontend-types-clean | A | `tsc --noEmit` |
| backend-lint-clean | A | `ruff check src/` |
| backend-types-clean | A | `pyright` |
| backend-security-clean | A | `bandit -r src/ -s B104,B608` |
| zero-flaky-tests | A | `python scripts/detect_flaky.py` (5 runs) |
| zero-asyncmock-warnings | A | `pytest 2>&1 \| grep -c "AsyncMock"` = 0 |
| backend-coverage-80 | B | `pytest --cov=src --cov-fail-under=80` |
| frontend-coverage-55-50-45 | C | `vitest run --coverage` (thresholds enforced) |
| mutation-shards-executed | D | All 5 shards + Stryker complete |
| thresholds-ratcheted | E | Config files updated |
| precommit-under-30s | E | `time scripts/pre-commit` < 30s |

## Relationships

```
CoverageThreshold --[verified-by]--> QualityGate (backend-coverage-80, frontend-coverage-55-50-45)
MutationShard --[produces]--> SurvivingMutant (0..n per shard)
SurvivingMutant --[resolved-by]--> Test assertion (for killable mutants)
FlakyTest --[detected-by]--> QualityGate (zero-flaky-tests)
QualityGate --[blocks]--> Phase transition (A→B, D→E, etc.)
```

## State Transitions

### QualityGate Lifecycle

```
pending → passed (verification command exits 0)
pending → failed (verification command exits non-zero)
failed → pending (fix applied, ready for re-verification)
```

### SurvivingMutant Lifecycle

```
unclassified → killable (test gap identified)
unclassified → equivalent (mutation doesn't change behavior)
unclassified → non-killable (impractical to test)
killable → resolved (targeted assertion written)
```
