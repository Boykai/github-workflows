# Tasks: Observability & Monitoring — OpenTelemetry Tracing, Sentry Error Tracking, SLA Alerting & Readiness Endpoint

**Input**: Design documents from `/specs/001-observability-monitoring/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are omitted per constitution principle IV (Test Optionality).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/` (backend), `solune/frontend/src/` (frontend — no changes this phase)
- **Tests**: `solune/backend/tests/`
- **Config**: `solune/backend/pyproject.toml`, `docker-compose.yml` (repo root)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new dependencies and create project scaffolding for observability features.

- [x] T001 Add OpenTelemetry dependencies to `solune/backend/pyproject.toml`: opentelemetry-api, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-httpx, opentelemetry-instrumentation-aiosqlite, opentelemetry-exporter-otlp
- [x] T002 Add Sentry dependency to `solune/backend/pyproject.toml`: sentry-sdk[fastapi]
- [x] T003 Add observability configuration fields to `solune/backend/src/config.py`: otel_enabled (bool, default False, env OTEL_ENABLED), otel_endpoint (str, default "http://localhost:4317", env OTEL_EXPORTER_OTLP_ENDPOINT), otel_service_name (str, default "solune-backend", env OTEL_SERVICE_NAME), sentry_dsn (str, default "", env SENTRY_DSN)
- [x] T004 Add alerting configuration fields to `solune/backend/src/config.py`: pipeline_stall_alert_minutes (int, default 30), agent_timeout_alert_minutes (int, default 15), rate_limit_critical_threshold (int, default 20), alert_webhook_url (str, default ""), alert_cooldown_minutes (int, default 15)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure modules that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create the alert dispatcher service in `solune/backend/src/services/alert_dispatcher.py` — implement AlertDispatcher class with `__init__(self, webhook_url: str = "", cooldown_minutes: int = 15)`, in-memory cooldown dict (`dict[str, datetime]`), and core `async def dispatch_alert(self, alert_type: str, summary: str, details: dict[str, Any]) -> None` method with cooldown enforcement (suppress if same alert_type fired within cooldown_minutes), structured WARNING log on dispatch, DEBUG log on suppression, and optional async HTTPX webhook POST (5s timeout, fire-and-forget, log warning on failure) per contract in `specs/001-observability-monitoring/contracts/alert-dispatcher.md`
- [x] T006 [P] Create the OTel setup module in `solune/backend/src/services/otel_setup.py` — implement `init_otel(service_name: str, endpoint: str) -> tuple[Tracer, Meter]` that configures TracerProvider with BatchSpanProcessor + OTLPSpanExporter, MeterProvider with OTLPMetricExporter, Resource with service.name attribute, FastAPIInstrumentor, HTTPXClientInstrumentor, and aiosqlite instrumentor; also implement a `get_tracer()` and `get_meter()` helper that returns the active tracer/meter or a no-op when OTel is not initialized (per research.md Decision 1)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Readiness Endpoint for Deployment Confidence (Priority: P1) 🎯 MVP

**Goal**: Expose `GET /api/v1/ready` that validates four critical subsystems (database writability, OAuth credentials, encryption service, polling task) and returns HTTP 200 / 503 with IETF health-check-format body.

**Independent Test**: Start the application with valid configuration → `curl GET /api/v1/ready` → HTTP 200 with all checks "pass". Intentionally degrade each subsystem → re-test → HTTP 503 with specific failure identified. Verify `GET /health` remains unchanged.

### Implementation for User Story 1

- [x] T007 [US1] Implement the readiness endpoint in `solune/backend/src/api/health.py` — add `GET /api/v1/ready` route that performs four checks in sequence: (1) database writeable via INSERT+DELETE on `_readiness_scratch` table (auto-CREATE TABLE IF NOT EXISTS), (2) OAuth configured via non-empty `settings.github_client_id` and `settings.github_client_secret`, (3) encryption enabled via `EncryptionService.enabled`, (4) polling alive via inspecting the asyncio.Task from `state.py` (pass if running or intentionally disabled). Return HTTP 200 with IETF health-check body when all pass, HTTP 503 when any fail, per contract in `specs/001-observability-monitoring/contracts/readiness.md`
- [x] T008 [US1] Define Pydantic response models for the readiness endpoint in `solune/backend/src/api/health.py` (or co-located): ReadinessCheckResult (component_id, component_type, status, time, optional output) and ReadinessResponse (status, checks dict) per data-model.md entities 1 and 2
- [x] T009 [US1] Wire the readiness endpoint into the FastAPI router — ensure it is registered under the existing health router or a new router included in `solune/backend/src/main.py`, verify `GET /health` remains completely unchanged (FR-005)

**Checkpoint**: At this point, User Story 1 should be fully functional — `GET /api/v1/ready` returns 200/503, `GET /health` unchanged.

---

## Phase 4: User Story 2 — SLA-Breach Alerting for Incident Response (Priority: P1)

**Goal**: Wire the alert dispatcher into recovery.py and polling_loop.py to automatically dispatch `pipeline_stall` and `rate_limit_critical` alerts with configurable thresholds and cooldown enforcement.

**Independent Test**: Set `PIPELINE_STALL_ALERT_MINUTES=1`, artificially stall a pipeline, observe "Alert dispatched: pipeline_stall" in logs. Set `RATE_LIMIT_CRITICAL_THRESHOLD=5000`, observe rate-limit alert in logs. Verify no duplicate alerts within 15 minutes.

### Implementation for User Story 2

- [x] T010 [US2] Instantiate AlertDispatcher in the application lifespan in `solune/backend/src/main.py` — create the dispatcher with `webhook_url=settings.alert_webhook_url` and `cooldown_minutes=settings.alert_cooldown_minutes`, store on `app.state.alert_dispatcher`
- [x] T011 [US2] Wire pipeline stall alerting into `solune/backend/src/services/copilot_polling/recovery.py` — after detecting a stall exceeding `settings.pipeline_stall_alert_minutes`, call `await alert_dispatcher.dispatch_alert("pipeline_stall", summary, details)` with issue_number, stall_duration_minutes, threshold_minutes, and pipeline_state per the integration example in `specs/001-observability-monitoring/contracts/alert-dispatcher.md`
- [x] T012 [US2] Wire rate-limit critical alerting into `solune/backend/src/services/copilot_polling/polling_loop.py` — after rate-limit check, if `remaining < settings.rate_limit_critical_threshold`, call `await alert_dispatcher.dispatch_alert("rate_limit_critical", summary, details)` with remaining, limit, threshold, and reset_at per the integration example in `specs/001-observability-monitoring/contracts/alert-dispatcher.md`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently — readiness probe functional, alerts dispatching on threshold breaches with cooldown.

---

## Phase 5: User Story 3 — Distributed Tracing for Incident Diagnosis (Priority: P2)

**Goal**: Instrument the FastAPI backend with opt-in OpenTelemetry tracing and metrics, add manual spans for critical operations, emit custom metrics, and correlate all spans with the existing X-Request-ID.

**Independent Test**: Enable `OTEL_ENABLED=true`, start Jaeger via `docker compose --profile observability up`, perform API requests and wait for polling cycles, verify spans appear in Jaeger UI at http://localhost:16686 with correct parent-child relationships, operation names, and request.id attributes. Disable tracing, confirm zero overhead (no OTel imports).

### Implementation for User Story 3

- [x] T013 [US3] Initialize OTel in the application lifespan in `solune/backend/src/main.py` — conditionally import and call `init_otel()` from `otel_setup.py` only when `settings.otel_enabled` is True, store tracer and meter on `app.state` (per research.md Decision 1 conditional import pattern)
- [x] T014 [P] [US3] Add manual OTel spans to polling operations in `solune/backend/src/services/copilot_polling/polling_loop.py` — wrap each polling cycle in a span named "polling.cycle" and each poll step in a child span "polling.step", include request.id attribute via synthetic ID (e.g., `poll-{uuid4().hex[:8]}`), record span status on errors
- [x] T015 [P] [US3] Add manual OTel spans to stall recovery in `solune/backend/src/services/copilot_polling/recovery.py` — wrap recovery operations in a span named "recovery.stall_check", include stall details as span attributes
- [x] T016 [P] [US3] Add manual OTel span to resolve_repository() in `solune/backend/src/utils.py` — wrap the function body in a span named "resolve_repository", include project_id as span attribute
- [x] T017 [P] [US3] Add manual OTel spans to encrypt/decrypt in `solune/backend/src/services/encryption.py` — wrap encrypt() in span "encryption.encrypt" and decrypt() in span "encryption.decrypt", include data_size attribute (never include plaintext/ciphertext content per research.md Decision 9)
- [x] T018 [US3] Emit custom OTel metrics in `solune/backend/src/services/copilot_polling/polling_loop.py` — record pipeline.active_count gauge (from `_pipeline_states` dict length), pipeline.cycle_duration_ms histogram (from span timing), and github.api_remaining gauge (from `get_last_rate_limit()`) per research.md Decision 8
- [x] T019 [US3] Correlate OTel spans with X-Request-ID in `solune/backend/src/services/otel_setup.py` or middleware — read `request_id_var.get("")` from `request_id.py` and set as `request.id` span attribute on every span; for background tasks generate synthetic request ID per research.md Decision 7

**Checkpoint**: At this point, tracing is fully functional when enabled and zero-overhead when disabled.

---

## Phase 6: User Story 4 — Error Tracking for Trend Analysis (Priority: P2)

**Goal**: Initialize Sentry SDK on startup when SENTRY_DSN is configured, auto-capture unhandled exceptions with rich context, and avoid double-tracing when OTel is also active.

**Independent Test**: Set `SENTRY_DSN` to a valid DSN, trigger an unhandled exception, verify it appears in Sentry dashboard with request_id, request path, and method. Confirm no Sentry initialization when DSN is empty.

### Implementation for User Story 4

- [x] T020 [US4] Initialize Sentry in the application lifespan in `solune/backend/src/main.py` — when `settings.sentry_dsn` is non-empty, call `sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0, integrations=[FastApiIntegration()])` to capture exceptions without creating duplicate traces (per research.md Decision 2)
- [x] T021 [US4] Enrich the generic exception handler with Sentry capture in `solune/backend/src/main.py` — in the existing exception handler (around line 495–520), add `sentry_sdk.capture_exception(exc)` with scope context: set_tag("request_id", request_id), set_context("request", {"path": request.url.path, "method": request.method}), and set_user({"id": user_id}) when available; guard with `if sentry_sdk.is_initialized()` check

**Checkpoint**: At this point, User Story 4 is complete — Sentry captures exceptions with rich context, no double-tracing with OTel.

---

## Phase 7: User Story 5 — Optional Trace Visualization Infrastructure (Priority: P3)

**Goal**: Add Jaeger to docker-compose.yml under an observability Compose profile for local trace visualization.

**Independent Test**: Run `docker compose --profile observability up -d`, verify Jaeger UI accessible at http://localhost:16686 and OTLP port 4317 accepting traces. Run `docker compose up` (no profile) and verify Jaeger is NOT started.

### Implementation for User Story 5

- [x] T022 [US5] Add Jaeger service to `docker-compose.yml` — add `jaeger` service using `jaegertracing/jaeger:latest` image with OTLP port 4317 and UI port 16686 mapped, under the `observability` Compose profile so it only starts with `docker compose --profile observability up` (per research.md Decision 6)

**Checkpoint**: Jaeger available for local trace visualization when profile is activated, zero impact on default deployments.

---

## Phase 8: User Story 6 — Rate-Limit History for Capacity Planning (Priority: P3, Optional)

**Goal**: Store rate-limit time-series snapshots in SQLite per polling cycle with 24-hour retention, expose via `GET /api/v1/rate-limit/history`.

**Independent Test**: Run several polling cycles, then `curl GET /api/v1/rate-limit/history?hours=24` and verify time-ordered snapshots with remaining, limit, reset_at. Verify data older than 24 hours is pruned.

### Implementation for User Story 6

- [x] T023 [P] [US6] Create the rate-limit tracker service in `solune/backend/src/services/rate_limit_tracker.py` — implement RateLimitTracker class with `async def record_snapshot(remaining, limit, reset_at)` that inserts into `rate_limit_snapshots` SQLite table (CREATE TABLE IF NOT EXISTS per data-model.md entity 5 schema) and prunes rows older than 24 hours on each insert; implement `async def get_history(hours: int = 24) -> list[dict]` that queries snapshots within the time window ordered by timestamp
- [x] T024 [P] [US6] Implement `GET /api/v1/rate-limit/history` endpoint in `solune/backend/src/api/health.py` (or a new router file) — accept `hours` query parameter (int, default 24, range 1–168), call RateLimitTracker.get_history(hours), return JSON with snapshots array, hours, and count per contract in `specs/001-observability-monitoring/contracts/rate-limit-history.md`
- [x] T025 [US6] Wire rate-limit snapshot recording into `solune/backend/src/services/copilot_polling/polling_loop.py` — after each polling cycle, read rate-limit data from `get_last_rate_limit()` and call `await rate_limit_tracker.record_snapshot(remaining, limit, reset_at)` if data is available

**Checkpoint**: Rate-limit history is captured per polling cycle and queryable via API with automatic 24-hour retention.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final integration verification and documentation.

- [x] T026 Verify zero-overhead regression when all observability features are disabled — start the application without OTEL_ENABLED, SENTRY_DSN, or ALERT_WEBHOOK_URL and confirm no OTel/Sentry imports, no additional network calls, and no behavior change from baseline
- [x] T027 [P] Verify `GET /health` liveness endpoint remains completely unchanged after all modifications (FR-005) in `solune/backend/src/api/health.py`
- [x] T028 Run `specs/001-observability-monitoring/quickstart.md` validation — execute each verification step from the quickstart guide to confirm all features work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (dependencies installed, config fields added) — BLOCKS all user stories
- **US1 Readiness (Phase 3)**: Depends on Phase 2 completion — no dependency on other user stories
- **US2 Alerting (Phase 4)**: Depends on Phase 2 completion (alert_dispatcher.py) — no dependency on US1
- **US3 Tracing (Phase 5)**: Depends on Phase 2 completion (otel_setup.py) — no dependency on US1 or US2
- **US4 Error Tracking (Phase 6)**: Depends on Phase 1 (Sentry dependency) — no dependency on US1, US2, or US3
- **US5 Jaeger (Phase 7)**: Depends on Phase 1 only — fully independent; optional
- **US6 Rate-Limit History (Phase 8)**: Depends on Phase 2 — fully independent; optional
- **Polish (Phase 9)**: Depends on ALL desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US3 (P2)**: Can start after Phase 2 — No dependencies on other stories
- **US4 (P2)**: Can start after Phase 1 — No dependencies on other stories
- **US5 (P3)**: Can start after Phase 1 — No dependencies on other stories
- **US6 (P3)**: Can start after Phase 2 — No dependencies on other stories

### Within Each User Story

- Models/schemas before endpoint handlers
- Service modules before integration wiring
- Core implementation before cross-cutting concerns

### Parallel Opportunities

- T001 and T002 can run in parallel (different dependency groups in same file)
- T003 and T004 can run in parallel (different config sections)
- T005 and T006 can run in parallel (different new files)
- T014, T015, T016, T017 can ALL run in parallel (different files, no dependencies between them)
- T023 and T024 can run in parallel (different new files)
- Once Phase 2 completes, US1, US2, US3, US4, US5, and US6 can ALL start in parallel

---

## Parallel Example: User Story 3 (Distributed Tracing)

```bash
# Launch all manual span instrumentation tasks together (different files):
Task T014: "Add manual OTel spans to polling operations in polling_loop.py"
Task T015: "Add manual OTel spans to stall recovery in recovery.py"
Task T016: "Add manual OTel span to resolve_repository() in utils.py"
Task T017: "Add manual OTel spans to encrypt/decrypt in encryption.py"

# Then sequentially:
Task T018: "Emit custom OTel metrics in polling_loop.py" (depends on T014)
Task T019: "Correlate OTel spans with X-Request-ID" (depends on T014-T17)
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 — Both P1)

1. Complete Phase 1: Setup (dependencies + config)
2. Complete Phase 2: Foundational (alert_dispatcher.py + otel_setup.py)
3. Complete Phase 3: US1 — Readiness Endpoint
4. Complete Phase 4: US2 — SLA-Breach Alerting
5. **STOP and VALIDATE**: Test readiness endpoint (200/503) and alerts (log output, cooldown)
6. Deploy/demo if ready — this is the MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 (Readiness) → Test independently → Deploy/Demo (deployment safety!)
3. Add US2 (Alerting) → Test independently → Deploy/Demo (incident detection!)
4. Add US3 (Tracing) → Test with Jaeger → Deploy/Demo (diagnostic power!)
5. Add US4 (Error Tracking) → Test with Sentry DSN → Deploy/Demo (trend analysis!)
6. Add US5 (Jaeger) → Test locally → Deploy/Demo (dev experience!)
7. Add US6 (Rate-Limit History) → Test query API → Deploy/Demo (capacity planning!)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Readiness) + US2 (Alerting) — both P1, tightly scoped
   - Developer B: US3 (Tracing) — largest story, benefits from dedicated focus
   - Developer C: US4 (Error Tracking) + US5 (Jaeger) + US6 (Rate-Limit History) — lighter stories
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All observability features are opt-in with safe defaults (SC-007)
- `GET /health` MUST remain unchanged throughout (FR-005)
- Encryption service is at `solune/backend/src/services/encryption.py` (not encryption_service.py)
- Frontend changes are explicitly out of scope for Phase 5
