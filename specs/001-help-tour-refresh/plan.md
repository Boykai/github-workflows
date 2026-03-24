# Implementation Plan: Help Page & Tour Guide Full Refresh + Backend Step-Count Bug Fix

**Branch**: `001-help-tour-refresh` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-help-tour-refresh/spec.md`

## Summary

Fix a critical backend bug where the Pydantic validator (`le=10`) and database CHECK constraint (`current_step <= 10`) silently reject tour steps 11–13, despite the frontend already supporting 13 steps. Expand the Spotlight Tour to 14 steps (adding an Activity page step), add Activity to the Help page feature guides (total: 9), add 4 new FAQ entries (total: 16), create a new celestial icon (`TimelineStarsIcon`), and remove the dead `/help: "help-link"` mapping from `Sidebar.tsx`. All changes are validated by updated backend and frontend test suites.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**: FastAPI + Pydantic (backend), React 18 + Vite (frontend), Lucide icons
**Storage**: SQLite (aiosqlite) with sequential SQL migration files
**Testing**: pytest (backend), Vitest + React Testing Library (frontend)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web (separate backend + frontend in `solune/` monorepo)
**Performance Goals**: N/A — no performance-critical changes; content + validation updates only
**Constraints**: Zero downtime migration (SQLite CHECK constraint update); backward-compatible API
**Scale/Scope**: 10 files changed, 1 new migration file, 1 new icon component

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` completed with 5 prioritized user stories and Given/When/Then scenarios |
| II. Template-Driven | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated | ✅ PASS | Work follows specify → plan → tasks → implement pipeline |
| IV. Test Optionality | ✅ PASS | Tests are explicitly required by FR-012: backend parametrized tests for step bounds 0–13, frontend `totalSteps` assertion update |
| V. Simplicity & DRY | ✅ PASS | No new abstractions — extends existing arrays, constants, and validators; single migration file |

**Pre-Phase 0 Gate**: ✅ PASSED — no violations

## Project Structure

### Documentation (this feature)

```text
specs/001-help-tour-refresh/
├── plan.md              # This file
├── research.md          # Phase 0 output — codebase research & decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — implementation quickstart
├── contracts/           # Phase 1 output — API contract changes
│   └── onboarding-api.yaml
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── onboarding.py           # FR-001: le=10 → le=13
│   │   └── migrations/
│   │       └── 038_onboarding_step_limit.sql  # FR-002: CHECK constraint update
│   └── tests/
│       └── unit/
│           └── test_api_onboarding.py   # FR-012: step boundary tests 0–13
└── frontend/
    └── src/
        ├── assets/
        │   └── onboarding/
        │       └── icons.tsx            # FR-006: TimelineStarsIcon
        ├── components/
        │   └── onboarding/
        │       └── SpotlightTour.tsx    # FR-003: 14th tour step (activity-link)
        ├── hooks/
        │   ├── useOnboarding.tsx        # FR-005: TOTAL_STEPS 13 → 14
        │   └── useOnboarding.test.tsx   # FR-012: totalSteps assertion update
        ├── layout/
        │   └── Sidebar.tsx              # FR-004: data-tour-step="activity-link" + FR-010: remove /help mapping
        └── pages/
            └── HelpPage.tsx             # FR-007: Activity guide + FR-008/009: FAQ audit + 4 new entries
```

**Structure Decision**: Web application (Option 2) — existing `solune/backend/` and `solune/frontend/` directories. All changes are modifications to existing files except the new migration `038_onboarding_step_limit.sql`.

## Complexity Tracking

> No violations — all changes are direct extensions of existing patterns. No new abstractions, libraries, or architectural decisions required.
