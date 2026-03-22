"""Centralized logging utilities — sanitization, structured formatting, and helpers.

This module provides:

- **Sensitive-data redaction**: A configurable list of regex patterns that scrub
  tokens, API keys, PII, and internal file paths from every log message before
  it reaches any sink.
- **SanitizingFormatter**: A :class:`logging.Formatter` subclass that applies
  redaction to every log record.
- **StructuredJsonFormatter**: A :class:`logging.Formatter` subclass that emits
  JSON-structured log entries for production log aggregation.
- **RequestIDFilter**: A :class:`logging.Filter` that injects the current
  request ID (from :data:`src.middleware.request_id.request_id_var`) into every
  log record.
- **get_logger(name)**: The standard way for modules to obtain a pre-configured
  logger instance.
- **handle_service_error(exc, operation, error_cls)**: Shared helper that logs
  the exception and raises the appropriate :class:`AppException` subclass with
  a safe message and no leaked internals.

Usage::

    from src.logging_utils import get_logger, handle_service_error

    logger = get_logger(__name__)

    try:
        ...
    except Exception as e:
        handle_service_error(e, "fetch board projects", GitHubAPIError)
"""

from __future__ import annotations

import functools
import json
import logging
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, NoReturn, TypeVar

if TYPE_CHECKING:
    from src.exceptions import AppException

_F = TypeVar("_F", bound=Callable[..., Awaitable[Any]])

# ---------------------------------------------------------------------------
# Sensitive-data redaction patterns
# ---------------------------------------------------------------------------

#: Maximum log message length.  Messages exceeding this limit are truncated.
MAX_LOG_MESSAGE_LENGTH = 10_000

#: Compiled redaction patterns — each tuple is ``(compiled_regex, replacement)``.
#: Patterns are applied in order; first match wins for overlapping regions.
_REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = []


def _compile_patterns() -> list[tuple[re.Pattern[str], str]]:
    """Build and compile redaction patterns.

    Patterns cover:
    - GitHub tokens (ghp_, gho_, ghs_, github_pat_)
    - Bearer / Basic auth headers
    - Generic API key / secret / password / token key-value pairs
    - Email addresses (simple PII pattern)
    - Internal absolute file paths (Unix and Windows)
    """
    raw: list[tuple[str, str]] = [
        # GitHub fine-grained / classic PATs and app tokens
        (r"(ghp_|gho_|ghs_|github_pat_)[A-Za-z0-9_]{10,}", "[REDACTED_GITHUB_TOKEN]"),
        # Bearer tokens
        (r"(?i)(Bearer\s+)[^\s,;\"']+", r"\1[REDACTED]"),
        # Basic auth
        (r"(?i)(Basic\s+)[^\s,;\"']+", r"\1[REDACTED]"),
        # Key-value patterns: api_key=xxx, secret=xxx, password=xxx, token=xxx
        (
            r"(?i)((?:api[_-]?key|secret|password|passwd|token|credential|authorization)"
            r"[\s]*[=:]\s*)[^\s,;\"\'}{)(\]\[]+",
            r"\1[REDACTED]",
        ),
        # Email addresses
        (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]"),
        # Internal Unix absolute paths (e.g. /home/user/..., /app/src/...)
        (r"(?<!\w)/(?:home|app|usr|var|tmp|opt|etc)/[^\s:,;\"']+", "[REDACTED_PATH]"),
        # Windows absolute paths (e.g. C:\Users\...)
        (r"[A-Z]:\\(?:Users|Windows|Program Files)[^\s:,;\"']*", "[REDACTED_PATH]"),
    ]
    return [(re.compile(pattern), repl) for pattern, repl in raw]


_REDACTION_PATTERNS = _compile_patterns()


def redact(message: str) -> str:
    """Scrub sensitive data from *message* using the configured pattern list.

    The function also truncates messages that exceed
    :data:`MAX_LOG_MESSAGE_LENGTH` to prevent log-storage exhaustion.
    """
    try:
        for pattern, replacement in _REDACTION_PATTERNS:
            message = pattern.sub(replacement, message)
        if len(message) > MAX_LOG_MESSAGE_LENGTH:
            message = message[:MAX_LOG_MESSAGE_LENGTH] + "... [TRUNCATED]"
    except Exception:
        # Resilience: never let sanitization crash the caller.
        message = "[REDACTION_ERROR] <message could not be sanitized>"
    return message


# ---------------------------------------------------------------------------
# Logging formatters & filters
# ---------------------------------------------------------------------------


class SanitizingFormatter(logging.Formatter):
    """Formatter that applies :func:`redact` to every log record message.

    This formatter wraps another formatter (or uses a default format) and
    ensures that *all* log output passes through the sanitization layer —
    regardless of which module emitted the record.
    """

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, **kwargs: Any) -> None:
        super().__init__(fmt, datefmt, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        try:
            formatted = super().format(record)
            return redact(formatted)
        except Exception:
            # Resilience: fall back to a minimal safe representation.
            return redact(f"{record.levelname} {record.name}: {record.getMessage()}")


class StructuredJsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects.

    Each JSON entry contains:
    - ``timestamp`` — ISO-8601 UTC timestamp
    - ``level`` — severity level name
    - ``message`` — the (already sanitized) log message
    - ``logger`` — logger name
    - ``request_id`` — correlation ID (injected by :class:`RequestIDFilter`)
    """

    def format(self, record: logging.LogRecord) -> str:
        try:
            message = record.getMessage()
            message = redact(message)

            entry: dict[str, object] = {
                "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                "level": record.levelname,
                "message": message,
                "logger": record.name,
                "request_id": getattr(record, "request_id", ""),
                "module": record.module,
            }

            # Include structured extra fields from extra={} kwargs
            for key in ("operation", "duration_ms", "error_type", "status_code"):
                val = getattr(record, key, None)
                if val is not None:
                    entry[key] = val

            # Include exception info if present
            if record.exc_info and record.exc_info[1] is not None:
                entry["exception"] = redact(self.formatException(record.exc_info))

            return json.dumps(entry, default=str)
        except Exception:
            # Resilience: never crash; emit a minimal JSON fallback.
            return json.dumps(
                {
                    "timestamp": datetime.now(tz=UTC).isoformat(),
                    "level": "ERROR",
                    "message": "[FORMATTER_ERROR] Failed to format log record",
                    "logger": "logging_utils",
                }
            )


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record.

    The request ID is read from
    :data:`src.middleware.request_id.request_id_var`.  Outside a request
    context the field defaults to ``""``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from src.middleware.request_id import request_id_var

            record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        except Exception:
            record.request_id = ""  # type: ignore[attr-defined]
        return True


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Return a logger instance for *name*.

    This is the standard way for all modules to obtain a logger.  The
    returned logger inherits the root configuration set up by
    :func:`src.config.setup_logging`.
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Error-handling helpers
# ---------------------------------------------------------------------------


def handle_service_error(
    exc: Exception,
    operation: str,
    error_cls: type[Exception] | None = None,
) -> NoReturn:
    """Log the exception and raise a structured exception with a safe message.

    This helper centralises the repeated pattern of:

    1. Logging the full exception context server-side.
    2. Raising a structured application exception with a generic message
       that does not leak internal details.

    Args:
        exc: The caught exception.
        operation: Human-readable description of the failed operation.
        error_cls: The exception class to raise.  Defaults to
            :class:`src.exceptions.GitHubAPIError` if not provided.
            Supports both :class:`AppException` subclasses (constructed
            with ``message=``) and plain exception types such as
            ``ValueError`` (constructed with a positional argument).

    Raises:
        Exception: Always raised (the specific subclass is *error_cls*).
    """
    from src.exceptions import GitHubAPIError

    if error_cls is None:
        error_cls = GitHubAPIError

    logger = logging.getLogger("error_handler")
    logger.error(
        "Operation '%s' failed: %s",
        operation,
        exc,
        exc_info=True,
    )

    msg = f"Failed to {operation}"
    from src.exceptions import AppException

    if issubclass(error_cls, AppException):
        raise error_cls(message=msg) from exc
    raise error_cls(msg) from exc


def handle_github_errors(
    operation: str,
    error_cls: type[AppException] | None = None,
) -> Callable[[_F], _F]:
    """Decorator that catches exceptions and raises a structured :class:`AppException`.

    Wraps an ``async`` endpoint or service function so that unhandled
    exceptions are logged with full context and re-raised as a safe
    :class:`AppException` subclass — preventing internal details from
    leaking to callers.

    Args:
        operation: Human-readable description of the operation (used in
            log messages and the raised exception message).
        error_cls: The :class:`AppException` subclass to raise.  Defaults
            to :class:`src.exceptions.GitHubAPIError`.

    Usage::

        @handle_github_errors("fetch board data")
        async def get_board(request: Request, ...):
            ...
    """

    def decorator(fn: _F) -> _F:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await fn(*args, **kwargs)
            except Exception as exc:
                from src.exceptions import AppException as _AppException

                # Don't double-wrap application exceptions
                if isinstance(exc, _AppException):
                    raise
                handle_service_error(exc, operation, error_cls)

        return wrapper  # type: ignore[return-value]

    return decorator
