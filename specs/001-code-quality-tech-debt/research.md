# Research: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep

**Feature**: 001-code-quality-tech-debt | **Date**: 2026-03-22

## Research Tasks

This research resolves all "NEEDS CLARIFICATION" items from the Technical Context section and investigates best practices for each technology choice and integration pattern.

---

### R-001: `cached_fetch()` Already Exists — Refactoring Strategy

**Question**: Does `cached_fetch()` need to be created, or does it already exist?

**Finding**: The `cached_fetch()` async helper **already exists** in `solune/backend/src/services/cache.py` (lines 187–277). It is a sophisticated cache-aside implementation with:
- Automatic cache miss/hit handling
- Optional forced refresh via `force_refresh` parameter
- Stale fallback when fetch fails (via `cache.get_stale()`)
- Rate-limit fallback with warnings
- Data-hash comparison for change detection (refresh TTL only if data unchanged)
- Configurable TTL via `ttl_seconds` parameter

**Decision**: No new helper function needs to be written. The work is **call-site refactoring** — replacing 10 instances of the inline cache.get → fetch → cache.set pattern with calls to the existing `cached_fetch()`.

**Rationale**: The existing implementation already handles all the edge cases documented in the spec (cache miss, stale fallback, error propagation). Writing a new function would duplicate logic.

**Alternatives Considered**:
- Writing a new, simpler version: Rejected because the existing version handles rate-limit detection and data-hash comparison, which some call sites need.
- Decorating functions with a caching decorator: Rejected because the call sites have varying signatures and context requirements that don't map cleanly to decorator patterns.

---

### R-002: `_cycle_cached()` Pattern Shape

**Question**: What is the exact shape of the cycle cache pattern, and can a single method handle all 7 call sites?

**Finding**: All 7 call sites follow an identical 4-step pattern:
1. Build cache key: `f"prefix:{owner}/{repo}/{number}"` or `f"prefix:{project_id}"`
2. Check cache: `cached = self._cycle_cache.get(cache_key)`
3. If hit: `self._cycle_cache_hit_count += 1; return cached`
4. On miss: fetch data, then `self._cycle_cache[cache_key] = result; return result`

The pattern is uniform enough for a single `_cycle_cached()` method with signature:
```python
async def _cycle_cached(self, cache_key: str, fetch_fn: Callable[[], Awaitable[T]]) -> T
```

**Decision**: Add `_cycle_cached()` as an instance method on `GitHubProjectsService` in `service.py`. The method accepts a cache key and an async callable, handles the cache check/set/hit-count logic, and returns the result.

**Rationale**: All 7 sites share the identical pattern. The callable approach avoids premature abstraction of the diverse fetch logic (GraphQL queries, REST calls, paginated fetches).

**Alternatives Considered**:
- Using a decorator: Rejected because the cache key construction varies per call site and depends on method arguments.
- Passing key components instead of a pre-built key: Rejected as unnecessary complexity; callers already construct descriptive keys.

---

### R-003: `handle_service_error()` Extension for ValueError

**Question**: How should `handle_service_error()` be extended to support `ValueError` (a non-`AppException` type) without breaking existing callers?

**Finding**: The current signature is:
```python
def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
```

The function constructs the raised exception via `error_cls(message=f"Failed to {operation}")`. `ValueError` does not accept a `message=` keyword argument — it uses positional args only.

**Decision**: Relax the type annotation from `type[AppException] | None` to `type[Exception] | None`. Adjust the raise logic to detect whether the class accepts `message=` as a keyword or falls back to positional construction:
```python
if issubclass(error_cls, AppException):
    raise error_cls(message=f"Failed to {operation}") from exc
else:
    raise error_cls(f"Failed to {operation}") from exc
```

**Rationale**: This preserves backward compatibility (existing callers pass `AppException` subclasses or `None`), supports `ValueError` without a wrapper class, and keeps the function simple.

**Alternatives Considered**:
- Introducing a thin `AIAgentError(ValueError)` wrapper: Rejected because the spec requires preserving the exact `ValueError` type at API boundaries, and a subclass would change `isinstance` checks.
- Creating a separate `handle_service_error_generic()`: Rejected as unnecessary duplication; a single function with type-aware construction is simpler.

---

### R-004: board.py Cache Pattern Compatibility with `cached_fetch()`

**Question**: Can the board.py cache pattern (dual-key lookups + stale fallback + rate-limit classification) be cleanly adapted to `cached_fetch()`?

**Finding**: The board.py pattern at lines ~221–234 and ~293–297 uses:
1. Multi-level cache checks (board-specific key, then generic project key)
2. Stale fallback with `cache.get_stale()`
3. Rate-limit error classification via `_classify_github_error(e)`
4. `GitHubAPIError` with `details={"reason": _classify_github_error(e)}`

The existing `cached_fetch()` already handles stale fallback and rate-limit detection internally. However, the **dual-key lookup** (checking two cache keys before fetching) and the **error details enrichment** (`details={"reason": ...}`) are specific to board.py and not supported by `cached_fetch()`.

**Decision**: Target 80% coverage as spec allows. The board.py call sites with dual-key lookups SHOULD remain inline. Simpler board.py call sites that follow the standard single-key pattern CAN be refactored. This is explicitly permitted by the spec: "if the generic wrapper cannot cleanly accommodate this variant, those instances SHOULD remain inline rather than be forced into an ill-fitting abstraction."

**Rationale**: Forcing dual-key lookups into `cached_fetch()` would require adding optional parameters for secondary keys, which over-generalizes the helper for a single consumer. Principle V (Simplicity) applies.

**Alternatives Considered**:
- Adding a `fallback_keys` parameter to `cached_fetch()`: Rejected as premature abstraction for a single call site.
- Wrapping the dual-key logic in a board-specific helper: Acceptable but lower priority; inline code is clear enough.

---

### R-005: Dead Code Verification — `branch_in_delete` Block Mutual Exclusivity

**Question**: Is the `branch_in_delete` inner block (cleanup_service.py lines 641–649) truly unreachable?

**Finding**: The categorization logic in `_classify_branches()` (lines 758–767) uses an exclusive `if/else`:
```python
for branch_data in branches_data:
    info = _categorize_branch(...)
    if info.eligible_for_deletion:
        to_delete.append(info)    # → branches_to_delete
    else:
        to_preserve.append(info)  # → branches_to_preserve
```

Each branch is placed in **exactly one** list. The `preserved_branch_names` set is built from `branches_to_preserve`, and `branches_to_delete` is the other list. By construction, a branch cannot appear in both sets simultaneously.

The existing TODO comment at lines 632–639 explicitly documents this: "The inner `branch_in_delete` check is unreachable because `preserved_branch_names` and `branches_to_delete` are built from the same exclusive categorisation."

**Decision**: The block IS unreachable. Remove lines 640–650 (the `branch_in_delete` check and its body). Add a regression test that exercises the `branch_preserved = True` code path to confirm the outer logic works correctly after removal.

**Rationale**: Code inspection confirms mutual exclusivity. The existing TODO was placed as a deliberate marker for future cleanup.

**Alternatives Considered**:
- Keeping the block with a debug assertion: Rejected because dead code adds confusion and inflates coverage denominators.
- Adding a runtime assertion instead of removing: Acceptable as a secondary safety net, but the spec requires removal.

---

### R-006: ai_agent.py String-Based Error Classification

**Question**: Should the fragile string-based error classification in ai_agent.py ("401", "404", "Access denied") be preserved, refactored, or documented as tech debt?

**Finding**: The 4 ai_agent.py error handling sites (L193, L262, L595, L769) use string matching on exception messages to classify errors:
```python
if "401" in error_msg or "Access denied" in error_msg:
    raise ValueError("AI provider authentication failed...")
elif "404" in error_msg or "Resource not found" in error_msg:
    raise ValueError("AI model/deployment not found...")
else:
    raise ValueError(f"Failed to {operation}: {error_msg}")
```

This pattern is duplicated verbatim across 3 of the 4 sites (with slight message variations).

**Decision**: During Phase C migration, the string-based classification logic should be **preserved as-is** within a private helper (e.g., `_classify_ai_error()`) that is called before `handle_service_error()`. The migration replaces the boilerplate `logger.error(...)` + `raise ValueError(...)` with `handle_service_error()` for the default case, while the classification branches remain as explicit conditionals. Document the string-based classification as technical debt with an inline comment.

**Rationale**: Changing the classification logic is out of scope for this refactoring (it would change error messages visible to API consumers). The spec requires behavioral equivalence.

**Alternatives Considered**:
- Refactoring to use exception type checking instead of string matching: Out of scope; would require changes to AI provider SDK error types.
- Moving classification into `handle_service_error()`: Rejected as over-generalization; this pattern is specific to AI provider errors.

---

### R-007: Spec 039 Directory and CHANGELOG Gap

**Question**: Does `specs/039-dead-code-cleanup/` exist? What is the CHANGELOG reference?

**Finding**: 
- `specs/039-dead-code-cleanup/` **does NOT exist** in the repository
- The CHANGELOG at `solune/CHANGELOG.md` (line ~81) references: "Dead code and technical debt cleanup specification (039-dead-code-cleanup)"
- This is a documentation gap — the spec was announced but never authored

**Decision**: Create `specs/039-dead-code-cleanup/` as the first act of Phase D. The spec will contain an inventory of all dead code items identified by `ruff check --select F401,F811` and `vulture`, with dispositions (remove, defer, or retain with justification). The `cleanup_service.py` L641–649 block must be counted in this inventory.

**Rationale**: The spec closes the CHANGELOG gap and provides an auditable record before any code is removed.

**Alternatives Considered**:
- Skipping the spec and just removing dead code: Rejected because the spec requirement is explicit in FR-006.
- Using a GitHub issue instead of a spec: Rejected because the formal spec format provides better auditability.

---

### R-008: Verification Gate Tooling

**Question**: What are the exact commands for the verification gate?

**Finding**: From `pyproject.toml` and existing CI configuration:
```bash
cd solune/backend
python -m pytest tests/ -x          # Stop at first failure
ruff check src/                      # Lint check, no new warnings
ruff check --select F401,F811 src/   # Dead code specific checks
```

Additional quality gates available:
```bash
pyright src/                         # Type checking
bandit -r src/                       # Security scanning
```

**Decision**: Use `pytest -x` + `ruff check` as the mandatory verification gate after every item. `pyright` and `bandit` are optional but recommended before final merge.

**Rationale**: Matches the spec's FR-011 requirement exactly.

---

## Summary of Resolved Items

| Item | Status | Resolution |
|------|--------|------------|
| `cached_fetch()` creation | ✅ RESOLVED | Already exists (cache.py L187–277); work is call-site refactoring |
| `_cycle_cached()` pattern shape | ✅ RESOLVED | Uniform 4-step pattern; single method with `(cache_key, fetch_fn)` signature |
| `handle_service_error()` ValueError support | ✅ RESOLVED | Relax type annotation + type-aware construction logic |
| board.py compatibility | ✅ RESOLVED | Dual-key sites stay inline; target 80% coverage |
| Dead code verification | ✅ RESOLVED | Block is unreachable by construction; safe to remove |
| ai_agent.py error classification | ✅ RESOLVED | Preserve string-based logic; document as tech debt |
| Spec 039 gap | ✅ RESOLVED | Create directory and author spec in Phase D |
| Verification tooling | ✅ RESOLVED | `pytest -x` + `ruff check` per FR-011 |

All NEEDS CLARIFICATION items resolved. Proceeding to Phase 1.
