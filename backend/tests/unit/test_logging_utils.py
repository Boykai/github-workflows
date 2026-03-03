"""Tests for the centralized logging utility module."""

import json
import logging

import pytest

from src.logging_utils import (
    MAX_LOG_MESSAGE_LENGTH,
    REDACTED,
    RequestIDFilter,
    SanitizingFormatter,
    StructuredJsonFormatter,
    get_logger,
    handle_service_error,
    redact,
    safe_error_response,
)

# ---------------------------------------------------------------------------
# redact() tests
# ---------------------------------------------------------------------------


class TestRedact:
    """Tests for the redact() function."""

    def test_redacts_github_ghp_token(self):
        msg = "Token: ghp_ABCDEFghijklmnop1234567890abcdefghijkl"
        assert REDACTED in redact(msg)
        assert "ghp_" not in redact(msg)

    def test_redacts_github_gho_token(self):
        msg = "OAuth: gho_ABCDEFghijklmnop1234567890abcdefghijkl"
        assert REDACTED in redact(msg)
        assert "gho_" not in redact(msg)

    def test_redacts_github_ghs_token(self):
        msg = "Server: ghs_ABCDEFghijklmnop1234567890abcdefghijkl"
        assert REDACTED in redact(msg)
        assert "ghs_" not in redact(msg)

    def test_redacts_github_pat_token(self):
        msg = "PAT: github_pat_ABCDEFGHIJKLMNOPQRSTUV"
        assert REDACTED in redact(msg)
        assert "github_pat_" not in redact(msg)

    def test_redacts_bearer_token(self):
        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"
        result = redact(msg)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        assert f"Bearer {REDACTED}" in result

    def test_redacts_basic_auth(self):
        msg = "Authorization: Basic dXNlcjpwYXNzd29yZA=="
        result = redact(msg)
        assert "dXNlcjpwYXNzd29yZA==" not in result
        assert f"Basic {REDACTED}" in result

    def test_redacts_email_addresses(self):
        msg = "User email is test.user@example.com"
        result = redact(msg)
        assert "test.user@example.com" not in result
        assert REDACTED in result

    def test_redacts_internal_file_paths(self):
        msg = "Error at /home/deploy/app/src/api/auth.py:42"
        result = redact(msg)
        assert "/home/deploy" not in result
        assert "[PATH]" in result

    def test_preserves_safe_text(self):
        msg = "User requested 5 items from the board"
        assert redact(msg) == msg

    def test_truncates_oversized_messages(self):
        msg = "x" * (MAX_LOG_MESSAGE_LENGTH + 1000)
        result = redact(msg)
        assert len(result) <= MAX_LOG_MESSAGE_LENGTH + len(" [TRUNCATED]")
        assert result.endswith("[TRUNCATED]")

    def test_does_not_truncate_within_limit(self):
        msg = "x" * 100
        assert redact(msg) == msg

    def test_handles_empty_string(self):
        assert redact("") == ""

    def test_redacts_key_value_pattern(self):
        msg = "token=ghp_ABCDEFghijklmnop1234567890abcdefghijkl"
        result = redact(msg)
        assert "ghp_" not in result

    def test_multiple_sensitive_values_in_one_message(self):
        msg = "Token ghp_ABCDEFghijklmnop1234567890abcdefghijkl and email user@test.com"
        result = redact(msg)
        assert "ghp_" not in result
        assert "user@test.com" not in result


# ---------------------------------------------------------------------------
# SanitizingFormatter tests
# ---------------------------------------------------------------------------


class TestSanitizingFormatter:
    """Tests for SanitizingFormatter."""

    def test_redacts_sensitive_data_in_log(self):
        fmt = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Token: ghp_ABCDEFghijklmnop1234567890abcdefghijkl",
            args=None,
            exc_info=None,
        )
        result = fmt.format(record)
        assert "ghp_" not in result
        assert REDACTED in result

    def test_preserves_safe_messages(self):
        fmt = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Board data loaded successfully",
            args=None,
            exc_info=None,
        )
        result = fmt.format(record)
        assert result == "Board data loaded successfully"


# ---------------------------------------------------------------------------
# StructuredJsonFormatter tests
# ---------------------------------------------------------------------------


class TestStructuredJsonFormatter:
    """Tests for StructuredJsonFormatter."""

    def test_emits_valid_json(self):
        fmt = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Hello world",
            args=None,
            exc_info=None,
        )
        result = fmt.format(record)
        parsed = json.loads(result)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Hello world"
        assert parsed["logger"] == "test.module"
        assert "timestamp" in parsed

    def test_redacts_sensitive_data_in_json(self):
        fmt = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Auth failed with token ghp_ABCDEFghijklmnop1234567890abcdefghijkl",
            args=None,
            exc_info=None,
        )
        result = fmt.format(record)
        parsed = json.loads(result)
        assert "ghp_" not in parsed["message"]
        assert REDACTED in parsed["message"]

    def test_includes_request_id_when_available(self):
        fmt = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=None,
            exc_info=None,
        )
        record.request_id = "abc-123"  # type: ignore[attr-defined]
        result = fmt.format(record)
        parsed = json.loads(result)
        assert parsed["request_id"] == "abc-123"

    def test_includes_exception_info_when_present(self):
        fmt = StructuredJsonFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Something failed",
            args=None,
            exc_info=exc_info,
        )
        result = fmt.format(record)
        parsed = json.loads(result)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


# ---------------------------------------------------------------------------
# RequestIDFilter tests
# ---------------------------------------------------------------------------


class TestRequestIDFilter:
    """Tests for RequestIDFilter."""

    def test_adds_request_id_attribute(self):
        filt = RequestIDFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=None,
            exc_info=None,
        )
        result = filt.filter(record)
        assert result is True
        assert hasattr(record, "request_id")

    def test_uses_context_var_value(self):
        from src.middleware.request_id import request_id_var

        token = request_id_var.set("test-rid-123")
        try:
            filt = RequestIDFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test",
                args=None,
                exc_info=None,
            )
            filt.filter(record)
            assert record.request_id == "test-rid-123"  # type: ignore[attr-defined]
        finally:
            request_id_var.reset(token)


# ---------------------------------------------------------------------------
# get_logger tests
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_logger_with_name(self):
        log = get_logger("my.module")
        assert isinstance(log, logging.Logger)
        assert log.name == "my.module"


# ---------------------------------------------------------------------------
# safe_error_response tests
# ---------------------------------------------------------------------------


class TestSafeErrorResponse:
    """Tests for safe_error_response()."""

    def test_returns_generic_message(self):
        msg = safe_error_response(ValueError("secret detail"), "fetch data")
        assert msg == "Failed to fetch data"
        assert "secret detail" not in msg

    def test_logs_full_error(self, caplog):
        with caplog.at_level(logging.ERROR):
            safe_error_response(RuntimeError("db connection failed"), "load settings")
        assert "db connection failed" in caplog.text


# ---------------------------------------------------------------------------
# handle_service_error tests
# ---------------------------------------------------------------------------


class TestHandleServiceError:
    """Tests for handle_service_error()."""

    def test_raises_specified_error_class(self):
        from src.exceptions import GitHubAPIError

        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(
                ValueError("raw detail"),
                "fetch projects",
                GitHubAPIError,
            )
        assert "raw detail" not in exc_info.value.message
        assert "Failed to fetch projects" in exc_info.value.message

    def test_preserves_cause_chain(self):
        from src.exceptions import GitHubAPIError

        original = RuntimeError("original")
        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(original, "sync data", GitHubAPIError)
        assert exc_info.value.__cause__ is original
