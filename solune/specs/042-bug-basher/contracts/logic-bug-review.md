# Logic Bug Review Contract

**Feature**: 042-bug-basher
**Date**: 2026-03-15
**Version**: 1.0
**Priority**: P3 — Reviewed after runtime errors

## Purpose

Defines the process for identifying and fixing logic bugs across the Solune codebase. This contract governs User Story 3 (Logic Bug Correction) and covers: incorrect state transitions, wrong API calls, off-by-one errors, data inconsistencies, broken control flow, and incorrect return values.

## Input: File Scope

Logic-critical files to review in order:

1. **Models/Enums**: All files in `solune/backend/src/models/` — state definitions, enum values, validation logic
2. **Service logic**: All files in `solune/backend/src/services/` — business logic, state transitions, data transformations
3. **API responses**: All files in `solune/backend/src/api/` — response construction, status codes, error mapping
4. **Frontend services**: All files in `solune/frontend/src/services/` — API client logic, request/response mapping
5. **Utilities**: `solune/backend/src/utils.py`, all files in `solune/frontend/src/utils/` — helper function correctness
6. **Frontend hooks**: State management logic in `solune/frontend/src/hooks/` — state update correctness
7. **Frontend components**: Complex components with conditional rendering or state logic

## Check Categories

### LB1: State Transition Errors

**Pattern**: State machines or workflows that transition to incorrect states, skip required states, or allow invalid transitions.

**Detection**:
- Enum-based status fields with state transition logic
- Status updates in service methods that don't validate the current state
- Frontend state reducers with incorrect state transitions
- Database constraints vs application-level validation inconsistencies

**Fix pattern**: Add state validation before transition; ensure the transition is valid for the current state.

**Regression test**: Attempt an invalid state transition and assert it's rejected or handled correctly.

### LB2: Off-by-One Errors

**Pattern**: Incorrect boundary conditions in loops, array indices, pagination, or range checks.

**Detection**:
- Pagination logic (page number, offset calculation, total count)
- Array slicing with `[start:end]` boundaries
- Loop termination conditions
- Comparison operators (`<` vs `<=`, `>` vs `>=`)

**Fix pattern**: Correct the boundary condition; test at boundary, one before, and one after.

**Regression test**: Test with boundary inputs (0, 1, max, max+1) and assert correct behavior.

### LB3: Incorrect Return Values

**Pattern**: Functions that return wrong values for specific inputs or edge cases.

**Detection**:
- Functions with multiple return paths — verify each path returns the correct type and value
- Default return values that may not match caller expectations
- Boolean functions with inverted logic
- Computed values with arithmetic errors

**Fix pattern**: Correct the return value logic.

**Regression test**: Test with the specific input that triggers the wrong return and assert the correct value.

### LB4: Control Flow Errors

**Pattern**: Unreachable code, mis-ordered conditions, missing early returns, or incorrect boolean logic.

**Detection**:
- `if/elif/else` chains where a broader condition shadows a more specific one
- Early returns that prevent necessary cleanup or logging
- Boolean expressions with wrong operators (`and` vs `or`, `&&` vs `||`)
- Switch/match statements with missing cases

**Fix pattern**: Reorder conditions, fix boolean logic, add missing cases.

**Regression test**: Exercise the corrected branch and assert expected behavior.

### LB5: Data Flow Inconsistencies

**Pattern**: Values transformed incorrectly between layers (API → service → database) or data lost in translation.

**Detection**:
- Pydantic model serialization/deserialization losing fields
- Database query results missing joins or filters
- Frontend API responses not mapping to TypeScript types correctly
- Incorrect field name mapping between layers

**Fix pattern**: Fix the transformation at the boundary where data is lost or incorrectly mapped.

**Regression test**: Pass data through the full path and assert the output matches the input.

## Output

For each finding, produce:
- A BugReportEntry with `category: logic`
- A code fix (if obvious) or TodoComment (if ambiguous)
- A regression test (if fixed)
- A commit with `fix(logic): <description>` message format

## Completion Criteria

- All model and service files reviewed for state transition correctness
- Pagination logic verified for boundary correctness
- All multi-return functions verified for correctness on all paths
- No unreachable code or shadowed conditions in control flow
- Data transformations between layers verified for consistency
