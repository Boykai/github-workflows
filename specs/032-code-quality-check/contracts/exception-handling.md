# Contract: Exception Handling Standards

**Phase**: 1 — Critical: Fix Silent Failures & Security
**Applies to**: All files in `backend/src/`

## Exception Handler Contract

### Standard Pattern: Log and Propagate

```python
# BEFORE (non-compliant)
try:
    result = await some_operation()
except Exception:
    pass

# AFTER (compliant)
try:
    result = await some_operation()
except httpx.HTTPStatusError as exc:
    logger.error("Failed to fetch resource: %s", exc)
    raise
except KeyError as exc:
    logger.warning("Missing expected key: %s", exc)
    raise ValidationError("Required data not found") from exc
```

### Standard Pattern: Safe External Response

```python
# BEFORE (non-compliant — leaks details)
except Exception as exc:
    await _reply(phone, f"Error: {exc}")

# AFTER (compliant — generic response, detailed logging)
from src.logging_utils import safe_error_response

except Exception as exc:
    safe_msg = safe_error_response(exc, "process agent command")
    await _reply(phone, f"⚠️ {safe_msg}")
```

### Standard Pattern: Service Error Handling in API Routes

```python
# BEFORE (non-compliant — ad-hoc try/log/raise)
try:
    result = await service.do_something(...)
except Exception as e:
    logger.error("Failed: %s", e)
    raise HTTPException(status_code=500, detail=str(e))

# AFTER (compliant — use centralized helper)
from src.logging_utils import handle_service_error

try:
    result = await service.do_something(...)
except httpx.HTTPStatusError as exc:
    handle_service_error(exc, "fetch project data")
except ValidationError as exc:
    handle_service_error(exc, "validate input", error_cls=ValidationError)
```

## CORS Configuration Contract

```python
# BEFORE (non-compliant)
app.add_middleware(
    CORSMiddleware,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AFTER (compliant)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],  # Retained — header enumeration deferred
)
```

## Exception Type Narrowing Guide

| Broad Catch | Narrow To | Context |
|-------------|-----------|---------|
| `except Exception` (GitHub API calls) | `except httpx.HTTPStatusError` | HTTP status errors from GitHub API |
| `except Exception` (JSON parsing) | `except (KeyError, ValueError, TypeError)` | Malformed response data |
| `except Exception` (DB operations) | `except aiosqlite.Error` | Database operation failures |
| `except Exception` (config loading) | `except (KeyError, ValueError, FileNotFoundError)` | Configuration resolution |
| `except Exception` (encryption) | `except cryptography.fernet.InvalidToken` | Token decryption failures |
| `except Exception` (websocket) | `except (ConnectionError, asyncio.TimeoutError)` | WebSocket communication |

## Fallback Pattern

When the specific exception set is not fully determinable, use a logged fallback:

```python
try:
    result = await operation()
except SpecificError as exc:
    logger.error("Known failure in operation: %s", exc)
    handle_specific_recovery(exc)
except Exception as exc:
    logger.warning("Unexpected error in operation: %s", exc, exc_info=True)
    raise  # Surface unexpected errors rather than silently swallowing
```

## Compliance Criteria

- [ ] Zero `except: pass` blocks remain
- [ ] All `except Exception` blocks either narrowed to specific types or have a logged fallback with `as exc`
- [ ] All external-facing error responses use `safe_error_response()`
- [ ] All API route error handlers use `handle_service_error()` or `safe_error_response()`
- [ ] CORS `allow_methods` lists explicit HTTP methods
