"""Structured health check endpoint (FR-020, FR-048).

Returns per-component health status following the IETF health check format:
- database: SELECT 1
- github_api: GET /rate_limit
- polling_loop: asyncio.Task state
- startup_checks: Configuration validation state
- version: Application version string

Also provides a readiness probe (GET /api/v1/ready) for Kubernetes-style
deployment gates (Phase 5 — FR-001 through FR-005).
"""

import time
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.logging_utils import get_logger

logger = get_logger(__name__)
router = APIRouter()

try:
    _APP_VERSION = version("solune-backend")
except PackageNotFoundError:
    _APP_VERSION = "0.0.0-dev"


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
        if not settings.github_client_secret:
            issues.append("GITHUB_CLIENT_SECRET not configured")
        if not settings.session_secret_key or len(settings.session_secret_key) < 32:
            issues.append("SESSION_SECRET_KEY not configured or too short")
        if not settings.github_webhook_secret:
            issues.append("GITHUB_WEBHOOK_SECRET not configured")

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


# ── Readiness probe (Phase 5) ──────────────────────────────────────────


class ReadinessCheckResult(BaseModel):
    """Single subsystem check result (IETF health-check format)."""

    component_id: str
    component_type: str = "component"
    status: str  # "pass" | "fail"
    time: str
    output: str | None = None


class ReadinessResponse(BaseModel):
    """Top-level readiness response (IETF health-check format)."""

    status: str  # "pass" | "fail"
    checks: dict[str, list[dict[str, Any]]]


async def _readiness_check_db() -> ReadinessCheckResult:
    """Verify database is writeable via INSERT + DELETE on scratch table."""
    now = datetime.now(UTC).isoformat()
    try:
        db = get_db()
        await db.execute("CREATE TABLE IF NOT EXISTS _readiness_scratch (id INTEGER PRIMARY KEY)")
        await db.execute("INSERT OR REPLACE INTO _readiness_scratch (id) VALUES (1)")
        await db.execute("DELETE FROM _readiness_scratch WHERE id = 1")
        await db.commit()
        return ReadinessCheckResult(component_id="database:writeable", status="pass", time=now)
    except Exception as exc:
        logger.warning("Readiness: database write check failed — %s", exc, exc_info=True)
        return ReadinessCheckResult(
            component_id="database:writeable",
            status="fail",
            time=now,
            output="Database write check failed",
        )


def _readiness_check_oauth() -> ReadinessCheckResult:
    """Verify GitHub OAuth client ID and secret are non-empty."""
    from src.config import get_settings

    now = datetime.now(UTC).isoformat()
    settings = get_settings()
    if settings.github_client_id and settings.github_client_secret:
        return ReadinessCheckResult(component_id="oauth:configured", status="pass", time=now)
    return ReadinessCheckResult(
        component_id="oauth:configured",
        status="fail",
        time=now,
        output="GitHub OAuth client ID or secret is empty",
    )


def _readiness_check_encryption() -> ReadinessCheckResult:
    """Verify EncryptionService is enabled (has a valid key)."""
    now = datetime.now(UTC).isoformat()
    try:
        from src.config import get_settings
        from src.services.encryption import EncryptionService

        settings = get_settings()
        svc = EncryptionService(settings.encryption_key, debug=settings.debug)
        if svc.enabled:
            return ReadinessCheckResult(component_id="encryption:enabled", status="pass", time=now)
        return ReadinessCheckResult(
            component_id="encryption:enabled",
            status="fail",
            time=now,
            output="Encryption service is disabled (no valid key)",
        )
    except Exception as exc:
        return ReadinessCheckResult(
            component_id="encryption:enabled",
            status="fail",
            time=now,
            output=f"Encryption check failed: {exc}",
        )


def _readiness_check_polling() -> ReadinessCheckResult:
    """Verify the polling task is alive or intentionally disabled."""
    now = datetime.now(UTC).isoformat()
    try:
        from src.config import get_settings

        settings = get_settings()
        # If polling is intentionally disabled (interval=0), that's a pass
        if settings.copilot_polling_interval == 0:
            return ReadinessCheckResult(component_id="polling:alive", status="pass", time=now)

        from src.services.copilot_polling import _polling_task
        from src.services.copilot_polling.state import _polling_state

        if _polling_task is not None and not _polling_task.done():
            return ReadinessCheckResult(component_id="polling:alive", status="pass", time=now)
        if _polling_state.is_running:
            return ReadinessCheckResult(component_id="polling:alive", status="pass", time=now)
        return ReadinessCheckResult(
            component_id="polling:alive",
            status="fail",
            time=now,
            output="Polling task has crashed and is not intentionally disabled",
        )
    except Exception as exc:
        return ReadinessCheckResult(
            component_id="polling:alive",
            status="fail",
            time=now,
            output=f"Polling check failed: {exc}",
        )


@router.get("/ready", tags=["health"])
async def readiness_check() -> JSONResponse:
    """Kubernetes-style readiness probe (Phase 5).

    Returns HTTP 200 only when ALL four subsystem checks pass.
    Returns HTTP 503 with IETF health-check-format body on any failure.
    """
    db_result = await _readiness_check_db()
    oauth_result = _readiness_check_oauth()
    encryption_result = _readiness_check_encryption()
    polling_result = _readiness_check_polling()

    all_results = [db_result, oauth_result, encryption_result, polling_result]
    has_failure = any(r.status == "fail" for r in all_results)
    overall = "fail" if has_failure else "pass"
    status_code = 503 if has_failure else 200

    checks: dict[str, list[dict[str, Any]]] = {}
    for r in all_results:
        entry: dict[str, Any] = {
            "component_id": r.component_id,
            "component_type": r.component_type,
            "status": r.status,
            "time": r.time,
        }
        if r.output is not None:
            entry["output"] = r.output
        checks[r.component_id] = [entry]

    return JSONResponse(
        status_code=status_code,
        content={"status": overall, "checks": checks},
    )


# ── Rate-limit history (Phase 5, optional) ─────────────────────────────


@router.get("/rate-limit/history", tags=["health"])
async def rate_limit_history(
    hours: int = Query(default=24, ge=1, le=168),
) -> JSONResponse:
    """Return rate-limit time-series snapshots (optional, P3).

    Query params:
        hours: Number of hours of history (1-168, default 24).
    """
    from src.services.rate_limit_tracker import RateLimitTracker

    tracker = RateLimitTracker()
    snapshots = await tracker.get_history(hours=hours)
    return JSONResponse(
        content={
            "snapshots": snapshots,
            "hours": hours,
            "count": len(snapshots),
        },
    )
