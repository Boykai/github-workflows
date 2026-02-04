"""Authentication API endpoints - OAuth flow."""

import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from src.constants import SESSION_COOKIE_NAME
from src.exceptions import AuthenticationError
from src.models.user import UserResponse, UserSession
from src.services.github_auth import github_auth_service

logger = logging.getLogger(__name__)
router = APIRouter()


def get_current_session(session_id: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)) -> UserSession:
    """Get current user session from cookie."""
    if not session_id:
        raise AuthenticationError("No session cookie")

    session = github_auth_service.get_session(session_id)
    if not session:
        raise AuthenticationError("Invalid or expired session")

    return session


async def get_session_dep(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> UserSession:
    """Dependency for getting current session from cookie."""
    return get_current_session(session_id)


@router.get("/github")
async def initiate_github_oauth() -> RedirectResponse:
    """Initiate GitHub OAuth flow by redirecting to GitHub authorization."""
    url, _state = github_auth_service.generate_oauth_url()
    logger.info("Redirecting to GitHub OAuth: %s", url[:50])
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/github/callback")
async def github_callback(
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state",
        )

    try:
        # Create session
        session = await github_auth_service.create_session(code)

        # Get frontend URL from settings (default: http://localhost:5173)
        frontend_url = settings.frontend_url
        
        # Redirect to frontend with session token in URL
        # Frontend will call /auth/session to set the cookie via the proxy
        redirect_url = f"{frontend_url}?session_token={session.session_id}"
        
        redirect = RedirectResponse(
            url=redirect_url,
            status_code=status.HTTP_302_FOUND,
        )

        logger.info("Created session for user: %s, redirecting to frontend", session.github_username)
        return redirect

    except ValueError as e:
        logger.error("OAuth error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Failed to create session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete authentication",
        )


@router.post("/session")
async def set_session_cookie(
    response: Response,
    session_token: Annotated[str, Query(description="Session token from OAuth callback")],
) -> UserResponse:
    """
    Set session cookie from token.
    
    Called by frontend after OAuth callback to set cookie via proxy.
    This ensures the cookie is associated with the frontend's origin.
    """
    session = github_auth_service.get_session(session_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )
    
    # Set the session cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=str(session.session_id),
        httponly=True,
        secure=False,  # Allow HTTP for development
        samesite="lax",
        max_age=8 * 60 * 60,  # 8 hours
        path="/",
    )
    
    logger.info("Set session cookie for user: %s", session.github_username)
    return UserResponse.from_session(session)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> UserResponse:
    """Get current authenticated user."""
    session = get_current_session(session_id)
    return UserResponse.from_session(session)


@router.post("/logout")
async def logout(
    response: Response,
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> dict:
    """Logout current user by revoking session."""
    if session_id:
        github_auth_service.revoke_session(session_id)

    response.delete_cookie(key=SESSION_COOKIE_NAME)
    return {"message": "Logged out successfully"}


@router.post("/dev-login")
async def dev_login(
    response: Response,
    github_token: str = Query(..., description="GitHub Personal Access Token"),
) -> UserResponse:
    """
    Development-only endpoint to login with a GitHub Personal Access Token.
    
    This bypasses OAuth and is only for testing/development purposes.
    """
    from src.config import get_settings
    settings = get_settings()
    
    if not settings.debug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Dev login is only available in debug mode",
        )
    
    try:
        session = await github_auth_service.create_session_from_token(github_token)
        
        # Set the session cookie
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=str(session.session_id),
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=8 * 60 * 60,
            path="/",
        )
        
        logger.info("Dev login successful for user: %s", session.github_username)
        return UserResponse.from_session(session)
        
    except Exception as e:
        logger.error("Dev login failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid GitHub token: {e}",
        )
