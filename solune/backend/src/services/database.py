"""SQLite database connection, initialization, and migration runner."""

import re
from datetime import UTC, datetime
from pathlib import Path

import aiosqlite

from src.config import get_settings
from src.logging_utils import get_logger

logger = get_logger(__name__)

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

    # Ensure directory exists with restricted permissions (0700)
    # Skip for in-memory databases (e.g. :memory: used in tests)
    db_dir = Path(db_path).parent
    is_in_memory = db_path == ":memory:" or db_path.startswith("file::memory:")
    if not is_in_memory and str(db_dir) != ".":
        db_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Restrict directory permissions so only the application user can access
        try:
            db_dir.chmod(0o700)
        except OSError:
            logger.warning("Could not set database directory permissions to 0700")

    logger.info("Initializing database at %s", db_path)

    # Open persistent connection
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row

    # Restrict database file permissions (0600) after creation
    # Skip for in-memory databases which have no file on disk
    if not is_in_memory:
        try:
            Path(db_path).chmod(0o600)
        except OSError:
            logger.warning("Could not set database file permissions to 0600")

    # Set pragmas (WAL mode, busy_timeout, foreign_keys)
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA busy_timeout=5000;")
    await db.execute("PRAGMA foreign_keys=ON;")

    # Integrity check before migrations
    db = await _check_integrity(db, db_path, is_in_memory)

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


async def _check_integrity(
    db: aiosqlite.Connection, db_path: str, is_in_memory: bool
) -> aiosqlite.Connection:
    """Run PRAGMA integrity_check. If corrupt, rename the file and start fresh."""
    try:
        cursor = await db.execute("PRAGMA integrity_check;")
        result = await cursor.fetchone()
        status = result[0] if result else "unknown"
    except (aiosqlite.DatabaseError, aiosqlite.OperationalError):
        logger.exception("integrity_check query failed for %s", db_path)
        status = "error"

    if status == "ok":
        return db

    logger.error("Database integrity check FAILED (%s): %s", db_path, status)

    if is_in_memory:
        logger.warning("In-memory database failed integrity check — continuing anyway")
        return db

    # Rename corrupt file and open a fresh connection
    await db.close()
    corrupt_name = f"{db_path}.corrupt.{int(datetime.now(UTC).timestamp())}"
    Path(db_path).rename(corrupt_name)
    logger.warning("Renamed corrupt database to %s — creating fresh database", corrupt_name)

    # Also move WAL/SHM sidecar files if present
    for suffix in ("-wal", "-shm"):
        sidecar = Path(db_path + suffix)
        if sidecar.exists():
            sidecar.rename(corrupt_name + suffix)

    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        Path(db_path).chmod(0o600)
    except OSError:
        logger.warning("Could not set recovered database file permissions to 0600")
    await db.execute("PRAGMA journal_mode=WAL;")
    await db.execute("PRAGMA busy_timeout=5000;")
    await db.execute("PRAGMA foreign_keys=ON;")
    return db


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
        await _reconcile_known_schema_drifts(db)
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
        except Exception as e:
            logger.exception("Failed to apply migration %s: %s", path.stem, e)
            raise

    await _reconcile_known_schema_drifts(db)
    logger.info("All migrations applied. Schema version: %d", current_version)


async def _reconcile_known_schema_drifts(db: aiosqlite.Connection) -> None:
    """Repair additive schema drift for persisted databases from older builds.

    Some long-lived SQLite volumes may report the latest schema version while
    still missing additive columns introduced in later app versions. Reconcile
    those cases defensively at startup so reads and writes do not crash.
    """
    if not await _table_exists(db, "agent_configs"):
        return

    if not await _column_exists(db, "agent_configs", "icon_name"):
        logger.warning("agent_configs table is missing icon_name; applying compatibility repair")
        await db.execute("ALTER TABLE agent_configs ADD COLUMN icon_name TEXT")
        await db.commit()


async def _table_exists(db: aiosqlite.Connection, table_name: str) -> bool:
    cursor = await db.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (table_name,),
    )
    return await cursor.fetchone() is not None


async def _column_exists(db: aiosqlite.Connection, table_name: str, column_name: str) -> bool:
    if not table_name.replace("_", "").isalnum():
        return False
    cursor = await db.execute(f"PRAGMA table_info([{table_name}])")
    rows = await cursor.fetchall()
    return any(row[1] == column_name for row in rows)


def _discover_migrations() -> list[tuple[int, Path]]:
    """
    Discover SQL migration files in the migrations directory.

    Files must match pattern: NNN_*.sql (e.g., 023_consolidated_schema.sql)
    Returns list of (version_number, file_path) sorted by version then filename.

    Logs a warning if duplicate version prefixes are detected.  Both files are
    still returned so existing deployments that already applied them are not
    broken.
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

    # Warn about duplicate version prefixes so operators can plan renumbering.
    # NOTE: Both files ARE applied because `_run_migrations()` pre-computes the
    # pending list (`v > current_version`) before iterating and only updates
    # schema_version once per version.  Duplicates are still applied in filename
    # order but renumbering is recommended to avoid confusion.
    seen: dict[int, list[str]] = {}
    for version, path in migrations:
        seen.setdefault(version, []).append(path.name)
    for version, files in sorted(seen.items()):
        if len(files) > 1:
            logger.warning(
                "Duplicate migration prefix %03d: %s — both files will be applied in "
                "filename order; consider renumbering to avoid ambiguity",
                version,
                ", ".join(files),
            )

    return sorted(migrations, key=lambda x: (x[0], x[1].name))


async def seed_global_settings(db: aiosqlite.Connection) -> None:
    """
    Seed global_settings from environment variables on first startup.

    Only inserts if the table has 0 rows (FR-020/FR-021).
    """
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM global_settings")
    row = await cursor.fetchone()

    if row is None or row["cnt"] > 0:
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
