# Testing Modernization Research

> Researched 2026-03-16 against the live Solune codebase.

---

## Topic 1: Backend Coverage Enforcement

### Decision

Add `[tool.coverage.run]` and `[tool.coverage.report]` sections to `pyproject.toml`, using `fail_under` in the `[tool.coverage.report]` section. Start with a threshold 2-3% below the current baseline and increment after each meaningful coverage gain.

### Configuration

```toml
# pyproject.toml

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 70          # start below current baseline, ratchet up
show_missing = true
skip_covered = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
]
```

The existing CI step (`pytest --cov=src --cov-report=term-missing`) will automatically pick up these settings from `pyproject.toml`.

### Rationale

- **`[tool.coverage.report]`** is where `fail_under` belongs — it controls the reporting/gate step, not the collection step.
- **`[tool.coverage.run]`** controls _what_ gets measured (source dirs, branch coverage).
- **Ratchet pattern**: set `fail_under` to `current_baseline - 2`, ensuring CI doesn't break on noise but prevents regression. After each sprint, measure and bump the threshold up. This avoids the "set it to 80% and leave a broken pipeline for weeks" anti-pattern.
- `branch = true` is best practice — line-only coverage hides untested conditional paths.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `--fail-under` CLI flag only | Duplicates config; `pyproject.toml` is the single source of truth |
| `setup.cfg` or `.coveragerc` | `pyproject.toml` is canonical for modern Python; project already uses it for ruff/pytest/pyright |
| `fail_under` in `[tool.coverage.run]` | Invalid — `fail_under` is a report-phase setting, not a collection-phase setting |
| Hard-coded 80% from day one | Will block merges until huge coverage push; ratchet is safer |

---

## Topic 2: Frontend Coverage Enforcement

### Decision

Add `coverage` block to the existing `vitest.config.ts` using `@vitest/coverage-v8` (already installed as devDependency). Use the `thresholds` key with per-metric minimums and enable `autoUpdate` for the ratchet pattern.

### Configuration

```ts
// vitest.config.ts
export default defineConfig({
  test: {
    // ...existing config...
    coverage: {
      provider: 'v8',
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'src/test/**',
        'src/**/*.test.{ts,tsx}',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
      thresholds: {
        lines: 60,
        branches: 55,
        functions: 60,
        statements: 60,
        // Auto-ratchet: bump thresholds when coverage improves
        autoUpdate: true,
      },
    },
  },
});
```

### Rationale

- **`@vitest/coverage-v8`** is already in `package.json` — no new dependency.
- **`thresholds`** is the Vitest 4 key (replaces the older `coverageThreshold` from Jest). Supports `lines`, `branches`, `functions`, `statements` as numbers. Positive = min percentage, negative = max uncovered count.
- **`autoUpdate: true`** implements the ratchet — Vitest rewrites `vitest.config.ts` thresholds when coverage exceeds them. Accepts a function `(newThreshold) => Math.floor(newThreshold)` for rounding control.
- **Glob-scoped thresholds** are available for critical directories: `'src/lib/**.ts': { lines: 90 }`.
- The existing `test:coverage` script (`vitest run --coverage`) will enforce thresholds.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Istanbul provider | v8 is faster, already installed, native V8 coverage is more accurate for TypeScript |
| Manual threshold bumps | `autoUpdate` automates the ratchet; one less manual step |
| `coveralls` / `codecov` cloud service | Adds external dependency; local threshold enforcement is faster feedback |
| Separate `vitest.coverage.ts` config | Unnecessary indirection; Vitest supports it inline |

---

## Topic 3: Backend Property-Based Testing with Hypothesis

### Decision

Add `hypothesis` to `[project.optional-dependencies] dev`, use `@given` + `@settings` decorators with pytest, and create Hypothesis profiles for `dev`/`ci`. Use `hypothesis.extra.pydantic` (`from_model`) for Pydantic v2 model fuzzing.

### Configuration

```toml
# pyproject.toml dev dependencies addition
"hypothesis[cli]>=6.130.0",
```

```python
# conftest.py or tests/conftest.py
from hypothesis import settings, HealthCheck

settings.register_profile("ci", max_examples=200, deadline=None)
settings.register_profile("dev", max_examples=10)

# Load from HYPOTHESIS_PROFILE env var or default
import os
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))
```

```python
# tests/property/test_models.py
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

class PipelineConfig(BaseModel):
    name: str
    max_retries: int
    enabled: bool

# Strategy that generates valid Pydantic instances
@given(st.builds(PipelineConfig, name=st.text(min_size=1), max_retries=st.integers(0, 10), enabled=st.booleans()))
def test_pipeline_config_roundtrip(config: PipelineConfig):
    data = config.model_dump()
    restored = PipelineConfig.model_validate(data)
    assert restored == config
```

### Rationale

- **pytest integration** is native — `@given` works as a decorator on any `test_*` function. No plugin needed; Hypothesis ships with a pytest plugin.
- **`asyncio_mode = "auto"`** (already set) means `@given` on `async def test_*` functions works out of the box with `pytest-asyncio >= 0.23`. Hypothesis generates data synchronously, the async function runs the assertions.
- **Pydantic v2**: Use `st.builds(MyModel, field=strategy)` — this calls the model constructor and Pydantic validation runs automatically. The older `hypothesis.extra.django` style `from_model` is for Django ORM; for Pydantic, `st.builds` is the canonical approach.
- **Settings profiles** let CI run 200 examples (thorough) while dev runs 10 (fast).
- `--hypothesis-profile=ci` can be passed in CI.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `hypothesis-jsonschema` | Generates from JSON Schema; `st.builds` is more precise for known Pydantic models |
| `schemathesis` | For API-level fuzzing, not unit-level model testing; complementary, not replacement |
| `faker` | Not property-based; generates single values, not property assertions with shrinking |
| `hypothesis.extra.pydantic` (hypothesmith) | Third-party; `st.builds` is first-party Hypothesis and works with Pydantic v2 directly |

---

## Topic 4: Frontend Property-Based Testing with fast-check

### Decision

Install `@fast-check/vitest` (the official Vitest integration) and use `test.prop` for property-based tests. Use `fc.assert`/`fc.property` for tests in non-Vitest contexts (pure utility libs).

### Configuration

```bash
npm install -D @fast-check/vitest fast-check
```

```ts
// src/lib/__tests__/url-utils.prop.test.ts
import { test, fc } from '@fast-check/vitest';

// test.prop — the idiomatic Vitest integration
test.prop([fc.string(), fc.string(), fc.string()])(
  'concatenated string always contains middle part',
  (a, b, c) => {
    return (a + b + c).includes(b);
  }
);

// Named parameters variant
test.prop({ input: fc.array(fc.integer()) })(
  'sorting is idempotent',
  ({ input }) => {
    const sorted1 = [...input].sort((a, b) => a - b);
    const sorted2 = [...sorted1].sort((a, b) => a - b);
    return JSON.stringify(sorted1) === JSON.stringify(sorted2);
  }
);

// Async properties
test.prop([fc.string({ minLength: 1 })])(
  'non-empty key round-trips through encode/decode',
  async (key) => {
    const encoded = encodeURIComponent(key);
    const decoded = decodeURIComponent(encoded);
    return decoded === key;
  }
);
```

### Rationale

- **`@fast-check/vitest`** provides `test.prop` which reads like normal Vitest tests, supports `.skip`, `.only`, `.concurrent`, and `{ seed, numRuns }` config.
- **`fc.assert` + `fc.property`** is the lower-level API — use it when you need more control (custom runners, describe blocks) or in pure JS utility code.
- fast-check is the de-facto standard for JS property testing (9.5 trust score, 1123 snippets).
- Supports Vitest modifiers: `test.skip.prop`, `test.only.prop`, `test.concurrent.prop`.
- `fc.configureGlobal({ seed: 12345 })` in setup file makes tests deterministic in CI.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `jsverify` | Unmaintained since 2019 |
| `testcheck-js` | Minimal community, no Vitest integration |
| Manually calling `fc.assert` everywhere | `test.prop` is cleaner Vitest integration, better error messages |
| `faker.js` | Not property-based; no shrinking, no exhaustive search |

---

## Topic 5: Backend Mutation Testing with mutmut

### Decision

Add `mutmut` to dev dependencies and configure via `[tool.mutmut]` in `pyproject.toml`. Scope to `src/services/` or specific high-value directories. Run on a weekly cron schedule in CI, not on every PR.

### Configuration

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = "src/services/"
tests_dir = "tests/"
runner = "python -m pytest -x -q"
dict_synonyms = "Struct,NamedStruct"
```

```yaml
# .github/workflows/mutation.yml (weekly)
name: Mutation Testing
on:
  schedule:
    - cron: '0 6 * * 1'  # Monday 6 AM UTC
  workflow_dispatch: {}

permissions:
  contents: read

jobs:
  backend-mutation:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: solune/backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - run: pip install -e ".[dev]" mutmut
      - run: mutmut run --paths-to-mutate=src/services/ --CI
      - run: mutmut results
```

### Rationale

- **`[tool.mutmut]`** in `pyproject.toml` is the standard config location. `paths_to_mutate` scopes mutations to avoid testing boilerplate.
- **`--CI`** flag produces non-interactive output suitable for CI.
- **Weekly schedule**: Mutation testing is slow (minutes to hours). Running on every PR would bottleneck CI. Weekly cron catches regression trends without blocking developers.
- **`-x` flag** in runner makes pytest stop on first failure per mutant — fastest feedback.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `cosmic-ray` | Less maintained, more complex config, smaller community |
| `mutatest` | Archived project |
| Running mutation on every PR | Too slow; mutation testing can take 10–60 min depending on test suite size |
| `mutmut` without scoping | Would mutate entire `src/` including low-value boilerplate; scope to services for ROI |

---

## Topic 6: Frontend Mutation Testing with Stryker

### Decision

Use `@stryker-mutator/core` + `@stryker-mutator/vitest-runner` with a `stryker.config.mjs` file. Scope `mutate` to `src/hooks/` and `src/lib/` initially. Run on the same weekly cron as backend mutation testing.

### Configuration

```bash
npm install -D @stryker-mutator/core @stryker-mutator/vitest-runner
```

```js
// stryker.config.mjs
/** @type {import('@stryker-mutator/api/core').StrykerOptions} */
export default {
  $schema: './node_modules/@stryker-mutator/core/schema/stryker-schema.json',
  testRunner: 'vitest',
  plugins: ['@stryker-mutator/vitest-runner'],
  mutate: [
    'src/hooks/**/*.ts',
    'src/lib/**/*.ts',
    '!src/**/*.test.*',
    '!src/**/*.spec.*',
  ],
  coverageAnalysis: 'perTest',
  reporters: ['clear-text', 'progress', 'html'],
  incremental: true,
  incrementalFile: 'reports/stryker-incremental.json',
  thresholds: {
    high: 80,
    low: 60,
    break: null,  // set to 50 once baseline established
  },
  concurrency: 4,
  timeoutMS: 10000,
  ignoreStatic: true,
};
```

```json
// package.json script
"test:mutate": "stryker run"
```

### Rationale

- **`@stryker-mutator/vitest-runner`** is the official plugin — Stryker discovers tests via vitest and runs them against mutants.
- **`.mjs` format** enables ESM imports and `@type` JSDoc for IDE autocomplete via the JSON schema.
- **`mutate` glob patterns** with `!` exclusions scope mutations to high-value utility code. `src/hooks/` and `src/lib/` are where most logic lives; `src/components/` can be added later.
- **`incremental: true`** caches results between runs — only re-tests mutants in changed files.
- **`coverageAnalysis: 'perTest'`** is the most efficient mode — only runs tests that cover each mutant.
- **`ignoreStatic: true`** skips static initializers (imports, constants) that generate many equivalent mutants.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Stryker with Jest runner | Project uses Vitest, not Jest |
| `infection` (PHP) | Wrong ecosystem |
| Running Stryker on every PR | Too slow for PR CI; weekly cron is standard practice |
| Scoping to all of `src/` | Too many mutants initially; start narrow, expand after baseline |

---

## Topic 7: API Contract Validation

### Decision

Export FastAPI's OpenAPI spec via a Python script, generate TypeScript types with `openapi-typescript`, and validate frontend mock factories against the spec in CI using a custom validation script.

### Configuration

```python
# scripts/export_openapi.py
"""Export FastAPI OpenAPI spec to JSON file."""
import json
import sys
sys.path.insert(0, "src")
from main import app  # adjust to actual app import

spec = app.openapi()
with open("openapi.json", "w") as f:
    json.dump(spec, f, indent=2)
print("Exported openapi.json")
```

```bash
# Generate TypeScript types from spec
npx openapi-typescript openapi.json -o src/types/api.generated.ts
```

```yaml
# CI step
- name: Validate API contract
  run: |
    cd solune/backend && python scripts/export_openapi.py
    cd ../frontend && npx openapi-typescript ../backend/openapi.json -o src/types/api.check.ts
    diff src/types/api.generated.ts src/types/api.check.ts
```

### Rationale

- **FastAPI auto-generates OpenAPI** from Pydantic models — `app.openapi()` returns the full spec dict. No extra library needed.
- **`openapi-typescript`** generates TypeScript interfaces directly from OpenAPI 3.x. The generated types can be diffed in CI to detect drift.
- This is lighter than Pact (which requires a broker, provider/consumer setup) — appropriate for a single-team monorepo where both sides are in the same repo.
- **Alternative for runtime validation**: `openapi-diff` (npm: `openapi-diff`) can compare two spec versions and report breaking changes.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Pact | Overkill for a monorepo; Pact is designed for multi-team microservices with separate repos and release cycles |
| `prism` (Stoplight) | Mock server approach; useful for contract testing but heavier setup |
| Manual TypeScript types | Drift-prone; auto-generation eliminates human error |
| `openapi-generator` | Generates full client SDKs; we only need types, `openapi-typescript` is lighter |
| `orval` | Similar to openapi-typescript but also generates React Query hooks; adds more generated code than needed for just contract validation |

---

## Topic 8: Visual Regression with Playwright

### Decision

Use Playwright's built-in `toHaveScreenshot()` API with `maxDiffPixels` tolerance. Store baselines in Git. Run only in the Chromium project; skip screenshots on Firefox/WebKit with `ignoreSnapshots: true`.

### Configuration

```ts
// playwright.config.ts additions
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 50,        // allow minor anti-aliasing diffs
      animations: 'disabled',    // freeze CSS/Web animations
      stylePath: './e2e/screenshot.css', // hide dynamic content
    },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
      ignoreSnapshots: true,   // don't compare screenshots on Firefox
    },
  ],
});
```

```ts
// e2e/visual.spec.ts
import { test, expect } from '@playwright/test';

test('dashboard renders correctly', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('dashboard.png');
});

test('specific component visual', async ({ page }) => {
  await page.goto('/agents');
  const card = page.getByTestId('agent-card');
  await expect(card).toHaveScreenshot('agent-card.png', {
    maxDiffPixels: 20,
  });
});
```

```css
/* e2e/screenshot.css — hide dynamic content during screenshots */
[data-testid="timestamp"],
[data-testid="avatar"] {
  visibility: hidden;
}
```

### Rationale

- **`toHaveScreenshot()`** auto-creates baselines on first run (stored in `<testfile>-snapshots/` directories alongside test files). Subsequent runs compare pixel-by-pixel.
- **`maxDiffPixels`** handles anti-aliasing and sub-pixel rendering differences across CI environments.
- **`animations: 'disabled'`** prevents flaky screenshots from in-progress CSS transitions.
- **Baselines stored in Git** — team reviews visual changes in PRs. Update with `npx playwright test --update-snapshots`.
- **`ignoreSnapshots: true`** on non-Chromium projects avoids maintaining separate baselines per browser (fonts/rendering vary too much).

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Percy / Chromatic (cloud) | Paid services; Playwright's built-in is free and sufficient for a single team |
| `pixelmatch` directly | `toHaveScreenshot()` already uses pixelmatch under the hood |
| `threshold` (ratio) | `maxDiffPixels` (absolute count) is more predictable than ratio for varying page sizes |
| Baselines in separate repo | Harder to review; keeping them alongside tests in Git is standard |

---

## Topic 9: Accessibility Testing

### Decision

Use `@axe-core/playwright` for E2E accessibility scans and `jest-axe` (already installed) for component-level a11y checks in Vitest. Create a shared test utility that wraps `axe` for consistent usage.

### Configuration

```bash
npm install -D @axe-core/playwright
```

```ts
// e2e/a11y.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('home page passes a11y', async ({ page }) => {
  await page.goto('/');
  const results = await new AxeBuilder({ page })
    .exclude('#third-party-widget')  // exclude known third-party issues
    .analyze();
  expect(results.violations).toEqual([]);
});

test('agents page passes a11y', async ({ page }) => {
  await page.goto('/agents');
  const results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});
```

```ts
// src/test/a11y-utils.ts — shared utility for component tests
import { axe, toHaveNoViolations } from 'jest-axe';
import { expect } from 'vitest';

expect.extend(toHaveNoViolations);

export async function expectNoA11yViolations(container: HTMLElement) {
  const results = await axe(container);
  expect(results).toHaveNoViolations();
}
```

```ts
// src/components/Button.test.tsx
import { render } from '@testing-library/react';
import { expectNoA11yViolations } from '@/test/a11y-utils';
import { Button } from './Button';

test('Button has no a11y violations', async () => {
  const { container } = render(<Button>Click me</Button>);
  await expectNoA11yViolations(container);
});
```

### Rationale

- **Two layers**: Component-level (jest-axe in Vitest, fast, catches ARIA/label issues early) + E2E-level (@axe-core/playwright, catches real browser rendering issues).
- **`jest-axe`** is already in `package.json` — zero new dependencies for component tests.
- **Shared utility** (`expectNoA11yViolations`) reduces boilerplate and ensures consistent configuration across all component tests.
- **`eslint-plugin-jsx-a11y`** is already configured in `eslint.config.js` — provides static analysis as the third layer.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `pa11y` | Good for CLI/CI but `@axe-core/playwright` integrates natively into existing Playwright tests |
| `jest-axe` only | Misses browser-level rendering issues (CSS hiding, focus traps, screen reader behavior) |
| `@axe-core/playwright` only | Slower than component tests; component-level catches issues earlier in dev loop |
| Lighthouse CI a11y score | Aggregate score is less actionable than individual violation reports |

---

## Topic 10: Multi-Browser E2E

### Decision

Add a Firefox project to the existing Playwright config. No separate base image needed — `npx playwright install firefox` works on the standard `ubuntu-latest` runner with system dependencies.

### Configuration

```ts
// playwright.config.ts — updated projects array
projects: [
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'] },
  },
  {
    name: 'firefox',
    use: { ...devices['Desktop Firefox'] },
    ignoreSnapshots: true,  // don't compare visual snapshots on Firefox
  },
],
```

```yaml
# CI step addition in .github/workflows/ci.yml
- name: Install Playwright browsers
  run: npx playwright install --with-deps chromium firefox
```

### Rationale

- **`--with-deps`** installs system dependencies (libgtk, libasound, etc.) automatically on Ubuntu.
- **No separate Docker image needed** — Playwright handles browser downloads. The GitHub Actions `ubuntu-latest` image has sufficient system libraries when `--with-deps` is used.
- **`ignoreSnapshots: true`** on Firefox avoids maintaining separate screenshot baselines (cross-browser font rendering differs too much).
- WebKit can be added later; Firefox is the highest-value second browser (different engine from Chromium).

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `mcr.microsoft.com/playwright:v1.58.2` Docker image | Heavier CI setup; `--with-deps` on ubuntu-latest is simpler |
| WebKit instead of Firefox | Firefox has more real-world usage share; Blink-vs-Gecko is the most valuable cross-engine check |
| Separate CI jobs per browser | Adds matrix complexity; running both in one job with Playwright's `--project` flag is simpler for 2 browsers |
| BrowserStack / Sauce Labs | Paid; Playwright's local browser installs are sufficient for CI |

---

## Topic 11: Security Scanning

### Decision

Add four security scanning tools: `pip-audit` and `bandit` for backend, `eslint-plugin-security` and `npm audit` for frontend. All run as steps in the existing CI jobs.

### Configuration

#### pip-audit

```bash
pip install pip-audit
pip-audit --require-hashes --strict --desc
```

```yaml
# CI step in backend job
- name: Security audit (pip-audit)
  run: pip-audit --strict
```

#### bandit

```toml
# pyproject.toml
[tool.bandit]
exclude_dirs = ["tests", "htmlcov"]
skips = ["B101"]  # skip assert_used (common in tests)
severity = "medium"
confidence = "medium"
```

```yaml
# CI step in backend job
- name: Security scan (bandit)
  run: bandit -r src -c pyproject.toml
```

```toml
# pyproject.toml dev dependencies addition
"pip-audit>=2.9.0",
"bandit[toml]>=1.9.0",
```

#### eslint-plugin-security

```bash
npm install -D eslint-plugin-security
```

```js
// eslint.config.js — add to existing flat config
import security from 'eslint-plugin-security';

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
      'jsx-a11y': jsxA11y,
      'security': security,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      ...security.configs.recommended.rules,
      // existing rules...
    },
  }
);
```

#### npm audit

```yaml
# CI step in frontend job
- name: Security audit (npm)
  run: npm audit --audit-level=high
```

### Rationale

- **`pip-audit`**: Checks installed packages against the PyPI advisory database (OSV). `--strict` exits non-zero on any vulnerability. Fast (<10s).
- **`bandit`**: Static analysis for Python security issues (SQL injection, hardcoded passwords, unsafe deserialization). `[toml]` extra enables `pyproject.toml` config. Severity/confidence set to `medium` to catch meaningful issues without noise.
- **`eslint-plugin-security`**: Flat config compatible. Catches `eval()`, `child_process`, regex DoS, `innerHTML` assignments. Integrates into the existing ESLint run — no separate CI step needed (already runs `npm run lint`).
- **`npm audit --audit-level=high`**: Checks npm dependencies against the advisory database. `--audit-level=high` ignores low/moderate to avoid blocking on non-exploitable issues.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| `safety` (Python) | Commercial license for full database; `pip-audit` uses the free OSV database |
| `snyk` | Paid for private repos; these tools are free and sufficient |
| `semgrep` | More powerful but heavier setup; bandit is standard for Python security |
| `npm audit --audit-level=critical` | Too permissive; `high` catches exploitable issues without excessive noise |
| GitHub Dependabot only | Good complement but only handles dependency versions, not code-level issues (bandit/eslint-plugin-security) |

---

## Topic 12: CI Integration Patterns

### Decision

Add security scanning as new steps within the existing `backend` and `frontend` jobs. Create a separate workflow file for weekly mutation testing. Do not create separate jobs for each new check.

### Configuration

```yaml
# .github/workflows/ci.yml — additions to existing backend job
      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=term-missing
        # fail_under enforced via pyproject.toml [tool.coverage.report]

      - name: Security audit (pip-audit)
        run: pip-audit --strict

      - name: Security scan (bandit)
        run: bandit -r src -c pyproject.toml
```

```yaml
# .github/workflows/ci.yml — additions to existing frontend job
      - name: Run tests
        run: npm test

      # npm audit uses the already-installed deps
      - name: Security audit (npm)
        run: npm audit --audit-level=high

      # eslint-plugin-security runs as part of existing lint step (no change needed)

      - name: Build
        run: npm run build
```

```yaml
# .github/workflows/mutation.yml — new file, weekly schedule
name: Mutation Testing

on:
  schedule:
    - cron: '0 6 * * 1'   # Monday 6:00 AM UTC
  workflow_dispatch: {}

permissions:
  contents: read

concurrency:
  group: mutation-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend-mutation:
    name: Backend Mutation
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: solune/backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
      - run: pip install -e ".[dev]" mutmut
      - run: mutmut run --paths-to-mutate=src/services/ --CI
      - run: mutmut results

  frontend-mutation:
    name: Frontend Mutation
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: solune/frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: npm
          cache-dependency-path: solune/frontend/package-lock.json
      - run: npm ci
      - run: npm install -D @stryker-mutator/core @stryker-mutator/vitest-runner
      - run: npx stryker run
```

### Rationale

- **Steps within existing jobs** (not separate jobs): Avoids runner provisioning overhead. Security scans (`pip-audit`, `bandit`, `npm audit`) take <30 seconds each — not worth the 30-60s job startup cost.
- **`eslint-plugin-security`** requires zero CI change — it runs as part of the existing `npm run lint` step in the frontend job.
- **Separate workflow for mutation**: Mutation testing runs 10-60 minutes. It should never block PR merges. A `workflow_dispatch` trigger allows manual runs. The `schedule` trigger runs weekly.
- **`concurrency` group** prevents overlapping mutation runs.
- **No matrix strategy** for mutation — backend and frontend mutation are separate jobs because they have different toolchains and failure modes.

### Alternatives Considered

| Alternative | Why not |
|---|---|
| Separate CI jobs for each security tool | Wastes 30-60s runner startup per tool; steps in existing jobs are faster |
| Mutation testing in PR CI | Too slow; blocks developer workflow |
| Single "security" job | Would need to install both Python and Node.js; reusing existing jobs is simpler |
| `workflow_call` reusable workflows | Over-engineering for 2 mutation jobs; direct workflow file is clearer |
| Nightly instead of weekly mutation | Mutation results don't change daily; weekly is sufficient for trend analysis |
