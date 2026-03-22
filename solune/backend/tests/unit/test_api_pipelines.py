"""Unit tests for pipeline launch endpoints."""

from __future__ import annotations

import asyncio
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


# ══════════════════════════════════════════════════════════════
# Pipeline CRUD — negative / error path tests
# ══════════════════════════════════════════════════════════════


class TestGetPipeline:
    """Tests for GET /pipelines/{project_id}/{pipeline_id}."""

    @pytest.mark.anyio
    async def test_get_returns_pipeline(self, client, mock_db):
        """Returns a saved pipeline by ID."""
        pid = await _create_pipeline(mock_db)
        resp = await client.get(f"/api/v1/pipelines/PVT_1/{pid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    @pytest.mark.anyio
    async def test_get_returns_404_for_missing_pipeline(self, client):
        """Returns 404 for a non-existent pipeline."""
        resp = await client.get("/api/v1/pipelines/PVT_1/no-such-id")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_get_returns_404_for_wrong_project(self, client, mock_db):
        """Pipeline exists under project A but request uses project B."""
        pid = await _create_pipeline(mock_db, project_id="PVT_A")
        resp = await client.get(f"/api/v1/pipelines/PVT_B/{pid}")
        assert resp.status_code == 404


class TestDeletePipeline:
    """Tests for DELETE /pipelines/{project_id}/{pipeline_id}."""

    @pytest.mark.anyio
    async def test_delete_existing_pipeline(self, client, mock_db):
        """Deletes a pipeline and returns success."""
        pid = await _create_pipeline(mock_db)
        resp = await client.delete(f"/api/v1/pipelines/PVT_1/{pid}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["deleted_id"] == pid

        # Verify it's gone
        resp2 = await client.get(f"/api/v1/pipelines/PVT_1/{pid}")
        assert resp2.status_code == 404

    @pytest.mark.anyio
    async def test_delete_returns_404_for_missing_pipeline(self, client):
        """Returns 404 when deleting a non-existent pipeline."""
        resp = await client.delete("/api/v1/pipelines/PVT_1/no-such-id")
        assert resp.status_code == 404


class TestUpdatePipeline:
    """Tests for PUT /pipelines/{project_id}/{pipeline_id}."""

    @pytest.mark.anyio
    async def test_update_name_and_description(self, client, mock_db):
        """Updates pipeline name and description."""
        pid = await _create_pipeline(mock_db)
        resp = await client.put(
            f"/api/v1/pipelines/PVT_1/{pid}",
            json={"name": "Renamed Pipeline", "description": "New desc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Renamed Pipeline"
        assert data["description"] == "New desc"

    @pytest.mark.anyio
    async def test_update_returns_404_for_missing_pipeline(self, client):
        """Returns 404 when updating a non-existent pipeline."""
        resp = await client.put(
            "/api/v1/pipelines/PVT_1/no-such-id",
            json={"name": "Nope"},
        )
        assert resp.status_code == 404


class TestListPipelines:
    """Tests for GET /pipelines/{project_id}."""

    @pytest.mark.anyio
    async def test_list_returns_empty_for_no_pipelines(self, client):
        """Returns empty list for a project with no pipelines."""
        resp = await client.get("/api/v1/pipelines/PVT_EMPTY")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pipelines"] == []
        assert data["total"] == 0

    @pytest.mark.anyio
    async def test_list_returns_created_pipelines(self, client, mock_db):
        """Lists all pipelines for a project."""
        service = PipelineService(mock_db)
        await service.create_pipeline(
            "PVT_LIST",
            PipelineConfigCreate(
                name="Pipeline Alpha",
                description="First",
                stages=[
                    PipelineStage(
                        id="s1",
                        name="S1",
                        order=0,
                        agents=[
                            PipelineAgentNode(
                                id="a1",
                                agent_slug="speckit.specify",
                                agent_display_name="Specify",
                                model_id="",
                                model_name="",
                                tool_ids=[],
                                tool_count=0,
                                config={},
                            )
                        ],
                    )
                ],
            ),
        )
        await service.create_pipeline(
            "PVT_LIST",
            PipelineConfigCreate(
                name="Pipeline Beta",
                description="Second",
                stages=[
                    PipelineStage(
                        id="s2",
                        name="S2",
                        order=0,
                        agents=[
                            PipelineAgentNode(
                                id="a2",
                                agent_slug="speckit.plan",
                                agent_display_name="Plan",
                                model_id="",
                                model_name="",
                                tool_ids=[],
                                tool_count=0,
                                config={},
                            )
                        ],
                    )
                ],
            ),
        )
        resp = await client.get("/api/v1/pipelines/PVT_LIST")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["pipelines"]) == 2


class TestSeedPresets:
    """Tests for POST /pipelines/{project_id}/seed-presets."""

    @pytest.mark.anyio
    async def test_seed_presets_creates_defaults(self, client):
        """Seeds preset pipelines for a project."""
        resp = await client.post("/api/v1/pipelines/PVT_PRESETS/seed-presets")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        assert len(data["seeded"]) == data["total"]
        assert data["skipped"] == []

    @pytest.mark.anyio
    async def test_seed_presets_is_idempotent(self, client):
        """A second seed call skips presets that already exist."""
        await client.post("/api/v1/pipelines/PVT_PRESETS_REPEAT/seed-presets")

        resp = await client.post("/api/v1/pipelines/PVT_PRESETS_REPEAT/seed-presets")

        assert resp.status_code == 200
        data = resp.json()
        assert data["seeded"] == []
        assert len(data["skipped"]) == data["total"]


class TestPipelineAssignment:
    """Tests for project pipeline assignment endpoints."""

    @pytest.mark.anyio
    async def test_get_assignment_defaults_to_empty_pipeline(self, client):
        """Projects without an assignment return an empty pipeline id."""
        resp = await client.get("/api/v1/pipelines/PVT_ASSIGNMENT/assignment")

        assert resp.status_code == 200
        assert resp.json() == {"project_id": "PVT_ASSIGNMENT", "pipeline_id": ""}

    @pytest.mark.anyio
    async def test_set_assignment_persists_selected_pipeline(self, client, mock_db):
        """Setting an assignment stores the selected pipeline for the project."""
        pipeline_id = await _create_pipeline(mock_db, project_id="PVT_ASSIGNMENT")

        resp = await client.put(
            "/api/v1/pipelines/PVT_ASSIGNMENT/assignment",
            json={"pipeline_id": pipeline_id},
        )

        assert resp.status_code == 200
        assert resp.json() == {"project_id": "PVT_ASSIGNMENT", "pipeline_id": pipeline_id}

        assignment = await PipelineService(mock_db).get_assignment("PVT_ASSIGNMENT")
        assert assignment.pipeline_id == pipeline_id

    @pytest.mark.anyio
    async def test_set_assignment_rejects_missing_pipeline(self, client):
        """Unknown pipeline ids return a not-found response."""
        resp = await client.put(
            "/api/v1/pipelines/PVT_ASSIGNMENT/assignment",
            json={"pipeline_id": "missing-pipeline"},
        )

        assert resp.status_code == 404
        assert "missing-pipeline" in resp.json()["error"]


class TestCreatePipeline:
    """Tests for POST /pipelines/{project_id}."""

    @pytest.mark.anyio
    async def test_create_pipeline(self, client, mock_db):
        """Creates a pipeline and returns 201."""
        resp = await client.post(
            "/api/v1/pipelines/PVT_1",
            json={
                "name": "New Pipeline",
                "description": "Testing creation",
                "stages": [
                    {
                        "id": "s1",
                        "name": "Build",
                        "order": 0,
                        "agents": [],
                    }
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Pipeline"
        assert data["project_id"] == "PVT_1"

    @pytest.mark.anyio
    async def test_create_pipeline_missing_name(self, client):
        """Missing name field returns 422."""
        resp = await client.post(
            "/api/v1/pipelines/PVT_1",
            json={"description": "No name", "stages": []},
        )
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_create_pipeline_rejects_duplicate_name(self, client, mock_db):
        """Creating a second pipeline with the same name returns a conflict."""
        await _create_pipeline(mock_db, project_id="PVT_DUPLICATE")

        resp = await client.post(
            "/api/v1/pipelines/PVT_DUPLICATE",
            json={
                "name": "Imported Issue Pipeline",
                "description": "Duplicate pipeline name",
                "stages": [
                    {
                        "id": "stage-duplicate",
                        "name": "Backlog",
                        "order": 0,
                        "agents": [],
                    }
                ],
            },
        )

        assert resp.status_code == 409
        assert "already exists" in resp.json()["error"]

    @pytest.mark.anyio
    async def test_update_pipeline_rejects_preset_changes(self, client, mock_db):
        """Preset pipelines cannot be modified through the API."""
        service = PipelineService(mock_db)
        await service.seed_presets("PVT_PRESET_LOCKED")
        seeded = await service.list_pipelines("PVT_PRESET_LOCKED")
        preset_id = next(pipeline.id for pipeline in seeded.pipelines if pipeline.is_preset)

        resp = await client.put(
            f"/api/v1/pipelines/PVT_PRESET_LOCKED/{preset_id}",
            json={"name": "Editable Preset"},
        )

        assert resp.status_code == 403
        assert "Cannot modify preset pipelines" in resp.json()["error"]


# ---------------------------------------------------------------------------
# T022 - Queue mode routing
# ---------------------------------------------------------------------------


class TestQueueModeRouting:
    """Tests for queue-mode gate in execute_pipeline_launch."""

    @pytest.mark.anyio
    async def test_pipeline_queued_when_queue_mode_active(
        self, client, mock_db, mock_github_service
    ):
        """When queue mode is ON and an active pipeline exists, new launches are queued."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.return_value = {
            "number": 100,
            "node_id": "I_node_100",
            "html_url": "https://github.com/owner/repo/issues/100",
        }

        mock_orchestrator = AsyncMock()

        async def add_to_project(ctx, recommendation=None):
            ctx.project_item_id = "PVTI_100"
            return "PVTI_100"

        mock_orchestrator.add_to_project_with_backlog.side_effect = add_to_project
        mock_orchestrator.create_all_sub_issues.return_value = {"speckit.specify": 101}

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
            patch(
                "src.api.pipelines.get_workflow_orchestrator",
                return_value=mock_orchestrator,
            ),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch("src.api.pipelines.count_active_pipelines_for_project", return_value=1),
            patch(
                "src.api.pipelines.get_queued_pipelines_for_project",
                return_value=["fake_queued"],
            ),
            patch("src.api.pipelines.set_pipeline_state"),
            patch("src.api.pipelines.get_agent_slugs", return_value=["speckit.specify"]),
            patch("src.api.pipelines.get_project_launch_lock", return_value=asyncio.Lock()),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Queued issue\n\nShould be queued.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "queued" in data["message"].lower()

    @pytest.mark.anyio
    async def test_pipeline_not_queued_when_no_active_pipelines(
        self, client, mock_db, mock_github_service
    ):
        """When queue mode is ON but no active pipeline exists, launch proceeds normally."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.return_value = {
            "number": 101,
            "node_id": "I_node_101",
            "html_url": "https://github.com/owner/repo/issues/101",
        }

        mock_orchestrator = AsyncMock()

        async def add_to_project(ctx, recommendation=None):
            ctx.project_item_id = "PVTI_101"
            return "PVTI_101"

        mock_orchestrator.add_to_project_with_backlog.side_effect = add_to_project
        mock_orchestrator.create_all_sub_issues.return_value = {"speckit.specify": 102}
        mock_orchestrator.assign_agent_for_status.return_value = True

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
            patch(
                "src.api.pipelines.get_workflow_orchestrator",
                return_value=mock_orchestrator,
            ),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch("src.api.pipelines.count_active_pipelines_for_project", return_value=0),
            patch("src.api.pipelines.set_pipeline_state"),
            patch("src.api.pipelines.get_agent_slugs", return_value=["speckit.specify"]),
            patch("src.api.pipelines.get_project_launch_lock", return_value=asyncio.Lock()),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
            ),
            patch("src.api.pipelines.get_pipeline_state", return_value=None),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Direct launch\n\nNo queue.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "queued" not in data["message"].lower()


# ---------------------------------------------------------------------------
# T023 - Position calculation
# ---------------------------------------------------------------------------


class TestPositionCalculation:
    """Tests for queue position reported in queued pipeline response."""

    @pytest.mark.anyio
    async def test_queue_position_reflects_depth(self, client, mock_db, mock_github_service):
        """Queue position should equal the length of the queued pipelines list."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.return_value = {
            "number": 200,
            "node_id": "I_node_200",
            "html_url": "https://github.com/owner/repo/issues/200",
        }

        mock_orchestrator = AsyncMock()

        async def add_to_project(ctx, recommendation=None):
            ctx.project_item_id = "PVTI_200"
            return "PVTI_200"

        mock_orchestrator.add_to_project_with_backlog.side_effect = add_to_project
        mock_orchestrator.create_all_sub_issues.return_value = {"speckit.specify": 201}

        # Simulate 3 already-queued pipelines
        queued_list = ["q1", "q2", "q3"]

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
            patch(
                "src.api.pipelines.get_workflow_orchestrator",
                return_value=mock_orchestrator,
            ),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch("src.api.pipelines.count_active_pipelines_for_project", return_value=1),
            patch(
                "src.api.pipelines.get_queued_pipelines_for_project",
                return_value=queued_list,
            ),
            patch("src.api.pipelines.set_pipeline_state"),
            patch("src.api.pipelines.get_agent_slugs", return_value=["speckit.specify"]),
            patch("src.api.pipelines.get_project_launch_lock", return_value=asyncio.Lock()),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Position test\n\nBody.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "#3" in data["message"]


# ---------------------------------------------------------------------------
# T024 - Dequeue trigger path
# ---------------------------------------------------------------------------


class TestDequeueTrigger:
    """Tests for _dequeue_next_pipeline in the polling pipeline module."""

    @pytest.mark.anyio
    async def test_dequeue_skipped_when_queue_mode_disabled(self):
        """No dequeue happens when queue mode is OFF."""
        from src.services.copilot_polling.pipeline import _dequeue_next_pipeline

        with (
            patch(
                "src.services.database.get_db",
                return_value=AsyncMock(),
            ),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=False,
            ),
        ):
            await _dequeue_next_pipeline("token", "PVT_1", "test")

    @pytest.mark.anyio
    async def test_dequeue_skipped_when_no_queued_pipelines(self):
        """No dequeue happens when the queue is empty."""
        from src.services.copilot_polling.pipeline import _dequeue_next_pipeline

        with (
            patch(
                "src.services.database.get_db",
                return_value=AsyncMock(),
            ),
            patch(
                "src.services.settings_store.is_queue_mode_enabled",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch("src.services.copilot_polling.pipeline._cp") as mock_cp,
        ):
            mock_cp.get_queued_pipelines_for_project.return_value = []
            await _dequeue_next_pipeline("token", "PVT_1", "test")
            mock_cp.set_pipeline_state.assert_not_called()


# ---------------------------------------------------------------------------
# T025 - Sub-issue error handling
# ---------------------------------------------------------------------------


class TestSubIssueErrors:
    """Tests for error handling when sub-issue creation or assignment fails."""

    @pytest.mark.anyio
    async def test_pipeline_state_error_returns_failure(self, client, mock_db, mock_github_service):
        """If pipeline state has an error after agent assignment, response indicates failure."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.return_value = {
            "number": 300,
            "node_id": "I_node_300",
            "html_url": "https://github.com/owner/repo/issues/300",
        }

        mock_orchestrator = AsyncMock()

        async def add_to_project(ctx, recommendation=None):
            ctx.project_item_id = "PVTI_300"
            return "PVTI_300"

        mock_orchestrator.add_to_project_with_backlog.side_effect = add_to_project
        mock_orchestrator.create_all_sub_issues.return_value = {}
        mock_orchestrator.assign_agent_for_status.return_value = True

        # Simulate pipeline state with error flag
        mock_pipeline_state = AsyncMock()
        mock_pipeline_state.error = "Agent assignment failed"

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
            patch(
                "src.api.pipelines.get_workflow_orchestrator",
                return_value=mock_orchestrator,
            ),
            patch(
                "src.services.copilot_polling.ensure_polling_started",
                new_callable=AsyncMock,
            ),
            patch("src.api.pipelines.get_pipeline_state", return_value=mock_pipeline_state),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Error case\n\nSub-issue failure.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "could not be assigned" in data["message"]

    @pytest.mark.anyio
    async def test_launch_catches_unexpected_exception(self, client, mock_db, mock_github_service):
        """Unexpected exceptions during launch yield success=False with a user-friendly message."""
        pipeline_id = await _create_pipeline(mock_db)
        mock_github_service.create_issue.return_value = {
            "number": 301,
            "node_id": "I_node_301",
            "html_url": "https://github.com/owner/repo/issues/301",
        }

        mock_orchestrator = AsyncMock()

        async def add_to_project(ctx, recommendation=None):
            ctx.project_item_id = "PVTI_301"
            return "PVTI_301"

        mock_orchestrator.add_to_project_with_backlog.side_effect = add_to_project
        mock_orchestrator.create_all_sub_issues.side_effect = RuntimeError("sub-issue API down")

        with (
            patch(
                "src.api.pipelines.resolve_repository",
                new_callable=AsyncMock,
                return_value=("owner", "repo"),
            ),
            patch("src.api.pipelines.github_projects_service", mock_github_service),
            patch(
                "src.api.pipelines.get_workflow_config",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch("src.api.pipelines.set_workflow_config", new_callable=AsyncMock),
            patch(
                "src.api.pipelines.get_workflow_orchestrator",
                return_value=mock_orchestrator,
            ),
        ):
            resp = await client.post(
                "/api/v1/pipelines/PVT_1/launch",
                json={
                    "issue_description": "# Sub-issue error\n\nBreaks during creation.",
                    "pipeline_id": pipeline_id,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
