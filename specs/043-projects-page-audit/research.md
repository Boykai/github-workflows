# Research: Projects Page Audit

**Feature**: `043-projects-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: Projects Page Component Decomposition Strategy

**Decision**: Decompose the 630-line `ProjectsPage.tsx` into 4 extracted sub-components (`ProjectSelector`, `PipelineSelector`, `BoardHeader`, `RateLimitBanner`) placed in the existing `src/components/board/` directory. The orchestrator page will delegate rendering to these components and remain ≤250 lines.

**Rationale**: The current page file at 630 lines violates the ≤250-line single-responsibility target (FR-001). Analysis of the page reveals four self-contained sections that can be extracted without changing behavior:

1. **Project selector dropdown** (~lines 170–270): Contains project list rendering, search filtering, selection logic, and the dropdown UI. Currently has its own `useState` for search and open/close state — a natural extraction boundary.
2. **Pipeline selector and grid** (~lines 450–580): Contains pipeline list query, selection mutation, grid rendering with status dots, and agent assignment display. Has its own `useMutation` and `useQuery` calls — a natural extraction boundary.
3. **Board header** (~lines 280–380): Contains the title bar with project name, sync status indicator, refresh button, and last-updated timestamp. Pure presentation with props from hooks.
4. **Rate limit banner** (~lines 380–430): Contains rate limit detection, reset countdown, and warning display. Self-contained logic using `isRateLimitApiError()` and `formatTimeUntil()`.

**Alternatives considered**:
- **Extract into a separate `src/components/projects/` directory**: Rejected because all board-related components already reside in `src/components/board/`, and splitting into two directories would fragment the feature's component hierarchy.
- **Extract into a single large sub-component**: Rejected because it would just move the complexity rather than decompose it. Four focused components with single responsibilities is preferable.
- **Use composition pattern with render props**: Rejected as unnecessarily complex for this use case. Simple prop passing (≤2 levels) between the page orchestrator and extracted components is sufficient.

---

### RT-002: Existing State Management Patterns Assessment

**Decision**: The existing hook architecture (`useProjectBoard`, `useProjects`, `useBoardControls`, `useBoardRefresh`) is well-structured and already follows React Query patterns. No new hooks need to be created. The audit should verify and improve existing hooks rather than replace them.

**Rationale**: Analysis of the four project-related hooks reveals:

- **`useProjectBoard.ts` (108 lines)**: Uses `useQuery` with `boardApi.listProjects` and `boardApi.getBoardData`, proper `staleTime` configuration via `STALE_TIME_PROJECTS` and `STALE_TIME_SHORT` constants, and returns typed state. Well-structured.
- **`useProjects.ts` (84 lines)**: Uses `useQuery` with `projectsApi.list` and `useMutation` with `projectsApi.select`, proper `staleTime` via `STALE_TIME_PROJECTS` and `STALE_TIME_MEDIUM`. Well-structured.
- **`useBoardControls.ts` (402 lines)**: Largest hook — contains drag-and-drop logic, filter/sort state, agent configuration mutations. At 402 lines, this hook is complex but each function is focused. May benefit from internal function extraction but does not need splitting.
- **`useBoardRefresh.ts` (264 lines)**: Manages refresh polling, rate limit tracking, and timer logic. Uses `useQuery` mutation invalidation patterns. Well-structured.

All hooks follow the `use*.ts` naming convention, use `@/` import aliases, and return typed objects. No raw `useEffect` + `fetch` patterns were found — all data fetching uses TanStack React Query.

**Alternatives considered**:
- **Create new hooks for extracted components**: Rejected because the existing hooks already encapsulate the data layer. Extracted components can receive data via props from the page orchestrator, keeping prop drilling to ≤2 levels.
- **Merge hooks into a single `useProjectsPage` hook**: Rejected because it would create a god-hook that violates single responsibility. The current four hooks have clear, separate concerns.

---

### RT-003: Loading, Error, and Empty State Patterns

**Decision**: The Projects page already implements loading, error, and empty states, but they need verification and potential enhancement against the audit checklist. Specifically: (a) loading uses `<CelestialLoader>` — confirmed present, (b) error states display messages but need verification for user-friendly format and retry actions, (c) empty state uses `<ProjectSelectionEmptyState>` — confirmed present, (d) rate limit detection uses `isRateLimitApiError()` and `extractRateLimitInfo()` — confirmed present.

**Rationale**: Codebase inspection reveals:

- **Loading state**: `ProjectsPage.tsx` checks `projectsListLoading` and `boardLoading` and renders `<CelestialLoader size="md" />`. ✅ Meets FR-009.
- **Error state**: `projectsError` and `boardError` are checked, but the error rendering needs verification for user-friendly message format (FR-026: "Could not [action]. [Reason]. [Suggested next step].") and retry action (FR-010).
- **Empty state**: `<ProjectSelectionEmptyState>` is rendered when no project is selected. When projects list is empty (no projects at all), verification needed for meaningful empty state (FR-012).
- **Rate limit**: `isRateLimitApiError()` is imported and used for detection. `extractRateLimitInfo()` and `formatTimeUntil()` are used for reset countdown display. ✅ Meets FR-011.
- **Partial loading**: Board section shows its own loading/error independently from project selector. ✅ Meets FR-013.
- **Error boundary**: `<ErrorBoundary>` wraps all routes in `App.tsx` (line 121). ✅ Meets FR-014.

**Alternatives considered**:
- **Add skeleton loading instead of spinner**: Considered as an enhancement (skeleton loading for board columns while data loads). This is a progressive improvement that can be evaluated during implementation but is not required by the spec.
- **Add toast notifications for all errors**: The spec requires user-visible error feedback but doesn't mandate toasts specifically. Inline error messages with retry actions satisfy the requirement.

---

### RT-004: Accessibility Compliance Assessment

**Decision**: Conduct a targeted accessibility audit focusing on the custom controls unique to the Projects page: the project selector dropdown, the pipeline selector dropdown, the board toolbar filters, and the issue detail modal. Use existing Radix UI primitives (which provide built-in ARIA support) where possible, and add manual ARIA attributes only to custom-built controls.

**Rationale**: The Projects page contains several custom interactive controls that may lack proper ARIA attributes:

1. **Project selector dropdown**: Custom-built with `useState` toggle and div-based list. Needs `role="listbox"`, `aria-expanded`, `aria-selected` on options, and keyboard arrow-key navigation.
2. **Pipeline selector dropdown**: Similar custom implementation. Needs the same ARIA treatment.
3. **Board toolbar**: Contains filter/sort buttons. Need `aria-label` attributes and keyboard accessibility verification.
4. **Issue detail modal** (`IssueDetailModal.tsx`): At 345 lines, this modal needs focus trapping verification and focus-return-to-trigger on close.
5. **Confirmation modals** (`CleanUpConfirmModal.tsx`): At 444 lines, needs focus trapping verification.

The existing shared UI components (`Button`, `Tooltip`, `Card`) from `src/components/ui/` use Radix primitives and already have good ARIA support. The audit should focus on the custom-built controls above.

**Alternatives considered**:
- **Full WCAG AAA compliance**: Rejected as out of scope. The spec targets WCAG 2.1 AA level, which is the standard for this audit.
- **Install axe-core for automated scanning**: Could be useful for validation but is not required for the planning phase. Can be added during implementation as a dev dependency for CI.

---

### RT-005: Inline Style Elimination Strategy

**Decision**: Replace the 2 identified inline `style={}` attributes in `ProjectsPage.tsx` with appropriate Tailwind patterns. Specifically: (a) `style={pipelineGridStyle}` (dynamic grid-template-columns) should use Tailwind arbitrary value or a CSS custom property, (b) `style={{ backgroundColor: dotColor }}` (dynamic status dot color from API) should use a CSS custom property set via inline style on a parent, then consumed via Tailwind class.

**Rationale**: FR-028 requires no inline style attributes. The two instances found are:

1. **Pipeline grid layout** (line 536): `style={pipelineGridStyle}` — This sets `grid-template-columns` based on the number of pipeline columns, which is dynamic (determined by API response). Cannot be fully eliminated because Tailwind requires class names to be statically analyzable. **Resolution**: Use Tailwind arbitrary value syntax `grid-cols-[repeat(N,minmax(0,1fr))]` where N is known at render time, applied via `cn()`. If N is truly dynamic, a CSS custom property (`--grid-cols`) set via minimal inline style with Tailwind `grid-cols-[var(--grid-cols)]` is acceptable.
2. **Status dot color** (line 552): `style={{ backgroundColor: dotColor }}` — The color comes from the `statusColorToCSS()` utility which maps API status colors to CSS values. This is inherently dynamic (colors defined by GitHub API). **Resolution**: Use `style={{ backgroundColor }}` wrapped in a utility class for all non-color properties. The `backgroundColor` inline style is the only acceptable exception for API-driven dynamic colors, documented in the audit findings.

**Alternatives considered**:
- **Pre-define all possible status colors as Tailwind classes**: Rejected because GitHub API status colors are user-defined and unpredictable — new colors could appear at any time.
- **Use CSS-in-JS**: Rejected because the project uses Tailwind utility-first approach exclusively.

---

### RT-006: Test Coverage Gap Analysis

**Decision**: The existing test suite covers the core hooks and several board components, but gaps exist for newly extracted components, edge cases (rate limit errors, null data, rapid project switching), and some interactive behaviors. The audit should expand tests using the existing Vitest + React Testing Library infrastructure without introducing new testing tools.

**Rationale**: Current test coverage for the Projects page feature:

| File | Has Tests | Coverage Notes |
|------|-----------|----------------|
| `ProjectsPage.tsx` | ✅ `ProjectsPage.test.tsx` | Needs expansion for error/empty/loading states |
| `useProjectBoard.ts` | ✅ `useProjectBoard.test.tsx` | Needs edge case coverage |
| `useProjects.ts` | ✅ `useProjects.test.tsx` | Needs error state coverage |
| `useBoardControls.ts` | ✅ `useBoardControls.test.tsx` | Needs edge case coverage |
| `useBoardRefresh.ts` | ✅ `useBoardRefresh.test.tsx` | Needs rate limit scenario coverage |
| `BoardColumn.tsx` | ✅ `BoardColumn.test.tsx` | Verify existing coverage |
| `IssueCard.tsx` | ✅ `IssueCard.test.tsx` | Verify existing coverage |
| `IssueDetailModal.tsx` | ✅ `IssueDetailModal.test.tsx` | Verify existing coverage |
| `ProjectIssueLaunchPanel.tsx` | ✅ `ProjectIssueLaunchPanel.test.tsx` | Verify existing coverage |
| `AgentTile.tsx` | ✅ `AgentTile.test.tsx` | Verify existing coverage |
| `AgentSaveBar.tsx` | ✅ `AgentSaveBar.test.tsx` | Verify existing coverage |
| `BoardToolbar.tsx` | ❌ No test file | Gap — needs tests for filter/sort interactions |
| `ProjectSelector.tsx` (NEW) | ❌ Not yet created | Gap — needs tests after extraction |
| `PipelineSelector.tsx` (NEW) | ❌ Not yet created | Gap — needs tests after extraction |
| `BoardHeader.tsx` (NEW) | ❌ Not yet created | Gap — needs tests after extraction |
| `RateLimitBanner.tsx` (NEW) | ❌ Not yet created | Gap — needs tests after extraction |

Test patterns follow codebase conventions: `vi.mock('@/services/api', ...)`, `renderHook()` with `createWrapper()`, `waitFor()` for async assertions.

**Alternatives considered**:
- **Add Playwright E2E tests**: Out of scope for this audit. The spec focuses on unit and component tests using the existing Vitest infrastructure.
- **Add snapshot tests**: Explicitly prohibited by audit checklist item 9.5 — prefer assertion-based tests.
