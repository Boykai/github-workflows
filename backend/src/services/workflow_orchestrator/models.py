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


class MainBranchInfo(TypedDict):
    """Typed info for an issue's main PR branch."""

    branch: str
    pr_number: int
    head_sha: str  # Commit SHA of the branch head (needed for baseRef)
