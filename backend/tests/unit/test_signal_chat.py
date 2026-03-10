"""Unit tests for Signal chat error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.models.signal import SignalConnection
from src.services.signal_chat import _run_workflow_orchestration, process_signal_chat


class TestProcessSignalChat:
    """Tests for Signal #agent command handling."""

    @pytest.mark.asyncio
    async def test_logs_repository_resolution_failure_and_continues(
        self, mock_db, caplog: pytest.LogCaptureFixture
    ) -> None:
        conn = SignalConnection(
            github_user_id="user-123",
            signal_phone_encrypted="enc",
            signal_phone_hash="hash",
        )

        with (
            patch("src.services.agent_creator.get_active_session", return_value=None),
            patch("src.services.agent_creator.is_admin_user", new_callable=AsyncMock, return_value=True),
            patch(
                "src.services.agent_creator.handle_agent_command",
                new_callable=AsyncMock,
                return_value="created",
            ) as mock_handle,
            patch("src.services.database.get_db", return_value=mock_db),
            patch(
                "src.services.signal_chat._get_user_access_token",
                new_callable=AsyncMock,
                return_value="token",
            ),
            patch(
                "src.utils.resolve_repository",
                new_callable=AsyncMock,
                side_effect=RuntimeError("repo lookup failed"),
            ),
            patch("src.services.signal_chat._reply_with_audit", new_callable=AsyncMock) as mock_reply,
            caplog.at_level("WARNING"),
        ):
            await process_signal_chat(conn, "#agent create triager", "PVT_123", "+15551234567")

        assert "Signal: could not resolve repository for project PVT_123" in caplog.text
        assert "repo lookup failed" in caplog.text
        assert mock_handle.await_args.kwargs["owner"] is None
        assert mock_handle.await_args.kwargs["repo"] is None
        mock_reply.assert_awaited_once_with(conn, "+15551234567", "created")


class TestRunWorkflowOrchestration:
    """Tests for workflow follow-up error handling."""

    @pytest.mark.asyncio
    async def test_returns_generic_error_message(self) -> None:
        with patch(
            "src.services.workflow_orchestrator.get_workflow_config",
            new_callable=AsyncMock,
            side_effect=RuntimeError("secret orchestration failure"),
        ):
            result = await _run_workflow_orchestration(
                token="token",
                project_id="PVT_123",
                owner="octo",
                repo="repo",
                issue_number=42,
                issue_node_id="node-1",
                item_id="item-1",
                session_id=uuid4(),
            )

        assert result["sub_issues"] == 0
        assert result["agent"] is None
        assert "secret orchestration failure" not in result["error"]
        assert "Workflow follow-up could not be completed automatically." in result["error"]
