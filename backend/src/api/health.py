"""Structured health check endpoint (FR-020).

Returns per-component health status following the IETF health check format:
- database: SELECT 1
- github_api: GET /rate_limit
- polling_loop: asyncio.Task state
"""

import logging
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db():
    """Import lazily to avoid circular imports."""
    from src.services.database import get_db as _get_db

    return _get_db()


async def _check_database() -> dict:
    """Check database connectivity with SELECT 1."""
    try:
        db = get_db()
        t0 = time.monotonic()
        await db.execute("SELECT 1")
        elapsed = round((time.monotonic() - t0) * 1000)
        return {"status": "pass", "time": f"{elapsed}ms"}
    except Exception as exc:
        logger.warning("Health check: database failed — %s", exc)
        return {"status": "fail", "output": str(exc)}


async def _check_github_api() -> dict:
    """Check GitHub API reachability via /rate_limit."""
    try:
        import httpx

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.github.com/rate_limit")
        elapsed = round((time.monotonic() - t0) * 1000)
        if resp.status_code < 500:
            return {"status": "pass", "time": f"{elapsed}ms"}
        return {"status": "fail", "output": f"HTTP {resp.status_code}"}
    except Exception as exc:
        logger.warning("Health check: github_api failed — %s", exc)
        return {"status": "fail", "output": str(exc)}


def _check_polling_loop() -> dict:
    """Check if the copilot polling task is alive."""
    try:
        from src.services.copilot_polling import _polling_task
        from src.services.copilot_polling.state import _polling_state

        if _polling_task is not None and not _polling_task.done():
            return {"status": "pass", "observed_value": "running"}
        if _polling_state.is_running:
            return {"status": "pass", "observed_value": "running"}
        return {"status": "warn", "observed_value": "stopped"}
    except Exception as exc:
        logger.warning("Health check: polling_loop failed — %s", exc)
        return {"status": "warn", "observed_value": f"error: {exc}"}


@router.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    """Structured health check for Docker and load balancers.

    Returns 200 for pass/warn, 503 for fail.
    """
    db_result = await _check_database()
    github_result = await _check_github_api()
    polling_result = _check_polling_loop()

    checks = {
        "database": [db_result],
        "github_api": [github_result],
        "polling_loop": [polling_result],
    }

    has_failure = any(c[0]["status"] == "fail" for c in checks.values())
    overall = "fail" if has_failure else "pass"
    status_code = 503 if has_failure else 200

    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "checks": checks},
    )
