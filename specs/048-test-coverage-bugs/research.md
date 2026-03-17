# Research: Increase Test Coverage & Surface Unknown Bugs

**Feature**: `048-test-coverage-bugs` | **Date**: 2026-03-16

## Research Tasks & Findings

### R1: Existing Backend Test Infrastructure & Patterns

**Decision**: Reuse all existing test patterns and shared fixtures from `tests/conftest.py`.

**Rationale**: The backend already has a mature test infrastructure with:
- `mock_db`: In-memory SQLite with migrations applied — used by all service tests
- `mock_session`, `mock_access_token`: Standard auth stubs
- `mock_github_service`, `mock_github_auth_service`, `mock_ai_agent_service`: AsyncMock specs for all major services
- `client`: httpx.AsyncClient wired to FastAPI with dependency overrides
- Autouse cache-clearing fixture for test isolation
- Helper factories: `make_mock_github_service(**overrides)`, `make_mock_github_auth_service(**overrides)`, etc.

Template files to follow:
- **API route tests**: `tests/unit/test_api_chat.py` — Uses `client` fixture, class-based test groups per endpoint, verifies status codes and response shapes
- **Service tests**: `tests/unit/test_pipeline_state_store.py` — Uses `mock_db` with DDL setup, helper factories for test data, covers CRUD + fallback behavior
- **GitHub mock tests**: `tests/unit/test_github_projects.py` (renamed from test_github_projects_service.py) — Mocks githubkit client methods, verifies request parameters and response transformation

**Alternatives considered**: Creating a new test framework or shared base class — rejected because the existing fixture-based approach is already well-established and used by 50+ test files.

---

### R2: Existing Frontend Test Infrastructure & Patterns

**Decision**: Reuse all existing test patterns from `src/test/` utilities and established test files.

**Rationale**: The frontend has a comprehensive testing setup:
- Environment: happy-dom (configured in `vitest.config.ts`)
- Setup file: `src/test/setup.ts`
- Test factories: `src/test/factories/` for generating test data
- Test utilities: `src/test/utils/` for shared helpers
- Coverage provider: `@vitest/coverage-v8`
- Pattern for hook tests: `renderHook` + mock API + `waitFor` (see `useAuth.test.tsx`)
- Pattern for component tests: `render` + `userEvent` + accessibility assertions via `jest-axe`

Template files to follow:
- **Hook tests**: `src/hooks/useAuth.test.tsx` — renderHook, mock API responses, waitFor async assertions
- **Component tests**: `src/components/ui/button.test.tsx` — render, user interaction, accessibility
- **Property tests**: `src/lib/utils.property.test.ts` — Vitest property-based testing
- **Fuzz tests**: `src/__tests__/fuzz/zodFieldRename.test.ts` — Schema fuzzing

**Alternatives considered**: Switching to jest or enzyme — rejected because Vitest is already configured, fast, and well-integrated with Vite.

---

### R3: CI Configuration for Advanced Tests

**Decision**: Add a separate CI job for backend advanced tests; verify frontend fuzz test discovery; create a new workflow for mutation testing.

**Rationale**:
- Backend advanced tests (property, fuzz, chaos, concurrency) exist in `tests/property/`, `tests/fuzz/`, `tests/chaos/`, `tests/concurrency/` and are already discovered by CI because `testpaths = ["tests"]` includes subdirectories. However, they run with default settings — no Hypothesis CI profile, no per-test timeout, and no failure isolation from the main suite.
- To run them effectively in CI, advanced tests need:
  - Explicit Hypothesis CI profile activation (`--hypothesis-seed=0` or `HYPOTHESIS_PROFILE=ci`)
  - A 120-second per-test timeout (`--timeout=120`)
  - A separate job to isolate failure impact (advanced test failures should not block basic coverage)
- Frontend fuzz tests in `src/__tests__/fuzz/` are included by the Vitest glob `src/**/*.{test,spec}.{ts,tsx}` — they should already be discovered. Verification needed.
- Mutation testing (mutmut backend, Stryker frontend) is configured locally but has no CI workflow.

**Alternatives considered**:
1. Running advanced tests inline with the main test job — rejected because chaos/concurrency tests can be slow and flaky; a separate job provides isolation.
2. Running mutation testing on every PR — rejected because mutation testing is slow (minutes to hours); weekly schedule is more appropriate.

---

### R4: Backend Time-Controlled Testing with freezegun

**Decision**: Add `freezegun` as a dev dependency for time-controlled backend tests.

**Rationale**:
- 15+ time-dependent behaviors exist in the backend: session expiry, token refresh buffer, rate-limit reset windows, adaptive polling intervals, backoff formulas, assignment grace periods, recovery cooldowns.
- None of these have time-controlled tests currently.
- `freezegun` is the standard Python library for freezing time in tests. It patches `datetime.datetime.now()`, `time.time()`, and related functions.
- Alternative: `time-machine` (faster C-based implementation) — both are viable, but `freezegun` is more widely known and the project already uses pure-Python test dependencies.
- The pytest-asyncio integration with freezegun is well-documented and works with async fixtures.

**Alternatives considered**:
1. `time-machine` — faster but less common in the ecosystem; `freezegun` is sufficient for test-time usage.
2. Manual `unittest.mock.patch` on `datetime` — fragile and error-prone; `freezegun` handles all edge cases automatically.

---

### R5: Production-Parity Testing Approach

**Decision**: Create a dedicated integration test fixture that sets `TESTING=0`, `DEBUG=false`, and provides synthetic production secrets.

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

### R6: Architecture Fitness Functions Implementation

**Decision**: Use Python's `ast` module for backend import analysis; use a simple regex/AST parser for frontend TypeScript import analysis.

**Rationale**:
- Backend: Python's `ast` module can parse import statements from source files without executing them. Rules to enforce:
  - `services/` never imports from `api/`
  - `api/` never imports from `*_store` directly
  - `models/` never imports from `services/` or `api/`
- Frontend: TypeScript imports can be analyzed via regex (`import ... from '...'`) or a lightweight AST parser. Rules:
  - Pages don't import other pages
  - Hooks don't import UI components
  - Utils don't import hooks
- Both need a known-violations allowlist that shrinks over time.

**Alternatives considered**:
1. Using `import-linter` (Python package) — adds an external dependency; `ast` is stdlib and sufficient.
2. Using ESLint rules for frontend — `eslint-plugin-import` could enforce boundaries, but a dedicated test is more visible and self-documenting.
3. Using `dependency-cruiser` for frontend — a powerful tool but heavy; a simple test is more aligned with the simplicity principle.

---

### R7: Coverage Ratchet Strategy

**Decision**: Bump CI thresholds immediately after each phase merges, never aspirationally.

**Rationale**:
- The ratchet pattern prevents coverage regression: once coverage reaches a new level, the threshold locks it in.
- Phases and their thresholds:
  - Phase 1 (Backend GitHub Integration): 69% → 74%
  - Phase 2 (Backend Polling/Services/Routes): 74% → 78%
  - Phase 3 (Backend Edge Cases): 78% → 80%
  - Phase 4 (Frontend Services/Hooks): 46/41/38/47 → 53/48/45/54
  - Phase 5 (Frontend Settings/Pipeline/Board): 53/48/45/54 → 58/53/50/59
  - Phase 6 (Frontend Remaining): 58/53/50/59 → 60/55/52/60
- Thresholds are bumped in `pyproject.toml` (`[tool.coverage.run] fail_under`) and `vitest.config.ts` (`coverage.thresholds`).
- Each threshold bump is committed as part of the phase's PR.

**Alternatives considered**: Setting final thresholds at the start and hoping tests fill in — rejected because this would break CI for all unrelated PRs until coverage catches up.

---

### R8: Hypothesis CI Profile Configuration

**Decision**: Use Hypothesis's CI profile (200 examples) for property-based tests in the CI advanced test job.

**Rationale**:
- The `tests/property/conftest.py` file configures Hypothesis profiles. The CI profile uses 200 examples (vs. default 100) for more thorough exploration without excessive runtime.
- Setting: `HYPOTHESIS_PROFILE=ci` environment variable or `--hypothesis-profile=ci` pytest flag.
- The 120-second per-test timeout ensures no single property test can run indefinitely.

**Alternatives considered**: Using the default profile — rejected because CI has more time budget than local development and should explore more examples.

---

### R9: Frontend Fuzz Test CI Discovery Verification

**Decision**: Verify that Vitest's include glob (`src/**/*.{test,spec}.{ts,tsx}`) discovers files in `src/__tests__/fuzz/`.

**Rationale**:
- The glob pattern `src/**/*.{test,spec}.{ts,tsx}` should match `src/__tests__/fuzz/jsonParse.test.tsx` and `src/__tests__/fuzz/zodFieldRename.test.ts`.
- No exclude patterns in `vitest.config.ts` target the `__tests__` directory.
- Verification: Run `npx vitest --reporter=verbose 2>&1 | grep fuzz` to confirm fuzz tests appear in the test output.
- If excluded, the fix is to ensure the glob pattern is correct or add the fuzz directory explicitly.

**Alternatives considered**: Moving fuzz tests into `src/test/fuzz/` — rejected because the current location follows the `__tests__` convention and should already be discovered.

---

### R10: WebSocket E2E Testing Approach

**Decision**: Use Playwright's WebSocket interception capabilities for lifecycle testing.

**Rationale**:
- Playwright 1.58 supports WebSocket interception and can simulate connection lifecycle events.
- The test flow: connect → receive data → kill WebSocket → verify polling fallback → reconnect → verify data freshness.
- The reconnection debounce test: send 5 rapid reconnect events, verify only one cache invalidation fires.
- These tests should be in the E2E test suite (`playwright test`) rather than unit tests, as they need the full application context.

**Alternatives considered**:
1. Using `mock-socket` for unit-level WebSocket testing — viable for the debounce test but insufficient for full lifecycle testing.
2. Using `ws` (Node WebSocket library) for a test server — adds complexity; Playwright's built-in support is sufficient.

---

### R11: New Dependency: freezegun

**Decision**: Add `freezegun` to backend dev dependencies in `pyproject.toml`.

**Rationale**:
- `freezegun` is the most widely used Python library for time-controlled testing (8M+ monthly downloads).
- It integrates seamlessly with pytest and pytest-asyncio.
- It patches `datetime.datetime.now()`, `datetime.date.today()`, `time.time()`, `time.localtime()`, `time.gmtime()`, `time.strftime()`.
- The `@freeze_time` decorator and `with freeze_time()` context manager provide clean test syntax.
- No other new dependencies are needed for this feature.

**Alternatives considered**: `time-machine` (C extension, faster) — both are good; `freezegun` chosen for wider ecosystem familiarity and pure-Python implementation.

## Summary of Decisions

| # | Topic | Decision | Key Reason |
|---|-------|----------|------------|
| R1 | Backend test patterns | Reuse existing fixtures | 50+ tests already use them |
| R2 | Frontend test patterns | Reuse existing patterns | happy-dom, renderHook, factories established |
| R3 | CI advanced tests | Separate job + mutation workflow | Isolation from main test suite |
| R4 | Time-controlled testing | freezegun library | Standard, well-integrated, pure-Python |
| R5 | Production-parity tests | Dedicated integration fixture | Avoids polluting unit test environment |
| R6 | Architecture fitness | ast (Python) + regex (TS) | Stdlib, no new dependencies |
| R7 | Coverage ratchet | Bump after each phase merges | Prevents regression without blocking PRs |
| R8 | Hypothesis CI profile | 200 examples with 120s timeout | More thorough than default, bounded runtime |
| R9 | Frontend fuzz discovery | Verify existing glob catches them | Should already work, just verify |
| R10 | WebSocket E2E | Playwright WebSocket interception | Built-in support, full lifecycle coverage |
| R11 | New dependency | freezegun (dev only) | Time-freezing for temporal behavior tests |
