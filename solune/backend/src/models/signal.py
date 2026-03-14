"""Signal messaging integration models.

Pydantic models for signal_connections, signal_messages, signal_conflict_banners
and all request/response schemas per contracts/signal-api.yaml.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

# ── Enums ────────────────────────────────────────────────────────────────


class SignalConnectionStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class SignalNotificationMode(StrEnum):
    ALL = "all"
    ACTIONS_ONLY = "actions_only"
    CONFIRMATIONS_ONLY = "confirmations_only"
    NONE = "none"


class SignalMessageDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SignalDeliveryStatus(StrEnum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class SignalLinkStatus(StrEnum):
    PENDING = "pending"
    CONNECTED = "connected"
    FAILED = "failed"
    EXPIRED = "expired"


# ── Database Row Models ──────────────────────────────────────────────────


class SignalConnection(BaseModel):
    """Represents a row in signal_connections table."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    github_user_id: str
    signal_phone_encrypted: str
    signal_phone_hash: str
    status: SignalConnectionStatus = SignalConnectionStatus.PENDING
    notification_mode: SignalNotificationMode = SignalNotificationMode.ALL
    last_active_project_id: str | None = None
    linked_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SignalMessage(BaseModel):
    """Represents a row in signal_messages table."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    connection_id: str
    direction: SignalMessageDirection
    chat_message_id: str | None = None
    content_preview: str | None = None
    delivery_status: SignalDeliveryStatus = SignalDeliveryStatus.PENDING
    retry_count: int = 0
    next_retry_at: str | None = None
    error_detail: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    delivered_at: str | None = None


class SignalConflictBanner(BaseModel):
    """Represents a row in signal_conflict_banners table."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    github_user_id: str
    message: str
    dismissed: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# ── API Request Models ───────────────────────────────────────────────────


class SignalLinkRequest(BaseModel):
    """POST /api/v1/signal/connection/link request body."""

    device_name: str = Field(default="Agent Projects", max_length=50)


class SignalPreferencesUpdate(BaseModel):
    """PUT /api/v1/signal/preferences request body."""

    notification_mode: SignalNotificationMode


class SignalInboundMessage(BaseModel):
    """Internal model for inbound Signal messages from the WebSocket listener."""

    source_number: str
    message_text: str
    timestamp: str
    has_attachment: bool = False


# ── API Response Models ──────────────────────────────────────────────────


class SignalConnectionResponse(BaseModel):
    """GET /api/v1/signal/connection response."""

    connection_id: str | None = None
    status: SignalConnectionStatus | None = None
    signal_identifier: str | None = None  # Masked phone, e.g. "+1***...7890"
    notification_mode: SignalNotificationMode | None = None
    linked_at: str | None = None
    last_active_project_id: str | None = None


class SignalLinkResponse(BaseModel):
    """POST /api/v1/signal/connection/link response."""

    qr_code_base64: str
    expires_in_seconds: int = 60


class SignalLinkStatusResponse(BaseModel):
    """GET /api/v1/signal/connection/link/status response."""

    status: SignalLinkStatus
    signal_identifier: str | None = None
    error_message: str | None = None


class SignalPreferencesResponse(BaseModel):
    """GET/PUT /api/v1/signal/preferences response."""

    notification_mode: SignalNotificationMode


class SignalBanner(BaseModel):
    """Single banner item in response."""

    id: str
    message: str
    created_at: str


class SignalBannersResponse(BaseModel):
    """GET /api/v1/signal/banners response."""

    banners: list[SignalBanner] = []


# ── Helpers ──────────────────────────────────────────────────────────────


def mask_phone_number(phone: str) -> str:
    """Mask a phone number for display: +1234567890 → +1***...7890"""
    n = len(phone)
    if n <= 4:
        return phone

    # Show up to 2 leading and 4 trailing characters, but always leave
    # at least one character masked in the middle.
    prefix_len = min(2, n - 2)
    suffix_len = min(4, n - prefix_len - 1)

    return f"{phone[:prefix_len]}***...{phone[-suffix_len:]}"
