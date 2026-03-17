"""Tests for agents API routes (src/api/agents.py).

Covers:
- GET    /api/v1/agents/{project_id}              → list_agents
- GET    /api/v1/agents/{project_id}/pending       → list_pending_agents
- DELETE /api/v1/agents/{project_id}/pending       → purge_pending_agents
- PATCH  /api/v1/agents/{project_id}/bulk-model    → bulk_update_models
- POST   /api/v1/agents/{project_id}              → create_agent
- PATCH  /api/v1/agents/{project_id}/{agent_id}    → update_agent
- DELETE /api/v1/agents/{project_id}/{agent_id}    → delete_agent
- POST   /api/v1/agents/{project_id}/chat          → agent_chat
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.agents import (
    Agent,
    AgentChatResponse,
    AgentCreateResult,
    AgentDeleteResult,
    AgentPendingCleanupResult,
    AgentStatus,
    BulkModelUpdateResult,
)

PROJECT_ID = "PVT_test123"
AGENT_ID = "agent-abc"
BASE = f"/api/v1/agents/{PROJECT_ID}"


def _mock_service():
    """Return an AsyncMock that stands in for AgentsService."""
    return AsyncMock(name="AgentsService")


def _sample_agent(**overrides) -> Agent:
    """Build a valid Agent model instance."""
    defaults = {
        "id": AGENT_ID,
        "name": "my-agent",
        "slug": "my-agent",
        "description": "A test agent",
        "system_prompt": "You are a helpful agent.",
        "status": AgentStatus.ACTIVE,
    }
    defaults.update(overrides)
    return Agent(**defaults)


def _sample_create_result(**overrides) -> AgentCreateResult:
    """Build a valid AgentCreateResult model instance."""
    defaults = {
        "agent": _sample_agent(),
        "pr_url": "https://github.com/owner/repo/pull/1",
        "pr_number": 1,
        "branch_name": "agent/my-agent",
    }
    defaults.update(overrides)
    return AgentCreateResult(**defaults)


# ── GET /{project_id} ──────────────────────────────────────────────────────


class TestListAgents:
    """Tests for the list_agents endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_list_agents_empty(self, client):
        """Returns empty list when no agents exist."""
        self.svc.list_agents.return_value = []
        resp = await client.get(BASE)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_agents_returns_items(self, client):
        """Returns agents from the service."""
        self.svc.list_agents.return_value = [_sample_agent()]
        resp = await client.get(BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "my-agent"


# ── GET /{project_id}/pending ──────────────────────────────────────────────


class TestListPendingAgents:
    """Tests for the list_pending_agents endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_list_pending_empty(self, client):
        """Returns empty list when no pending agents."""
        self.svc.list_pending_agents.return_value = []
        resp = await client.get(f"{BASE}/pending")
        assert resp.status_code == 200
        assert resp.json() == []


# ── DELETE /{project_id}/pending ───────────────────────────────────────────


class TestPurgePendingAgents:
    """Tests for the purge_pending_agents endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_purge_pending_success(self, client):
        """Purges stale pending agents and returns count."""
        self.svc.purge_pending_agents.return_value = AgentPendingCleanupResult(deleted_count=2)
        resp = await client.delete(f"{BASE}/pending")
        assert resp.status_code == 200
        assert resp.json()["deleted_count"] == 2


# ── PATCH /{project_id}/bulk-model ─────────────────────────────────────────


class TestBulkUpdateModels:
    """Tests for the bulk_update_models endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_bulk_update_success(self, client):
        """Bulk update returns result from the service."""
        self.svc.bulk_update_models.return_value = BulkModelUpdateResult(
            updated_count=3,
            target_model_id="gpt-4o",
            target_model_name="GPT-4o",
        )
        resp = await client.patch(
            f"{BASE}/bulk-model",
            json={"target_model_id": "gpt-4o", "target_model_name": "GPT-4o"},
        )
        assert resp.status_code == 200
        assert resp.json()["updated_count"] == 3


# ── POST /{project_id} ────────────────────────────────────────────────────


class TestCreateAgent:
    """Tests for the create_agent endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_create_agent_success(self, client):
        """Creates agent and returns 201."""
        self.svc.create_agent.return_value = _sample_create_result()
        resp = await client.post(
            BASE,
            json={
                "name": "my-agent",
                "description": "A test agent",
                "system_prompt": "You are helpful.",
            },
        )
        assert resp.status_code == 201

    async def test_create_agent_value_error_returns_422(self, client):
        """ValueError from service is mapped to 422."""
        self.svc.create_agent.side_effect = ValueError("duplicate name")
        resp = await client.post(
            BASE,
            json={
                "name": "my-agent",
                "description": "dup",
                "system_prompt": "prompt",
            },
        )
        assert resp.status_code == 422

    async def test_create_agent_runtime_error_returns_502(self, client):
        """RuntimeError from service is mapped to 502 (via GitHubAPIError)."""
        self.svc.create_agent.side_effect = RuntimeError("GitHub API down")
        resp = await client.post(
            BASE,
            json={
                "name": "my-agent",
                "description": "fail",
                "system_prompt": "prompt",
            },
        )
        assert resp.status_code == 502


# ── PATCH /{project_id}/{agent_id} ────────────────────────────────────────


class TestUpdateAgent:
    """Tests for the update_agent endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_update_agent_success(self, client):
        """Updates agent and returns result."""
        self.svc.update_agent.return_value = _sample_create_result()
        resp = await client.patch(
            f"{BASE}/{AGENT_ID}",
            json={"description": "updated desc"},
        )
        assert resp.status_code == 200

    async def test_update_agent_not_found_returns_404(self, client):
        """LookupError from service is mapped to 404."""
        self.svc.update_agent.side_effect = LookupError("agent not found")
        resp = await client.patch(
            f"{BASE}/{AGENT_ID}",
            json={"description": "missing"},
        )
        assert resp.status_code == 404

    async def test_update_agent_value_error_returns_422(self, client):
        """ValueError from service is mapped to 422."""
        self.svc.update_agent.side_effect = ValueError("invalid field")
        resp = await client.patch(
            f"{BASE}/{AGENT_ID}",
            json={"description": "bad"},
        )
        assert resp.status_code == 422


# ── DELETE /{project_id}/{agent_id} ────────────────────────────────────────


class TestDeleteAgent:
    """Tests for the delete_agent endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_delete_agent_success(self, client):
        """Deletes agent and returns result."""
        self.svc.delete_agent.return_value = AgentDeleteResult(
            success=True,
            pr_url="https://github.com/owner/repo/pull/3",
            pr_number=3,
        )
        resp = await client.delete(f"{BASE}/{AGENT_ID}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_delete_agent_not_found_returns_404(self, client):
        """LookupError from service is mapped to 404."""
        self.svc.delete_agent.side_effect = LookupError("agent not found")
        resp = await client.delete(f"{BASE}/{AGENT_ID}")
        assert resp.status_code == 404

    async def test_delete_agent_runtime_error_returns_502(self, client):
        """RuntimeError from service is mapped to 502 (via GitHubAPIError)."""
        self.svc.delete_agent.side_effect = RuntimeError("GitHub API failure")
        resp = await client.delete(f"{BASE}/{AGENT_ID}")
        assert resp.status_code == 502


# ── POST /{project_id}/chat ───────────────────────────────────────────────


class TestAgentChat:
    """Tests for the agent_chat endpoint."""

    @pytest.fixture(autouse=True)
    def _patch(self):
        svc = _mock_service()
        self.svc = svc
        with (
            patch("src.api.agents._get_service", return_value=svc),
            patch(
                "src.api.agents.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.agents.get_db", return_value=MagicMock()),
        ):
            yield

    async def test_agent_chat_success(self, client):
        """Chat returns response from service."""
        self.svc.chat.return_value = AgentChatResponse(
            reply="Hello!",
            session_id="sess-1",
        )
        resp = await client.post(
            f"{BASE}/chat",
            json={"message": "Help me build an agent"},
        )
        assert resp.status_code == 200
        assert resp.json()["reply"] == "Hello!"
