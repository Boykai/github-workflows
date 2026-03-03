"""Centralized logging utilities for sanitization, structured formatting, and DRY error handling.

This module provides:
- **Sensitive-data redaction**: The :func:`redact` function scrubs tokens, API keys, PII,
  credentials, and internal file paths from arbitrary strings before they reach any log sink.
- **SanitizingFormatter**: A :class:`logging.Formatter` subclass that automatically applies
  :func:`redact` to every log record message.
- **StructuredJsonFormatter**: A :class:`logging.Formatter` subclass that emits log records
  as single-line JSON objects (timestamp, level, message, logger, request_id, context).
- **RequestIDFilter**: A :class:`logging.Filter` that injects the current
  ``request_id`` from the :mod:`src.middleware.request_id` ``ContextVar`` into every log record.
- **get_logger(name)**: The standard way for all modules to obtain a pre-configured logger.
- **safe_error_response(logger, msg, exc)**: Logs detailed error info server-side and returns
  a generic user-safe message string.
- **handle_service_error(logger, operation, exc, status_code, exc_class)**: Shared pattern
  for "log exception + raise safe AppException".

Usage::

    from src.logging_utils import get_logger, safe_error_response, handle_service_error

    logger = get_logger(__name__)

    # In an except block:
    safe_msg = safe_error_response(logger, "Failed to fetch data", exc)

    # Or raise directly:
    handle_service_error(logger, "fetch board data", exc)
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import re
import sys
import traceback
from typing import Any

# ---------------------------------------------------------------------------
# Sensitive-data redaction patterns
# ---------------------------------------------------------------------------

_PLACEHOLDER = "[REDACTED]"

#: Maximum log message length (characters).  Messages exceeding this limit
#: are truncated with a ``[TRUNCATED]`` suffix.
MAX_LOG_MESSAGE_LENGTH = 10_000

#: Compiled patterns that match sensitive data in log messages.
#: Each tuple is (compiled_regex, replacement_string).
_SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = []


def _compile_patterns() -> list[tuple[re.Pattern[str], str]]:
    """Build and compile the sensitive-data regex patterns."""
    raw: list[tuple[str, str]] = [
        # GitHub tokens (ghp_, gho_, ghs_, github_pat_)
        (r"(ghp_[A-Za-z0-9_]{1,255})", _PLACEHOLDER),
        (r"(gho_[A-Za-z0-9_]{1,255})", _PLACEHOLDER),
        (r"(ghs_[A-Za-z0-9_]{1,255})", _PLACEHOLDER),
        (r"(github_pat_[A-Za-z0-9_]{1,255})", _PLACEHOLDER),
        # Bearer / Basic auth headers
        (r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", r"\1" + _PLACEHOLDER),
        (r"(Basic\s+)[A-Za-z0-9+/]+=*", r"\1" + _PLACEHOLDER),
        # Generic API key patterns (key=..., api_key=..., apikey=...)
        (
            r"(?i)((?:api[_-]?key|secret|token|password|passwd|credential)[=:]\s*)[\S]+",
            r"\1" + _PLACEHOLDER,
        ),
        # Email addresses (PII)
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", _PLACEHOLDER),
        # Internal absolute file paths (Unix & Windows)
        (r"(/(?:home|root|Users|app|var|tmp|etc)/[^\s:\"']+)", _PLACEHOLDER),
        (r"([A-Z]:\\(?:Users|Windows|Program Files)[^\s:\"']*)", _PLACEHOLDER),
    ]
    return [(re.compile(pattern), repl) for pattern, repl in raw]


_SENSITIVE_PATTERNS = _compile_patterns()


def redact(text: str) -> str:
    """Scrub sensitive data from *text* using the configured pattern list.

    Returns the sanitized string.  If *text* exceeds :data:`MAX_LOG_MESSAGE_LENGTH`
    it is truncated **after** redaction.
    """
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    if len(text) > MAX_LOG_MESSAGE_LENGTH:
        text = text[:MAX_LOG_MESSAGE_LENGTH] + " [TRUNCATED]"
    return text


# ---------------------------------------------------------------------------
# Logging filter – request ID injection
# ---------------------------------------------------------------------------


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record.

    The request ID is read from the ``ContextVar`` defined in
    :mod:`src.middleware.request_id`.  Outside a request context the
    value defaults to ``""``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from src.middleware.request_id import request_id_var

            record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        except Exception:
            record.request_id = ""  # type: ignore[attr-defined]
        return True


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


class SanitizingFormatter(logging.Formatter):
    """Formatter that applies :func:`redact` to every log message.

    Wraps an inner formatter (or default) and sanitizes the final output.
    Falls back to ``stderr`` if the redaction/formatting layer itself fails
    so that the application never crashes due to a logging error.
    """

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, **kwargs: Any) -> None:
        super().__init__(fmt, datefmt, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        try:
            formatted = super().format(record)
            return redact(formatted)
        except Exception:
            # Resilience: never crash the app because of a formatting error.
            try:
                print(  # noqa: T201
                    f"[LOGGING FALLBACK] {record.levelname} {record.getMessage()}",
                    file=sys.stderr,
                )
            except Exception:
                pass
            return f"{record.levelname} {record.getMessage()}"


class StructuredJsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects.

    Fields: ``timestamp``, ``level``, ``message``, ``logger``, ``request_id``,
    and an optional ``context`` dict for extra metadata.
    """

    def format(self, record: logging.LogRecord) -> str:
        try:
            message = redact(record.getMessage())
            entry: dict[str, Any] = {
                "timestamp": _dt.datetime.fromtimestamp(record.created, tz=_dt.UTC).isoformat(),
                "level": record.levelname,
                "message": message,
                "logger": record.name,
                "request_id": getattr(record, "request_id", ""),
            }
            if record.exc_info and record.exc_info[1]:
                entry["exception"] = redact("".join(traceback.format_exception(*record.exc_info)))
            return json.dumps(entry, default=str)
        except Exception:
            try:
                print(  # noqa: T201
                    f"[LOGGING FALLBACK] {record.levelname} {record.getMessage()}",
                    file=sys.stderr,
                )
            except Exception:
                pass
            return json.dumps({"level": record.levelname, "message": record.getMessage()})


# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Return a logger pre-configured with the application's root settings.

    This is the standard way for all modules to obtain a logger::

        from src.logging_utils import get_logger
        logger = get_logger(__name__)

    The logger inherits the formatters, filters, and handlers attached by
    :func:`src.config.setup_logging`.
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# DRY error-handling helpers
# ---------------------------------------------------------------------------


def safe_error_response(
    logger: logging.Logger,
    message: str,
    exc: Exception,
) -> str:
    """Log detailed error info server-side and return a generic user-safe message.

    Args:
        logger: Logger instance for the calling module.
        message: Human-readable operation description (e.g. "Failed to fetch data").
        exc: The caught exception.

    Returns:
        The *message* string (safe for inclusion in an API response).
    """
    logger.error("%s: %s", message, exc, exc_info=True)
    return message


def handle_service_error(
    logger: logging.Logger,
    operation: str,
    exc: Exception,
    *,
    status_code: int = 502,
    exc_class: type | None = None,
) -> None:
    """Log an exception and raise a safe :class:`~src.exceptions.AppException`.

    This extracts the repeated "log + raise" pattern used across API modules.

    Args:
        logger: Logger instance for the calling module.
        operation: Short description of the failed operation.
        exc: The caught exception.
        status_code: HTTP status code for the raised exception (default 502).
        exc_class: Exception class to raise (default :class:`GitHubAPIError`).

    Raises:
        AppException (or *exc_class*) with a safe message.
    """
    from src.exceptions import GitHubAPIError

    logger.error("%s failed: %s", operation, exc, exc_info=True)
    cls = exc_class or GitHubAPIError
    raise cls(message=f"{operation} failed") from exc
