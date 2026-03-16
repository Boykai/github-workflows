# Quickstart: Modernize Testing to Surface Unknown Bugs

**Branch**: `046-modernize-testing` | **Date**: 2026-03-16

## Prerequisites

- Python 3.12+ with the backend virtualenv activated
- Node.js 20+ with `npm ci` run in `solune/frontend/`
- Docker (for full integration verification)

## Phase 1: Coverage Enforcement

### Backend

1. Measure the current baseline:
   ```bash
   cd solune/backend
   pytest --cov=src --cov-report=term-missing
   ```
   Note the total coverage percentage (e.g., 72%).

2. Add coverage configuration to `pyproject.toml`:
   ```toml
   [tool.coverage.run]
   source = ["src"]
   branch = true

   [tool.coverage.report]
   fail_under = 70  # set to baseline - 2
   show_missing = true
   skip_covered = true
   exclude_lines = [
       "pragma: no cover",
       "if TYPE_CHECKING:",
   ]
   ```

3. Verify: Delete a test file temporarily, run `pytest --cov=src` — CI should fail.

### Frontend

1. Measure the current baseline:
   ```bash
   cd solune/frontend
   npm run test:coverage
   ```
   Note line, branch, function, statement percentages.

2. Add coverage thresholds to `vitest.config.ts`:
   ```ts
   coverage: {
     provider: 'v8',
     thresholds: {
       lines: 40,    // set to baseline - 2
       branches: 30,
       functions: 35,
       statements: 40,
     },
   },
   ```

3. Verify: Remove a test file temporarily, run `npm run test:coverage` — should fail.

## Phase 2: Property-Based Tests

### Backend (Hypothesis)

1. Install: `pip install hypothesis`
2. Create `tests/property/` directory
3. Write a property test:
   ```python
   from hypothesis import given, strategies as st
   from src.models.agent import AgentConfig

   @given(name=st.text(min_size=1, max_size=200))
   def test_agent_config_name_roundtrip(name):
       config = AgentConfig(name=name, ...)
       assert config.name == name
   ```
4. Run: `pytest tests/property/`

### Frontend (fast-check)

1. Install: `npm install -D @fast-check/vitest`
2. Write a property test:
   ```ts
   import { test } from '@fast-check/vitest';
   import fc from 'fast-check';

   test.prop([fc.string()], 'formatAgentName never crashes', (input) => {
     expect(() => formatAgentName(input)).not.toThrow();
   });
   ```
3. Run: `npm test`

## Phase 3: Mutation Testing

### Backend (mutmut)

1. Install: `pip install mutmut`
2. Configure in `pyproject.toml`:
   ```toml
   [tool.mutmut]
   paths_to_mutate = "src/services/"
   tests_dir = "tests/"
   ```
3. Run: `mutmut run` (takes 10-30 min for `src/services/`)
4. View results: `mutmut results`

### Frontend (Stryker)

1. Install: `npm install -D @stryker-mutator/core @stryker-mutator/vitest-runner`
2. Create `stryker.config.mjs`:
   ```js
   /** @type {import('@stryker-mutator/api/core').PartialStrykerOptions} */
   export default {
     testRunner: 'vitest',
     vitest: { configFile: 'vitest.config.ts' },
     mutate: ['src/hooks/**/*.ts', 'src/lib/**/*.ts'],
     incremental: true,
     timeoutMS: 60000,
   };
   ```
3. Run: `npx stryker run`

## Phase 4: Contract Validation

1. Create `solune/scripts/export-openapi.sh`:
   ```bash
   #!/usr/bin/env bash
   cd solune/backend
   python -c "from src.main import app; import json; print(json.dumps(app.openapi(), indent=2))" > openapi.json
   ```
2. Generate TypeScript types: `npx openapi-typescript openapi.json -o src/types/api.generated.ts`
3. Write a CI step that diffs the generated types against the existing type definitions.

## Phase 5: Visual & Accessibility Regression

1. Add `toHaveScreenshot()` to existing E2E tests:
   ```ts
   await expect(page).toHaveScreenshot('dashboard.png', { maxDiffPixels: 100 });
   ```
2. Generate baselines: `npx playwright test --update-snapshots`
3. Add Firefox to `playwright.config.ts` projects.
4. Add `@axe-core/playwright`:
   ```ts
   import AxeBuilder from '@axe-core/playwright';
   const results = await new AxeBuilder({ page }).analyze();
   expect(results.violations).toEqual([]);
   ```

## Phase 6: Security Scanning

1. Backend: `pip install pip-audit bandit`
2. Frontend: `npm install -D eslint-plugin-security`
3. Run:
   ```bash
   pip-audit
   bandit -r src/ -ll -ii
   npm audit --audit-level=moderate
   npm run lint
   ```

## Verification Checklist

- [ ] `pytest --cov=src` fails when coverage drops below threshold
- [ ] `npm run test:coverage` fails when coverage drops below threshold
- [ ] Property tests generate 1000+ inputs and either pass or report minimized failures
- [ ] `mutmut results` lists surviving mutants with file/line
- [ ] `stryker run` produces an HTML report with mutation scores
- [ ] Renaming a backend response field triggers contract validation failure
- [ ] CSS change triggers `toHaveScreenshot()` failure
- [ ] Removing a form label triggers a11y audit failure
- [ ] `pip-audit` reports a deliberately pinned vulnerable package
- [ ] `bandit` catches a deliberately introduced hardcoded secret
- [ ] `npm audit` reports a deliberately pinned vulnerable package
- [ ] ESLint security plugin catches a deliberately introduced `eval()` call
