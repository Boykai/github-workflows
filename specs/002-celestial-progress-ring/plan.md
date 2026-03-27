# Implementation Plan: Celestial Loading Progress Ring

**Branch**: `002-celestial-progress-ring` | **Date**: 2026-03-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-celestial-progress-ring/spec.md`

## Summary

Replace the static `CelestialLoader` spinner on long-loading pages (ProjectsPage, AgentsPipelinePage, SettingsPage) with a new `CelestialLoadingProgress` component that renders a circular SVG progress ring with phased status labels, a time-based minimum progress animation, twinkling star decorations, and the existing sun+planet animation centered inside the ring. Progress is derived entirely from React Query hook resolution states — no backend changes required. The component uses `stroke-dashoffset` CSS transitions for smooth ring fill, gold/primary gradient stroke, and proper `role="progressbar"` accessibility attributes.

## Technical Context

**Language/Version**: TypeScript 5.x / React 18.x  
**Primary Dependencies**: React, TanStack React Query, Vitest, React Testing Library  
**Storage**: N/A (client-side only; progress derived from hook states)  
**Testing**: Vitest + React Testing Library (`npm run test`, `npx vitest run <path>`)  
**Target Platform**: Web (modern browsers, responsive)  
**Project Type**: Web application (monorepo: `solune/frontend/` for frontend)  
**Performance Goals**: Ring must begin animating within 200ms of mount; negligible overhead  
**Constraints**: No backend changes; no modification of existing CelestialLoader.tsx; dark mode must maintain gold ring visibility  
**Scale/Scope**: 1 new component, 1 new CSS class, 3 page integrations, 1 new test file, 1 updated test file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | Feature spec with prioritized user stories (P1, P2), Given-When-Then scenarios, and edge cases exists at `specs/002-celestial-progress-ring/spec.md` |
| **II. Template-Driven Workflow** | ✅ PASS | Spec follows `spec-template.md`; this plan follows `plan-template.md` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | `speckit.plan` agent produces plan artifacts; `speckit.tasks` will follow |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests explicitly required by FR-016, FR-017 in spec |
| **V. Simplicity and DRY** | ✅ PASS | Single reusable component for all three pages; no premature abstraction; progress formula is `max(minProgress, completedPhases / totalPhases)` |

**Gate Result**: ✅ All principles satisfied. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/002-celestial-progress-ring/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── CelestialLoadingProgress.api.md
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/
├── src/
│   ├── components/
│   │   └── common/
│   │       ├── CelestialLoader.tsx            # Existing — NOT modified
│   │       ├── CelestialLoadingProgress.tsx   # NEW component
│   │       └── CelestialLoadingProgress.test.tsx  # NEW tests
│   ├── pages/
│   │   ├── ProjectsPage.tsx                   # MODIFIED — replace loader
│   │   ├── ProjectsPage.test.tsx              # MODIFIED — update mocks
│   │   ├── AgentsPipelinePage.tsx             # MODIFIED — replace loader
│   │   └── SettingsPage.tsx                   # MODIFIED — replace loader
│   └── index.css                              # MODIFIED — add .celestial-ring-glow
```

**Structure Decision**: Web application structure under `solune/frontend/`. New component placed in `src/components/common/` alongside existing `CelestialLoader.tsx` for discoverability. Tests colocated per project convention.

## Phase 0: Research Summary

All technical decisions resolved. See [research.md](./research.md) for full details.

Key decisions:
1. **SVG ring technique**: `stroke-dasharray` + `stroke-dashoffset` with CSS `transition` — no JS animation loop
2. **Progress formula**: `max(minProgress, completedPhases / totalPhases)` computed in component
3. **Time-based floor**: `useEffect` + `setInterval` incrementing from 0→15% over 3s, capping at 30%
4. **Gradient stroke**: SVG `<linearGradient>` using `hsl(var(--gold))` and `hsl(var(--primary))` design tokens
5. **Phase label**: First incomplete phase in the ordered array; transitions via `celestial-fade-in` class
6. **Twinkling stars**: Absolute-positioned `<span>` elements with `celestial-twinkle` / `celestial-twinkle-delayed` classes
7. **Glow effect**: New `.celestial-ring-glow` class using `filter: drop-shadow()` with gold token
8. **CelestialLoader embedding**: `<foreignObject>` centering the existing component inside the SVG ring

## Phase 1: Design

### Data Model

See [data-model.md](./data-model.md) for entity definitions.

Core entities:
- **Phase**: `{ label: string; complete: boolean }`
- **ProgressState**: Computed as `max(minProgress, completedCount / totalCount)`

### Component API Contract

See [contracts/CelestialLoadingProgress.api.md](./contracts/CelestialLoadingProgress.api.md) for full interface.

```typescript
interface CelestialLoadingProgressProps {
  phases: { label: string; complete: boolean }[];
  className?: string;
}
```

### Page Integration Points

| Page | Loading Condition | Phases |
|------|-------------------|--------|
| **ProjectsPage** (~L455) | `selectedProjectId && boardLoading` | 1. "Connecting to GitHub…" (`!projectsLoading`), 2. "Loading project board…" (`!boardLoading`), 3. "Loading pipelines…" (`!savedPipelinesLoading`), 4. "Loading agents…" (`!!agents`) |
| **AgentsPipelinePage** (~L155) | `projectId && boardLoading` | 1. "Connecting to GitHub…" (`!projectsLoading`), 2. "Loading board data…" (`!boardLoading`), 3. "Loading agents…" (`!agentsLoading`) |
| **SettingsPage** (~L68) | `userLoading` | 1. "Loading user settings…" (`!userLoading`), 2. "Loading global settings…" (`!globalLoading`) |

### CSS Addition

```css
/* index.css — after existing celestial utility classes */
.celestial-ring-glow {
  filter: drop-shadow(0 0 6px hsl(var(--gold) / 0.4))
          drop-shadow(0 0 14px hsl(var(--gold) / 0.15));
}
```

### Quickstart

See [quickstart.md](./quickstart.md) for implementation steps.

## Constitution Re-Check (Post-Design)

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First Development** | ✅ PASS | Design aligns with all FR-001 through FR-017 |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow templates |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan complete; ready for `speckit.tasks` |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests required (FR-016, FR-017); test file and mock updates planned |
| **V. Simplicity and DRY** | ✅ PASS | Single component reused across 3 pages; formula is trivial `max()`; no over-abstraction |

**Gate Result**: ✅ All principles satisfied post-design.

## Complexity Tracking

No violations to justify. All complexity is inherent to the feature requirements:
- Single new component (no unnecessary abstractions)
- Direct CSS transitions (no animation library)
- Progress derived from existing hook states (no new data layer)
