"""Tests for MCP store operations (src/services/mcp_store.py).

Covers:
- validate_url_not_ssrf — SSRF validation for MCP endpoint URLs
  - Scheme enforcement (http/https only)
  - Private/reserved/loopback/link-local/unspecified IP rejection
  - Hostname normalization (trailing dot, case-insensitive)
  - Localhost pattern matching (localhost, localhost.localdomain)
  - 0.0.0.0 (unspecified address) rejection
  - Valid public URLs pass through
- create_mcp — per-user MCP limit enforcement
- list_mcps  — listing user-scoped MCPs
- delete_mcp — ownership-scoped deletion
"""

import pytest

from src.exceptions import McpLimitExceededError, McpValidationError
from src.models.mcp import McpConfigurationCreate
from src.services.mcp_store import (
    MAX_MCPS_PER_USER,
    create_mcp,
    delete_mcp,
    list_mcps,
    validate_url_not_ssrf,
)

# ── validate_url_not_ssrf ──────────────────────────────────────────────────


class TestValidateUrlNotSsrf:
    """Unit tests for the SSRF URL validation helper."""

    # ── Valid URLs that should pass ──

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/mcp",
            "http://example.com/api/v1",
            "https://mcp.acme.io:8443/endpoint",
            "https://8.8.8.8/dns",
            "http://93.184.216.34/resource",
        ],
    )
    def test_valid_public_urls_pass(self, url: str):
        """Public HTTP(S) URLs should pass validation unchanged."""
        assert validate_url_not_ssrf(url) == url

    # ── Scheme enforcement ──

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com/file",
            "file:///etc/passwd",
            "gopher://evil.com",
            "javascript:alert(1)",
        ],
    )
    def test_rejects_non_http_schemes(self, url: str):
        """Non-HTTP(S) schemes must be rejected."""
        with pytest.raises(ValueError, match="Only http and https URLs are allowed"):
            validate_url_not_ssrf(url)

    # ── Missing hostname ──

    def test_rejects_url_without_hostname(self):
        """URLs without a hostname must be rejected."""
        with pytest.raises(ValueError, match="URL must have a valid hostname"):
            validate_url_not_ssrf("http:///no-host")

    # ── Private / reserved IPv4 ──

    @pytest.mark.parametrize(
        "ip",
        [
            "10.0.0.1",
            "172.16.0.1",
            "192.168.1.1",
        ],
    )
    def test_rejects_private_ipv4(self, ip: str):
        """Private IPv4 addresses (RFC 1918) must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf(f"http://{ip}/api")

    # ── Loopback ──

    def test_rejects_ipv4_loopback(self):
        """127.0.0.1 (IPv4 loopback) must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://127.0.0.1/api")

    def test_rejects_ipv6_loopback(self):
        """::1 (IPv6 loopback) must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://[::1]/api")

    # ── Unspecified address (0.0.0.0) — critical SSRF bypass vector ──

    def test_rejects_unspecified_address(self):
        """0.0.0.0 resolves to the local machine on most OSes and must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://0.0.0.0/api")

    def test_rejects_ipv6_unspecified(self):
        """[::] (IPv6 unspecified) must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://[::]/api")

    # ── Link-local ──

    def test_rejects_link_local(self):
        """169.254.x.x (link-local) must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://169.254.169.254/latest/meta-data")

    # ── Localhost hostname variants ──

    def test_rejects_localhost(self):
        """Plain 'localhost' hostname must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://localhost/api")

    def test_rejects_localhost_with_trailing_dot(self):
        """'localhost.' (FQDN with trailing dot) must also be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://localhost./api")

    def test_rejects_localhost_localdomain(self):
        """'localhost.localdomain' must be blocked (first label is localhost)."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://localhost.localdomain/api")

    def test_rejects_localhost_case_insensitive(self):
        """Hostname normalisation should treat 'LOCALHOST' as 'localhost'."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://LOCALHOST/api")

    # ── Reserved ──

    def test_rejects_reserved_ip(self):
        """240.0.0.1 is in the reserved range and must be blocked."""
        with pytest.raises(ValueError, match="private or reserved"):
            validate_url_not_ssrf("http://240.0.0.1/api")


# ── CRUD Operations ───────────────────────────────────────────────────────


class TestCreateMcp:
    """Tests for the create_mcp service function."""

    async def test_create_mcp_success(self, mock_db):
        """A valid MCP should be created and returned."""
        data = McpConfigurationCreate(name="Test MCP", endpoint_url="https://example.com/mcp")
        result = await create_mcp(mock_db, "user-1", data)

        assert result.name == "Test MCP"
        assert result.endpoint_url == "https://example.com/mcp"
        assert result.is_active is True
        assert result.id  # UUID generated

    async def test_create_mcp_ssrf_rejected(self, mock_db):
        """Creating an MCP with a private-IP URL raises McpValidationError."""
        data = McpConfigurationCreate(name="Bad MCP", endpoint_url="http://192.168.1.1/api")
        with pytest.raises(McpValidationError, match="private or reserved"):
            await create_mcp(mock_db, "user-1", data)

    async def test_create_mcp_limit_exceeded(self, mock_db):
        """Exceeding MAX_MCPS_PER_USER raises McpLimitExceededError."""
        data = McpConfigurationCreate(name="MCP", endpoint_url="https://example.com/mcp")
        for i in range(MAX_MCPS_PER_USER):
            await create_mcp(
                mock_db,
                "user-1",
                McpConfigurationCreate(
                    name=f"MCP {i}", endpoint_url=f"https://example.com/mcp/{i}"
                ),
            )

        with pytest.raises(McpLimitExceededError, match="Maximum of"):
            await create_mcp(mock_db, "user-1", data)

    async def test_create_mcp_limit_is_per_user(self, mock_db):
        """The MCP limit is per-user; a second user is unaffected."""
        for i in range(MAX_MCPS_PER_USER):
            await create_mcp(
                mock_db,
                "user-1",
                McpConfigurationCreate(
                    name=f"MCP {i}", endpoint_url=f"https://example.com/mcp/{i}"
                ),
            )

        # Different user should succeed
        data = McpConfigurationCreate(
            name="Other User MCP", endpoint_url="https://example.com/other"
        )
        result = await create_mcp(mock_db, "user-2", data)
        assert result.name == "Other User MCP"


class TestListMcps:
    """Tests for the list_mcps service function."""

    async def test_list_empty(self, mock_db):
        """Listing MCPs for a user with none returns an empty list."""
        result = await list_mcps(mock_db, "user-1")
        assert result.mcps == []
        assert result.count == 0

    async def test_list_returns_only_user_mcps(self, mock_db):
        """Listing MCPs only returns configurations owned by the specified user."""
        await create_mcp(
            mock_db,
            "user-1",
            McpConfigurationCreate(name="User1 MCP", endpoint_url="https://example.com/1"),
        )
        await create_mcp(
            mock_db,
            "user-2",
            McpConfigurationCreate(name="User2 MCP", endpoint_url="https://example.com/2"),
        )

        result = await list_mcps(mock_db, "user-1")
        assert result.count == 1
        assert result.mcps[0].name == "User1 MCP"


class TestDeleteMcp:
    """Tests for the delete_mcp service function."""

    async def test_delete_own_mcp(self, mock_db):
        """Users can delete their own MCP configurations."""
        created = await create_mcp(
            mock_db,
            "user-1",
            McpConfigurationCreate(name="To Delete", endpoint_url="https://example.com/del"),
        )

        assert await delete_mcp(mock_db, "user-1", created.id) is True

        # Verify it's gone
        result = await list_mcps(mock_db, "user-1")
        assert result.count == 0

    async def test_delete_nonexistent_returns_false(self, mock_db):
        """Deleting a non-existent MCP returns False (not found)."""
        assert await delete_mcp(mock_db, "user-1", "nonexistent-id") is False

    async def test_cannot_delete_other_users_mcp(self, mock_db):
        """Users cannot delete another user's MCP configuration."""
        created = await create_mcp(
            mock_db,
            "user-1",
            McpConfigurationCreate(name="Private MCP", endpoint_url="https://example.com/priv"),
        )

        # user-2 tries to delete user-1's MCP → returns False
        assert await delete_mcp(mock_db, "user-2", created.id) is False

        # MCP still exists for user-1
        result = await list_mcps(mock_db, "user-1")
        assert result.count == 1
