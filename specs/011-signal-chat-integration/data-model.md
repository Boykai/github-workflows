# Data Model: Signal Messaging Integration

**Feature**: `011-signal-chat-integration`  
**Date**: 2026-02-27  
**Source**: [spec.md](spec.md), [research.md](research.md)

## Entities

### SignalConnection

Represents the link between an app user and the app's Signal number. One per user.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique connection identifier |
| `github_user_id` | TEXT | UNIQUE, NOT NULL, FK → user_sessions | App user who owns this connection |
| `signal_phone_encrypted` | TEXT | NOT NULL | User's Signal phone number, Fernet-encrypted at rest |
| `signal_phone_hash` | TEXT | NOT NULL, INDEX | SHA-256 hash of phone number for lookup without decryption |
| `status` | TEXT | NOT NULL, DEFAULT 'pending' | Connection status: `pending`, `connected`, `error`, `disconnected` |
| `notification_mode` | TEXT | NOT NULL, DEFAULT 'all' | Notification preference: `all`, `actions_only`, `confirmations_only`, `none` |
| `last_active_project_id` | TEXT | NULL | Most recently active project for inbound message routing (FR-006) |
| `linked_at` | TEXT (ISO 8601) | NULL | Timestamp when QR code link was completed |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Row creation timestamp |
| `updated_at` | TEXT (ISO 8601) | NOT NULL | Last modification timestamp |

**Lifecycle**: Created when user initiates linking → status `pending` → `connected` on successful QR scan → `disconnected` on user disconnect (row then deleted per FR-014, PII removed). Status `error` set on delivery failures / stale link detection.

**Unique phone constraint**: `signal_phone_hash` is indexed. On new connection, if the hash already exists for another user, the old connection is set to `disconnected` and deleted (FR-015 — banner notification queued for the displaced user).

---

### SignalMessage

Audit log of Signal messages sent and received. Used for delivery tracking and retry state.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique message record identifier |
| `connection_id` | TEXT (UUID) | NOT NULL, FK → signal_connections | Parent connection |
| `direction` | TEXT | NOT NULL | `inbound` or `outbound` |
| `chat_message_id` | TEXT (UUID) | NULL | Associated app ChatMessage ID (null for auto-replies) |
| `content_preview` | TEXT | NULL | First 200 chars of message (not PII — truncated content for debugging) |
| `delivery_status` | TEXT | NOT NULL, DEFAULT 'pending' | `pending`, `delivered`, `failed`, `retrying` |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | Number of retry attempts (max 3) |
| `next_retry_at` | TEXT (ISO 8601) | NULL | Scheduled time for next retry attempt |
| `error_detail` | TEXT | NULL | Last error message (for failed deliveries) |
| `created_at` | TEXT (ISO 8601) | NOT NULL | Record creation timestamp |
| `delivered_at` | TEXT (ISO 8601) | NULL | Actual delivery timestamp |

**Retention**: SignalMessage rows are retained for observability (FR-011) but contain no PII. The `connection_id` FK may reference a deleted connection after disconnect; this is acceptable since the rows are for audit only.

---

### SignalConflictBanner

Tracks dismissible in-app banners for users whose Signal link was displaced by another user (FR-015).

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | TEXT (UUID) | PK | Unique banner identifier |
| `github_user_id` | TEXT | NOT NULL, INDEX | User who should see the banner |
| `message` | TEXT | NOT NULL | Banner text to display |
| `dismissed` | INTEGER | NOT NULL, DEFAULT 0 | 0 = active, 1 = dismissed |
| `created_at` | TEXT (ISO 8601) | NOT NULL | When the banner was created |

**Lifecycle**: Created when a phone conflict displaces a user → shown on next chat/settings load → deleted after dismissal.

---

## Relationships

```text
user_sessions (existing)
  └── 1:0..1 ──→ signal_connections (one optional connection per user)
                    └── 1:N ──→ signal_messages (audit log of all Signal traffic)

user_sessions (existing)
  └── 1:N ──→ signal_conflict_banners (active banners for displaced users)
```

## State Transitions

### SignalConnection.status

```text
                    ┌──────────┐
        User opens  │ (no row) │  No connection exists
        Settings    └────┬─────┘
                         │ Initiate linking
                         ▼
                    ┌──────────┐
                    │ pending  │  QR code generated, waiting for scan
                    └────┬─────┘
                    ╱         ╲
           Scan success    Scan fail/timeout
                  ╱             ╲
           ┌───────────┐   ┌─────────┐
           │ connected  │   │  error  │──→ User retries → pending
           └─────┬──────┘   └─────────┘
                 │
          User disconnects
          OR phone conflict
                 │
           ┌──────────────┐
           │ disconnected │──→ Row deleted (PII purged per FR-014)
           └──────────────┘
```

### SignalMessage.delivery_status (outbound)

```text
  ┌─────────┐      success     ┌───────────┐
  │ pending │ ────────────────→ │ delivered │
  └────┬────┘                   └───────────┘
       │ failure
       ▼
  ┌──────────┐    retry < 3    ┌──────────┐
  │ retrying │ ←──────────────→ │ retrying │  (30s → 2min → 8min backoff)
  └────┬─────┘                  └──────────┘
       │ retry >= 3
       ▼
  ┌────────┐
  │ failed │  (logged, message dropped)
  └────────┘
```

## Validation Rules

- **signal_phone_encrypted**: Must be a valid Fernet-encrypted string. Decrypted value must match E.164 phone number format (`+` followed by 1-15 digits).
- **signal_phone_hash**: SHA-256 hex digest, 64 characters.
- **notification_mode**: Must be one of `all`, `actions_only`, `confirmations_only`, `none`.
- **status**: Must be one of `pending`, `connected`, `error`, `disconnected`.
- **direction**: Must be `inbound` or `outbound`.
- **delivery_status**: Must be one of `pending`, `delivered`, `failed`, `retrying`.
- **retry_count**: 0-3 inclusive.
- **content_preview**: Max 200 characters, no PII (phone numbers redacted before storage).

## Migration SQL

File: `backend/src/migrations/004_add_signal_tables.sql`

```sql
-- Migration 004: Signal messaging integration tables

CREATE TABLE IF NOT EXISTS signal_connections (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL UNIQUE,
    signal_phone_encrypted TEXT NOT NULL,
    signal_phone_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    notification_mode TEXT NOT NULL DEFAULT 'all',
    last_active_project_id TEXT,
    linked_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signal_conn_user ON signal_connections(github_user_id);
CREATE INDEX IF NOT EXISTS idx_signal_conn_phone_hash ON signal_connections(signal_phone_hash);
CREATE INDEX IF NOT EXISTS idx_signal_conn_status ON signal_connections(status);

CREATE TABLE IF NOT EXISTS signal_messages (
    id TEXT PRIMARY KEY,
    connection_id TEXT NOT NULL,
    direction TEXT NOT NULL,
    chat_message_id TEXT,
    content_preview TEXT,
    delivery_status TEXT NOT NULL DEFAULT 'pending',
    retry_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at TEXT,
    error_detail TEXT,
    created_at TEXT NOT NULL,
    delivered_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_signal_msg_conn ON signal_messages(connection_id);
CREATE INDEX IF NOT EXISTS idx_signal_msg_status ON signal_messages(delivery_status);
CREATE INDEX IF NOT EXISTS idx_signal_msg_retry ON signal_messages(next_retry_at)
    WHERE delivery_status = 'retrying';

CREATE TABLE IF NOT EXISTS signal_conflict_banners (
    id TEXT PRIMARY KEY,
    github_user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    dismissed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signal_banner_user ON signal_conflict_banners(github_user_id)
    WHERE dismissed = 0;
```
