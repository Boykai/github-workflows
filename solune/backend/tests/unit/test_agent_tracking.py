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
- Group-aware tracking (6-column format, group labels, backward compat)
"""

from dataclasses import dataclass

from src.models.agent import AgentAssignment
from src.models.workflow import ExecutionGroupMapping
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
    config: dict | None = None


def _make_mappings(
    statuses_and_agents: dict[str, list[str | tuple[str, dict | None]]],
) -> dict[str, list[_FakeAgent]]:
    result: dict[str, list[_FakeAgent]] = {}
    for s, agents in statuses_and_agents.items():
        fake_agents: list[_FakeAgent] = []
        for a in agents:
            if isinstance(a, tuple):
                fake_agents.append(_FakeAgent(slug=a[0], config=a[1]))
            else:
                fake_agents.append(_FakeAgent(slug=a))
        result[s] = fake_agents
    return result


# Sample markdown body with a 5-column tracking section (new format with Model column)
SAMPLE_BODY = """\
Issue description here.

---

## 🤖 Agent Pipeline

| # | Status | Agent | Model | State |
|---|--------|-------|-------|-------|
| 1 | Backlog | `speckit.specify` | gpt-4o | ✅ Done |
| 2 | Ready | `speckit.plan` | claude-3-5-sonnet | 🔄 Active |
| 3 | In Progress | `speckit.implement` | TBD | ⏳ Pending |
"""

# Legacy markdown body with old 4-column tracking section (no Model column)


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

    def test_model_extracted_from_config(self):
        mappings = _make_mappings(
            {
                "Backlog": [("a1", {"model_name": "gpt-4o"})],
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Backlog"])
        assert len(steps) == 1
        assert steps[0].model == "gpt-4o"

    def test_model_empty_when_config_none(self):
        mappings = _make_mappings({"Backlog": [("a1", None)]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog"])
        assert steps[0].model == ""

    def test_model_empty_when_config_empty_dict(self):
        mappings = _make_mappings({"Backlog": [("a1", {})]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog"])
        assert steps[0].model == ""

    def test_model_empty_when_config_has_no_model_name(self):
        mappings = _make_mappings({"Backlog": [("a1", {"other_key": "value"})]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog"])
        assert steps[0].model == ""

    def test_model_empty_when_no_config_attr(self):
        """Plain string agents (via _FakeAgent default) have model=''."""
        mappings = _make_mappings({"Backlog": ["a1"]})
        steps = build_agent_pipeline_steps(mappings, ["Backlog"])
        assert steps[0].model == ""


# =============================================================================
# render_tracking_markdown
# =============================================================================


class TestRenderTrackingMarkdown:
    def test_contains_header(self):
        steps = [AgentStep(1, "Backlog", "a1", state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert TRACKING_HEADER in md

    def test_contains_agent_name(self):
        steps = [AgentStep(1, "Backlog", "my.agent", state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert "`my.agent`" in md

    def test_contains_state(self):
        steps = [AgentStep(1, "Backlog", "a1", state=STATE_ACTIVE)]
        md = render_tracking_markdown(steps)
        assert STATE_ACTIVE in md

    def test_multiple_rows(self):
        steps = [
            AgentStep(1, "Backlog", "a1", state=STATE_DONE),
            AgentStep(2, "Ready", "a2", state=STATE_PENDING),
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

    def test_model_column_header(self):
        steps = [AgentStep(1, "Backlog", "a1", model="gpt-4o", state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert "| # | Status | Agent | Model | State |" in md

    def test_model_displayed_in_row(self):
        steps = [AgentStep(1, "Backlog", "a1", model="gpt-4o", state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert "| gpt-4o |" in md

    def test_empty_model_renders_as_tbd(self):
        steps = [AgentStep(1, "Backlog", "a1", model="", state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert "| TBD |" in md

    def test_mixed_model_and_tbd(self):
        steps = [
            AgentStep(1, "Backlog", "a1", model="gpt-4o", state=STATE_DONE),
            AgentStep(2, "Ready", "a2", model="", state=STATE_PENDING),
            AgentStep(3, "In Progress", "a3", model="claude-3-5-sonnet", state=STATE_PENDING),
        ]
        md = render_tracking_markdown(steps)
        assert "| gpt-4o |" in md
        assert "| TBD |" in md
        assert "| claude-3-5-sonnet |" in md

    def test_pipe_in_model_name_escaped(self):
        steps = [AgentStep(1, "Backlog", "a1", model="model|v2", state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert "model\\|v2" in md

    def test_long_model_name_preserved(self):
        long_name = "custom-fine-tuned-gpt-4o-2026-03-extended-context"
        steps = [AgentStep(1, "Backlog", "a1", model=long_name, state=STATE_PENDING)]
        md = render_tracking_markdown(steps)
        assert long_name in md


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
        assert steps[0].model == "gpt-4o"
        assert steps[1].agent_name == "speckit.plan"
        assert STATE_ACTIVE in steps[1].state
        assert steps[1].model == "claude-3-5-sonnet"
        assert steps[2].agent_name == "speckit.implement"
        assert STATE_PENDING in steps[2].state
        assert steps[2].model == ""

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
        impl_step = next(s for s in steps if s.agent_name == "speckit.implement")
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
        impl = next(s for s in steps if s.agent_name == "speckit.implement")
        assert STATE_ACTIVE in impl.state

    def test_mark_agent_done_helper(self):
        new_body = mark_agent_done(SAMPLE_BODY, "speckit.plan")
        steps = parse_tracking_from_body(new_body)
        plan = next(s for s in steps if s.agent_name == "speckit.plan")
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

    def test_human_exact_done(self):
        """Exact 'Done!' with no agent prefix returns 'human'."""
        assert check_last_comment_for_done([{"body": "Done!"}]) == "human"

    def test_human_done_with_trailing_whitespace_rejected(self):
        """'Done! ' (trailing space) must NOT match the Human pattern.

        The spec requires the literal exact string 'Done!' to trigger
        Human step completion — no whitespace tolerance.
        """
        assert check_last_comment_for_done([{"body": "Done! "}]) is None

    def test_human_done_with_leading_whitespace_rejected(self):
        """' Done!' (leading space) must NOT match the Human pattern."""
        assert check_last_comment_for_done([{"body": " Done!"}]) is None

    def test_human_done_case_sensitive(self):
        """'done!' (lowercase) must NOT match — case-sensitive."""
        assert check_last_comment_for_done([{"body": "done!"}]) is None


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
        assert "## 🤖 Agent Pipeline" not in result
        assert TRACKING_HEADER in result
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


# =============================================================================
# Model preservation through state update cycle (US3)
# =============================================================================


class TestModelPreservation:
    def test_model_preserved_through_mark_active(self):
        """Models are preserved when an agent state changes."""
        new_body = mark_agent_active(SAMPLE_BODY, "speckit.implement")
        steps = parse_tracking_from_body(new_body)
        assert steps is not None
        specify = next(s for s in steps if s.agent_name == "speckit.specify")
        plan = next(s for s in steps if s.agent_name == "speckit.plan")
        impl = next(s for s in steps if s.agent_name == "speckit.implement")
        assert specify.model == "gpt-4o"
        assert plan.model == "claude-3-5-sonnet"
        assert impl.model == ""
        assert STATE_ACTIVE in impl.state

    def test_append_tracking_idempotent_with_model(self):
        """append_tracking_to_body is idempotent with 5-column tracking tables."""
        mappings = _make_mappings(
            {
                "Ready": [("a1", {"model_name": "gpt-4o"})],
            }
        )
        first = append_tracking_to_body("body", mappings, ["Ready"])
        second = append_tracking_to_body(first, mappings, ["Ready"])
        assert first == second
        # Verify exactly one tracking section
        assert first.count(TRACKING_HEADER) == 1


# =============================================================================
# Group-aware tracking: 6-column format
# =============================================================================


# Sample markdown body with a 6-column tracking section (group column)
SAMPLE_BODY_6COL = """\
Issue description here.

---

## 🤖 Agents Pipelines

| # | Status | Group | Agent | Model | State |
|---|--------|-------|-------|-------|-------|
| 1 | Ready | G1 (series) | `speckit.plan` | gpt-4o | ✅ Done |
| 2 | Ready | G1 (series) | `speckit.tasks` | gpt-4o | 🔄 Active |
| 3 | Ready | G2 (parallel) | `speckit.implement` | TBD | ⏳ Pending |
| 4 | Ready | G2 (parallel) | `speckit.review` | TBD | ⏳ Pending |
"""


def _make_group_mappings(
    status_groups: dict[str, list[tuple[str, str, list[str | tuple[str, dict | None]]]]],
) -> dict[str, list[ExecutionGroupMapping]]:
    """Build group_mappings for testing.

    Args:
        status_groups: dict mapping status to list of (group_id, execution_mode, agents).
            Each agent is either a slug string or a (slug, config) tuple.
    """
    result: dict[str, list[ExecutionGroupMapping]] = {}
    for status, groups in status_groups.items():
        egm_list = []
        for order, (group_id, mode, agents) in enumerate(groups):
            agent_assignments = []
            for a in agents:
                if isinstance(a, tuple):
                    agent_assignments.append(AgentAssignment(slug=a[0], config=a[1]))
                else:
                    agent_assignments.append(AgentAssignment(slug=a))
            egm_list.append(
                ExecutionGroupMapping(
                    group_id=group_id,
                    order=order,
                    execution_mode=mode,
                    agents=agent_assignments,
                )
            )
        result[status] = egm_list
    return result


class TestBuildAgentPipelineStepsWithGroups:
    """Tests for build_agent_pipeline_steps with group_mappings."""

    def test_single_sequential_group(self):
        mappings = _make_mappings({"Ready": ["a1", "a2"]})
        group_mappings = _make_group_mappings(
            {
                "Ready": [("g1", "sequential", ["a1", "a2"])],
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Ready"], group_mappings)
        assert len(steps) == 2
        assert steps[0].group_label == "G1 (series)"
        assert steps[0].group_execution_mode == "sequential"
        assert steps[1].group_label == "G1 (series)"

    def test_single_parallel_group(self):
        mappings = _make_mappings({"Ready": ["a1", "a2", "a3"]})
        group_mappings = _make_group_mappings(
            {
                "Ready": [("g1", "parallel", ["a1", "a2", "a3"])],
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Ready"], group_mappings)
        assert len(steps) == 3
        assert steps[0].group_label == "G1 (parallel)"
        assert steps[0].group_execution_mode == "parallel"

    def test_mixed_groups_in_one_status(self):
        mappings = _make_mappings({"Ready": ["a1", "a2", "a3", "a4"]})
        group_mappings = _make_group_mappings(
            {
                "Ready": [
                    ("g1", "sequential", ["a1", "a2"]),
                    ("g2", "parallel", ["a3", "a4"]),
                ],
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Ready"], group_mappings)
        assert len(steps) == 4
        assert steps[0].group_label == "G1 (series)"
        assert steps[1].group_label == "G1 (series)"
        assert steps[2].group_label == "G2 (parallel)"
        assert steps[3].group_label == "G2 (parallel)"

    def test_group_numbering_resets_per_status(self):
        """Group numbering G1, G2... resets for each status."""
        mappings = _make_mappings(
            {
                "Backlog": ["a1"],
                "Ready": ["a2", "a3"],
            }
        )
        group_mappings = _make_group_mappings(
            {
                "Backlog": [("bg1", "sequential", ["a1"])],
                "Ready": [
                    ("rg1", "sequential", ["a2"]),
                    ("rg2", "parallel", ["a3"]),
                ],
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Backlog", "Ready"], group_mappings)
        assert steps[0].group_label == "G1 (series)"  # Backlog group
        assert steps[1].group_label == "G1 (series)"  # Ready group 1
        assert steps[2].group_label == "G2 (parallel)"  # Ready group 2

    def test_flat_fallback_when_no_groups(self):
        """When group_mappings is None or empty, existing flat behavior is used."""
        mappings = _make_mappings({"Ready": ["a1", "a2"]})
        steps = build_agent_pipeline_steps(mappings, ["Ready"], None)
        assert len(steps) == 2
        assert steps[0].group_label == ""
        assert steps[0].group_execution_mode == ""

    def test_flat_fallback_for_status_without_groups(self):
        """Status without groups in group_mappings uses flat fallback."""
        mappings = _make_mappings(
            {
                "Backlog": ["a1"],
                "Ready": ["a2"],
            }
        )
        group_mappings = _make_group_mappings(
            {
                "Backlog": [("g1", "sequential", ["a1"])],
                # Ready has no groups
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Backlog", "Ready"], group_mappings)
        assert steps[0].group_label == "G1 (series)"  # Backlog has groups
        assert steps[1].group_label == ""  # Ready falls back to flat

    def test_model_extracted_in_group_path(self):
        mappings = _make_mappings({"Ready": [("a1", {"model_name": "gpt-4o"})]})
        group_mappings = _make_group_mappings(
            {
                "Ready": [("g1", "sequential", [("a1", {"model_name": "gpt-4o"})])],
            }
        )
        steps = build_agent_pipeline_steps(mappings, ["Ready"], group_mappings)
        assert steps[0].model == "gpt-4o"


class TestRenderTrackingMarkdown6Col:
    """Tests for 6-column render when group_label is present."""

    def test_renders_6col_header(self):
        steps = [
            AgentStep(
                index=1,
                status="Ready",
                agent_name="a1",
                group_label="G1 (series)",
                group_execution_mode="sequential",
            ),
        ]
        md = render_tracking_markdown(steps)
        assert "| # | Status | Group | Agent | Model | State |" in md

    def test_renders_group_label_in_row(self):
        steps = [
            AgentStep(
                index=1,
                status="Ready",
                agent_name="a1",
                group_label="G1 (series)",
                group_execution_mode="sequential",
            ),
        ]
        md = render_tracking_markdown(steps)
        assert "G1 (series)" in md
        assert "`a1`" in md

    def test_falls_back_to_5col_when_no_groups(self):
        steps = [
            AgentStep(index=1, status="Ready", agent_name="a1"),
        ]
        md = render_tracking_markdown(steps)
        assert "| # | Status | Agent | Model | State |" in md
        assert "Group" not in md

    def test_mixed_group_and_no_group_steps(self):
        """When any step has group_label, all steps rendered with 6-col format."""
        steps = [
            AgentStep(
                index=1,
                status="Backlog",
                agent_name="a1",
                group_label="G1 (series)",
            ),
            AgentStep(index=2, status="Ready", agent_name="a2"),
        ]
        md = render_tracking_markdown(steps)
        assert "| # | Status | Group | Agent | Model | State |" in md


class TestParseTrackingFromBody6Col:
    """Tests for parsing 6-column tracking table."""

    def test_parse_6col_format(self):
        steps = parse_tracking_from_body(SAMPLE_BODY_6COL)
        assert steps is not None
        assert len(steps) == 4

        # First step
        assert steps[0].index == 1
        assert steps[0].status == "Ready"
        assert steps[0].group_label == "G1 (series)"
        assert steps[0].agent_name == "speckit.plan"
        assert steps[0].model == "gpt-4o"
        assert STATE_DONE in steps[0].state

        # Second step
        assert steps[1].group_label == "G1 (series)"
        assert steps[1].group_execution_mode == "sequential"

        # Third step (parallel group)
        assert steps[2].group_label == "G2 (parallel)"
        assert steps[2].group_execution_mode == "parallel"
        assert steps[2].agent_name == "speckit.implement"

    def test_parse_5col_fallback(self):
        """5-column format still works (backward compat)."""
        steps = parse_tracking_from_body(SAMPLE_BODY)
        assert steps is not None
        assert len(steps) == 3
        assert steps[0].group_label == ""

    def test_group_metadata_parsed_from_label(self):
        """group_order and group_execution_mode extracted from group_label."""
        steps = parse_tracking_from_body(SAMPLE_BODY_6COL)
        assert steps is not None

        # G1 (series) → order=0, mode=sequential
        assert steps[0].group_order == 0
        assert steps[0].group_execution_mode == "sequential"

        # G2 (parallel) → order=1, mode=parallel
        assert steps[2].group_order == 1
        assert steps[2].group_execution_mode == "parallel"

    def test_no_tracking_section(self):
        assert parse_tracking_from_body("just a body with no tracking") is None


class TestUpdateAgentStatePreservesGroups:
    """update_agent_state should preserve group_label through parse→modify→re-render."""

    def test_preserves_group_label_on_state_update(self):
        body = SAMPLE_BODY_6COL
        updated = update_agent_state(body, "speckit.tasks", STATE_DONE)
        steps = parse_tracking_from_body(updated)
        assert steps is not None
        # Agent updated
        step = next(s for s in steps if s.agent_name == "speckit.tasks")
        assert STATE_DONE in step.state
        # Group labels preserved
        assert step.group_label == "G1 (series)"
        # Other steps unchanged
        parallel_step = next(s for s in steps if s.agent_name == "speckit.implement")
        assert parallel_step.group_label == "G2 (parallel)"

    def test_mark_active_preserves_groups(self):
        body = SAMPLE_BODY_6COL
        updated = mark_agent_active(body, "speckit.implement")
        steps = parse_tracking_from_body(updated)
        assert steps is not None
        step = next(s for s in steps if s.agent_name == "speckit.implement")
        assert STATE_ACTIVE in step.state
        assert step.group_label == "G2 (parallel)"


class TestAppendTrackingWithGroups:
    """Tests for append_tracking_to_body with group_mappings."""

    def test_append_with_groups_produces_6col(self):
        mappings = _make_mappings({"Ready": ["a1", "a2"]})
        group_mappings = _make_group_mappings(
            {
                "Ready": [("g1", "sequential", ["a1", "a2"])],
            }
        )
        result = append_tracking_to_body("body", mappings, ["Ready"], group_mappings=group_mappings)
        assert "| # | Status | Group | Agent | Model | State |" in result
        assert "G1 (series)" in result

    def test_append_without_groups_produces_5col(self):
        mappings = _make_mappings({"Ready": ["a1"]})
        result = append_tracking_to_body("body", mappings, ["Ready"])
        assert "| # | Status | Agent | Model | State |" in result
        assert "Group" not in result

    def test_append_idempotent_with_groups(self):
        mappings = _make_mappings({"Ready": ["a1", "a2"]})
        group_mappings = _make_group_mappings(
            {
                "Ready": [("g1", "sequential", ["a1", "a2"])],
            }
        )
        first = append_tracking_to_body("body", mappings, ["Ready"], group_mappings=group_mappings)
        second = append_tracking_to_body(first, mappings, ["Ready"], group_mappings=group_mappings)
        assert first == second
        assert first.count(TRACKING_HEADER) == 1
