"""Signal conversational AI — processes inbound messages through the AI pipeline.

Mirrors the web chat UX: feature-request detection, status-change parsing,
task generation, and proposal CONFIRM/REJECT — all via Signal text messages.

Privacy & security:
- GitHub tokens are retrieved from the encrypted session store, never exposed
  to Signal or logged.
- Phone numbers come from the WebSocket envelope (trusted sidecar), and are
  only used for the immediate reply.
- Outbound messages create signal_messages audit rows for tracking.

Called as a fire-and-forget task from signal_bridge._process_inbound_ws_message.
"""

from __future__ import annotations

import logging
from uuid import NAMESPACE_URL, UUID, uuid5

from src.constants import DEFAULT_STATUS_COLUMNS
from src.models.chat import ActionType, ChatMessage, SenderType
from src.models.signal import (
    SignalConnection,
    SignalDeliveryStatus,
    SignalMessageDirection,
)

logger = logging.getLogger(__name__)

# One pending proposal per user — new proposals overwrite old ones.
_signal_pending: dict[str, dict] = {}

_CONFIRM_WORDS = frozenset({"confirm", "yes", "approve", "ok", "y"})
_REJECT_WORDS = frozenset({"reject", "no", "cancel", "n"})


def _signal_session_id(github_user_id: str):
    """Deterministic UUID5 session id for a Signal user."""
    return uuid5(NAMESPACE_URL, f"signal:{github_user_id}")


# ── Token helper ─────────────────────────────────────────────────────────


async def _get_user_access_token(github_user_id: str) -> str | None:
    """Retrieve the GitHub access token from the user's most recent session.

    Tokens are stored encrypted at rest in the session store and are only
    decrypted in-process for API calls.  Returns None if no session exists.
    """
    from src.services.database import get_db
    from src.services.session_store import get_sessions_by_user

    db = get_db()
    sessions = await get_sessions_by_user(db, github_user_id)
    if not sessions:
        return None
    # Most recent session first
    sessions.sort(key=lambda s: s.updated_at, reverse=True)
    return sessions[0].access_token


# ── Reply helpers ────────────────────────────────────────────────────────


async def _reply(source_phone: str, text: str) -> None:
    """Quick Signal reply — no audit row (for errors / info)."""
    from src.services.signal_bridge import send_message

    try:
        await send_message(source_phone, text)
    except Exception as e:
        logger.warning("Signal reply failed: %s", e)


async def _reply_with_audit(
    conn: SignalConnection,
    source_phone: str,
    text: str,
    chat_msg: ChatMessage | None = None,
) -> None:
    """Send a Signal reply and create an outbound audit row."""
    from src.services.signal_bridge import (
        create_signal_message,
        send_message,
        update_signal_message_status,
    )

    audit = await create_signal_message(
        connection_id=conn.id,
        direction=SignalMessageDirection.OUTBOUND,
        chat_message_id=str(chat_msg.message_id) if chat_msg else None,
        content_preview=text[:200],
        delivery_status=SignalDeliveryStatus.PENDING,
    )
    try:
        await send_message(source_phone, text)
        await update_signal_message_status(audit.id, SignalDeliveryStatus.DELIVERED)
    except Exception as e:
        logger.warning("Signal reply delivery failed: %s", e)
        await update_signal_message_status(
            audit.id, SignalDeliveryStatus.FAILED, error_detail=str(e)[:500]
        )


# ── Main entry point ────────────────────────────────────────────────────


async def process_signal_chat(
    conn: SignalConnection,
    message_text: str,
    project_id: str,
    source_phone: str,
) -> None:
    """Route an inbound Signal message to CONFIRM/REJECT or the AI pipeline.

    Called as a fire-and-forget asyncio.Task so the WebSocket listener
    is never blocked by AI latency.
    """
    normalized = message_text.strip().lower()

    if normalized in _CONFIRM_WORDS and conn.github_user_id in _signal_pending:
        await _handle_confirm(conn, source_phone, project_id)
        return

    if normalized in _REJECT_WORDS and conn.github_user_id in _signal_pending:
        await _handle_reject(conn, source_phone)
        return

    await _run_ai_pipeline(conn, message_text, project_id, source_phone)


# ── Workflow orchestration helper ────────────────────────────────────────


async def _run_workflow_orchestration(
    *,
    token: str,
    project_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    issue_node_id: str,
    item_id: str,
    session_id: UUID,
    github_user_id: str = "",
) -> dict:
    """Set up workflow config, create sub-issues, and assign the first agent.

    Mirrors Step 3 of the web app's ``confirm_proposal`` flow.  Returns a
    summary dict ``{"sub_issues": int, "agent": str | None, "error": str | None}``
    for the caller to include in the user reply.

    Args:
        github_user_id: The GitHub user ID of the user who triggered the
            workflow.  Used to load user-specific agent pipeline mappings
            from their project settings.
    """
    from src.config import get_settings
    from src.models.workflow import WorkflowConfiguration
    from src.services.copilot_polling import ensure_polling_started
    from src.services.github_projects import github_projects_service as gh
    from src.services.workflow_orchestrator import (
        PipelineState,
        WorkflowContext,
        get_agent_slugs,
        get_workflow_config,
        get_workflow_orchestrator,
        set_pipeline_state,
        set_workflow_config,
    )
    from src.services.workflow_orchestrator.config import load_user_agent_mappings
    from src.utils import utcnow

    result: dict = {"sub_issues": 0, "agent": None, "error": None}

    try:
        settings = get_settings()

        # ── Load or bootstrap workflow config ──
        config = await get_workflow_config(project_id)
        if not config:
            config = WorkflowConfiguration(
                project_id=project_id,
                repository_owner=owner,
                repository_name=repo,
                copilot_assignee=settings.default_assignee,
            )
            await set_workflow_config(project_id, config)
        else:
            config.repository_owner = owner
            config.repository_name = repo
            if not config.copilot_assignee:
                config.copilot_assignee = settings.default_assignee

        # ── Apply user-specific agent pipeline mappings ──
        if github_user_id:
            user_mappings = await load_user_agent_mappings(github_user_id, project_id)
            if user_mappings:
                logger.info(
                    "Applying user-specific agent pipeline mappings for user=%s project=%s",
                    github_user_id,
                    project_id,
                )
                config.agent_mappings = user_mappings
                await set_workflow_config(project_id, config)

        # ── Set issue status to Backlog ──
        backlog_status = config.status_backlog
        await gh.update_item_status_by_name(
            access_token=token,
            project_id=project_id,
            item_id=item_id,
            status_name=backlog_status,
        )
        logger.info("Set issue #%d status to '%s' on project", issue_number, backlog_status)

        # ── Build workflow context ──
        ctx = WorkflowContext(
            session_id=str(session_id),
            project_id=project_id,
            access_token=token,
            repository_owner=owner,
            repository_name=repo,
            config=config,
        )
        ctx.issue_id = issue_node_id
        ctx.issue_number = issue_number
        ctx.project_item_id = item_id

        orchestrator = get_workflow_orchestrator()

        # ── Create all sub-issues upfront ──
        agent_sub_issues = await orchestrator.create_all_sub_issues(ctx)
        if agent_sub_issues:
            # Populate agents for the initial status so the polling loop
            # doesn't see an empty list and immediately consider the
            # pipeline "complete" (is_complete = 0 >= len([]) = True).
            backlog_agents = get_agent_slugs(config, backlog_status)
            pipeline_state = PipelineState(
                issue_number=issue_number,
                project_id=project_id,
                status=backlog_status,
                agents=backlog_agents,
                agent_sub_issues=agent_sub_issues,
                started_at=utcnow(),
            )
            set_pipeline_state(issue_number, pipeline_state)
            result["sub_issues"] = len(agent_sub_issues)
            logger.info(
                "Pre-created %d sub-issues for issue #%d",
                len(agent_sub_issues),
                issue_number,
            )

        # ── Assign firstBacklog agent ──
        await orchestrator.assign_agent_for_status(ctx, backlog_status, agent_index=0)

        backlog_slugs = get_agent_slugs(config, backlog_status)
        if backlog_slugs:
            result["agent"] = backlog_slugs[0]

        # ── Start Copilot polling ──
        await ensure_polling_started(
            access_token=token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            caller="signal_confirm",
        )

    except Exception as e:
        logger.warning(
            "Issue #%d created but workflow orchestration failed: %s",
            issue_number,
            e,
        )
        result["error"] = str(e)[:200]

    return result


# ── CONFIRM / REJECT ────────────────────────────────────────────────────


async def _handle_confirm(
    conn: SignalConnection,
    source_phone: str,
    project_id: str,
) -> None:
    """Execute the user's pending proposal (issue/task/status update)."""
    pending = _signal_pending.pop(conn.github_user_id, None)
    if not pending:
        await _reply(source_phone, "No pending proposal to confirm.")
        return

    token = await _get_user_access_token(conn.github_user_id)
    if not token:
        _signal_pending[conn.github_user_id] = pending  # restore
        await _reply(
            source_phone,
            "⚠️ Session expired. Please log in to the app and try again.",
        )
        return

    from src.api.chat import add_message

    signal_sid = _signal_session_id(conn.github_user_id)
    pid = pending.get("project_id", project_id)

    try:
        from src.services.cache import cache, get_project_items_cache_key
        from src.services.github_projects import github_projects_service as gh
        from src.utils import resolve_repository

        owner, repo = await resolve_repository(token, pid)

        # ── Issue creation from recommendation ──
        if pending["type"] == "issue_create":
            from src.api.chat import _recommendations

            rec = _recommendations.get(pending["recommendation_id"])
            if not rec:
                await _reply(source_phone, "⚠️ Proposal expired. Send your request again.")
                return

            body_parts = [f"**User Story:**\n{rec.user_story}\n\n**Requirements:**"]
            body_parts.extend(f"- {r}" for r in rec.functional_requirements)
            if rec.technical_notes:
                body_parts.append(f"\n**Technical Notes:**\n{rec.technical_notes}")

            issue = await gh.create_issue(
                access_token=token,
                owner=owner,
                repo=repo,
                title=rec.title,
                body="\n".join(body_parts),
            )
            item_id = await gh.add_issue_to_project(
                access_token=token,
                project_id=pid,
                issue_node_id=issue["node_id"],
            )
            cache.delete(get_project_items_cache_key(pid))

            # ── Workflow orchestration (sub-issues + agent assignment) ──
            wf = await _run_workflow_orchestration(
                token=token,
                project_id=pid,
                owner=owner,
                repo=repo,
                issue_number=issue["number"],
                issue_node_id=issue["node_id"],
                item_id=item_id,
                session_id=signal_sid,
                github_user_id=conn.github_user_id,
            )

            msg = ChatMessage(
                session_id=signal_sid,
                sender_type=SenderType.SYSTEM,
                content=f"✅ Issue created: **{rec.title}** (#{issue['number']})",
                action_type=ActionType.ISSUE_CREATE,
                action_data={"status": "confirmed", "issue_number": issue["number"]},
            )
            add_message(signal_sid, msg)

            # Build reply with orchestration details
            reply_lines = [
                "✅ *Issue Created*\n",
                f"*{rec.title}* — #{issue['number']}",
                issue["html_url"],
            ]
            if wf["sub_issues"]:
                reply_lines.append(f"\n📌 {wf['sub_issues']} sub-issue(s) created")
            if wf["agent"]:
                reply_lines.append(f"🤖 Assigned to agent: _{wf['agent']}_")
            if wf["error"]:
                reply_lines.append(f"\n⚠️ Workflow: _{wf['error']}_")

            await _reply_with_audit(conn, source_phone, "\n".join(reply_lines), msg)
            return

        # ── Task creation from proposal ──
        if pending["type"] == "task_create":
            from src.api.chat import _proposals
            from src.models.recommendation import ProposalStatus

            proposal = _proposals.get(pending.get("proposal_id", ""))
            if not proposal:
                await _reply(source_phone, "⚠️ Proposal expired. Send your request again.")
                return

            issue = await gh.create_issue(
                access_token=token,
                owner=owner,
                repo=repo,
                title=proposal.final_title,
                body=proposal.final_description or "",
            )
            item_id = await gh.add_issue_to_project(
                access_token=token,
                project_id=pid,
                issue_node_id=issue["node_id"],
            )
            proposal.status = ProposalStatus.CONFIRMED
            cache.delete(get_project_items_cache_key(pid))

            # ── Workflow orchestration (sub-issues + agent assignment) ──
            wf = await _run_workflow_orchestration(
                token=token,
                project_id=pid,
                owner=owner,
                repo=repo,
                issue_number=issue["number"],
                issue_node_id=issue["node_id"],
                item_id=item_id,
                session_id=signal_sid,
                github_user_id=conn.github_user_id,
            )

            msg = ChatMessage(
                session_id=signal_sid,
                sender_type=SenderType.SYSTEM,
                content=f"✅ Task created: **{proposal.final_title}** (#{issue['number']})",
                action_type=ActionType.TASK_CREATE,
                action_data={"status": "confirmed", "issue_number": issue["number"]},
            )
            add_message(signal_sid, msg)

            # Build reply with orchestration details
            reply_lines = [
                "✅ *Task Created*\n",
                f"*{proposal.final_title}* — #{issue['number']}",
                issue["html_url"],
            ]
            if wf["sub_issues"]:
                reply_lines.append(f"\n📌 {wf['sub_issues']} sub-issue(s) created")
            if wf["agent"]:
                reply_lines.append(f"🤖 Assigned to agent: _{wf['agent']}_")
            if wf["error"]:
                reply_lines.append(f"\n⚠️ Workflow: _{wf['error']}_")

            await _reply_with_audit(conn, source_phone, "\n".join(reply_lines), msg)
            return

        # ── Status update ──
        if pending["type"] == "status_update":
            from src.api.chat import _proposals
            from src.models.recommendation import ProposalStatus

            proposal = _proposals.get(pending.get("proposal_id", ""))
            if not proposal:
                await _reply(source_phone, "⚠️ Proposal expired. Send your request again.")
                return

            await gh.update_item_status_by_name(
                access_token=token,
                project_id=pid,
                item_id=pending["task_id"],
                status_name=pending["target_status"],
            )
            proposal.status = ProposalStatus.CONFIRMED
            cache.delete(get_project_items_cache_key(pid))

            title = pending.get("task_title", "")
            target = pending["target_status"]
            msg = ChatMessage(
                session_id=signal_sid,
                sender_type=SenderType.SYSTEM,
                content=f"✅ Status updated: **{title}** → _{target}_",
            )
            add_message(signal_sid, msg)
            await _reply_with_audit(
                conn,
                source_phone,
                f"✅ *Status Updated*\n\n*{title}* → _{target}_",
                msg,
            )
            return

    except Exception as e:
        logger.error("Signal CONFIRM failed for user %s: %s", conn.github_user_id, e)
        await _reply(source_phone, f"⚠️ Could not complete: {str(e)[:200]}")


async def _handle_reject(conn: SignalConnection, source_phone: str) -> None:
    """Cancel the user's pending proposal."""
    pending = _signal_pending.pop(conn.github_user_id, None)
    if not pending:
        await _reply(source_phone, "No pending proposal to cancel.")
        return

    from src.api.chat import _proposals, add_message
    from src.models.recommendation import ProposalStatus

    signal_sid = _signal_session_id(conn.github_user_id)

    proposal_id = pending.get("proposal_id")
    if proposal_id:
        proposal = _proposals.get(proposal_id)
        if proposal:
            proposal.status = ProposalStatus.CANCELLED

    msg = ChatMessage(
        session_id=signal_sid,
        sender_type=SenderType.SYSTEM,
        content="❌ Proposal cancelled.",
    )
    add_message(signal_sid, msg)
    await _reply_with_audit(conn, source_phone, "❌ Proposal cancelled.", msg)


# ── AI Pipeline ──────────────────────────────────────────────────────────


async def _run_ai_pipeline(
    conn: SignalConnection,
    message_text: str,
    project_id: str,
    source_phone: str,
) -> None:
    """Process through the AI pipeline and send the response via Signal.

    Mirrors the three-stage detection in the web chat endpoint:
    1. Feature-request → issue recommendation
    2. Status-change → status-update proposal
    3. General input → task proposal
    """
    from src.api.chat import _proposals, _recommendations, add_message
    from src.models.recommendation import (
        AITaskProposal,
        ProposalStatus,
        RecommendationStatus,
    )
    from src.services.ai_agent import get_ai_agent_service
    from src.services.cache import (
        cache,
        get_project_items_cache_key,
        get_user_projects_cache_key,
    )

    signal_sid = _signal_session_id(conn.github_user_id)

    token = await _get_user_access_token(conn.github_user_id)
    if not token:
        await _reply(
            source_phone,
            "⚠️ Your web session has expired. Please log in to the app, then try again.",
        )
        return

    try:
        ai_service = get_ai_agent_service()
    except ValueError:
        await _reply(
            source_phone,
            "⚠️ AI is not configured. Set up your AI provider in the app settings.",
        )
        return

    # ── Gather project context ──
    project_name = "Unknown Project"
    project_columns: list[str] = []
    cached_projects = cache.get(get_user_projects_cache_key(conn.github_user_id))
    if cached_projects:
        for p in cached_projects:
            if p.project_id == project_id:
                project_name = p.name
                project_columns = [col.name for col in p.status_columns]
                break

    current_tasks = cache.get(get_project_items_cache_key(project_id)) or []

    try:
        # ── 1. Feature-request detection ──
        is_feature = False
        try:
            is_feature = await ai_service.detect_feature_request_intent(
                message_text, github_token=token
            )
        except Exception:
            pass

        if is_feature:
            rec = await ai_service.generate_issue_recommendation(
                user_input=message_text,
                project_name=project_name,
                session_id=str(signal_sid),
                github_token=token,
            )
            _recommendations[str(rec.recommendation_id)] = rec
            _signal_pending[conn.github_user_id] = {
                "type": "issue_create",
                "recommendation_id": str(rec.recommendation_id),
                "project_id": project_id,
            }

            requirements = "\n".join(f"• {r}" for r in rec.functional_requirements[:6])
            ai_msg = ChatMessage(
                session_id=signal_sid,
                sender_type=SenderType.ASSISTANT,
                content=(
                    f"Issue Recommendation: {rec.title}\n\n"
                    f"{rec.user_story}\n\nRequirements:\n"
                    + "\n".join(f"- {r}" for r in rec.functional_requirements)
                ),
                action_type=ActionType.ISSUE_CREATE,
                action_data={
                    "recommendation_id": str(rec.recommendation_id),
                    "proposed_title": rec.title,
                    "status": RecommendationStatus.PENDING.value,
                },
            )
            add_message(signal_sid, ai_msg)
            await _reply_with_audit(
                conn,
                source_phone,
                f"📋 *Issue Recommendation*\n"
                f"_Project: {project_name}_\n\n"
                f"*{rec.title}*\n\n"
                f"{rec.user_story[:300]}\n\n"
                f"*Requirements:*\n{requirements}\n\n"
                f"Reply *CONFIRM* to create or *REJECT* to cancel.",
                ai_msg,
            )
            return

        # ── 2. Status-change detection ──
        status_change = await ai_service.parse_status_change_request(
            user_input=message_text,
            available_tasks=[t.title for t in current_tasks],
            available_statuses=project_columns or DEFAULT_STATUS_COLUMNS,
            github_token=token,
        )

        if status_change:
            target_task = ai_service.identify_target_task(
                task_reference=status_change.task_reference,
                available_tasks=current_tasks,
            )

            if target_task:
                proposal = AITaskProposal(
                    session_id=signal_sid,
                    original_input=message_text,
                    proposed_title=target_task.title,
                    proposed_description=(
                        f"Move from '{target_task.status}' to '{status_change.target_status}'"
                    ),
                )
                _proposals[str(proposal.proposal_id)] = proposal
                _signal_pending[conn.github_user_id] = {
                    "type": "status_update",
                    "proposal_id": str(proposal.proposal_id),
                    "project_id": project_id,
                    "task_id": target_task.github_item_id,
                    "task_title": target_task.title,
                    "target_status": status_change.target_status,
                }

                ai_msg = ChatMessage(
                    session_id=signal_sid,
                    sender_type=SenderType.ASSISTANT,
                    content=(f"Status Update: {target_task.title} → {status_change.target_status}"),
                    action_type=ActionType.STATUS_UPDATE,
                    action_data={
                        "proposal_id": str(proposal.proposal_id),
                        "task_title": target_task.title,
                        "target_status": status_change.target_status,
                        "status": ProposalStatus.PENDING.value,
                    },
                )
                add_message(signal_sid, ai_msg)
                await _reply_with_audit(
                    conn,
                    source_phone,
                    f"📋 *Status Change Proposal*\n"
                    f"_Project: {project_name}_\n\n"
                    f"*{target_task.title}*\n"
                    f"_{target_task.status}_ → "
                    f"_{status_change.target_status}_\n\n"
                    f"Reply *CONFIRM* to apply or *REJECT* to cancel.",
                    ai_msg,
                )
                return

            # Task not found
            ai_msg = ChatMessage(
                session_id=signal_sid,
                sender_type=SenderType.ASSISTANT,
                content=(f"Could not find a task matching '{status_change.task_reference}'."),
            )
            add_message(signal_sid, ai_msg)
            await _reply_with_audit(
                conn,
                source_phone,
                f"⚠️ Couldn't find a task matching "
                f"_{status_change.task_reference}_. "
                f"Try a more specific name.",
                ai_msg,
            )
            return

        # ── 3. Task generation (default) ──
        generated = await ai_service.generate_task_from_description(
            user_input=message_text,
            project_name=project_name,
            github_token=token,
        )

        proposal = AITaskProposal(
            session_id=signal_sid,
            original_input=message_text,
            proposed_title=generated.title,
            proposed_description=generated.description,
        )
        _proposals[str(proposal.proposal_id)] = proposal
        _signal_pending[conn.github_user_id] = {
            "type": "task_create",
            "proposal_id": str(proposal.proposal_id),
            "project_id": project_id,
        }

        ai_msg = ChatMessage(
            session_id=signal_sid,
            sender_type=SenderType.ASSISTANT,
            content=(f"Task Proposal: {generated.title}\n\n{generated.description[:500]}"),
            action_type=ActionType.TASK_CREATE,
            action_data={
                "proposal_id": str(proposal.proposal_id),
                "proposed_title": generated.title,
                "status": ProposalStatus.PENDING.value,
            },
        )
        add_message(signal_sid, ai_msg)
        await _reply_with_audit(
            conn,
            source_phone,
            f"📋 *Task Proposal*\n"
            f"_Project: {project_name}_\n\n"
            f"*{generated.title}*\n\n"
            f"{generated.description[:500]}\n\n"
            f"Reply *CONFIRM* to create or *REJECT* to cancel.",
            ai_msg,
        )

    except Exception as e:
        logger.error(
            "Signal AI pipeline failed for user %s: %s",
            conn.github_user_id,
            e,
            exc_info=True,
        )
        error_msg = ChatMessage(
            session_id=signal_sid,
            sender_type=SenderType.ASSISTANT,
            content=f"Processing failed: {str(e)[:200]}",
        )
        add_message(signal_sid, error_msg)
        await _reply(
            source_phone,
            f"⚠️ I couldn't process your message. Please try again.\n\n_{str(e)[:200]}_",
        )
