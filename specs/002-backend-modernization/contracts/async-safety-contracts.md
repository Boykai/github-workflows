# Async Safety Contracts

**Feature**: 002-backend-modernization | **Date**: 2026-03-15

## Contract: Application Lifecycle (TaskGroup)

The application MUST use `asyncio.TaskGroup` for managing background tasks created during the lifespan context.

### Startup Behavior

```
Application Start (lifespan __aenter__)
  → Initialize database
  → async with asyncio.TaskGroup() as tg:
      tg.create_task(_session_cleanup_loop())
      tg.create_task(_polling_watchdog_loop())
      tg.create_task(start_signal_ws_listener())
      tg.create_task(_run_startup_agent_mcp_sync_background())
      yield  # Hold open during app lifetime
  → TaskGroup __aexit__ cancels and awaits all tasks
  → Close database
```

### Shutdown Behavior

```
Shutdown Signal (SIGTERM/SIGINT)
  → FastAPI lifespan exits the 'yield'
  → TaskGroup cancels all child tasks (CancelledError injected)
  → TaskGroup awaits all child tasks (up to event loop timeout)
  → Each task's CancelledError handler runs (cleanup, logging)
  → TaskGroup __aexit__ completes
  → Database connections closed
```

**Constraints**:
- Each background task MUST catch `asyncio.CancelledError` and perform cleanup
- Each background task MUST catch general `Exception` internally to prevent cross-task cancellation
- No "task was destroyed but it is pending" warnings may appear in logs after shutdown
- All tasks MUST complete or cancel within 30 seconds of shutdown signal

### Exception Handling

```
TaskGroup handles ExceptionGroup:
  → If a task raises an unhandled exception (not CancelledError):
    → All sibling tasks are cancelled
    → ExceptionGroup is raised from TaskGroup
    → Lifespan catches ExceptionGroup and logs individual exceptions
    → Application proceeds to shutdown (close DB, etc.)
```

## Contract: TaskRegistry

The application MUST track all fire-and-forget tasks via a central `TaskRegistry` singleton.

### Registration API

```python
from src.services.task_registry import task_registry

# Create and register a task
task = task_registry.create_task(
    some_coroutine(),
    name="signal-delivery-{message_id}"
)
# Returns: asyncio.Task (already started and registered)
```

**Constraints**:
- `create_task()` MUST accept any coroutine and an optional `name` parameter
- `create_task()` MUST register a done-callback that removes the task from the registry
- Tasks that raise exceptions MUST be logged at WARNING level with the task name and exception
- The registry MUST be safe for concurrent `create_task()` calls (async-safe, not thread-safe)

### Drain API

```python
# During shutdown
undrained = await task_registry.drain(timeout=30.0)
if undrained:
    logger.warning("Tasks did not complete within drain timeout: %s", undrained)
```

**Behavior**:
1. Gather all currently registered tasks
2. Await all tasks with `asyncio.wait(tasks, timeout=timeout)`
3. Cancel any tasks that exceed the timeout
4. Return list of tasks that were cancelled (undrained)
5. Log each undrained task's name at WARNING level

**Constraints**:
- `drain()` MUST NOT raise exceptions (fire-and-forget semantics)
- `drain()` MUST be called before database connections are closed
- `drain()` MUST be idempotent (safe to call multiple times)
- New tasks created during drain are tracked but not awaited by the in-progress drain

### Affected Call Sites

All `asyncio.create_task()` calls MUST be replaced with `task_registry.create_task()`:

| File | Current Call | Registry Name |
|------|-------------|---------------|
| `api/chat.py:681` | `asyncio.create_task(_deliver())` | `"signal-delivery-{session_id}"` |
| `api/signal.py` | `asyncio.create_task(_post_link())` | `"signal-post-link"` |
| `services/signal_bridge.py:667` | `asyncio.create_task(_safe_process())` | `"signal-ai-process-{source}"` |
| `services/signal_delivery.py:279` | `asyncio.create_task(_delivery_task(...))` | `"signal-send-{audit_id}"` |
| `services/copilot_polling/__init__.py:285` | `_aio.create_task(poll_for_copilot_completion(...))` | `"copilot-poll-{project_id}"` |
| `services/model_fetcher.py:323` | `asyncio.create_task(self._background_refresh(...))` | `"model-refresh-{cache_key}"` |
| `services/github_projects/service.py:328` | `asyncio.create_task(_execute_graphql())` | `"graphql-{cache_key}"` |
| `services/workflow_orchestrator/transitions.py` | `loop.create_task(coro)` | `"workflow-transition-{state}"` |
| `main.py:401` | `asyncio.create_task(_run_startup_agent_mcp_sync_background())` | `"startup-agent-mcp-sync"` |

**Post-migration**: Remove `"RUF006"` from the `ignore` list in `pyproject.toml` and verify zero violations with `ruff check --select=RUF006 src/`.

## Contract: External API Timeout

All external API calls MUST have a timeout guard preventing indefinite event loop blocking.

### GitHub GraphQL Calls

```python
# Before (no timeout)
data = await client.async_graphql(query, variables=variables)

# After (with timeout)
try:
    data = await asyncio.wait_for(
        client.async_graphql(query, variables=variables),
        timeout=settings.api_timeout_seconds  # default: 30
    )
except asyncio.TimeoutError:
    raise AppException(
        message=f"GitHub API request timed out after {settings.api_timeout_seconds}s",
        status_code=504
    )
```

**Constraints**:
- Default timeout: 30 seconds (configurable via `Settings.api_timeout_seconds`)
- `TimeoutError` MUST be caught and re-raised as a structured `AppException` (not silently swallowed)
- The timeout applies to the full GraphQL round-trip (auth, request, response parsing)
- Timeout MUST NOT break the in-flight request deduplication (BoundedDict cleanup still runs)

### Other External Calls

| Service | Call | Timeout |
|---------|------|---------|
| Model Fetcher | Model list fetch | 30s (same setting) |
| Copilot Polling | Completion status check | 30s |
| Signal Bridge | WebSocket connect | 30s (websockets library default) |

## Contract: WebSocket Reconnection

The Signal WebSocket listener MUST use exponential backoff for reconnection after failures.

### Reconnection Behavior

```
[WebSocket Connected]
  → Process messages normally
  → On connection close/error:
    → Log disconnection with reason
    → Calculate delay: min(base * 2^failures + jitter, cap)
      where base=1s, cap=300s, jitter=random(0, 1)
    → Sleep for delay
    → Attempt reconnect
    → On success: reset failures to 0, log reconnection
    → On failure: increment failures, loop
```

**Constraints**:
- Base delay: 1 second (first reconnection attempt)
- Maximum delay: 300 seconds (5 minutes)
- Jitter: Random float between 0 and 1 second (prevents thundering herd)
- Backoff MUST reset to base (1s) on successful connection
- `CancelledError` MUST propagate immediately (no reconnection on intentional shutdown)
- Each reconnection attempt MUST log the attempt number and calculated delay
- WebSocket MUST be explicitly closed in the `finally` block before reconnection
