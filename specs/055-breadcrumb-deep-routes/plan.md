# Implementation Plan: Breadcrumb Deep Route Support

**Branch**: `055-breadcrumb-deep-routes` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/055-breadcrumb-deep-routes/spec.md`

## Summary

The Breadcrumb component currently matches the pathname against the flat `NAV_ROUTES` array and always renders exactly two segments: "Home" + the matched top-level route label. Deep routes like `/apps/my-cool-app` show only "Home > Apps" — the dynamic `:appName` parameter is ignored. There is no mechanism for arbitrary-depth breadcrumbs, dynamic labels, or route metadata beyond the two-segment limit.

This plan introduces three changes:
1. **BreadcrumbContext** — a React Context with `useBreadcrumb` hook that allows page components to register human-readable labels for dynamic path segments (e.g., the actual app name instead of the URL slug)
2. **Segment-parsing breadcrumb logic** — replace the single `NAV_ROUTES.find()` lookup with pathname splitting that produces a breadcrumb item per path segment, resolving labels from (a) the breadcrumb context, (b) `NAV_ROUTES` configuration, or (c) title-cased fallback
3. **BreadcrumbProvider** wired into AppLayout — wraps the authenticated layout so all pages can participate in dynamic label registration

All changes are frontend-only (no backend endpoints needed). No new dependencies required.

## Technical Context

**Language/Version**: TypeScript 5.x + React 19.2
**Primary Dependencies**: React Router v7 (useLocation, Link), TanStack Query v5.91 (existing), Lucide React (ChevronRight icon)
**Storage**: N/A (no persistence — breadcrumb state is ephemeral React context)
**Testing**: Vitest + happy-dom + @testing-library/react (existing frontend test setup)
**Target Platform**: Web application (browser frontend)
**Project Type**: Web application (`solune/frontend/` tree — frontend-only changes)
**Performance Goals**: Breadcrumb must re-render within a single React commit when route changes; no perceptible delay
**Constraints**: No new npm dependencies; context cleanup must prevent label leakage across routes
**Scale/Scope**: 3 new files (context, provider, hook), 2 modified files (Breadcrumb component, AppLayout), 9 existing NAV_ROUTES entries, routes up to 5 levels deep

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Specification-First Development | ✅ PASS | `spec.md` includes 4 prioritized user stories (P1×2, P2×2) with Given-When-Then acceptance criteria, edge cases, and 12 functional requirements |
| II. Template-Driven Workflow | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| III. Agent-Orchestrated Execution | ✅ PASS | Plan phase produces `plan.md`, `research.md`, `data-model.md`, `quickstart.md`; tasks deferred to `/speckit.tasks` |
| IV. Test Optionality with Clarity | ✅ PASS | Tests not explicitly mandated by spec; existing Vitest suite validates no regressions. Tests optional per constitution |
| V. Simplicity and DRY | ✅ PASS | Uses built-in React Context — no new libraries, no external state management. Breadcrumb parsing is a pure function over the pathname string. Title-case fallback is a single utility function |

**Gate Result**: ✅ ALL GATES PASS — proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/055-breadcrumb-deep-routes/
├── plan.md              # This file
├── research.md          # Phase 0 — research findings
├── data-model.md        # Phase 1 — entity/state model
├── quickstart.md        # Phase 1 — implementation quickstart
├── contracts/           # Phase 1 — component contracts (no backend APIs)
│   └── breadcrumb-context.md
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/frontend/src/
├── hooks/
│   └── useBreadcrumb.ts          # NEW: BreadcrumbContext, BreadcrumbProvider, useBreadcrumb hook
├── layout/
│   ├── AppLayout.tsx             # MODIFY: wrap Outlet with BreadcrumbProvider
│   └── Breadcrumb.tsx            # MODIFY: rewrite to parse all path segments, resolve labels
└── lib/
    └── breadcrumb-utils.ts       # NEW: toTitleCase utility, buildBreadcrumbSegments pure function
```

**Structure Decision**: Web application structure — all changes within `solune/frontend/src/`. Frontend-only feature; no backend changes needed. The breadcrumb context hook follows the existing pattern of one hook per file in `src/hooks/`. The utility function goes in `src/lib/` following the existing `utils.ts` pattern.

## Implementation Phases

### Phase 1 — Breadcrumb Context & Provider (P1 foundation)

Sequential dependency chain:

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 1.1 | `src/lib/breadcrumb-utils.ts` | Create `toTitleCase(slug)` utility: replaces hyphens/underscores with spaces, capitalizes each word | — |
| 1.2 | `src/hooks/useBreadcrumb.ts` | Create `BreadcrumbContext` holding a `Map<string, string>` of path→label mappings, `BreadcrumbProvider` component, and `useBreadcrumb()` hook returning `{ setLabel, removeLabel }` | 1.1 |
| 1.3 | `src/layout/AppLayout.tsx` | Wrap `<Outlet />` (and `<TopBar />`) with `<BreadcrumbProvider>` so all child pages and the breadcrumb component share the same context | 1.2 |

### Phase 2 — Multi-Segment Breadcrumb Rendering (P1 core)

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 2.1 | `src/lib/breadcrumb-utils.ts` | Add `buildBreadcrumbSegments(pathname, navRoutes, labelOverrides)` — splits pathname into segments, resolves each label from overrides → NAV_ROUTES → title-case fallback | 1.1, 1.2 |
| 2.2 | `src/layout/Breadcrumb.tsx` | Rewrite to use `useBreadcrumbLabels()` for context label map + `buildBreadcrumbSegments()` for segment generation. Render all segments with correct link/text behavior | 2.1, 1.3 |

### Phase 3 — Page Integration (P1 dynamic labels)

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 3.1 | `src/pages/AppsPage.tsx` | Call `useBreadcrumb().setLabel('/apps/<appName>', displayName)` when the app detail view renders, to show the real app name instead of the URL slug | 2.2 |

### Phase 4 — Edge Cases & Polish (P2)

All steps can be done in parallel:

| Step | File | Action | Depends On |
|------|------|--------|------------|
| 4.1 | `src/lib/breadcrumb-utils.ts` | Handle trailing slash normalization, query string / hash stripping | 2.1 |
| 4.2 | `src/hooks/useBreadcrumb.ts` | Ensure cleanup on unmount (useEffect return) to prevent label leakage | 1.2 |

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State mechanism | React Context with `Map<string, string>` | Simplest approach — no new dependencies, integrates with React lifecycle for automatic cleanup. Context is scoped to AppLayout, shared between Breadcrumb and page components |
| Label resolution order | Context override → NAV_ROUTES label → title-case fallback | Gives page components full control while maintaining consistency with sidebar labels for known routes |
| Utility location | `src/lib/breadcrumb-utils.ts` | Pure functions (no React) separated from hook logic for testability; follows existing `src/lib/utils.ts` pattern |
| Provider placement | Wrapping `<Outlet />` and `<TopBar />` in AppLayout | Both the Breadcrumb (inside TopBar) and page components (inside Outlet) need access to the same context |
| Segment path construction | Cumulative join: `/` + segments[0..i].join('/') | Standard breadcrumb pattern; each segment links to its cumulative path |
| Trailing slash handling | Strip before splitting | `/apps/` and `/apps` produce identical segments per FR-011 |
| No new npm dependencies | Native React Context + string manipulation | Constitution Principle V (Simplicity) — existing React APIs are sufficient |
| No backend changes | Frontend-only feature | Breadcrumb labels come from URL structure + client-side context, not from an API |

## Complexity Tracking

> No constitution violations detected. No complexity justifications needed.
