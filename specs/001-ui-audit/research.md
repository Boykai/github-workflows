# Research: UI Audit

**Feature**: `001-ui-audit` | **Date**: 2026-03-27 | **Plan**: [plan.md](plan.md)

## Overview

This document consolidates all research findings for the UI Audit feature. All Technical Context items were resolvable from the existing codebase — no NEEDS CLARIFICATION markers remained after initial exploration.

---

## Research Task 1: Page Size and Architecture Compliance

**Decision**: Three pages exceed the 250-line limit and require decomposition. One page is borderline.

**Findings**:

| Page | Lines | Status | Action Required |
|------|-------|--------|-----------------|
| ProjectsPage.tsx | 503 | ❌ OVER LIMIT | Decompose into sub-components in `src/components/board/` |
| AppsPage.tsx | 325 | ❌ OVER LIMIT | Decompose into sub-components in `src/components/apps/` |
| AgentsPipelinePage.tsx | 313 | ❌ OVER LIMIT | Decompose into sub-components in `src/components/pipeline/` |
| ActivityPage.tsx | 251 | ⚠️ BORDERLINE | Review; extract if logic-heavy sections identified |
| AgentsPage.tsx | 238 | ✅ WITHIN LIMIT | — |
| HelpPage.tsx | 221 | ✅ WITHIN LIMIT | — |
| ChoresPage.tsx | 181 | ✅ WITHIN LIMIT | — |
| AppPage.tsx | 141 | ✅ WITHIN LIMIT | — |
| LoginPage.tsx | 119 | ✅ WITHIN LIMIT | — |
| SettingsPage.tsx | 107 | ✅ WITHIN LIMIT | — |
| ToolsPage.tsx | 104 | ✅ WITHIN LIMIT | — |
| NotFoundPage.tsx | 29 | ✅ WITHIN LIMIT | — |

**Rationale**: The 250-line limit is specified in FR-001. Pages over the limit must be decomposed. Feature component directories already exist for all three oversized pages, making extraction straightforward.

**Alternatives Considered**: Raising the limit was rejected because the spec is explicit at 250 lines and the existing component directories show the codebase convention favors decomposition.

---

## Research Task 2: Data Fetching Patterns

**Decision**: All pages use React Query (TanStack Query 5.91.0) for data fetching. No raw `useEffect` + `fetch` patterns exist.

**Findings**:
- All API calls go through `@/services/api.ts` which wraps TanStack Query
- Custom hooks (e.g., `useProjects`, `useAgents`, `useApps`, `useTools`, `useChores`) encapsulate query logic
- Mutation hooks use `useMutation` with `onError` and `onSuccess` callbacks
- Query key conventions follow `[feature].all / .list(id) / .detail(id)` pattern

**Rationale**: The existing pattern is fully compliant with FR-007 and FR-008. No remediation needed.

---

## Research Task 3: Loading, Error, and Empty State Coverage

**Decision**: Loading states have 100% coverage. Error states are handled via route-level ErrorBoundary plus inline error handling. Empty states have two gaps.

**Findings**:

| Category | Coverage | Gaps |
|----------|----------|------|
| Loading states | ✅ 100% | All data-fetching pages show loaders (CelestialLoader or skeleton) |
| Error states | ✅ Route-level | Global ErrorBoundary in App.tsx; some pages lack local ErrorBoundary |
| Empty states | ⚠️ ~85% | AgentsPage and AgentsPipelinePage lack explicit empty-state UI |
| Rate limit detection | ✅ Available | `RateLimitContext` and `isRateLimitApiError()` exist in codebase |

**Pages needing local ErrorBoundary**: ProjectsPage, AgentsPipelinePage, ChoresPage (complex state, multiple data sources per FR-014/FR-015).

**Rationale**: Route-level ErrorBoundary catches unhandled errors, but pages with multiple data sources should isolate failures per section (FR-014).

---

## Research Task 4: Type Safety Analysis

**Decision**: Codebase is highly type-safe. Two acceptable `any` usages found (browser API compatibility); all type assertions are safe `as const` patterns.

**Findings**:
- **`any` types**: 1 occurrence in `useVoiceInput.ts:42` (`window as any` for Web Audio API) — justified exception for legacy browser API
- **Type assertions**: All 3 occurrences use `as const` which is a TypeScript best practice, not an unsafe cast
- **API response types**: Types in `src/types/index.ts` and `src/types/apps.ts` align with backend Pydantic models
- **Strict mode**: `tsconfig.json` has `strict: true`, `noUnusedLocals`, `noUnusedParameters`

**Rationale**: The existing type safety level meets FR-016 and FR-017. The `window as any` for Web Audio API is a documented justified exception (browser APIs lack TypeScript definitions for experimental features).

---

## Research Task 5: Accessibility (a11y) Patterns

**Decision**: The codebase uses `eslint-plugin-jsx-a11y` for linting and Radix UI for accessible primitives. Specific audit of ARIA attributes, focus management, and keyboard navigation must be done per-page during implementation.

**Findings**:
- **ESLint a11y plugin**: Configured in `eslint.config.js` with recommended rules
- **Radix UI primitives**: Tooltip, Popover, HoverCard — all include built-in ARIA attributes and keyboard handling
- **Focus management**: Radix dialogs handle focus trapping automatically
- **Custom controls**: Must be audited per-page for ARIA compliance (FR-018 through FR-024)
- **Focus-visible styles**: Tailwind `focus-visible:` ring utilities available

**Rationale**: The tooling foundation is solid. Per-page audit is needed to verify all custom interactive elements (non-Radix) have proper ARIA attributes and keyboard handling.

---

## Research Task 6: Styling and Dark Mode Compliance

**Decision**: Most pages use Tailwind utility classes correctly. AppsPage has hardcoded color values that need migration to design system tokens.

**Findings**:
- **Inline styles**: 1 occurrence in AgentsPage.tsx (`style={{ backgroundColor: dotColor }}`) — data-driven, acceptable
- **Hardcoded colors in AppsPage**: Multiple `zinc-*` and `emerald-*` Tailwind classes instead of semantic design tokens (`border-border`, `text-muted-foreground`, `bg-primary`)
- **Dark mode**: Most pages use `dark:` variants correctly; AppsPage and modal overlays use `bg-black/50` (acceptable for overlays)
- **Spacing scale**: All pages use standard Tailwind spacing (`gap-4`, `p-6`); no arbitrary values found

**Rationale**: The Tailwind color system uses semantic tokens via CSS variables. Pages should use `bg-background`, `text-foreground`, `border-border`, etc. instead of raw color values for theme consistency (FR-035).

---

## Research Task 7: Performance Patterns

**Decision**: Performance optimizations are already landed from a prior `001-performance-review` spec. Verified patterns include `React.memo` on expensive components, `useMemo` on derived data, `useCallback` on stabilized props, and selective query invalidation.

**Findings**:
- **React.memo**: Applied to `IssueCard`, `BoardColumn` (board components)
- **useMemo**: Applied to derived data in `ProjectsPage` (filtering, sorting)
- **useCallback**: Applied to drag handlers, event handlers passed to memoized children
- **key={index}**: Only used in skeleton loaders (stable order, no reordering risk)
- **Virtualization**: No lists exceed 50 items in typical usage; pagination handles large datasets
- **RAF-gated listeners**: Drag listeners use `requestAnimationFrame` for performance

**Rationale**: Prior performance review addressed most concerns. The audit confirms compliance with FR-037 through FR-039. No new performance issues identified.

---

## Research Task 8: Test Coverage Assessment

**Decision**: Test infrastructure is comprehensive. All hooks have colocated `.test.ts` files. Page tests exist for 11 of 12 pages. Convention uses Vitest, `renderHook()`, `vi.mock()`, `waitFor`, and `createWrapper()`.

**Findings**:
- **Hook tests**: All 70+ hooks have colocated test files
- **Page tests**: 11 of 12 pages have `.test.tsx` files (ActivityPage lacks a test file)
- **Test patterns**: Consistent use of `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`
- **Component tests**: Feature component directories contain test files alongside implementations
- **No snapshot tests**: Assertion-based testing throughout

**Gap**: `ActivityPage.tsx` has no corresponding `ActivityPage.test.tsx` file.

**Rationale**: The test foundation meets FR-040 through FR-042. The ActivityPage test gap must be addressed during implementation.

---

## Research Task 9: Code Hygiene

**Decision**: Codebase is clean. No `console.log` statements found (only `console.warn`/`console.error` for error logging). All imports use `@/` alias. No dead code or magic strings identified.

**Findings**:
- **console.log**: Zero occurrences. `console.warn` used in 2 places (pipeline seeding errors), `console.error` in 1 place (WebSocket parse errors)
- **Import aliases**: 100% use `@/` path alias
- **Dead code**: No unused imports or commented-out blocks found in page files
- **File naming**: All conventions followed (PascalCase `.tsx` for components, `use*.ts` for hooks)
- **Magic strings**: Event categories, query keys, route paths properly defined as constants

**Rationale**: Code hygiene meets FR-043 through FR-045. The `console.warn` usage for error logging is appropriate and does not violate the "no console.log" rule.

---

## Summary of Research Decisions

| # | Topic | Decision | Impact |
|---|-------|----------|--------|
| 1 | Page size | 3 pages need decomposition | HIGH — structural changes |
| 2 | Data fetching | Fully compliant | NONE — no changes needed |
| 3 | Loading/error/empty | 2 empty state gaps, 3 ErrorBoundary gaps | MEDIUM — targeted additions |
| 4 | Type safety | Highly compliant, 1 justified exception | LOW — document exception |
| 5 | Accessibility | Foundation solid, per-page audit needed | MEDIUM — per-page work |
| 6 | Styling | AppsPage hardcoded colors | MEDIUM — token migration |
| 7 | Performance | Prior review addressed concerns | LOW — verify only |
| 8 | Test coverage | 1 missing page test (ActivityPage) | LOW — add test file |
| 9 | Code hygiene | Fully compliant | NONE — no changes needed |

All NEEDS CLARIFICATION items resolved. Ready for Phase 1 design.
