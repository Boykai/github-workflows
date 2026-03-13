# Feature Specification: Dead Code & Technical Debt Cleanup

**Feature Branch**: `039-dead-code-cleanup`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "Plan: Dead Code & Technical Debt Cleanup"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Remove Dead Code and Build Artifacts (Priority: P1)

As a developer, I want build artifacts and dead code removed from the codebase so that the code index is accurate, search results are uncluttered, and the project maintains a clean footprint.

**Why this priority**: Dead code and build artifacts directly pollute tooling (e.g., CodeGraph Context indexing), inflate repository size, and create confusion about what code is actively used. This is the foundation all other cleanup depends on.

**Independent Test**: Can be fully tested by verifying that `backend/htmlcov/`, `frontend/coverage/`, `frontend/e2e-report/`, and `frontend/test-results/` are removed from the working tree, and that the duplicate `formatTimeAgo` in `DynamicDropdown.tsx` is replaced with the shared utility import. Dead code scanning should return no results for removed artifacts.

**Acceptance Scenarios**:

1. **Given** the repository contains gitignored build artifact directories (`backend/htmlcov/`, `frontend/coverage/`), **When** a developer runs the cleanup, **Then** those directories are removed from the local working tree and excluded from code indexing tools.
2. **Given** `DynamicDropdown.tsx` defines a local `formatTimeAgo` function, **When** the duplicate is removed, **Then** the component imports and uses the shared `formatTimeAgo` from `@/utils/formatTime` with a `new Date(isoString)` conversion at the call site.
3. **Given** the duplicate function is removed, **When** the frontend test suite runs, **Then** all existing tests pass with zero regressions.

---

### User Story 2 - Annotate and Document Legacy Code Paths (Priority: P1)

As a developer, I want legacy code paths clearly annotated with deprecation timelines and migration tracking so that the team knows what is safe to remove and when.

**Why this priority**: The codebase has 11 legacy markers and 5 TODOs that lack context. Without clear deprecation annotations, legacy code accumulates indefinitely and creates maintenance risk. This story is equal priority to Story 1 because it prevents future debt accumulation.

**Independent Test**: Can be tested by searching for `DEPRECATED(` annotations in affected files and verifying each legacy code path has a documented removal timeline or migration plan.

**Acceptance Scenarios**:

1. **Given** `_ROW_RE_OLD` in `agent_tracking.py` parses the old 4-column format, **When** the deprecation annotation is added, **Then** the code includes a clear comment specifying removal conditions (e.g., "Remove after all tracked issues use 5-column format").
2. **Given** the pipeline legacy path at `pipeline.py` L2075, **When** deprecation markers are added, **Then** each legacy reference includes a `DEPRECATED(vX.Y)` comment with a linked tracking issue.
3. **Given** deprecated fields (`agents`, `execution_mode`) exist in `pipeline.py` and `index.ts`, **When** migration tracking is added, **Then** the system logs encounters of the legacy format to monitor adoption rate.
4. **Given** `old_status` in `StatusUpdateActionData` is superseded by `current_status`/`target_status`, **When** the field is audited, **Then** it is either marked `@deprecated` with removal conditions or removed if no backend code sends it.
5. **Given** `_resetForTesting` is exported from production hooks, **When** `@internal` JSDoc annotations are added, **Then** the function is documented as test-only to prevent external use.
6. **Given** `AITaskProposal` has an inaccurate "Temporary entity" docstring but 28+ usages, **When** the docstring is updated, **Then** it reflects the model's permanent status.
7. **Given** `docs/configuration.md` says "001 through 020" but migrations go to 022, **When** the documentation is updated, **Then** the migration count is accurate and blocking migrations (017, 018, 021) are annotated as historical/removed.
8. **Given** `clearLegacyStorage` exists in `useChatHistory.ts`, **When** the function is audited, **Then** it is either removed (if localStorage is no longer used) or documented with an `@internal` annotation explaining its security purpose.

---

### User Story 3 - Consolidate Duplicate Patterns (DRY) (Priority: P2)

As a developer, I want repeated code patterns extracted into shared utilities so that bug fixes and improvements only need to happen in one place.

**Why this priority**: While not blocking, 18 inline error handlers (14 direct migration candidates) and repeated cache/validation patterns increase maintenance burden and risk of inconsistent behavior. Consolidation improves reliability and reduces code volume.

**Independent Test**: Can be tested by verifying that `handle_service_error` is used in all applicable API endpoints, `cached_fetch` replaces repeated cache patterns, and `require_selected_project` replaces repeated validation checks — with all backend tests passing.

**Acceptance Scenarios**:

1. **Given** 18 inline `except Exception as e: logger.error(...)` patterns exist across API endpoints (14 direct migration candidates, 4 intentional skips), **When** the direct candidates are migrated to `handle_service_error`, **Then** error handling is consistent across all endpoints (excluding intentionally different catches like WebSocket handlers).
2. **Given** three API modules repeat the cache check/get/set pattern, **When** `cached_fetch` is created in `backend/src/services/cache.py`, **Then** all three call sites use the shared wrapper with equivalent behavior.
3. **Given** 5+ places repeat `if not session.selected_project_id: raise ValidationError(...)`, **When** `require_selected_project` is added to `backend/src/dependencies.py`, **Then** all validation sites use the shared helper.
4. **Given** `pipeline_source` field may be unused by the frontend, **When** end-to-end usage is verified, **Then** the field is either confirmed consumed or marked `@deprecated`.
5. **Given** file upload storage in `chat.py` is marked "for now", **When** the temporary storage is addressed, **Then** it either has documented lifecycle management (cleanup on restart or TTL) or a migration plan to cloud storage.

---

### User Story 4 - Reduce Function Complexity (Priority: P2)

As a developer, I want high-complexity functions decomposed into smaller, focused sub-functions so that the code is easier to understand, test, and maintain.

**Why this priority**: Seven functions have cyclomatic complexity (CC) greater than 50, with the highest at CC=123. These are maintenance hotspots that are difficult to review, test, and extend. Decomposition is essential but depends on earlier cleanup (Stories 1–3) being complete to avoid conflicts.

**Independent Test**: Can be tested by measuring cyclomatic complexity of each refactored function and verifying the target CC is met, with all unit and integration tests passing.

**Acceptance Scenarios**:

1. **Given** `post_agent_outputs_from_pr` has CC=123, **When** it is decomposed into sub-functions (PR detection, file extraction, comment posting, tracking update), **Then** each extracted function has CC < 30 and all tests pass.
2. **Given** `assign_agent_for_status` has CC=91, **When** it is decomposed (agent resolution, branch creation, Copilot assignment, tracking update), **Then** each extracted function has CC < 25 and all tests pass.
3. **Given** `recover_stalled_issues` has CC=72, **When** it is decomposed (stall detection, cooldown check, reassignment attempt, state reconciliation), **Then** each extracted function has CC < 20 and all tests pass.
4. **Given** `GlobalSettings` component has CC=96, **When** sub-components are extracted for each settings section with custom hooks for state management, **Then** each sub-component has CC < 30 and all frontend tests pass.
5. **Given** `LoginPage` component has CC=90, **When** authentication flow is extracted into a custom hook and OAuth callback handling is separated, **Then** each piece has CC < 30 and all frontend tests pass.

---

### User Story 5 - Plan Future Architectural Migrations (Priority: P3)

As a technical lead, I want migration plans documented for singleton removal and in-memory store migration so that these larger refactors can be scoped and executed in dedicated specs.

**Why this priority**: Singleton patterns (17+ import sites) and in-memory stores (15+ code paths) are architectural concerns that require separate, dedicated specifications. This story only produces planning artifacts, not implementation.

**Independent Test**: Can be tested by verifying that migration plans exist with complete checklists of affected files and import sites, and that backward-compat aliases and deprecated settings are audited with clear removal criteria.

**Acceptance Scenarios**:

1. **Given** `github_projects_service` uses a module-level singleton with 17+ direct imports, **When** the migration plan is created, **Then** it includes a provider pattern design and a checklist of all import sites that need migration.
2. **Given** in-memory stores (`_messages`, `_proposals`, `_recommendations`) in `chat.py` are lost on restart, **When** the migration plan is created, **Then** it references existing migration 012 tables and lists all ~15 code paths needing transaction management.
3. **Given** backward-compat aliases exist in `chat.py`, `issue_generation.py`, and `auth.py`, **When** consumer audit is complete, **Then** unused aliases are identified for removal.
4. **Given** `agent_pipeline_mappings` is a legacy settings field, **When** the deprecation audit is complete, **Then** the field's usage status is documented with removal criteria.
5. **Given** all phases are complete, **When** the final cleanup sweep runs, **Then** orphaned imports are removed, all tests pass, and project structure documentation is updated if needed.

---

### Edge Cases

- What happens when removing a build artifact directory that does not exist on a given developer's machine? The cleanup should be idempotent — skip directories that are already absent.
- How does the system handle a legacy format record encountered after the deprecation deadline? Migration tracking logs should capture these for monitoring, and the system should continue to function via the fallback path until explicitly removed.
- What if decomposing a high-complexity function changes the public API surface? Extracted sub-functions should remain internal (private/unexported) to preserve the existing API contract.
- What if `clearLegacyStorage` is called but localStorage is already empty? The function should be a no-op in that case — no errors thrown.
- What if a backward-compat alias is still consumed by an external integration not visible in the codebase? The audit should check API documentation and any known external consumers before removal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST remove gitignored build artifact directories (`backend/htmlcov/`, `frontend/coverage/`, `frontend/e2e-report/`, `frontend/test-results/`) from the working tree without affecting git-tracked files.
- **FR-002**: System MUST replace the local `formatTimeAgo` function in `DynamicDropdown.tsx` with an import from the shared `@/utils/formatTime` utility, adapting for the string-to-Date signature difference at the call site.
- **FR-003**: System MUST audit `clearLegacyStorage` in `useChatHistory.ts` and either remove it (if localStorage is no longer used) or annotate it with `@internal` documentation explaining its security purpose.
- **FR-004**: System MUST update the `AITaskProposal` docstring in `recommendation.py` to accurately reflect its permanent status (remove "Temporary entity" language).
- **FR-005**: System MUST update `docs/configuration.md` to reflect the correct migration count (022) and annotate blocking migrations (017, 018, 021) as historical/removed.
- **FR-006**: System MUST add deprecation timeline annotations to legacy code paths including `_ROW_RE_OLD` in `agent_tracking.py`, the LEGACY path in `pipeline.py`, and deprecated fields in `pipeline.py` and `index.ts`.
- **FR-007**: System MUST add migration tracking (logging) when legacy pipeline format is encountered to monitor adoption rate of the new format.
- **FR-008**: System MUST mark `old_status` in `StatusUpdateActionData` as `@deprecated` or remove it after verifying no backend code sends the field.
- **FR-009**: System MUST add `@internal` JSDoc annotations to `_resetForTesting` exports in production hooks.
- **FR-010**: System MUST migrate 14 inline error handling patterns across 6 API files to use the shared `handle_service_error` utility, excluding 4 intentionally different catches (WebSocket, non-fatal warnings).
- **FR-011**: System MUST create a `cached_fetch` generic wrapper in `backend/src/services/cache.py` that encapsulates the repeated cache check/get/set pattern.
- **FR-012**: System MUST create a `require_selected_project` validation helper in `backend/src/dependencies.py` that replaces 5+ repeated validation checks.
- **FR-013**: System MUST verify `pipeline_source` field usage end-to-end and either confirm frontend consumption or mark it `@deprecated`.
- **FR-014**: System MUST address temporary file upload storage in `chat.py` by adding lifecycle management (cleanup on restart or TTL) or documenting it as intentional for self-hosted deployments.
- **FR-015**: System MUST decompose `post_agent_outputs_from_pr` (CC=123) into sub-functions each with CC < 30.
- **FR-016**: System MUST decompose `assign_agent_for_status` (CC=91) into sub-functions each with CC < 25.
- **FR-017**: System MUST decompose `recover_stalled_issues` (CC=72) into sub-functions each with CC < 20.
- **FR-018**: System MUST decompose `GlobalSettings` component (CC=96) into sub-components each with CC < 30.
- **FR-019**: System MUST decompose `LoginPage` component (CC=90) into sub-components each with CC < 30.
- **FR-020**: System MUST create migration planning documents for singleton removal (`github_projects_service`) and in-memory store migration (`chat.py` dictionaries to SQLite), listing all affected files and code paths.
- **FR-021**: System MUST audit backward-compat aliases in `chat.py`, `issue_generation.py`, and `auth.py` and remove any that have no remaining consumers.
- **FR-022**: System MUST verify `agent_pipeline_mappings` deprecation status and remove UI editing and auto-backfill code if no project uses the old format.
- **FR-023**: System MUST run a final cleanup sweep removing orphaned imports and updating project structure documentation.

### Key Entities

- **Build Artifact**: Gitignored output directory (coverage reports, test results) that should not persist in the working tree or be indexed by code analysis tools.
- **Legacy Code Path**: A code branch, regex pattern, or data format maintained for backward compatibility with older data or workflows, requiring deprecation annotation and migration tracking.
- **Shared Utility**: A reusable function (`handle_service_error`, `cached_fetch`, `require_selected_project`) extracted from duplicated inline patterns to enforce DRY principles.
- **Complexity Hotspot**: A function or component with cyclomatic complexity exceeding project thresholds (CC > 40), requiring decomposition into focused sub-units.
- **Migration Plan**: A planning artifact documenting the scope, affected files, and migration strategy for an architectural change (singleton removal, in-memory to persistent storage) to be executed in a separate specification.
- **Deprecation Annotation**: A structured comment (`DEPRECATED(vX.Y)`, `@deprecated`, `@internal`) that documents removal conditions, timeline, and tracking issue for legacy code.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All build artifact directories are removed and code analysis tools index only source files — verified by dead code scan returning zero results for coverage report functions.
- **SC-002**: Zero duplicate utility functions exist in the codebase — the local `formatTimeAgo` in `DynamicDropdown.tsx` is eliminated.
- **SC-003**: 100% of legacy code paths (11 markers) have deprecation annotations with explicit removal conditions or tracking issues.
- **SC-004**: All 5 TODO items are resolved — either addressed, annotated with timeline, or converted to tracked issues.
- **SC-005**: Error handling consolidation reduces inline catch patterns from 14 to 0 across the 6 targeted API files (excluding 4 intentional exceptions).
- **SC-006**: All 5 high-complexity functions are decomposed to meet their target cyclomatic complexity (CC < 30 for most, CC < 25 for `assign_agent_for_status`, CC < 20 for `recover_stalled_issues`).
- **SC-007**: All existing unit tests pass after each phase — zero test regressions across backend and frontend suites.
- **SC-008**: All existing type checks pass — zero errors from backend and frontend type checkers.
- **SC-009**: Migration plans for singleton removal and in-memory store migration include complete file inventories (17+ and 15+ affected paths respectively).
- **SC-010**: End-to-end smoke tests pass after all phases — pipeline creation, agent assignment, and chat workflows function correctly.

## Assumptions

- The codebase baseline of 465 files, 4653 functions, and 803 classes (from CGC) is accurate at the time of execution.
- Build artifact directories (`htmlcov/`, `coverage/`, etc.) are gitignored and safe to delete without affecting any developer's committed work.
- The `handle_service_error` utility already exists and follows an established pattern that can be adopted by the 14 inline error handlers (4 additional catches are intentionally different).
- Migration 012 tables (`chat_messages`, `chat_proposals`, `chat_recommendations`) already exist in the database schema and can be referenced in the migration plan.
- Singleton and in-memory store migrations are explicitly deferred to separate specifications — only planning artifacts are produced in this feature.
- WebSocket handlers and non-fatal warning catches are intentionally different from the standard error handling pattern and should be preserved as-is.
- The "blocking" migrations (017, 018, 021) have already been fully removed from the codebase and only need documentation annotation.
- CGC (CodeGraph Context) checkpoints are used for validation after every 5 steps, not as a runtime production dependency.
- The project follows a phased execution model where each phase can be independently verified before proceeding.
