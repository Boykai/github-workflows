# Feature Specification: Fix Playwright Auth Setup, Mutation-Testing CI Noise, and Deprecated Chores Hook Usage

**Feature Branch**: `001-fix-ci-auth-chores`  
**Created**: 2026-03-28  
**Status**: Draft  
**Input**: User description: "Fix Playwright auth setup, mutation-testing CI noise, and deprecated chores hook usage"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Isolate Playwright Auth Setup from Default Test Runs (Priority: P1)

As a maintainer running end-to-end tests, I want the manual authentication setup file to be excluded from default test discovery so that standard test runs do not fail or hang waiting for interactive OAuth login.

**Why this priority**: The auth setup file being discovered by default Playwright runs causes misleading test failures and blocks CI. Fixing this restores CI reliability for the 64 existing E2E tests and is the highest-impact change.

**Independent Test**: Can be fully tested by running `npx playwright test --list` and confirming `save-auth-state.ts` does not appear in the test listing, then running `npx playwright test` and confirming all 64 tests still pass.

**Acceptance Scenarios**:

1. **Given** the Playwright configuration has `testIgnore` set to exclude `save-auth-state.ts`, **When** a developer runs `npx playwright test` without any environment variables, **Then** `save-auth-state.ts` is not listed or executed and all 64 existing E2E tests pass.
2. **Given** the environment variable `AUTH_SETUP=1` is set, **When** a developer runs the dedicated auth setup project, **Then** `save-auth-state.ts` executes and saves browser storage state for reuse by downstream projects.
3. **Given** the Playwright configuration defines a performance project that depends on the auth setup project, **When** the auth setup project completes successfully, **Then** the performance project runs using the saved authentication state.
4. **Given** the environment variable `AUTH_SETUP` is not set (or set to any value other than `1`), **When** a developer runs `npx playwright test`, **Then** the auth setup project is skipped entirely and no auth-related test appears in the run.

---

### User Story 2 - Eliminate Misleading Mutation-Testing CI Failures (Priority: P1)

As a maintainer monitoring CI dashboards, I want mutation-testing jobs to appear green even when mutants survive so that surviving mutants are treated as informational findings rather than CI failures.

**Why this priority**: Mutation testing exit code 1 (surviving mutants) currently produces misleading red annotations in CI, making it harder to spot real failures. This is equal priority with the Playwright fix since both directly affect CI reliability.

**Independent Test**: Can be fully tested by triggering the mutation-testing workflow and confirming the job completes with a green status even when the mutation tool reports surviving mutants.

**Acceptance Scenarios**:

1. **Given** the mutation-testing workflow is configured with job-level continue-on-error, **When** the mutation runner exits with code 1 due to surviving mutants, **Then** the CI job status shows as green (success).
2. **Given** the frontend mutation configuration uses concurrency 4 and timeout factor 2.5, **When** mutation tests run on CI, **Then** they complete within the allocated CI time budget without timing out.
3. **Given** only one mutation-testing workflow file exists, **When** a maintainer reviews the repository workflows, **Then** they find a single `mutation-testing.yml` and no `mutation.yml`.
4. **Given** the consolidated workflow uses Node 22 and 30-day artifact retention, **When** mutation reports are generated, **Then** the artifacts are available for download for 30 days after the run.

---

### User Story 3 - Migrate Deprecated Chores Hook to Paginated Version (Priority: P2)

As a maintainer, I want all consumers of the deprecated `useChoresList` hook migrated to `useChoresListPaginated` so that the deprecated export can be safely removed and the codebase stays consistent with the preferred pagination pattern.

**Why this priority**: This is a code hygiene improvement that does not affect CI reliability but reduces technical debt. The deprecated hook still works, so this is lower urgency than the CI-impacting changes.

**Independent Test**: Can be fully tested by searching the codebase for any remaining references to `useChoresList` (the non-paginated version) and confirming zero results, then running the full frontend test suite to verify no regressions.

**Acceptance Scenarios**:

1. **Given** `ChoresPage.tsx` is updated to use `useChoresListPaginated`, **When** a user navigates to the Chores page, **Then** the page renders and behaves identically to before the migration (same data displayed, same loading states).
2. **Given** `useCommandPalette.ts` is updated to use `useChoresListPaginated`, **When** a user opens the command palette (Ctrl+K / Cmd+K), **Then** chore items appear in the palette exactly as before.
3. **Given** the deprecated `useChoresList` export is removed from `useChores.ts`, **When** a developer attempts to import `useChoresList`, **Then** the import fails at compile time (the export no longer exists).
4. **Given** all migrations are complete, **When** the full frontend test suite runs, **Then** all existing tests pass without modification.

---

### User Story 4 - Document Upstream Vitest Deprecation Warning (Priority: P3)

As a maintainer reading CI logs, I want a comment in the Vitest configuration explaining that the `vitest/suite` deprecation warning comes from an upstream dependency so that contributors do not waste time trying to fix it in project code.

**Why this priority**: This is a documentation-only change with no functional impact. It prevents wasted investigation time but is the lowest priority since the warning is harmless.

**Independent Test**: Can be fully tested by opening `vitest.config.ts` and confirming the explanatory comment is present and accurately references the upstream source.

**Acceptance Scenarios**:

1. **Given** `vitest.config.ts` contains a comment about the `vitest/suite` deprecation, **When** a contributor sees the warning in test output, **Then** the comment directs them to the upstream `@fast-check/vitest@0.3.0` package as the source.

---

### Edge Cases

- What happens when `AUTH_SETUP=1` is set but no browser is available (headless CI)? The auth setup file is designed for headed interactive use; in headless environments the OAuth redirect will fail gracefully and the test will time out with a clear error.
- What happens when `useChoresListPaginated` is called where `useChoresList` was used and the consumer only reads the first page? The paginated hook returns the first page of results by default, which matches the previous behavior of returning all chores (assuming the first page size covers normal chore counts).
- What happens if the old `mutation.yml` workflow file is not deleted? Two mutation workflows would run on different schedules, wasting CI resources and creating confusion about which results to trust.
- What happens if a new contributor adds a direct import of `useChoresList` after the migration? The import will fail at compile time since the export is removed, providing immediate feedback.

## Requirements *(mandatory)*

### Functional Requirements

#### Playwright Auth Setup Isolation

- **FR-001**: System MUST add `save-auth-state.ts` to the Playwright `testIgnore` configuration so it is excluded from default test discovery by `npx playwright test`.
- **FR-002**: System MUST define a dedicated Playwright project (e.g., "auth-setup") that runs `save-auth-state.ts` only when the `AUTH_SETUP` environment variable is set to `1`.
- **FR-003**: System MUST configure the Playwright performance project to depend on the auth-setup project so that authentication state is established before performance tests execute.
- **FR-004**: System MUST preserve the existing CI-safe mocked authentication used by the 14 standard E2E specs; those tests must continue to pass without the `AUTH_SETUP` variable.

#### Mutation-Testing CI Configuration

- **FR-005**: System MUST update the frontend mutation testing configuration to use concurrency 4 (up from 2) and timeout factor 2.5 to accommodate CI runtime overhead.
- **FR-006**: System MUST configure `mutation-testing.yml` with job-level `continue-on-error: true` so that surviving mutants do not produce red CI annotations.
- **FR-007**: System MUST consolidate the two duplicate mutation workflows into a single `mutation-testing.yml` file using Node 22 and 30-day artifact retention.
- **FR-008**: System MUST delete the old `mutation.yml` workflow file to eliminate the duplicate.

#### Deprecated Hook Migration

- **FR-009**: System MUST replace the `useChoresList` import and call in `ChoresPage.tsx` with `useChoresListPaginated`, adapting data access to use the paginated response shape.
- **FR-010**: System MUST replace the `useChoresList` import and call in `useCommandPalette.ts` with `useChoresListPaginated`, adapting data access to use the paginated response shape.
- **FR-011**: System MUST remove the deprecated `useChoresList` function and its export from `useChores.ts`.

#### Documentation

- **FR-012**: System SHOULD add a comment in `vitest.config.ts` documenting that the `vitest/suite` deprecation warning originates from `@fast-check/vitest@0.3.0` and is not fixable in project code.

### Assumptions

- All 3,582 backend tests, 1,364 frontend tests, and 64 E2E tests currently pass and will continue to pass after these changes.
- Mutation testing exit code 1 is the expected result when surviving mutants exist; this is informational, not a failure.
- No dead code exists that references `useChoresList` beyond the two identified consumers (`ChoresPage.tsx` and `useCommandPalette.ts`).
- The `@fast-check/vitest` deprecation warning is an upstream issue in the latest package version (0.3.0) and cannot be resolved by changes in this project.
- The paginated hook (`useChoresListPaginated`) returns data in a shape that includes at minimum the first page of results, which is sufficient for the command palette and chores page initial render.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running `npx playwright test --list` shows zero references to `save-auth-state.ts` in the test listing.
- **SC-002**: All 64 E2E tests pass when run via `npx playwright test` without `AUTH_SETUP` set.
- **SC-003**: The auth setup file executes successfully when `AUTH_SETUP=1` is set and a headed browser is available.
- **SC-004**: Mutation-testing CI jobs display green status even when surviving mutants cause the tool to exit with code 1.
- **SC-005**: Only one mutation workflow file (`mutation-testing.yml`) exists in `.github/workflows/`; no `mutation.yml` is present.
- **SC-006**: Frontend mutation tests complete within CI time limits using concurrency 4 and timeout factor 2.5.
- **SC-007**: Zero references to the deprecated `useChoresList` function exist anywhere in the codebase after migration.
- **SC-008**: All 1,364 frontend unit tests pass after the hook migration without test modifications.
- **SC-009**: All 3,582 backend tests remain green (no regressions from workflow changes).
- **SC-010**: The `vitest.config.ts` file contains a comment referencing `@fast-check/vitest@0.3.0` as the source of the deprecation warning.
