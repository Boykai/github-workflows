# Data Model: Comprehensive Test Coverage to 90%+

**Feature**: `050-comprehensive-test-coverage`
**Date**: 2026-03-17

---

## Entities

### Coverage Baseline

A JSON document recording current coverage metrics for both backend and frontend. Acts as the source of truth for the coverage ratchet mechanism.

**File**: `.coverage-baseline.json` (repository root)

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `version` | string | Schema version | Semver format (e.g., `"1.0.0"`) |
| `updated_at` | string | ISO 8601 timestamp of last update | Must be valid ISO 8601 |
| `backend.lines` | number | Backend line coverage percentage | 0–100, monotonically increasing |
| `backend.branches` | number | Backend branch coverage percentage | 0–100, monotonically increasing |
| `frontend.statements` | number | Frontend statement coverage | 0–100, monotonically increasing |
| `frontend.branches` | number | Frontend branch coverage | 0–100, monotonically increasing |
| `frontend.functions` | number | Frontend function coverage | 0–100, monotonically increasing |
| `frontend.lines` | number | Frontend line coverage | 0–100, monotonically increasing |

**Validation Rules**:

- All percentage values must be between 0 and 100 (inclusive)
- No value may decrease from the previous committed version (ratchet constraint)
- `updated_at` must be a valid ISO 8601 timestamp
- `version` must follow semver

**Example**:

```json
{
  "version": "1.0.0",
  "updated_at": "2026-03-17T15:00:00Z",
  "backend": {
    "lines": 71,
    "branches": 0
  },
  "frontend": {
    "statements": 49,
    "branches": 44,
    "functions": 41,
    "lines": 50
  }
}
```

---

### Coverage Threshold Configuration

Configured minimum coverage levels enforced by the CI pipeline. These are embedded in existing config files and increase through phases.

**Backend** (`solune/backend/pyproject.toml` → `[tool.coverage.report]`):

| Field | Type | Description | Phase Progression |
|-------|------|-------------|-------------------|
| `fail_under` | number | Minimum line coverage | 71 → 75 → 85 → 90 |

**Frontend** (`solune/frontend/vitest.config.ts` → `coverage.thresholds`):

| Field | Type | Description | Phase Progression |
|-------|------|-------------|-------------------|
| `statements` | number | Min statement coverage | 49 → 80 → 90 |
| `branches` | number | Min branch coverage | 44 → 75 → 85 |
| `functions` | number | Min function coverage | 41 → 70 → 85 |
| `lines` | number | Min line coverage | 50 → 80 → 90 |

---

### Quarantined Test

A test identified as flaky by the detection system, marked for tracking and resolution.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `test_id` | string | Fully qualified test name | Unique within suite |
| `quarantined_at` | string | ISO 8601 date of quarantine | Must be valid date |
| `reason` | string | Description of flaky behavior | Non-empty |
| `marker` | string | Backend: `@pytest.mark.flaky`, Frontend: `test.fixme()` | Must use appropriate marker |

**Validation Rules**:

- Maximum 5 quarantined tests at any time (system-wide)
- Must be resolved or removed within 30 days of quarantine
- Quarantined tests do not block CI

---

### Mutation Score Report

Output from mutation testing runs, tracking test quality beyond coverage.

**Backend** (per shard):

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `shard` | string | Named shard identifier | One of defined shards |
| `score` | number | Mutation kill percentage | Target: ≥75% |
| `killed` | number | Mutants killed by tests | Non-negative integer |
| `survived` | number | Mutants that survived | Non-negative integer |
| `timeout` | number | Mutants that timed out | Non-negative integer |

**Frontend**:

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `score` | number | Mutation kill percentage | Target: ≥60%, break threshold |
| `killed` | number | Mutants killed | Non-negative integer |
| `survived` | number | Mutants survived | Non-negative integer |

---

### Visual Snapshot Baseline

Stored screenshots used for visual regression detection.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `page` | string | Page identifier | Matches route |
| `viewport` | string | Viewport size label | One of 3 defined sizes |
| `color_mode` | string | `"light"` or `"dark"` | Enum: light, dark |
| `snapshot_path` | string | Path to baseline image | Relative to e2e snapshots dir |

**Total snapshots**: ~42 (7 pages × 3 viewports × 2 modes)

---

## Relationships

```
Coverage Baseline  ──reads──>  CI Pipeline  ──enforces──>  Coverage Threshold
                                    │
                                    ├──runs──>  diff-cover  ──reports──>  PR Annotations
                                    │
                                    ├──runs──>  Mutation Testing  ──produces──>  Mutation Score Report
                                    │
                                    └──runs──>  E2E Tests  ──compares──>  Visual Snapshot Baseline

Flaky Detection Script  ──identifies──>  Quarantined Test  ──tracked by──>  CI Pipeline
```

---

## State Transitions

### Coverage Threshold Lifecycle

```
Phase 1:  backend=75, frontend=49/44/41/50  (initial bump)
    │
    ▼
Phase 2:  backend=85                         (after service + API tests)
    │
Phase 3:  frontend=80/75/70/80              (after hook + component tests)
    │
    ▼
Phase 8:  backend=90, frontend=90/85/85/90  (final lock)
```

Thresholds ONLY increase — the ratchet ensures no decrease is possible.

### E2E Blocking State

```
Non-blocking (continue-on-error: true)
    │
    ▼  [2+ weeks of 0 flaky failures]
Blocking (continue-on-error removed)
```

### Quarantined Test Lifecycle

```
Healthy  ──[detected flaky]──>  Quarantined
    ▲                                │
    │                                ├──[fixed within 30 days]──> Healthy
    │                                │
    └────────────────────────────────└──[not fixed in 30 days]──> Removed
```
