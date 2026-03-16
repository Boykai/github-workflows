# Data Model: Increase Test Coverage & Surface Unknown Bugs

**Feature**: `048-test-coverage-bugs` | **Date**: 2026-03-16

## Overview

This feature does not introduce new application data models. It adds test files, CI configuration, and coverage enforcement. The "entities" below describe the conceptual structures that the implementation plan tracks and manipulates.

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
| `priority` | string | P1–P11 from spec priority |

### Coverage Metrics

Tracks coverage numbers for a specific point in time.

| Field | Type | Description |
|-------|------|-------------|
| `line` | number | Line coverage percentage |
| `branch` | number | Branch coverage percentage (frontend only, backend has no threshold) |
| `function` | number | Function coverage percentage (frontend only) |
| `statement` | number | Statement coverage percentage (frontend only) |

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

## Relationships

```
Coverage Phase ──has── Coverage Metrics (before/after/threshold)
Coverage Phase ──depends-on── Coverage Phase
Architecture Rule ──contains── Import Violation[]
CI Job Definition ──enforces── Coverage Phase (via threshold)
CI Job Definition ──runs── Architecture Rule (via test execution)
```

## Phase → Module Mapping

### Backend Phases

| Phase | Target Modules | New Test Files |
|-------|---------------|----------------|
| Phase 1 (P2) | `github_projects/graphql.py`, `issues.py`, `pull_requests.py`, `branches.py`, `copilot.py`, `identities.py`, `repository.py`, `projects.py`, `board.py`, `agents.py` | `tests/unit/test_graphql.py`, `test_issues.py`, `test_pull_requests.py`, `test_repository.py`, `test_branches.py`, `test_copilot.py`, `test_identities.py`, `test_projects.py`, `test_board.py` |
| Phase 2 (P3) | `copilot_polling/state.py`, `pipeline.py`, `state_validation.py`, `helpers.py`; `metadata_service.py`, `guard_service.py`, `chat_store.py`, `app_service.py`, `signal_delivery.py`, `github_commit_workflow.py`, `signal_bridge.py`; `api/apps.py`, `cleanup.py`, `metadata.py`, `signal.py`; `dependencies.py`, `protocols.py` | `tests/unit/test_polling_state.py`, `test_polling_pipeline.py`, `test_state_validation.py`, `test_polling_helpers.py`, `test_metadata_service.py`, `test_guard_service.py`, `test_chat_store.py`, `test_app_service.py`, `test_signal_delivery.py`, `test_github_commit_workflow.py`, `test_signal_bridge.py`, `test_api_apps.py`, `test_api_cleanup.py`, `test_api_metadata.py`, `test_api_signal.py`, `test_dependencies.py`, `test_protocols.py` |
| Phase 3 (P4) | Top 10 files by uncovered branches (determined by HTML coverage report) | `tests/unit/test_edge_cases_*.py` (files TBD based on coverage report) |

### Frontend Phases

| Phase | Target Modules | New Test Files |
|-------|---------------|----------------|
| Phase 4 (P5) | `services/schemas/*.ts` (6 files), `services/api.ts`, 24 hooks | `services/schemas/*.test.ts`, `hooks/*.test.tsx` (20+ files) |
| Phase 5 (P6) | `components/settings/` (14), `components/pipeline/` (8), `components/board/` (12) | `components/settings/*.test.tsx`, `components/pipeline/*.test.tsx`, `components/board/*.test.tsx` |
| Phase 6 (P6) | `components/agents/` (8), `components/tools/` (9), `components/chores/` (10), `components/chat/` (6), `layout/` (8), remaining | `components/*/*.test.tsx`, `layout/*.test.tsx` |

### Bug-Surfacing Phases

| Phase | Type | New Files |
|-------|------|-----------|
| Phase 7 (P1) | CI config | `.github/workflows/ci.yml` (modified), `.github/workflows/mutation.yml` (new) |
| Phase 8 (P8) | Time-controlled | `tests/unit/test_time_dependent.py`, frontend `*.test.ts` files with `vi.useFakeTimers()` |
| Phase 9 (P7) | Production-parity | `tests/integration/test_production_mode.py`, `tests/integration/test_config_matrix.py` |
| Phase 10 (P9) | Architecture | `tests/architecture/test_import_rules.py`, `src/__tests__/architecture/test_import_rules.test.ts` |
| Phase 11 (P10) | Property/fuzz | `tests/property/test_polling_tiers.py`, `test_prompt_generators.py`, `tests/fuzz/test_webhook_fuzz_expanded.py`, frontend `*.property.test.ts` |
| Phase 12 (P11) | WebSocket E2E | Playwright test files |

## Validation Rules

1. **Coverage ratchet**: Thresholds can only increase, never decrease
2. **Architecture allowlist**: Can only shrink (violations removed), never grow (new violations added) after initial baseline
3. **Test timeout**: All advanced tests must complete within 120 seconds per test
4. **CI budget**: Backend test suite increase ≤90s total; Frontend test suite increase ≤60s total
5. **Template conformance**: All new test files must follow the structure of their designated template file
