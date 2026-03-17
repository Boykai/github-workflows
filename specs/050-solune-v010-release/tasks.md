# Tasks: Solune v0.1.0 Public Release

**Input**: Design documents from `/specs/050-solune-v010-release/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are explicitly required by the specification (FR-041 through FR-044) and are included as dedicated Phase 11 tasks. Test tasks within feature phases are included only where they directly validate that phase's acceptance criteria.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. The plan's 9-phase structure maps to user stories as follows:
- Phase 1 (Security & Data Integrity) → US1 + US2
- Phase 2 (Code Quality) → US3
- Phase 3 (Core Features) → US4 + US5 + US7
- Phase 4 (Security Hardening) → US2 (continued)
- Phase 5 (Performance) → US9
- Phase 6 (Visual Polish) → US6
- Phase 7 (Documentation) → US8
- Phase 8 (Test Coverage) → Cross-cutting
- Phase 9 (Release Engineering) → US10

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `solune/backend/src/`, `solune/frontend/src/`
- **Migrations**: `solune/backend/src/migrations/`
- **Tests**: `solune/backend/tests/`, `solune/frontend/tests/`, `solune/frontend/e2e/`
- **Docker**: `solune/backend/Dockerfile`, `solune/frontend/Dockerfile`, `solune/docker-compose.yml`
- **Docs**: `solune/docs/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — verify current state and prepare for phased delivery

- [ ] T001 Verify monorepo structure and "Solune" rebrand completeness per plan assumption in solune/
- [ ] T002 [P] Verify backend dependencies are current in solune/backend/pyproject.toml (FastAPI >=0.135, Pydantic 2.12, aiosqlite, cryptography 46)
- [ ] T003 [P] Verify frontend dependencies are current in solune/frontend/package.json (React 19.2, Vite 7.3, TanStack Query 5.90, Tailwind CSS 4.2, @dnd-kit)
- [ ] T004 [P] Verify existing CI pipeline passes: ruff check, pyright, pytest, eslint, tsc, vitest per .github/workflows/ci.yml
- [ ] T005 Confirm existing migration chain integrity (023–028) in solune/backend/src/migrations/

---

## Phase 2: Foundational — Security & Data Integrity (Release Blockers)

**Purpose**: Core security and data persistence that MUST be complete before ANY feature work

**⚠️ CRITICAL**: No feature work (Phases 4+) can begin until this phase is complete. US1 and US2 tasks in this phase are release blockers.

### US1: Pipeline State Persistence (FR-001, FR-002, FR-003)

- [ ] T006 [US1] Create database migration 029_pipeline_state_persistence.sql with pipeline_runs, pipeline_stage_states, stage_groups, and onboarding_tour_state tables per data-model.md in solune/backend/src/migrations/029_pipeline_state_persistence.sql
- [ ] T007 [US1] Add access_control_enabled column to projects table and visual_identifier/display_order columns to agents table in solune/backend/src/migrations/029_pipeline_state_persistence.sql
- [ ] T008 [US1] Create PipelineRun Pydantic model with state validation rules per data-model.md in solune/backend/src/models/pipeline_run.py
- [ ] T009 [P] [US1] Create PipelineStageState Pydantic model with transition rules per data-model.md in solune/backend/src/models/pipeline_stage_state.py
- [ ] T010 [P] [US1] Create StageGroup Pydantic model with execution_mode enum (sequential/parallel) in solune/backend/src/models/stage_group.py
- [ ] T011 [US1] Create PipelineStateService for persisting pipeline runs to SQLite via aiosqlite in solune/backend/src/services/copilot_polling/pipeline_state_service.py
- [ ] T012 [US1] Implement startup state rebuild — query incomplete runs from DB and reconstruct in-memory working set in solune/backend/src/services/copilot_polling/pipeline_state_service.py
- [ ] T013 [US1] Add SQLite PRAGMA integrity_check on startup with fallback to in-memory + admin notification (edge case #1) in solune/backend/src/services/copilot_polling/pipeline_state_service.py
- [ ] T014 [US1] Remove 500-entry cap on in-memory pipeline state dict in solune/backend/src/services/copilot_polling/
- [ ] T015 [US1] Implement transactional writes for concurrent pipeline state updates (edge case #2) in solune/backend/src/services/copilot_polling/pipeline_state_service.py
- [ ] T016 [US1] Wire PipelineStateService into FastAPI dependency injection in solune/backend/src/dependencies.py

### US2: Security Critical Fixes (FR-004, FR-005, FR-006, FR-007, FR-008)

- [ ] T017 [P] [US2] Set HttpOnly=True and SameSite=Strict on all authentication cookies in solune/backend/src/api/auth.py (FR-004)
- [ ] T018 [P] [US2] Add startup validation for ENCRYPTION_KEY — refuse to start if missing or default value in solune/backend/src/main.py (FR-005)
- [ ] T019 [P] [US2] Add startup validation for SESSION_SECRET_KEY — refuse if missing or default in solune/backend/src/main.py (FR-005)
- [ ] T020 [P] [US2] Add startup validation for GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in solune/backend/src/main.py (FR-005)
- [ ] T021 [US2] Enumerate ALL missing config variables in a single error message on startup failure (edge case #3) in solune/backend/src/main.py
- [ ] T022 [US2] Implement project-level access control middleware — verify user membership, return 403 on unauthorized access in solune/backend/src/middleware/project_access.py (FR-006)
- [ ] T023 [US2] Wire project access control middleware into FastAPI app in solune/backend/src/main.py
- [ ] T024 [US2] Audit codebase for hardcoded secrets using bandit and manual review — move findings to env vars (FR-007)
- [ ] T025 [P] [US2] Add Pydantic validation models for all API input boundaries lacking explicit validation in solune/backend/src/api/ (FR-008)
- [ ] T026 [P] [US2] Validate and sanitize file upload inputs (path traversal, MIME type) in solune/backend/src/api/chat.py (FR-008)

**Checkpoint**: Pipeline state persists across restarts, all security blockers resolved. Application refuses to start with insecure config.

---

## Phase 3: User Story 3 — Clean, Maintainable Codebase (Priority: P2) 🎯

**Goal**: Refactor backend God class, reduce complexity, eliminate dead code, decompose frontend modules — all files under limits

**Independent Test**: All backend files < 1,500 lines, all functions CC ≤ 25, all frontend modules < 200 lines, zero static analysis errors

**Depends on**: Phase 2 complete

### Dead Code Cleanup (FR-013)

- [ ] T027 [US3] Identify and remove unused build artifacts and dead code across solune/backend/src/ and solune/frontend/src/
- [ ] T028 [P] [US3] Annotate legacy code with deprecation markers or remove per spec 039 in solune/backend/src/

### Complexity & DRY Reduction (FR-010, FR-011, FR-014)

- [ ] T029 [US3] Extract single resolve_repository() utility to shared module — eliminate all duplicates in solune/backend/src/services/github_projects/utils.py (FR-011)
- [ ] T030 [US3] Decompose high-complexity functions (CC 42–123 → ≤25) in solune/backend/src/services/github_projects/service.py (FR-010)
- [ ] T031 [P] [US3] Decompose high-complexity functions in solune/backend/src/services/copilot_polling/ polling services (FR-010)
- [ ] T032 [US3] Replace emoji-based state representations with typed enumerations in solune/backend/src/services/ (FR-014)

### God Class Split (FR-009)

- [ ] T033 [US3] Extract GitHubIssuesService from service.py into solune/backend/src/services/github_projects/issues_service.py
- [ ] T034 [US3] Extract GitHubPRService from service.py into solune/backend/src/services/github_projects/pr_service.py
- [ ] T035 [US3] Extract GitHubBranchesService from service.py into solune/backend/src/services/github_projects/branches_service.py
- [ ] T036 [US3] Slim remaining GitHubProjectsService coordinator in solune/backend/src/services/github_projects/service.py to < 1,500 lines
- [ ] T037 [US3] Update all imports and DI wiring for extracted services in solune/backend/src/dependencies.py
- [ ] T038 [US3] Verify all backend files < 1,500 lines with `find src -name "*.py" -exec wc -l {} +`

### Frontend Decomposition (FR-012)

- [ ] T039 [P] [US3] Split usePipelineConfig (616 lines) into usePipelineList, usePipelineAssignment, usePipelineExecution, usePipelineGroups in solune/frontend/src/hooks/
- [ ] T040 [P] [US3] Create index.ts barrel export for split pipeline hooks in solune/frontend/src/hooks/pipeline/index.ts
- [ ] T041 [P] [US3] Split GlobalSettings (380 lines) into GeneralSettings, SecuritySettings, IntegrationSettings sub-components in solune/frontend/src/components/settings/
- [ ] T042 [P] [US3] Create index.ts barrel export for split settings components in solune/frontend/src/components/settings/index.ts
- [ ] T043 [US3] Verify all frontend modules < 200 lines with `find src -name "*.tsx" -o -name "*.ts" | xargs wc -l | sort -rn`

### Best Practices & Infrastructure (FR-009, FR-010)

- [ ] T044 [P] [US3] Modernize dependency injection patterns in solune/backend/src/dependencies.py per spec 035 Phases 4-7
- [ ] T045 [P] [US3] Pin Docker base image versions to digests in solune/backend/Dockerfile and solune/frontend/Dockerfile (FR-046)
- [ ] T046 [P] [US3] Add upper-bound constraints to Python dependencies in solune/backend/pyproject.toml
- [ ] T047 [P] [US3] Consolidate mock factories in solune/backend/tests/ to reduce test duplication
- [ ] T048 [US3] Run full static analysis suite (ruff check, pyright, eslint, tsc) — verify zero errors (FR-009, FR-010)

**Checkpoint**: Codebase is clean, modular, and all size/complexity limits met. Ready for feature work.

---

## Phase 4: User Story 1 — Reliable Pipeline Execution (Priority: P1) — Pipeline Features Track A

**Goal**: Label-based pipeline state tracking with 60% API call reduction for recovery

**Independent Test**: Start a multi-stage pipeline, restart app mid-execution, verify pipeline resumes from last known state. View 500+ historical runs without data loss.

**Depends on**: Phase 2 (US1 pipeline persistence) + Phase 3 (God class split)

### Label-Based Pipeline State (FR-015)

- [ ] T049 [US1] Implement GitHub label manager for pipeline state labels (format: `solune:pipeline:{run_id}:stage:{stage_id}:{status}`) in solune/backend/src/services/copilot_polling/label_manager.py
- [ ] T050 [US1] Implement label lifecycle — create on stage running, update (delete+create) on state change per contracts/events.md in solune/backend/src/services/copilot_polling/label_manager.py
- [ ] T051 [US1] Implement recovery protocol — query solune:pipeline:* labels on startup, reconcile with DB, resume running pipelines per contracts/events.md in solune/backend/src/services/copilot_polling/label_manager.py
- [ ] T052 [US1] Implement PipelineRunStateChanged and PipelineStageStateChanged internal event dataclasses per contracts/events.md in solune/backend/src/models/pipeline_events.py
- [ ] T053 [US1] Wire label manager as consumer of pipeline state change events in solune/backend/src/services/copilot_polling/

### Pipeline Run API Endpoints

- [ ] T054 [US1] Implement POST /api/v1/pipelines/{pipeline_id}/runs — create and start pipeline run per contracts/rest-api.md in solune/backend/src/api/pipelines.py
- [ ] T055 [US1] Implement GET /api/v1/pipelines/{pipeline_id}/runs — list runs with pagination, no artificial cap (FR-003) in solune/backend/src/api/pipelines.py
- [ ] T056 [US1] Implement GET /api/v1/pipelines/{pipeline_id}/runs/{run_id} — detailed run state with all stages/groups in solune/backend/src/api/pipelines.py
- [ ] T057 [US1] Implement POST /api/v1/pipelines/{pipeline_id}/runs/{run_id}/cancel per contracts/rest-api.md in solune/backend/src/api/pipelines.py
- [ ] T058 [US1] Implement POST /api/v1/pipelines/{pipeline_id}/runs/{run_id}/recover — rebuild state and resume (FR-002) in solune/backend/src/api/pipelines.py
- [ ] T059 [US1] Add WebSocket pipeline state push notifications per contracts/events.md in solune/backend/src/api/pipelines.py

**Checkpoint**: Pipeline state fully persistent, label-based recovery functional, all run endpoints operational.

---

## Phase 5: User Story 4 — Visual Pipeline Builder with Group Execution (Priority: P2)

**Goal**: Drag-and-drop pipeline builder with sequential/parallel group support

**Independent Test**: Create pipeline with mixed groups via visual builder, save, run, verify stages execute in correct group order

**Depends on**: Phase 4 (pipeline run API + label-based state)

### Stage Group Backend (FR-016)

- [ ] T060 [US4] Implement group execution orchestrator — sequential groups complete before next, parallel stages launch simultaneously in solune/backend/src/services/copilot_polling/group_executor.py
- [ ] T061 [US4] Implement GET /api/v1/pipelines/{pipeline_id}/groups — list stage groups per contracts/rest-api.md in solune/backend/src/api/pipelines.py
- [ ] T062 [US4] Implement PUT /api/v1/pipelines/{pipeline_id}/groups — create/update groups atomically with validation per contracts/rest-api.md in solune/backend/src/api/pipelines.py

### Pipeline Builder Frontend (FR-017)

- [ ] T063 [US4] Create PipelineBuilder page component with @dnd-kit sortable for stage ordering within groups in solune/frontend/src/components/pipelines/PipelineBuilder.tsx
- [ ] T064 [P] [US4] Create StageGroup component with sequential/parallel toggle in solune/frontend/src/components/pipelines/StageGroup.tsx
- [ ] T065 [P] [US4] Create DraggableStage component for individual stages within groups in solune/frontend/src/components/pipelines/DraggableStage.tsx
- [ ] T066 [US4] Implement usePipelineGroups hook for group CRUD via TanStack Query in solune/frontend/src/hooks/pipeline/usePipelineGroups.ts
- [ ] T067 [US4] Add pipeline builder route and navigation in solune/frontend/src/App.tsx
- [ ] T068 [US4] Handle large pipelines (50+ stages) with virtualized rendering and zoom/pan (edge case #4) in solune/frontend/src/components/pipelines/PipelineBuilder.tsx

**Checkpoint**: Visual pipeline builder functional with group execution. Users can create, configure, and run grouped pipelines.

---

## Phase 6: User Story 5 — Agent Orchestration and Parallel Layout (Priority: P2)

**Goal**: Side-by-side agent layout with MCP tool synchronization

**Independent Test**: Launch two agents in parallel, verify side-by-side display with distinct visual indicators, confirm MCP config propagates to agent files

**Depends on**: Phase 3 (frontend decomposition for component structure)

### Parallel Agent Layout (FR-018)

- [ ] T069 [US5] Create ParallelAgentLayout component for side-by-side agent display with visual differentiation in solune/frontend/src/components/agents/ParallelAgentLayout.tsx
- [ ] T070 [P] [US5] Create AgentCard component with color/icon visual identifiers in solune/frontend/src/components/agents/AgentCard.tsx
- [ ] T071 [US5] Integrate parallel agent layout into agents page in solune/frontend/src/pages/AgentsPage.tsx

### MCP Tool Sync (FR-019)

- [ ] T072 [US5] Implement MCPConfigUpdated event handler — propagate tools to all agent config files per contracts/events.md in solune/backend/src/services/agents/mcp_sync.py
- [ ] T073 [US5] Extend PUT /api/v1/projects/{project_id}/mcp-config to trigger propagation and return agents_updated count per contracts/rest-api.md in solune/backend/src/api/projects.py
- [ ] T074 [US5] Implement agent file writer — update YAML agent configs with tools: ["*"] or explicit list per contracts/events.md in solune/backend/src/services/agents/mcp_sync.py

**Checkpoint**: Agents display side-by-side with distinct visuals. MCP config changes propagate to all agent files.

---

## Phase 7: User Story 7 — Chat and Voice Input Enhancements (Priority: P3)

**Goal**: Fix voice input cross-browser, enable chat file attachments to GitHub issues, paste issue descriptions with pipeline config

**Independent Test**: Use voice input in Firefox + Chrome, upload file attachment that appears on GitHub issue, paste issue description with pipeline config selection

**Depends on**: Phase 4 (pipeline config association for issue upload)

### Voice Input Fix (FR-020)

- [ ] T075 [US7] Fix Firefox speech recognition — detect unprefixed SpeechRecognition API, fall back gracefully with user message for unsupported browsers (edge case #5) in solune/frontend/src/components/chat/VoiceInput.tsx
- [ ] T076 [P] [US7] Fix grammar configuration for speech recognition in solune/frontend/src/components/chat/VoiceInput.tsx

### Chat Attachment to GitHub Issue (FR-021)

- [ ] T077 [US7] Implement POST /api/v1/chat/{conversation_id}/attachments — upload file and forward to GitHub issue per contracts/rest-api.md in solune/backend/src/api/chat.py
- [ ] T078 [US7] Add file upload UI in chat input with size limit (25MB) and type validation in solune/frontend/src/components/chat/ChatInput.tsx
- [ ] T079 [US7] Handle attachment upload failure gracefully — send message with inline error, allow retry (edge case #7) in solune/frontend/src/components/chat/ChatInput.tsx

### Issue Upload with Pipeline Config (FR-022)

- [ ] T080 [US7] Implement POST /api/v1/issues/create-with-pipeline — create GitHub issue with pipeline config association per contracts/rest-api.md in solune/backend/src/api/issues.py
- [ ] T081 [US7] Create IssueUpload component with description paste area and pipeline config selector in solune/frontend/src/components/issues/IssueUpload.tsx

**Checkpoint**: Voice input works cross-browser. File attachments forward to GitHub issues. Issue creation with pipeline config is functional.

---

## Phase 8: User Story 2 (Continued) — Security Hardening (Priority: P1)

**Goal**: Complete remaining security findings — containers, headers, rate limiting, localStorage, debug mode

**Independent Test**: Verify non-root containers, all HTTP security headers present, rate limiting active on auth endpoints, no sensitive data in localStorage

**Depends on**: Phase 2 (critical security fixes) + Phase 5 (feature stabilization)

### High-Priority Security (FR-024, FR-025)

- [ ] T082 [US2] Verify and enforce non-root user in solune/backend/Dockerfile — confirm appuser UID/GID set (FR-024)
- [ ] T083 [P] [US2] Configure non-root nginx user in solune/frontend/Dockerfile (FR-024)
- [ ] T084 [US2] Add HTTP security headers (CSP, HSTS, Referrer-Policy, Permissions-Policy, X-Content-Type-Options, X-Frame-Options) to nginx config per contracts/rest-api.md in solune/frontend/nginx.conf (FR-025)
- [ ] T085 [P] [US2] Add HTTP security headers to FastAPI middleware for API responses in solune/backend/src/middleware/ (FR-025)
- [ ] T086 [US2] Minimize OAuth scope to minimum required permissions in solune/backend/src/api/auth.py

### Medium-Priority Security (FR-026, FR-027, FR-028)

- [ ] T087 [US2] Extend slowapi rate limiting to auth endpoints (/api/v1/auth/*) and pipeline run creation per contracts/rest-api.md in solune/backend/src/api/auth.py (FR-026)
- [ ] T088 [US2] Audit frontend for sensitive data in localStorage — encrypt or move to session cookies in solune/frontend/src/ (FR-027)
- [ ] T089 [US2] Decouple debug mode from production config — ensure DEBUG defaults to false, reject DEBUG=true when ENCRYPTION_KEY is production-grade in solune/backend/src/main.py (FR-028)

### Low-Priority Security

- [ ] T090 [P] [US2] Configure least-privilege GitHub Actions permissions in .github/workflows/ci.yml
- [ ] T091 [P] [US2] Add avatar URL validation (allowlist GitHub avatar domain) in solune/backend/src/api/ or solune/frontend/src/

### Bug Basher Remaining

- [ ] T092 [US2] Perform codebase-wide audit for runtime errors, logic bugs, and auth bypasses — each fix gets a regression test in solune/backend/ and solune/frontend/

**Checkpoint**: All security findings resolved. Containers non-root, headers hardened, rate limiting active.

---

## Phase 9: User Story 9 — Performance-Optimized Experience (Priority: P3)

**Goal**: 50% idle API call reduction, 30% cache improvement, sub-2s page loads, 60fps scroll

**Independent Test**: Measure idle network activity (50% reduction), page load times (< 2s), interaction latency (< 100ms), scroll FPS (60fps)

**Depends on**: Phases 4-7 complete (features stabilized before optimization)

### Establish Baselines (FR-029)

- [ ] T093 [US9] Record pre-optimization baselines: idle API requests/minute, endpoint response times, React Profiler render counts in solune/docs/performance-baseline.md

### Backend Optimization (FR-029, FR-030, FR-031)

- [ ] T094 [US9] Add Cache-Control and ETag headers to read-only GET endpoints in solune/backend/src/api/ (FR-030)
- [ ] T095 [US9] Implement conditional GET (304 Not Modified) using If-None-Match header in solune/backend/src/middleware/
- [ ] T096 [US9] Eliminate unnecessary idle background API calls — reduce polling frequency for inactive data in solune/backend/src/services/copilot_polling/ (FR-029)
- [ ] T097 [US9] Implement change-detection-based refresh skipping — skip data refreshes when underlying data unchanged (FR-031) in solune/backend/src/services/

### Frontend Optimization (FR-032)

- [ ] T098 [P] [US9] Increase staleTime for stable data (projects, pipeline configs) and reduce refetchInterval for active polling in solune/frontend/src/constants.ts
- [ ] T099 [P] [US9] Disable refetchOnWindowFocus for non-critical queries across TanStack Query hooks in solune/frontend/src/hooks/
- [ ] T100 [US9] Add React.memo() to expensive list item components and useMemo/useCallback for computed values in solune/frontend/src/components/
- [ ] T101 [US9] Implement virtualized list rendering for 50+ pipeline runs (edge case #4) in solune/frontend/src/components/pipelines/
- [ ] T102 [US9] Throttle hot event listeners (scroll, resize) in solune/frontend/src/hooks/

**Checkpoint**: Performance targets met — 50% idle reduction, sub-2s loads, 60fps scroll.

---

## Phase 10: User Story 6 — Accessible, Polished User Interface (Priority: P3)

**Goal**: WCAG AA compliance, consistent theming, responsive layouts, no visual bugs

**Independent Test**: Automated contrast audit passes both themes, keyboard-only navigation works on all pages, responsive at 320-1920px

**Depends on**: Phases 4-7 complete (all UI features in place before polishing)

### Theme Contrast Audit (FR-033, FR-035)

- [ ] T103 [US6] Run npm run audit:theme-contrast and fix all WCAG AA violations (4.5:1 normal text, 3:1 large text) in solune/frontend/src/
- [ ] T104 [US6] Run npm run audit:theme-colors and replace all hardcoded color values with Tailwind theme tokens in solune/frontend/src/ (FR-035)
- [ ] T105 [US6] Verify theme changes apply immediately to modals and overlays (edge case #8) in solune/frontend/src/components/

### Keyboard Navigation & Focus (FR-034)

- [ ] T106 [US6] Add focus-visible:ring-2 utilities to all interactive elements across solune/frontend/src/components/ (FR-034)
- [ ] T107 [US6] Verify keyboard-only navigation through all major pages (Projects, Pipelines, Agents, Chat, Settings)

### Page Audits (FR-036)

- [ ] T108 [P] [US6] Perform visual cohesion, bug-free states, accessibility, and responsiveness audit on Projects page in solune/frontend/src/pages/ProjectsPage.tsx
- [ ] T109 [P] [US6] Perform UI consistency, quality, UX, and accessibility audit on Pipelines page in solune/frontend/src/pages/PipelinesPage.tsx
- [ ] T110 [P] [US6] Perform visual consistency, bugs, accessibility, and interactive elements audit on Agents page in solune/frontend/src/pages/AgentsPage.tsx
- [ ] T111 [US6] Verify responsive layouts at 320px, 768px, 1024px, and 1920px viewports across all pages (FR-036)

**Checkpoint**: All UI elements meet WCAG AA, keyboard navigable, responsive at all breakpoints.

---

## Phase 11: User Story 8 — Documentation and Guided Onboarding (Priority: P3)

**Goal**: Up-to-date docs, interactive 9-step onboarding tour, Help page with FAQ, exportable API docs

**Independent Test**: Follow setup guide from scratch, complete onboarding tour, verify documented features match behavior

**Depends on**: Phases 4-7 complete (document final feature state)

### Documentation Refresh (FR-037)

- [ ] T112 [US8] Audit and update README with current setup instructions in solune/README.md or solune/docs/
- [ ] T113 [P] [US8] Audit and update setup guide in solune/docs/setup.md
- [ ] T114 [P] [US8] Audit and update configuration reference in solune/docs/config.md
- [ ] T115 [P] [US8] Audit and update API documentation in solune/docs/api/
- [ ] T116 [P] [US8] Audit and update architecture documentation in solune/docs/architecture.md

### Onboarding Tour (FR-038)

- [ ] T117 [US8] Create OnboardingTourState API endpoints (GET/PUT /api/v1/onboarding/state) per contracts/rest-api.md in solune/backend/src/api/onboarding.py
- [ ] T118 [US8] Create OnboardingTour component with 9-step celestial-themed spotlight tour per contracts/events.md steps 1-9 in solune/frontend/src/components/onboarding/OnboardingTour.tsx
- [ ] T119 [US8] Implement tour state persistence hook (useOnboardingTour) with advance/dismiss/complete/restart actions in solune/frontend/src/hooks/useOnboardingTour.ts
- [ ] T120 [US8] Wire onboarding tour to first login detection — auto-start for new users in solune/frontend/src/App.tsx
- [ ] T121 [US8] Add restart tour option on Help page in solune/frontend/src/pages/HelpPage.tsx

### Help Page (FR-039)

- [ ] T122 [US8] Create HelpPage component with searchable FAQ content rendered with react-markdown in solune/frontend/src/pages/HelpPage.tsx
- [ ] T123 [US8] Add Help page route and navigation link in solune/frontend/src/App.tsx

### API Reference (FR-040)

- [ ] T124 [US8] Export OpenAPI JSON via GET /openapi.json and verify all endpoints documented in solune/backend/src/main.py
- [ ] T125 [US8] Generate and publish API reference docs from OpenAPI spec in solune/docs/api/

**Checkpoint**: Documentation is current, onboarding tour functional, Help page live, API reference complete.

---

## Phase 12: Feature Removal — Remove Blocking Feature

**Purpose**: Full removal of blocking feature from UI, backend, and database (FR-023)

**Depends on**: Phase 3 (code quality — clean foundation for removal)

- [ ] T126 Remove blocking feature UI components from solune/frontend/src/components/
- [ ] T127 Remove blocking feature backend logic and API endpoints from solune/backend/src/api/ and solune/backend/src/services/
- [ ] T128 Create migration to remove blocking feature data from database in solune/backend/src/migrations/
- [ ] T129 Remove blocking feature tests from solune/backend/tests/ and solune/frontend/tests/

---

## Phase 13: Test Coverage Gap Closure (FR-041, FR-042, FR-043, FR-044)

**Purpose**: Achieve coverage targets — 80% backend, 70% frontend, E2E for all major flows

**Depends on**: All feature phases complete (test final code state)

### Backend Coverage (71% → 80%) (FR-041)

- [ ] T130 [P] Add unit tests for security middleware (auth, CSRF, rate limiting, project access) in solune/backend/tests/unit/test_middleware/
- [ ] T131 [P] Add unit tests for pipeline state persistence service in solune/backend/tests/unit/test_pipeline_state_service.py
- [ ] T132 [P] Add unit tests for pipeline orchestration and group execution in solune/backend/tests/unit/test_group_executor.py
- [ ] T133 [P] Add unit tests for webhook handlers in solune/backend/tests/unit/
- [ ] T134 [P] Add unit tests for extracted GitHub services (issues, PR, branches) in solune/backend/tests/unit/test_github_services/
- [ ] T135 Verify backend coverage ≥ 80% with `pytest --cov=src --cov-report=term-missing`

### Frontend Coverage (50% → 70%) (FR-042)

- [ ] T136 [P] Add component tests for PipelineBuilder in solune/frontend/tests/components/PipelineBuilder.test.tsx
- [ ] T137 [P] Add component tests for settings sub-components in solune/frontend/tests/components/settings/
- [ ] T138 [P] Add component tests for chat attachments and voice input in solune/frontend/tests/components/chat/
- [ ] T139 [P] Add component tests for auth flow components in solune/frontend/tests/components/auth/
- [ ] T140 [P] Add component tests for parallel agent layout in solune/frontend/tests/components/agents/
- [ ] T141 [P] Add hook tests for split pipeline hooks in solune/frontend/tests/hooks/
- [ ] T142 Verify frontend coverage ≥ 70% with `npm run test:coverage`

### E2E Coverage (FR-043, FR-044)

- [ ] T143 [P] Add Playwright E2E test for full flow: create project → configure pipeline → run agents → review PR in solune/frontend/e2e/
- [ ] T144 [P] Add Playwright E2E test for onboarding tour completion in solune/frontend/e2e/
- [ ] T145 [P] Add Playwright E2E test for voice input in Chrome and Firefox in solune/frontend/e2e/
- [ ] T146 [P] Add Playwright E2E test for chat attachment upload in solune/frontend/e2e/
- [ ] T147 Add axe-core accessibility assertions to all Playwright page navigations (FR-044) in solune/frontend/e2e/

### Mutation Testing

- [ ] T148 Run mutmut full suite on backend — address surviving mutants in security and pipeline logic in solune/backend/
- [ ] T149 Run Stryker full suite on frontend — address surviving mutants in critical paths in solune/frontend/

**Checkpoint**: Backend ≥ 80%, frontend ≥ 70%, E2E covers all major flows, accessibility assertions in place.

---

## Phase 14: User Story 10 — Production-Ready Release Package (Priority: P1)

**Goal**: Validated release with correct versioning, secure containers, environment validation, release checklist

**Independent Test**: Fresh docker compose up from .env.example — all services healthy in 120s, version strings consistent at 0.1.0

**Depends on**: All previous phases complete

### Version & Changelog (FR-045)

- [ ] T150 [US10] Finalize CHANGELOG.md under [0.1.0] section in solune/CHANGELOG.md
- [ ] T151 [P] [US10] Verify version string 0.1.0 in solune/backend/pyproject.toml
- [ ] T152 [P] [US10] Verify version string 0.1.0 in solune/frontend/package.json
- [ ] T153 [US10] Tag release as v0.1.0

### Docker Image Finalization (FR-046)

- [ ] T154 [US10] Verify pinned base image digests (not :latest tags) in solune/backend/Dockerfile (FR-046)
- [ ] T155 [P] [US10] Verify pinned base image digests in solune/frontend/Dockerfile (FR-046)
- [ ] T156 [US10] Verify optimized multi-stage builds and healthcheck in solune/docker-compose.yml

### Environment Validation (FR-047, FR-048)

- [ ] T157 [US10] Verify .env.example covers ALL required configuration variables in solune/.env.example (FR-047)
- [ ] T158 [US10] Verify startup rejects insecure production config (default secrets, debug=true) via integration test (FR-048)

### Enhanced Health Endpoint

- [ ] T159 [US10] Enhance GET /api/v1/health to include startup_checks and version per contracts/rest-api.md in solune/backend/src/api/health.py

### Release Checklist (FR-049)

- [ ] T160 [US10] Execute full release verification checklist per quickstart.md Release Verification Checklist section:
  - All tests green (pytest, vitest, playwright)
  - Coverage thresholds met (≥70% FE, ≥80% BE)
  - Static analysis clean (ruff, pyright, eslint, tsc)
  - Security scans clean (pip-audit, bandit, npm audit)
  - Docker Compose from scratch — all 3 services healthy
  - Walk onboarding tour end-to-end
  - Full user flow: create project → configure pipeline → run agents → review PR
  - WCAG AA contrast verified in both themes
  - Cross-browser: Chrome, Firefox, Edge, Safari
  - No open P1/P2 bugs
- [ ] T161 [US10] Create release notes summarizing all changes for v0.1.0

**Checkpoint**: Release package validated. All gates passed. Ready to ship v0.1.0.

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ──────────► Phase 2 (Security & Data Integrity — US1+US2 blockers)
                                 │
                                 ▼
                            Phase 3 (Code Quality — US3)
                                 │
                    ┌────────────┼────────────┬──────────────┬──────────────┐
                    ▼            ▼            ▼              ▼              ▼
              Phase 4       Phase 6       Phase 7        Phase 8       Phase 12
           (Pipeline —     (Agents —     (Chat —       (Security      (Remove
             US1)           US5)          US7)          Hardening     Blocking)
                |                                        — US2)
                ▼
              Phase 5
           (Builder —
              US4)
                                 │ (all features complete)
                    ┌────────────┼────────────┬──────────────┐
                    ▼            ▼            ▼              ▼
              Phase 9       Phase 10      Phase 11      Phase 13
           (Performance    (Visual       (Docs —       (Test
             — US9)        Polish —       US8)          Coverage)
                            US6)
                                 │ (all done)
                                 ▼
                            Phase 14 (Release — US10)
```

### User Story Dependencies

- **US1 (P1) Pipeline Persistence**: Phase 2 → Phase 4 (label-based state). Foundation for all Track A.
- **US2 (P1) Security**: Phase 2 (blockers) → Phase 8 (hardening). Can parallelize with other stories between phases.
- **US3 (P2) Code Quality**: Phase 3. Blocks all feature work. No dependencies on other stories.
- **US4 (P2) Pipeline Builder**: Depends on US1 (Phase 4) + US3 (Phase 3). Phase 5.
- **US5 (P2) Agents**: Depends on US3 (frontend decomposition). Phase 6. Parallel with US4.
- **US6 (P3) Visual Polish**: Depends on all feature phases complete. Phase 10.
- **US7 (P3) Chat & Voice**: Voice fix (T075-T076) has no dependencies. Issue upload depends on US1 (pipeline config). Phase 7.
- **US8 (P3) Documentation**: Depends on all features complete. Phase 11.
- **US9 (P3) Performance**: Depends on feature stabilization. Phase 9.
- **US10 (P1) Release**: Depends on ALL other phases. Phase 14.

### Within Each User Story

- Models before services
- Services before API endpoints
- Backend before frontend (for API-dependent UI)
- Core implementation before integration and polish

### Parallel Opportunities

**Within Phase 2 (Security & Data Integrity)**:
- T017-T020 (cookie flags, startup validations) can run in parallel
- T008-T010 (Pydantic models) can run in parallel
- T025-T026 (input validation) can run in parallel

**Within Phase 3 (Code Quality)**:
- T039-T042 (frontend decomposition) can run in parallel with T033-T036 (God class split)
- T044-T047 (best practices/infrastructure) can run in parallel

**Phase 4-7 (Feature Tracks)**:
- Phase 4 (Pipeline/US1), Phase 6 (Agents/US5), Phase 7 (Chat/US7) can proceed in parallel once Phase 3 is complete
- Within each track, [P]-marked tasks can parallelize

**Phase 9-11 (Post-Feature)**:
- Performance (Phase 9), Visual Polish (Phase 10), Documentation (Phase 11) can proceed in parallel

**Within Phase 13 (Test Coverage)**:
- All [P]-marked test tasks can run in parallel across backend/frontend/E2E

---

## Parallel Example: Phase 2 (Security & Data Integrity)

```bash
# Launch all startup validation tasks in parallel (different files):
Task T017: "Set HttpOnly/SameSite cookies in auth.py"
Task T018: "Startup validation for ENCRYPTION_KEY in main.py"
Task T019: "Startup validation for SESSION_SECRET_KEY in main.py"
Task T020: "Startup validation for GitHub OAuth in main.py"

# Launch all Pydantic models in parallel (different files):
Task T008: "PipelineRun model in models/pipeline_run.py"
Task T009: "PipelineStageState model in models/pipeline_stage_state.py"
Task T010: "StageGroup model in models/stage_group.py"
```

## Parallel Example: Phase 3 (Code Quality)

```bash
# Backend God class split and frontend decomposition can proceed in parallel:
# Team A (Backend):
Task T033: "Extract GitHubIssuesService"
Task T034: "Extract GitHubPRService"
Task T035: "Extract GitHubBranchesService"

# Team B (Frontend — parallel with Team A):
Task T039: "Split usePipelineConfig hook"
Task T041: "Split GlobalSettings component"
```

## Parallel Example: Feature Tracks (Phases 4-7)

```bash
# Three feature tracks can run in parallel after Phase 3:

# Track A (Pipeline): T049-T068
# Track B (Agents):   T069-T074
# Track C (Chat):     T075-T081

# Track D (Feature Removal): T126-T129 (parallel with all tracks)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup verification
2. Complete Phase 2: Security & Data Integrity (US1 pipeline persistence + US2 critical security)
3. **STOP and VALIDATE**: Pipeline state survives restarts, security blockers resolved
4. This alone makes Solune viable for real-world use

### Incremental Delivery

1. Phase 1-2 → Security & persistence foundation ready
2. Phase 3 → Codebase is clean and maintainable (US3)
3. Phase 4 → Pipeline features operational (US1 label-based state)
4. Phase 5 → Visual builder live (US4)
5. Phase 6-7 → Agent layout + Chat enhancements (US5, US7)
6. Phase 8-11 → Polish: security hardening, performance, accessibility, docs (US2, US6, US8, US9)
7. Phase 12-13 → Cleanup + test coverage
8. Phase 14 → Release validation (US10)

Each phase adds value without breaking previous work.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phases 1-3 together (foundation)
2. Once Phase 3 is done:
   - Developer A: Track A — Pipeline Features (Phases 4-5)
   - Developer B: Track B — Agents + Track D Removal (Phase 6 + 12)
   - Developer C: Track C — Chat & Voice (Phase 7)
   - Developer D: Security Hardening (Phase 8)
3. Post-feature (Phases 9-11): parallelize performance, polish, docs
4. Phase 13-14: Full team on test coverage and release

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable at its checkpoint
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are relative to repository root
- Migration numbering continues from existing 028 → 029
- Tests are spec-mandated (FR-041 through FR-044) and grouped in Phase 13 for efficiency
- Total: 161 tasks across 14 phases covering all 49 functional requirements and 10 user stories
