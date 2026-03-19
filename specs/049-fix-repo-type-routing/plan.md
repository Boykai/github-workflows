# Implementation Plan: Fix App Creation to Respect Repo Type for Issue/Pipeline Placement

**Branch**: `049-fix-repo-type-routing` | **Date**: 2026-03-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/049-fix-repo-type-routing/spec.md`

## Summary

Pipeline launch and scaffold operations currently ignore app `repo_type`, routing all issues and commits to Solune's default repository. The fix introduces repo-type-aware routing: `same-repo` uses the user-supplied `project_id`, `new-repo` uses `app.github_project_id`, and `external-repo` parses the URL to scaffold into the correct repo and auto-creates a Project V2 for pipeline launches.

## Technical Context

**Language/Version**: Python 3.12, TypeScript (ES2022)
**Primary Dependencies**: FastAPI 0.135+, Pydantic 2.12+, aiosqlite, githubkit, React 18, TanStack Query, Vite
**Storage**: SQLite (WAL mode, aiosqlite) — `apps` table with `repo_type`, `external_repo_url`, `github_project_id`, `github_project_url` columns
**Testing**: pytest (3,088 tests), vitest (1,145 tests), pyright, ruff, eslint, tsc
**Target Platform**: Linux server (Docker), SPA frontend (nginx)
**Project Type**: web (FastAPI backend + React frontend)
**Performance Goals**: N/A — this is a correctness fix, not a performance feature
**Constraints**: Must not regress existing same-repo workflows; all GitHub API calls async
**Scale/Scope**: Single-user platform; ~15 backend source files affected, ~3 frontend files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` complete with 5 prioritized user stories, GWT acceptance criteria, edge cases |
| II. Template-Driven | ✅ PASS | Using canonical `plan-template.md`; all artifacts follow templates |
| III. Agent-Orchestrated | ✅ PASS | Running via `/speckit.plan` agent; outputs hand off to `/speckit.tasks` |
| IV. Test Optionality | ✅ PASS | Tests explicitly required in spec (SC-001 through SC-007 demand verification); will include unit tests |
| V. Simplicity and DRY | ✅ PASS | Fix modifies existing code paths with minimal new abstractions; `parse_github_url()` is a single utility; no new services or layers introduced |

**Gate result**: PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/049-fix-repo-type-routing/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── app-create.md    # Updated API contract for app creation
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── api/
│   │   └── apps.py              # Pipeline launch routing by repo_type
│   ├── models/
│   │   └── app.py               # URL validation on AppCreate
│   ├── services/
│   │   └── app_service.py       # External-repo scaffold routing, auto-create project
│   └── utils.py                 # parse_github_url() utility
└── tests/
    └── unit/
        ├── test_api_apps.py     # Updated pipeline launch tests
        ├── test_app_service.py  # External-repo scaffold tests
        └── test_utils.py        # URL parsing tests

solune/frontend/
├── src/
│   └── components/apps/
│       └── CreateAppDialog.tsx  # project_id scoping by repo_type
└── src/
    └── components/apps/
        └── CreateAppDialog.test.tsx  # Frontend test updates
```

**Structure Decision**: Web application (backend + frontend). All changes modify existing files — no new services, modules, or layers introduced. One new utility function (`parse_github_url`) in `utils.py`.

## Constitution Check — Post-Design Re-evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Spec unchanged; design artifacts align with all 9 FRs |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Plan complete; ready for `/speckit.tasks` handoff |
| IV. Test Optionality | ✅ PASS | Tests required per spec; `parse_github_url` unit tests, scaffold routing tests, pipeline routing tests planned |
| V. Simplicity and DRY | ✅ PASS | One new utility (`parse_github_url`), parameter substitutions in existing code, conditional routing — minimal complexity added |

**Post-design gate result**: PASS — proceed to Phase 2 (`/speckit.tasks`).

## Complexity Tracking

> No violations — no entries needed.
