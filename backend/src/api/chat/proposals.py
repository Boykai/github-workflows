"""Chat proposal endpoints — confirm and cancel AI task proposals."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.api.chat._state import _proposals, _trigger_signal_delivery, add_message
from src.constants import GITHUB_ISSUE_BODY_MAX_LENGTH
from src.dependencies import get_connection_manager, get_github_service, require_selected_project
from src.exceptions import NotFoundError, ValidationError
from src.logging_utils import get_logger
from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.common import MessageResponse
from src.models.recommendation import AITaskProposal, ProposalConfirmRequest, ProposalStatus
from src.models.user import UserSession
from src.models.workflow import WorkflowConfiguration
from src.services.cache import cache, get_project_items_cache_key
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


async def _lookup_proposal(proposal_id: str, session_id: str) -> AITaskProposal | None:
    """Look up a proposal by ID, falling back to database if not in memory."""
    proposal = _proposals.get(proposal_id)
    if proposal is not None:
        return proposal

    # Phase B: DB fallback when proposal is not in memory (e.g. after restart)
    try:
        from src.services.chat_store import get_proposals as _get_proposals

        rows = await _get_proposals(get_db(), session_id)
        for row in rows:
            if row["proposal_id"] == proposal_id:
                proposal = AITaskProposal(
                    proposal_id=row["proposal_id"],
                    session_id=row["session_id"],
                    original_input=row["original_input"],
                    proposed_title=row["proposed_title"],
                    proposed_description=row["proposed_description"],
                    status=row["status"],
                    edited_title=row.get("edited_title"),
                    edited_description=row.get("edited_description"),
                    created_at=row["created_at"],
                    expires_at=row["expires_at"],
                    file_urls=row.get("file_urls", []),
                )
                _proposals[proposal_id] = proposal
                return proposal
    except Exception as exc:
        logger.debug("DB proposal lookup failed (non-fatal): %s", exc)

    return None


@router.post("/proposals/{proposal_id}/confirm", response_model=AITaskProposal)
async def confirm_proposal(
    proposal_id: str,
    request: ProposalConfirmRequest | None,
    session: Annotated[UserSession, Depends(get_session_dep)],
    github_projects_service=Depends(get_github_service),  # noqa: B008
    connection_manager=Depends(get_connection_manager),  # noqa: B008
) -> AITaskProposal:
    """Confirm an AI task proposal and create the task."""
    proposal = await _lookup_proposal(proposal_id, str(session.session_id))

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
    project_id = require_selected_project(session)
    owner, repo = await resolve_repository(session.access_token, project_id)

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

        # Phase A write-through: persist confirmed status to SQLite
        try:
            from src.services.chat_store import update_proposal_status as _update_status

            await _update_status(
                get_db(),
                proposal_id=str(proposal.proposal_id),
                status=proposal.status.value,
                edited_title=proposal.edited_title,
                edited_description=proposal.edited_description,
            )
        except Exception as e:
            logger.debug("Proposal status persistence failed (non-fatal): %s", e)

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


@router.delete("/proposals/{proposal_id}", response_model=MessageResponse)
async def cancel_proposal(
    proposal_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Cancel an AI task proposal."""
    proposal = await _lookup_proposal(proposal_id, str(session.session_id))

    if not proposal:
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    if str(proposal.session_id) != str(session.session_id):
        raise NotFoundError(f"Proposal not found: {proposal_id}")

    proposal.status = ProposalStatus.CANCELLED

    # Phase A write-through: persist cancelled status to SQLite
    try:
        from src.services.chat_store import update_proposal_status as _update_status

        await _update_status(
            get_db(),
            proposal_id=str(proposal.proposal_id),
            status=proposal.status.value,
        )
    except Exception as e:
        logger.debug("Proposal status persistence failed (non-fatal): %s", e)

    # Add cancellation message
    cancel_message = ChatMessage(
        session_id=session.session_id,
        sender_type=SenderType.SYSTEM,
        content="Task creation cancelled.",
    )
    add_message(session.session_id, cancel_message)

    return {"message": "Proposal cancelled"}
