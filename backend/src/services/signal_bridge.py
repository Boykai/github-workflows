"""Signal bridge service — HTTP client for signal-cli-rest-api sidecar.

Provides the core async HTTP interface to the signal-cli-rest-api container
for QR code linking, message sending/receiving, and account management.

User-story-specific methods (connection lifecycle — T009, WebSocket — T018)
are added in later tasks; this module establishes the shared foundation.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import re
from datetime import UTC, datetime

import httpx
import websockets

from src.config import get_settings
from src.models.signal import (
    SignalConflictBanner,
    SignalConnection,
    SignalConnectionStatus,
    SignalDeliveryStatus,
    SignalMessage,
    SignalMessageDirection,
)
from src.services.database import get_db
from src.services.encryption import EncryptionService

logger = logging.getLogger(__name__)

# ── Encryption helper (reuses existing EncryptionService) ────────────────

_encryption: EncryptionService | None = None


def _get_encryption() -> EncryptionService:
    global _encryption
    if _encryption is None:
        settings = get_settings()
        _encryption = EncryptionService(settings.encryption_key)
    return _encryption


def _hash_phone(phone: str) -> str:
    """SHA-256 hex digest of a phone number for index lookup."""
    return hashlib.sha256(phone.encode()).hexdigest()


# ── Core HTTP helpers ────────────────────────────────────────────────────


def _signal_base_url() -> str:
    return get_settings().signal_api_url


async def request_qr_code(device_name: str = "Agent Projects") -> bytes:
    """Request a QR code PNG image from signal-cli-rest-api.

    Returns raw PNG bytes.
    """
    url = f"{_signal_base_url()}/v1/qrcodelink"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params={"device_name": device_name})
        resp.raise_for_status()
        return resp.content


async def request_qr_code_base64(device_name: str = "Agent Projects") -> str:
    """Request a QR code and return it as a base64-encoded PNG string."""
    raw = await request_qr_code(device_name)
    return base64.b64encode(raw).decode()


async def _get_registered_phone() -> str | None:
    """Resolve the Signal phone number for this instance.

    Priority:
    1. SIGNAL_PHONE_NUMBER env var (explicit config).
    2. First account registered on the signal-cli-rest-api sidecar
       (auto-discovered after QR-code linking).

    Returns an E.164 phone string or None.
    """
    settings = get_settings()
    if settings.signal_phone_number:
        return settings.signal_phone_number
    # Auto-discover from sidecar
    try:
        accounts = await get_accounts()
        if accounts:
            return accounts[0]
    except Exception as e:
        logger.debug("Could not auto-discover Signal phone: %s", e)
    return None


async def check_link_complete() -> dict:
    """Check if the linking process completed.

    Returns a dict with keys: linked (bool), number (str|None).
    Queries the signal-cli-rest-api /v1/accounts endpoint to discover
    whether a phone number has been registered (via QR-code linking).
    """
    url = f"{_signal_base_url()}/v1/accounts"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            accounts = resp.json()
            if not isinstance(accounts, list) or not accounts:
                return {"linked": False, "number": None}
            # If env var is set, look for that specific number
            settings = get_settings()
            if settings.signal_phone_number:
                if settings.signal_phone_number in accounts:
                    return {"linked": True, "number": settings.signal_phone_number}
                return {"linked": False, "number": None}
            # No env var — return the first registered account
            return {"linked": True, "number": accounts[0]}
    except Exception as e:
        logger.warning("Failed to check link status: %s", e)
        return {"linked": False, "number": None}


async def send_message(recipient: str, message: str, text_mode: str = "styled") -> bool:
    """Send a text message via Signal.

    Args:
        recipient: Phone number in E.164 format.
        message: Message text (supports styled markdown).
        text_mode: 'styled' for markdown-like formatting.

    Returns True on success, raises on failure.
    """
    phone = await _get_registered_phone()
    if not phone:
        raise ValueError(
            "No registered Signal account — set SIGNAL_PHONE_NUMBER or link via QR code"
        )

    url = f"{_signal_base_url()}/v2/send"
    payload = {
        "message": message,
        "number": phone,
        "recipients": [recipient],
        "text_mode": text_mode,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
    return True


async def get_accounts() -> list[str]:
    """List registered/linked Signal phone numbers on the sidecar."""
    url = f"{_signal_base_url()}/v1/accounts"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


# ── Database helpers (shared across user stories) ────────────────────────


async def get_connection_by_user(github_user_id: str) -> SignalConnection | None:
    """Fetch the signal connection for a user, or None."""
    db = get_db()
    cursor = await db.execute(
        "SELECT * FROM signal_connections WHERE github_user_id = ? AND status != 'disconnected'",
        (github_user_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return SignalConnection(**dict(row))


async def get_connection_by_phone_hash(phone_hash: str) -> SignalConnection | None:
    """Fetch a connected signal connection by phone hash."""
    db = get_db()
    cursor = await db.execute(
        "SELECT * FROM signal_connections WHERE signal_phone_hash = ? AND status = 'connected'",
        (phone_hash,),
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return SignalConnection(**dict(row))


async def create_connection(github_user_id: str, phone_number: str) -> SignalConnection:
    """Create a new signal connection with encrypted phone storage.

    Handles phone conflict detection: if another user already has this phone
    linked, that connection is deactivated and a conflict banner is created.
    """
    db = get_db()
    enc = _get_encryption()
    phone_hash = _hash_phone(phone_number)
    now = datetime.now(UTC).isoformat()

    # ── Phone conflict detection (FR-015) ──
    existing = await get_connection_by_phone_hash(phone_hash)
    if existing and existing.github_user_id != github_user_id:
        # Deactivate old connection
        await db.execute(
            "UPDATE signal_connections SET status = 'disconnected', updated_at = ? WHERE id = ?",
            (now, existing.id),
        )
        # Purge PII from old connection
        await db.execute(
            "UPDATE signal_connections SET signal_phone_encrypted = '', signal_phone_hash = '' WHERE id = ?",
            (existing.id,),
        )
        # Create conflict banner for displaced user
        banner = SignalConflictBanner(
            github_user_id=existing.github_user_id,
            message="Your Signal connection was deactivated because another account linked the same phone number. Please re-link if needed.",
        )
        await db.execute(
            "INSERT INTO signal_conflict_banners (id, github_user_id, message, dismissed, created_at) VALUES (?, ?, ?, ?, ?)",
            (banner.id, banner.github_user_id, banner.message, banner.dismissed, banner.created_at),
        )
        await db.commit()
        logger.info(
            "Phone conflict: displaced user %s, banner %s", existing.github_user_id, banner.id
        )

    # Delete any existing connection for THIS user (re-link scenario)
    await db.execute(
        "DELETE FROM signal_connections WHERE github_user_id = ?",
        (github_user_id,),
    )

    conn = SignalConnection(
        github_user_id=github_user_id,
        signal_phone_encrypted=enc.encrypt(phone_number),
        signal_phone_hash=phone_hash,
        status=SignalConnectionStatus.CONNECTED,
        linked_at=now,
        created_at=now,
        updated_at=now,
    )

    await db.execute(
        """INSERT INTO signal_connections
        (id, github_user_id, signal_phone_encrypted, signal_phone_hash,
         status, notification_mode, last_active_project_id, linked_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            conn.id,
            conn.github_user_id,
            conn.signal_phone_encrypted,
            conn.signal_phone_hash,
            conn.status.value,
            conn.notification_mode.value,
            conn.last_active_project_id,
            conn.linked_at,
            conn.created_at,
            conn.updated_at,
        ),
    )
    await db.commit()
    logger.info("Created signal connection %s for user %s", conn.id, github_user_id)
    return conn


async def disconnect_and_purge(github_user_id: str) -> bool:
    """Disconnect Signal and immediately delete all PII (FR-014).

    Returns True if a connection was found and deleted.
    """
    db = get_db()
    cursor = await db.execute(
        "DELETE FROM signal_connections WHERE github_user_id = ?",
        (github_user_id,),
    )
    await db.commit()
    deleted = cursor.rowcount > 0
    if deleted:
        logger.info("Disconnected and purged PII for user %s", github_user_id)
    return deleted


async def get_banners_for_user(github_user_id: str) -> list[SignalConflictBanner]:
    """Get undismissed conflict banners for a user."""
    db = get_db()
    cursor = await db.execute(
        "SELECT * FROM signal_conflict_banners WHERE github_user_id = ? AND dismissed = 0",
        (github_user_id,),
    )
    rows = await cursor.fetchall()
    return [SignalConflictBanner(**dict(r)) for r in rows]


async def dismiss_banner(banner_id: str, github_user_id: str) -> bool:
    """Mark a banner as dismissed. Returns True if found and updated."""
    db = get_db()
    cursor = await db.execute(
        "UPDATE signal_conflict_banners SET dismissed = 1 WHERE id = ? AND github_user_id = ?",
        (banner_id, github_user_id),
    )
    await db.commit()
    return cursor.rowcount > 0


async def create_signal_message(
    connection_id: str,
    direction: SignalMessageDirection,
    chat_message_id: str | None = None,
    content_preview: str | None = None,
    delivery_status: SignalDeliveryStatus = SignalDeliveryStatus.PENDING,
) -> SignalMessage:
    """Insert a signal_messages audit row."""
    db = get_db()
    msg = SignalMessage(
        connection_id=connection_id,
        direction=direction,
        chat_message_id=chat_message_id,
        content_preview=content_preview[:200] if content_preview else None,
        delivery_status=delivery_status,
    )
    await db.execute(
        """INSERT INTO signal_messages
        (id, connection_id, direction, chat_message_id, content_preview,
         delivery_status, retry_count, next_retry_at, error_detail, created_at, delivered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            msg.id,
            msg.connection_id,
            msg.direction.value,
            msg.chat_message_id,
            msg.content_preview,
            msg.delivery_status.value,
            msg.retry_count,
            msg.next_retry_at,
            msg.error_detail,
            msg.created_at,
            msg.delivered_at,
        ),
    )
    await db.commit()
    return msg


async def update_signal_message_status(
    message_id: str,
    status: SignalDeliveryStatus,
    error_detail: str | None = None,
    next_retry_at: str | None = None,
) -> None:
    """Update a signal_messages row's delivery status."""
    db = get_db()
    now = datetime.now(UTC).isoformat()
    delivered_at = now if status == SignalDeliveryStatus.DELIVERED else None

    await db.execute(
        """UPDATE signal_messages
        SET delivery_status = ?, error_detail = ?, next_retry_at = ?,
            delivered_at = COALESCE(?, delivered_at),
            retry_count = CASE WHEN ? = 'retrying' THEN retry_count + 1 ELSE retry_count END
        WHERE id = ?""",
        (status.value, error_detail, next_retry_at, delivered_at, status.value, message_id),
    )
    await db.commit()


async def update_last_active_project(github_user_id: str, project_id: str) -> None:
    """Update the last_active_project_id for inbound message routing."""
    db = get_db()
    now = datetime.now(UTC).isoformat()
    await db.execute(
        "UPDATE signal_connections SET last_active_project_id = ?, updated_at = ? WHERE github_user_id = ? AND status = 'connected'",
        (project_id, now, github_user_id),
    )
    await db.commit()


async def store_inbound_message(
    conn: SignalConnection,
    message_text: str,
    project_id: str | None = None,
) -> str:
    """Store an inbound Signal message in the chat system and create audit row.

    Creates a ChatMessage, adds it to the in-memory message store,
    and inserts a signal_messages audit row (direction=inbound).

    Returns the chat_message_id.
    """
    from uuid import NAMESPACE_URL, uuid5

    from src.api.chat import add_message
    from src.models.chat import ChatMessage, SenderType

    # Deterministic session ID so all Signal messages for a user share one session
    signal_session_id = uuid5(NAMESPACE_URL, f"signal:{conn.github_user_id}")

    user_message = ChatMessage(
        session_id=signal_session_id,
        sender_type=SenderType.USER,
        content=message_text,
    )
    add_message(signal_session_id, user_message)

    chat_message_id = str(user_message.message_id)

    await create_signal_message(
        connection_id=conn.id,
        direction=SignalMessageDirection.INBOUND,
        chat_message_id=chat_message_id,
        content_preview=message_text[:200],
        delivery_status=SignalDeliveryStatus.DELIVERED,
    )

    logger.info(
        "Stored inbound Signal message %s for user %s (project: %s)",
        chat_message_id,
        conn.github_user_id,
        project_id,
    )

    return chat_message_id


# ── WebSocket Inbound Listener (T018) ───────────────────────────────────

# Global handle so main.py lifespan can cancel it
_ws_listener_task: asyncio.Task | None = None


async def send_welcome_message(phone: str) -> None:
    """Send an introduction message after Signal account linking.

    Explains available commands so the user can start chatting via Signal.
    """
    text = (
        "\U0001f44b *Welcome to Agent Projects!*\n\n"
        "Your Signal account is now connected. "
        "You can chat with me just like the chat window in the app.\n\n"
        "*Here's what you can do:*\n"
        "\u2022 Describe a feature and I'll draft a GitHub issue\n"
        "\u2022 Ask to update a task's status\n"
        "\u2022 Describe a task and I'll create a proposal\n"
        "\u2022 Reply *CONFIRM* to approve or *REJECT* to cancel proposals\n\n"
        "Use *#project-name* to target a specific project.\n\n"
        "_To start, make sure you have an active project in the app, "
        "then send me a message here!_"
    )
    try:
        await send_message(phone, text)
        logger.info("Sent welcome message to newly linked Signal user")
    except Exception as e:
        logger.warning("Failed to send welcome message: %s", e)


async def start_signal_ws_listener() -> None:
    """Start the WebSocket listener as a background task.

    Called from the FastAPI lifespan handler.  Resolves the phone number
    from SIGNAL_PHONE_NUMBER env var or the signal-cli-rest-api sidecar.
    """
    global _ws_listener_task
    if _ws_listener_task and not _ws_listener_task.done():
        return  # Already running
    phone = await _get_registered_phone()
    if not phone:
        logger.warning("No registered Signal account — WebSocket listener not started")
        return
    _ws_listener_task = asyncio.create_task(_ws_listen_loop(phone))
    logger.info("Signal WebSocket listener started for %s", phone)


async def restart_signal_ws_listener() -> None:
    """Stop and restart the WS listener (e.g. after new account linking)."""
    await stop_signal_ws_listener()
    await start_signal_ws_listener()


async def stop_signal_ws_listener() -> None:
    """Cancel the WebSocket listener task gracefully."""
    global _ws_listener_task
    if _ws_listener_task and not _ws_listener_task.done():
        _ws_listener_task.cancel()
        try:
            await _ws_listener_task
        except asyncio.CancelledError:
            pass
    _ws_listener_task = None
    logger.info("Signal WebSocket listener stopped")


async def _ws_listen_loop(phone: str) -> None:
    """Persistent WebSocket listener with reconnection (5s/10s backoff)."""
    base = _signal_base_url()
    ws_scheme = "wss" if base.startswith("https://") else "ws"
    netloc = base.split("://", 1)[-1].rstrip("/")
    url = f"{ws_scheme}://{netloc}/v1/receive/{phone}"

    while True:
        try:
            async with websockets.connect(url, ping_interval=30) as ws:
                logger.info("Connected to Signal WebSocket at %s", url)
                async for raw_message in ws:
                    try:
                        data = json.loads(raw_message)
                        await _process_inbound_ws_message(data)
                    except json.JSONDecodeError:
                        logger.warning("Received non-JSON message on Signal WS")
                    except Exception:
                        logger.exception("Error processing inbound Signal message")
        except asyncio.CancelledError:
            logger.info("Signal WebSocket listener cancelled")
            return
        except (websockets.ConnectionClosed, ConnectionError) as e:
            logger.warning("Signal WebSocket disconnected: %s. Reconnecting in 5s...", e)
            await asyncio.sleep(5)
        except Exception:
            logger.exception(
                "Unexpected error in Signal WebSocket listener. Reconnecting in 10s..."
            )
            await asyncio.sleep(10)


# ── Inbound Message Processing (T019) ───────────────────────────────────

# Pattern for #project-name override (FR-013)
_PROJECT_TAG_RE = re.compile(r"#([\w-]+)")


async def _process_inbound_ws_message(data: dict) -> None:
    """Process an inbound Signal message from the WebSocket stream.

    The sidecar is a **linked device**, so we ONLY process
    syncMessage.sentMessage "Note to Self" (destination == source).
    All other envelope types (dataMessage from contacts, typing
    indicators, read receipts) are silently ignored.

    Handles:
    - syncMessage.sentMessage "Note to Self" (user sent from primary device)
    - Phone hash lookup to find the linked user (FR-006)
    - Project routing via last_active_project_id
    - #project-name override (FR-013)
    - Auto-reply for media/attachments (FR-010)
    - Message truncation at 100K chars
    """
    envelope = data.get("envelope", data)
    source = envelope.get("source") or envelope.get("sourceNumber")

    if not source:
        return  # Not a user message, skip

    # ── Extract message text from syncMessage only ─────────────────
    # The sidecar runs as a **linked device**, so the ONLY messages
    # we should process are syncMessage.sentMessage "Note to Self"
    # (destination == source).  dataMessage envelopes are messages
    # from OTHER people in the user's Signal contacts — the app must
    # NEVER reply to those.
    sync_message = envelope.get("syncMessage")

    if not sync_message:
        return  # dataMessage, typing indicators, receipts — ignore

    sent = sync_message.get("sentMessage")
    if not sent:
        return  # Read receipts, typing, etc.

    dest = sent.get("destinationNumber") or sent.get("destination", "")
    if dest != source:
        return  # Message to someone else — not our business

    message_text: str = sent.get("message", "")
    has_attachment: bool = bool(sent.get("attachments"))

    # Auto-reply for attachments (FR-010)
    if has_attachment:
        await _send_auto_reply(
            source,
            "⚠️ Only text messages are supported. Please send your message as text.",
        )
        if not message_text:
            return
        # Attachment included a text caption — continue processing the text

    if not message_text:
        return

    # Truncate at 100K chars
    if len(message_text) > 100_000:
        message_text = message_text[:100_000]

    # Look up sender by phone hash
    phone_hash = _hash_phone(source)
    conn = await get_connection_by_phone_hash(phone_hash)

    if not conn:
        # The user's phone is no longer linked — silently ignore.
        # This can happen if they unlinked in the app but the sidecar
        # is still running on their Signal account.
        logger.debug("Ignoring Note-to-Self from unlinked phone %s", phone_hash[:8])
        return

    # Determine target project
    project_id = conn.last_active_project_id

    # Check for #project-name override (FR-013)
    tag_match = _PROJECT_TAG_RE.search(message_text)
    if tag_match:
        project_tag = tag_match.group(1)
        resolved_project_id = await _resolve_project_by_name(conn.github_user_id, project_tag)
        if resolved_project_id:
            project_id = resolved_project_id
            # Update last_active_project
            await update_last_active_project(conn.github_user_id, project_id)
            # Strip the tag from the message
            message_text = message_text.replace(f"#{project_tag}", "").strip()

    if not project_id:
        # Try to list available projects so the user can pick one
        project_list = await _list_user_projects(conn.github_user_id)
        if project_list and len(project_list) == 1:
            # Auto-select the only project
            name, pid = project_list[0]
            project_id = pid
            await update_last_active_project(conn.github_user_id, project_id)
            await _send_auto_reply(
                source,
                f"Auto-selected your only project: *{name}*",
            )
        elif project_list:
            tags = "\n".join(
                f"  • *#{p_name.lower().replace(' ', '-')}*" for p_name, _ in project_list
            )
            await _send_auto_reply(
                source,
                f"No active project selected. Include a project tag in your message:\n\n"
                f"{tags}\n\n"
                f"Example: *#project-name Add green background to app*",
            )
            return
        else:
            await _send_auto_reply(
                source,
                "No projects found. Open a project in the app first, then send a message here.",
            )
            return

    # Store message in chat system and create audit row
    await store_inbound_message(conn, message_text, project_id)

    # Fire-and-forget AI processing and Signal reply
    async def _safe_process() -> None:
        try:
            from src.services.signal_chat import process_signal_chat

            await process_signal_chat(conn, message_text, project_id, source)
        except Exception:
            logger.exception("Signal AI processing failed")

    asyncio.create_task(_safe_process())


async def _send_auto_reply(recipient: str, text: str) -> None:
    """Send an auto-reply message via Signal."""
    try:
        await send_message(recipient, text)
    except Exception as e:
        logger.warning("Failed to send auto-reply to %s: %s", recipient[:6], e)


async def _resolve_project_by_name(github_user_id: str, name: str) -> str | None:
    """Resolve a project name/tag to a project_id.

    Matches by name (case-insensitive, spaces→hyphens).
    Uses _list_user_projects which falls back to GitHub API if cache is empty.
    """
    try:
        projects = await _list_user_projects(github_user_id)
        for p_name, p_id in projects:
            if p_name.lower().replace(" ", "-") == name.lower() or p_name.lower() == name.lower():
                return p_id
        return None
    except Exception:
        return None


async def _list_user_projects(github_user_id: str) -> list[tuple[str, str]]:
    """Return [(name, project_id), ...] for the user's projects.

    Attempts cache first; falls back to GitHub API using the user's
    stored access token if cache is empty.
    """
    try:
        from src.services.cache import cache, get_user_projects_cache_key

        projects = cache.get(get_user_projects_cache_key(github_user_id))
        if projects:
            return [(p.name, p.project_id) for p in projects]

        # Cache empty — try fetching from GitHub directly
        from src.services.database import get_db as _get_db
        from src.services.github_projects import github_projects_service
        from src.services.session_store import get_sessions_by_user

        db = _get_db()
        sessions = await get_sessions_by_user(db, github_user_id)
        if not sessions:
            return []
        session = sorted(sessions, key=lambda s: s.updated_at, reverse=True)[0]
        token = session.access_token
        username = session.github_username
        if not token or not username:
            return []
        fetched = await github_projects_service.list_user_projects(token, username)
        if fetched:
            cache.set(get_user_projects_cache_key(github_user_id), fetched)
            return [(p.name, p.project_id) for p in fetched]
        return []
    except Exception:
        logger.debug("Failed to list projects for user %s", github_user_id, exc_info=True)
        return []
