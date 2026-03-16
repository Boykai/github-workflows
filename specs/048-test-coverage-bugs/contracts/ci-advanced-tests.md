# CI Contract: Advanced Tests Job

**Feature**: `048-test-coverage-bugs` | **Date**: 2026-03-16

## Purpose

Define the contract for the new CI job that runs backend advanced tests (property-based, fuzz, chaos, concurrency) on every pull request, and verifies frontend fuzz test discovery.

## Backend Advanced Tests Job

### Job Definition

```yaml
# Added to .github/workflows/ci.yml
backend-advanced-tests:
  name: Backend Advanced Tests
  runs-on: ubuntu-latest
  defaults:
    run:
      working-directory: solune/backend
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: "3.12"
    - run: pip install -e ".[dev]"
    - name: Run property-based tests
      run: pytest tests/property/ --timeout=120 -v
      env:
        HYPOTHESIS_PROFILE: ci
    - name: Run fuzz tests
      run: pytest tests/fuzz/ --timeout=120 -v
    - name: Run chaos tests
      run: pytest tests/chaos/ --timeout=120 -v
    - name: Run concurrency tests
      run: pytest tests/concurrency/ --timeout=120 -v
```

### Behavior Contract

| Aspect | Specification |
|--------|--------------|
| **Trigger** | `pull_request` (same as main backend job) |
| **Timeout per test** | 120 seconds (`--timeout=120`) |
| **Hypothesis profile** | `ci` (200 examples) |
| **Known xfail tests** | Reported but do not block the build |
| **Failure behavior** | Job fails if any non-xfail test fails; does not block other jobs |
| **Dependencies** | None (runs in parallel with other CI jobs) |

### Expected Failure Handling

Tests marked with `@pytest.mark.xfail` (e.g., known race conditions in `test_interleaving.py` and `test_polling_races.py`) are expected failures:
- They are **reported** in test output with `[XFAIL]` markers
- They do **not** block the CI build
- If an xfail test starts passing (`XPASS`), it is reported as an unexpected pass (which may optionally be treated as a failure to prompt removing the xfail marker)

## Frontend Fuzz Test Verification

### Verification Contract

The frontend test suite (`npm run test:coverage`) MUST discover and execute fuzz tests located in `src/__tests__/fuzz/`:
- `src/__tests__/fuzz/jsonParse.test.tsx`
- `src/__tests__/fuzz/zodFieldRename.test.ts`

**Verification method**: The Vitest include glob `src/**/*.{test,spec}.{ts,tsx}` covers `src/__tests__/fuzz/*.test.{ts,tsx}`. No configuration change needed unless tests are being excluded.

## Acceptance Criteria

1. ✅ Backend advanced tests run as a separate CI job on every PR
2. ✅ Per-test timeout of 120 seconds is enforced
3. ✅ Hypothesis CI profile (200 examples) is used for property tests
4. ✅ Known xfail tests do not block the build
5. ✅ Frontend fuzz tests are discovered and executed in the standard test run
