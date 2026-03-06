# Data Model: Bug Bash — Full Codebase Review & Fix

**Feature Branch**: `025-bug-basher`

## Entities

This feature does not introduce, modify, or remove any application data entities, database tables, API models, or state structures. All existing Pydantic models, SQLite schemas, TypeScript interfaces, and React Query cache keys remain unchanged (FR-024: no public API surface changes).

The entities below are **process artifacts** — they define the structure of the bug bash output, not application data models.

### Bug Report Entry

Represents a single identified bug in the summary table output (FR-023).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `number` | integer | Sequential bug number (1-based) | Unique, auto-incrementing |
| `file` | string | Relative path from repository root | Must be a valid file path in the repo |
| `lines` | string | Line number(s) affected | Format: `N` (single) or `N-M` (range) |
| `category` | enum | Bug category | One of: Security, Runtime, Logic, Test, Quality |
| `description` | string | Brief description of the bug | Max ~100 characters, human-readable |
| `status` | enum | Resolution status | One of: `✅ Fixed`, `⚠️ Flagged (TODO)` |

**Example**:

| # | File | Line(s) | Category | Description | Status |
|---|------|---------|----------|-------------|--------|
| 1 | `backend/src/api/auth.py` | 42-45 | Security | Missing input validation on redirect URI | ✅ Fixed |
| 2 | `backend/src/services/cache.py` | 100 | Logic | Off-by-one in TTL calculation | ⚠️ Flagged (TODO) |

### Regression Test

Represents a test case added to validate a bug fix (FR-013). Not a data model — a testing pattern.

| Attribute | Description |
|-----------|-------------|
| **Location** | Same test file as existing tests for the module, or new test file if none exists |
| **Naming** | `test_<module>_<bug_description>` — descriptive of what was broken |
| **Structure** | Arrange → Act → Assert pattern (consistent with existing test style) |
| **Assertion** | Must verify the **fixed** behavior, not just absence of error |
| **Negative case** | Should also verify the previously-broken behavior would have been caught |

**Example pattern** (Python/pytest):
```python
async def test_auth_validates_redirect_uri_no_open_redirect():
    """Regression: redirect_uri was not validated, allowing open redirects."""
    # Arrange
    malicious_uri = "https://evil.example.com/steal-token"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await handle_callback(code="valid", state="valid", redirect_uri=malicious_uri)
    assert exc_info.value.status_code == 400
```

**Example pattern** (TypeScript/Vitest):
```typescript
it('should reject invalid URLs in API calls', () => {
  // Regression: unsanitized URLs could cause open redirect
  expect(() => api.redirect('https://evil.example.com')).toThrow();
});
```

### TODO(bug-bash) Flag

Represents an ambiguous issue left for human review (FR-022). Implemented as a code comment, not a data model.

| Attribute | Description |
|-----------|-------------|
| **Marker** | `# TODO(bug-bash):` (Python) or `// TODO(bug-bash):` (TypeScript) |
| **Category** | One of: Security, Runtime, Logic, Test, Quality |
| **Description** | What the issue is |
| **Options** | Available approaches (at least 2) |
| **Rationale** | Why this needs human judgment (not auto-fixable) |

**Example**:
```python
# TODO(bug-bash): Security — CORS allows wildcard origin in dev mode.
# Options: (A) Restrict to specific origins only, (B) Keep wildcard for dev but add env check.
# Needs human review because: changing CORS could break local development workflows.
```

## State Transitions

No new state machines are introduced by this feature. Existing state transitions in the workflow orchestrator and session management are audit targets (FR-011) but their schemas are not modified.

## Relationships

No new entity relationships are introduced. The Bug Report Entry, Regression Test, and TODO Flag are independent output artifacts — they reference source code locations but do not form a data graph.
