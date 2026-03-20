"""GitHub OAuth authentication service."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID

from githubkit import GitHub, TokenAuthStrategy
from githubkit.retry import RETRY_RATE_LIMIT, RETRY_SERVER_ERROR, RetryChainDecision

from src.config import get_settings
from src.logging_utils import get_logger
from src.models.user import UserSession
from src.services.database import get_db
from src.services.session_store import (
    delete_session as store_delete_session,
)
from src.services.session_store import (
    get_session as store_get_session,
)
from src.services.session_store import (
    save_session as store_save_session,
)
from src.utils import BoundedDict

logger = get_logger(__name__)

# OAuth state storage — intentionally in-memory for single-instance MVP.
# Bounded to 1000 entries with TTL-based pruning to prevent unbounded growth.
# Data is lost on application restart, which is acceptable because OAuth state
# tokens are short-lived (10-minute TTL) and only needed during the active
# OAuth flow. Users simply re-initiate the OAuth flow after a restart.
_oauth_states: BoundedDict[str, datetime] = BoundedDict(maxlen=1000)

_OAUTH_STATE_TTL = timedelta(minutes=10)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"  # nosec B105
GITHUB_USER_API_URL = "https://api.github.com/user"


class GitHubAuthService:
    """Service for GitHub OAuth authentication."""

    def __init__(self):
        self.settings = get_settings()

    async def close(self):
        """No-op — SDK manages its own connections."""
        pass

    def generate_oauth_url(self) -> tuple[str, str]:
        """
        Generate GitHub OAuth authorization URL.

        Returns:
            Tuple of (authorization_url, state)
        """
        # Prune expired states on each generation to prevent stale buildup
        _prune_expired_states()

        state = secrets.token_urlsafe(32)
        _oauth_states[state] = datetime.now(UTC)

        params = {
            "client_id": self.settings.github_client_id,
            "redirect_uri": self.settings.github_redirect_uri,
            # The app creates issues, sub-issues, comments, labels, and PRs.
            # GitHub returns misleading 404s for many of those writes when the
            # OAuth token only has project/read scopes, so repository scope is
            # required here for the core workflow to function.
            "scope": "read:user read:org project repo",
            "state": state,
        }

        url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
        return url, state

    def validate_state(self, state: str) -> bool:
        """
        Validate OAuth state parameter.

        Args:
            state: OAuth state to validate

        Returns:
            True if state is valid and not expired
        """
        if state not in _oauth_states:
            return False

        created_at = _oauth_states.pop(state)
        # State expires after the configured TTL
        return datetime.now(UTC) - created_at < _OAUTH_STATE_TTL

    async def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from GitHub callback

        Returns:
            Token response containing access_token, refresh_token, expires_in
        """
        response = await GitHub(
            TokenAuthStrategy("placeholder"),
            auto_retry=RetryChainDecision(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR),
        ).arequest(
            "POST",
            GITHUB_TOKEN_URL,
            data={
                "client_id": self.settings.github_client_id,
                "client_secret": self.settings.github_client_secret,
                "code": code,
                "redirect_uri": self.settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        return response.json()

    async def get_github_user(self, access_token: str) -> dict:
        """
        Get GitHub user info using access token.

        Args:
            access_token: GitHub OAuth access token

        Returns:
            GitHub user data
        """
        github = GitHub(
            TokenAuthStrategy(access_token),
            auto_retry=RetryChainDecision(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR),
        )
        resp = await github.rest.users.async_get_authenticated()
        return resp.parsed_data.model_dump()

    async def create_session(self, code: str) -> UserSession:
        """
        Create user session from OAuth code.

        Args:
            code: Authorization code from GitHub callback

        Returns:
            Created user session
        """
        # Exchange code for token
        token_data = await self.exchange_code_for_token(code)

        if "error" in token_data:
            raise ValueError(
                f"OAuth error: {token_data.get('error_description', token_data['error'])}"
            )

        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        # Get user info
        user_data = await self.get_github_user(access_token)

        # Calculate token expiration
        token_expires_at = None
        if expires_in:
            token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        # Create session
        session = UserSession(
            github_user_id=str(user_data["id"]),
            github_username=user_data["login"],
            github_avatar_url=user_data.get("avatar_url"),
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
        )

        # Store session in SQLite
        db = get_db()
        await store_save_session(db, session)
        logger.info("Created session for user %s", session.github_username)

        return session

    async def refresh_token(self, session: UserSession) -> UserSession:
        """
        Refresh expired access token.

        Args:
            session: User session with expired token

        Returns:
            Updated session with new tokens
        """
        if not session.refresh_token:
            raise ValueError("No refresh token available")

        response = await GitHub(
            TokenAuthStrategy("placeholder"),
            auto_retry=RetryChainDecision(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR),
        ).arequest(
            "POST",
            GITHUB_TOKEN_URL,
            data={
                "client_id": self.settings.github_client_id,
                "client_secret": self.settings.github_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": session.refresh_token,
            },
            headers={"Accept": "application/json"},
        )
        token_data = response.json()

        if "error" in token_data:
            raise ValueError(
                f"Token refresh error: {token_data.get('error_description', token_data['error'])}"
            )

        # Update session
        session.access_token = token_data["access_token"]
        session.refresh_token = token_data.get("refresh_token", session.refresh_token)

        expires_in = token_data.get("expires_in")
        if expires_in:
            session.token_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        session.updated_at = datetime.now(UTC)
        db = get_db()
        await store_save_session(db, session)

        logger.info("Refreshed token for user %s", session.github_username)
        return session

    async def create_session_from_token(self, access_token: str) -> UserSession:
        """
        Create user session directly from a GitHub Personal Access Token.

        This is for development/testing purposes to bypass OAuth flow.

        Args:
            access_token: GitHub Personal Access Token

        Returns:
            Created user session
        """
        # Verify token by getting user info
        user_data = await self.get_github_user(access_token)

        # Create session (PATs don't have refresh tokens or expiration)
        session = UserSession(
            github_user_id=str(user_data["id"]),
            github_username=user_data["login"],
            github_avatar_url=user_data.get("avatar_url"),
            access_token=access_token,
            refresh_token=None,
            token_expires_at=None,  # PATs don't expire
        )

        # Store session in SQLite
        db = get_db()
        await store_save_session(db, session)
        logger.info("Created session from PAT for user %s", session.github_username)

        return session

    async def get_session(self, session_id: str | UUID) -> UserSession | None:
        """
        Get session by ID.

        Args:
            session_id: Session ID to lookup

        Returns:
            User session or None if not found/expired
        """
        db = get_db()
        return await store_get_session(db, session_id)

    async def update_session(self, session: UserSession) -> None:
        """
        Update session in storage.

        Args:
            session: Session to update
        """
        session.updated_at = datetime.now(UTC)
        db = get_db()
        await store_save_session(db, session)

    async def revoke_session(self, session_id: str | UUID) -> bool:
        """
        Revoke and remove session.

        Args:
            session_id: Session ID to revoke

        Returns:
            True if session was found and revoked
        """
        db = get_db()
        deleted = await store_delete_session(db, session_id)
        if deleted:
            logger.info("Revoked session %s", session_id)
        return deleted


def _prune_expired_states() -> None:
    """Remove expired OAuth states from the bounded dict."""
    now = datetime.now(UTC)
    expired = [k for k, v in _oauth_states.items() if now - v >= _OAUTH_STATE_TTL]
    for k in expired:
        _oauth_states.pop(k, None)


# Global service instance
github_auth_service = GitHubAuthService()
