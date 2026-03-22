# Feature Specification: Observability & Monitoring — OpenTelemetry Tracing, Sentry Error Tracking, SLA Alerting & Readiness Endpoint

**Feature Branch**: `001-observability-monitoring`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Phase 5: Observability & Monitoring — OpenTelemetry Tracing, Sentry Error Tracking, SLA Alerting & Readiness Endpoint"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Readiness Endpoint for Deployment Confidence (Priority: P1)

As a platform operator deploying the application to a container orchestrator, I need a readiness endpoint that comprehensively validates all critical subsystems — database writability, authentication credentials, encryption availability, and background task health — so that the orchestrator only routes traffic to instances that are fully operational, preventing users from hitting a partially-booted or degraded service.

**Why this priority**: The readiness endpoint is the foundation of safe deployments and zero-downtime operations. Without it, traffic can be routed to instances missing database connectivity or encryption, causing silent data corruption or service errors. This is the simplest deliverable with the highest operational safety impact and has no external dependencies.

**Independent Test**: Can be fully tested by starting the application with valid configuration and calling `GET /api/v1/ready`, verifying HTTP 200 with a health-check body. Then, each subsystem can be intentionally degraded (e.g., invalid database path, missing OAuth credentials, disabled encryption, killed polling task) and the endpoint re-tested for HTTP 503 with a descriptive failure body.

**Acceptance Scenarios**:

1. **Given** the application is fully started with valid configuration, **When** `GET /api/v1/ready` is called, **Then** it returns HTTP 200 with a body indicating all checks passed (database writeable, OAuth configured, encryption enabled, polling task alive).
2. **Given** the database is unreachable or read-only, **When** `GET /api/v1/ready` is called, **Then** it returns HTTP 503 with a structured body identifying the database check as failed.
3. **Given** GitHub OAuth client ID or secret is empty/missing, **When** `GET /api/v1/ready` is called, **Then** it returns HTTP 503 identifying the OAuth credential check as failed.
4. **Given** the encryption service is disabled, **When** `GET /api/v1/ready` is called, **Then** it returns HTTP 503 identifying the encryption check as failed.
5. **Given** the polling background task has crashed and is not intentionally disabled, **When** `GET /api/v1/ready` is called, **Then** it returns HTTP 503 identifying the polling task check as failed.
6. **Given** the polling task is intentionally disabled via configuration, **When** `GET /api/v1/ready` is called, **Then** the polling task check passes (intentional disable is not a failure).
7. **Given** the existing `GET /health` liveness endpoint, **When** any change is made to health checking, **Then** `GET /health` continues to return the same responses as before — it is unchanged.

---

### User Story 2 — SLA-Breach Alerting for Incident Response (Priority: P1)

As a platform operator, I want the system to automatically detect and alert on SLA-critical conditions — pipeline stalls exceeding a configurable threshold and critically low GitHub API rate limits — so that I can respond to incidents before they visibly degrade user experience, using either log-based monitoring or external webhook integrations.

**Why this priority**: Alerting is the bridge between observability data and human action. Without proactive alerts, operators only discover incidents when users report problems. The pluggable alert dispatcher with log-only default mode has zero external dependencies, making it immediately useful in any deployment while supporting optional webhook integration for teams with incident management tools.

**Independent Test**: Can be tested by configuring a very low pipeline stall threshold (e.g., 1 minute), artificially stalling a pipeline, and verifying that an alert is dispatched (visible in logs). Rate limit alerts can be tested by configuring a high critical threshold and verifying alert dispatch when the API remaining count drops below it. Cooldown can be verified by checking that repeated threshold breaches within 15 minutes do not produce duplicate alerts.

**Acceptance Scenarios**:

1. **Given** a stalled pipeline that has exceeded the configurable `pipeline_stall_alert_minutes` threshold (default 30 minutes), **When** stall recovery detects the condition, **Then** a `pipeline_stall` alert is dispatched via the alert dispatcher with a summary and details about the stalled pipeline.
2. **Given** the GitHub API remaining quota drops below the configurable `rate_limit_critical_threshold` (default 20), **When** the polling loop detects the condition, **Then** a `rate_limit_critical` alert is dispatched with the current remaining count and limit details.
3. **Given** a `pipeline_stall` alert was dispatched less than 15 minutes ago, **When** another stall condition is detected for the same alert type, **Then** the alert is suppressed (cooldown enforcement) and no duplicate alert is sent.
4. **Given** the `alert_webhook_url` setting is configured, **When** an alert is dispatched, **Then** the alert payload is delivered to the webhook URL in addition to being logged.
5. **Given** no `alert_webhook_url` is configured (default), **When** an alert is dispatched, **Then** the alert is logged as a structured log message and no external network calls are made.
6. **Given** configurable thresholds for `pipeline_stall_alert_minutes` (default 30), `agent_timeout_alert_minutes` (default 15), and `rate_limit_critical_threshold` (default 20), **When** an operator adjusts these values, **Then** the alerting behavior respects the new thresholds.

---

### User Story 3 — Distributed Tracing for Incident Diagnosis (Priority: P2)

As a platform operator investigating a production incident, I want distributed tracing across all backend operations — including request handling, polling cycles, stall recovery, repository resolution, and encryption — so that I can trace the full lifecycle of any operation, identify bottlenecks, and correlate traces with structured logs using the existing request ID.

**Why this priority**: Distributed tracing is the most powerful diagnostic tool for complex production issues, but it requires the readiness and alerting infrastructure (P1) to be in place first. Tracing is opt-in and adds no overhead when disabled, making it safe to deploy incrementally.

**Independent Test**: Can be tested by enabling tracing, performing operations (API requests, polling cycles, stall recovery), and verifying that spans appear in the trace collector UI with correct parent-child relationships, operation names, and request ID attributes. A separate regression test confirms that disabling tracing results in zero tracing-related overhead.

**Acceptance Scenarios**:

1. **Given** tracing is enabled via configuration, **When** the application starts, **Then** the tracing system is initialized with automatic instrumentation for HTTP request handling, outbound HTTP calls, and database operations.
2. **Given** tracing is enabled, **When** a polling cycle executes, **Then** a trace span is created for the overall cycle and child spans for each poll step, with timing and status attributes.
3. **Given** tracing is enabled, **When** stall recovery runs, **Then** a trace span captures the recovery operation with details about the stalled items.
4. **Given** tracing is enabled, **When** a repository resolution call is made, **Then** a trace span captures the call duration and result.
5. **Given** tracing is enabled, **When** encryption or decryption operations occur, **Then** trace spans capture the timing of these operations.
6. **Given** tracing is enabled, **When** any trace span is created, **Then** the existing `X-Request-ID` context variable is included as a span attribute, making traces cross-referenceable with structured JSON logs.
7. **Given** tracing is disabled (default), **When** the application runs, **Then** zero tracing-related overhead is incurred — no tracing libraries are imported, no spans are created, and no network calls to trace collectors occur.
8. **Given** tracing is enabled, **When** operations execute, **Then** the following custom metrics are emitted: active pipeline count (gauge), polling cycle duration (histogram), and GitHub API remaining quota (gauge).

---

### User Story 4 — Error Tracking for Trend Analysis (Priority: P2)

As a platform operator, I want all unhandled exceptions to be automatically captured and reported to a centralized error tracking service with rich context (user ID, project ID, request path, request ID), so that I can identify error trends, track regressions, and prioritize fixes based on frequency and impact.

**Why this priority**: Error tracking complements distributed tracing by capturing the "what went wrong" alongside the "where it happened." It is opt-in (no-op when unconfigured) and enriches existing exception handling without changing error behavior, making it a safe addition after core observability is in place.

**Independent Test**: Can be tested by configuring the error tracking DSN, triggering an unhandled exception, and verifying it appears in the error tracking service dashboard with correct context tags (user ID, project ID, request path, request ID). A regression test confirms that without the DSN configured, no error tracking initialization occurs and no network calls are made.

**Acceptance Scenarios**:

1. **Given** the error tracking DSN is configured, **When** the application starts, **Then** the error tracking service is initialized and automatically captures unhandled exceptions with request context.
2. **Given** the error tracking service is initialized, **When** an unhandled exception occurs in any request, **Then** the exception is reported with enriched context including user ID, project ID, request path, and request ID tag.
3. **Given** both error tracking and distributed tracing are enabled simultaneously, **When** the application runs, **Then** no double-tracing occurs — the error tracking service's own tracing is disabled to avoid duplicate trace data.
4. **Given** the error tracking DSN is not configured (default), **When** the application runs, **Then** no error tracking initialization occurs and no network calls are made to any external error tracking service.

---

### User Story 5 — Optional Trace Visualization Infrastructure (Priority: P3)

As a developer working on the platform locally, I want a one-command setup for a trace visualization tool that receives and displays distributed traces, so that I can visually inspect trace data during development and debugging without needing to configure external services.

**Why this priority**: This is a developer convenience feature that enhances the tracing experience but is not required for production observability. It is activated only through an explicit opt-in mechanism (Compose profile) and has no impact on production deployments.

**Independent Test**: Can be tested by starting the development environment with the observability profile enabled, performing traced operations, and verifying that traces appear in the visualization UI with correct span hierarchies and timing.

**Acceptance Scenarios**:

1. **Given** the developer activates the observability profile in the development environment, **When** the environment starts, **Then** a trace visualization service is available and accepting trace data on the standard telemetry port.
2. **Given** the trace visualization service is running and tracing is enabled, **When** the application processes requests and background operations, **Then** traces are visible in the visualization UI with correct span hierarchies, timing, and attributes.
3. **Given** the developer does not activate the observability profile, **When** the development environment starts, **Then** no trace visualization service is started and no resources are consumed.

---

### User Story 6 — Rate Limit History for Capacity Planning (Priority: P3)

As a platform operator monitoring GitHub API usage patterns, I want historical rate-limit data captured over time and accessible through an API, so that I can identify usage trends, plan for capacity, and correlate rate-limit drops with specific operations or time periods.

**Why this priority**: This is an enhancement to existing rate-limit visibility (the color-coded bar already shows current state). Historical data provides trend analysis capability but is not critical for incident detection (which is covered by the P1 alerting story). This is optional/low-priority per the technical notes.

**Independent Test**: Can be tested by running several polling cycles, then querying the history endpoint and verifying that timestamped rate-limit snapshots are returned with remaining, limit, and reset values. Retention can be verified by checking that data older than 24 hours is automatically pruned.

**Acceptance Scenarios**:

1. **Given** the application is running with polling enabled, **When** each polling cycle completes, **Then** a rate-limit snapshot (timestamp, remaining, limit, reset time) is recorded.
2. **Given** rate-limit snapshots have been recorded, **When** `GET /api/v1/rate-limit/history?hours=24` is called, **Then** it returns a time-ordered list of snapshots from the last 24 hours.
3. **Given** rate-limit snapshots older than 24 hours exist, **When** retention cleanup runs, **Then** snapshots older than 24 hours are automatically deleted.
4. **Given** a configurable time window parameter (default 24 hours), **When** the history endpoint is called with a different `hours` value, **Then** it returns snapshots for the requested time window.

---

### Edge Cases

- What happens when the database becomes read-only during a readiness check? The readiness endpoint detects the failure via the write-then-delete probe and returns HTTP 503 without corrupting data.
- What happens when the trace collector is unreachable while tracing is enabled? The application continues to function normally; trace export failures are handled gracefully and logged without impacting request processing.
- What happens when the error tracking service is unreachable after initialization? The application continues to function normally; error reporting failures are handled gracefully in the background.
- What happens when webhook delivery fails for an alert? The alert is still logged locally; webhook delivery failures are logged as warnings but do not prevent the alert from being recorded.
- What happens when multiple subsystem failures occur simultaneously during a readiness check? The endpoint reports all failures in its response body, not just the first one encountered.
- What happens when the cooldown period expires exactly at the boundary (e.g., 15 minutes to the second)? The next alert of the same type is allowed to fire — boundary is inclusive (at or after 15 minutes).
- What happens when the polling task is restarted after a crash? The readiness endpoint begins reporting healthy again once the task is alive, without requiring a full application restart.
- What happens when rate-limit history has no data (fresh deployment)? The history endpoint returns an empty list with HTTP 200, not an error.
- What happens when tracing is enabled but no trace collector is configured? Tracing initializes with the configured endpoint (defaulting to localhost); export failures are handled gracefully.

## Requirements *(mandatory)*

### Functional Requirements

#### Readiness Endpoint

- **FR-001**: System MUST expose a `GET /api/v1/ready` readiness endpoint that returns HTTP 200 only when all four subsystem checks pass: database is writeable, authentication credentials are present, encryption service is enabled, and the polling background task is alive or intentionally disabled.
- **FR-002**: System MUST return HTTP 503 from the readiness endpoint when any subsystem check fails, with a structured response body following the IETF health-check format that identifies which checks passed and which failed.
- **FR-003**: The readiness endpoint's database check MUST verify actual write capability by inserting into and deleting from a scratch table, not merely testing connectivity.
- **FR-004**: The readiness endpoint MUST treat a polling task that is intentionally disabled via configuration as a passing check (not a failure).
- **FR-005**: The existing `GET /health` liveness endpoint MUST remain completely unchanged — no modifications to its behavior, response format, or status codes.

#### Alert Dispatcher

- **FR-006**: System MUST implement a pluggable alert dispatcher with the interface `dispatch_alert(alert_type, summary, details)` that supports log-only mode by default and optional webhook delivery when a webhook URL is configured.
- **FR-007**: The alert dispatcher MUST enforce per-type cooldown, preventing the same alert type from firing more than once per 15 minutes, regardless of delivery mode.
- **FR-008**: System MUST dispatch a `pipeline_stall` alert when stall recovery detects a pipeline stall exceeding the configurable `pipeline_stall_alert_minutes` threshold (default: 30 minutes).
- **FR-009**: System MUST dispatch a `rate_limit_critical` alert when the polling loop detects that the GitHub API remaining quota is below the configurable `rate_limit_critical_threshold` (default: 20).
- **FR-010**: System MUST support configurable thresholds: `pipeline_stall_alert_minutes` (default 30), `agent_timeout_alert_minutes` (default 15), and `rate_limit_critical_threshold` (default 20).
- **FR-011**: When a webhook URL is configured, the alert dispatcher MUST deliver the alert payload to the webhook URL via HTTP. On delivery failure, the alert MUST still be logged locally.

#### Distributed Tracing

- **FR-012**: System MUST support opt-in distributed tracing that is gated behind a configuration flag (disabled by default), such that deployments without the flag incur zero import or runtime overhead.
- **FR-013**: When tracing is enabled, system MUST automatically instrument HTTP request handling, outbound HTTP client calls, and database operations.
- **FR-014**: When tracing is enabled, system MUST create manual trace spans for: each polling cycle and individual poll steps, stall recovery operations, repository resolution calls, and encrypt/decrypt operations.
- **FR-015**: When tracing is enabled, system MUST emit custom metrics: active pipeline count (gauge), polling cycle duration (histogram), and GitHub API remaining quota (gauge).
- **FR-016**: All trace spans MUST include the existing `X-Request-ID` context variable as a span attribute, enabling cross-referencing between traces and structured JSON logs.
- **FR-017**: When tracing is disabled (default), no tracing libraries MUST be imported and no tracing-related processing MUST occur.

#### Error Tracking

- **FR-018**: System MUST support opt-in error tracking that initializes only when a DSN is configured, auto-capturing unhandled exceptions with request context.
- **FR-019**: When error tracking is active, the generic exception handler MUST enrich reported exceptions with context: user ID, project ID, request path, and request ID tag.
- **FR-020**: When both error tracking and distributed tracing are enabled simultaneously, the error tracking service's own trace sampling MUST be set to zero to avoid duplicate trace data.
- **FR-021**: When no error tracking DSN is configured (default), no error tracking initialization MUST occur and no external network calls MUST be made.

#### Rate-Limit History (Optional)

- **FR-022**: System SHOULD record rate-limit snapshots (timestamp, remaining, limit, reset time) sampled each polling cycle.
- **FR-023**: System SHOULD expose a `GET /api/v1/rate-limit/history` endpoint that returns time-ordered snapshots for a configurable time window (default 24 hours via `hours` query parameter).
- **FR-024**: System SHOULD automatically prune rate-limit snapshots older than 24 hours.

#### Trace Visualization Infrastructure (Optional)

- **FR-025**: System SHOULD provide an optional local trace visualization service activated only through a dedicated environment profile, with no impact on default or production deployments.

### Key Entities

- **Readiness Check Result**: Represents the outcome of a single subsystem health check — includes the check name (database, oauth, encryption, polling), status (pass/fail), and optional failure details. Aggregated into the readiness endpoint response.
- **Alert**: Represents a dispatched alert event — includes alert type (pipeline_stall, rate_limit_critical), summary text, detail payload, dispatch timestamp, and delivery status (logged, webhook_sent, webhook_failed).
- **Alert Cooldown Record**: Tracks the last dispatch time for each alert type to enforce the 15-minute cooldown window — includes alert type and last fired timestamp.
- **Trace Span**: Represents a unit of work in a distributed trace — includes operation name, start/end time, parent span reference, status, and attributes (including request ID). Created automatically for instrumented operations and manually for critical backend operations.
- **Custom Metric**: Represents a named measurement emitted during operation — includes metric name (pipeline.active_count, pipeline.cycle_duration_ms, github.api_remaining), metric type (gauge or histogram), and current value.
- **Rate-Limit Snapshot**: Represents a point-in-time capture of GitHub API rate-limit state — includes timestamp, remaining calls, total limit, and reset time. Stored with 24-hour retention.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Readiness endpoint correctly reports healthy (HTTP 200) within 2 seconds when all subsystems are operational, and correctly reports unhealthy (HTTP 503) within 2 seconds when any subsystem is degraded — achieving 100% accuracy across all four check types.
- **SC-002**: SLA-breach alerts fire within 60 seconds of threshold violation detection, with zero duplicate alerts within the 15-minute cooldown window per alert type.
- **SC-003**: When tracing is disabled, the application exhibits zero measurable overhead — no additional memory consumption, no additional network calls, and no increase in request latency compared to a baseline without the tracing feature deployed.
- **SC-004**: When tracing is enabled, all critical operations (request handling, polling cycles, recovery, resolution, encryption) produce correlated trace spans that include the request ID, enabling operators to trace any operation end-to-end.
- **SC-005**: When error tracking is configured, 100% of unhandled exceptions are captured with full context (user ID, project ID, request path, request ID), enabling operators to identify the top error sources within 5 minutes of an incident.
- **SC-006**: Operators can determine application readiness for traffic within 5 seconds of querying the readiness endpoint — reducing deployment-related incident detection time from minutes (user-reported) to seconds (automated).
- **SC-007**: All observability features (tracing, error tracking, alerting) are fully opt-in with safe defaults (disabled), requiring zero configuration changes for existing deployments to continue operating without any behavioral change.
- **SC-008**: Rate-limit history (when enabled) provides at least 24 hours of historical data, allowing operators to identify usage patterns and plan capacity adjustments.

## Assumptions

- The existing `GET /health` liveness endpoint follows a simple alive/dead pattern and does not perform deep subsystem validation — justifying the need for a separate readiness endpoint.
- The `X-Request-ID` context variable is already propagated through all request handling middleware and is available for inclusion in trace span attributes.
- The existing structured JSON logging system supports log correlation with trace IDs when the request ID is included as both a log field and a span attribute.
- The existing polling loop and stall recovery mechanisms expose sufficient hooks (lifecycle events, health status) to integrate alerting without modifying their core logic.
- The error tracking service's SDK supports disabling its own tracing independently of exception capture, allowing both error tracking and distributed tracing to coexist without conflict.
- Webhook alert delivery uses a fire-and-forget pattern with timeout protection — the alert dispatcher does not retry failed webhook deliveries to avoid blocking critical operations.
- The database scratch table used by the readiness check is created if it does not exist and uses minimal schema to avoid schema migration dependencies.
- Configuration for all observability features uses environment variables with sensible defaults, following the existing configuration pattern in the application.
