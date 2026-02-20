"""HTTP client infrastructure for GitHub Projects service."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import httpx

from .graphql_queries import (
    GITHUB_GRAPHQL_URL,
    INITIAL_BACKOFF_SECONDS,
    MAX_BACKOFF_SECONDS,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)


class GitHubClientMixin:
    """HTTP client and GraphQL infrastructure."""

    _client: httpx.AsyncClient

    def __init__(self):
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    # ──────────────────────────────────────────────────────────────────
    # T057: Rate limit handling with exponential backoff
    # ──────────────────────────────────────────────────────────────────
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        headers: dict,
        json: dict | None = None,
    ) -> httpx.Response:
        """
        Make HTTP request with exponential backoff on rate limits.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Request URL
            headers: Request headers
            json: Optional JSON body

        Returns:
            Response object

        Raises:
            httpx.HTTPStatusError: If request fails after retries
        """
        backoff = INITIAL_BACKOFF_SECONDS

        for attempt in range(MAX_RETRIES + 1):
            try:
                if method.upper() == "GET":
                    response = await self._client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await self._client.post(url, json=json, headers=headers)
                elif method.upper() == "PATCH":
                    response = await self._client.patch(url, json=json, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                # Check for rate limit
                if response.status_code == 403:
                    remaining = response.headers.get("X-RateLimit-Remaining", "0")
                    if remaining == "0":
                        reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
                        wait_seconds = max(reset_time - int(datetime.utcnow().timestamp()), backoff)
                        wait_seconds = min(wait_seconds, MAX_BACKOFF_SECONDS)

                        logger.warning(
                            "Rate limited. Waiting %d seconds before retry %d/%d",
                            wait_seconds,
                            attempt + 1,
                            MAX_RETRIES,
                        )
                        await asyncio.sleep(wait_seconds)
                        backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                        continue

                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503) and attempt < MAX_RETRIES:
                    logger.warning(
                        "Request failed with %d. Retrying in %d seconds (%d/%d)",
                        e.response.status_code,
                        backoff,
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)
                else:
                    raise

        raise httpx.HTTPStatusError(
            "Max retries exceeded",
            request=httpx.Request("GET", ""),  # type: ignore[arg-type]
            response=httpx.Response(500),
        )

    async def _graphql(
        self,
        access_token: str,
        query: str,
        variables: dict,
        extra_headers: dict | None = None,
    ) -> dict:
        """
        Execute GraphQL query against GitHub API.

        Args:
            access_token: GitHub OAuth access token
            query: GraphQL query string
            variables: Query variables
            extra_headers: Optional extra headers (e.g., for Copilot assignment)

        Returns:
            GraphQL response data
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if extra_headers:
            headers.update(extra_headers)

        response = await self._client.post(
            GITHUB_GRAPHQL_URL,
            json={"query": query, "variables": variables},
            headers=headers,
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            error_msg = "; ".join(e.get("message", str(e)) for e in result["errors"])
            raise ValueError(f"GraphQL error: {error_msg}")

        return result.get("data", {})
