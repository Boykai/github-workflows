# Review Contract: Test Quality Audit (P4)

**Category**: Test Gaps & Test Quality
**Priority**: P4
**Scope**: All files in `backend/tests/` and `frontend/src/**/*.test.*`

## Checklist

### Untested Code Paths
- [ ] Critical business logic has corresponding test coverage
- [ ] Error handling paths are tested (not just happy paths)
- [ ] Edge cases identified in spec are covered by tests
- [ ] Authentication/authorization logic is tested for both allow and deny cases

### Tests That Pass for Wrong Reasons
- [ ] Mock objects return realistic data (not MagicMock auto-returns leaking)
- [ ] Assertions actually test the right thing (not asserting on mock defaults)
- [ ] Tests fail when the feature they validate is intentionally broken
- [ ] No tests that always pass regardless of implementation

### Mock Quality
- [ ] Mock patches target the correct import path (where used, not where defined)
- [ ] Mock return values match real API contracts
- [ ] No MagicMock objects leaking into production paths (e.g., database file paths)
- [ ] Mock side effects are realistic (proper exceptions, realistic delays)

### Assertion Quality
- [ ] Assertions are specific (not just `assertTrue(result)`)
- [ ] Expected values are explicit (not derived from the code under test)
- [ ] Error messages are descriptive for failure diagnosis
- [ ] Negative assertions exist (verify things that shouldn't happen)

### Edge Case Coverage
- [ ] Empty input handling is tested
- [ ] Boundary values are tested
- [ ] Concurrent operation scenarios are tested where relevant
- [ ] Error recovery paths are tested

## Acceptance Criteria
- Corrected tests fail when the feature they validate is broken
- No mock objects leaking into production code paths
- Each corrected test has a clear assertion that validates specific behavior
- All test fixes validated by `pytest` and `vitest`
