# Feature Specification: Codebase Modernization & Technical Debt Reduction

**Feature Branch**: `038-code-quality-overhaul`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Analyze codebase for improvement opportunities leveraging modern best practices, modular design, and reduce technical debt"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent Error Handling Across All Endpoints (Priority: P1)

As a developer maintaining the backend, I want all API endpoints to use a single, consistent error handling pattern so that error responses are predictable, logs are structured, and I spend less time debugging production issues.

**Why this priority**: Inconsistent error handling is the highest-risk debt — it causes silent failures, inconsistent API responses, and makes debugging unreliable. Consolidating error helpers (already built but unused) has the widest blast radius across all endpoints with zero behavior change for end users.

**Independent Test**: Can be fully tested by running the existing backend test suite (`pytest tests/ -x`) and verifying all endpoints return consistent error shapes. Delivers immediate reliability improvement.

**Acceptance Scenarios**:

1. **Given** an API endpoint encounters a service-level error, **When** the error propagates to the response, **Then** the response uses a standardized error structure with a correlation ID and appropriate HTTP status code.
2. **Given** any endpoint raises an unexpected exception, **When** the error is caught, **Then** the error is logged with full context (request ID, endpoint, parameters) and the user receives a safe, non-leaking error message.
3. **Given** a developer adds a new API endpoint, **When** they follow the established pattern, **Then** they use the shared error helper rather than writing custom try/catch/log blocks.

---

### User Story 2 - Eliminate Duplicated Backend Code Paths (Priority: P1)

As a developer, I want duplicated logic (repository resolution, project selection guards, cache patterns) consolidated into reusable helpers so that bug fixes and behavior changes only need to happen in one place.

**Why this priority**: Duplicated code is a multiplier for bugs — a fix in one place but not the other 7 creates subtle regressions. This story removes ~300+ lines of redundancy with no user-facing behavior change.

**Independent Test**: Can be fully tested by running `pytest tests/ -x` — every test must pass identically before and after consolidation. Delivers immediate maintainability improvement.

**Acceptance Scenarios**:

1. **Given** any feature needs to resolve which repository to operate on, **When** the resolution logic executes, **Then** it uses a single canonical function rather than inline ad-hoc resolution.
2. **Given** an endpoint requires a selected project, **When** no project is selected, **Then** the guard is applied via a shared dependency rather than repeated inline checks in each endpoint.
3. **Given** a service needs to fetch cacheable data, **When** requesting data that is already cached and valid, **Then** it uses a shared caching wrapper rather than manual cache-check/get/set inline.

---

### User Story 3 - Chat Module Decomposition and Persistence (Priority: P2)

As a developer, I want the oversized chat module split into focused sub-modules and wired to persistent storage so that I can work on chat commands, proposals, uploads, and core messaging independently without merge conflicts, and chat history survives backend restarts.

**Why this priority**: The chat module (713 lines, 5+ responsibilities) is the most-changed file and a bottleneck for parallel work. Persistence is built but not wired in, meaning chat history is lost on every container restart — a user-facing pain point.

**Independent Test**: Can be tested by sending messages, triggering agent commands, confirming proposals, uploading files, then restarting the backend container and verifying chat history is preserved. Each sub-module can be developed and tested in isolation.

**Acceptance Scenarios**:

1. **Given** a user sends a chat message, **When** the backend restarts, **Then** the message history is preserved and available on the next session.
2. **Given** a user triggers an agent command in chat, **When** the command handler executes, **Then** it is served by a dedicated command-handling module rather than a monolithic file.
3. **Given** a user uploads a file attachment, **When** the upload completes, **Then** the upload flow is handled by a dedicated upload module with clear boundaries.
4. **Given** the in-memory proposal/recommendation state exists, **When** migrating to persistence, **Then** a write-through strategy is used (write to both stores, read from persistent) to minimize regression risk.

---

### User Story 4 - Automated Type Contract Between Backend and Frontend (Priority: P2)

As a frontend developer, I want TypeScript types auto-generated from the backend's schema so that type drift between frontend and backend is impossible and I spend zero time manually synchronizing type definitions.

**Why this priority**: Manual type maintenance is error-prone and has already caused known drift. Auto-generation eliminates an entire class of bugs (mismatched field names, missing properties, wrong enum values) and also establishes a shared constants contract for status names and labels.

**Independent Test**: Can be tested by modifying a backend model field and verifying the generated frontend types update automatically. Delivers immediate type safety improvement.

**Acceptance Scenarios**:

1. **Given** the backend schema changes, **When** the type generation script runs, **Then** updated frontend type definitions are produced with no manual editing.
2. **Given** the frontend imports generated types, **When** a type-check runs, **Then** any mismatches between frontend usage and backend schema are caught as compile errors.
3. **Given** status names and pipeline constants are defined in the backend, **When** the constants generation runs, **Then** a shared constants file is produced for the frontend, eliminating hardcoded status strings.

---

### User Story 5 - Frontend Hook Decomposition and Test Coverage (Priority: P3)

As a frontend developer, I want complex hooks decomposed into focused single-responsibility hooks and I want missing page and component tests added so that I can safely refactor UI code with confidence.

**Why this priority**: The pipeline config hook manages 5 concerns in 193 lines, making it hard to test and change safely. Six pages and several high-interaction components have no tests, meaning regressions go undetected.

**Independent Test**: Can be tested by running `npm run test:coverage` and verifying increased coverage for the pages/ and components/pipeline/ directories. Each new test file is independently valuable.

**Acceptance Scenarios**:

1. **Given** the pipeline configuration hook, **When** decomposed, **Then** each sub-hook (orchestration, CRUD, dirty tracking) is independently testable.
2. **Given** a user navigates to any page in the application, **When** the page renders, **Then** a corresponding test file verifies the page renders correctly and handles key interactions.
3. **Given** a user interacts with pipeline toolbar, model selector, or unsaved changes dialog, **When** tests run, **Then** those components have dedicated test coverage.

---

### User Story 6 - Observability and Production Hardening (Priority: P3)

As an operator running the application in production, I want structured JSON logs, distributed tracing, and proper security headers so that I can effectively debug issues, trace requests end-to-end, and meet security best practices.

**Why this priority**: Observability is foundational for production operations. While not user-facing, it unblocks faster incident response and meets baseline security expectations (CSP headers). Lower priority because the system functions without it.

**Independent Test**: Can be tested by running `docker compose up`, verifying logs are JSON-formatted, checking HTTP response headers include CSP, and confirming trace context propagates through request chains.

**Acceptance Scenarios**:

1. **Given** the backend processes a request, **When** a log entry is written, **Then** it is emitted as structured JSON with a correlation/request ID.
2. **Given** a browser loads the frontend, **When** the response headers are inspected, **Then** a Content Security Policy header is present.
3. **Given** the backend makes an external API call, **When** tracing is enabled, **Then** the trace context propagates from the incoming request through the outgoing call.
4. **Given** a frontend JavaScript error occurs, **When** the error is unhandled, **Then** it is reported to a backend endpoint for server-side logging.

---

### Edge Cases

- What happens when the canonical repository resolution function receives conflicting inputs (e.g., session has one repo, request body specifies another)?
- How does the system handle a backend restart mid-proposal (user confirmed but persistence write hasn't completed)?
- What happens when the OpenAPI schema is unavailable or malformed during type generation?
- How does the frontend behave if the generated constants file is out of date (e.g., developer forgets to regenerate)?
- What happens when structured logging encounters non-serializable objects in log context?
- How does the cache wrapper handle concurrent requests for the same uncached resource (thundering herd)?

## Requirements *(mandatory)*

### Functional Requirements

#### DRY Consolidation

- **FR-001**: All API endpoints that resolve a repository MUST use a single canonical resolution function rather than inline logic.
- **FR-002**: All API endpoints MUST use shared error handling helpers for catch/log/respond patterns.
- **FR-003**: All cacheable data fetches MUST use a shared caching wrapper that encapsulates check/get/set/TTL logic.
- **FR-004**: All endpoints requiring a selected project MUST enforce the check via a shared dependency guard.

#### Modular Decomposition

- **FR-005**: The chat module MUST be split into sub-modules by responsibility: core messaging, command handling, proposal flow, and file uploads.
- **FR-006**: Chat messages, proposals, and recommendations MUST be persisted to durable storage and survive backend restarts.
- **FR-007**: Chat persistence MUST use a write-through strategy during migration: write to persistent storage on every operation, progressively switch reads from in-memory to persistent, then remove in-memory state.
- **FR-008**: The pipeline configuration hook MUST be decomposed into hooks with single responsibilities: orchestration, CRUD operations, and dirty-state tracking.

#### Type Safety & Contracts

- **FR-009**: A type generation script MUST produce frontend type definitions from the backend's API schema.
- **FR-010**: A constants generation mechanism MUST produce a shared constants file containing status names, agent slugs, and pipeline defaults for the frontend.
- **FR-011**: All backend API endpoints MUST declare response models in their route definitions to ensure complete schema exposure.

#### Observability & Hardening

- **FR-012**: Backend logs MUST be emitted as structured JSON with request correlation IDs.
- **FR-013**: Distributed tracing MUST propagate context from incoming requests through outgoing external API calls.
- **FR-014**: The frontend MUST be served with a Content Security Policy header.
- **FR-015**: Unhandled frontend errors MUST be reported to the backend for server-side logging.

#### Test Coverage

- **FR-016**: Every user-facing page MUST have a corresponding test file that verifies rendering and key interactions.
- **FR-017**: High-interaction pipeline components (toolbar, model selector, unsaved changes dialog) MUST have dedicated test files.
- **FR-018**: Chat persistence MUST be verified by an integration test that confirms messages survive a backend restart cycle.

#### Developer Experience

- **FR-019**: Database migrations MUST support a dry-run mode or rollback capability.
- **FR-020**: The pre-commit hook MUST verify generated types are up-to-date when backend models change.
- **FR-021**: The CI pipeline MUST use the same runtime version the project targets.

### Key Entities

- **Chat Message**: A single message in a conversation (sender, content, timestamp, conversation ID). Transitions from in-memory to persistent storage.
- **Chat Proposal**: A pending action proposed by the AI agent (proposal type, payload, status: pending/confirmed/cancelled). Must survive restarts.
- **Chat Recommendation**: A set of suggested tasks/issues generated by the AI agent (items, status, conversation context). Must survive restarts.
- **Pipeline Configuration**: User-defined pipeline settings (name, agent assignments, stages, dirty state). Frontend hook manages lifecycle.
- **Generated Type Contract**: Auto-generated type definitions derived from backend schema (type names, field shapes, enum values). Build artifact, not runtime data.
- **Shared Constants**: Status names, agent slugs, pipeline defaults shared between backend and frontend. Build-time generated artifact.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Total duplicated code lines in backend API modules reduced by at least 250 lines (from ~300+ identified).
- **SC-002**: All existing backend tests pass without modification after DRY consolidation (zero behavior change).
- **SC-003**: Chat message history persists across backend restarts — 100% of messages recoverable after a restart cycle.
- **SC-004**: The chat module file count increases from 1 to 4, with no single file exceeding 200 lines.
- **SC-005**: Frontend type definitions are generated from backend schema with zero manual type declarations for API-consumed types.
- **SC-006**: Zero hardcoded status/label strings remain in frontend source files after constants generation.
- **SC-007**: Backend test suite passes on the same runtime version used in production (version alignment between CI and project target).
- **SC-008**: Page-level test coverage increases from 1 tested page to 7 tested pages.
- **SC-009**: Pipeline component test coverage increases from 0 to 3 dedicated component test files.
- **SC-010**: Backend logs are parseable as valid JSON by standard log aggregation tools.
- **SC-011**: Frontend HTTP responses include a Content Security Policy header.
- **SC-012**: Pipeline configuration hook is split into 3 hooks, each under 80 lines.

## Assumptions

- The existing `services/chat_store.py` implementation and `012_chat_persistence.sql` migration are correct and production-ready. No new persistence layer needs to be built from scratch.
- The mixin pattern in `services/github_projects/service.py` (4700 LOC) is intentionally well-organized and does NOT need decomposition.
- SQLite remains the database; no PostgreSQL migration is in scope.
- OAuth state stored in-memory is an acceptable tradeoff (users re-initiate if container restarts mid-flow).
- `openapi-typescript` is sufficient for initial type generation (zero runtime, types-only). A full API client generator like `orval` is out of scope.
- Build-time codegen for shared constants (file generation) is preferred over a runtime API endpoint.
- Scope is limited to code-level improvements; operational infrastructure changes (PostgreSQL, Redis, Sentry, external APM) are excluded.
- The frontend serves from a static file server with configurable response headers (CSP can be added at the server level).

## Scope Boundaries

### In Scope

- Backend DRY consolidation (repository resolution, error helpers, cache wrapper, project guard)
- Chat module decomposition and persistence wiring
- Frontend hook decomposition
- OpenAPI-to-TypeScript type generation pipeline
- Shared constants codegen (backend → frontend)
- Structured JSON logging
- Distributed tracing instrumentation
- Content Security Policy headers
- Frontend error reporting to backend
- Missing page and component test files
- Chat persistence integration test
- CI runtime version alignment
- Migration rollback/dry-run support
- Pre-commit type freshness check

### Out of Scope

- Database engine migration (SQLite → PostgreSQL)
- External monitoring services (Sentry, Datadog, etc.)
- GitHub service layer refactoring (mixin pattern is clean)
- New user-facing features or UI changes
- Authentication flow changes
- Performance optimization (caching strategy changes, query optimization)
- API versioning changes
