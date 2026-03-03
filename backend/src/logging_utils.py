"""Centralized logging utility for sanitization, structured formatting, and error handling.

This module provides:

- **Sensitive-data redaction**: A configurable set of regex patterns that scrub
  tokens, API keys, PII, and internal file paths from log messages before they
  reach any log sink.

- **SanitizingFormatter**: A ``logging.Formatter`` subclass that applies the
  redaction function to every log record.

- **StructuredJsonFormatter**: A ``logging.Formatter`` subclass that emits log
  records as single-line JSON objects (timestamp, level, message, logger, context).

- **RequestIDFilter**: A ``logging.Filter`` that injects the current request ID
  from the ``ContextVar`` in ``middleware.request_id`` into each log record.

- **get_logger(name)**: The standard way for all modules to obtain a logger.

- **safe_error_response(exc, operation)**: Logs full error detail server-side
  and returns a generic user-safe message string.

- **handle_service_error(exc, operation, error_class)**: Shared pattern for
  logging + raising safe ``AppException`` subclasses.

Usage::

    from src.logging_utils import get_logger, safe_error_response

    logger = get_logger(__name__)

    try:
        ...
    except Exception as e:
        msg = safe_error_response(e, "fetch board projects")
        raise GitHubAPIError(message=msg) from e
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Redaction patterns
# ---------------------------------------------------------------------------

#: Maximum allowed length for a single log message.  Messages exceeding this
#: limit are truncated and a ``[TRUNCATED]`` marker is appended.
MAX_LOG_MESSAGE_LENGTH: int = 10_000

#: Placeholder used when sensitive data is redacted.
REDACTED = "[REDACTED]"

#: Compiled regex patterns that match sensitive data in log messages.
#: Each entry is a tuple of (compiled_pattern, replacement_string).
_SENSITIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = []


def _compile_patterns() -> list[tuple[re.Pattern[str], str]]:
    """Build and compile the default set of sensitive-data patterns."""
    raw: list[tuple[str, str]] = [
        # GitHub tokens (ghp_, gho_, ghs_, github_pat_)
        (r"ghp_[A-Za-z0-9_]{36,}", REDACTED),
        (r"gho_[A-Za-z0-9_]{36,}", REDACTED),
        (r"ghs_[A-Za-z0-9_]{36,}", REDACTED),
        (r"github_pat_[A-Za-z0-9_]{22,}", REDACTED),
        # Bearer / Basic auth headers
        (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", f"Bearer {REDACTED}"),
        (r"Basic\s+[A-Za-z0-9+/]+=*", f"Basic {REDACTED}"),
        # Generic long hex/base64 tokens (≥32 chars, commonly API keys)
        (
            r"(?:token|key|secret|password|apikey|api_key|access_token|auth)\s*[=:]\s*['\"]?[A-Za-z0-9\-._~+/]{32,}['\"]?",
            REDACTED,
        ),
        # Email addresses (PII)
        (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", REDACTED),
        # Internal absolute file paths (Unix-style) — redact system-specific
        # prefixes but keep the last two path components for context.
        (r"(?:/(?:home|Users|app|var|tmp|opt|srv|usr|etc)/)[^\s:\"']+", "[PATH]"),
    ]
    return [(re.compile(pat), repl) for pat, repl in raw]


_SENSITIVE_PATTERNS = _compile_patterns()


def redact(message: str) -> str:
    """Scrub sensitive data from *message* using the configured pattern list.

    Returns the redacted string.  If the message exceeds
    ``MAX_LOG_MESSAGE_LENGTH`` it is truncated.
    """
    try:
        for pattern, replacement in _SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)
        if len(message) > MAX_LOG_MESSAGE_LENGTH:
            message = message[:MAX_LOG_MESSAGE_LENGTH] + " [TRUNCATED]"
    except Exception:
        # Never let sanitization failures crash the caller.
        message = "[REDACTION ERROR] " + message[:200]
    return message


# ---------------------------------------------------------------------------
# Formatters and filters
# ---------------------------------------------------------------------------


class SanitizingFormatter(logging.Formatter):
    """Formatter that redacts sensitive data from every log record."""

    def __init__(self, fmt: str | None = None, datefmt: str | None = None, **kwargs: Any) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt, **kwargs)

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        try:
            original = super().format(record)
            return redact(original)
        except Exception:
            # Fallback: emit something rather than crash.
            try:
                fallback = f"{record.levelname} - {record.getMessage()}"
                return redact(fallback)
            except Exception:
                return "[FORMATTING ERROR]"


class StructuredJsonFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects.

    Fields: ``timestamp``, ``level``, ``message``, ``logger``, ``request_id``
    (if available), and ``context`` (extra fields).
    """

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        try:
            message = redact(record.getMessage())
            entry: dict[str, Any] = {
                "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                "level": record.levelname,
                "message": message,
                "logger": record.name,
            }
            # Inject request_id if present on the record
            request_id = getattr(record, "request_id", None)
            if request_id:
                entry["request_id"] = request_id

            # Include exception info if present
            if record.exc_info and record.exc_info[1] is not None:
                entry["exception"] = redact(self.formatException(record.exc_info))

            return json.dumps(entry, default=str)
        except Exception:
            return json.dumps({"level": "ERROR", "message": "[JSON FORMATTING ERROR]"})


class RequestIDFilter(logging.Filter):
    """Inject the current request ID into every log record.

    The request ID is read from the ``ContextVar`` defined in
    ``src.middleware.request_id``.
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
    """Return a logger for *name*.

    This is the standard way for all modules to obtain a logger.  It simply
    delegates to ``logging.getLogger`` today but centralises the call so
    future enhancements (e.g. attaching extra context) require only one
    change.
    """
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Safe error helpers
# ---------------------------------------------------------------------------


def safe_error_response(
    exc: Exception,
    operation: str,
    *,
    logger: logging.Logger | None = None,
) -> str:
    """Log detailed error info server-side and return a generic user-safe string.

    Args:
        exc: The caught exception.
        operation: A short description of what was being attempted.
        logger: Optional logger; falls back to the module logger.

    Returns:
        A safe, user-facing error message that never includes internal details.
    """
    log = logger or logging.getLogger(__name__)
    log.error("Error during %s: %s", operation, exc, exc_info=True)
    return f"Failed to {operation}"


def handle_service_error(
    exc: Exception,
    operation: str,
    error_class: type[Exception],
    *,
    logger: logging.Logger | None = None,
) -> None:
    """Log *exc* and raise *error_class* with a safe message.

    This extracts the repeated pattern::

        except Exception as e:
            logger.error("...: %s", e)
            raise SomeAppException(message="...", details={"error": str(e)}) from e

    into a single helper.

    Args:
        exc: The caught exception.
        operation: A short human-readable description.
        error_class: The ``AppException`` subclass to raise.
        logger: Optional logger; falls back to the module logger.

    Raises:
        error_class: Always raised with a safe message.
    """
    msg = safe_error_response(exc, operation, logger=logger)
    raise error_class(message=msg) from exc


# ---------------------------------------------------------------------------
# Self-resilience helper
# ---------------------------------------------------------------------------


def _fallback_stderr(message: str) -> None:
    """Last-resort output when the logging subsystem itself fails."""
    try:
        ts = datetime.now(tz=UTC).isoformat()
        print(f"[LOGGING FALLBACK {ts}] {message}", file=sys.stderr, flush=True)  # noqa: T201
    except Exception:
        pass  # Absolutely nothing more we can do.
