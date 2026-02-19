"""Unit tests for agent tracking service."""

from src.services.agent_tracking import (
    STATE_ACTIVE,
    STATE_DONE,
    STATE_PENDING,
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


class _FakeAgent:
    """Minimal stand-in for AgentAssignment with a slug attribute."""

    def __init__(self, slug: str):
        self.slug = slug


def _make_body_with_tracking(steps: list[AgentStep]) -> str:
    """Build a sample issue body with a tracking section."""
    return "Issue description\n" + render_tracking_markdown(steps)


def _sample_steps() -> list[AgentStep]:
    return [
        AgentStep(1, "Backlog", "speckit.specify", STATE_PENDING),
        AgentStep(2, "Ready", "speckit.plan", STATE_PENDING),
        AgentStep(3, "In Progress", "speckit.implement", STATE_PENDING),
    ]


# ── build_agent_pipeline_steps ───────────────────────────────────────────────


class TestBuildAgentPipelineSteps:
    """Tests for build_agent_pipeline_steps."""

    def test_single_status_single_agent(self):
        """Should create one step for one agent in one status."""
        mappings = {"Backlog": [_FakeAgent("speckit.specify")]}
        status_order = ["Backlog"]

        steps = build_agent_pipeline_steps(mappings, status_order)

        assert len(steps) == 1
        assert steps[0].index == 1
        assert steps[0].status == "Backlog"
        assert steps[0].agent_name == "speckit.specify"
        assert steps[0].state == STATE_PENDING

    def test_multiple_statuses(self):
        """Should produce steps across multiple statuses in order."""
        mappings = {
            "Backlog": [_FakeAgent("speckit.specify")],
            "Ready": [_FakeAgent("speckit.plan")],
        }
        status_order = ["Backlog", "Ready"]

        steps = build_agent_pipeline_steps(mappings, status_order)

        assert len(steps) == 2
        assert steps[0].agent_name == "speckit.specify"
        assert steps[1].agent_name == "speckit.plan"
        assert steps[1].index == 2

    def test_multiple_agents_per_status(self):
        """Should produce steps for each agent within a status."""
        mappings = {
            "Backlog": [_FakeAgent("agent.a"), _FakeAgent("agent.b")],
        }
        status_order = ["Backlog"]

        steps = build_agent_pipeline_steps(mappings, status_order)

        assert len(steps) == 2
        assert steps[0].agent_name == "agent.a"
        assert steps[1].agent_name == "agent.b"

    def test_empty_mappings(self):
        """Should return empty list for empty mappings."""
        steps = build_agent_pipeline_steps({}, [])

        assert steps == []

    def test_status_not_in_mappings(self):
        """Should skip statuses that have no agents in mappings."""
        mappings = {"Backlog": [_FakeAgent("agent.a")]}
        status_order = ["Backlog", "Missing"]

        steps = build_agent_pipeline_steps(mappings, status_order)

        assert len(steps) == 1


# ── render_tracking_markdown ─────────────────────────────────────────────────


class TestRenderTrackingMarkdown:
    """Tests for render_tracking_markdown."""

    def test_contains_header(self):
        """Should contain the pipeline header."""
        md = render_tracking_markdown(_sample_steps())

        assert "## 🤖 Agent Pipeline" in md

    def test_contains_table_rows(self):
        """Should contain a row for each step."""
        md = render_tracking_markdown(_sample_steps())

        assert "`speckit.specify`" in md
        assert "`speckit.plan`" in md
        assert "`speckit.implement`" in md

    def test_contains_separator(self):
        """Should start with a --- separator."""
        md = render_tracking_markdown(_sample_steps())

        assert "---" in md

    def test_empty_steps(self):
        """Should still produce header with no rows."""
        md = render_tracking_markdown([])

        assert "## 🤖 Agent Pipeline" in md


# ── append_tracking_to_body ──────────────────────────────────────────────────


class TestAppendTrackingToBody:
    """Tests for append_tracking_to_body."""

    def test_appends_to_plain_body(self):
        """Should append tracking section to a body without one."""
        mappings = {"Backlog": [_FakeAgent("speckit.specify")]}
        status_order = ["Backlog"]

        result = append_tracking_to_body("My issue", mappings, status_order)

        assert result.startswith("My issue")
        assert "`speckit.specify`" in result

    def test_replaces_existing_tracking(self):
        """Should replace old tracking section (idempotent)."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)
        mappings = {"Backlog": [_FakeAgent("new.agent")]}
        status_order = ["Backlog"]

        result = append_tracking_to_body(body, mappings, status_order)

        assert "`new.agent`" in result
        # Old agents should be gone
        assert "`speckit.specify`" not in result


# ── parse_tracking_from_body ─────────────────────────────────────────────────


class TestParseTrackingFromBody:
    """Tests for parse_tracking_from_body."""

    def test_parses_valid_tracking(self):
        """Should parse steps from a body with tracking."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)

        parsed = parse_tracking_from_body(body)

        assert parsed is not None
        assert len(parsed) == 3
        assert parsed[0].agent_name == "speckit.specify"
        assert parsed[2].agent_name == "speckit.implement"

    def test_returns_none_without_tracking(self):
        """Should return None when no tracking section exists."""
        result = parse_tracking_from_body("Just a plain issue body")

        assert result is None

    def test_returns_none_for_empty_body(self):
        """Should return None for empty body."""
        result = parse_tracking_from_body("")

        assert result is None

    def test_preserves_state_values(self):
        """Should preserve the state value from the table."""
        steps = [AgentStep(1, "Backlog", "agent.a", STATE_DONE)]
        body = _make_body_with_tracking(steps)

        parsed = parse_tracking_from_body(body)

        assert parsed is not None
        assert STATE_DONE in parsed[0].state


# ── get_current_agent_from_tracking ──────────────────────────────────────────


class TestGetCurrentAgentFromTracking:
    """Tests for get_current_agent_from_tracking."""

    def test_returns_active_agent(self):
        """Should return the active agent step."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_DONE),
            AgentStep(2, "Ready", "agent.b", STATE_ACTIVE),
            AgentStep(3, "In Progress", "agent.c", STATE_PENDING),
        ]
        body = _make_body_with_tracking(steps)

        result = get_current_agent_from_tracking(body)

        assert result is not None
        assert result.agent_name == "agent.b"

    def test_returns_none_when_no_active(self):
        """Should return None when no agent is active."""
        steps = [AgentStep(1, "Backlog", "agent.a", STATE_PENDING)]
        body = _make_body_with_tracking(steps)

        result = get_current_agent_from_tracking(body)

        assert result is None

    def test_returns_none_without_tracking(self):
        """Should return None when no tracking section exists."""
        result = get_current_agent_from_tracking("plain body")

        assert result is None


# ── get_next_pending_agent ───────────────────────────────────────────────────


class TestGetNextPendingAgent:
    """Tests for get_next_pending_agent."""

    def test_returns_first_pending(self):
        """Should return the first pending agent."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_DONE),
            AgentStep(2, "Ready", "agent.b", STATE_PENDING),
            AgentStep(3, "In Progress", "agent.c", STATE_PENDING),
        ]
        body = _make_body_with_tracking(steps)

        result = get_next_pending_agent(body)

        assert result is not None
        assert result.agent_name == "agent.b"

    def test_returns_none_when_all_done(self):
        """Should return None when all agents are done."""
        steps = [AgentStep(1, "Backlog", "agent.a", STATE_DONE)]
        body = _make_body_with_tracking(steps)

        result = get_next_pending_agent(body)

        assert result is None

    def test_returns_none_without_tracking(self):
        """Should return None for body without tracking."""
        result = get_next_pending_agent("no tracking here")

        assert result is None


# ── update_agent_state ───────────────────────────────────────────────────────


class TestUpdateAgentState:
    """Tests for update_agent_state."""

    def test_updates_existing_agent(self):
        """Should update the target agent's state."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)

        result = update_agent_state(body, "speckit.plan", STATE_ACTIVE)
        parsed = parse_tracking_from_body(result)

        assert parsed is not None
        assert STATE_ACTIVE in parsed[1].state

    def test_agent_not_found(self):
        """Should return body unchanged when agent not found."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)

        result = update_agent_state(body, "nonexistent.agent", STATE_ACTIVE)

        assert result == body

    def test_no_tracking_section(self):
        """Should return body unchanged when no tracking section."""
        body = "plain body"

        result = update_agent_state(body, "agent.a", STATE_ACTIVE)

        assert result == body

    def test_preserves_issue_description(self):
        """Should preserve original issue text."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)

        result = update_agent_state(body, "speckit.specify", STATE_DONE)

        assert "Issue description" in result


# ── mark_agent_active / mark_agent_done ──────────────────────────────────────


class TestMarkAgentHelpers:
    """Tests for mark_agent_active and mark_agent_done."""

    def test_mark_active(self):
        """mark_agent_active should set state to Active."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)

        result = mark_agent_active(body, "speckit.specify")
        parsed = parse_tracking_from_body(result)

        assert parsed is not None
        assert STATE_ACTIVE in parsed[0].state

    def test_mark_done(self):
        """mark_agent_done should set state to Done."""
        steps = _sample_steps()
        body = _make_body_with_tracking(steps)

        result = mark_agent_done(body, "speckit.specify")
        parsed = parse_tracking_from_body(result)

        assert parsed is not None
        assert STATE_DONE in parsed[0].state


# ── check_last_comment_for_done ──────────────────────────────────────────────


class TestCheckLastCommentForDone:
    """Tests for check_last_comment_for_done."""

    def test_detects_done_comment(self):
        """Should detect '<agent>: Done!' pattern."""
        comments = [{"body": "speckit.specify: Done!"}]

        result = check_last_comment_for_done(comments)

        assert result == "speckit.specify"

    def test_ignores_non_done_comments(self):
        """Should return None for non-Done comments."""
        comments = [{"body": "Just a regular comment"}]

        result = check_last_comment_for_done(comments)

        assert result is None

    def test_empty_comments(self):
        """Should return None for empty comment list."""
        result = check_last_comment_for_done([])

        assert result is None

    def test_only_checks_last_comment(self):
        """Should only check the last comment, not earlier ones."""
        comments = [
            {"body": "speckit.specify: Done!"},
            {"body": "some follow-up"},
        ]

        result = check_last_comment_for_done(comments)

        assert result is None

    def test_strips_whitespace(self):
        """Should handle trailing whitespace in Done marker."""
        comments = [{"body": "agent.a: Done!  "}]

        result = check_last_comment_for_done(comments)

        assert result == "agent.a"


# ── determine_next_action ────────────────────────────────────────────────────


class TestDetermineNextAction:
    """Tests for determine_next_action."""

    def test_no_tracking_returns_no_tracking(self):
        """Should return 'no_tracking' when body has no tracking section."""
        result = determine_next_action("plain body", [])

        assert result.action == "no_tracking"

    def test_active_agent_done_returns_advance(self):
        """Should return 'advance_pipeline' when active agent has Done comment."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_ACTIVE),
            AgentStep(2, "Ready", "agent.b", STATE_PENDING),
        ]
        body = _make_body_with_tracking(steps)
        comments = [{"body": "agent.a: Done!"}]

        result = determine_next_action(body, comments)

        assert result.action == "advance_pipeline"
        assert result.agent_name == "agent.a"

    def test_active_agent_not_done_returns_wait(self):
        """Should return 'wait' when active agent hasn't posted Done."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_ACTIVE),
            AgentStep(2, "Ready", "agent.b", STATE_PENDING),
        ]
        body = _make_body_with_tracking(steps)

        result = determine_next_action(body, [])

        assert result.action == "wait"
        assert result.agent_name == "agent.a"

    def test_no_active_with_pending_returns_assign(self):
        """Should return 'assign_agent' when no active but pending exists."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_DONE),
            AgentStep(2, "Ready", "agent.b", STATE_PENDING),
        ]
        body = _make_body_with_tracking(steps)

        result = determine_next_action(body, [])

        assert result.action == "assign_agent"
        assert result.agent_name == "agent.b"

    def test_all_done_returns_transition(self):
        """Should return 'transition_status' when all agents are done."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_DONE),
            AgentStep(2, "Ready", "agent.b", STATE_DONE),
        ]
        body = _make_body_with_tracking(steps)

        result = determine_next_action(body, [])

        assert result.action == "transition_status"
        assert result.target_status == "Ready"

    def test_done_from_different_agent_returns_wait(self):
        """Should 'wait' when Done comment is from a different agent."""
        steps = [
            AgentStep(1, "Backlog", "agent.a", STATE_ACTIVE),
            AgentStep(2, "Ready", "agent.b", STATE_PENDING),
        ]
        body = _make_body_with_tracking(steps)
        comments = [{"body": "agent.b: Done!"}]

        result = determine_next_action(body, comments)

        assert result.action == "wait"
