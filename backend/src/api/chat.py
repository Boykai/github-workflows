"""Chat API endpoints."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.api.auth import get_session_dep
from src.constants import DEFAULT_STATUS_COLUMNS, GITHUB_ISSUE_BODY_MAX_LENGTH
from src.dependencies import get_connection_manager, get_github_service
from src.exceptions import NotFoundError, ValidationError
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
from src.services.cache import (
    cache,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)
from src.services.workflow_orchestrator import (
    WorkflowContext,
    get_agent_slugs,
    get_workflow_config,
    get_workflow_orchestrator,
    set_workflow_config,
)
from src.utils import resolve_repository, utcnow

logger = logging.getLogger(__name__)
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


async def _resolve_repository(session: UserSession) -> tuple[str, str]:
    """Resolve repository owner and name for issue creation."""
    if not session.selected_project_id:
        raise ValidationError("No project selected")
    return await resolve_repository(session.access_token, session.selected_project_id)


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
    if not session.selected_project_id:
        raise ValidationError("Please select a project first")

    selected_project_id = session.selected_project_id

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

    # ──────────────────────────────────────────────────────────────────
    # PRIORITY 0: #agent command — custom agent creation
    # ──────────────────────────────────────────────────────────────────
    from src.services.agent_creator import (
        get_active_session,
        handle_agent_command,
    )
    from src.services.database import get_db

    session_key = str(session.session_id)
    is_agent_command = chat_request.content.strip().lower().startswith(
        "/agent"
    ) or chat_request.content.strip().lower().startswith("#agent")
    active_agent_session = get_active_session(session_key)

    if is_agent_command or active_agent_session:
        try:
            db = get_db()
            owner, repo = await _resolve_repository(session)
            agent_response_text = await handle_agent_command(
                message=chat_request.content,
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

    # ──────────────────────────────────────────────────────────────────
    # PRIORITY 1: Check if this is a feature request (T013, T014)
    # ──────────────────────────────────────────────────────────────────
    ai_service = get_ai_agent_service()

    try:
        is_feature_request = await ai_service.detect_feature_request_intent(
            chat_request.content, github_token=session.access_token
        )
    except Exception as e:
        logger.warning("Feature request detection failed: %s", e)
        is_feature_request = False

    if is_feature_request:
        # Generate issue recommendation (T015, T016)
        try:
            # Fetch repo metadata for dynamic prompt injection
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
                user_input=chat_request.content,
                project_name=project_name,
                session_id=str(session.session_id),
                github_token=session.access_token,
                metadata_context=metadata_context,
            )

            recommendation.selected_pipeline_id = chat_request.pipeline_id or None

            # Store recommendation (T016)
            _recommendations[str(recommendation.recommendation_id)] = recommendation

            # Format requirements for display - show ALL of them
            requirements_preview = "\n".join(
                f"- {req}" for req in recommendation.functional_requirements
            )

            # Format technical notes preview
            technical_notes_preview = ""
            if recommendation.technical_notes:
                technical_notes_preview = f"\n\n**Technical Notes:**\n{recommendation.technical_notes[:300]}{'...' if len(recommendation.technical_notes) > 300 else ''}"

            # Create assistant response with issue_create action (T015)
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
                    "ai_enhance": chat_request.ai_enhance,
                    "file_urls": chat_request.file_urls,
                    "pipeline_id": chat_request.pipeline_id,
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
            # T017: Error handling for AI generation failures
            logger.error("Failed to generate issue recommendation: %s", e, exc_info=True)
            error_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content="I couldn't generate an issue recommendation from your feature request. Please try again with more detail.",
            )
            add_message(session.session_id, error_message)
            return error_message

    # ──────────────────────────────────────────────────────────────────
    # PRIORITY 2: Check if this is a status change request
    # ──────────────────────────────────────────────────────────────────
    status_change = await ai_service.parse_status_change_request(
        user_input=chat_request.content,
        available_tasks=[t.title for t in current_tasks],
        available_statuses=(project_columns or DEFAULT_STATUS_COLUMNS),
        github_token=session.access_token,
    )

    if status_change:
        # This is a status change request - identify target task and status
        target_task = ai_service.identify_target_task(
            task_reference=status_change.task_reference,
            available_tasks=current_tasks,
        )

        if target_task:
            target_status = status_change.target_status

            # Find the status column info
            status_option_id = ""
            status_field_id = ""
            if cached_projects:
                for p in cached_projects:
                    if p.project_id == selected_project_id:
                        for col in p.status_columns:
                            if col.name.lower() == target_status.lower():
                                status_option_id = col.option_id
                                status_field_id = col.field_id
                                target_status = col.name  # Use exact name
                                break
                        break

            # Create a status change proposal
            proposal = AITaskProposal(
                session_id=session.session_id,
                original_input=chat_request.content,
                proposed_title=target_task.title,
                proposed_description=f"Move from '{target_task.status}' to '{target_status}'",
            )
            _proposals[str(proposal.proposal_id)] = proposal

            # Create assistant response with status change action
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
        else:
            # Could not identify the task
            error_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"I couldn't find a task matching '{status_change.task_reference}'. Please try again with a more specific task name.",
            )
            add_message(session.session_id, error_message)

            return error_message

    # ──────────────────────────────────────────────────────────────────
    # PRIORITY 3: Generate task from description
    # Two branches: metadata-only (ai_enhance=False) vs full AI (ai_enhance=True)
    # ──────────────────────────────────────────────────────────────────

    # Metadata-only path: user's raw input as description, AI-generated title only
    if not chat_request.ai_enhance:
        try:
            title = await ai_service.generate_title_from_description(
                user_input=chat_request.content,
                project_name=project_name,
                github_token=session.access_token,
            )

            proposal = AITaskProposal(
                session_id=session.session_id,
                original_input=chat_request.content,
                proposed_title=title,
                proposed_description=chat_request.content,
            )
            _proposals[str(proposal.proposal_id)] = proposal

            description_preview = chat_request.content[:200]
            if len(chat_request.content) > 200:
                description_preview += "..."

            assistant_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"I've created a task proposal:\n\n**{title}**\n\n{description_preview}\n\nClick confirm to create this task.",
                action_type=ActionType.TASK_CREATE,
                action_data={
                    "proposal_id": str(proposal.proposal_id),
                    "proposed_title": title,
                    "proposed_description": chat_request.content,
                    "status": ProposalStatus.PENDING.value,
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
            user_input=chat_request.content,
            project_name=project_name,
            github_token=session.access_token,
        )

        # Create proposal
        proposal = AITaskProposal(
            session_id=session.session_id,
            original_input=chat_request.content,
            proposed_title=generated.title,
            proposed_description=generated.description,
        )
        _proposals[str(proposal.proposal_id)] = proposal

        # Create assistant response with proposal
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
        add_message(session.session_id, assistant_message)
        _trigger_signal_delivery(session, assistant_message, project_name)

        return assistant_message

    except Exception as e:
        logger.error("Failed to generate task: %s", e, exc_info=True)

        # Return error message
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content="I couldn't generate a task from your description. Please try again with more detail.",
        )
        add_message(session.session_id, error_message)

        return error_message


@router.post("/proposals/{proposal_id}/confirm", response_model=AITaskProposal)
async def confirm_proposal(
    proposal_id: str,
    request: ProposalConfirmRequest | None,
    session: Annotated[UserSession, Depends(get_session_dep)],
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

    # Narrowed: _resolve_repository validates selected_project_id is not None
    project_id = session.selected_project_id
    if project_id is None:
        raise ValidationError("No project selected")

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

            # Apply user-specific agent pipeline mappings if available
            from src.services.workflow_orchestrator.config import load_user_agent_mappings

            user_mappings = await load_user_agent_mappings(session.github_user_id, project_id)
            if user_mappings:
                logger.info(
                    "Applying user-specific agent pipeline mappings for user=%s project=%s",
                    session.github_user_id,
                    project_id,
                )
                config.agent_mappings = user_mappings
                await set_workflow_config(project_id, config)

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
            ctx = WorkflowContext(
                session_id=str(session.session_id),
                project_id=project_id,
                access_token=session.access_token,
                repository_owner=owner,
                repository_name=repo,
                config=config,
            )
            ctx.issue_id = issue_node_id
            ctx.issue_number = issue_number
            ctx.project_item_id = item_id

            orchestrator = get_workflow_orchestrator()

            # Create all sub-issues upfront so the user can see the full pipeline
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
