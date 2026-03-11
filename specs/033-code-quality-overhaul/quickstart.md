# Quickstart: Code Quality & Technical Debt Overhaul

**Branch**: `033-code-quality-overhaul` | **Date**: 2026-03-10

## Developer Guide — Refactored Architecture

This document explains the key architectural changes introduced by the overhaul and how to work with the refactored codebase.

---

## 1. GitHub API Services (Phase 4)

### Before: One class for everything

```python
from src.services.github_projects.service import github_projects_service

# Every API domain mixed in one 5,338-line class
await github_projects_service.create_issue(owner, repo, title)
await github_projects_service.merge_pull_request(node_id)
await github_projects_service.create_branch(owner, repo, name, base)
await github_projects_service.get_project_items(project_id)
```

### After: Domain-specific services

```python
# Each domain is a focused service (<800 lines)
from src.services.github_projects.issues import github_issues_service
from src.services.github_projects.pull_requests import github_pr_service
from src.services.github_projects.branches import github_branch_service
from src.services.github_projects.projects import github_board_service
from src.services.github_projects.identities import is_copilot_author

# In API endpoints, use FastAPI dependency injection:
async def my_endpoint(
    issues: GitHubIssuesService = Depends(get_github_issues_service),
):
    await issues.create_issue(owner, repo, title)
```

### Bot Detection (Static Functions)

```python
# Before: service method
github_projects_service.is_copilot_author(login)

# After: standalone module function
from src.services.github_projects.identities import is_copilot_author
is_copilot_author(login)
```

---

## 2. Structured Logging (Cross-cutting)

### Usage

```python
from src.logging_utils import get_logger

logger = get_logger(__name__)

# Simple log (still valid)
logger.info("Processing task")

# Structured log with context (preferred for service operations)
logger.info("Issue created", extra={"operation": "create_issue", "issue_number": 42})
```

All log output is JSON-formatted automatically by the root handler. No per-file configuration needed.

---

## 3. DRY Helpers (Phase 2)

### Repository Resolution

```python
# Before: 8 different code paths with inconsistent fallbacks
owner = request.app.state.github_service.repo_owner or config.default_repo.split("/")[0]

# After: one canonical function
from src.utils import resolve_repository
owner, repo = await resolve_repository(request)
```

### Project Validation

```python
# Before: inline check repeated 5 times
project_id = request.app.state.get("selected_project_id")
if not project_id:
    raise HTTPException(status_code=400, detail="No project selected")

# After: dependency injection
from src.dependencies import require_selected_project
async def my_endpoint(project_id: str = Depends(require_selected_project)):
    ...
```

### Cached Fetch

```python
# Before: inline cache pattern
from src.utils import cached_fetch

data = await cached_fetch(
    cache=app_cache,
    key=f"projects:{project_id}",
    fetch_fn=lambda: github_service.get_project_items(project_id),
    refresh=force_refresh,
)
```

---

## 4. Agent Step States (Phase 3)

### Before: String matching

```python
if "✅" in cell_text or "Done" in cell_text:
    # done
elif "🔄" in cell_text:
    # active
```

### After: Typed enum

```python
from src.models.agent import AgentStepState

state = AgentStepState.from_markdown(cell_text)
match state:
    case AgentStepState.DONE:
        ...
    case AgentStepState.ACTIVE:
        ...
```

---

## 5. Phase Completion Workflow

Each phase follows this workflow:

1. **Clean stale tests**: Remove/update tests that validate behavior being changed
2. **Implement changes**: Make the refactoring changes
3. **Run verification**:
   - Backend: `pytest -x` (all tests pass)
   - Frontend: `npx vitest run` (all tests pass)
   - Linting: `ruff check backend/src/` / `npx eslint .`
   - Complexity: `cgc analyze complexity` (verify targets met)
4. **Commit**: Detailed commit message describing changes, motivation, and verified criteria

---

## 6. File Size Targets

| Category | Threshold | Verification |
|----------|-----------|--------------|
| Backend functions | Complexity ≤ 25 | `cgc analyze complexity` |
| Backend files | ≤ 1,500 lines | `wc -l` |
| Domain services | ≤ 800 lines | `wc -l` |
| Frontend components | ≤ 200 lines | `wc -l` |
| Frontend hooks | ≤ 200 lines | `wc -l` |
| Extracted helpers | ≤ 200 lines | `wc -l` |
