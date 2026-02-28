# Implementation Plan: Add MCP Configuration Support for GitHub Agents in Settings Page

**Branch**: `012-mcp-settings-config` | **Date**: 2026-02-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-mcp-settings-config/spec.md`

## Summary

Add MCP (Model Context Protocol) configuration management to the Settings page, allowing authenticated GitHub OAuth users to add, view, and remove MCP server configurations scoped to their GitHub account. The implementation adds a new `mcp_configurations` SQLite table, REST API endpoints under `/api/v1/settings/mcps`, and a new `McpSettings` frontend component integrated into the existing Settings page. Server-side SSRF validation ensures endpoint URLs are safe. See [research.md](./research.md) for decision rationale.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React (frontend)  
**Primary Dependencies**: FastAPI, aiosqlite, Pydantic v2 (backend); React 18, Vite, shadcn/ui tokens (frontend)  
**Storage**: SQLite (WAL mode) via aiosqlite — new `mcp_configurations` table (migration 006)  
**Testing**: pytest (backend), Vitest + React Testing Library (frontend)  
**Target Platform**: Linux server (Docker), modern browsers  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: MCP list loads within 3 seconds (SC-006), add/remove operations reflect within 5 seconds (SC-001, SC-002)  
**Constraints**: Max 25 MCPs per user (FR-012), SSRF prevention on endpoint URLs (FR-010), OAuth session required for all operations  
**Scale/Scope**: Single Settings page sub-section, 3 API endpoints, 1 new DB table, 1 new UI component

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | `spec.md` exists with prioritized user stories (P1, P2), Given-When-Then scenarios, and edge cases |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates |
| III. Agent-Orchestrated Execution | ✅ PASS | `speckit.plan` agent produces plan.md and Phase 0/1 artifacts |
| IV. Test Optionality | ✅ PASS | Tests not mandated in spec; will follow existing test patterns if present |
| V. Simplicity and DRY | ✅ PASS | Single table, reuses existing auth/settings patterns, no new abstractions |

### Post-Design Check (Phase 1 Gate)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ PASS | All FR items (FR-001 through FR-013) have corresponding design artifacts |
| II. Template-Driven Workflow | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all generated |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan ready for handoff to `speckit.tasks` |
| IV. Test Optionality | ✅ PASS | No test mandate; tests optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Reuses `_upsert_row`, `get_session_dep`, `SettingsSection`, existing API patterns. No new frameworks or abstractions. |

## Project Structure

### Documentation (this feature)

```text
specs/012-mcp-settings-config/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions and rationale
├── data-model.md        # Phase 1: Entity definitions and migration SQL
├── quickstart.md        # Phase 1: Development setup and testing guide
├── contracts/
│   └── mcp-api.md       # Phase 1: REST API contract (GET, POST, DELETE)
├── checklists/
│   └── requirements.md  # Requirements checklist
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── migrations/
│   │   └── 006_add_mcp_configurations.sql   # New table
│   ├── models/
│   │   └── mcp.py                           # Pydantic models (request/response/row)
│   ├── services/
│   │   └── mcp_store.py                     # CRUD operations for mcp_configurations
│   └── api/
│       ├── __init__.py                      # Register MCP router
│       └── mcp.py                           # REST endpoints (GET, POST, DELETE)
└── tests/                                   # Optional: pytest tests

frontend/
├── src/
│   ├── types/
│   │   └── index.ts                         # Add MCP TypeScript interfaces
│   ├── services/
│   │   └── api.ts                           # Add mcpApi client methods
│   ├── hooks/
│   │   └── useMcpSettings.ts                # React hook for MCP async state
│   ├── components/
│   │   └── settings/
│   │       └── McpSettings.tsx              # MCP settings UI component
│   └── pages/
│       └── SettingsPage.tsx                 # Add McpSettings section
└── tests/                                   # Optional: Vitest tests
```

**Structure Decision**: Web application structure (Option 2). The repository already uses `backend/` and `frontend/` top-level directories with established patterns for models, services, API routes, components, pages, hooks, and types. All new files follow existing naming conventions and directory structure.

## Complexity Tracking

> No constitution violations detected. All design decisions follow existing patterns.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
