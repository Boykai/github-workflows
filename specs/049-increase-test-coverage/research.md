# Research: Increase Test Coverage to Surface Unknown Bugs

**Feature**: `049-increase-test-coverage` | **Date**: 2026-03-17

## Research Tasks & Findings

### RT-001: Existing Backend Test Infrastructure & Patterns

**Decision**: Reuse all existing test patterns and shared fixtures from `tests/conftest.py` without introducing new frameworks or base classes.

**Rationale**: The backend already has a mature test infrastructure established across 50+ test files:
- `mock_db`: In-memory SQLite with migrations applied — used by all service tests
- `mock_session`, `mock_access_token`: Standard auth stubs
- `mock_github_service`, `mock_github_auth_service`, `mock_ai_agent_service`: AsyncMock specs for all major services
- `client`: httpx.AsyncClient wired to FastAPI with dependency overrides
- Autouse cache-clearing fixture for test isolation
- Helper factories: `make_mock_github_service(**overrides)`, `make_mock_github_auth_service(**overrides)`, etc. in `tests/helpers/factories.py`

Template files to follow:
- **API route tests**: `tests/unit/test_api_chat.py` — Uses `client` fixture, class-based test groups per endpoint, verifies status codes and response shapes
- **Service tests**: `tests/unit/test_pipeline_state_store.py` — Uses `mock_db` with DDL setup, helper factories for test data, covers CRUD and fallback behavior
- **GitHub integration tests**: `tests/unit/test_github_projects.py` — Mocks githubkit client methods, verifies request parameters and response transformation

**Alternatives considered**: Creating a new test framework or shared base class — rejected because the existing fixture-based approach is well-established and creating new abstractions violates Constitution Principle V (Simplicity & DRY).

---

### RT-002: Existing Frontend Test Infrastructure & Patterns

**Decision**: Reuse all existing test patterns from `src/test/` utilities and established test files.

**Rationale**: The frontend has a comprehensive testing setup:
- Environment: happy-dom (configured in `vitest.config.ts`)
- Setup file: `src/test/setup.ts` with `createMockApi()` factory
- Test factories: `src/test/factories/index.ts` for generating typed test data
- Test utilities: `src/test/test-utils.tsx` for `renderWithProviders()` helper
- Accessibility assertions: `src/test/a11y-helpers.ts` for `expectNoA11yViolations()`
- Coverage provider: `@vitest/coverage-v8`
- Pattern for hook tests: `renderHook()` + mock API + `waitFor()` (see `useAuth.test.tsx`)
- Pattern for component tests: `render()` + `userEvent` + accessibility assertions via `jest-axe`

Template files to follow:
- **Hook tests**: `src/hooks/useAuth.test.tsx` — renderHook, mock API responses, waitFor async assertions
- **Component tests**: `src/components/settings/SettingsSection.test.tsx` — render, user interaction, accessibility
- **Schema tests**: Pure input/output testing of Zod schemas — no mocking required

**Alternatives considered**: Switching to jest or enzyme — rejected because Vitest is already configured, fast, and well-integrated with Vite.

---

### RT-003: CI Configuration for Advanced Tests

**Decision**: Add a separate CI job for backend advanced tests; verify frontend fuzz test discovery; create a new workflow for mutation testing; add a flaky detection scheduled job.

**Rationale**:
- Backend advanced tests (property, fuzz, chaos, concurrency) exist in `tests/property/`, `tests/fuzz/`, `tests/chaos/`, `tests/concurrency/` and are already discovered by pytest because `testpaths = ["tests"]` includes subdirectories. However, they currently run with default settings — no Hypothesis CI profile, no per-test timeout, and no failure isolation from the main suite.
- To run them effectively in CI, advanced tests need:
  - Explicit Hypothesis CI profile activation (`HYPOTHESIS_PROFILE=ci`)
  - A 120-second per-test timeout (`--timeout=120`)
  - A separate job to isolate failure impact (advanced test failures should not block basic coverage initially)
- Frontend fuzz tests in `src/__tests__/fuzz/` are included by the Vitest glob `src/**/*.{test,spec}.{ts,tsx}` — they should already be discovered. Verification needed.
- Mutation testing (mutmut backend, Stryker frontend) needs a weekly CI workflow.
- Flaky detection requires running the backend suite 3× on schedule and diffing results.

**Alternatives considered**:
1. Running advanced tests inline with the main test job — rejected because chaos/concurrency tests can be slow and flaky; a separate job provides isolation.
2. Running mutation testing on every PR — rejected because mutation testing is slow (minutes to hours); weekly schedule is the standard approach.

---

### RT-004: Backend Time-Controlled Testing with freezegun

**Decision**: Use `freezegun` as a dev dependency for time-controlled backend tests.

**Rationale**:
- 15+ time-dependent behaviors exist in the backend: session expiry, token refresh buffer, rate-limit reset windows, adaptive polling intervals, backoff formulas, assignment grace periods, recovery cooldowns.
- None of these have time-controlled tests currently.
- `freezegun` is the standard Python library for freezing time in tests. It patches `datetime.datetime.now()`, `time.time()`, and related functions.
- The pytest-asyncio integration with freezegun is well-documented and works with async fixtures.
- `freezegun` is pure Python with no C extensions, aligning with the project's dev dependency style.

**Alternatives considered**:
1. `time-machine` — faster C-based implementation, but less common in the ecosystem; `freezegun` is sufficient for test-time usage.
2. Manual `unittest.mock.patch` on `datetime` — fragile and error-prone; `freezegun` handles all edge cases (subclasses, `time.time()`, etc.) automatically.

---

### RT-005: Production-Parity Testing Approach

**Decision**: Create a dedicated integration test fixture that sets production-like configuration (encryption, CSRF, webhook secrets) and exercises production-only code paths.

**Rationale**:
- The entire test suite currently runs with `TESTING=1` and `DEBUG=True`, meaning production-only code paths (encryption enforcement, CSRF protection, rate limiting, admin validation, webhook secret verification) are never exercised.
- A production-mode fixture needs:
  - `TESTING=0` (disables test shortcuts)
  - `DEBUG=false` (enables production security features)
  - `ENCRYPTION_KEY=<generated Fernet key>` (enables encryption)
  - `GITHUB_WEBHOOK_SECRET=<hex string>` (enables webhook verification)
- These tests should be in `tests/integration/test_production_mode.py` to avoid polluting unit test fixtures.
- Configuration matrix tests verify startup behavior for all critical env var combinations.

**Alternatives considered**: Running the full test suite in production mode — rejected because many unit tests rely on test-mode shortcuts. A targeted integration test suite is more focused and reliable.

---

### RT-006: Architecture Fitness Functions Implementation

**Decision**: Use Python's `ast` module for backend import analysis; use a simple TypeScript import parser for frontend import analysis.

**Rationale**:
- Backend: Python's `ast` module can parse import statements from source files without executing them. Rules to enforce:
  - `services/` never imports from `api/`
  - `api/` never imports from `*_store` directly
  - `models/` never imports from `services/` or `api/`
- Frontend: TypeScript imports can be analyzed via regex or a lightweight parser. Rules:
  - Pages don't import other pages
  - Hooks don't import UI components
  - Utils don't import hooks
- Both need a known-violations allowlist that shrinks over time.

**Alternatives considered**:
1. Using `import-linter` (Python package) — adds an external dependency; `ast` is stdlib and sufficient.
2. Using ESLint rules for frontend — `eslint-plugin-import` could enforce boundaries, but a dedicated test is more visible and self-documenting.
3. Using `dependency-cruiser` for frontend — powerful but heavy; a simple test aligns with Constitution Principle V (Simplicity & DRY).

---

### RT-007: Coverage Ratchet Strategy

**Decision**: Bump CI thresholds immediately after each phase merges. Set thresholds 2% below actual achieved coverage to absorb minor fluctuations.

**Rationale**:
- The ratchet pattern prevents coverage regression: once coverage reaches a new level, the threshold locks it in.
- Backend phases and thresholds:
  - Phase 2 (GitHub integration + polling + chores + API routes): 71% → 76%
  - Phase 5 (Mutation-hardened edge cases): 76% → 80%
- Frontend phases and thresholds:
  - Phase 3 (Schemas + hooks): ~50/45/42/51 → 53/48/45/54
  - Phase 4 (Components): 53/48/45/54 → 60/55/52/60
- Thresholds are bumped in `pyproject.toml` (`fail_under`) and `vitest.config.ts` (`coverage.thresholds`).
- Each threshold bump is committed as part of the phase's PR.
- The 2% buffer prevents CI breakage from normal code churn.

**Alternatives considered**: Setting final thresholds at the start — rejected because this would break CI for all unrelated PRs until coverage catches up.

---

### RT-008: Hypothesis CI Profile Configuration

**Decision**: Use Hypothesis's CI profile (200 examples) for property-based tests in the CI advanced test job.

**Rationale**:
- The `tests/property/conftest.py` file configures Hypothesis profiles. The CI profile uses 200 examples (vs. default 100) for more thorough exploration without excessive runtime.
- Setting: `HYPOTHESIS_PROFILE=ci` environment variable in the CI job.
- The 120-second per-test timeout ensures no single property test can run indefinitely.
- This balance gives better bug-finding probability while staying within the 90-second CI budget constraint for backend.

**Alternatives considered**: Using the default profile — rejected because CI has more time budget than local development and should explore more examples.

---

### RT-009: Frontend Fuzz Test CI Discovery

**Decision**: Verify that Vitest's include glob discovers files in `src/__tests__/fuzz/`. No configuration change expected.

**Rationale**:
- The glob pattern `src/**/*.{test,spec}.{ts,tsx}` should match `src/__tests__/fuzz/jsonParse.test.tsx` and `src/__tests__/fuzz/zodFieldRename.test.ts`.
- No exclude patterns in `vitest.config.ts` target the `__tests__` directory.
- Verification: Run `npx vitest --reporter=verbose 2>&1 | grep fuzz` to confirm fuzz tests appear in the test output.

**Alternatives considered**: Moving fuzz tests to a different directory — rejected because the current location follows established conventions and should already be discovered.

---

### RT-010: Contract Validation Approach

**Decision**: Verify `createMockApi()` types align with `openapi.json` schemas using a CI-run validation script.

**Rationale**:
- `solune/scripts/validate-contracts.sh` already exists as a contract validation script.
- The `createMockApi()` factory in `src/test/setup.ts` must produce types that match the actual API surface defined in `openapi.json`.
- Contract drift occurs silently — automated CI validation catches it immediately.
- Running on every CI build ensures contracts never accumulate drift.

**Alternatives considered**: Manual contract review — rejected because drift is insidious and only detected when tests start failing for unrelated reasons.

---

### RT-011: Flaky Test Detection Approach

**Decision**: Run the backend test suite 3 times on a scheduled CI job, compare results, and flag tests with inconsistent outcomes. Report the 20 slowest tests.

**Rationale**:
- Flaky tests erode developer trust in CI and can mask real failures.
- Running 3× and diffing pass/fail results per test identifies intermittent failures.
- The 20 slowest tests report identifies optimization targets for staying within CI budget.
- This should run on a schedule (not per-PR) to avoid blocking development.

**Alternatives considered**:
1. Using `pytest-rerunfailures` — retries failures but doesn't detect non-determinism; useful for tolerance but not detection.
2. Enabling Vitest's `retry` option for frontend — same limitation; retries mask flakiness instead of surfacing it.

---

### RT-012: WebSocket Lifecycle Testing

**Decision**: Use Playwright's WebSocket interception for full lifecycle testing of the connect → receive → disconnect → polling fallback → reconnect flow.

**Rationale**:
- Playwright 1.58 supports WebSocket route interception and can simulate lifecycle events.
- The test flow: connect → receive data → kill WebSocket → verify polling fallback → reconnect → verify data freshness.
- This is an E2E-level test that requires the full application context.
- Reconnection debounce tests can verify that rapid disconnect/reconnect events only trigger one cache invalidation.

**Alternatives considered**:
1. `mock-socket` for unit-level testing — viable for debounce but insufficient for full lifecycle.
2. Custom WebSocket test server — adds complexity; Playwright's built-in support is sufficient.

## Summary of Decisions

| # | Topic | Decision | Key Reason |
|---|-------|----------|------------|
| RT-001 | Backend test patterns | Reuse existing fixtures | 50+ tests already use them |
| RT-002 | Frontend test patterns | Reuse existing patterns | happy-dom, renderHook, factories established |
| RT-003 | CI advanced tests | Separate job + mutation workflow + flaky detection | Isolation from main test suite |
| RT-004 | Time-controlled testing | freezegun library | Standard, well-integrated, pure-Python |
| RT-005 | Production-parity tests | Dedicated integration fixture | Avoids polluting unit test environment |
| RT-006 | Architecture fitness | ast (Python) + regex (TS) | Stdlib, no new dependencies |
| RT-007 | Coverage ratchet | Bump after each phase, 2% buffer | Prevents regression without blocking PRs |
| RT-008 | Hypothesis CI profile | 200 examples with 120s timeout | More thorough than default, bounded runtime |
| RT-009 | Frontend fuzz discovery | Verify existing glob | Should already work, just verify |
| RT-010 | Contract validation | CI-run validation script | Catches drift immediately |
| RT-011 | Flaky detection | 3× run + diff on schedule | Surfaces non-determinism without blocking |
| RT-012 | WebSocket lifecycle | Playwright WebSocket interception | Built-in support, full lifecycle coverage |
