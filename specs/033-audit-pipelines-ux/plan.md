# Implementation Plan: Audit Pipelines Page for UI Consistency, Quality & UX

**Branch**: `033-audit-pipelines-ux` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/033-audit-pipelines-ux/spec.md`

## Summary

Conduct a comprehensive audit of the Pipelines page (`AgentsPipelinePage.tsx`) and its 10 child components against the Project Solune design system, WCAG 2.1 Level AA accessibility standards, and established cross-page patterns. The audit covers five categories—visual consistency, functional bugs, accessibility, UX quality, and code quality—and produces a prioritized report with severity-rated findings and actionable remediation recommendations. An initial designer audit (see `audit-report.md`) identified 6 findings and fixed 3 in-PR; this plan covers the systematic resolution of remaining open findings (PIPE-004, PIPE-005, PIPE-006) plus the full-scope audit verification and remediation across all five user stories from the spec.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4 (with `@tailwindcss/vite`), shadcn/ui (Radix UI primitives), dnd-kit (drag-and-drop), lucide-react 0.577 (icons), class-variance-authority 0.7.1 (frontend); FastAPI 0.135, aiosqlite 0.22, Pydantic v2.12 (backend)
**Storage**: SQLite with WAL mode (aiosqlite) — `pipeline_configs` table for pipeline CRUD
**Testing**: Vitest 4.0 + Testing Library (happy-dom) + jest-axe for a11y (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); responsive down to tablet
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Page load < 3s; interactions responsive within 100ms; animations smooth at 60fps
**Constraints**: No new libraries; use existing design tokens (`index.css`), shared utilities (`cn()` from `@/lib/utils`), and component patterns; all className composition via `cn()`; `noUnusedLocals` and `noUnusedParameters` enforced
**Scale/Scope**: 1 page (`AgentsPipelinePage.tsx`), 10 pipeline components, ~15 files to audit; remediation touches 3–5 component files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 12 functional requirements (FR-001–FR-012), 8 success criteria, edge cases identified |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement); initial designer audit already completed |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec. Existing jest-axe tests cover baseline a11y; new tests optional but recommended for PIPE-004 remediation (aria-invalid/aria-describedby) |
| **V. Simplicity/DRY** | ✅ PASS | Remediation reuses existing design tokens, shared components (`Tooltip`, `CelestialLoader`), and established patterns from other pages. No new abstractions or libraries. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace back to spec FRs (FR-001–FR-012); data-model.md maps entities to spec Key Entities; contracts map audit categories to functional requirements |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Existing jest-axe infrastructure available; new a11y tests recommended for PIPE-004 but not mandated |
| **V. Simplicity/DRY** | ✅ PASS | All remediation uses existing patterns: `Tooltip` component for name reveal (already used in SavedWorkflowsList), `aria-invalid`/`aria-describedby` standard HTML attributes, `celestial-panel` class for skeleton styling. No new components, no new libraries. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/033-audit-pipelines-ux/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: Audit entity definitions, finding model
├── quickstart.md        # Phase 1: Developer onboarding and audit execution guide
├── contracts/
│   ├── audit-process.md # Phase 1: Audit methodology and category contracts
│   └── components.md    # Phase 1: Component remediation interface contracts
├── checklists/
│   └── requirements.md  # Specification quality checklist (complete)
├── audit-report.md      # Initial designer audit (6 findings, 3 fixed)
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── pages/
│   │   ├── AgentsPipelinePage.tsx            # AUDIT TARGET: Main pipeline page (460 lines)
│   │   └── AgentsPipelinePage.test.tsx       # EXISTING: Page-level tests
│   ├── components/
│   │   └── pipeline/
│   │       ├── PipelineBoard.tsx             # MODIFY: Add aria-invalid/aria-describedby (PIPE-004)
│   │       ├── PipelineBoard.test.tsx        # EXISTING: Board tests (extend for a11y)
│   │       ├── SavedWorkflowsList.tsx        # MODIFY: Upgrade skeleton styling (PIPE-005)
│   │       ├── SavedWorkflowsList.test.tsx   # EXISTING: Workflow list tests
│   │       ├── StageCard.tsx                 # AUDIT: Stage card component (363 lines)
│   │       ├── StageCard.test.tsx            # EXISTING: Stage card tests
│   │       ├── AgentNode.tsx                 # AUDIT: Agent node component (123 lines)
│   │       ├── AgentNode.test.tsx            # EXISTING: Agent node tests
│   │       ├── PipelineToolbar.tsx           # AUDIT: Toolbar component (173 lines)
│   │       ├── PipelineFlowGraph.tsx         # AUDIT: Flow visualization (230 lines)
│   │       ├── PipelineFlowGraph.test.tsx    # EXISTING: Flow graph tests
│   │       ├── ModelSelector.tsx             # AUDIT: Model picker popover (12KB)
│   │       ├── PipelineModelDropdown.tsx     # AUDIT: Pipeline-level model dropdown
│   │       ├── UnsavedChangesDialog.tsx      # AUDIT: Confirmation dialog
│   │       ├── PresetBadge.tsx               # AUDIT: Preset indicator badge
│   │       └── index.ts                     # Barrel exports
│   ├── components/
│   │   └── ui/
│   │       ├── button.tsx                   # REFERENCE: Shared button component
│   │       ├── card.tsx                     # REFERENCE: Shared card component
│   │       ├── input.tsx                    # REFERENCE: Shared input component
│   │       ├── tooltip.tsx                  # REFERENCE: Shared tooltip (used for PIPE-003 fix)
│   │       └── confirmation-dialog.tsx      # REFERENCE: Shared dialog component
│   ├── lib/
│   │   └── utils.ts                         # REFERENCE: cn() utility for className composition
│   └── index.css                            # REFERENCE: Design tokens (colors, spacing, animations)
```

**Structure Decision**: Web application (frontend/ + backend/). This audit is frontend-focused. The backend is not modified — it serves as context for understanding API contracts and data models. Remediation changes are confined to 2–3 frontend component files. No new files are created; no backend changes are needed.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| Reuse `Tooltip` component for long name reveal | Already used in `SavedWorkflowsList` for pipeline names (PIPE-003 already fixed). Consistent pattern across the page. | Custom popover or modal for name display (rejected: over-engineered for a truncation reveal; Tooltip is the established pattern) |
| Standard `aria-invalid` + `aria-describedby` for validation a11y | Native HTML attributes — zero runtime cost, maximum assistive technology compatibility. Matches WCAG 2.1 SC 3.3.1 and 4.1.2. | Custom ARIA live region for validation errors (rejected: input-linked attributes are the standard pattern; live regions are better for dynamic notifications, not form validation) |
| Upgrade skeleton to match `celestial-panel` pattern | Other pages (AgentsPage, ProjectsPage) use `celestial-panel` class with border and gradient for loading states. Aligning SavedWorkflowsList skeletons to this pattern improves visual consistency. | Keep generic pulse blocks (rejected: the spec explicitly calls out visual consistency as P1; generic skeletons are the documented finding PIPE-005) |
