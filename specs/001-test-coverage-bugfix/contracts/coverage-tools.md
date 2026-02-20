# Contracts: Coverage Tool Interfaces

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20

## Overview

This feature does not introduce new API endpoints or modify existing ones. The "contracts" for this feature describe the CLI interfaces used to run tests and generate coverage reports, plus the expected output formats.

---

## Frontend Coverage Contract

### Input: CLI Command

```bash
cd frontend && npx vitest run --coverage
```

### Expected Output

- Console summary with per-file coverage (lines, branches, functions, statements)
- Coverage report in `frontend/coverage/` directory
- Exit code 0 if all tests pass

### Coverage Report Format (Vitest/v8)

```text
 % Coverage report from v8
-----------------------------|---------|----------|---------|---------|-------------------
File                         | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
-----------------------------|---------|----------|---------|---------|-------------------
All files                    |   XX.XX |    XX.XX |   XX.XX |   XX.XX |
 src/hooks/useAuth.ts        |   XX.XX |    XX.XX |   XX.XX |   XX.XX | ...
 ...                         |   ...   |    ...   |   ...   |   ...   | ...
-----------------------------|---------|----------|---------|---------|-------------------
```

---

## Backend Coverage Contract

### Input: CLI Command

```bash
cd backend && python -m pytest --cov=src --cov-report=term-missing tests/
```

### Expected Output

- Console summary with per-file coverage (statements, missing, coverage percentage)
- Missing line numbers for each file
- Exit code 0 if all tests pass

### Coverage Report Format (pytest-cov)

```text
---------- coverage: ... ----------
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/api/auth.py                            XX     XX    XX%   ...
src/services/cache.py                      XX     XX    XX%   ...
...
---------------------------------------------------------------------
TOTAL                                     XXX    XXX    XX%
```

---

## Test File Naming Contracts

### Frontend

| Convention | Pattern | Example |
|------------|---------|---------|
| Unit tests | `{module}.test.{ts,tsx}` co-located with source | `src/hooks/useAuth.test.tsx` |
| E2E tests | `e2e/{name}.spec.ts` | `e2e/ui.spec.ts` |

### Backend

| Convention | Pattern | Example |
|------------|---------|---------|
| Unit tests | `tests/unit/test_{module}.py` | `tests/unit/test_cache.py` |
| Integration | `tests/integration/test_{feature}.py` | `tests/integration/test_custom_agent_assignment.py` |
| E2E tests | `tests/test_{scope}_e2e.py` | `tests/test_api_e2e.py` |

---

## Test Structure Contract (AAA Pattern)

### Frontend Example

```typescript
describe('ModuleName', () => {
  it('should do expected behavior when condition', async () => {
    // Arrange
    const mockData = { /* setup */ };
    vi.mocked(dependency).mockResolvedValue(mockData);

    // Act
    const { result } = renderHook(() => useHook(), { wrapper });

    // Assert
    expect(result.current.value).toBe(expected);
  });
});
```

### Backend Example

```python
class TestModuleName:
    @patch("src.services.module.dependency")
    async def test_expected_behavior_when_condition(self, mock_dep):
        # Arrange
        mock_dep.return_value = mock_data

        # Act
        result = await function_under_test(input)

        # Assert
        assert result == expected
```
