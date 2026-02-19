# Research: SQLite-Backed Settings Storage

**Feature**: 006-sqlite-settings-storage
**Date**: 2026-02-19
**Status**: Complete — all NEEDS CLARIFICATION resolved

## 1. aiosqlite Connection Management in FastAPI

**Decision**: Use a single persistent connection opened in the FastAPI `lifespan` context manager, stored on `app.state` or a module-level variable. Pass to handlers via dependency injection.

**Rationale**: aiosqlite wraps each connection in a single dedicated background thread with a serialized request queue — one connection already handles concurrency correctly. SQLite enforces single-writer semantics; multiple connections would only contend on the write lock. A single persistent connection avoids repeated connect/close overhead (file open, WAL recovery, pragma setup). FastAPI's `lifespan` async context manager is the canonical place to open before `yield` and close after.

**Alternatives Considered**:
- Connection-per-request: High overhead for SQLite, no pooling benefit. Rejected.
- Connection pool (e.g., via `databases` library): Anti-pattern for SQLite embedded databases. Pool contention adds complexity with no throughput gain. Rejected.
- SQLAlchemy async engine: Heavy dependency layer for simple SQLite. Still uses aiosqlite underneath. Rejected.

## 2. Pydantic Model ↔ SQLite Row Conversion

**Decision**: Use `model_dump()` for INSERT (Pydantic → dict → named SQL parameters) and `model_validate()` for SELECT (sqlite3.Row → dict → Pydantic model). Set `db.row_factory = aiosqlite.Row`.

**Rationale**: `aiosqlite.Row` supports key-based access; `dict(row)` converts directly to a dict for `model_validate()`. SQL parameters passed directly from `model_dump()`: `await db.execute("INSERT INTO t (a, b) VALUES (:a, :b)", model.model_dump())`. Pydantic v2 handles type coercion (e.g., SQLite 0/1 → bool). For JSON-serialized columns (notification preferences), use `json.dumps()` on write and `json.loads()` on read.

**Alternatives Considered**:
- Manual dict construction: Error-prone, misses Pydantic validation. Rejected.
- SQLModel: Merges Pydantic + SQLAlchemy but requires SQLAlchemy, overkill for raw SQL. Rejected.

## 3. Schema Migration with Embedded Version Table

**Decision**: `schema_version` table with single row tracking current version integer. Discovery of `.sql` files from `migrations/` directory sorted by numeric prefix. At startup, compare DB version to highest migration number and apply missing migrations sequentially within a transaction.

**Rationale**: Spec requires this pattern (FR-004). Self-contained — no external tools or dependencies. Migration runner is ~40 lines of Python. Each migration runs in a transaction; on success update version, on failure rollback and abort startup. Forward-only: if DB version exceeds app version, refuse to start (per spec clarification). The `schema_version` table itself is created with `CREATE TABLE IF NOT EXISTS` before migration check.

**Alternatives Considered**:
- Alembic: Industry standard but overkill for single-file SQLite with < 10 tables. Adds SQLAlchemy dependency. Rejected.
- Auto-detect schema changes: Fragile, can't handle renames or data transforms. Rejected.
- Migrations as Python functions: Workable, but `.sql` files are more transparent and reviewable. Rejected.

## 4. Background Task for Periodic Session Cleanup

**Decision**: Use `asyncio.create_task()` in the `lifespan` startup to spawn a long-lived coroutine with `while True` / `await asyncio.sleep(interval)`. Cancel on shutdown.

**Rationale**: FastAPI runs on a single asyncio event loop. `create_task()` is zero-dependency. Pattern already used in this codebase. Store task reference for clean shutdown cancellation.

**Alternatives Considered**:
- FastAPI `BackgroundTasks`: Per-request, not periodic. Wrong tool. Rejected.
- APScheduler: Full scheduler library for a single periodic task. Overkill. Rejected.
- Celery/ARQ: External task queues requiring Redis. Massively over-engineered. Rejected.

## 5. SQLite WAL Mode

**Decision**: Enable WAL mode. Execute `PRAGMA journal_mode=WAL;` after opening connection at startup. Also set `PRAGMA busy_timeout=5000;` and `PRAGMA foreign_keys=ON;`.

**Rationale**: Concurrent reads don't block writes and vice versa — essential for a web application with concurrent requests. WAL is persistent once set. Standard practice for any concurrent SQLite usage. Additional pragmas: busy_timeout prevents immediate lock failures; foreign_keys enforces referential integrity.

**Tradeoffs**: Creates two extra files (`-wal`, `-shm`) alongside database — fine for Docker volumes. Slightly slower for read-only workloads but irrelevant for mixed read/write.

**Alternatives Considered**:
- Default journal mode (DELETE): Readers block writers. Unacceptable for concurrent web app. Rejected.

## 6. aiosqlite vs ORM Libraries

**Decision**: Use raw aiosqlite. No ORM, no abstraction layer.

**Rationale**: 4-5 tables with simple CRUD, no complex joins. Pydantic handles validation/serialization. aiosqlite is a thin wrapper mirroring stdlib sqlite3 — zero learning curve. Minimal dependency surface (zero transitive deps). Raw SQL is transparent and debuggable.

**Alternatives Considered**:
- SQLModel: Elegant Pydantic-SQLAlchemy integration but adds SQLAlchemy transitive dependency, async requires additional adapter anyway. Overkill for 4-5 tables. Rejected.
- `databases` library (encode): Async abstraction over SQLAlchemy Core. Maintenance appears slow (last release Mar 2024). Connection pooling counter-productive for SQLite. Rejected.
- Tortoise ORM: Full-featured async ORM. Heavy dependency, wrong philosophy for "keep it simple." Rejected.
- SQLAlchemy Core (async): Query builder. Adds ~15MB dependency for parameterized string formatting on 4-5 tables. Rejected.

## Summary of Technology Decisions

| Aspect | Decision | Key Reason |
|--------|----------|------------|
| Database library | aiosqlite (raw) | Simplest for 4-5 tables; no ORM needed |
| Connection pattern | Single persistent connection in lifespan | SQLite single-writer; avoids connect/close overhead |
| Model mapping | `model_dump()` / `model_validate()` | Pydantic handles all serialization/validation |
| Schema migrations | Embedded version table + .sql files | Self-contained; no external deps; spec-required |
| Periodic cleanup | `asyncio.create_task()` in lifespan | Zero-dependency; existing codebase pattern |
| Journal mode | WAL | Concurrent read/write without blocking |
| Additional pragmas | `busy_timeout=5000`, `foreign_keys=ON` | Lock resilience + referential integrity |
