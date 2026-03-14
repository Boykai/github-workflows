# Feature Specification: Codebase Improvement Plan — Modern Best Practices Overhaul

**Feature Branch**: `035-best-practices-overhaul`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "Full-stack audit across 465 files / 4,567 functions. Seven-phase overhaul covering data integrity, cyclomatic complexity reduction, DRY & error handling consolidation, dependency injection modernization, security hardening, observability & testing, and developer experience improvements."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Pipeline State Survives Container Restart (Priority: P1)

An operations engineer restarts the application container during a routine deployment. Before this overhaul, all in-flight pipeline state — which issues are being processed, which agents are assigned, which branches belong to which issues — is silently lost because the state lives only in an in-memory dictionary with a 500-entry cap. After the overhaul, the pipeline state is persisted so that on restart, all in-progress work resumes exactly where it left off. No issues are orphaned and no agent assignments are duplicated.

**Why this priority**: Data loss on restart is a silent, unrecoverable failure that affects every user of the system. All other improvements are meaningless if the core orchestration state can be lost at any time. This is the critical foundation that blocks all other phases.

**Independent Test**: Stop the running application container. Verify that at least 5 in-flight pipeline states exist. Restart the container. Confirm all 5 pipeline states are recovered and processing resumes without manual intervention.

**Acceptance Scenarios**:

1. **Given** the application has 10 active pipeline states, **When** the container is stopped and restarted, **Then** all 10 pipeline states are recovered and processing continues.
2. **Given** the in-memory state dictionary reaches its capacity limit, **When** a new pipeline state is added, **Then** the oldest state is evicted from memory but remains available via the persistent store.
3. **Given** two concurrent requests attempt to update the same pipeline state, **When** both writes complete, **Then** no data is corrupted and the final state reflects a valid sequential ordering of the updates.
4. **Given** a chat conversation is in progress with 20 messages and 3 proposals, **When** the container restarts, **Then** all messages and proposals are recovered and the conversation continues seamlessly.

---

### User Story 2 — Developer Fixes a Bug in a High-Complexity Function (Priority: P1)

A developer receives a bug report about incorrect agent output processing. The relevant function today is over 1,000 lines with a cyclomatic complexity score of 123. The developer must read the entire function, mentally track dozens of conditional branches, and hope their fix doesn't break an unrelated code path. After the overhaul, the function is decomposed into focused handlers — scanning, analysis, extraction, and advancement — each under 200 lines. The developer identifies the exact handler responsible, fixes the bug, writes a targeted test, and is confident no other logic is affected.

**Why this priority**: The five highest-complexity functions are the primary source of defects and the biggest barrier to developer productivity. Reducing their complexity is a force multiplier for every future change.

**Independent Test**: Measure cyclomatic complexity of the 5 target functions before and after refactoring. Confirm all score at or below their target thresholds. Run the full existing test suite and confirm zero regressions.

**Acceptance Scenarios**:

1. **Given** `post_agent_outputs_from_pr` has a cyclomatic complexity of 123, **When** it is decomposed into handler functions, **Then** no individual function exceeds a complexity score of 15.
2. **Given** `assign_agent_for_status` has a cyclomatic complexity of 91, **When** it is refactored into strategy patterns, **Then** no individual function exceeds a complexity score of 20.
3. **Given** `recover_stalled_issues` has two functions scoring 72 and 66, **When** they are decomposed, **Then** no individual function exceeds a complexity score of 20.
4. **Given** `usePipelineConfig` returns 30 properties in a flat bag, **When** it is restructured using hook composition, **Then** each sub-hook returns at most 8 properties and the parent hook returns focused objects.
5. **Given** `useAgentConfig` has a cyclomatic complexity of 69, **When** it is decomposed into sub-hooks, **Then** no individual hook exceeds a complexity score of 25.

---

### User Story 3 — Developer Adds a New API Endpoint Needing Repository Info (Priority: P1)

A developer building a new API endpoint needs the current repository owner and name. Today, 8 separate code paths resolve this information with different fallback logic — some check only the cache, others do a 3-step fallback, and the developer doesn't know which to use. After the overhaul, a single canonical function is the only way to resolve repository information, consistently documented and called in every endpoint. The developer calls it once and gets correct, consistent behavior.

**Why this priority**: Inconsistent repository resolution across 8 paths produces subtle, hard-to-diagnose bugs where different endpoints behave differently for the same user. Eliminating duplication removes over 100 lines of redundant code and a whole class of inconsistency bugs.

**Independent Test**: Search the codebase for all repository resolution call sites. Confirm every endpoint uses the single canonical function. Delete the duplicate functions and confirm the full test suite passes.

**Acceptance Scenarios**:

1. **Given** 8 separate repository resolution code paths exist, **When** consolidation is complete, **Then** all callers use the single canonical resolution function.
2. **Given** bare `except Exception` blocks exist in 15+ locations, **When** error handling is consolidated, **Then** all exception handlers use the existing error infrastructure with specific exception types and structured logging.
3. **Given** API endpoints accept raw `dict` parameters, **When** type-safe inputs are implemented, **Then** every API endpoint validates its input through a defined data model before processing.

---

### User Story 4 — Developer Writes Tests Without Service Coupling (Priority: P2)

A developer needs to write a unit test for a service that depends on the GitHub API client. Today, module-level singletons instantiate real services at import time, making test isolation impossible without monkeypatching global state. After the overhaul, all services are injected through the application's dependency framework. The developer creates a test with a mock dependency, runs it in isolation, and gets a fast, deterministic result.

**Why this priority**: Test isolation is the foundation of reliable testing. Without it, tests are flaky, slow, and coupled to external services. This change enables meaningful test coverage increases in Phase 6.

**Independent Test**: Write a unit test for any service that currently uses a module-level singleton. Confirm the test can inject a mock dependency without modifying global state. Confirm the test runs in under 1 second.

**Acceptance Scenarios**:

1. **Given** services are instantiated as module-level singletons, **When** dependency injection is modernized, **Then** every service is created through the application lifecycle and injected via the dependency framework.
2. **Given** circular imports force lazy import hacks, **When** shared protocols are extracted into an interfaces module, **Then** all lazy import workarounds are removed and all imports are direct.
3. **Given** a race condition exists in lazy service initialization, **When** services are created during application startup, **Then** no race conditions exist in service creation.

---

### User Story 5 — Security Auditor Reviews the Application (Priority: P2)

A security auditor assesses the application's HTTP security posture. Today, CORS allows all headers, no Content Security Policy headers are sent, the first user is automatically promoted to admin, and session access control lacks user-scoped restrictions. After the overhaul, CORS specifies only the headers the application actually uses, CSP headers restrict content sources, admin designation requires an explicit configuration, and sessions are bound to specific users.

**Why this priority**: Security gaps are production risks that cannot be deferred. While they don't block other development work, they represent vulnerabilities that grow more dangerous as the user base expands.

**Independent Test**: Use a security scanning tool to verify CORS headers, CSP headers, and session controls. Attempt to access another user's session and confirm it is denied. Create a new account and confirm it does not receive admin privileges without explicit designation.

**Acceptance Scenarios**:

1. **Given** CORS allows all headers, **When** security hardening is complete, **Then** only explicitly required headers are allowed.
2. **Given** no CSP headers are sent, **When** CSP middleware is added, **Then** every response includes a Content Security Policy header restricting content sources.
3. **Given** the first user is auto-promoted to admin, **When** admin designation is changed, **Then** admin status requires explicit configuration and is not granted by default.
4. **Given** sessions lack user-scoped access control, **When** session hardening is complete, **Then** each session is bound to a specific user and cannot be used to access another user's data.

---

### User Story 6 — Developer Investigates a Production Error (Priority: P2)

A developer is paged for a production issue. They check the application logs but find no trace of the error — the relevant code path catches all exceptions silently. After the overhaul, every exception handler logs the error with full context, including the traceback and relevant request data. The developer finds the error immediately in the logs, identifies the root cause, and deploys a fix.

**Why this priority**: Silent error swallowing makes production debugging impossible. Combined with empty integration test directories, the current state means bugs are neither caught in testing nor visible in production.

**Independent Test**: Trigger a known error condition in an endpoint that currently swallows exceptions. Confirm the error appears in the application logs with a full traceback. Run the new integration tests and confirm they catch the previously-silent failure.

**Acceptance Scenarios**:

1. **Given** some exception handlers swallow errors without logging, **When** observability improvements are complete, **Then** every exception handler logs the error with full traceback and context.
2. **Given** the integration test directory is empty, **When** pipeline lifecycle tests are added, **Then** the integration test suite covers the core pipeline workflow from creation through completion.
3. **Given** some test assertions accept overly broad status codes, **When** assertions are tightened, **Then** every test assertion checks for a specific expected status code.
4. **Given** build artifacts are tracked in version control, **When** cleanup is complete, **Then** generated directories are excluded from version control tracking.

---

### User Story 7 — Developer Uses a Frontend Hook with a Clean API (Priority: P3)

A frontend developer needs to use pipeline configuration in a new component. Today, the relevant hook returns 30 properties in a flat object, and the developer must read the hook's source code to understand which properties they need. After the overhaul, the hook returns focused objects grouped by concern — CRUD operations, validation state, and configuration state. The developer destructures only the group they need and the code is self-documenting.

**Why this priority**: Developer experience improvements make the codebase more approachable for new contributors and reduce time-to-productivity on every future frontend task. This is important but not urgent.

**Independent Test**: Import the restructured hook in a new component. Confirm it provides grouped objects instead of flat properties. Confirm all existing components that use the hook continue to function correctly.

**Acceptance Scenarios**:

1. **Given** `usePipelineConfig` returns 30 flat properties, **When** the API surface is reduced, **Then** it returns focused objects grouped by concern with each group containing at most 8 properties.
2. **Given** custom retry logic runs alongside the existing retry library, **When** retry standardization is complete, **Then** all retry logic uses the project's existing retry library.

---

### Edge Cases

- What happens when the persistent store is unavailable at startup? The application should start with the in-memory cache alone and attempt to reconnect to the persistent store, logging a warning.
- What happens when the persistent store and the in-memory cache disagree on a pipeline state? The persistent store is treated as the source of truth; the in-memory cache is refreshed from it.
- What happens when a security header restricts a legitimate cross-origin request? The allowed origins list must include all configured frontend domains, and the configuration must be updatable without code changes.
- What happens when a refactored function's extracted helper is called with unexpected input? Each extracted function must validate its inputs and raise a specific, documented exception rather than allowing undefined behavior.
- What happens when a module-level singleton import is removed but a third-party dependency still expects it? Backward-compatible aliases or adapter functions must be provided during a transition period, documented for removal.

## Requirements *(mandatory)*

### Functional Requirements

**Phase 1 — Data Integrity & Reliability**

- **FR-001**: System MUST persist all pipeline orchestration state to durable storage so that state survives application restarts.
- **FR-002**: System MUST persist all chat messages and proposals to durable storage so that conversations survive application restarts.
- **FR-003**: System MUST use an in-memory cache as a fast-access layer in front of the persistent store, with write-through semantics ensuring every write reaches durable storage before being acknowledged.
- **FR-004**: System MUST protect all shared mutable state with concurrency-safe locking so that concurrent operations cannot corrupt data.
- **FR-005**: System MUST integrate the existing but unused chat persistence migration so that the migration runs during application startup.

**Phase 2 — Cyclomatic Complexity Reduction**

- **FR-006**: System MUST decompose `post_agent_outputs_from_pr` into focused handler functions so that no individual function exceeds a cyclomatic complexity of 15.
- **FR-007**: System MUST refactor `assign_agent_for_status` using strategy patterns so that no individual function exceeds a cyclomatic complexity of 20.
- **FR-008**: System MUST decompose `recover_stalled_issues` into focused recovery functions so that no individual function exceeds a cyclomatic complexity of 20.
- **FR-009**: System MUST restructure `usePipelineConfig` using hook composition so that no individual hook exceeds a cyclomatic complexity of 25, and each sub-hook returns at most 8 properties.
- **FR-010**: System MUST restructure `useAgentConfig` using hook composition so that no individual hook exceeds a cyclomatic complexity of 25.

**Phase 3 — DRY & Error Handling Consolidation**

- **FR-011**: System MUST consolidate all repository resolution paths into a single canonical function, eliminating all duplicate resolution logic.
- **FR-012**: System MUST route all exception handling through the existing error infrastructure functions (`handle_service_error`, `safe_error_response`) rather than bare exception catches.
- **FR-013**: System MUST replace all bare `except Exception` blocks with specific exception types and structured error logging that includes the full traceback.
- **FR-014**: System MUST validate all API endpoint inputs through defined data models, replacing all raw dictionary parameters with structured validation.
- **FR-015**: System MUST use discriminated unions for webhook payload validation to ensure type-safe handling of different webhook event types.

**Phase 4 — Dependency Injection Modernization**

- **FR-016**: System MUST create all service instances during application startup lifecycle, not as module-level singletons.
- **FR-017**: System MUST provide all service dependencies through the application's dependency injection framework, not through direct imports of singleton instances.
- **FR-018**: System MUST extract shared protocols into a dedicated interfaces module to break all circular import workarounds.
- **FR-019**: System MUST remove all lazy import hacks and conditional factory loading patterns once circular dependencies are resolved.

**Phase 5 — Security Hardening**

- **FR-020**: System MUST specify an explicit list of allowed CORS headers rather than accepting all headers.
- **FR-021**: System MUST include Content Security Policy headers in every HTTP response.
- **FR-022**: System MUST require explicit administrative designation via configuration rather than auto-promoting the first user to admin.
- **FR-023**: System MUST enforce user-scoped session access so that a session token can only access data belonging to the session's authenticated user.

**Phase 6 — Observability & Testing**

- **FR-024**: System MUST log every caught exception with full traceback and request context — no exception handler may silently discard errors.
- **FR-025**: System MUST capture unhandled frontend errors and promise rejections so they are reportable.
- **FR-026**: System MUST include integration tests covering the full pipeline lifecycle from creation through completion.
- **FR-027**: System MUST use specific expected status codes in all test assertions rather than accepting ranges of codes.
- **FR-028**: System MUST exclude all generated build artifacts from version control tracking.

**Phase 7 — Developer Experience**

- **FR-029**: System MUST restructure hook APIs to return focused, grouped objects instead of flat property bags, with each group containing at most 8 properties.
- **FR-030**: System MUST standardize all retry logic on the project's existing retry library, removing all parallel custom retry implementations.

### Key Entities

- **Pipeline State**: Represents the processing state of a single issue through the automation pipeline. Attributes include the issue identifier, current processing stage, assigned agent, associated branch, and timestamps. Relationships: belongs to a project, references an issue, may have sub-issues.
- **Chat Conversation**: Represents a user's interaction with the AI assistant for a specific context. Attributes include messages (role, content, timestamp) and proposals (content, status, metadata). Relationships: belongs to a user, associated with a project context.
- **Service Instance**: Represents a managed service within the application's dependency injection framework. Attributes include service type, initialization state, and dependencies. Relationships: may depend on other service instances, managed by the application lifecycle.
- **Session**: Represents an authenticated user's session. Attributes include the user identifier, authentication token, creation timestamp, and expiration. Relationships: bound to exactly one user, grants access only to that user's data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All in-flight pipeline states survive an application restart — zero data loss on container stop/start cycle.
- **SC-002**: No backend function exceeds a cyclomatic complexity score of 25 (down from a current maximum of 123).
- **SC-003**: No frontend hook exceeds a cyclomatic complexity score of 25 (down from a current maximum of 79).
- **SC-004**: All duplicate repository resolution paths are eliminated — exactly one canonical function exists and is used by all callers.
- **SC-005**: Zero bare `except Exception` blocks remain in application code (excluding intentional resilience patterns in logging infrastructure).
- **SC-006**: All API endpoints validate inputs through structured data models — zero raw dictionary parameters accepted.
- **SC-007**: Zero module-level singleton service instances exist — all services are created during application startup and injected via the dependency framework.
- **SC-008**: CORS configuration specifies an explicit allow-list of headers — the wildcard header permission is removed.
- **SC-009**: Every HTTP response includes a Content Security Policy header.
- **SC-010**: Admin privileges require explicit configuration — a new user account is never auto-promoted to admin.
- **SC-011**: Every exception handler logs the full traceback — zero silent exception swallowing in application code.
- **SC-012**: Integration test suite covers the pipeline lifecycle — at least one end-to-end pipeline test exists and passes.
- **SC-013**: All generated build artifacts are excluded from version control — no committed files in coverage, test-results, or report directories.
- **SC-014**: All existing tests continue to pass after every phase — zero regressions introduced.
- **SC-015**: Static analysis tools (type checker, linter) report zero new errors after every phase.

## Assumptions

- The existing persistent storage mechanism is appropriate for the current scale and does not need to be replaced with a different storage system.
- The existing retry library (`tenacity`) provides sufficient functionality for all current retry use cases.
- The existing error handling infrastructure (`handle_service_error`, `safe_error_response`) is correctly implemented and only needs to be adopted, not rewritten.
- The existing chat persistence migration (`012_chat_persistence.sql`) is correct and only needs to be integrated into the startup sequence.
- The application's dependency framework supports lifecycle-managed service creation without requiring a third-party container library.
- Frontend hook composition can be achieved using the existing state management approach (TanStack Query + local state) without introducing new libraries.
- Build artifact directories (`htmlcov/`, `coverage/`, `e2e-report/`, `test-results/`) can be safely removed from version control without breaking any CI/CD pipelines that depend on committed artifacts.
- Phase 1 (Data Integrity) must be completed before any other phase begins, as it establishes the reliability foundation.
- Phases 2 through 5 can proceed in parallel after Phase 1 is complete.
- Phases 6 and 7 are independent and can proceed at any time.

## Dependencies

- Phase 1 completion blocks Phases 2, 3, 4, and 5.
- Phase 4 (Dependency Injection) enables more effective testing in Phase 6.
- Phase 3 (Error Handling Consolidation) supports Phase 6 (Observability) by ensuring consistent error infrastructure.
- The existing persistent storage infrastructure must be operational before Phase 1 work begins.
- The existing chat persistence migration file must be present and syntactically valid.

## Scope Boundaries

**Included**:
- Data integrity improvements (persistent state, chat persistence, async-safe locking)
- Cyclomatic complexity reduction for the 5 highest-complexity functions
- DRY consolidation (repository resolution, error handling, type-safe inputs)
- Dependency injection modernization (eliminate singletons, resolve circular imports)
- Security hardening (CORS, CSP, admin designation, session scoping)
- Observability improvements (error logging, frontend telemetry, integration tests, assertion tightening)
- Developer experience (hook API surface reduction, retry standardization)
- Build artifact cleanup from version control

**Excluded**:
- New feature development or UI/UX changes
- Migration to a different storage system
- Introduction of new state management libraries
- Changes to the current dependency versions (all are current)
- Performance optimization beyond what complexity reduction provides
- Infrastructure changes (deployment, CI/CD pipeline modifications)
