"""Outbound Signal message delivery with formatting and retry.

Formats chat messages for Signal's styled text mode, delivers them via
signal_bridge.send_message, and tracks delivery status in signal_messages.

Uses tenacity for exponential-backoff retry (30s → 2min → 8min per FR-008).
Fire-and-forget via asyncio.create_task so the chat response is not blocked.
"""

from __future__ import annotations

import asyncio
import logging

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import get_settings
from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.signal import (
    SignalConnectionStatus,
    SignalDeliveryStatus,
    SignalMessageDirection,
    SignalNotificationMode,
)
from src.services.signal_bridge import (
    create_signal_message,
    get_connection_by_user,
    send_message,
    update_signal_message_status,
)

logger = logging.getLogger(__name__)

# ── Retry-eligible transport errors (excludes 4xx HTTPStatusError) ───────

_RETRYABLE_ERRORS = (
    httpx.ConnectError,
    httpx.TimeoutException,
    ConnectionError,
    TimeoutError,
    OSError,
)

# ── Message Formatting ───────────────────────────────────────────────────

MAX_SIGNAL_MESSAGE_LENGTH = 4000  # Conservative limit for readability


def format_signal_message(
    message: ChatMessage,
    project_name: str | None = None,
    deep_link_url: str | None = None,
) -> str:
    """Format a ChatMessage for Signal's styled text mode.

    Uses *bold*, _italic_, and emoji anchors per research.md Topic 3.
    """
    parts: list[str] = []

    # Header with emoji based on action type
    header = _get_header(message)
    parts.append(header)

    # Project context
    if project_name:
        parts.append(f"_Project: {project_name}_")

    parts.append("")  # blank line

    # Message body — summarize action-bearing messages
    body = _format_body(message)
    parts.append(body)

    # Deep link
    if deep_link_url:
        parts.append("")
        parts.append(f"👉 Open in app: {deep_link_url}")

    text = "\n".join(parts)

    # Truncate if needed
    if len(text) > MAX_SIGNAL_MESSAGE_LENGTH:
        text = text[: MAX_SIGNAL_MESSAGE_LENGTH - 20] + "\n\n_…message truncated_"

    return text


def _get_header(message: ChatMessage) -> str:
    """Return a styled header line based on action type."""
    if message.action_type == ActionType.TASK_CREATE:
        status = (message.action_data or {}).get("status", "")
        if status == "confirmed":
            return "✅ *Task Created*"
        return "📋 *Task Proposal*"

    if message.action_type == ActionType.STATUS_UPDATE:
        status = (message.action_data or {}).get("status", "")
        if status == "confirmed":
            return "✅ *Status Updated*"
        return "📋 *Status Change Proposal*"

    if message.action_type == ActionType.ISSUE_CREATE:
        status = (message.action_data or {}).get("status", "")
        if status == "confirmed":
            return "✅ *Issue Created*"
        return "📋 *Issue Recommendation*"

    if message.sender_type == SenderType.SYSTEM:
        return "🔔 *System Notification*"

    return "💬 *Assistant Message*"


def _format_body(message: ChatMessage) -> str:
    """Format the message body, summarising action-bearing messages."""
    action_data = message.action_data or {}

    if message.action_type == ActionType.TASK_CREATE:
        title = action_data.get("proposed_title", "")
        if title:
            return f"*{title}*\n\n{message.content[:500]}"

    if message.action_type == ActionType.STATUS_UPDATE:
        task = action_data.get("task_title", "")
        target = action_data.get("target_status", "")
        if task and target:
            return f"*{task}* → _{target}_\n\n{message.content[:500]}"

    if message.action_type == ActionType.ISSUE_CREATE:
        title = action_data.get("proposed_title", "")
        if title:
            return f"*{title}*\n\n{message.content[:500]}"

    # Generic: just use the content
    return message.content[:1000]


# ── Notification Preference Filtering (FR-007) ──────────────────────────


def should_deliver(notification_mode: SignalNotificationMode, message: ChatMessage) -> bool:
    """Check if a message should be delivered based on the user's preference.

    Returns True if the message passes the preference filter.
    """
    if notification_mode == SignalNotificationMode.NONE:
        return False

    if notification_mode == SignalNotificationMode.ALL:
        return True

    if notification_mode == SignalNotificationMode.ACTIONS_ONLY:
        # Only deliver messages with action proposals (pending)
        return (
            message.action_type
            in (
                ActionType.TASK_CREATE,
                ActionType.STATUS_UPDATE,
                ActionType.ISSUE_CREATE,
            )
            and (message.action_data or {}).get("status") == "pending"
        )

    if notification_mode == SignalNotificationMode.CONFIRMATIONS_ONLY:
        # Only deliver system confirmations
        return message.sender_type == SenderType.SYSTEM or (
            message.action_data is not None
            and (message.action_data or {}).get("status") == "confirmed"
        )

    return True


# ── Delivery with Retry (FR-008) ────────────────────────────────────────


@retry(
    stop=stop_after_attempt(4),  # 1 initial + 3 retries
    wait=wait_exponential(
        multiplier=30, exp_base=4, min=30, max=480
    ),  # 30s → 120s → 480s per FR-008
    retry=retry_if_exception_type(_RETRYABLE_ERRORS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def _deliver_with_retry(recipient: str, text: str) -> None:
    """Deliver a Signal message with tenacity retry."""
    await send_message(recipient, text)


async def _delivery_task(
    recipient: str,
    text: str,
    signal_message_id: str,
) -> None:
    """Background task: deliver and update audit row status."""
    try:
        await _deliver_with_retry(recipient, text)
        await update_signal_message_status(
            signal_message_id,
            SignalDeliveryStatus.DELIVERED,
        )
        logger.info("Signal message %s delivered", signal_message_id)
    except Exception as exc:
        logger.error(
            "Signal message %s failed after all retries: %s",
            signal_message_id,
            exc,
        )
        await update_signal_message_status(
            signal_message_id,
            SignalDeliveryStatus.FAILED,
            error_detail=str(exc)[:500],
        )


async def deliver_chat_message_via_signal(
    github_user_id: str,
    message: ChatMessage,
    project_name: str | None = None,
    project_id: str | None = None,
) -> None:
    """Fire-and-forget delivery of a chat message to the user's linked Signal.

    Checks connection status and notification preferences before sending.
    Creates a signal_messages audit row and launches a background retry task.
    """
    conn = await get_connection_by_user(github_user_id)
    if not conn or conn.status != SignalConnectionStatus.CONNECTED:
        return  # No active connection — skip silently

    # Check notification preference filter (FR-007)
    if not should_deliver(conn.notification_mode, message):
        logger.debug(
            "Signal delivery skipped for user %s: preference=%s, action_type=%s",
            github_user_id,
            conn.notification_mode.value,
            message.action_type,
        )
        return

    # Decrypt phone number for delivery
    from src.services.signal_bridge import _get_encryption

    enc = _get_encryption()
    try:
        phone = enc.decrypt(conn.signal_phone_encrypted)
    except Exception:
        logger.error("Failed to decrypt phone for user %s", github_user_id)
        return

    # Build deep link
    settings = get_settings()
    deep_link = None
    if project_id:
        deep_link = f"{settings.frontend_url}/projects/{project_id}/chat"

    # Format
    text = format_signal_message(message, project_name=project_name, deep_link_url=deep_link)

    # Create audit row
    audit = await create_signal_message(
        connection_id=conn.id,
        direction=SignalMessageDirection.OUTBOUND,
        chat_message_id=str(message.message_id),
        content_preview=text[:200],
        delivery_status=SignalDeliveryStatus.PENDING,
    )

    # Fire-and-forget background retry task
    asyncio.create_task(_delivery_task(phone, text, audit.id))
