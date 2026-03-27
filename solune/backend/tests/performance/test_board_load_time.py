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
    """Authenticate via the backend's token-login flow and return a client with session cookies."""
    # The backend stores sessions in cookies set during the OAuth callback.
    # For perf tests we POST to the internal dev-token endpoint if available,
    # otherwise fall back to injecting the Authorization header directly.
    resp = await client.get(
        f"{BACKEND_URL}/api/v1/auth/me",
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return client

    # If Bearer auth isn't supported, try cookie-based session.
    # We send a request with the token as a cookie value that the backend
    # might accept via its session middleware.
    client.cookies.set("session", GITHUB_TOKEN)
    resp = await client.get(f"{BACKEND_URL}/api/v1/auth/me", timeout=10)
    if resp.status_code == 200:
        return client

    pytest.skip(
        f"Could not authenticate against backend (status {resp.status_code}). "
        "Ensure PERF_GITHUB_TOKEN is a valid session cookie or Bearer token."
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
