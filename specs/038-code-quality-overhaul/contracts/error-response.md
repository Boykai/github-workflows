# Contract: Standardized Error Response

**Feature**: 038-code-quality-overhaul | **Status**: Draft

## Purpose

Define the unified error response shape returned by all API endpoints. Currently, 13 of 17 API files use inline `try/except` blocks with ad-hoc error formatting. After consolidation, all errors flow through `handle_service_error()` and the global `AppException` handler, producing this consistent shape.

## Response Schema

### Error Response (HTTP 4xx/5xx)

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Repository not found: owner/repo",
    "request_id": "abc123-def456-...",
    "details": {}
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `error.code` | string | Yes | Machine-readable error code from `AppException` subclass name (e.g., `NOT_FOUND`, `VALIDATION_ERROR`, `RATE_LIMIT_EXCEEDED`) |
| `error.message` | string | Yes | Human-readable error description. No internal details in production. |
| `error.request_id` | string | Yes | Correlation ID from `X-Request-ID` header (set by `RequestIDMiddleware`) |
| `error.details` | object | No | Optional structured data (validation field errors, retry-after seconds, etc.) |

### Error Codes (mapped from `exceptions.py`)

| Exception Class | HTTP Status | Error Code |
|-----------------|-------------|------------|
| `AuthenticationError` | 401 | `AUTHENTICATION_ERROR` |
| `NotFoundError` | 404 | `NOT_FOUND` |
| `ValidationError` | 422 | `VALIDATION_ERROR` |
| `GitHubAPIError` | 502 | `GITHUB_API_ERROR` |
| `RateLimitError` | 429 | `RATE_LIMIT_EXCEEDED` |
| `ConflictError` | 409 | `CONFLICT` |
| `McpError` | 502 | `MCP_ERROR` |
| `DatabaseError` | 500 | `DATABASE_ERROR` |
| `ServiceUnavailableError` | 503 | `SERVICE_UNAVAILABLE` |
| `ConfigurationError` | 500 | `CONFIGURATION_ERROR` |
| Unhandled `Exception` | 500 | `INTERNAL_ERROR` |

### Response Headers

| Header | Value | Source |
|--------|-------|--------|
| `X-Request-ID` | UUID string | `RequestIDMiddleware` (already implemented) |
| `Content-Type` | `application/json` | FastAPI default |

## Existing Implementation

The global handler in `main.py` already returns this shape for `AppException` subclasses:

```python
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.error_code, "message": str(exc), "request_id": get_request_id()}},
    )
```

The work is extending coverage: replacing 100+ inline `try/except` blocks with calls to `handle_service_error()` which raises the appropriate `AppException` subclass.

## Frontend Error Reporting Endpoint

### `POST /api/v1/errors`

Receives frontend JavaScript errors for server-side logging.

**Request Body**:
```json
{
  "message": "TypeError: Cannot read properties of undefined",
  "stack": "at ChatPanel.render (ChatPanel.tsx:42)...",
  "url": "/projects/123/chat",
  "timestamp": "2026-03-12T10:30:00Z",
  "user_agent": "Mozilla/5.0..."
}
```

**Response**: `204 No Content` (fire-and-forget)

**Constraints**:
- Rate limited: 10 requests/minute per session
- Max `message` length: 2,000 characters
- Max `stack` length: 10,000 characters
- No persistence — logged at ERROR level, then discarded
- No authentication required (errors can occur pre-auth)
