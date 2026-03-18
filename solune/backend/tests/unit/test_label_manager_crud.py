"""Tests for label_manager async CRUD operations.

Covers create, update, delete, and query operations against the GitHub API,
including the create-before-delete ordering fix in update_pipeline_label.
"""

from __future__ import annotations

from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

_MOD = "src.services.copilot_polling.label_manager"
_GH = "src.services.github_projects.github_projects_service"


def _response(status_code: int, parsed_data=None):
    """Build a mock GitHub REST response."""
    r = SimpleNamespace(status_code=status_code)
    if parsed_data is not None:
        r.parsed_data = parsed_data
    return r


def _patches(rest_mock: AsyncMock):
    """Patch the github_projects_service at its source so lazy imports pick it up."""
    stack = ExitStack()
    mock_gps = SimpleNamespace(rest_request=rest_mock)
    stack.enter_context(patch(_GH, mock_gps))
    return stack


# ── create_pipeline_label ──────────────────────────────────────────


class TestCreatePipelineLabel:
    async def test_returns_label_name_on_success(self):
        mock_rest = AsyncMock(return_value=_response(201))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import create_pipeline_label

            result = await create_pipeline_label("tok", "o", "r", 1, "build", "running")
        assert result == "solune:pipeline:1:stage:build:running"
        mock_rest.assert_awaited_once()

    async def test_returns_label_name_on_422_already_exists(self):
        mock_rest = AsyncMock(return_value=_response(422))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import create_pipeline_label

            result = await create_pipeline_label("tok", "o", "r", 5, "test", "pending")
        assert result == "solune:pipeline:5:stage:test:pending"

    async def test_returns_none_on_500_error(self):
        mock_rest = AsyncMock(return_value=_response(500))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import create_pipeline_label

            result = await create_pipeline_label("tok", "o", "r", 1, "build", "running")
        assert result is None

    async def test_returns_none_on_exception(self):
        mock_rest = AsyncMock(side_effect=RuntimeError("network"))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import create_pipeline_label

            result = await create_pipeline_label("tok", "o", "r", 1, "build", "running")
        assert result is None

    async def test_returns_none_when_response_is_none(self):
        mock_rest = AsyncMock(return_value=None)
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import create_pipeline_label

            result = await create_pipeline_label("tok", "o", "r", 1, "build", "running")
        assert result is None


# ── delete_pipeline_label ──────────────────────────────────────────


class TestDeletePipelineLabel:
    async def test_returns_true_on_success(self):
        mock_rest = AsyncMock(return_value=_response(204))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import delete_pipeline_label

            result = await delete_pipeline_label(
                "tok", "o", "r", "solune:pipeline:1:stage:build:running"
            )
        assert result is True
        mock_rest.assert_awaited_once()

    async def test_returns_false_on_exception(self):
        mock_rest = AsyncMock(side_effect=RuntimeError("not found"))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import delete_pipeline_label

            result = await delete_pipeline_label("tok", "o", "r", "nonexistent")
        assert result is False


# ── update_pipeline_label (bug fix: create-before-delete) ──────────


class TestUpdatePipelineLabel:
    async def test_creates_new_label_before_deleting_old(self):
        """Verify create-before-delete ordering to prevent state loss."""
        call_order: list[str] = []

        async def track_rest(token, method, url, **kw):
            call_order.append(method)
            if method == "POST":
                return _response(201)
            return _response(204)

        mock_rest = AsyncMock(side_effect=track_rest)
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import update_pipeline_label

            result = await update_pipeline_label("tok", "o", "r", 1, "build", "pending", "running")

        assert result == "solune:pipeline:1:stage:build:running"
        assert call_order == ["POST", "DELETE"], (
            f"Expected create (POST) before delete (DELETE), got {call_order}"
        )

    async def test_preserves_old_label_when_create_fails(self):
        """If new label creation fails, old label must NOT be deleted."""
        mock_rest = AsyncMock(return_value=_response(500))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import update_pipeline_label

            result = await update_pipeline_label("tok", "o", "r", 1, "build", "pending", "running")

        assert result is None
        # Only one call (POST for create) — no DELETE should have been issued.
        assert mock_rest.await_count == 1
        args = mock_rest.call_args_list[0]
        assert args[0][1] == "POST"

    async def test_returns_new_label_on_success(self):
        async def handle_rest(token, method, url, **kw):
            if method == "POST":
                return _response(201)
            return _response(204)

        mock_rest = AsyncMock(side_effect=handle_rest)
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import update_pipeline_label

            result = await update_pipeline_label(
                "tok", "o", "r", 42, "deploy", "running", "completed"
            )

        assert result == "solune:pipeline:42:stage:deploy:completed"

    async def test_tolerates_old_label_delete_failure(self):
        """Even if the old label DELETE fails, the new label is still returned."""

        async def handle_rest(token, method, url, **kw):
            if method == "POST":
                return _response(201)
            raise RuntimeError("delete failed")

        mock_rest = AsyncMock(side_effect=handle_rest)
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import update_pipeline_label

            result = await update_pipeline_label("tok", "o", "r", 1, "build", "pending", "running")

        # New label should still be returned (delete failure is non-fatal)
        assert result == "solune:pipeline:1:stage:build:running"


# ── query_pipeline_labels ──────────────────────────────────────────


class TestQueryPipelineLabels:
    async def test_returns_parsed_labels(self):
        labels_page = [
            {"name": "solune:pipeline:1:stage:build:running"},
            {"name": "solune:pipeline:1:stage:test:pending"},
            {"name": "bug"},  # non-pipeline, should be filtered out
        ]
        mock_rest = AsyncMock(return_value=SimpleNamespace(parsed_data=labels_page))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import query_pipeline_labels

            result = await query_pipeline_labels("tok", "o", "r")

        assert len(result) == 2
        assert result[0].run_id == 1
        assert result[0].stage_id == "build"
        assert result[1].stage_id == "test"

    async def test_handles_empty_response(self):
        mock_rest = AsyncMock(return_value=SimpleNamespace(parsed_data=[]))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import query_pipeline_labels

            result = await query_pipeline_labels("tok", "o", "r")

        assert result == []

    async def test_handles_api_exception(self):
        mock_rest = AsyncMock(side_effect=RuntimeError("api error"))
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import query_pipeline_labels

            result = await query_pipeline_labels("tok", "o", "r")

        assert result == []

    async def test_paginates_when_full_page_returned(self):
        """When first page returns 100 items, should request next page."""
        page1 = [{"name": f"solune:pipeline:1:stage:s{i}:running"} for i in range(100)]
        page2 = [{"name": "solune:pipeline:1:stage:final:completed"}]

        call_count = 0

        async def paginated_rest(token, method, url, params=None, **kw):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return SimpleNamespace(parsed_data=page1)
            return SimpleNamespace(parsed_data=page2)

        mock_rest = AsyncMock(side_effect=paginated_rest)
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import query_pipeline_labels

            result = await query_pipeline_labels("tok", "o", "r")

        assert len(result) == 101
        assert call_count == 2

    async def test_handles_none_response(self):
        mock_rest = AsyncMock(return_value=None)
        with _patches(mock_rest):
            from src.services.copilot_polling.label_manager import query_pipeline_labels

            result = await query_pipeline_labels("tok", "o", "r")

        assert result == []
