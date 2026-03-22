# Quickstart: Phase 2 — Code Quality & DRY Consolidation

**Feature**: 001-code-quality-dry  
**Date**: 2026-03-22

## Overview

This feature consolidates duplicated patterns across the Solune backend API layer into shared, tested utilities. No new features are added — all changes are internal refactoring with zero external API changes.

## What Changes

| Area | Change | Impact |
|------|--------|--------|
| Error handling | 14 inline catch→raise blocks → `handle_service_error()` | Consistent logging and exception classification |
| Caching | 4 inline cache-aside patterns → `cached_fetch()` | ~160 fewer lines of duplicated cache logic |
| Fallback resilience | `_with_fallback()` on base service | Declarative primary→verify→fallback pattern |
| Repository resolution | REST fallback step added | More resilient repo lookup when GraphQL fails |
| Startup deduplication | Inline owner/repo extraction → `resolve_repository()` | Single source of truth for repo resolution |

## Prerequisites

- Python ≥3.12 (target 3.13)
- Existing Solune backend development environment
- All Phase 1 work completed (validation helper consolidation — Item 2.3)

## Development Workflow

### Run existing tests first (baseline)

```bash
cd solune/backend
python -m pytest tests/unit/ -x -q
```

### After changes — verify no regressions

```bash
# Unit tests — must all pass with no modifications
python -m pytest tests/unit/ -x -q

# Specific test files for new/modified utilities
python -m pytest tests/unit/test_cache.py -v      # cached_fetch() extensions
python -m pytest tests/unit/test_service.py -v     # _with_fallback() tests
python -m pytest tests/unit/test_utils.py -v       # resolve_repository() REST fallback

# Lint and type checks
ruff check src/
pyright src/
```

### Grep audit for error-handling completeness

```bash
# Should return ONLY excluded patterns (health, WebSocket, error-returning handlers)
grep -rn 'logger.error\|logger.exception' src/api/ | grep -v handle_service_error
```

## Key Patterns to Follow

### Using `cached_fetch()` (for new endpoints)

```python
from src.services.cache import cached_fetch, cache

result = await cached_fetch(
    cache_instance=cache,
    key=f"my_endpoint:{user_id}",
    fetch_fn=lambda: fetch_from_github(token, project_id),
    ttl_seconds=300,
    stale_fallback=True,
    rate_limit_fallback=True,          # Optional: handle rate limits gracefully
    data_hash_fn=compute_data_hash,    # Optional: avoid re-caching identical data
)
```

### Using `_with_fallback()` (for resilient operations)

```python
result = await self._with_fallback(
    primary_fn=lambda: self._do_via_graphql(token, args),
    fallback_fn=lambda: self._do_via_rest(token, args),
    operation="my_operation",
    verify_fn=lambda: self._verify_result(token, expected_id),  # Optional
)
# result is T | None — None means total failure (soft-failure contract)
```

### Using `handle_service_error()` (for error handling)

```python
from src.logging_utils import handle_service_error
from src.exceptions import GitHubAPIError

try:
    result = await some_api_call()
except Exception as e:
    handle_service_error(e, "operation description", GitHubAPIError)
    # Never reaches here — handle_service_error always raises
```

## Phase Execution Order

Phases A, B, and C can execute in parallel. Phase D is sequential.

```
Phase A: Repository Resolution (FR-017–019)     ──┐
Phase B: Cache Unification (FR-005–011)          ──┼── Parallel
Phase C: Fallback Abstraction (FR-012–016)       ──┘
Phase D: Error Handling (FR-001–004)             ── Sequential (verify → decide → migrate)
Phase E: Verification (FR-020–025)               ── After all phases complete
```

## Files Modified (Summary)

| File | Changes |
|------|---------|
| `src/services/cache.py` | Extend `cached_fetch()` with `rate_limit_fallback`, `data_hash_fn` |
| `src/services/github_projects/service.py` | Add `_with_fallback()` method |
| `src/services/github_projects/issues.py` | Refactor `add_issue_to_project()` to use `_with_fallback()` |
| `src/utils.py` | Add REST fallback step to `resolve_repository()` |
| `src/main.py` | Replace inline owner/repo extraction with `resolve_repository()` |
| `src/api/board.py` | Migrate 3 error sites + 2 cache patterns to shared utilities |
| `src/api/tools.py` | Migrate applicable error sites to `handle_service_error()` |
| `src/api/projects.py` | Migrate `list_projects()` cache to `cached_fetch()` |
| `src/api/chat.py` | Migrate `send_message()` cache reads to `cached_fetch()` |
| `src/api/pipelines.py` | Migrate 1 error site |
| `src/api/tasks.py` | Migrate 1 error site |
| `src/api/webhooks.py` | Migrate 2 error sites |
| `tests/unit/test_cache.py` | Add tests for `cached_fetch()` extensions |
| `tests/unit/test_service.py` | Add tests for `_with_fallback()` |
| `tests/unit/test_utils.py` | Add test for REST fallback in `resolve_repository()` |
