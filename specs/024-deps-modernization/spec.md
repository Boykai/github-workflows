# Feature Specification: Full Dependency & Pattern Modernization

**Feature Branch**: `024-deps-modernization`  
**Created**: 2026-03-06  
**Status**: Draft  
**Input**: User description: "Update all packages to current most up-to-date versions, update entire codebase. Update code to use most modern patterns, functions, and best practices."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Backend Dependency & Runtime Upgrade (Priority: P1)

As a developer, I want all backend Python dependencies updated to their latest stable versions and the Python runtime upgraded to 3.13 so that the backend benefits from security patches, performance improvements, and access to modern language features.

This includes upgrading FastAPI, Uvicorn, Pydantic, httpx, tenacity, websockets, aiosqlite, openai, and all dev tooling (pytest, ruff, pyright). Unused dependencies (python-jose) are removed. The Dockerfile base image moves from Python 3.12 to 3.13. Ruff lint rules are expanded to enforce modern Python idioms (FURB, PTH, PERF, RUF rule sets).

**Why this priority**: The backend is the core of the system — all API endpoints, AI agent orchestration, and data persistence flow through it. Keeping it on current, supported versions is the highest-priority maintenance activity. Removing unused dependencies reduces attack surface.

**Independent Test**: Can be fully tested by installing backend dependencies, running the full pytest suite, running ruff and pyright checks, and verifying the Docker image builds and starts successfully with a passing health check.

**Acceptance Scenarios**:

1. **Given** the backend pyproject.toml with updated dependency versions, **When** `pip install -e ".[dev]"` is run in a clean virtual environment, **Then** all packages install without conflicts and no deprecation warnings are emitted at import time.
2. **Given** the updated backend, **When** the full pytest suite is executed, **Then** all existing tests pass without modification (or with minimal compatibility adjustments documented in commit messages).
3. **Given** the updated ruff configuration with expanded rule sets (FURB, PTH, PERF, RUF), **When** `ruff check src/` is run, **Then** no errors are reported (auto-fixable issues have been resolved).
4. **Given** the updated Dockerfile with Python 3.13-slim, **When** `docker build` is run, **Then** the image builds successfully and the health check endpoint responds within 10 seconds of container start.
5. **Given** the dependency list, **When** audited for unused packages, **Then** python-jose is no longer present in pyproject.toml since it is not imported anywhere in the codebase.

---

### User Story 2 - Frontend Dependency & Runtime Upgrade (Priority: P1)

As a developer, I want all frontend JavaScript/TypeScript dependencies updated to their latest stable versions and the Node.js runtime upgraded to 22 LTS so that the frontend benefits from security patches, performance improvements, and modern toolchain features.

This includes upgrading React 18 to 19, Vite 5 to 6, Tailwind CSS 3 to 4, TypeScript, ESLint, Vitest, Playwright, TanStack Query, dnd-kit, lucide-react, and all dev tooling. Unused dependencies (socket.io-client) are removed. The Dockerfile base image moves from Node 20 to Node 22.

**Why this priority**: The frontend directly affects user experience. React 19, Tailwind v4, and Vite 6 represent the current generation of the frontend toolchain. Staying current prevents accumulation of migration debt. Removing socket.io-client (unused — native WebSocket is used) reduces bundle size.

**Independent Test**: Can be fully tested by running `npm install`, `npm run type-check`, `npm run lint`, `npm run test`, and `npm run build` — all must succeed. The Docker image must build and serve the app via nginx.

**Acceptance Scenarios**:

1. **Given** the updated package.json, **When** `npm install` is run in a clean node_modules, **Then** all packages install without peer dependency conflicts.
2. **Given** the React 19 upgrade, **When** the application renders in a browser, **Then** all existing UI components display and function identically to their pre-upgrade behavior.
3. **Given** the Tailwind v4 migration, **When** the application loads, **Then** all styles (light mode, dark mode, custom theme colors, animations) render correctly with no visual regressions.
4. **Given** the Vite 6 upgrade, **When** `npm run build` is executed, **Then** the production build completes successfully with source maps and outputs to the dist/ directory.
5. **Given** the updated dependencies, **When** `npm run test` is executed, **Then** all existing unit tests pass.
6. **Given** the dependency list, **When** audited for unused packages, **Then** socket.io-client is no longer present since the codebase uses native WebSocket.

---

### User Story 3 - Frontend Code Pattern Modernization (Priority: P2)

As a developer, I want frontend code patterns updated to leverage React 19 and Tailwind v4 best practices so that the codebase uses modern idioms and reduces unnecessary boilerplate.

This includes removing `forwardRef` wrappers from UI components (React 19 treats `ref` as a regular prop), migrating Tailwind configuration from JavaScript config files to CSS-first `@theme` blocks, replacing `@tailwind` directives with `@import "tailwindcss"`, and removing the now-unnecessary PostCSS config and autoprefixer dependency.

**Why this priority**: These code changes are a direct consequence of the dependency upgrades in P1. While the app may function without them, leaving deprecated patterns creates inconsistency and makes future maintenance harder. They are lower priority than getting the dependencies installed and working.

**Independent Test**: Can be verified by confirming that no `forwardRef` calls exist in UI components, that `tailwind.config.js` and `postcss.config.js` are deleted, and that the CSS-first Tailwind configuration in `index.css` produces identical styling output.

**Acceptance Scenarios**:

1. **Given** the React 19 upgrade is complete, **When** shadcn/ui components (button, input, card) are inspected, **Then** none use `React.forwardRef` — `ref` is accepted as a regular prop.
2. **Given** the Tailwind v4 migration, **When** the project source is inspected, **Then** `tailwind.config.js` and `postcss.config.js` no longer exist.
3. **Given** the Tailwind v4 CSS-first configuration in `index.css`, **When** the app renders, **Then** all theme colors, fonts, shadows, border-radii, and animations match the previous Tailwind v3 output.
4. **Given** the Vite config update, **When** inspected, **Then** the `@tailwindcss/vite` plugin is registered and no legacy PostCSS-based Tailwind integration remains.

---

### User Story 4 - Backend Code Pattern Modernization (Priority: P2)

As a developer, I want backend code patterns updated to comply with expanded ruff lint rules and any breaking API changes in upgraded dependencies (tenacity v9, websockets v14) so that the codebase uses modern Python idioms throughout.

**Why this priority**: Like P2 frontend patterns, these changes are a direct consequence of P1 upgrades. The backend already uses modern FastAPI (lifespan), Pydantic v2 (model_config, field_validator), and asyncio (get_running_loop) patterns. Remaining work is limited to compatibility adjustments for tenacity 9.x and websockets 14.x API changes, plus applying auto-fixes from expanded ruff rules.

**Independent Test**: Can be verified by running `ruff check src/` (no errors), `pyright src/` (no errors), and `pytest` (all tests pass) after applying the modernization changes.

**Acceptance Scenarios**:

1. **Given** tenacity upgraded to v9, **When** all retry-decorated functions in the services layer are executed, **Then** retry behavior is identical to pre-upgrade (exponential backoff, max attempts preserved).
2. **Given** websockets upgraded to v14, **When** the Signal WebSocket listener connects and receives messages, **Then** connection handling and message parsing work identically to pre-upgrade.
3. **Given** expanded ruff rules (FURB, PTH, PERF, RUF), **When** `ruff check src/` is run, **Then** zero violations are reported.

---

### User Story 5 - Infrastructure Verification (Priority: P3)

As a developer, I want the Docker Compose stack to build and run successfully with all upgraded components so that the full system can be deployed with confidence.

**Why this priority**: This is an integration verification that depends on all previous stories being complete. It validates that the backend and frontend work together in containerized deployment.

**Independent Test**: Can be verified by running `docker compose build` followed by `docker compose up` and confirming both services pass health checks and can communicate.

**Acceptance Scenarios**:

1. **Given** updated Dockerfiles (Python 3.13, Node 22), **When** `docker compose build` is executed, **Then** both backend and frontend images build without errors.
2. **Given** the built containers, **When** `docker compose up` is executed, **Then** both services start, pass health checks, and the frontend can reach the backend API through the nginx proxy.

---

### Edge Cases

- What happens when a dependency has a breaking change that cascades through multiple service files? Each breaking dependency change (tenacity v9, websockets v14, React 19 ref changes, Tailwind v4 config migration) is handled as an explicit sub-task with its own verification.
- What happens when a Tailwind v3 utility class is renamed or removed in v4? All component files are audited for deprecated class names during the Tailwind migration step.
- What happens when a shadcn/ui component relies on `forwardRef` internally? Each shadcn/ui component (button, input, card) is individually updated and its unit test re-run to verify behavior.
- What happens when the expanded ruff rules flag hundreds of violations? `ruff check --fix` is used to auto-fix safe changes first; remaining manual fixes are reviewed individually.
- What happens when the `@dnd-kit` packages have incompatible major version splits? Package versions are verified to be the latest compatible set (core v6, modifiers v9, sortable v10 are already latest at time of writing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend Dockerfile MUST use Python 3.13-slim as its base image.
- **FR-002**: The backend pyproject.toml MUST specify `requires-python = ">=3.12"` and all dependency minimums MUST be updated to latest stable versions as of March 2026.
- **FR-003**: The unused `python-jose[cryptography]` dependency MUST be removed from pyproject.toml.
- **FR-004**: The ruff configuration MUST target Python 3.13 and include FURB, PTH, PERF, and RUF rule sets in addition to existing rules.
- **FR-005**: The pytest-asyncio configuration MUST be compatible with version 0.25+ (including `asyncio_default_fixture_loop_scope` if required).
- **FR-006**: The pyright configuration MUST target Python 3.13.
- **FR-007**: The frontend Dockerfile MUST use Node 22-alpine as its builder base image.
- **FR-008**: The frontend package.json MUST specify React 19, Vite 6, Tailwind CSS 4, and all other dependencies at their latest stable versions as of March 2026.
- **FR-009**: The unused `socket.io-client` dependency MUST be removed from package.json.
- **FR-010**: The Tailwind CSS configuration MUST be migrated from JavaScript config files (`tailwind.config.js`, `postcss.config.js`) to CSS-first configuration using `@import "tailwindcss"` and `@theme` blocks in `index.css`.
- **FR-011**: The `autoprefixer` and `tailwindcss-animate` dev dependencies MUST be removed (functionality is built into Tailwind v4).
- **FR-012**: The Vite configuration MUST use the `@tailwindcss/vite` plugin instead of PostCSS-based Tailwind integration.
- **FR-013**: All shadcn/ui components MUST be updated to remove `React.forwardRef` wrappers and accept `ref` as a regular prop (React 19 pattern).
- **FR-014**: The `components.json` (shadcn config) MUST be updated for Tailwind v4 compatibility.
- **FR-015**: All existing backend tests MUST pass after dependency updates.
- **FR-016**: All existing frontend unit tests MUST pass after dependency updates.
- **FR-017**: The frontend production build (`npm run build`) MUST complete successfully.
- **FR-018**: Both Docker images MUST build successfully and pass health checks.
- **FR-019**: Backend code MUST pass `ruff check` with the expanded rule set (zero violations).
- **FR-020**: Backend code MUST pass `pyright` type checking with no errors.
- **FR-021**: Frontend code MUST pass `tsc --noEmit` type checking with no errors.
- **FR-022**: Frontend code MUST pass ESLint with no errors.

## Scope Boundaries

### In Scope

- Updating all dependency versions in pyproject.toml and package.json to latest stable releases
- Upgrading runtime environments (Python 3.12→3.13, Node 20→22)
- Migrating Tailwind CSS v3 to v4 (CSS-first configuration)
- Upgrading React 18 to 19 (removing forwardRef boilerplate)
- Upgrading Vite 5 to 6
- Removing unused dependencies (python-jose, socket.io-client)
- Expanding ruff lint rules and applying auto-fixes
- Updating Dockerfiles and verifying Docker Compose builds
- Minimal code changes required for compatibility with new dependency versions

### Out of Scope

- Architectural refactoring (no changes to service layer, state management, or routing patterns)
- Adding new features or capabilities
- Migrating state management (TanStack Query is already modern and appropriate)
- Rewriting or restructuring existing components beyond what's required for compatibility
- Database schema changes
- Adding new dependencies not required for upgrading existing ones
- Performance optimization beyond what comes naturally from updated dependencies
- Migrating from class-based to functional patterns (already functional throughout)

## Assumptions

- All target dependency versions are released and stable as of March 2026
- The `github-copilot-sdk` and `azure-ai-inference` packages maintain backward compatibility with their current API surface (these are vendor-specific SDKs with less predictable release cycles)
- The `@dnd-kit` package versions (core v6, modifiers v9, sortable v10) represent the latest compatible set — no unified major version bump is expected
- shadcn/ui has published Tailwind v4-compatible component patterns
- The existing test suite provides adequate coverage to detect regressions from dependency updates
- No new environment variables or configuration changes are required beyond what's in existing `.env` / `docker-compose.yml`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero dependency installation warnings or conflicts when installing backend packages in a clean environment.
- **SC-002**: Zero dependency installation warnings or peer dependency conflicts when installing frontend packages in a clean environment.
- **SC-003**: 100% of existing backend tests pass after all updates (same pass rate as pre-upgrade).
- **SC-004**: 100% of existing frontend unit tests pass after all updates (same pass rate as pre-upgrade).
- **SC-005**: Zero ruff violations reported with the expanded rule set (FURB, PTH, PERF, RUF added).
- **SC-006**: Zero pyright type errors in backend source.
- **SC-007**: Zero TypeScript type errors in frontend source.
- **SC-008**: Zero ESLint errors in frontend source.
- **SC-009**: Frontend production build completes in under 60 seconds.
- **SC-010**: Both Docker images build successfully and services pass health checks within 30 seconds of container start.
- **SC-011**: No visual regressions in UI rendering (light mode, dark mode, theme colors, animations all render correctly).
- **SC-012**: Zero unused dependencies remain in either pyproject.toml or package.json (python-jose and socket.io-client removed).
