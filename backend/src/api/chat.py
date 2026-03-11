"""Chat API endpoints."""

from __future__ import annotations

import asyncio
import re
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
    with_blocking_label,
)
from src.dependencies import get_connection_manager, get_github_service, require_selected_project
from src.exceptions import NotFoundError, ValidationError
from src.logging_utils import get_logger
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
ALLOWED_DOC_TYPES = {".pdf", ".txt", ".md", ".csv", ".json", ".yaml", ".yml"}
ALLOWED_ARCHIVE_TYPES = {".zip"}
BLOCKED_TYPES = {".exe", ".sh", ".bat", ".cmd", ".js", ".py", ".rb"}
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_DOC_TYPES | ALLOWED_ARCHIVE_TYPES


class FileUploadResponse(BaseModel):
    """Response from file upload endpoint."""

    filename: str
    file_url: str
    file_size: int
    content_type: str


# TODO(018-codebase-audit-refactor): Migrate these in-memory stores to SQLite
# using the chat_messages, chat_proposals, and chat_recommendations tables
# created by migration 012_chat_persistence.sql. The migration file is ready
# and the tables will be created on next application startup. This refactoring
# was deferred because it requires updating ~15 code paths in this 713-line file
# with careful transaction management and error handling.
# In-memory storage for chat messages and proposals (MVP — lost on restart)
_messages: dict[str, list[ChatMessage]] = {}
_proposals: dict[str, AITaskProposal] = {}
# In-memory storage for issue recommendations (T007 — lost on restart)
_recommendations: dict[str, IssueRecommendation] = {}
# Module-level compiled regex for #block detection (no \s* prefix — avoids ReDoS)
_BLOCK_PATTERN = re.compile(r"#block\b", re.IGNORECASE)


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
    add_message(session.session_id, agent_msg)
    _trigger_signal_delivery(session, agent_msg, project_name)
    return agent_msg


async def _resolve_blocking_status(
    content: str,
    selected_project_id: str,
) -> tuple[bool, str]:
    """Priority 0.5: Detect #block tag and resolve blocking status.

    Returns (is_blocking, cleaned_content) where cleaned_content has the
    #block tag stripped.
    """
    is_blocking = bool(_BLOCK_PATTERN.search(content))
    if is_blocking:
        cleaned = " ".join(_BLOCK_PATTERN.sub("", content).split())
        logger.info("Detected #block in message — is_blocking=True, stripped content")
        return True, cleaned

    # Fall through to project-level override, then pipeline default
    try:
        from src.services.pipelines.service import PipelineService

        _pipeline_svc = PipelineService(get_db())
        _assignment = await _pipeline_svc.get_assignment(selected_project_id)
        if _assignment.blocking_override is not None:
            logger.debug(
                "is_blocking resolved from project override: %s", _assignment.blocking_override
            )
            return _assignment.blocking_override, content
        if _assignment.pipeline_id:
            _pipeline_cfg = await _pipeline_svc.get_pipeline(
                selected_project_id, _assignment.pipeline_id
            )
            if _pipeline_cfg and _pipeline_cfg.blocking:
                logger.debug("is_blocking resolved from pipeline default: True")
                return True, content
    except Exception as e:
        logger.debug("Pipeline blocking resolution failed for chat request: %s", e)

    return False, content


async def _handle_feature_request(
    session: UserSession,
    content: str,
    ai_service: AIAgentService,
    project_name: str,
    is_blocking: bool,
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
            from src.services.metadata_service import MetadataService

            metadata_svc = MetadataService()
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
        recommendation.is_blocking = is_blocking

        _recommendations[str(recommendation.recommendation_id)] = recommendation

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
                "is_blocking": is_blocking,
                "pipeline_id": pipeline_id,
            },
        )
        add_message(session.session_id, assistant_message)
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
        add_message(session.session_id, error_message)
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
        add_message(session.session_id, error_message)
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
    _proposals[str(proposal.proposal_id)] = proposal

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
    add_message(session.session_id, assistant_message)
    _trigger_signal_delivery(session, assistant_message, project_name)
    return assistant_message


async def _handle_task_generation(
    session: UserSession,
    content: str,
    ai_service: AIAgentService,
    project_name: str,
    is_blocking: bool,
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
                is_blocking=is_blocking,
                selected_pipeline_id=pipeline_id or None,
            )
            _proposals[str(proposal.proposal_id)] = proposal

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
                    "is_blocking": is_blocking,
                },
            )
            add_message(session.session_id, assistant_message)
            _trigger_signal_delivery(session, assistant_message, project_name)
            return assistant_message

        except Exception as e:
            logger.error("Failed to generate metadata (ai_enhance=off): %s", e, exc_info=True)
            error_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content="I couldn't generate metadata for your request. Your input was preserved — please try again.",
            )
            add_message(session.session_id, error_message)
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
            is_blocking=is_blocking,
            selected_pipeline_id=pipeline_id or None,
        )
        _proposals[str(proposal.proposal_id)] = proposal

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
                "is_blocking": is_blocking,
            },
        )
        add_message(session.session_id, assistant_message)
        _trigger_signal_delivery(session, assistant_message, project_name)
        return assistant_message

    except Exception as e:
        logger.error("Failed to generate task: %s", e, exc_info=True)
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content="I couldn't generate a task from your description. Please try again with more detail.",
        )
        add_message(session.session_id, error_message)
        return error_message


async def _resolve_repository(session: UserSession) -> tuple[str, str]:
    """Resolve repository owner and name for issue creation."""
    project_id = require_selected_project(session)
    return await resolve_repository(session.access_token, project_id)


def get_session_messages(session_id: UUID) -> list[ChatMessage]:
    """Get messages for a session."""
    return _messages.get(str(session_id), [])


def add_message(session_id: UUID, message: ChatMessage) -> None:
    """Add a message to a session."""
    key = str(session_id)
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
        asyncio.create_task(_deliver())
    except RuntimeError:
        pass  # No running event loop — skip silently


@router.get("/messages", response_model=ChatMessagesResponse)
async def get_messages(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChatMessagesResponse:
    """Get chat messages for current session."""
    messages = get_session_messages(session.session_id)
    return ChatMessagesResponse(messages=messages)


@router.delete("/messages")
async def clear_messages(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict[str, str]:
    """Clear all chat messages for current session."""
    key = str(session.session_id)
    if key in _messages:
        _messages[key] = []
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

    # ── Priority 0.5: #block detection ───────────────────────────────
    is_blocking, content = await _resolve_blocking_status(
        chat_request.content,
        selected_project_id,
    )

    # ── Priority 1: Feature request → issue recommendation ───────────
    feature_msg = await _handle_feature_request(
        session,
        content,
        ai_service,
        project_name,
        is_blocking,
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
        is_blocking,
        chat_request.ai_enhance,
        chat_request.pipeline_id,
    )


@router.post("/proposals/{proposal_id}/confirm", response_model=AITaskProposal)
@limiter.limit("10/minute")
async def confirm_proposal(
    request: Request,
    proposal_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    proposal_edits: ProposalConfirmRequest | None = None,
    github_projects_service=Depends(get_github_service),  # noqa: B008
    connection_manager=Depends(get_connection_manager),  # noqa: B008
) -> AITaskProposal:
    """Confirm an AI task proposal and create the task."""
    proposal = _proposals.get(proposal_id)

    if not proposal:
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if str(proposal.session_id) != str(session.session_id):
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if proposal.is_expired:
        proposal.status = ProposalStatus.CANCELLED
        raise ValidationError("Proposal has expired")

    if proposal.status != ProposalStatus.PENDING:
        raise ValidationError(f"Proposal already {proposal.status.value}")

    # Apply edits if provided
    if proposal_edits:
        if proposal_edits.edited_title:
            proposal.edited_title = proposal_edits.edited_title
            proposal.status = ProposalStatus.EDITED
        if proposal_edits.edited_description:
            proposal.edited_description = proposal_edits.edited_description
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
            labels=with_blocking_label([], proposal.is_blocking),
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
        add_message(session.session_id, confirm_message)
        _trigger_signal_delivery(session, confirm_message)

        logger.info(
            "Created issue #%d from proposal %s: %s",
            issue_number,
            proposal_id,
            proposal.final_title,
        )

        # Step 3: Set up workflow config and assign agent for Backlog status
        try:
            # Resolve is_blocking from the proposal
            proposal_is_blocking = proposal.is_blocking

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
                    selected_mappings, selected_pipeline_name, selected_exec_modes = (
                        selected_pipeline
                    )
                    pipeline_result = PipelineResolutionResult(
                        agent_mappings=selected_mappings,
                        source="pipeline",
                        pipeline_name=selected_pipeline_name,
                        pipeline_id=proposal.selected_pipeline_id,
                        stage_execution_modes=selected_exec_modes,
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
            # This must happen before the blocking queue check so that sub-issues
            # are always created even when the issue enters the queue as pending.
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

            # Blocking queue: enqueue issue and check if it should activate.
            # Only gates agent assignment — sub-issues are already created above.
            issue_activated = True
            try:
                from src.services import blocking_queue as bq_service

                repo_key = f"{owner}/{repo}"
                _bq_entry, issue_activated = await bq_service.enqueue_issue(
                    repo_key, issue_number, project_id, proposal_is_blocking
                )
                if not issue_activated:
                    logger.info(
                        "Issue #%d is pending in blocking queue — skipping agent assignment",
                        issue_number,
                    )
                    return proposal
            except Exception as e:
                logger.debug("Blocking queue enqueue skipped in confirm_proposal: %s", e)

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
        logger.error("Failed to create issue from proposal: %s", e)
        raise ValidationError("Failed to create issue") from e


@router.delete("/proposals/{proposal_id}")
async def cancel_proposal(
    proposal_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Cancel an AI task proposal."""
    proposal = _proposals.get(proposal_id)

    if not proposal:
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if str(proposal.session_id) != str(session.session_id):
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    proposal.status = ProposalStatus.CANCELLED

    # Add cancellation message
    cancel_message = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.SYSTEM,
        content="Task creation cancelled.",
    )
    add_message(session.session_id, cancel_message)

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
    if len(content) > MAX_FILE_SIZE_BYTES:
        return JSONResponse(
            status_code=413,
            content={
                "filename": file.filename,
                "error": "File exceeds the 10 MB size limit",
                "error_code": "file_too_large",
            },
        )

    # For now, store files in a temporary upload directory and serve via a local URL.
    # In production, these would be uploaded to GitHub's CDN or a cloud storage service.
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
