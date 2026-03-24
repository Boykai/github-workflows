"""Authentication API endpoints - OAuth flow."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from slowapi.util import get_remote_address

from src.constants import SESSION_COOKIE_NAME
from src.exceptions import AppException, AuthenticationError, NotFoundError, ValidationError
from src.logging_utils import get_logger, handle_service_error
from src.middleware.rate_limit import limiter
from src.models.user import UserResponse, UserSession
from src.services.github_auth import github_auth_service

logger = get_logger(__name__)
router = APIRouter()


def _set_session_cookie(response: Response, session_id: str) -> None:
    """Set the session cookie with secure defaults on *response*.

    Centralises cookie-flag configuration so that every endpoint that
    issues a session cookie uses identical settings.
    """
    from src.config import get_settings

    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=settings.effective_cookie_secure,
        samesite="strict",
        max_age=settings.cookie_max_age,
        path="/",
    )


# Refresh the token when it expires within this window to avoid
# mid-request failures against GitHub's API.
_TOKEN_REFRESH_BUFFER = timedelta(minutes=5)


async def get_current_session(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> UserSession:
    """Get current user session from cookie.

    Can be used as a FastAPI ``Depends()`` or called directly with a raw
    session-id string (e.g. from a WebSocket query parameter).

    Automatically refreshes the GitHub access token when it is expired
    or about to expire (within a 5-minute buffer), so downstream API
    calls always use a valid token.
    """
    if not session_id:
        raise AuthenticationError("No session cookie")

    session = await github_auth_service.get_session(session_id)
    if not session:
        raise AuthenticationError("Invalid or expired session")

    # Auto-refresh expired / nearly-expired tokens
    if (
        session.token_expires_at is not None
        and session.token_expires_at - _TOKEN_REFRESH_BUFFER <= datetime.now(UTC)
    ):
        if session.refresh_token:
            try:
                session = await github_auth_service.refresh_token(session)
                logger.info("Auto-refreshed token for user %s", session.github_username)
            except Exception:
                logger.warning(
                    "Token refresh failed for user %s — forcing re-login",
                    session.github_username,
                    exc_info=True,
                )
                raise AuthenticationError(
                    "Your GitHub session has expired. Please log in again."
                ) from None
        else:
            logger.warning(
                "Token expired with no refresh_token for user %s",
                session.github_username,
            )
            raise AuthenticationError("Your GitHub session has expired. Please log in again.")

    return session


# Alias for FastAPI Depends() usage — 95+ call sites use this name.
get_session_dep = get_current_session


@router.get("/github")
async def initiate_github_oauth() -> RedirectResponse:
    """Initiate GitHub OAuth flow by redirecting to GitHub authorization."""
    url, _state = github_auth_service.generate_oauth_url()
    logger.info("Redirecting to GitHub OAuth: %s", url[:50])
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/github/callback")
@limiter.limit("20/minute", key_func=get_remote_address)
async def github_callback(
    request: Request,
    code: Annotated[str, Query(description="Authorization code from GitHub")],
    state: Annotated[str, Query(description="OAuth state parameter")],
    response: Response,
) -> RedirectResponse:
    """Handle GitHub OAuth callback and create session."""
    from src.config import get_settings

    settings = get_settings()

    # Validate state
    if not github_auth_service.validate_state(state):
        logger.warning("Invalid OAuth state: %s", state[:20])
        raise ValidationError("Invalid or expired OAuth state")

    try:
        # Create session
        session = await github_auth_service.create_session(code)

        # Get frontend URL from settings (default: http://localhost:5173)
        frontend_url = settings.frontend_url

        # Redirect to frontend — session token delivered via secure cookie only
        redirect_url = f"{frontend_url}/auth/callback"

        redirect = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )
        _set_session_cookie(redirect, str(session.session_id))

        logger.info(
            "Created session for user: %s, redirecting to frontend",
            session.github_username,
        )
        return redirect

    except ValueError as e:
        logger.warning("OAuth token exchange failed: %s", e)
        raise ValidationError("Authentication failed") from e
    except Exception as e:
        handle_service_error(e, "complete authentication", AppException)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> UserResponse:
    """Get current authenticated user."""
    session = await get_current_session(session_id)
    return UserResponse.from_session(session)


@router.post("/logout")
async def logout(
    response: Response,
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> dict:
    """Logout current user by revoking session."""
    if session_id:
        await github_auth_service.revoke_session(session_id)

    from src.config import get_settings

    settings = get_settings()
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=settings.effective_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    return {"message": "Logged out successfully"}


class DevLoginRequest(BaseModel):
    """Request body for dev-login endpoint."""

    github_token: str = Field(..., min_length=1, max_length=255)


@router.post("/dev-login")
async def dev_login(
    body: DevLoginRequest,
    response: Response,
) -> UserResponse:
    """
    Development-only endpoint to login with a GitHub Personal Access Token.

    This bypasses OAuth and is only for testing/development purposes.
    Credentials are accepted in the POST body (JSON), never in the URL.
    """
    from src.config import get_settings

    settings = get_settings()

    if not settings.debug:
        raise NotFoundError("Not Found")

    try:
        session = await github_auth_service.create_session_from_token(body.github_token)

        # Set the session cookie
        _set_session_cookie(response, str(session.session_id))

        logger.info("Dev login successful for user: %s", session.github_username)
        return UserResponse.from_session(session)

    except Exception as e:
        handle_service_error(e, "dev login", AuthenticationError)
