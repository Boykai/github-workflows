# Implementation Plan: Chores Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Branch**: `043-chores-page-audit` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/043-chores-page-audit/spec.md`

## Summary

Conduct a comprehensive audit of the Chores page (`frontend/src/pages/ChoresPage.tsx`) and all its child components (ChoresPanel, ChoreCard, AddChoreModal, FeaturedRitualsPanel, ChoreChatFlow, ChoreInlineEditor, ChoreScheduleConfig, ConfirmChoreModal, PipelineSelector) within Project Solune. The primary goal is to ensure visual consistency with the Celestial design system, enforce single-responsibility component architecture (≤250 lines per file), eliminate type-safety gaps, enforce WCAG AA accessibility compliance, validate responsive behavior across desktop/tablet/mobile breakpoints, verify all interactive elements function correctly with proper feedback, add missing loading/error/empty states, and ensure code quality follows established project conventions. Three components exceed the 250-line target (ChoresPanel at 543 lines, ChoreCard at 584 lines, AddChoreModal at 356 lines) and require decomposition. No backend API changes are required — this is a frontend-only audit-and-refactor effort.

## Technical Context

**Language/Version**: TypeScript 5.9 with React 19.2
**Primary Dependencies**: React 19.2, TanStack React Query 5.90, Tailwind CSS 4.2 (via `@tailwindcss/vite`), Radix UI (Slot, Tooltip), Lucide React icons, class-variance-authority, tailwind-merge, react-router-dom 7.13
**Storage**: N/A (frontend-only; backend uses SQLite with FastAPI)
**Testing**: Vitest 4.0.18 (unit, happy-dom), Testing Library (React)
**Target Platform**: Modern browsers (desktop, tablet, mobile web)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Page interactive within 3 seconds; user actions reflected in under 1 second perceived response time; no jank with 100+ chores
**Constraints**: WCAG AA minimum (4.5:1 contrast normal text, 3:1 large text/UI); 44×44px minimum touch targets on mobile; no hardcoded colors — all must reference design tokens; ≤250 lines per component file
**Scale/Scope**: Single page audit affecting 9 frontend components, 1 custom hook (11 exports), 1 page component, 4 existing test files; no new features, purely audit and refinement

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` exists with 8 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 23 functional requirements, and clear scope boundaries |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | This plan is produced by the `speckit.plan` agent with clear inputs/outputs; handoff to `speckit.tasks` |
| **IV. Test Optionality** | ✅ PASS | Tests are explicitly requested in spec (User Story 7, P3). Existing 4 test files (757 lines) will be verified; new tests created only where gaps exist per spec requirements |
| **V. Simplicity and DRY** | ✅ PASS | Audit refactors toward simplicity — decomposing oversized components, extracting duplicated logic into hooks, reusing existing shared primitives. No new abstractions or libraries introduced |

**Gate Result**: ✅ ALL PASS — proceed to Phase 0.

### Post-Phase 1 Re-Evaluation

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | Data model and contracts align with spec requirements; all 23 functional requirements traced to audit points |
| **II. Template-Driven** | ✅ PASS | All generated artifacts (research.md, data-model.md, contracts/, quickstart.md) follow prescribed templates |
| **III. Agent-Orchestrated** | ✅ PASS | Clear handoff to `speckit.tasks` after this phase |
| **IV. Test Optionality** | ✅ PASS | Test requirements scoped to User Story 7 (P3); existing test infrastructure maintained and extended per spec |
| **V. Simplicity and DRY** | ✅ PASS | Component decomposition reduces complexity; extracted hooks consolidate duplicated patterns; no new abstractions beyond what spec requires |

**Gate Result**: ✅ ALL PASS — proceed to Phase 2 (tasks generation).

## Project Structure

### Documentation (this feature)

```text
specs/043-chores-page-audit/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — component analysis, accessibility patterns, performance practices
├── data-model.md        # Phase 1 output — entity model for Chores page components
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
│   │   └── ChoresPage.tsx                    # Main page component (166 lines) — PRIMARY AUDIT TARGET
│   ├── components/
│   │   ├── chores/
│   │   │   ├── ChoresPanel.tsx               # Main chores list + search/sort/add (543 lines) — DECOMPOSE
│   │   │   ├── ChoreCard.tsx                 # Individual chore display + actions (584 lines) — DECOMPOSE
│   │   │   ├── AddChoreModal.tsx             # Create chore modal + auto-merge (356 lines) — DECOMPOSE
│   │   │   ├── FeaturedRitualsPanel.tsx      # Featured chore stats cards (204 lines)
│   │   │   ├── ChoreChatFlow.tsx             # Chat-based template refinement (191 lines)
│   │   │   ├── ChoreInlineEditor.tsx         # Inline chore definition editor (115 lines)
│   │   │   ├── ChoreScheduleConfig.tsx       # Schedule type/value selector (93 lines)
│   │   │   ├── ConfirmChoreModal.tsx         # Confirmation dialog for chore ops (92 lines)
│   │   │   ├── PipelineSelector.tsx          # Pipeline dropdown selector (85 lines)
│   │   │   └── __tests__/
│   │   │       ├── AddChoreModal.test.tsx    # (255 lines)
│   │   │       ├── ChoreScheduleConfig.test.tsx # (188 lines)
│   │   │       ├── ChoresPanel.test.tsx      # (242 lines)
│   │   │       └── FeaturedRitualsPanel.test.tsx # (72 lines)
│   │   ├── common/
│   │   │   ├── CelestialLoader.tsx           # Loading spinner
│   │   │   ├── CelestialCatalogHero.tsx      # Page hero section
│   │   │   ├── ErrorBoundary.tsx             # Error boundary wrapper
│   │   │   └── ProjectSelectionEmptyState.tsx # Empty state (no project selected)
│   │   └── ui/
│   │       ├── button.tsx                    # Shared button (CVA variants)
│   │       ├── card.tsx                      # Shared card
│   │       ├── input.tsx                     # Shared input
│   │       ├── tooltip.tsx                   # Radix tooltip wrapper
│   │       └── confirmation-dialog.tsx       # Confirmation modal
│   ├── hooks/
│   │   └── useChores.ts                      # Chores data fetching + mutations (192 lines, 11 exports)
│   ├── services/
│   │   └── api.ts                            # API client (choresApi — 10 endpoints, lines 654-783)
│   ├── types/
│   │   └── index.ts                          # Chore types (lines 882-1023): Chore, ChoreTemplate, ChoreCreate, etc.
│   ├── constants/
│   │   ├── tooltip-content.ts                # Tooltip copy for chores (10 keys)
│   │   └── chat-placeholders.ts              # Chat flow placeholder config
│   ├── utils/
│   │   ├── formatTime.ts                     # formatTimeAgo, formatTimeUntil
│   │   └── rateLimit.ts                      # extractRateLimitInfo, isRateLimitApiError
│   ├── lib/
│   │   └── utils.ts                          # cn() — clsx + tailwind-merge
│   └── index.css                             # Celestial design system tokens + custom classes
└── package.json                              # React 19, Vitest, Tailwind v4
```

**Structure Decision**: Web application (frontend-only audit). All changes target `frontend/src/` — primarily `pages/ChoresPage.tsx` and `components/chores/`. No backend modifications are needed. Three components (ChoresPanel, ChoreCard, AddChoreModal) require decomposition into sub-components within `src/components/chores/`. The existing hook (`useChores.ts`) and type definitions are well-structured and require only refinement.

## Complexity Tracking

> No violations identified. All changes follow simplicity principles — decomposing oversized components, extracting inline logic into hooks, reusing shared UI primitives, and enforcing design-token consistency. No new abstractions, libraries, or architectural changes are introduced.
