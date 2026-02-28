"""Tests for MCP API endpoints (src/api/mcp.py).

Covers:
- GET    /api/v1/settings/mcps       → list_mcp_configurations
- POST   /api/v1/settings/mcps       → create_mcp_configuration
- DELETE  /api/v1/settings/mcps/{id}  → delete_mcp_configuration

These tests exercise the full FastAPI stack (routing, auth dependency,
validation, exception handlers) with an in-memory SQLite database.
The conftest ``client`` fixture patches ``get_db`` in both
``src.api.settings`` and ``src.api.mcp``.

Error responses are validated to use the standard AppException
``{"error": "...", "details": {...}}`` format (not HTTPException's
``{"detail": "..."}`` format) ensuring consistency with the frontend
``ApiError`` parser.
"""

from src.services.mcp_store import MAX_MCPS_PER_USER

# ── GET /settings/mcps ─────────────────────────────────────────────────────


class TestListMcpConfigurations:
    """GET /api/v1/settings/mcps endpoint tests."""

    async def test_list_empty(self, client):
        """Returns an empty list when the user has no MCPs."""
        resp = await client.get("/api/v1/settings/mcps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["mcps"] == []
        assert data["count"] == 0

    async def test_list_after_create(self, client):
        """After creating an MCP, listing returns it."""
        await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Test MCP", "endpoint_url": "https://example.com/mcp"},
        )
        resp = await client.get("/api/v1/settings/mcps")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["mcps"][0]["name"] == "Test MCP"


# ── POST /settings/mcps ────────────────────────────────────────────────────


class TestCreateMcpConfiguration:
    """POST /api/v1/settings/mcps endpoint tests."""

    async def test_create_success(self, client):
        """Creating a valid MCP returns 201 with the configuration."""
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "My MCP", "endpoint_url": "https://example.com/mcp"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My MCP"
        assert data["endpoint_url"] == "https://example.com/mcp"
        assert data["is_active"] is True
        assert "id" in data

    async def test_create_ssrf_private_ip_rejected(self, client):
        """Creating an MCP with a private-IP URL returns 400 with error message."""
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Bad", "endpoint_url": "http://192.168.1.1/api"},
        )
        assert resp.status_code == 400
        data = resp.json()
        # AppException handler produces {"error": "...", "details": {...}}
        assert "private or reserved" in data["error"]

    async def test_create_ssrf_localhost_rejected(self, client):
        """Creating an MCP with a localhost URL returns 400."""
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Local", "endpoint_url": "http://localhost/api"},
        )
        assert resp.status_code == 400
        assert "private or reserved" in resp.json()["error"]

    async def test_create_ssrf_zero_ip_rejected(self, client):
        """0.0.0.0 (unspecified address) must be blocked."""
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Zero", "endpoint_url": "http://0.0.0.0/api"},
        )
        assert resp.status_code == 400
        assert "private or reserved" in resp.json()["error"]

    async def test_create_limit_exceeded(self, client):
        """Exceeding the per-user MCP limit returns 409."""
        for i in range(MAX_MCPS_PER_USER):
            resp = await client.post(
                "/api/v1/settings/mcps",
                json={
                    "name": f"MCP {i}",
                    "endpoint_url": f"https://example.com/mcp/{i}",
                },
            )
            assert resp.status_code == 201, f"Failed creating MCP #{i}: {resp.text}"

        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "One Too Many", "endpoint_url": "https://example.com/extra"},
        )
        assert resp.status_code == 409
        assert "Maximum of" in resp.json()["error"]

    async def test_create_validates_name_required(self, client):
        """Pydantic rejects an empty name (min_length=1)."""
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "", "endpoint_url": "https://example.com/mcp"},
        )
        assert resp.status_code == 422  # Pydantic validation error

    async def test_create_validates_url_required(self, client):
        """Pydantic rejects an empty endpoint_url."""
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Valid Name", "endpoint_url": ""},
        )
        assert resp.status_code == 422

    async def test_error_response_uses_appexception_format(self, client):
        """Error responses must use {\"error\": ...} not {\"detail\": ...}.

        This ensures the frontend ApiError parser can extract messages correctly.
        """
        resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Bad", "endpoint_url": "http://127.0.0.1/api"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "error" in data, "Expected AppException format with 'error' key"
        assert "detail" not in data, "Should not use HTTPException 'detail' format"


# ── DELETE /settings/mcps/{mcp_id} ─────────────────────────────────────────


class TestDeleteMcpConfiguration:
    """DELETE /api/v1/settings/mcps/{mcp_id} endpoint tests."""

    async def test_delete_success(self, client):
        """Deleting an owned MCP returns 200."""
        create_resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "To Delete", "endpoint_url": "https://example.com/del"},
        )
        mcp_id = create_resp.json()["id"]

        resp = await client.delete(f"/api/v1/settings/mcps/{mcp_id}")
        assert resp.status_code == 200
        assert "message" in resp.json()

    async def test_delete_nonexistent_returns_404(self, client):
        """Deleting a non-existent MCP returns 404 with error format."""
        resp = await client.delete("/api/v1/settings/mcps/nonexistent-id")
        assert resp.status_code == 404
        data = resp.json()
        assert "error" in data
        assert "not found" in data["error"].lower()

    async def test_delete_removes_from_list(self, client):
        """After deletion, the MCP no longer appears in the list."""
        create_resp = await client.post(
            "/api/v1/settings/mcps",
            json={"name": "Ephemeral", "endpoint_url": "https://example.com/eph"},
        )
        mcp_id = create_resp.json()["id"]

        await client.delete(f"/api/v1/settings/mcps/{mcp_id}")

        list_resp = await client.get("/api/v1/settings/mcps")
        assert list_resp.json()["count"] == 0
