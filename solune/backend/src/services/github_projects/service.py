from __future__ import annotations

import asyncio
import contextvars
import hashlib
import json as json_mod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeVar

from src.logging_utils import get_logger

if TYPE_CHECKING:
    from src.services.github_projects import GitHubClientFactory

# Domain mixins — method implementations live in separate files
from src.services.github_projects.agents import AgentsMixin
from src.services.github_projects.board import BoardMixin
from src.services.github_projects.branches import BranchesMixin
from src.services.github_projects.copilot import CopilotMixin
from src.services.github_projects.identities import (
    is_copilot_author as _is_copilot_author,
)
from src.services.github_projects.identities import (
    is_copilot_reviewer_bot as _is_copilot_reviewer_bot,
)
from src.services.github_projects.identities import (
    is_copilot_swe_agent as _is_copilot_swe_agent,
)
from src.services.github_projects.issues import IssuesMixin
from src.services.github_projects.projects import ProjectsMixin
from src.services.github_projects.pull_requests import PullRequestsMixin
from src.services.github_projects.repository import RepositoryMixin
from src.utils import BoundedDict

logger = get_logger(__name__)

_T = TypeVar("_T")

# Request-scoped storage for rate limit info.
_request_rate_limit: contextvars.ContextVar[dict[str, int] | None] = contextvars.ContextVar(
    "_request_rate_limit", default=None
)


class GitHubProjectsService(
    AgentsMixin,
    BoardMixin,
    BranchesMixin,
    CopilotMixin,
    IssuesMixin,
    ProjectsMixin,
    PullRequestsMixin,
    RepositoryMixin,
):
    """Service for interacting with GitHub Projects V2 API."""

    def __init__(self, client_factory: GitHubClientFactory | None = None):
        # Import here to avoid circular import at module level
        if client_factory is None:
            from src.services.github_projects import GitHubClientFactory

            client_factory = GitHubClientFactory()
        self._client_factory = client_factory
        self._last_rate_limit: dict[str, int] | None = None
        self._inflight_graphql: BoundedDict[str, asyncio.Task[dict]] = BoundedDict(
            maxlen=256,
            on_evict=self._cancel_evicted_graphql,
        )
        self._coalesced_hit_count: int = 0
        self._cycle_cache_hit_count: int = 0
        self._cycle_cache: dict[str, object] = {}

    def clear_cycle_cache(self) -> None:
        """Clear the per-poll-cycle cache.

        Must be called at the start of each polling loop iteration so
        that stale data from the previous cycle is never served.
        """
        if self._cycle_cache:
            logger.debug(
                "Clearing cycle cache (%d entries, %d hits this cycle)",
                len(self._cycle_cache),
                self._cycle_cache_hit_count,
            )
        self._cycle_cache.clear()
        self._cycle_cache_hit_count = 0

    @staticmethod
    def _cancel_evicted_graphql(_key: str, task: asyncio.Task) -> None:  # type: ignore[type-arg]
        """Cancel an evicted GraphQL task that hasn't finished yet."""
        if not task.done():
            task.cancel()

    def _invalidate_cycle_cache(self, *keys: str) -> None:
        """Remove specific entries from the cycle cache after a write."""
        for key in keys:
            self._cycle_cache.pop(key, None)

    async def _rest(
        self,
        access_token: str,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict | list | str:
        """Execute a REST API call via the SDK client.

        Routes through githubkit for automatic retry, throttling, and auth.
        Returns parsed JSON or raw text for non-JSON responses.
        """
        client = await self._client_factory.get_client(access_token)
        kwargs: dict = {}
        if json is not None:
            kwargs["json"] = json
        if params is not None:
            kwargs["params"] = params
        if headers is not None:
            kwargs["headers"] = headers
        response = await client.arequest(method, path, **kwargs)
        # Extract rate-limit headers from REST responses
        try:
            limit = response.headers.get("X-RateLimit-Limit")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset_at = response.headers.get("X-RateLimit-Reset")
            if limit is not None and remaining is not None and reset_at is not None:
                info: dict[str, int] = {
                    "limit": int(limit),
                    "remaining": int(remaining),
                    "reset_at": int(reset_at),
                    "used": int(limit) - int(remaining),
                }
                _request_rate_limit.set(info)
                self._last_rate_limit = info
        except (ValueError, TypeError):
            pass
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    async def _rest_response(
        self,
        access_token: str,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
    ):
        """Execute a REST API call and return the raw SDK Response.

        Used when callers need to check status_code or headers directly.
        """
        client = await self._client_factory.get_client(access_token)
        kwargs: dict = {}
        if json is not None:
            kwargs["json"] = json
        if params is not None:
            kwargs["params"] = params
        if headers is not None:
            kwargs["headers"] = headers
        response = await client.arequest(method, path, **kwargs)
        # Extract rate-limit headers
        try:
            limit = response.headers.get("X-RateLimit-Limit")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset_at = response.headers.get("X-RateLimit-Reset")
            if limit is not None and remaining is not None and reset_at is not None:
                info_rl: dict[str, int] = {
                    "limit": int(limit),
                    "remaining": int(remaining),
                    "reset_at": int(reset_at),
                    "used": int(limit) - int(remaining),
                }
                _request_rate_limit.set(info_rl)
                self._last_rate_limit = info_rl
        except (ValueError, TypeError):
            pass
        return response

    async def close(self):
        """Close SDK client pool."""
        await self._client_factory.close_all()

    async def rest_request(
        self,
        access_token: str,
        method: str,
        path: str,
        **kwargs,
    ):
        """Public REST request — for code outside this module that needs GitHub REST access."""
        return await self._rest_response(access_token, method, path, **kwargs)

    async def _with_fallback(
        self,
        primary_fn: Callable[[], Awaitable[_T]],
        fallback_fn: Callable[[], Awaitable[_T]],
        context_msg: str,
    ) -> tuple[_T, str]:
        """Execute primary_fn, falling back to fallback_fn on failure.

        Both strategies are logged. If both fail, raises with context from
        both exceptions.

        Returns:
            Tuple of (result, strategy_used) where strategy_used is
            "primary" or "fallback".
        """
        try:
            result = await primary_fn()
            return result, "primary"
        except Exception as primary_err:
            logger.warning(
                "%s: primary strategy failed (%s), trying fallback",
                context_msg,
                primary_err,
            )
            try:
                result = await fallback_fn()
                logger.info("%s: fallback strategy succeeded", context_msg)
                return result, "fallback"
            except Exception as fallback_err:
                raise RuntimeError(
                    f"{context_msg}: both strategies failed. "
                    f"Primary: {primary_err}; Fallback: {fallback_err}"
                ) from fallback_err

    @staticmethod
    def is_copilot_author(login: str) -> bool:
        return _is_copilot_author(login)

    @staticmethod
    def is_copilot_swe_agent(login: str) -> bool:
        return _is_copilot_swe_agent(login)

    @staticmethod
    def is_copilot_reviewer_bot(login: str) -> bool:
        return _is_copilot_reviewer_bot(login)

    def get_last_rate_limit(self) -> dict[str, int] | None:
        """Return the most recent rate limit info for the current request.

        Prefers the request-scoped context var (safe under concurrency),
        falling back to the instance-level value for callers outside an
        async request context.
        """
        return _request_rate_limit.get() or self._last_rate_limit

    def clear_last_rate_limit(self) -> None:
        """Clear both the request-scoped contextvar and instance-level rate-limit caches.

        Called by the polling loop when stale rate-limit data is detected
        (e.g. the reset window has already passed but the cached remaining
        count is still zero).  Both caches must be cleared because
        ``get_last_rate_limit`` prefers the contextvar — clearing only
        the instance attribute would leave stale data in the contextvar,
        causing the polling loop to re-read it and enter an infinite
        pause/sleep cycle.
        """
        _request_rate_limit.set(None)
        self._last_rate_limit = None

    # ──────────────────────────────────────────────────────────────────
    # T057: Rate limit handling with exponential backoff
    # ──────────────────────────────────────────────────────────────────
    async def _graphql(
        self,
        access_token: str,
        query: str,
        variables: dict,
        extra_headers: dict | None = None,
        graphql_features: list[str] | None = None,
    ) -> dict:
        """Execute GraphQL query against GitHub API via githubkit SDK.

        Uses the SDK's async_graphql() for standard calls. For calls requiring
        custom headers (e.g. GraphQL-Features for Copilot assignment), routes
        through arequest() instead. Preserves inflight request coalescing.
        """
        # Build a stable cache key for inflight coalescing
        token_prefix = hashlib.sha256(access_token.encode()).hexdigest()[:16]
        cache_key = hashlib.sha256(
            (
                token_prefix
                + query
                + json_mod.dumps(
                    {
                        "variables": variables,
                        "features": graphql_features or [],
                        "extra_headers": sorted((extra_headers or {}).items()),
                    },
                    sort_keys=True,
                )
            ).encode()
        ).hexdigest()

        # Inflight coalescing — reuse in-progress identical request
        inflight = self._inflight_graphql.get(cache_key)
        if inflight:
            self._coalesced_hit_count += 1
            logger.debug("GraphQL in-flight coalescing hit for key %s…", cache_key[:12])
            return await inflight

        async def _execute_graphql() -> dict:
            from src.config import get_settings

            timeout = get_settings().api_timeout_seconds
            client = await self._client_factory.get_client(access_token)

            async def _inner() -> dict:
                if graphql_features or extra_headers:
                    # Custom headers required — use arequest() for full control
                    headers: dict[str, str] = {}
                    if extra_headers:
                        headers.update(extra_headers)
                    if graphql_features:
                        headers["GraphQL-Features"] = ",".join(graphql_features)
                    response = await client.arequest(
                        "POST",
                        "/graphql",
                        json={"query": query, "variables": variables},
                        headers=headers,
                    )
                    result = response.json()
                    if "errors" in result:
                        error_msg = "; ".join(e.get("message", str(e)) for e in result["errors"])
                        logger.error("GraphQL error: %s", error_msg)
                        raise ValueError("GitHub API request failed")
                    return result.get("data", {})
                else:
                    # Standard GraphQL — SDK handles auth, retry, cache, errors
                    return await client.async_graphql(query, variables=variables)

            try:
                return await asyncio.wait_for(_inner(), timeout=timeout)
            except TimeoutError:
                from src.exceptions import GitHubAPIError

                raise GitHubAPIError(
                    "GitHub GraphQL request timed out",
                    details={"timeout_seconds": timeout},
                ) from None

        from src.services.task_registry import task_registry

        task: asyncio.Task[dict] = task_registry.create_task(
            _execute_graphql(), name=f"graphql-{cache_key[:16]}"
        )
        self._inflight_graphql[cache_key] = task
        try:
            return await task
        finally:
            current = self._inflight_graphql.get(cache_key)
            if current is task:
                self._inflight_graphql.pop(cache_key, None)


# TODO(018-codebase-audit-refactor): Module-level singleton should be removed
# in favor of exclusive app.state registration. Deferred because 17+ files
# import this directly in non-request contexts (background tasks, signal bridge,
# orchestrator) where Request.app.state is not available.
# Global service instance
github_projects_service = GitHubProjectsService()
