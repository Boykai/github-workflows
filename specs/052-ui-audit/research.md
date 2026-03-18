# Research: UI Audit — Page-Level Quality & Consistency

**Feature**: 052-ui-audit | **Date**: 2026-03-18 | **Status**: Complete

## Research Tasks

### RT-001: Page Inventory and Sizing Assessment

**Context**: The spec requires auditing all top-level route pages. We need to identify which pages exceed the 250-line limit and require structural decomposition.

**Decision**: Prioritize pages by line count (largest first) since oversized pages are most likely to have multiple quality issues. Three pages exceed the 250-line threshold and will require component extraction.

**Findings**:

| Page | Lines | Status | Priority |
|------|-------|--------|----------|
| AppsPage.tsx | 707 | ⚠️ Exceeds limit (2.8x) | High — extract 3–4 sub-components |
| ProjectsPage.tsx | 629 | ⚠️ Exceeds limit (2.5x) | High — extract 3–4 sub-components |
| AgentsPipelinePage.tsx | 417 | ⚠️ Exceeds limit (1.7x) | Medium — extract 1–2 sub-components |
| AgentsPage.tsx | 230 | ✅ Within limit | Low |
| HelpPage.tsx | 195 | ✅ Within limit | Low |
| ChoresPage.tsx | 166 | ✅ Within limit | Low |
| AppPage.tsx | 141 | ✅ Within limit | Low |
| LoginPage.tsx | 119 | ✅ Within limit | Low |
| SettingsPage.tsx | 107 | ✅ Within limit | Low |
| ToolsPage.tsx | 87 | ✅ Within limit | Low |
| NotFoundPage.tsx | 29 | ✅ Within limit | Minimal |

**Rationale**: The 250-line threshold from FR-020 is strict but achievable. The three oversized pages (AppsPage, ProjectsPage, AgentsPipelinePage) likely contain inline sub-sections that can be extracted into their existing feature component directories (`src/components/apps/`, `src/components/board/`, `src/components/pipeline/`).

**Alternatives considered**:
- Raising the line limit — rejected because the spec explicitly mandates 250 lines (FR-020)
- Splitting by render sections only — rejected because hook/state logic also contributes to file size and should be extracted per FR-023

---

### RT-002: Existing Component Library and Reuse Patterns

**Context**: The spec mandates using existing shared components (CelestialLoader, ErrorBoundary, ConfirmationDialog, etc.) rather than reimplementing. We need to verify what's available and identify any gaps.

**Decision**: The existing component library is comprehensive. No new shared components need to be created — all required primitives exist.

**Findings**:

| Required Component | Available At | Status |
|-------------------|-------------|--------|
| Loading indicator | `src/components/common/CelestialLoader.tsx` | ✅ Available — accepts `size` prop |
| Error boundary | `src/components/common/ErrorBoundary.tsx` | ✅ Available — wraps routes in App.tsx |
| Empty state | `src/components/common/ProjectSelectionEmptyState.tsx` | ✅ Available — can be used as pattern |
| Confirmation dialog | `src/components/ui/confirmation-dialog.tsx` | ✅ Available — used via `useConfirmation` hook |
| Tooltip | `src/components/ui/tooltip.tsx` | ✅ Available — Radix UI wrapper |
| Button | `src/components/ui/button.tsx` | ✅ Available |
| Card | `src/components/ui/card.tsx` | ✅ Available |
| Input | `src/components/ui/input.tsx` | ✅ Available |
| Hover card | `src/components/ui/hover-card.tsx` | ✅ Available — Radix UI wrapper |
| Popover | `src/components/ui/popover.tsx` | ✅ Available — Radix UI wrapper |
| Agent icon | `src/components/common/ThemedAgentIcon.tsx` | ✅ Available |
| `cn()` utility | `src/lib/utils.ts` | ✅ Available — clsx + tailwind-merge |

**Rationale**: The design system is mature with Radix UI primitives providing built-in accessibility (focus trapping, keyboard navigation, ARIA attributes). Using these as-is satisfies multiple checklist items simultaneously (accessibility, consistency, keyboard support).

**Alternatives considered**:
- Creating new shared empty-state variants per feature — rejected because the existing `ProjectSelectionEmptyState` pattern can be followed with feature-specific inline empty states
- Adding a generic `<PageError>` component — considered but deferred; inline error states with retry buttons are more appropriate given the per-section error handling requirement (FR-007)

---

### RT-003: Data Fetching Patterns and Query Key Conventions

**Context**: The spec requires React Query for all API calls (no raw useEffect + fetch), proper query key conventions, and mutation error handling. We need to understand the current patterns.

**Decision**: Follow the established TanStack Query v5 patterns already in use across the codebase. Query keys use hierarchical arrays.

**Findings**:

- **Query client configuration** (App.tsx): No refetch on window focus, smart retry (skip 401/403/404/429, max 1 retry)
- **Query key patterns** observed in hooks:
  - `['agents']` — list all agents
  - `['agents', agentId]` — single agent detail
  - `['projects', projectId, 'board']` — scoped to project
  - `['chores']`, `['tools']`, `['settings']` — feature-level lists
- **Mutation patterns**: `useMutation` with `onSuccess` calling `queryClient.invalidateQueries`, `onError` surfacing toast/feedback
- **Custom hooks**: 44 hooks encapsulate data fetching; each returns query/mutation state
- **API service**: 18 namespaces in `src/services/api.ts` (1199 lines) — well-organized

**Rationale**: The codebase already follows React Query best practices. The audit should verify each page uses these patterns consistently rather than introducing new conventions.

**Alternatives considered**:
- Introducing a query key factory pattern (e.g., `createQueryKeys()`) — rejected because the existing array-based keys are consistent and well-understood; changing the pattern would exceed audit scope
- Adding global error handling via QueryClient `onError` — rejected because per-mutation error handling gives more specific user feedback (FR-005, FR-018)

---

### RT-004: Accessibility Testing Strategy

**Context**: The spec requires full keyboard accessibility, ARIA attributes, focus management, and color contrast compliance (WCAG 2.1 AA). We need to determine the testing approach.

**Decision**: Use a combination of manual checklist verification, existing ESLint jsx-a11y rules, and the existing `test:a11y` npm script. No new tooling setup is required.

**Findings**:

- **ESLint jsx-a11y plugin**: Already configured in `eslint.config.js` with `label-has-associated-control` rule (assert: "either", depth: 3)
- **Radix UI primitives**: Tooltip, Popover, HoverCard, Dialog provide built-in accessibility (focus trapping, keyboard navigation, ARIA attributes)
- **npm script**: `test:a11y` exists for accessibility-specific tests
- **Tailwind focus styles**: `focus-visible:` ring variants available; codebase uses `celestial-focus` class
- **Color contrast**: Tailwind CSS theme uses CSS variables — dark mode via `dark:` variants

**Rationale**: The existing tooling stack (ESLint jsx-a11y + Radix UI + manual verification) is sufficient for the audit scope. Automated accessibility testing tooling setup is explicitly out of scope per the spec.

**Alternatives considered**:
- Adding axe-core automated testing — rejected (explicitly out of scope: "Automated accessibility testing tooling setup")
- Adding Pa11y CI integration — rejected (same scope exclusion)
- Using Lighthouse CI for accessibility scores — rejected (out of scope and adds CI complexity)

---

### RT-005: Dark Mode and Theming Verification

**Context**: The spec requires all pages to render correctly in both light and dark modes (FR-025). We need to understand the theming approach.

**Decision**: Verify that all pages use Tailwind `dark:` variants and CSS variables from the theme. No hardcoded color values (e.g., `#fff`, `bg-white`) should remain.

**Findings**:

- **Theming approach**: Tailwind CSS v4.2.0 with CSS custom properties
- **Dark mode toggle**: Available in settings (theme preference)
- **Existing audit scripts**: `npm run audit:theme-*` scripts exist for theme validation
- **Common violations**: Hardcoded colors like `bg-white`, `text-black`, `border-gray-200` instead of semantic tokens
- **Verification**: Visual inspection at 768px, 1024px, 1440px, 1920px in both modes

**Rationale**: The theme infrastructure is mature. The audit's role is to catch per-page violations where developers used hardcoded values instead of theme-aware alternatives.

**Alternatives considered**:
- Creating automated theme regression tests — deferred (would be a new feature, out of audit scope)
- Adding CSS custom property linting — considered but the existing theme audit scripts cover this

---

### RT-006: Test Coverage Strategy for Audited Pages

**Context**: The spec requires hook tests, component tests, and edge-case coverage for each audited page (FR-031 through FR-033, User Story 6). We need to determine the testing approach.

**Decision**: Follow the established test patterns using Vitest + React Testing Library. Tests will be co-located with source files.

**Findings**:

- **Test utilities**: `src/test/test-utils.tsx` provides `renderWithProviders()` wrapping QueryClientProvider, ConfirmationDialogProvider, TooltipProvider
- **Query client for tests**: `createTestQueryClient()` with no retries, infinite gcTime
- **API mocking**: `vi.mock('@/services/api', ...)` pattern
- **Hook testing**: `renderHook()` with mocked API responses
- **Coverage thresholds** (vitest.config.ts): 49% statements, 44% branches, 41% functions, 50% lines
- **Existing test count**: 134 test files across the codebase
- **Test factories**: `src/test/factories/index.ts` for test data

**Rationale**: The testing infrastructure is well-established. Each page audit adds tests following existing patterns — no new test utilities or infrastructure needed.

**Note from memory**: AppsPage tests use `render()` from test-utils (TooltipProvider only, no QueryClientProvider). When a component uses `useQuery` directly, mock `@tanstack/react-query` module instead. Do not use `renderWithProviders` if it renders children twice.

**Alternatives considered**:
- Snapshot testing — explicitly rejected by the spec ("No snapshot tests: Prefer assertion-based tests over fragile snapshots")
- Integration tests with MSW (Mock Service Worker) — deferred; vi.mock is the established pattern and changing it exceeds audit scope
- Mutation testing per page — available via Stryker but not required by the spec

---

### RT-007: Page Audit Execution Order

**Context**: The spec states "The ordering of page audits is determined by user traffic and risk — higher-traffic pages are audited first." We need to determine the audit order.

**Decision**: Prioritize by a combination of page complexity (line count), user visibility (traffic proxy), and risk (number of quality dimensions likely to fail).

**Findings**:

| Priority | Page | Rationale |
|----------|------|-----------|
| 1 | AppsPage (707 lines) | Largest page, highest structural risk, likely most quality issues |
| 2 | ProjectsPage (629 lines) | Second largest, core user workflow, high visibility |
| 3 | AgentsPipelinePage (417 lines) | Third largest, complex interactive UI (drag-and-drop pipeline builder) |
| 4 | AgentsPage (230 lines) | Near limit, agent management is a core feature |
| 5 | ChoresPage (166 lines) | Moderate size, automation feature with CRUD operations |
| 6 | HelpPage (195 lines) | User-facing help/documentation, copy quality is critical |
| 7 | SettingsPage (107 lines) | Settings management, form-heavy page |
| 8 | ToolsPage (87 lines) | Tool management, moderate complexity |
| 9 | AppPage (141 lines) | Home/chat page, primary user entry point but likely already polished |
| 10 | LoginPage (119 lines) | Auth page, simpler UI, lower risk |
| 11 | NotFoundPage (29 lines) | Minimal page, lowest risk |

**Rationale**: Starting with the largest/most complex pages yields the highest quality improvement per audit iteration. These pages are also most likely to have structural violations (exceeding 250 lines), missing states, and accessibility gaps.

**Alternatives considered**:
- Alphabetical order — rejected because it doesn't account for risk or impact
- Random order — rejected because it doesn't optimize for maximum quality improvement
- Starting with smallest pages — rejected because small pages are already likely compliant and provide less learning value for establishing the audit process
