from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.constants import SESSION_COOKIE_NAME


@pytest.mark.anyio
async def test_auth_callback_redirects_to_frontend_and_sets_cookie(
    client,
    mock_session,
    mock_github_auth_service,
    mock_settings,
):
    mock_settings.frontend_url = "https://frontend.example"
    mock_github_auth_service.validate_state = MagicMock(return_value=True)
    mock_github_auth_service.create_session.return_value = mock_session

    response = await client.get(
        "/api/v1/auth/github/callback",
        params={"code": "valid-code", "state": "valid-state"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "https://frontend.example/auth/callback"
    assert SESSION_COOKIE_NAME in response.headers.get("set-cookie", "")


@pytest.mark.anyio
async def test_auth_callback_rejects_invalid_state(client, mock_github_auth_service):
    mock_github_auth_service.validate_state = MagicMock(return_value=False)

    response = await client.get(
        "/api/v1/auth/github/callback",
        params={"code": "any-code", "state": "expired-state"},
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert response.json()["error"] == "Invalid or expired OAuth state"
