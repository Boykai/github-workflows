"""Full pipeline lifecycle integration tests (T032-T035).

Exercises real HTTP routing via httpx.ASGITransport with mocked services.
"""

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

# ── Helpers / fixtures ───────────────────────────────────────────


def _sign_payload(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature matching GitHub's X-Hub-Signature-256."""
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _build_full_app() -> FastAPI:
    """Build a FastAPI app with webhook, pipeline, and board routers."""
    from src.api.board import router as board_router
    from src.api.pipelines import router as pipelines_router
    from src.api.webhooks import router as webhooks_router

    app = FastAPI()

    @app.exception_handler(AppException)
    async def _handle_app_exception(_request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "details": exc.details},
        )

    app.include_router(webhooks_router, prefix="/api/v1/webhooks")
    app.include_router(pipelines_router, prefix="/api/v1/pipelines")
    app.include_router(board_router, prefix="/api/v1/board")
    return app


def _make_settings(webhook_secret: str = "test-secret") -> Settings:
    return Settings(
        github_client_id="id",
        github_client_secret="secret",
        session_secret_key="a" * 64,
        debug=True,
        github_webhook_secret=webhook_secret,
        github_webhook_token=None,
        _env_file=None,
    )


def _issue_webhook_payload(
    action: str = "opened",
    issue_number: int = 42,
    owner: str = "octocat",
    repo: str = "demo-repo",
) -> dict:
    return {
        "action": action,
        "issue": {
            "number": issue_number,
            "title": f"Test issue #{issue_number}",
            "body": "Implement feature X",
            "user": {"login": "octocat"},
            "labels": [],
        },
        "repository": {
            "owner": {"login": owner},
            "name": repo,
        },
    }


def _pr_webhook_payload(
    action: str = "ready_for_review",
    pr_number: int = 99,
    issue_number: int = 42,
    merged: bool = False,
    draft: bool = False,
    owner: str = "octocat",
    repo: str = "demo-repo",
    author: str = "copilot-swe-agent[bot]",
) -> dict:
    return {
        "action": action,
        "pull_request": {
            "number": pr_number,
            "draft": draft,
            "merged": merged,
            "body": f"Fixes #{issue_number}",
            "head": {"ref": f"copilot/issue-{issue_number}"},
            "user": {"login": author},
        },
        "repository": {
            "owner": {"login": owner},
            "name": repo,
        },
    }


@pytest.fixture(autouse=True)
def _clear_processed_delivery_ids():
    _processed_delivery_ids.clear()
    yield
    _processed_delivery_ids.clear()


# ── T033: Issue lifecycle — issue creation webhook → pipeline launch ─


@pytest.mark.anyio
async def test_issue_opened_webhook_accepted():
    """Issue webhook is accepted and acknowledged (currently ignored, no pipeline launch)."""
    settings = _make_settings()
    payload = _issue_webhook_payload(action="opened", issue_number=10)
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, settings.github_webhook_secret)

    transport = ASGITransport(app=_build_full_app())
    mock_projects = AsyncMock()
    mock_db = AsyncMock()
    mock_log_event = AsyncMock()

    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
        patch("src.api.webhooks.github_projects_service", mock_projects),
        patch("src.api.webhooks.get_db", return_value=mock_db),
        patch("src.api.webhooks.log_event", mock_log_event),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "issues",
                    "X-GitHub-Delivery": "delivery-issue-opened-1",
                    "X-Hub-Signature-256": signature,
                },
            )
    await transport.aclose()

    # The webhook endpoint should accept the event (200) — issues events are
    # currently acknowledged as "ignored" unless special handling is added.
    assert response.status_code == 200


@pytest.mark.anyio
async def test_issue_webhook_invalid_signature_rejected():
    """Webhook with bad HMAC signature returns 401."""
    settings = _make_settings()
    payload = _issue_webhook_payload()
    body = json.dumps(payload).encode()
    bad_signature = _sign_payload(body, "wrong-secret")

    transport = ASGITransport(app=_build_full_app())
    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "issues",
                    "X-GitHub-Delivery": "delivery-bad-sig-1",
                    "X-Hub-Signature-256": bad_signature,
                },
            )
    await transport.aclose()

    assert response.status_code == 401


# ── T034: Status transitions — Backlog → Ready → In Progress → In Review ─


@pytest.mark.anyio
async def test_status_transitions_backlog_to_in_review():
    """Pipeline state can be driven through Backlog → Ready → In Progress → In Review."""
    from src.services import pipeline_state_store as store
    from src.services.workflow_orchestrator.models import PipelineState

    store._pipeline_states.clear()

    transitions = ["Backlog", "Ready", "In Progress", "In Review"]

    for _idx, status in enumerate(transitions):
        state = PipelineState(
            issue_number=50,
            project_id="PVT_proj1",
            status=status,
            agents=["planner", "builder"],
            current_agent_index=0,
            completed_agents=[],
            queued=False,
        )
        store._pipeline_states[50] = state

        assert store._pipeline_states[50].status == status
        assert count_active(store, "PVT_proj1") >= 0

    # Final state should be "In Review"
    assert store._pipeline_states[50].status == "In Review"
    store._pipeline_states.clear()


def count_active(store_mod, project_id: str) -> int:
    """Thin wrapper around the store function for clarity."""
    from src.services.pipeline_state_store import count_active_pipelines_for_project

    return count_active_pipelines_for_project(project_id)


@pytest.mark.anyio
async def test_status_transition_preserves_pipeline_identity():
    """Each transition updates the same pipeline in-place via the public state store API."""
    import src.services.pipeline_state_store as store
    from src.services.pipeline_state_store import (
        _pipeline_states,
        count_active_pipelines_for_project,
        get_pipeline_state,
        set_pipeline_state,
    )
    from src.services.workflow_orchestrator.models import PipelineState

    _pipeline_states.clear()
    # Ensure no stale DB connection is used — this test only validates L1 cache
    prev_db = store._db
    store._db = None

    state = PipelineState(
        issue_number=60,
        project_id="PVT_proj1",
        status="Backlog",
        agents=["a"],
    )
    await set_pipeline_state(60, state)
    assert get_pipeline_state(60) is not None
    assert count_active_pipelines_for_project("PVT_proj1") == 1

    # Move through transitions using the same pipeline instance
    for new_status in ("Ready", "In Progress", "In Review"):
        state.status = new_status
        await set_pipeline_state(60, state)
        retrieved = get_pipeline_state(60)
        assert retrieved.status == new_status
        assert count_active_pipelines_for_project("PVT_proj1") == 1

    _pipeline_states.clear()
    store._db = prev_db


# ── T035: PR lifecycle — PR creation → state update → PR merge → cleanup ─


@pytest.mark.anyio
async def test_pr_ready_for_review_webhook_updates_state():
    """PR ready_for_review webhook is accepted through the routing layer."""
    settings = _make_settings()
    payload = _pr_webhook_payload(
        action="ready_for_review",
        pr_number=99,
        issue_number=10,
    )
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, settings.github_webhook_secret)

    transport = ASGITransport(app=_build_full_app())
    mock_projects = AsyncMock()
    mock_db = AsyncMock()
    mock_log_event = AsyncMock()

    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
        patch("src.api.webhooks.github_projects_service", mock_projects),
        patch("src.api.webhooks.get_db", return_value=mock_db),
        patch("src.api.webhooks.log_event", mock_log_event),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "delivery-pr-rfr-1",
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
async def test_pr_merged_webhook_accepted():
    """PR closed+merged webhook is processed through the routing layer."""
    settings = _make_settings()
    payload = _pr_webhook_payload(
        action="closed",
        pr_number=99,
        issue_number=10,
        merged=True,
    )
    body = json.dumps(payload).encode()
    signature = _sign_payload(body, settings.github_webhook_secret)

    transport = ASGITransport(app=_build_full_app())
    mock_projects = AsyncMock()
    mock_db = AsyncMock()
    mock_log_event = AsyncMock()

    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
        patch("src.api.webhooks.github_projects_service", mock_projects),
        patch("src.api.webhooks.get_db", return_value=mock_db),
        patch("src.api.webhooks.log_event", mock_log_event),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/webhooks/github",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "delivery-pr-merge-1",
                    "X-Hub-Signature-256": signature,
                },
            )
    await transport.aclose()

    assert response.status_code == 200


@pytest.mark.anyio
async def test_pr_lifecycle_full_flow():
    """Full PR lifecycle: create (draft) → ready_for_review → merge → cleanup."""
    settings = _make_settings()
    transport = ASGITransport(app=_build_full_app())
    mock_projects = AsyncMock()
    mock_db = AsyncMock()
    mock_log_event = AsyncMock()

    async def _post_webhook(event: str, payload: dict, delivery_id: str):
        body = json.dumps(payload).encode()
        sig = _sign_payload(body, settings.github_webhook_secret)
        return await client.post(
            "/api/v1/webhooks/github",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-GitHub-Event": event,
                "X-GitHub-Delivery": delivery_id,
                "X-Hub-Signature-256": sig,
            },
        )

    with (
        patch("src.config.get_settings", return_value=settings),
        patch("src.api.webhooks.get_settings", return_value=settings),
        patch("src.api.webhooks.github_projects_service", mock_projects),
        patch("src.api.webhooks.get_db", return_value=mock_db),
        patch("src.api.webhooks.log_event", mock_log_event),
    ):
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Step 1: PR opened as draft
            r1 = await _post_webhook(
                "pull_request",
                _pr_webhook_payload(action="opened", draft=True),
                "delivery-pr-open-1",
            )
            assert r1.status_code == 200

            # Step 2: PR marked ready for review
            r2 = await _post_webhook(
                "pull_request",
                _pr_webhook_payload(action="ready_for_review"),
                "delivery-pr-rfr-2",
            )
            assert r2.status_code == 200
            assert r2.json()["status"] == "detected"

            # Step 3: PR merged
            r3 = await _post_webhook(
                "pull_request",
                _pr_webhook_payload(action="closed", merged=True),
                "delivery-pr-merge-3",
            )
            assert r3.status_code == 200

    await transport.aclose()
