# Implementation Plan: Frontend Polish & Performance — Lucide Barrel File, ChoresPanel Bug Fix, Error Recovery Hints

**Branch**: `001-frontend-polish-performance` | **Date**: 2026-03-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-frontend-polish-performance/spec.md`

## Summary

This plan covers three independent workstreams that improve frontend maintainability, data correctness, and user-facing error recovery:

- **Phase A — Centralized Icon Imports**: Create a barrel file at `solune/frontend/src/lib/icons.ts` re-exporting all ~85 Lucide icons used across ~68 import sites, migrate every import, and add an ESLint `no-restricted-imports` rule to prevent drift. This is purely organizational — Vite already tree-shakes and chunks icons via `manualChunks`.
- **Phase B — ChoresPanel Bug Fix**: Add a lightweight `GET /{project_id}/chore-names` backend endpoint returning an unpaginated `list[str]` of all chore names, a `useAllChoreNames` hook with 60-second stale time, and rewire the template membership check in `ChoresPanel.tsx` to use the complete list instead of paginated/filtered results.
- **Phase C — Error Recovery Hints**: Create `solune/frontend/src/utils/errorHints.ts` with HTTP-status-code-based error classification returning `{ title, hint, action? }` objects, integrate into `ErrorBoundary.tsx` and `ProjectBoardErrorBanners.tsx`, and extend `EmptyState.tsx` with an optional `hint` prop for error-variant empty states.

All three phases are independent and can be executed in parallel. Each phase has internal step dependencies documented below.

## Technical Context

**Language/Version**: TypeScript 5.x (frontend), Python 3.11+ (backend)
**Primary Dependencies**: React 18, TanStack Query (react-query), Vite, lucide-react (frontend); FastAPI, aiosqlite (backend)
**Storage**: SQLite via aiosqlite (backend)
**Testing**: Vitest with happy-dom + v8 coverage (frontend); pytest (backend)
**Target Platform**: Web application (SPA served by Vite, API served by FastAPI)
**Project Type**: Web (frontend + backend monorepo under `solune/`)
**Performance Goals**: Icon vendor chunk size unchanged or smaller after barrel file migration; chore-names endpoint <50ms for typical project sizes
**Constraints**: All changes must pass `npm run lint` and `npm run test:coverage`; error hints are English-only (i18n deferred)
**Scale/Scope**: ~68 files with lucide-react imports, ~85 unique icons, ~88 import sites; 11 existing chore endpoints; 2 error display components + 1 empty state component

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | `spec.md` completed with prioritized user stories (P1–P3), acceptance scenarios, and edge cases |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates from `.specify/templates/` |
| **III. Agent-Orchestrated Execution** | ✅ PASS | Plan phase produces plan.md, research.md, data-model.md, contracts/, quickstart.md as defined |
| **IV. Test Optionality** | ✅ PASS | Tests are included where mandated by spec (FR-015: existing lint + coverage must pass). No new test infrastructure required — existing Vitest + pytest suites cover changes. Unit tests for `errorHints.ts` and `useAllChoreNames` follow existing patterns |
| **V. Simplicity and DRY** | ✅ PASS | Barrel file avoids premature abstraction (manual maintenance preferred over auto-generation script); chore-names endpoint returns minimal `list[str]` instead of full objects; error hints use simple status-code switch, not complex parsing |

**Gate Result**: ✅ All principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-frontend-polish-performance/
├── plan.md              # This file
├── research.md          # Phase 0 output — research findings
├── data-model.md        # Phase 1 output — entity definitions
├── quickstart.md        # Phase 1 output — developer quickstart guide
├── contracts/           # Phase 1 output — API contracts
│   └── chore-names.yaml # OpenAPI spec for chore-names endpoint
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
solune/
├── backend/
│   └── src/
│       └── api/
│           └── chores.py              # Add GET /{project_id}/chore-names endpoint
└── frontend/
    ├── eslint.config.js               # Add no-restricted-imports rule for lucide-react
    └── src/
        ├── lib/
        │   └── icons.ts               # NEW: Barrel file re-exporting all Lucide icons
        ├── utils/
        │   └── errorHints.ts          # NEW: Error classification + hint generation
        ├── components/
        │   ├── common/
        │   │   ├── ErrorBoundary.tsx   # Integrate getErrorHint()
        │   │   └── EmptyState.tsx      # Add optional hint prop
        │   ├── board/
        │   │   └── ProjectBoardErrorBanners.tsx  # Integrate getErrorHint()
        │   └── chores/
        │       └── ChoresPanel.tsx     # Replace paginated check with useAllChoreNames
        ├── hooks/
        │   └── useChores.ts           # Add useAllChoreNames hook
        ├── pages/
        │   ├── AgentsPage.tsx         # Pass hint to error-variant EmptyState
        │   ├── ToolsPage.tsx          # Pass hint to error-variant EmptyState
        │   └── ChoresPage.tsx         # Pass hint to error-variant EmptyState
        └── services/
            └── schemas/               # Add chore-names API type if needed
```

**Structure Decision**: Web application structure — existing `solune/backend/` and `solune/frontend/` layout. All changes fit within existing directory conventions. Two new files created (`icons.ts`, `errorHints.ts`); all others are modifications to existing files.

## Implementation Phases

### Phase A — Centralized Icon Imports (Steps 1–3)

| Step | Description | Depends On | Files |
|------|-------------|------------|-------|
| A.1 | Create barrel file `src/lib/icons.ts` exporting all ~85 Lucide icons | — | `src/lib/icons.ts` |
| A.2 | Migrate all ~68 import sites from `lucide-react` to `@/lib/icons` | A.1 | ~68 component/page files |
| A.3 | Add ESLint `no-restricted-imports` rule for `lucide-react` | A.2 | `eslint.config.js` |

**Verification**: `grep -rn "from 'lucide-react'" src/` returns zero results; ESLint blocks direct imports; icons-vendor chunk size unchanged.

### Phase B — ChoresPanel Bug Fix (Steps 4–6)

| Step | Description | Depends On | Files |
|------|-------------|------------|-------|
| B.4 | Add `GET /{project_id}/chore-names` backend endpoint | — | `chores.py` |
| B.5 | Add `useAllChoreNames` hook + API client method | B.4 | `useChores.ts`, API service file |
| B.6 | Replace paginated membership check in ChoresPanel | B.5 | `ChoresPanel.tsx` |

**Verification**: Create chores, apply filters, confirm all templates show correct "already created" status.

### Phase C — Error Recovery Hints (Steps 7–10)

| Step | Description | Depends On | Files |
|------|-------------|------------|-------|
| C.7 | Create `errorHints.ts` with `getErrorHint()` utility | — | `src/utils/errorHints.ts` |
| C.8 | Integrate into `ErrorBoundary.tsx` | C.7 | `ErrorBoundary.tsx` |
| C.9 | Integrate into `ProjectBoardErrorBanners.tsx` | C.7 | `ProjectBoardErrorBanners.tsx` |
| C.10 | Extend `EmptyState.tsx` with `hint` prop; update pages | C.7 | `EmptyState.tsx`, `AgentsPage.tsx`, `ToolsPage.tsx`, `ChoresPage.tsx` |

**Verification**: Simulate 401, 429, network errors; confirm hint text, icons, and action links appear correctly.

## Complexity Tracking

> No constitution violations to justify. All changes follow simplicity and DRY principles.
