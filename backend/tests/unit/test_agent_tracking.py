"""Unit tests for agent tracking pure functions.

Covers:
- build_agent_pipeline_steps()
- render_tracking_markdown()
- parse_tracking_from_body()
- get_current_agent_from_tracking()
- get_next_pending_agent()
- determine_next_action()
- update_agent_state / mark_agent_active / mark_agent_done
- check_last_comment_for_done()
- append_tracking_to_body()
"""

from dataclasses import dataclass

from src.services.agent_tracking import (
    STATE_ACTIVE,
    STATE_DONE,
    STATE_PENDING,
    TRACKING_HEADER,
    AgentStep,
    append_tracking_to_body,
    build_agent_pipeline_steps,
    check_last_comment_for_done,
    determine_next_action,
    get_current_agent_from_tracking,
    get_next_pending_agent,
    mark_agent_active,
    mark_agent_done,
    parse_tracking_from_body,
    render_tracking_markdown,
    update_agent_state,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


@dataclass
class _FakeAgent:
    """Minimal stand-in for AgentAssignment (has a ``slug`` attr)."""

    slug: str


def _make_mappings(
    statuses_and_agents: dict[str, list[str]],
) -> dict[str, list[_FakeAgent]]:
    return {s: [_FakeAgent(slug=a) for a in agents] for s, agents in statuses_and_agents.items()}


# Sample markdown body with a tracking section
SAMPLE_BODY = """\
Issue description here.

---

## 🤖 Agent Pipeline

| # | Status | Agent | State |
|---|--------|-------|-------|
| 1 | Backlog | `speckit.specify` | ✅ Done |
| 2 | Ready | `speckit.plan` | 🔄 Active |
| 3 | In Progress | `speckit.implement` | ⏳ Pending |
"""


# =============================================================================
# build_agent_pipeline_steps
# =============================================================================


class TestBuildAgentPipelineSteps:
    def test_basic_pipeline(self):
        mappings = _make_mappings({"Backlog": ["a1"], "Ready": ["a2"]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog", "Ready"])
        assert len(steps) == 2
        assert steps[0].agent_name == "a1"
        assert steps[0].status == "Backlog"
        assert steps[0].index == 1
        assert steps[1].agent_name == "a2"
        assert steps[1].index == 2

    def test_all_states_start_pending(self):
        mappings = _make_mappings({"Ready": ["x"]})
        steps = build_agent_pipeline_steps(mappings, ["Ready"])
        assert all(s.state == STATE_PENDING for s in steps)

    def test_multiple_agents_per_status(self):
        mappings = _make_mappings({"Ready": ["a1", "a2", "a3"]})
        steps = build_agent_pipeline_steps(mappings, ["Ready"])
        assert len(steps) == 3
        assert [s.agent_name for s in steps] == ["a1", "a2", "a3"]

    def test_empty_mappings(self):
        steps = build_agent_pipeline_steps({}, ["Backlog"])
        assert steps == []

    def test_empty_status_order(self):
        mappings = _make_mappings({"Backlog": ["a1"]})
        steps = build_agent_pipeline_steps(mappings, [])
        assert steps == []

    def test_case_insensitive_lookup(self):
        mappings = _make_mappings({"backlog": ["agent-1"]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog"])
        assert len(steps) == 1
        assert steps[0].agent_name == "agent-1"

    def test_status_not_in_mappings_skipped(self):
        mappings = _make_mappings({"Ready": ["a1"]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog", "Ready"])
        assert len(steps) == 1
        assert steps[0].status == "Ready"


# =============================================================================
# render_tracking_markdown
# =============================================================================


class TestRenderTrackingMarkdown:
    def test_contains_header(self):
        steps = [AgentStep(1, "Backlog", "a1", STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert TRACKING_HEADER in md

    def test_contains_agent_name(self):
        steps = [AgentStep(1, "Backlog", "my.agent", STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert "`my.agent`" in md

    def test_contains_state(self):
        steps = [AgentStep(1, "Backlog", "a1", STATE_ACTIVE)]
        md = render_tracking_markdown(steps)
        assert STATE_ACTIVE in md

    def test_multiple_rows(self):
        steps = [
            AgentStep(1, "Backlog", "a1", STATE_DONE),
            AgentStep(2, "Ready", "a2", STATE_PENDING),
        ]
        md = render_tracking_markdown(steps)
        assert "| 1 |" in md
        assert "| 2 |" in md

    def test_empty_steps(self):
        md = render_tracking_markdown([])
        assert TRACKING_HEADER in md
        # Should still have header + separator but no data rows
        lines = [line for line in md.split("\n") if line.startswith("|")]
        # header row + separator row = 2
        assert len(lines) == 2


# =============================================================================
# parse_tracking_from_body
# =============================================================================


class TestParseTrackingFromBody:
    def test_parse_sample_body(self):
        steps = parse_tracking_from_body(SAMPLE_BODY)
        assert steps is not None
        assert len(steps) == 3
        assert steps[0].agent_name == "speckit.specify"
        assert STATE_DONE in steps[0].state
        assert steps[1].agent_name == "speckit.plan"
        assert STATE_ACTIVE in steps[1].state
        assert steps[2].agent_name == "speckit.implement"
        assert STATE_PENDING in steps[2].state

    def test_no_tracking_returns_none(self):
        assert parse_tracking_from_body("Just a normal issue body.") is None

    def test_empty_body(self):
        assert parse_tracking_from_body("") is None


# =============================================================================
# get_current_agent_from_tracking
# =============================================================================


class TestGetCurrentAgentFromTracking:
    def test_finds_active_agent(self):
        step = get_current_agent_from_tracking(SAMPLE_BODY)
        assert step is not None
        assert step.agent_name == "speckit.plan"

    def test_no_active_returns_none(self):
        body = SAMPLE_BODY.replace(STATE_ACTIVE, STATE_DONE)
        step = get_current_agent_from_tracking(body)
        assert step is None

    def test_no_tracking_returns_none(self):
        assert get_current_agent_from_tracking("no tracking here") is None


# =============================================================================
# get_next_pending_agent
# =============================================================================


class TestGetNextPendingAgent:
    def test_finds_first_pending(self):
        step = get_next_pending_agent(SAMPLE_BODY)
        assert step is not None
        assert step.agent_name == "speckit.implement"

    def test_no_pending_returns_none(self):
        body = SAMPLE_BODY.replace(STATE_PENDING, STATE_DONE)
        step = get_next_pending_agent(body)
        assert step is None


# =============================================================================
# update_agent_state / mark_agent_active / mark_agent_done
# =============================================================================


class TestUpdateAgentState:
    def test_update_state(self):
        new_body = update_agent_state(SAMPLE_BODY, "speckit.implement", STATE_ACTIVE)
        steps = parse_tracking_from_body(new_body)
        assert steps is not None
        impl_step = [s for s in steps if s.agent_name == "speckit.implement"][0]
        assert STATE_ACTIVE in impl_step.state

    def test_unknown_agent_returns_unchanged(self):
        new_body = update_agent_state(SAMPLE_BODY, "nonexistent.agent", STATE_DONE)
        assert new_body == SAMPLE_BODY

    def test_no_tracking_returns_unchanged(self):
        body = "plain text"
        assert update_agent_state(body, "x", STATE_DONE) == body

    def test_mark_agent_active_helper(self):
        new_body = mark_agent_active(SAMPLE_BODY, "speckit.implement")
        get_current_agent_from_tracking(new_body)
        # There might be two active now (plan was already active); just check implement
        steps = parse_tracking_from_body(new_body)
        impl = [s for s in steps if s.agent_name == "speckit.implement"][0]
        assert STATE_ACTIVE in impl.state

    def test_mark_agent_done_helper(self):
        new_body = mark_agent_done(SAMPLE_BODY, "speckit.plan")
        steps = parse_tracking_from_body(new_body)
        plan = [s for s in steps if s.agent_name == "speckit.plan"][0]
        assert STATE_DONE in plan.state


# =============================================================================
# check_last_comment_for_done
# =============================================================================


class TestCheckLastCommentForDone:
    def test_done_comment(self):
        comments = [{"body": "speckit.plan: Done!"}]
        assert check_last_comment_for_done(comments) == "speckit.plan"

    def test_no_comments(self):
        assert check_last_comment_for_done([]) is None

    def test_non_done_comment(self):
        assert check_last_comment_for_done([{"body": "Just a comment"}]) is None

    def test_multiple_comments_checks_last(self):
        comments = [
            {"body": "some earlier comment"},
            {"body": "my.agent: Done!"},
        ]
        assert check_last_comment_for_done(comments) == "my.agent"

    def test_whitespace_tolerance(self):
        assert check_last_comment_for_done([{"body": "  agent.x:  Done!  "}]) == "agent.x"


# =============================================================================
# append_tracking_to_body
# =============================================================================


class TestAppendTrackingToBody:
    def test_appends_to_plain_body(self):
        mappings = _make_mappings({"Backlog": ["a1"]})
        result = append_tracking_to_body("Hello world", mappings, ["Backlog"])
        assert "Hello world" in result
        assert TRACKING_HEADER in result
        assert "`a1`" in result

    def test_replaces_existing_tracking(self):
        mappings = _make_mappings({"Ready": ["newagent"]})
        result = append_tracking_to_body(SAMPLE_BODY, mappings, ["Ready"])
        # Old agents should be gone
        assert "speckit.specify" not in result
        assert "`newagent`" in result

    def test_idempotent(self):
        mappings = _make_mappings({"Ready": ["a1"]})
        first = append_tracking_to_body("body", mappings, ["Ready"])
        second = append_tracking_to_body(first, mappings, ["Ready"])
        assert first == second


# =============================================================================
# determine_next_action
# =============================================================================


class TestDetermineNextAction:
    def test_no_tracking(self):
        action = determine_next_action("plain body", [])
        assert action.action == "no_tracking"

    def test_active_agent_waiting(self):
        action = determine_next_action(SAMPLE_BODY, [])
        assert action.action == "wait"
        assert action.agent_name == "speckit.plan"

    def test_active_agent_done(self):
        comments = [{"body": "speckit.plan: Done!"}]
        action = determine_next_action(SAMPLE_BODY, comments)
        assert action.action == "advance_pipeline"
        assert action.agent_name == "speckit.plan"

    def test_no_active_assigns_next_pending(self):
        # Remove the active agent, keep pending
        body = SAMPLE_BODY.replace(STATE_ACTIVE, STATE_DONE)
        action = determine_next_action(body, [])
        assert action.action == "assign_agent"
        assert action.agent_name == "speckit.implement"

    def test_all_done_transitions_status(self):
        body = SAMPLE_BODY.replace(STATE_ACTIVE, STATE_DONE).replace(STATE_PENDING, STATE_DONE)
        action = determine_next_action(body, [])
        assert action.action == "transition_status"

    def test_done_comment_for_wrong_agent_still_waits(self):
        comments = [{"body": "other.agent: Done!"}]
        action = determine_next_action(SAMPLE_BODY, comments)
        assert action.action == "wait"
