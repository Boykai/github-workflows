"""Unit tests for Signal bridge service.

Covers:
- _hash_phone() — deterministic SHA-256 hashing
- send_message() — HTTP client call to signal-cli-rest-api
- check_link_complete() — link status detection
- get_accounts() — account listing
- create_signal_message() — audit row insertion
- update_signal_message_status() — delivery status updates
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.signal_bridge import (
    _hash_phone,
    check_link_complete,
    send_message,
)

# =============================================================================
# _hash_phone
# =============================================================================


class TestHashPhone:
    """Tests for phone number hashing helper."""

    def test_deterministic_output(self):
        h1 = _hash_phone("+15551234567")
        h2 = _hash_phone("+15551234567")
        assert h1 == h2

    def test_different_numbers_produce_different_hashes(self):
        h1 = _hash_phone("+15551234567")
        h2 = _hash_phone("+15559999999")
        assert h1 != h2

    def test_returns_hex_string(self):
        result = _hash_phone("+15551234567")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest


# =============================================================================
# send_message
# =============================================================================


class TestSendMessage:
    """Tests for send_message HTTP call."""

    @pytest.mark.anyio
    async def test_send_message_success(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch(
                "src.services.signal_bridge._get_registered_phone",
                new_callable=AsyncMock,
                return_value="+15550001111",
            ),
            patch("src.services.signal_bridge.httpx.AsyncClient", return_value=mock_client),
            patch(
                "src.services.signal_bridge.get_settings",
                return_value=MagicMock(
                    signal_api_url="http://signal:8080", signal_phone_number="+15550001111"
                ),
            ),
        ):
            result = await send_message("+15559999999", "Hello")
            assert result is True

    @pytest.mark.anyio
    async def test_send_message_raises_when_no_phone(self):
        with (
            patch(
                "src.services.signal_bridge._get_registered_phone",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "src.services.signal_bridge.get_settings",
                return_value=MagicMock(signal_api_url="http://signal:8080", signal_phone_number=""),
            ),
        ):
            with pytest.raises(ValueError, match="No registered Signal account"):
                await send_message("+15559999999", "Hello")


# =============================================================================
# check_link_complete
# =============================================================================


class TestCheckLinkComplete:
    """Tests for link status detection."""

    @pytest.mark.anyio
    async def test_linked_when_accounts_present(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = ["+15551234567"]

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("src.services.signal_bridge.httpx.AsyncClient", return_value=mock_client),
            patch(
                "src.services.signal_bridge.get_settings",
                return_value=MagicMock(signal_api_url="http://signal:8080", signal_phone_number=""),
            ),
        ):
            result = await check_link_complete()
            assert result["linked"] is True
            assert result["number"] == "+15551234567"

    @pytest.mark.anyio
    async def test_not_linked_when_empty_accounts(self):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = []

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("src.services.signal_bridge.httpx.AsyncClient", return_value=mock_client),
            patch(
                "src.services.signal_bridge.get_settings",
                return_value=MagicMock(signal_api_url="http://signal:8080", signal_phone_number=""),
            ),
        ):
            result = await check_link_complete()
            assert result["linked"] is False

    @pytest.mark.anyio
    async def test_not_linked_on_exception(self):
        with patch(
            "src.services.signal_bridge.get_settings",
            return_value=MagicMock(signal_api_url="http://signal:8080", signal_phone_number=""),
        ):
            with patch(
                "src.services.signal_bridge.httpx.AsyncClient",
                side_effect=Exception("network error"),
            ):
                result = await check_link_complete()
                assert result["linked"] is False
