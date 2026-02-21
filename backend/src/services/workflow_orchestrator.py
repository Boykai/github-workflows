"""
GitHub Issue Workflow Orchestrator

This file contains all workflow logic in one place for easy reading and modification.

WORKFLOW STATES:
  ANALYZING → RECOMMENDATION_PENDING → CREATING → BACKLOG → READY → IN_PROGRESS → IN_REVIEW

TRANSITIONS:
  1. User message → AI generates recommendation (ANALYZING → RECOMMENDATION_PENDING)
  2. User confirms → Create GitHub Issue (RECOMMENDATION_PENDING → CREATING)
  3. Issue created → Add to project with Backlog status (CREATING → BACKLOG)
  4. Auto-transition → Update to Ready status (BACKLOG → READY)
  5. Status detection → Move to In Progress, assign Copilot (READY → IN_PROGRESS)
  6. Completion detection → Move to In Review, assign owner (IN_PROGRESS → IN_REVIEW)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, TypedDict

from src.models.chat import (
    AgentAssignment,
    IssueMetadata,
    IssueRecommendation,
    TriggeredBy,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)
from src.services.agent_tracking import append_tracking_to_body

if TYPE_CHECKING:
    from src.services.ai_agent import AIAgentService
    from src.services.github_projects import GitHubProjectsService

logger = logging.getLogger(__name__)


def _ci_get(mappings: dict, key: str, default=None):
    """Case-insensitive dict lookup for status names."""
    if key in mappings:
        return mappings[key]
    key_lower = key.lower()
    for k, v in mappings.items():
        if k.lower() == key_lower:
            return v
    return default if default is not None else []


def get_agent_slugs(config: WorkflowConfiguration, status: str) -> list[str]:
    """Extract ordered slug strings for a given status. Case-insensitive lookup."""
    return [
        a.slug if hasattr(a, "slug") else str(a) for a in _ci_get(config.agent_mappings, status, [])
    ]


def get_status_order(config: WorkflowConfiguration) -> list[str]:
    """Return the ordered list of pipeline statuses from configuration."""
    return [
        config.status_backlog,
        config.status_ready,
        config.status_in_progress,
        config.status_in_review,
    ]


def get_next_status(config: WorkflowConfiguration, current_status: str) -> str | None:
    """Return the next status in the pipeline, or None if at the end."""
    order = get_status_order(config)
    try:
        idx = order.index(current_status)
        if idx + 1 < len(order):
            return order[idx + 1]
    except ValueError:
        pass
    return None


def find_next_actionable_status(config: WorkflowConfiguration, current_status: str) -> str | None:
    """
    Find the next status that has agents assigned (pass-through logic, T028).

    Starting from the status *after* current_status, walk forward through the
    pipeline. Return the first status that has agents or the final status in
    the pipeline (even if it has no agents, to avoid infinite skipping).
    Returns None if current_status is already the last one.
    """
    order = get_status_order(config)
    try:
        start = order.index(current_status) + 1
    except ValueError:
        return None

    for i in range(start, len(order)):
        candidate = order[i]
        if get_agent_slugs(config, candidate) or i == len(order) - 1:
            return candidate
    return None


class WorkflowState(Enum):
    """Workflow states for tracking issue lifecycle."""

    ANALYZING = "analyzing"
    RECOMMENDATION_PENDING = "recommendation_pending"
    CREATING = "creating"
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    ERROR = "error"


@dataclass
class WorkflowContext:
    """Context passed through workflow transitions."""

    session_id: str
    project_id: str
    access_token: str
    repository_owner: str = ""
    repository_name: str = ""
    recommendation_id: str | None = None
    issue_id: str | None = None
    issue_number: int | None = None
    issue_url: str | None = None
    project_item_id: str | None = None
    current_state: WorkflowState = WorkflowState.ANALYZING
    config: WorkflowConfiguration | None = None


@dataclass
class PipelineState:
    """Tracks per-issue pipeline progress through sequential agents."""

    issue_number: int
    project_id: str
    status: str
    agents: list[str]
    current_agent_index: int = 0
    completed_agents: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    error: str | None = None
    agent_assigned_sha: str = ""  # HEAD SHA when the current agent was assigned
    # Maps agent_name → sub-issue info for sub-issue-per-agent workflow
    agent_sub_issues: dict[str, dict] = field(default_factory=dict)
    # {agent_name: {"number": int, "node_id": str, "url": str}}

    @property
    def current_agent(self) -> str | None:
        """Get the currently active agent, or None if pipeline is complete."""
        if self.current_agent_index < len(self.agents):
            return self.agents[self.current_agent_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all agents in the pipeline have completed."""
        return self.current_agent_index >= len(self.agents)

    @property
    def next_agent(self) -> str | None:
        """Get the next agent after the current one, or None if last."""
        next_idx = self.current_agent_index + 1
        if next_idx < len(self.agents):
            return self.agents[next_idx]
        return None


# In-memory storage for workflow transitions (audit log)
_transitions: list[WorkflowTransition] = []

# In-memory storage for workflow configurations (per project)
_workflow_configs: dict[str, WorkflowConfiguration] = {}

# In-memory storage for pipeline states (per issue number)
_pipeline_states: dict[int, PipelineState] = {}


class MainBranchInfo(TypedDict):
    """Typed info for an issue's main PR branch."""

    branch: str
    pr_number: int
    head_sha: str  # Commit SHA of the branch head (needed for baseRef)


# In-memory storage for the "main" PR branch per issue
# The first PR's branch becomes the base for all subsequent agent branches
# Maps issue_number -> {branch: str, pr_number: int}
_issue_main_branches: dict[int, MainBranchInfo] = {}

# Global sub-issue mapping store that persists across pipeline state resets.
# When pipeline state is removed during status transitions (e.g., Backlog → Ready),
# the agent_sub_issues on PipelineState are lost.  This global store retains the
# mapping so subsequent agents can still look up (and close) their sub-issues.
# Maps issue_number → {agent_name → {"number": int, "node_id": str, "url": str}}
_issue_sub_issue_map: dict[int, dict[str, dict]] = {}


def get_workflow_config(project_id: str) -> WorkflowConfiguration | None:
    """Get workflow configuration for a project.

    Checks in-memory cache first, then falls back to SQLite project_settings.
    """
    cached = _workflow_configs.get(project_id)
    if cached is not None:
        return cached

    # Fall back to SQLite
    config = _load_workflow_config_from_db(project_id)
    if config is not None:
        _workflow_configs[project_id] = config
    return config


def set_workflow_config(
    project_id: str,
    config: WorkflowConfiguration,
    github_user_id: str | None = None,
) -> None:
    """Set workflow configuration for a project.

    Updates in-memory cache and persists to SQLite project_settings.
    """
    _workflow_configs[project_id] = config
    _persist_workflow_config_to_db(project_id, config, github_user_id)


def _load_workflow_config_from_db(project_id: str) -> WorkflowConfiguration | None:
    """Load workflow configuration from SQLite project_settings table.

    Uses synchronous sqlite3 to avoid event-loop issues with aiosqlite.
    SQLite reads are fast (sub-millisecond) so this is safe to call from
    any context (sync or async).
    """
    import json
    import sqlite3

    try:
        from src.config import get_settings

        db_path = get_settings().database_path
    except Exception:
        return None

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Try loading from the workflow_config column first (full config)
        cursor = conn.execute(
            "SELECT workflow_config FROM project_settings WHERE project_id = ? AND workflow_config IS NOT NULL LIMIT 1",
            (project_id,),
        )
        row = cursor.fetchone()
        if row and row["workflow_config"]:
            raw = json.loads(row["workflow_config"])
            conn.close()
            logger.info(
                "Loaded workflow config from DB (workflow_config column) for project %s", project_id
            )
            return WorkflowConfiguration(**raw)

        # Fall back to agent_pipeline_mappings only
        cursor = conn.execute(
            "SELECT agent_pipeline_mappings FROM project_settings WHERE project_id = ? AND agent_pipeline_mappings IS NOT NULL LIMIT 1",
            (project_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row and row["agent_pipeline_mappings"]:
            raw_mappings = json.loads(row["agent_pipeline_mappings"])
            # Convert raw dicts to AgentAssignment objects
            agent_mappings: dict[str, list[AgentAssignment]] = {}
            for status, agents in raw_mappings.items():
                agent_mappings[status] = [
                    AgentAssignment(**a) if isinstance(a, dict) else AgentAssignment(slug=str(a))
                    for a in agents
                ]
            logger.info(
                "Loaded workflow config from DB (agent_pipeline_mappings column) for project %s",
                project_id,
            )
            config = WorkflowConfiguration(
                project_id=project_id,
                repository_owner="",
                repository_name="",
                agent_mappings=agent_mappings,
            )
            # Backfill: persist the full config to workflow_config column
            # so subsequent loads use the preferred path.
            try:
                _persist_workflow_config_to_db(project_id, config)
                logger.info("Backfilled workflow_config column for project %s", project_id)
            except Exception:
                pass
            return config

        return None
    except Exception:
        logger.warning(
            "Failed to load workflow config from DB for project %s", project_id, exc_info=True
        )
        return None


def _persist_workflow_config_to_db(
    project_id: str,
    config: WorkflowConfiguration,
    github_user_id: str | None = None,
) -> None:
    """Persist workflow configuration to SQLite project_settings table.

    Uses synchronous sqlite3 for reliable writes from any context.
    SQLite in WAL mode supports concurrent access from multiple connections.
    """
    import json
    import sqlite3
    from datetime import UTC, datetime

    try:
        from src.config import get_settings

        db_path = get_settings().database_path
    except Exception:
        return

    # Serialize config
    config_json = config.model_dump_json()
    agent_mappings_json = json.dumps(
        {
            status: [
                a.model_dump(mode="json") if hasattr(a, "model_dump") else {"slug": str(a)}
                for a in agents
            ]
            for status, agents in config.agent_mappings.items()
        }
    )
    now = datetime.now(UTC).isoformat()

    # Use a placeholder user if not provided (backward compat)
    user_id = github_user_id or "__workflow__"

    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA busy_timeout=5000;")

        cursor = conn.execute(
            "SELECT 1 FROM project_settings WHERE github_user_id = ? AND project_id = ?",
            (user_id, project_id),
        )
        existing = cursor.fetchone()

        if existing:
            conn.execute(
                "UPDATE project_settings SET agent_pipeline_mappings = ?, workflow_config = ?, updated_at = ? "
                "WHERE github_user_id = ? AND project_id = ?",
                (agent_mappings_json, config_json, now, user_id, project_id),
            )
        else:
            conn.execute(
                "INSERT INTO project_settings (github_user_id, project_id, agent_pipeline_mappings, workflow_config, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, project_id, agent_mappings_json, config_json, now),
            )
        conn.commit()
        conn.close()
        logger.info("Persisted workflow config to DB for project %s (user=%s)", project_id, user_id)
    except Exception:
        logger.warning(
            "Failed to persist workflow config to DB for project %s", project_id, exc_info=True
        )


def get_transitions(issue_id: str | None = None, limit: int = 50) -> list[WorkflowTransition]:
    """Get workflow transitions, optionally filtered by issue_id."""
    if issue_id:
        filtered = [t for t in _transitions if t.issue_id == issue_id]
        return filtered[-limit:]
    return _transitions[-limit:]


def get_pipeline_state(issue_number: int) -> PipelineState | None:
    """Get pipeline state for a specific issue."""
    return _pipeline_states.get(issue_number)


def get_all_pipeline_states() -> dict[int, PipelineState]:
    """Get all pipeline states."""
    return dict(_pipeline_states)


def set_pipeline_state(issue_number: int, state: PipelineState) -> None:
    """Set or update pipeline state for an issue."""
    _pipeline_states[issue_number] = state


def remove_pipeline_state(issue_number: int) -> None:
    """Remove pipeline state for an issue (e.g., after status transition)."""
    _pipeline_states.pop(issue_number, None)


def get_issue_main_branch(issue_number: int) -> MainBranchInfo | None:
    """
    Get the main PR branch for an issue.

    The first PR's branch becomes the "main" branch for all subsequent
    agent work on that issue.

    Returns:
        Dict with 'branch' and 'pr_number' keys, or None if not set.
    """
    return _issue_main_branches.get(issue_number)


def get_issue_sub_issues(issue_number: int) -> dict[str, dict]:
    """Get the global sub-issue mapping for an issue.

    This store persists across pipeline state resets so that agents
    assigned after a status transition can still find their sub-issues.

    Returns:
        Dict mapping agent_name → {"number": int, "node_id": str, "url": str},
        or empty dict if not set.
    """
    return _issue_sub_issue_map.get(issue_number, {})


def set_issue_sub_issues(issue_number: int, mappings: dict[str, dict]) -> None:
    """Store sub-issue mappings globally for an issue.

    Called when sub-issues are created upfront (create_all_sub_issues) or
    reconstructed from GitHub API.  Merges with existing mappings so that
    partial reconstructions don't overwrite earlier data.
    """
    existing = _issue_sub_issue_map.get(issue_number, {})
    existing.update(mappings)
    _issue_sub_issue_map[issue_number] = existing


def set_issue_main_branch(
    issue_number: int, branch: str, pr_number: int, head_sha: str = ""
) -> None:
    """
    Set the main PR branch for an issue.

    This should only be called once when the first PR is created for an issue.
    All subsequent agents will branch from and merge back into this branch.

    Args:
        issue_number: GitHub issue number
        branch: The first PR's head branch name (e.g., copilot/update-app-title-workflows)
        pr_number: The first PR's number
        head_sha: The commit SHA of the branch head (needed for baseRef)
    """
    if issue_number in _issue_main_branches:
        logger.debug(
            "Issue #%d already has main branch set to '%s', not overwriting",
            issue_number,
            _issue_main_branches[issue_number].get("branch"),
        )
        return
    _issue_main_branches[issue_number] = {
        "branch": branch,
        "pr_number": pr_number,
        "head_sha": head_sha,
    }
    logger.info(
        "Set main branch for issue #%d: '%s' (PR #%d, SHA: %s)",
        issue_number,
        branch,
        pr_number,
        head_sha[:8] if head_sha else "none",
    )


def clear_issue_main_branch(issue_number: int) -> None:
    """Clear the main branch tracking for an issue (e.g., when issue is closed)."""
    _issue_main_branches.pop(issue_number, None)


def update_issue_main_branch_sha(issue_number: int, head_sha: str) -> None:
    """
    Update the HEAD SHA for an issue's main branch.

    Called after merging a child PR into the main branch so the next agent
    gets the correct (post-merge) commit SHA as its base_ref.

    Args:
        issue_number: GitHub issue number
        head_sha: New HEAD SHA after the child PR merge
    """
    if issue_number not in _issue_main_branches:
        logger.warning(
            "Cannot update HEAD SHA for issue #%d — no main branch set",
            issue_number,
        )
        return
    old_sha = _issue_main_branches[issue_number].get("head_sha", "")
    _issue_main_branches[issue_number]["head_sha"] = head_sha
    logger.info(
        "Updated HEAD SHA for issue #%d main branch '%s': %s → %s",
        issue_number,
        _issue_main_branches[issue_number].get("branch", ""),
        old_sha[:8] if old_sha else "none",
        head_sha[:8] if head_sha else "none",
    )


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
            metadata_section = f"""## Metadata

| Field | Value |
|-------|-------|
| Priority | {metadata.priority.value if metadata.priority else "P2"} |
| Size | {metadata.size.value if metadata.size else "M"} |
| Estimate | {metadata.estimate_hours}h |
| Start Date | {metadata.start_date or "TBD"} |
| Target Date | {metadata.target_date or "TBD"} |
| Labels | {labels_str} |

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
    ) -> bool:
        """
        Update the agent tracking table in the GitHub Issue body.

        Fetches the current issue body, updates the agent's state in the
        tracking table, and pushes the updated body back to GitHub.

        Args:
            ctx: Workflow context with issue info
            agent_name: Agent name (e.g. "speckit.specify")
            new_state: "active" or "done"

        Returns:
            True if the issue body was updated successfully
        """
        from src.services.agent_tracking import mark_agent_active, mark_agent_done

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
                updated_body = mark_agent_active(body, agent_name)
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
    def log_transition(
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
        config = ctx.config or get_workflow_config(ctx.project_id)
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

                # Add the sub-issue to the same GitHub Project as the parent
                sub_node_id = sub_issue.get("node_id", "")
                if sub_node_id and ctx.project_id:
                    try:
                        await self.github.add_issue_to_project(
                            access_token=ctx.access_token,
                            project_id=ctx.project_id,
                            issue_node_id=sub_node_id,
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

        body = self.format_issue_body(recommendation)

        # Append the agent pipeline tracking table to the issue body
        config = ctx.config or get_workflow_config(ctx.project_id)
        if config and config.agent_mappings:
            status_order = get_status_order(config)
            body = append_tracking_to_body(body, config.agent_mappings, status_order)
            logger.info("Appended agent pipeline tracking to issue body")

        issue = await self.github.create_issue(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            title=recommendation.title,
            body=body,
            labels=["ai-generated"],
        )

        ctx.issue_id = issue["node_id"]
        ctx.issue_number = issue["number"]
        ctx.issue_url = issue["html_url"]

        logger.info("Created issue #%d: %s", issue["number"], issue["html_url"])
        return issue

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
        config = ctx.config or get_workflow_config(ctx.project_id)
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
        self.log_transition(
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

        config = ctx.config or get_workflow_config(ctx.project_id)
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
            self.log_transition(
                ctx=ctx,
                from_status=config.status_backlog,
                to_status=config.status_ready,
                triggered_by=TriggeredBy.AUTOMATIC,
                success=True,
            )
        else:
            self.log_transition(
                ctx=ctx,
                from_status=config.status_backlog,
                to_status=config.status_ready,
                triggered_by=TriggeredBy.AUTOMATIC,
                success=False,
                error_message="Failed to update status",
            )

        return success

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

        Args:
            ctx: Workflow context with issue info
            status: Workflow status name (e.g., "Backlog", "Ready")
            agent_index: Index into the agent list for this status (default: 0 = first agent)

        Returns:
            True if agent assignment succeeded
        """
        config = ctx.config or get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        if ctx.issue_id is None:
            raise ValueError("issue_id required for agent assignment")
        if ctx.issue_number is None:
            raise ValueError("issue_number required for agent assignment")

        agents = _ci_get(config.agent_mappings, status, [])
        if not agents:
            logger.info("No agents configured for status '%s'", status)
            return True  # No agents to assign is not an error

        if agent_index >= len(agents):
            logger.info(
                "Agent index %d out of range for status '%s' (has %d agents)",
                agent_index,
                status,
                len(agents),
            )
            return True  # All agents already processed

        agent_name = (
            agents[agent_index].slug
            if hasattr(agents[agent_index], "slug")
            else str(agents[agent_index])
        )
        logger.info(
            "Assigning agent '%s' (index %d/%d) for status '%s' on issue #%s",
            agent_name,
            agent_index + 1,
            len(agents),
            status,
            ctx.issue_number,
        )

        # Determine the base branch for this agent
        #
        # Branching strategy (hierarchical PR model):
        #   - The FIRST agent uses base_ref="main":
        #       Creates branch "copilot/xxx" → PR targets "main"
        #       This PR's branch becomes the "main branch" for the issue.
        #   - ALL subsequent agents use the HEAD commit SHA of the main branch:
        #       base_ref=<commit_sha> → Copilot creates a CHILD branch from that commit
        #       The child PR targets the main branch (not "main")
        #       After the agent completes, the child PR is squash-merged into the
        #       main branch and the child branch is deleted.
        #
        # We pass the main PR's **branch name** (not a commit SHA) as baseRef
        # because GitHub's Copilot assignment API requires a valid ref name.
        # Copilot will create a new child branch from the HEAD of that branch
        # and open a PR targeting it.
        existing_pr = None
        base_ref = "main"
        current_head_sha = ""  # Track HEAD SHA at assignment time

        if ctx.issue_number:
            # Check if we already have a "main branch" stored for this issue
            main_branch_info = get_issue_main_branch(ctx.issue_number)

            if main_branch_info:
                # Subsequent agent — create a child branch from the main branch.
                main_branch = str(main_branch_info["branch"])
                main_pr_number = main_branch_info["pr_number"]

                # Fetch current PR details to capture the latest HEAD SHA
                # (used for tracking/audit purposes, NOT as baseRef)
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

                # Use the main PR's branch name as base_ref so Copilot creates
                # a child branch from it. The child PR will target this branch.
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

                # Pass existing_pr as informational context only — subsequent
                # agents create their own child PRs but benefit from knowing
                # about the main PR for context.
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
                        # Fetch full PR details to get commit SHA
                        pr_details = await self.github.get_pull_request(
                            access_token=ctx.access_token,
                            owner=ctx.repository_owner,
                            repo=ctx.repository_name,
                            pr_number=existing_pr["number"],
                        )
                        head_sha = ""
                        if pr_details and pr_details.get("last_commit", {}).get("sha"):
                            head_sha = pr_details["last_commit"]["sha"]

                        # Store this as the main branch for the issue
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

                        # Link the first PR to the GitHub Issue
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

        # ── Look up pre-created Sub-Issue for this agent ─────────────
        # Sub-issues are created upfront in create_all_sub_issues() so
        # the user can see the full scope immediately.  Here we look up
        # the existing sub-issue from the pipeline state, falling back to
        # the global sub-issue store which survives pipeline state resets.
        sub_issue_node_id = ctx.issue_id  # fallback: parent issue
        sub_issue_number = ctx.issue_number  # fallback: parent issue number
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
            logger.warning(
                "No pre-created sub-issue found for agent '%s' on issue #%d — "
                "falling back to parent issue",
                agent_name,
                ctx.issue_number,
            )

        # Fetch issue context for the agent's custom instructions.
        # Use the SUB-ISSUE data (not parent) so Copilot focuses only on
        # the sub-issue and doesn't create duplicate PRs for the parent.
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
                    "Prepared custom instructions for agent '%s' from issue #%d (length: %d chars, existing_pr: %s)",
                    agent_name,
                    instruction_issue_number,
                    len(custom_instructions),
                    f"#{existing_pr['number']}" if existing_pr else "None",
                )
            except Exception as e:
                logger.warning("Failed to fetch issue context for agent '%s': %s", agent_name, e)

        # Assign the agent with retry-with-backoff
        # GitHub's Copilot API can return transient errors, especially right after
        # a child PR merge. We retry up to 3 times with exponential backoff.
        import asyncio

        # ── Dedup guard ──────────────────────────────────────────────
        # If this exact agent+issue was already assigned recently (within
        # the grace period), skip the duplicate assignment.  This closes
        # race windows where multiple code-paths (polling steps, recovery,
        # status-transition) all converge on the same assignment.
        pending_key = f"{ctx.issue_number}:{agent_name}"
        try:
            from src.services.copilot_polling import (
                ASSIGNMENT_GRACE_PERIOD_SECONDS,
                _pending_agent_assignments,
                _recovery_last_attempt,
            )

            existing_ts = _pending_agent_assignments.get(pending_key)
            if existing_ts is not None:
                age = (datetime.utcnow() - existing_ts).total_seconds()
                if age < ASSIGNMENT_GRACE_PERIOD_SECONDS:
                    logger.warning(
                        "Skipping duplicate assignment of agent '%s' on issue #%d "
                        "(already assigned %.0fs ago, grace=%ds)",
                        agent_name,
                        ctx.issue_number,
                        age,
                        ASSIGNMENT_GRACE_PERIOD_SECONDS,
                    )
                    return True  # Treat as success — the original assignment is in flight

            # Pre-set recovery cooldown and pending flag BEFORE the assignment
            # API call. This prevents a race where the polling/recovery loop sees
            # the issue between the unassign and re-assign steps and fires a
            # duplicate assignment.
            _recovery_last_attempt[ctx.issue_number] = datetime.utcnow()
            _pending_agent_assignments[pending_key] = datetime.utcnow()
            logger.debug(
                "Pre-set recovery cooldown and pending flag for agent '%s' on issue #%d",
                agent_name,
                ctx.issue_number,
            )
        except ImportError:
            pass  # copilot_polling not available in tests

        max_retries = 3
        base_delay = 3  # seconds
        success = False

        for attempt in range(max_retries):
            logger.info(
                "Assigning agent '%s' to sub-issue #%s (parent #%s) with base_ref='%s' (attempt %d/%d)",
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
            )

            if success:
                break

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)  # 3s, 6s, 12s
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

            # Mark agent as 🔄 Active in the issue body tracking table
            await self._update_agent_tracking_state(ctx, agent_name, "active")

            # Mark the sub-issue as "in progress" (add label, ensure open)
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

                # Update the sub-issue's project board Status to "In Progress"
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
                        "Failed to update sub-issue #%d project board status: %s",
                        sub_issue_number,
                        e,
                    )

            # Refresh recovery cooldown timestamp now that assignment succeeded
            try:
                from src.services.copilot_polling import (
                    _recovery_last_attempt,
                )

                _recovery_last_attempt[ctx.issue_number] = datetime.utcnow()
            except ImportError:
                pass
        else:
            logger.warning(
                "Failed to assign agent '%s' to issue #%s",
                agent_name,
                ctx.issue_number,
            )
            # Clear pending flag so recovery can retry later
            try:
                from src.services.copilot_polling import (
                    _pending_agent_assignments,
                )

                _pending_agent_assignments.pop(pending_key, None)
            except ImportError:
                pass

        # Create / update pipeline state
        # Capture the HEAD SHA at assignment time for commit-based completion detection
        assigned_sha = current_head_sha or ""
        if not assigned_sha and ctx.issue_number:
            main_branch_info = get_issue_main_branch(ctx.issue_number)
            if main_branch_info and main_branch_info.get("head_sha"):
                assigned_sha = main_branch_info.get("head_sha", "")

        # Preserve existing sub-issue mappings from previous agents
        existing_pipeline = get_pipeline_state(ctx.issue_number)
        existing_sub_issues = existing_pipeline.agent_sub_issues if existing_pipeline else {}

        # Add the new agent's sub-issue info
        agent_sub_issues = dict(existing_sub_issues)
        if sub_issue_info:
            agent_sub_issues[agent_name] = sub_issue_info

        pipeline_state = PipelineState(
            issue_number=ctx.issue_number,
            project_id=ctx.project_id,
            status=status,
            agents=[a.slug if hasattr(a, "slug") else str(a) for a in agents],
            current_agent_index=agent_index,
            completed_agents=[
                a.slug if hasattr(a, "slug") else str(a) for a in agents[:agent_index]
            ],
            started_at=datetime.utcnow(),
            error=None if success else f"Failed to assign agent '{agent_name}'",
            agent_assigned_sha=assigned_sha,
            agent_sub_issues=agent_sub_issues,
        )
        set_pipeline_state(ctx.issue_number, pipeline_state)

        # Log the transition
        self.log_transition(
            ctx=ctx,
            from_status=status,
            to_status=status,
            triggered_by=TriggeredBy.AUTOMATIC,
            success=success,
            assigned_user=f"copilot:{agent_name}" if success else None,
            error_message=None if success else f"Failed to assign agent '{agent_name}'",
        )

        return success

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

        config = ctx.config or get_workflow_config(ctx.project_id)
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
            self.log_transition(
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
        self.log_transition(
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

        config = ctx.config or get_workflow_config(ctx.project_id)
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

        # Update status to In Review
        status_success = await self.github.update_item_status_by_name(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            item_id=ctx.project_item_id,
            status_name=config.status_in_review,
        )

        if not status_success:
            self.log_transition(
                ctx=ctx,
                from_status=config.status_in_progress,
                to_status=config.status_in_review,
                triggered_by=TriggeredBy.DETECTION,
                success=False,
                error_message="Failed to update status to In Review",
            )
            return False

        # Determine reviewer (use configured or fall back to repo owner)
        reviewer = config.review_assignee
        if not reviewer:
            reviewer = await self.github.get_repository_owner(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
            )

        # Assign reviewer
        assign_success = await self.github.assign_issue(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            issue_number=ctx.issue_number,
            assignees=[reviewer] if reviewer else [],
        )

        ctx.current_state = WorkflowState.IN_REVIEW
        self.log_transition(
            ctx=ctx,
            from_status=config.status_in_progress,
            to_status=config.status_in_review,
            triggered_by=TriggeredBy.DETECTION,
            success=True,
            assigned_user=reviewer if assign_success else None,
        )

        if assign_success:
            logger.info(
                "Issue #%d transitioned to In Review, assigned to %s, PR #%d ready",
                ctx.issue_number,
                reviewer,
                completed_pr["number"],
            )
        else:
            logger.warning(
                "Issue #%d transitioned to In Review but failed to assign %s",
                ctx.issue_number,
                reviewer,
            )

        return True

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

        config = ctx.config or get_workflow_config(ctx.project_id)
        if not config:
            logger.warning("No workflow config for project %s", ctx.project_id)
            return False

        logger.info("Issue %s complete, transitioning to In Review", ctx.issue_id)

        # Update status to In Review
        status_success = await self.github.update_item_status_by_name(
            access_token=ctx.access_token,
            project_id=ctx.project_id,
            item_id=ctx.project_item_id,
            status_name=config.status_in_review,
        )

        if not status_success:
            self.log_transition(
                ctx=ctx,
                from_status=config.status_in_progress,
                to_status=config.status_in_review,
                triggered_by=TriggeredBy.DETECTION,
                success=False,
                error_message="Failed to update status to In Review",
            )
            return False

        # Determine reviewer (use configured or fall back to repo owner)
        reviewer = config.review_assignee
        if not reviewer:
            reviewer = await self.github.get_repository_owner(
                access_token=ctx.access_token,
                owner=ctx.repository_owner,
                repo=ctx.repository_name,
            )

        # Assign reviewer
        assign_success = await self.github.assign_issue(
            access_token=ctx.access_token,
            owner=ctx.repository_owner,
            repo=ctx.repository_name,
            issue_number=ctx.issue_number,
            assignees=[reviewer] if reviewer else [],
        )

        ctx.current_state = WorkflowState.IN_REVIEW
        self.log_transition(
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

        return True

    # ──────────────────────────────────────────────────────────────────
    # FULL WORKFLOW: Execute from confirmation to Ready (T022+T023+T031)
    # ──────────────────────────────────────────────────────────────────
    async def execute_full_workflow(
        self, ctx: WorkflowContext, recommendation: IssueRecommendation
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

            # Step 3: Assign the first agent for Backlog status
            # If Backlog has no agents, use pass-through to find next actionable status (T028)
            config = ctx.config or get_workflow_config(ctx.project_id)
            status_name = config.status_backlog if config else "Backlog"

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

            # Pre-register the recovery cooldown BEFORE calling assign_agent_for_status.
            # This prevents the polling/recovery loop from racing during sub-issue
            # creation. NOTE: We only set _recovery_last_attempt (NOT
            # _pending_agent_assignments) because the latter would cause the dedup
            # guard inside assign_agent_for_status to skip the actual assignment.
            if ctx.issue_number:
                try:
                    from src.services.copilot_polling import (
                        _recovery_last_attempt,
                    )

                    _recovery_last_attempt[ctx.issue_number] = datetime.utcnow()
                    logger.debug(
                        "Set recovery cooldown for issue #%d before sub-issue creation",
                        ctx.issue_number,
                    )
                except ImportError:
                    pass

            # Create all sub-issues upfront so the user can see the full pipeline
            agent_sub_issues = await self.create_all_sub_issues(ctx)
            if agent_sub_issues and ctx.issue_number is not None:
                # Store in pipeline state so assign_agent_for_status can look them up
                pipeline_state = PipelineState(
                    issue_number=ctx.issue_number,
                    project_id=ctx.project_id,
                    status=status_name,
                    agents=[],  # Will be set properly by assign_agent_for_status
                    agent_sub_issues=agent_sub_issues,
                )
                set_pipeline_state(ctx.issue_number, pipeline_state)
                logger.info(
                    "Pre-created %d sub-issues for issue #%d",
                    len(agent_sub_issues),
                    ctx.issue_number,
                )

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

            self.log_transition(
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
