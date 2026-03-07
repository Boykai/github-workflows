# Implementation Plan: Agents Page — Sun/Moon Avatars, Featured Agents, Inline Editing with PR Flow, Bulk Model Update, Repo Name Display & Tools Editor

**Branch**: `029-agents-page-ux` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/029-agents-page-ux/spec.md`

## Summary

Enhance the Agents page with six capabilities: (1) deterministic sun/moon themed SVG avatars assigned via a hash of the agent slug, (2) an improved "Featured Agents" section that supplements usage-ranked agents with recently created agents (within 3 days) to fill up to 3 slots, (3) inline agent definition editing through the existing modal editor with a persistent unsaved-changes indicator and a navigation-blocking confirmation modal that auto-creates a GitHub PR on save, (4) a "Bulk Update All Models" action with a confirmation dialog listing all affected agents, (5) repository name display showing only the repo name (not owner/repo) with CSS text-overflow ellipsis in a fitted bubble, and (6) an interactive tools editor within the agent configuration allowing add, remove, and reorder operations. The frontend extends `AgentCard.tsx`, `AgentsPanel.tsx`, and `AddAgentModal.tsx` with new components for avatars, tools editing, and bulk model update. The backend adds a `PATCH /api/v1/agents/{project_id}/bulk-model` endpoint for batch model updates. All agent edits continue to use the existing PR-based save flow via `agent_creator.py` → `commit_files_workflow()`.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — existing `agent_configs` table; Git-backed `.github/agents/*.agent.md` files on repo default branch
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Avatar rendering < 50ms; Featured Agents calculation < 100ms; Inline edit form interaction < 100ms; Bulk model update < 60s for up to 50 agents; PR creation on save < 30s
**Constraints**: No new UI library additions; sun/moon icons as inline SVG (no external avatar library); all agent edits must create PRs (existing pattern); agent config file format (.agent.md YAML frontmatter) unchanged
**Scale/Scope**: ~6 modified frontend components, ~3 new frontend components, 1 new backend endpoint, 1 new hook, modifications to existing hooks and API client

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 20 functional requirements, 8 success criteria, edge cases |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass |
| **V. Simplicity/DRY** | ✅ PASS | Extends existing agent components and patterns; reuses lucide-react icons, TanStack Query, existing API client and PR creation flow; no new libraries required; avatars use inline SVG (no library) |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-020) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `AgentCard`, `AgentsPanel`, `AddAgentModal` components. Avatars use a simple deterministic hash → SVG index mapping with no external library. Featured Agents extends existing sort logic with a date filter. Inline editing extends the existing modal editor. Bulk model update is a single new endpoint wrapping the existing per-agent update logic. Tools editor reuses existing `useAgentTools` hook and `ToolSelectorModal`. Repo name display is a CSS-only change. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/029-agents-page-ux/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R7)
├── data-model.md        # Phase 1: Entity definitions, types, state machines
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   ├── api.md           # Phase 1: REST API endpoint contracts
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── agents.py                   # MODIFIED: Add bulk-model endpoint
│   ├── models/
│   │   └── agents.py                   # MODIFIED: Add BulkModelUpdate request/response models
│   └── services/
│       └── agents/
│           └── service.py              # MODIFIED: Add bulk_update_models() method

frontend/
├── src/
│   ├── components/
│   │   └── agents/
│   │       ├── AgentCard.tsx            # MODIFIED: Add avatar, repo name display, edit button enhancements
│   │       ├── AgentsPanel.tsx          # MODIFIED: Enhanced Featured Agents logic (date supplement), bulk update button
│   │       ├── AddAgentModal.tsx        # MODIFIED: Enhanced inline editing with unsaved-changes tracking
│   │       ├── AgentAvatar.tsx          # NEW: Sun/moon themed SVG avatar component
│   │       ├── BulkModelUpdateDialog.tsx # NEW: Confirmation dialog for bulk model update
│   │       └── ToolsEditor.tsx          # NEW: Interactive tools list editor (add/remove/reorder)
│   ├── hooks/
│   │   ├── useAgents.ts                # MODIFIED: Add useBulkUpdateModels mutation
│   │   └── useAgentTools.ts            # MODIFIED: Enhanced for reorder support
│   ├── pages/
│   │   └── AgentsPage.tsx              # MODIFIED: Wire unsaved-changes navigation guard, bulk update action
│   └── services/
│       └── api.ts                       # MODIFIED: Add bulkUpdateModels API method
```

**Structure Decision**: Web application (frontend/ + backend/). All changes extend existing directories and components. New files are scoped to `frontend/src/components/agents/` following the existing domain-scoped pattern. Backend changes are minimal — one new endpoint and one new service method for bulk model updates. The avatar component is a pure presentational component with no external dependencies. The tools editor reuses the existing `useAgentTools` hook infrastructure.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Inline SVG avatars (no library) | 12 hand-crafted sun/moon SVG icons embedded in a single component; deterministic hash of slug selects index. Zero runtime dependency, instant rendering, fully customizable styling. | `boring-avatars` library (rejected: adds dependency for a simple use case; our icons are thematic, not generic geometric shapes; YAGNI) |
| Frontend-computed usage count | Usage count is already computed client-side from column assignments (`agentUsageCounts`). No backend change needed for Featured Agents ranking. | Backend usage tracking table (rejected: over-engineered; current column-assignment count is sufficient and already implemented) |
| Existing modal for inline editing | The `AddAgentModal` already supports edit mode with structured form fields. Enhance it with unsaved-changes tracking and navigation guard rather than building a new inline editor. | Full inline editor replacing the card (rejected: significantly more complex; modal pattern is established and familiar to users; same functionality with less risk) |
| Single bulk endpoint | One `PATCH /bulk-model` endpoint that updates all agents' runtime model preferences in SQLite in a single call. No PRs created — model preferences are local overrides, consistent with existing per-agent model update behavior. | Frontend-only batch calling update N times (rejected: N API calls vs. 1; less atomic error reporting) |
