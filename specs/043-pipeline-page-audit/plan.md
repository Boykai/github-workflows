# Implementation Plan: Pipeline Page Audit

**Branch**: `043-pipeline-page-audit` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/043-pipeline-page-audit/spec.md`

## Summary

Conduct a comprehensive audit of the Pipeline page (`frontend/src/pages/AgentsPipelinePage.tsx`) and all its child components (pipeline board, stage cards, agent nodes, execution groups, saved workflows list, analytics dashboard, model selector, toolbar, dialogs) within Project Solune. The primary goal is to ensure visual consistency with the Celestial design system, eliminate rendering bugs and broken states, enforce WCAG AA accessibility compliance, validate responsive behavior across desktop/tablet breakpoints (768px–1920px), verify all interactive elements function correctly with proper feedback (including unsaved-changes guards), and ensure code quality follows established project conventions. No backend API changes are required — this is a frontend-only audit-and-refactor effort.

## Technical Context

**Language/Version**: TypeScript 5.9 with React 19.2
**Primary Dependencies**: React 19, TanStack React Query 5.90, Tailwind CSS v4 (via `@tailwindcss/vite`), Radix UI (Slot, Tooltip), Lucide React icons, class-variance-authority, tailwind-merge, react-router-dom 7.13, react-markdown 10.1
**Storage**: N/A (frontend-only; backend uses SQLite with FastAPI)
**Testing**: Vitest 4.0.18 (unit, happy-dom), Testing Library (React), jest-axe (accessibility)
**Target Platform**: Modern browsers (desktop 1280px+, tablet/laptop 768px–1279px)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Page interactive within 3 seconds; user actions reflected in under 1 second perceived response time; no jank with 50+ saved pipelines
**Constraints**: WCAG AA minimum (4.5:1 contrast normal text, 3:1 large text/UI); no hardcoded colors — all must reference design tokens; Pipeline page is a power-user tool, not expected to be fully functional below 768px
**Scale/Scope**: Single page audit affecting 19 frontend components, 7 custom hooks, 1 page component (417 lines), 15 type definitions, 9 API endpoints; no new features, purely audit and refinement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 6 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, clear scope boundaries, and 26 functional requirements |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | This plan is produced by the `speckit.plan` agent with clear inputs/outputs |
| **IV. Test Optionality** | ✅ PASS | Tests are not mandated by spec; existing tests (PipelineBoard, PipelineFlowGraph, StageCard, AgentNode, SavedWorkflowsList, usePipelineConfig, usePipelineReducer) will be verified to pass but no new test creation is required unless accessibility scanning reveals gaps |
| **V. Simplicity and DRY** | ✅ PASS | Audit refactors toward simplicity; no new abstractions introduced. All changes simplify or consolidate existing code |

### Post-Phase 1 Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Data model and contracts align with spec requirements; all 26 functional requirements traced to audit points |
| **II. Template-Driven** | ✅ PASS | All generated artifacts (research.md, data-model.md, contracts/, quickstart.md) follow prescribed templates |
| **III. Agent-Orchestrated** | ✅ PASS | Clear handoff to `speckit.tasks` after this phase |
| **IV. Test Optionality** | ✅ PASS | No new test infrastructure added; existing 5 component test files and 2 hook test files maintained |
| **V. Simplicity and DRY** | ✅ PASS | No new abstractions; refactors consolidate duplicate patterns and align with design tokens |

## Project Structure

### Documentation (this feature)

```text
specs/043-pipeline-page-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — design system analysis, accessibility patterns, performance best practices
├── data-model.md        # Phase 1 output — entity model for Pipeline page components
├── quickstart.md        # Phase 1 output — developer guide for running the audit
├── contracts/           # Phase 1 output — component interface contracts
│   └── component-contracts.yaml
├── checklists/          # Quality checklist from spec phase
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── pages/
│   │   └── AgentsPipelinePage.tsx              # Main page component (~417 lines) — PRIMARY AUDIT TARGET
│   ├── components/
│   │   ├── pipeline/
│   │   │   ├── AgentNode.tsx                   # Individual agent node in execution group (~187 lines)
│   │   │   ├── AgentNode.test.tsx              # Agent node unit tests
│   │   │   ├── ExecutionGroupCard.tsx          # Execution group with mode toggle (~223 lines)
│   │   │   ├── ModelSelector.tsx               # Model selection dropdown (~290 lines)
│   │   │   ├── ParallelStageGroup.tsx          # Parallel group layout (~30 lines)
│   │   │   ├── PipelineAnalytics.tsx           # Analytics dashboard (~295 lines)
│   │   │   ├── PipelineBoard.tsx               # Main pipeline stage grid (~299 lines)
│   │   │   ├── PipelineBoard.test.tsx          # Board unit tests
│   │   │   ├── PipelineFlowGraph.tsx           # Visual flow diagram (~235 lines)
│   │   │   ├── PipelineFlowGraph.test.tsx      # Flow graph unit tests
│   │   │   ├── PipelineModelDropdown.tsx       # Model override dropdown (~117 lines)
│   │   │   ├── PipelineToolbar.tsx             # Save/discard/delete controls (~172 lines)
│   │   │   ├── PresetBadge.tsx                 # Preset indicator badge (~55 lines)
│   │   │   ├── SavedWorkflowsList.tsx          # Saved pipelines list (~237 lines)
│   │   │   ├── SavedWorkflowsList.test.tsx     # Saved workflows unit tests
│   │   │   ├── StageCard.tsx                   # Stage card with agents/groups (~362 lines)
│   │   │   ├── StageCard.test.tsx              # Stage card unit tests
│   │   │   ├── UnsavedChangesDialog.tsx        # Save/discard/cancel dialog (~69 lines)
│   │   │   └── index.ts                        # Barrel export
│   │   ├── common/
│   │   │   ├── CelestialLoader.tsx             # Loading spinner
│   │   │   ├── CelestialCatalogHero.tsx        # Page hero section
│   │   │   └── ProjectSelectionEmptyState.tsx  # Empty state when no project
│   │   └── ui/
│   │       ├── button.tsx                      # Shared button (CVA variants)
│   │       ├── card.tsx                        # Shared card
│   │       ├── input.tsx                       # Shared input
│   │       ├── tooltip.tsx                     # Radix tooltip wrapper
│   │       └── confirmation-dialog.tsx         # Confirmation modal
│   ├── hooks/
│   │   ├── usePipelineConfig.ts               # Pipeline orchestration hook (~232 lines)
│   │   ├── usePipelineBoardMutations.ts       # Board-level mutation hooks (~418 lines)
│   │   ├── usePipelineReducer.ts              # Pipeline state machine (~115 lines)
│   │   ├── usePipelineModelOverride.ts        # Model override derivation (~98 lines)
│   │   ├── usePipelineValidation.ts           # Field validation (~38 lines)
│   │   ├── useSelectedPipeline.ts             # Pipeline selection context
│   │   └── useConfirmation.ts                 # Confirmation dialog hook
│   ├── services/
│   │   └── api.ts                             # API client (pipelinesApi: list, get, create, update, delete, seedPresets, getAssignment, setAssignment, launch)
│   ├── types/
│   │   └── index.ts                           # PipelineConfig, PipelineStage, ExecutionGroup, PipelineAgentNode, PipelineConfigCreate, PipelineConfigUpdate, PipelineConfigListResponse, PipelineConfigSummary, PipelineIssueLaunchRequest, ProjectPipelineAssignment, PipelineBoardState, PipelineModelOverride, PipelineValidationErrors, PresetPipelineDefinition, PresetSeedResult
│   ├── utils/
│   │   ├── formatTime.ts                      # formatTimeAgo, formatTimeUntil
│   │   ├── rateLimit.ts                       # extractRateLimitInfo, isRateLimitApiError
│   │   └── formatAgentName.ts                 # Agent display name formatting
│   ├── lib/
│   │   └── utils.ts                           # cn() — clsx + tailwind-merge
│   └── index.css                              # Celestial design system tokens + custom classes
└── package.json                               # React 19, Vitest, Tailwind v4
```

**Structure Decision**: Web application (frontend-only audit). All changes target `frontend/src/` — primarily `pages/AgentsPipelinePage.tsx` and `components/pipeline/`. No backend modifications are needed. The existing project structure is well-established and no structural reorganization is planned.

## Complexity Tracking

> No violations identified. All changes follow simplicity principles — refactoring toward design-token consistency, removing hardcoded values, and standardizing existing patterns. No new abstractions, libraries, or architectural changes are introduced.
