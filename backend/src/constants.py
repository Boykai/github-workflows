"""Application-wide constants."""

# Default status columns for projects without custom columns
DEFAULT_STATUS_COLUMNS = ["Todo", "In Progress", "Done"]

# Cache key prefixes
CACHE_PREFIX_PROJECTS = "projects:user"
CACHE_PREFIX_PROJECT_ITEMS = "project:items"

# Session cookie name
SESSION_COOKIE_NAME = "session_id"


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
# Workflow Status Names
# ──────────────────────────────────────────────────────────────────────────────


class StatusNames:
    """Standard workflow status column names."""

    BACKLOG = "Backlog"
    READY = "Ready"
    IN_PROGRESS = "In Progress"
    IN_REVIEW = "In Review"
    DONE = "Done"


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
    "copilot-review": "Copilot Review",
    "copilot": "GitHub Copilot",
}


# ──────────────────────────────────────────────────────────────────────────────
# Cache Key Helpers
# ──────────────────────────────────────────────────────────────────────────────


def cache_key_issue_pr(issue_number: int, pr_number: int) -> str:
    """Generate cache key for processed issue PR."""
    return f"{issue_number}:{pr_number}"


def cache_key_agent_output(issue_number: int, agent: str, pr_number: int) -> str:
    """Generate cache key for posted agent outputs."""
    return f"{issue_number}:{agent}:{pr_number}"


def cache_key_review_requested(issue_number: int) -> str:
    """Generate cache key for Copilot review request tracking."""
    return f"copilot_review_requested:{issue_number}"


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
    "good first issue",
    "help wanted",
    # Domain labels
    "security",
    "performance",
    "accessibility",
    "ux",
]
