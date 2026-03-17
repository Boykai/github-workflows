# Research: Solune v0.1.0 Public Release

**Branch**: `050-solune-v010-release` | **Date**: 2026-03-17 | **Plan**: [plan.md](./plan.md)

## Overview

This document resolves all technical unknowns identified during plan creation. The Solune v0.1.0 release builds on an existing, well-established codebase with no NEEDS CLARIFICATION items in the Technical Context. Research focuses on best practices for the key technical challenges: pipeline state persistence, God class decomposition, security hardening, performance optimization, and release engineering.

---

## R-001: Pipeline State Persistence Strategy

**Context**: FR-001 through FR-003 require migrating from an in-memory dict (500-entry cap) to durable storage. The existing stack uses SQLite via aiosqlite with SQL-based migrations.

**Decision**: Extend the existing SQLite database with new migration(s) for pipeline state tables. Use the established migration framework (sequential numbered SQL files in `backend/src/migrations/`).

**Rationale**:
- SQLite is already the production database — no new infrastructure dependency
- aiosqlite provides async I/O, preventing blocking during pipeline state writes
- The migration framework is proven (6 migrations: 023–028) and well-understood
- SQLite WAL mode supports concurrent reads during writes, sufficient for single-instance deployment
- Transactional writes satisfy the concurrent pipeline update edge case (spec edge case #2)

**Alternatives Considered**:
- **Redis**: Rejected — adds a new service dependency, overkill for single-instance deployment, not aligned with Docker Compose simplicity constraint
- **File-based JSON**: Rejected — no transactional integrity, corruption risk on crash, no query capability for historical data
- **PostgreSQL**: Rejected — adds heavyweight service, Docker Compose complexity, not justified for expected scale

**Implementation Notes**:
- New migration: `029_pipeline_state_persistence.sql` (create `pipeline_runs` and `pipeline_stage_states` tables)
- Startup rebuild: Query incomplete runs from DB, reconstruct in-memory working set
- Remove 500-entry cap: DB has no artificial row limit
- Corruption detection: Use SQLite `PRAGMA integrity_check` on startup, fall back to in-memory with admin notification if corruption detected (spec edge case #1)

---

## R-002: God Class Decomposition Strategy

**Context**: `backend/src/services/github_projects/service.py` is 5,338 lines. FR-009 requires all files under 1,500 lines. FR-010 requires cyclomatic complexity ≤ 25. FR-011 requires no duplicate utility functions.

**Decision**: Extract domain-specific service classes following the existing service module pattern. Split into `GitHubIssuesService`, `GitHubPRService`, `GitHubBranchesService`, and retain a slim `GitHubProjectsService` coordinator.

**Rationale**:
- The codebase already uses a service-per-domain pattern (see `services/agents/`, `services/copilot_polling/`, `services/chores/`)
- Extracting by GitHub API domain (issues, PRs, branches) creates natural boundaries that align with GitHub's own API structure
- A coordinator service retains cross-cutting project-level operations
- This approach allows incremental extraction — one domain at a time, each independently testable

**Alternatives Considered**:
- **Mixin-based decomposition**: Rejected — mixins obscure method resolution, make testing harder, and don't reduce file size if kept in one file
- **Functional decomposition (utility modules)**: Rejected — loses the service abstraction, makes dependency injection harder, fragments related methods across unrelated modules
- **Full rewrite**: Rejected — high regression risk, blocks all dependent work, violates YAGNI

**Implementation Notes**:
- Step 1: Identify method groups by GitHub API domain (issue methods, PR methods, branch methods)
- Step 2: Extract shared utilities (e.g., `resolve_repository()`) to a common module first (FR-011)
- Step 3: Extract each domain service with its own file, inheriting shared base or receiving dependencies via constructor
- Step 4: Update imports and DI wiring in `dependencies.py`
- Step 5: Verify no file exceeds 1,500 lines, no function exceeds CC 25

---

## R-003: Frontend Module Decomposition

**Context**: `GlobalSettings` component (380 lines) and `usePipelineConfig` hook (616 lines) exceed the 200-line target (FR-012). The frontend uses React 19 with TypeScript, TanStack Query, and Vite.

**Decision**: Split by responsibility into sub-modules within the same directory. Use React's composition model (custom hooks, sub-components) rather than creating a new abstraction layer.

**Rationale**:
- The existing codebase uses custom hooks for data fetching (`useProjects`, `useProjectBoard`) — extending this pattern is natural
- TanStack Query's hook-per-query model encourages small, focused hooks
- Sub-components in the same directory maintain co-location of related code
- Vite's tree-shaking ensures no bundle size penalty from splitting

**Alternatives Considered**:
- **State management library (Zustand, Jotai)**: Rejected — TanStack Query already handles server state; adding another state library adds complexity without benefit
- **Monolithic refactor**: Rejected — a single large refactoring PR is risky; incremental splitting by responsibility is safer

**Implementation Notes**:
- `usePipelineConfig` → split into `usePipelineList`, `usePipelineAssignment`, `usePipelineExecution`, `usePipelineGroups`
- `GlobalSettings` → split into `GeneralSettings`, `SecuritySettings`, `IntegrationSettings` sub-components
- Each sub-module under 200 lines, exported from an index file for backward compatibility

---

## R-004: Security Hardening Best Practices

**Context**: FR-004 through FR-008 and FR-024 through FR-028 cover security across cookies, encryption, access control, input validation, container security, HTTP headers, rate limiting, and localStorage.

**Decision**: Layer security controls using FastAPI middleware (backend) and HTTP headers (frontend nginx config). Follow OWASP best practices for each control.

**Rationale**:
- FastAPI middleware is the established pattern for cross-cutting concerns (existing middleware for CSRF, CSP, request IDs)
- nginx configuration handles HTTP security headers at the edge (CSP, HSTS, Referrer-Policy, Permissions-Policy)
- slowapi is already a dependency for rate limiting — extend to sensitive endpoints
- The existing `encryption.py` service provides Fernet encryption — extend to enforce key presence on startup

**Alternatives Considered**:
- **External WAF/reverse proxy**: Rejected — adds infrastructure complexity beyond Docker Compose constraint
- **Third-party auth service (Auth0, Keycloak)**: Rejected — existing GitHub OAuth is retained per assumptions

**Implementation Notes**:
- **Cookies** (FR-004): Set `httponly=True`, `samesite="strict"` in `auth.py` cookie handlers
- **Encryption enforcement** (FR-005): Add startup validation in `main.py` that checks `ENCRYPTION_KEY` is set and not a default value
- **Access control** (FR-006): Add project membership check middleware, return 403 for unauthorized
- **Hardcoded secrets** (FR-007): Automated scan with `bandit` + manual review; move any findings to env vars
- **Input validation** (FR-008): Pydantic models at API boundaries (already partially in place), add explicit validation for file uploads and path parameters
- **Non-root containers** (FR-024): Backend Dockerfile already has `appuser`; verify UID/GID are set, verify frontend nginx runs as non-root
- **HTTP headers** (FR-025): Add to nginx.conf: `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`
- **Rate limiting** (FR-026): Extend slowapi decorators to auth endpoints (`/api/v1/auth/*`)
- **localStorage** (FR-027): Audit frontend for sensitive data in localStorage; encrypt or move to session cookies
- **Debug mode** (FR-028): Ensure `DEBUG` defaults to `false`; startup rejects `DEBUG=true` when `ENCRYPTION_KEY` looks production-grade

---

## R-005: Pipeline Builder & Group Execution Architecture

**Context**: FR-015 through FR-017 require label-based state tracking, group execution (sequential/parallel), and a visual drag-and-drop pipeline builder.

**Decision**: Extend the existing pipeline configuration model with group metadata. Use @dnd-kit (already a dependency) for the visual builder. Use GitHub labels for state tracking via the existing githubkit integration.

**Rationale**:
- @dnd-kit is already installed (`@dnd-kit/core`, `@dnd-kit/modifiers`, `@dnd-kit/sortable`, `@dnd-kit/utilities`) — no new dependency
- GitHub labels are a natural fit for pipeline state (visible in GitHub UI, queryable via API, reduces polling)
- The Kanban-style builder aligns with the existing board component patterns (`components/board/`)

**Alternatives Considered**:
- **react-beautiful-dnd**: Rejected — already have @dnd-kit; adding another DnD library is unnecessary
- **Custom WebSocket state sync**: Rejected — label-based state uses GitHub's existing infrastructure, reducing backend complexity
- **YAML-based configuration**: Rejected — spec explicitly requires visual builder; YAML can be an export format

**Implementation Notes**:
- **Data model**: Add `stage_groups` table with `execution_mode` (sequential/parallel), `order`, and FK to `pipeline_configs`
- **Label format**: `solune:pipeline:{run_id}:stage:{stage_id}:{status}` (e.g., `solune:pipeline:42:stage:build:completed`)
- **Builder UI**: New page/component using @dnd-kit sortable for stage ordering within groups, with toggle for sequential/parallel per group
- **API**: New endpoints for group CRUD, pipeline execution with group ordering

---

## R-006: Accessibility & Theme Compliance

**Context**: FR-033 through FR-036 require WCAG AA compliance, keyboard navigation, no hardcoded colors, and responsive layouts (320px–1920px).

**Decision**: Audit existing Tailwind CSS theme configuration, replace hardcoded colors with theme tokens, and add focus-visible utilities. Use existing audit scripts (`audit-theme-colors.mjs`, `check-theme-contrast.mjs`).

**Rationale**:
- Tailwind CSS 4 has built-in theme system with CSS custom properties — ideal for dynamic theming
- The project already has audit scripts for theme colors and contrast checking
- jest-axe and @axe-core/playwright are already dependencies for automated accessibility testing

**Alternatives Considered**:
- **CSS-in-JS (styled-components, emotion)**: Rejected — Tailwind is already the styling system; switching would be a massive rewrite
- **Manual contrast checking**: Rejected — existing automation scripts and axe-core provide reliable automated checking

**Implementation Notes**:
- Run `npm run audit:theme-colors` to identify hardcoded colors
- Run `npm run audit:theme-contrast` to measure current contrast ratios
- Replace hardcoded colors with Tailwind theme classes (e.g., `text-gray-600` → `text-foreground-secondary`)
- Add `focus-visible:ring-2` utilities to all interactive elements
- Test responsive layouts at 320px, 768px, 1024px, 1920px breakpoints
- Add axe-core assertions to Playwright E2E tests (FR-044)

---

## R-007: Performance Optimization Approach

**Context**: FR-029 through FR-032 require 50% idle API reduction, 30% cache improvement, change-detection-based refresh skipping, and targeted component rerenders.

**Decision**: Establish baselines first (after feature stabilization), then optimize using TanStack Query's built-in features (stale time, refetch intervals, enabled flags) for frontend and response caching with ETags for backend.

**Rationale**:
- TanStack Query already supports all required optimization patterns: `staleTime`, `refetchInterval`, `refetchOnWindowFocus`, `enabled` flag for conditional fetching
- The existing `STALE_TIME_*` constants in `constants.ts` provide a foundation to tune
- Backend caching via `services/cache.py` is already in place — extend with ETag/If-None-Match support
- Measuring before optimizing (Phase 5 after Phase 3) prevents premature optimization per spec assumption #4

**Alternatives Considered**:
- **Service worker caching**: Rejected — adds complexity, Docker Compose deployment doesn't benefit from offline-first patterns
- **GraphQL**: Rejected — would require rewriting the entire API layer; REST with targeted optimization is sufficient for expected scale
- **Server-sent events for real-time updates**: Rejected — websockets are already in the dependency list; SSE adds another protocol without clear benefit

**Implementation Notes**:
- **Baseline**: Record idle network activity (requests/minute), endpoint response times, React Profiler render counts
- **Backend**: Add `Cache-Control` and `ETag` headers to read endpoints; implement conditional GET (304 Not Modified)
- **Frontend**: Increase `staleTime` for stable data (projects, pipeline configs), reduce `refetchInterval` for active polling, disable refetch on window focus for non-critical queries
- **Rendering**: Use `React.memo()` for expensive list items, `useMemo`/`useCallback` for computed values, virtualized lists for 50+ pipeline runs

---

## R-008: Documentation & Onboarding Patterns

**Context**: FR-037 through FR-040 require current documentation, interactive onboarding tour, Help page with FAQ, and exportable API docs.

**Decision**: Use react-joyride (or similar spotlight library) for the onboarding tour, FastAPI's built-in OpenAPI export for API docs, and manual documentation audit against actual codebase behavior.

**Rationale**:
- FastAPI generates OpenAPI/Swagger docs natively — already behind the `ENABLE_DOCS` env var
- The spec mentions a "celestial-themed" onboarding tour, aligning with Solune's existing theme
- react-markdown is already a dependency for rendering help content
- Documentation files exist in `solune/docs/` — audit and update rather than rewrite

**Alternatives Considered**:
- **Docusaurus/GitBook**: Rejected — adds build infrastructure; inline docs in the repo are simpler for a Docker Compose deployment
- **Storybook for component docs**: Rejected — useful but out of scope for v0.1.0; focus on user-facing docs

**Implementation Notes**:
- **Onboarding**: 9-step tour: (1) Welcome → (2) Projects → (3) Create Project → (4) Pipeline Config → (5) Pipeline Builder → (6) Agents → (7) Chat → (8) Settings → (9) Help. State persisted per user (new `onboarding_state` in user settings).
- **Help page**: Static FAQ content rendered with react-markdown, searchable by keyword
- **API docs**: Export OpenAPI JSON via `GET /openapi.json`, verify all endpoints documented, include in `docs/api/`
- **Doc audit**: Compare each doc page against current codebase behavior, update screenshots and command examples

---

## R-009: Release Engineering & Docker Hardening

**Context**: FR-045 through FR-049 require version consistency, pinned base images, environment validation, insecure-config rejection, and zero P1/P2 bugs.

**Decision**: Add startup validation in the FastAPI app that checks all required configuration before accepting requests. Pin all Docker base image digests. Create a release checklist as a verification script.

**Rationale**:
- Startup validation is a common FastAPI pattern using `@app.on_event("startup")` or lifespan handlers
- Pinning Docker images by digest (not just tag) prevents supply chain attacks
- A scripted release checklist ensures repeatable verification

**Alternatives Considered**:
- **Helm charts / Kubernetes manifests**: Rejected — Docker Compose only per constraints
- **GitHub Release automation**: Rejected — manual release process is sufficient for v0.1.0; automate in future versions

**Implementation Notes**:
- **Version strings**: Verify `0.1.0` in `pyproject.toml`, `package.json`, `CHANGELOG.md` — add CI check
- **Docker pins**: Update `python:3.13-slim` → `python:3.13-slim@sha256:...`, `nginx:1.27-alpine` → `nginx:1.27-alpine@sha256:...`, `node:22-alpine` → `node:22-alpine@sha256:...`
- **Startup validation**: Check `ENCRYPTION_KEY` is set and not default, `SESSION_SECRET_KEY` is set, `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set, `DEBUG` is not `true` in production mode
- **Release checklist**: Script that runs all CI checks locally, verifies Docker build, checks version strings, validates `.env.example` completeness

---

## R-010: Test Coverage Strategy

**Context**: FR-041 (80% backend), FR-042 (70% frontend), FR-043 (E2E flows), FR-044 (accessibility assertions). Current: 71% backend, ~50% frontend.

**Decision**: Gap analysis-driven test authoring. Identify uncovered critical paths using coverage reports, prioritize security middleware, pipeline logic, and UI interaction tests.

**Rationale**:
- Coverage reports from CI already identify uncovered lines — use these as a roadmap
- The biggest gaps are likely in new features (pipeline builder, group execution) and security middleware
- Mutation testing (Stryker/mutmut) validates test quality, not just coverage percentage

**Alternatives Considered**:
- **AI-generated test suites**: Rejected — fragile, high maintenance cost; targeted manual test authoring produces better tests
- **Coverage-only approach (no mutation testing)**: Rejected — spec explicitly requires mutation testing (FR implicit from parent issue verification section)

**Implementation Notes**:
- **Backend priority areas**: Security middleware (auth, CSRF, rate limiting), pipeline state persistence (new code), GitHub service split (regression tests), webhook handlers
- **Frontend priority areas**: Pipeline builder (new component), settings components, chat attachments, auth flows
- **E2E scenarios**: Project creation → pipeline config → agent run → PR review (full flow), onboarding tour completion, voice input (Chrome + Firefox)
- **Accessibility**: Add `axe-core` assertions to every Playwright page navigation
- **Mutation testing**: Run after unit test coverage targets are met; focus on surviving mutants in security and pipeline logic
