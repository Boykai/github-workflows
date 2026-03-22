from __future__ import annotations

import asyncio

import httpx
import pytest

from src.services.github_projects.service import GitHubProjectsService


@pytest.mark.asyncio
async def test_with_fallback_returns_fallback_result_after_primary_failure() -> None:
    service = GitHubProjectsService()

    async def primary() -> dict[str, str]:
        raise TimeoutError("primary timed out")

    async def fallback() -> dict[str, str]:
        return {"status": "fallback"}

    result = await service._with_fallback(primary, fallback, "load projects")

    assert result == {"status": "fallback"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [ConnectionError("network down"), httpx.ReadTimeout("timeout")],
)
async def test_with_fallback_returns_none_when_both_strategies_fail(error: BaseException) -> None:
    service = GitHubProjectsService()

    async def primary() -> dict[str, str]:
        raise error

    async def fallback() -> dict[str, str]:
        raise RuntimeError("fallback failed")

    result = await service._with_fallback(primary, fallback, "sync repository")
    assert result is None


@pytest.mark.asyncio
async def test_with_fallback_propagates_cancellation_without_running_fallback() -> None:
    service = GitHubProjectsService()

    async def primary() -> dict[str, str]:
        raise asyncio.CancelledError()

    async def fallback() -> dict[str, str]:
        raise AssertionError("fallback should not run when the primary task is cancelled")

    # CancelledError is a BaseException, not Exception, so it propagates
    with pytest.raises(asyncio.CancelledError):
        await service._with_fallback(primary, fallback, "sync repository")
