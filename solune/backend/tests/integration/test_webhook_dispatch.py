from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.api.webhooks import _processed_delivery_ids
from src.config import Settings
from src.exceptions import AppException


def _sign_payload(payload: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _build_webhook_app() -> FastAPI:
    from src.api.webhooks import router as webhooks_router

    app = FastAPI()

    @app.exception_handler(AppException)
    async def _handle_app_exception(_request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "details": exc.details},
        )

    app.include_router(webhooks_router, prefix="/api/v1/webhooks")
    return app


@pytest.fixture(autouse=True)
def _clear_processed_delivery_ids():
    _processed_delivery_ids.clear()
    yield
    _processed_delivery_ids.clear()


@pytest.mark.anyio
async def test_webhook_ready_for_review_reports_action_needed_without_webhook_token():
    webhook_secret = "integration-secret"
    settings = Settings(
        github_client_id="id",
        github_client_secret="secret",
        session_secret_key="a" * 64,
        debug=True,
        github_webhook_secret=webhook_secret,
        github_webhook_token=None,
        _env_file=None,
    )
    payload = {
        "action": "ready_for_review",
        "pull_request": {
            "number": 42,
            "draft": False,
            "merged": False,
            "body": "Fixes #10",
            "head": {"ref": "copilot/issue-10"},
            "user": {"login": "copilot-swe-agent[bot]"},
        },
        "repository": {
            "owner": {"login": "octocat"},
            "name": "demo-repo",
        },
    }
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, webhook_secret)

    transport = ASGITransport(app=_build_webhook_app())
    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
        patch("src.api.webhooks.github_projects_service", AsyncMock()),
        patch("src.api.webhooks.get_db", return_value=AsyncMock()),
        patch("src.api.webhooks.log_event", new_callable=AsyncMock),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "delivery-ready-1",
                    "X-Hub-Signature-256": signature,
                },
            )
    await transport.aclose()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "detected"
    assert data["issue_number"] == 10
    assert data["action_needed"] == "update_issue_status_to_in_review"


@pytest.mark.anyio
async def test_webhook_duplicate_delivery_short_circuits_second_dispatch():
    webhook_secret = "integration-secret"
    settings = Settings(
        github_client_id="id",
        github_client_secret="secret",
        session_secret_key="a" * 64,
        debug=True,
        github_webhook_secret=webhook_secret,
        _env_file=None,
    )
    payload = {"zen": "Keep it logically awesome."}
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, webhook_secret)

    transport = ASGITransport(app=_build_webhook_app())
    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            first = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "ping",
                    "X-GitHub-Delivery": "delivery-ping-1",
                    "X-Hub-Signature-256": signature,
                },
            )
            second = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "ping",
                    "X-GitHub-Delivery": "delivery-ping-1",
                    "X-Hub-Signature-256": signature,
                },
            )
    await transport.aclose()

    assert first.status_code == 200
    assert first.json()["status"] == "ignored"
    assert second.status_code == 200
    assert second.json() == {"status": "duplicate", "delivery_id": "delivery-ping-1"}
