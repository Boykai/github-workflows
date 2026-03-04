# Review Contract: Logic Bug Audit (P3)

**Category**: Logic Bugs
**Priority**: P3
**Scope**: All files in `backend/src/` and `frontend/src/`

## Checklist

### State Transitions
- [ ] Workflow state machine transitions are valid (no illegal state jumps)
- [ ] Board column ordering is maintained correctly
- [ ] Task status changes follow defined lifecycle
- [ ] Session state is consistent across operations

### API Call Correctness
- [ ] HTTP methods match intent (GET for reads, POST for creates, etc.)
- [ ] API URL construction is correct (no missing path segments)
- [ ] Request/response serialization matches expected schema
- [ ] Pagination handles edge cases (empty results, last page, zero offset)

### Boundary Conditions
- [ ] Off-by-one errors in loops, slicing, and indexing
- [ ] Empty collection handling (empty lists, dicts, strings)
- [ ] Boundary values for numeric parameters (zero, negative, max)
- [ ] String operations handle empty strings and special characters

### Data Consistency
- [ ] Database writes and reads use consistent key formats
- [ ] Cache invalidation covers all mutation paths
- [ ] Settings persist correctly across sessions
- [ ] User-specific data is properly scoped (no cross-user leaks)

### Control Flow
- [ ] Conditional branches cover all cases (no missing else/default)
- [ ] Early returns don't skip necessary cleanup
- [ ] Loop break/continue logic is correct
- [ ] Async/await is used correctly (no missing `await` on coroutines)

### Return Values
- [ ] Functions return the documented type in all code paths
- [ ] Error conditions return appropriate error values
- [ ] Boolean logic is correct (no inverted conditions)
- [ ] Comparison operators are correct (`==` vs `is`, `<` vs `<=`)

## Acceptance Criteria
- All logic bugs have corresponding regression tests
- All state transitions match intended design
- All fixes validated by `pytest`, `vitest`, and `ruff check`
