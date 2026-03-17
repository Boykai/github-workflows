"""Structured health check endpoint (FR-020, FR-048).

Returns per-component health status following the IETF health check format:
- database: SELECT 1
- github_api: GET /rate_limit
- polling_loop: asyncio.Task state
- startup_checks: Configuration validation state
- version: Application version string
"""

import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.logging_utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

_APP_VERSION = "0.1.0"


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
        logger.warning("Health check: database failed — %s", exc, exc_info=True)
        return {"status": "fail", "output": "database connectivity"}


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
        logger.warning("Health check: github_api failed — %s", exc, exc_info=True)
        return {"status": "fail", "output": "GitHub API connectivity"}


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
        logger.warning("Health check: polling_loop failed — %s", exc, exc_info=True)
        return {"status": "warn", "observed_value": "error"}


def _check_startup_config() -> dict:
    """Validate that startup configuration is complete and secure."""
    try:
        from src.config import get_settings

        settings = get_settings()
        issues: list[str] = []

        if not settings.encryption_key:
            issues.append("ENCRYPTION_KEY not configured")
        if not settings.github_client_id:
            issues.append("GITHUB_CLIENT_ID not configured")

        if issues:
            return {
                "status": "warn",
                "observed_value": "incomplete",
                "issues": issues,
            }
        return {"status": "pass", "observed_value": "valid"}
    except Exception as exc:
        logger.warning("Health check: startup_checks failed — %s", exc, exc_info=True)
        return {"status": "warn", "observed_value": "error"}


@router.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    """Structured health check for Docker and load balancers.

    Returns 200 for pass/warn, 503 for fail.
    Includes startup validation state and version per FR-048.
    """
    db_result = await _check_database()
    github_result = await _check_github_api()
    polling_result = _check_polling_loop()
    startup_result = _check_startup_config()

    checks = {
        "database": [db_result],
        "github_api": [github_result],
        "polling_loop": [polling_result],
        "startup_checks": [startup_result],
    }

    has_failure = any(c[0]["status"] == "fail" for c in checks.values())
    overall = "fail" if has_failure else "pass"
    status_code = 503 if has_failure else 200

    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall,
            "version": _APP_VERSION,
            "checks": checks,
        },
    )
