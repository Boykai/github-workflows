# Implementation Plan: New Repository & New Project Creation for Solune

**Branch**: `049-repo-project-creation` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/049-repo-project-creation/spec.md`

## Summary

Add "New Repository" and "New Project" creation capabilities throughout Solune. This plan extends the existing GitHub service layer with repository creation (REST), project creation (GraphQL), and project-to-repository linking (GraphQL). A template file manager reads bundled `.github/`, `.specify/`, and `.gitignore` files and replaces `copilot-instructions.md` with a generic placeholder. The backend models, database schema, and API endpoints are extended to support the `new-repo` app type and standalone project creation. The frontend gains a repo type selector in the app creation dialog, a standalone "New Repository" button, a "+ New Project" option in the project selector dropdown, and repo type badges on app cards.

## Technical Context

**Language/Version**: Python 3.13 (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI + Pydantic + GitHubKit (backend), React 19 + Vite 7 + TanStack Query (frontend)
**Storage**: aiosqlite (SQLite — `apps` table extended with new columns)
**Testing**: pytest + pytest-asyncio (backend), Vitest + Testing Library (frontend)
**Target Platform**: Linux (Docker containers)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: App creation completes in <60s including all GitHub API calls; standalone project creation in <15s
**Constraints**: ~4 GitHub API calls per new-repo creation — well within rate limits; existing OAuth scopes (`repo` + `project`) are sufficient
**Scale/Scope**: 5 new backend service methods, 1 new service module, 1 DB migration, 3 new/updated API endpoints, 6 frontend file modifications

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|---|---|---|
| I. Specification-First | PASS | `spec.md` created with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, and explicit scope boundaries |
| II. Template-Driven | PASS | Using canonical `plan-template.md`; all artifacts in `specs/049-repo-project-creation/` |
| III. Agent-Orchestrated | PASS | Plan produced by `/speckit.plan`; tasks will follow via `/speckit.tasks` |
| IV. Test Optionality | PASS | Tests included as Phase 5 — spec explicitly defines unit + integration test requirements |
| V. Simplicity / DRY | PASS | Extends existing mixin pattern for GitHub service methods; reuses existing AppCreate model with optional fields; no new abstractions beyond the template file reader |
| Branch/Dir Naming | PASS | `049-repo-project-creation` follows `###-short-name` pattern |
| Phase-Based Execution | PASS | Specify → Plan (this) → Tasks → Implement |
| Independent User Stories | PASS | All 5 stories are independently implementable — Story 1 (new repo) can ship alone; Story 2 (standalone project) is independent; Stories 3–5 build on shared infrastructure but are individually testable |

No violations. No complexity-tracking entries required.

### Post-Design Re-evaluation

| Principle | Status | Notes |
|---|---|---|
| I. Specification-First | PASS | All research findings align with spec requirements; no spec amendments needed |
| II. Template-Driven | PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | PASS | Phase handoff from plan → tasks is clean |
| IV. Test Optionality | PASS | Test phase (Phase 5) is included per spec requirements |
| V. Simplicity / DRY | PASS | Template file reader is the only new module; all other changes extend existing patterns. Generic copilot-instructions is a hardcoded string to avoid filesystem dependency at runtime |

## Project Structure

### Documentation (this feature)

```text
specs/049-repo-project-creation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── backend-api.md   # REST API endpoint contracts
│   └── graphql-mutations.md  # GraphQL mutation contracts
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── Dockerfile                                  # MODIFY: Add COPY for template files
│   ├── src/
│   │   ├── models/
│   │   │   └── app.py                              # MODIFY: Extend RepoType, AppCreate, App
│   │   ├── services/
│   │   │   ├── app_service.py                      # MODIFY: Add create_app_with_new_repo(), create_standalone_project()
│   │   │   ├── template_files.py                   # CREATE: Template file reader + generic copilot-instructions
│   │   │   └── github_projects/
│   │   │       ├── graphql.py                      # MODIFY: Add 3 new GraphQL mutations
│   │   │       ├── repository.py                   # MODIFY: Add create_repository(), list_available_owners()
│   │   │       └── projects.py                     # MODIFY: Add create_project_v2(), link_project_to_repository()
│   │   ├── api/
│   │   │   ├── apps.py                             # MODIFY: Route POST /apps by repo_type, add GET /apps/owners
│   │   │   └── projects.py                         # MODIFY: Add POST /projects/create
│   │   └── migrations/
│   │       └── 028_new_repo_support.sql            # CREATE: Schema extension for new-repo type
│   └── tests/
│       └── unit/
│           ├── test_github_repository.py           # CREATE: Tests for create_repository, list_available_owners
│           ├── test_github_projects_create.py       # CREATE: Tests for create_project_v2, link_project_to_repository
│           ├── test_template_files.py              # CREATE: Tests for template reader
│           └── test_app_service_new_repo.py        # CREATE: Tests for create_app_with_new_repo, create_standalone_project
├── frontend/
│   ├── src/
│   │   ├── types/
│   │   │   └── apps.ts                             # MODIFY: Add 'new-repo' to RepoType, new fields, Owner type
│   │   ├── services/
│   │   │   └── api.ts                              # MODIFY: Add appsApi.owners(), projectsApi.create()
│   │   ├── hooks/
│   │   │   ├── useApps.ts                          # MODIFY: Add useOwners() hook
│   │   │   └── useProjects.ts                      # MODIFY: Add useCreateProject() hook
│   │   ├── pages/
│   │   │   └── AppsPage.tsx                        # MODIFY: Repo type selector, conditional fields, "New Repository" button
│   │   ├── layout/
│   │   │   └── ProjectSelector.tsx                 # MODIFY: Add "+ New Project" option + creation dialog
│   │   └── components/
│   │       └── apps/
│   │           ├── AppCard.tsx                      # MODIFY: Add repo type badge + repo/project links
│   │           └── AppDetailView.tsx               # MODIFY: Add repo/project links
│   └── ...
└── ...
```

**Structure Decision**: Web application. All changes land in the existing `solune/backend/` and `solune/frontend/` structure. New backend code extends existing mixin classes and service modules. The only new module is `template_files.py`. Frontend changes are modifications to existing components and hooks. No new top-level directories.

## Complexity Tracking

> No violations. No entries required.
