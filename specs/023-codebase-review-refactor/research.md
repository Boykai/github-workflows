# Research: Full Codebase Review & Refactoring

**Branch**: `023-codebase-review-refactor` | **Date**: 2026-03-06

## R1: python-jose Dependency Status

**Decision**: Remove `python-jose[cryptography]>=3.3.0` from `pyproject.toml`.

**Rationale**: Zero import references exist in the entire backend source tree. Grep for `jose`, `jwt`, `JWT`, `JWTError`, and `JoseError` across `backend/src/` returned no matches. The application does not perform JWT operations server-side — authentication is handled via GitHub OAuth tokens passed through as bearer tokens. The dependency was likely added speculatively and never used.

**Alternatives considered**:
- Keep as optional dependency for future JWT needs → Rejected: YAGNI (Constitution Principle V). Can be re-added when actually needed.
- Replace with PyJWT → Rejected: No JWT functionality exists to migrate. No replacement needed.

**Risk**: Near-zero. Static analysis (grep + linter) confirms zero references. `pip install --dry-run` should verify no transitive dependency breaks.

## R2: tenacity Dependency Status

**Decision**: Keep `tenacity>=8.2.0`. It IS actively used.

**Rationale**: `backend/src/services/signal_delivery.py` line 16 imports `from tenacity import (retry, stop_after_attempt, wait_exponential, RetryError)`. The spec assumed tenacity was unused because custom retry logic exists elsewhere, but the Signal delivery service uses tenacity's decorator-based retry for message delivery.

**Note**: The custom retry logic in the GitHub service layer (via `_with_fallback()` helper and manual retry loops) is separate from tenacity and serves different retry semantics (multiple API strategies vs. exponential backoff).

## R3: _with_fallback() Helper Usage

**Decision**: Remove `_with_fallback()` method during service decomposition.

**Rationale**: Defined at `service.py:210` but never called — only the definition line appears in grep results. No callers exist in the entire codebase. The fallback pattern used by `add_issue_to_project()` and `assign_copilot_to_issue()` uses inline multi-step chains instead of this helper.

**Alternatives considered**:
- Refactor callers to USE `_with_fallback()` → Rejected: would enlarge scope. The inline patterns work correctly. Can be reconsidered in a future pass.

## R4: Frontend jsdom vs happy-dom

**Decision**: Remove `jsdom` from `package.json` devDependencies.

**Rationale**: `frontend/vitest.config.ts` line 14 configures `environment: 'happy-dom'`. The `jsdom` package is listed in `package.json` (line 57: `"jsdom": "^27.4.0"`) but never referenced in any test configuration, test file, or source file. Only `happy-dom` is the active test environment.

**Risk**: Low. Remove from `package.json`, run `npm install`, verify all tests pass.

## R5: @dnd-kit Version Alignment

**Decision**: Align all `@dnd-kit` packages to compatible versions.

**Current state**:
- `@dnd-kit/core`: `^6.3.1` (old major)
- `@dnd-kit/modifiers`: `^9.0.0` (new major)
- `@dnd-kit/sortable`: `^10.0.0` (newest major)
- `@dnd-kit/utilities`: `^3.2.2` (old major)

**Rationale**: The `@dnd-kit` ecosystem underwent a major rewrite. `@dnd-kit/sortable@10` is designed to work with `@dnd-kit/core@6` via peer dependencies but `@dnd-kit/modifiers@9` may have incompatibilities. Need to verify peer dependency requirements.

**Approach**: Run `npm ls @dnd-kit/core` to check resolved peer dependency tree. If warnings exist, align to the versions that `@dnd-kit/sortable@10` expects. Test drag-and-drop functionality in the board after any version changes.

**Risk**: Medium. DnD-kit version changes may affect drag behavior. Manual board testing required.

## R6: Service Decomposition — Module Boundaries

**Decision**: Decompose `service.py` (4,941 LOC) into 8 focused modules + facade.

**Research findings** (from exhaustive method-to-line mapping):

| Module | Methods | Line Range | Est. LOC |
|--------|---------|------------|----------|
| `client.py` | `_rest`, `_rest_response`, `rest_request`, `_graphql`, `get_last_rate_limit`, `clear_last_rate_limit`, `close` | 64-349 | ~300 |
| `projects.py` | `list_user_projects`, `list_org_projects`, `_parse_projects`, `get_project_items` | 351-519 | ~170 |
| `board.py` | `list_board_projects`, `get_board_data`, `_reconcile_board_items`, `create_draft_item`, `update_item_status` | 521-1237 | ~720 |
| `issues.py` | `create_issue`, `update_issue_body`, `update_issue_state`, `add_issue_to_project`, `_verify_item_on_project`, `_get_project_rest_info`, `_add_issue_to_project_rest`, `assign_issue`, `get_issue_with_comments`, `format_issue_context_as_prompt`, `check_agent_completion_comment`, `check_issue_closed`, `create_sub_issue`, `get_sub_issues`, `tailor_body_for_agent`, `validate_assignee`, `create_issue_comment` | 1239-2100, 4129-4284 | ~750 |
| `copilot.py` | `is_copilot_author`, `is_copilot_swe_agent`, `get_copilot_bot_id`, `unassign_copilot_from_issue`, `is_copilot_assigned_to_issue`, `assign_copilot_to_issue`, `_assign_copilot_rest`, `_assign_copilot_graphql` | 235-252, 1637-2416 | ~400 |
| `pull_requests.py` | `_search_open_prs_for_issue_rest`, `find_existing_pr_for_issue`, `get_linked_pull_requests`, `get_pull_request`, `mark_pr_ready_for_review`, `request_copilot_review`, `merge_pull_request`, `delete_branch`, `update_pr_base`, `link_pull_request_to_issue`, `has_copilot_reviewed_pr`, `get_pr_timeline_events`, `check_copilot_finished_events`, `check_copilot_pr_completion`, `create_pull_request` | 2418-3820, 4720-4760 | ~700 |
| `fields.py` | `get_project_fields`, `update_project_item_field`, `set_issue_metadata`, `update_item_status_by_name`, `update_sub_issue_project_status` | 3824-4109, 2418-2618 | ~350 |
| `repository.py` | `get_repository_info`, `get_repository_owner`, `get_project_repository`, `create_branch`, `get_branch_head_oid`, `commit_files`, `get_directory_contents`, `get_file_content`, `get_file_content_from_ref`, `get_pr_changed_files`, `list_available_agents` | 1980-2030, 4360-4835 | ~450 |

**Facade pattern**: `service.py` retains the `GitHubProjectsService` class but delegates to module-level classes. The `__init__.py` re-exports `GitHubProjectsService` so all existing `from src.services.github_projects import ...` imports continue to work.

**Alternatives considered**:
- Flat functions instead of class decomposition → Rejected: methods share `self._client_factory`, `self._cycle_cache`, and HTTP client state. Class composition preserves shared state naturally.
- Mixin-based decomposition → Rejected: Python mixins are fragile with complex MRO. Composition (delegate to owned objects) is cleaner.

## R7: Circular Import Risk in Decomposition

**Decision**: Use composition pattern with dependency injection to avoid circular imports.

**Current imports in service.py:**
```python
from src.models.agent import AgentSource, AvailableAgent
from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.task import Task
from src.services.github_projects.graphql import (...)
from src.utils import BoundedDict, utcnow
```
Plus dynamic imports:
- `from src.services.workflow_orchestrator import get_workflow_config` (line 891, inside method body)
- `from src.services.cache import cache, get_sub_issues_cache_key` (line 4155, inside method body)

**Risk analysis**: Low. The current imports are all downward (service → models, service → utils). No model imports the service. The dynamic imports are already inline (inside method bodies) which naturally avoids circular deps. Decomposed modules will import from `client.py` (shared HTTP infrastructure) and from `models/` — both one-directional.

**Mitigation**: If any circular dependency surfaces during implementation, resolve via:
1. Move the import inside the method body (lazy import)
2. Use `TYPE_CHECKING` guard for type-only imports

## R8: Error Handling Helper Adoption Strategy

**Decision**: Adopt `handle_service_error()` and `safe_error_response()` across all API endpoints.

**Current state**: ~40+ try/except blocks across 14 API route files. Zero calls to the existing helpers in `logging_utils.py`.

**Pattern to standardize**: Each endpoint's error path follows this inline pattern:
```python
try:
    result = await service.do_thing(...)
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Failed to do thing: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

`handle_service_error(e, "do thing", GitHubAPIError)` encapsulates this pattern with structured logging and proper error classification.

**Approach**: Create a decorator or context manager that wraps the common pattern. This avoids editing every endpoint's body — instead, apply at the route level. Evaluate both approaches during implementation:
1. Decorator: `@handle_errors("operation_name")` 
2. Direct helper calls: Keep existing helpers, systematically adopt in each endpoint

**Alternatives considered**:
- FastAPI exception handlers only → Rejected: too coarse. Different endpoints need different operation context strings for logging.
- Global middleware → Rejected: loses per-endpoint operation context.

## R9: Cache Wrapper Pattern

**Decision**: Create `_cycle_cached()` method on the base client mixin to eliminate 7× duplicated inline cache patterns.

**Current duplicated pattern** (appears 7 times in service.py):
```python
cache_key = f"prefix:{discriminator}"
cached = self._cycle_cache.get(cache_key)
if cached is not None:
    self._cycle_cache_hit_count += 1
    return cached
# ... actual fetch ...
self._cycle_cache[cache_key] = result
return result
```

**Proposed wrapper**: 
```python
async def _cycle_cached(self, key: str, fetch: Callable[[], Awaitable[T]]) -> T:
    cached = self._cycle_cache.get(key)
    if cached is not None:
        self._cycle_cache_hit_count += 1
        return cached
    result = await fetch()
    self._cycle_cache[key] = result
    return result
```

Each call site becomes: `return await self._cycle_cached(f"issue:{key}", lambda: self._fetch_issue(...))`

## R10: Backend Dependency Version Floor Updates

**Decision**: Update version floors to latest compatible stable versions. Research deferred to implementation phase — each update tested individually.

**Approach**: For each dependency, run `pip install --upgrade <pkg>` in the venv, run tests, and update the floor version in `pyproject.toml`. Do NOT pin exact versions — keep `>=` floor pattern for flexibility.

**Priority order** (highest risk first):
1. `githubkit>=0.14.0` → check current installed version, update floor
2. `fastapi>=0.109.0` → likely 0.115+ available
3. `pydantic>=2.5.0` → likely 2.10+ available
4. `httpx>=0.26.0` → likely 0.28+ available
5. Remaining deps: incremental updates

## R11: Frontend Dependency Version Floor Updates

**Decision**: Update conservative versions only. Defer React 19 and Tailwind v4.

**Confirmed scope**:
- Remove `jsdom` (unused)
- Align `@dnd-kit` packages (verify peer deps)
- Update `typescript`, `vitest`, `vite` if compatible
- Do NOT upgrade React 18 → 19 (spec exclusion)
- Do NOT upgrade Tailwind 3 → 4 (spec exclusion)

## R12: Initialization Consolidation Strategy

**Decision**: Consolidate to lifespan + `Depends()` pattern. Deprecate module-level globals.

**Current state** (3 patterns):
1. **Lifespan**: `main.py` creates services in lifespan, stores on `app.state`
2. **Module-level globals**: `service.py:4941` creates `github_projects_service = GitHubProjectsService()`
3. **Dependency injection**: `dependencies.py` provides `get_github_service()` which tries `app.state` first, falls back to module global

**Target state**: All services created in lifespan, stored on `app.state`, accessed exclusively via `Depends(get_github_service)`. Module-level global in `service.py` removed. `github_commit_workflow.py` line 12's direct import replaced with DI parameter.

**Migration strategy**: 
1. First, ensure all API routes use `Depends()` (most already do)
2. Update `github_commit_workflow.py` to accept service as parameter
3. Remove module-level `github_projects_service` singleton from `service.py`
4. Remove fallback logic from `dependencies.py`
5. Run full test suite after each step
