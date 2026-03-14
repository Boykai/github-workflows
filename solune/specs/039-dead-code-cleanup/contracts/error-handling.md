# Error Handling Contract

**Feature**: 039-dead-code-cleanup
**Date**: 2026-03-13
**Version**: 1.0

## Purpose

Defines the single coherent error handling pattern for all backend API endpoints. All error handlers in API layer code must follow this contract to ensure consistent logging, safe error messages, and predictable exception propagation.

## The Standard Pattern

All API endpoint error handlers MUST use `handle_service_error()` from `backend/src/logging_utils.py`:

```python
from src.logging_utils import handle_service_error
from src.exceptions import ValidationError  # or appropriate subclass

try:
    result = await some_service_operation(...)
except Exception as e:
    handle_service_error(e, "descriptive operation name", ValidationError)
```

### What `handle_service_error` Does

1. **Logs** the full exception with traceback at ERROR level (server-side only)
2. **Raises** the specified `AppException` subclass with a safe generic message
3. **Chains** the original exception via `from exc` for debugging

### What It Does NOT Do

- Does not return values — always raises (`NoReturn`)
- Does not suppress exceptions — always re-raises as structured error
- Does not send error details to the client — message is generic

## Error Class Selection

| Context | Error Class | HTTP Status |
|---------|------------|-------------|
| Invalid user input / missing fields | `ValidationError` | 422 |
| Resource not found | `NotFoundError` | 404 |
| Authentication failure | `AuthorizationError` | 401/403 |
| GitHub API failure | `GitHubAPIError` | 502 |
| General service failure | `AppException` | 500 |

## Exceptions to This Contract

The following patterns are intentionally different and MUST NOT be migrated:

### 1. Silent-Fail Patterns (Non-Fatal)

When a failure should not abort the request:

```python
try:
    is_feature_request = await detect_feature_request(...)
except Exception as e:
    logger.warning("Feature request detection failed: %s", e)
    is_feature_request = False  # Proceed with default
```

**Rule**: If the catch block sets a fallback value and continues processing, do NOT use `handle_service_error`.

### 2. Error-Response Patterns (Chat Endpoints)

When a failure produces a user-visible error message in the chat:

```python
except Exception as e:
    logger.error("AI pipeline failed: %s", e, exc_info=True)
    error_message = ChatMessage(
        sender=SenderType.SYSTEM,
        content=f"Sorry, I encountered an error: {str(e)}",
    )
    add_message(session_id, error_message)
    return error_message
```

**Rule**: If the catch block returns a ChatMessage error response, it is a domain-specific pattern. Consider extracting to a `_chat_error_response(e, operation)` helper for DRY within `chat.py`, but do NOT use `handle_service_error`.

### 3. WebSocket Handlers

WebSocket error handling has different semantics (connection lifecycle, message-level vs. connection-level errors):

**Rule**: WebSocket error handlers are exempt from this contract. They follow their own close/retry patterns.

### 4. Dual-Exception Handlers

When specific exceptions should propagate unchanged:

```python
except ValidationError:
    raise  # Re-raise validation errors as-is
except Exception as e:
    handle_service_error(e, "create issue from proposal", ValidationError)
```

**Rule**: When a specific `AppException` subclass should propagate without modification, use a bare `raise` before the generic `except Exception` clause.

## Migration Checklist

| File | Inline Catches | Direct Candidates | Skip (Intentional) |
|------|---------------|-------------------|---------------------|
| `chat.py` | 5 | 1 (L952) | 4 (L167 silent-fail, L249/389/437 error-response) |
| `projects.py` | 5 | 5 | 0 |
| `webhooks.py` | 4 | 4 | 0 |
| `signal.py` | 2 | 2 | 0 |
| `auth.py` | 1 | 1 | 0 |
| `chores.py` | 1 | 1 | 0 |
| **Total** | **18** | **14** | **4** |

## Verification

After migration:
- All `except Exception as e: logger.error(...)` patterns in targeted files are replaced
- All replaced handlers use `handle_service_error` with appropriate error class
- No behavioral change: same errors are raised, same messages are logged
- All existing tests pass without modification
