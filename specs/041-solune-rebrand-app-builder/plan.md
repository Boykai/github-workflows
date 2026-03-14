# Implementation Plan: Solune Rebrand & App Builder Architecture

**Branch**: `041-solune-rebrand-app-builder` | **Date**: 2026-03-14 | **Spec**: [`spec.md`](spec.md)
**Input**: Feature specification from `/specs/041-solune-rebrand-app-builder/spec.md`

## Summary

Rename the project to "Solune", restructure as a monorepo (`solune/` + `apps/`), rebrand all references across ~70+ files, add multi-app management (create/edit/preview via chat with parent-issue intake), a new Apps page with iframe preview and start/stop controls, `/<app-name>` slash command for context switching, and `@admin`/`@adminlock` guard for self-editing protection. The implementation extends the existing FastAPI + React + SQLite stack, adding new backend models/services/routes for app lifecycle, new frontend pages/components for app management, and middleware-level guard enforcement.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI 0.135+, React 19.2, Vite 7.3, TanStack Query v5, Pydantic v2, aiosqlite
**Storage**: SQLite with aiosqlite (async, WAL mode) — existing `settings.db` at `/var/lib/ghchat/data/settings.db` (will become `/var/lib/solune/data/settings.db`)
**Testing**: pytest 9.0+ (backend), Vitest 4.0+ (frontend), Playwright (E2E)
**Target Platform**: Linux server (Docker Compose), browser SPA
**Project Type**: Web application (frontend + backend monorepo → evolving to platform monorepo)
**Performance Goals**: App creation < 1 min (SC-005), lifecycle transitions < 5s (SC-006), Apps page load < 3s (SC-007), preview load < 10s (SC-008), context switch < 2s (SC-009)
**Constraints**: SQLite single-writer (WAL mitigates), Docker networking for app preview isolation, path validation for security (no traversal)
**Scale/Scope**: Single-user to small-team usage, ~10-50 managed apps, 6 user stories across 6 phases, ~70+ files for rebrand

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS

Spec includes 6 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, clear scope boundaries, edge cases, and independent test criteria. Each story is independently implementable and testable.

### II. Template-Driven Workflow — ✅ PASS

All artifacts follow canonical templates: `spec.md` from spec-template, `plan.md` from plan-template. Generated artifacts (research.md, data-model.md, contracts/, quickstart.md) follow the plan-template structure.

### III. Agent-Orchestrated Execution — ✅ PASS

This plan is produced by the `speckit.plan` agent. It will hand off to `speckit.tasks` for task decomposition. Each phase has clear inputs/outputs.

### IV. Test Optionality with Clarity — ✅ PASS

Tests are not explicitly mandated in the spec for all stories. Backend CRUD operations and path validation warrant unit tests. Frontend component rendering warrants basic tests. E2E tests for app lifecycle are recommended but optional per constitution.

### V. Simplicity and DRY — ⚠️ JUSTIFIED VIOLATION

The monorepo restructure introduces additional complexity (nested `solune/` directory, root-level orchestration). This is justified: the `apps/` directory model is the core architectural change that transforms the platform from single-project to multi-app. See Complexity Tracking below.

## Project Structure

### Documentation (this feature)

```text
specs/041-solune-rebrand-app-builder/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
│   ├── apps-api.md      # App management REST API
│   ├── admin-guard.md   # Guard middleware contract
│   └── slash-commands.md# Context switching contract
├── checklists/          # Existing
│   └── requirements.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (post-restructure repository layout)

```text
# Root level (after monorepo restructure)
solune/                          # Current codebase relocated here
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── apps.py          # NEW: App management routes
│   │   ├── models/
│   │   │   └── app.py           # NEW: App data model
│   │   ├── services/
│   │   │   ├── app_service.py   # NEW: App lifecycle service
│   │   │   └── guard_service.py # NEW: Admin guard enforcement
│   │   ├── middleware/
│   │   │   └── admin_guard.py   # NEW: @admin/@adminlock middleware
│   │   └── migrations/
│   │       └── 024_apps.sql     # NEW: Apps table migration
│   └── tests/
│       ├── test_app_service.py  # NEW: App service tests
│       └── test_guard.py        # NEW: Guard tests
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── AppsPage.tsx     # NEW: Apps management page
│   │   ├── components/
│   │   │   └── apps/            # NEW: App-related components
│   │   │       ├── AppCard.tsx
│   │   │       ├── AppDetailView.tsx
│   │   │       └── AppPreview.tsx
│   │   ├── hooks/
│   │   │   └── useApps.ts       # NEW: App data hooks
│   │   ├── services/
│   │   │   └── appsApi.ts       # NEW: Apps API client
│   │   └── types/
│   │       └── apps.ts          # NEW: App TypeScript types
│   └── tests/
├── docs/
├── scripts/
├── specs/
├── docker-compose.yml           # Solune-internal compose
├── CHANGELOG.md
└── mcp.json

apps/                            # Generated applications live here
├── .gitkeep
└── <app-name>/                  # Scaffolded per-app directory
    ├── README.md
    ├── src/
    ├── config.json
    └── CHANGELOG.md

.github/                         # Agents, workflows (serve whole repo)
├── agents/
├── workflows/
└── prompts/

README.md                        # Root-level repo README (Solune platform)
docker-compose.yml               # Root-level orchestration compose
```

**Structure Decision**: Web application (Option 2) extended to monorepo layout. The existing `backend/` + `frontend/` structure moves under `solune/`. A new `apps/` directory at the root holds generated applications. `.github/` stays at root. New files are added within the existing backend/frontend structure following established patterns (Pydantic models, FastAPI routers, React pages/components).

## Complexity Tracking

> Constitution Check V (Simplicity and DRY) has a justified violation.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Monorepo nesting (`solune/` + `apps/`) | Core architectural change: separates platform code from generated apps, enabling guard enforcement and multi-app isolation | Flat structure with `apps/` alongside `backend/`/`frontend/` lacks clear platform vs. app boundary; guards would require complex path matching instead of simple directory-level checks |
| Admin guard middleware | Prevents agents from accidentally modifying platform code during app-building operations | No guard: too risky once agents build apps autonomously — a single misrouted operation could corrupt platform code |
| Root-level orchestration compose | Manages both platform services and dynamically created app services from a single entry point | Separate compose files per app: increases operational complexity, makes it harder to manage networking between platform and apps |
