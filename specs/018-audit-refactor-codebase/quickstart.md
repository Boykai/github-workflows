# Quickstart: Audit & Refactor FastAPI+React GitHub Projects Copilot Codebase

**Feature**: 018-audit-refactor-codebase
**Date**: 2026-03-04

> Step-by-step implementation guide. Execute phases in order; each phase builds on the previous.

## Prerequisites

- Python 3.11+
- Node.js 18+ with npm
- Access to the repository on branch `018-audit-refactor-codebase`
- `ruff` installed for Python linting/formatting

## Phase 1 — Modernize Packages

### Step 1.1: Remove `agent-framework-core`

1. Open `backend/pyproject.toml`
2. Delete the line: `"agent-framework-core>=1.0.0a1",`
3. Delete the comment line above it: `# Microsoft Agent Framework (orchestration layer)`
4. Verify: `grep -r "agent_framework" backend/src/` returns no results

### Step 1.2: Bump Backend Dependencies

1. Open `backend/pyproject.toml`
2. Update dependency version specifiers to latest stable:
   - `"fastapi>=0.135.0"`
   - `"uvicorn[standard]>=0.41.0"`
   - `"httpx>=0.28.0"`
   - `"pydantic>=2.12.0"`
   - `"pydantic-settings>=2.7.0"`
   - `"python-multipart>=0.0.20"`
   - `"pyyaml>=6.0.2"`
   - `"github-copilot-sdk>=0.1.29"`
   - `"openai>=2.24.0"`
   - `"azure-ai-inference>=1.0.0b9"`
   - `"aiosqlite>=0.22.0"`
   - `"tenacity>=9.1.0"`
   - `"websockets>=14.0"`
3. Verify: `cd backend && pip install -e ".[dev]"` succeeds
4. Verify: Run test suite per-file as documented

### Step 1.3: Bump Frontend Dependencies

1. Open `frontend/package.json`
2. Update `@tanstack/react-query` to `^5.90.0`
3. Run: `cd frontend && npm install`
4. Verify: `npm test` passes, `npm run build` succeeds

## Phase 2 — DRY Consolidation

### Step 2A: Extract CopilotClientPool

1. Open `backend/src/services/completion_providers.py`
2. Add `CopilotClientPool` class BEFORE `CopilotCompletionProvider`:
   - Move `_token_key()` (static method) and `_get_or_create_client()` into the pool
   - Replace `self._clients: dict[str, Any]` with `BoundedDict[str, Any](maxlen=50)`
   - Add `cleanup()` method to stop all cached clients
3. Update `CopilotCompletionProvider`:
   - Remove its `_clients`, `_token_key()`, `_get_or_create_client()`
   - Accept `CopilotClientPool` in `__init__` or use a module-level instance
4. Open `backend/src/services/model_fetcher.py`:
   - Import `CopilotClientPool` from `completion_providers`
   - Remove `GitHubCopilotModelFetcher._clients`, `_token_key()`, `_get_or_create_client()`
   - Use the shared pool instance
5. Verify: Run `pytest tests/unit/test_completion_providers.py` and `pytest tests/unit/test_model_fetcher.py`

### Step 2B: Extract `_with_fallback()` Helper

1. Open `backend/src/services/github_projects/service.py`
2. Add `_with_fallback()` as a private async method on `GitHubProjectsService`:
   ```python
   async def _with_fallback(self, primary_fn, fallback_fn, context_msg):
       try:
           return await primary_fn()
       except Exception as exc:
           logger.warning("%s primary failed (%s), trying fallback", context_msg, exc)
           return await fallback_fn()
   ```
3. Refactor `assign_copilot()` to use `_with_fallback()`
4. Refactor `add_issue_to_project()` to use `_with_fallback()`
5. Refactor `request_copilot_review()` to use `_with_fallback()`
6. Verify: Run relevant tests

### Step 2C: Document Retry Logic Relationship

1. Open `backend/src/services/github_projects/service.py`
2. Add clear docstring/comments to `_request_with_retry()` noting it is THE single retry strategy
3. Add clear docstring/comments to `_graphql()` noting it delegates to `_request_with_retry()` and adds ETag caching
4. No structural code changes needed (already unified)

### Step 2D: Consolidate Header Construction

1. Open `backend/src/services/github_projects/service.py`
2. Add optional `graphql_features: str | None = None` parameter to `_build_headers()`
3. Find all inline header construction that duplicates `_build_headers()` output
4. Replace with calls to `_build_headers()`
5. Verify: Run service tests

## Phase 3 — Fix Anti-Patterns

### Step 3A: Parameterize Hardcoded Model

1. Open `backend/src/services/github_projects/graphql.py`
2. Change `ASSIGN_COPILOT_MUTATION` to accept `$model: String!` variable
3. Replace `model: "claude-opus-4.6"` with `model: $model`
4. Open `backend/src/services/github_projects/service.py`
5. Update GraphQL call to pass `model` variable from `AgentAssignmentConfig.model`
6. Update REST payload similarly
7. Verify: Run tests for agent assignment

### Step 3B: Document and Bound Chat State

1. Open `backend/src/api/chat.py`
2. Import `BoundedDict` from `src.utils`
3. Replace `_messages: dict[...] = {}` with `BoundedDict[...](maxlen=1000)`
4. Same for `_proposals` and `_recommendations`
5. Add TODO comment: `# TODO: Migrate to SQLite for persistence across restarts (MVP: in-memory only)`
6. Verify: Run chat API tests

### Step 3C: Implement `delete_files`

1. Open `backend/src/services/github_commit_workflow.py`
2. Find the `commit_files()` function that builds the GraphQL `createCommitOnBranch` payload
3. Add `deletions` entries to `fileChanges` when `delete_files` is provided:
   ```python
   if delete_files:
       file_changes["deletions"] = [{"path": p} for p in delete_files]
   ```
4. Remove the warning log stub
5. Verify: Add/update tests if test infrastructure exists

### Step 3D: Document OAuth State Limitations

1. Open `backend/src/services/github_auth.py`
2. Add documentation comments above `_oauth_states`:
   ```python
   # OAuth verification state (ephemeral, single-instance only).
   # Bounded to 1000 entries with FIFO eviction. In a multi-instance
   # deployment, OAuth flows started on one instance cannot be completed
   # on another. For multi-instance support, migrate to SQLite.
   ```
3. No code changes needed (already uses BoundedDict)

### Step 3E: Consolidate Singleton Registration

1. Open `backend/src/dependencies.py`
2. Remove module-level fallback imports
3. Have each dependency function raise a clear error if `app.state` attribute is missing
4. Ensure `backend/src/main.py` sets all `app.state` attributes before routes are registered
5. Verify: Run all API tests

### Step 3F: Bound Workflow Orchestrator Caches

1. Open `backend/src/services/workflow_orchestrator/transitions.py`
2. Import `BoundedDict` from `src.utils`
3. Replace `_pipeline_states: dict[int, PipelineState] = {}` with `BoundedDict[int, PipelineState](maxlen=500)`
4. Same for `_issue_main_branches` and `_issue_sub_issue_map`
5. Verify: Run orchestrator tests

## Verification Checklist

After all phases are complete:

- [ ] `cd backend && ruff check src tests && ruff format --check src tests` — no errors
- [ ] `cd backend && python -m pytest tests/unit/test_*.py -q` — all tests pass (run per-file)
- [ ] `cd frontend && npm test` — all tests pass
- [ ] `cd frontend && npm run build` — builds successfully
- [ ] `grep -r "agent.framework" backend/` — no results
- [ ] `grep -r "claude-opus-4.6" backend/src/` — no hardcoded model strings
- [ ] All in-memory caches use `BoundedDict`/`BoundedSet`
