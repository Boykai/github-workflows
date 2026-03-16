# Contract: CI Pipeline Additions

**Feature**: 046-modernize-testing

This document defines the contracts between the new CI pipeline steps and the project's configuration files. Since this feature is infrastructure-focused (no new HTTP endpoints), the "contracts" are the interfaces between tools and their configuration.

---

## Contract 1: Coverage Enforcement (Backend)

**Producer**: `pytest --cov=src --cov-report=term-missing`
**Consumer**: CI backend job

### Input

- `pyproject.toml` with `[tool.coverage.run]` and `[tool.coverage.report]` sections
- Python source files in `src/`
- Test files in `tests/`

### Output

- Terminal coverage report with per-file line-miss details
- Exit code 2 if `fail_under` threshold is not met (fail)
- Exit code 0 if threshold is met (pass)

### Contract Rules

- `fail_under` MUST be a float between 0 and 100
- Any value below the threshold produces a non-zero exit code
- Report MUST include file paths and missing line numbers

---

## Contract 2: Coverage Enforcement (Frontend)

**Producer**: `vitest run --coverage`
**Consumer**: CI frontend job

### Input

- `vitest.config.ts` with `test.coverage` block containing `thresholds`
- TypeScript source files in `src/`
- Test files matching `src/**/*.{test,spec}.{ts,tsx}`

### Output

- Terminal coverage report with per-file details
- Non-zero exit code if any threshold (lines, branches, functions, statements) is not met
- When `autoUpdate: true`, vitest.config.ts thresholds are updated in-place when coverage improves

### Contract Rules

- All four threshold types (lines, branches, functions, statements) MUST be configured
- Thresholds MUST be integers or floats between 0 and 100

---

## Contract 3: API Contract Validation

**Producer**: FastAPI backend (`app.openapi()`)
**Consumer**: CI contract-validation step

### Input

- Running FastAPI application instance (or importable `app` object)
- Frontend mock factories in `src/test/` and type definitions

### Output (export step)

- `openapi.json` — full OpenAPI 3.1 specification in JSON format

### Output (validation step)

- Pass: All frontend mock shapes conform to OpenAPI schema definitions
- Fail: List of mismatched fields with expected (from spec) vs actual (from mocks)

### Contract Rules

- `openapi.json` MUST be regenerated on every CI run (not committed)
- Validation compares schema property names and types
- Additional frontend-only properties are permitted (superset OK)
- Missing required properties from the spec are errors

---

## Contract 4: Mutation Testing Reports

**Producer**: mutmut (backend) / Stryker (frontend)
**Consumer**: Developers (via CI artifacts)

### Output Format (mutmut)

```
Surviving mutants:
  - src/services/pipeline_service.py:42 — Changed `==` to `!=`
  - src/services/tools/service.py:87 — Removed return value
```

### Output Format (Stryker)

```json
{
  "files": {
    "src/hooks/useAgents.ts": {
      "mutants": [
        {
          "id": "1",
          "status": "Survived",
          "location": { "start": { "line": 15, "column": 4 } },
          "description": "ConditionalExpression: replaced true with false"
        }
      ]
    }
  }
}
```

### Contract Rules

- Reports MUST include: file path, line number, mutation description, survival status
- Mutation testing runs MUST have a per-mutant timeout to prevent infinite loops
- Reports are CI artifacts (uploaded), not committed

---

## Contract 5: Security Scanning

**Producer**: pip-audit, bandit, npm audit, eslint-plugin-security
**Consumer**: CI jobs

### Output (pip-audit)

- Exit 0: No known vulnerabilities
- Exit 1: Vulnerabilities found, listing package name, installed version, CVE ID, fixed version

### Output (bandit)

- Exit 0: No findings at configured severity/confidence
- Exit 1: Findings listed with file, line, rule ID, severity, description

### Output (npm audit)

- Exit 0: No vulnerabilities at configured audit level
- Exit 1+: Vulnerabilities listed with package, severity, advisory URL

### Output (eslint-plugin-security)

- Integrated into existing `npm run lint` step
- ESLint reports security violations as errors alongside existing rules

### Contract Rules

- All four tools MUST produce non-zero exit codes on findings
- Findings MUST include enough context to locate and fix the issue

---

## Contract 6: Visual Regression

**Producer**: Playwright `toHaveScreenshot()`
**Consumer**: CI E2E job

### Input

- Baseline screenshots in `e2e/*.spec.ts-snapshots/` (committed)
- Current rendered pages via Playwright browser

### Output

- Pass: All screenshots match within configured tolerance
- Fail: Diff images showing pixel-level differences, stored as test artifacts

### Contract Rules

- `maxDiffPixels` or `maxDiffPixelRatio` MUST be configured to allow sub-pixel anti-aliasing variance
- Screenshots are Chromium-only (Firefox excluded via `ignoreSnapshots: true`)
- Missing baselines on first run generate new baselines (test passes)
- Baseline updates require explicit `--update-snapshots` flag

---

## Contract 7: Accessibility Audits

**Producer**: jest-axe (component tests), @axe-core/playwright (E2E tests)
**Consumer**: CI test jobs

### Output

- Pass: No WCAG violations detected
- Fail: Violation list with rule ID, impact level, affected HTML element, and remediation guidance

### Contract Rules

- Component tests use `expectNoA11yViolations()` from `src/test/a11y-helpers.ts`
- E2E tests use `@axe-core/playwright` `AxeBuilder` API
- Both produce axe-core compatible output
