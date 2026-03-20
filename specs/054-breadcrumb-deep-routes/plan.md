# Implementation Plan: Breadcrumb Deep Route Support

**Branch**: `054-breadcrumb-deep-routes` | **Date**: 2026-03-20 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/054-breadcrumb-deep-routes/spec.md`

## Summary

The Breadcrumb component currently matches the pathname against the flat `NAV_ROUTES` array and renders at most two segments: "Home" + the matched route label. Dynamic path segments (e.g., `:appName`) are ignored, producing incomplete trails like "Home > Apps" for `/apps/my-cool-app`.

This plan introduces:

1. **Full-depth path parsing** — split the pathname into all segments and render one breadcrumb item per segment plus a leading "Home" link.
2. **Route metadata resolution** — match segments against `NAV_ROUTES` labels for known routes (e.g., `/apps` → "Apps").
3. **Dynamic label context** — a `BreadcrumbContext` + `useBreadcrumb` hook that lets pages inject human-readable labels at runtime (e.g., the actual app name instead of the URL slug).
4. **Accessibility hardening** — semantic `<nav>` landmark, `<ol>` list structure, `aria-current="page"` on the last segment, and decorative separators hidden from screen readers.

All changes are frontend-only. No backend or API changes are required.

## Technical Context

**Language/Version**: TypeScript 5.x, React 18  
**Primary Dependencies**: React, React Router DOM v6, Lucide React (icons), TanStack Query v5  
**Storage**: N/A (frontend-only; breadcrumb state lives in React context)  
**Testing**: Vitest + React Testing Library (`cd solune/frontend && npx vitest run`)  
**Target Platform**: Web browser (single-page application)  
**Project Type**: Web application (frontend within `solune/frontend/`)  
**Performance Goals**: Breadcrumb renders synchronously with route changes; dynamic label updates appear within 1 render cycle of `setLabel` call  
**Constraints**: No backend changes; no new npm dependencies; breadcrumb must remain a pure client-side component  
**Scale/Scope**: 8 top-level routes, route depth 2–5 segments; single `BreadcrumbProvider` at layout root

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ Pass | `spec.md` exists with 4 prioritized user stories, acceptance scenarios, and edge cases |
| II. Template-Driven | ✅ Pass | Using canonical `plan-template.md`; all artifacts follow standard structure |
| III. Agent-Orchestrated | ✅ Pass | Work executed via `speckit.plan` agent with clear inputs/outputs |
| IV. Test Optionality | ✅ Pass | Tests not explicitly mandated in spec; will be added if requested during `speckit.tasks` |
| V. Simplicity and DRY | ✅ Pass | Context + hook is idiomatic React; no new abstractions beyond what React provides; no premature generalization |

**Pre-Phase 0 gate result**: All principles pass. Proceeding to Phase 0.

### Post-Design Re-evaluation (after Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First | ✅ Pass | All design artifacts trace back to spec requirements (FR-001 through FR-016) |
| II. Template-Driven | ✅ Pass | plan.md, research.md, data-model.md, quickstart.md, contracts/ all follow canonical structure |
| III. Agent-Orchestrated | ✅ Pass | Phase 0 and Phase 1 completed via speckit.plan agent |
| IV. Test Optionality | ✅ Pass | No tests mandated; test strategy deferred to speckit.tasks phase |
| V. Simplicity and DRY | ✅ Pass | Design adds 1 new file (useBreadcrumb.ts), modifies 2 existing files; no new dependencies; no over-abstraction |

**Post-design gate result**: All principles pass. No violations. Ready for Phase 2 (speckit.tasks).

## Project Structure

### Documentation (this feature)

```text
specs/054-breadcrumb-deep-routes/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions and patterns
├── data-model.md        # Phase 1: entities and data flow
├── quickstart.md        # Phase 1: developer guide for implementation
├── contracts/           # Phase 1: component interface contracts
│   └── breadcrumb-components.md
└── tasks.md             # Phase 2 output (NOT created by speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/src/
├── layout/
│   ├── Breadcrumb.tsx          # MODIFY — full-depth segment rendering, route metadata, accessibility
│   ├── AppLayout.tsx           # MODIFY — wrap Outlet with BreadcrumbProvider
│   └── TopBar.tsx              # NO CHANGE — already renders <Breadcrumb />
├── hooks/
│   └── useBreadcrumb.ts        # NEW — BreadcrumbContext provider + useBreadcrumb hook
├── constants.ts                # NO CHANGE — NAV_ROUTES already has path/label pairs
├── types/
│   └── index.ts                # NO CHANGE — NavRoute type sufficient as-is
└── pages/
    └── AppsPage.tsx            # MODIFY — example: inject dynamic label via useBreadcrumb
```

**Structure Decision**: This is a frontend-only feature within the existing `solune/frontend/` web application structure. No backend changes needed. The new `useBreadcrumb.ts` hook follows the established pattern of one hook per file in `solune/frontend/src/hooks/`.

## Complexity Tracking

> No Constitution Check violations. No complexity justifications needed.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *(none)* | — | — |
