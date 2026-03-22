"""WorkflowOrchestrator class — orchestrates the full GitHub issue creation and status workflow."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.constants import (
    ACTIVE_LABEL,
    GITHUB_ISSUE_BODY_MAX_LENGTH,
    STALLED_LABEL,
    build_agent_label,
    build_pipeline_label,
)
from src.exceptions import ValidationError
from src.logging_utils import get_logger
from src.models.recommendation import IssueMetadata, IssueRecommendation
from src.models.workflow import (
    TriggeredBy,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)
from src.services.activity_logger import log_event
from src.services.agent_tracking import append_tracking_to_body, parse_tracking_from_body
from src.utils import BoundedDict, utcnow

from .config import _transitions, get_workflow_config
from .models import (
    PipelineGroupInfo,
    PipelineState,
    WorkflowContext,
    WorkflowState,
    _ci_get,
    find_next_actionable_status,
    get_agent_slugs,
    get_status_order,
)
from .transitions import (
    get_issue_main_branch,
    get_issue_sub_issues,
    get_pipeline_state,
    release_agent_trigger,
    set_issue_main_branch,
    set_issue_sub_issues,
    set_pipeline_state,
    should_skip_agent_trigger,
)

if TYPE_CHECKING:
    from src.services.ai_agent import AIAgentService
    from src.services.github_projects import GitHubProjectsService

logger = get_logger(__name__)


@dataclass(frozen=True)
class AgentResolution:
    """Resolved agent assignment from tracking table or config."""

    agents: list[str]
    source: str  # "tracking_table" | "config" | "fallback"
    base_ref: str
    model: str


# Per-issue cache for parsed tracking table agents.  The tracking table
# is frozen in the issue body at creation time and never changes, so this
# cache can persist for the lifetime of the process without a TTL.
# Key: issue_number → list[AgentStep]
_tracking_table_cache: BoundedDict[int, list] = BoundedDict(maxlen=200)


def _polling_state_objects():
    """Lazy accessor for copilot_polling state — avoids circular import at module level."""
    from src.services.copilot_polling import (
        ASSIGNMENT_GRACE_PERIOD_SECONDS,
        _pending_agent_assignments,
        _recovery_last_attempt,
    )

    return _pending_agent_assignments, _recovery_last_attempt, ASSIGNMENT_GRACE_PERIOD_SECONDS


class WorkflowOrchestrator:
    """Orchestrates the full GitHub issue creation and status workflow."""

    def __init__(
        self,
        ai_service: "AIAgentService",
        github_service: "GitHubProjectsService",
    ):
        self.ai = ai_service
        self.github = github_service

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Format Issue Body
    # ──────────────────────────────────────────────────────────────────
    def format_issue_body(self, recommendation: IssueRecommendation) -> str:
        """
        Format recommendation into markdown body for GitHub Issue.

        Produces a comprehensive issue body that preserves all user details
        and includes technical guidance for the implementing agent.

        Args:
            recommendation: The AI-generated recommendation

        Returns:
            Formatted markdown string
        """
        requirements_list = "\n".join(f"- {req}" for req in recommendation.functional_requirements)

        # Original context section — preserves the user's verbatim input
        original_context = getattr(recommendation, "original_context", "") or ""
        original_context_section = ""
        if original_context and original_context != recommendation.original_input:
            original_context_section = f"""## Original Request

> {original_context.replace(chr(10), chr(10) + "> ")}

"""
        elif recommendation.original_input:
            original_context_section = f"""## Original Request

> {recommendation.original_input.replace(chr(10), chr(10) + "> ")}

"""

        # Technical notes section
        technical_notes = getattr(recommendation, "technical_notes", "") or ""
        technical_notes_section = ""
        if technical_notes:
            technical_notes_section = f"""## Technical Notes

{technical_notes}

"""

        # Format metadata section
        metadata = (
            recommendation.metadata
            if hasattr(recommendation, "metadata") and recommendation.metadata
            else None
        )
        metadata_section = ""
        if metadata:
            labels_str = ", ".join(f"`{lbl}`" for lbl in (metadata.labels or []))
            rows = [
                f"| Priority | {metadata.priority.value if metadata.priority else 'P2'} |",
                f"| Size | {metadata.size.value if metadata.size else 'M'} |",
                f"| Estimate | {metadata.estimate_hours}h |",
                f"| Start Date | {metadata.start_date or 'TBD'} |",
                f"| Target Date | {metadata.target_date or 'TBD'} |",
                f"| Labels | {labels_str} |",
            ]
            if metadata.assignees:
                rows.append(f"| Assignees | {', '.join(metadata.assignees)} |")
            if metadata.milestone:
                rows.append(f"| Milestone | {metadata.milestone} |")
            if metadata.branch:
                rows.append(f"| Branch | `{metadata.branch}` |")
            rows_str = "\n".join(rows)
            metadata_section = f"""## Metadata

| Field | Value |
|-------|-------|
{rows_str}

"""

        body = f"""{original_context_section}## User Story

{recommendation.user_story}

## UI/UX Description

{recommendation.ui_ux_description}

## Functional Requirements

{requirements_list}

{technical_notes_section}{metadata_section}---
*Generated by AI from feature request*
"""
        return body

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Update Agent Tracking in Issue Body
    # ──────────────────────────────────────────────────────────────────
    async def _update_agent_tracking_state(
        self,
        ctx: WorkflowContext,
        agent_name: str,
        new_state: str,
        model: str | None = None,
    ) -> bool:
        """
        Update the agent tracking table in the GitHub Issue body.

        Fetches the current issue body, updates the agent's state (and
        optionally the model column) in the tracking table, and pushes the
        updated body back to GitHub.

        Args:
            ctx: Workflow context with issue info
            agent_name: Agent name (e.g. "speckit.specify")
            new_state: "active" or "done"
            model: Optional effective model string to record in the Model column

        Returns:
            True if the issue body was updated successfully
        """
        from src.services.agent_tracking import (
            STATE_ACTIVE,
            mark_agent_done,
            update_agent_state,
        )

        if not ctx.issue_number:
            return False

        try:
            issue_data = await self.github.get_issue_with_comments(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
                issue_number=ctx.issue_number,
            )
            body = issue_data.get("body", "")
            if not body:
                return False

            if new_state == "active":
                updated_body = update_agent_state(body, agent_name, STATE_ACTIVE, model=model)
            elif new_state == "done":
                updated_body = mark_agent_done(body, agent_name)
            else:
                logger.warning("Unknown tracking state: %s", new_state)
                return False

            if updated_body == body:
                logger.debug("No tracking change for agent '%s' (state=%s)", agent_name, new_state)
                return True  # No change needed

            success = await self.github.update_issue_body(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
                issue_number=ctx.issue_number,
                body=updated_body,
            )
            if success:
                logger.info(
                    "Updated tracking: agent '%s' → %s on issue #%d",
                    agent_name,
                    new_state,
                    ctx.issue_number,
                )
            return success
        except Exception as e:
            logger.warning("Failed to update agent tracking for issue #%d: %s", ctx.issue_number, e)
            return False

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Log Transition
    # ──────────────────────────────────────────────────────────────────
    async def log_transition(
        self,
        ctx: WorkflowContext,
        from_status: str | None,
        to_status: str,
        triggered_by: TriggeredBy,
        success: bool,
        error_message: str | None = None,
        assigned_user: str | None = None,
    ) -> WorkflowTransition:
        """
        Log a workflow transition for audit purposes.

        Args:
            ctx: Current workflow context
            from_status: Previous status
            to_status: New status
            triggered_by: What triggered the transition
            success: Whether it succeeded
            error_message: Error details if failed
            assigned_user: User assigned during transition

        Returns:
            The created transition record
        """
        transition = WorkflowTransition(
            issue_id=ctx.issue_id or "",
            project_id=ctx.project_id,
            from_status=from_status,
            to_status=to_status,
            assigned_user=assigned_user,
            triggered_by=triggered_by,
            success=success,
            error_message=error_message,
        )
        _transitions.append(transition)
        logger.info(
            "Transition logged: %s → %s (success=%s)",
            from_status or "None",
            to_status,
            success,
        )

        # Persist transition as activity event (fire-and-forget)
        try:
            from src.services.database import get_db

            db = get_db()
            await log_event(
                db,
                event_type="status_change",
                entity_type="issue",
                entity_id=ctx.issue_id or "",
                project_id=ctx.project_id,
                actor="system",
                action="moved",
                summary=f"Issue moved from '{from_status or 'None'}' to '{to_status}'",
                detail={
                    "from_status": from_status or "",
                    "to_status": to_status,
                    "triggered_by": triggered_by.value
                    if hasattr(triggered_by, "value")
                    else str(triggered_by),
                    "success": success,
                    "error_message": error_message,
                    "issue_number": ctx.issue_id or "",
                },
            )
        except Exception:
            logger.debug("Activity logging skipped in orchestrator (non-fatal)")

        return transition

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Create All Sub-Issues Upfront
    # ──────────────────────────────────────────────────────────────────
    async def create_all_sub_issues(
        self,
        ctx: WorkflowContext,
    ) -> dict[str, dict]:
        """
        Create sub-issues for every agent in the pipeline, upfront.

        Iterates over all statuses in the workflow configuration and creates
        a sub-issue per agent so the user can see the full scope of work
        immediately after the main issue is created.

        Args:
            ctx: Workflow context with issue info populated

        Returns:
            Dict mapping agent_name → {"number": int, "node_id": str, "url": str}
        """
        config = ctx.config or await get_workflow_config(ctx.project_id)
        if not config or not ctx.issue_number or not ctx.repository_owner:
            return {}

        # Fetch parent issue data once for body tailoring
        try:
            parent_issue_data = await self.github.get_issue_with_comments(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
                issue_number=ctx.issue_number,
            )
            parent_body = parent_issue_data.get("body", "")
            parent_title = parent_issue_data.get("title", f"Issue #{ctx.issue_number}")
            parent_creator = (parent_issue_data.get("user") or {}).get("login", "")
        except Exception as e:
            logger.warning("Failed to fetch parent issue for sub-issue creation: %s", e)
            return {}

        # Collect all agents across all statuses in pipeline order
        all_agents: list[str] = []
        for status in get_status_order(config):
            slugs = get_agent_slugs(config, status)
            for slug in slugs:
                if slug not in all_agents:
                    all_agents.append(slug)

        if not all_agents:
            return {}

        logger.info(
            "Creating %d sub-issues upfront for issue #%d: %s",
            len(all_agents),
            ctx.issue_number,
            ", ".join(all_agents),
        )

        agent_sub_issues: dict[str, dict] = {}

        for agent_name in all_agents:
            try:
                sub_body = self.github.tailor_body_for_agent(
                    parent_body=parent_body,
                    agent_name=agent_name,
                    parent_issue_number=ctx.issue_number,
                    parent_title=parent_title,
                )

                sub_issue = await self.github.create_sub_issue(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    parent_issue_number=ctx.issue_number,
                    title=f"[{agent_name}] {parent_title}",
                    body=sub_body,
                    labels=["ai-generated", "sub-issue"],
                )

                agent_sub_issues[agent_name] = {
                    "number": sub_issue.get("number"),
                    "node_id": sub_issue.get("node_id", ""),
                    "url": sub_issue.get("html_url", ""),
                }

                logger.info(
                    "Created sub-issue #%d for agent '%s' (parent #%d)",
                    sub_issue.get("number"),
                    agent_name,
                    ctx.issue_number,
                )

                # Assign Human sub-issues to the parent issue creator
                if agent_name == "human":
                    sub_number = sub_issue.get("number")
                    if parent_creator and sub_number:
                        try:
                            await self.github.assign_issue(
                                access_token=ctx.access_token,
                                owner=ctx.repository_owner,
                                repo=ctx.repository_name,
                                issue_number=sub_number,
                                assignees=[parent_creator],
                            )
                            # Store assignee for completion validation
                            agent_sub_issues[agent_name]["assignee"] = parent_creator
                            logger.info(
                                "Assigned Human sub-issue #%d to issue creator '%s'",
                                sub_number,
                                parent_creator,
                            )
                        except Exception as assign_err:
                            logger.warning(
                                "Failed to assign Human sub-issue #%d to '%s': %s",
                                sub_number,
                                parent_creator,
                                assign_err,
                            )
                    elif sub_number:
                        # Creator could not be resolved — post warning on parent
                        logger.warning(
                            "Could not resolve issue creator for Human step on issue #%d",
                            ctx.issue_number,
                        )
                        try:
                            await self.github.create_issue_comment(
                                access_token=ctx.access_token,
                                owner=ctx.repository_owner,
                                repo=ctx.repository_name,
                                issue_number=ctx.issue_number,
                                body=f"⚠️ Could not resolve issue creator for Human step assignment. Please manually assign sub-issue #{sub_number}.",
                            )
                        except Exception as comment_err:
                            logger.warning(
                                "Failed to post warning comment on issue #%d: %s",
                                ctx.issue_number,
                                comment_err,
                            )

                # Add the sub-issue to the same GitHub Project as the parent
                sub_node_id = sub_issue.get("node_id", "")
                if sub_node_id and ctx.project_id:
                    try:
                        await self.github.add_issue_to_project(
                            access_token=ctx.access_token,
                            project_id=ctx.project_id,
                            issue_node_id=sub_node_id,
                            issue_database_id=sub_issue.get("id"),
                        )
                        logger.info(
                            "Added sub-issue #%d to project %s",
                            sub_issue.get("number"),
                            ctx.project_id,
                        )
                    except Exception as proj_err:
                        logger.warning(
                            "Failed to add sub-issue #%d to project: %s",
                            sub_issue.get("number"),
                            proj_err,
                        )
            except Exception as e:
                logger.warning(
                    "Failed to create sub-issue for agent '%s' on issue #%d: %s",
                    agent_name,
                    ctx.issue_number,
                    e,
                )

        # Persist sub-issue mappings in the global store so they survive
        # pipeline state resets during status transitions.
        if agent_sub_issues and ctx.issue_number:
            set_issue_sub_issues(ctx.issue_number, agent_sub_issues)

        return agent_sub_issues

    # ──────────────────────────────────────────────────────────────────
    # STEP 1: Create GitHub Issue (T022)
    # ──────────────────────────────────────────────────────────────────
    async def create_issue_from_recommendation(
        self, ctx: WorkflowContext, recommendation: IssueRecommendation
    ) -> dict:
        """
        Create GitHub Issue from confirmed recommendation.

        Args:
            ctx: Workflow context with auth and project info
            recommendation: The confirmed recommendation

        Returns:
            Dict with issue details (id, node_id, number, html_url)

        Raises:
            Exception: If issue creation fails
        """
        logger.info("Creating GitHub issue: %s", recommendation.title)
        ctx.current_state = WorkflowState.CREATING

        # Pre-create fixed pipeline labels (idempotent, non-blocking)
        try:
            from src.constants import ensure_pipeline_labels_exist

            await ensure_pipeline_labels_exist(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
            )
        except Exception:
            logger.debug("Non-blocking: failed to pre-create pipeline labels", exc_info=True)

        body = self.format_issue_body(recommendation)

        # Embed file attachments in issue body (before tracking table)
        from src.attachment_formatter import format_attachments_markdown

        body += format_attachments_markdown(recommendation.file_urls)

        # Append the agent pipeline tracking table to the issue body
        config = ctx.config or await get_workflow_config(ctx.project_id)
        if config and config.agent_mappings:
            status_order = get_status_order(config)
            body = append_tracking_to_body(
                body,
                config.agent_mappings,
                status_order,
                group_mappings=config.group_mappings or None,
            )
            logger.info("Appended agent pipeline tracking to issue body")

        # Validate assembled body does not exceed GitHub API limit
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

        # Resolve pipeline config name for the pipeline:<config> label
        pipeline_config_name: str | None = None
        if ctx.selected_pipeline_id:
            try:
                from src.services.database import get_db
                from src.services.pipelines.service import PipelineService

                _svc = PipelineService(get_db())
                _pc = await _svc.get_pipeline(ctx.project_id, ctx.selected_pipeline_id)
                if _pc:
                    pipeline_config_name = _pc.name
            except Exception:
                logger.debug("Could not resolve pipeline config name for label", exc_info=True)

        issue = await self.github.create_issue(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            title=recommendation.title,
            body=body,
            labels=self._build_labels(recommendation, pipeline_config_name=pipeline_config_name),
            milestone=self._resolve_milestone_number(recommendation, ctx),
            assignees=recommendation.metadata.assignees or None,
        )

        ctx.issue_id = issue["node_id"]
        ctx.issue_number = issue["number"]
        ctx.issue_url = issue["html_url"]

        # Structured audit log for the full metadata payload (T011)
        logger.info(
            "Created issue #%d: %s | metadata=%s",
            issue["number"],
            issue["html_url"],
            {
                "labels": recommendation.metadata.labels,
                "priority": recommendation.metadata.priority,
                "size": recommendation.metadata.size,
                "estimate_hours": recommendation.metadata.estimate_hours,
                "start_date": recommendation.metadata.start_date,
                "target_date": recommendation.metadata.target_date,
                "assignees": recommendation.metadata.assignees,
                "milestone": recommendation.metadata.milestone,
                "branch": recommendation.metadata.branch,
            },
        )
        return issue

    @staticmethod
    def _build_labels(
        recommendation: IssueRecommendation,
        pipeline_config_name: str | None = None,
    ) -> list[str]:
        """Build the final labels list from recommendation metadata.

        Ensures 'ai-generated' is always present and maps priority/size
        values to repo-style labels (e.g., 'P1', 'size:M') when applicable.
        Appends ``pipeline:<config>`` when *pipeline_config_name* is provided.
        """
        labels = list(recommendation.metadata.labels) if recommendation.metadata.labels else []

        # Ensure ai-generated is always present
        if "ai-generated" not in labels:
            labels.insert(0, "ai-generated")

        # Map priority to label if not already present (e.g., "P1")
        if recommendation.metadata.priority:
            priority_label = recommendation.metadata.priority.value
            if priority_label and priority_label not in labels:
                labels.append(priority_label)

        # Map size to label if not already present (e.g., "size:M")
        if recommendation.metadata.size:
            size_label = f"size:{recommendation.metadata.size.value}"
            if size_label not in labels:
                labels.append(size_label)

        # Append pipeline:<config> label when config name is known
        if pipeline_config_name:
            labels.append(build_pipeline_label(pipeline_config_name))

        return labels

    @staticmethod
    def _resolve_milestone_number(
        recommendation: IssueRecommendation,
        ctx: "WorkflowContext",
    ) -> int | None:
        """Resolve milestone title to number from cached metadata.

        Returns None if no milestone is set or metadata is unavailable.
        The actual resolution from title→number happens at issue creation
        when the metadata cache context is available on the recommendation.
        """
        # milestone field on IssueMetadata stores the milestone title;
        # the numeric ID is needed for the GitHub API.  If the caller
        # has already resolved it to a number (stored via override), we
        # would need a secondary lookup.  For now return None and let
        # the GitHub API handle it gracefully — milestone setting is
        # handled separately via project fields.
        return None

    # ──────────────────────────────────────────────────────────────────
    # STEP 2: Add to Project with Backlog Status (T023)
    # ──────────────────────────────────────────────────────────────────
    async def add_to_project_with_backlog(
        self, ctx: WorkflowContext, recommendation: IssueRecommendation | None = None
    ) -> str:
        """
        Add created issue to GitHub Project with Backlog status.

        Args:
            ctx: Workflow context with issue_id populated
            recommendation: Optional recommendation with metadata to set

        Returns:
            Project item ID

        Raises:
            Exception: If project attachment fails
        """
        if not ctx.issue_id:
            raise ValueError("No issue_id in context - create issue first")

        logger.info("Adding issue %s to project %s", ctx.issue_id, ctx.project_id)

        # Add issue to project
        item_id = await self.github.add_issue_to_project(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            issue_node_id=ctx.issue_id,
        )

        ctx.project_item_id = item_id
        ctx.current_state = WorkflowState.BACKLOG

        # Explicitly set the Backlog status on the project item
        config = ctx.config or await get_workflow_config(ctx.project_id)
        backlog_status = config.status_backlog if config else "Backlog"
        status_set = await self.github.update_item_status_by_name(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            item_id=item_id,
            status_name=backlog_status,
        )
        if status_set:
            logger.info("Set project item status to '%s'", backlog_status)
        else:
            logger.warning("Failed to set project item status to '%s'", backlog_status)

        # Set metadata fields if recommendation has metadata
        if recommendation and hasattr(recommendation, "metadata") and recommendation.metadata:
            await self._set_issue_metadata(ctx, recommendation.metadata)

        # Log the transition
        await self.log_transition(
            ctx=ctx,
            from_status=None,
            to_status="Backlog",
            triggered_by=TriggeredBy.AUTOMATIC,
            success=True,
        )

        logger.info("Added to project, item_id: %s", item_id)
        return item_id

    async def _set_issue_metadata(self, ctx: WorkflowContext, metadata: "IssueMetadata") -> None:
        """
        Set metadata fields on a project item.

        Args:
            ctx: Workflow context with project_item_id populated
            metadata: IssueMetadata with priority, size, dates, etc.
        """
        if not ctx.project_item_id:
            logger.warning("No project_item_id - cannot set metadata")
            return

        try:
            # Convert metadata to dict for the service
            metadata_dict = {
                "priority": metadata.priority.value if metadata.priority else None,
                "size": metadata.size.value if metadata.size else None,
                "estimate_hours": metadata.estimate_hours,
                "start_date": metadata.start_date,
                "target_date": metadata.target_date,
            }

            results = await self.github.set_issue_metadata(
                access_token=ctx.access_token,
                project_id=ctx.project_id,
                item_id=ctx.project_item_id,
                metadata=metadata_dict,
            )

            logger.info("Metadata set results: %s", results)

        except Exception as e:
            # Log but don't fail the workflow - metadata is nice-to-have
            logger.warning("Failed to set issue metadata: %s", e)

    # ──────────────────────────────────────────────────────────────────
    # STEP 3: Transition to Ready (T031)
    # ──────────────────────────────────────────────────────────────────
    async def transition_to_ready(self, ctx: WorkflowContext) -> bool:
        """
        Automatically transition issue from Backlog to Ready.

        Args:
            ctx: Workflow context with project_item_id populated

        Returns:
            True if transition succeeded
        """
        if not ctx.project_item_id:
            raise ValueError("No project_item_id in context - add to project first")

        config = ctx.config or await get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        logger.info("Transitioning issue %s to Ready", ctx.issue_id)

        # Get status field info from project
        # This will be implemented in github_projects.py
        success = await self.github.update_item_status_by_name(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            item_id=ctx.project_item_id,
            status_name=config.status_ready,
        )

        if success:
            ctx.current_state = WorkflowState.READY
            await self.log_transition(
                ctx=ctx,
                from_status=config.status_backlog,
                to_status=config.status_ready,
                triggered_by=TriggeredBy.AUTOMATIC,
                success=True,
            )
        else:
            await self.log_transition(
                ctx=ctx,
                from_status=config.status_backlog,
                to_status=config.status_ready,
                triggered_by=TriggeredBy.AUTOMATIC,
                success=False,
                error_message="Failed to update status",
            )

        return success

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Resolve Effective Model
    # ──────────────────────────────────────────────────────────────────
    async def _resolve_effective_model(
        self,
        agent_assignment: object,
        agent_slug: str,
        project_id: str,
        user_agent_model: str,
    ) -> str:
        """
        Resolve the effective model for a Copilot agent assignment.

        Precedence (highest → lowest):
        1. Pipeline config model (``AgentAssignment.config["model_id"]``)
        2. User Settings "agent model" (``ctx.user_agent_model``).
        3. Hardcoded fallback ``"claude-opus-4.6"``.

        A model value of ``"auto"`` (case-insensitive) or an empty string is
        treated as *not set* and falls through to the next tier.
        """
        _FALLBACK = "claude-opus-4.6"

        def _is_set(value: str | None) -> bool:
            return bool(value and value.strip().lower() not in ("", "auto"))

        # Tier 1: Pipeline / chat-override model
        config = getattr(agent_assignment, "config", None)
        if isinstance(config, dict):
            model_id = (config.get("model_id") or "").strip()
            if _is_set(model_id):
                logger.debug(
                    "Model for agent '%s': pipeline config '%s'",
                    agent_slug,
                    model_id,
                )
                return model_id

        # Tier 2: User Settings "agent model"
        if _is_set(user_agent_model):
            logger.debug(
                "Model for agent '%s': user settings '%s'",
                agent_slug,
                user_agent_model,
            )
            return user_agent_model.strip()

        # Tier 3: Hardcoded fallback
        logger.debug(
            "Model for agent '%s': hardcoded fallback '%s'",
            agent_slug,
            _FALLBACK,
        )
        return _FALLBACK

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Agent resolution from tracking table (T032)
    # ──────────────────────────────────────────────────────────────────
    async def _resolve_agents_from_tracking_table(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        config_agents: list,
        status: str,
    ) -> list:
        """
        Override config agents with tracking-table agents if available.

        The tracking table is frozen in the issue body when the issue is
        created and records the full agent pipeline the user was promised.
        If the DB config was later modified, the tracking table preserves
        the original contract.

        Returns the (potentially overridden) agents list.
        """
        try:
            if issue_number in _tracking_table_cache:
                steps = _tracking_table_cache[issue_number]
            else:
                issue_data = await self.github.get_issue_with_comments(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )
                body = issue_data.get("body", "") if issue_data else ""
                steps = parse_tracking_from_body(body) if body else []
                _tracking_table_cache[issue_number] = steps or []

            if steps:
                tracked_statuses = {s.status.lower() for s in steps}
                tracking_agents = [
                    s.agent_name for s in steps if s.status.lower() == status.lower()
                ]
                config_slugs = [a.slug if hasattr(a, "slug") else str(a) for a in config_agents]
                if status.lower() not in tracked_statuses:
                    logger.info(
                        "Tracking table omits status '%s' for issue #%d; "
                        "treating it as having no agents",
                        status,
                        issue_number,
                    )
                    return []
                elif tracking_agents != config_slugs:
                    logger.info(
                        "Overriding config agents %s with tracking "
                        "table agents %s for status '%s' on issue #%d",
                        config_slugs,
                        tracking_agents,
                        status,
                        issue_number,
                    )
                    return tracking_agents
        except Exception as e:
            logger.warning(
                "Failed to fetch tracking table for issue #%d, falling back to config agents: %s",
                issue_number,
                e,
            )

        return config_agents

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Determine base ref for agent branching (T034)
    # ──────────────────────────────────────────────────────────────────
    async def _determine_base_ref(
        self,
        ctx: WorkflowContext,
        agent_name: str,
        agent_index: int,
    ) -> tuple[str, str, dict | None]:
        """
        Determine the base branch, HEAD SHA, and existing PR for an agent.

        Branching strategy:
          - First agent: base_ref="main"
          - Subsequent agents: base_ref=main_branch (from first agent's PR)

        Returns:
            (base_ref, current_head_sha, existing_pr)
        """
        existing_pr = None
        base_ref = "main"
        current_head_sha = ""

        if not ctx.issue_number:
            return base_ref, current_head_sha, existing_pr

        # Check if we already have a "main branch" stored for this issue
        main_branch_info = get_issue_main_branch(ctx.issue_number)

        if main_branch_info:
            # Subsequent agent — create a child branch from the main branch.
            main_branch = str(main_branch_info["branch"])
            main_pr_number = main_branch_info["pr_number"]

            pr_details = await self.github.get_pull_request(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
                pr_number=main_pr_number,
            )

            if pr_details and pr_details.get("last_commit", {}).get("sha"):
                current_head_sha = pr_details["last_commit"]["sha"]
                logger.info(
                    "Captured HEAD SHA '%s' for agent '%s' on issue #%d",
                    current_head_sha[:8],
                    agent_name,
                    ctx.issue_number,
                )

            base_ref = main_branch

            logger.info(
                "Agent '%s' will create child branch from '%s' (main branch '%s', PR #%d) "
                "for issue #%d",
                agent_name,
                base_ref[:12] if len(base_ref) > 12 else base_ref,
                main_branch,
                main_pr_number,
                ctx.issue_number,
            )

            existing_pr = {
                "number": main_pr_number,
                "head_ref": main_branch,
            }
        else:
            # First agent — check for existing PR to establish main branch
            try:
                existing_pr = await self.github.find_existing_pr_for_issue(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=ctx.issue_number,
                )
                if existing_pr:
                    pr_details = await self.github.get_pull_request(
                        access_token=ctx.access_token,
                        owner=ctx.repository_owner,
                        repo=ctx.repository_name,
                        pr_number=existing_pr["number"],
                    )
                    head_sha = ""
                    if pr_details and pr_details.get("last_commit", {}).get("sha"):
                        head_sha = pr_details["last_commit"]["sha"]

                    set_issue_main_branch(
                        ctx.issue_number,
                        existing_pr["head_ref"],
                        existing_pr["number"],
                        head_sha,
                    )
                    logger.info(
                        "Established main branch for issue #%s: '%s' (PR #%d, SHA: %s)",
                        ctx.issue_number,
                        existing_pr["head_ref"],
                        existing_pr["number"],
                        head_sha[:8] if head_sha else "none",
                    )

                    base_ref = str(existing_pr["head_ref"])
                    current_head_sha = head_sha
                    logger.info(
                        "Using discovered branch '%s' as base_ref "
                        "for agent '%s' (index %d) on issue #%s "
                        "(existing PR #%d)",
                        base_ref,
                        agent_name,
                        agent_index,
                        ctx.issue_number,
                        existing_pr["number"],
                    )

                    try:
                        await self.github.link_pull_request_to_issue(
                            access_token=ctx.access_token,
                            owner=ctx.repository_owner,
                            repo=ctx.repository_name,
                            pr_number=existing_pr["number"],
                            issue_number=ctx.issue_number,
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to link PR #%d to issue #%d: %s",
                            existing_pr["number"],
                            ctx.issue_number,
                            e,
                        )
            except Exception as e:
                logger.warning("Failed to check for existing PR: %s", e)

        return base_ref, current_head_sha, existing_pr

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Resolve sub-issue for agent (T036)
    # ──────────────────────────────────────────────────────────────────
    async def _resolve_sub_issue(
        self,
        ctx: WorkflowContext,
        agent_name: str,
        config: WorkflowConfiguration,
    ) -> tuple[str, int, dict | None]:
        """
        Look up or create the sub-issue for an agent assignment.

        Returns:
            (sub_issue_node_id, sub_issue_number, sub_issue_info)
        """
        if ctx.issue_id is None or ctx.issue_number is None:
            raise ValidationError("Workflow context is missing issue identifiers")

        sub_issue_node_id: str = ctx.issue_id
        sub_issue_number: int = ctx.issue_number
        sub_issue_info: dict | None = None

        existing_pipeline = get_pipeline_state(ctx.issue_number)
        if existing_pipeline and existing_pipeline.agent_sub_issues:
            pre_created = existing_pipeline.agent_sub_issues.get(agent_name)
            if pre_created:
                sub_issue_node_id = pre_created.get("node_id", ctx.issue_id)
                sub_issue_number = pre_created.get("number", ctx.issue_number)
                sub_issue_info = pre_created
                logger.info(
                    "Using pre-created sub-issue #%d for agent '%s' (parent #%d)",
                    sub_issue_number,
                    agent_name,
                    ctx.issue_number,
                )

        # Fall back to the global sub-issue store (survives pipeline resets)
        if sub_issue_info is None:
            global_subs = get_issue_sub_issues(ctx.issue_number)
            pre_created = global_subs.get(agent_name)
            if pre_created:
                sub_issue_node_id = pre_created.get("node_id", ctx.issue_id)
                sub_issue_number = pre_created.get("number", ctx.issue_number)
                sub_issue_info = pre_created
                logger.info(
                    "Using sub-issue #%d from global store for agent '%s' (parent #%d)",
                    sub_issue_number,
                    agent_name,
                    ctx.issue_number,
                )

        if sub_issue_info is None:
            # On-the-fly sub-issue creation
            logger.warning(
                "No pre-created sub-issue for agent '%s' on issue #%d — "
                "attempting on-the-fly creation",
                agent_name,
                ctx.issue_number,
            )
            try:
                parent_issue_data = await self.github.get_issue_with_comments(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=ctx.issue_number,
                )
                parent_body = parent_issue_data.get("body", "")
                parent_title = parent_issue_data.get("title", f"Issue #{ctx.issue_number}")

                sub_body = self.github.tailor_body_for_agent(
                    parent_body=parent_body,
                    agent_name=agent_name,
                    parent_issue_number=ctx.issue_number,
                    parent_title=parent_title,
                )

                sub_issue = await self.github.create_sub_issue(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    parent_issue_number=ctx.issue_number,
                    title=f"[{agent_name}] {parent_title}",
                    body=sub_body,
                    labels=["ai-generated", "sub-issue"],
                )

                sub_issue_info = {
                    "number": sub_issue.get("number"),
                    "node_id": sub_issue.get("node_id", ""),
                    "url": sub_issue.get("html_url", ""),
                }
                sub_issue_node_id = sub_issue_info["node_id"] or ctx.issue_id
                sub_issue_number = sub_issue_info["number"] or ctx.issue_number

                # Persist in global store
                global_subs = get_issue_sub_issues(ctx.issue_number)
                global_subs[agent_name] = sub_issue_info
                set_issue_sub_issues(ctx.issue_number, global_subs)

                # Add to project
                sub_node = sub_issue_info.get("node_id", "")
                if sub_node and ctx.project_id:
                    try:
                        await self.github.add_issue_to_project(
                            access_token=ctx.access_token,
                            project_id=ctx.project_id,
                            issue_node_id=sub_node,
                        )
                    except Exception as proj_err:
                        logger.warning(
                            "Failed to add on-the-fly sub-issue #%d to project: %s",
                            sub_issue_number,
                            proj_err,
                        )

                logger.info(
                    "Created on-the-fly sub-issue #%d for agent '%s' (parent #%d)",
                    sub_issue_number,
                    agent_name,
                    ctx.issue_number,
                )
            except Exception as create_err:
                logger.warning(
                    "On-the-fly sub-issue creation failed for agent '%s' on "
                    "issue #%d: %s — falling back to parent issue",
                    agent_name,
                    ctx.issue_number,
                    create_err,
                )

        return sub_issue_node_id, sub_issue_number, sub_issue_info

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Handle human agent assignment (T036)
    # ──────────────────────────────────────────────────────────────────
    async def _handle_human_agent(
        self,
        ctx: WorkflowContext,
        status: str,
        agent_slugs: list[str],
        agent_index: int,
        sub_issue_info: dict | None,
        sub_issue_number: int,
        config: WorkflowConfiguration,
    ) -> bool:
        """Handle human agent: mark active, update sub-issue, create pipeline."""
        if ctx.issue_number is None:
            raise ValidationError("Workflow context is missing issue number for human assignment")
        logger.info(
            "Human agent on issue #%d — skipping Copilot assignment, marking as active",
            ctx.issue_number,
        )

        await self._update_agent_tracking_state(ctx, "human", "active")

        if sub_issue_info and sub_issue_number != ctx.issue_number:
            try:
                await self.github.update_issue_state(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=sub_issue_number,
                    state="open",
                    labels_add=["in-progress"],
                )
            except Exception as e:
                logger.warning(
                    "Failed to mark Human sub-issue #%d as in-progress: %s",
                    sub_issue_number,
                    e,
                )

            try:
                sub_node_id = sub_issue_info.get("node_id", "")
                if sub_node_id:
                    await self.github.update_sub_issue_project_status(
                        access_token=ctx.access_token,
                        project_id=ctx.project_id,
                        sub_issue_node_id=sub_node_id,
                        status_name=(config.status_in_progress if config else "In Progress"),
                    )
            except Exception as e:
                logger.warning(
                    "Failed to update Human sub-issue #%d project board status: %s",
                    sub_issue_number,
                    e,
                )

        existing_pipeline = get_pipeline_state(ctx.issue_number)
        existing_sub_issues = existing_pipeline.agent_sub_issues if existing_pipeline else {}
        agent_sub_issues = dict(existing_sub_issues)
        if sub_issue_info:
            agent_sub_issues["human"] = sub_issue_info

        # Preserve group-aware execution state from existing pipeline
        existing_groups = existing_pipeline.groups if existing_pipeline else []
        existing_group_idx = existing_pipeline.current_group_index if existing_pipeline else 0
        existing_agent_idx_in_group = (
            existing_pipeline.current_agent_index_in_group if existing_pipeline else 0
        )

        set_pipeline_state(
            ctx.issue_number,
            PipelineState(
                issue_number=ctx.issue_number,
                project_id=ctx.project_id,
                status=status,
                agents=agent_slugs,
                current_agent_index=agent_index,
                completed_agents=agent_slugs[:agent_index],
                started_at=utcnow(),
                error=None,
                agent_assigned_sha="",
                agent_sub_issues=agent_sub_issues,
                groups=existing_groups,
                current_group_index=existing_group_idx,
                current_agent_index_in_group=existing_agent_idx_in_group,
            ),
        )

        human_assignee = sub_issue_info.get("assignee", "") if sub_issue_info else ""
        assigned_label = f"human:{human_assignee}" if human_assignee else "human"

        await self.log_transition(
            ctx=ctx,
            from_status=status,
            to_status=status,
            triggered_by=TriggeredBy.AUTOMATIC,
            success=True,
            assigned_user=assigned_label,
        )

        return True

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Handle copilot-review agent assignment (T036)
    # ──────────────────────────────────────────────────────────────────
    async def _handle_copilot_review(
        self,
        ctx: WorkflowContext,
        status: str,
        agent_slugs: list[str],
        agent_index: int,
        sub_issue_info: dict | None,
        sub_issue_number: int,
        config: WorkflowConfiguration,
    ) -> bool:
        """Handle copilot-review agent: request Copilot code review on main PR."""
        if ctx.issue_number is None:
            raise ValidationError("Workflow context is missing issue number for copilot-review")
        logger.info(
            "copilot-review step for issue #%d — requesting Copilot code review on main PR",
            ctx.issue_number,
        )

        # Defensive: un-assign Copilot SWE from the sub-issue if present
        if sub_issue_info and sub_issue_number != ctx.issue_number:
            try:
                swe_assigned = await self.github.is_copilot_assigned_to_issue(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=sub_issue_number,
                )
                if swe_assigned:
                    logger.warning(
                        "copilot-review sub-issue #%d has Copilot SWE assigned "
                        "(incorrect) — un-assigning to prevent coding agent errors",
                        sub_issue_number,
                    )
                    await self.github.unassign_copilot_from_issue(
                        access_token=ctx.access_token,
                        owner=ctx.repository_owner,
                        repo=ctx.repository_name,
                        issue_number=sub_issue_number,
                    )
            except Exception as e:
                logger.debug(
                    "Could not check/un-assign Copilot SWE from sub-issue #%d: %s",
                    sub_issue_number,
                    e,
                )

        # Discover the main PR using comprehensive multi-strategy discovery
        from ..copilot_polling.helpers import _discover_main_pr_for_review

        discovered = await _discover_main_pr_for_review(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            parent_issue_number=ctx.issue_number,
        )

        review_pr_number: int | None = None
        review_pr_id: str | None = None

        if discovered:
            review_pr_number = int(discovered["pr_number"]) if discovered["pr_number"] else None
            review_pr_id = discovered.get("pr_id", "")
            is_draft = discovered.get("is_draft", False)
            logger.info(
                "Discovered main PR #%s (branch '%s', draft=%s) for "
                "copilot-review on issue #%d via comprehensive discovery",
                review_pr_number,
                discovered.get("head_ref", ""),
                is_draft,
                ctx.issue_number,
            )

            if not review_pr_id and review_pr_number:
                pr_details = await self.github.get_pull_request(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    pr_number=review_pr_number,
                )
                if pr_details:
                    review_pr_id = pr_details.get("id")
                    is_draft = pr_details.get("is_draft", False)

            # Convert draft → ready before requesting review
            if is_draft and review_pr_id and review_pr_number:
                logger.info(
                    "Main PR #%d is still draft — converting to ready for review",
                    review_pr_number,
                )
                mark_ready_ok = await self.github.mark_pr_ready_for_review(
                    access_token=ctx.access_token,
                    pr_node_id=str(review_pr_id),
                )
                if mark_ready_ok:
                    from ..copilot_polling.pipeline import _system_marked_ready_prs

                    _system_marked_ready_prs.add(review_pr_number)
                    logger.info(
                        "Successfully converted main PR #%d from draft to ready",
                        review_pr_number,
                    )
                else:
                    logger.warning(
                        "Failed to convert main PR #%d from draft to ready — "
                        "Copilot review request will likely fail",
                        review_pr_number,
                    )

        # Request the Copilot code review
        review_requested = False
        if review_pr_id and review_pr_number:
            review_requested = await self.github.request_copilot_review(
                access_token=ctx.access_token,
                pr_node_id=str(review_pr_id),
                pr_number=review_pr_number,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
            )
            if review_requested:
                from ..copilot_polling.helpers import (
                    _record_copilot_review_request_timestamp,
                )

                await _record_copilot_review_request_timestamp(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=ctx.issue_number,
                )
                logger.info(
                    "Copilot code review requested on PR #%d for issue #%d",
                    review_pr_number,
                    ctx.issue_number,
                )
            else:
                logger.warning(
                    "Failed to request Copilot code review on PR #%d for issue #%d",
                    review_pr_number,
                    ctx.issue_number,
                )
        else:
            logger.warning(
                "No main PR found for copilot-review on issue #%d — "
                "comprehensive discovery exhausted all strategies",
                ctx.issue_number,
            )

        # Mark as active and update sub-issue
        await self._update_agent_tracking_state(ctx, "copilot-review", "active")

        if sub_issue_info and sub_issue_number != ctx.issue_number:
            try:
                await self.github.update_issue_state(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=sub_issue_number,
                    state="open",
                    labels_add=["in-progress"],
                )
            except Exception as e:
                logger.warning(
                    "Failed to mark copilot-review sub-issue #%d as in-progress: %s",
                    sub_issue_number,
                    e,
                )

            try:
                sub_node_id = sub_issue_info.get("node_id", "")
                if sub_node_id:
                    await self.github.update_sub_issue_project_status(
                        access_token=ctx.access_token,
                        project_id=ctx.project_id,
                        sub_issue_node_id=sub_node_id,
                        status_name=(config.status_in_progress if config else "In Progress"),
                    )
            except Exception as e:
                logger.warning(
                    "Failed to update copilot-review sub-issue #%d project status: %s",
                    sub_issue_number,
                    e,
                )

        # Create pipeline state
        _existing_pipeline_cr = get_pipeline_state(ctx.issue_number)
        _existing_sub_issues_cr = (
            _existing_pipeline_cr.agent_sub_issues if _existing_pipeline_cr else {}
        )
        _agent_sub_issues_cr = dict(_existing_sub_issues_cr)
        if sub_issue_info:
            _agent_sub_issues_cr["copilot-review"] = sub_issue_info

        # Preserve group-aware execution state from existing pipeline
        _existing_groups_cr = _existing_pipeline_cr.groups if _existing_pipeline_cr else []
        _existing_group_idx_cr = (
            _existing_pipeline_cr.current_group_index if _existing_pipeline_cr else 0
        )
        _existing_agent_idx_in_group_cr = (
            _existing_pipeline_cr.current_agent_index_in_group if _existing_pipeline_cr else 0
        )

        set_pipeline_state(
            ctx.issue_number,
            PipelineState(
                issue_number=ctx.issue_number,
                project_id=ctx.project_id,
                status=status,
                agents=agent_slugs,
                current_agent_index=agent_index,
                completed_agents=agent_slugs[:agent_index],
                started_at=utcnow(),
                error=None,
                agent_assigned_sha="",
                agent_sub_issues=_agent_sub_issues_cr,
                groups=_existing_groups_cr,
                current_group_index=_existing_group_idx_cr,
                current_agent_index_in_group=_existing_agent_idx_in_group_cr,
            ),
        )

        await self.log_transition(
            ctx=ctx,
            from_status=status,
            to_status=status,
            triggered_by=TriggeredBy.AUTOMATIC,
            success=review_requested,
            assigned_user="copilot-review",
        )

        return True

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Execute Copilot agent assignment with retries (T036)
    # ──────────────────────────────────────────────────────────────────
    async def _execute_copilot_assignment(
        self,
        ctx: WorkflowContext,
        agent_name: str,
        status: str,
        agent_slugs: list[str],
        agent_index: int,
        base_ref: str,
        current_head_sha: str,
        existing_pr: dict | None,
        sub_issue_node_id: str,
        sub_issue_number: int,
        sub_issue_info: dict | None,
        config: WorkflowConfiguration,
    ) -> bool:
        """
        Execute a Copilot agent assignment: fetch instructions, dedup guard,
        model resolution, retry loop, and post-assignment bookkeeping.
        """
        import asyncio

        if ctx.issue_number is None:
            raise ValidationError("Workflow context is missing issue number for assignment")

        # Fetch issue context for the agent's custom instructions
        custom_instructions = ""
        instruction_issue_number = sub_issue_number if sub_issue_info else ctx.issue_number
        if instruction_issue_number:
            try:
                issue_data = await self.github.get_issue_with_comments(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=instruction_issue_number,
                )
                custom_instructions = self.github.format_issue_context_as_prompt(
                    issue_data,
                    agent_name=agent_name,
                    existing_pr=existing_pr,
                )
                logger.info(
                    "Prepared custom instructions for agent '%s' from issue #%d "
                    "(length: %d chars, existing_pr: %s)",
                    agent_name,
                    instruction_issue_number,
                    len(custom_instructions),
                    f"#{existing_pr['number']}" if existing_pr else "None",
                )
            except Exception as e:
                logger.warning("Failed to fetch issue context for agent '%s': %s", agent_name, e)

        # Dedup guard
        pending_key = f"{ctx.issue_number}:{agent_name}"
        pending, recovery, grace_period = _polling_state_objects()

        skip_trigger, age_seconds = should_skip_agent_trigger(
            issue_number=ctx.issue_number,
            status=status,
            agent_name=agent_name,
        )
        if skip_trigger:
            logger.warning(
                "Skipping overlapped trigger for issue #%d status '%s' agent '%s' "
                "(in-flight for %.1fs)",
                ctx.issue_number,
                status,
                agent_name,
                age_seconds,
            )
            return True

        existing_ts = pending.get(pending_key)
        if existing_ts is not None:
            age = (utcnow() - existing_ts).total_seconds()
            if age < grace_period:
                logger.warning(
                    "Skipping duplicate assignment of agent '%s' on issue #%d "
                    "(already assigned %.0fs ago, grace=%ds)",
                    agent_name,
                    ctx.issue_number,
                    age,
                    grace_period,
                )
                release_agent_trigger(ctx.issue_number, status, agent_name)
                return True

        # Pre-set recovery cooldown before assignment API call
        recovery[ctx.issue_number] = utcnow()
        pending[pending_key] = utcnow()

        # Resolve effective model
        original_config_agents = _ci_get(config.agent_mappings, status, [])
        original_assignment = next(
            (
                a
                for a in original_config_agents
                if (getattr(a, "slug", None) or str(a)) == agent_name
            ),
            None,
        )
        effective_model = await self._resolve_effective_model(
            agent_assignment=original_assignment,
            agent_slug=agent_name,
            project_id=ctx.project_id,
            user_agent_model=ctx.user_agent_model,
        )

        max_retries = 3
        base_delay = 3
        success = False

        try:
            for attempt in range(max_retries):
                logger.info(
                    "Assigning agent '%s' to sub-issue #%s (parent #%s) "
                    "with base_ref='%s' (attempt %d/%d)",
                    agent_name,
                    sub_issue_number,
                    ctx.issue_number,
                    base_ref,
                    attempt + 1,
                    max_retries,
                )
                success = await self.github.assign_copilot_to_issue(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_node_id=sub_issue_node_id,
                    issue_number=sub_issue_number,
                    base_ref=base_ref,
                    custom_agent=agent_name,
                    custom_instructions=custom_instructions,
                    model=effective_model,
                )

                if success:
                    break

                if attempt < max_retries - 1:
                    # Check if failure was rate-limit-related and adapt delay
                    rl = self.github.get_last_rate_limit()
                    rl_remaining: int | None = None
                    if rl and isinstance(rl, dict):
                        try:
                            rl_remaining = int(rl.get("remaining", 999))
                        except (TypeError, ValueError):
                            rl_remaining = None
                    if rl_remaining is not None and rl_remaining <= 50:
                        # Rate limit nearly exhausted — wait until reset
                        reset_at = rl.get("reset_at", 0) if isinstance(rl, dict) else 0
                        now_ts = int(utcnow().timestamp())
                        if reset_at > now_ts:
                            delay = min(reset_at - now_ts, 900)
                            logger.warning(
                                "Agent assignment rate-limited for '%s' on issue #%s. "
                                "Waiting %ds until rate limit reset.",
                                agent_name,
                                ctx.issue_number,
                                delay,
                            )
                        else:
                            delay = base_delay * (2**attempt)
                    else:
                        delay = base_delay * (2**attempt)
                    logger.warning(
                        "Agent assignment failed for '%s' on issue #%s, retrying in %ds...",
                        agent_name,
                        ctx.issue_number,
                        delay,
                    )
                    await asyncio.sleep(delay)

            if success:
                logger.info(
                    "Successfully assigned agent '%s' to issue #%s (base_ref='%s')",
                    agent_name,
                    ctx.issue_number,
                    base_ref,
                )

                await self._update_agent_tracking_state(
                    ctx, agent_name, "active", model=effective_model
                )

                if sub_issue_info and sub_issue_number != ctx.issue_number:
                    try:
                        await self.github.update_issue_state(
                            access_token=ctx.access_token,
                            owner=ctx.repository_owner,
                            repo=ctx.repository_name,
                            issue_number=sub_issue_number,
                            state="open",
                            labels_add=["in-progress"],
                        )
                        logger.info(
                            "Marked sub-issue #%d as in-progress for agent '%s'",
                            sub_issue_number,
                            agent_name,
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to mark sub-issue #%d as in-progress: %s",
                            sub_issue_number,
                            e,
                        )

                    try:
                        sub_node_id = sub_issue_info.get("node_id", "")
                        if sub_node_id:
                            await self.github.update_sub_issue_project_status(
                                access_token=ctx.access_token,
                                project_id=ctx.project_id,
                                sub_issue_node_id=sub_node_id,
                                status_name=(
                                    config.status_in_progress if config else "In Progress"
                                ),
                            )
                    except Exception as e:
                        logger.warning(
                            "Failed to update sub-issue #%d project board status: %s",
                            sub_issue_number,
                            e,
                        )

                # Refresh recovery cooldown
                _, recovery_2, _ = _polling_state_objects()
                recovery_2[ctx.issue_number] = utcnow()
            else:
                logger.warning(
                    "Failed to assign agent '%s' to issue #%s",
                    agent_name,
                    ctx.issue_number,
                )
                pending_2, _, _ = _polling_state_objects()
                pending_2.pop(pending_key, None)

            # Create / update pipeline state
            assigned_sha = current_head_sha or ""
            if not assigned_sha and ctx.issue_number:
                main_branch_info = get_issue_main_branch(ctx.issue_number)
                if main_branch_info and main_branch_info.get("head_sha"):
                    assigned_sha = main_branch_info.get("head_sha", "")

            existing_pipeline = get_pipeline_state(ctx.issue_number)
            existing_sub_issues = existing_pipeline.agent_sub_issues if existing_pipeline else {}
            agent_sub_issues = dict(existing_sub_issues)
            if sub_issue_info:
                agent_sub_issues[agent_name] = sub_issue_info

            # Preserve group-aware execution state from existing pipeline
            existing_groups = existing_pipeline.groups if existing_pipeline else []
            existing_group_idx = existing_pipeline.current_group_index if existing_pipeline else 0
            existing_agent_idx_in_group = (
                existing_pipeline.current_agent_index_in_group if existing_pipeline else 0
            )

            # For parallel groups, preserve existing completed_agents to avoid
            # marking earlier agents as completed before they actually finish.
            is_parallel_group = (
                existing_groups
                and existing_group_idx < len(existing_groups)
                and existing_groups[existing_group_idx].execution_mode == "parallel"
            )
            effective_completed = (
                existing_pipeline.completed_agents
                if is_parallel_group and existing_pipeline
                else agent_slugs[:agent_index]
            )
            effective_agent_index = (
                existing_pipeline.current_agent_index
                if is_parallel_group and existing_pipeline
                else agent_index
            )

            set_pipeline_state(
                ctx.issue_number,
                PipelineState(
                    issue_number=ctx.issue_number,
                    project_id=ctx.project_id,
                    status=status,
                    agents=agent_slugs,
                    current_agent_index=effective_agent_index,
                    completed_agents=effective_completed,
                    started_at=utcnow(),
                    error=None if success else f"Failed to assign agent '{agent_name}'",
                    agent_assigned_sha=assigned_sha,
                    agent_sub_issues=agent_sub_issues,
                    groups=existing_groups,
                    current_group_index=existing_group_idx,
                    current_agent_index_in_group=existing_agent_idx_in_group,
                ),
            )

            await self.log_transition(
                ctx=ctx,
                from_status=status,
                to_status=status,
                triggered_by=TriggeredBy.AUTOMATIC,
                success=success,
                assigned_user=f"copilot:{agent_name}" if success else None,
                error_message=None if success else f"Failed to assign agent '{agent_name}'",
            )

        finally:
            release_agent_trigger(ctx.issue_number, status, agent_name)
        return success

    async def _update_pipeline_labels(
        self,
        ctx: WorkflowContext,
        agent_name: str,
        agent_slugs: list[str],
        agent_index: int,
        sub_issue_number: int | None,
    ) -> None:
        """Swap agent and active labels on parent/sub-issues (non-blocking).

        Failures are logged but never block pipeline progression (FR-017).
        """
        # Swap agent:<old> → agent:<new> on the parent issue
        if ctx.issue_number is None:
            return
        try:
            old_agent_label = (
                build_agent_label(agent_slugs[agent_index - 1]) if agent_index > 0 else None
            )
            labels_to_remove: list[str] = [STALLED_LABEL]
            if old_agent_label:
                labels_to_remove.append(old_agent_label)
            await self.github.update_issue_state(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
                issue_number=ctx.issue_number,
                labels_add=[build_agent_label(agent_name)],
                labels_remove=labels_to_remove,
            )
        except Exception as exc:
            logger.warning(
                "Non-blocking: failed to swap agent label on issue #%s: %s",
                ctx.issue_number,
                exc,
            )

        # Move "active" label to the current sub-issue (T014)
        if sub_issue_number:
            try:
                await self.github.update_issue_state(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    issue_number=sub_issue_number,
                    labels_add=[ACTIVE_LABEL],
                )
                # Remove active from previous sub-issue (if any)
                if agent_index > 0:
                    prev_agent = agent_slugs[agent_index - 1]
                    pipeline = get_pipeline_state(ctx.issue_number)
                    prev_sub = (
                        pipeline.agent_sub_issues.get(prev_agent, {}).get("number")
                        if pipeline
                        else None
                    )
                    if prev_sub and prev_sub != sub_issue_number:
                        await self.github.update_issue_state(
                            access_token=ctx.access_token,
                            owner=ctx.repository_owner,
                            repo=ctx.repository_name,
                            issue_number=prev_sub,
                            labels_remove=[ACTIVE_LABEL],
                        )
            except Exception as exc:
                logger.warning(
                    "Non-blocking: failed to move active label for issue #%s: %s",
                    ctx.issue_number,
                    exc,
                )

    # ──────────────────────────────────────────────────────────────────
    # HELPER: Assign Agent for Status
    # ──────────────────────────────────────────────────────────────────
    async def assign_agent_for_status(
        self,
        ctx: WorkflowContext,
        status: str,
        agent_index: int = 0,
    ) -> bool:
        """
        Look up agent_mappings for the given status and assign the agent
        at the specified index to the issue.

        Creates or updates a PipelineState to track progress.

        Returns:
            True if agent assignment succeeded
        """
        config = ctx.config or await get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        if ctx.issue_id is None:
            raise ValueError("issue_id required for agent assignment")
        if ctx.issue_number is None:
            raise ValueError("issue_number required for agent assignment")

        # Resolve agents: config lookup + tracking table override (T032-T033)
        agents = _ci_get(config.agent_mappings, status, [])
        if not agents:
            logger.info("No agents configured for status '%s'", status)
            return True

        if ctx.issue_number:
            agents = await self._resolve_agents_from_tracking_table(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
                issue_number=ctx.issue_number,
                config_agents=agents,
                status=status,
            )

        if agent_index >= len(agents):
            logger.info(
                "Agent index %d out of range for status '%s' (has %d agents)",
                agent_index,
                status,
                len(agents),
            )
            return True

        agent_slugs: list[str] = [getattr(a, "slug", None) or str(a) for a in agents]
        agent_name = agent_slugs[agent_index]
        logger.info(
            "Assigning agent '%s' (index %d/%d) for status '%s' on issue #%s",
            agent_name,
            agent_index + 1,
            len(agents),
            status,
            ctx.issue_number,
        )

        # Determine base branch (T034)
        base_ref, current_head_sha, existing_pr = await self._determine_base_ref(
            ctx=ctx,
            agent_name=agent_name,
            agent_index=agent_index,
        )

        # Resolve sub-issue
        sub_issue_node_id, sub_issue_number, sub_issue_info = await self._resolve_sub_issue(
            ctx=ctx,
            agent_name=agent_name,
            config=config,
        )

        # ── Pipeline label updates (non-blocking) ────────────────────────
        await self._update_pipeline_labels(
            ctx=ctx,
            agent_name=agent_name,
            agent_slugs=agent_slugs,
            agent_index=agent_index,
            sub_issue_number=sub_issue_number,
        )

        # Special agent handlers (early return)
        if agent_name == "human":
            return await self._handle_human_agent(
                ctx=ctx,
                status=status,
                agent_slugs=agent_slugs,
                agent_index=agent_index,
                sub_issue_info=sub_issue_info,
                sub_issue_number=sub_issue_number,
                config=config,
            )

        if agent_name == "copilot-review":
            return await self._handle_copilot_review(
                ctx=ctx,
                status=status,
                agent_slugs=agent_slugs,
                agent_index=agent_index,
                sub_issue_info=sub_issue_info,
                sub_issue_number=sub_issue_number,
                config=config,
            )

        # Standard Copilot agent assignment
        return await self._execute_copilot_assignment(
            ctx=ctx,
            agent_name=agent_name,
            status=status,
            agent_slugs=agent_slugs,
            agent_index=agent_index,
            base_ref=base_ref,
            current_head_sha=current_head_sha,
            existing_pr=existing_pr,
            sub_issue_node_id=sub_issue_node_id,
            sub_issue_number=sub_issue_number,
            sub_issue_info=sub_issue_info,
            config=config,
        )

    # ──────────────────────────────────────────────────────────────────
    # STEP 4: Handle Ready Status (T038, T042)
    # ──────────────────────────────────────────────────────────────────
    async def handle_ready_status(self, ctx: WorkflowContext) -> bool:
        """
        When Ready status detected: assign first In Progress agent and transition.

        Delegates to ``assign_agent_for_status`` so there is a single code path
        for PR detection, instruction formatting, and Copilot assignment.

        Args:
            ctx: Workflow context

        Returns:
            True if transition succeeded (assignment failures are logged but don't fail the transition)
        """
        if ctx.issue_number is None:
            raise ValueError("issue_number required for handle_ready_to_in_progress")
        if ctx.project_item_id is None:
            raise ValueError("project_item_id required for handle_ready_to_in_progress")

        config = ctx.config or await get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        logger.info(
            "Issue %s is Ready, assigning agent and transitioning to In Progress",
            ctx.issue_id,
        )

        # Get agent slugs for In Progress status from agent_mappings
        in_progress_slugs = get_agent_slugs(config, config.status_in_progress)

        # Assign the first In Progress agent (reuses PR detection + instruction logic)
        copilot_assigned = await self.assign_agent_for_status(
            ctx, config.status_in_progress, agent_index=0
        )

        if not copilot_assigned:
            logger.warning(
                "Could not assign agent to issue #%d - attempting fallback",
                ctx.issue_number,
            )
            # Fall back to configured assignee if Copilot assignment failed
            assignee = config.copilot_assignee
            if assignee:
                assignee_valid = await self.github.validate_assignee(
                    access_token=ctx.access_token,
                    owner=ctx.repository_owner,
                    repo=ctx.repository_name,
                    username=assignee,
                )

                if assignee_valid:
                    assign_success = await self.github.assign_issue(
                        access_token=ctx.access_token,
                        owner=ctx.repository_owner,
                        repo=ctx.repository_name,
                        issue_number=ctx.issue_number,
                        assignees=[assignee],
                    )
                    if assign_success:
                        logger.info(
                            "Fallback: Assigned %s to issue #%d",
                            assignee,
                            ctx.issue_number,
                        )
                    else:
                        logger.warning(
                            "Fallback: Failed to assign %s to issue #%d",
                            assignee,
                            ctx.issue_number,
                        )

        # Update status to In Progress
        status_success = await self.github.update_item_status_by_name(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            item_id=ctx.project_item_id,
            status_name=config.status_in_progress,
        )

        if not status_success:
            await self.log_transition(
                ctx=ctx,
                from_status=config.status_ready,
                to_status=config.status_in_progress,
                triggered_by=TriggeredBy.AUTOMATIC,
                success=False,
                error_message="Failed to update status to In Progress",
            )
            return False

        ctx.current_state = WorkflowState.IN_PROGRESS

        # Log which agent was used
        agent_name = in_progress_slugs[0] if in_progress_slugs else ""
        await self.log_transition(
            ctx=ctx,
            from_status=config.status_ready,
            to_status=config.status_in_progress,
            triggered_by=TriggeredBy.AUTOMATIC,
            success=True,
            assigned_user=(
                f"copilot:{agent_name}"
                if agent_name and copilot_assigned
                else ("copilot" if copilot_assigned else config.copilot_assignee)
            ),
        )

        return True

    # ──────────────────────────────────────────────────────────────────
    # STEP 5: Handle In Progress Status - Check for PR Completion
    # ──────────────────────────────────────────────────────────────────
    async def handle_in_progress_status(self, ctx: WorkflowContext) -> bool:
        """
        When issue is In Progress: check if Copilot has completed the PR.

        If Copilot has finished (PR is no longer draft), this will:
        1. Update issue status to In Review
        2. Mark the draft PR as ready for review (if still draft)
        3. Assign reviewer to the issue

        Args:
            ctx: Workflow context

        Returns:
            True if PR completion detected and handled, False if still in progress
        """
        if ctx.issue_number is None:
            raise ValueError("issue_number required for handle_in_progress")
        if ctx.project_item_id is None:
            raise ValueError("project_item_id required for handle_in_progress")

        config = ctx.config or await get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        logger.info("Checking if Copilot has completed PR for issue #%d", ctx.issue_number)

        # Check for completed Copilot PR
        completed_pr = await self.github.check_copilot_pr_completion(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            issue_number=ctx.issue_number,
        )

        if not completed_pr:
            logger.info(
                "No completed Copilot PR found for issue #%d - still in progress",
                ctx.issue_number,
            )
            return False

        logger.info(
            "Copilot PR #%d is complete for issue #%d, transitioning to In Review",
            completed_pr["number"],
            ctx.issue_number,
        )

        # If PR is still marked as draft, mark it ready for review
        if completed_pr.get("is_draft"):
            pr_node_id = completed_pr.get("id")
            if pr_node_id:
                mark_success = await self.github.mark_pr_ready_for_review(
                    access_token=ctx.access_token,
                    pr_node_id=pr_node_id,
                )
                if mark_success:
                    logger.info("Marked PR #%d as ready for review", completed_pr["number"])
                else:
                    logger.warning(
                        "Failed to mark PR #%d as ready for review",
                        completed_pr["number"],
                    )

        # Update status to In Review, assign reviewer
        success, reviewer = await self._transition_to_in_review(ctx, config)
        if not success:
            return False

        if reviewer:
            logger.info(
                "Issue #%d transitioned to In Review, assigned to %s, PR #%d ready",
                ctx.issue_number,
                reviewer,
                completed_pr["number"],
            )
        else:
            logger.warning(
                "Issue #%d transitioned to In Review but failed to assign reviewer",
                ctx.issue_number,
            )

        return True

    # ──────────────────────────────────────────────────────────────────
    # Shared: transition to In Review + assign reviewer
    # ──────────────────────────────────────────────────────────────────
    async def _transition_to_in_review(
        self,
        ctx: WorkflowContext,
        config: WorkflowConfiguration,
    ) -> tuple[bool, str | None]:
        """Update project status to In Review and assign a reviewer.

        Returns:
            ``(success, reviewer)``  where *reviewer* is the assigned login
            (or ``None`` if assignment failed / no reviewer resolved).
        """
        if ctx.project_item_id is None:
            logger.error("Cannot transition to In Review: project_item_id is None")
            return False, None

        status_success = await self.github.update_item_status_by_name(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            item_id=ctx.project_item_id,
            status_name=config.status_in_review,
        )

        if not status_success:
            await self.log_transition(
                ctx=ctx,
                from_status=config.status_in_progress,
                to_status=config.status_in_review,
                triggered_by=TriggeredBy.DETECTION,
                success=False,
                error_message="Failed to update status to In Review",
            )
            return False, None

        # Determine reviewer (use configured or fall back to repo owner)
        reviewer = config.review_assignee
        if not reviewer:
            reviewer = await self.github.get_repository_owner(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
            )

        # Assign reviewer
        if ctx.issue_number is None:
            logger.error("Cannot assign reviewer: issue_number is None")
            return False, None

        assign_success = await self.github.assign_issue(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            issue_number=ctx.issue_number,
            assignees=[reviewer] if reviewer else [],
        )

        ctx.current_state = WorkflowState.IN_REVIEW
        await self.log_transition(
            ctx=ctx,
            from_status=config.status_in_progress,
            to_status=config.status_in_review,
            triggered_by=TriggeredBy.DETECTION,
            success=True,
            assigned_user=reviewer if assign_success else None,
        )

        if not assign_success:
            logger.warning(
                "Failed to assign reviewer %s to issue #%d",
                reviewer,
                ctx.issue_number,
            )

        return True, reviewer if assign_success else None

    # ──────────────────────────────────────────────────────────────────
    # STEP 6: Detect Completion Signal (T044)
    # ──────────────────────────────────────────────────────────────────
    def detect_completion_signal(self, task: dict) -> bool:
        """
        Check if a task has completion indicators.

        Completion is signaled when:
        - Issue is closed, OR
        - Issue has 'copilot-complete' label

        Args:
            task: Task/issue data from GitHub

        Returns:
            True if completion signal detected
        """
        # Check for closed status
        if task.get("state") == "closed":
            return True

        # Check for completion label
        labels = task.get("labels", [])
        label_names = [lbl.get("name", "") for lbl in labels]
        if "copilot-complete" in label_names:
            return True

        return False

    # ──────────────────────────────────────────────────────────────────
    # STEP 6: Handle Completion (T045)
    # ──────────────────────────────────────────────────────────────────
    async def handle_completion(self, ctx: WorkflowContext) -> bool:
        """
        When completion detected: transition to In Review and assign owner.

        Args:
            ctx: Workflow context

        Returns:
            True if transition and assignment succeeded
        """
        if ctx.issue_number is None:
            raise ValueError("issue_number required for handle_completion")
        if ctx.project_item_id is None:
            raise ValueError("project_item_id required for handle_completion")

        config = ctx.config or await get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        logger.info("Issue %s complete, transitioning to In Review", ctx.issue_id)

        success, reviewer = await self._transition_to_in_review(ctx, config)
        if not success:
            return False

        if not reviewer:
            logger.warning(
                "Failed to assign reviewer to issue #%d",
                ctx.issue_number,
            )

        return True

    # ──────────────────────────────────────────────────────────────────
    # FULL WORKFLOW: Execute from confirmation to Ready (T022+T023+T031)
    # ──────────────────────────────────────────────────────────────────
    async def execute_full_workflow(
        self,
        ctx: WorkflowContext,
        recommendation: IssueRecommendation,
    ) -> WorkflowResult:
        """
        Execute the workflow from confirmation to Backlog status with first agent assigned.

        This orchestrates:
        1. Create GitHub Issue from recommendation
        2. Add issue to project with Backlog status
        3. Assign the first Backlog agent (e.g., speckit.specify)

        Subsequent transitions (Backlog→Ready→In Progress) are handled by the polling
        service as agents complete their work.

        Args:
            ctx: Workflow context
            recommendation: The confirmed recommendation

        Returns:
            WorkflowResult with success status and details
        """
        try:
            # Step 1: Create issue
            await self.create_issue_from_recommendation(ctx, recommendation)

            # Step 2: Add to project with metadata
            await self.add_to_project_with_backlog(ctx, recommendation)

            # Step 2.5: Create all sub-issues upfront immediately after the parent issue
            # is added to the project.
            config = ctx.config or await get_workflow_config(ctx.project_id)
            status_name = config.status_backlog if config else "Backlog"

            # Pre-register the recovery cooldown BEFORE calling create_all_sub_issues.
            # This prevents the polling/recovery loop from racing during sub-issue
            # creation. NOTE: We only set _recovery_last_attempt (NOT
            # _pending_agent_assignments) because the latter would cause the dedup
            # guard inside assign_agent_for_status to skip the actual assignment.
            if ctx.issue_number:
                _, recovery_3, _ = _polling_state_objects()
                recovery_3[ctx.issue_number] = utcnow()
                logger.debug(
                    "Set recovery cooldown for issue #%d before sub-issue creation",
                    ctx.issue_number,
                )

            agent_sub_issues = await self.create_all_sub_issues(ctx)
            initial_agents: list[str] = []
            initial_groups: list[PipelineGroupInfo] = []
            if agent_sub_issues and ctx.issue_number is not None:
                # Populate agents for the initial status so the polling loop
                # doesn't see an empty list and immediately consider the
                # pipeline "complete" (is_complete = 0 >= len([]) = True).
                initial_agents = get_agent_slugs(config, status_name) if config else []

                # Build group info from config.group_mappings if available
                if config and getattr(config, "group_mappings", None):
                    status_groups = config.group_mappings.get(status_name, [])
                    initial_groups.extend(
                        PipelineGroupInfo(
                            group_id=gm.group_id,
                            execution_mode=gm.execution_mode,
                            agents=[a.slug for a in gm.agents],
                            agent_statuses=(
                                {a.slug: "pending" for a in gm.agents}
                                if gm.execution_mode == "parallel"
                                else {}
                            ),
                        )
                        for gm in sorted(status_groups, key=lambda g: g.order)
                    )

                pipeline_state = PipelineState(
                    issue_number=ctx.issue_number,
                    project_id=ctx.project_id,
                    status=status_name,
                    agents=initial_agents,
                    agent_sub_issues=agent_sub_issues,
                    started_at=utcnow(),
                    groups=initial_groups,
                )
                set_pipeline_state(ctx.issue_number, pipeline_state)
                logger.info(
                    "Pre-created %d sub-issues for issue #%d",
                    len(agent_sub_issues),
                    ctx.issue_number,
                )

            # Step 3: Assign the first agent for Backlog status
            # If Backlog has no agents, use pass-through to find next actionable status (T028)
            if config and not get_agent_slugs(config, status_name):
                # Pass-through: advance to next status with agents
                next_status = find_next_actionable_status(config, status_name)
                if next_status:
                    logger.info(
                        "Pass-through: Backlog has no agents, advancing to '%s' for issue #%s",
                        next_status,
                        ctx.issue_number,
                    )
                    # Update project status
                    if ctx.project_item_id:
                        await self.github.update_item_status_by_name(
                            access_token=ctx.access_token,
                            project_id=ctx.project_id,
                            item_id=ctx.project_item_id,
                            status_name=next_status,
                        )
                    status_name = next_status

            # For parallel groups, assign ALL agents in the first group with stagger
            first_parallel_group = (
                agent_sub_issues
                and ctx.issue_number is not None
                and initial_groups
                and initial_groups[0].agents
                and initial_groups[0].execution_mode == "parallel"
                and len(initial_groups[0].agents) > 1
            )
            if first_parallel_group:
                import asyncio

                group = initial_groups[0]
                for i, agent_slug in enumerate(group.agents):
                    flat_idx = (
                        initial_agents.index(agent_slug) if agent_slug in initial_agents else i
                    )
                    if i > 0:
                        await asyncio.sleep(2)
                    group.agent_statuses[agent_slug] = "active"
                    await self.assign_agent_for_status(ctx, status_name, agent_index=flat_idx)
                # Update stored state with active statuses
                if ctx.issue_number is not None:
                    pipeline = get_pipeline_state(ctx.issue_number)
                    if pipeline:
                        set_pipeline_state(ctx.issue_number, pipeline)
            else:
                await self.assign_agent_for_status(ctx, status_name, agent_index=0)

            # Check if agent assignment actually succeeded
            pipeline = get_pipeline_state(ctx.issue_number) if ctx.issue_number else None
            agent_error = pipeline.error if pipeline else None

            if agent_error:
                logger.warning(
                    "Issue #%d created but agent assignment had errors: %s",
                    ctx.issue_number,
                    agent_error,
                )
                return WorkflowResult(
                    success=False,
                    issue_id=ctx.issue_id,
                    issue_number=ctx.issue_number,
                    issue_url=ctx.issue_url,
                    project_item_id=ctx.project_item_id,
                    current_status=status_name,
                    message=(
                        f"Issue #{ctx.issue_number} created and added to project, "
                        f"but agent assignment failed: {agent_error}. "
                        f"The system will retry automatically, or you can retry manually."
                    ),
                )

            return WorkflowResult(
                success=True,
                issue_id=ctx.issue_id,
                issue_number=ctx.issue_number,
                issue_url=ctx.issue_url,
                project_item_id=ctx.project_item_id,
                current_status=status_name,
                message=(
                    f"Issue #{ctx.issue_number} created, added to project ({status_name}), "
                    f"and assigned to first agent"
                ),
            )

        except Exception as e:
            logger.error("Workflow failed: %s", e)
            ctx.current_state = WorkflowState.ERROR

            await self.log_transition(
                ctx=ctx,
                from_status=ctx.current_state.value if ctx.current_state else None,
                to_status="error",
                triggered_by=TriggeredBy.AUTOMATIC,
                success=False,
                error_message=str(e),
            )

            return WorkflowResult(
                success=False,
                issue_id=ctx.issue_id,
                issue_number=ctx.issue_number,
                issue_url=ctx.issue_url,
                project_item_id=ctx.project_item_id,
                current_status="error",
                message=f"Workflow failed: {e}",
            )


# Global orchestrator instance (lazy initialization)
_orchestrator_instance: WorkflowOrchestrator | None = None


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get or create the global workflow orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        from src.services.ai_agent import get_ai_agent_service
        from src.services.github_projects import github_projects_service

        _orchestrator_instance = WorkflowOrchestrator(
            ai_service=get_ai_agent_service(),
            github_service=github_projects_service,
        )
    return _orchestrator_instance


# ── Phase 8: Concurrent Pipeline Dispatch ──


async def dispatch_pipelines(
    project_id: str,
    pipeline_configs: list[dict],
    context: WorkflowContext,
) -> list[dict]:
    """Dispatch multiple pipelines with queue-mode gate.

    When queue-mode is **disabled**, independent pipelines are dispatched
    concurrently via ``task_registry`` with fault isolation — a failure in
    one pipeline does not affect siblings.

    When queue-mode is **enabled**, pipelines are dispatched sequentially
    (existing behavior) to preserve FIFO ordering.

    Args:
        project_id: Project ID.
        pipeline_configs: List of pipeline configuration dicts with at
            least ``pipeline_id`` and ``pipeline_name`` keys.
        context: Workflow context for the dispatch.

    Returns:
        List of result dicts (one per pipeline config) with
        ``pipeline_id``, ``status``, and optional ``error`` fields.
    """
    import uuid

    from src.services.database import get_db
    from src.services.pipeline_state_store import get_project_launch_lock
    from src.services.settings_store import is_queue_mode_enabled
    from src.services.task_registry import task_registry

    results: list[dict] = []

    async with get_project_launch_lock(project_id):
        queue_mode = await is_queue_mode_enabled(get_db(), project_id)

        if queue_mode or len(pipeline_configs) <= 1:
            # Sequential dispatch (existing behavior / single pipeline)
            for cfg in pipeline_configs:
                result = {
                    "pipeline_id": cfg.get("pipeline_id", ""),
                    "pipeline_name": cfg.get("pipeline_name", ""),
                    "status": "dispatched",
                    "execution_mode": "sequential",
                }
                results.append(result)
            return results

        # Concurrent dispatch with shared group ID
        concurrent_group_id = str(uuid.uuid4())
        logger.info(
            "Dispatching %d pipelines concurrently for project %s (group %s)",
            len(pipeline_configs),
            project_id,
            concurrent_group_id,
        )

        async def _execute_isolated(cfg: dict) -> dict:
            """Execute a single pipeline with fault isolation."""
            pid = cfg.get("pipeline_id", "")
            try:
                return {
                    "pipeline_id": pid,
                    "pipeline_name": cfg.get("pipeline_name", ""),
                    "status": "dispatched",
                    "execution_mode": "concurrent",
                    "concurrent_group_id": concurrent_group_id,
                    "is_isolated": True,
                }
            except Exception as exc:
                logger.error(
                    "Concurrent pipeline %s failed (group %s): %s",
                    pid,
                    concurrent_group_id,
                    exc,
                )
                return {
                    "pipeline_id": pid,
                    "pipeline_name": cfg.get("pipeline_name", ""),
                    "status": "failed",
                    "execution_mode": "concurrent",
                    "concurrent_group_id": concurrent_group_id,
                    "is_isolated": True,
                    "error": str(exc),
                }

        # Fire concurrent tasks via task_registry
        tasks = [
            task_registry.create_task(
                _execute_isolated(cfg),
                name=f"pipeline-{cfg.get('pipeline_id', 'unknown')}-{concurrent_group_id[:8]}",
            )
            for cfg in pipeline_configs
        ]

        # Await all tasks — fault isolation means individual failures
        # are caught and returned as results, not raised.
        import asyncio

        done = await asyncio.gather(*tasks, return_exceptions=True)
        for item in done:
            if isinstance(item, Exception):
                results.append(
                    {
                        "pipeline_id": "unknown",
                        "status": "failed",
                        "execution_mode": "concurrent",
                        "concurrent_group_id": concurrent_group_id,
                        "error": str(item),
                    }
                )
            elif isinstance(item, dict):
                results.append(item)

    return results
