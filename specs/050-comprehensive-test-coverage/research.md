# Research: Comprehensive Test Coverage to 90%+

**Feature**: `050-comprehensive-test-coverage`
**Date**: 2026-03-17
**Status**: Complete

---

## Research Task 1: Current Coverage Baseline and Gap Analysis

### Decision

Use the existing coverage infrastructure (pytest-cov for backend, Vitest v8 for frontend) with incremental threshold ratcheting. Current baselines: backend 71% lines, frontend 49% statements / 44% branches / 41% functions / 50% lines.

### Rationale

The existing tooling is mature and well-integrated into CI. Rather than replacing tools, the strategy adds enforcement layers (ratchet, diff-cover) on top of established infrastructure. The gap between current and target (71→90 backend, 49→90 frontend) requires phased increases to avoid blocking all PRs.

### Alternatives Considered

- **All-at-once threshold bump**: Rejected — would block all PRs until coverage target is met, paralyzing development.
- **Per-file thresholds instead of aggregate**: Rejected — too granular and maintenance-heavy; aggregate thresholds with diff-cover achieves the same goal more simply.
- **Replace Vitest with Jest**: Rejected — Vitest is already configured, faster for Vite projects, and has adequate coverage tooling.

---

## Research Task 2: Coverage Ratchet Implementation Patterns

### Decision

Implement a JSON baseline file (`.coverage-baseline.json`) with a CI comparison step. A helper script (`solune/scripts/update-coverage-baseline.sh`) bumps the baseline after intentional increases.

### Rationale

JSON baseline provides machine-readable, diffable, version-controlled coverage state. The comparison step reads both the baseline and current coverage XML/JSON output, then fails CI if any metric decreased. This is simpler and more transparent than tool-specific ratchet plugins.

### Alternatives Considered

- **coveralls/codecov cloud ratchet**: Rejected — adds external dependency, slower feedback, requires token management.
- **pytest-cov `--cov-fail-under` only**: Rejected — only supports a single line-coverage threshold; cannot ratchet multiple metrics or prevent decreases.
- **Git hook enforcement**: Rejected — easily bypassed, not centralized, doesn't cover CI-only metrics.

---

## Research Task 3: Diff-Coverage Best Practices

### Decision

Use `diff-cover` (Python tool) for backend and a custom Vitest coverage comparison for frontend. Report coverage of changed lines on every PR as a non-blocking annotation.

### Rationale

`diff-cover` integrates with `coverage.xml` output and Git diffs natively. It provides line-level feedback without blocking PRs, allowing developers to see gaps while the team ratchets overall thresholds upward. For frontend, Vitest's `--changed` flag or a similar diff-based approach can be used.

### Alternatives Considered

- **Blocking diff-cover**: Rejected — too aggressive initially; would block infrastructure/config PRs with no testable code.
- **Codecov PR annotations**: Rejected — requires external service; self-hosted solution is more reliable and faster.

---

## Research Task 4: Flaky Test Detection and Quarantine

### Decision

Implement a nightly `detect_flaky.py` script that reruns the test suite with `--count=5` (pytest-repeat) and identifies tests that fail inconsistently. Quarantined tests use `@pytest.mark.flaky` (backend) and `test.fixme()` (frontend). Cap at 5 quarantined tests.

### Rationale

Nightly detection catches flakiness without slowing CI. The quarantine markers allow flaky tests to be skipped in blocking CI while remaining visible for resolution. The 5-test cap prevents quarantine from becoming a dumping ground.

### Alternatives Considered

- **pytest-rerunfailures in CI**: Rejected — masks flakiness rather than surfacing it; increases CI time.
- **Immediate test removal**: Rejected — loses coverage; quarantine preserves the test for eventual fixing.
- **Weekly manual review**: Rejected — too slow; automation catches issues before they accumulate.

---

## Research Task 5: Mutation Testing Expansion Strategy

### Decision

Expand mutmut shards from 4 to 7 (adding `api`, `middleware`, `models` shards) and expand Stryker scope to include `src/services/**` and `src/utils/**`. Set Stryker `thresholds.break: 60` to make frontend mutations blocking.

### Rationale

Current mutation testing covers only `src/services/` (backend) and `src/hooks/**` + `src/lib/**` (frontend). The expanded scope covers the most business-critical code paths. Named shards keep CI time manageable by parallelizing mutation runs. The 60% break threshold for Stryker is aggressive enough to catch weak tests without being unreachable.

### Alternatives Considered

- **Single large mutmut run**: Rejected — too slow; sharding enables parallelism and per-area thresholds.
- **Frontend mutation testing with vitest-mutate**: Rejected — Stryker is already configured and more mature.
- **75% Stryker threshold**: Rejected — frontend starts from a lower base; 60% is a realistic first target.

---

## Research Task 6: Property-Based and Fuzz Testing Libraries

### Decision

Use Hypothesis (already available as a dependency) for backend property tests and fast-check for frontend. Fuzz tests extend existing `tests/fuzz/` infrastructure.

### Rationale

Hypothesis is the standard Python property-based testing library with pytest integration. fast-check is the leading TypeScript equivalent with excellent Vitest compatibility. Both generate random inputs that exercise invariants, catching edge cases that example-based tests miss. The existing `tests/property/` and `tests/fuzz/` directories confirm this infrastructure is already scaffolded.

### Alternatives Considered

- **Backend: hypothesis-jsonschema**: Considered as complement — useful for OpenAPI schema fuzzing but separate from core property tests.
- **Frontend: jsverify**: Rejected — less maintained than fast-check, smaller community.
- **AFL-based fuzzing**: Rejected — overkill for this codebase; Python/TS fuzz tests in-process are sufficient.

---

## Research Task 7: E2E Expansion and Visual Regression Strategy

### Decision

Add 10 new Playwright spec files targeting uncovered user workflows. Add `toHaveScreenshot()` assertions at 3 viewport sizes × 2 color modes for every major page. Make E2E blocking only after 2+ weeks of zero flaky failures.

### Rationale

Current E2E coverage (14 specs) focuses on auth, navigation, and settings. The new specs cover feature-specific workflows (pipeline builder, agent management, apps, chores, tools). Visual regression at multiple viewports catches responsive layout bugs. The stability prerequisite for blocking E2E prevents false failure fatigue.

### Alternatives Considered

- **Cypress instead of Playwright**: Rejected — Playwright is already configured with fixtures, viewports, and snapshots.
- **Percy/Chromatic for visual regression**: Rejected — external service; Playwright's built-in `toHaveScreenshot()` is sufficient and free.
- **Immediately blocking E2E**: Rejected — current `continue-on-error: true` exists for a reason; stability must be proven first.

---

## Research Task 8: Schemathesis and Contract Testing

### Decision

Integrate schemathesis to auto-generate API test cases from the existing `openapi.json` export. Run in CI as part of the contract-validation job. Enhance `validate-contracts.sh` with response body validation.

### Rationale

Schemathesis automatically generates test cases from OpenAPI schemas, catching schema violations, missing fields, and type mismatches without manual test authoring. The existing `export-openapi.py` script already generates the schema. Adding schemathesis to the existing contract-validation workflow is minimal overhead.

### Alternatives Considered

- **Dredd**: Rejected — less actively maintained than schemathesis; schemathesis has better property-based test generation.
- **Manual contract tests**: Rejected — doesn't scale; schema-driven generation catches more edge cases automatically.
- **Pact for consumer-driven contracts**: Rejected — overkill for a single frontend/backend pair; schemathesis covers the use case.

---

## Research Task 9: Backend Service Module Testing Patterns

### Decision

Follow the existing test patterns in `tests/unit/` — use `mock_db` fixture with real SQLite, `make_mock_*_service()` factories, and async test functions with `asyncio_mode="auto"`. Each service module gets a dedicated test file covering happy path + error paths.

### Rationale

The existing test infrastructure (conftest.py fixtures, factory helpers, async support) is well-designed for service-level testing. Matching existing patterns ensures consistency and reduces onboarding friction. The `mock_db` fixture with real SQLite provides realistic database behavior without external dependencies.

### Alternatives Considered

- **Docker-based integration database**: Rejected — too heavy for unit tests; mock_db with SQLite is sufficient and fast.
- **Mocking all database calls**: Rejected — loses SQL validation; real SQLite catches query errors.
- **Shared test base classes**: Rejected — violates YAGNI; individual test files with shared fixtures are simpler.

---

## Research Task 10: Frontend Component Testing Patterns

### Decision

Follow the existing patterns in `src/**/*.test.tsx` — use `renderWithProviders()` from `test-utils.tsx`, `createMockApi()` from `setup.ts`, and factory functions from `src/test/factories/`. Every interactive component test includes `expectNoA11yViolations()` for accessibility.

### Rationale

The existing test utilities handle QueryClient setup, provider wrapping, and API mocking consistently. Adding component tests that follow this pattern integrates seamlessly. The accessibility check ensures new component tests contribute to both coverage and quality.

### Alternatives Considered

- **Testing Library with user-event v14**: Already in use — continue using it for interaction testing.
- **Storybook interaction tests**: Rejected — adds tooling complexity; direct Vitest tests are faster and more focused.
- **Snapshot testing for components**: Rejected — brittle and low-value; render → interact → assert is more reliable.
