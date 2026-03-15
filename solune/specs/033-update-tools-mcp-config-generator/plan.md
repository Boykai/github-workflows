# Implementation Plan: Update Tools Page — GitHub.com MCP Configuration Generator

**Branch**: `033-update-tools-mcp-config-generator` | **Date**: 2026-03-10 | **Spec**: Parent issue #3039
**Input**: Feature specification from parent issue #3039 and sub-issue #3078

## Summary

Replace the existing "Configure GitHub Toolset" section on the Tools page with a dynamic GitHub.com MCP Configuration Generator. The generator builds a ready-to-copy `mcpServers` JSON configuration block from the user's active project MCPs combined with always-included Built-In MCPs (Context7, Code Graph Context). The UI displays a syntax-highlighted, read-only code block with a one-click "Copy to Clipboard" button, Built-In badges, real-time reactivity to MCP toggle changes, and an empty-state guidance message when no user tools are active.

**Technical approach**: A pure utility function `buildGitHubMcpConfig(tools)` in `frontend/src/lib/` handles config generation (merging user tools + built-ins, deduplication, JSON serialization) decoupled from the UI. A new `GitHubMcpConfigGenerator` React component replaces the legacy `GitHubToolsetSelector` in `ToolsPanel`, consuming active tools via existing TanStack Query hooks. No backend changes are required — the feature is entirely frontend-driven using existing API responses.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.11 (backend — no changes needed)
**Primary Dependencies**: React 18, TanStack Query, Tailwind CSS, Lucide React icons, Vitest (tests)
**Storage**: N/A — reads from existing MCP tools state via `useToolsList` hook; no new persistence
**Testing**: Vitest with happy-dom environment; existing test infrastructure in `frontend/src/lib/` and `frontend/src/components/tools/`
**Target Platform**: Web browser (desktop + responsive mobile)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Config generation must be instantaneous (<10ms) for up to 25 tools (MAX_TOOLS_PER_PROJECT); real-time reactivity on MCP toggle
**Constraints**: Clipboard API with fallback for insecure contexts; JSON output must conform to GitHub.com `mcpServers` schema
**Scale/Scope**: Single page section replacement; ~400 lines of new/modified frontend code (component + utility + tests)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Feature specified via parent issue #3039 with user story, functional requirements, and acceptance criteria |
| **II. Template-Driven** | ✅ PASS | All artifacts follow `.specify/templates/` structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md; tasks phase follows |
| **IV. Test Optionality** | ✅ PASS | Tests included — the spec explicitly requires a unit-testable utility function; existing test infrastructure covers both the utility and component |
| **V. Simplicity & DRY** | ✅ PASS | Single utility function + single component; reuses existing hooks, types, and API layer; no new abstractions or backend changes |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0 research.

### Post-Phase 1 Re-check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All functional requirements mapped to design artifacts |
| **II. Template-Driven** | ✅ PASS | All generated artifacts follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Clean handoff from plan → tasks |
| **IV. Test Optionality** | ✅ PASS | Tests scoped to utility function + component rendering |
| **V. Simplicity & DRY** | ✅ PASS | No unnecessary complexity introduced; existing patterns reused |

## Project Structure

### Documentation (this feature)

```text
specs/033-update-tools-mcp-config-generator/
├── plan.md              # This file
├── research.md          # Phase 0: Technical research & decisions
├── data-model.md        # Phase 1: Entity definitions & relationships
├── quickstart.md        # Phase 1: Getting started guide
├── contracts/
│   ├── api.md           # Phase 1: API contracts (existing — no changes)
│   └── components.md    # Phase 1: Component contracts & interfaces
└── tasks.md             # Phase 2: Task decomposition (created by /speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── lib/
│   │   ├── buildGitHubMcpConfig.ts          # Core config generator utility
│   │   └── buildGitHubMcpConfig.test.ts     # Unit tests for utility
│   ├── components/tools/
│   │   ├── GitHubMcpConfigGenerator.tsx      # New config generator component
│   │   ├── GitHubToolsetSelector.tsx         # Legacy component (to be removed)
│   │   ├── ToolsPanel.tsx                    # Container (imports new component)
│   │   └── ToolsEnhancements.test.tsx        # Component integration tests
│   ├── hooks/
│   │   └── useTools.ts                       # Existing hook (no changes)
│   ├── pages/
│   │   └── ToolsPage.tsx                     # Existing page (no changes)
│   └── types/
│       └── index.ts                          # Existing types (no changes)
└── tests/
```

**Structure Decision**: Web application layout (Option 2). This feature is purely frontend — all changes are contained within `frontend/src/lib/` (utility), `frontend/src/components/tools/` (component), and their co-located test files. No backend modifications required. The existing `useToolsList` hook provides reactive MCP tool data, and the existing `McpToolConfig` type provides the data contract.

## Complexity Tracking

> No constitution violations identified. Feature follows existing patterns and adds minimal new code.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
