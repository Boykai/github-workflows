"""Tests for issue creation retry with backoff.

The create_issue method should use exponential backoff retry logic
for transient failures (429, 503) to match the existing _request_with_retry
pattern used elsewhere in GitHubProjectsService.

Covers: FR-008
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.services.github_projects.service import GitHubProjectsService


class TestIssueCreationRetry:
    """create_issue should retry on transient HTTP errors."""

    @pytest.fixture
    def service(self):
        """Create a GitHubProjectsService instance with a mocked client."""
        svc = GitHubProjectsService()
        svc._client = AsyncMock(spec=httpx.AsyncClient)
        return svc

    @pytest.mark.asyncio
    async def test_create_issue_retries_on_503(self, service):
        """Issue creation retries on 503 Service Unavailable.

        First call returns 503, second call succeeds.
        """
        fail_response = httpx.Response(
            status_code=503,
            request=httpx.Request("POST", "https://api.github.com/repos/o/r/issues"),
        )
        success_response = httpx.Response(
            status_code=201,
            json={
                "id": 1,
                "node_id": "I_1",
                "number": 42,
                "html_url": "https://github.com/o/r/issues/42",
            },
            request=httpx.Request("POST", "https://api.github.com/repos/o/r/issues"),
        )

        service._client.post.side_effect = [fail_response, success_response]

        # Patch asyncio.sleep to avoid real delays
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await service.create_issue(
                access_token="test-token",
                owner="o",
                repo="r",
                title="Test Issue",
                body="Test body",
            )

        assert result["number"] == 42
        # Should have been called more than once (retried)
        assert service._client.post.call_count >= 2

    @pytest.mark.asyncio
    async def test_create_issue_retries_on_429(self, service):
        """Issue creation retries on 429 Too Many Requests."""
        fail_response = httpx.Response(
            status_code=429,
            headers={"Retry-After": "1"},
            request=httpx.Request("POST", "https://api.github.com/repos/o/r/issues"),
        )
        success_response = httpx.Response(
            status_code=201,
            json={
                "id": 2,
                "node_id": "I_2",
                "number": 43,
                "html_url": "https://github.com/o/r/issues/43",
            },
            request=httpx.Request("POST", "https://api.github.com/repos/o/r/issues"),
        )

        service._client.post.side_effect = [fail_response, success_response]

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await service.create_issue(
                access_token="test-token",
                owner="o",
                repo="r",
                title="Test Issue",
                body="Test body",
            )

        assert result["number"] == 43
        assert service._client.post.call_count >= 2

    @pytest.mark.asyncio
    async def test_create_issue_succeeds_without_retry(self, service):
        """Issue creation succeeds on first attempt — no retry needed."""
        success_response = httpx.Response(
            status_code=201,
            json={
                "id": 3,
                "node_id": "I_3",
                "number": 44,
                "html_url": "https://github.com/o/r/issues/44",
            },
            request=httpx.Request("POST", "https://api.github.com/repos/o/r/issues"),
        )

        service._client.post.return_value = success_response

        result = await service.create_issue(
            access_token="test-token",
            owner="o",
            repo="r",
            title="Test Issue",
            body="Test body",
        )

        assert result["number"] == 44
        assert service._client.post.call_count == 1

    @pytest.mark.asyncio
    async def test_create_issue_raises_after_max_retries(self, service):
        """Issue creation raises after exhausting retries."""
        fail_response = httpx.Response(
            status_code=503,
            request=httpx.Request("POST", "https://api.github.com/repos/o/r/issues"),
        )

        # Always return 503
        service._client.post.return_value = fail_response

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.HTTPStatusError):
                await service.create_issue(
                    access_token="test-token",
                    owner="o",
                    repo="r",
                    title="Test Issue",
                    body="Test body",
                )
