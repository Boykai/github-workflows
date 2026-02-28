# Test Conventions Contract: 013-test-coverage-dry

**Date**: 2026-02-28

> This feature does not introduce new API endpoints or modify existing ones. Instead of REST/GraphQL contracts, this document defines the **testing conventions and contracts** that all test code must follow.

## Backend Test Conventions (pytest)

### File Naming
- Unit tests: `backend/tests/unit/test_<module_name>.py` mirroring `backend/src/<module_path>.py`
- Integration tests: `backend/tests/integration/test_<scenario>.py`
- Shared helpers: `backend/tests/helpers/<utility_type>.py`

### Test Structure (AAA Pattern)
```python
class TestFeatureBehavior:
    """Tests for <module> <feature> behavior."""

    async def test_descriptive_name_communicating_intent(self, client, mock_session):
        # Arrange
        mock_data = make_test_entity(field="value")
        mock_service.method.return_value = mock_data

        # Act
        response = await client.get("/api/v1/endpoint")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "value", "Expected field to match the mock data"
    ```

### Naming Convention
- Test class: `Test<Feature><Behavior>` (e.g., `TestAuthLogin`, `TestBoardColumnMove`)
- Test method: `test_<behavior_description>` (e.g., `test_returns_401_when_session_expired`)
- Test names must communicate intent without reading the test body

### Fixtures and Factories
- Use conftest.py fixtures for DI (database, client, service mocks)
- Use factory functions from `tests/helpers/factories.py` for test data
- Never duplicate factory logic across test files
- Factory signature: `make_<entity>(**overrides) -> Entity`

### Assertion Guidelines
- Always include assertion messages for non-obvious assertions
- Use `assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"`
- For complex objects, assert specific fields rather than entire objects
- Use custom assertion helpers from `tests/helpers/assertions.py` for repeated patterns

### Isolation Rules
- Each test must pass when run in isolation (`pytest tests/unit/test_file.py::TestClass::test_method`)
- No test may depend on execution order or state from another test
- Use in-memory SQLite (from conftest.py `mock_db`) for all database tests
- Mock all external services (GitHub API, AI providers, Signal)

---

## Frontend Test Conventions (Vitest + React Testing Library)

### File Naming
- Hook tests: `frontend/src/hooks/<hookName>.test.tsx` co-located with hook
- Component tests: `frontend/src/components/<category>/<ComponentName>.test.tsx` co-located with component
- Page tests: `frontend/src/pages/<PageName>.test.tsx` co-located with page
- Service tests: `frontend/src/services/<service>.test.ts` co-located with service

### Test Structure (AAA Pattern)
```typescript
describe('ComponentName', () => {
  it('describes expected behavior clearly', () => {
    // Arrange
    const mockData = createMockEntity({ field: 'value' });
    vi.mocked(apiModule.method).mockResolvedValue(mockData);

    // Act
    const { result } = renderHook(() => useHook(), { wrapper });

    // Assert
    expect(result.current.data).toEqual(mockData);
  });
});
```

### Naming Convention
- `describe` block: Component or hook name (e.g., `describe('useAuth', ...)`)
- `it` block: Behavior description starting with verb (e.g., `it('returns user data after successful login', ...)`)

### Mock Strategy
- Use `vi.mock()` for module mocking
- Use `createMockApi()` from `src/test/setup.ts` for API mocks
- Use factory functions from `src/test/factories/` for test data
- Never duplicate mock setup across test files

### Isolation Rules
- Each test must clean up after itself (QueryClient cache, mocks)
- Use `renderWithProviders()` from `src/test/test-utils.tsx` for component rendering
- Use `createTestQueryClient()` for each test to avoid cache leaks

---

## CI Contract

### Backend (must be re-enabled)
```yaml
- name: Run tests
  run: pytest --cov=src --cov-report=term-missing
```

### Frontend (already active)
```yaml
- name: Run tests
  run: npm test
```

### Stability Requirements
- Zero flaky failures across 5+ consecutive CI runs
- No tests may be skipped without documented rationale
- All tests must complete within the CI job timeout
