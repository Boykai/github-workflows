# Feature Specification: Advanced Testing for Deep Unknown Bugs

**Feature Branch**: `047-advanced-testing`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Level 2 — Advanced Testing for Deep Unknown Bugs: concurrency & race condition testing, fault injection & chaos testing, stateful property-based testing, runtime type validation, fuzz testing, integration testing without mocks, and flaky test detection."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Concurrency & Race Condition Testing (Priority: P1)

As a developer, I want the test suite to detect concurrency bugs in shared backend state so that race conditions in the polling subsystem and multi-step database operations are caught before production.

The backend polling subsystem has shared mutable state accessed by multiple concurrent async tasks (watchdog, polling loop, API handlers). Multi-step operations in the workflow orchestrator and signal bridge run without transaction safety. Concurrency stress tests will spawn parallel coroutines that exercise these shared resources simultaneously, enforce invariants (e.g., only one polling loop active at a time), and inject failures between steps to verify rollback or cleanup behavior.

**Why this priority**: Known unprotected shared state means real race conditions exist today — these tests will find bugs immediately with high confidence.

**Independent Test**: Can be fully tested by running the new concurrency test suite against the existing backend. Any invariant violation or duplicate-loop detection is a confirmed bug.

**Acceptance Scenarios**:

1. **Given** the polling subsystem is idle, **When** two concurrent tasks attempt to start the polling loop simultaneously, **Then** only one polling loop runs and the second is rejected or queued.
2. **Given** a multi-step orchestrator operation (create issue + track + update state), **When** a failure is injected at step 2, **Then** all prior steps are rolled back and the system is in a consistent state.
3. **Given** two tasks read and write the same polling state field, **When** they execute with forced interleaving using barriers, **Then** read-write ordering invariants hold and no data is corrupted.

---

### User Story 2 — Fault Injection & Chaos Testing (Priority: P2)

As a developer, I want systematic fault injection tests for every external service dependency so that background loops and service calls degrade gracefully under realistic failure conditions.

The background loops (polling watchdog, session cleanup, Signal WebSocket listener) have resilience logic that is never tested. Fault injection tests will systematically inject timeout errors, connection failures, partial responses, and cancellation errors into all external call paths (GitHub REST/GraphQL, Signal WebSocket, LLM provider), verifying the system logs, retries, and never crashes.

**Why this priority**: Background loops and the Signal listener are critical infrastructure — silent message loss and spin-looping on failure are high-severity production risks.

**Independent Test**: Can be tested by starting background loops in isolation, injecting specific failures, and asserting correct retry behavior, backoff timing, and logging output.

**Acceptance Scenarios**:

1. **Given** the system calls an external service, **When** that service returns a timeout or connection error, **Then** the system logs the error and retries (cleanup loop with exponential backoff; watchdog at fixed 30s interval — the lack of watchdog backoff is a known deficiency to surface).
2. **Given** the Signal WebSocket listener is running, **When** a message processing error occurs, **Then** the failed message is logged with enough detail to reconstruct it.
3. **Given** the polling watchdog monitors its inner task, **When** the inner task is killed, **Then** the watchdog restarts it correctly without spin-looping.

---

### User Story 3 — Stateful Property-Based Testing (Priority: P3)

As a developer, I want automated exploration of thousands of random pipeline state transitions so that invalid state combinations are caught without manually writing every edge case.

The pipeline has a formal state model with status, agent index, completed agents, execution mode, and parallel agent statuses. Stateful property tests will model the pipeline as a state machine with rules (start, advance, fail, skip, complete, cancel) and invariants (valid index bounds, valid status transitions, completed-agents subset correctness). The same approach applies to the bounded cache data structures.

**Why this priority**: The pipeline state machine is complex enough to have non-obvious invalid-state edge cases that manual test-writing would miss.

**Independent Test**: Can be tested by running the stateful test suite which exercises 10,000+ random transition sequences per run. Any invariant violation is a confirmed bug.

**Acceptance Scenarios**:

1. **Given** the pipeline state machine model, **When** 10,000+ random sequences of start/advance/fail/skip/complete/cancel transitions run, **Then** no sequence reaches an invalid state (e.g., "completed" transitioning back to "in_progress", current_agent_index exceeding agent count).
2. **Given** the bounded cache structures, **When** random sequences of insert/read/delete operations run, **Then** item count never exceeds the configured maximum and eviction order is correct.

---

### User Story 4 — Runtime Type Validation (Priority: P4)

As a developer, I want runtime validation of API responses on the frontend and webhook payloads on the backend so that type drift between frontend and backend is caught immediately rather than causing silent undefined values.

The frontend has zero runtime validation of API responses — TypeScript types exist only at compile time. The backend accepts webhook payloads as untyped dictionaries and navigates them with fragile chained `.get()` calls. Runtime validation schemas for the highest-traffic API responses and typed webhook payload models will catch field renames, type changes, and missing fields at the boundary.

**Why this priority**: Type drift between frontend and backend is a real, recurring class of bugs. Typed webhook models also replace fragile `.get().get()` chains with validated access.

**Independent Test**: Can be tested by deliberately changing a backend response field name and verifying the frontend runtime validation catches it, and by sending a webhook payload missing a required field and verifying the backend rejects it.

**Acceptance Scenarios**:

1. **Given** a frontend API call, **When** the backend response is missing a required field or has a changed type, **Then** runtime validation raises an error in development/test mode.
2. **Given** a webhook payload arrives, **When** it is missing a required field, **Then** the typed payload model rejects it with a clear validation error.
3. **Given** a model field stored as untyped data, **When** unexpected shapes (deeply nested objects, null values, unicode keys) are stored and retrieved, **Then** the data round-trips correctly through the storage layer without corruption.

---

### User Story 5 — Fuzz Testing for Parsing Boundaries (Priority: P5)

As a developer, I want fuzz testing of all parsing boundaries (webhook JSON, markdown generation, frontend JSON.parse calls) so that malformed input never causes unhandled crashes.

Three key parsing boundaries accept external input and can crash on unexpected structures: the webhook payload handler (untyped dict from GitHub), markdown table generation (agent/model names injected into formatted strings), and frontend JSON.parse call sites (raw WebSocket messages). Fuzz tests will generate random payloads, malformed JSON, and adversarial strings to exercise these boundaries and verify graceful error handling.

**Why this priority**: Parsing boundaries are where external (untrusted) data enters the system — any unhandled exception here is both a bug and a potential reliability risk.

**Independent Test**: Can be tested by running the fuzz suite and checking that no fuzzed input causes an unhandled exception.

**Acceptance Scenarios**:

1. **Given** a structurally valid but unexpected webhook payload, **When** it is processed by the webhook handler, **Then** no unhandled exception occurs.
2. **Given** malformed JSON, empty strings, or deeply nested objects, **When** they are passed to frontend JSON.parse call sites, **Then** the call site handles the error gracefully.
3. **Given** adversarial strings (backticks, newlines, angle brackets, unicode) as agent or model names, **When** they are rendered into markdown tables, **Then** the table structure remains valid.

---

### User Story 6 — Integration Testing Without Mocks (Priority: P6)

As a developer, I want integration tests that wire up real internal components (database, services, middleware, WebSocket) with only external services mocked, so that wiring bugs invisible to fully-mocked unit tests are caught.

The current test suite mocks almost all dependencies. A "thin mock" integration test configuration that only mocks external services (GitHub, LLM, Signal) but uses real internal wiring will exercise the actual component interactions. Additionally, migration regression tests will verify database schema evolution preserves existing data.

**Why this priority**: Integration wiring bugs are structurally invisible to the current fully-mocked suite — this is a known blind spot.

**Independent Test**: Can be tested by running the thin-mock integration suite through critical user flows (create project, send chat, view board) and verifying end-to-end behavior.

**Acceptance Scenarios**:

1. **Given** a thin-mock test client with real internal wiring, **When** a critical user flow (project creation → chat → board view) is executed, **Then** all internal component interactions succeed without error.
2. **Given** a database at migration N with test data, **When** migration N+1 is applied, **Then** existing data is preserved or correctly transformed.

---

### User Story 7 — Flaky Test Detection & Test Quality (Priority: P7)

As a developer, I want automated flaky test detection and test execution time tracking so that non-deterministic failures are identified and slow tests are flagged for investigation.

Flaky tests erode trust in the test suite and hide real failures. Running the suite multiple times in CI (scheduled, not on every PR) and flagging any test that produces inconsistent results will surface non-determinism. Execution time reporting highlights tests that are suspiciously slow (likely doing real I/O) or suspiciously fast (likely not testing anything).

**Why this priority**: This is test quality infrastructure — important but lower urgency than finding actual bugs.

**Independent Test**: Can be tested by running the suite 3 times and comparing results. Any test with inconsistent pass/fail is flagged.

**Acceptance Scenarios**:

1. **Given** the test suite runs 3 times in CI, **When** a test passes in some runs but fails in others, **Then** it is reported as flaky with the failing runs identified.
2. **Given** test execution completes, **When** the 20 slowest tests are reported, **Then** tests exceeding 5 seconds are flagged for review.

---

### Edge Cases

- What happens when concurrent tasks race on a state field that is created lazily (doesn't exist yet at read time)?
- How does the system handle a fault injection scenario where the database connection itself is lost mid-transaction?
- What happens when a fuzz-generated payload passes HMAC verification but contains no recognizable event type?
- How do stateful property tests handle the pipeline being cancelled and restarted in rapid succession?
- What happens when a thin-mock integration test triggers a real WebSocket connection that the test infrastructure can't clean up?
- How does frontend runtime validation behave when the response is a valid but empty object `{}`?

## Requirements *(mandatory)*

### Functional Requirements

**Concurrency & Race Conditions**

- **FR-001**: Test suite MUST include stress tests that spawn multiple concurrent coroutines accessing shared polling state and assert that invariants (single active loop, consistent state) are maintained.
- **FR-002**: Test suite MUST include transaction safety tests that inject failures between steps of multi-step database operations and verify the system does not end up in a half-committed state.
- **FR-003**: Test suite MUST include forced-interleaving tests that use synchronization barriers to reproduce specific race condition orderings.

**Fault Injection & Chaos**

- **FR-004**: Test suite MUST systematically inject timeout errors, connection failures, partial responses, and cancellation errors for every external service dependency.
- **FR-005**: Test suite MUST verify that background loops (polling watchdog, session cleanup) restart correctly after inner task failure without spin-looping.
- **FR-006**: Test suite MUST verify that failed Signal messages are logged with sufficient detail to reconstruct the original message content (minimum: message sender, timestamp, first 500 characters of content, and error traceback).

**Stateful Property-Based Testing**

- **FR-007**: Test suite MUST include a state machine model of the pipeline that explores at least 10,000 random transition sequences per test run and enforces state invariants.
- **FR-008**: Test suite MUST include stateful tests for bounded cache structures verifying max-size enforcement and eviction ordering under random operation sequences.

**Runtime Type Validation**

- **FR-009**: The five highest-traffic frontend API responses MUST have runtime validation schemas that detect missing or mistyped fields in development/test mode.
- **FR-010**: Backend webhook payloads MUST be validated against typed models that reject payloads missing required fields with clear error messages.
- **FR-011**: Test suite MUST verify that all model fields stored as untyped data round-trip correctly through the storage layer with unexpected shapes (nested objects, null, unicode keys, deep nesting).

**Fuzz Testing**

- **FR-012**: Test suite MUST fuzz webhook payload parsing with randomly generated payloads and assert no unhandled exceptions.
- **FR-013**: Test suite MUST fuzz frontend JSON.parse call sites with malformed JSON, empty strings, and deeply nested objects.
- **FR-014**: Test suite MUST fuzz markdown table generation with adversarial agent/model names and verify table structural integrity.

**Integration Testing**

- **FR-015**: Test suite MUST include a thin-mock test configuration that only mocks external services while wiring real internal components.
- **FR-016**: Test suite MUST include database migration regression tests verifying data preservation across sequential migration application.

**Test Quality**

- **FR-017**: CI MUST include a scheduled job that runs the test suite multiple times and flags any test with inconsistent results as flaky.
- **FR-018**: CI MUST report the 20 slowest tests with execution times to identify tests exceeding acceptable duration thresholds.

### Key Entities

- **Polling State**: Shared mutable state governing the polling subsystem lifecycle (running status, processed issues, pending assignments, claimed PRs).
- **Pipeline State**: Formal state model with status, current agent index, completed agents, execution mode, and parallel agent statuses — target of state machine verification.
- **Bounded Cache**: Fixed-size cache structures (BoundedDict, BoundedSet) with eviction policies — target of stateful property tests.
- **Webhook Payload**: Incoming event payloads from GitHub (pull request events, issue events) — currently untyped, target of runtime validation and fuzz testing.
- **API Response**: Backend responses consumed by the frontend (projects, board, chat, pipeline, settings) — currently validated only at compile time, target of runtime schema validation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Concurrency stress tests reproduce at least one real race condition (e.g., duplicate polling loop), and the fix is verifiable by a then-passing test.
- **SC-002**: Fault injection tests discover at least one previously unhandled failure path in external service calls or background loops.
- **SC-003**: The Signal message loss test demonstrates the bug concretely — a processing error discards a message with no retry, dead-letter, or sufficient log detail.
- **SC-004**: Stateful pipeline tests explore 10,000+ transition sequences per run with zero invalid states reached (or any invalid state found is a confirmed, fixable bug).
- **SC-005**: Deliberately changing a backend API response field causes the frontend runtime validation to catch it in development/test mode.
- **SC-006**: A webhook payload missing a required field is rejected by the typed model with a clear validation error rather than causing a downstream crash.
- **SC-007**: Fuzz tests find at least one crash or unhandled exception in webhook parsing, JSON.parse paths, or markdown rendering that is subsequently fixed.
- **SC-008**: Thin-mock integration tests discover at least one wiring bug that is invisible to the current fully-mocked test suite.
- **SC-009**: Migration regression tests verify that all 5 existing migration files (023–027) apply sequentially without data loss.
- **SC-010**: Flaky test detection identifies all non-deterministic tests, and the flaky test count is reduced to zero after remediation.
- **SC-011**: All new tests run within the existing CI time budget — total backend test suite execution does not increase by more than 60 seconds.

## Assumptions

- The existing foundational test infrastructure from feature 046 (coverage enforcement, mutation testing, property-based testing, contract validation) is already merged and available on `main`.
- External service mocks (GitHub API, LLM provider, Signal) already exist in the test fixtures and can be reused for the thin-mock integration configuration.
- The backend's async framework supports deterministic task interleaving via synchronization primitives (events, barriers) for reproducibility.
- Runtime type validation on the frontend is intended for development/test mode only and does not add overhead to production builds.
- Flaky test detection runs as a scheduled (nightly or weekly) CI job, not on every PR, to avoid excessive CI cost.
- Fuzz tests use reproducible seeds so that any discovered crash can be reliably reproduced.
