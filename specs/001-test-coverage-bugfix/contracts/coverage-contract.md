# Contracts: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20
**Purpose**: Define the contracts between testing tools, test files, and coverage reporting.

## Overview

This feature does not introduce new API endpoints or modify existing ones. The contracts below define the interface between the test infrastructure (tools and configuration) and the test files produced by this effort.

## Contract 1: Frontend Coverage Tool Interface

**Tool**: Vitest with `@vitest/coverage-v8`
**Invocation**: `npm run test:coverage` (equivalent to `vitest run --coverage`)

### Input Contract

- Test files must match the glob pattern: `src/**/*.{test,spec}.{ts,tsx}`
- Test environment: `happy-dom` (configured in `vitest.config.ts`)
- Setup file: `src/test/setup.ts` (executed before each test file)

### Output Contract

- Coverage report includes: lines, branches, statements, functions
- Report formats: text (terminal), and optionally lcov/json for CI integration
- Per-file breakdown shows uncovered line numbers
- Overall aggregate percentage is the primary metric for the 85% target

### Coverage Thresholds

| Metric | Minimum Target |
|--------|---------------|
| Statements | 85% (aggregate) |
| Branches | 85% (aggregate) |
| Lines | 85% (aggregate) |
| Functions | 85% (aggregate) |

## Contract 2: Backend Coverage Tool Interface

**Tool**: PyTest with `pytest-cov`
**Invocation**: `pytest --cov=src --cov-report=term-missing --cov-report=html`

### Input Contract

- Test files must match the pattern: `tests/**/test_*.py`
- Test discovery: `testpaths = ["tests"]` (configured in `pyproject.toml`)
- Async mode: `auto` (configured in `pyproject.toml`)
- Shared fixtures: `tests/conftest.py`

### Output Contract

- Coverage report includes: lines, branches (with `--cov-branch`), missing lines
- Report formats: term-missing (terminal with uncovered lines), html (browsable report)
- Per-file breakdown shows uncovered line ranges
- Overall aggregate percentage is the primary metric for the 85% target

### Coverage Thresholds

| Metric | Minimum Target |
|--------|---------------|
| Lines | 85% (aggregate) |
| Branches | 85% (aggregate) |

## Contract 3: Test File Naming Convention

### Frontend

| Pattern | Location | Example |
|---------|----------|---------|
| `{name}.test.ts` | Co-located with source | `hooks/useAuth.test.tsx` |
| `{name}.test.tsx` | Co-located with source | `components/board/ProjectBoard.test.tsx` |

### Backend

| Pattern | Location | Example |
|---------|----------|---------|
| `test_{name}.py` | `tests/unit/` | `tests/unit/test_github_auth.py` |
| `test_{name}.py` | `tests/integration/` | `tests/integration/test_custom_agent_assignment.py` |

## Contract 4: Test Structure (AAA Pattern)

Each test case must follow this structure:

### Frontend (Vitest)

```typescript
describe('ModuleName', () => {
  it('should [expected behavior] when [condition]', () => {
    // Arrange
    const input = setupTestData();

    // Act
    const result = functionUnderTest(input);

    // Assert
    expect(result).toEqual(expectedOutput);
  });
});
```

### Backend (PyTest)

```python
class TestModuleName:
    def test_expected_behavior_when_condition(self):
        # Arrange
        input_data = create_test_data()

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_output
```

## Contract 5: Commit Message Convention

| Type | Pattern | Example |
|------|---------|---------|
| Test addition | `test: [scope] description` | `test: add unit tests for useAuth hook` |
| Bug fix | `fix: [scope] description` | `fix: correct null check in github_auth service` |
| Test infrastructure | `chore: [scope] description` | `chore: update vitest coverage configuration` |
