# Implementation Plan: Recent Interactions — Filter Deleted Items & Display Only Parent Issues with Project Board Status Colors

**Branch**: `026-recent-interactions-filter` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-recent-interactions-filter/spec.md`

## Summary

Enhance the existing Recent Interactions sidebar panel to: (1) filter out deleted/non-existent issues by validating cached entries against live board data, (2) restrict display to parent issues only (exclude sub-issues, PRs, draft issues), (3) color-code each entry by its project board status column using the existing `StatusColor` system, and (4) show a clear empty state when no valid parent issues remain. All changes are frontend-only — the existing `BoardDataResponse` API already provides all necessary data (item content type, sub-issues list, status color per column). No new backend endpoints or GraphQL queries are needed.

## Technical Context

**Language/Version**: TypeScript ~5.9, React 19.2, Vite 7.3
**Primary Dependencies**: react-router-dom v7, TanStack Query 5.90, Tailwind CSS v4, lucide-react 0.577
**Storage**: localStorage (sidebar state), in-memory (board data via TanStack Query cache)
**Testing**: Vitest 4 + Testing Library + happy-dom (unit), Playwright (E2E)
**Target Platform**: Desktop browsers, 1024px minimum viewport width
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: Panel renders within 3 seconds even with 50 cached entries (SC-006); status colors update within one render cycle (SC-003)
**Constraints**: No new backend APIs, no new npm dependencies, existing color system reused, WCAG AA contrast compliance
**Scale/Scope**: 3 modified files, 1 new constant, ~150 LOC net change

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 4 prioritized user stories (P1×2, P2, P3), acceptance scenarios, edge cases, and 11 functional requirements |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates; plan.md uses plan-template.md structure |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan); single-responsibility agent model |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests must continue to pass. Test updates included only where existing test fixtures change. |
| **V. Simplicity/DRY** | ✅ PASS | Reuses existing `StatusColor` system, `colorUtils.ts` functions, and `BoardDataResponse` structure. No new abstractions — only modifies the existing `useRecentParentIssues` hook and `Sidebar` component. No new dependencies. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts trace to spec FRs. research.md resolves all unknowns. |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No new test mandate. Existing tests must pass. |
| **V. Simplicity/DRY** | ✅ PASS | Total net change ~150 LOC across 3 files. Reuses existing color utilities and types. No unnecessary abstractions introduced. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/026-recent-interactions-filter/
├── plan.md              # This file
├── research.md          # Phase 0: 5 research items (R1–R5)
├── data-model.md        # Phase 1: Type changes, hook contract, state transitions
├── quickstart.md        # Phase 1: Developer onboarding guide
├── contracts/
│   └── components.md    # Phase 1: Updated component interface contracts
├── checklists/
│   └── requirements.md  # Pre-existing: Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/src/
├── types/index.ts                          # MODIFIED: Extend RecentInteraction type with status + statusColor fields
├── hooks/useRecentParentIssues.ts          # MODIFIED: Add parent-only filtering, sub-issue exclusion, status color mapping
├── layout/Sidebar.tsx                      # MODIFIED: Render status color accent on each recent interaction entry
├── components/board/colorUtils.ts          # EXISTING (no changes): statusColorToCSS(), statusColorToBg() reused
└── constants.ts                            # EXISTING (no changes): No new constants needed — status colors from board data
```

**Structure Decision**: Web application (Option 2 — `frontend/` + `backend/`). All changes are in `frontend/src/`. Backend is unchanged. The existing `BoardDataResponse` → `BoardColumn` → `BoardStatusOption.color` pipeline already provides status colors. The `useRecentParentIssues` hook is the single point of change for filtering logic, and `Sidebar.tsx` is the single point of change for rendering.

## Complexity Tracking

No violations to justify. All changes reuse existing infrastructure:

- Status colors: Reuse `StatusColor` type + `statusColorToCSS()` / `statusColorToBg()` from `colorUtils.ts`
- Parent detection: Reuse `BoardItem.content_type` and cross-reference `SubIssue` arrays already in `BoardDataResponse`
- Deletion detection: Items not present in `BoardDataResponse` are implicitly deleted/removed from the board
- Empty state: Enhance existing empty state text in `Sidebar.tsx`
