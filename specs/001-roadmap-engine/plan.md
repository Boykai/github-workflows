# Implementation Plan: Self-Evolving Roadmap Engine

**Branch**: `001-roadmap-engine` | **Date**: 2026-03-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-roadmap-engine/spec.md`

## Summary

Add an AI-driven roadmap engine that automatically generates batches of feature proposals from a product owner's seed vision and launches them through the existing pipeline. The engine hooks into the queue-empty path of `_dequeue_next_pipeline()` for auto-launch, exposes REST endpoints for manual trigger/config/history/veto, persists cycle audit records to a new `roadmap_cycles` SQLite table, and sends Signal notifications on each cycle. All issue creation is delegated to the existing `execute_pipeline_launch()` — zero new issue-creation code. Configuration is stored as JSON fields on `ProjectBoardConfig` in the existing `project_settings` table (no schema migration for config; one migration for the audit table).

## Technical Context

**Language/Version**: Python ≥3.12 (backend), TypeScript ~5.9 / React 19.2 (frontend)
**Primary Dependencies**: FastAPI ≥0.135, Pydantic ≥2.12, aiosqlite ≥0.22, github-copilot-sdk ≥0.1.30, codegraphcontext ≥0.2.9, tenacity ≥9.1, @tanstack/react-query ^5.91
**Storage**: SQLite via aiosqlite — existing `project_settings` table (JSON config fields) + new `roadmap_cycles` table (audit/dedup)
**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend)
**Target Platform**: Linux server (Docker), modern browsers
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Manual generation completes in <60s; history endpoint loads 100 cycles in <2s; auto-launch triggers within 6 minutes of idle (5-min debounce + 1-min tolerance)
**Constraints**: 10 auto-cycles/day cap per project; 5-minute debounce on queue-empty hook; batch size 1–10 (default 3); seed vision max 10,000 characters
**Scale/Scope**: Per-project feature; single-digit concurrent projects expected; ~15 agent assignments per cycle at default batch size

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md contains 6 prioritized user stories (P1–P6) with Given-When-Then acceptance scenarios, edge cases, and success criteria |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates (plan.md, research.md, data-model.md, contracts/, quickstart.md) |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Single-responsibility: generator generates, launcher launches, hook triggers — clear handoffs |
| **IV. Test Optionality** | ✅ PASS | Spec says "SHOULD include unit tests" — tests are recommended but not mandated. Include when explicitly tasked |
| **V. Simplicity and DRY** | ✅ PASS | 100% reuse of execute_pipeline_launch(), blocking-queue skip, and Signal delivery. No new issue-creation code. New migration only for audit table (justified by dedup/history requirements) |

**Gate result: PASS** — no violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-roadmap-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output — resolved unknowns & decisions
├── data-model.md        # Phase 1 output — entity schemas & relationships
├── quickstart.md        # Phase 1 output — developer implementation guide
├── contracts/           # Phase 1 output — OpenAPI endpoint specs
│   └── roadmap-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
solune/backend/
├── src/
│   ├── models/
│   │   └── roadmap.py                       # NEW — RoadmapItem, RoadmapBatch, RoadmapCycleLog, RoadmapConfig
│   ├── services/
│   │   └── roadmap/                         # NEW — roadmap service package
│   │       ├── __init__.py
│   │       ├── generator.py                 # NEW — generate_roadmap_batch()
│   │       └── launcher.py                  # NEW — launch_roadmap_batch()
│   ├── api/
│   │   └── roadmap.py                       # NEW — REST endpoints (5 routes)
│   ├── prompts/
│   │   └── roadmap_generation.py            # NEW — AI prompt template
│   ├── migrations/
│   │   └── 039_roadmap_cycles.sql           # NEW — roadmap_cycles audit table
│   └── services/
│       ├── copilot_polling/
│       │   └── pipeline.py                  # MODIFY — queue-empty hook in _dequeue_next_pipeline()
│       ├── settings_store.py                # MODIFY — add roadmap config read/write helpers
│       └── signal_delivery.py               # MODIFY — add roadmap notification formatter
├── tests/                                   # Tests (when explicitly tasked)
│   ├── unit/
│   │   ├── test_roadmap_models.py
│   │   ├── test_roadmap_generator.py
│   │   └── test_roadmap_debounce.py
│   └── integration/
│       └── test_roadmap_cycle.py

solune/frontend/
├── src/
│   ├── components/
│   │   └── settings/
│   │       └── RoadmapSettings.tsx          # NEW — settings panel section
│   ├── components/
│   │   └── board/
│   │       └── RoadmapBadge.tsx             # NEW — compact state badge
│   ├── types/
│   │   └── index.ts                         # MODIFY — add roadmap types to ProjectBoardConfig
│   └── pages/
│       └── ProjectsPage.tsx                 # MODIFY — integrate RoadmapBadge
```

**Structure Decision**: Web application pattern (Option 2). New backend code follows existing conventions: Pydantic models in `src/models/`, service modules in `src/services/`, FastAPI routers in `src/api/`, prompt templates in `src/prompts/`. The roadmap service is organized as a package (`src/services/roadmap/`) with separate generator and launcher modules to maintain single-responsibility. Frontend additions follow existing component colocation patterns.

## Complexity Tracking

> No violations detected — Constitution Check passed cleanly. No complexity justifications needed.
