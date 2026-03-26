"""Chat API endpoints."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.api.auth import get_session_dep
from src.constants import (
    DEFAULT_STATUS_COLUMNS,
    GITHUB_ISSUE_BODY_MAX_LENGTH,
)
from src.dependencies import get_connection_manager, get_github_service, require_selected_project
from src.exceptions import NotFoundError, ValidationError
from src.logging_utils import get_logger, handle_service_error
from src.middleware.rate_limit import limiter
from src.models.chat import (
    ActionType,
    ChatMessage,
    ChatMessageRequest,
    ChatMessagesResponse,
    SenderType,
)
from src.models.recommendation import (
    AITaskProposal,
    IssueRecommendation,
    ProposalConfirmRequest,
    ProposalStatus,
    RecommendationStatus,
)
from src.models.user import UserSession
from src.models.workflow import WorkflowConfiguration
from src.services.ai_agent import get_ai_agent_service

if TYPE_CHECKING:
    from src.services.ai_agent import AIAgentService
from src.services.cache import (
    cache,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)
from src.services.database import get_db
from src.services.settings_store import get_effective_user_settings
from src.services.workflow_orchestrator import (
    WorkflowContext,
    get_agent_slugs,
    get_workflow_config,
    get_workflow_orchestrator,
    set_workflow_config,
)
from src.utils import resolve_repository, utcnow

logger = get_logger(__name__)
router = APIRouter()

# ── File upload validation constants ─────────────────────────────────────
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_FILES_PER_MESSAGE = 5
ALLOWED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
ALLOWED_DOC_TYPES = {".pdf", ".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".vtt", ".srt"}
ALLOWED_ARCHIVE_TYPES = {".zip"}
BLOCKED_TYPES = {".exe", ".sh", ".bat", ".cmd", ".js", ".py", ".rb"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES | ALLOWED_ARCHIVE_TYPES


class FileUploadResponse(BaseModel):
    """Response from file upload endpoint."""

    filename: str
    file_url: str
    file_size: int
    content_type: str


# ── SQLite-backed chat persistence ───────────────────────────────────────
#
# Chat messages, proposals, and recommendations are persisted to SQLite
# via chat_store.py (tables from 023_consolidated_schema.sql).  In-memory
# dicts act as a read-through cache backed by SQLite (single source of truth).
# Writes go to SQLite first, then update the cache on success.

_messages: dict[str, list[ChatMessage]] = {}
_proposals: dict[str, AITaskProposal] = {}
_recommendations: dict[str, IssueRecommendation] = {}
_locks: dict[str, asyncio.Lock] = {}

_PERSIST_MAX_RETRIES = 3
_PERSIST_BASE_DELAY = 0.1  # 100ms, 200ms, 400ms


def _get_lock(key: str) -> asyncio.Lock:
    """Return a per-key asyncio lock (lazy-created)."""
    if key not in _locks:
        _locks[key] = asyncio.Lock()
    return _locks[key]


async def _retry_persist(
    fn,
    *args,
    context: str = "",
    **kwargs,
) -> None:
    """Retry a persistence function with exponential backoff.

    Only *transient* SQLite errors (``OperationalError`` — e.g. database
    locked, busy, I/O) are retried.  Permanent errors (``IntegrityError``,
    ``ProgrammingError``, etc.) are re-raised immediately.

    Raises :class:`PersistenceError` after all retries are exhausted.
    """
    import sqlite3

    from src.exceptions import PersistenceError

    last_exc: Exception | None = None
    for attempt in range(1, _PERSIST_MAX_RETRIES + 1):
        try:
            await fn(*args, **kwargs)
            return
        except sqlite3.OperationalError as exc:
            last_exc = exc
            logger.warning(
                "Persist attempt %d/%d failed (%s): %s",
                attempt,
                _PERSIST_MAX_RETRIES,
                context,
                exc,
            )
            if attempt < _PERSIST_MAX_RETRIES:
                await asyncio.sleep(_PERSIST_BASE_DELAY * (2 ** (attempt - 1)))
        except Exception:
            raise  # Non-transient — fail fast

    raise PersistenceError(
        f"Failed to persist {context} after {_PERSIST_MAX_RETRIES} retries",
        details={"context": context, "last_error": str(last_exc)},
    )


async def _persist_message(session_id: UUID, message: ChatMessage) -> None:
    """Persist a chat message to SQLite with retry."""
    from src.services import chat_store

    db = get_db()
    await _retry_persist(
        chat_store.save_message,
        db,
        session_id=str(session_id),
        message_id=str(message.message_id),
        sender_type=message.sender_type.value,
        content=message.content,
        action_type=message.action_type.value if message.action_type else None,
        action_data=json.dumps(message.action_data) if message.action_data else None,
        context=f"message:{message.message_id}",
    )


async def _persist_proposal(proposal: AITaskProposal) -> None:
    """Persist a proposal to SQLite with retry."""
    from src.services import chat_store

    db = get_db()
    await _retry_persist(
        chat_store.save_proposal,
        db,
        session_id=str(proposal.session_id),
        proposal_id=str(proposal.proposal_id),
        original_input=proposal.original_input,
        proposed_title=proposal.proposed_title,
        proposed_description=proposal.proposed_description,
        status=proposal.status.value,
        edited_title=proposal.edited_title,
        edited_description=proposal.edited_description,
        created_at=proposal.created_at.isoformat(),
        expires_at=proposal.expires_at.isoformat(),
        file_urls=proposal.file_urls or None,
        selected_pipeline_id=proposal.selected_pipeline_id,
        context=f"proposal:{proposal.proposal_id}",
    )


async def _persist_recommendation(recommendation: IssueRecommendation) -> None:
    """Persist a recommendation to SQLite with retry."""
    from src.services import chat_store

    db = get_db()
    await _retry_persist(
        chat_store.save_recommendation,
        db,
        session_id=str(recommendation.session_id),
        recommendation_id=str(recommendation.recommendation_id),
        data=json.dumps(recommendation.model_dump(mode="json")),
        status=recommendation.status.value,
        file_urls=recommendation.file_urls or None,
        context=f"recommendation:{recommendation.recommendation_id}",
    )


async def store_proposal(proposal: AITaskProposal) -> None:
    """Persist a proposal to SQLite, then update cache."""
    await _persist_proposal(proposal)
    _proposals[str(proposal.proposal_id)] = proposal


async def store_recommendation(recommendation: IssueRecommendation) -> None:
    """Persist a recommendation to SQLite, then update cache."""
    await _persist_recommendation(recommendation)
    _recommendations[str(recommendation.recommendation_id)] = recommendation


async def get_proposal(proposal_id: str) -> AITaskProposal | None:
    """Get a proposal by ID from cache or SQLite."""
    # Fast path: in-memory cache
    proposal = _proposals.get(proposal_id)
    if proposal is not None:
        return proposal

    # Slow path: load from SQLite
    try:
        from src.services import chat_store

        db = get_db()
        row = await chat_store.get_proposal_by_id(db, proposal_id)
        if row is None:
            return None
        from datetime import datetime as _dt

        raw_expires = row["expires_at"] or _default_expires_at(row["created_at"])
        parsed_expires = (
            _dt.fromisoformat(raw_expires) if isinstance(raw_expires, str) else raw_expires
        )

        proposal = AITaskProposal(
            proposal_id=row["proposal_id"],
            session_id=row["session_id"],
            original_input=row["original_input"],
            proposed_title=row["proposed_title"],
            proposed_description=row["proposed_description"],
            status=ProposalStatus(row["status"]),
            edited_title=row.get("edited_title"),
            edited_description=row.get("edited_description"),
            file_urls=row.get("file_urls", []),
            selected_pipeline_id=row.get("selected_pipeline_id"),
            created_at=row["created_at"],
            expires_at=parsed_expires,
        )
        _proposals[proposal_id] = proposal
        return proposal
    except Exception:
        logger.warning("Failed to load proposal from SQLite", exc_info=True)
        return None


async def get_recommendation(recommendation_id: str) -> IssueRecommendation | None:
    """Get a recommendation by ID from cache or SQLite."""
    # Fast path: in-memory cache
    rec = _recommendations.get(recommendation_id)
    if rec is not None:
        return rec

    # Slow path: load from SQLite
    try:
        from src.services import chat_store

        db = get_db()
        row = await chat_store.get_recommendation_by_id(db, recommendation_id)
        if row is None:
            return None
        data = json.loads(row["data"]) if isinstance(row["data"], str) else row["data"]
        rec = IssueRecommendation.model_validate(data)
        rec.status = RecommendationStatus(chat_store.recommendation_status_from_db(row["status"]))
        _recommendations[str(rec.recommendation_id)] = rec
        return rec
    except Exception:
        logger.warning("Failed to load recommendation from SQLite", exc_info=True)
        return None


def _default_expires_at(created_at_str: str) -> str:
    """Compute a fallback expires_at when the stored value is NULL."""
    from datetime import datetime, timedelta

    try:
        created = datetime.fromisoformat(created_at_str)
        return (created + timedelta(minutes=10)).isoformat()
    except (ValueError, TypeError):
        return created_at_str


# ── Command dispatch helpers (extracted from send_message) ───────────────


async def _handle_agent_command(
    session: UserSession,
    content: str,
    selected_project_id: str,
    project_name: str,
    project_columns: list[str],
) -> ChatMessage | None:
    """Priority 0: Handle /agent or #agent custom agent creation commands.

    Returns an assistant ChatMessage if the command was handled, None otherwise.
    """
    from src.services.agent_creator import get_active_session, handle_agent_command

    session_key = str(session.session_id)
    is_agent_command = content.strip().lower().startswith(
        "/agent"
    ) or content.strip().lower().startswith("#agent")
    active_agent_session = get_active_session(session_key)

    if not (is_agent_command or active_agent_session):
        return None

    try:
        db = get_db()
        owner, repo = await _resolve_repository(session)
        agent_response_text = await handle_agent_command(
            message=content,
            session_key=session_key,
            project_id=selected_project_id,
            owner=owner,
            repo=repo,
            github_user_id=session.github_user_id,
            access_token=session.access_token,
            db=db,
            project_columns=project_columns,
        )
    except Exception as exc:
        logger.error("#agent command failed: %s", exc)
        agent_response_text = (
            "**Error:** The `#agent` command encountered an unexpected error. Please try again."
        )

    agent_msg = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.ASSISTANT,
        content=agent_response_text,
    )
    await add_message(session.session_id, agent_msg)
    _trigger_signal_delivery(session, agent_msg, project_name)
    return agent_msg


async def _handle_transcript_upload(
    session: UserSession,
    ai_service: AIAgentService,
    project_name: str,
    pipeline_id: str | None,
    file_urls: list[str] | None,
) -> ChatMessage | None:
    """Priority 0.5: Detect transcript files and generate issue recommendation.

    Checks uploaded files for transcript content. If a transcript is detected,
    analyses it via the Transcribe agent and returns an assistant message with
    an ``IssueRecommendation``.  Returns ``None`` when no transcript is found
    so the next handler in the dispatch chain can run.
    """
    if not file_urls:
        return None

    from src.services.transcript_detector import detect_transcript

    upload_dir = Path(tempfile.gettempdir()) / "chat-uploads"

    for file_url in file_urls:
        # Resolve the local file path from the upload URL.
        # Sanitise with os.path.basename (CodeQL-recognised path sanitizer)
        # to strip all directory components and prevent path-traversal.
        raw_name = file_url.rsplit("/", 1)[-1] if "/" in file_url else file_url
        filename = os.path.basename(raw_name)  # noqa: PTH119 — CodeQL sanitizer
        if not filename:
            continue

        # Build the candidate path and normalise it so CodeQL can verify
        # the subsequent prefix check neutralises any traversal attempt.
        candidate = os.path.normpath(os.path.join(str(upload_dir), filename))  # noqa: PTH118
        safe_prefix = os.path.normpath(str(upload_dir)) + os.sep
        if not candidate.startswith(safe_prefix):
            continue

        file_path = Path(candidate)
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.warning("Could not read uploaded file %s: %s", filename, exc)
            continue

        # Strip the 8-char UUID prefix added during upload (format: "abcd1234-original.ext")
        original_name = filename[9:] if len(filename) > 9 and filename[8] == "-" else filename
        result = detect_transcript(original_name, content)

        if not result.is_transcript:
            continue

        # Transcript detected — run through the Transcribe agent
        try:
            metadata_context: dict | None = None
            try:
                owner, repo = await _resolve_repository(session)
                from src.services.github_projects import github_projects_service
                from src.services.metadata_service import MetadataService

                metadata_svc = MetadataService(github_service=github_projects_service)
                ctx = await metadata_svc.get_or_fetch(session.access_token, owner, repo)
                metadata_context = ctx.model_dump()
            except Exception as md_err:
                logger.warning("Metadata fetch for transcript prompt failed: %s", md_err)

            recommendation = await ai_service.analyze_transcript(
                transcript_content=content,
                project_name=project_name,
                session_id=str(session.session_id),
                github_token=session.access_token,
                metadata_context=metadata_context,
            )

            recommendation.selected_pipeline_id = pipeline_id or None
            recommendation.file_urls = file_urls or []

            await store_recommendation(recommendation)

            requirements_preview = "\n".join(
                f"- {req}" for req in recommendation.functional_requirements
            )

            technical_notes_preview = ""
            if recommendation.technical_notes:
                technical_notes_preview = f"\n\n**Technical Notes:**\n{recommendation.technical_notes[:300]}{'...' if len(recommendation.technical_notes) > 300 else ''}"

            assistant_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"""I've analysed the uploaded transcript and generated a GitHub issue recommendation:

**{recommendation.title}**

**User Story:**
{recommendation.user_story}

**UI/UX Description:**
{recommendation.ui_ux_description}

**Functional Requirements:**
{requirements_preview}{technical_notes_preview}

Click **Confirm** to create this issue in GitHub, or **Reject** to discard.""",
                action_type=ActionType.ISSUE_CREATE,
                action_data={
                    "recommendation_id": str(recommendation.recommendation_id),
                    "proposed_title": recommendation.title,
                    "user_story": recommendation.user_story,
                    "original_context": recommendation.original_context,
                    "ui_ux_description": recommendation.ui_ux_description,
                    "functional_requirements": recommendation.functional_requirements,
                    "technical_notes": recommendation.technical_notes,
                    "status": RecommendationStatus.PENDING.value,
                    "file_urls": file_urls,
                    "pipeline_id": pipeline_id,
                },
            )
            await add_message(session.session_id, assistant_message)
            _trigger_signal_delivery(session, assistant_message, project_name)

            logger.info(
                "Generated transcript recommendation %s: %s",
                recommendation.recommendation_id,
                recommendation.title,
            )
            return assistant_message

        except Exception as e:
            logger.error("Failed to analyse transcript: %s", e, exc_info=True)
            error_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"I couldn't extract requirements from the uploaded transcript ({type(e).__name__}). Please try again or paste the transcript content directly.",
            )
            await add_message(session.session_id, error_message)
            return error_message

    return None


async def _handle_feature_request(
    session: UserSession,
    content: str,
    ai_service: AIAgentService,
    project_name: str,
    pipeline_id: str | None,
    ai_enhance: bool,
    file_urls: list[str] | None,
) -> ChatMessage | None:
    """Priority 1: Detect feature request intent and generate issue recommendation.

    Returns an assistant ChatMessage if the intent was a feature request, None otherwise.
    """
    try:
        is_feature_request = await ai_service.detect_feature_request_intent(
            content, github_token=session.access_token
        )
    except Exception as e:
        logger.warning("Feature request detection failed: %s", e)
        is_feature_request = False

    if not is_feature_request:
        return None

    try:
        metadata_context: dict | None = None
        try:
            owner, repo = await _resolve_repository(session)
            from src.services.github_projects import github_projects_service
            from src.services.metadata_service import MetadataService

            metadata_svc = MetadataService(github_service=github_projects_service)
            ctx = await metadata_svc.get_or_fetch(session.access_token, owner, repo)
            metadata_context = ctx.model_dump()
        except Exception as md_err:
            logger.warning("Metadata fetch for prompt injection failed: %s", md_err)

        recommendation = await ai_service.generate_issue_recommendation(
            user_input=content,
            project_name=project_name,
            session_id=str(session.session_id),
            github_token=session.access_token,
            metadata_context=metadata_context,
        )

        recommendation.selected_pipeline_id = pipeline_id or None
        recommendation.file_urls = file_urls or []

        await store_recommendation(recommendation)

        requirements_preview = "\n".join(
            f"- {req}" for req in recommendation.functional_requirements
        )

        technical_notes_preview = ""
        if recommendation.technical_notes:
            technical_notes_preview = f"\n\n**Technical Notes:**\n{recommendation.technical_notes[:300]}{'...' if len(recommendation.technical_notes) > 300 else ''}"

        assistant_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=f"""I've generated a GitHub issue recommendation:

**{recommendation.title}**

**User Story:**
{recommendation.user_story}

**UI/UX Description:**
{recommendation.ui_ux_description}

**Functional Requirements:**
{requirements_preview}{technical_notes_preview}

Click **Confirm** to create this issue in GitHub, or **Reject** to discard.""",
            action_type=ActionType.ISSUE_CREATE,
            action_data={
                "recommendation_id": str(recommendation.recommendation_id),
                "proposed_title": recommendation.title,
                "user_story": recommendation.user_story,
                "original_context": recommendation.original_context,
                "ui_ux_description": recommendation.ui_ux_description,
                "functional_requirements": recommendation.functional_requirements,
                "technical_notes": recommendation.technical_notes,
                "status": RecommendationStatus.PENDING.value,
                "ai_enhance": ai_enhance,
                "file_urls": file_urls,
                "pipeline_id": pipeline_id,
            },
        )
        await add_message(session.session_id, assistant_message)
        _trigger_signal_delivery(session, assistant_message, project_name)

        logger.info(
            "Generated issue recommendation %s: %s",
            recommendation.recommendation_id,
            recommendation.title,
        )
        return assistant_message

    except Exception as e:
        logger.error("Failed to generate issue recommendation: %s", e, exc_info=True)
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content="I couldn't generate an issue recommendation from your feature request. Please try again with more detail.",
        )
        await add_message(session.session_id, error_message)
        return error_message


async def _handle_status_change(
    session: UserSession,
    content: str,
    ai_service: AIAgentService,
    current_tasks: list,
    project_columns: list[str],
    cached_projects: list | None,
    selected_project_id: str,
    project_name: str,
) -> ChatMessage | None:
    """Priority 2: Parse status change request and create proposal.

    Returns an assistant ChatMessage if a status change was detected, None otherwise.
    """
    status_change = await ai_service.parse_status_change_request(
        user_input=content,
        available_tasks=[t.title for t in current_tasks],
        available_statuses=(project_columns or DEFAULT_STATUS_COLUMNS),
        github_token=session.access_token,
    )
    if not status_change:
        return None

    target_task = ai_service.identify_target_task(
        task_reference=status_change.task_reference,
        available_tasks=current_tasks,
    )

    if not target_task:
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=f"I couldn't find a task matching '{status_change.task_reference}'. Please try again with a more specific task name.",
        )
        await add_message(session.session_id, error_message)
        return error_message

    target_status = status_change.target_status
    status_option_id = ""
    status_field_id = ""
    if cached_projects:
        for p in cached_projects:
            if p.project_id == selected_project_id:
                for col in p.status_columns:
                    if col.name.lower() == target_status.lower():
                        status_option_id = col.option_id
                        status_field_id = col.field_id
                        target_status = col.name
                        break
                break

    proposal = AITaskProposal(
        session_id=session.session_id,
        original_input=content,
        proposed_title=target_task.title,
        proposed_description=f"Move from '{target_task.status}' to '{target_status}'",
    )
    await store_proposal(proposal)

    assistant_message = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.ASSISTANT,
        content=f"I'll update the status of **{target_task.title}** from **{target_task.status}** to **{target_status}**.\n\nClick confirm to apply this change.",
        action_type=ActionType.STATUS_UPDATE,
        action_data={
            "proposal_id": str(proposal.proposal_id),
            "task_id": target_task.github_item_id,
            "task_title": target_task.title,
            "current_status": target_task.status,
            "target_status": target_status,
            "status_option_id": status_option_id,
            "status_field_id": status_field_id,
            "status": ProposalStatus.PENDING.value,
        },
    )
    await add_message(session.session_id, assistant_message)
    _trigger_signal_delivery(session, assistant_message, project_name)
    return assistant_message


async def _handle_task_generation(
    session: UserSession,
    content: str,
    ai_service: AIAgentService,
    project_name: str,
    ai_enhance: bool,
    pipeline_id: str | None,
) -> ChatMessage:
    """Priority 3: Generate task from description (metadata-only or full AI).

    Always returns a ChatMessage (success or error).
    """
    if not ai_enhance:
        try:
            title = await ai_service.generate_title_from_description(
                user_input=content,
                project_name=project_name,
                github_token=session.access_token,
            )

            proposal = AITaskProposal(
                session_id=session.session_id,
                original_input=content,
                proposed_title=title,
                proposed_description=content,
                selected_pipeline_id=pipeline_id or None,
            )
            await store_proposal(proposal)

            description_preview = content[:200]
            if len(content) > 200:
                description_preview += "..."

            assistant_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"I've created a task proposal:\n\n**{title}**\n\n{description_preview}\n\nClick confirm to create this task.",
                action_type=ActionType.TASK_CREATE,
                action_data={
                    "proposal_id": str(proposal.proposal_id),
                    "proposed_title": title,
                    "proposed_description": content,
                    "status": ProposalStatus.PENDING.value,
                },
            )
            await add_message(session.session_id, assistant_message)
            _trigger_signal_delivery(session, assistant_message, project_name)
            return assistant_message

        except Exception as e:
            logger.error("Failed to generate metadata (ai_enhance=off): %s", e, exc_info=True)
            error_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content="I couldn't generate metadata for your request. Your input was preserved — please try again.",
            )
            await add_message(session.session_id, error_message)
            return error_message

    # Full AI pipeline: generate both title and description via AI
    try:
        generated = await ai_service.generate_task_from_description(
            user_input=content,
            project_name=project_name,
            github_token=session.access_token,
        )

        proposal = AITaskProposal(
            session_id=session.session_id,
            original_input=content,
            proposed_title=generated.title,
            proposed_description=generated.description,
            selected_pipeline_id=pipeline_id or None,
        )
        await store_proposal(proposal)

        assistant_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=(
                f"I've created a task proposal:\n\n**{generated.title}**\n\n"
                f"{generated.description[:200]}"
                f"{'...' if len(generated.description) > 200 else ''}"
                "\n\nClick confirm to create this task."
            ),
            action_type=ActionType.TASK_CREATE,
            action_data={
                "proposal_id": str(proposal.proposal_id),
                "proposed_title": generated.title,
                "proposed_description": generated.description,
                "status": ProposalStatus.PENDING.value,
            },
        )
        await add_message(session.session_id, assistant_message)
        _trigger_signal_delivery(session, assistant_message, project_name)
        return assistant_message

    except Exception as e:
        logger.error("Failed to generate task: %s", e, exc_info=True)

        # Provide a specific, actionable error message based on failure type
        error_str = str(e)
        if (
            "401" in error_str
            or "Access denied" in error_str
            or "authentication" in error_str.lower()
        ):
            user_hint = (
                "AI provider authentication failed. Please re-authenticate via "
                "GitHub OAuth or check your AI provider credentials in Settings."
            )
        elif (
            "404" in error_str
            or "Resource not found" in error_str
            or "not found" in error_str.lower()
        ):
            user_hint = (
                "The configured AI model could not be found. Please verify your "
                "AI provider and model settings (current model may be unavailable)."
            )
        elif "timed out" in error_str.lower() or isinstance(e, TimeoutError):
            user_hint = (
                "The AI request timed out. The service may be temporarily "
                "unavailable — please try again in a moment."
            )
        elif isinstance(e, (ImportError, ModuleNotFoundError)):
            user_hint = (
                "The AI provider SDK is not available or incompatible. "
                "Please check the server logs and verify the SDK installation."
            )
        else:
            user_hint = (
                "I couldn't generate a task from your description. "
                "Please try again with more detail."
            )

        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=user_hint,
        )
        await add_message(session.session_id, error_message)
        return error_message


async def _resolve_repository(session: UserSession) -> tuple[str, str]:
    """Resolve repository owner and name for issue creation."""
    project_id = require_selected_project(session)
    return await resolve_repository(session.access_token, project_id)


async def get_session_messages(session_id: UUID) -> list[ChatMessage]:
    """Get messages for a session from cache or SQLite."""
    key = str(session_id)
    cached = _messages.get(key)
    if cached is not None:
        return cached

    # Load from SQLite on cache miss
    try:
        from src.services import chat_store

        db = get_db()
        rows = await chat_store.get_messages(db, key)
        messages = []
        for row in rows:
            action_data = None
            if row.get("action_data"):
                try:
                    action_data = json.loads(row["action_data"])
                except (json.JSONDecodeError, TypeError):
                    action_data = None
            messages.append(
                ChatMessage(
                    message_id=row["message_id"],
                    session_id=row["session_id"],
                    sender_type=SenderType(row["sender_type"]),
                    content=row["content"],
                    action_type=ActionType(row["action_type"]) if row.get("action_type") else None,
                    action_data=action_data,
                )
            )
        _messages[key] = messages
        return messages
    except Exception:
        logger.warning("Failed to load messages from SQLite", exc_info=True)
        return []


async def add_message(session_id: UUID, message: ChatMessage) -> None:
    """Persist a message to SQLite, then update cache."""
    key = str(session_id)
    await _persist_message(session_id, message)
    async with _get_lock(key):
        if key not in _messages:
            _messages[key] = []
        _messages[key].append(message)


def _trigger_signal_delivery(
    session: UserSession,
    message: ChatMessage,
    project_name: str | None = None,
) -> None:
    """Fire-and-forget Signal delivery for assistant/system messages.

    Only delivers for non-user messages when the user has an active Signal connection.
    """
    if message.sender_type == SenderType.USER:
        return

    async def _deliver() -> None:
        try:
            from src.services.signal_delivery import deliver_chat_message_via_signal

            await deliver_chat_message_via_signal(
                github_user_id=session.github_user_id,
                message=message,
                project_name=project_name,
                project_id=session.selected_project_id,
            )
        except Exception as e:
            logger.debug("Signal delivery trigger failed (non-fatal): %s", e)

    try:
        from src.services.task_registry import task_registry

        task_registry.create_task(_deliver(), name="signal-delivery")
    except RuntimeError:
        pass  # No running event loop — skip silently


@router.get("/messages", response_model=ChatMessagesResponse)
async def get_messages(
    session: Annotated[UserSession, Depends(get_session_dep)],
    limit: int = 50,
    offset: int = 0,
) -> ChatMessagesResponse:
    """Get chat messages for current session with pagination.

    Pagination is performed at the database level to avoid loading all
    rows into memory for sessions with large message histories.
    """
    from src.services import chat_store

    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    key = str(session.session_id)

    db = get_db()
    total = await chat_store.count_messages(db, key)
    rows = await chat_store.get_messages(db, key, limit=limit, offset=offset)
    paginated: list[ChatMessage] = []
    for row in rows:
        action_data = None
        if row.get("action_data"):
            try:
                action_data = json.loads(row["action_data"])
            except (json.JSONDecodeError, TypeError):
                action_data = None
        paginated.append(
            ChatMessage(
                message_id=row["message_id"],
                session_id=row["session_id"],
                sender_type=SenderType(row["sender_type"]),
                content=row["content"],
                action_type=ActionType(row["action_type"]) if row.get("action_type") else None,
                action_data=action_data,
            )
        )
    return ChatMessagesResponse(
        messages=paginated,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/messages")
async def clear_messages(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict[str, str]:
    """Clear all chat messages for current session."""
    key = str(session.session_id)
    _messages.pop(key, None)
    try:
        from src.services import chat_store

        db = get_db()
        await chat_store.clear_messages(db, key)
    except Exception:
        logger.warning("Failed to clear messages from SQLite", exc_info=True)
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
            handle_service_error(exc, "validate pipeline")

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
        await add_message(session.session_id, error_msg)
        return error_msg

    # Create user message
    user_message = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.USER,
        content=chat_request.content,
    )
    await add_message(session.session_id, user_message)

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

    # Strip slash-command prefixes so the AI prompt receives clean user input
    import re as _re

    content = _re.sub(r"^/plan\s+", "", content)

    # ── Priority 0.5: Transcript upload → issue recommendation ────────
    transcript_msg = await _handle_transcript_upload(
        session,
        ai_service,
        project_name,
        chat_request.pipeline_id,
        chat_request.file_urls,
    )
    if transcript_msg:
        return transcript_msg

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


@router.post("/proposals/{proposal_id}/confirm", response_model=AITaskProposal)
async def confirm_proposal(
    proposal_id: str,
    request: ProposalConfirmRequest | None,
    session: Annotated[UserSession, Depends(get_session_dep)],
    github_projects_service=Depends(get_github_service),  # noqa: B008
    connection_manager=Depends(get_connection_manager),  # noqa: B008
) -> AITaskProposal:
    """Confirm an AI task proposal and create the task."""
    proposal = await get_proposal(proposal_id)

    if not proposal:
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if str(proposal.session_id) != str(session.session_id):
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if proposal.is_expired:
        proposal.status = ProposalStatus.CANCELLED
        try:
            from src.services import chat_store

            db = get_db()
            await chat_store.update_proposal_status(db, proposal_id, ProposalStatus.CANCELLED.value)
        except Exception:
            logger.warning("Failed to update expired proposal status in SQLite", exc_info=True)
        raise ValidationError("Proposal has expired")

    if proposal.status != ProposalStatus.PENDING:
        raise ValidationError(f"Proposal already {proposal.status.value}")

    # Apply edits if provided
    if request:
        if request.edited_title:
            proposal.edited_title = request.edited_title
            proposal.status = ProposalStatus.EDITED
        if request.edited_description:
            proposal.edited_description = request.edited_description
            if proposal.status != ProposalStatus.EDITED:
                proposal.status = ProposalStatus.EDITED

    # Resolve repository info for issue creation
    owner, repo = await _resolve_repository(session)

    project_id = require_selected_project(session)

    # Validate description does not exceed GitHub API limit before attempting
    # issue creation.  This check lives outside the try/except below so that the
    # structured ValidationError (with body_length/max_length details) is never
    # caught by the broad ``except Exception`` handler and re-wrapped — which
    # would drop the ``details`` payload and return a misleading error message.
    body = proposal.final_description or ""

    # Embed file attachments in issue body
    from src.attachment_formatter import format_attachments_markdown

    body += format_attachments_markdown(proposal.file_urls)

    if len(body) > GITHUB_ISSUE_BODY_MAX_LENGTH:
        raise ValidationError(
            f"Issue body is {len(body)} characters, which exceeds the "
            f"GitHub API limit of {GITHUB_ISSUE_BODY_MAX_LENGTH} characters. "
            "Please shorten the description.",
            details={
                "body_length": len(body),
                "max_length": GITHUB_ISSUE_BODY_MAX_LENGTH,
            },
        )

    # Create the issue in GitHub
    try:
        # Step 1: Create a real GitHub Issue via REST API
        issue = await github_projects_service.create_issue(
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            title=proposal.final_title,
            body=body,
            labels=[],
        )

        issue_number = issue["number"]
        issue_node_id = issue["node_id"]
        issue_url = issue["html_url"]
        issue_database_id = issue["id"]  # Integer database ID for REST API fallback

        # Step 2: Add the issue to the project
        item_id = await github_projects_service.add_issue_to_project(
            access_token=session.access_token,
            project_id=project_id,
            issue_node_id=issue_node_id,
            issue_database_id=issue_database_id,
        )

        proposal.status = ProposalStatus.CONFIRMED
        try:
            from src.services import chat_store

            db = get_db()
            await chat_store.update_proposal_status(
                db,
                proposal_id,
                ProposalStatus.CONFIRMED.value,
                edited_title=proposal.edited_title,
                edited_description=proposal.edited_description,
            )
        except Exception:
            logger.warning("Failed to update proposal status in SQLite", exc_info=True)

        # Invalidate cache
        cache.delete(get_project_items_cache_key(project_id))

        # Broadcast WebSocket message to connected clients
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "task_created",
                "task_id": item_id,
                "title": proposal.final_title,
                "issue_number": issue_number,
                "issue_url": issue_url,
            },
        )

        # Add confirmation message
        confirm_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.SYSTEM,
            content=f"✅ Issue created: **{proposal.final_title}** ([#{issue_number}]({issue_url}))",
            action_type=ActionType.TASK_CREATE,
            action_data={
                "proposal_id": str(proposal.proposal_id),
                "task_id": item_id,
                "issue_number": issue_number,
                "issue_url": issue_url,
                "status": ProposalStatus.CONFIRMED.value,
            },
        )
        await add_message(session.session_id, confirm_message)
        _trigger_signal_delivery(session, confirm_message)

        logger.info(
            "Created issue #%d from proposal %s: %s",
            issue_number,
            proposal_id,
            proposal.final_title,
        )

        # Step 3: Set up workflow config and assign agent for Backlog status
        try:
            from src.config import get_settings

            settings = get_settings()

            config = await get_workflow_config(project_id)
            if not config:
                config = WorkflowConfiguration(
                    project_id=project_id,
                    repository_owner=owner,
                    repository_name=repo,
                    copilot_assignee=settings.default_assignee,
                )
                await set_workflow_config(
                    project_id,
                    config,
                )
            else:
                config.repository_owner = owner
                config.repository_name = repo
                if not config.copilot_assignee:
                    config.copilot_assignee = settings.default_assignee

            # Apply explicitly selected pipeline first, then project/user/default fallback
            from src.services.workflow_orchestrator.config import (
                PipelineResolutionResult,
                load_pipeline_as_agent_mappings,
                resolve_project_pipeline_mappings,
            )

            if proposal.selected_pipeline_id:
                selected_pipeline = await load_pipeline_as_agent_mappings(
                    project_id, proposal.selected_pipeline_id
                )
                if selected_pipeline is not None:
                    (
                        selected_mappings,
                        selected_pipeline_name,
                        selected_exec_modes,
                        selected_grp_mappings,
                    ) = selected_pipeline
                    pipeline_result = PipelineResolutionResult(
                        agent_mappings=selected_mappings,
                        source="pipeline",
                        pipeline_name=selected_pipeline_name,
                        pipeline_id=proposal.selected_pipeline_id,
                        stage_execution_modes=selected_exec_modes,
                        group_mappings=selected_grp_mappings,
                    )
                else:
                    logger.warning(
                        "Selected pipeline %s not found for proposal %s on project %s; falling back",
                        proposal.selected_pipeline_id,
                        proposal_id,
                        project_id,
                    )
                    pipeline_result = await resolve_project_pipeline_mappings(
                        project_id, session.github_user_id
                    )
            else:
                pipeline_result = await resolve_project_pipeline_mappings(
                    project_id, session.github_user_id
                )

            if pipeline_result.agent_mappings:
                logger.info(
                    "Applying %s agent pipeline mappings for project=%s (pipeline=%s)",
                    pipeline_result.source,
                    project_id,
                    pipeline_result.pipeline_name or "N/A",
                )
                config.agent_mappings = pipeline_result.agent_mappings
                await set_workflow_config(project_id, config)

            # Populate pipeline metadata on the proposal response
            proposal.pipeline_name = pipeline_result.pipeline_name
            proposal.pipeline_source = pipeline_result.source

            # Set issue status to Backlog on the project
            backlog_status = config.status_backlog
            await github_projects_service.update_item_status_by_name(
                access_token=session.access_token,
                project_id=project_id,
                item_id=item_id,
                status_name=backlog_status,
            )
            logger.info(
                "Set issue #%d status to '%s' on project",
                issue_number,
                backlog_status,
            )

            # Assign the first Backlog agent
            try:
                effective_user_settings = await get_effective_user_settings(
                    get_db(), session.github_user_id
                )
                user_chat_model = effective_user_settings.ai.model
                user_agent_model = effective_user_settings.ai.agent_model
            except Exception:
                logger.warning(
                    "Could not load effective user settings for session %s; user_chat_model left empty",
                    session.session_id,
                )
                user_chat_model = ""
                user_agent_model = ""

            ctx = WorkflowContext(
                session_id=str(session.session_id),
                project_id=project_id,
                access_token=session.access_token,
                repository_owner=owner,
                repository_name=repo,
                selected_pipeline_id=proposal.selected_pipeline_id,
                config=config,
                user_chat_model=user_chat_model,
                user_agent_model=user_agent_model,
            )
            ctx.issue_id = issue_node_id
            ctx.issue_number = issue_number
            ctx.project_item_id = item_id

            orchestrator = get_workflow_orchestrator()

            # Create all sub-issues upfront so the user can see the full pipeline.
            agent_sub_issues = await orchestrator.create_all_sub_issues(ctx)
            if agent_sub_issues:
                from src.services.workflow_orchestrator import (
                    PipelineState,
                    set_pipeline_state,
                )

                # Populate agents for the initial status so the polling loop
                # doesn't see an empty list and immediately consider the
                # pipeline "complete" (is_complete = 0 >= len([]) = True).
                initial_agents = get_agent_slugs(config, backlog_status)
                pipeline_state = PipelineState(
                    issue_number=issue_number,
                    project_id=project_id,
                    status=backlog_status,
                    agents=initial_agents,
                    agent_sub_issues=agent_sub_issues,
                    started_at=utcnow(),
                )
                set_pipeline_state(issue_number, pipeline_state)
                logger.info(
                    "Pre-created %d sub-issues for issue #%d",
                    len(agent_sub_issues),
                    issue_number,
                )

            await orchestrator.assign_agent_for_status(ctx, backlog_status, agent_index=0)

            # Send agent_assigned WebSocket notification
            backlog_slugs = get_agent_slugs(config, backlog_status)
            if backlog_slugs:
                await connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "agent_assigned",
                        "issue_number": issue_number,
                        "agent_name": backlog_slugs[0],
                        "status": backlog_status,
                    },
                )

            # Ensure Copilot polling is running so the pipeline advances
            # after agents complete their work (creates PRs).
            from src.services.copilot_polling import ensure_polling_started

            await ensure_polling_started(
                access_token=session.access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                caller="confirm_proposal",
            )

        except Exception as e:
            logger.warning(
                "Issue #%d created but agent assignment failed: %s",
                issue_number,
                e,
            )

        return proposal

    except ValidationError:
        raise
    except Exception as e:
        handle_service_error(e, "create issue from proposal", ValidationError)


@router.delete("/proposals/{proposal_id}")
async def cancel_proposal(
    proposal_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Cancel an AI task proposal."""
    proposal = await get_proposal(proposal_id)

    if not proposal:
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if str(proposal.session_id) != str(session.session_id):
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    proposal.status = ProposalStatus.CANCELLED
    try:
        from src.services import chat_store

        db = get_db()
        await chat_store.update_proposal_status(db, proposal_id, ProposalStatus.CANCELLED.value)
    except Exception:
        logger.warning("Failed to update proposal status in SQLite", exc_info=True)

    # Add cancellation message
    cancel_message = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.SYSTEM,
        content="Task creation cancelled.",
    )
    await add_message(session.session_id, cancel_message)

    return {"message": "Proposal cancelled"}


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),  # noqa: B008
    session: UserSession = Depends(get_session_dep),  # noqa: B008
) -> FileUploadResponse | JSONResponse:
    """Upload a file for attachment to a future GitHub Issue.

    Validates file size and type, then stores the file temporarily.
    The returned URL can be embedded in issue bodies.
    """
    if not file.filename:
        return JSONResponse(
            status_code=400,
            content={"filename": "", "error": "No file provided", "error_code": "no_file"},
        )

    # Validate file type
    ext = Path(file.filename).suffix.lower()
    if ext in BLOCKED_TYPES:
        return JSONResponse(
            status_code=415,
            content={
                "filename": file.filename,
                "error": f"File type {ext} is not supported",
                "error_code": "unsupported_type",
            },
        )
    if ext not in ALLOWED_TYPES:
        return JSONResponse(
            status_code=415,
            content={
                "filename": file.filename,
                "error": f"File type {ext} is not supported",
                "error_code": "unsupported_type",
            },
        )

    # Read file content and validate size
    content = await file.read()
    if len(content) == 0:
        return JSONResponse(
            status_code=400,
            content={
                "filename": file.filename,
                "error": "Empty file - cannot attach a file with no content",
                "error_code": "empty_file",
            },
        )
    if len(content) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "filename": file.filename,
                "error": "File exceeds the 10 MB size limit",
                "error_code": "file_too_large",
            },
        )

    # Store files in a temporary upload directory and serve via a local URL.
    # This is intentional for self-hosted single-instance deployments where
    # simplicity outweighs cloud storage benefits.  Files reside in the OS
    # temp directory and are cleaned up automatically on system restart.
    # For multi-instance or cloud deployments, migrate to object storage
    # (e.g. S3 / GCS) in a dedicated specification.
    upload_id = str(uuid4())[:8]
    # Sanitise the original filename to prevent path-traversal attacks:
    # strip null bytes first (could confuse Path parsing on some platforms),
    # then strip directory components so e.g. "../../etc/passwd" becomes "passwd".
    cleaned = file.filename.replace("\x00", "")
    basename = Path(cleaned).name
    if not basename:
        basename = "upload"
    safe_filename = f"{upload_id}-{basename}"

    # Store in a temporary directory
    upload_dir = Path(tempfile.gettempdir()) / "chat-uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_filename

    # Verify resolved path stays inside upload_dir (defense-in-depth)
    if not file_path.resolve().is_relative_to(upload_dir.resolve()):
        return JSONResponse(
            status_code=400,
            content={
                "filename": file.filename,
                "error": "Invalid filename",
                "error_code": "invalid_filename",
            },
        )

    file_path.write_bytes(content)

    # Generate a file URL — in production this would be a GitHub CDN URL
    file_url = f"/api/v1/chat/uploads/{safe_filename}"

    return FileUploadResponse(
        filename=file.filename,
        file_url=file_url,
        file_size=len(content),
        content_type=file.content_type or "application/octet-stream",
    )
