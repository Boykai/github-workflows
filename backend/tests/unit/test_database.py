"""Unit tests for database init, migration runner, and seeding.

Covers:
- init_database()
- _run_migrations()
- _discover_migrations()
- seed_global_settings()
- get_db() / close_database()
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

from src.services.database import (
    _column_exists,
    _discover_migrations,
    _run_migrations,
    close_database,
    get_db,
    init_database,
    seed_global_settings,
)


@pytest.fixture
async def raw_db():
    """Fresh in-memory SQLite database with NO migrations applied.

    Use for _run_migrations tests that need to start from scratch.
    """
    db = await aiosqlite.connect(":memory:")
    db.row_factory = aiosqlite.Row
    yield db
    await db.close()


# =============================================================================
# _discover_migrations
# =============================================================================


class TestDiscoverMigrations:
    def test_returns_sorted_tuples(self):
        migrations = _discover_migrations()
        assert len(migrations) >= 2
        versions = [v for v, _ in migrations]
        assert versions == sorted(versions)

    def test_first_migration_is_001(self):
        migrations = _discover_migrations()
        assert migrations[0][0] == 1
        assert "001_" in migrations[0][1].name

    def test_paths_are_valid(self):
        for _, path in _discover_migrations():
            assert path.exists()
            assert path.suffix == ".sql"

    def test_empty_dir_returns_empty(self, tmp_path):
        with patch("src.services.database.MIGRATIONS_DIR", tmp_path):
            assert _discover_migrations() == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        with patch("src.services.database.MIGRATIONS_DIR", tmp_path / "nope"):
            assert _discover_migrations() == []


# =============================================================================
# _run_migrations
# =============================================================================


class TestRunMigrations:
    async def test_creates_schema_version_table(self, raw_db):
        await _run_migrations(raw_db)
        cur = await raw_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        row = await cur.fetchone()
        assert row is not None

    async def test_applies_all_migrations(self, raw_db):
        """After running migrations, all tables should exist."""
        await _run_migrations(raw_db)
        for table in ("user_sessions", "user_preferences", "project_settings", "global_settings"):
            cur = await raw_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
            )
            assert (await cur.fetchone()) is not None, f"Table {table} missing"

    async def test_idempotent(self, raw_db):
        """Running migrations twice should not raise."""
        await _run_migrations(raw_db)
        await _run_migrations(raw_db)

    async def test_schema_version_tracks_progress(self, raw_db):
        await _run_migrations(raw_db)
        cur = await raw_db.execute("SELECT version FROM schema_version LIMIT 1")
        row = await cur.fetchone()
        migrations = _discover_migrations()
        max_ver = max(v for v, _ in migrations)
        assert row["version"] == max_ver

    async def test_refuses_if_db_ahead(self, raw_db):
        """If DB schema version is ahead of app version, raise RuntimeError."""
        await _run_migrations(raw_db)
        # Bump the DB version way ahead
        await raw_db.execute("UPDATE schema_version SET version = 9999")
        await raw_db.commit()
        with pytest.raises(RuntimeError, match="ahead of"):
            await _run_migrations(raw_db)

    async def test_repairs_missing_icon_name_column_when_schema_version_is_current(self, raw_db):
        """Startup should self-heal older agent_configs schemas on persisted volumes."""
        migrations = _discover_migrations()
        max_ver = max(v for v, _ in migrations)

        await raw_db.execute(
            "CREATE TABLE schema_version (version INTEGER NOT NULL, applied_at TEXT NOT NULL)"
        )
        await raw_db.execute(
            "INSERT INTO schema_version (version, applied_at) VALUES (?, datetime('now'))",
            (max_ver,),
        )

        old_agent_migrations = [
            path
            for _, path in migrations
            if path.name in {"007_agent_configs.sql", "014_agent_default_models.sql"}
        ]
        for migration_path in old_agent_migrations:
            await raw_db.executescript(Path(migration_path).read_text(encoding="utf-8"))
        await raw_db.commit()

        await _run_migrations(raw_db)

        cur = await raw_db.execute("PRAGMA table_info(agent_configs)")
        columns = [row[1] for row in await cur.fetchall()]
        assert "icon_name" in columns


# =============================================================================
# seed_global_settings
# =============================================================================


class TestSeedGlobalSettings:
    async def test_seeds_when_empty(self, mock_db, mock_settings):
        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)
        cur = await mock_db.execute("SELECT COUNT(*) as cnt FROM global_settings")
        row = await cur.fetchone()
        assert row["cnt"] == 1

    async def test_uses_settings_values(self, mock_db, mock_settings):
        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)
        cur = await mock_db.execute("SELECT ai_provider FROM global_settings WHERE id = 1")
        row = await cur.fetchone()
        assert row["ai_provider"] == mock_settings.ai_provider

    async def test_does_not_overwrite_existing(self, mock_db, mock_settings):
        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)
            # Seed again — should be a no-op
            await seed_global_settings(mock_db)
        cur = await mock_db.execute("SELECT COUNT(*) as cnt FROM global_settings")
        row = await cur.fetchone()
        assert row["cnt"] == 1


# =============================================================================
# get_db / close_database
# =============================================================================


class TestGetDb:
    def test_raises_when_not_initialized(self):
        with patch("src.services.database._connection", None):
            with pytest.raises(RuntimeError, match="not initialized"):
                get_db()

    def test_returns_connection_when_set(self, mock_db):
        with patch("src.services.database._connection", mock_db):
            assert get_db() is mock_db


class TestCloseDatabase:
    async def test_close_resets_connection(self):
        fake = AsyncMock()
        with patch("src.services.database._connection", fake):
            await close_database()
        fake.close.assert_awaited_once()

    async def test_close_noop_when_none(self):
        """Should not raise if already None."""
        with patch("src.services.database._connection", None):
            await close_database()  # Should not raise


# =============================================================================
# init_database (integration-ish, uses temp path)
# =============================================================================


class TestInitDatabase:
    async def test_creates_db_and_runs_migrations(self, tmp_path, mock_settings):
        db_path = str(tmp_path / "test.db")
        mock_settings.database_path = db_path
        with patch("src.services.database.get_settings", return_value=mock_settings):
            db = await init_database()
            try:
                cur = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'"
                )
                assert (await cur.fetchone()) is not None
            finally:
                await db.close()
                # Reset module-level connection
                import src.services.database as dbmod

                dbmod._connection = None


# =============================================================================
# _column_exists — SQL injection guard regression tests
# =============================================================================


class TestColumnExistsSQLInjectionGuard:
    """Regression tests for _column_exists input validation.

    Bug: _column_exists previously interpolated table_name via f-string without
    validation, allowing potential SQL injection through crafted table names.
    Fix: validate table_name is alphanumeric + underscore only.
    """

    async def test_rejects_sql_injection_in_table_name(self, raw_db: aiosqlite.Connection):
        """Malicious table names must be rejected (return False) instead of
        being interpolated into the PRAGMA statement."""
        result = await _column_exists(raw_db, "x); DROP TABLE user_sessions; --", "col")
        assert result is False

    async def test_rejects_parentheses_in_table_name(self, raw_db: aiosqlite.Connection):
        result = await _column_exists(raw_db, "tbl(evil)", "col")
        assert result is False

    async def test_allows_valid_table_name(self, raw_db: aiosqlite.Connection):
        await raw_db.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        assert await _column_exists(raw_db, "test_table", "name") is True
        assert await _column_exists(raw_db, "test_table", "nonexistent") is False

    async def test_allows_underscored_table_name(self, raw_db: aiosqlite.Connection):
        await raw_db.execute("CREATE TABLE my_table_v2 (col_a TEXT)")
        assert await _column_exists(raw_db, "my_table_v2", "col_a") is True
