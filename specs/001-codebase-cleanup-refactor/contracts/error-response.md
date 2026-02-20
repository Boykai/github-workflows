# API Contract: Unified Error Response

**Feature**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-20

> This refactoring does not change any API endpoint signatures, request formats, or success response shapes (FR-001). This contract documents the **standardized error response structure** that all endpoints must conform to after refactoring (FR-008, FR-009).

## Error Response Schema

All API error responses MUST conform to this structure:

```json
{
  "error": "string (required) — User-safe error message",
  "detail": "string (optional) — Additional context, never internal details",
  "status_code": "integer (required) — HTTP status code"
}
```

### Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error` | string | Yes | Sanitized, user-facing error message. Never includes stack traces, exception class names, or database details. |
| `detail` | string | No | Optional supplementary information. Must be safe for end-user consumption. |
| `status_code` | integer | Yes | HTTP status code matching the response status. |

### Excluded from Response (Server-Side Only)

The following MUST be logged server-side but NEVER returned in the response body:

- Stack traces
- Exception class names (e.g., `ValueError`, `KeyError`)
- Database query details
- Internal file paths
- Third-party API keys or tokens
- Raw exception messages from dependencies

## Exception-to-Response Mapping

| Exception Class | HTTP Status | Default Error Message |
|----------------|-------------|----------------------|
| `AuthenticationError` | 401 | "Authentication required" |
| `AuthorizationError` | 403 | "Access denied" |
| `NotFoundError` | 404 | "Resource not found" |
| `ValidationError` | 422 | (custom per-field message) |
| `RateLimitError` | 429 | "Rate limit exceeded" |
| `GitHubAPIError` | 502 | (custom message from GitHub) |
| `AppException` (base) | 500 | (custom message) |
| `Exception` (catch-all) | 500 | "Internal server error" |

## Implementation Mechanism

```python
# In main.py — existing handler (enhanced)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )

# New catch-all handler for unexpected exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )
```

## Unchanged Contracts

The following are **NOT changed** by this refactoring:

- All endpoint paths (e.g., `/api/v1/projects`, `/api/v1/chat/messages`)
- All request body schemas
- All success response schemas
- All query parameter formats
- Authentication mechanism (cookie-based sessions)
- WebSocket message formats
