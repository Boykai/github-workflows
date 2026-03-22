"""Tests for centralized logging utilities."""

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
)

# ---------------------------------------------------------------------------
# redact()
# ---------------------------------------------------------------------------


class TestRedact:
    """Tests for the redact() sanitization function."""

    def test_redacts_github_pat(self) -> None:
        msg = "Token is ghp_abc1234567890xyz"
        assert "ghp_" not in redact(msg)
        assert "[REDACTED_GITHUB_TOKEN]" in redact(msg)

    def test_redacts_github_oauth_token(self) -> None:
        msg = "gho_SomeOAuthToken1234"
        assert "gho_" not in redact(msg)

    def test_redacts_github_server_token(self) -> None:
        msg = "ghs_ServerToServer12345"
        assert "ghs_" not in redact(msg)

    def test_redacts_github_fine_grained_pat(self) -> None:
        msg = "github_pat_SomeFineGrainedPAT"
        assert "github_pat_" not in redact(msg)

    def test_redacts_bearer_token(self) -> None:
        msg = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
        result = redact(msg)
        assert "eyJhbG" not in result
        assert "[REDACTED]" in result

    def test_redacts_basic_auth(self) -> None:
        msg = "Authorization: Basic dXNlcjpwYXNz"
        result = redact(msg)
        assert "dXNlcjpwYXNz" not in result
        assert "[REDACTED]" in result

    def test_redacts_api_key_value(self) -> None:
        msg = "api_key=sk-1234567890abcdef"
        result = redact(msg)
        assert "sk-1234567890abcdef" not in result
        assert "[REDACTED]" in result

    def test_redacts_secret_value(self) -> None:
        msg = "secret=mysupersecret123"
        result = redact(msg)
        assert "mysupersecret123" not in result

    def test_redacts_password_value(self) -> None:
        msg = "password=hunter2"
        result = redact(msg)
        assert "hunter2" not in result

    def test_redacts_email_address(self) -> None:
        msg = "User email is john.doe@example.com"
        result = redact(msg)
        assert "john.doe@example.com" not in result
        assert "[REDACTED_EMAIL]" in result

    def test_redacts_unix_paths(self) -> None:
        msg = "Error in /home/user/project/src/main.py"
        result = redact(msg)
        assert "/home/user" not in result
        assert "[REDACTED_PATH]" in result

    def test_redacts_app_paths(self) -> None:
        msg = "Loading /app/src/config.py"
        result = redact(msg)
        assert "/app/src" not in result

    def test_preserves_safe_content(self) -> None:
        msg = "Request processed successfully with status 200"
        assert redact(msg) == msg

    def test_truncates_oversized_messages(self) -> None:
        msg = "x" * (MAX_LOG_MESSAGE_LENGTH + 1000)
        result = redact(msg)
        assert len(result) <= MAX_LOG_MESSAGE_LENGTH + 50  # allow for suffix
        assert "[TRUNCATED]" in result

    def test_empty_message(self) -> None:
        assert redact("") == ""

    def test_only_sensitive_data_still_produces_output(self) -> None:
        """Redaction should not suppress the log entry entirely."""
        msg = "ghp_abc1234567890xyz"
        result = redact(msg)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# SanitizingFormatter
# ---------------------------------------------------------------------------


class TestSanitizingFormatter:
    """Tests for the SanitizingFormatter."""

    def test_sanitizes_log_message(self) -> None:
        formatter = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Token: ghp_abc1234567890xyz",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert "ghp_abc" not in output
        assert "[REDACTED_GITHUB_TOKEN]" in output

    def test_preserves_safe_messages(self) -> None:
        formatter = SanitizingFormatter(fmt="%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="All systems operational",
            args=(),
            exc_info=None,
        )
        assert "All systems operational" in formatter.format(record)


# ---------------------------------------------------------------------------
# StructuredJsonFormatter
# ---------------------------------------------------------------------------


class TestStructuredJsonFormatter:
    """Tests for the StructuredJsonFormatter."""

    def test_produces_valid_json(self) -> None:
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test_module",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Something happened",
            args=(),
            exc_info=None,
        )
        record.request_id = "abc123"  # type: ignore[attr-defined]
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Something happened"
        assert parsed["logger"] == "test_module"
        assert parsed["request_id"] == "abc123"
        assert "timestamp" in parsed

    def test_sanitizes_sensitive_data_in_json(self) -> None:
        formatter = StructuredJsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Auth failed with token ghp_secret123456",
            args=(),
            exc_info=None,
        )
        record.request_id = ""  # type: ignore[attr-defined]
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "ghp_secret" not in parsed["message"]
        assert "[REDACTED_GITHUB_TOKEN]" in parsed["message"]

    def test_includes_exception_info(self) -> None:
        formatter = StructuredJsonFormatter()
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
            msg="Operation failed",
            args=(),
            exc_info=exc_info,
        )
        record.request_id = ""  # type: ignore[attr-defined]
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


# ---------------------------------------------------------------------------
# RequestIDFilter
# ---------------------------------------------------------------------------


class TestRequestIDFilter:
    """Tests for the RequestIDFilter."""

    def test_sets_request_id_on_record(self) -> None:
        from src.middleware.request_id import request_id_var

        token = request_id_var.set("test-request-123")
        try:
            f = RequestIDFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="hi",
                args=(),
                exc_info=None,
            )
            f.filter(record)
            assert record.request_id == "test-request-123"  # type: ignore[attr-defined]
        finally:
            request_id_var.reset(token)

    def test_defaults_to_empty_string(self) -> None:
        f = RequestIDFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hi",
            args=(),
            exc_info=None,
        )
        f.filter(record)
        assert record.request_id == ""  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# get_logger
# ---------------------------------------------------------------------------


class TestGetLogger:
    """Tests for the get_logger helper."""

    def test_returns_logger_with_given_name(self) -> None:
        logger = get_logger("my_module")
        assert logger.name == "my_module"

    def test_returns_standard_logger_instance(self) -> None:
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)


# ---------------------------------------------------------------------------
# handle_service_error
# ---------------------------------------------------------------------------


class TestHandleServiceError:
    """Tests for the handle_service_error helper."""

    def test_raises_default_github_api_error(self) -> None:
        from src.exceptions import GitHubAPIError

        exc = RuntimeError("connection timeout")
        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(exc, "fetch projects")
        assert "fetch projects" in exc_info.value.message
        assert "connection timeout" not in exc_info.value.message

    def test_raises_specified_error_class(self) -> None:
        from src.exceptions import NotFoundError

        exc = KeyError("missing")
        with pytest.raises(NotFoundError):
            handle_service_error(exc, "find item", NotFoundError)

    def test_does_not_leak_details(self) -> None:
        from src.exceptions import GitHubAPIError

        exc = RuntimeError("secret info: password=hunter2")
        with pytest.raises(GitHubAPIError) as exc_info:
            handle_service_error(exc, "do thing")
        assert "hunter2" not in exc_info.value.message
        assert exc_info.value.details == {}

    def test_logs_full_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        from src.exceptions import GitHubAPIError

        exc = RuntimeError("internal detail")
        with caplog.at_level(logging.ERROR, logger="error_handler"), pytest.raises(GitHubAPIError):
            handle_service_error(exc, "test op")
        assert "internal detail" in caplog.text

    def test_raises_value_error_with_positional_message(self) -> None:
        """ValueError (non-AppException) is constructed with a positional arg."""
        exc = RuntimeError("provider error")
        with pytest.raises(ValueError, match="Failed to call AI provider"):
            handle_service_error(exc, "call AI provider", ValueError)

    def test_value_error_does_not_leak_details(self) -> None:
        exc = RuntimeError("secret-key-12345")
        with pytest.raises(ValueError) as exc_info:
            handle_service_error(exc, "process request", ValueError)
        assert "secret-key-12345" not in str(exc_info.value)
        assert "process request" in str(exc_info.value)
