# Quickstart: Observability & Monitoring

**Feature**: 001-observability-monitoring
**Date**: 2026-03-22

## Prerequisites

- Python 3.12+ (3.13 recommended)
- Docker & Docker Compose (for Jaeger visualization)
- Access to the Solune backend source (`solune/backend/`)

## 1. Install New Dependencies

```bash
cd solune/backend
pip install -e ".[dev]"
```

The following packages are added to `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| `opentelemetry-api` | OTel tracing/metrics API |
| `opentelemetry-sdk` | OTel SDK implementation |
| `opentelemetry-instrumentation-fastapi` | Auto-instrument FastAPI |
| `opentelemetry-instrumentation-httpx` | Auto-instrument HTTPX |
| `opentelemetry-instrumentation-aiosqlite` | Auto-instrument aiosqlite |
| `opentelemetry-exporter-otlp` | OTLP span/metric exporter |
| `sentry-sdk[fastapi]` | Sentry error tracking |

## 2. Readiness Endpoint (P1, Zero Config)

The readiness endpoint works out of the box with no additional configuration:

```bash
# Start the backend
cd solune/backend && python -m src.main

# Check readiness
curl -s http://localhost:8000/api/v1/ready | python -m json.tool
```

**Expected output** (all systems healthy):
```json
{
  "status": "pass",
  "checks": {
    "database:writeable": [{"status": "pass", ...}],
    "oauth:configured": [{"status": "pass", ...}],
    "encryption:enabled": [{"status": "pass", ...}],
    "polling:alive": [{"status": "pass", ...}]
  }
}
```

**Verify degraded state** (remove OAuth credentials):
```bash
GITHUB_CLIENT_ID="" GITHUB_CLIENT_SECRET="" python -m src.main &
curl -s http://localhost:8000/api/v1/ready
# Returns HTTP 503 with oauth:configured → fail
```

The existing liveness probe is unchanged:
```bash
curl -s http://localhost:8000/api/v1/health
# Same response as before — no changes
```

## 3. SLA Alerting (P1, Zero Config for Log-Only)

Alerting works in log-only mode by default. No external dependencies required.

### Test Pipeline Stall Alerts

```bash
# Set a low threshold for testing (1 minute instead of 30)
export PIPELINE_STALL_ALERT_MINUTES=1

# Start the backend and create a stalled pipeline
# Watch logs for: "Alert dispatched: pipeline_stall"
```

### Test Rate-Limit Alerts

```bash
# Set a high threshold for testing
export RATE_LIMIT_CRITICAL_THRESHOLD=5000

# Start the backend with polling — any rate limit will trigger
# Watch logs for: "Alert dispatched: rate_limit_critical"
```

### Enable Webhook Delivery (Optional)

```bash
# Point to your webhook receiver (e.g., Slack incoming webhook)
export ALERT_WEBHOOK_URL="https://hooks.example.com/alerts"

# Alerts will be POSTed as JSON to this URL
```

## 4. OpenTelemetry Tracing (P2, Opt-in)

### Quick Start with Jaeger

```bash
# Start Jaeger for trace visualization
docker compose --profile observability up -d

# Enable tracing
export OTEL_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=solune-backend

# Start the backend
cd solune/backend && python -m src.main
```

### View Traces

1. Open Jaeger UI: http://localhost:16686
2. Select service: `solune-backend`
3. Click "Find Traces"
4. Perform operations (API requests, wait for polling cycles)
5. Refresh Jaeger to see traces with span hierarchies

### Verify Zero Overhead When Disabled

```bash
# Default: OTEL_ENABLED is not set (false)
# No OTel libraries are imported, no spans created, no network calls
python -c "import importlib; importlib.import_module('src.main')"
# Should NOT import any opentelemetry modules
```

## 5. Sentry Error Tracking (P2, Opt-in)

```bash
# Enable Sentry
export SENTRY_DSN="https://examplePublicKey@o0.ingest.sentry.io/0"

# Start the backend
cd solune/backend && python -m src.main

# Trigger a test exception
curl -X POST http://localhost:8000/api/v1/nonexistent-endpoint

# Check your Sentry dashboard for the captured exception
# It should include: request_id, request path, method
```

### With OTel Active (No Double Tracing)

```bash
export OTEL_ENABLED=true
export SENTRY_DSN="https://..."

# Sentry captures exceptions but does NOT create traces
# (traces_sample_rate=0 is set automatically)
```

## 6. Rate-Limit History (P3, Optional)

```bash
# Start the backend with polling enabled
# Wait for a few polling cycles

# Query history
curl -s "http://localhost:8000/api/v1/rate-limit/history?hours=24" | python -m json.tool
```

**Expected output**:
```json
{
  "snapshots": [
    {"timestamp": "2026-03-22T13:00:00Z", "remaining": 4850, "limit": 5000, "reset_at": 1742655600},
    {"timestamp": "2026-03-22T13:01:00Z", "remaining": 4847, "limit": 5000, "reset_at": 1742655600}
  ],
  "hours": 24,
  "count": 2
}
```

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_ENABLED` | `false` | Enable OpenTelemetry tracing/metrics |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | OTLP collector endpoint |
| `OTEL_SERVICE_NAME` | `solune-backend` | Service name in traces |
| `SENTRY_DSN` | _(empty)_ | Sentry DSN (empty = disabled) |
| `PIPELINE_STALL_ALERT_MINUTES` | `30` | Pipeline stall alert threshold |
| `AGENT_TIMEOUT_ALERT_MINUTES` | `15` | Agent timeout alert threshold |
| `RATE_LIMIT_CRITICAL_THRESHOLD` | `20` | Rate-limit critical alert threshold |
| `ALERT_WEBHOOK_URL` | _(empty)_ | Webhook URL (empty = log-only) |
| `ALERT_COOLDOWN_MINUTES` | `15` | Cooldown between same-type alerts |

## Verification Checklist

- [ ] `GET /api/v1/ready` returns 200 when all systems healthy
- [ ] `GET /api/v1/ready` returns 503 when any system degraded
- [ ] `GET /api/v1/health` remains unchanged
- [ ] Pipeline stall alert appears in logs when threshold exceeded
- [ ] Rate-limit alert appears in logs when threshold breached
- [ ] No duplicate alerts within 15-minute cooldown window
- [ ] Traces visible in Jaeger when `OTEL_ENABLED=true`
- [ ] Exceptions appear in Sentry when `SENTRY_DSN` configured
- [ ] Zero overhead confirmed when all observability features disabled
