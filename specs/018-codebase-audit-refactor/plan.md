# Implementation Plan: Codebase Audit & Refactor

**Branch**: `018-codebase-audit-refactor` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/018-codebase-audit-refactor/spec.md`

## Summary

Full-sweep refactor of a FastAPI + React codebase: modernize all dependencies (remove unused `agent-framework-core`, bump SDK/library versions), DRY up duplicated patterns (CopilotClient caching, fallback chains, retry logic, header construction), fix anti-patterns (hardcoded model in GraphQL, in-memory chat state → SQLite, dead `delete_files` stub, dual service initialization), and add intelligent GitHub API rate-limit management (500ms inter-call buffers, adaptive polling with 60s base / 2x backoff / 5min cap). All changes within existing file boundaries.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript 5.4 (frontend)
**Primary Dependencies**: FastAPI, httpx, github-copilot-sdk, openai, azure-ai-inference, aiosqlite (backend); React 18, Vite 5, @tanstack/react-query 5, vitest 4 (frontend)
**Storage**: SQLite with WAL mode, 10 existing migrations (adding 011 for chat persistence)
**Testing**: pytest + pytest-asyncio (backend), vitest + @playwright/test (frontend)
**Target Platform**: Linux server (Docker), single-instance deployment
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Stay within GitHub's 5,000 req/hour REST / 5,000 points/hour GraphQL rate limits; ≥500ms between consecutive API calls
**Constraints**: Refactor in-place (no new files/modules except SQL migration); backward-compatible API endpoints; ruff formatting, 100-char line length, double quotes
**Scale/Scope**: ~4,800-line service.py, ~700-line chat.py, ~300-line completion_providers.py, ~110-line model_fetcher.py, ~200-line github_commit_workflow.py; ~15 affected backend files, ~1 frontend file (package.json)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — PASS
Prioritized user stories (P1×2, P2×2) with Given-When-Then acceptance scenarios exist in spec.md. All 5 clarifications resolved via `/speckit.clarify`.

### II. Template-Driven Workflow — PASS
Using canonical spec and plan templates. All artifacts follow `.specify/templates/`.

### III. Agent-Orchestrated Execution — PASS
Following specify → plan → tasks → implement pipeline. Single-responsibility phases.

### IV. Test Optionality with Clarity — PASS
FR-022 mandates test updates to reflect refactored interfaces. Tests are required because the spec explicitly specifies them ("run pytest after backend changes, npm test after frontend changes").

### V. Simplicity and DRY — PASS (with justified additions)
The entire feature is about DRY consolidation and simplification. New abstractions (`CopilotClientPool`, `_with_fallback` helper) are justified by eliminating copy-pasted code in 3+ locations. No premature abstraction — each consolidation addresses verified duplication. See Complexity Tracking for the one new file (SQL migration).

## Project Structure

### Documentation (this feature)

```text
specs/018-codebase-audit-refactor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── pyproject.toml                              # FR-001..003: dependency updates
├── src/
│   ├── main.py                                 # FR-016: verify app.state only
│   ├── dependencies.py                         # FR-016: remove module-global fallbacks
│   ├── utils.py                                # FR-008: BoundedDict/BoundedSet (existing)
│   ├── api/
│   │   ├── chat.py                             # FR-015: SQLite persistence; FR-017: bound collections
│   │   └── workflow.py                         # FR-017: bound _recent_requests
│   ├── models/
│   │   ├── chat.py                             # FR-015: models already exist (ChatMessage)
│   │   └── recommendation.py                   # FR-015: AITaskProposal, IssueRecommendation
│   ├── migrations/
│   │   └── 011_chat_persistence.sql            # FR-015: new migration (exception: required by migration system)
│   ├── services/
│   │   ├── completion_providers.py             # FR-007/008: extract CopilotClientPool
│   │   ├── model_fetcher.py                    # FR-007/008: use shared CopilotClientPool
│   │   ├── github_commit_workflow.py           # FR-014: implement file deletion
│   │   ├── github_auth.py                      # FR-015: document OAuth in-memory limitation
│   │   ├── github_projects/
│   │   │   ├── graphql.py                      # FR-013: parameterize model in ASSIGN_COPILOT_MUTATION
│   │   │   └── service.py                      # FR-009..011, FR-018..021: DRY + rate limiting
│   │   ├── copilot_polling/
│   │   │   ├── state.py                        # FR-017: bound processed_issues
│   │   │   └── polling_loop.py                 # FR-019: adaptive polling (60s/2x/5min)
│   │   └── workflow_orchestrator/
│   │       ├── transitions.py                  # FR-017: bound _pipeline_states, etc.
│   │       ├── config.py                       # FR-017: bound _workflow_configs
│   │       └── orchestrator.py                 # FR-017: bound _tracking_table_cache
│   └── services/database.py                    # existing — used for migrations
└── tests/                                      # FR-022: update tests

frontend/
├── package.json                                # FR-004: dependency updates
```

**Structure Decision**: Existing web application layout (backend + frontend). All changes occur within existing files except one SQL migration file required by the migration system's numbered-file convention.

## Complexity Tracking

| Addition | Why Needed | Simpler Alternative Rejected Because |
|----------|------------|-------------------------------------|
| `011_chat_persistence.sql` (new file) | FR-015 requires SQLite persistence; migration system requires numbered SQL files in `migrations/` | Cannot modify schema without a migration file — this is a hard constraint of the existing `_run_migrations()` system |
| `CopilotClientPool` class in `completion_providers.py` | FR-007/008: eliminates identical cache logic duplicated across 2 files; adds bounded eviction + cleanup | Leaving duplication means bugs fixed in one place are missed in the other; model_fetcher currently has no `cleanup()` |
| `_with_fallback()` helper in `service.py` | FR-009: 3 methods use identical try-primary/catch/try-fallback/log chains | Inline fallback requires maintaining identical error handling in 3+ places; helper is ~15 lines |
