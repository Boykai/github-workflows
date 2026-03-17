"""Tests for Signal API routes (src/api/signal.py).

Covers:
- GET    /api/v1/signal/connection                → get_signal_connection
- POST   /api/v1/signal/connection/link           → initiate_signal_link
- DELETE /api/v1/signal/connection                → disconnect_signal
- GET    /api/v1/signal/preferences               → get_signal_preferences
- PUT    /api/v1/signal/preferences               → update_signal_preferences
- GET    /api/v1/signal/banners                   → get_signal_banners
- POST   /api/v1/signal/banners/{id}/dismiss      → dismiss_signal_banner
- POST   /api/v1/signal/webhook/inbound           → handle_inbound_signal_message
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models.signal import (
    SignalConnection,
    SignalConnectionStatus,
    SignalNotificationMode,
)

# ── Helpers ─────────────────────────────────────────────────────────────────

_API = "src.api.signal"
_BRIDGE = "src.services.signal_bridge"


def _connected_conn(**overrides) -> SignalConnection:
    defaults = {
        "id": "conn-1",
        "github_user_id": "12345",
        "signal_phone_encrypted": "encrypted-phone",
        "signal_phone_hash": "hash123",
        "status": SignalConnectionStatus.CONNECTED,
        "notification_mode": SignalNotificationMode.ALL,
        "linked_at": "2024-01-01T00:00:00",
    }
    defaults.update(overrides)
    return SignalConnection(**defaults)


# ── GET /signal/connection ────────────────────────────────────────────────


class TestGetSignalConnection:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(f"{_API}.get_connection_by_user", new_callable=AsyncMock) as get_conn,
            patch(f"{_BRIDGE}._get_encryption") as get_enc,
        ):
            self.mock_get_conn = get_conn
            self.mock_enc = MagicMock()
            get_enc.return_value = self.mock_enc
            yield

    async def test_no_connection(self, client):
        self.mock_get_conn.return_value = None
        resp = await client.get("/api/v1/signal/connection")
        assert resp.status_code == 200
        assert resp.json()["status"] is None

    async def test_connected(self, client):
        self.mock_get_conn.return_value = _connected_conn()
        self.mock_enc.decrypt.return_value = "+1234567890"
        resp = await client.get("/api/v1/signal/connection")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "connected"
        assert data["signal_identifier"] is not None

    async def test_decrypt_failure_masks_gracefully(self, client):
        self.mock_get_conn.return_value = _connected_conn()
        self.mock_enc.decrypt.side_effect = Exception("decrypt failed")
        resp = await client.get("/api/v1/signal/connection")
        assert resp.status_code == 200
        assert resp.json()["signal_identifier"] is None


# ── POST /signal/connection/link ──────────────────────────────────────────


class TestInitiateSignalLink:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(f"{_API}.get_connection_by_user", new_callable=AsyncMock) as get_conn,
            patch(f"{_API}.request_qr_code_base64", new_callable=AsyncMock) as qr,
        ):
            self.mock_get_conn = get_conn
            self.mock_qr = qr
            yield

    async def test_link_success(self, client):
        self.mock_get_conn.return_value = None
        self.mock_qr.return_value = "base64-qr-data"
        resp = await client.post(
            "/api/v1/signal/connection/link",
            json={"device_name": "TestDevice"},
        )
        assert resp.status_code == 200
        assert resp.json()["qr_code_base64"] == "base64-qr-data"

    async def test_link_already_connected(self, client):
        self.mock_get_conn.return_value = _connected_conn()
        resp = await client.post(
            "/api/v1/signal/connection/link",
            json={"device_name": "TestDevice"},
        )
        assert resp.status_code == 409

    async def test_link_default_device_name(self, client):
        self.mock_get_conn.return_value = None
        self.mock_qr.return_value = "base64-qr"
        resp = await client.post("/api/v1/signal/connection/link", json={})
        assert resp.status_code == 200


# ── DELETE /signal/connection ─────────────────────────────────────────────


class TestDisconnectSignal:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with patch(f"{_API}.disconnect_and_purge", new_callable=AsyncMock) as mock:
            self.mock_disconnect = mock
            yield

    async def test_disconnect_success(self, client):
        self.mock_disconnect.return_value = True
        resp = await client.delete("/api/v1/signal/connection")
        assert resp.status_code == 200
        assert "disconnected" in resp.json()["message"].lower()

    async def test_disconnect_no_connection(self, client):
        self.mock_disconnect.return_value = False
        resp = await client.delete("/api/v1/signal/connection")
        assert resp.status_code == 404


# ── GET /signal/preferences ──────────────────────────────────────────────


class TestGetSignalPreferences:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with patch(f"{_API}.get_connection_by_user", new_callable=AsyncMock) as mock:
            self.mock_get_conn = mock
            yield

    async def test_preferences_success(self, client):
        self.mock_get_conn.return_value = _connected_conn(
            notification_mode=SignalNotificationMode.ACTIONS_ONLY,
        )
        resp = await client.get("/api/v1/signal/preferences")
        assert resp.status_code == 200
        assert resp.json()["notification_mode"] == "actions_only"

    async def test_preferences_no_connection(self, client):
        self.mock_get_conn.return_value = None
        resp = await client.get("/api/v1/signal/preferences")
        assert resp.status_code == 404


# ── GET /signal/banners ──────────────────────────────────────────────────


class TestGetSignalBanners:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with patch(f"{_API}.get_banners_for_user", new_callable=AsyncMock) as mock:
            self.mock_banners = mock
            yield

    async def test_banners_empty(self, client):
        self.mock_banners.return_value = []
        resp = await client.get("/api/v1/signal/banners")
        assert resp.status_code == 200
        assert resp.json()["banners"] == []

    async def test_banners_with_items(self, client):
        from src.models.signal import SignalConflictBanner

        banner = SignalConflictBanner(
            id="b-1",
            github_user_id="12345",
            message="Phone conflict detected",
            created_at="2024-01-01T00:00:00",
        )
        self.mock_banners.return_value = [banner]
        resp = await client.get("/api/v1/signal/banners")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["banners"]) == 1
        assert data["banners"][0]["message"] == "Phone conflict detected"


# ── POST /signal/banners/{id}/dismiss ────────────────────────────────────


class TestDismissBanner:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with patch(f"{_API}.dismiss_banner", new_callable=AsyncMock) as mock:
            self.mock_dismiss = mock
            yield

    async def test_dismiss_success(self, client):
        self.mock_dismiss.return_value = True
        resp = await client.post("/api/v1/signal/banners/b-1/dismiss")
        assert resp.status_code == 200
        assert "dismissed" in resp.json()["message"].lower()

    async def test_dismiss_not_found(self, client):
        self.mock_dismiss.return_value = False
        resp = await client.post("/api/v1/signal/banners/nonexistent/dismiss")
        assert resp.status_code == 404


# ── POST /signal/webhook/inbound ─────────────────────────────────────────


class TestInboundWebhook:
    @pytest.fixture(autouse=True)
    def _patch(self):
        with (
            patch(f"{_API}.get_connection_by_phone_hash", new_callable=AsyncMock) as get_phone,
            patch(f"{_API}._hash_phone", return_value="hashed") as hash_phone,
            patch(f"{_API}.store_inbound_message", new_callable=AsyncMock) as store,
            patch(f"{_API}.get_settings") as get_settings,
        ):
            self.mock_get_phone = get_phone
            self.mock_hash = hash_phone
            self.mock_store = store
            mock_settings = MagicMock()
            mock_settings.signal_webhook_secret = "test-secret"
            get_settings.return_value = mock_settings
            yield

    async def test_webhook_success(self, client):
        conn = _connected_conn()
        self.mock_get_phone.return_value = conn
        self.mock_store.return_value = "msg-123"
        resp = await client.post(
            "/api/v1/signal/webhook/inbound",
            json={
                "source_number": "+1234567890",
                "message_text": "Hello",
                "timestamp": "2024-01-01T00:00:00",
            },
            headers={"X-Signal-Webhook-Secret": "test-secret"},
        )
        assert resp.status_code == 200
        assert resp.json()["processed"] is True

    async def test_webhook_missing_secret(self, client):
        resp = await client.post(
            "/api/v1/signal/webhook/inbound",
            json={
                "source_number": "+1234567890",
                "message_text": "Hello",
                "timestamp": "2024-01-01T00:00:00",
            },
        )
        assert resp.status_code == 403

    async def test_webhook_wrong_secret(self, client):
        resp = await client.post(
            "/api/v1/signal/webhook/inbound",
            json={
                "source_number": "+1234567890",
                "message_text": "Hello",
                "timestamp": "2024-01-01T00:00:00",
            },
            headers={"X-Signal-Webhook-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403

    async def test_webhook_unlinked_sender(self, client):
        self.mock_get_phone.return_value = None
        resp = await client.post(
            "/api/v1/signal/webhook/inbound",
            json={
                "source_number": "+9999999999",
                "message_text": "Hello",
                "timestamp": "2024-01-01T00:00:00",
            },
            headers={"X-Signal-Webhook-Secret": "test-secret"},
        )
        assert resp.status_code == 422
