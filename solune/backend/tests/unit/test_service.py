"""Unit tests for GitHubProjectsService._with_fallback()."""

import pytest

from src.services.github_projects.service import GitHubProjectsService


class TestWithFallback:
    """Tests for _with_fallback() soft-failure contract."""

    @pytest.mark.asyncio
    async def test_primary_succeeds_without_verify(self):
        """Primary success without verify_fn should return primary result."""
        service = GitHubProjectsService()

        async def primary():
            return "primary_result"

        async def fallback():
            raise AssertionError("fallback should not be called")

        result = await service._with_fallback(primary, fallback, "test op")
        assert result == "primary_result"

    @pytest.mark.asyncio
    async def test_primary_succeeds_with_verify_passing(self):
        """Primary success + verify passes should return primary result."""
        service = GitHubProjectsService()

        async def primary():
            return "primary_result"

        async def verify():
            return True

        async def fallback():
            raise AssertionError("fallback should not be called")

        result = await service._with_fallback(primary, fallback, "test op", verify_fn=verify)
        assert result == "primary_result"

    @pytest.mark.asyncio
    async def test_primary_succeeds_verify_fails_fallback_succeeds(self):
        """Primary success + verify fails should call fallback and return its result."""
        service = GitHubProjectsService()

        async def primary():
            return "primary_result"

        async def verify():
            return False

        async def fallback():
            return "fallback_result"

        result = await service._with_fallback(primary, fallback, "test op", verify_fn=verify)
        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_primary_raises_fallback_succeeds(self):
        """Primary failure should call fallback and return its result."""
        service = GitHubProjectsService()

        async def primary():
            raise RuntimeError("primary failed")

        async def fallback():
            return "fallback_result"

        result = await service._with_fallback(primary, fallback, "test op")
        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_both_raise_returns_none(self):
        """Both primary and fallback failure should return None (soft-failure)."""
        service = GitHubProjectsService()

        async def primary():
            raise RuntimeError("primary failed")

        async def fallback():
            raise RuntimeError("fallback failed")

        result = await service._with_fallback(primary, fallback, "test op")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_raises_treated_as_failure_fallback_called(self):
        """verify_fn raising should be treated as failure, triggering fallback."""
        service = GitHubProjectsService()

        async def primary():
            return "primary_result"

        async def verify():
            raise RuntimeError("verify crashed")

        async def fallback():
            return "fallback_result"

        result = await service._with_fallback(primary, fallback, "test op", verify_fn=verify)
        assert result == "fallback_result"

    @pytest.mark.asyncio
    async def test_verify_fails_fallback_fails_returns_primary_result(self):
        """When verify fails and fallback also fails, return primary result."""
        service = GitHubProjectsService()

        async def primary():
            return "primary_result"

        async def verify():
            return False

        async def fallback():
            raise RuntimeError("fallback also failed")

        result = await service._with_fallback(primary, fallback, "test op", verify_fn=verify)
        assert result == "primary_result"
