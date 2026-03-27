"""
Performance test for board data load time.

Measures the real response time of GET /api/v1/board/projects/{project_id}
against a running backend with a live GitHub session.

Prerequisites
-------------
* Running backend: ``docker compose up -d`` (or ``uvicorn``)
* Env vars:
    PERF_GITHUB_TOKEN  - a GitHub personal access token with ``project`` scope
    PERF_PROJECT_ID    - the GitHub project node ID to test (e.g. PVT_xxx)

These are never committed - they're developer-local or CI-secret only.

Run
---
    PERF_GITHUB_TOKEN=ghp_xxx PERF_PROJECT_ID=PVT_xxx \
        pytest tests/performance/ -v -m performance

The ``performance`` marker keeps these out of the normal test suite.
"""

from __future__ import annotations

import os
import time

import httpx
import pytest

BACKEND_URL = os.environ.get("PERF_BACKEND_URL", "http://localhost:8000")
GITHUB_TOKEN = os.environ.get("PERF_GITHUB_TOKEN")
PROJECT_ID = os.environ.get("PERF_PROJECT_ID")
MAX_LOAD_SECONDS = 10


def _skip_if_missing_prereqs() -> None:
    if not GITHUB_TOKEN:
        pytest.skip("PERF_GITHUB_TOKEN not set")
    if not PROJECT_ID:
        pytest.skip("PERF_PROJECT_ID not set")


async def _ensure_backend_running(client: httpx.AsyncClient) -> None:
    try:
        resp = await client.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
        if resp.status_code != 200:
            pytest.skip(f"Backend unhealthy (status {resp.status_code})")
    except httpx.ConnectError:
        pytest.skip("Backend not reachable")


async def _create_session(client: httpx.AsyncClient) -> httpx.AsyncClient:
    """Authenticate via the backend's dev-login endpoint and return a client with session cookies."""
    # The backend uses cookie-based sessions (cookie name: "session_id").
    # POST to /api/v1/auth/dev-login with a GitHub PAT to obtain a real
    # session cookie.  This endpoint is only available when DEBUG=true.
    resp = await client.post(
        f"{BACKEND_URL}/api/v1/auth/dev-login",
        json={"github_token": GITHUB_TOKEN},
        timeout=10,
    )
    if resp.status_code == 200:
        # The response sets a session_id cookie automatically.
        return client

    pytest.skip(
        f"Could not authenticate via dev-login (status {resp.status_code}). "
        "Ensure the backend is running with DEBUG=true and PERF_GITHUB_TOKEN is a valid GitHub PAT."
    )
    return client  # unreachable, keeps type-checker happy


@pytest.mark.performance
class TestBoardLoadPerformance:
    """Board endpoint response-time assertions."""

    @pytest.mark.anyio
    async def test_board_data_loads_within_threshold(self) -> None:
        """GET /api/v1/board/projects/{id} must respond in < 10 s."""
        _skip_if_missing_prereqs()

        async with httpx.AsyncClient() as client:
            await _ensure_backend_running(client)
            client = await _create_session(client)

            start = time.monotonic()
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/board/projects/{PROJECT_ID}",
                timeout=MAX_LOAD_SECONDS + 5,  # generous timeout so we measure, not cut off
            )
            elapsed = time.monotonic() - start

            print(f"\n  ⏱  Board data response: {elapsed:.2f}s  (status {resp.status_code})")

            assert resp.status_code == 200, (
                f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
            )
            assert elapsed < MAX_LOAD_SECONDS, (
                f"Board data took {elapsed:.1f}s — exceeds {MAX_LOAD_SECONDS}s threshold"
            )

    @pytest.mark.anyio
    async def test_board_data_cached_response_is_fast(self) -> None:
        """Second request (cached) should be significantly faster."""
        _skip_if_missing_prereqs()

        async with httpx.AsyncClient() as client:
            await _ensure_backend_running(client)
            client = await _create_session(client)

            # First request — populates cache
            await client.get(
                f"{BACKEND_URL}/api/v1/board/projects/{PROJECT_ID}",
                timeout=MAX_LOAD_SECONDS + 5,
            )

            # Second request — should hit cache
            start = time.monotonic()
            resp = await client.get(
                f"{BACKEND_URL}/api/v1/board/projects/{PROJECT_ID}",
                timeout=5,
            )
            elapsed = time.monotonic() - start

            print(f"\n  ⏱  Cached board response: {elapsed:.2f}s  (status {resp.status_code})")

            assert resp.status_code == 200
            # Cached response should be well under 2 seconds
            assert elapsed < 2, f"Cached board data took {elapsed:.1f}s — cache may not be working"
