"""Unit tests for custom application exceptions."""

from fastapi import status

from src.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    GitHubAPIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestAppException:
    """Tests for the base AppException."""

    def test_default_status_code(self):
        """AppException should default to 500."""
        exc = AppException("something broke")

        assert exc.message == "something broke"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.details == {}

    def test_custom_status_code_and_details(self):
        """AppException should accept custom status_code and details."""
        details = {"field": "name"}
        exc = AppException("bad input", status_code=400, details=details)

        assert exc.status_code == 400
        assert exc.details == details

    def test_str_representation(self):
        """AppException str should be the message."""
        exc = AppException("msg")
        assert str(exc) == "msg"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_message(self):
        """Should have default message and 401 status."""
        exc = AuthenticationError()

        assert exc.message == "Authentication required"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_custom_message(self):
        """Should accept a custom message."""
        exc = AuthenticationError("Token expired")

        assert exc.message == "Token expired"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_message(self):
        """Should have default message and 403 status."""
        exc = AuthorizationError()

        assert exc.message == "Access denied"
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_custom_message(self):
        """Should accept a custom message."""
        exc = AuthorizationError("Insufficient permissions")

        assert exc.message == "Insufficient permissions"


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_message(self):
        """Should have default message and 404 status."""
        exc = NotFoundError()

        assert exc.message == "Resource not found"
        assert exc.status_code == status.HTTP_404_NOT_FOUND

    def test_custom_message(self):
        """Should accept a custom message."""
        exc = NotFoundError("Issue #42 not found")

        assert exc.message == "Issue #42 not found"


class TestValidationError:
    """Tests for ValidationError."""

    def test_message_and_status(self):
        """Should have 422 status."""
        exc = ValidationError("Invalid input")

        assert exc.message == "Invalid input"
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_with_details(self):
        """Should store details dict."""
        details = {"field": "title", "reason": "too long"}
        exc = ValidationError("Invalid input", details=details)

        assert exc.details == details

    def test_without_details(self):
        """Details should default to empty dict."""
        exc = ValidationError("Invalid input")

        assert exc.details == {}


class TestGitHubAPIError:
    """Tests for GitHubAPIError."""

    def test_message_and_status(self):
        """Should have 502 status."""
        exc = GitHubAPIError("GitHub is down")

        assert exc.message == "GitHub is down"
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY

    def test_with_details(self):
        """Should store details dict."""
        details = {"response_code": 503}
        exc = GitHubAPIError("GitHub is down", details=details)

        assert exc.details == details


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_message_and_retry(self):
        """Should have default message, 429 status, and default retry_after."""
        exc = RateLimitError()

        assert exc.message == "Rate limit exceeded"
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.retry_after == 60

    def test_custom_message_and_retry(self):
        """Should accept custom message and retry_after."""
        exc = RateLimitError("Slow down", retry_after=120)

        assert exc.message == "Slow down"
        assert exc.retry_after == 120

    def test_inherits_from_app_exception(self):
        """All custom exceptions should inherit from AppException."""
        assert issubclass(RateLimitError, AppException)
        assert issubclass(AuthenticationError, AppException)
        assert issubclass(AuthorizationError, AppException)
        assert issubclass(NotFoundError, AppException)
        assert issubclass(ValidationError, AppException)
        assert issubclass(GitHubAPIError, AppException)
