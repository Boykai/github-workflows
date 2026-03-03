"""Centralized logging utility with sanitization, structured formatting, and request-ID injection.

This module provides:

* **Sensitive-data redaction** — A configurable set of regex patterns that automatically
  scrub tokens, API keys, PII, credentials, and internal file paths from every log
  message before it reaches any log sink.

* **SanitizingFormatter** — A ``logging.Formatter`` subclass that applies the redaction
  function to every log record.  It is *always* attached to the root logger so that
  no sensitive data can leak regardless of output mode.

* **StructuredJsonFormatter** — A ``logging.Formatter`` subclass that emits each log
  record as a single-line JSON object with standard fields (``timestamp``, ``level``,
  ``message``, ``logger``, ``request_id``, and optional context).  Intended for
  production environments where log aggregation tools ingest machine-parseable output.

* **RequestIDFilter** — A ``logging.Filter`` that reads the current request ID from
  the ``ContextVar`` in ``src.middleware.request_id`` and injects it into every log
  record so that both human-readable and structured formatters can include it.

* **get_logger(name)** — The standard way for all modules to obtain a logger.  Returns
  a ``logging.Logger`` pre-configured with the module name.

* **safe_error_response(logger, exc, operation, static_msg)** — Logs detailed error
  context server-side and returns a generic user-safe message string.

* **handle_service_error(exc, operation, status_code, logger)** — A shared helper
  that logs the exception with context and raises the appropriate ``AppException``.

Usage::

    from src.logging_utils import get_logger
    logger = get_logger(__name__)
"""

from __future__ import annotations

import json
import logging
import re
import sys
import traceback
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.exceptions import AppException

# Maximum length for a single log message before truncation.
MAX_LOG_MESSAGE_LENGTH = 10_000

# Placeholder used to replace sensitive data in log output.
REDACTED = "[REDACTED]"

# ---------------------------------------------------------------------------
# Sensitive-data redaction patterns
# ---------------------------------------------------------------------------
# Each entry is a compiled regex that matches a category of sensitive data.
# The patterns are applied *in order*; the first match wins for overlapping
# regions.  Add new patterns here — all formatters pick them up automatically.

SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    # GitHub tokens  (ghp_, gho_, ghs_, github_pat_)
    re.compile(r"\b(ghp_[A-Za-z0-9_]{36,})\b"),
    re.compile(r"\b(gho_[A-Za-z0-9_]{36,})\b"),
    re.compile(r"\b(ghs_[A-Za-z0-9_]{36,})\b"),
    re.compile(r"\b(github_pat_[A-Za-z0-9_]{22,})\b"),
    # Bearer / Basic auth headers
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"(Basic\s+)[A-Za-z0-9+/]+=*", re.IGNORECASE),
    # Generic API key patterns  (key=…, api_key=…, apikey=…, token=…, secret=…)
    re.compile(
        r"(?i)((?:api[_-]?key|token|secret|password|credential|auth)['\"]?\s*[:=]\s*['\"]?)"
        r"([A-Za-z0-9\-._~+/]{8,})",
    ),
    # Email addresses (PII)
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    # Internal absolute file paths (Unix & Windows)
    re.compile(r"(/(?:home|app|usr|var|etc|tmp|opt|root)/[^\s:\"']+)"),
    re.compile(r"([A-Z]:\\(?:Users|Windows|Program Files)[^\s:\"']+)"),
]


def redact(text: str) -> str:
    """Scrub sensitive data from *text* using :data:`SENSITIVE_PATTERNS`.

    Returns the redacted string.  If *text* is not a string it is returned
    unchanged (defensive — the caller should pass strings).
    """
    if not isinstance(text, str):
        return text
    result = text
    for pattern in SENSITIVE_PATTERNS:
        # For patterns with capturing groups that have a prefix to keep,
        # preserve the prefix and redact the secret part.
        if pattern.groups >= 2:
            result = pattern.sub(rf"\1{REDACTED}", result)
        else:
            result = pattern.sub(REDACTED, result)
    return result


def _truncate(text: str, max_length: int = MAX_LOG_MESSAGE_LENGTH) -> str:
    """Truncate *text* to *max_length*, appending an indicator if trimmed."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [truncated, total {len(text)} chars]"


# ---------------------------------------------------------------------------
# Logging filter: RequestIDFilter
# ---------------------------------------------------------------------------


class RequestIDFilter(logging.Filter):
    """Inject the current request ID from the ``ContextVar`` into every log record.

    The attribute ``request_id`` is added to the record so that formatters
    can include it via ``%(request_id)s``.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        from src.middleware.request_id import request_id_var

        record.request_id = request_id_var.get("")  # type: ignore[attr-defined]
        return True


# ---------------------------------------------------------------------------
# Logging formatters
# ---------------------------------------------------------------------------


class SanitizingFormatter(logging.Formatter):
    """Formatter that redacts sensitive data and truncates oversized messages.

    This formatter wraps another formatter (or a format string) and applies
    :func:`redact` + :func:`_truncate` to the final output.  It is designed
    to be the *outermost* formatter so that no sensitive data ever reaches
    the log sink.

    If formatting itself raises, the error is written to *stderr* and a
    safe fallback message is returned so the application never crashes due
    to a logging failure.
    """

    def format(self, record: logging.LogRecord) -> str:
        try:
            output = super().format(record)
            return _truncate(redact(output))
        except Exception:
            # Resilience: never crash the app because of a logging error.
            try:
                print(
                    f"[LOGGING ERROR] Failed to format log record: {traceback.format_exc()}",
                    file=sys.stderr,
                )
            except Exception:
                pass
            return f"{record.levelname}: {_truncate(redact(str(record.msg)))}"


class StructuredJsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects.

    Fields: ``timestamp``, ``level``, ``message``, ``logger``,
    ``request_id``, and any extra ``context`` attached to the record.
    """

    def format(self, record: logging.LogRecord) -> str:
        try:
            message = record.getMessage()
            entry: dict[str, Any] = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "message": _truncate(redact(message)),
                "logger": record.name,
                "request_id": getattr(record, "request_id", ""),
            }
            if record.exc_info and record.exc_info[1] is not None:
                entry["exception"] = redact(self.formatException(record.exc_info))
            context = getattr(record, "context", None)
            if context:
                entry["context"] = context
            return json.dumps(entry, default=str)
        except Exception:
            try:
                print(
                    f"[LOGGING ERROR] StructuredJsonFormatter failed: {traceback.format_exc()}",
                    file=sys.stderr,
                )
            except Exception:
                pass
            return json.dumps(
                {
                    "level": record.levelname,
                    "message": _truncate(redact(str(record.msg))),
                    "error": "formatter_failure",
                }
            )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Return a logger for *name*.

    This is the standard way for all modules to obtain a logger instance.
    The logger inherits the root configuration set by :func:`setup_logging`
    in ``config.py``.
    """
    return logging.getLogger(name)


def safe_error_response(
    logger: logging.Logger,
    exc: Exception,
    operation: str,
    static_message: str = "An internal error occurred",
) -> str:
    """Log detailed error info server-side and return a safe user message.

    Args:
        logger: The logger to write the detailed entry to.
        exc: The caught exception.
        operation: A human-readable description of the operation that failed.
        static_message: The generic message returned to the caller.

    Returns:
        *static_message* — a string safe to include in API responses.
    """
    logger.error(
        "%s failed: %s",
        operation,
        exc,
        exc_info=True,
    )
    return static_message


def handle_service_error(
    exc: Exception,
    operation: str,
    logger: logging.Logger,
    *,
    error_class: type[AppException] | None = None,
    status_code: int = 502,
    static_message: str | None = None,
) -> None:
    """Log the exception and raise an :class:`AppException`.

    This is the shared "log-then-raise" helper that replaces duplicated
    ``try/except`` blocks across API modules.

    Args:
        exc: The caught exception.
        operation: Human-readable operation name for the log message.
        logger: Logger instance for the calling module.
        error_class: The AppException subclass to raise (default ``GitHubAPIError``).
        status_code: HTTP status code if *error_class* is not provided.
        static_message: User-safe message.  Defaults to ``"<operation> failed"``.

    Raises:
        AppException (or a subclass) with a safe message.
    """
    from src.exceptions import GitHubAPIError

    safe_msg = static_message or f"{operation} failed"
    logger.error("%s: %s", operation, exc, exc_info=True)

    if error_class is not None:
        raise error_class(message=safe_msg) from exc

    raise GitHubAPIError(message=safe_msg) from exc
