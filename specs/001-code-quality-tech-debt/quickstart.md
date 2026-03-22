# Quickstart: Code Quality & Technical Debt — Cache Wrapper Extraction, Error Handling Consolidation & Dead Code Sweep

**Feature**: 001-code-quality-tech-debt | **Date**: 2026-03-22

## Prerequisites

- Python ≥3.12 installed
- Repository cloned: `github-workflows`
- Working directory: `solune/backend/`

## Setup

```bash
cd solune/backend
pip install -e ".[dev]"
```

## Verification Commands

Run these after every completed item:

```bash
# Mandatory gate (FR-011)
cd solune/backend
python -m pytest tests/ -x          # Stop at first failure
ruff check src/                      # No new warnings

# Dead code analysis (Phase D)
ruff check --select F401,F811 src/   # Unused imports / redefined names
# vulture src/                       # Dead code detection (install separately if needed)

# Optional quality checks
pyright src/                         # Type checking
bandit -r src/                       # Security scanning
```

## Development Workflow

### Phase A: Parallel Items (Stories 1, 2, 5)

#### Item 1.1 — `_cycle_cached()` Extraction

1. Open `solune/backend/src/services/github_projects/service.py`
2. Add `_cycle_cached()` method to `GitHubProjectsService` class:
   ```python
   async def _cycle_cached(self, cache_key: str, fetch_fn: Callable[[], Awaitable[T]]) -> T:
       cached = self._cycle_cache.get(cache_key)
       if cached is not None:
           self._cycle_cache_hit_count += 1
           return cached  # type: ignore[return-value]
       result = await fetch_fn()
       self._cycle_cache[cache_key] = result
       return result
   ```
3. Refactor all 7 call sites in: `pull_requests.py`, `projects.py`, `copilot.py`, `issues.py`
4. Run verification gate

#### Item 1.2 — Deviation Comments

1. Open `solune/backend/src/api/workflow.py`
2. Add inline comment near line ~543 explaining `session.github_username` fallback
3. Add inline comment near line ~615 explaining partial-resolution pattern
4. Run verification gate

#### Item 1.5 — Dead Code Removal

1. Open `solune/backend/src/services/cleanup_service.py`
2. Verify mutual exclusivity of `preserved_branch_names` and `branches_to_delete` in `_classify_branches()`
3. Remove lines 640–650 (the `branch_in_delete` check and its body)
4. Add regression test for `branch_preserved` code path
5. Run verification gate

### Phase B: `cached_fetch()` Call-Site Refactoring (Story 1)

1. Identify all cache.get → fetch → cache.set patterns across the 5 target files
2. Replace with `await cached_fetch(cache_key, fetch_fn, ttl_seconds=...)` 
3. Leave board.py dual-key sites inline if they don't fit the generic wrapper
4. Run verification gate after each file

### Phase C: Error Handling Migration (Story 3)

1. Relax `error_cls` type in `handle_service_error()` from `type[AppException] | None` to `type[Exception] | None`
2. Add type-aware construction logic (keyword `message=` for AppException, positional for others)
3. Update tests in `test_logging_utils.py` for the new type support
4. Migrate board.py patterns (3 sites)
5. Migrate ai_agent.py patterns (4 sites) — preserve string-based error classification
6. Migrate agents/service.py pattern (1 site — bare raise)
7. Run verification gate after each file

### Phase D: Spec 039 & Dead Code Sweep (Story 4)

1. Create `specs/039-dead-code-cleanup/` directory
2. Run `ruff check --select F401,F811 src/` and capture output
3. Run `vulture src/` and capture output
4. Author `specs/039-dead-code-cleanup/spec.md` with inventory and dispositions
5. Execute time-boxed sweep of confirmed dead code
6. Run verification gate

## Key Files

| File | Purpose |
|------|---------|
| `src/services/cache.py` | Global cache + `cached_fetch()` helper |
| `src/services/github_projects/service.py` | `GitHubProjectsService` + `_cycle_cached()` |
| `src/logging_utils.py` | `handle_service_error()` |
| `src/exceptions.py` | `AppException` hierarchy |
| `src/services/cleanup_service.py` | Dead code block (lines 641–649) |
| `src/api/workflow.py` | Deviation documentation sites |
| `src/services/ai_agent.py` | ValueError error handling sites |

## What NOT to Change

- **Singleton patterns** at `service.py:464` and `agents.py` — deferred to separate PR (FR-008)
- **Exception types** at API boundaries — must remain identical
- **Cache TTLs** — must remain identical
- **Stale-fallback semantics** — must remain identical
- **board.py dual-key cache sites** — keep inline if abstraction is ill-fitting
