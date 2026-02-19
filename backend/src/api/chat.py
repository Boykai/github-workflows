"""Chat API endpoints."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.constants import DEFAULT_STATUS_COLUMNS
from src.exceptions import NotFoundError, ValidationError
from src.models.chat import (
    ActionType,
    AITaskProposal,
    ChatMessage,
    ChatMessageRequest,
    ChatMessagesResponse,
    IssueRecommendation,
    ProposalConfirmRequest,
    ProposalStatus,
    RecommendationStatus,
    SenderType,
    WorkflowConfiguration,
)
from src.models.user import UserSession
from src.services.ai_agent import get_ai_agent_service
from src.services.cache import (
    cache,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.services.workflow_orchestrator import (
    WorkflowContext,
    get_agent_slugs,
    get_workflow_config,
    get_workflow_orchestrator,
    set_workflow_config,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for chat messages and proposals (MVP)
_messages: dict[str, list[ChatMessage]] = {}
_proposals: dict[str, AITaskProposal] = {}
# In-memory storage for issue recommendations (T007)
_recommendations: dict[str, IssueRecommendation] = {}


async def _resolve_repository(session: UserSession) -> tuple[str, str]:
    """Resolve repository owner and name for issue creation."""
    if not session.selected_project_id:
        raise ValidationError("No project selected")

    project_id = session.selected_project_id

    # Try project items first
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        project_id,
    )
    if repo_info:
        return repo_info

    # Try workflow config
    config = get_workflow_config(project_id)
    if config and config.repository_owner and config.repository_name:
        return config.repository_owner, config.repository_name

    # Fall back to default repository from settings
    from src.config import get_settings

    settings = get_settings()
    if settings.default_repo_owner and settings.default_repo_name:
        return settings.default_repo_owner, settings.default_repo_name

    raise ValidationError(
        "No repository found for this project. Configure DEFAULT_REPOSITORY in .env "
        "or ensure the project has at least one linked issue."
    )


def get_session_messages(session_id: UUID) -> list[ChatMessage]:
    """Get messages for a session."""
    return _messages.get(str(session_id), [])


def add_message(session_id: UUID, message: ChatMessage) -> None:
    """Add a message to a session."""
    key = str(session_id)
    if key not in _messages:
        _messages[key] = []
    _messages[key].append(message)


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
async def send_message(
    request: ChatMessageRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> ChatMessage:
    """Send a chat message and get AI response."""
    # Require project selection
    if not session.selected_project_id:
        raise ValidationError("Please select a project first")

    selected_project_id = session.selected_project_id

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
        content=request.content,
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
    # PRIORITY 1: Check if this is a feature request (T013, T014)
    # ──────────────────────────────────────────────────────────────────
    ai_service = get_ai_agent_service()

    try:
        is_feature_request = await ai_service.detect_feature_request_intent(
            request.content, github_token=session.access_token
        )
    except Exception as e:
        logger.warning("Feature request detection failed: %s", e)
        is_feature_request = False

    if is_feature_request:
        # Generate issue recommendation (T015, T016)
        try:
            recommendation = await ai_service.generate_issue_recommendation(
                user_input=request.content,
                project_name=project_name,
                session_id=str(session.session_id),
                github_token=session.access_token,
            )

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
                },
            )
            add_message(session.session_id, assistant_message)

            logger.info(
                "Generated issue recommendation %s: %s",
                recommendation.recommendation_id,
                recommendation.title,
            )

            return assistant_message

        except Exception as e:
            # T017: Error handling for AI generation failures
            logger.error("Failed to generate issue recommendation: %s", e)
            error_message = ChatMessage(
                session_id=session.session_id,
                sender_type=SenderType.ASSISTANT,
                content=f"I couldn't generate an issue recommendation from your feature request. Please try again with more detail.\n\nError: {str(e)}",
            )
            add_message(session.session_id, error_message)
            return error_message

    # ──────────────────────────────────────────────────────────────────
    # PRIORITY 2: Check if this is a status change request
    # ──────────────────────────────────────────────────────────────────
    status_change = await ai_service.parse_status_change_request(
        user_input=request.content,
        available_tasks=[t.title for t in current_tasks],
        available_statuses=(project_columns if project_columns else DEFAULT_STATUS_COLUMNS),
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
                original_input=request.content,
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

    # Not a status change - generate task from description
    try:
        generated = await ai_service.generate_task_from_description(
            user_input=request.content,
            project_name=project_name,
            github_token=session.access_token,
        )

        # Create proposal
        proposal = AITaskProposal(
            session_id=session.session_id,
            original_input=request.content,
            proposed_title=generated.title,
            proposed_description=generated.description,
        )
        _proposals[str(proposal.proposal_id)] = proposal

        # Create assistant response with proposal
        assistant_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=f"I've created a task proposal:\n\n**{generated.title}**\n\n{generated.description[:200]}...\n\nClick confirm to create this task.",
            action_type=ActionType.TASK_CREATE,
            action_data={
                "proposal_id": str(proposal.proposal_id),
                "proposed_title": generated.title,
                "proposed_description": generated.description,
                "status": ProposalStatus.PENDING.value,
            },
        )
        add_message(session.session_id, assistant_message)

        return assistant_message

    except Exception as e:
        logger.error("Failed to generate task: %s", e)

        # Return error message
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content=f"I couldn't generate a task from your description. Please try again with more detail.\n\nError: {str(e)}",
        )
        add_message(session.session_id, error_message)

        return error_message


@router.post("/proposals/{proposal_id}/confirm", response_model=AITaskProposal)
async def confirm_proposal(
    proposal_id: str,
    request: ProposalConfirmRequest | None,
    session: Annotated[UserSession, Depends(get_session_dep)],
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
    assert project_id is not None

    # Create the issue in GitHub
    try:
        # Step 1: Create a real GitHub Issue via REST API
        issue = await github_projects_service.create_issue(
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            title=proposal.final_title,
            body=proposal.final_description or "",
        )

        issue_number = issue["number"]
        issue_node_id = issue["node_id"]
        issue_url = issue["html_url"]

        # Step 2: Add the issue to the project
        item_id = await github_projects_service.add_issue_to_project(
            access_token=session.access_token,
            project_id=project_id,
            issue_node_id=issue_node_id,
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

            config = get_workflow_config(project_id)
            if not config:
                config = WorkflowConfiguration(
                    project_id=project_id,
                    repository_owner=owner,
                    repository_name=repo,
                    copilot_assignee=settings.default_assignee,
                )
                set_workflow_config(project_id, config)
            else:
                config.repository_owner = owner
                config.repository_name = repo
                if not config.copilot_assignee:
                    config.copilot_assignee = settings.default_assignee

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

                pipeline_state = PipelineState(
                    issue_number=issue_number,
                    project_id=project_id,
                    status=backlog_status,
                    agents=[],
                    agent_sub_issues=agent_sub_issues,
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

        except Exception as e:
            logger.warning(
                "Issue #%d created but agent assignment failed: %s",
                issue_number,
                e,
            )

        return proposal

    except Exception as e:
        logger.error("Failed to create issue from proposal: %s", e)
        raise ValidationError(f"Failed to create issue: {e}") from e


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
