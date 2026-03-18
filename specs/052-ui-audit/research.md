# Research: UI Audit

**Feature**: `052-ui-audit`
**Date**: 2026-03-18
**Status**: Complete

---

## Research Task 1: Page Line Counts and Extraction Candidates

### Decision

Three pages exceed the 250-line threshold and require sub-component extraction:
- **AppsPage.tsx** (709 lines) — highest priority for extraction
- **ProjectsPage.tsx** (631 lines) — second priority
- **AgentsPipelinePage.tsx** (417 lines) — third priority

The remaining 8 pages (AgentsPage 230, AppPage 141, ChoresPage 166, HelpPage 195, LoginPage 119, NotFoundPage 29, SettingsPage 107, ToolsPage 87) are within the threshold.

### Rationale

The 250-line threshold from the audit checklist (FR-004) is the hard boundary. Pages exceeding it must have self-contained sections identified and extracted into `src/components/[feature]/`. The extraction targets are the feature-specific sub-sections already visible in each page (e.g., list sections, detail views, form sections, filter bars).

### Alternatives Considered

- **Raise the threshold to 500 lines**: Rejected — the spec explicitly states 250 lines as the standard, and the audit checklist enforces it.
- **Split only the largest page**: Rejected — all three pages exceeding the threshold should be addressed for consistency. The audit must evaluate all pages against the same standard.

---

## Research Task 2: Existing Shared Component Coverage

### Decision

The existing shared component library covers the core needs for audit remediation:

**UI Primitives** (`src/components/ui/`):
- `Button` — standard button with variants
- `Card` — container card with consistent padding/rounding
- `Input` — form input with label support
- `Tooltip` — hover tooltip for truncated text
- `ConfirmationDialog` — destructive action confirmation with focus trapping
- `HoverCard` — rich hover cards for previews
- `Popover` — dropdown/menu popovers

**Common Components** (`src/components/common/`):
- `CelestialLoader` — loading spinner with size variants
- `ErrorBoundary` — error boundary wrapper
- `ProjectSelectionEmptyState` — empty state with call-to-action
- `ThemedAgentIcon` — themed agent avatar icons
- `CelestialCatalogHero` — hero/banner display
- `agentIcons` — icon definitions

All components are built on Radix UI primitives with Tailwind CSS styling and support dark mode. The `ConfirmationDialog` includes a manual focus trap implementation.

### Rationale

Reusing these existing components ensures consistency across pages (FR-007) and avoids reimplementing equivalent functionality. The `ConfirmationDialog` already implements focus trapping for accessibility compliance (FR-026). The `CelestialLoader` provides the standard loading indicator (FR-015).

### Alternatives Considered

- **Add new shared components for skeleton loading**: Deferred — skeleton loaders would be a nice enhancement but are not required by the spec. The `CelestialLoader` satisfies FR-015. Skeleton loaders can be introduced as page-specific components if needed during remediation.
- **Replace manual focus trap with focus-trap-react**: Rejected — the existing manual implementation works correctly and adding a new dependency violates the no-new-dependencies constraint.

---

## Research Task 3: Data Fetching Patterns Across Pages

### Decision

The codebase uses TanStack React Query consistently for data fetching. All 18 API module exports in `api.ts` are consumed through custom hooks in `src/hooks/`. The primary patterns are:

1. **Query hooks**: `useQuery` with typed API responses and proper query keys (e.g., `useAgents`, `useApps`, `useProjects`, `useChores`, `useTools`)
2. **Mutation hooks**: `useMutation` with `onSuccess` invalidation and `onError` handling
3. **Query key conventions**: Feature-based keys like `['agents']`, `['apps']`, `['projects']`, `['board', 'data', id]`

Potential issues to audit per page:
- Raw `useEffect` + `fetch` patterns that bypass React Query
- Missing `onError` handlers on mutations
- Duplicate API calls between page and child components
- Missing `staleTime` configuration

### Rationale

TanStack React Query is the established data fetching standard (FR-010). The audit should verify each page's hooks follow the established patterns and identify any outliers. The 42 custom hooks represent substantial coverage — the risk is inconsistency between hooks rather than missing hook abstractions.

### Alternatives Considered

- **Standardize all query keys into a central registry**: Deferred — this would be a valuable improvement but exceeds the audit's "no new features" constraint. The audit should document any inconsistencies for future standardization.

---

## Research Task 4: Accessibility Testing Infrastructure

### Decision

The project has robust accessibility testing infrastructure already in place:

- **ESLint jsx-a11y plugin** (`eslint-plugin-jsx-a11y ^6.10.2`) — static analysis of JSX for accessibility violations
- **jest-axe** (`^10.0.0`) — axe-core integration for unit/component tests
- **@axe-core/playwright** (`^4.10.1`) — axe-core integration for E2E tests
- **ESLint rule**: `jsx-a11y/label-has-associated-control` with max depth 3

For the audit, accessibility verification should:
1. Run ESLint with jsx-a11y rules on each page and its components
2. Use keyboard navigation testing (Tab, Enter, Space, Escape) manually
3. Verify ARIA attributes on custom controls
4. Check color contrast meets WCAG AA (4.5:1)
5. Verify focus-visible styles on interactive elements

### Rationale

The existing tooling handles static analysis (ESLint), unit-level a11y testing (jest-axe), and E2E a11y testing (axe-core/playwright). The audit should leverage these tools rather than introducing new ones. Manual keyboard navigation testing complements automated checks by catching interaction patterns that static analysis cannot detect.

### Alternatives Considered

- **Add Storybook with a11y addon**: Rejected — this would be a significant new dependency and infrastructure addition that exceeds the audit scope.
- **Use pa11y for automated page-level testing**: Rejected — @axe-core/playwright already covers this use case in E2E tests.

---

## Research Task 5: Testing Patterns and Conventions

### Decision

The project uses the following testing conventions:

**Test Framework**: Vitest with React Testing Library
**Test File Naming**: `[ComponentName].test.tsx` or `use[Hook].test.ts`
**Test Utilities**: Custom `test-utils.tsx` providing a render wrapper with `TooltipProvider`
**Mock Patterns**:
- `vi.mock('@/services/api', ...)` for API mocking
- `renderHook()` for custom hook testing
- `waitFor()` for async assertions
- `createWrapper()` for query client provider wrapping

**Key Conventions**:
- No snapshot tests (FR-051 explicitly prohibits them)
- Assertion-based tests only
- Tests cover happy path, error state, loading state, and edge cases
- AppsPage tests use `render()` from test-utils (TooltipProvider only, no QueryClientProvider)
- When components use `useQuery` directly, mock `@tanstack/react-query` module
- Do NOT use `renderWithProviders` (renders children twice)

**Coverage**: 139 existing test files across hooks, components, services, and E2E

### Rationale

Following established test conventions ensures new audit tests are consistent with the existing suite. The prohibition on snapshot tests aligns with FR-051. The specific mock patterns and wrapper utilities are important to follow to avoid test failures.

### Alternatives Considered

- **Introduce testing-library/jest-dom matchers**: Already available via Vitest — no additional setup needed.
- **Add Cypress for visual regression testing**: Rejected — Playwright is already configured for E2E tests. Adding Cypress would create tooling duplication.

---

## Research Task 6: Dark Mode and Theming Implementation

### Decision

The frontend uses Tailwind CSS `dark:` variants for dark mode support. The theme is CSS-variable-based, set at the document root level. Key patterns:

- **Theme-aware classes**: `bg-card`, `text-card-foreground`, `border-border` (CSS variables)
- **Dark mode variants**: `dark:bg-gray-800`, `dark:text-gray-100`, etc.
- **Conditional styling**: `cn()` utility from `src/lib/utils.ts` (clsx + tailwind-merge)
- **No inline styles**: Tailwind utility classes only (FR-040)
- **No hardcoded colors**: No `#fff`, `bg-white`, or similar (FR-042)

The audit should check each page for:
1. Hardcoded color values that don't adapt to dark mode
2. Inline `style={}` attributes that bypass the theme system
3. Missing `dark:` variants on background, text, and border colors
4. Arbitrary spacing values (e.g., `p-[13px]`) instead of the standard scale

### Rationale

Tailwind CSS's dark mode support via CSS variables and `dark:` variants is the established pattern. The audit verifies compliance rather than introducing a new theming approach.

### Alternatives Considered

- **Migrate to CSS-in-JS for theming**: Rejected — Tailwind CSS is the established styling framework, and the project has significant investment in utility classes.
- **Add a design token system**: Deferred — valuable but exceeds audit scope. The audit should document any ad-hoc color values for future token migration.

---

## Research Task 7: Rate Limit Error Handling Pattern

### Decision

The codebase has an established pattern for rate limit error detection via `isRateLimitApiError()` utility. The audit should verify each page that makes API calls:

1. Handles errors with user-friendly messages (FR-037)
2. Detects rate limit errors specifically (FR-017)
3. Provides retry actions on error states (FR-016)
4. Uses the `ApiError` class from `src/services/api.ts` for typed error handling

The `ApiError` class includes status codes and error objects, enabling distinction between rate limit errors (HTTP 429 or GitHub-specific rate limit responses) and other errors.

### Rationale

Rate limit detection is a specific requirement (FR-017) that goes beyond generic error handling. The existing `isRateLimitApiError()` utility must be used consistently across all pages that make API calls.

### Alternatives Considered

- **Implement global rate limit handling in the API layer**: Deferred — a global interceptor would be valuable but is a new feature. The audit ensures each page handles rate limits correctly using the existing utility.
