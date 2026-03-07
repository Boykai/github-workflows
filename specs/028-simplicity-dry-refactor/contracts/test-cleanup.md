# Contract: Test Cleanup

**Feature**: `028-simplicity-dry-refactor` | **Phase**: 5

---

## Mock Consolidation

### Current State

| Location | Contents | Issue |
|----------|----------|-------|
| `tests/conftest.py` | 11 shared fixtures (mock_session, mock_db, mock_github_service, client, etc.) | **Canonical** — keep and expand |
| `tests/helpers/mocks.py` | Additional mock factories | **Duplicate** — merge into conftest |
| `tests/helpers/factories.py` | Data factories | **Keep** — factories are complementary |
| `tests/helpers/assertions.py` | Custom assertions | **Keep** — assertions are complementary |
| Individual test files | Inline `@patch` decorators and local mock definitions | **Replace** with conftest fixtures |

### Migration Plan

1. **Audit** `tests/helpers/mocks.py` — identify which factories are unique vs. duplicates of conftest fixtures.
2. **Move** unique factories to `conftest.py` as new fixtures.
3. **Remove** duplicate factories.
4. **Delete** `tests/helpers/mocks.py`.
5. **Update** any test files that import from `tests.helpers.mocks`.

### Inline Patch Replacement

**Target**: `tests/unit/test_api_e2e.py` (and similar files with heavy inline patching)

| Current Pattern | After |
|----------------|-------|
| `@patch("src.services.github_projects.service.GitHubProjectsService")` | Use `mock_github_service` fixture from conftest |
| `@patch("src.api.chat.get_session_dep")` | Use `mock_session` fixture from conftest |
| Local `MagicMock()` / `AsyncMock()` definitions | Use conftest fixtures with appropriate scope |

### Validation

| Check | Method |
|-------|--------|
| `tests/helpers/mocks.py` removed | File does not exist |
| No broken imports | `pytest --collect-only` succeeds |
| All tests pass | `pytest` green |
| ~80 lines saved | Diff shows net line reduction in test files |
