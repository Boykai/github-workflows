# Implementation Plan: Observability & Monitoring — OpenTelemetry Tracing, Sentry Error Tracking, SLA Alerting & Readiness Endpoint

**Branch**: `001-observability-monitoring` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-observability-monitoring/spec.md`

## Summary

Add comprehensive observability and monitoring to the Solune backend: a Kubernetes-style readiness endpoint (`GET /api/v1/ready`) validating four critical subsystems; a pluggable alert dispatcher with per-type cooldown for SLA-breach notifications; opt-in OpenTelemetry distributed tracing and metrics gated behind `OTEL_ENABLED`; opt-in Sentry error tracking gated behind `SENTRY_DSN`; and optional rate-limit history storage with a query API. All features default to disabled/log-only, requiring zero configuration changes for existing deployments.

## Technical Context

**Language/Version**: Python 3.13 (target-version in ruff/pyright), requires >=3.12
**Primary Dependencies**: FastAPI, Pydantic (BaseSettings), HTTPX, aiosqlite, slowapi; new: opentelemetry-api, opentelemetry-sdk, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-httpx, opentelemetry-instrumentation-aiosqlite, opentelemetry-exporter-otlp, sentry-sdk[fastapi]
**Storage**: SQLite via aiosqlite (path: `/var/lib/solune/data/settings.db`); new scratch table for readiness write-check; optional `rate_limit_snapshots` table for history
**Testing**: pytest (existing backend test suite in `solune/backend/tests/`)
**Target Platform**: Linux server (Docker, Kubernetes)
**Project Type**: Web application (backend: FastAPI Python, frontend: React/TypeScript)
**Performance Goals**: Readiness endpoint responds within 2 seconds (SC-001); alerts fire within 60 seconds of threshold violation (SC-002); zero measurable overhead when tracing disabled (SC-003)
**Constraints**: All observability features must be fully opt-in with safe defaults (SC-007); no mandatory external dependencies; `GET /health` must remain unchanged (FR-005)
**Scale/Scope**: Backend-only changes (no mandatory frontend work); 6 user stories (2×P1, 2×P2, 2×P3); ~8 modified files, ~3 new files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, edge cases, and scope boundaries. |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. |
| **III. Agent-Orchestrated** | ✅ PASS | `speckit.plan` agent produces plan.md, research.md, data-model.md, contracts/, quickstart.md. Handoff to `speckit.tasks` for tasks.md. |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; spec focuses on acceptance scenarios. Tests may be added during implementation per operator discretion. |
| **V. Simplicity & DRY** | ✅ PASS | Alert dispatcher uses simple log-only default; OTel/Sentry are opt-in with zero-overhead when disabled; no premature abstraction. |
| **Branch Naming** | ✅ PASS | Feature uses `001-observability-monitoring` pattern. |
| **Phase-Based Execution** | ✅ PASS | Specify phase complete → Plan phase (this artifact) → Tasks → Implement. |
| **Independent Stories** | ✅ PASS | All 6 user stories have independent test criteria and deliver standalone value. |

**Gate Result**: ✅ ALL PASSED — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-observability-monitoring/
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions and research
├── data-model.md        # Phase 1: Entity definitions and relationships
├── quickstart.md        # Phase 1: Developer quick-start guide
├── contracts/           # Phase 1: API endpoint specifications
│   ├── readiness.md     # GET /api/v1/ready contract
│   ├── rate-limit-history.md  # GET /api/v1/rate-limit/history contract
│   └── alert-dispatcher.md    # Alert dispatcher interface contract
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (speckit.tasks — not created here)
```

### Source Code (repository root)

```text
solune/backend/
├── pyproject.toml                          # MODIFY: Add OTel + Sentry dependencies
├── src/
│   ├── config.py                           # MODIFY: Add otel_enabled, otel_endpoint,
│   │                                       #   otel_service_name, sentry_dsn,
│   │                                       #   pipeline_stall_alert_minutes,
│   │                                       #   agent_timeout_alert_minutes,
│   │                                       #   rate_limit_critical_threshold,
│   │                                       #   alert_webhook_url, alert_cooldown_minutes
│   ├── main.py                             # MODIFY: Lifespan (OTel/Sentry init),
│   │                                       #   exception handler (Sentry capture)
│   ├── api/
│   │   └── health.py                       # MODIFY: Add GET /api/v1/ready endpoint
│   ├── middleware/
│   │   └── request_id.py                   # READ-ONLY: Request ID context variable
│   ├── logging_utils.py                    # READ-ONLY: Structured logging infrastructure
│   ├── utils.py                            # MODIFY: Add OTel span to resolve_repository()
│   └── services/
│       ├── alert_dispatcher.py             # NEW: Pluggable alert dispatcher
│       ├── otel_setup.py                   # NEW: OTel TracerProvider/MeterProvider init
│       ├── rate_limit_tracker.py           # NEW (optional): Rate-limit snapshot storage
│       ├── encryption_service.py           # MODIFY: Add OTel spans to encrypt/decrypt
│       ├── copilot_polling/
│       │   ├── polling_loop.py             # MODIFY: Add OTel spans + rate_limit_critical alert
│       │   ├── recovery.py                 # MODIFY: Add OTel spans + pipeline_stall alert
│       │   └── state.py                    # READ-ONLY: Polling state constants
│       └── github_projects/
│           └── service.py                  # READ-ONLY: _extract_rate_limit_headers()
└── tests/                                  # Existing test infrastructure

docker-compose.yml                          # MODIFY: Add optional Jaeger service (observability profile)
```

**Structure Decision**: Web application structure (backend + frontend). All Phase 5 changes are backend-only. Frontend changes are explicitly out of scope per spec. New files follow existing service pattern in `solune/backend/src/services/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| OTel conditional import gating | Zero-overhead requirement (FR-012, FR-017, SC-003) demands that OTel libraries are not even imported when disabled | Simple flag-check would still import libraries, consuming memory and startup time |
| Separate `otel_setup.py` module | Isolates OTel initialization complexity from main.py lifespan; contains TracerProvider, MeterProvider, instrumentor setup | Inline in main.py would bloat the lifespan function and mix concerns |
| Alert dispatcher as separate service | Reusable across recovery.py and polling_loop.py with shared cooldown state | Duplicating cooldown logic in each call site would violate DRY |
