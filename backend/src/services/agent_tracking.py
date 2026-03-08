"""
Agent Tracking via GitHub Issue Body Markdown

Appends a tracking section to each GitHub Issue body that shows the full
agent pipeline and each agent's status.  The polling loop reads this section
(plus the last issue comment) to decide what to do next — no fragile
in-memory state required.

Markdown format appended to the issue body:

    ---

    ## 🤖 Agents Pipelines

    | # | Status | Agent | Model | State |
    |---|--------|-------|-------|-------|
    | 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |
    | 2 | Ready | `speckit.plan` | claude-3-5-sonnet | ✅ Done |
    | 3 | Ready | `speckit.tasks` | TBD | 🔄 Active |
    | 4 | In Progress | `speckit.implement` | gpt-4o | ⏳ Pending |

State values:
    ⏳ Pending   — not yet started
    🔄 Active    — currently assigned to Copilot
    ✅ Done      — "<agent>: Done!" comment posted
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.agent import AgentAssignment

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

TRACKING_HEADER = "## 🤖 Agents Pipelines"
TRACKING_SEPARATOR = "---"

STATE_PENDING = "⏳ Pending"
STATE_ACTIVE = "🔄 Active"
STATE_DONE = "✅ Done"

# Regex to detect the tracking section already present in issue body
_TRACKING_SECTION_RE = re.compile(
    r"---\s*\n\s*##\s*🤖\s*(?:Agent Pipeline|Agents Pipelines).*",
    re.DOTALL,
)

# Regex to parse a single row (5-column): | 1 | Backlog | `speckit.specify` | gpt-4o | ⏳ Pending |
_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|\s*([^|\n]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|"
)

# Legacy regex for old 4-column format: | 1 | Backlog | `speckit.specify` | ⏳ Pending |
_ROW_RE_OLD = re.compile(r"\|\s*(\d+)\s*\|\s*([^|\n]+?)\s*\|\s*`([^`]+)`\s*\|\s*([^|\n]+?)\s*\|")


# ── Data types ───────────────────────────────────────────────────────────────


@dataclass
class AgentStep:
    """One row in the agent pipeline table."""

    index: int
    status: str  # e.g. "Backlog", "Ready", "In Progress"
    agent_name: str  # e.g. "speckit.specify"
    model: str = ""  # e.g. "gpt-4o"; empty string → renders as "TBD"
    state: str = STATE_PENDING  # one of STATE_PENDING / STATE_ACTIVE / STATE_DONE


# ── Generating the tracking section ─────────────────────────────────────────


def build_agent_pipeline_steps(
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
) -> list[AgentStep]:
    """
    Build the ordered list of agent steps from the workflow configuration.

    Args:
        agent_mappings: Status name → list of AgentAssignment objects
        status_order:   Ordered list of statuses that have agents
                        (e.g. ["Backlog", "Ready", "In Progress"])

    Returns:
        Flat ordered list of AgentStep with all states set to PENDING
    """
    steps: list[AgentStep] = []
    idx = 1
    for status in status_order:
        # Case-insensitive lookup: status names may differ in casing
        # between the config defaults and the user's project board.
        matched_agents = agent_mappings.get(status, None)
        if matched_agents is None:
            status_lower = status.lower()
            for k, v in agent_mappings.items():
                if k.lower() == status_lower:
                    matched_agents = v
                    break
        if not matched_agents:
            matched_agents = []
        for agent in matched_agents:
            agent_slug = agent.slug if hasattr(agent, "slug") else str(agent)
            config = getattr(agent, "config", None)
            model = config.get("model_name", "") if isinstance(config, dict) else ""
            steps.append(
                AgentStep(
                    index=idx,
                    status=status,
                    agent_name=agent_slug,
                    model=model,
                    state=STATE_PENDING,
                )
            )
            idx += 1
    return steps


def render_tracking_markdown(steps: list[AgentStep]) -> str:
    """
    Render the tracking table as a markdown string.

    Returns the full section (separator + header + table) that gets
    appended to the issue body.
    """
    lines = [
        "",
        TRACKING_SEPARATOR,
        "",
        TRACKING_HEADER,
        "",
        "| # | Status | Agent | Model | State |",
        "|---|--------|-------|-------|-------|",
    ]
    for step in steps:
        model_display = (step.model or "TBD").replace("|", "\\|")
        lines.append(
            f"| {step.index} | {step.status} | `{step.agent_name}` | {model_display} | {step.state} |"
        )
    lines.append("")
    return "\n".join(lines)


def append_tracking_to_body(
    body: str,
    agent_mappings: dict[str, list[AgentAssignment]],
    status_order: list[str],
) -> str:
    """
    Append (or replace) the tracking section at the end of an issue body.

    If the tracking section is already present it will be replaced so the
    function is idempotent.
    """
    steps = build_agent_pipeline_steps(agent_mappings, status_order)
    tracking = render_tracking_markdown(steps)

    # Strip existing tracking section if present
    body_clean = _TRACKING_SECTION_RE.sub("", body).rstrip()

    return body_clean + "\n" + tracking


# ── Parsing the tracking section from an issue body ─────────────────────────


def parse_tracking_from_body(body: str) -> list[AgentStep] | None:
    """
    Parse the agent tracking table from a GitHub Issue body.

    Returns:
        List of AgentStep or None if no tracking section found.
    """
    match = _TRACKING_SECTION_RE.search(body)
    if not match:
        return None

    section = match.group(0)
    steps: list[AgentStep] = []
    for row_match in _ROW_RE.finditer(section):
        idx = int(row_match.group(1))
        status = row_match.group(2).strip()
        agent_name = row_match.group(3).strip()
        model = row_match.group(4).strip()
        state = row_match.group(5).strip()
        steps.append(
            AgentStep(index=idx, status=status, agent_name=agent_name, model=model, state=state)
        )

    # Fallback: try legacy 4-column format if no rows matched with 5-column regex
    if not steps:
        for row_match in _ROW_RE_OLD.finditer(section):
            idx = int(row_match.group(1))
            status = row_match.group(2).strip()
            agent_name = row_match.group(3).strip()
            state = row_match.group(4).strip()
            steps.append(
                AgentStep(index=idx, status=status, agent_name=agent_name, model="", state=state)
            )

    return steps or None


def get_current_agent_from_tracking(body: str) -> AgentStep | None:
    """
    Return the agent step that is currently 🔄 Active, or None.
    """
    steps = parse_tracking_from_body(body)
    if not steps:
        return None
    for step in steps:
        if STATE_ACTIVE in step.state:
            return step
    return None


def get_next_pending_agent(body: str) -> AgentStep | None:
    """
    Return the first agent step that is ⏳ Pending, or None.
    """
    steps = parse_tracking_from_body(body)
    if not steps:
        return None
    for step in steps:
        if STATE_PENDING in step.state:
            return step
    return None


# ── Updating the tracking section ───────────────────────────────────────────


def update_agent_state(
    body: str,
    agent_name: str,
    new_state: str,
) -> str:
    """
    Update a specific agent's state in the tracking table and return the
    new full issue body.

    If the agent is not found or there's no tracking section, the body
    is returned unchanged.
    """
    steps = parse_tracking_from_body(body)
    if not steps:
        return body

    found = False
    for step in steps:
        if step.agent_name == agent_name:
            step.state = new_state
            found = True
            break

    if not found:
        logger.warning("Agent '%s' not found in tracking section", agent_name)
        return body

    tracking = render_tracking_markdown(steps)
    body_clean = _TRACKING_SECTION_RE.sub("", body).rstrip()
    return body_clean + "\n" + tracking


def mark_agent_active(body: str, agent_name: str) -> str:
    """Set agent to 🔄 Active in the tracking table."""
    return update_agent_state(body, agent_name, STATE_ACTIVE)


def mark_agent_done(body: str, agent_name: str) -> str:
    """Set agent to ✅ Done in the tracking table."""
    return update_agent_state(body, agent_name, STATE_DONE)


# ── Comment-based completion check ─────────────────────────────────────────


def check_last_comment_for_done(
    comments: list[dict],
) -> str | None:
    """
    Check the last issue comment for an "<agent>: Done!" marker.

    Also supports the Human agent pattern: an exact "Done!" comment
    (no agent prefix) returns "human" as the agent name.

    Args:
        comments: List of comment dicts with "body" key, ordered oldest-first

    Returns:
        The agent name if the last comment is a Done! marker, else None
    """
    if not comments:
        return None

    raw_body = comments[-1].get("body", "")
    stripped_body = raw_body.strip()
    # Match pattern: "speckit.specify: Done!" (must be the whole comment).
    # Whitespace tolerance is intentional for agent patterns — editors or
    # bots may emit trailing spaces.
    match = re.match(r"^(.+?):\s*Done!\s*$", stripped_body)
    if match:
        return match.group(1).strip()
    # Match Human agent pattern: EXACT "Done!" with no whitespace tolerance.
    # The spec requires the literal string "Done!" with no surrounding
    # whitespace to trigger Human step completion.
    if raw_body == "Done!":
        return "human"
    return None


# ── Derive next action from issue body + comments ──────────────────────────


@dataclass
class PipelineAction:
    """What the polling loop should do next for this issue."""

    action: (
        str  # "assign_agent" | "advance_pipeline" | "transition_status" | "wait" | "no_tracking"
    )
    agent_name: str | None = None
    agent_step: AgentStep | None = None
    target_status: str | None = None  # for transition_status


def determine_next_action(
    body: str,
    comments: list[dict],
) -> PipelineAction:
    """
    Read the issue body tracking table and last comment to decide what
    the polling loop should do.

    Logic:
      1. Parse the tracking table.
      2. If no tracking → return "no_tracking".
      3. Find the Active agent. If a Done! comment exists for it → "advance_pipeline".
      4. If no Active agent, find the next Pending → "assign_agent".
      5. If no Pending agents left → "transition_status".
      6. Otherwise → "wait".
    """
    steps = parse_tracking_from_body(body)
    if not steps:
        return PipelineAction(action="no_tracking")

    # Find active agent
    active_step = None
    for step in steps:
        if STATE_ACTIVE in step.state:
            active_step = step
            break

    # Check if last comment says the active agent finished
    done_agent = check_last_comment_for_done(comments)

    if active_step and done_agent and done_agent == active_step.agent_name:
        # Active agent posted Done! → advance
        return PipelineAction(
            action="advance_pipeline",
            agent_name=active_step.agent_name,
            agent_step=active_step,
        )

    if active_step:
        # Agent is active but not done yet → wait
        return PipelineAction(
            action="wait", agent_name=active_step.agent_name, agent_step=active_step
        )

    # No active agent — find first pending
    pending_step = None
    for step in steps:
        if STATE_PENDING in step.state:
            pending_step = step
            break

    if pending_step:
        return PipelineAction(
            action="assign_agent",
            agent_name=pending_step.agent_name,
            agent_step=pending_step,
        )

    # All done — check if we need a status transition
    # Find the last done step's status — that tells us where we are
    last_done = None
    for step in reversed(steps):
        if STATE_DONE in step.state:
            last_done = step
            break

    if last_done:
        return PipelineAction(
            action="transition_status",
            target_status=last_done.status,
        )

    return PipelineAction(action="wait")
