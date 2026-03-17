# CI Contract: Advanced Tests Job

**Feature**: `049-increase-test-coverage` | **Date**: 2026-03-17

## Purpose

Define the contract for the CI job that runs backend advanced tests (property-based, fuzz, chaos, concurrency) on every pull request, verifies frontend fuzz test discovery, and detects flaky tests on a schedule.

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
| **Failure behavior** | Non-blocking initially (allow-failure); becomes blocking once baselines stabilize |
| **Dependencies** | None (runs in parallel with other CI jobs) |

### Expected Failure Handling

Tests marked with `@pytest.mark.xfail` are expected failures:
- They are **reported** in test output with `[XFAIL]` markers
- They do **not** block the CI build
- If an xfail test starts passing (`XPASS`), it is reported as an unexpected pass

## Frontend Fuzz Test Verification

### Verification Contract

The frontend test suite (`npm run test:coverage`) MUST discover and execute fuzz tests located in `src/__tests__/fuzz/`:
- `src/__tests__/fuzz/jsonParse.test.tsx`
- `src/__tests__/fuzz/zodFieldRename.test.ts`

**Verification method**: The Vitest include glob `src/**/*.{test,spec}.{ts,tsx}` covers `src/__tests__/fuzz/*.test.{ts,tsx}`. No configuration change needed unless tests are being excluded.

## Flaky Test Detection Job

### Job Definition

```yaml
# Added to .github/workflows/ci.yml (schedule trigger)
flaky-detection:
  name: Flaky Test Detection
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
    - name: Run test suite 3 times
      run: |
        for i in 1 2 3; do
          pytest tests/ --tb=line -q --junitxml=run-$i.xml || true
        done
    - name: Compare results and flag flaky tests
      run: python scripts/detect_flaky.py run-1.xml run-2.xml run-3.xml
    - name: Report 20 slowest tests
      run: pytest tests/ --durations=20 -q --no-header 2>&1 | head -25
```

### Behavior Contract

| Aspect | Specification |
|--------|--------------|
| **Trigger** | `schedule` (weekly) + `workflow_dispatch` |
| **Runs** | 3 complete test suite executions |
| **Detection** | Any test with different results across runs is flagged as flaky |
| **Output** | Flaky test report + 20 slowest tests report |
| **Blocking** | Never blocks PRs — informational only |

## Acceptance Criteria

1. ✅ Backend advanced tests run as a separate CI job on every PR
2. ✅ Per-test timeout of 120 seconds is enforced
3. ✅ Hypothesis CI profile (200 examples) is used for property tests
4. ✅ Known xfail tests do not block the build
5. ✅ Frontend fuzz tests are discovered and executed in the standard test run
6. ✅ Flaky test detection runs on schedule with 3× execution
7. ✅ The 20 slowest tests are reported
8. ✅ Advanced tests are non-blocking initially, transitioning to blocking after baselines stabilize
