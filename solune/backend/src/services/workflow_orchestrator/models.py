"""Shared data classes and pure helpers for the workflow orchestrator package."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TypedDict

from src.models.workflow import WorkflowConfiguration


def _ci_get(mappings: dict, key: str, default=None):
    """Case-insensitive dict lookup for status names."""
    if key in mappings:
        return mappings[key]
    key_lower = key.lower()
    for k, v in mappings.items():
        if k.lower() == key_lower:
            return v
    return default if default is not None else []


def get_stage_execution_mode(config: WorkflowConfiguration, status: str) -> str:
    """Return the execution mode for a given status. Defaults to 'sequential'."""
    modes = getattr(config, "stage_execution_modes", {})
    if not modes:
        return "sequential"
    # Case-insensitive lookup
    if status in modes:
        return modes[status]
    status_lower = status.lower()
    for k, v in modes.items():
        if k.lower() == status_lower:
            return v
    return "sequential"


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
    selected_pipeline_id: str | None = None
    issue_id: str | None = None
    issue_number: int | None = None
    issue_url: str | None = None
    project_item_id: str | None = None
    current_state: WorkflowState = WorkflowState.ANALYZING
    config: WorkflowConfiguration | None = None
    # User's effective chat AI model from settings — used for app chat responses.
    user_chat_model: str = ""
    # User's effective agent AI model from settings — used as Tier 2 fallback in
    # agent model resolution when the pipeline config does not provide a
    # non-Auto model.  Empty string means no user preference has been supplied
    # and the hardcoded default is used instead.
    user_agent_model: str = ""


@dataclass
class PipelineGroupInfo:
    """Runtime tracking of an execution group within a pipeline status."""

    group_id: str
    execution_mode: str = "sequential"
    agents: list[str] = field(default_factory=list)
    agent_statuses: dict[str, str] = field(default_factory=dict)


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
    # Preserve original transition target when Copilot moves an issue
    # to "In Progress" before the pipeline agents for the original
    # status have finished.  Without these, the correct target is lost
    # on the next poll cycle and the pipeline jumps straight to In Review.
    original_status: str | None = None
    target_status: str | None = None
    # Parallel execution support
    execution_mode: str = "sequential"
    parallel_agent_statuses: dict[str, str] = field(default_factory=dict)
    failed_agents: list[str] = field(default_factory=list)
    # Group-aware execution support
    groups: list[PipelineGroupInfo] = field(default_factory=list)
    current_group_index: int = 0
    current_agent_index_in_group: int = 0
    # Queue mode: True when pipeline is waiting for another to complete
    queued: bool = False
    # Phase 8: Concurrent pipeline execution tracking
    concurrent_group_id: str | None = None  # Links concurrent sibling executions
    is_isolated: bool = True  # Fault isolation flag for concurrent pipelines
    recovered_at: datetime | None = None  # Timestamp of label-driven state recovery
    # Auto merge: True when pipeline should auto-squash-merge parent PR on completion
    auto_merge: bool = False

    @property
    def current_agent(self) -> str | None:
        """Get the currently active agent, or None if pipeline is complete."""
        if self.groups:
            # Skip empty groups to avoid stalling the pipeline
            idx = self.current_group_index
            while idx < len(self.groups):
                group = self.groups[idx]
                if group.agents:
                    if self.current_agent_index_in_group < len(group.agents):
                        return group.agents[self.current_agent_index_in_group]
                    break
                idx += 1
            return None
        # Flat fallback (existing behavior)
        if self.current_agent_index < len(self.agents):
            return self.agents[self.current_agent_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Check if all agents in the pipeline have completed."""
        if self.groups:
            # Skip empty groups
            idx = self.current_group_index
            while idx < len(self.groups) and not self.groups[idx].agents:
                idx += 1
            if idx >= len(self.groups):
                return True
            group = self.groups[idx]
            if group.execution_mode == "parallel":
                # Ensure all agents in the group are accounted for
                if len(group.agent_statuses) < len(group.agents):
                    return False
                return all(s in ("completed", "failed") for s in group.agent_statuses.values())
            return False
        # Flat fallback (existing behavior)
        if self.execution_mode == "parallel" and self.parallel_agent_statuses:
            return all(s in ("completed", "failed") for s in self.parallel_agent_statuses.values())
        return self.current_agent_index >= len(self.agents)

    @property
    def is_parallel_stage_failed(self) -> bool:
        """Check if any agent in a parallel stage has failed."""
        return len(self.failed_agents) > 0

    @property
    def next_agent(self) -> str | None:
        """Get the next agent after the current one, or None if last."""
        next_idx = self.current_agent_index + 1
        if next_idx < len(self.agents):
            return self.agents[next_idx]
        return None


class MainBranchInfo(TypedDict):
    """Typed info for an issue's main PR branch."""

    branch: str
    pr_number: int
    head_sha: str  # Commit SHA of the branch head (needed for baseRef)
