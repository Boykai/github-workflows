# Migration Plan: Singleton Removal for `github_projects_service`

**Date**: 2026-03-13
**Feature**: 039-dead-code-cleanup (planning only — implementation deferred)

## Current State

Module-level singletons are created in:
- `backend/src/services/github_projects/service.py` L338-343
- `backend/src/services/github_projects/agents.py` L363-367

Both are exported via `backend/src/services/github_projects/__init__.py` L56 and imported across 25+ files with 207+ total references.

## Problem

The singleton pattern makes testing harder (global state) and prevents per-request configuration. However, 17+ files import the singleton in non-request contexts (background tasks, signal bridge, orchestrator) where `Request.app.state` is not available.

## Proposed Pattern: `get_service()` Provider

```python
# backend/src/services/github_projects/provider.py

_instance: GitHubProjectsService | None = None

def get_service() -> GitHubProjectsService:
    """Return the shared service instance."""
    global _instance
    if _instance is None:
        _instance = GitHubProjectsService()
    return _instance

def set_service(service: GitHubProjectsService) -> None:
    """Override the service instance (for testing)."""
    global _instance
    _instance = service
```

## Migration Checklist

### Request-context consumers (use FastAPI Depends)
- [ ] `backend/src/api/board.py` (4 refs)
- [ ] `backend/src/api/chat.py` (4 refs)
- [ ] `backend/src/api/projects.py` (8 refs)
- [ ] `backend/src/api/tasks.py` (3 refs)
- [ ] `backend/src/api/workflow.py` (3 refs)
- [ ] `backend/src/api/webhooks.py` (6 refs)
- [ ] `backend/src/api/agents.py` (via service refs)
- [ ] `backend/src/api/cleanup.py` (via service refs)

### Non-request-context consumers (use get_service())
- [ ] `backend/src/services/copilot_polling/agent_output.py`
- [ ] `backend/src/services/copilot_polling/pipeline.py`
- [ ] `backend/src/services/copilot_polling/recovery.py`
- [ ] `backend/src/services/copilot_polling/polling_loop.py`
- [ ] `backend/src/services/copilot_polling/helpers.py`
- [ ] `backend/src/services/copilot_polling/state_validation.py`
- [ ] `backend/src/services/copilot_polling/completion.py`
- [ ] `backend/src/services/workflow_orchestrator/orchestrator.py`
- [ ] `backend/src/services/chores/service.py`
- [ ] `backend/src/services/signal_bridge.py`

### Test updates
- [ ] Update all test fixtures to use `set_service()` for mocking

## Risks

- Large blast radius (25+ files)
- Background tasks need a reliable way to access the service without FastAPI request context
- Must maintain backward compatibility during migration (keep old import working)

## Recommendation

Implement as a separate spec with phased rollout — migrate request-context consumers first (using `Depends`), then non-request consumers (using `get_service()`).
