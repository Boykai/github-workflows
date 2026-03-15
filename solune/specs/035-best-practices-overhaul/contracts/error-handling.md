# Contract: Error Handling Consolidation

**Feature**: `035-best-practices-overhaul` | **Phase**: 3 — DRY & Error Handling
**Applies to**: All `backend/src/api/*.py` endpoint files

## Purpose

Replace all bare `except Exception` blocks with the existing error infrastructure (`handle_service_error()`, `@handle_github_errors` decorator) and add specific exception types.

## Existing Infrastructure

### `handle_service_error()` — Direct Call

```python
# Location: backend/src/logging_utils.py

def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[AppException] | None = None,
) -> NoReturn:
    """Log exception and raise structured AppException."""
```

**Usage**: Inside `try/except` blocks where you need fine-grained control:
```python
try:
    result = await service.do_something()
except httpx.HTTPStatusError as exc:
    handle_service_error(exc, "fetch project data", GitHubAPIError)
```

### `@handle_github_errors` — Decorator

```python
# Location: backend/src/logging_utils.py

def handle_github_errors(
    operation: str,
    error_cls: type[AppException] | None = None,
) -> Callable:
    """Decorator — catches exceptions and raises structured AppException."""
```

**Usage**: Wraps entire endpoint functions:
```python
@router.get("/projects")
@handle_github_errors("list projects")
async def list_projects(request: Request, ...):
    ...  # No try/except needed — decorator handles it
```

## Transformation Rules

### Rule 1: Bare `except Exception` → Specific Type + `handle_service_error`

**Before**:
```python
try:
    owner, repo = await resolve_repository(token, project_id)
except Exception as exc:
    raise ValidationError(f"Could not resolve repository: {exc}")
```

**After**:
```python
try:
    owner, repo = await resolve_repository(token, project_id)
except AppException:
    raise  # Don't wrap application exceptions
except Exception as exc:
    handle_service_error(exc, "resolve repository", ValidationError)
```

### Rule 2: Endpoint-Level Catch-All → Decorator

**Before**:
```python
@router.post("/agents/assign")
async def assign_agent(request: Request, ...):
    try:
        ...  # entire function body
    except Exception as e:
        logger.error("Failed to assign agent: %s", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
```

**After**:
```python
@router.post("/agents/assign")
@handle_github_errors("assign agent")
async def assign_agent(request: Request, ...):
    ...  # No try/except needed
```

### Rule 3: Health Check Exception → Specific Type

**Before**:
```python
except Exception as exc:
    return {"status": "fail", "error": str(exc)}
```

**After**:
```python
except aiosqlite.Error as exc:
    logger.error("Database health check failed", exc_info=True)
    return {"status": "fail", "error": "database connectivity"}
except Exception as exc:
    logger.error("Health check failed", exc_info=True)
    return {"status": "fail", "error": "unexpected error"}
```

## Target Files and Counts

| File | Current Bare Catches | Target |
|------|---------------------|--------|
| `api/agents.py` | ~8 | 0 bare catches |
| `api/workflow.py` | ~6 | 0 bare catches |
| `api/health.py` | ~3 | 0 bare catches (use specific DB exception types) |
| `api/chat.py` | ~2 | 0 bare catches |
| `api/projects.py` | ~2 | 0 bare catches |
| `api/settings.py` | ~1 | 0 bare catches |
| `api/webhooks.py` | ~1 | 0 bare catches |
| Other API files | Variable | 0 bare catches |

## Exception Type Hierarchy

```text
AppException (base)
├── GitHubAPIError      — GitHub API call failures
├── ValidationError     — Input validation failures
├── DatabaseError       — SQLite/persistence failures
├── AuthenticationError — Auth/session failures
└── NotFoundError       — Resource not found
```

All exception types are defined in `backend/src/exceptions.py`.

## Verification

After consolidation:
- `grep -r "except Exception" backend/src/api/` should return 0 results (excluding intentional resilience patterns documented with `# noqa` comments).
- All caught exceptions log with `exc_info=True`.
- No exception handler silently discards errors.
