# Implementation Plan: Agents Page Audit

**Branch**: `043-agents-page-audit` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/043-agents-page-audit/spec.md`

## Summary

Conduct a comprehensive audit of the Agents page (`AgentsPage.tsx`) and all its child components — the Agent Catalog (hero, cards, inline editor, modals, search, bulk update) and the Orbital Map / Column Assignments panel (drag-and-drop tiles, preset selector, save bar, add-agent popover). The primary goal is to enforce modular component architecture (≤250 lines per file), ensure reliable loading/error/empty states, achieve WCAG AA accessibility compliance, polish text/copy and UX feedback, verify responsive design and dark mode, improve type safety, add comprehensive test coverage, and enforce code hygiene. This is a frontend-only audit-and-refactor effort affecting approximately 20 components totaling ~5,400 lines across `src/components/agents/`, `src/components/board/`, `src/pages/AgentsPage.tsx`, and 3 custom hooks.

## Technical Context

**Language/Version**: TypeScript 5.9 with React 19.2
**Primary Dependencies**: React 19, TanStack React Query 5.90, Tailwind CSS v4.2 (via `@tailwindcss/vite`), Radix UI (Slot 1.2, Tooltip 1.2), Lucide React 0.577, class-variance-authority 0.7, tailwind-merge 3.5, react-router-dom 7.13, @dnd-kit/core 6.3 + @dnd-kit/sortable 10.0
**Storage**: N/A (frontend-only; backend uses SQLite with FastAPI)
**Testing**: Vitest 4.0 (unit, happy-dom), Testing Library React 16.3, jest-axe 10.0 (accessibility)
**Target Platform**: Modern browsers (desktop, tablet, mobile web)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Page interactive within 3 seconds; user actions reflected in under 1 second perceived response time; smooth scrolling and sub-100ms interaction response with 50+ agents in catalog
**Constraints**: WCAG AA minimum (4.5:1 contrast normal text, 3:1 large text/UI); 44×44px minimum touch targets on mobile; no hardcoded colors — all must reference design tokens
**Scale/Scope**: Single page audit affecting ~20 frontend components, ~3 custom hooks, 1 page component; no new features, purely audit and refinement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 7 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and 24 functional requirements |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | This plan is produced by the `speckit.plan` agent with clear inputs (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md) |
| **IV. Test Optionality** | ✅ PASS | Tests are explicitly requested in User Story 6 (P3). Existing tests (AgentsPanel, AddAgentModal, AgentSaveBar, AgentTile, ThemedAgentIcon) will be verified; new hook and component tests will be added per FR-019 and FR-020 |
| **V. Simplicity and DRY** | ✅ PASS | Audit refactors toward simplicity — decomposing oversized components, extracting hooks, consolidating patterns. No new abstractions introduced beyond what the spec requires |

### Post-Phase 1 Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Data model and contracts align with all 7 user stories and 24 functional requirements |
| **II. Template-Driven** | ✅ PASS | All generated artifacts (research.md, data-model.md, contracts/, quickstart.md) follow prescribed templates |
| **III. Agent-Orchestrated** | ✅ PASS | Clear handoff to `speckit.tasks` after this phase completes |
| **IV. Test Optionality** | ✅ PASS | Test requirements clearly scoped: hook tests via renderHook(), component interaction tests, edge case coverage per FR-019/FR-020 |
| **V. Simplicity and DRY** | ✅ PASS | No new abstractions; refactors consolidate duplicate patterns (hardcoded colors → design tokens, inconsistent focus styles → celestial-focus, oversized components → sub-components) |

## Project Structure

### Documentation (this feature)

```text
specs/043-agents-page-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — design system, accessibility, responsive, performance research
├── data-model.md        # Phase 1 output — entity model for Agents page components
├── quickstart.md        # Phase 1 output — developer guide for running the audit
├── contracts/           # Phase 1 output — component interface contracts
│   └── component-contracts.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/
│   │   ├── AgentsPage.tsx                     # Main page component (~230 lines) — PRIMARY AUDIT TARGET
│   │   └── AgentsPipelinePage.tsx              # Pipeline visualization with agent config (~417 lines)
│   ├── components/
│   │   ├── agents/                            # Agent Catalog components
│   │   │   ├── AgentsPanel.tsx                # Catalog container with search, sort, featured, grid (~565 lines)
│   │   │   ├── AgentCard.tsx                  # Individual agent card with badges, actions (~286 lines)
│   │   │   ├── AgentAvatar.tsx                # Agent avatar with themed icon fallback (~210 lines)
│   │   │   ├── AgentInlineEditor.tsx          # Expandable editor for agent config (~272 lines)
│   │   │   ├── AddAgentModal.tsx              # Agent creation/edit modal (~520 lines)
│   │   │   ├── AgentIconPickerModal.tsx       # Icon selection modal with catalog (~117 lines)
│   │   │   ├── AgentIconCatalog.tsx           # Reusable icon grid for selection (~70 lines)
│   │   │   ├── AgentChatFlow.tsx              # Chat flow component (~199 lines)
│   │   │   ├── BulkModelUpdateDialog.tsx      # Two-step bulk model update dialog (~165 lines)
│   │   │   └── ToolsEditor.tsx                # Ordered tool list with CRUD (~132 lines)
│   │   ├── board/                             # Orbital Map / Column Assignments
│   │   │   ├── AgentConfigRow.tsx             # DnD orchestrator with presets (~480 lines)
│   │   │   ├── AgentPresetSelector.tsx        # Preset buttons + saved pipelines dropdown (~519 lines)
│   │   │   ├── AgentTile.tsx                  # Sortable agent tile in column (~308 lines)
│   │   │   ├── AgentColumnCell.tsx            # Droppable column container (~168 lines)
│   │   │   ├── AddAgentPopover.tsx            # Dropdown for adding agents to columns (~208 lines)
│   │   │   ├── AgentDragOverlay.tsx           # Floating drag preview (~69 lines)
│   │   │   └── AgentSaveBar.tsx               # Floating save/discard bar (~55 lines)
│   │   ├── common/
│   │   │   ├── ThemedAgentIcon.tsx            # Celestial-themed agent icon component (~95 lines)
│   │   │   ├── agentIcons.tsx                 # Icon name/slug mapping registry (~547 lines)
│   │   │   ├── CelestialCatalogHero.tsx       # Shared hero section (~119 lines)
│   │   │   ├── CelestialLoader.tsx            # Loading spinner (~45 lines)
│   │   │   ├── ErrorBoundary.tsx              # Error catch boundary (~69 lines)
│   │   │   └── ProjectSelectionEmptyState.tsx # Empty state UI (~176 lines)
│   │   └── ui/
│   │       ├── button.tsx                     # Shared button (CVA variants, celestial-focus)
│   │       ├── card.tsx                       # Card component with consistent styling
│   │       ├── tooltip.tsx                    # Radix tooltip wrapper with contentKey
│   │       └── confirmation-dialog.tsx        # Shared confirmation modal
│   ├── hooks/
│   │   ├── useAgents.ts                       # Agent CRUD hooks (~108 lines)
│   │   ├── useAgentConfig.ts                  # Agent-to-column mapping state + dirty tracking (~349 lines)
│   │   └── useAgentTools.ts                   # Tool assignment hooks (~39 lines)
│   ├── services/
│   │   └── api.ts                             # API client (agentsApi group: list, create, update, delete, chat, bulkUpdateModels, syncMcps)
│   ├── types/
│   │   └── index.ts                           # AgentConfig, AgentCreate, AgentUpdate, AgentAssignment, AvailableAgent, etc.
│   ├── constants/
│   │   ├── tooltip-content.ts                 # Centralized tooltip strings (agents.*, board.*, chat.*)
│   │   └── chat-placeholders.ts               # Chat placeholder strings
│   ├── lib/
│   │   └── utils.ts                           # cn() — clsx + tailwind-merge
│   └── index.css                              # Celestial design system tokens + custom classes
└── package.json                               # React 19, Vitest, Tailwind v4
```

**Structure Decision**: Web application (frontend + backend). This audit is frontend-only. All changes target `solune/frontend/src/` — primarily `pages/AgentsPage.tsx`, `components/agents/`, `components/board/Agent*`, and `hooks/useAgent*.ts`. No backend modifications are needed. The existing project structure is well-established and no structural reorganization is planned.

## Complexity Tracking

> No violations identified. All changes follow simplicity principles — decomposing oversized components into sub-components, extracting complex state into hooks, consolidating hardcoded values into design tokens, and standardizing focus indicators. No new abstractions, libraries, or architectural changes are introduced.
