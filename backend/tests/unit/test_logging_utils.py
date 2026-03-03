"""Unit tests for src.logging_utils — centralized logging utility."""

import json
import logging

import pytest

from src.logging_utils import (
    MAX_LOG_MESSAGE_LENGTH,
    REDACTED,
    RequestIDFilter,
    SanitizingFormatter,
    StructuredJsonFormatter,
    _truncate,
    get_logger,
    handle_service_error,
    redact,
    safe_error_response,
)

# ---------------------------------------------------------------------------
# redact()
# ---------------------------------------------------------------------------


class TestRedact:
    """Tests for the sensitive-data redaction function."""

    def test_github_personal_access_token(self):
        text = "token=ghp_ABCDEFghijklmnop1234567890abcdefghijklmnop"
        result = redact(text)
        assert "ghp_" not in result
        assert REDACTED in result

    def test_github_oauth_token(self):
        text = "gho_ABCDEFghijklmnop1234567890abcdefghijklmnop"
        result = redact(text)
        assert "gho_" not in result
        assert REDACTED in result

    def test_github_server_token(self):
        text = "ghs_ABCDEFghijklmnop1234567890abcdefghijklmnop"
        result = redact(text)
        assert "ghs_" not in result
        assert REDACTED in result

    def test_github_pat_token(self):
        text = "github_pat_ABCDEFGHIJKLMNOPQRSTUV"
        result = redact(text)
        assert "github_pat_" not in result
        assert REDACTED in result

    def test_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc"
        result = redact(text)
        assert "eyJ" not in result
        assert REDACTED in result

    def test_basic_auth(self):
        text = "Authorization: Basic dXNlcjpwYXNzd29yZA=="
        result = redact(text)
        assert "dXNlcjpwYXNzd29yZA==" not in result
        assert REDACTED in result

    def test_api_key_pattern(self):
        text = "api_key=sk-proj-abcdefg1234567890"
        result = redact(text)
        assert "sk-proj-" not in result
        assert REDACTED in result

    def test_email_address(self):
        text = "User john.doe@example.com logged in"
        result = redact(text)
        assert "john.doe@example.com" not in result
        assert REDACTED in result

    def test_unix_internal_path(self):
        text = "Error at /home/runner/work/project/src/main.py:42"
        result = redact(text)
        assert "/home/runner" not in result
        assert REDACTED in result

    def test_windows_internal_path(self):
        text = r"Error at C:\Users\admin\project\src\main.py"
        result = redact(text)
        assert r"C:\Users" not in result
        assert REDACTED in result

    def test_no_sensitive_data(self):
        text = "Normal log message with no secrets"
        result = redact(text)
        assert result == text

    def test_non_string_passthrough(self):
        assert redact(42) == 42  # type: ignore[arg-type]
        assert redact(None) is None  # type: ignore[arg-type]

    def test_empty_string(self):
        assert redact("") == ""

    def test_multiple_sensitive_items(self):
        text = "token=ghp_ABCDEFghijklmnop1234567890abcdefghijklmnop user=test@example.com"
        result = redact(text)
        assert "ghp_" not in result
        assert "test@example.com" not in result


# ---------------------------------------------------------------------------
# _truncate()
# ---------------------------------------------------------------------------


class TestTruncate:
    """Tests for the log message truncation function."""

    def test_short_message_unchanged(self):
        msg = "short message"
        assert _truncate(msg) == msg

    def test_exact_limit_unchanged(self):
        msg = "x" * MAX_LOG_MESSAGE_LENGTH
        assert _truncate(msg) == msg

    def test_oversized_truncated(self):
        msg = "x" * (MAX_LOG_MESSAGE_LENGTH + 500)
        result = _truncate(msg)
        assert len(result) < len(msg)
        assert "truncated" in result

    def test_custom_limit(self):
        msg = "abcdefghij"
        result = _truncate(msg, max_length=5)
        assert result.startswith("abcde")
        assert "truncated" in result


# ---------------------------------------------------------------------------
# RequestIDFilter
# ---------------------------------------------------------------------------


class TestRequestIDFilter:
    """Tests for the request-ID log filter."""

    def test_injects_request_id(self):
        from src.middleware.request_id import request_id_var

        filt = RequestIDFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        token = request_id_var.set("test-rid-123")
        try:
            filt.filter(record)
            assert record.request_id == "test-rid-123"  # type: ignore[attr-defined]
        finally:
            request_id_var.reset(token)

    def test_empty_default(self):
        filt = RequestIDFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        filt.filter(record)
        assert record.request_id == ""  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# SanitizingFormatter
# ---------------------------------------------------------------------------


class TestSanitizingFormatter:
    """Tests for the sanitizing log formatter."""

    def test_redacts_sensitive_data(self):
        fmt = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="key=ghp_ABCDEFghijklmnop1234567890abcdefghijklmnop",
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "ghp_" not in output
        assert REDACTED in output

    def test_truncates_oversized(self):
        fmt = SanitizingFormatter(fmt="%(message)s")
        long_msg = "x" * (MAX_LOG_MESSAGE_LENGTH + 1000)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=long_msg,
            args=(),
            exc_info=None,
        )
        output = fmt.format(record)
        assert "truncated" in output

    def test_resilience_on_format_error(self):
        """Formatter should not crash even if the format string is broken."""
        fmt = SanitizingFormatter(fmt="%(nonexistent)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello",
            args=(),
            exc_info=None,
        )
        # Should not raise
        output = fmt.format(record)
        assert isinstance(output, str)


# ---------------------------------------------------------------------------
# StructuredJsonFormatter
# ---------------------------------------------------------------------------


class TestStructuredJsonFormatter:
    """Tests for the structured JSON log formatter."""

    def test_valid_json_output(self):
        fmt = StructuredJsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
        record = logging.LogRecord(
            name="test.module",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="something happened",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-abc"  # type: ignore[attr-defined]
        output = fmt.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "WARNING"
        assert parsed["message"] == "something happened"
        assert parsed["logger"] == "test.module"
        assert parsed["request_id"] == "req-abc"
        assert "timestamp" in parsed

    def test_redacts_sensitive_data_in_json(self):
        fmt = StructuredJsonFormatter(datefmt="%Y-%m-%dT%H:%M:%S")
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Failed with token ghp_ABCDEFghijklmnop1234567890abcdefghijklmnop",
            args=(),
            exc_info=None,
        )
        record.request_id = ""  # type: ignore[attr-defined]
        output = fmt.format(record)
        parsed = json.loads(output)
        assert "ghp_" not in parsed["message"]


# ---------------------------------------------------------------------------
# get_logger()
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for the logger factory function."""

    def test_returns_logger(self):
        lg = get_logger("my_module")
        assert isinstance(lg, logging.Logger)
        assert lg.name == "my_module"

    def test_same_logger_returned(self):
        lg1 = get_logger("my_module")
        lg2 = get_logger("my_module")
        assert lg1 is lg2


# ---------------------------------------------------------------------------
# safe_error_response()
# ---------------------------------------------------------------------------


class TestSafeErrorResponse:
    """Tests for the safe error response helper."""

    def test_returns_static_message(self):
        lg = logging.getLogger("test_safe")
        exc = RuntimeError("secret database connection string")
        msg = safe_error_response(lg, exc, "DB query", "Something went wrong")
        assert msg == "Something went wrong"
        assert "database" not in msg

    def test_default_message(self):
        lg = logging.getLogger("test_safe")
        exc = RuntimeError("oops")
        msg = safe_error_response(lg, exc, "operation")
        assert msg == "An internal error occurred"


# ---------------------------------------------------------------------------
# handle_service_error()
# ---------------------------------------------------------------------------


class TestHandleServiceError:
    """Tests for the shared log-then-raise helper."""

    def test_raises_github_api_error_by_default(self):
        from src.exceptions import GitHubAPIError

        lg = logging.getLogger("test_handle")
        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(RuntimeError("boom"), "fetch data", lg)
        assert "fetch data failed" in exc_info.value.message

    def test_raises_custom_exception_class(self):
        from src.exceptions import AppException

        lg = logging.getLogger("test_handle")
        with pytest.raises(AppException):
            handle_service_error(
                RuntimeError("boom"),
                "operation",
                lg,
                error_class=AppException,
                static_message="Custom error message",
            )

    def test_custom_static_message(self):
        from src.exceptions import GitHubAPIError

        lg = logging.getLogger("test_handle")
        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(RuntimeError("boom"), "op", lg, static_message="Custom message")
        assert exc_info.value.message == "Custom message"
