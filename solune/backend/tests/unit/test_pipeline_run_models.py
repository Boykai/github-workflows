"""Tests for pipeline run models — validation rules (FR-001, FR-002, FR-003)."""

import pytest
from pydantic import ValidationError

from src.models.pipeline_run import PipelineRun, PipelineRunCreate
from src.models.pipeline_stage_state import PipelineStageState
from src.models.stage_group import StageGroup


class TestPipelineRunCreate:
    def test_default_trigger_is_manual(self):
        create = PipelineRunCreate()
        assert create.trigger == "manual"

    def test_accepts_webhook_trigger(self):
        create = PipelineRunCreate(trigger="webhook")
        assert create.trigger == "webhook"

    def test_accepts_scheduled_trigger(self):
        create = PipelineRunCreate(trigger="scheduled")
        assert create.trigger == "scheduled"

    def test_rejects_invalid_trigger(self):
        with pytest.raises(ValidationError):
            PipelineRunCreate(trigger="invalid")


class TestPipelineRunValidation:
    def test_completed_at_required_for_terminal_status(self):
        with pytest.raises(ValidationError, match="completed_at must be set"):
            PipelineRun(
                id=1,
                pipeline_config_id="pc-1",
                project_id="proj-1",
                status="completed",
                started_at="2026-01-01T00:00:00Z",
                completed_at=None,
            )

    def test_completed_at_forbidden_for_active_status(self):
        with pytest.raises(ValidationError, match="completed_at must be None"):
            PipelineRun(
                id=1,
                pipeline_config_id="pc-1",
                project_id="proj-1",
                status="pending",
                started_at="2026-01-01T00:00:00Z",
                completed_at="2026-01-01T01:00:00Z",
            )

    def test_valid_pending_run(self):
        run = PipelineRun(
            id=1,
            pipeline_config_id="pc-1",
            project_id="proj-1",
            status="pending",
            started_at="2026-01-01T00:00:00Z",
        )
        assert run.status == "pending"
        assert run.completed_at is None

    def test_valid_completed_run(self):
        run = PipelineRun(
            id=1,
            pipeline_config_id="pc-1",
            project_id="proj-1",
            status="completed",
            started_at="2026-01-01T00:00:00Z",
            completed_at="2026-01-01T01:00:00Z",
        )
        assert run.status == "completed"


class TestPipelineStageState:
    def test_creates_with_defaults(self):
        state = PipelineStageState(
            id=1,
            pipeline_run_id=1,
            stage_id="build",
        )
        assert state.status == "pending"
        assert state.group_id is None
        assert state.agent_id is None


class TestStageGroup:
    def test_validates_execution_mode(self):
        with pytest.raises(ValidationError):
            StageGroup(
                id=1,
                pipeline_config_id="pc-1",
                name="Test",
                execution_mode="invalid",
                order_index=0,
            )

    def test_validates_empty_name(self):
        with pytest.raises(ValidationError):
            StageGroup(
                id=1,
                pipeline_config_id="pc-1",
                name="",
                execution_mode="sequential",
                order_index=0,
            )

    def test_valid_sequential_group(self):
        group = StageGroup(
            id=1,
            pipeline_config_id="pc-1",
            name="Build Group",
            execution_mode="sequential",
            order_index=0,
        )
        assert group.execution_mode == "sequential"
        assert group.name == "Build Group"

    def test_valid_parallel_group(self):
        group = StageGroup(
            id=1,
            pipeline_config_id="pc-1",
            name="Test Group",
            execution_mode="parallel",
            order_index=1,
        )
        assert group.execution_mode == "parallel"
