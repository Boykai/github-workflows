# Feature Specification: Code Quality & Technical Debt Overhaul

**Feature Branch**: `033-code-quality-overhaul`  
**Created**: 2026-03-10  
**Status**: Draft  
**Input**: User description: "Systematic 6-phase plan to reduce complexity, eliminate duplication, modernize patterns, and remove dead code across a 121K-LOC full-stack app. Targets the 8 highest-complexity functions (complexity 42–123), DRY violations across 8+ files, the 5,338-line God class, and infrastructure hygiene."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Developer Encounters a Bug in the Polling Pipeline (Priority: P1)

A developer needs to fix a bug in the agent output posting logic. Today, the relevant function is 1,100 lines long with 6+ levels of nesting. The developer must read and understand the entire function to identify which sub-responsibility contains the bug. After the overhaul, each sub-responsibility is a clearly-named function under 200 lines. The developer locates the bug by reading only the relevant helper, fixes it, and writes a targeted unit test — all without risk of side-effects in unrelated logic.

**Why this priority**: The highest-complexity functions (complexity 42–123) are the primary source of defects and the primary barrier to onboarding. Reducing their complexity directly reduces defect rates and developer cognitive load across every future code change.

**Independent Test**: Can be verified by running `cgc analyze complexity` before and after refactoring. All refactored backend functions score below 25. All existing tests pass without modification.

**Acceptance Scenarios**:

1. **Given** the backend codebase with 8 functions scoring complexity > 40, **When** all Phase 3 refactoring is complete, **Then** no backend function exceeds a cyclomatic complexity score of 25.
2. **Given** `post_agent_outputs_from_pr()` is a single 1,100-line function, **When** it is decomposed into focused helper functions, **Then** each extracted helper is independently unit-testable and under 200 lines.
3. **Given** `assign_agent_for_status()` mixes agent resolution, base branch strategy, and model precedence in a single method, **When** it is refactored, **Then** each concern (agent resolution, branch strategy, model resolution) is a separate function or dataclass.

---

### User Story 2 — Developer Adds a New API Endpoint That Needs Repository Info (Priority: P1)

A developer building a new API endpoint needs the current repository owner and name. Today, 8 separate code paths resolve repository information with inconsistent fallback logic — some check only the cache, others do a full 3-step fallback. The developer doesn't know which pattern to copy. After the overhaul, a single `resolve_repository()` function is the canonical entry point, documented and used consistently in all endpoints. The developer calls it once and has correct, consistent behavior.

**Why this priority**: DRY violations cause inconsistent behavior across endpoints and confuse developers choosing which code path to follow. Consolidating them eliminates a class of subtle bugs (missing fallback steps) and removes ~230 lines of duplicated code.

**Independent Test**: Can be verified by confirming all repository resolution call sites use `resolve_repository()` and the removed duplicate functions are gone. `ruff check` passes. `pytest -x` passes.

**Acceptance Scenarios**:

1. **Given** 8 separate repository resolution code paths exist, **When** DRY consolidation is complete, **Then** all callers use the single canonical `resolve_repository()` function.
2. **Given** `_get_repository_info()` in workflow.py duplicates logic from utils.py, **When** Phase 2 is complete, **Then** `_get_repository_info()` is deleted and the 102-line inlined fallback in main.py is removed.
3. **Given** 5 endpoints repeat the "no project selected" validation check, **When** `require_selected_project()` is extracted, **Then** all 5 callers use the shared helper with identical error messaging.
4. **Given** cache check/refresh/set patterns are repeated in 4 API files, **When** `cached_fetch()` is extracted, **Then** all 4 callers use the generic wrapper.

---

### User Story 3 — Developer Needs to Modify Issue Creation Logic (Priority: P2)

A developer must change how issues are created — for example, adding a new field. The GitHub API service is a single 5,338-line class with 50+ methods spanning issues, PRs, branches, projects, and bot detection. The developer must scroll through thousands of lines to find the relevant methods, risking accidental changes to unrelated concerns. After the overhaul, issue-related methods live in a dedicated `GitHubIssuesService` class. The developer opens one focused file, makes the change, and runs tests for that service only.

**Why this priority**: The God class is the largest maintainability liability. Splitting it enables parallel development (multiple developers can work on issues, PRs, and branches simultaneously) and makes each domain testable in isolation.

**Independent Test**: Can be verified by measuring file sizes after split. Core service.py is under 1,500 lines. Each extracted service is under 800 lines. All existing callers compile and pass tests.

**Acceptance Scenarios**:

1. **Given** service.py is 5,338 lines, **When** domain services are extracted, **Then** no single file exceeds 1,500 lines and each extracted service is under 800 lines.
2. **Given** issue methods, PR methods, and branch methods coexist in one class, **When** split is complete, **Then** each domain has its own service class inheriting from a shared `GitHubBaseClient`.
3. **Given** rate-limit management uses both contextvars and instance attributes, **When** `RateLimitManager` is extracted, **Then** all rate-limit state lives in a single dedicated class.
4. **Given** bot detection methods are static, **When** `GitHubIdentities` is extracted, **Then** bot detection is a standalone utility with no service dependency.

---

### User Story 4 — Developer Modifies the Settings Page Form (Priority: P2)

A developer needs to add a new setting field to the global settings form. The current component is 380 lines with 14 form fields inline, manual flatten/unflatten logic, and no sub-component decomposition. The developer must understand the entire form's state management to add a single field. After the overhaul, the form is split into logical sections (AI settings, display, workflow, notifications). The developer adds the field to the relevant section component with standard form handling.

**Why this priority**: Frontend complexity hotspots slow UI iteration. Breaking monolithic components into focused sections follows React best practices and makes each section independently testable.

**Independent Test**: Can be verified by running `npx vitest run` and `npx tsc --noEmit`. Manual test: settings page saves all fields correctly. Each extracted section component renders independently in tests.

**Acceptance Scenarios**:

1. **Given** GlobalSettings.tsx is a single 380-line component with 14 inline fields, **When** it is decomposed, **Then** each section component is under 100 lines.
2. **Given** usePipelineConfig.ts manages 10+ useState calls in 616 lines, **When** it is split into focused hooks, **Then** each hook manages a single concern and is under 200 lines.
3. **Given** LoginPage.tsx has 8 levels of nesting with 20+ decorative divs, **When** refactored, **Then** decorative elements are extracted into a reusable background component.

---

### User Story 5 — Operations Verifies Build Reproducibility (Priority: P3)

An operations team member runs `docker compose build` and gets a different image than what was built last month because dependencies resolved to newer, potentially breaking versions. After the overhaul, all Docker images are pinned to specific versions, Python dependency ranges have upper bounds, and the build produces consistent results.

**Why this priority**: Build reproducibility prevents production surprises. While not a daily developer concern, unpinned dependencies and `latest` tags are a ticking time bomb for deployment reliability.

**Independent Test**: Can be verified by confirming `docker compose build` succeeds, no `latest` tags remain in docker-compose.yml, and pyproject.toml has upper bounds on all major dependencies.

**Acceptance Scenarios**:

1. **Given** signal-api uses the `latest` Docker tag, **When** infrastructure hygiene is complete, **Then** all Docker image tags are pinned to specific semantic versions.
2. **Given** Python dependencies have no upper bounds, **When** pyproject.toml is updated, **Then** every major dependency has an explicit upper bound (e.g., `<1.0.0`).
3. **Given** pyright runs in `basic` mode, **When** upgraded to `standard` mode, **Then** the codebase passes type-checking or all exceptions are explicitly documented.

---

### User Story 6 — Developer Writes Tests for a High-Complexity Function (Priority: P3)

A developer wants to add tests for `recover_stalled_issues()` (complexity 72). Today, the function has deeply nested loops, emoji-based state detection via string matching, and interleaved API calls — making it nearly impossible to unit-test in isolation. After the overhaul, each sub-responsibility (cooldown check, tracking table validation, agent reassignment) is a separate function. The developer writes targeted unit tests for each, achieving high coverage without complex integration setups.

**Why this priority**: High-complexity functions with thin test coverage are the highest-risk code in the codebase. Making them testable is a prerequisite for safe future changes.

**Independent Test**: Can be verified by running `pytest --cov` before and after. Coverage for refactored modules increases. Each extracted helper has dedicated unit tests.

**Acceptance Scenarios**:

1. **Given** agent_output.py, recovery.py, cleanup_service.py, and chat.py have thin test coverage relative to their complexity, **When** Phase 3 refactoring + Phase 6 test additions are complete, **Then** each refactored module has at least 70% line coverage.
2. **Given** mock factories are duplicated between conftest.py and helpers/mocks.py, **When** consolidated, **Then** a single source of mock creation exists.
3. **Given** test mocks accept any call signature, **When** `spec=` is added to mock constructors, **Then** mocks reject calls with incorrect parameters.

---

### Edge Cases

- What happens when a refactored function's extracted helper is called with arguments from a legacy code path that relied on side effects of the original monolithic function? Each extraction must preserve the same external behavior verified by existing tests.
- How does the system handle the God class split when callers import the service as a singleton? Dependency injection must be updated atomically — partial splits that leave some callers on the old class and others on the new would break at runtime.
- What if the `cached_fetch()` wrapper introduces subtle timing differences compared to the inline cache pattern? Each callsite must be individually verified with both cache-hit and cache-miss scenarios.
- What happens when existing tests mock the old monolithic service class but the split creates multiple new classes? Tests must be updated to mock the correct new service, or a compatibility facade must exist during the transition.
- How does the system handle Phase 3.5 chat storage migration (dict → persistent store) when the application is running? The migration must be backward-compatible — existing in-memory messages should be accessible during the transition period.
- What if upper-bounding Python dependencies in Phase 6 excludes a version already installed in production? Bounds must be set to include the currently deployed version.

## Clarifications

### Session 2026-03-10

- Q: How should the God class split be transitioned (big-bang, incremental with facade, or incremental without facade)? → A: Incremental without facade: extract one service at a time; immediately update all callers of that domain in the same PR.
- Q: Should refactored modules adopt structured logging requirements? → A: Require structured logging (JSON) across the entire backend, not just refactored modules.
- Q: How is "phase done" determined before moving to the next phase? → A: All tests passing (stale/bad tests removed first), then commit changes with a detailed description before moving to the next phase.

## Requirements *(mandatory)*

### Functional Requirements

#### Phase 1: Dead Code & Build Artifact Cleanup

- **FR-001**: All static analysis false positives from coverage report artifacts (htmlcov/) MUST be eliminated from analysis tool output by ensuring artifacts are excluded from analysis scope.
- **FR-002**: All commented-out code blocks in backend source files MUST be removed unless they contain an active TODO with a tracked issue number.
- **FR-003**: Unused utility functions (`handle_service_error()`, `safe_error_response()`) MUST either be adopted by Phase 2 callers or deleted.

#### Phase 2: DRY Consolidation

- **FR-004**: All repository resolution logic MUST use a single canonical function as entry point, with no duplicate implementations remaining.
- **FR-005**: All API endpoints requiring a selected project MUST validate through a single shared helper that returns the project ID or raises a consistent error.
- **FR-006**: All cache check/refresh/set patterns MUST use a generic wrapper function, eliminating inline cache management in API endpoints.
- **FR-007**: Error handling across API endpoints MUST use a shared pattern (helper function or decorator) that logs consistently and raises typed exceptions.
- **FR-008**: Frontend case-insensitive key matching MUST use a single utility function rather than inline logic repeated across hooks.

#### Phase 3: Backend Complexity Reduction

- **FR-009**: No backend function MUST exceed a cyclomatic complexity score of 25 after refactoring.
- **FR-010**: Each extracted helper function MUST be independently unit-testable — accepting explicit parameters rather than relying on closure over parent scope.
- **FR-011**: Emoji-based state detection strings MUST be replaced with a typed enumeration for agent step states.
- **FR-012**: The in-memory chat message store MUST be replaced with a persistent store that has an automatic expiration mechanism to prevent unbounded memory growth.
- **FR-013**: The polling loop MUST define steps as a data structure (list of step definitions) rather than repeated inline conditional blocks.

#### Phase 4: God Class Decomposition

- **FR-014**: The monolithic GitHub API service MUST be split into domain-specific services (issues, pull requests, branches, projects) inheriting from a shared base client. Each service MUST be extracted incrementally without a facade — all callers of a given domain MUST be updated to use the new service in the same PR as the extraction.
- **FR-015**: Rate-limit management MUST be encapsulated in a dedicated class rather than spread across contextvars and instance attributes.
- **FR-016**: Static utility methods (bot detection) MUST be moved to a standalone module with no service class dependency.
- **FR-017**: Method return types MUST use typed models rather than raw dictionaries for the most-called service methods.

#### Phase 5: Frontend Complexity Reduction

- **FR-018**: No frontend component or hook MUST exceed 200 lines after refactoring. Monolithic components MUST be decomposed into focused sub-components.
- **FR-019**: Shared time/date calculation logic MUST be extracted into a reusable utility module.
- **FR-020**: Type-unsafe casts (`as unknown as ...`) for API response data MUST be replaced with validated schemas.
- **FR-021**: Form state management for settings MUST use a declarative approach eliminating manual flatten/unflatten cycles.

#### Phase 6: Infrastructure & Testing Hygiene

- **FR-022**: All Docker image references MUST use pinned semantic version tags, not `latest` or bare tags.
- **FR-023**: All major Python dependencies MUST have explicit upper-bound version constraints.
- **FR-024**: Test mock constructors MUST use `spec=` parameter to validate call signatures at test time.
- **FR-025**: Duplicate mock factory definitions MUST be consolidated into a single location.
- **FR-026**: Every refactored high-complexity function MUST have dedicated unit tests covering its primary and error paths.

#### Cross-Cutting: Structured Logging

- **FR-027**: All backend modules MUST use structured JSON logging via Python's standard `logging` module with a JSON formatter. Plain-text log calls (bare `print()`, unstructured `logger.info("message")`) MUST be replaced with structured key-value log entries.
- **FR-028**: Each structured log entry MUST include at minimum: timestamp, level, module, and a message field. Service-layer logs SHOULD additionally include correlation context (request ID or operation ID) where available.

#### Cross-Cutting: Phase Completion Gates

- **FR-029**: Before starting each phase, any stale, broken, or obsolete tests related to the phase's scope MUST be identified and removed. Tests that validate behavior being intentionally changed are updated or replaced, not left to fail.
- **FR-030**: Each phase MUST be committed as a self-contained changeset with a detailed commit message describing what was changed, why, and which success criteria were verified. All tests (`pytest -x` for backend, `vitest run` for frontend) MUST pass before the commit is made.

### Key Entities

- **Function Complexity Score**: A numeric measure (cyclomatic complexity) of a function's branching paths. The target threshold after refactoring is ≤ 25. Tracked per function, reported by static analysis tools.
- **DRY Violation**: A pattern where identical or near-identical logic exists in multiple locations. Each violation is identified by the duplicated pattern, the files affected, and the line count savings when consolidated.
- **Domain Service**: A focused class responsible for a single area of GitHub API interaction (issues, PRs, branches, projects). Each inherits shared HTTP/caching infrastructure from a base client.
- **Refactoring Phase**: A self-contained scope of changes that can be verified independently. Each phase has entry prerequisites, file scope, and pass/fail verification criteria.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All backend functions score below 25 on cyclomatic complexity (currently 8 functions score 40–123).
- **SC-002**: Total backend source lines of code decrease by at least 200 lines through DRY consolidation (currently ~43,000 lines).
- **SC-003**: The largest backend file is under 1,500 lines (currently 5,338 lines in service.py).
- **SC-004**: No single frontend component or hook exceeds 200 lines (currently 6 files exceed 380 lines).
- **SC-005**: All existing tests continue to pass after each phase — zero regressions introduced.
- **SC-006**: Backend test coverage for refactored modules reaches at least 70% line coverage.
- **SC-007**: Static analysis (`ruff check`, `pyright`, `tsc --noEmit`, `eslint`) produces zero new warnings after all phases.
- **SC-008**: Docker builds are fully reproducible — no `latest` tags and all dependency versions have explicit bounds.
- **SC-009**: No backend function requires reading more than 200 lines to understand a single responsibility. Verified by: `wc -l` on all extracted helper functions returns ≤200 for each.
- **SC-010**: The number of duplicate code patterns (as identified by the DRY analysis) is reduced to zero for the patterns tracked in Phase 2 (repository resolution, project validation, cache patterns, error handling).

## Assumptions

- The existing test suite is comprehensive enough to catch regressions introduced by refactoring. Each phase includes running the full test suite as a gate. Stale or broken tests are cleaned up before each phase begins.
- Performance characteristics (response times, memory usage) are maintained or improved. No refactoring should introduce additional latency or resource consumption.
- All refactoring is internal. No public API contracts (HTTP endpoints, WebSocket messages, Docker compose interface) change.
- The team uses Python 3.13+ and TypeScript 5.9+ — modern language features (match/case, satisfies, etc.) are available.
- The `cgc analyze complexity` tool is the agreed-upon measure for cyclomatic complexity scoring.
- The in-memory chat storage migration (Phase 3.5) uses SQLite consistent with the existing session storage pattern, not an external datastore.
- React Hook Form + Zod adoption (Phase 5.1) is approved as a new frontend dependency.
- Structured JSON logging is adopted backend-wide using Python's standard `logging` module with a JSON formatter (e.g., `python-json-logger` or equivalent).

## Scope Boundaries

**In scope**:
- Refactoring existing code for reduced complexity, elimination of duplication, and improved testability
- Extracting helper functions, dataclasses, enums, and utilities from oversized modules
- Splitting monolithic classes into domain-specific services
- Infrastructure version pinning and dependency hygiene
- Adding tests for previously untestable high-complexity code
- Migrating in-memory chat storage to persistent store

**Out of scope**:
- New user-facing features or capabilities
- Architecture changes beyond the God class split (no new services, databases, or infrastructure)
- Frontend framework migration (staying on React 19 + Vite 7)
- CI/CD pipeline changes (this spec covers code changes only)
- Performance optimization beyond what naturally results from cleaner code structure
