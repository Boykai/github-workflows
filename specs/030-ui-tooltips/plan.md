# Implementation Plan: Comprehensive Tooltips Across App UI for Feature Explainability and UX Guidance

**Branch**: `030-ui-tooltips` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/030-ui-tooltips/spec.md`

## Summary

Add a comprehensive, accessible tooltip system across all interactive UI elements in the application to provide contextual guidance, feature explanations, and decision-consequence communication. The implementation introduces a reusable `Tooltip` wrapper component built on `@radix-ui/react-tooltip` for robust positioning, flip behavior, and accessibility semantics. All tooltip copy is sourced from a centralized TypeScript content registry keyed by UI element identifiers, enabling easy auditing, updates, and future localization. The system supports desktop hover (with ~300ms delay), mobile long-press, keyboard focus triggers, Escape-key dismissal, and a two-tier progressive disclosure pattern (concise summary + optional "Learn more" link) for complex features like agent configuration and pipeline decision nodes. Tooltip styling follows the existing celestial design system with theme-aware dark/light backgrounds, directional arrows, max-width ~280px, and WCAG 2.1 AA color contrast compliance.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend-only feature)
**Primary Dependencies**: React 19.2, @radix-ui/react-tooltip (new), Tailwind CSS v4, lucide-react 0.577, class-variance-authority 0.7
**Storage**: N/A — tooltip content is static TypeScript constants; no database or localStorage changes
**Testing**: Vitest 4 + Testing Library + jest-axe (accessibility)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); mobile browsers (touch interactions)
**Project Type**: Web application (frontend-only changes)
**Performance Goals**: Tooltip display adds <50ms of perceived latency beyond the intentional 300ms hover delay; zero layout shift on tooltip appearance/dismissal
**Constraints**: Must use existing design system tokens (--popover, --foreground, --border, etc.); must meet WCAG 2.1 AA (4.5:1 contrast ratio); must not obstruct adjacent interactive elements; tooltip animations must respect `prefers-reduced-motion`
**Scale/Scope**: 1 new UI primitive component (`Tooltip`), 1 new content registry module, ~9 pages/component areas to instrument with tooltips, 0 backend changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P2), Given-When-Then acceptance scenarios, 13 functional requirements (FR-001–FR-013), 8 success criteria, edge cases, and assumptions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass; accessibility tests recommended given WCAG requirements |
| **V. Simplicity/DRY** | ✅ PASS | Single reusable Tooltip wrapper component with centralized content registry; uses battle-tested Radix UI Tooltip primitive rather than custom positioning logic; one new dependency justified by accessibility and positioning requirements |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-013) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Accessibility tests recommended but not mandated; existing tests unaffected |
| **V. Simplicity/DRY** | ✅ PASS | Single `Tooltip` primitive wraps any element with a `contentKey` prop. Content registry is a flat TypeScript object — no abstraction layers, no state management, no context providers beyond Radix's built-in `TooltipProvider`. Progressive disclosure is opt-in via an optional `learnMoreUrl` field. The one new dependency (`@radix-ui/react-tooltip`) is from the same Radix ecosystem already in use (`@radix-ui/react-slot`) and provides ARIA semantics, intelligent positioning, and animation support that would require ~500+ lines to replicate manually. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/030-ui-tooltips/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Entity definitions, types, registry structure
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Component interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   └── ui/
│   │       └── tooltip.tsx              # NEW: Reusable Tooltip wrapper component (Radix-based)
│   ├── constants/
│   │   └── tooltip-content.ts           # NEW: Centralized tooltip content registry
│   ├── pages/
│   │   ├── AgentsPage.tsx               # MODIFIED: Add tooltips to agent management controls
│   │   ├── AgentsPipelinePage.tsx        # MODIFIED: Add tooltips to pipeline configuration controls
│   │   ├── AppPage.tsx                  # MODIFIED: Add tooltips to dashboard elements
│   │   ├── ChoresPage.tsx               # MODIFIED: Add tooltips to chore management controls
│   │   ├── SettingsPage.tsx             # MODIFIED: Add tooltips to settings controls
│   │   └── ToolsPage.tsx               # MODIFIED: Add tooltips to tools management controls
│   ├── components/
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx            # MODIFIED: Add tooltips to agent card actions
│   │   │   ├── AgentsPanel.tsx          # MODIFIED: Add tooltips to panel controls
│   │   │   └── AddAgentModal.tsx        # MODIFIED: Add tooltips to agent configuration fields
│   │   ├── board/
│   │   │   ├── BoardToolbar.tsx         # MODIFIED: Add tooltips to toolbar controls
│   │   │   ├── RefreshButton.tsx        # MODIFIED: Add tooltip (currently placeholder)
│   │   │   └── CleanUpButton.tsx        # MODIFIED: Add tooltip (currently placeholder)
│   │   ├── chat/
│   │   │   ├── ChatToolbar.tsx          # MODIFIED: Add tooltips to chat controls
│   │   │   └── ChatInterface.tsx        # MODIFIED: Add tooltips to chat actions
│   │   ├── chores/
│   │   │   └── ChoreCard.tsx            # MODIFIED: Add tooltips to chore card actions
│   │   ├── pipeline/
│   │   │   ├── StageCard.tsx            # MODIFIED: Add tooltips to pipeline stage controls
│   │   │   ├── PipelineBoard.tsx        # MODIFIED: Add tooltips to pipeline board actions
│   │   │   └── ModelSelector.tsx        # MODIFIED: Add tooltips to model selection
│   │   ├── settings/                    # MODIFIED: Add tooltips to settings panel controls
│   │   └── tools/                       # MODIFIED: Add tooltips to tools management controls
│   └── App.tsx                          # MODIFIED: Wrap app with Radix TooltipProvider
├── package.json                         # MODIFIED: Add @radix-ui/react-tooltip dependency
```

**Structure Decision**: Web application (frontend-only). This feature is entirely a frontend concern — no backend changes, no database changes, no API changes. All changes extend existing directories and components. The single new primitive component (`tooltip.tsx`) lives in `frontend/src/components/ui/` following the existing pattern for base UI components (`button.tsx`, `card.tsx`, `input.tsx`). The tooltip content registry is a new `constants/` directory following standard React project conventions for static data modules.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| @radix-ui/react-tooltip (new dependency) | Provides WCAG-compliant ARIA semantics, intelligent positioning with flip/shift, animation support, keyboard handling, and portal rendering out of the box. Same Radix ecosystem already used for `@radix-ui/react-slot` in Button component. | Custom tooltip with manual `getBoundingClientRect()` positioning (rejected: existing `AddAgentPopover` pattern requires ~150 lines per component; doesn't handle ARIA or keyboard focus; not DRY for 30+ tooltip instances) |
| Centralized TypeScript registry (not JSON) | TypeScript provides type safety for tooltip keys, IDE autocomplete, and compile-time validation of key references. Simpler than a JSON file + separate type definition. | JSON file with dynamic import (rejected: no type safety; harder to validate key references at build time; adds async loading concern) |
| Single Tooltip wrapper (not per-component) | One `<Tooltip>` component wraps any trigger element, resolving content from the registry by key. Consistent API across the codebase — drop-in with a single `contentKey` prop. | Inline tooltip strings per component (rejected: violates FR-009 centralized registry requirement; makes auditing and localization impossible) |
