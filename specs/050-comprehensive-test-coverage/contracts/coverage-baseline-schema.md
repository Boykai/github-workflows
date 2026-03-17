# Contract: Coverage Baseline Schema

**Feature**: `050-comprehensive-test-coverage`
**Date**: 2026-03-17

---

## `.coverage-baseline.json` Schema

This file is committed to the repository root and serves as the ratchet reference.

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Coverage Baseline",
  "description": "Coverage metrics baseline for ratchet enforcement",
  "type": "object",
  "required": ["version", "updated_at", "backend", "frontend"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Schema version in semver format"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp of last update"
    },
    "backend": {
      "type": "object",
      "required": ["lines"],
      "properties": {
        "lines": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Backend line coverage percentage"
        },
        "branches": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Backend branch coverage percentage"
        }
      }
    },
    "frontend": {
      "type": "object",
      "required": ["statements", "branches", "functions", "lines"],
      "properties": {
        "statements": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Frontend statement coverage"
        },
        "branches": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Frontend branch coverage"
        },
        "functions": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Frontend function coverage"
        },
        "lines": {
          "type": "number",
          "minimum": 0,
          "maximum": 100,
          "description": "Frontend line coverage"
        }
      }
    }
  }
}
```

### Ratchet Constraint (enforced by CI script)

```
For each metric M in {backend.lines, backend.branches,
                       frontend.statements, frontend.branches,
                       frontend.functions, frontend.lines}:
  current_value(M) >= baseline_value(M)
```

If any metric decreases, the CI step exits with a non-zero code and prints:

```
COVERAGE REGRESSION DETECTED:
  {metric_name}: {current_value}% < baseline {baseline_value}%
  Decrease of {delta}% is not allowed.
```

---

## `update-coverage-baseline.sh` Interface

```bash
# Usage
solune/scripts/update-coverage-baseline.sh

# Behavior
# 1. Reads current coverage from backend coverage.xml and frontend coverage-summary.json
# 2. Validates that all metrics are >= current baseline
# 3. Writes new .coverage-baseline.json with updated values
# 4. Prints diff of changes for review

# Exit codes
# 0 - Baseline updated successfully
# 1 - Current coverage is below baseline (regression detected)
# 2 - Missing coverage report files
```
