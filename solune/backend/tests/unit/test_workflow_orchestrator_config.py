from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models.pipeline import PipelineAgentNode, PipelineConfig, PipelineStage
from src.services.workflow_orchestrator.config import (
    PipelineResolutionResult,
    load_pipeline_as_agent_mappings,
    resolve_project_pipeline_mappings,
)


class FakeCursor:
    def __init__(self, row):
        self._row = row

    async def fetchone(self):
        return self._row


class FakeConnection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.execute_calls = []
        self.row_factory = None
        self.committed = False

    async def execute(self, sql, params=None):
        self.execute_calls.append((sql, params))
        if sql.startswith("SELECT "):
            row = self.rows.pop(0) if self.rows else None
            return FakeCursor(row)
        return FakeCursor(None)

    async def commit(self):
        self.committed = True


class FakeConnectContext:
    def __init__(self, connection):
        self.connection = connection

    async def __aenter__(self):
        return self.connection

    async def __aexit__(self, exc_type, exc, tb):
        return False


class TestLoadPipelineAsAgentMappings:
    @pytest.mark.asyncio
    async def test_converts_pipeline_stages_to_agent_assignments(self):
        pipeline = PipelineConfig(
            id="pipeline-1",
            project_id="project-1",
            name="Full Review Pipeline",
            description="",
            stages=[
                PipelineStage(
                    id="stage-2",
                    name="Ready",
                    order=2,
                    agents=[
                        PipelineAgentNode(
                            id="agent-2",
                            agent_slug="speckit.plan",
                            agent_display_name="Planner",
                            model_id="model-2",
                            model_name="Model 2",
                            tool_ids=[],
                            tool_count=0,
                            config={},
                        )
                    ],
                ),
                PipelineStage(
                    id="stage-1",
                    name="Backlog",
                    order=1,
                    agents=[
                        PipelineAgentNode(
                            id="agent-1",
                            agent_slug="speckit.specify",
                            agent_display_name="Specifier",
                            model_id="model-1",
                            model_name="Model 1",
                            tool_ids=[],
                            tool_count=0,
                            config={},
                        )
                    ],
                ),
            ],
            created_at="2026-03-08T00:00:00Z",
            updated_at="2026-03-08T00:00:00Z",
        )

        mock_service = Mock()
        mock_service.get_pipeline = AsyncMock(return_value=pipeline)

        with (
            patch("src.services.database.get_db", return_value=Mock()),
            patch("src.services.pipelines.service.PipelineService", return_value=mock_service),
        ):
            (
                mappings,
                pipeline_name,
                exec_modes,
                _grp_mappings,
            ) = await load_pipeline_as_agent_mappings("project-1", "pipeline-1")

        assert pipeline_name == "Full Review Pipeline"
        assert list(mappings.keys()) == ["Backlog", "Ready"]
        assert mappings["Backlog"][0].slug == "speckit.specify"
        assert mappings["Backlog"][0].display_name == "Specifier"
        assert mappings["Backlog"][0].config == {
            "model_id": "model-1",
            "model_name": "Model 1",
        }
        assert mappings["Ready"][0].slug == "speckit.plan"
        assert exec_modes == {"Backlog": "sequential", "Ready": "sequential"}


class TestResolveProjectPipelineMappings:
    @pytest.mark.asyncio
    async def test_uses_project_pipeline_when_assignment_exists(self):
        connection = FakeConnection(rows=[{"assigned_pipeline_id": "pipeline-1"}])

        with (
            patch("src.config.get_settings", return_value=Mock(database_path="test.db")),
            patch(
                "src.services.workflow_orchestrator.config.aiosqlite.connect",
                return_value=FakeConnectContext(connection),
            ),
            patch(
                "src.services.workflow_orchestrator.config.load_pipeline_as_agent_mappings",
                new=AsyncMock(return_value=({"Backlog": []}, "Full Review Pipeline", {}, {})),
            ) as mock_load_pipeline,
            patch(
                "src.services.workflow_orchestrator.config.load_user_agent_mappings",
                new=AsyncMock(return_value=None),
            ) as mock_load_user,
        ):
            result = await resolve_project_pipeline_mappings("project-1", "user-1")

        assert isinstance(result, PipelineResolutionResult)
        assert result.source == "pipeline"
        assert result.pipeline_id == "pipeline-1"
        assert result.pipeline_name == "Full Review Pipeline"
        assert result.agent_mappings == {"Backlog": []}
        mock_load_pipeline.assert_awaited_once_with("project-1", "pipeline-1")
        mock_load_user.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_falls_back_to_user_mappings_when_no_pipeline_is_assigned(self):
        connection = FakeConnection(rows=[None])
        user_mappings = {"In Progress": [Mock(slug="speckit.implement")]}

        with (
            patch("src.config.get_settings", return_value=Mock(database_path="test.db")),
            patch(
                "src.services.workflow_orchestrator.config.aiosqlite.connect",
                return_value=FakeConnectContext(connection),
            ),
            patch(
                "src.services.workflow_orchestrator.config.load_user_agent_mappings",
                new=AsyncMock(return_value=user_mappings),
            ) as mock_load_user,
        ):
            result = await resolve_project_pipeline_mappings("project-1", "user-1")

        assert result.source == "user"
        assert result.pipeline_name is None
        assert result.agent_mappings == user_mappings
        mock_load_user.assert_awaited_once_with("user-1", "project-1")

    @pytest.mark.asyncio
    async def test_falls_back_to_default_mappings_when_no_assignment_or_user_mappings_exist(self):
        connection = FakeConnection(rows=[None])

        with (
            patch("src.config.get_settings", return_value=Mock(database_path="test.db")),
            patch(
                "src.services.workflow_orchestrator.config.aiosqlite.connect",
                return_value=FakeConnectContext(connection),
            ),
            patch(
                "src.services.workflow_orchestrator.config.load_user_agent_mappings",
                new=AsyncMock(return_value=None),
            ),
            patch("src.constants.DEFAULT_AGENT_MAPPINGS", {"Backlog": ["speckit.specify"]}),
            patch("src.constants.AGENT_DISPLAY_NAMES", {"speckit.specify": "Specifier"}),
        ):
            result = await resolve_project_pipeline_mappings("project-1", "user-1")

        assert result.source == "default"
        assert result.pipeline_name is None
        assert list(result.agent_mappings.keys()) == ["Backlog"]
        assert result.agent_mappings["Backlog"][0].slug == "speckit.specify"
        assert result.agent_mappings["Backlog"][0].display_name == "Specifier"

    @pytest.mark.asyncio
    async def test_clears_stale_assignment_when_assigned_pipeline_is_missing(self):
        select_connection = FakeConnection(rows=[{"assigned_pipeline_id": "pipeline-9"}])
        cleanup_connection = FakeConnection()

        with (
            patch("src.config.get_settings", return_value=Mock(database_path="test.db")),
            patch(
                "src.services.workflow_orchestrator.config.aiosqlite.connect",
                side_effect=[
                    FakeConnectContext(select_connection),
                    FakeConnectContext(cleanup_connection),
                ],
            ),
            patch(
                "src.services.workflow_orchestrator.config.load_pipeline_as_agent_mappings",
                new=AsyncMock(return_value=None),
            ) as mock_load_pipeline,
            patch(
                "src.services.workflow_orchestrator.config.load_user_agent_mappings",
                new=AsyncMock(return_value=None),
            ),
        ):
            result = await resolve_project_pipeline_mappings("project-1", "user-1")

        assert result.source == "default"
        assert mock_load_pipeline.await_count == 1
        assert cleanup_connection.execute_calls[0] == ("PRAGMA busy_timeout=5000;", None)
        assert cleanup_connection.execute_calls[1] == (
            "UPDATE project_settings SET assigned_pipeline_id = '' WHERE github_user_id = ? AND project_id = ?",
            ("__workflow__", "project-1"),
        )
        assert cleanup_connection.committed is True
