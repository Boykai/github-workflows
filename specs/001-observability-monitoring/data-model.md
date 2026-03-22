# Data Model: Observability & Monitoring

**Feature**: 001-observability-monitoring
**Date**: 2026-03-22
**Source**: [spec.md](./spec.md), [research.md](./research.md)

## Entities

### 1. Readiness Check Result

**Purpose**: Represents the outcome of a single subsystem health check in the readiness endpoint response.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `component_id` | `str` | Yes | Unique check identifier (e.g., `database:writeable`, `oauth:configured`) |
| `component_type` | `str` | Yes | Always `"component"` per IETF health-check format |
| `status` | `str` | Yes | `"pass"` or `"fail"` |
| `time` | `str` (ISO-8601) | Yes | Timestamp when the check was performed |
| `output` | `str` | No | Human-readable failure description (only present on failure) |

**Validation Rules**:
- `status` must be exactly `"pass"` or `"fail"` — no `"warn"` for readiness checks
- `time` must be valid ISO-8601 with timezone

**Relationships**: Aggregated into the `ReadinessResponse` envelope.

---

### 2. Readiness Response

**Purpose**: Top-level response body for `GET /api/v1/ready`, following IETF draft-inadarei-api-health-check format.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `str` | Yes | `"pass"` if all checks pass, `"fail"` if any check fails |
| `checks` | `dict[str, list[ReadinessCheckResult]]` | Yes | Map of check name to list of check results |

**Validation Rules**:
- `status` is `"pass"` only when ALL four checks have `status: "pass"`
- `status` is `"fail"` if ANY check has `status: "fail"`
- All four checks must always be present: `database:writeable`, `oauth:configured`, `encryption:enabled`, `polling:alive`

**State Transitions**: N/A — stateless per-request computation.

---

### 3. Alert Event

**Purpose**: Represents a dispatched alert from the alert dispatcher. Not persisted to database — exists as a runtime event logged and optionally delivered via webhook.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alert_type` | `str` | Yes | Alert category: `"pipeline_stall"` or `"rate_limit_critical"` |
| `summary` | `str` | Yes | Human-readable one-line summary |
| `details` | `dict[str, Any]` | Yes | Structured detail payload (varies by alert type) |
| `fired_at` | `str` (ISO-8601) | Yes | Timestamp when the alert was dispatched |
| `delivery` | `str` | Yes | Delivery outcome: `"logged"`, `"webhook_sent"`, `"webhook_failed"` |

**Validation Rules**:
- `alert_type` must be a recognized type string
- `summary` must be non-empty
- `fired_at` must be valid ISO-8601

**Relationships**: Subject to cooldown enforcement via `AlertCooldownRecord`.

---

### 4. Alert Cooldown Record

**Purpose**: Tracks the last dispatch time for each alert type to enforce the 15-minute cooldown window. In-memory only — not persisted.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alert_type` | `str` | Yes | The alert type being tracked |
| `last_fired_at` | `datetime` | Yes | UTC timestamp of last successful dispatch |

**Validation Rules**:
- Cooldown window is 15 minutes (configurable via `alert_cooldown_minutes`)
- An alert is suppressed if `utcnow() - last_fired_at < cooldown_minutes`
- Boundary is inclusive: alert fires at exactly 15 minutes

**State Transitions**:
- `None → last_fired_at`: First alert of this type dispatched
- `last_fired_at → updated`: Alert dispatched after cooldown expired

**Storage**: `dict[str, datetime]` in `AlertDispatcher` instance (in-memory).

---

### 5. Rate-Limit Snapshot (Optional)

**Purpose**: Point-in-time capture of GitHub API rate-limit state, stored for historical trend analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `int` | Yes | Auto-increment primary key |
| `timestamp` | `str` (ISO-8601) | Yes | When the snapshot was captured |
| `remaining` | `int` | Yes | GitHub API calls remaining |
| `limit` | `int` | Yes | GitHub API total call limit |
| `reset_at` | `int` | Yes | Unix timestamp when the rate limit resets |

**Validation Rules**:
- `remaining` must be >= 0
- `limit` must be > 0
- `reset_at` must be a valid Unix timestamp
- Rows older than 24 hours are automatically pruned

**Storage**: SQLite table `rate_limit_snapshots`.

**SQL Schema**:
```sql
CREATE TABLE IF NOT EXISTS rate_limit_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    remaining INTEGER NOT NULL,
    "limit" INTEGER NOT NULL,
    reset_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_snapshots_timestamp 
    ON rate_limit_snapshots(timestamp);
```

---

### 6. Readiness Scratch Table

**Purpose**: Minimal table used by the readiness endpoint to verify database write capability. Contains no persistent data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `int` | Yes | Primary key (always value `1`) |

**Validation Rules**:
- Table is auto-created if missing
- Each readiness check inserts a row with `id=1` and immediately deletes it
- No data persists between checks

**SQL Schema**:
```sql
CREATE TABLE IF NOT EXISTS _readiness_scratch (
    id INTEGER PRIMARY KEY
);
```

---

## Entity Relationship Diagram

```text
┌─────────────────────┐
│  ReadinessResponse   │
│  - status            │
│  - checks            │──────────────┐
└─────────────────────┘              │ contains 4
                                      ▼
                          ┌──────────────────────┐
                          │ ReadinessCheckResult  │
                          │ - component_id        │
                          │ - status              │
                          │ - time                │
                          │ - output (optional)   │
                          └──────────────────────┘

┌─────────────────────┐       enforces        ┌─────────────────────┐
│    AlertEvent        │◄─────────────────────│ AlertCooldownRecord  │
│  - alert_type        │                       │ - alert_type         │
│  - summary           │                       │ - last_fired_at      │
│  - details           │                       └─────────────────────┘
│  - fired_at          │                       (in-memory dict)
│  - delivery          │
└─────────────────────┘
  (runtime event)

┌─────────────────────┐
│ RateLimitSnapshot    │  (optional, P3)
│  - id                │
│  - timestamp         │
│  - remaining         │
│  - limit             │
│  - reset_at          │
└─────────────────────┘
  (SQLite table)
```

## Configuration Fields (config.py additions)

| Field | Type | Default | Environment Variable | Description |
|-------|------|---------|---------------------|-------------|
| `otel_enabled` | `bool` | `False` | `OTEL_ENABLED` | Enable OpenTelemetry tracing and metrics |
| `otel_endpoint` | `str` | `"http://localhost:4317"` | `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint |
| `otel_service_name` | `str` | `"solune-backend"` | `OTEL_SERVICE_NAME` | Service name for traces |
| `sentry_dsn` | `str` | `""` | `SENTRY_DSN` | Sentry DSN (empty = disabled) |
| `pipeline_stall_alert_minutes` | `int` | `30` | `PIPELINE_STALL_ALERT_MINUTES` | Minutes before stall triggers alert |
| `agent_timeout_alert_minutes` | `int` | `15` | `AGENT_TIMEOUT_ALERT_MINUTES` | Minutes before agent timeout triggers alert |
| `rate_limit_critical_threshold` | `int` | `20` | `RATE_LIMIT_CRITICAL_THRESHOLD` | API remaining count below which critical alert fires |
| `alert_webhook_url` | `str` | `""` | `ALERT_WEBHOOK_URL` | Webhook URL for alert delivery (empty = log-only) |
| `alert_cooldown_minutes` | `int` | `15` | `ALERT_COOLDOWN_MINUTES` | Minutes between duplicate alerts of same type |
