# Data Model: Increase Test Coverage to Surface Unknown Bugs

**Feature**: `049-increase-test-coverage` | **Date**: 2026-03-17

## Overview

This feature does not introduce new application data models or persistence changes. It adds test files, CI configuration, and coverage enforcement. The "entities" below describe the conceptual structures that the implementation plan tracks and manipulates.

## Entities

### Coverage Phase

Represents a discrete unit of test-writing work with a defined scope and coverage target.

| Field | Type | Description |
|-------|------|-------------|
| `phase_id` | string | Unique identifier (e.g., `phase-1`, `phase-7`) |
| `name` | string | Human-readable phase name |
| `scope` | enum | `backend` \| `frontend` \| `ci` \| `both` |
| `target_modules` | string[] | List of source modules to be tested |
| `coverage_before` | CoverageMetrics | Coverage metrics before phase |
| `coverage_after` | CoverageMetrics | Expected coverage metrics after phase |
| `threshold_bump` | CoverageMetrics | New CI threshold to set after merge |
| `template_files` | string[] | Existing test files to use as templates |
| `new_test_files` | string[] | Test files to create |
| `dependencies` | string[] | Phase IDs that must complete first |
| `priority` | string | P1–P3 from spec priority |

### Coverage Metrics

Tracks coverage numbers for a specific point in time.

| Field | Type | Description |
|-------|------|-------------|
| `line` | number | Line coverage percentage |
| `branch` | number | Branch coverage percentage |
| `function` | number | Function coverage percentage (frontend only) |
| `statement` | number | Statement coverage percentage (frontend only) |

### Test Suite

A collection of test files grouped by testing strategy.

| Field | Type | Description |
|-------|------|-------------|
| `suite_type` | enum | `unit` \| `property` \| `fuzz` \| `chaos` \| `concurrency` \| `mutation` \| `architecture` \| `integration` |
| `platform` | enum | `backend` \| `frontend` |
| `timeout_seconds` | number | Maximum per-test execution time |
| `blocking` | boolean | Whether failures block merge |
| `ci_trigger` | enum | `pull_request` \| `schedule` \| `workflow_dispatch` |

### Mutation Report

Results from mutation testing showing surviving and killed mutants.

| Field | Type | Description |
|-------|------|-------------|
| `platform` | enum | `backend` \| `frontend` |
| `tool` | string | `mutmut` (backend) or `@stryker-mutator` (frontend) |
| `total_mutants` | number | Total mutations generated |
| `killed_count` | number | Mutants killed by tests |
| `surviving_count` | number | Mutants that survived tests |
| `survival_rate` | number | Percentage of mutants surviving |
| `top_survivors` | MutantSurvivor[] | Ranked list of surviving mutants |

### Mutant Survivor

A single mutation that survived the test suite.

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Source file containing the mutant |
| `line` | number | Line number of the mutation |
| `mutation_type` | enum | `boundary` \| `boolean_negation` \| `arithmetic` \| `conditional` \| `return_value` |
| `original` | string | Original code |
| `mutated` | string | Mutated code |

### Architecture Rule

Defines a directional import constraint between code layers.

| Field | Type | Description |
|-------|------|-------------|
| `rule_id` | string | Unique rule identifier |
| `source_layer` | string | The layer being checked (e.g., `services/`) |
| `forbidden_target` | string | The layer that must not be imported (e.g., `api/`) |
| `platform` | enum | `backend` \| `frontend` |
| `known_violations` | ImportViolation[] | Existing violations in the allowlist |

### Import Violation

Represents a known layer violation that is temporarily allowed.

| Field | Type | Description |
|-------|------|-------------|
| `source_file` | string | File containing the violating import |
| `import_target` | string | The forbidden module being imported |
| `reason` | string | Why this violation exists |
| `tracked_since` | date | When the violation was added to the allowlist |

### CI Job Definition

Describes a CI job to be added or modified.

| Field | Type | Description |
|-------|------|-------------|
| `job_name` | string | CI job identifier |
| `workflow_file` | string | Which workflow YAML file contains this job |
| `trigger` | enum | `pull_request` \| `schedule` \| `workflow_dispatch` |
| `schedule` | string? | Cron expression for scheduled jobs |
| `commands` | string[] | Shell commands to execute |
| `timeout_minutes` | number | Maximum job runtime |
| `required` | boolean | Whether job failure blocks merge |

### Flaky Test Record

A test identified as producing inconsistent results.

| Field | Type | Description |
|-------|------|-------------|
| `test_name` | string | Fully qualified test name |
| `file_path` | string | Test file containing the test |
| `failure_rate` | number | Percentage of runs where the test fails |
| `remediation_status` | enum | `identified` \| `quarantined` \| `fixed` |

## Relationships

```
Coverage Phase ──has── Coverage Metrics (before/after/threshold)
Coverage Phase ──depends-on── Coverage Phase
Coverage Phase ──creates── Test Suite
Test Suite ──contains── Test Files
Architecture Rule ──contains── Import Violation[]
CI Job Definition ──enforces── Coverage Phase (via threshold)
CI Job Definition ──runs── Test Suite
CI Job Definition ──runs── Architecture Rule (via test execution)
Mutation Report ──contains── Mutant Survivor[]
Mutation Report ──generated-by── CI Job Definition (weekly schedule)
Flaky Test Record ──detected-by── CI Job Definition (scheduled 3× run)
```

## Phase → Module Mapping

### Backend Phases

| Phase | Target Modules | New Test Files |
|-------|---------------|----------------|
| Phase 2 (Backend Coverage 71→76%) | `github_projects/agents.py`, `copilot_polling/helpers.py`, `copilot_polling/pipeline.py`, `chores/chat.py`, `chores/template_builder.py`, `api/agents.py`, `api/health.py`, `api/webhook_models.py` | `tests/unit/test_github_agents.py`, `tests/unit/test_polling_helpers.py`, `tests/unit/test_polling_pipeline.py`, `tests/unit/test_chores_chat.py`, `tests/unit/test_chores_template_builder.py`, `tests/unit/test_api_agents.py`, `tests/unit/test_api_health.py`, `tests/unit/test_api_webhook_models.py` |
| Phase 5 (Mutation Hardening) | Top 20 surviving mutants from `src/services/` | `tests/unit/test_mutation_kills.py` (targeted boundary/negation/arithmetic tests) |

### Frontend Phases

| Phase | Target Modules | New Test Files |
|-------|---------------|----------------|
| Phase 3 (Hooks & Services 50→53/48/45/54%) | `services/schemas/*.ts` (6 files), 24 untested hooks | `services/schemas/*.test.ts` (6 files), `hooks/*.test.tsx` (24 files) |
| Phase 4 (Components 53→60/55/52/60%) | `components/settings/` (14), `components/board/` (11), `components/pipeline/` (9), remaining ~19 | `components/**/*.test.tsx` (~53 files) |
| Phase 5 (Mutation Hardening) | Top 20 surviving mutants | Strengthened assertions in existing test files |

### CI & Cross-Cutting Phases

| Phase | Type | New/Modified Files |
|-------|------|-------------------|
| Phase 1 (CI Foundation) | CI config | `.github/workflows/ci.yml` (modified: advanced test job, flaky detection), `.github/workflows/mutation.yml` (new) |
| Phase 6 (Production-Parity & Time) | Integration tests | `tests/integration/test_production_mode.py`, `tests/unit/test_time_dependent.py`, frontend time-controlled tests |
| Phase 7 (Architecture) | Fitness tests | `tests/architecture/test_import_rules.py`, `src/__tests__/architecture/import-rules.test.ts` |

## State Transitions

### Coverage Threshold Lifecycle

```
INITIAL (current thresholds)
  ↓ Phase 2 merges → bump backend to 76%
PHASE_2_RATCHETED
  ↓ Phase 3 merges → bump frontend to 53/48/45/54%
PHASE_3_RATCHETED
  ↓ Phase 4 merges → bump frontend to 60/55/52/60%
PHASE_4_RATCHETED
  ↓ Phase 5 merges → bump backend to 80%
FINAL (80% backend, 60/55/52/60% frontend)
```

### Advanced Test CI Status

```
NON_BLOCKING (initial: allow-failure)
  ↓ baselines stabilize (0 flaky after 2 weeks)
BLOCKING (failures prevent merge)
```

## Validation Rules

1. **Coverage ratchet**: Thresholds can only increase, never decrease
2. **Architecture allowlist**: Can only shrink (violations removed), never grow (new violations added) after initial baseline
3. **Test timeout**: All advanced tests must complete within 120 seconds per test
4. **CI budget**: Backend test suite increase ≤90s total; Frontend test suite increase ≤60s total
5. **Template conformance**: All new test files must follow the structure of their designated template file
6. **Mutation kill target**: ≥10 previously-surviving mutants killed per mutation-hardening phase
