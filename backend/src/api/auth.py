"""Authentication API endpoints - OAuth flow."""

import logging
import re
from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Query, Response, status
from fastapi.responses import RedirectResponse

from src.exceptions import AuthenticationError
from src.models.user import ProfileUpdateRequest, UserResponse, UserSession
from src.services.github_auth import github_auth_service

logger = logging.getLogger(__name__)
router = APIRouter()

SESSION_COOKIE_NAME = "session_id"
EMAIL_VALIDATION_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'


def get_current_session(session_id: str | None = Cookie(None, alias=SESSION_COOKIE_NAME)) -> UserSession:
    """Get current user session from cookie."""
    if not session_id:
        raise AuthenticationError("No session cookie")

    session = github_auth_service.get_session(session_id)
    if not session:
        raise AuthenticationError("Invalid or expired session")

    return session


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

        # Get frontend URL from settings or default
        frontend_url = getattr(settings, 'frontend_url', 'http://localhost:3003')
        
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


@router.patch("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> UserResponse:
    """
    Update user profile information.
    
    Validates and updates user profile fields like name, email, bio, and location.
    """
    session = get_current_session(session_id)
    
    # Validate email format if provided
    if profile_data.email is not None:
        email = profile_data.email.strip()
        if email:  # Only validate if not empty
            if not re.match(EMAIL_VALIDATION_PATTERN, email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format",
                )
    
    # Update session with new profile data
    if profile_data.name is not None:
        session.name = profile_data.name.strip() or None
    if profile_data.email is not None:
        session.email = profile_data.email.strip() or None
    if profile_data.bio is not None:
        session.bio = profile_data.bio.strip() or None
    if profile_data.location is not None:
        session.location = profile_data.location.strip() or None
    
    # Save updated session
    github_auth_service.update_session(session)
    
    logger.info("Updated profile for user: %s", session.github_username)
    return UserResponse.from_session(session)
