# Implementation Plan: Custom Agent Creation via Chat (#agent)

**Branch**: `001-custom-agent-creation` | **Date**: 2026-02-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-custom-agent-creation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enable admin users to create fully configured custom GitHub agents through a guided multi-step conversation using the `#agent` command in both in-app chat and Signal. The system parses the command, resolves project context and status column, uses AI to generate agent configuration (name, description, system prompt), presents an interactive preview with edit loop, and upon confirmation executes a creation pipeline that produces: a persisted agent config, GitHub Project column (if new), GitHub Issue, dedicated branch with config files (YAML + README), Pull Request, and project board status update — all with best-effort execution and per-step status reporting.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript ~5.4 (frontend)
**Primary Dependencies**: FastAPI ≥0.109 + Uvicorn, React 18 + Vite 5 + TanStack Query v5, httpx ≥0.26, aiosqlite ≥0.20, github-copilot-sdk, Pydantic ≥2.5
**Storage**: SQLite (WAL mode, file-backed at `/app/data/settings.db`) — agent pipeline mappings stored as JSON in `project_settings` table
**Testing**: pytest ≥7.4 + pytest-asyncio (backend), Vitest (frontend)
**Target Platform**: Docker Compose (3 services: backend port 8000, frontend port 5173→nginx, signal-api port 8080)
**Project Type**: Web application (FastAPI backend + React SPA frontend)
**Performance Goals**: Agent creation flow completes in <5 minutes including user interaction (SC-001)
**Constraints**: No new database tables (use existing schema + migration if needed), no new pip/npm dependencies unless critical, async throughout, admin-only access
**Scale/Scope**: Single-user creation flow, one agent at a time, in-memory conversation state

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Pre-Design | Post-Design | Notes |
|-----------|------------|-------------|-------|
| **I. Specification-First** | ✅ PASS | ✅ PASS | `spec.md` complete with 5 prioritized user stories, Given/When/Then scenarios, scope boundaries, and measurable success criteria |
| **II. Template-Driven** | ✅ PASS | ✅ PASS | All artifacts follow canonical templates: spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md |
| **III. Agent-Orchestrated** | ✅ PASS | ✅ PASS | `AgentCreatorService` is single-responsibility with clear inputs (command text, session context) and outputs (response markdown, state updates, pipeline results) |
| **IV. Test Optionality** | ✅ PASS | ✅ PASS | Unit tests included for `parse_command()`, `fuzzy_match_status()`, `generate_preview()`, and pipeline execution. Not TDD-mandated |
| **V. Simplicity & DRY** | ✅ PASS | ⚠️ PASS (with justification) | Reuses `_call_completion()`, `_parse_json_response()`, `require_admin`, `BoundedDict`, `resolve_repository()`. One new table added — justified in Complexity Tracking |

**Branch/Directory Naming**: ✅ `001-custom-agent-creation` follows `###-short-name` pattern.
**Phase-Based Execution**: ✅ Spec → Plan → Tasks → Implement sequence respected.
**Independent User Stories**: ✅ All 5 stories can be developed/tested independently; P1 delivers standalone MVP.

## Project Structure

### Documentation (this feature)

```text
specs/001-custom-agent-creation/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── agent-creator-api.yaml  # Internal service contract
├── checklists/
│   └── requirements.md  # Quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── chat.py                    # MODIFY — register #agent command routing
│   ├── models/
│   │   └── agent_creator.py           # CREATE — AgentCreationState, AgentPreview, PipelineStepResult models
│   ├── services/
│   │   ├── agent_creator.py           # CREATE — AgentCreatorService (core orchestrator)
│   │   ├── ai_agent.py                # MODIFY — add generate_agent_config() method
│   │   ├── signal_chat.py             # MODIFY — register #agent command routing
│   │   └── github_projects/
│   │       └── service.py             # MODIFY — add create_branch(), commit_files(), create_pull_request() methods
│   └── migrations/
│       └── 007_agent_configs.sql      # CREATE — agent_configs table (if needed)
└── tests/
    └── unit/
        └── test_agent_creator.py      # CREATE — unit tests

frontend/
└── src/
    └── hooks/
        └── useChat.ts                 # MODIFY — pass selected project context with messages
```

**Structure Decision**: Web application structure (Option 2). All new backend code lives in `backend/src/services/agent_creator.py` as a single-responsibility service orchestrator. New Pydantic models in `backend/src/models/agent_creator.py`. Frontend changes minimal — only enriching the chat message payload with project context.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| New `agent_configs` DB table (spec said "no new tables") | Custom agents require storing multi-line system prompts, tool lists, and GitHub artifact references (issue/PR/branch). This data is structurally different from pipeline routing config. | Embedding full agent definitions as JSON in `project_settings.agent_pipeline_mappings` was rejected because: (1) would mix agent definitions with pipeline routing, violating single-responsibility; (2) multi-line system prompts in nested JSON are fragile; (3) no ability to query/deduplicate agent names across projects; (4) existing pipeline mapping schema (`list[str]` of slugs) would need breaking changes |
