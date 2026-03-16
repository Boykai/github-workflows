"""Tests for done_items_store — SQLite cache for Done-status project items.

Covers:
- init_done_items_store (DB reference registration)
- save_done_items / get_done_items round-trip for task and board types
- get_done_items returns None when no cached data exists
- clear_done_items removes rows for a project
- Upsert behaviour (save overwrites older snapshot)
- Graceful handling when DB is not initialised
- Board API fallback builds a partial board from DB-cached Done items
"""

from __future__ import annotations

import aiosqlite
import pytest

from src.services import done_items_store as store

# ── Schema ───────────────────────────────────────────────────────

_DONE_ITEMS_DDL = """
CREATE TABLE IF NOT EXISTS done_items_cache (
    project_id   TEXT    NOT NULL,
    item_type    TEXT    NOT NULL DEFAULT 'task',
    items_json   TEXT    NOT NULL,
    item_count   INTEGER NOT NULL DEFAULT 0,
    data_hash    TEXT,
    updated_at   TEXT    NOT NULL,
    PRIMARY KEY (project_id, item_type)
);
"""


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset():
    """Reset module state between tests."""
    old_db = store._db
    store._db = None
    yield
    store._db = old_db


@pytest.fixture
async def db():
    """In-memory SQLite with done_items_cache table."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.executescript(_DONE_ITEMS_DDL)
    await conn.commit()
    yield conn
    await conn.close()


# ── Tests ────────────────────────────────────────────────────────


class TestDoneItemsStoreInit:
    """init_done_items_store registers the DB connection."""

    @pytest.mark.asyncio
    async def test_init_sets_db(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)
        assert store._db is db


class TestDoneItemsRoundTrip:
    """save_done_items persists items that get_done_items can reload."""

    @pytest.mark.asyncio
    async def test_save_and_load_task_items(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)

        items = [
            {"title": "Fix bug", "status": "Done", "issue_number": 1},
            {"title": "Add tests", "status": "Done", "issue_number": 2},
        ]
        await store.save_done_items("PVT_proj1", items, item_type="task")

        loaded = await store.get_done_items("PVT_proj1", item_type="task")
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["title"] == "Fix bug"
        assert loaded[1]["issue_number"] == 2

    @pytest.mark.asyncio
    async def test_save_and_load_board_items(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)

        items = [{"item_id": "PVTI_1", "status": "Done", "title": "Done issue"}]
        await store.save_done_items("PVT_proj1", items, item_type="board")

        loaded = await store.get_done_items("PVT_proj1", item_type="board")
        assert loaded is not None
        assert len(loaded) == 1
        assert loaded[0]["item_id"] == "PVTI_1"

    @pytest.mark.asyncio
    async def test_separate_types_independent(self, db: aiosqlite.Connection):
        """task and board rows for the same project are independent."""
        await store.init_done_items_store(db)

        task_items = [{"title": "Task Done", "status": "Done"}]
        board_items = [{"item_id": "B1", "status": "Done"}]

        await store.save_done_items("PVT_proj1", task_items, item_type="task")
        await store.save_done_items("PVT_proj1", board_items, item_type="board")

        assert len(await store.get_done_items("PVT_proj1", item_type="task")) == 1
        assert len(await store.get_done_items("PVT_proj1", item_type="board")) == 1


class TestDoneItemsCacheMiss:
    """get_done_items returns None when no data exists."""

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)
        assert await store.get_done_items("PVT_nonexistent") is None

    @pytest.mark.asyncio
    async def test_returns_none_when_db_not_initialised(self):
        """Before init_done_items_store, get always returns None."""
        assert store._db is None
        assert await store.get_done_items("PVT_proj1") is None


class TestDoneItemsUpsert:
    """save_done_items overwrites the previous snapshot."""

    @pytest.mark.asyncio
    async def test_upsert_replaces_items(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)

        initial = [{"title": "Old", "status": "Done"}]
        await store.save_done_items("PVT_proj1", initial, item_type="task")

        updated = [{"title": "New A", "status": "Done"}, {"title": "New B", "status": "Done"}]
        await store.save_done_items("PVT_proj1", updated, item_type="task")

        loaded = await store.get_done_items("PVT_proj1", item_type="task")
        assert len(loaded) == 2
        assert loaded[0]["title"] == "New A"


class TestClearDoneItems:
    @pytest.mark.asyncio
    async def test_clear_specific_type(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)

        await store.save_done_items("PVT_proj1", [{"t": 1}], item_type="task")
        await store.save_done_items("PVT_proj1", [{"b": 1}], item_type="board")

        await store.clear_done_items("PVT_proj1", item_type="task")

        assert await store.get_done_items("PVT_proj1", item_type="task") is None
        assert await store.get_done_items("PVT_proj1", item_type="board") is not None

    @pytest.mark.asyncio
    async def test_clear_all_types(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)

        await store.save_done_items("PVT_proj1", [{"t": 1}], item_type="task")
        await store.save_done_items("PVT_proj1", [{"b": 1}], item_type="board")

        await store.clear_done_items("PVT_proj1")

        assert await store.get_done_items("PVT_proj1", item_type="task") is None
        assert await store.get_done_items("PVT_proj1", item_type="board") is None

    @pytest.mark.asyncio
    async def test_clear_noop_when_db_not_initialised(self):
        """clear does not raise when DB is not set."""
        await store.clear_done_items("PVT_proj1")


class TestDoneItemsDataHash:
    """save_done_items computes a data hash stored alongside items."""

    @pytest.mark.asyncio
    async def test_hash_is_stored(self, db: aiosqlite.Connection):
        await store.init_done_items_store(db)

        items = [{"status": "Done", "title": "Test"}]
        await store.save_done_items("PVT_proj1", items, item_type="task")

        cursor = await db.execute(
            "SELECT data_hash, item_count FROM done_items_cache WHERE project_id = ?",
            ("PVT_proj1",),
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["data_hash"] is not None
        assert len(row["data_hash"]) == 64  # SHA-256 hex
        assert row["item_count"] == 1
