# ADR-002: SQLite with WAL mode and numbered auto-migrations

**Status**: Accepted
**Date**: 2025-Q1

## Context

The backend needs a persistence layer for sessions, user settings, agent configurations, Signal connections, and audit logs. The deployment target is a single-server Docker Compose stack without an external database.

Options evaluated:

- **PostgreSQL** — Full ACID, horizontal scale, but requires a separate container and connection pool management.
- **Redis** — Fast key-value, but session data needs TTL semantics and the relational model is awkward.
- **SQLite (synchronous)** — Simple but blocks the async event loop under concurrent writes.
- **SQLite with aiosqlite + WAL mode** — Non-blocking async interface, WAL mode allows one writer + multiple concurrent readers, zero operational overhead.

## Decision

Use SQLite via `aiosqlite` in WAL (Write-Ahead Logging) mode at `DATABASE_PATH` (default `/app/data/settings.db`).

Schema is managed by numbered SQL files in `backend/src/migrations/` (currently `001` through `012`). A `schema_version` table tracks applied migrations; the database layer runs pending migrations at startup in order.

## Consequences

- **+** Zero operational overhead — no extra container, no connection string management.
- **+** WAL mode gives read concurrency without blocking; acceptable for single-server load.
- **+** Numbered migrations are explicit, reversible (by backup + rollback), and Git-traceable.
- **−** Not suitable for multi-replica deployments — SQLite is single-writer.
- **−** No schema rollback support; forward-only migrations mean mistakes require a new migration file.
- **Note**: The `solune-data` Docker volume must be mounted to persist the database across container restarts.
