# Implementation Plan: Add Tools Page with MCP Configuration Upload and Agent Tool Selection via Grid Modal

**Branch**: `027-mcp-tools-page` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/027-mcp-tools-page/spec.md`

## Summary

Add a dedicated Tools page for managing MCP (Model Context Protocol) configurations, positioned directly below the Agents page in the left navigation bar. The page mirrors the Agents page layout and allows users to upload MCP configuration JSON files that are validated and synced to the connected GitHub repository via the Contents API (targeting `.copilot/mcp.json`). Each MCP tool is displayed as a card with sync status tracking (Synced/Pending/Error) and re-sync/delete actions. On the Agent creation/edit form, a new "Add Tools" section opens a full overlay modal with a responsive tile grid of available MCP tools, supporting multi-select with visual checkmarks. Selected tools persist as removable chips on the agent form and are stored via a junction table alongside the existing `agent_configs.tools` JSON column.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, react-router-dom v7, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — extending existing `mcp_configurations` table + new `agent_tool_associations` junction table
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers, 768px minimum viewport width; Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Tools page load < 2s (SC-001); Upload + sync < 30s (SC-002); Tool selection in modal < 60s (SC-004)
**Constraints**: No new UI libraries; must not break existing MCP Settings page or Agent CRUD; 256 KB max config file size; 25 MCP configs per user limit
**Scale/Scope**: ~8 new frontend components, ~2 new hooks, 1 new backend service, 1 new migration, 5+ new REST endpoints, ~3 modified frontend components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 20 functional requirements (FR-001–FR-020), 12 success criteria, edge cases, key entities |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing MCP table and patterns; reuses existing UI components (Card, Button, Badge, Input); mirrors AgentsPage structure without premature abstraction; new `ToolsService` follows established service pattern |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts (data-model.md, contracts/, quickstart.md) trace back to spec FRs (FR-001–FR-020) and success criteria (SC-001–SC-012) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected by schema extension (ALTER TABLE with defaults) |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `mcp_configurations` table via ALTER TABLE (no new table for tools). Mirrors AgentsPage/AgentsPanel patterns without a generic ResourcePage abstraction (only 2 consumers — YAGNI). ToolsService follows MCP store + agents service patterns. Tool selector modal is a standalone component, not over-engineered. Dual storage for agent-tool associations (JSON column + junction table) justified by bidirectional query needs. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/027-mcp-tools-page/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R8)
├── data-model.md        # Phase 1: Entity definitions, types, DB schema, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py                  # MODIFIED: Register tools router
│   │   └── tools.py                     # NEW: CRUD + sync endpoints for MCP tools
│   ├── models/
│   │   └── tools.py                     # NEW: Pydantic models (McpToolConfig, validation)
│   ├── services/
│   │   └── tools/
│   │       ├── __init__.py              # NEW: Re-exports
│   │       └── service.py              # NEW: ToolsService (CRUD + validation + GitHub sync)
│   └── migrations/
│       └── 014_extend_mcp_tools.sql     # NEW: Extend mcp_configurations + agent_tool_associations
└── tests/
    └── unit/                            # Existing tests — no changes expected

frontend/
├── src/
│   ├── pages/
│   │   └── ToolsPage.tsx                # NEW: Tools page mirroring AgentsPage layout
│   ├── components/
│   │   ├── tools/                       # NEW directory
│   │   │   ├── ToolsPanel.tsx           # NEW: Tool catalog panel
│   │   │   ├── ToolCard.tsx             # NEW: Individual tool card with sync status
│   │   │   ├── UploadMcpModal.tsx       # NEW: Upload/paste MCP config modal
│   │   │   ├── ToolSelectorModal.tsx    # NEW: Tile-grid tool selection modal
│   │   │   └── ToolChips.tsx            # NEW: Removable chip display for selected tools
│   │   └── agents/
│   │       └── AddAgentModal.tsx        # MODIFIED: Add "Add Tools" section
│   ├── hooks/
│   │   ├── useTools.ts                  # NEW: Tool CRUD state management
│   │   └── useAgentTools.ts             # NEW: Agent-tool assignment management
│   ├── services/
│   │   └── api.ts                       # MODIFIED: Add toolsApi + extend agentsApi
│   ├── types/
│   │   └── index.ts                     # MODIFIED: Add MCP tool TypeScript interfaces
│   └── constants.ts                     # MODIFIED: Add Tools nav route
```

**Structure Decision**: Web application (frontend/ + backend/). The repo already has `frontend/` and `backend/` directories. A new `frontend/src/components/tools/` directory is added for tool management components, following the existing pattern of domain-scoped component directories (`agents/`, `board/`, `chores/`, `pipeline/`). A new `backend/src/services/tools/` service directory follows the pattern of `agents/` and `chores/` services. The existing `mcp_configurations` database table is extended via ALTER TABLE to avoid creating a redundant table.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Extend `mcp_configurations` table | MCP tools are the same conceptual entity as existing MCP configs, extended with sync tracking and project scoping | Creating a new `mcp_tools` table (rejected: duplicates existing data, breaks Settings page MCP list) |
| Dual storage for agent-tool associations | JSON column on agents for fast reads + junction table for reverse lookups (find agents by tool) | JSON column only (rejected: inefficient reverse queries for delete warnings per FR-016) |
| Direct commit sync (not PR-based) | MCP configs are infrastructure; PRs add unnecessary workflow overhead compared to agent definitions which have code review needs | PR-based sync like agent creation (rejected: over-engineered for config files) |
| No generic ResourcePage wrapper | Only 2 consumers (Agents, Tools); abstraction would be premature per Constitution Principle V | Generic wrapper (rejected: YAGNI — complex prop drilling for 2 pages) |
