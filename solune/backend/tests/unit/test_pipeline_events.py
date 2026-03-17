"""Tests for pipeline event dataclasses."""

from src.models.pipeline_events import (
    MCPConfigUpdated,
    PipelineRunStateChanged,
    PipelineStageStateChanged,
)


class TestPipelineRunStateChanged:
    def test_creates_with_required_fields(self):
        event = PipelineRunStateChanged(
            run_id=1,
            pipeline_config_id="pc-1",
            project_id="proj-1",
            previous_status="pending",
            new_status="running",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert event.run_id == 1
        assert event.previous_status == "pending"
        assert event.new_status == "running"
        assert event.error_message is None

    def test_creates_with_error_message(self):
        event = PipelineRunStateChanged(
            run_id=1,
            pipeline_config_id="pc-1",
            project_id="proj-1",
            previous_status="running",
            new_status="failed",
            timestamp="2026-01-01T00:00:00Z",
            error_message="Stage build failed",
        )
        assert event.error_message == "Stage build failed"


class TestPipelineStageStateChanged:
    def test_creates_with_required_fields(self):
        event = PipelineStageStateChanged(
            stage_state_id=1,
            pipeline_run_id=1,
            stage_id="build",
            group_id=None,
            previous_status="pending",
            new_status="running",
            agent_id=None,
            timestamp="2026-01-01T00:00:00Z",
        )
        assert event.stage_id == "build"
        assert event.group_id is None

    def test_creates_with_agent_and_group(self):
        event = PipelineStageStateChanged(
            stage_state_id=1,
            pipeline_run_id=1,
            stage_id="test",
            group_id=5,
            previous_status="pending",
            new_status="running",
            agent_id="agent-1",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert event.group_id == 5
        assert event.agent_id == "agent-1"


class TestMCPConfigUpdated:
    def test_creates_with_defaults(self):
        event = MCPConfigUpdated(
            project_id="proj-1",
            owner="user",
            repo="repo",
        )
        assert event.tools == []
        assert event.timestamp == ""

    def test_creates_with_tools(self):
        event = MCPConfigUpdated(
            project_id="proj-1",
            owner="user",
            repo="repo",
            tools=["tool-a", "tool-b"],
            timestamp="2026-01-01T00:00:00Z",
        )
        assert len(event.tools) == 2
