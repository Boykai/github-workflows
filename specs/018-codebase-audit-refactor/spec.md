# Feature Specification: Codebase Audit & Refactor

**Feature Branch**: `018-codebase-audit-refactor`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Audit and refactor FastAPI + React codebase: modernize packages, DRY up code, fix anti-patterns. Refactor in-place with rate limiting improvements for GitHub API calls."

## Clarifications

### Session 2026-03-05

- Q: Should the `delete_files` stub be implemented or the parameter removed? → A: Implement file deletion using GraphQL `fileChanges.deletions`.
- Q: Which service initialization pattern should be kept — `app.state` or module-level globals? → A: Keep `app.state`, remove module-level globals.
- Q: What are the default timing values for rate-limit buffers and adaptive polling? → A: 500ms gap between calls, 60s base poll interval, 2x backoff multiplier (conservative).
- Q: Should chat messages/proposals be persisted to SQLite or just documented as in-memory? → A: Persist to SQLite.
- Q: What is the maximum size bound for the shared CopilotClientPool? → A: 50 clients.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dependencies Stay Current and Lean (Priority: P1)

As a developer maintaining this application, I want all backend and frontend dependencies to be up-to-date and free of unused packages so that the project benefits from the latest bug fixes, security patches, and performance improvements — and new contributors are not confused by phantom dependencies.

**Why this priority**: Outdated or unused dependencies create security vulnerabilities, increase build times, and mislead developers about what the system actually uses. This is the lowest-risk, highest-trust change and unblocks all other refactoring.

**Independent Test**: Can be fully tested by running the full test suite after dependency updates and verifying all imports resolve correctly. Delivers immediate value by reducing attack surface and build footprint.

**Acceptance Scenarios**:

1. **Given** the backend has a dependency (`agent-framework-core`) that is never imported anywhere, **When** it is removed from the dependency manifest, **Then** the application starts successfully and all tests pass.
2. **Given** the backend uses the GitHub Copilot SDK, **When** the SDK version is updated to the latest stable release, **Then** all SDK-dependent features (client creation, model listing, session management) continue to work and tests pass.
3. **Given** the frontend has dependencies for React, build tools, and testing, **When** they are updated to latest stable versions, **Then** the frontend builds, runs, and passes all tests without regressions.
4. **Given** the backend uses `openai` and `azure-ai-inference` packages, **When** they are updated to latest stable releases, **Then** the Azure OpenAI fallback provider continues to function correctly.

---

### User Story 2 - Shared Infrastructure Eliminates Duplicated Code (Priority: P1)

As a developer working on the GitHub integration layer, I want duplicated patterns (client caching, header construction, fallback strategies, retry logic) to each exist in exactly one place so that bug fixes and behavior changes only need to happen once and the codebase is easier to understand.

**Why this priority**: Duplicated logic is the single largest source of inconsistency bugs and maintenance overhead. Consolidating these patterns directly improves reliability and reduces future development time.

**Independent Test**: Can be tested by running the full backend test suite after consolidation. Each consolidated pattern can also be tested in isolation with unit tests verifying the shared implementation handles all previously-covered cases.

**Acceptance Scenarios**:

1. **Given** two services independently cache Copilot SDK clients using identical logic, **When** the caching is consolidated into a single shared mechanism, **Then** both services use the same cache and client creation happens only once per unique token.
2. **Given** the GitHub service has multiple methods that follow a "try primary approach → catch error → try fallback approach → log result" pattern, **When** a generic fallback helper is introduced, **Then** each paired method delegates to the helper, reducing boilerplate while preserving the same behavior.
3. **Given** HTTP retry logic exists in two separate places with overlapping concerns, **When** the retry strategy is unified, **Then** all HTTP calls use one consistent retry mechanism with exponential backoff that also handles rate-limit responses.
4. **Given** HTTP headers are constructed in multiple places with varying feature flags, **When** header construction is consolidated into a single builder, **Then** all API calls use the shared builder and feature flags are passed as parameters.

---

### User Story 3 - Anti-Patterns Are Resolved for Production Readiness (Priority: P2)

As an operator deploying this application, I want known anti-patterns (hardcoded configuration, volatile in-memory state, dead code, inconsistent initialization) to be cleaned up so that the system behaves predictably across restarts and is easier to debug in production.

**Why this priority**: Anti-patterns create subtle, hard-to-diagnose production issues (data loss on restart, confusion from dead code paths, inconsistent initialization). Fixing them improves operational confidence.

**Independent Test**: Each anti-pattern fix can be tested independently. For example, parameterizing the hardcoded model can be tested by verifying the mutation accepts a model argument; documenting in-memory state limitations can be verified by inspecting code comments.

**Acceptance Scenarios**:

1. **Given** a GraphQL mutation has a model identifier hardcoded in the query string, **When** the mutation is refactored to accept the model as a parameter, **Then** the caller can pass any model identifier and the mutation uses it correctly.
2. **Given** the file-commit workflow accepts a "delete files" parameter that is silently ignored, **When** file deletion is implemented using the GraphQL API's supported deletion mechanism, **Then** callers can delete files in a commit and the operation completes successfully.
3. **Given** in-memory chat stores (messages, proposals, recommendations) are lost on application restart, **When** they are migrated to SQLite persistence, **Then** chat data survives restarts and existing API endpoints return the same data shape as before.
4. **Given** OAuth states remain in-memory, **When** a code comment is added documenting this limitation, **Then** developers and operators understand the trade-off.
4. **Given** services are registered both as application-level state and as module-level globals, **When** module-level globals are removed in favor of `app.state`, **Then** all services are accessed via `app.state` and tests can cleanly override service instances by setting `app.state` values.
5. **Given** some in-memory collections lack size bounds, **When** all in-memory caches are verified to use bounded collections, **Then** the application is protected from unbounded memory growth.

---

### User Story 4 - GitHub API Rate Limits Are Respected Intelligently (Priority: P2)

As a user performing bulk operations (creating multiple issues, assigning agents, polling for status), I want the system to space out GitHub API calls with timing buffers and avoid unnecessary requests so that I am never blocked by rate limiting and the UI remains responsive.

**Why this priority**: Hitting GitHub rate limits degrades the user experience severely — operations fail, polling stalls, and the user has no recourse but to wait. Smart request management directly impacts usability for power users.

**Independent Test**: Can be tested by running integration tests that verify timing gaps between consecutive API calls, and by checking that the polling loop adapts its frequency based on recent API responses.

**Acceptance Scenarios**:

1. **Given** the system makes rapid consecutive GitHub API calls (e.g., assigning agents to multiple issues), **When** timing buffers are applied between calls, **Then** the calls are spaced to stay well within GitHub's rate limit thresholds.
2. **Given** a polling loop checks for agent completion status, **When** no changes have been detected in recent polls, **Then** the polling interval increases (backs off) to reduce unnecessary API calls.
3. **Given** the system receives a rate-limit response (HTTP 429 or `retry-after` header) from GitHub, **When** the retry logic processes the response, **Then** the system waits the specified time before retrying and does not make additional calls during the wait period.
4. **Given** cached data is still fresh, **When** a new request would fetch the same data, **Then** the cached version is used instead of making a new API call.

---

### Edge Cases

- What happens when a dependency update introduces a breaking API change in the Copilot SDK? The system should fail gracefully with clear error messages indicating version incompatibility.
- What happens when both the primary and fallback strategies fail for a GitHub API call? The unified fallback helper should propagate the error with context from both attempts.
- What happens when the shared client cache grows large (many unique tokens)? The cache should use bounded collections to prevent unbounded memory growth.
- What happens when GitHub's rate limit resets mid-operation? The retry logic should detect the reset and resume normal operation immediately rather than waiting for the full backoff period.
- What happens when a GraphQL mutation that previously had a hardcoded model receives an empty or invalid model parameter? The system should validate the parameter and return a clear error before sending the request.
- What happens when the `delete_files` parameter contains paths that don't exist in the repository? The commit operation should handle this gracefully (GitHub's API may ignore non-existent deletions or return an error).
- What happens when the SQLite migration for chat persistence fails on an existing database? The migration should be additive (new tables) and not affect existing data.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1: Modernize Packages

- **FR-001**: The backend dependency manifest MUST NOT include `agent-framework-core` since it is unused by the codebase.
- **FR-002**: The GitHub Copilot SDK dependency MUST be at the latest stable version available on PyPI.
- **FR-003**: The `openai` and `azure-ai-inference` backend dependencies MUST be at their latest stable versions.
- **FR-004**: Frontend dependencies (`react`, `@tanstack/react-query`, `vite`, `vitest`, `playwright`) MUST be at their latest stable versions.
- **FR-005**: After all dependency updates, the full backend test suite MUST pass with zero failures.
- **FR-006**: After all dependency updates, the full frontend test suite MUST pass with zero failures.

#### Phase 2: DRY Consolidation

- **FR-007**: A single shared client caching mechanism MUST replace the duplicate caching logic currently present in the completion provider and model fetcher services.
- **FR-008**: The shared client cache MUST use a bounded collection with a default maximum of 50 entries to prevent unbounded memory growth.
- **FR-009**: A generic fallback helper MUST be available for methods that follow the "try primary → catch → try fallback → log" pattern.
- **FR-010**: HTTP retry logic MUST be unified into a single strategy that handles both standard HTTP errors and GitHub-specific rate-limit responses (HTTP 429, secondary rate limits, `retry-after` headers).
- **FR-011**: HTTP header construction MUST be consolidated into a single builder that accepts optional feature flags (e.g., GraphQL feature headers for specific mutations).
- **FR-012**: All DRY consolidation MUST happen within existing file boundaries — no new modules or files may be created.

#### Phase 3: Fix Anti-Patterns

- **FR-013**: The GraphQL mutation for assigning Copilot MUST accept the model as a parameter rather than having it hardcoded in the query string.
- **FR-014**: The file-commit workflow MUST implement file deletion support using the GraphQL `createCommitOnBranch` mutation's `deletions` field in `fileChanges`.
- **FR-015**: Chat messages, proposals, and recommendations MUST be persisted to SQLite (using the existing database service and migration system) so that data survives application restarts. OAuth states MUST have code comments documenting that they remain in-memory (acceptable for single-instance MVP).
- **FR-016**: Service initialization MUST use the `app.state` pattern exclusively; module-level global service variables MUST be removed.
- **FR-017**: All in-memory caches and collections used for operational state MUST use bounded collections (verified for pipeline states, branch mappings, sub-issue mappings, processed PR sets, pending assignments).

#### Rate Limiting & Request Optimization

- **FR-018**: Consecutive GitHub API calls within a single operation MUST include a configurable timing buffer between requests, defaulting to 500ms.
- **FR-019**: The background polling loop MUST implement adaptive polling intervals starting at 60 seconds, doubling (2x backoff) when no state changes are detected, up to a configurable maximum (default 5 minutes), and resetting to baseline when activity resumes.
- **FR-020**: The retry mechanism MUST respect `retry-after` headers and GitHub's rate-limit reset timestamps.
- **FR-021**: The system MUST NOT make redundant API calls when cached data is still considered fresh.

#### Testing

- **FR-022**: All existing tests MUST be updated to reflect refactored code (renamed methods, consolidated interfaces, new parameters).
- **FR-023**: The refactored code MUST maintain backward compatibility for all API endpoints consumed by the frontend.

### Key Entities

- **CopilotClientPool**: A shared, bounded cache (max 50 entries) of Copilot SDK client instances keyed by token hash. Used by both the completion provider and model fetcher services to avoid duplicate client creation.
- **FallbackResult**: The outcome of a primary-then-fallback operation, capturing which strategy succeeded, any errors from the failed strategy, and the result value.
- **RateLimitState**: Tracks the current GitHub API rate limit status — remaining calls, reset timestamp, and whether the system is currently in a backoff period.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The backend dependency manifest contains zero unused packages (verified by static import analysis).
- **SC-002**: All backend and frontend dependencies are at their latest stable versions as of the date of the refactor.
- **SC-003**: The number of duplicated code patterns (client caching, fallback chains, header construction) is reduced to zero — each pattern exists in exactly one place.
- **SC-004**: 100% of existing tests pass after all refactoring changes, with tests updated as necessary to match new interfaces.
- **SC-005**: All in-memory collections used for caching or operational state have explicit size bounds.
- **SC-006**: Zero hardcoded configuration values exist in query strings or mutation definitions — all configurable values are passed as parameters.
- **SC-007**: Consecutive GitHub API calls within a single user operation are spaced by at least 500ms (configurable).
- **SC-008**: The background polling loop's interval doubles after each consecutive poll with no state changes (starting at 60s, capping at 5 minutes).
- **SC-009**: All API endpoints maintain their existing request/response contracts (backward compatibility verified by end-to-end tests).
- **SC-010**: The refactoring introduces no new files or modules — all changes occur within existing file boundaries.

## Assumptions

- The application is deployed as a single instance (no horizontal scaling), making in-memory state acceptable for MVP with documented limitations.
- GitHub's rate limit for authenticated API calls is 5,000 requests/hour for REST and 5,000 points/hour for GraphQL, which is the baseline for timing buffer calculations.
- The Copilot SDK, `openai`, and `azure-ai-inference` packages maintain backward-compatible APIs across minor version updates.
- SQLite with WAL mode is sufficient for the current scale; no migration to a different database is in scope.
- The dual AI provider pattern (Copilot SDK primary + Azure OpenAI fallback) is a permanent architectural decision, not a temporary measure.
- Frontend dependency updates (React, Vite, etc.) will not require React 19 migration patterns — if React 19 introduces breaking changes, the update should stay on the latest React 18.x.
- "Refactor in-place" means changes happen within existing file boundaries; small helper functions/classes may be added to existing files but no new files or module directories are created.
