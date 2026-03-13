"""Chat messaging endpoints — send, receive, and clear messages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Request

from src.api.auth import get_session_dep
from src.dependencies import require_selected_project
from src.exceptions import ValidationError
from src.logging_utils import get_logger
from src.middleware.rate_limit import limiter
from src.models.chat import (
    ChatMessage,
    ChatMessageRequest,
    ChatMessagesResponse,
    SenderType,
)
from src.models.common import MessageResponse
from src.models.user import UserSession
from src.services.ai_agent import get_ai_agent_service

if TYPE_CHECKING:
    pass

from src.api.chat._state import (
    _messages,
    add_message,
    get_session_messages,
)
from src.api.chat.commands import (
    _handle_agent_command,
    _handle_feature_request,
    _handle_status_change,
    _handle_task_generation,
)
from src.services.cache import (
    cache,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/messages", response_model=ChatMessagesResponse)
async def get_messages(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChatMessagesResponse:
    """Get chat messages for current session."""
    # Phase B: try DB read first, fallback to in-memory
    try:
        from src.services.chat_store import get_messages as _get_db_messages
        from src.services.database import get_db

        db = get_db()
        rows = await _get_db_messages(db, session_id=str(session.session_id))
        if rows:
            from src.models.chat import ActionType, SenderType

            db_messages = []
            for row in rows:
                import json as _json

                action_data = _json.loads(row["action_data"]) if row.get("action_data") else None
                action_type_val = row.get("action_type")
                db_messages.append(
                    ChatMessage(
                        message_id=row["message_id"],
                        session_id=row["session_id"],
                        sender_type=SenderType(row["sender_type"]),
                        content=row["content"],
                        action_type=ActionType(action_type_val) if action_type_val else None,
                        action_data=action_data,
                    )
                )
            return ChatMessagesResponse(messages=db_messages)
    except Exception:
        pass  # Fallback to in-memory

    messages = get_session_messages(session.session_id)
    return ChatMessagesResponse(messages=messages)


@router.delete("/messages", response_model=MessageResponse)
async def clear_messages(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict[str, str]:
    """Clear all chat messages for current session."""
    key = str(session.session_id)
    if key in _messages:
        _messages[key] = []

    # Phase A write-through: clear persisted messages too
    try:
        from src.services.chat_store import clear_messages as _clear_db
        from src.services.database import get_db

        await _clear_db(get_db(), session_id=key)
    except Exception:
        pass  # Non-fatal — in-memory already cleared

    return {"message": "Chat history cleared"}


@router.post("/messages", response_model=ChatMessage)
@limiter.limit("10/minute")
async def send_message(
    request: Request,
    chat_request: ChatMessageRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChatMessage:
    """Send a chat message and get AI response."""
    # Require project selection
    selected_project_id = require_selected_project(session)

    # Validate pipeline_id if provided
    if chat_request.pipeline_id:
        from src.services.database import get_db
        from src.services.pipelines.service import PipelineService

        try:
            db = get_db()
            pipeline_svc = PipelineService(db)
            pipeline = await pipeline_svc.get_pipeline(
                selected_project_id, chat_request.pipeline_id
            )
            if pipeline is None:
                raise ValidationError(f"Pipeline not found: {chat_request.pipeline_id}")
        except ValidationError:
            raise
        except Exception as exc:
            logger.warning(
                "Pipeline validation failed for pipeline_id=%s: %s", chat_request.pipeline_id, exc
            )
            raise ValidationError(f"Pipeline not found: {chat_request.pipeline_id}") from exc

    # Try to get AI service (optional)
    try:
        ai_service = get_ai_agent_service()
    except ValueError:
        # AI not configured - return error message
        error_msg = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content="AI features are not configured. Please set up your AI provider credentials (GitHub Copilot OAuth or Azure OpenAI) to use chat functionality.",
        )
        add_message(session.session_id, error_msg)
        return error_msg

    # Create user message
    user_message = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.USER,
        content=chat_request.content,
    )
    add_message(session.session_id, user_message)

    # Get project details for context
    project_name = "Unknown Project"
    project_columns = []
    cache_key = get_user_projects_cache_key(session.github_user_id)
    cached_projects = cache.get(cache_key)
    if cached_projects:
        for p in cached_projects:
            if p.project_id == selected_project_id:
                project_name = p.name
                project_columns = [col.name for col in p.status_columns]
                break

    # Get current tasks for context
    tasks_cache_key = get_project_items_cache_key(selected_project_id)
    current_tasks = cache.get(tasks_cache_key) or []

    # ── Priority 0: #agent command — custom agent creation ──────────
    agent_msg = await _handle_agent_command(
        session,
        chat_request.content,
        selected_project_id,
        project_name,
        project_columns,
    )
    if agent_msg:
        return agent_msg

    content = chat_request.content

    # ── Priority 1: Feature request → issue recommendation ───────────
    feature_msg = await _handle_feature_request(
        session,
        content,
        ai_service,
        project_name,
        chat_request.pipeline_id,
        chat_request.ai_enhance,
        chat_request.file_urls,
    )
    if feature_msg:
        return feature_msg

    # ── Priority 2: Status change request ────────────────────────────
    status_msg = await _handle_status_change(
        session,
        content,
        ai_service,
        current_tasks,
        project_columns,
        cached_projects,
        selected_project_id,
        project_name,
    )
    if status_msg:
        return status_msg

    # ── Priority 3: Task generation (metadata-only or full AI) ───────
    return await _handle_task_generation(
        session,
        content,
        ai_service,
        project_name,
        chat_request.ai_enhance,
        chat_request.pipeline_id,
    )
