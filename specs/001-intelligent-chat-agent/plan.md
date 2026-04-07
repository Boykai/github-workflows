# Implementation Plan: Intelligent Chat Agent (Microsoft Agent Framework)

**Branch**: `001-intelligent-chat-agent` | **Date**: 2026-04-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-intelligent-chat-agent/spec.md`

## Summary

Replace the existing completion-based `AIAgentService` (raw LLM calls + manual JSON parsing) with a **Microsoft Agent Framework** `Agent` that uses function tools to take actions, `AgentSession` for multi-turn memory, and middleware for logging/security. The hardcoded priority-dispatch cascade in `chat.py` (`_handle_transcript_upload` → `_handle_feature_request` → `_handle_status_change` → `_handle_task_generation`) becomes the agent's natural reasoning — instead of `if/elif` tiers, the agent decides which tool to call based on its instructions. The REST API contract (`ChatMessage` schema, existing endpoints) stays the same so the frontend needs minimal changes. A new SSE streaming endpoint is additive.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript ~6.0.2 / React ^19.2.0 (frontend)
**Primary Dependencies**: FastAPI (backend HTTP), Microsoft Agent Framework (`agent-framework-core`, `agent-framework-github-copilot`, `agent-framework-azure-ai`), Pydantic v2 (models), aiosqlite (storage)
**Storage**: SQLite via aiosqlite (existing `database.py` — chat messages, sessions, proposals, recommendations); `AgentSession.state` supplements but does not replace SQLite
**Testing**: pytest + pytest-asyncio (backend), Vitest + @testing-library/react (frontend)
**Target Platform**: Linux server (Docker container), browser SPA (Vite-built React)
**Project Type**: Web application (backend + frontend monorepo under `solune/`)
**Performance Goals**: First streaming token within 2 seconds; 50 concurrent sessions without cross-contamination or degradation
**Constraints**: API contract backwards-compatible (ChatMessage schema unchanged); deprecate-not-delete old layers; `ai_enhance=False` bypass preserved
**Scale/Scope**: Single-instance deployment (SQLite), ~12 frontend pages, ~1000-line AI service module replaced

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Specification-First Development** | ✅ PASS | `spec.md` contains 6 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, edge cases, and 20 functional requirements |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` — plan.md, research.md, data-model.md, contracts/, quickstart.md |
| **III. Agent-Orchestrated Execution** | ✅ PASS | This plan is produced by the `speckit.plan` agent with well-defined inputs (spec.md) and outputs (Phase 0–1 artifacts) |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are included per spec (FR-006 session isolation, SC-006 80% coverage of new code). New `test_agent_tools.py`, `test_chat_agent.py`; updated `test_api_chat.py` |
| **V. Simplicity and DRY** | ✅ PASS | Single agent replaces 4 separate dispatch handlers and 3 prompt modules. No new abstractions beyond what Agent Framework provides. Deprecate-not-delete avoids premature removal |

**Gate result**: PASS — all principles satisfied. No complexity violations.

## Project Structure

### Documentation (this feature)

```text
specs/001-intelligent-chat-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — developer getting-started
├── contracts/           # Phase 1 output — API contracts
│   ├── streaming-sse.md # SSE streaming endpoint contract
│   └── agent-tools.md   # Agent tool schemas
└── checklists/
    └── requirements.md  # Requirements traceability
```

### Source Code (repository root)

```text
solune/backend/
├── pyproject.toml                          # MODIFY: add agent-framework-* deps
├── src/
│   ├── config.py                           # MODIFY: no new settings needed (reuse ai_provider, azure_openai_*, copilot_model)
│   ├── api/
│   │   └── chat.py                         # MODIFY: replace priority dispatch with agent_service.run()
│   ├── models/
│   │   └── chat.py                         # UNCHANGED: ChatMessage schema preserved
│   ├── prompts/
│   │   ├── agent_instructions.py           # CREATE: unified agent system prompt
│   │   ├── task_generation.py              # DEPRECATE: add warnings
│   │   ├── issue_generation.py             # DEPRECATE: add warnings
│   │   └── transcript_analysis.py          # DEPRECATE: add warnings
│   └── services/
│       ├── agent_tools.py                  # CREATE: @tool-decorated functions
│       ├── agent_provider.py               # CREATE: factory for Copilot / Azure agents
│       ├── chat_agent.py                   # CREATE: ChatAgentService (session mgmt, response conversion)
│       ├── agent_middleware.py             # CREATE: logging + security middleware
│       ├── ai_agent.py                     # DEPRECATE: add warnings
│       ├── completion_providers.py         # DEPRECATE: add warnings
│       └── signal_chat.py                  # MODIFY: use ChatAgentService.run()
└── tests/
    └── unit/
        ├── test_agent_tools.py             # CREATE: tool tests with mocked context
        ├── test_chat_agent.py              # CREATE: session/response conversion tests
        └── test_api_chat.py                # MODIFY: mock ChatAgentService instead of ai_service

solune/frontend/
├── src/
│   ├── services/
│   │   └── api.ts                          # MODIFY: add streaming sendMessage variant
│   └── components/
│       └── chat/
│           ├── ChatInterface.tsx           # MODIFY: use streaming when available
│           └── MessageBubble.tsx           # MODIFY: progressive token rendering
└── (no new test files required — existing chat tests cover integration)
```

**Structure Decision**: Web application structure — the project already uses `solune/backend/` and `solune/frontend/` as established roots. All new files are placed within the existing directory hierarchy. No new top-level directories.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
