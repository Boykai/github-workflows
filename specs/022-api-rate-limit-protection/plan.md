# Implementation Plan: Reduce GitHub API Rate Limit Consumption

**Branch**: `022-api-rate-limit-protection` | **Date**: 2026-03-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/022-api-rate-limit-protection/spec.md`

## Summary

The app consumes ~1,000+ GitHub API calls/hour while idle on the project board page due to three compounding issues: (1) WebSocket sends refresh messages every 30 seconds regardless of data changes, (2) the frontend invalidates both the tasks and expensive board data queries on every WebSocket message, and (3) the board data endpoint makes N+M API calls per refresh with misaligned cache TTLs. The fix adds hash-based WebSocket change detection, decouples frontend query invalidation, adds independent sub-issue caching, and aligns cache TTLs — reducing idle consumption to ~70-100 calls/hour.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.8 (frontend)
**Primary Dependencies**: FastAPI 0.109+, TanStack React Query 5.17, native WebSocket (asyncio)
**Storage**: SQLite (aiosqlite) for persistence, in-memory `InMemoryCache` with TTL for API response caching
**Testing**: pytest 7.4+ / pytest-asyncio 0.23+ (backend), vitest 4.0+ (frontend)
**Target Platform**: Linux server (Docker), modern browser (React 18.3 SPA)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: <100 GitHub API calls/hour while idle (down from ~1,000+)
**Constraints**: Must not break manual refresh (cache bypass), must detect real changes within 30 seconds
**Scale/Scope**: Projects with up to ~300 items, 20+ issues with sub-issues, 2+ repositories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | Spec completed with 4 prioritized user stories, acceptance scenarios, and success criteria |
| II. Template-Driven | ✅ PASS | Using canonical plan template. All artifacts follow standard structure |
| III. Agent-Orchestrated | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md |
| IV. Test Optionality | ✅ PASS | Tests not explicitly requested in spec. Existing tests must continue passing (SC-006) |
| V. Simplicity and DRY | ✅ PASS | All changes are minimal, targeted edits to existing files. No new abstractions, no new modules. Reuses existing InMemoryCache |

**Gate Result**: PASS — no violations, proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/022-api-rate-limit-protection/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal contracts, no new API endpoints)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── board.py          # FR-007: Change cache TTL 120→300
│   │   └── projects.py       # FR-001/002: Add hash-based change detection to WebSocket
│   ├── services/
│   │   ├── cache.py          # FR-005: Add sub-issue cache key helper
│   │   └── github_projects/
│   │       └── service.py    # FR-005/006: Add sub-issue caching in get_sub_issues()
│   └── constants.py          # Add CACHE_PREFIX_SUB_ISSUES constant
└── tests/                    # Existing tests must pass (SC-006)

frontend/
└── src/
    └── hooks/
        └── useRealTimeSync.ts  # FR-003/004: Decouple query invalidation
```

**Structure Decision**: Web application (backend + frontend). All changes are edits to existing files — no new modules or components created. This follows the Simplicity principle (Constitution V).

## Complexity Tracking

> No violations found. No complexity justifications needed.
