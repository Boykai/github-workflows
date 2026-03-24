"""Application-wide constants."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.services.github_projects.service import GitHubProjectsService

# ──────────────────────────────────────────────────────────────────────────────
# Workflow Status Names
# ──────────────────────────────────────────────────────────────────────────────


class StatusNames:
    """Standard workflow status column names."""

    BACKLOG = "Backlog"
    READY = "Ready"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"


# Default status columns for projects without custom columns
DEFAULT_STATUS_COLUMNS = [StatusNames.BACKLOG, StatusNames.IN_PROGRESS, StatusNames.DONE]

# Default status name assigned to newly created items in GitHub Projects.
# GitHub Projects uses "Todo" as the initial status column name.
DEFAULT_STATUS_BACKLOG = "Todo"

# Cache key prefixes
CACHE_PREFIX_PROJECTS = "projects:user"
CACHE_PREFIX_PROJECT_ITEMS = "project:items"
CACHE_PREFIX_SUB_ISSUES = "sub_issues"
CACHE_PREFIX_REPO_AGENTS = "repo:agents"

# Session cookie name
SESSION_COOKIE_NAME = "session_id"


# ──────────────────────────────────────────────────────────────────────────────
# GitHub API Limits
# ──────────────────────────────────────────────────────────────────────────────

GITHUB_ISSUE_BODY_MAX_LENGTH = 65_536

# ──────────────────────────────────────────────────────────────────────────────
# Notification Event Types
# ──────────────────────────────────────────────────────────────────────────────

NOTIFICATION_EVENT_TYPES = [
    "task_status_change",
    "agent_completion",
    "new_recommendation",
    "chat_mention",
]


# ──────────────────────────────────────────────────────────────────────────────
# Agent Configuration
# ──────────────────────────────────────────────────────────────────────────────


# Known .md output files for specific agents.
# Used to label expected vs. extra .md files when posting PR outputs as issue comments.
# Any agent can produce output files — this mapping is NOT a gatekeeper.
# Agents not listed here (or with an empty list) still get full PR completion
# detection, output posting for any .md files found, and Done! marker posting.
AGENT_OUTPUT_FILES: dict[str, list[str]] = {
    "speckit.specify": ["spec.md"],
    "speckit.plan": ["plan.md"],
    "speckit.tasks": ["tasks.md"],
}

# Default agent mappings for each status (Spec Kit pipeline)
DEFAULT_AGENT_MAPPINGS: dict[str, list[str]] = {
    StatusNames.BACKLOG: ["speckit.specify"],
    StatusNames.READY: ["speckit.plan", "speckit.tasks"],
    StatusNames.IN_PROGRESS: ["speckit.implement"],
    StatusNames.IN_REVIEW: ["copilot-review"],
}

# Human-readable display names for known agents
AGENT_DISPLAY_NAMES: dict[str, str] = {
    "speckit.specify": "Spec Kit - Specify",
    "speckit.plan": "Spec Kit - Plan",
    "speckit.tasks": "Spec Kit - Tasks",
    "speckit.implement": "Spec Kit - Implement",
    "speckit.analyze": "Spec Kit - Analyze",
    "copilot-review": "Copilot Review",
    "copilot": "GitHub Copilot",
    "human": "Human",
}


# ──────────────────────────────────────────────────────────────────────────────
# Cache Key Helpers
# ──────────────────────────────────────────────────────────────────────────────


def cache_key_issue_pr(
    issue_number: int,
    pr_number: int,
    project_id: str = "",
) -> str:
    """Generate cache key for processed issue PR.

    Scoped to *project_id* to prevent collisions across projects with
    the same issue/PR numbers.
    """
    if not project_id:
        warnings.warn(
            "cache_key_issue_pr() called without project_id — cache key is unscoped "
            "and may collide across projects. Pass project_id explicitly.",
            DeprecationWarning,
            stacklevel=2,
        )
    prefix = f"{project_id}:" if project_id else ""
    return f"{prefix}{issue_number}:{pr_number}"


def cache_key_agent_output(
    issue_number: int,
    agent: str,
    pr_number: int,
    project_id: str = "",
) -> str:
    """Generate cache key for posted agent outputs."""
    if not project_id:
        warnings.warn(
            "cache_key_agent_output() called without project_id — cache key is unscoped "
            "and may collide across projects. Pass project_id explicitly.",
            DeprecationWarning,
            stacklevel=2,
        )
    prefix = f"{project_id}:" if project_id else ""
    return f"{prefix}{issue_number}:{agent}:{pr_number}"


def cache_key_review_requested(issue_number: int, project_id: str = "") -> str:
    """Generate cache key for Copilot review request tracking."""
    if not project_id:
        warnings.warn(
            "cache_key_review_requested() called without project_id — cache key is unscoped "
            "and may collide across projects. Pass project_id explicitly.",
            DeprecationWarning,
            stacklevel=2,
        )
    prefix = f"{project_id}:" if project_id else ""
    return f"{prefix}copilot_review_requested:{issue_number}"


# ──────────────────────────────────────────────────────────────────────────────
# Issue Labels  (single source of truth)
# ──────────────────────────────────────────────────────────────────────────────
# Canonical list of allowed issue labels.  IssueLabel enum in models/chat.py
# is derived from this list — do NOT duplicate or redefine these values.

LABELS: list[str] = [
    # Type labels (pick ONE primary type)
    "feature",
    "bug",
    "enhancement",
    "refactor",
    "documentation",
    "testing",
    "infrastructure",
    # Scope labels (pick all that apply)
    "frontend",
    "backend",
    "database",
    "api",
    # Status labels
    "ai-generated",
    "sub-issue",
    "good first issue",
    "help wanted",
    # Domain labels
    "security",
    "performance",
    "accessibility",
    "ux",
    # Pipeline state labels (dynamic prefixed labels are also valid)
    "active",
    "stalled",
]


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline State Labels
# ──────────────────────────────────────────────────────────────────────────────
# Labels used for fast-path pipeline state detection from the GraphQL board
# query.  These supplement (never replace) the Markdown tracking table.

PIPELINE_LABEL_PREFIX: str = "pipeline:"
AGENT_LABEL_PREFIX: str = "agent:"
SUB_ISSUE_LABEL: str = "sub-issue"
ACTIVE_LABEL: str = "active"
STALLED_LABEL: str = "stalled"

# Pre-creation colours (hex without '#')
PIPELINE_LABEL_COLOR: str = "0052cc"
AGENT_LABEL_COLOR: str = "7057ff"
ACTIVE_LABEL_COLOR: str = "0e8a16"
STALLED_LABEL_COLOR: str = "d73a4a"


# ── Parsing: label string → extracted value ──────────────────────────────────


def extract_pipeline_config(label_name: str) -> str | None:
    """Return the config name from a ``pipeline:<config>`` label, or None."""
    if label_name.startswith(PIPELINE_LABEL_PREFIX):
        return label_name[len(PIPELINE_LABEL_PREFIX) :]
    return None


def extract_agent_slug(label_name: str) -> str | None:
    """Return the agent slug from an ``agent:<slug>`` label, or None."""
    if label_name.startswith(AGENT_LABEL_PREFIX):
        return label_name[len(AGENT_LABEL_PREFIX) :]
    return None


# ── Building: value → label string ───────────────────────────────────────────


def build_pipeline_label(config_name: str) -> str:
    """Build a ``pipeline:<config>`` label string."""
    return f"{PIPELINE_LABEL_PREFIX}{config_name}"


def build_agent_label(agent_slug: str) -> str:
    """Build an ``agent:<slug>`` label string."""
    return f"{AGENT_LABEL_PREFIX}{agent_slug}"


# ── Querying: label list → extracted value ───────────────────────────────────


def _label_name(label: object) -> str:
    """Extract the name from a label that may be a dict or an object."""
    if isinstance(label, dict):
        return label.get("name", "")
    return getattr(label, "name", "")


def find_pipeline_label(labels: list) -> str | None:
    """Return the pipeline config name from the first ``pipeline:*`` label."""
    for label in labels:
        name = _label_name(label)
        config = extract_pipeline_config(name)
        if config is not None:
            return config
    return None


def find_agent_label(labels: list) -> str | None:
    """Return the agent slug from the first ``agent:*`` label."""
    for label in labels:
        name = _label_name(label)
        slug = extract_agent_slug(name)
        if slug is not None:
            return slug
    return None


def has_stalled_label(labels: list) -> bool:
    """Return True if any label in the list is the ``stalled`` label."""
    for label in labels:
        if _label_name(label) == STALLED_LABEL:
            return True
    return False


async def ensure_pipeline_labels_exist(
    access_token: str,
    owner: str,
    repo: str,
    github_service: GitHubProjectsService | None = None,
) -> None:
    """Pre-create fixed pipeline labels with correct colours.

    Creates ``active`` (green) and ``stalled`` (red).  Dynamic
    ``pipeline:*`` and ``agent:*`` labels are created on first use by
    the GitHub ``POST /labels`` endpoint embedded in ``update_issue_state``.

    Idempotent — 422 (already exists) is silently ignored.
    """
    if github_service is None:
        from src.services.github_projects import github_projects_service

        github_service = github_projects_service

    _FIXED_LABELS = [
        (ACTIVE_LABEL, ACTIVE_LABEL_COLOR, "Marks the active agent sub-issue"),
        (STALLED_LABEL, STALLED_LABEL_COLOR, "Pipeline is stalled and needs recovery"),
    ]

    try:
        for name, color, description in _FIXED_LABELS:
            try:
                resp = await github_service.rest_request(
                    access_token,
                    "POST",
                    f"/repos/{owner}/{repo}/labels",
                    json={"name": name, "color": color, "description": description},
                )
                if resp.status_code == 422:
                    pass  # already exists — idempotent
                elif resp.status_code >= 400:
                    from src.logging_utils import get_logger

                    get_logger(__name__).warning(
                        "Failed to pre-create label '%s': %d %s",
                        name,
                        resp.status_code,
                        resp.text,
                    )
            except Exception:
                from src.logging_utils import get_logger

                get_logger(__name__).warning("Failed to pre-create label '%s'", name, exc_info=True)
    except Exception:
        from src.logging_utils import get_logger

        get_logger(__name__).warning("Failed to pre-create pipeline labels", exc_info=True)
