# Contract: Structured Logging

**Branch**: `033-code-quality-overhaul` | **Phase**: Cross-cutting (FR-027, FR-028)

## Purpose

Standardize all backend logging to structured JSON format using the existing `StructuredJsonFormatter` from `logging_utils.py`.

## Configuration Contract

```python
# In main.py lifespan or logging_utils.py setup function:
def configure_structured_logging(level: str = "INFO") -> None:
    """Configure root logger with structured JSON output.

    Sets StructuredJsonFormatter as the handler for all loggers.
    Adds RequestIDFilter for correlation context.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level))

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(RequestIDFilter())

    root.handlers.clear()
    root.addHandler(handler)
```

## Log Entry Schema

Every log entry MUST produce valid JSON with these fields:

| Field | Type | Required | Source |
|-------|------|----------|--------|
| `timestamp` | string (ISO 8601) | YES | Formatter |
| `level` | string | YES | Formatter |
| `message` | string | YES | Logger call |
| `logger` | string | YES | `%(name)s` |
| `request_id` | string | CONDITIONAL | RequestIDFilter (present during request handling) |
| `module` | string | YES | `%(module)s` |

Additional fields via `extra={}`:

| Field | Type | When |
|-------|------|------|
| `operation` | string | Service-layer operations (e.g., "create_issue") |
| `duration_ms` | float | Timed operations |
| `error_type` | string | Exception handling |
| `status_code` | int | API responses |

## Migration Rules

1. **Replace `print()` calls**: Zero `print()` statements found in production code (confirmed by research). Only string literals containing "print" exist.
2. **Replace bare `logger.info("message")`**: Add `extra={}` where operation context is available. Bare string messages are acceptable for simple status logs.
3. **Import convention**: All files SHOULD use `from src.logging_utils import get_logger` and `logger = get_logger(__name__)`. Files using bare `import logging` / `logging.getLogger(__name__)` will still work (the root handler formats all log output) but the convention is preferred for consistency.

## Invariants

- The root logger handler MUST be `StructuredJsonFormatter` — no file writes `logging.basicConfig()` or adds its own handler
- `SanitizingFormatter` MUST remain active (it's composed into `StructuredJsonFormatter`) — secrets/tokens are never logged
- Test output MUST remain human-readable — tests can override the formatter via pytest's `caplog` fixture (pytest already captures log records, not formatted output)
