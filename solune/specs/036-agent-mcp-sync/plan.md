# Implementation Plan: Agent MCP Sync — Propagate Activated & Built-in MCPs to Agent Files

**Branch**: `036-agent-mcp-sync` | **Date**: 2026-03-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/036-agent-mcp-sync/spec.md`

## Summary

Implement a centralized agent file sync utility that keeps every `.github/agents/*.agent.md` file's `mcp-servers` field in sync with the current set of activated and built-in MCPs, while unconditionally enforcing `tools: ["*"]` on all agent definitions. The sync runs on three triggers: (1) MCP activation/deactivation via the Tools page, (2) agent file creation/update, and (3) application startup. The backend service reads the current activation state from the `mcp_configurations` database table and the `BUILTIN_MCPS` registry, merges them into each agent's YAML frontmatter `mcp-servers` field (deduplicating by server key), sets `tools: ["*"]`, and commits the updated files to the repository. The frontend triggers this sync after tool toggle mutations and surfaces warnings when restrictive `tools` values are overridden.

## Technical Context

**Language/Version**: Python 3.13 (backend, floor ≥3.12), TypeScript 5.9 (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, httpx, PyYAML (backend); React 19.2, TanStack React Query 5.90 (frontend)
**Storage**: aiosqlite (`mcp_configurations` table) + GitHub repository files (agent `.agent.md` files, `mcp.json`)
**Testing**: pytest (backend), Vitest 4.0 (frontend)
**Target Platform**: Linux server (backend API), browser (frontend SPA)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Sync 25 agent files with 10 active MCPs in < 5 seconds (SC-007)
**Constraints**: Must be idempotent — repeated runs produce zero file modifications if state is unchanged (SC-004)
**Scale/Scope**: ~15 agent files, ~2 built-in MCPs, up to 25 user-activated MCPs per project

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Full spec exists at `specs/036-agent-mcp-sync/spec.md` with 5 prioritized user stories, Given-When-Then acceptance scenarios, and independent test criteria. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates. Plan follows `plan-template.md`. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | `speckit.plan` agent produces this plan with well-defined inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are included for the sync utility (backend unit tests) and the frontend integration (Vitest). This is justified by the data-integrity nature of the feature — incorrect sync could corrupt agent files across the repository. |
| **V. Simplicity and DRY** | ✅ PASS | Single centralized sync function (`sync_agent_mcps`) avoids duplication across creation/update/startup paths. No premature abstractions — the sync utility is a direct merge operation. |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/036-agent-mcp-sync/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── agent-sync-api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── services/
│   │   ├── agents/
│   │   │   ├── service.py           # Modified: add sync_agent_mcps() method
│   │   │   └── agent_mcp_sync.py    # NEW: centralized MCP sync utility
│   │   └── tools/
│   │       └── service.py           # Modified: call sync after tool operations
│   ├── api/
│   │   ├── agents.py                # Modified: trigger sync on create/update
│   │   └── tools.py                 # Modified: trigger sync on activate/deactivate
│   └── startup.py                   # Modified: trigger sync on app startup
└── tests/
    └── unit/
        └── test_agent_mcp_sync.py   # NEW: unit tests for sync utility

frontend/
├── src/
│   ├── hooks/
│   │   └── useTools.ts              # Modified: invalidate agent queries after sync
│   ├── lib/
│   │   └── buildGitHubMcpConfig.ts  # Reference only (BUILTIN_MCPS constant)
│   └── services/
│       └── api.ts                   # Modified: add syncAgentMcps API call
└── tests/
    └── unit/
        └── buildGitHubMcpConfig.test.ts  # Existing tests, no changes
```

**Structure Decision**: Web application structure (Option 2). Changes span both `backend/` and `frontend/` directories, modifying existing services and adding one new module (`agent_mcp_sync.py`) in the backend agents service.

## Complexity Tracking

> No constitution violations detected. No complexity justifications required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | — | — |
