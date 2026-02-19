"""SQLite database connection, initialization, and migration runner."""

import logging
import os
import re
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from src.config import get_settings

logger = logging.getLogger(__name__)

# Module-level connection reference (set during init, used via get_db)
_connection: aiosqlite.Connection | None = None

# Path to migrations directory (sibling to services/)
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


async def init_database() -> aiosqlite.Connection:
    """
    Initialize the SQLite database: open connection, set pragmas, run migrations.

    Returns the persistent connection. Called once during FastAPI lifespan startup.
    """
    global _connection

    settings = get_settings()
    db_path = settings.database_path

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    logger.info("Initializing database at %s", db_path)

    # Open persistent connection
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    # Set pragmas (WAL mode, busy_timeout, foreign_keys)
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA busy_timeout=5000;")
    await db.execute("PRAGMA foreign_keys=ON;")

    # Run migrations
    await _run_migrations(db)

    _connection = db
    logger.info("Database initialized at %s", db_path)
    return db


async def close_database() -> None:
    """Close the persistent database connection. Called during lifespan shutdown."""
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
        logger.info("Database connection closed")


def get_db() -> aiosqlite.Connection:
    """
    Get the persistent database connection.

    Raises RuntimeError if database has not been initialized.
    """
    if _connection is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _connection


async def _run_migrations(db: aiosqlite.Connection) -> None:
    """
    Run pending SQL migrations.

    1. Create schema_version table if not exists
    2. Read current version
    3. Discover .sql migration files sorted by numeric prefix
    4. If DB version > app version, refuse to start
    5. Apply pending migrations sequentially in transactions
    """
    # Ensure schema_version table exists
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    await db.commit()

    # Get current version
    cursor = await db.execute("SELECT version FROM schema_version LIMIT 1")
    row = await cursor.fetchone()
    current_version = row["version"] if row else 0

    if not row:
        # Initialize version row
        now = datetime.now(UTC).isoformat()
        await db.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
            (0, now),
        )
        await db.commit()

    # Discover migration files
    migration_files = _discover_migrations()

    if not migration_files:
        logger.info("No migration files found in %s", MIGRATIONS_DIR)
        return

    # Highest available migration version
    max_migration_version = max(v for v, _ in migration_files)

    # Check for schema version ahead of app (refuse to start)
    if current_version > max_migration_version:
        error_msg = (
            f"Database schema version ({current_version}) is ahead of "
            f"application version ({max_migration_version}). "
            f"Refusing to start to protect data integrity."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Apply pending migrations
    pending = [(v, path) for v, path in migration_files if v > current_version]

    if not pending:
        logger.info("Database schema is up to date (version %d)", current_version)
        return

    for version, path in sorted(pending):
        logger.info("Applying migration %s (%d → %d)", path.stem, current_version, version)
        sql = path.read_text(encoding="utf-8")

        try:
            await db.executescript(sql)
            now = datetime.now(UTC).isoformat()
            await db.execute(
                "UPDATE schema_version SET version = ?, applied_at = ?",
                (version, now),
            )
            await db.commit()
            current_version = version
            logger.info("Applied migration %s (schema version: %d)", path.stem, version)
        except Exception:
            logger.exception("Failed to apply migration %s", path.stem)
            raise

    logger.info("All migrations applied. Schema version: %d", current_version)


def _discover_migrations() -> list[tuple[int, Path]]:
    """
    Discover SQL migration files in the migrations directory.

    Files must match pattern: NNN_*.sql (e.g., 001_initial_schema.sql)
    Returns list of (version_number, file_path) sorted by version.
    """
    if not MIGRATIONS_DIR.exists():
        return []

    pattern = re.compile(r"^(\d{3})_.*\.sql$")
    migrations: list[tuple[int, Path]] = []

    for path in sorted(MIGRATIONS_DIR.iterdir()):
        match = pattern.match(path.name)
        if match:
            version = int(match.group(1))
            migrations.append((version, path))

    return sorted(migrations, key=lambda x: x[0])


async def seed_global_settings(db: aiosqlite.Connection) -> None:
    """
    Seed global_settings from environment variables on first startup.

    Only inserts if the table has 0 rows (FR-020/FR-021).
    """
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM global_settings")
    row = await cursor.fetchone()

    if row["cnt"] > 0:
        logger.debug("Global settings already exist, skipping seed")
        return

    settings = get_settings()
    now = datetime.now(UTC).isoformat()

    await db.execute(
        """
        INSERT INTO global_settings (
            id, ai_provider, ai_model, ai_temperature,
            theme, default_view, sidebar_collapsed,
            default_repository, default_assignee, copilot_polling_interval,
            notify_task_status_change, notify_agent_completion,
            notify_new_recommendation, notify_chat_mention,
            allowed_models, updated_at
        ) VALUES (
            1, ?, ?, 0.7,
            'light', 'chat', 0,
            ?, ?, ?,
            1, 1, 1, 1,
            '[]', ?
        )
        """,
        (
            settings.ai_provider,
            settings.copilot_model,
            settings.default_repository,
            settings.default_assignee,
            settings.copilot_polling_interval,
            now,
        ),
    )
    await db.commit()
    logger.info("Global settings seeded from environment variables")
