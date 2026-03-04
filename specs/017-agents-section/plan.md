# Implementation Plan: Agents Section on Project Board

**Branch**: `017-agents-section` | **Date**: 2026-03-03 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/017-agents-section/spec.md`

## Summary

Add an "Agents" section below the existing "Chores" section on the project board page to manage Custom GitHub Agent configurations. Users can view, create, delete, and (P3) edit agents directly from the UI. Agent creation generates `.github/agents/<slug>.agent.md` and `.github/prompts/<slug>.prompt.md` files via branch + PR workflow, reusing the existing `agent_creator.py` service logic. Agent listing merges SQLite (pre-merge) and GitHub repo (post-merge) sources, deduplicated by slug. Includes best practices documentation.

## Technical Context

**Language/Version**: Python ≥3.11 (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI ≥0.109, React 18.3, TanStack Query 5, Tailwind CSS 3.4, aiosqlite ≥0.20, PyYAML ≥6.0
**Storage**: SQLite via aiosqlite (`agent_configs` table exists), GitHub repo files via GraphQL API
**Testing**: pytest ≥7.4 + pytest-asyncio (backend), Vitest 4 + Testing Library (frontend)
**Target Platform**: Docker (Linux) — web application
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Agent list load time ≤ Chores section load time
**Constraints**: Agent prompt content ≤ 30,000 characters (GitHub limit); filenames restricted to `.`, `-`, `_`, `a-z`, `A-Z`, `0-9`
**Scale/Scope**: Single-user admin tool; tens of agents per repository

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Specification-First Development — ✅ PASS
Spec exists at `specs/017-agents-section/spec.md` with 6 prioritized user stories (P1-P3), Given-When-Then acceptance scenarios, edge cases, and clarifications.

### II. Template-Driven Workflow — ✅ PASS
All artifacts follow canonical templates. Plan uses `plan-template.md`. Spec uses `spec-template.md`.

### III. Agent-Orchestrated Execution — ✅ PASS
Plan produced by `/speckit.plan` agent. Tasks will be produced by `/speckit.tasks`. Clear handoffs defined.

### IV. Test Optionality with Clarity — ✅ PASS
Tests not mandated in spec. Will be included if requested during task generation. No TDD approach specified.

### V. Simplicity and DRY — ✅ PASS
FR-006 explicitly requires reusing `agent_creator.py` logic. Key DRY opportunities:
- `_generate_config_files()` → reuse for file generation
- `AgentPreview.name_to_slug()` → reuse for slug creation
- GitHub commit workflow (branch → commit → PR) → reuse existing `github_projects_service` methods
- Sparse input detection → reuse existing `isSparseInput()` heuristic from Chores
- No new abstractions needed; existing patterns are sufficient

## Project Structure

### Documentation (this feature)

```text
specs/017-agents-section/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── agents-api.yaml  # OpenAPI contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── agents.py              # NEW — Pydantic models for agent CRUD
│   ├── services/
│   │   ├── agent_creator.py       # MODIFY — extract shared functions for DRY reuse
│   │   └── agents/                # NEW — agents section service
│   │       ├── __init__.py
│   │       └── service.py         # AgentsService (list, create, delete, edit)
│   └── api/
│       └── agents.py              # NEW — REST router /agents/
├── tests/
│   └── unit/
│       └── test_agents_api.py     # NEW — agent API tests

frontend/
├── src/
│   ├── components/
│   │   └── agents/                # NEW — agents UI components
│   │       ├── AgentsPanel.tsx     # Container panel (mirrors ChoresPanel)
│   │       ├── AgentCard.tsx       # Individual agent card with status badge
│   │       ├── AddAgentModal.tsx   # Create agent form/modal
│   │       └── AgentChatFlow.tsx   # Sparse input refinement flow
│   ├── hooks/
│   │   └── useAgents.ts           # NEW — TanStack Query hooks
│   ├── services/
│   │   └── api.ts                 # MODIFY — add agentsApi object
│   └── pages/
│       └── ProjectBoardPage.tsx   # MODIFY — render AgentsPanel below ChoresPanel

docs/
└── custom-agents-best-practices.md  # NEW — best practices documentation
```

**Structure Decision**: Web application (frontend + backend). New files follow the exact same patterns as the existing Chores feature. Backend service in `services/agents/` module. Frontend components in `components/agents/` directory. Shared logic extracted from `agent_creator.py` into importable functions.

## Complexity Tracking

> No violations detected. No complexity justifications needed.
