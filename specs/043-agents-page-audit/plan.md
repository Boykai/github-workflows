# Implementation Plan: Agents Page Audit

**Branch**: `043-agents-page-audit` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/043-agents-page-audit/spec.md`

## Summary

Comprehensive audit of the Agents page (~20 components, ~5,400 lines of agent-related code) to enforce modern best practices, modular design, accurate text/copy, and zero bugs. The audit covers component decomposition (reducing oversized files to ≤250 lines), accessibility (WCAG AA), error/loading/empty states, type safety (zero `any`), test coverage, and UI/UX polish. No new features or backend changes — this is a pure frontend refactoring and quality improvement effort.

The approach follows a phased strategy: structural decomposition first (unblocking all other improvements), then state handling, accessibility, UX polish, testing, and finally validation.

## Technical Context

**Language/Version**: TypeScript 5.9 + React 19.2
**Primary Dependencies**: TanStack React Query 5.90, Tailwind CSS 4.2, Radix UI primitives, Lucide React (icons), @dnd-kit/core 6.3 + @dnd-kit/sortable 10.0 (drag-and-drop), Vite 7.3
**Storage**: N/A (frontend-only audit; backend API consumed as-is)
**Testing**: Vitest 4.0.18 + @testing-library/react + @testing-library/user-event
**Target Platform**: Web (modern browsers, desktop-first responsive design 768px–1920px)
**Project Type**: Web application (monorepo: `solune/frontend/`)
**Performance Goals**: Page interactive within 3 seconds; <1 second perceived response for mutations; smooth rendering with 50+ agents in catalog
**Constraints**: WCAG AA minimum (4.5:1 contrast ratio, 44×44px touch targets); no hardcoded colors; all styling via Tailwind utility classes; no inline `style={}`; zero `any` types; zero ESLint warnings
**Scale/Scope**: ~20 components across `src/components/agents/` (10 files, 2,536 lines), `src/components/board/Agent*` (7 files, ~1,981 lines), shared components in `src/components/common/` (~694 agent-related lines), 3 custom hooks (496 lines), 1 page file (251 lines)

## Constitution Check (Pre-Phase 0)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Specification-First** | ✅ PASS | `spec.md` contains 7 prioritized user stories (P1–P3) with Given-When-Then acceptance scenarios, clear scope boundaries, and independent testing criteria |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/`. This plan follows `plan-template.md` |
| **III. Agent-Orchestrated** | ✅ PASS | This plan is output of the `speckit.plan` agent. Single-responsibility agents handle each phase |
| **IV. Test Optionality** | ✅ PASS | Tests are explicitly requested in User Story 6 (P3). Hook and component tests mandated in FR-019, FR-020. Tests follow existing codebase conventions |
| **V. Simplicity & DRY** | ✅ PASS | Audit refactors toward existing design tokens and shared components. No new abstractions, libraries, or architectural patterns introduced. Decomposition reduces complexity |

**Gate Result**: ✅ ALL GATES PASS — proceeding to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/043-agents-page-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── component-contracts.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── pages/
│   │   └── AgentsPage.tsx                     # 251 lines — page orchestrator
│   ├── components/
│   │   ├── agents/                            # 10 files, 2,536 lines — catalog components
│   │   │   ├── AgentsPanel.tsx                # 565 lines (OVER LIMIT — decompose)
│   │   │   ├── AddAgentModal.tsx              # 520 lines (OVER LIMIT — decompose)
│   │   │   ├── AgentCard.tsx                  # 286 lines (OVER LIMIT — decompose)
│   │   │   ├── AgentInlineEditor.tsx          # 272 lines (OVER LIMIT — decompose)
│   │   │   ├── AgentAvatar.tsx                # 210 lines
│   │   │   ├── AgentChatFlow.tsx              # 199 lines
│   │   │   ├── BulkModelUpdateDialog.tsx      # 165 lines
│   │   │   ├── ToolsEditor.tsx                # 132 lines
│   │   │   ├── AgentIconPickerModal.tsx       # 117 lines
│   │   │   └── AgentIconCatalog.tsx           # 70 lines
│   │   ├── board/                             # Agent-related board components
│   │   │   ├── AgentPresetSelector.tsx        # 519 lines (OVER LIMIT — decompose)
│   │   │   ├── AgentConfigRow.tsx             # 480 lines (OVER LIMIT — decompose)
│   │   │   ├── AgentTile.tsx                  # 295 lines (OVER LIMIT — decompose)
│   │   │   ├── AddAgentPopover.tsx            # 208 lines
│   │   │   ├── AgentColumnCell.tsx            # 168 lines
│   │   │   ├── AgentDragOverlay.tsx           # 69 lines
│   │   │   └── AgentSaveBar.tsx               # 49 lines
│   │   ├── common/                            # Shared components (consume as-is)
│   │   │   ├── CelestialLoader.tsx            # 45 lines
│   │   │   ├── ErrorBoundary.tsx              # 69 lines
│   │   │   ├── ProjectSelectionEmptyState.tsx # 176 lines
│   │   │   ├── ThemedAgentIcon.tsx            # 95 lines
│   │   │   ├── agentIcons.tsx                 # 547 lines
│   │   │   └── CelestialCatalogHero.tsx       # 119 lines
│   │   └── ui/                                # UI primitives (consume as-is)
│   ├── hooks/
│   │   ├── useAgentConfig.ts                  # 349 lines — agent assignment state management
│   │   ├── useAgents.ts                       # 108 lines — agent list/pending queries
│   │   └── useAgentTools.ts                   # 39 lines — agent tools state
│   ├── services/
│   │   └── api.ts                             # agentsApi (9 endpoints), pipelinesApi
│   └── types/
│       └── index.ts                           # AgentConfig, AgentAssignment, AvailableAgent, etc.
├── __tests__/                                 # Existing test files
│   ├── components/agents/__tests__/
│   │   ├── AddAgentModal.test.tsx
│   │   └── AgentsPanel.test.tsx
│   ├── components/board/
│   │   ├── AgentSaveBar.test.tsx
│   │   └── AgentTile.test.tsx
│   └── components/common/
│       └── ThemedAgentIcon.test.tsx
```

**Structure Decision**: Web application structure. All changes scoped to `solune/frontend/src/` — specifically the `components/agents/`, `components/board/Agent*`, `hooks/useAgent*.ts`, and `pages/AgentsPage.tsx` files. No backend changes. Shared components (`ui/`, `common/`) consumed as-is.

### Components Exceeding 250-Line Limit

| Component | Current Lines | Action Required |
|-----------|--------------|-----------------|
| AgentsPanel.tsx | 565 | Extract AgentSearch, AgentSortControls, SpotlightSection, AgentList |
| AddAgentModal.tsx | 520 | Separate create/edit flows, extract AgentForm |
| AgentPresetSelector.tsx | 519 | Extract PresetButtons, SavedPipelinesDropdown |
| AgentConfigRow.tsx | 480 | Extract column mapping logic, DnD orchestration |
| AgentTile.tsx | 295 | Extract ConstellationSVG, TileActions |
| AgentCard.tsx | 286 | Extract AgentCardActions, AgentCardMetadata |
| AgentInlineEditor.tsx | 272 | Extract AgentEditForm, validation logic to hook |

## Complexity Tracking

> No constitution violations detected. All audit work follows existing patterns and reduces complexity.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Component decomposition | Extract sub-components into `src/components/agents/` | Follows single-responsibility principle; 7 files exceed 250-line limit |
| Hook extraction | Move complex state logic to dedicated hooks | Existing pattern (useAgentConfig already exists); no new abstractions |
| Test additions | Add tests per FR-019/FR-020 using existing patterns | Tests explicitly requested in spec; follows vi.mock/renderHook conventions |
| No new libraries | Use existing Radix UI, Tailwind, dnd-kit | Simplicity principle; existing tooling sufficient |

## Constitution Check (Post-Phase 1)

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Specification-First** | ✅ PASS | Plan artifacts (research.md, data-model.md, contracts/, quickstart.md) generated from spec.md user stories |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates |
| **III. Agent-Orchestrated** | ✅ PASS | Plan output handed off to `speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Tests scoped to US6 (P3) as requested in spec; existing test patterns preserved |
| **V. Simplicity & DRY** | ✅ PASS | Decomposition reduces file sizes; no new abstractions; design tokens replace hardcoded values |

**Gate Result**: ✅ ALL GATES PASS — ready for Phase 2 task generation.
