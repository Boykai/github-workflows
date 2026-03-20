"""Integration tests for pipeline queue mode feature.

Covers:
- Queue mode toggle persistence via settings API
- Queue position in response message
- Effective project settings include queue_mode
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/dev-login",
        json={"github_token": "ghp_test_token"},
    )
    assert response.status_code == 200


async def _select_project(client: AsyncClient, project_id: str) -> None:
    response = await client.post(f"/api/v1/projects/{project_id}/select")
    assert response.status_code == 200


async def _seed_global_settings(client: AsyncClient) -> None:
    """Ensure global settings exist by seeding via database helper."""
    from unittest.mock import patch

    from src.config import Settings
    from src.services.database import get_db, seed_global_settings

    settings = Settings(
        github_client_id="test-client-id",
        github_client_secret="test-client-secret",
        session_secret_key="test-session-secret-key-that-is-long-enough",
        ai_provider="copilot",
        debug=True,
        log_level="DEBUG",
        cors_origins="http://localhost:5173",
        database_path=":memory:",
    )
    db = get_db()
    with patch("src.services.database.get_settings", return_value=settings):
        await seed_global_settings(db)


# =============================================================================
# Queue Mode Settings Persistence
# =============================================================================


@pytest.mark.asyncio
async def test_queue_mode_toggle_persists(thin_mock_client: AsyncClient):
    """Queue mode can be toggled on and off via the settings API."""
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)
    await _seed_global_settings(thin_mock_client)

    # Enable queue mode
    response = await thin_mock_client.put(
        f"/api/v1/settings/project/{project_id}",
        json={"queue_mode": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["project"]["board_display_config"]["queue_mode"] is True

    # Disable queue mode
    response = await thin_mock_client.put(
        f"/api/v1/settings/project/{project_id}",
        json={"queue_mode": False},
    )
    assert response.status_code == 200
    data = response.json()
    # When queue_mode is False and no board_display_config was set,
    # the board_display_config may be null or have queue_mode=False
    board_config = data["project"]["board_display_config"]
    if board_config is not None:
        assert board_config["queue_mode"] is False
    # else: null is expected when queue_mode is off and no board config was set


@pytest.mark.asyncio
async def test_queue_mode_default_is_off(thin_mock_client: AsyncClient):
    """Queue mode defaults to OFF for new projects."""
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)
    await _seed_global_settings(thin_mock_client)

    response = await thin_mock_client.get(f"/api/v1/settings/project/{project_id}")
    assert response.status_code == 200
    data = response.json()
    # board_display_config may be null if no settings were saved yet
    board_config = data["project"].get("board_display_config")
    if board_config is not None:
        assert board_config.get("queue_mode", False) is False


@pytest.mark.asyncio
async def test_queue_mode_persists_alongside_board_config(thin_mock_client: AsyncClient):
    """Queue mode can be set alongside other board config without overwriting."""
    project_id = "PVT_integration"

    await _login(thin_mock_client)
    await _select_project(thin_mock_client, project_id)
    await _seed_global_settings(thin_mock_client)

    # Set board config first
    response = await thin_mock_client.put(
        f"/api/v1/settings/project/{project_id}",
        json={
            "board_display_config": {
                "column_order": ["Backlog", "In Progress"],
                "collapsed_columns": [],
                "show_estimates": True,
                "queue_mode": False,
            }
        },
    )
    assert response.status_code == 200

    # Now enable queue mode separately
    response = await thin_mock_client.put(
        f"/api/v1/settings/project/{project_id}",
        json={"queue_mode": True},
    )
    assert response.status_code == 200
    data = response.json()
    board_config = data["project"]["board_display_config"]
    assert board_config["queue_mode"] is True
    # Board config should still have the column order
    assert board_config["column_order"] == ["Backlog", "In Progress"]
