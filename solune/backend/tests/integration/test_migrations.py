from __future__ import annotations

from pathlib import Path

import aiosqlite
import pytest

from src.services.database import _discover_migrations


async def _apply_migration(db: aiosqlite.Connection, path: Path) -> None:
    await db.executescript(path.read_text(encoding="utf-8"))
    await db.commit()


async def _table_names(db: aiosqlite.Connection) -> set[str]:
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    rows = await cursor.fetchall()
    return {row[0] if isinstance(row, tuple) else row["name"] for row in rows}


async def _column_names(db: aiosqlite.Connection, table: str) -> set[str]:
    cursor = await db.execute(f"PRAGMA table_info([{table}])")
    rows = await cursor.fetchall()
    return {row[1] if isinstance(row, tuple) else row["name"] for row in rows}


async def _index_names(db: aiosqlite.Connection) -> set[str]:
    cursor = await db.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    rows = await cursor.fetchall()
    return {row[0] if isinstance(row, tuple) else row["name"] for row in rows}


@pytest.mark.anyio
async def test_migrations_apply_sequentially_with_expected_schema_shapes():
    db = await aiosqlite.connect(":memory:")
    try:
        migration_map = dict(_discover_migrations())

        await _apply_migration(db, migration_map[23])
        tables_after_023 = await _table_names(db)
        assert {"agent_configs", "pipeline_configs", "project_settings", "user_sessions"}.issubset(
            tables_after_023
        )

        await _apply_migration(db, migration_map[24])
        assert "apps" in await _table_names(db)
        assert "active_app_name" in await _column_names(db, "user_sessions")

        await _apply_migration(db, migration_map[25])
        foreign_key_cursor = await db.execute("PRAGMA foreign_key_list(apps)")
        foreign_keys = await foreign_key_cursor.fetchall()
        target_tables = {row[2] if isinstance(row, tuple) else row["table"] for row in foreign_keys}
        assert "pipeline_configs" in target_tables

        await _apply_migration(db, migration_map[26])
        indexes_after_026 = await _index_names(db)
        assert {
            "idx_global_settings_admin",
            "idx_user_sessions_project",
            "idx_chat_messages_session",
            "idx_chat_proposals_session",
            "idx_chat_recommendations_session",
        }.issubset(indexes_after_026)

        await _apply_migration(db, migration_map[27])
        assert "done_items_cache" in await _table_names(db)
    finally:
        await db.close()


@pytest.mark.anyio
async def test_apps_data_survives_024_to_025_table_rebuild():
    db = await aiosqlite.connect(":memory:")
    try:
        migration_map = dict(_discover_migrations())

        await _apply_migration(db, migration_map[23])
        await _apply_migration(db, migration_map[24])

        await db.execute(
            """
            INSERT INTO pipeline_configs (id, project_id, name, description, stages, created_at, updated_at, is_preset, preset_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "pipeline-1",
                "PVT_integration",
                "Human Pipeline",
                "",
                "[]",
                "2026-03-16T00:00:00Z",
                "2026-03-16T00:00:00Z",
                0,
                "",
            ),
        )
        await db.execute(
            """
            INSERT INTO apps (name, display_name, description, directory_path, associated_pipeline_id, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("demo-app", "Demo App", "", "/tmp/demo-app", "pipeline-1", "active"),
        )
        await db.commit()

        await _apply_migration(db, migration_map[25])

        cursor = await db.execute(
            "SELECT associated_pipeline_id, status FROM apps WHERE name = ?",
            ("demo-app",),
        )
        row = await cursor.fetchone()
        assert row is not None
        values = (
            tuple(row) if isinstance(row, tuple) else (row["associated_pipeline_id"], row["status"])
        )
        assert values == ("pipeline-1", "active")
    finally:
        await db.close()


@pytest.mark.anyio
async def test_final_schema_matches_expected_latest_tables_and_columns():
    db = await aiosqlite.connect(":memory:")
    try:
        for _version, path in _discover_migrations():
            await _apply_migration(db, path)

        expected_tables = {
            "agent_configs",
            "apps",
            "chat_messages",
            "done_items_cache",
            "global_settings",
            "pipeline_configs",
            "pipeline_states",
            "project_settings",
            "user_sessions",
        }
        assert expected_tables.issubset(await _table_names(db))

        assert {"active_app_name", "selected_project_id"}.issubset(
            await _column_names(db, "user_sessions")
        )
        assert {"associated_pipeline_id", "repo_type", "external_repo_url"}.issubset(
            await _column_names(db, "apps")
        )
        assert {"project_id", "item_type", "items_json", "data_hash"}.issubset(
            await _column_names(db, "done_items_cache")
        )
    finally:
        await db.close()
