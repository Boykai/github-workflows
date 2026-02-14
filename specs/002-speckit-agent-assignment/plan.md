# Implementation Plan: Spec Kit Custom Agent Assignment by Status

**Branch**: `002-speckit-agent-assignment` | **Date**: 2026-02-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-speckit-agent-assignment/spec.md`

## Summary

Replace the single `custom_agent` field in workflow configuration with a per-status agent mapping that orchestrates Spec Kit custom agents across the full issue lifecycle. When an issue enters Backlog, assign `speckit.specify`; on Ready, run `speckit.plan` then `speckit.tasks` sequentially; on In Progress, assign `speckit.implement`. Extend the existing polling service to detect comment-based completion markers (`<agent-name>: All done!>`) for specify/plan/tasks agents and use existing PR-based detection for implement. Pipeline state is held in-memory and reconstructed from GitHub Issue comments on restart.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, httpx, Pydantic 2.x, pydantic-settings  
**Storage**: In-memory (dicts/lists); GitHub Issue comments as durable source of truth  
**Testing**: pytest, pytest-asyncio, ruff, black  
**Target Platform**: Linux server (Docker)  
**Project Type**: Web application (backend + frontend)  
**Performance Goals**: Agent assignment within 10s of status change; sequential agent handoff within 30s of completion detection  
**Constraints**: In-memory state (no database); GitHub API rate limits (5000 req/hr authenticated); polling interval configurable (default 60s)  
**Scale/Scope**: Single-user/small-team project management tool; <100 concurrent issues tracked

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Specification-First Development — PASS

The feature has a complete `spec.md` with 4 prioritized user stories (P1-P4), Given-When-Then acceptance scenarios for each, clear scope boundaries, and 5 resolved clarifications. All requirements are captured before planning.

### Principle II: Template-Driven Workflow — PASS

All artifacts follow canonical templates from `.specify/templates/`. This plan follows the `plan-template.md` structure. Output artifacts (research.md, data-model.md, contracts/, quickstart.md) will follow their respective templates.

### Principle III: Agent-Orchestrated Execution — PASS

This feature is itself about agent orchestration. The specify→plan→tasks→implement pipeline aligns directly with this principle. Each agent has ONE clear purpose, operates on well-defined inputs, and hands off via explicit transitions (completion markers).

### Principle IV: Test Optionality — PASS

Tests are not explicitly requested in the feature spec. The existing test suite covers the current workflow. New tests may be added during implementation if needed but are not mandated by this plan.

### Principle V: Simplicity and DRY — PASS

The approach extends existing services (polling, orchestrator, GitHub API) rather than creating new abstractions. The agent mapping is a simple dict (`Dict[str, List[str]]`). Pipeline state is a lightweight dataclass. No new frameworks or patterns introduced.

**Gate Result**: ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/002-speckit-agent-assignment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── chat.py              # Update WorkflowConfiguration (agent_mappings field)
│   ├── services/
│   │   ├── workflow_orchestrator.py  # Refactor to use agent mappings, add pipeline state
│   │   ├── copilot_polling.py        # Extend to poll Backlog/Ready for completion comments
│   │   └── github_projects.py       # Add check_agent_completion_comment() method
│   └── api/
│       └── workflow.py           # Update config endpoints for agent mappings
└── tests/
    ├── unit/
    │   ├── test_workflow_orchestrator.py  # Update for new pipeline logic
    │   └── test_copilot_polling.py       # Update for multi-status polling
    └── integration/
        └── test_custom_agent_assignment.py  # Update for agent mapping

frontend/
└── src/
    └── types/
        └── index.ts              # Update WorkflowConfiguration type (agent_mappings)
```

**Structure Decision**: Option 2 — Web application with `backend/` (Python/FastAPI) and `frontend/` (TypeScript/Vite). This matches the existing repository structure. Changes are concentrated in the backend services layer with a minor frontend type update.

## Complexity Tracking

> No violations found. All Constitution principles pass without justification needed.
