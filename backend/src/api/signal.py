"""Signal connection management API endpoints.

Handles Signal account linking (QR code flow), connection status,
disconnection with PII purge, notification preferences, and conflict banners.

Endpoints are mounted at /api/v1/signal/ per contracts/signal-api.yaml.
"""

import logging
from datetime import UTC
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.auth import get_session_dep
from src.config import get_settings
from src.models.signal import (
    SignalBanner,
    SignalBannersResponse,
    SignalConnectionResponse,
    SignalConnectionStatus,
    SignalInboundMessage,
    SignalLinkRequest,
    SignalLinkResponse,
    SignalLinkStatus,
    SignalLinkStatusResponse,
    SignalPreferencesResponse,
    SignalPreferencesUpdate,
    mask_phone_number,
)
from src.models.user import UserSession
from src.services.signal_bridge import (
    _hash_phone,
    check_link_complete,
    create_connection,
    disconnect_and_purge,
    dismiss_banner,
    get_banners_for_user,
    get_connection_by_phone_hash,
    get_connection_by_user,
    request_qr_code_base64,
    store_inbound_message,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Connection Management (FR-001, FR-002, FR-003, FR-014) ───────────────


@router.get("/connection", response_model=SignalConnectionResponse)
async def get_signal_connection(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SignalConnectionResponse:
    """Get current Signal connection status. FR-002."""
    conn = await get_connection_by_user(session.github_user_id)
    if not conn:
        return SignalConnectionResponse()

    # Decrypt phone for masking (display only)
    from src.services.signal_bridge import _get_encryption

    enc = _get_encryption()
    try:
        phone = enc.decrypt(conn.signal_phone_encrypted)
        masked = mask_phone_number(phone)
    except Exception:
        masked = None

    return SignalConnectionResponse(
        connection_id=conn.id,
        status=conn.status,
        signal_identifier=masked,
        notification_mode=conn.notification_mode,
        linked_at=conn.linked_at,
        last_active_project_id=conn.last_active_project_id,
    )


@router.post("/connection/link", response_model=SignalLinkResponse)
async def initiate_signal_link(
    body: SignalLinkRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SignalLinkResponse:
    """Generate QR code for Signal linking. FR-001."""
    # Check for existing active connection
    existing = await get_connection_by_user(session.github_user_id)
    if existing and existing.status == SignalConnectionStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an active Signal connection",
        )

    try:
        qr_base64 = await request_qr_code_base64(body.device_name)
    except Exception as e:
        logger.error("Failed to request QR code from signal-api: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate QR code from Signal service",
        ) from e

    return SignalLinkResponse(
        qr_code_base64=qr_base64,
        expires_in_seconds=60,
    )


@router.get("/connection/link/status", response_model=SignalLinkStatusResponse)
async def check_signal_link_status(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SignalLinkStatusResponse:
    """Poll link completion status after QR code display."""
    # First check if user already has a completed connection
    existing = await get_connection_by_user(session.github_user_id)
    if existing and existing.status == SignalConnectionStatus.CONNECTED:
        from src.services.signal_bridge import _get_encryption

        enc = _get_encryption()
        try:
            phone = enc.decrypt(existing.signal_phone_encrypted)
            masked = mask_phone_number(phone)
        except Exception:
            masked = None

        return SignalLinkStatusResponse(
            status=SignalLinkStatus.CONNECTED,
            signal_identifier=masked,
        )

    # Check signal-cli-rest-api for link completion
    result = await check_link_complete()
    if result.get("linked") and result.get("number"):
        phone = result["number"]
        # Create the connection record
        await create_connection(session.github_user_id, phone)
        return SignalLinkStatusResponse(
            status=SignalLinkStatus.CONNECTED,
            signal_identifier=mask_phone_number(phone),
        )

    return SignalLinkStatusResponse(status=SignalLinkStatus.PENDING)


@router.delete("/connection")
async def disconnect_signal(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Disconnect Signal account and purge PII. FR-003, FR-014."""
    deleted = await disconnect_and_purge(session.github_user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Signal connection exists",
        )
    return {"message": "Signal account disconnected"}


# ── Notification Preferences (FR-007) ────────────────────────────────────


@router.get("/preferences", response_model=SignalPreferencesResponse)
async def get_signal_preferences(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SignalPreferencesResponse:
    """Get Signal notification preferences. FR-007."""
    conn = await get_connection_by_user(session.github_user_id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Signal connection exists",
        )
    return SignalPreferencesResponse(notification_mode=conn.notification_mode)


@router.put("/preferences", response_model=SignalPreferencesResponse)
async def update_signal_preferences(
    body: SignalPreferencesUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SignalPreferencesResponse:
    """Update Signal notification preferences. FR-007."""
    from datetime import datetime

    from src.services.database import get_db

    conn = await get_connection_by_user(session.github_user_id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Signal connection exists",
        )

    db = get_db()
    now = datetime.now(UTC).isoformat()
    await db.execute(
        "UPDATE signal_connections SET notification_mode = ?, updated_at = ? WHERE id = ?",
        (body.notification_mode.value, now, conn.id),
    )
    await db.commit()

    logger.info(
        "Updated Signal notification preference for user %s to %s",
        session.github_username,
        body.notification_mode.value,
    )

    return SignalPreferencesResponse(notification_mode=body.notification_mode)


# ── Conflict Banners (FR-015) ────────────────────────────────────────────


@router.get("/banners", response_model=SignalBannersResponse)
async def get_signal_banners(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> SignalBannersResponse:
    """Get active (undismissed) conflict banners. FR-015."""
    banners = await get_banners_for_user(session.github_user_id)
    return SignalBannersResponse(
        banners=[SignalBanner(id=b.id, message=b.message, created_at=b.created_at) for b in banners]
    )


@router.post("/banners/{banner_id}/dismiss")
async def dismiss_signal_banner(
    banner_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Dismiss a conflict banner. FR-015."""
    dismissed = await dismiss_banner(banner_id, session.github_user_id)
    if not dismissed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found",
        )
    return {"message": "Banner dismissed"}


# ── Inbound Webhook (Internal, FR-006, FR-009) ──────────────────────────


@router.post("/webhook/inbound")
async def handle_inbound_signal_message(
    body: SignalInboundMessage,
    x_signal_secret: str | None = Header(None, alias="X-Signal-Webhook-Secret"),
) -> dict:
    """Receive an inbound Signal message from external integrations.

    Protected by shared secret when SIGNAL_WEBHOOK_SECRET is configured.
    The WebSocket listener calls store_inbound_message() directly.
    """
    settings = get_settings()
    if settings.signal_webhook_secret:
        if x_signal_secret != settings.signal_webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook secret",
            )

    source = body.source_number
    phone_hash = _hash_phone(source)

    conn = await get_connection_by_phone_hash(phone_hash)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unlinked sender",
        )

    if body.has_attachment and not body.message_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only text messages are supported",
        )

    chat_message_id = await store_inbound_message(
        conn, body.message_text, conn.last_active_project_id
    )

    return {
        "processed": True,
        "chat_message_id": chat_message_id,
    }
