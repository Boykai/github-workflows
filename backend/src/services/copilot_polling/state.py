"""
Polling state & module-level variables for the Copilot polling service.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PollingState:
    """State tracking for the polling service."""

    is_running: bool = False
    last_poll_time: datetime | None = None
    poll_count: int = 0
    errors_count: int = 0
    last_error: str | None = None
    processed_issues: dict[int, datetime] = field(default_factory=dict)


# Global polling state
_polling_state = PollingState()

# Reference to the current polling asyncio.Task so we can cancel it
# before starting a new one (prevents concurrent loops).
_polling_task: asyncio.Task | None = None

# Track issues we've already processed to avoid duplicate updates
_processed_issue_prs: set[str] = set()  # "issue_number:pr_number"

# Track issues where we've already posted agent outputs to avoid duplicates
_posted_agent_outputs: set[str] = set()  # "issue_number:agent_name:pr_number"

# Track which child PRs have been claimed/attributed to an agent
# This prevents subsequent agents from re-using already-completed child PRs
_claimed_child_prs: set[str] = set()  # "issue_number:pr_number:agent_name"

# Track agents that we've already assigned (pending Copilot to start working).
# Maps "issue_number:agent_name" → datetime of assignment.
# This prevents the polling loop from re-assigning the same agent every cycle
# before Copilot has had time to create its child PR.
_pending_agent_assignments: dict[str, datetime] = {}  # key -> assignment timestamp

# Grace period (seconds) after assigning an agent before any recovery /
# "agent never assigned" logic is allowed to fire for the same issue.
# Copilot typically takes 30-90s to create a WIP PR after assignment.
ASSIGNMENT_GRACE_PERIOD_SECONDS = 120

# Track PRs that OUR system converted from draft → ready.
# This prevents _check_main_pr_completion Signal 1 from misinterpreting
# a non-draft PR as agent completion when we ourselves marked it ready.
_system_marked_ready_prs: set[int] = set()  # pr_number

# Recovery cooldown: tracks when we last attempted recovery for each issue.
# Prevents re-assigning an agent every poll cycle — gives Copilot time to start.
_recovery_last_attempt: dict[int, datetime] = {}  # issue_number -> last attempt time
RECOVERY_COOLDOWN_SECONDS = 300  # 5 minutes between recovery attempts per issue
