# Contract: Fallback Helper

**Module**: `backend/src/services/github_projects/service.py`
**Type**: Internal async method on `GitHubProjectsService`

---

## Purpose

Generic async helper that executes a primary operation, catches failures, and transparently falls back to an alternative operation. Replaces repeated try/except fallback chains throughout the service.

## Interface

```python
async def _with_fallback(
    self,
    primary_fn: Callable[[], Awaitable[T]],
    fallback_fn: Callable[[], Awaitable[T]],
    context_msg: str,
) -> T:
    """Execute primary_fn; on failure, log and execute fallback_fn.
    
    Args:
        primary_fn: Zero-arg async callable for the primary strategy.
        fallback_fn: Zero-arg async callable for the fallback strategy.
        context_msg: Human-readable context for log messages
                     (e.g., "assign copilot to issue #42").
    
    Returns:
        Result of whichever function succeeds.
    
    Raises:
        Exception: If both primary and fallback fail, raises the fallback
                   exception with the primary exception context logged.
    """
    ...
```

## Consumers

| Operation | Primary | Fallback | Context |
|-----------|---------|----------|---------|
| Assign Copilot | `_assign_copilot_graphql()` | `_assign_copilot_rest()` | `"assign copilot to issue"` |
| Request Review | `_request_copilot_review_rest()` | `_request_copilot_review_graphql()` | `"request copilot review"` |
| Add to Project | `_add_issue_to_project_graphql()` | `_add_issue_to_project_rest()` | `"add issue to project"` |

## Behavioral Contract

- **Primary first**: Always attempts `primary_fn` first
- **Logging**: On primary failure, logs at WARNING: `"{context_msg}: primary failed ({error}), trying fallback"`
- **Fallback propagation**: If fallback succeeds, returns its result; if fallback fails, raises with both error contexts
- **Type safety**: Generic over return type `T` — caller determines the expected type
- **No retry**: The helper does NOT retry — retry logic is handled by `_request_with_retry()` within each strategy function

## Error Behavior

```python
# Pseudocode
try:
    return await primary_fn()
except Exception as primary_err:
    logger.warning("%s: primary failed (%s), trying fallback", context_msg, primary_err)
    try:
        return await fallback_fn()
    except Exception as fallback_err:
        logger.error("%s: fallback also failed (%s)", context_msg, fallback_err)
        raise fallback_err from primary_err
```
