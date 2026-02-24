# Feature Specification: Codebase Cleanup & Refactor

**Feature Branch**: `009-codebase-cleanup-refactor`  
**Created**: 2026-02-22  
**Status**: Draft  
**Input**: User description: "Analyze entire codebase to look for refactor opportunities. Remove legacy/old stale code. Keep it simple. Keep it DRY. Use best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Eliminate Dead Code and Stale Artifacts (Priority: P1)

As a developer working on this project, I want all unused code, stale imports, and dead code paths removed so that the codebase only contains code that is actively used, reducing confusion and cognitive load when navigating files.

**Why this priority**: Dead code is the lowest-risk, highest-clarity refactor target. Removing it immediately reduces file sizes, eliminates misleading code paths, and makes all subsequent refactoring easier and safer.

**Independent Test**: After removal, the application builds successfully, all existing tests pass, and a workspace-wide search confirms the deleted symbols are no longer referenced anywhere.

**Acceptance Scenarios**:

1. **Given** the backend defines `RateLimiter` in `main.py` and it is not wired into any middleware or endpoint, **When** a developer searches for `RateLimiter` usage, **Then** zero references exist because the class has been removed.
2. **Given** the frontend defines `ErrorToast`, `ErrorBanner`, and `RateLimitIndicator` components that are never imported, **When** those component files are deleted, **Then** the application compiles without errors and no import references to them remain.
3. **Given** `types/index.ts` exports `AVAILABLE_LABELS` and `NotificationEventType` that are never referenced by consumers, **When** those exports are removed, **Then** the build succeeds with no missing-import errors.
4. **Given** `identify_target_status` in `ai_agent.py` appears to be dead code, **When** it is removed (after confirming zero callers), **Then** no runtime or test failures occur.
5. **Given** `useWorkflow.ts` and `IssueRecommendationPreview.tsx` have redundant default exports alongside named exports, **When** default exports are removed, **Then** all importers still resolve correctly via named exports.
6. **Given** the `frontend/src/utils/` directory is empty, **When** it either houses newly-extracted utilities or is deleted, **Then** no empty placeholder directories remain.

---

### User Story 2 - Decompose Oversized Backend Modules (Priority: P1)

As a developer, I want the three largest backend files (`copilot_polling.py` at ~4,045 lines, `github_projects.py` at ~4,449 lines, and `workflow_orchestrator.py` at ~2,049 lines) broken into focused, single-responsibility modules so that each file is easier to understand, test, and modify independently.

**Why this priority**: These oversized files are the primary source of complexity, circular dependencies, and merge conflicts. Decomposing them unblocks all other refactoring work and improves developer velocity.

**Independent Test**: After decomposition, every existing test passes, each new module has a clear single responsibility, and no circular imports exist between the new modules.

**Acceptance Scenarios**:

1. **Given** `copilot_polling.py` contains polling lifecycle, agent output extraction, pipeline advancement, recovery logic, and completion detection, **When** it is decomposed, **Then** each responsibility lives in its own module (e.g., polling lifecycle, agent output handling, pipeline advancement, recovery, completion detection) each with a single cohesive responsibility.
2. **Given** `github_projects.py` contains CRUD operations, GraphQL execution, board transformation, PR detection, and Copilot assignment, **When** it is decomposed, **Then** separate focused service modules exist, each with a single cohesive responsibility.
3. **Given** `workflow_orchestrator.py` mixes pure workflow logic with in-memory state management and 6 global dicts, **When** it is decomposed, **Then** workflow state management is separated from workflow transition logic.
4. **Given** `copilot_polling.py` imports from `workflow_orchestrator.py` and vice versa, **When** both are decomposed, **Then** no circular import chains exist between the resulting modules.

---

### User Story 3 - Consolidate Duplicated Backend Patterns (Priority: P2)

As a developer, I want repeated code patterns in the backend extracted into shared utilities so that bug fixes and behavior changes only need to happen in one place.

**Why this priority**: DRY violations create divergent behavior over time and increase the surface area for bugs. These are medium-risk refactors that depend on stable module boundaries from User Story 2.

**Independent Test**: After extraction, each duplicated pattern exists in exactly one location, all callers use the shared implementation, and all tests pass.

**Acceptance Scenarios**:

1. **Given** repository resolution logic is duplicated across `api/chat.py`, `api/tasks.py`, and `api/workflow.py`, **When** a shared `resolve_repository()` utility is extracted, **Then** all three endpoints delegate to the shared function and produce identical behavior.
2. **Given** Copilot polling startup is duplicated across `api/chat.py`, `api/projects.py`, and `api/workflow.py`, **When** a single `start_copilot_polling()` function is provided in the polling module, **Then** all three API files call the shared function.
3. **Given** `UserSession` construction from a database row is done in two places in `session_store.py`, **When** a `_row_to_session(row)` helper is extracted, **Then** both `get_session()` and `get_sessions_by_user()` use it.
4. **Given** the settings upsert pattern is duplicated in `settings_store.py`, **When** a generic `_upsert_row()` helper is extracted, **Then** both `upsert_user_preferences()` and `upsert_project_settings()` use it.
5. **Given** `handle_in_progress_status` and `handle_completion` in `workflow_orchestrator.py` share ~80% identical logic, **When** a shared `_transition_to_in_review()` helper is extracted, **Then** both functions delegate to it.
6. **Given** `PREDEFINED_LABELS` in `prompts/issue_generation.py` and `AVAILABLE_LABELS` in `models/chat.py` are near-identical, **When** a single canonical definition is placed in `constants.py`, **Then** all consumers reference that single source.

---

### User Story 4 - Consolidate Duplicated Frontend Patterns (Priority: P2)

As a developer, I want duplicated frontend code extracted into shared hooks, utilities, and components so that the UI layer is consistent and maintainable.

**Why this priority**: Frontend duplication leads to inconsistent UX and makes adding new features error-prone. This is a medium-risk, high-value cleanup.

**Independent Test**: After consolidation, duplicate definitions no longer exist, all affected components render correctly, and all frontend tests pass.

**Acceptance Scenarios**:

1. **Given** `StatusChangeProposal` is defined identically in `useChat.ts` and `ChatInterface.tsx`, **When** it is moved to a shared types module, **Then** both files import from the shared location.
2. **Given** `generateId()` is duplicated in `useAgentConfig.ts` and `AgentPresetSelector.tsx`, **When** it is extracted to a shared utility, **Then** both files import the shared function.
3. **Given** four settings components (`AIPreferences`, `DisplayPreferences`, `WorkflowDefaults`, `NotificationPreferences`) repeat identical form-state boilerplate, **When** a shared `useSettingsForm` hook is extracted, **Then** each component uses the shared hook and the form-state logic exists in one place.
4. **Given** `GlobalSettings.tsx` re-implements all 17 settings fields instead of composing existing section components, **When** it is refactored to compose the existing section components, **Then** field definitions exist only in the section components.
5. **Given** "time ago" formatting is duplicated in `ProjectBoardPage.tsx` and `ProjectSidebar.tsx`, **When** a shared `formatTimeAgo()` utility is created, **Then** both files use it.
6. **Given** `useWorkflow.ts` and `useAgentConfig.ts` use raw `fetch()` instead of the centralized API client, **When** they are migrated to the centralized API client and shared data-fetching pattern, **Then** all data-fetching follows the same pattern across the application.

---

### User Story 5 - Modernize Deprecated Patterns and Enforce Best Practices (Priority: P2)

As a developer, I want deprecated API calls replaced with modern equivalents and inconsistent practices standardized so that the codebase follows current best practices uniformly.

**Why this priority**: Deprecated APIs will eventually break in future runtime versions and inconsistencies create confusion. These changes are low-risk and can be done incrementally.

**Independent Test**: After migration, a search for deprecated patterns returns zero results, and all tests pass on the target runtime versions.

**Acceptance Scenarios**:

1. **Given** `datetime.utcnow()` is used in 30+ locations across the backend (deprecated since Python 3.12), **When** all occurrences are replaced with `datetime.now(UTC)`, **Then** zero uses of `datetime.utcnow()` remain and all timestamp behavior is consistent.
2. **Given** `asyncio.get_event_loop().time()` is used in `api/projects.py`, **When** it is replaced with a non-deprecated equivalent, **Then** the deprecated call is eliminated.
3. **Given** auth cookies have hardcoded `secure=False` and `max_age` values instead of reading from settings, **When** these values are derived from configuration, **Then** the cookie behavior is configurable per environment.
4. **Given** `workflow_orchestrator.py` uses synchronous database access inside an async application, **When** it is replaced with async-compatible database access, **Then** the event loop is no longer blocked by database calls.
5. **Given** `get_pr_timeline_events` in `github_projects.py` creates a new HTTP client per call instead of using the shared client, **When** it is updated to use the shared client, **Then** connection pooling is utilized and resource waste is eliminated.
6. **Given** some service methods bypass the shared retry/backoff logic for HTTP calls, **When** read-only and idempotent calls are routed through consistent retry logic, **Then** transient failures on reads/idempotent writes are handled uniformly, while non-idempotent mutations fail fast without retry.
7. **Given** frontend components use hardcoded magic numbers (poll intervals, timeout durations, expiry times), **When** these are extracted to named constants, **Then** each magic number is defined once with a descriptive name.

---

### User Story 6 - Improve Structural Organization (Priority: P3)

As a developer, I want clear module boundaries, proper separation of concerns, and consistent patterns so that the codebase is intuitive to navigate and extend.

**Why this priority**: Structural improvements have the broadest long-term impact but carry the highest risk. They should be done after the targeted cleanups in Stories 1–5 stabilize the codebase.

**Independent Test**: After restructuring, the application starts and behaves identically, all tests pass, and the code organization follows the established conventions.

**Acceptance Scenarios**:

1. **Given** `models/chat.py` contains ~15 models spanning chat, workflow, agent, and recommendation concerns, **When** it is split into focused model files, **Then** each model file has a single cohesive theme.
2. **Given** API endpoint handlers contain significant business logic, **When** business logic is moved into service classes, **Then** API handlers only handle request parsing, service delegation, and response formatting.
3. **Given** singleton services are instantiated as module-level globals (making testing difficult), **When** services are provided via dependency injection, **Then** services can be easily mocked in tests.
4. **Given** `api/auth.py` has two near-duplicate session dependency functions (`get_current_session` and `get_session_dep`), **When** they are consolidated into a single function, **Then** session resolution follows one code path.
5. **Given** frontend import paths inconsistently use path aliases and relative paths, **When** all imports are normalized to the path alias convention, **Then** import style is consistent across the entire frontend.
6. **Given** no error boundary exists in the frontend, **When** an error boundary is added at the application root, **Then** runtime errors in components display a fallback UI instead of a blank screen.
7. **Given** `AppContent` in `App.tsx` manages 6+ unrelated concerns, **When** concerns are distributed to appropriate view-specific wrappers, **Then** hooks only execute when their corresponding view is active.

---

### Edge Cases

- What happens when removing dead code that appears unused but is accessed via dynamic imports or reflection? Verify through runtime testing, not just static analysis.
- What happens when decomposing modules that are imported by external tooling or scripts outside the main application? Audit all entry points including test files, migration scripts, and CI workflows.
- What happens when renaming or moving modules that are referenced in configuration files (e.g., Docker, CI pipelines)? Update all configuration references as part of each refactor.
- How does the system handle import errors during a partial decomposition? Each module split must be atomic — all callers updated in the same commit.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove all identified dead code (unused classes, functions, components, type exports) without changing any user-facing behavior.
- **FR-002**: System MUST decompose backend files with multiple responsibilities into focused single-responsibility modules, targeting ~600 lines as a guideline (not a hard limit).
- **FR-003**: System MUST eliminate all identified duplicate code patterns by extracting shared utilities, hooks, or helpers that all callers reference.
- **FR-004**: System MUST replace all uses of `datetime.utcnow()` with `datetime.now(UTC)` across the entire backend.
- **FR-005**: System MUST replace all deprecated API calls with their modern equivalents.
- **FR-006**: System MUST migrate all frontend data-fetching hooks to use the centralized API client and the shared caching/query pattern.
- **FR-007**: System MUST extract all hardcoded magic numbers into named constants with descriptive names.
- **FR-008**: System MUST resolve circular import dependencies between backend modules.
- **FR-009**: System MUST ensure all existing tests continue to pass after each refactoring change.
- **FR-010**: System MUST split `models/chat.py` into cohesive, single-theme model files.
- **FR-011**: System MUST consolidate duplicate label definitions into a single source of truth in the constants module.
- **FR-012**: System MUST consolidate duplicate session dependency functions into a single function.
- **FR-013**: System MUST move duplicate type definitions (e.g., `StatusChangeProposal`) to the shared types module.
- **FR-014**: System MUST extract a shared settings-form hook to eliminate form boilerplate duplication across settings components.
- **FR-015**: System MUST refactor `GlobalSettings.tsx` to compose existing section components instead of re-implementing all fields.
- **FR-016**: System MUST derive hardcoded cookie configuration values from application settings.
- **FR-017**: System MUST route all read-only and idempotent HTTP calls through consistent retry/backoff logic. Non-idempotent mutations (e.g., create issue, merge PR) MUST fail fast without retry to avoid duplicate side effects.
- **FR-018**: System MUST add an error boundary at the frontend application root.

### Key Entities

- **Backend Module**: A Python file in `src/services/`, `src/api/`, or `src/models/` — key attributes are file path, line count, responsibility scope, and import dependencies.
- **Shared Utility**: An extracted function or class that replaces duplicated code — key attributes are location, list of callers, and the pattern it replaces.
- **Frontend Hook**: A custom hook in `src/hooks/` — key attributes are data-fetching pattern, state managed, and components that consume it.
- **Named Constant**: A descriptive variable replacing a magic number — key attributes are name, value, and all usage locations.

## Clarifications

### Session 2026-02-22

- Q: The spec contradicts itself on whether the 600-line file size limit is a hard requirement (FR-002) or a soft guideline (Assumptions). Which takes precedence? → A: Soft guideline only — aim for ~600 lines but focus on single-responsibility rather than strict line count enforcement.
- Q: Should each user story be delivered atomically (all tests pass at merge point), or can intermediate commits have failing tests? → A: Atomic per user story — each story lands as one commit/PR with all tests passing at each merge point. Intermediate WIP is allowed locally but never merged with failures.
- Q: Should the spec include a performance regression gate given module decomposition changes import graphs and FR-017 changes network behavior? → A: Yes — no measurable performance regression in application startup time or API response latency (p95) after refactoring.
- Q: Should retry logic apply to all HTTP calls including mutations, or only read-only operations? → A: Retry reads and idempotent writes only. Non-idempotent mutations (create issue, merge PR) fail fast without retry to avoid duplicate side effects.
- Q: User Story 6 includes adding a React Error Boundary and migrating to dependency injection — both add new capabilities beyond pure cleanup. Should they remain in scope? → A: Keep both in scope. They improve code quality and are natural extensions of the cleanup effort.

## Assumptions

- The ~600-line target is a soft guideline only — single-responsibility is the primary decomposition driver, not line count. A file may exceed 600 lines if it has one cohesive responsibility.
- "Dead code" is determined by static analysis (zero import references) and confirmed by successful test execution after removal.
- The existing test suite is the primary regression safety net; no new tests are required by this spec (though decomposed modules should be structured to be independently testable).
- Module decomposition will preserve all existing public APIs — only internal organization changes.
- Each user story is delivered as one atomic commit or squashed PR. All tests must pass at each merge point; intermediate work-in-progress states are allowed locally but never merged with failures.
- The application is deployed as a single backend + single frontend; there are no external consumers of backend Python modules that would break from internal restructuring.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every backend source file has a single clear responsibility (currently three files mix 3–5 concerns each). The ~600-line guideline is a soft target; single-responsibility is the primary metric.
- **SC-002**: Zero occurrences of `datetime.utcnow()` remain in the codebase (currently 30+).
- **SC-003**: All identified dead code artifacts are removed — at minimum: unused backend classes/functions and unused frontend components/type exports.
- **SC-004**: Zero circular import chains exist between backend modules.
- **SC-005**: Every duplicated utility function (repository resolution, polling startup, time formatting, ID generation, session construction, settings upsert) exists in exactly one location.
- **SC-006**: 100% of frontend data-fetching hooks use the centralized API client and caching pattern.
- **SC-007**: All existing automated tests pass after refactoring with no test modifications that weaken assertions.
- **SC-008**: Total lines of code across the codebase is reduced by at least 10% through dead code removal and deduplication.
- **SC-009**: No hardcoded magic numbers remain in frontend hook or component files — all are replaced with named constants.
- **SC-010**: Application starts successfully and all user-facing features behave identically before and after refactoring.
- **SC-011**: No measurable performance regression in application startup time or API response latency (p95) after refactoring.
