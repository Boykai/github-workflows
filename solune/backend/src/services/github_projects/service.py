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

    async def _cycle_cached(self, cache_key: str, fetch_fn: Callable[[], Awaitable[_T]]) -> _T:
        """Return a cached result or call *fetch_fn*, store the result and return it.

        Encapsulates the per-poll-cycle memoisation pattern used across
        multiple service methods:

        1. ``self._cycle_cache.get(cache_key)``
        2. On hit → increment ``_cycle_cache_hit_count`` and return.
        3. On miss → ``await fetch_fn()``, store in ``_cycle_cache``, return.

        The caller is responsible for error handling — if *fetch_fn* raises,
        the exception propagates without storing a value in the cache.
        """
        cached = self._cycle_cache.get(cache_key)
        if cached is not None:
            self._cycle_cache_hit_count += 1
            return cached  # type: ignore[return-value]
        result = await fetch_fn()
        self._cycle_cache[cache_key] = result
        return result

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
        self._extract_rate_limit_headers(response)
        # Detect secondary rate limit (abuse detection) on REST calls
        retry_after = response.headers.get("Retry-After")
        if retry_after and response.status_code in (403, 429):
            wait = int(retry_after) if retry_after.isdigit() else 60
            logger.warning(
                "GitHub secondary rate limit on REST %s %s (status=%d, Retry-After=%s). "
                "Waiting %ds before raising.",
                method,
                path,
                response.status_code,
                retry_after,
                wait,
            )
            await asyncio.sleep(wait)
            from src.exceptions import RateLimitError

            raise RateLimitError(
                "GitHub secondary rate limit exceeded",
                retry_after=wait,
            )
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
        from githubkit.exception import RequestFailed

        client = await self._client_factory.get_client(access_token)
        kwargs: dict = {}
        if json is not None:
            kwargs["json"] = json
        if params is not None:
            kwargs["params"] = params
        if headers is not None:
            kwargs["headers"] = headers
        try:
            response = await client.arequest(method, path, **kwargs)
        except RequestFailed as exc:
            # githubkit raises on non-2xx; return the Response so callers
            # can inspect status_code / body as originally intended.
            response = exc.response
        # Extract rate-limit headers
        self._extract_rate_limit_headers(response)
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
        operation: str,
        verify_fn: Callable[[], Awaitable[bool]] | None = None,
    ) -> _T | None:
        """Execute *primary_fn*, optionally verify, then fall back on failure.

        Implements the primary → verify → fallback resilience pattern with
        a **soft-failure contract**: returns ``None`` only when primary
        itself raises **and** fallback also fails.  Never raises exceptions
        to the caller.

        Flow:
        1. Call *primary_fn()*.  If it succeeds **and** either no *verify_fn*
           is provided or *verify_fn()* returns ``True``, the primary result
           is returned.
        2. If *verify_fn* returns ``False`` / raises, call *fallback_fn()*.
           If fallback succeeds, return its result; if fallback also fails,
           return the primary result (primary did succeed, verification was
           merely advisory).
        3. If *primary_fn* itself raises, call *fallback_fn()*.  If fallback
           succeeds, return its result; if fallback also fails, return
           ``None`` (total failure).

        All exceptions in primary, verify, and fallback paths are caught
        and logged — the caller never sees them.

        Args:
            primary_fn: Async callable (no args) for the primary strategy.
            fallback_fn: Async callable (no args) for the fallback strategy.
            operation: Human-readable description of the operation (for logs).
            verify_fn: Optional async callable that returns ``True`` when
                the primary result should be accepted.

        Returns:
            The result from *primary_fn* or *fallback_fn*, or ``None``
            when both strategies fail.
        """
        try:
            result = await primary_fn()

            if verify_fn is not None:
                try:
                    verified = await verify_fn()
                except Exception as verify_err:
                    logger.warning(
                        "%s: verification failed (%s), trying fallback",
                        operation,
                        verify_err,
                    )
                    verified = False

                if not verified:
                    logger.warning(
                        "%s: primary succeeded but verification failed, trying fallback",
                        operation,
                    )
                    try:
                        fallback_result = await fallback_fn()
                        logger.info("%s: fallback strategy succeeded", operation)
                        return fallback_result
                    except Exception as fallback_err:
                        logger.warning(
                            "%s: fallback also failed (%s), returning primary result",
                            operation,
                            fallback_err,
                        )
                        return result

            return result
        except Exception as primary_err:
            logger.warning(
                "%s: primary strategy failed (%s), trying fallback",
                operation,
                primary_err,
                exc_info=True,
            )
            try:
                result = await fallback_fn()
                logger.info("%s: fallback strategy succeeded", operation)
                return result
            except Exception as fallback_err:
                logger.warning(
                    "%s: both strategies failed. Primary: %s; Fallback: %s",
                    operation,
                    primary_err,
                    fallback_err,
                    exc_info=True,
                )
                return None

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

    def _extract_rate_limit_headers(self, response) -> None:
        """Extract rate-limit headers from any HTTP response (REST or GraphQL)."""
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
                    # Extract rate-limit headers from GraphQL responses
                    self._extract_rate_limit_headers(response)
                    # Detect secondary rate limit (abuse detection)
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and response.status_code in (403, 429):
                        wait = int(retry_after) if retry_after.isdigit() else 60
                        logger.warning(
                            "GitHub secondary rate limit hit (status=%d, Retry-After=%s). "
                            "Waiting %ds before raising.",
                            response.status_code,
                            retry_after,
                            wait,
                        )
                        await asyncio.sleep(wait)
                        from src.exceptions import RateLimitError

                        raise RateLimitError(
                            "GitHub secondary rate limit exceeded",
                            retry_after=wait,
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
#
# FR-008 (001-code-quality-tech-debt) explicitly defers this to a follow-up PR.
# Required scope for that PR:
#   1. Audit all 17+ consuming files (background tasks, signal bridge,
#      orchestrator, polling loops).
#   2. Introduce a get_github_service() accessor pattern that returns the
#      singleton from app.state in request contexts and falls back to the
#      module-level instance in non-request contexts.
#   3. Update all affected test mocks to use the accessor.
# Global service instance
github_projects_service = GitHubProjectsService()
