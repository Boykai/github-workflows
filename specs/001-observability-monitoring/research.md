# Research: Observability & Monitoring

**Feature**: 001-observability-monitoring
**Date**: 2026-03-22
**Status**: Complete — all unknowns resolved

## Decision 1: OpenTelemetry SDK Configuration Strategy

**Context**: The application must support opt-in distributed tracing with zero overhead when disabled (FR-012, FR-017, SC-003). The question is how to gate OTel imports and initialization.

**Decision**: Use conditional imports behind `OTEL_ENABLED=true` with a dedicated `otel_setup.py` module that is only imported and called from `main.py` lifespan when the flag is set.

**Rationale**:
- Python's import system loads modules eagerly — importing `opentelemetry` even to check a flag adds ~15ms startup time and ~5MB memory
- Gating at the import level ensures truly zero overhead for deployments that don't use tracing
- A no-op tracer/meter pattern (returning context managers that do nothing) allows instrumented code to call tracing functions without checking flags at every call site
- The `otel_setup.py` module isolates all OTel provider configuration (TracerProvider, MeterProvider, OTLP exporters, FastAPIInstrumentor, HTTPXClientInstrumentor, aiosqlite instrumentor)

**Alternatives Considered**:
1. **Always import, disable via NoOpTracer**: Simpler code but violates SC-003 (zero overhead) — import alone adds measurable cost
2. **Feature flag in each instrumented function**: Excessive boilerplate and easy to forget in new code
3. **Plugin/entry-point architecture**: Over-engineered for a single opt-in feature

**Implementation Pattern**:
```python
# otel_setup.py — only imported when OTEL_ENABLED=true
def init_otel(service_name: str, endpoint: str) -> tuple[Tracer, Meter]:
    ...

# main.py lifespan
if settings.otel_enabled:
    from src.services.otel_setup import init_otel
    tracer, meter = init_otel(settings.otel_service_name, settings.otel_endpoint)
    app.state.tracer = tracer
    app.state.meter = meter

# Instrumented code uses a helper that returns no-op when tracer not set
def get_tracer() -> Tracer | NoOpTracer:
    return getattr(app.state, "tracer", NoOpTracer())
```

---

## Decision 2: Sentry SDK Coexistence with OpenTelemetry

**Context**: Both Sentry and OpenTelemetry can produce trace data. When both are active, duplicate traces waste resources and confuse operators (FR-020).

**Decision**: Initialize Sentry with `traces_sample_rate=0` to disable Sentry's own tracing while keeping exception capture active.

**Rationale**:
- `sentry-sdk[fastapi]` auto-instruments FastAPI with its own tracing by default
- Setting `traces_sample_rate=0` disables Sentry tracing completely while preserving exception capture, breadcrumbs, and request context enrichment
- OpenTelemetry handles all tracing when both are active
- This is the Sentry-recommended approach for OTel coexistence

**Alternatives Considered**:
1. **Use Sentry's OTel integration (`sentry_sdk.integrations.opentelemetry`)**: Adds complexity and couples the two systems; the spec explicitly says to use `traces_sample_rate=0`
2. **Disable Sentry entirely when OTel is active**: Loses error tracking when tracing is enabled — undesirable

---

## Decision 3: Alert Dispatcher Architecture

**Context**: The alert dispatcher (FR-006–FR-011) must support log-only and webhook delivery with per-type cooldown. The question is state management and extensibility.

**Decision**: Implement as a singleton service class with in-memory cooldown tracking (`dict[str, datetime]`), log-only default, and optional async HTTPX webhook delivery.

**Rationale**:
- In-memory cooldown state is sufficient because alerts are non-critical (missed cooldown on restart is acceptable)
- Singleton pattern aligns with existing service patterns (e.g., `github_projects_service` registered in `main.py` lifespan)
- `httpx.AsyncClient` is already a project dependency — reuse for webhook POST calls
- Log-only default means zero external dependencies in the default deployment

**Alternatives Considered**:
1. **SQLite-backed cooldown state**: Survives restarts but adds unnecessary complexity for a 15-minute cooldown window
2. **Abstract base class with delivery plugins**: Over-engineered for two delivery modes (log + webhook)
3. **Celery/task queue for delivery**: Massive dependency for fire-and-forget webhook calls

**Interface**:
```python
class AlertDispatcher:
    async def dispatch_alert(
        self, alert_type: str, summary: str, details: dict[str, Any]
    ) -> None:
        """Dispatch alert with cooldown enforcement."""
```

---

## Decision 4: Readiness Endpoint Design

**Context**: The readiness endpoint (FR-001–FR-005) must check four subsystems and follow IETF health-check format. The question is response format and check implementation.

**Decision**: Use IETF draft-inadarei-api-health-check format with individual check results. Database write-check uses a dedicated `_readiness_scratch` table with INSERT+DELETE. Polling task check inspects the asyncio.Task state from `state.py`.

**Rationale**:
- IETF health-check format is the industry standard for Kubernetes readiness probes
- The existing `/health` endpoint uses `SELECT 1` for database checking — the readiness endpoint needs a stronger write-check via INSERT+DELETE to catch read-only filesystem or disk-full conditions
- A dedicated scratch table (`_readiness_scratch`) avoids interfering with application data
- The scratch table is auto-created if missing (no migration dependency)
- Checking `_polling_task` from `state.py` is non-intrusive — just inspect `asyncio.Task.done()`

**Alternatives Considered**:
1. **Extend existing `/health` endpoint**: Violates FR-005 (health must remain unchanged); conflates liveness and readiness semantics
2. **Write to an existing table**: Risk of data corruption or unintended side effects
3. **Use filesystem write test instead of DB**: Doesn't validate database layer specifically

**Response Format**:
```json
{
  "status": "pass",
  "checks": {
    "database:writeable": [{"status": "pass", "time": "2026-03-22T14:00:00Z"}],
    "oauth:configured": [{"status": "pass", "time": "2026-03-22T14:00:00Z"}],
    "encryption:enabled": [{"status": "pass", "time": "2026-03-22T14:00:00Z"}],
    "polling:alive": [{"status": "pass", "time": "2026-03-22T14:00:00Z"}]
  }
}
```

---

## Decision 5: Rate-Limit History Storage (Optional, P3)

**Context**: FR-022–FR-024 require optional storage of rate-limit snapshots with 24-hour retention, exposed via API.

**Decision**: Use a dedicated SQLite table `rate_limit_snapshots` with columns `(id, timestamp, remaining, limit, reset_at)`. Sample each polling cycle by reading from `_extract_rate_limit_headers()` in `service.py`. Prune rows older than 24 hours after each insert.

**Rationale**:
- SQLite is already the persistence layer — no new dependencies
- Sampling per polling cycle (~60s default interval) produces ~1,440 rows/day — negligible storage
- Prune-on-insert is simpler than a scheduled cleanup job
- Reusing `_extract_rate_limit_headers()` / `get_last_rate_limit()` from `service.py` avoids duplicate GitHub API calls

**Alternatives Considered**:
1. **In-memory circular buffer**: Lost on restart; 24-hour retention with 60s intervals would consume significant memory
2. **Separate time-series database (InfluxDB, Prometheus)**: Massive dependency for a low-priority feature
3. **File-based CSV logging**: No query capability; cleanup is more complex

---

## Decision 6: Jaeger Service Integration (Optional, P3)

**Context**: FR-025 requires an optional local trace visualization service.

**Decision**: Add `jaeger` service to `docker-compose.yml` under an `observability` Compose profile, using `jaegertracing/jaeger:latest` with OTLP port 4317 and UI port 16686.

**Rationale**:
- Compose profiles are the standard Docker mechanism for optional services
- `docker compose --profile observability up` activates Jaeger only when needed
- Jaeger all-in-one image supports OTLP natively — no collector configuration needed
- Zero impact on default `docker compose up` (no profile = Jaeger not started)

**Alternatives Considered**:
1. **Zipkin**: Less feature-rich; Jaeger is the de-facto standard for OTel visualization
2. **Grafana Tempo**: Requires additional Grafana setup — too complex for local dev
3. **Separate docker-compose.observability.yml file**: Compose profiles are cleaner and more discoverable

---

## Decision 7: Request ID Correlation with OTel Spans

**Context**: FR-016 requires all OTel spans to include the X-Request-ID for log-trace correlation.

**Decision**: Read `request_id_var.get("")` from the existing `contextvars.ContextVar` in `request_id.py` and set it as a span attribute `request.id` on every span. For background tasks (polling, recovery) that run outside request context, generate a synthetic request ID per cycle.

**Rationale**:
- The existing `RequestIDMiddleware` already sets `request_id_var` for every HTTP request
- `ContextVar` is inherently async-safe — reading it in span creation code is zero-cost
- Background tasks don't have HTTP request context, so a synthetic ID (e.g., `poll-{uuid4().hex[:8]}`) provides traceability for polling/recovery spans
- Setting the attribute name as `request.id` follows OTel semantic conventions for custom attributes

**Alternatives Considered**:
1. **Use OTel Baggage propagation**: Adds complexity and is designed for cross-service propagation, not intra-service correlation
2. **Patch logging to include trace_id**: Requires modifying the existing logging infrastructure — higher risk
3. **Only correlate HTTP request spans**: Misses polling and recovery spans which are critical for debugging

---

## Decision 8: Custom Metrics Strategy

**Context**: FR-015 requires three custom metrics: `pipeline.active_count` (gauge), `pipeline.cycle_duration_ms` (histogram), `github.api_remaining` (gauge).

**Decision**: Create metrics via the OTel MeterProvider initialized in `otel_setup.py`. Record values at the natural measurement points: active count from `_pipeline_states` dict length, cycle duration via span timing, API remaining from `get_last_rate_limit()`.

**Rationale**:
- OTel Meter API provides native gauge and histogram instrument types
- Metrics are exported via the same OTLP endpoint as traces — no additional infrastructure
- Recording at natural points avoids additional polling/sampling overhead
- When OTel is disabled, metric recording calls are no-ops (same gating as tracing)

**Alternatives Considered**:
1. **Prometheus client library**: Adds a separate metrics dependency and export endpoint; OTel handles both traces and metrics
2. **StatsD**: Requires a StatsD collector — additional infrastructure
3. **Custom in-memory counters exposed via API**: Limited utility without aggregation/visualization

---

## Decision 9: Encryption Service Instrumentation

**Context**: FR-014 requires OTel spans for encrypt/decrypt operations.

**Decision**: Add conditional span creation in the encryption service's `encrypt()` and `decrypt()` methods using the no-op tracer pattern. Span attributes include operation type and data size (not data content).

**Rationale**:
- Encryption operations are security-sensitive — span attributes must never include plaintext or ciphertext
- Data size is safe to record and useful for performance analysis
- The no-op tracer pattern means zero overhead when tracing is disabled
- Existing `EncryptionService` is a class with well-defined methods — adding spans is non-intrusive

**Alternatives Considered**:
1. **Decorator-based instrumentation**: Less explicit about which attributes to capture; harder to exclude sensitive data
2. **Middleware-level instrumentation**: Encryption doesn't happen at the middleware level

---

## Technology Best Practices

### OpenTelemetry Python Best Practices
- Use `BatchSpanProcessor` (not `SimpleSpanProcessor`) for production — batches exports to reduce overhead
- Set `OTEL_EXPORTER_OTLP_ENDPOINT` to configure the collector endpoint externally
- Use `Resource` with `service.name` attribute for service identification
- Prefer `tracer.start_as_current_span()` context manager for automatic span lifecycle management
- Set span status to `ERROR` with exception recording on failures

### Sentry FastAPI Best Practices
- Initialize once in lifespan startup, not at module import time
- Use `sentry_sdk.init(traces_sample_rate=0)` when OTel handles tracing
- Use `sentry_sdk.capture_exception()` in exception handlers for explicit capture
- Use `sentry_sdk.set_context()` and `sentry_sdk.set_tag()` for enrichment
- The FastAPI integration auto-captures request context when initialized with `FastApiIntegration`

### Alert Webhook Best Practices
- Use fire-and-forget with timeout (5s) to avoid blocking critical operations
- Log delivery failures as warnings — alert is still recorded locally
- Include `alert_type`, `summary`, `details`, and `fired_at` in webhook payload
- Use `Content-Type: application/json` for webhook delivery
