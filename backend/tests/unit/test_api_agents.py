"""Tests for agents API routes (src/api/agents.py).

Regression tests for bug-bash security fixes:
- Error messages in API responses must not leak internal exception details.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.agents import (
    Agent,
    AgentCreateResult,
    AgentDeleteResult,
    AgentSource,
    AgentStatus,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_agent(**kw) -> Agent:
    defaults = {
        "id": "agent-1",
        "name": "Test Agent",
        "slug": "test-agent",
        "description": "A test agent",
        "system_prompt": "You are a test agent.",
        "status": AgentStatus.ACTIVE,
        "tools": [],
        "source": AgentSource.LOCAL,
    }
    defaults.update(kw)
    return Agent(**defaults)


def _make_create_result(**kw) -> AgentCreateResult:
    defaults = {
        "agent": _make_agent(),
        "pr_url": "https://github.com/owner/repo/pull/1",
        "pr_number": 1,
        "branch_name": "agents/test-agent",
    }
    defaults.update(kw)
    return AgentCreateResult(**defaults)


def _make_delete_result(**kw) -> AgentDeleteResult:
    defaults = {
        "success": True,
        "pr_url": "https://github.com/owner/repo/pull/2",
        "pr_number": 2,
        "branch_name": "agents/delete-test-agent",
    }
    defaults.update(kw)
    return AgentDeleteResult(**defaults)


# ── Security: Error Detail Leak Regression Tests ────────────────────────────


@pytest.mark.asyncio
class TestAgentsErrorLeakRegression:
    """Verify that agents API never leaks internal exception text in HTTP responses."""

    async def test_create_agent_value_error_does_not_leak(self, client):
        """POST create_agent ValueError must not expose exception text."""
        mock_svc = AsyncMock()
        mock_svc.create_agent.side_effect = ValueError(
            "Invalid slug: contains /etc/passwd path traversal"
        )
        with (
            patch("src.api.agents.resolve_repository", return_value=("owner", "repo")),
            patch("src.api.agents._get_service", return_value=mock_svc),
        ):
            resp = await client.post(
                "/api/v1/agents/PVT_test",
                json={
                    "name": "Bad Agent",
                    "system_prompt": "test prompt",
                },
            )
        assert resp.status_code == 400
        body = resp.json()
        assert "/etc/passwd" not in str(body)
        assert "path traversal" not in str(body)
        assert body["detail"] == "Invalid agent configuration"

    async def test_update_agent_value_error_does_not_leak(self, client):
        """PATCH update_agent ValueError must not expose exception text."""
        mock_svc = AsyncMock()
        mock_svc.update_agent.side_effect = ValueError(
            "Sensitive internal error: DB connection string leaked"
        )
        with (
            patch("src.api.agents.resolve_repository", return_value=("owner", "repo")),
            patch("src.api.agents._get_service", return_value=mock_svc),
        ):
            resp = await client.patch(
                "/api/v1/agents/PVT_test/agent-1",
                json={"name": "Updated Agent"},
            )
        assert resp.status_code == 400
        body = resp.json()
        assert "DB connection" not in str(body)
        assert "Sensitive" not in str(body)

    async def test_update_agent_lookup_error_does_not_leak(self, client):
        """PATCH update_agent LookupError must not expose exception text."""
        mock_svc = AsyncMock()
        mock_svc.update_agent.side_effect = LookupError(
            "Agent file not found at /home/user/.secrets/agent.yaml"
        )
        with (
            patch("src.api.agents.resolve_repository", return_value=("owner", "repo")),
            patch("src.api.agents._get_service", return_value=mock_svc),
        ):
            resp = await client.patch(
                "/api/v1/agents/PVT_test/agent-1",
                json={"name": "Updated Agent"},
            )
        assert resp.status_code == 404
        body = resp.json()
        assert "/home/user/.secrets" not in str(body)
        assert body["detail"] == "Agent not found"

    async def test_delete_agent_value_error_does_not_leak(self, client):
        """DELETE delete_agent ValueError must not expose exception text."""
        mock_svc = AsyncMock()
        mock_svc.delete_agent.side_effect = ValueError(
            "Invalid agent_id: SQL injection attempt ' OR 1=1 --"
        )
        with (
            patch("src.api.agents.resolve_repository", return_value=("owner", "repo")),
            patch("src.api.agents._get_service", return_value=mock_svc),
        ):
            resp = await client.delete("/api/v1/agents/PVT_test/agent-1")
        assert resp.status_code == 400
        body = resp.json()
        assert "SQL injection" not in str(body)
        assert "OR 1=1" not in str(body)

    async def test_delete_agent_lookup_error_does_not_leak(self, client):
        """DELETE delete_agent LookupError must not expose exception text."""
        mock_svc = AsyncMock()
        mock_svc.delete_agent.side_effect = LookupError(
            "No agent found in /var/data/agents/internal-db"
        )
        with (
            patch("src.api.agents.resolve_repository", return_value=("owner", "repo")),
            patch("src.api.agents._get_service", return_value=mock_svc),
        ):
            resp = await client.delete("/api/v1/agents/PVT_test/agent-1")
        assert resp.status_code == 404
        body = resp.json()
        assert "/var/data" not in str(body)
        assert body["detail"] == "Agent not found"
