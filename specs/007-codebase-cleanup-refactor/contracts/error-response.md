# Error Response Contract

**Feature**: `007-codebase-cleanup-refactor` | **Date**: 2026-02-19

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
        Optional structured metadata. Used for validation errors (field-level
        details) or rate limiting (retry-after hints). MUST NOT contain internal
        diagnostic information. Null when no additional context is needed.
```

### Status Code Mapping

| HTTP Status | Error Type | `error` field value | `details` field |
|-------------|-----------|-------------------|-----------------|
| 400 | Bad Request | Contextual message from `ValidationError` | Optional field errors |
| 401 | Authentication Required | `"Authentication required"` | `null` |
| 403 | Access Denied | `"Access denied"` | `null` |
| 404 | Not Found | `"Resource not found"` or contextual | `null` |
| 422 | Validation Error | `"Validation failed"` | `{"fields": {...}}` |
| 429 | Rate Limit Exceeded | `"Rate limit exceeded"` | `{"retry_after": seconds}` |
| 502 | Upstream Error | `"GitHub API error"` or `"External service error"` | `null` |
| 500 | Internal Error | `"Internal server error"` | `null` |

### Security Requirements

1. **No stack traces** in any error response body, regardless of environment
2. **No exception class names** (e.g., `"KeyError"`, `"AttributeError"`)
3. **No database information** (table names, query details, connection strings)
4. **No file paths** or line numbers
5. Full diagnostic details MUST be logged server-side via `logger.error()` with `traceback.format_exc()`

### Implementation Notes

The error handlers in `main.py` already handle `AppException` and generic `Exception`. Changes:
- `AppException` handler: returns `{"error": exc.detail, "details": exc.details}` (already correct)
- Generic `Exception` handler: returns `{"error": "Internal server error", "details": null}` (already correct for response; needs enhanced server-side logging)
- All `HTTPException` raises replaced with `AppException` subclasses to ensure consistent routing through the same handler

## Existing API Contracts (Unchanged)

All existing endpoint signatures, request bodies, response shapes, query parameters, and authentication mechanisms remain identical. The following API groups are in scope for error handling standardization only:

- `/auth/*` — OAuth flow, session management
- `/projects/*` — Project CRUD
- `/board/*` — Board data retrieval
- `/tasks/*` — Task CRUD
- `/chat/*` — Chat messages, proposals
- `/workflow/*` — Workflow configuration, polling control
- `/settings/*` — Settings CRUD
- `/webhooks/*` — GitHub webhook handler

No contract changes are made to successful (2xx) responses.
