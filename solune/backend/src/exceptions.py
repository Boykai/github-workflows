"""Custom application exceptions."""

from fastapi import status


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppException):
    """Authorization failed."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationError(AppException):
    """Validation error."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, details=details
        )


class GitHubAPIError(AppException):
    """GitHub API error."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message, status_code=status.HTTP_502_BAD_GATEWAY, details=details)


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        details: dict | None = None,
    ):
        super().__init__(
            message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )
        self.retry_after = retry_after


class ConflictError(AppException):
    """Resource conflict (e.g., duplicate creation, concurrent modification)."""

    def __init__(self, message: str = "Resource conflict", details: dict | None = None):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT, details=details)


class McpValidationError(AppException):
    """MCP configuration validation failed (e.g. SSRF, invalid URL)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)


class McpLimitExceededError(AppException):
    """User has reached the maximum number of MCP configurations."""

    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class DatabaseError(AppException):
    """Database or persistence error."""

    def __init__(self, message: str = "Database error", details: dict | None = None):
        super().__init__(
            message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=details
        )


class PersistenceError(DatabaseError):
    """Persistence operation failed after retries."""

    def __init__(self, message: str = "Persistence failed", details: dict | None = None):
        super().__init__(message, details=details)
