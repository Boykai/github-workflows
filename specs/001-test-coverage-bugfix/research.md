# Research: Improve Test Coverage to 85% and Fix Discovered Bugs

**Feature**: `001-test-coverage-bugfix` | **Date**: 2026-02-20
**Purpose**: Resolve all unknowns from Technical Context and establish best practices for the testing effort.

## Research Tasks

### R-001: Current Coverage Baseline

**Decision**: Run `vitest run --coverage` (frontend) and `pytest --cov=src --cov-report=term-missing` (backend) to establish the starting baseline before writing any new tests.

**Rationale**: The spec assumes coverage is below 85%. Measuring the actual baseline is necessary to prioritize which modules need the most attention and to provide the before/after comparison required by FR-011 and SC-005.

**Alternatives Considered**:
- Estimating coverage from test file count — rejected because file count does not correlate with branch or statement coverage
- Using only line coverage — rejected because branch coverage is a better indicator of test thoroughness; both should be measured

### R-002: Frontend Testing Strategy (Vitest + React Testing Library)

**Decision**: Use Vitest with `@vitest/coverage-v8` for coverage and `@testing-library/react` with `happy-dom` environment for component testing. Co-locate test files with source files using the `*.test.tsx` / `*.test.ts` naming convention (matching existing pattern in `hooks/`).

**Rationale**: The project already has Vitest 4, @testing-library/react 16, and happy-dom configured in `vitest.config.ts`. Three existing test files in `hooks/` demonstrate co-located test placement. Reusing the existing setup avoids configuration churn and maintains consistency.

**Alternatives Considered**:
- Switching to Jest — rejected because Vitest is already configured and integrated with the Vite build toolchain
- Moving tests to a separate `__tests__/` directory — rejected because existing convention co-locates tests with source in `hooks/`; extending this to `components/` and `services/` maintains consistency
- Using jsdom instead of happy-dom — rejected because happy-dom is already configured in `vitest.config.ts` and is faster; jsdom is listed as a devDependency but not actively used

### R-003: Backend Testing Strategy (PyTest)

**Decision**: Use PyTest with `pytest-cov` for coverage and `pytest-asyncio` for async endpoint testing. Place tests in `backend/tests/unit/` for unit tests and `backend/tests/integration/` for integration tests, following the existing directory structure.

**Rationale**: The backend already has a mature test structure with 11 unit test files, 1 integration test file, a `conftest.py` with shared fixtures, and `pytest-asyncio` configured in `auto` mode. Extending this setup ensures consistency.

**Alternatives Considered**:
- Using unittest instead of PyTest — rejected because PyTest is already configured and provides better fixture support and async testing
- Co-locating tests with source — rejected because the existing convention uses a separate `tests/` directory

### R-004: Coverage Exclusion Patterns

**Decision**: Exclude the following from coverage calculations:
- Frontend: `main.tsx` (entry point/bootstrap), `vite-env.d.ts` (type declarations), `types/index.ts` (pure type definitions), E2E tests
- Backend: `__init__.py` files, `migrations/`, `prompts/` (static template strings), `main.py` (app bootstrap/startup), configuration files

**Rationale**: These files contain bootstrap code, type declarations, or static content that cannot be meaningfully unit-tested. Excluding them prevents distorting coverage metrics and aligns with FR-006 (tests must validate real behaviors, not inflate coverage).

**Alternatives Considered**:
- Including all files with no exclusions — rejected because it would require writing meaningless tests for type declarations and bootstrap code, violating FR-006
- Excluding more files — rejected because being too aggressive with exclusions could hide important untested logic

### R-005: Test Structure Best Practices (AAA Pattern)

**Decision**: All new tests must follow the Arrange-Act-Assert pattern:
- **Arrange**: Set up test fixtures, mocks, and preconditions
- **Act**: Execute the function or component behavior under test
- **Assert**: Verify the expected outcome

Each test must be independent (no shared mutable state) and deterministic (same result every run).

**Rationale**: Required by FR-003, FR-004, and FR-005. The AAA pattern is the industry standard for test readability and maintainability. Existing tests in the repo already follow this pattern informally.

**Alternatives Considered**:
- BDD-style (Given-When-Then) test structure — rejected because the spec explicitly mandates AAA and existing tests use AAA implicitly
- Property-based testing — out of scope for this effort; could be added later for data-intensive modules

### R-006: Bug Fix Workflow

**Decision**: When a new test exposes a bug:
1. Write the failing test first (Red)
2. Fix the bug in the source code (Green)
3. Commit the bug fix separately from test additions with a clear commit message (e.g., `fix: [module] description of bug`)

**Rationale**: Required by FR-007 and FR-008. Separating bug fix commits from test commits enables clear code review and traceability. The Red-Green approach ensures each bug has a corresponding regression test.

**Alternatives Considered**:
- Fixing bugs in a separate branch — rejected because FR-007 mandates same-branch fixes
- Combining bug fix and test commits — rejected because FR-008 requires distinguishable commits

### R-007: Frontend Modules Prioritization

**Decision**: Prioritize frontend testing in this order based on complexity and user impact:
1. **Hooks** (useAuth, useProjects, useProjectBoard, useChat, useSettings, useWorkflow, useAgentConfig, useAppTheme, useRealTimeSync) — core business logic
2. **Services** (api.ts) — API communication layer
3. **Components** (board/, chat/, common/, auth/, settings/, sidebar/) — UI rendering
4. **Pages** (ProjectBoardPage, SettingsPage) — page-level composition
5. **Utilities** (colorUtils.ts) — pure functions

**Rationale**: Hooks contain the majority of frontend business logic and state management. Services handle API communication. Components are more straightforward to test but numerous. This prioritization ensures the highest-value code is tested first.

**Alternatives Considered**:
- Testing components first — rejected because hooks drive component behavior; testing hooks first provides foundation
- Testing only hooks and services — rejected because components may contain rendering logic and conditional branches that need coverage

### R-008: Backend Modules Prioritization

**Decision**: Prioritize backend testing in this order based on coverage gaps:
1. **Services without tests** — any service file in `backend/src/services/` without a corresponding test file
2. **API routes without tests** — any route file in `backend/src/api/` without a corresponding test file
3. **Models** — Pydantic model validation and edge cases
4. **Existing tests with low coverage** — expand existing test files to cover untested branches
5. **Config and exceptions** — utility modules

**Rationale**: Services contain the core business logic. API routes define the contract surface. Models enforce data integrity. Filling these gaps first maximizes coverage improvement per test written.

**Alternatives Considered**:
- Writing integration tests first — rejected because unit tests provide faster feedback and more granular coverage data
- Testing only untested files — rejected because existing test files may have significant branch coverage gaps

## Summary

All NEEDS CLARIFICATION items have been resolved. The testing strategy reuses existing frameworks and conventions. No new dependencies are required. The prioritization focuses on high-value, high-impact modules first for both frontend and backend.
