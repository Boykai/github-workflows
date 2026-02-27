-- Migration 005: Enforce UNIQUE on signal_phone_hash
-- Prevents race conditions in phone conflict detection (FR-015).
-- Partial index excludes empty hashes left by disconnected rows.

DROP INDEX IF EXISTS idx_signal_conn_phone_hash;
CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_conn_phone_hash
    ON signal_connections(signal_phone_hash)
    WHERE signal_phone_hash != '';
