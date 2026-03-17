# Implementation Plan: Debug & Fix Apps Page — New App Creation UX

**Branch**: `051-fix-app-creation-ux` | **Date**: 2026-03-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/051-fix-app-creation-ux/spec.md`

## Summary

The "Create New App" flow creates a GitHub repo and commits template files, but has three critical gaps: (1) template files silently fail to copy with no user feedback, (2) no Parent Issue is created to kickstart the Agent Pipeline despite `pipeline_id` existing on `AppCreate`, and (3) the frontend lacks pipeline selection and post-creation feedback. This plan addresses all three gaps across backend services, database model, and frontend components by hardening error collection in `build_template_files()`, wiring up the existing orchestrator/polling infrastructure after repo creation, and adding pipeline selection + full warning display to the frontend.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI, Pydantic, asyncio (backend); React 18, TanStack Query, Tailwind CSS (frontend)
**Storage**: SQLite via raw SQL migrations (`solune/backend/src/migrations/`)
**Testing**: pytest with asyncio_mode="auto" (backend); Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker Compose), modern browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: App creation end-to-end (repo + files + Parent Issue + sub-issues + polling) within 90 seconds under normal conditions; branch-readiness poll up to ~15 seconds
**Constraints**: GitHub API rate limits; best-effort pattern for non-critical steps (Parent Issue, Azure secrets)
**Scale/Scope**: Single-tenant Solune platform; ~50 screens; changes touch 14 files across backend and frontend

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` includes 5 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, independent tests, and edge cases |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan decomposes into phases with clear inputs/outputs; implementation will be task-driven |
| **IV. Test Optionality** | ✅ PASS | Spec explicitly requests backend + frontend test updates (FR-014 verification steps 7–8); tests are mandated by the specification |
| **V. Simplicity and DRY** | ✅ PASS | Plan reuses existing patterns (`_create_parent_issue_sub_issues`, `execute_full_workflow`, `ensure_polling_started`) rather than introducing new abstractions; no premature abstraction |

**Gate result**: ✅ All principles satisfied. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/051-fix-app-creation-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output — resolved clarifications
├── data-model.md        # Phase 1 output — entity model changes
├── quickstart.md        # Phase 1 output — developer getting-started guide
├── contracts/           # Phase 1 output — API contracts
│   ├── api-endpoints.md
│   └── frontend-components.md
└── tasks.md             # Phase 2 output (created by /speckit.tasks, NOT this command)
```

### Source Code (repository root)

```text
apps/solune/
├── backend/
│   ├── src/
│   │   ├── models/
│   │   │   └── app.py                          # Add parent_issue_number, parent_issue_url
│   │   ├── services/
│   │   │   ├── template_files.py               # Harden build_template_files(), warning propagation
│   │   │   ├── app_service.py                  # Fix poll timeout, add parent issue creation, wire pipeline
│   │   │   ├── agent_tracking.py               # Reference: append_tracking_to_body()
│   │   │   ├── workflow_orchestrator/
│   │   │   │   └── orchestrator.py             # Reference: execute_full_workflow(), create_all_sub_issues()
│   │   │   └── copilot_polling/
│   │   │       └── polling_loop.py             # Reference: ensure_polling_started()
│   │   ├── api/
│   │   │   └── tasks.py                        # Reference: _create_parent_issue_sub_issues() pattern
│   │   └── migrations/
│   │       └── 029_app_parent_issue.sql        # New migration: parent_issue_number, parent_issue_url
│   └── tests/
│       └── unit/
│           └── test_app_service_new_repo.py    # Update: parent issue, pipeline, template warnings
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── AppsPage.tsx                    # Pipeline selector, all-warnings, success feedback
│   │   │   └── AppsPage.test.tsx               # Update: pipeline selector, warnings display
│   │   ├── components/
│   │   │   └── apps/
│   │   │       ├── AppDetailView.tsx           # Parent issue link, pipeline info
│   │   │       └── AppCard.tsx                 # Pipeline status badge
│   │   ├── types/
│   │   │   └── apps.ts                         # Add parent_issue_number, parent_issue_url
│   │   └── services/
│   │       └── api.ts                          # Reference: existing API client methods
│   └── tests/
```

**Structure Decision**: Web application pattern — changes span the existing `apps/solune/backend/` and `apps/solune/frontend/` (previously `solune/backend/` and `solune/frontend/`) directories. The monorepo layout with `apps/` prefix is established by migration 028 and the current branch.

## Complexity Tracking

> No constitution violations detected. All changes reuse existing patterns and infrastructure.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
