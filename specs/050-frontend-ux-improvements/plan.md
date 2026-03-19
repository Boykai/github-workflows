# Implementation Plan: Solune Frontend UX Improvements

**Branch**: `050-frontend-ux-improvements` | **Date**: 2026-03-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/050-frontend-ux-improvements/spec.md`

## Summary

Solune has a polished celestial design with strong accessibility foundations but several significant UX gaps across six areas: silent mutations (no toast feedback), raw-text chat rendering (no markdown/code blocks), static kanban board (no drag-and-drop), generic spinners (no skeleton loading), no keyboard shortcuts, and various polish items. This plan addresses all six phases using the existing React 19 + Vite + Tailwind v4 + TanStack Query stack. Only one new dependency (`sonner`) is needed — `react-markdown`, `remark-gfm`, and `@dnd-kit/*` are already installed but under-utilized. All changes are frontend-only except Phase 3 (kanban drag-and-drop) which relies on the existing `update_item_status_by_name` backend service method.

## Technical Context

**Language/Version**: TypeScript 5.x / React 19 / Vite  
**Primary Dependencies**: React 19, TanStack Query v5, @dnd-kit/core ^6.3.1, @dnd-kit/sortable ^10.0.0, react-markdown ^10.1.0, remark-gfm ^4.0.1, sonner (NEW — toast library), Radix UI primitives, lucide-react, class-variance-authority, zod  
**Storage**: N/A (all state via TanStack Query against Python/FastAPI backend)  
**Testing**: Vitest + happy-dom (unit/component), Playwright (E2E), jest-axe + @axe-core/playwright (a11y). Thresholds: 50/44/41/50 (statements/branches/functions/lines)  
**Target Platform**: Web (320px–1920px viewport range, desktop + mobile responsive)  
**Project Type**: Web application (frontend SPA within `solune/frontend/`)  
**Performance Goals**: Toast display < 100ms after mutation, skeleton → content transition with zero layout shift, drag-drop card move < 2s end-to-end, 60fps drag animations  
**Constraints**: Bundle size increase < 10KB gzipped (sonner ≈ 4KB), WCAG 2.1 AA compliance for all new interactive elements, prefers-reduced-motion support for all animations  
**Scale/Scope**: ~50 screens/views, 6 phases of UX improvements, 33 functional requirements, 11 success criteria

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | spec.md completed with 6 prioritized user stories (P1–P6), GWT acceptance scenarios, independent test criteria, and clear scope boundaries |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase generates plan.md, research.md, data-model.md, contracts/, quickstart.md — clear handoff to tasks phase |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated in spec; existing vitest coverage thresholds apply to new code. A11y tests recommended for FR-004, FR-017, FR-022–FR-027 |
| V. Simplicity and DRY | ✅ PASS | Reuses existing libraries (react-markdown, dnd-kit, celestial theme). Only 1 new dependency (sonner). Follows existing patterns (AgentDragOverlay for dnd, CelestialLoader for loading) |

**Gate Result**: ✅ ALL PASS — proceeding to Phase 0 research.

### Post-Design Re-evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | All design artifacts (data-model.md, contracts/) trace back to spec.md functional requirements (FR-001 through FR-033) |
| II. Template-Driven Workflow | ✅ PASS | Plan, research, data-model, contracts, and quickstart all follow canonical template structure |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase complete with all outputs. Clear handoff to `/speckit.tasks` for Phase 2 task generation |
| IV. Test Optionality with Clarity | ✅ PASS | No tests mandated. Existing coverage thresholds (50/44/41/50) apply. A11y testing recommended for keyboard shortcuts and DnD |
| V. Simplicity and DRY | ✅ PASS | Design reuses installed libraries (react-markdown, dnd-kit, Radix, celestial theme tokens). Only 1 new dependency (sonner, ~4KB). Follows existing patterns (AgentDragOverlay for DnD, celestial-panel for styling). No unnecessary abstractions |

**Post-Design Gate Result**: ✅ ALL PASS — ready for `/speckit.tasks`.

## Project Structure

### Documentation (this feature)

```text
specs/050-frontend-ux-improvements/
├── plan.md              # This file
├── research.md          # Phase 0 output — technology decisions and research
├── data-model.md        # Phase 1 output — entity models and state shapes
├── quickstart.md        # Phase 1 output — developer onboarding guide
├── contracts/           # Phase 1 output — component API contracts
│   ├── toast-system.md
│   ├── chat-markdown.md
│   ├── kanban-dnd.md
│   ├── skeleton-loading.md
│   ├── keyboard-shortcuts.md
│   └── quick-wins.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── components/
│   │   ├── board/
│   │   │   ├── ProjectBoard.tsx         # MODIFY: wrap with DndContext
│   │   │   ├── ProjectBoardContent.tsx  # MODIFY: empty state enrichment
│   │   │   ├── BoardColumn.tsx          # MODIFY: make droppable + skeleton
│   │   │   ├── BoardToolbar.tsx         # MODIFY: add priority filter
│   │   │   ├── IssueCard.tsx            # MODIFY: make draggable + skeleton
│   │   │   ├── AgentDragOverlay.tsx     # REFERENCE: existing dnd-kit pattern
│   │   │   └── IssueDragOverlay.tsx     # NEW: drag overlay for issue cards
│   │   ├── chat/
│   │   │   ├── MessageBubble.tsx        # MODIFY: markdown rendering
│   │   │   ├── ChatInterface.tsx        # MODIFY: date separators, Ctrl+Enter
│   │   │   ├── CodeBlock.tsx            # NEW: code block with copy button
│   │   │   └── CopyMessageAction.tsx    # NEW: hover copy for AI messages
│   │   ├── common/
│   │   │   └── CelestialLoader.tsx      # KEEP: route-level suspense only
│   │   ├── onboarding/
│   │   │   ├── SpotlightTour.tsx        # REFERENCE ONLY
│   │   │   └── SpotlightTooltip.tsx     # MODIFY: add step progress indicator
│   │   └── ui/
│   │       ├── skeleton.tsx             # NEW: Skeleton primitive component
│   │       └── shortcut-modal.tsx       # NEW: keyboard shortcut help modal
│   ├── hooks/
│   │   ├── useGlobalShortcuts.ts        # NEW: global keyboard shortcuts hook
│   │   ├── useBoardDnd.ts              # NEW: board drag-and-drop state hook
│   │   ├── useBoardControls.ts          # MODIFY: add priority filter support
│   │   └── [existing hooks]             # MODIFY: add toast calls to mutation hooks
│   ├── layout/
│   │   ├── AppLayout.tsx                # MODIFY: add <Toaster /> provider
│   │   └── NotificationBell.tsx         # MODIFY: add pulse animation
│   ├── services/
│   │   └── api.ts                       # MODIFY: add board issue status update endpoint
│   └── types/
│       └── index.ts                     # MODIFY: add DnD-related types
└── package.json                         # MODIFY: add sonner dependency
```

**Structure Decision**: Web application with all changes in `solune/frontend/`. Frontend-only modifications except for one new API call in `api.ts` to the existing backend `update_item_status_by_name` service. No backend code changes needed — the backend already supports status updates via the `update_project_item_field` GraphQL mutation.

## Complexity Tracking

> No constitution violations detected. All changes follow existing patterns and reuse installed dependencies.
