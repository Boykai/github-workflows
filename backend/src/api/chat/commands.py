"""Command dispatch helpers for chat messages.

These functions implement the priority-ordered command handling chain called
by ``send_message`` in ``messaging.py``.  Each handler returns a
:class:`ChatMessage` when it handles the input, or ``None`` to pass through
to the next priority level.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.api.chat._state import (
    _proposals,
    _recommendations,
    _trigger_signal_delivery,
    add_message,
)
from src.constants import DEFAULT_STATUS_COLUMNS
from src.dependencies import require_selected_project
from src.logging_utils import get_logger
from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.recommendation import (
    AITaskProposal,
    ProposalStatus,
    RecommendationStatus,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.utils import resolve_repository

if TYPE_CHECKING:
    from src.services.ai_agent import AIAgentService

logger = get_logger(__name__)


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
        owner, repo = await resolve_repository(session.access_token, selected_project_id)
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
            project_id = require_selected_project(session)
            owner, repo = await resolve_repository(session.access_token, project_id)
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
        recommendation.file_urls = file_urls or []

        _recommendations[str(recommendation.recommendation_id)] = recommendation

        # Phase A write-through: persist recommendation to SQLite
        try:
            import json as _json

            from src.services.chat_store import save_recommendation as _save_rec

            await _save_rec(
                get_db(),
                session_id=str(session.session_id),
                recommendation_id=str(recommendation.recommendation_id),
                data=_json.dumps(recommendation.model_dump(mode="json")),
                file_urls=recommendation.file_urls or None,
            )
        except Exception as e:
            logger.debug("Recommendation persistence failed (non-fatal): %s", e)

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

    # Phase A write-through: persist status-change proposal to SQLite
    try:
        from src.services.chat_store import save_proposal as _save_prop

        await _save_prop(
            get_db(),
            session_id=str(session.session_id),
            proposal_id=str(proposal.proposal_id),
            original_input=proposal.original_input,
            proposed_title=proposal.proposed_title,
            proposed_description=proposal.proposed_description,
        )
    except Exception as e:
        logger.debug("Proposal persistence failed (non-fatal): %s", e)

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
            _proposals[str(proposal.proposal_id)] = proposal

            # Phase A write-through: persist metadata-only proposal to SQLite
            try:
                from src.services.chat_store import save_proposal as _save_prop

                await _save_prop(
                    get_db(),
                    session_id=str(session.session_id),
                    proposal_id=str(proposal.proposal_id),
                    original_input=proposal.original_input,
                    proposed_title=proposal.proposed_title,
                    proposed_description=proposal.proposed_description,
                )
            except Exception as e:
                logger.debug("Proposal persistence failed (non-fatal): %s", e)

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
            selected_pipeline_id=pipeline_id or None,
        )
        _proposals[str(proposal.proposal_id)] = proposal

        # Phase A write-through: persist AI-generated proposal to SQLite
        try:
            from src.services.chat_store import save_proposal as _save_prop

            await _save_prop(
                get_db(),
                session_id=str(session.session_id),
                proposal_id=str(proposal.proposal_id),
                original_input=proposal.original_input,
                proposed_title=proposal.proposed_title,
                proposed_description=proposal.proposed_description,
            )
        except Exception as e:
            logger.debug("Proposal persistence failed (non-fatal): %s", e)

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
        error_message = ChatMessage(
            session_id=session.session_id,
            sender_type=SenderType.ASSISTANT,
            content="I couldn't generate a task from your description. Please try again with more detail.",
        )
        add_message(session.session_id, error_message)
        return error_message
