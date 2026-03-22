# Feature Specification: Phase 2 — Code Quality & DRY Consolidation

**Feature Branch**: `001-code-quality-dry`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "Phase 2 — Code Quality & DRY Consolidation: REST Fallback, cached_fetch() Expansion, handle_service_error() Adoption, _with_fallback() Abstraction"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Unified Error-Handling Across Services (Priority: P1)

As a backend developer maintaining the API layer, I want all catch-and-raise error-handling blocks consolidated into a single shared utility so that error logging, message sanitisation, and exception classification follow one consistent pattern and future endpoints adopt it by default.

**Why this priority**: Inconsistent error handling is the highest-risk maintenance burden. Fourteen separate catch→raise blocks each have slightly different log levels, message formats, and exception classes. A single missed update during an incident could leak internal details or produce confusing client responses. Consolidating first establishes the safety baseline for all other refactoring in this phase.

**Independent Test**: Can be fully tested by triggering each migrated error path in unit tests and verifying that the logged message, raised exception class, and client-visible payload match the expected contract. Delivers immediate value by proving no error-path regressions exist.

**Acceptance Scenarios**:

1. **Given** a service call that raises an unexpected exception in any of the 14 migrated locations, **When** the error is caught, **Then** the system logs the full exception context server-side and raises a structured application exception with a safe, generic client message — identical to the behaviour before migration.
2. **Given** an error handler that currently returns an error dictionary rather than raising (health check, WebSocket, error-returning webhook handlers), **When** the consolidation is applied, **Then** those handlers remain untouched and continue returning dicts as before.
3. **Given** the 7 error sites in the tools module that currently raise HTTP-level exceptions, **When** the middleware behaviour is reviewed, **Then** a documented decision is made about whether those sites convert to application exception subclasses or remain as-is, and the migration aligns with that decision.

---

### User Story 2 — Standardised Caching with Graceful Degradation (Priority: P2)

As a backend developer, I want all cache-aside patterns across the project-list, board, and chat endpoints to use a single shared caching utility — with optional rate-limit-aware fallback and data-hashing support — so that cache logic is defined in one place and every endpoint automatically benefits from stale-data degradation and consistent TTL management.

**Why this priority**: Four endpoints currently implement nearly identical cache-check → fetch → store → stale-fallback logic inline (approximately 260 lines combined). Extending caching behaviour (e.g., adding metrics, changing TTL strategy) requires touching every copy. Unifying under one utility is the highest-leverage DRY improvement after error handling.

**Independent Test**: Can be fully tested by calling each migrated endpoint with the cache warm, cold, and stale (simulated fetch failure) and verifying identical response payloads and status codes compared to the current implementation.

**Acceptance Scenarios**:

1. **Given** the shared caching utility already supports basic cache-aside and stale fallback, **When** optional rate-limit-aware fallback and data-hash comparison parameters are added, **Then** all existing callers of the caching utility continue to work without modification (full backward compatibility).
2. **Given** the project-list endpoint currently has approximately 50 lines of inline cache logic, **When** it is migrated to the shared utility, **Then** the endpoint produces the same response for cache-hit, cache-miss, rate-limit, and generic-error scenarios.
3. **Given** the board-projects endpoint manages two separate cache keys, **When** it is migrated, **Then** the dual-key behaviour is preserved through a composed fetch function rather than adding a multi-key parameter to the shared utility.
4. **Given** the board-data endpoint (approximately 90 lines of cache logic), **When** it is migrated, **Then** stale-data fallback, pagination, and sub-issue enrichment continue to work identically.
5. **Given** the send-message endpoint reads from pre-populated caches for project and task context, **When** its cache-read pattern is migrated, **Then** the AI context assembly is unaffected and defaults are preserved on cache misses.
6. **Given** the send-tasks function uses stale-revalidation counters and hash-diffing, **When** evaluated for migration, **Then** it is either migrated (if the extended signature accommodates its patterns cleanly) or left in place with a justification comment documenting why.

---

### User Story 3 — Resilient Fallback Abstraction for Service Operations (Priority: P3)

As a backend developer, I want a reusable fallback abstraction on the base service that encapsulates the primary-attempt → optional-verify → fallback-attempt pattern so that multi-strategy operations (such as adding issues to a project) are expressed declaratively and new fallback chains can be composed without hand-rolling the same control flow.

**Why this priority**: The add-issue-to-project operation currently contains a complex multi-strategy fallback (GraphQL → verify → REST) that is difficult to follow and extend. Extracting this into a shared abstraction makes it easier to apply the same resilience pattern to other service operations and reduces the risk of introducing subtle bugs when adding new fallback strategies.

**Independent Test**: Can be fully tested by invoking the abstraction with mock primary/fallback/verify functions covering three scenarios: primary succeeds, primary fails but fallback succeeds, and both fail. Delivers value by proving the soft-failure contract (returns None on total failure, never raises).

**Acceptance Scenarios**:

1. **Given** a service operation using the fallback abstraction, **When** the primary function succeeds, **Then** the result is returned without invoking the fallback.
2. **Given** a service operation using the fallback abstraction, **When** the primary function fails and a verify function is provided, **Then** the verify function is called before attempting the fallback.
3. **Given** a service operation using the fallback abstraction, **When** both primary and fallback functions fail, **Then** the abstraction returns None without raising any exception (soft-failure contract).
4. **Given** the add-issue-to-project operation is refactored to use the abstraction, **When** the GraphQL strategy fails and the REST fallback succeeds, **Then** the behaviour is identical to the current multi-strategy implementation.
5. **Given** candidate operations in the copilot-reviewer-assignment and existing-PR-lookup services, **When** they are evaluated for adoption, **Then** each is either migrated (if the abstraction demonstrably simplifies the implementation) or left as-is with a documented rationale.

---

### User Story 4 — Repository Resolution Hardening and Deduplication (Priority: P3)

As a backend developer, I want a REST-based repository lookup step added to the shared repository-resolution utility and all duplicated owner/repo extraction logic replaced with calls to that utility so that repository resolution is more resilient and defined in exactly one place.

**Why this priority**: The repository-resolution utility currently falls back from a project-items lookup directly to a workflow-config lookup, missing the opportunity to recover via a simpler REST-based call. Separately, the application startup code duplicates approximately 15 lines of the same fallback logic inline. While lower risk than error handling or caching, this deduplication prevents the two copies from diverging.

**Independent Test**: Can be fully tested by simulating a project-items failure and verifying that the new REST step resolves the repository before the workflow-config step is reached. The startup deduplication can be tested by confirming the startup still resolves repositories correctly after replacement.

**Acceptance Scenarios**:

1. **Given** the project-items lookup fails (e.g., due to permissions or API error), **When** the REST-based repository lookup succeeds, **Then** the repository is resolved without falling through to the workflow-config step.
2. **Given** the REST-based repository lookup also fails, **When** the workflow-config step has valid data, **Then** the repository is resolved from workflow config as before.
3. **Given** the application startup currently has inline owner/repo extraction logic, **When** that logic is replaced with a call to the shared utility, **Then** the startup behaviour (including its fallback to webhook-token strategy on failure) is preserved.

---

### Edge Cases

- What happens when the caching utility's fetch function raises during a rate-limit-aware fallback and no stale data exists? The utility must propagate the original exception rather than masking it.
- What happens when the fallback abstraction's verify function itself raises? The abstraction must treat a verify failure the same as a verify returning False — proceed to the fallback without raising.
- What happens when the composed fetch function for dual-cache-key endpoints updates one cache key successfully but fails on the second? The successfully cached data must not be rolled back; the failed key should follow the standard stale-fallback path.
- What happens when all 14 migrated error-handling sites are exercised concurrently under load? The shared error utility must be stateless and thread/async-safe with no shared mutable state.
- What happens when the REST repository lookup returns a repository the caller does not have access to? The resolution utility must treat this the same as a lookup failure and proceed to the next fallback step.
- What happens when existing callers of the caching utility pass no new optional parameters? Full backward compatibility must be maintained — behaviour must be identical to pre-extension.

## Requirements *(mandatory)*

### Functional Requirements

#### Error Handling Consolidation

- **FR-001**: System MUST migrate 14 identified manual catch→raise error-handling patterns to the shared error-handling utility: 3 in the board module, 7 in the tools module, 1 in the pipelines module, 1 in the tasks module, and 2 in the webhooks module.
- **FR-002**: System MUST preserve the exact client-visible behaviour of each migrated error site — same exception class, same status code, same client message format, same logged context.
- **FR-003**: System MUST NOT migrate error handlers that return error dictionaries rather than raising exceptions (health check endpoints, WebSocket handlers, error-returning webhook handlers).
- **FR-004**: System MUST verify, by inspecting the exception-handler middleware configuration, whether the 7 tools-module error sites that currently raise HTTP-level exceptions should be converted to application exception subclasses. The migration must align with the middleware's existing behaviour.

#### Cache Pattern Unification

- **FR-005**: System MUST extend the shared caching utility with an optional rate-limit-aware fallback parameter in a fully backward-compatible manner (existing callers must not require changes).
- **FR-006**: System MUST extend the shared caching utility with an optional data-hash comparison parameter in a fully backward-compatible manner.
- **FR-007**: System MUST migrate the project-list endpoint (approximately 50 lines of inline cache logic) to the shared caching utility.
- **FR-008**: System MUST migrate the board-projects endpoint (approximately 87 lines of inline cache logic) to the shared caching utility, handling its two separate cache keys through a composed fetch function rather than adding a multi-key parameter.
- **FR-009**: System MUST migrate the board-data endpoint (approximately 90 lines of inline cache logic) to the shared caching utility.
- **FR-010**: System MUST migrate the send-message cache-read pattern (approximately 30 lines) to the shared caching utility.
- **FR-011**: System SHOULD evaluate the send-tasks function for migration to the shared caching utility. If the stale-revalidation counters and hash-diffing patterns do not fit cleanly within the extended signature, the function must remain in place with a justification comment.

#### Fallback Pattern Abstraction

- **FR-012**: System MUST create a reusable fallback abstraction on the base service with the following contract: accepts a primary function, a fallback function, an operation description, and an optional verify function.
- **FR-013**: The fallback abstraction MUST preserve the soft-failure contract: return None on total failure and never propagate exceptions to the caller.
- **FR-014**: The fallback abstraction MUST support an optional verify function that is called between primary and fallback attempts, generalising the verify-between-strategies pattern.
- **FR-015**: System MUST refactor the add-issue-to-project operation to use the fallback abstraction, maintaining identical behaviour to the current multi-strategy implementation.
- **FR-016**: System SHOULD evaluate applying the fallback abstraction to the copilot-reviewer-assignment and existing-PR-lookup operations, applying it only where it demonstrably simplifies the implementation.

#### Repository Resolution

- **FR-017**: System MUST add a REST-based repository lookup fallback step to the shared repository-resolution utility, inserted between the project-items step and the workflow-config step.
- **FR-018**: The new REST fallback step MUST follow the same pattern used in the existing REST-based issue-lookup implementation.
- **FR-019**: System MUST replace the inline owner/repo extraction logic in the application startup (approximately 15 lines) with a direct call to the shared repository-resolution utility, preserving the existing webhook-token fallback behaviour on failure.

#### Verification

- **FR-020**: All existing unit tests MUST continue to pass with no behaviour changes after the refactoring.
- **FR-021**: System MUST include unit tests for the extended caching utility covering rate-limit-aware fallback and data-hash comparison parameters.
- **FR-022**: System MUST include unit tests for the fallback abstraction covering primary-success, primary-fail-with-fallback-success, and both-fail scenarios.
- **FR-023**: System MUST include a unit test that simulates a project-items failure to verify the REST fallback path in repository resolution.
- **FR-024**: Integration smoke tests MUST confirm no user-facing regressions across board, project, and chat endpoints.
- **FR-025**: A grep-based audit MUST verify that error/exception log entries outside the shared error-handling utility correspond only to non-raise patterns (health checks, WebSocket handlers, error-returning handlers).

### Key Entities

- **Shared Error-Handling Utility**: A centralised function that logs the full exception context server-side and raises a structured application exception with a safe client message. Used by all service-layer catch→raise patterns.
- **Shared Caching Utility**: A cache-aside function that checks cache, calls a fetch function on miss, stores the result, and optionally falls back to stale data on errors. Extended with rate-limit-aware fallback and data-hash comparison hooks.
- **Fallback Abstraction**: A base-service method that encapsulates primary-attempt → optional-verify → fallback-attempt control flow, preserving a soft-failure contract (returns None, never raises).
- **Repository Resolution Utility**: A multi-step fallback function that resolves repository owner and name from a project ID, with caching and token-scoped isolation. Extended with a REST-based lookup step.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total lines of duplicated cache-aside logic across the four migrated endpoints is reduced by at least 60% (from approximately 260 lines to fewer than 100 lines of call-site code).
- **SC-002**: All 14 migrated error-handling sites produce identical client-visible responses (same status codes, same message formats) as measured by before/after comparison of unit test assertions.
- **SC-003**: 100% of existing unit tests pass without modification after the refactoring (zero behavioural regressions).
- **SC-004**: The fallback abstraction is covered by unit tests for all three scenarios (primary success, primary-fail + fallback-success, both-fail) with 100% branch coverage of the abstraction itself.
- **SC-005**: A grep-based audit of error/exception log statements outside the shared error-handling utility returns only entries from excluded locations (health checks, WebSocket handlers, error-returning handlers) — zero unexpected manual catch→raise patterns remain.
- **SC-006**: Integration smoke tests across board, project-list, and chat endpoints confirm no user-facing regressions in response payloads, status codes, or soft-failure behaviours.
- **SC-007**: Repository resolution succeeds when the project-items lookup fails but the REST fallback returns a valid result, verified by a unit test that mocks the project-items failure.
- **SC-008**: New developers can add a cached endpoint or a fallback-resilient operation by calling a single shared utility with fewer than 5 lines of call-site code, as demonstrated by the migrated endpoints.

## Assumptions

- The validation helper consolidation (Item 2.3) is fully completed and requires no action in this phase.
- The existing exception-handler middleware in the application handles all `AppException` subclasses uniformly (structured JSON response with status code, message, and details) and has a generic fallback for unhandled exceptions.
- The `RateLimitError`, `AuthenticationError`, and `GitHubAPIError` exception classes already exist and are subclasses of `AppException`.
- The base service class uses a mixin architecture, and the fallback abstraction will be added as a method on the base class (or a mixin) accessible to all service mixins.
- The REST-based repository lookup pattern already exists in the issues module and can be adapted for the repository-resolution utility without requiring new external API contracts.
- The dual-cache-key pattern in the board-projects endpoint can be handled by composing a single fetch function that internally manages both keys, without requiring the caching utility to be aware of multiple keys.
- WebSocket handlers, health check endpoints, and error-returning webhook handlers are explicitly excluded from all migrations in this phase.

## Scope Boundaries

**In scope:**
- Migration of 14 catch→raise patterns to the shared error-handling utility
- Extension of the shared caching utility with rate-limit-aware fallback and data-hash comparison
- Migration of 4 endpoints to the shared caching utility
- Evaluation (not guaranteed migration) of send-tasks to the shared caching utility
- Creation of the fallback abstraction on the base service
- Refactoring of add-issue-to-project to use the fallback abstraction
- Evaluation of fallback abstraction for copilot-reviewer and existing-PR-lookup
- REST fallback in repository resolution
- Deduplication of startup owner/repo extraction
- Unit and integration tests for all new and modified utilities

**Out of scope:**
- Health check endpoint error handling
- WebSocket handler error handling
- Error-returning webhook handler patterns
- UI/UX changes (this is a pure backend refactoring)
- New feature development or API contract changes
- Performance optimisation beyond what DRY consolidation achieves
- Changes to the validation helper (Item 2.3, already completed)

## Phase Parallelism

- **Phase A** (repository resolution hardening — FR-017, FR-018, FR-019) can proceed independently.
- **Phase B** (cache pattern unification — FR-005 through FR-011) requires the caching utility extension (FR-005, FR-006) to be completed before endpoint migrations (FR-007 through FR-011).
- **Phase C** (fallback abstraction — FR-012 through FR-016) can proceed independently.
- **Phase D** (error handling consolidation — FR-001 through FR-004) requires the tools-module exception-type verification (FR-004) to be completed before migrating those 7 sites.
- Phases A, B, and C can run in parallel. Phase D steps are sequential (verify → decide → migrate).
