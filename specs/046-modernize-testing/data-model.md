# Data Model: Modernize Testing to Surface Unknown Bugs

**Branch**: `046-modernize-testing` | **Date**: 2026-03-16

## Overview

This feature is test-infrastructure focused — it does not introduce runtime data entities or persistence changes. The "entities" below represent configuration artifacts and CI outputs that the feature introduces.

## Configuration Entities

### CoverageConfig (Backend)

Configures pytest-cov behavior and the coverage gate.

| Field | Type | Description |
|---|---|---|
| source | list[str] | Directories to instrument (e.g., `["src"]`) |
| branch | bool | Whether to measure branch coverage |
| fail_under | float | Minimum coverage percentage to pass CI |
| exclude_lines | list[str] | Patterns excluded from coverage measurement |

**Location**: `solune/backend/pyproject.toml` under `[tool.coverage.run]` and `[tool.coverage.report]`

**Validation**: `fail_under` must be ≥ 0 and ≤ 100. `source` must be non-empty.

### CoverageConfig (Frontend)

Configures Vitest coverage thresholds.

| Field | Type | Description |
|---|---|---|
| provider | string | Coverage provider (`"v8"`) |
| thresholds.lines | number | Minimum line coverage percentage |
| thresholds.branches | number | Minimum branch coverage percentage |
| thresholds.functions | number | Minimum function coverage percentage |
| thresholds.statements | number | Minimum statement coverage percentage |
| thresholds.autoUpdate | boolean | Auto-raise thresholds when coverage improves |

**Location**: `solune/frontend/vitest.config.ts` under `test.coverage`

### MutationConfig (Backend)

Configures mutmut mutation testing scope.

| Field | Type | Description |
|---|---|---|
| paths_to_mutate | string | Source path to mutate (e.g., `src/services/`) |
| tests_dir | string | Test directory for validation (e.g., `tests/`) |
| runner | string | Test runner command |

**Location**: `solune/backend/pyproject.toml` under `[tool.mutmut]`

### MutationConfig (Frontend)

Configures Stryker mutation testing scope.

| Field | Type | Description |
|---|---|---|
| mutate | list[string] | Glob patterns for source files to mutate |
| testRunner | string | Test runner (`"vitest"`) |
| vitest.configFile | string | Path to vitest config |
| incremental | boolean | Reuse previous results for unchanged files |
| timeoutMS | number | Per-mutant timeout |

**Location**: `solune/frontend/stryker.config.mjs`

### OpenAPISpec

The auto-generated API specification used for contract validation.

| Field | Type | Description |
|---|---|---|
| openapi | string | OpenAPI version (e.g., `"3.1.0"`) |
| info | object | API title, version, description |
| paths | object | Every route with request/response schemas |
| components.schemas | object | All Pydantic model schemas |

**Location**: Generated at CI time to `solune/backend/openapi.json`; not committed.

**Relationships**: Validated against frontend mock factories in `solune/frontend/src/test/` to detect schema drift.

### SecurityConfig (Backend)

Configures Bandit security linting.

| Field | Type | Description |
|---|---|---|
| targets | list[string] | Directories to scan |
| skips | list[string] | Rule IDs to suppress (if any) |
| severity | string | Minimum severity to report |
| confidence | string | Minimum confidence to report |

**Location**: `solune/backend/pyproject.toml` under `[tool.bandit]`

## State Transitions

### Coverage Threshold Ratchet

```
INITIAL → BASELINED → ENFORCED → RATCHETED
```

1. **INITIAL**: No threshold configured.
2. **BASELINED**: Run coverage tool, record current percentage.
3. **ENFORCED**: Set `fail_under` to `baseline - 2%`. CI gates on this.
4. **RATCHETED**: Periodically increase `fail_under` after test improvements land.

### Mutation Report Lifecycle

```
SCHEDULED → RUNNING → COMPLETED → REVIEWED
```

1. **SCHEDULED**: Cron triggers the mutation workflow.
2. **RUNNING**: Mutants generated and tested.
3. **COMPLETED**: Report generated listing surviving mutants.
4. **REVIEWED**: Developer reviews surviving mutants, strengthens tests or acknowledges.

### Screenshot Baseline Lifecycle

```
MISSING → GENERATED → COMMITTED → COMPARED
```

1. **MISSING**: No baseline exists for the page/component.
2. **GENERATED**: First test run creates the baseline snapshot.
3. **COMMITTED**: Baseline committed to repository and reviewed in PR.
4. **COMPARED**: Subsequent runs diff against committed baseline.

## Relationships

```
CoverageConfig (backend) ──────→ CI backend job (pytest --cov)
CoverageConfig (frontend) ─────→ CI frontend job (vitest --coverage)
MutationConfig (backend) ──────→ CI scheduled workflow (mutmut)
MutationConfig (frontend) ─────→ CI scheduled workflow (Stryker)
OpenAPISpec ────────────────────→ Contract validation CI step
SecurityConfig (backend) ──────→ CI backend job (bandit)
Screenshot baselines ──────────→ CI E2E job (Playwright toHaveScreenshot)
```
