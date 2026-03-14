"""Unit tests for fast-path pipeline reconstruction from labels."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_DB_PATCH = "src.services.database.get_db"


def _mock_pipeline_response(configs):
    """Wrap a list of configs in a response-like object with .pipelines."""
    resp = MagicMock()
    resp.pipelines = configs
    return resp


# ── _build_pipeline_from_labels ──────────────────────────────────────────────


class TestBuildPipelineFromLabels:
    """Verify _build_pipeline_from_labels builds correct PipelineState."""

    def _make_pipeline_config(self, name, agents_by_stage):
        """Create a minimal PipelineConfig-like object."""
        stages = []
        for stage_agents in agents_by_stage:
            stage = MagicMock()
            agent_objs = []
            for slug in stage_agents:
                a = MagicMock()
                a.slug = slug
                agent_objs.append(a)
            stage.agents = agent_objs
            stages.append(stage)
        config = MagicMock()
        config.name = name
        config.stages = stages
        return config

    @pytest.mark.asyncio
    async def test_returns_none_when_no_pipeline_label(self):
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        result = await _build_pipeline_from_labels(
            issue_number=1,
            project_id="PVT_1",
            status="In Progress",
            labels=[{"name": "bug", "color": "000"}],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_no_agent_label(self):
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        result = await _build_pipeline_from_labels(
            issue_number=1,
            project_id="PVT_1",
            status="In Progress",
            labels=[{"name": "pipeline:speckit-full", "color": "0052cc"}],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_config_not_found(self):
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        with (
            patch(_DB_PATCH, return_value=MagicMock()),
            patch("src.services.pipelines.service.PipelineService") as mock_svc_cls,
        ):
            mock_svc = AsyncMock()
            mock_svc.list_pipelines = AsyncMock(return_value=_mock_pipeline_response([]))
            mock_svc_cls.return_value = mock_svc

            result = await _build_pipeline_from_labels(
                issue_number=1,
                project_id="PVT_1",
                status="In Progress",
                labels=[
                    {"name": "pipeline:speckit-full", "color": "0052cc"},
                    {"name": "agent:speckit.plan", "color": "7057ff"},
                ],
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_builds_correct_pipeline_state(self):
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        config = self._make_pipeline_config(
            "speckit-full",
            [["speckit.specify"], ["speckit.plan", "speckit.tasks"], ["speckit.implement"]],
        )

        with (
            patch(_DB_PATCH, return_value=MagicMock()),
            patch("src.services.pipelines.service.PipelineService") as mock_svc_cls,
        ):
            mock_svc = AsyncMock()
            mock_svc.list_pipelines = AsyncMock(return_value=_mock_pipeline_response([config]))
            mock_svc_cls.return_value = mock_svc

            result = await _build_pipeline_from_labels(
                issue_number=42,
                project_id="PVT_1",
                status="Ready",
                labels=[
                    {"name": "pipeline:speckit-full", "color": "0052cc"},
                    {"name": "agent:speckit.plan", "color": "7057ff"},
                ],
            )

            assert result is not None
            assert result.issue_number == 42
            assert result.project_id == "PVT_1"
            assert result.status == "Ready"
            assert result.agents == [
                "speckit.specify",
                "speckit.plan",
                "speckit.tasks",
                "speckit.implement",
            ]
            assert result.current_agent_index == 1
            assert result.current_agent == "speckit.plan"
            assert result.completed_agents == ["speckit.specify"]

    @pytest.mark.asyncio
    async def test_returns_none_when_agent_not_in_config(self):
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        config = self._make_pipeline_config("test-pipe", [["speckit.specify"]])

        with (
            patch(_DB_PATCH, return_value=MagicMock()),
            patch("src.services.pipelines.service.PipelineService") as mock_svc_cls,
        ):
            mock_svc = AsyncMock()
            mock_svc.list_pipelines = AsyncMock(return_value=_mock_pipeline_response([config]))
            mock_svc_cls.return_value = mock_svc

            result = await _build_pipeline_from_labels(
                issue_number=1,
                project_id="PVT_1",
                status="In Progress",
                labels=[
                    {"name": "pipeline:test-pipe", "color": "0052cc"},
                    {"name": "agent:unknown-agent", "color": "7057ff"},
                ],
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_first_agent_has_no_completed(self):
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        config = self._make_pipeline_config("simple", [["speckit.specify"], ["speckit.plan"]])

        with (
            patch(_DB_PATCH, return_value=MagicMock()),
            patch("src.services.pipelines.service.PipelineService") as mock_svc_cls,
        ):
            mock_svc = AsyncMock()
            mock_svc.list_pipelines = AsyncMock(return_value=_mock_pipeline_response([config]))
            mock_svc_cls.return_value = mock_svc

            result = await _build_pipeline_from_labels(
                issue_number=1,
                project_id="PVT_1",
                status="Backlog",
                labels=[
                    {"name": "pipeline:simple", "color": "0052cc"},
                    {"name": "agent:speckit.specify", "color": "7057ff"},
                ],
            )

            assert result is not None
            assert result.current_agent_index == 0
            assert result.completed_agents == []
            assert result.current_agent == "speckit.specify"


# ── Fast-path integration in _get_or_reconstruct_pipeline ────────────────────


class TestFastPathIntegration:
    """Verify fast-path is used when labels are provided, fallthrough when absent."""

    @pytest.mark.asyncio
    async def test_fast_path_skipped_when_labels_none(self):
        """When labels=None, fast-path should be skipped entirely."""
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        # With empty labels, fast-path returns None (no pipeline/agent labels)
        result = await _build_pipeline_from_labels(
            issue_number=1,
            project_id="PVT_1",
            status="In Progress",
            labels=[],
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_fast_path_fallthrough_on_missing_labels(self):
        """When only one of two required labels is present, returns None."""
        from src.services.copilot_polling.pipeline import _build_pipeline_from_labels

        # Only pipeline label, no agent label
        result = await _build_pipeline_from_labels(
            issue_number=1,
            project_id="PVT_1",
            status="In Progress",
            labels=[{"name": "pipeline:x", "color": "0052cc"}],
        )
        assert result is None
