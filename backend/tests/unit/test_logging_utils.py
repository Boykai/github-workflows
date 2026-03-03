"""Unit tests for backend/src/logging_utils.py — centralized logging utilities."""

import json
import logging

import pytest

from src.logging_utils import (
    MAX_LOG_MESSAGE_LENGTH,
    RequestIDFilter,
    SanitizingFormatter,
    StructuredJsonFormatter,
    get_logger,
    handle_service_error,
    redact,
    safe_error_response,
)

# ---------------------------------------------------------------------------
# redact()
# ---------------------------------------------------------------------------


class TestRedact:
    """Tests for the redact() function."""

    def test_github_token_ghp(self):
        assert "[REDACTED]" in redact("token=ghp_abc123XYZ")

    def test_github_token_gho(self):
        assert "[REDACTED]" in redact("gho_secretValue123")

    def test_github_token_ghs(self):
        assert "[REDACTED]" in redact("ghs_tokenValue456")

    def test_github_pat(self):
        assert "[REDACTED]" in redact("github_pat_myLongPatValue")

    def test_bearer_token(self):
        result = redact("Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.payload.sig")
        assert "eyJhbGciOiJSUzI1NiJ9" not in result
        assert "[REDACTED]" in result

    def test_basic_auth(self):
        result = redact("Authorization: Basic dXNlcjpwYXNz")
        assert "dXNlcjpwYXNz" not in result

    def test_api_key_pattern(self):
        result = redact("api_key=sk_live_abc123")
        assert "sk_live_abc123" not in result
        assert "[REDACTED]" in result

    def test_email_address(self):
        result = redact("User email is user@example.com and name is John")
        assert "user@example.com" not in result
        assert "[REDACTED]" in result

    def test_unix_file_path(self):
        result = redact("Error at /home/deploy/app/src/main.py:42")
        assert "/home/deploy/app/src/main.py:42" not in result

    def test_windows_file_path(self):
        result = redact(r"Error at C:\Users\admin\project\src\main.py")
        assert r"C:\Users\admin" not in result

    def test_plain_text_unchanged(self):
        msg = "Everything is fine"
        assert redact(msg) == msg

    def test_truncation(self):
        long_msg = "a" * (MAX_LOG_MESSAGE_LENGTH + 500)
        result = redact(long_msg)
        assert result.endswith("[TRUNCATED]")
        assert len(result) <= MAX_LOG_MESSAGE_LENGTH + 20  # allow suffix

    def test_password_pattern(self):
        result = redact("password=mysecretpassword123")
        assert "mysecretpassword123" not in result

    def test_token_colon_pattern(self):
        result = redact("token: abc123secretvalue")
        assert "abc123secretvalue" not in result


# ---------------------------------------------------------------------------
# RequestIDFilter
# ---------------------------------------------------------------------------


class TestRequestIDFilter:
    """Tests for the RequestIDFilter."""

    def test_adds_request_id_attribute(self):
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
        result = filt.filter(record)
        assert result is True
        assert hasattr(record, "request_id")

    def test_request_id_defaults_to_empty(self):
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
    """Tests for the SanitizingFormatter."""

    def test_sanitizes_message(self):
        fmt = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Token: ghp_abc123XYZ",
            args=(),
            exc_info=None,
        )
        result = fmt.format(record)
        assert "ghp_abc123XYZ" not in result
        assert "[REDACTED]" in result

    def test_plain_message_passes_through(self):
        fmt = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Everything is fine",
            args=(),
            exc_info=None,
        )
        result = fmt.format(record)
        assert result == "Everything is fine"


# ---------------------------------------------------------------------------
# StructuredJsonFormatter
# ---------------------------------------------------------------------------


class TestStructuredJsonFormatter:
    """Tests for the StructuredJsonFormatter."""

    def test_emits_valid_json(self):
        fmt = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Something happened",
            args=(),
            exc_info=None,
        )
        record.request_id = "abc123"  # type: ignore[attr-defined]
        result = fmt.format(record)
        data = json.loads(result)
        assert data["level"] == "WARNING"
        assert data["message"] == "Something happened"
        assert data["logger"] == "test.module"
        assert data["request_id"] == "abc123"
        assert "timestamp" in data

    def test_sanitizes_sensitive_data_in_json(self):
        fmt = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Auth failed for ghp_secretToken123",
            args=(),
            exc_info=None,
        )
        record.request_id = ""  # type: ignore[attr-defined]
        result = fmt.format(record)
        data = json.loads(result)
        assert "ghp_secretToken123" not in data["message"]
        assert "[REDACTED]" in data["message"]


# ---------------------------------------------------------------------------
# get_logger()
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for the get_logger() factory."""

    def test_returns_logger(self):
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


# ---------------------------------------------------------------------------
# safe_error_response()
# ---------------------------------------------------------------------------


class TestSafeErrorResponse:
    """Tests for the safe_error_response() helper."""

    def test_returns_message(self):
        logger = logging.getLogger("test.safe")
        msg = safe_error_response(logger, "Operation failed", ValueError("secret details"))
        assert msg == "Operation failed"

    def test_does_not_contain_exception_text(self):
        logger = logging.getLogger("test.safe")
        msg = safe_error_response(logger, "Something went wrong", RuntimeError("ghp_token123"))
        assert "ghp_token123" not in msg


# ---------------------------------------------------------------------------
# handle_service_error()
# ---------------------------------------------------------------------------


class TestHandleServiceError:
    """Tests for the handle_service_error() helper."""

    def test_raises_github_api_error_by_default(self):
        from src.exceptions import GitHubAPIError

        logger = logging.getLogger("test.handle")
        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(logger, "Fetch data", RuntimeError("db down"))
        assert "Fetch data failed" in str(exc_info.value)
        # Must NOT contain the original exception text
        assert "db down" not in exc_info.value.message

    def test_raises_custom_exception_class(self):
        from src.exceptions import AppException

        logger = logging.getLogger("test.handle")
        with pytest.raises(AppException):
            handle_service_error(
                logger,
                "Compute",
                ValueError("oops"),
                exc_class=AppException,
            )
