"""Module-level mutable state and constants for the polling service."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from src.logging_utils import get_logger
from src.utils import BoundedDict, BoundedSet

_logger = get_logger(__name__)


@dataclass
class PollingState:
    """State tracking for the polling service."""

    is_running: bool = False
    last_poll_time: datetime | None = None
    poll_count: int = 0
    errors_count: int = 0
    last_error: str | None = None
    processed_issues: BoundedDict[int, datetime] = field(
        default_factory=lambda: BoundedDict(maxlen=2000)
    )


@dataclass
class MonitoredProject:
    """Metadata for a project registered for multi-project polling."""

    project_id: str
    owner: str
    repo: str
    access_token: str
    registered_at: datetime
    last_polled: datetime | None = None


# ── Multi-project registry ──
# Maps project_id → MonitoredProject.  The main polling loop iterates
# over all registered projects each cycle (round-robin).  Projects are
# registered on pipeline creation and auto-discovered on startup.
_monitored_projects: dict[str, MonitoredProject] = {}


def register_project(
    project_id: str,
    owner: str,
    repo: str,
    access_token: str,
) -> bool:
    """Register a project for multi-project polling.

    Returns ``True`` if newly registered, ``False`` if already present
    (access_token/owner/repo are updated in-place either way).
    """
    from src.utils import utcnow

    existing = _monitored_projects.get(project_id)
    if existing is not None:
        existing.access_token = access_token
        existing.owner = owner
        existing.repo = repo
        return False

    _monitored_projects[project_id] = MonitoredProject(
        project_id=project_id,
        owner=owner,
        repo=repo,
        access_token=access_token,
        registered_at=utcnow(),
    )
    _logger.info(
        "Registered project %s (%s/%s) for multi-project monitoring",
        project_id,
        owner,
        repo,
    )
    return True


def unregister_project(project_id: str) -> bool:
    """Remove a project from multi-project polling.

    Returns ``True`` if removed, ``False`` if not found.
    """
    removed = _monitored_projects.pop(project_id, None)
    if removed is not None:
        _logger.info(
            "Unregistered project %s (%s/%s) from multi-project monitoring",
            project_id,
            removed.owner,
            removed.repo,
        )
        return True
    return False


def get_monitored_projects() -> list[MonitoredProject]:
    """Return all registered projects (snapshot)."""
    return list(_monitored_projects.values())


# Global polling state
_polling_state = PollingState()

# Reference to the current polling asyncio.Task so we can cancel it
# before starting a new one (prevents concurrent loops).
_polling_task: asyncio.Task | None = None

# Secondary polling tasks for new-repo / external-repo app pipelines.
# Keyed by project_id so at most one loop runs per project.
# Each task auto-stops when the pipeline completes.
_app_polling_tasks: dict[str, asyncio.Task] = {}

# Track issues we've already processed to avoid duplicate updates
_processed_issue_prs: BoundedSet[str] = BoundedSet(maxlen=1000)  # "issue_number:pr_number"

# Deduplication cache for ensure_copilot_review_requested calls.
# Keys have the format produced by cache_key_review_requested():
# "{project_id}:copilot_review_requested:{issue_number}"
# Kept separate from _processed_issue_prs to avoid mixing key namespaces
# and to allow independent size tuning.
_review_requested_cache: BoundedSet[str] = BoundedSet(maxlen=500)

# Track issues where we've already posted agent outputs to avoid duplicates
_posted_agent_outputs: BoundedSet[str] = BoundedSet(
    maxlen=500
)  # "issue_number:agent_name:pr_number"

# Track which child PRs have been claimed/attributed to an agent
# This prevents subsequent agents from re-using already-completed child PRs
_claimed_child_prs: BoundedSet[str] = BoundedSet(maxlen=500)  # "issue_number:pr_number:agent_name"

# Track agents that we've already assigned (pending Copilot to start working).
# Maps "issue_number:agent_name" → datetime of assignment.
# This prevents the polling loop from re-assigning the same agent every cycle
# before Copilot has had time to create its child PR.
_pending_agent_assignments: BoundedDict[str, datetime] = BoundedDict(
    maxlen=500
)  # key -> assignment timestamp

# Grace period (seconds) after assigning an agent before any recovery /
# "agent never assigned" logic is allowed to fire for the same issue.
# Copilot typically takes 30-90s to create a WIP PR after assignment.
ASSIGNMENT_GRACE_PERIOD_SECONDS = 120

# Track PRs that OUR system converted from draft → ready.
# This prevents _check_main_pr_completion Signal 1 from misinterpreting
# a non-draft PR as agent completion when we ourselves marked it ready.
_system_marked_ready_prs: BoundedSet[int] = BoundedSet(maxlen=500)  # pr_number

# Track when a Copilot review was first detected on a PR.  The pipeline
# requires the review to be confirmed on TWO consecutive poll cycles before
# marking copilot-review as done.  This eliminates false positives from
# transient GitHub API race conditions where a review object briefly
# appears before being fully committed.
_copilot_review_first_detected: BoundedDict[int, datetime] = BoundedDict(
    maxlen=200
)  # issue_number -> first detection timestamp
COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS: float = (
    30.0  # min seconds between first detection and confirmation
)

# Buffer (seconds) added to the Solune request timestamp when filtering
# reviews.  Any Copilot review submitted within this window after the
# request is treated as a possible in-flight auto-triggered review and
# ignored.  This guards against the race where GitHub's auto-review
# completes slightly after Solune records its request timestamp.
COPILOT_REVIEW_REQUEST_BUFFER_SECONDS: float = 120.0

# Track when Solune explicitly requested a Copilot code review for each
# parent issue.  Records the UTC timestamp of the request so that only
# reviews submitted *after* the request (+ buffer) are counted — any
# review that GitHub.com auto-triggered before Solune's request is
# ignored.  The orchestrator records the timestamp when it assigns
# copilot-review, and the self-healing path in _check_copilot_review_done
# re-records it after a server restart.
_copilot_review_requested_at: BoundedDict[int, datetime] = BoundedDict(
    maxlen=200
)  # parent_issue_number -> UTC timestamp of review request

# Recovery cooldown: tracks when we last attempted recovery for each issue.
# Prevents re-assigning an agent every poll cycle — gives Copilot time to start.
_recovery_last_attempt: BoundedDict[int, datetime] = BoundedDict(
    maxlen=200
)  # issue_number -> last attempt time
RECOVERY_COOLDOWN_SECONDS = 300  # 5 minutes between recovery attempts per issue

# Merge failure counter: tracks consecutive merge failures per issue.
# When the count exceeds MAX_MERGE_RETRIES the pipeline skips the merge
# and advances, posting a warning comment on the issue.
_merge_failure_counts: BoundedDict[int, int] = BoundedDict(
    maxlen=200
)  # issue_number -> consecutive failure count
MAX_MERGE_RETRIES: int = 3

# Delay (seconds) after merging / before status updates to let GitHub sync.
POST_ACTION_DELAY_SECONDS: float = 2.0

# ── Rate-limit-aware polling thresholds ──
# When remaining quota drops below RATE_LIMIT_PAUSE_THRESHOLD, the polling
# loop sleeps until the reset window instead of burning through the budget.
RATE_LIMIT_PAUSE_THRESHOLD: int = 50

# When remaining quota drops below RATE_LIMIT_SLOW_THRESHOLD, the polling
# loop doubles its interval to conserve budget.
RATE_LIMIT_SLOW_THRESHOLD: int = 200

# When remaining quota drops below RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD, the
# polling loop skips the most expensive steps (Step 0: agent output posting)
# to avoid exhausting the budget on a single cycle.
RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD: int = 100
# ── Activity-based adaptive polling ──
# Counter for consecutive polls with no state changes. When no activity is
# detected (no PRs merged, no statuses advanced, no agent outputs posted),
# the effective interval doubles each cycle up to MAX_POLL_INTERVAL_SECONDS.
# Resets to 0 when any state change occurs.
_consecutive_idle_polls: int = 0
MAX_POLL_INTERVAL_SECONDS: int = 300  # 5 minutes cap

# ── Phase 8: Adaptive polling tier configuration ──
# Defines the polling tiers and thresholds for activity-based interval adjustment.
# Activity score is computed from a sliding window of recent poll results.
POLLING_TIER_HIGH_INTERVAL: int = 3  # seconds — fast polling during active periods
POLLING_TIER_MEDIUM_INTERVAL: int = 10  # seconds — moderate polling
POLLING_TIER_LOW_INTERVAL: int = 30  # seconds — slow polling during idle
POLLING_TIER_BACKOFF_MAX_INTERVAL: int = 60  # seconds — max backoff on errors

# Activity score thresholds for tier transitions (0.0-1.0)
ACTIVITY_SCORE_HIGH_THRESHOLD: float = 0.6  # score > threshold → high tier
ACTIVITY_SCORE_MEDIUM_THRESHOLD: float = 0.2  # score > threshold → medium tier

# Sliding window size for change detection
ACTIVITY_WINDOW_SIZE: int = 5

# Sliding window of recent poll change-detection results (True = changes detected)
_activity_window: deque[bool] = deque(maxlen=ACTIVITY_WINDOW_SIZE)

# Current adaptive polling tier
_adaptive_tier: str = "medium"  # "high" | "medium" | "low" | "backoff"

# Consecutive poll failure counter for exponential backoff
_consecutive_poll_failures: int = 0
