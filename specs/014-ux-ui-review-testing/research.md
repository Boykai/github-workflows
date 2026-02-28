# Research: Deep UX/UI Review, Polish & Meaningful Frontend Test Coverage

**Feature**: 014-ux-ui-review-testing | **Date**: 2026-02-28

## Research Task 1: Current Design Token Centralization

### Decision
Design tokens are **well-centralized** via CSS custom properties in `frontend/src/index.css` and referenced through Tailwind CSS configuration in `frontend/tailwind.config.js`. No hardcoded inline color/spacing/font values need to be extracted.

### Rationale
- **Colors**: 11 semantic tokens (background, foreground, primary, secondary, destructive, muted, accent, popover, card, border, input, ring) defined as HSL CSS variables with complete light/dark mode variants
- **Spacing/Radius**: A single `--radius` variable (0.5rem) controls border radius consistently
- **Typography**: Inter font family defined in Tailwind config; no hardcoded font stacks found in components
- **Token flow**: CSS variables → Tailwind config references (`hsl(var(--primary))`) → Components use Tailwind utility classes (e.g., `bg-primary`, `text-foreground`)
- **ThemeProvider.tsx**: React Context-based theme management with light/dark/system support, persisted to localStorage
- **`cn()` utility**: All components use `cn()` from `lib/utils.ts` (clsx + twMerge) for consistent class merging

### Alternatives Considered
- Migrating to a dedicated design token tool (Style Dictionary, Figma Tokens) — rejected as over-engineered; the CSS variable + Tailwind approach is already clean and maintainable
- Moving tokens to a JSON file — rejected; CSS variables are directly consumed by both Tailwind and browser, adding a build step would increase complexity

---

## Research Task 2: Interactive Element State Coverage

### Decision
UI primitives (Button, Card, Input) have **comprehensive interactive states** via CVA (class-variance-authority) and Tailwind utilities. Board, chat, and settings components consistently apply hover, focus, and disabled patterns. No major gaps identified in state coverage.

### Rationale
Analysis of component interactive states:
- **Button** (`ui/button.tsx`): CVA-based variants with `hover:bg-primary/90`, `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`, `disabled:pointer-events-none disabled:opacity-50` across all 6 variants
- **Input** (`ui/input.tsx`): `focus-visible:ring-2 focus-visible:ring-ring`, `disabled:cursor-not-allowed disabled:opacity-50`, `placeholder:text-muted-foreground`
- **Board components**: IssueCard has `role="button"`, `tabIndex={0}`, keyboard handlers (Enter/Space), hover transitions
- **Chat components**: Send button disabled during `isSending`, textarea auto-expands with max-height constraint
- **Settings components**: SettingsSection wrapper manages saving/success/error states with timed auto-dismiss
- **Observation**: All components use `transition-colors` or `transition-all` for smooth state changes

### Alternatives Considered
- Adding a custom focus-visible polyfill — unnecessary; all modern target browsers support `:focus-visible` natively
- Creating a shared interactive state mixin — rejected; Tailwind utility classes with CVA already provide this abstraction

---

## Research Task 3: Accessibility (WCAG AA) Compliance Status

### Decision
The codebase has a **solid accessibility foundation** (semantic HTML, keyboard handlers, ARIA attributes, focus management) but lacks automated enforcement. Adding `eslint-plugin-jsx-a11y` for linting and `axe-core` for runtime testing will catch regressions and surface any missed gaps.

### Rationale
Current accessibility patterns found:
- **Semantic HTML**: Proper heading hierarchy, `<time>` elements, `<img>` with alt attributes
- **Keyboard navigation**: Interactive divs with `tabIndex={0}` and `onKeyDown` handlers for Enter/Space
- **ARIA**: `aria-hidden="true"` on decorative icons, `aria-label` on icon-only buttons, `aria-live` regions for dynamic status messages
- **Focus indicators**: All focusable elements use `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
- **Color contrast**: Theme tokens use standard foreground/background pairs that should meet 4.5:1 ratios (needs verification with axe-core)
- **Gaps identified**: No automated a11y linting rules in ESLint config; no automated a11y test runner; no `eslint-plugin-jsx-a11y` installed

### Alternatives Considered
- Pa11y CI — rejected in favor of axe-core due to better React Testing Library integration (via `@axe-core/react` or `jest-axe`)
- Lighthouse CI — considered for performance but heavier than axe-core for a11y; can be added later for performance auditing (Research Task 8)
- Manual-only auditing — rejected; automated tools catch >50% of WCAG AA issues consistently

---

## Research Task 4: Form Validation Patterns

### Decision
Forms use **custom inline validation** (no external library) with per-field error state and immediate feedback. The existing patterns are consistent and well-implemented. The audit should verify all forms follow the established pattern and that no forms allow full-page reloads on submission.

### Rationale
Analysis of form components:
- **MCP Settings** (`McpSettings.tsx`): Custom `validate()` function on submit; field-specific error state (`nameError`, `urlError`); errors clear on field change; HTML `maxLength` constraints; `preventDefault()` on form submit
- **Agent Config** (`AgentConfigRow.tsx`): Dirty state tracking (`isDirty`); save/discard workflow; confirmation flows for destructive operations
- **Settings Sections** (`SettingsSection.tsx`): Wrapper component manages save state lifecycle (idle → saving → success/error) with auto-dismiss; uses `onSave` callback pattern
- **Chat Input** (`ChatInterface.tsx`): Form submit handler with `preventDefault()`; textarea with auto-expand; disabled during `isSending`
- **Global Settings** (`GlobalSettings.tsx`): Numeric inputs with `min`/`max`/`step` constraints; dropdown selections

### Alternatives Considered
- Adding a form library (React Hook Form, Formik) — rejected per constraint of no new UI frameworks; existing custom validation is clean and consistent
- Zod schema validation on the client — rejected; the existing per-field validation is sufficient for the current form complexity

---

## Research Task 5: UI State Handling Coverage

### Decision
UI state handling (loading, empty, error, success) is **well-implemented** in data-fetching components with consistent patterns. Some components may need review to ensure all four states are explicitly handled.

### Rationale
State handling patterns found:
- **Loading states**: Spinner/skeleton patterns in McpSettings ("Loading MCP configurations..."), DynamicDropdown (loading spinner), ChatInterface (animated dots during `isSending`)
- **Empty states**: McpSettings ("No MCPs configured yet"), ChatInterface ("Start a conversation" with example prompts)
- **Error states**: McpSettings (red error alert + retry), DynamicDropdown (error + retry button, auth_required state, rate_limited state), SettingsSection (red "Failed to save" toast)
- **Success states**: McpSettings (green success banner), SettingsSection (green "Saved!" toast with auto-dismiss)
- **ErrorBoundary** (`common/ErrorBoundary.tsx`): Catches unhandled component errors with fallback UI
- **Observation**: The SettingsSection wrapper provides a reusable save-state pattern (idle/saving/success/error) that most settings components use consistently

### Alternatives Considered
- Creating a generic `<AsyncState>` wrapper component — rejected per YAGNI; the existing per-component state handling is clear and each component has unique empty/error messaging
- React Suspense for loading states — not applicable; TanStack Query handles async state, and Suspense boundaries would require significant refactoring

---

## Research Task 6: Current Frontend Test Coverage and Gaps

### Decision
The frontend has **9 unit/integration tests** covering 6 hooks and 2 components. Significant gaps exist for all board components (11 files), most chat components, most settings components, pages, and the API service layer. The test infrastructure (setup.ts, test-utils.tsx, factories/) is mature and ready for expansion.

### Rationale
- **Covered**: useAuth, useRealTimeSync, useProjects, useWorkflow, useProjectBoard, useSettingsForm, useChat (hooks); LoginButton, ErrorBoundary (components)
- **Uncovered hooks**: useSettings, useMcpSettings, useAgentConfig, useAvailableAgents, useAppTheme, and others
- **Uncovered components**: All 11 board components, most of 6 chat components, most of 12 settings components, all UI primitives
- **Uncovered pages**: ProjectBoardPage, SettingsPage
- **Uncovered services**: api.ts (9 namespaces)
- **E2E**: Playwright configured but `e2e/` directory has no test files
- **Test infrastructure strengths**: `createMockApi()` provides typed mocks for all API namespaces; `renderWithProviders()` handles QueryClient wrapping; factory functions create properly typed test data with overrides

### Alternatives Considered
- E2E-only testing strategy — rejected because E2E tests are slow and don't provide isolation for component logic
- Snapshot testing for component output — rejected per spec requirement to use behavior-driven approach
- Adding MSW (Mock Service Worker) — rejected; existing `vi.mock()` + `createMockApi()` is working well and adding MSW would be a new dependency

---

## Research Task 7: Behavior-Driven Testing Best Practices for React

### Decision
Follow React Testing Library's philosophy: test what users see and do, not implementation details. Use `getByRole`, `getByLabelText`, `getByText`, and `getByPlaceholderText` queries. Avoid `getByTestId` unless no semantic alternative exists.

### Rationale
Best practices from the React Testing Library documentation and community:
- **Query priority**: `getByRole` > `getByLabelText` > `getByText` > `getByDisplayValue` > `getByPlaceholderText` > `getByTestId`
- **User interaction**: Use `@testing-library/user-event` (already available via test-utils.tsx) for realistic event simulation
- **Async patterns**: Use `waitFor`, `findBy*` queries for asynchronous state changes (TanStack Query mutations/queries)
- **Avoid**: Testing state values directly, asserting on CSS classes, testing internal hook implementations
- **Hook testing**: Use `renderHook` from `@testing-library/react` with QueryClient wrapper — existing 6 hook tests already follow this pattern
- **Component testing**: Render with `renderWithProviders`, interact via user-event, assert on visible output

### Alternatives Considered
- Enzyme shallow rendering — rejected; deprecated and tests implementation details
- Custom test renderers — rejected; React Testing Library + renderWithProviders is sufficient
- Cypress Component Testing — rejected; would add a heavy dependency for marginal benefit over Vitest + RTL

---

## Research Task 8: Automated Accessibility Auditing in CI

### Decision
Add `axe-core` via `@axe-core/react` for development-time warnings and `vitest-axe` (or `jest-axe` compatible with Vitest) for automated accessibility assertions in tests. Add `eslint-plugin-jsx-a11y` for static analysis. Defer Lighthouse CI to a future iteration for performance monitoring.

### Rationale
- **axe-core**: Industry-standard accessibility engine; catches ~57% of WCAG 2.1 issues automatically; zero false positives design
- **vitest-axe / jest-axe**: Allows `expect(container).toHaveNoViolations()` assertions in component tests; integrates naturally with existing Vitest + RTL setup
- **eslint-plugin-jsx-a11y**: Static analysis catches a11y issues at authoring time (missing alt text, incorrect ARIA, non-interactive element handlers); integrates with existing ESLint config
- **CI integration**: Add a11y assertions to component tests → failures surface in existing "Run tests" CI step; add jsx-a11y to ESLint → failures surface in existing "Lint" CI step
- **Lighthouse CI**: Requires a running server and more complex CI configuration; better suited as a separate initiative focused on performance

### Alternatives Considered
- Pa11y — rejected; less React ecosystem integration than axe-core
- Lighthouse CI for both a11y and performance — deferred; heavier setup, and axe-core provides deeper WCAG coverage for accessibility specifically
- Manual-only a11y auditing — rejected; automated tools provide consistent baseline and prevent regressions

---

## Research Task 9: Responsive Layout Testing Strategy

### Decision
Test responsive layouts at three breakpoints (mobile ≤768px, tablet 769–1024px, desktop ≥1025px) using Playwright viewport configuration for E2E tests and `matchMedia` mocking for Vitest component tests where responsive behavior is logic-driven.

### Rationale
- **Tailwind responsive classes**: The codebase uses Tailwind responsive prefixes (`sm:`, `md:`, `lg:`) for layout changes; these are CSS-only and best verified visually or via E2E
- **Playwright viewport**: Supports `page.setViewportSize()` for testing at specific breakpoints; already configured in `playwright.config.ts`
- **Component-level**: Most responsive behavior is CSS-only (Tailwind breakpoints), so unit tests are not useful for layout; focus E2E tests on critical views (Board, Settings)
- **Known areas**: Board columns layout, settings sidebar/main layout, chat popup positioning, navigation menu collapse

### Alternatives Considered
- Visual regression testing (Percy, Chromatic) — rejected; adds external dependency and cost; manual Playwright viewport tests are sufficient for this scope
- CSS-in-JS media query testing — not applicable; Tailwind handles responsiveness at the CSS level

---

## Research Task 10: Performance Auditing Approach

### Decision
Audit performance using Chrome DevTools Lighthouse locally and document findings in the findings log. Defer CI-integrated Lighthouse to a future iteration. Focus on identifying obvious performance issues (large bundle size, unnecessary re-renders, missing lazy loading).

### Rationale
- **Current state**: No performance monitoring tooling exists in the project
- **Local Lighthouse**: Zero-setup approach — run Lighthouse in Chrome DevTools on each customer-facing view, record LCP/CLS/FID scores
- **CI integration complexity**: Lighthouse CI requires a running server, which adds Docker/process management complexity to the CI pipeline; this is better as a standalone follow-up
- **Quick wins to look for**: Bundle size analysis via `vite build --report`, React.lazy for route-level code splitting, image optimization, unnecessary large dependencies

### Alternatives Considered
- web-vitals npm package for real-user monitoring — out of scope for audit; this is a testing/review feature, not a monitoring feature
- Lighthouse CI in Docker — feasible but adds significant CI complexity; better as a dedicated performance feature
