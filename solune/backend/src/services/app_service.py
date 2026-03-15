# ruff: noqa: PTH103,PTH110,PTH118,PTH123
# ^^^ os.path used intentionally — CodeQL recognises os.path.realpath+startswith
# as a path-traversal sanitiser but does not recognise pathlib.Path.is_relative_to.
"""App lifecycle service for Solune multi-app management.

Handles CRUD operations, state transitions, directory scaffolding,
and path validation for applications managed by the platform.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from src.exceptions import ConflictError, NotFoundError, ValidationError
from src.logging_utils import get_logger
from src.models.app import (
    APP_NAME_PATTERN,
    RESERVED_NAMES,
    App,
    AppCreate,
    AppStatus,
    AppStatusResponse,
    AppUpdate,
)

logger = get_logger(__name__)

# Resolve the repository root (three levels up from this file)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
_APPS_DIR = _REPO_ROOT / "apps"
_APPS_DIR_REALPATH = os.path.realpath(str(_APPS_DIR)) + os.sep

# Valid state transitions: mapping from current status to set of allowed next statuses
_VALID_TRANSITIONS: dict[AppStatus, set[AppStatus]] = {
    AppStatus.CREATING: {AppStatus.ACTIVE, AppStatus.ERROR},
    AppStatus.ACTIVE: {AppStatus.STOPPED, AppStatus.ERROR},
    AppStatus.STOPPED: {AppStatus.ACTIVE},
    AppStatus.ERROR: {AppStatus.CREATING},
}


def validate_app_name(name: str) -> None:
    """Validate an application name for safety and uniqueness rules.

    Raises ``ValidationError`` on any violation.
    """
    if not re.match(APP_NAME_PATTERN, name):
        raise ValidationError(
            f"Invalid app name '{name}': must be 2-64 lowercase alphanumeric "
            "characters or hyphens, starting and ending with alphanumeric."
        )
    if len(name) < 2 or len(name) > 64:
        raise ValidationError(
            f"Invalid app name '{name}': length must be between 2 and 64 characters."
        )
    if name in RESERVED_NAMES:
        raise ValidationError(f"App name '{name}' is reserved and cannot be used.")
    # Path traversal protection
    if ".." in name or "/" in name or "\\" in name:
        raise ValidationError(f"Invalid app name '{name}': path traversal characters not allowed.")


def _safe_app_path(name: str) -> str:
    """Return a realpath-resolved app directory string, raising on any traversal.

    Uses ``os.path.realpath`` + ``str.startswith`` so that static analysis
    tools (CodeQL) can verify the path is confined to the ``apps/`` tree.
    """
    validate_app_name(name)
    candidate = os.path.join(str(_APPS_DIR), name)
    real = os.path.realpath(candidate)
    if not real.startswith(_APPS_DIR_REALPATH):
        raise ValidationError(f"Invalid app name '{name}': resolved path escapes apps directory.")
    return real


def _scaffold_app_directory(safe_dir: str, name: str, display_name: str, description: str) -> None:
    """Create the on-disk scaffold for a new application.

    ``safe_dir`` must already be validated via ``_safe_app_path``.
    """
    if os.path.exists(safe_dir):
        raise ConflictError(f"Directory already exists for app '{name}'.")

    os.makedirs(safe_dir)

    # README.md
    readme_path = os.path.join(safe_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# {display_name}\n\n{description}\n\nCreated by the Solune platform.\n")

    # config.json
    config_path = os.path.join(safe_dir, "config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "name": name,
                "display_name": display_name,
                "version": "0.1.0",
                "created_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            f,
            indent=2,
        )
        f.write("\n")

    # src/.gitkeep
    src_dir = os.path.join(safe_dir, "src")
    os.makedirs(src_dir)
    gitkeep = os.path.join(src_dir, ".gitkeep")
    with open(gitkeep, "w"):
        pass

    # CHANGELOG.md
    changelog_path = os.path.join(safe_dir, "CHANGELOG.md")
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(f"# Changelog — {display_name}\n\nAll notable changes will be documented here.\n")

    # docker-compose.yml template
    compose_path = os.path.join(safe_dir, "docker-compose.yml")
    with open(compose_path, "w", encoding="utf-8") as f:
        f.write(
            f"# Docker Compose for {display_name}\n# Extend or customize as needed.\nservices: {{}}\n"
        )


def _row_to_app(row: aiosqlite.Row) -> App:
    """Convert a database row to an App model."""
    return App(
        name=row["name"],
        display_name=row["display_name"],
        description=row["description"],
        directory_path=row["directory_path"],
        associated_pipeline_id=row["associated_pipeline_id"],
        status=AppStatus(row["status"]),
        repo_type=row["repo_type"],
        external_repo_url=row["external_repo_url"],
        port=row["port"],
        error_message=row["error_message"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------------------------------------------------------------------------
# CRUD Operations
# ---------------------------------------------------------------------------


async def create_app(db: aiosqlite.Connection, payload: AppCreate) -> App:
    """Create a new application with directory scaffolding."""
    validate_app_name(payload.name)

    # Check for duplicate
    cursor = await db.execute("SELECT name FROM apps WHERE name = ?", (payload.name,))
    if await cursor.fetchone():
        raise ConflictError(f"App '{payload.name}' already exists.")

    directory_path = f"apps/{payload.name}"

    # Validate and scaffold the directory
    safe_dir = _safe_app_path(payload.name)
    _scaffold_app_directory(safe_dir, payload.name, payload.display_name, payload.description)

    # Insert into database
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    await db.execute(
        """
        INSERT INTO apps (
            name, display_name, description, directory_path,
            associated_pipeline_id, status, repo_type, external_repo_url,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name,
            payload.display_name,
            payload.description,
            directory_path,
            payload.pipeline_id,
            AppStatus.ACTIVE.value,  # Scaffold completes immediately
            payload.repo_type.value,
            payload.external_repo_url,
            now,
            now,
        ),
    )
    await db.commit()

    logger.info("Created app '%s' at %s", payload.name, directory_path)

    cursor = await db.execute("SELECT * FROM apps WHERE name = ?", (payload.name,))
    row = await cursor.fetchone()
    if not row:
        raise NotFoundError(f"App '{payload.name}' not found after creation.")
    return _row_to_app(row)


async def list_apps(
    db: aiosqlite.Connection,
    *,
    status_filter: AppStatus | None = None,
) -> list[App]:
    """List all applications, optionally filtered by status."""
    if status_filter:
        cursor = await db.execute(
            "SELECT * FROM apps WHERE status = ? ORDER BY created_at DESC",
            (status_filter.value,),
        )
    else:
        cursor = await db.execute("SELECT * FROM apps ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [_row_to_app(row) for row in rows]


async def get_app(db: aiosqlite.Connection, name: str) -> App:
    """Get an application by name."""
    cursor = await db.execute("SELECT * FROM apps WHERE name = ?", (name,))
    row = await cursor.fetchone()
    if not row:
        raise NotFoundError(f"App '{name}' not found.")
    return _row_to_app(row)


async def update_app(db: aiosqlite.Connection, name: str, payload: AppUpdate) -> App:
    """Update application metadata."""
    app = await get_app(db, name)

    updates: dict[str, str | None] = {}
    if payload.display_name is not None:
        updates["display_name"] = payload.display_name
    if payload.description is not None:
        updates["description"] = payload.description
    if payload.pipeline_id is not None:
        updates["associated_pipeline_id"] = payload.pipeline_id

    if not updates:
        return app

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values())
    values.append(name)

    await db.execute(f"UPDATE apps SET {set_clause} WHERE name = ?", values)
    await db.commit()

    return await get_app(db, name)


# ---------------------------------------------------------------------------
# Lifecycle Operations
# ---------------------------------------------------------------------------


async def start_app(db: aiosqlite.Connection, name: str) -> AppStatusResponse:
    """Transition an app to 'active' status."""
    app = await get_app(db, name)

    if app.status == AppStatus.ACTIVE:
        return AppStatusResponse(
            name=app.name, status=app.status, port=app.port, error_message=app.error_message
        )

    if AppStatus.ACTIVE not in _VALID_TRANSITIONS.get(app.status, set()):
        raise ValidationError(
            f"Cannot start app '{name}': invalid transition from '{app.status.value}' to 'active'."
        )

    await db.execute(
        "UPDATE apps SET status = ?, error_message = NULL WHERE name = ?",
        (AppStatus.ACTIVE.value, name),
    )
    await db.commit()

    updated = await get_app(db, name)
    logger.info("Started app '%s'", name)
    return AppStatusResponse(
        name=updated.name,
        status=updated.status,
        port=updated.port,
        error_message=updated.error_message,
    )


async def stop_app(db: aiosqlite.Connection, name: str) -> AppStatusResponse:
    """Transition an app to 'stopped' status."""
    app = await get_app(db, name)

    if app.status == AppStatus.STOPPED:
        return AppStatusResponse(
            name=app.name, status=app.status, port=app.port, error_message=app.error_message
        )

    if AppStatus.STOPPED not in _VALID_TRANSITIONS.get(app.status, set()):
        raise ValidationError(
            f"Cannot stop app '{name}': invalid transition from '{app.status.value}' to 'stopped'."
        )

    await db.execute(
        "UPDATE apps SET status = ?, port = NULL WHERE name = ?",
        (AppStatus.STOPPED.value, name),
    )
    await db.commit()

    updated = await get_app(db, name)
    logger.info("Stopped app '%s'", name)
    return AppStatusResponse(
        name=updated.name,
        status=updated.status,
        port=updated.port,
        error_message=updated.error_message,
    )


async def delete_app(db: aiosqlite.Connection, name: str) -> None:
    """Delete an application — must be stopped or in error/creating state first."""
    app = await get_app(db, name)

    if app.status == AppStatus.ACTIVE:
        raise ValidationError(f"Cannot delete app '{name}': must stop the app first.")

    # Remove directory with traversal-safe path resolution
    validate_app_name(app.name)
    candidate = os.path.join(str(_APPS_DIR), app.name)
    real = os.path.realpath(candidate)
    if not real.startswith(_APPS_DIR_REALPATH):
        raise ValidationError(
            f"Invalid app name '{app.name}': resolved path escapes apps directory."
        )
    if os.path.exists(real):
        shutil.rmtree(real)
        logger.info("Removed directory for app '%s'", name)

    await db.execute("DELETE FROM apps WHERE name = ?", (name,))
    await db.commit()
    logger.info("Deleted app '%s'", name)


async def get_app_status(db: aiosqlite.Connection, name: str) -> AppStatusResponse:
    """Get the current status of an application."""
    app = await get_app(db, name)
    return AppStatusResponse(
        name=app.name, status=app.status, port=app.port, error_message=app.error_message
    )


def resolve_working_directory(active_app_name: str | None) -> str:
    """Return the working directory path for the active context.

    Returns ``apps/<app-name>`` when an app is selected, or ``solune``
    for the platform context.
    """
    if active_app_name:
        return f"apps/{active_app_name}"
    return "solune"
