# Error Response Contract

**Feature**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-22

> This refactoring introduces no new API endpoints and changes no existing request/response contracts (FR-001). The only contract being formalized is the **error response structure**, which is currently inconsistent across endpoints.

## Standardized Error Response

All API endpoints MUST return errors in this format:

```json
{
  "error": "string — user-facing message (sanitized)",
  "details": "object | null — optional structured metadata"
}
```

### Response Schema

```yaml
ErrorResponse:
  type: object
  required:
    - error
  properties:
    error:
      type: string
      description: >
        Human-readable error message safe for display to end users.
        MUST NOT contain stack traces, exception class names, database details,
        or any internal implementation information.
    details:
      type: object
      nullable: true
      description: >
        Optional structured metadata providing additional context.
        Used primarily for validation errors (field-level details).
        MUST NOT contain stack traces or internal details.
```

### Status Code Mapping

All errors are mapped through the `AppException` hierarchy defined in `backend/src/exceptions.py`:

| HTTP Status | Exception Class | Default Message | When Used |
|-------------|----------------|-----------------|-----------|
| 400 | `ValidationError` | "Bad request" | Malformed request body/params |
| 401 | `AuthenticationError` | "Authentication required" | Missing/invalid session |
| 403 | `AuthorizationError` | "Access denied" | Insufficient permissions |
| 404 | `NotFoundError` | "Resource not found" | Entity does not exist |
| 422 | `ValidationError` | "Validation failed" | Business rule violation |
| 429 | `RateLimitError` | "Rate limit exceeded" | GitHub API rate limit hit |
| 502 | `GitHubAPIError` | "GitHub API error" | Upstream GitHub API failure |
| 500 | (unhandled `Exception`) | "Internal server error" | Unexpected failures |

### Error Handler Implementation

```python
# main.py — AppException handler
@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "details": exc.details},
    )

# main.py — Generic fallback handler
@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": None},
    )
```

### Security Requirements (FR-009)

- **NEVER** include stack traces in response bodies
- **NEVER** include exception class names in response bodies
- **NEVER** include database error details in response bodies
- **ALWAYS** log full diagnostic details server-side via `logger.error()`
- **ALWAYS** return sanitized, user-facing messages in the `error` field

### Migration from HTTPException

The following 9 `HTTPException` uses must be replaced:

| File | Current | Replacement |
|------|---------|-------------|
| `api/auth.py` | `HTTPException(400, "Missing code")` | `ValidationError("Missing authorization code")` |
| `api/auth.py` | `HTTPException(400, "Token exchange failed")` | `AuthenticationError("Token exchange failed")` |
| `api/auth.py` | `HTTPException(400, "Failed to get user")` | `AuthenticationError("Failed to retrieve user information")` |
| `api/webhooks.py` | `HTTPException(400, "Missing signature")` | `ValidationError("Missing webhook signature")` |
| `api/webhooks.py` | `HTTPException(401, "Invalid signature")` | `AuthenticationError("Invalid webhook signature")` |
| Other locations | Various `HTTPException` uses | Corresponding `AppException` subclass |

### Bare Exception Block Strategy

The 73 bare `except Exception` blocks across services will be addressed as follows:

| Context | Strategy |
|---------|----------|
| Non-critical checks (e.g., "is PR merged?") | Keep catch, add `logger.warning()`, return sentinel value |
| Operations that should surface failures (e.g., "create issue") | Re-raise as `GitHubAPIError` or appropriate `AppException` subclass |
| Truly unexpected errors | Let propagate to generic exception handler |
