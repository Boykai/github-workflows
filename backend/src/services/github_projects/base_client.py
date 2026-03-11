"""Shared HTTP infrastructure for GitHub API domain services.

Provides ``_rest``, ``_rest_response``, ``_graphql``, and ``_with_fallback``
methods that all domain-specific mixins rely on.  Extracted from the former
monolithic ``GitHubProjectsService`` so that rate-limit tracking, ETag
caching, request coalescing, and retry logic live in a single place.
"""

from __future__ import annotations

import asyncio
import hashlib
import json as json_mod
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, TypeVar

from src.logging_utils import get_logger
from src.services.github_projects.rate_limit import RateLimitManager
from src.utils import BoundedDict

if TYPE_CHECKING:
    from src.services.github_projects import GitHubClientFactory

logger = get_logger(__name__)

_T = TypeVar("_T")


class GitHubBaseClient:
    """Base client providing GitHub API HTTP infrastructure.

    Handles authentication (via *GitHubClientFactory*), rate-limit tracking,
    request coalescing, and retry/fallback logic.  Domain mixins
    (``IssuesMixin``, ``BranchesMixin``, …) call ``self._rest()``,
    ``self._graphql()``, etc. which resolve here.
    """

    def __init__(self, client_factory: GitHubClientFactory | None = None) -> None:
        if client_factory is None:
            from src.services.github_projects import GitHubClientFactory

            client_factory = GitHubClientFactory()
        self._client_factory = client_factory
        self._rate_limit = RateLimitManager()
        self._inflight_graphql: BoundedDict[str, asyncio.Task[dict]] = BoundedDict(maxlen=256)
        self._coalesced_hit_count: int = 0
        self._cycle_cache_hit_count: int = 0
        self._cycle_cache: dict[str, object] = {}

    # ------------------------------------------------------------------
    # Cycle cache helpers
    # ------------------------------------------------------------------

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

    def _invalidate_cycle_cache(self, *keys: str) -> None:
        """Remove specific entries from the cycle cache after a write."""
        for key in keys:
            self._cycle_cache.pop(key, None)

    # ------------------------------------------------------------------
    # REST helpers
    # ------------------------------------------------------------------

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
        self._rate_limit.extract_from_headers(response.headers)
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
        self._rate_limit.extract_from_headers(response.headers)
        return response

    async def rest_request(
        self,
        access_token: str,
        method: str,
        path: str,
        **kwargs,
    ):
        """Public REST request — for code outside this module."""
        return await self._rest_response(access_token, method, path, **kwargs)

    # ------------------------------------------------------------------
    # Fallback helper
    # ------------------------------------------------------------------

    async def _with_fallback(
        self,
        primary_fn: Callable[[], Awaitable[_T]],
        fallback_fn: Callable[[], Awaitable[_T]],
        context_msg: str,
    ) -> tuple[_T, str]:
        """Execute *primary_fn*, falling back to *fallback_fn* on failure.

        Returns:
            Tuple of ``(result, strategy_used)`` where *strategy_used* is
            ``"primary"`` or ``"fallback"``.
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

    # ------------------------------------------------------------------
    # GraphQL
    # ------------------------------------------------------------------

    async def _graphql(
        self,
        access_token: str,
        query: str,
        variables: dict,
        extra_headers: dict | None = None,
        graphql_features: list[str] | None = None,
    ) -> dict:
        """Execute GraphQL query against GitHub API via githubkit SDK.

        Uses the SDK's ``async_graphql()`` for standard calls. For calls
        requiring custom headers (e.g. GraphQL-Features for Copilot
        assignment), routes through ``arequest()`` instead.  Preserves
        inflight request coalescing.
        """
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

        inflight = self._inflight_graphql.get(cache_key)
        if inflight:
            self._coalesced_hit_count += 1
            logger.debug("GraphQL in-flight coalescing hit for key %s…", cache_key[:12])
            return await inflight

        async def _execute_graphql() -> dict:
            client = await self._client_factory.get_client(access_token)

            if graphql_features or extra_headers:
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
                data = result.get("data", {})
            else:
                data = await client.async_graphql(query, variables=variables)

            return data

        task: asyncio.Task[dict] = asyncio.create_task(_execute_graphql())
        self._inflight_graphql[cache_key] = task
        try:
            return await task
        finally:
            current = self._inflight_graphql.get(cache_key)
            if current is task:
                self._inflight_graphql.pop(cache_key, None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close SDK client pool."""
        await self._client_factory.close_all()
