"""Module-level mutable state and constants for the polling service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

from src.utils import BoundedDict, BoundedSet


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
