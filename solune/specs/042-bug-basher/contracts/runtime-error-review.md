# Runtime Error Review Contract

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Version**: 1.0
**Priority**: P2 — Reviewed after security vulnerabilities

## Purpose

Defines the process for identifying and fixing runtime errors across the Solune codebase. This contract governs User Story 2 (Runtime Error Elimination) and covers: unhandled exceptions, race conditions, null/None references, missing imports, type errors, file handle leaks, and database connection leaks.

## Input: File Scope

Runtime-critical files to review in order:

1. **Database layer**: `solune/backend/src/services/database.py`, `solune/backend/src/services/chat_store.py` — connection lifecycle, transaction handling
2. **Service layer**: All files in `solune/backend/src/services/` — error handling, resource management
3. **API routes**: All files in `solune/backend/src/api/` — exception handling in route handlers
4. **WebSocket**: `solune/backend/src/services/websocket.py` — connection lifecycle, message handling
5. **Middleware**: All files in `solune/backend/src/middleware/` — error propagation
6. **React hooks**: All files in `solune/frontend/src/hooks/` — cleanup functions, race conditions
7. **Entry points**: `solune/backend/src/main.py`, `solune/frontend/src/main.tsx` — startup errors

## Check Categories

### RT1: Unhandled Exceptions

**Pattern**: Code paths that can raise exceptions without try/except handling, especially in async functions.

**Detection**: Review async route handlers and service methods for operations that can fail (database queries, file I/O, HTTP calls, JSON parsing) without error handling.

**Fix pattern**: Add try/except with appropriate error response (HTTP status code for API routes, logging + graceful degradation for services).

**Regression test**: Trigger the error condition (e.g., mock a database failure) and assert graceful handling.

### RT2: Resource Leaks

**Pattern**: File handles, database connections, or other system resources opened without guaranteed cleanup.

**Detection**:
- Search for `open()` not in a `with` statement
- Search for database connections acquired without context manager
- Search for WebSocket connections without close handlers
- Review `useEffect` hooks for missing cleanup return functions

**Fix pattern**: Use context managers (`with`, `async with`), `try/finally`, or cleanup return functions in `useEffect`.

**Regression test**: Simulate the error path and assert the resource is released (e.g., connection count returns to zero).

### RT3: Null/None References

**Pattern**: Accessing attributes or methods on potentially null/None values without guards.

**Detection**:
- Dictionary `[]` access on optional keys (should use `.get()` with default)
- Attribute access on function returns that can be `None`
- Optional fields in Pydantic models accessed without null checks
- TypeScript optional chaining (`?.`) missing where needed

**Fix pattern**: Add null guards, use `.get()` with defaults, add optional chaining.

**Regression test**: Pass null/None input and assert no exception is raised.

### RT4: Missing Imports

**Pattern**: Imports that would fail at runtime due to missing modules, circular dependencies, or conditional import errors.

**Detection**: Review import sections for:
- Imports from modules that don't exist in the project
- Circular import patterns (A imports B imports A)
- Conditional imports with incorrect conditions

**Fix pattern**: Correct the import path or restructure to break circular dependency.

**Regression test**: Import the module and assert it loads without error.

### RT5: Type Errors

**Pattern**: Runtime type mismatches, especially between Pydantic models and database schemas.

**Detection**:
- Enum values that differ between code and database (e.g., `accepted` vs `confirmed`)
- Datetime parsing with `fromisoformat()` on strings with `Z` suffix
- Integer/string confusion in comparisons
- Type narrowing issues in TypeScript

**Fix pattern**: Add explicit type conversion, normalize values at boundaries.

**Regression test**: Pass the edge-case value and assert correct handling.

## Output

For each finding, produce:
- A BugReportEntry with `category: runtime`
- A code fix (if obvious) or TodoComment (if ambiguous)
- A regression test (if fixed)
- A commit with `fix(runtime): <description>` message format

## Completion Criteria

- All service and API files reviewed for error handling
- No unguarded resource acquisition without cleanup
- No null/None dereferences on optional values
- All imports resolve correctly
- All known type mismatches (enum mappings, datetime parsing) are handled
