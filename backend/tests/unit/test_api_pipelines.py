"""Unit tests for pipeline launch endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.models.pipeline import (
    PipelineAgentNode,
    PipelineConfigCreate,
    PipelineStage,
)
from src.services.pipelines.service import PipelineService


async def _create_pipeline(mock_db, project_id: str = "PVT_1") -> str:
    """Create a saved pipeline for route tests and return its ID."""
    service = PipelineService(mock_db)
    pipeline = await service.create_pipeline(
        project_id,
        PipelineConfigCreate(
            name="Imported Issue Pipeline",
            description="Launches imported parent issues",
            stages=[
                PipelineStage(
                    id="stage-backlog",
                    name="Backlog",
                    order=0,
                    agents=[
                        PipelineAgentNode(
                            id="agent-specify",
                            agent_slug="speckit.specify",
                            agent_display_name="Spec Kit - Specify",
                            model_id="",
                            model_name="",
                            tool_ids=[],
                            tool_count=0,
                            config={},
                        )
                    ],
                )
            ],
            blocking=False,
        ),
    )
    return pipeline.id


class TestLaunchPipelineIssue:
    """Tests for POST /pipelines/{project_id}/launch."""

    @pytest.mark.anyio
    async def test_launch_success(self, client, mock_db, mock_github_service):
        """Creates a GitHub issue and starts the selected pipeline."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.return_value = {
            "number": 42,
            "node_id": "I_node_42",
            "html_url": "https://github.com/owner/repo/issues/42",
        }

        mock_orchestrator = AsyncMock()

        async def add_to_project(ctx, recommendation=None):
            ctx.project_item_id = "PVTI_42"
            return "PVTI_42"

        mock_orchestrator.add_to_project_with_backlog.side_effect = add_to_project
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status.return_value = True

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config", new_callable=AsyncMock, return_value=None
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
            patch("src.api.pipelines.get_workflow_orchestrator", return_value=mock_orchestrator),
            patch(
                "src.services.blocking_queue.enqueue_issue",
                new_callable=AsyncMock,
                return_value=({}, True),
            ),
            patch("src.services.copilot_polling.ensure_polling_started", new_callable=AsyncMock),
            patch("src.api.pipelines.get_pipeline_state", return_value=None),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Import this issue\n\nCarry over the original context.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["issue_number"] == 42
        assert "launched with the selected pipeline" in data["message"]
        mock_github_service.create_issue.assert_awaited_once()
        _, kwargs = mock_github_service.create_issue.await_args
        assert kwargs["title"] == "Import this issue"
        assert "Carry over the original context." in kwargs["body"]

    @pytest.mark.anyio
    async def test_launch_rejects_whitespace_only_description(self, client, mock_db):
        """Whitespace-only descriptions return a validation error."""
        pipeline_id = await _create_pipeline(mock_db)

        resp = await client.post(
            "/api/v1/pipelines/PVT_1/launch",
            json={"issue_description": "   \n\t", "pipeline_id": pipeline_id},
        )

        assert resp.status_code == 422
        assert "Issue description is required" in resp.json()["error"]

    @pytest.mark.anyio
    async def test_launch_returns_404_for_missing_pipeline(self, client):
        """Deleted or unknown pipelines fail gracefully."""
        with patch(
            "src.api.pipelines.resolve_repository",
            new_callable=AsyncMock,
            return_value=("owner", "repo"),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "## Existing issue\n\nUse this text.",
                    "pipeline_id": "missing-pipeline",
                },
            )

        assert resp.status_code == 404
        assert "Selected pipeline config is no longer available" in resp.json()["error"]

    @pytest.mark.anyio
    async def test_launch_handles_issue_creation_failure_without_assigning_pipeline(
        self, client, mock_db, mock_github_service
    ):
        """Issue creation failures return a scoped error response and keep assignment unchanged."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.side_effect = RuntimeError("GitHub issue create failed")

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config", new_callable=AsyncMock, return_value=None
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Import this issue\n\nCarry over the original context.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        assert resp.json() == {
            "success": False,
            "issue_id": None,
            "issue_number": None,
            "issue_url": None,
            "project_item_id": None,
            "current_status": "error",
            "message": "We couldn't launch the pipeline from this issue description. Please try again.",
        }

        assignment = await PipelineService(mock_db).get_assignment("PVT_1")
        assert assignment.pipeline_id == ""
