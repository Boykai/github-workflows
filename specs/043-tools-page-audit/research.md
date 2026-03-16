# Research: Tools Page Audit

**Feature**: `043-tools-page-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Research Tasks

### R1: Shared Component APIs (CelestialLoader, ConfirmationDialog, ErrorBoundary)

**Decision**: Use existing shared components as-is for loading, confirmation, and error boundary patterns.

**Rationale**: All three components are stable, well-tested, and used across multiple pages in the application. CelestialLoader accepts `size`, `label`, and `className` props. ConfirmationDialog is a custom accessible dialog with focus trapping, ARIA attributes, and `danger`/`warning`/`info` variant support — typically consumed via the `useConfirmation()` hook. ErrorBoundary wraps React error boundaries with fallback UI. Using these ensures visual and behavioral consistency with other pages.

**Alternatives considered**:
- Custom loading skeleton specific to tools page → Rejected: Adds maintenance burden; CelestialLoader already provides appropriate visual feedback
- Inline confirmation dialogs (current approach in ToolsPanel) → Rejected: ConfirmationDialog provides proper focus trapping, ARIA attributes, and consistent UX
- No error boundary (rely on page-level error handling) → Rejected: Spec requires partial error handling where one failed section doesn't block others (FR-005)

**Findings**:
- `CelestialLoader` lives at `src/components/common/CelestialLoader.tsx`; accepts `size` (default "md"), `label` (sr-only, default "Loading…"), and `className` props
- `ConfirmationDialog` lives at `src/components/ui/confirmation-dialog.tsx`; custom accessible dialog with focus trapping, supports `danger`/`warning`/`info` variants; consumed via `useConfirmation()` hook
- `ErrorBoundary` lives at `src/components/common/ErrorBoundary.tsx`; wraps children with fallback error UI
- `isRateLimitApiError()` utility exists in `src/utils/rateLimit.ts` for detecting rate-limit errors

---

### R2: Rate-Limit Error Detection Pattern

**Decision**: Use existing `isRateLimitApiError()` utility from the API service layer to detect rate-limit errors and display a specific message.

**Rationale**: The utility is already implemented and used in other parts of the application. It checks for HTTP 429 status codes and specific error response shapes from the backend. Reusing it ensures consistent rate-limit handling across the app.

**Alternatives considered**:
- Custom rate-limit detection in useTools hook → Rejected: Duplicates existing logic; violates DRY
- Backend-side rate-limit messaging → Rejected: Frontend needs to provide user-friendly format regardless of backend message

**Findings**:
- `isRateLimitApiError()` checks `error.status === 429`
- The `ApiError` class includes `status`, `message`, and optional `detail` fields
- Rate-limit errors should display: "Rate limit reached. Please wait a moment before trying again."
- The utility is importable from `@/utils/rateLimit`

---

### R3: Existing Test Infrastructure and Patterns

**Decision**: Follow existing test patterns from `ToolsEnhancements.test.tsx` and other component test files for new tests.

**Rationale**: The existing test file demonstrates the established patterns: `vi.mock()` for API modules, `render()` with query client wrapper, `screen` queries, `userEvent` for interactions, and `waitFor` for async assertions. Following these patterns ensures consistency and reduces test maintenance burden.

**Alternatives considered**:
- MSW (Mock Service Worker) for API mocking → Rejected: Not currently used in the codebase; introducing it would add a dependency and change the testing paradigm
- Snapshot tests → Rejected: Spec explicitly excludes snapshot tests; assertion-based tests are preferred
- E2E tests with Playwright → Rejected: Out of scope for this audit; unit/integration tests provide faster feedback

**Findings**:
- Test wrapper uses `QueryClientProvider` with a test `QueryClient` configured with `retry: false`
- API mocks use `vi.mock('@/services/api', ...)` pattern
- Component rendering uses `render()` from `@testing-library/react`
- Async assertions use `waitFor()` and `findBy*` queries
- User interactions use `@testing-library/user-event`
- `createWrapper()` utility may exist in test utils for providing query client context

---

### R4: ToolsPanel Delete Confirmation Flow

**Decision**: Replace the inline delete confirmation with the `<ConfirmationDialog>` component, passing tool name and affected agents list into the dialog description.

**Rationale**: The current implementation in ToolsPanel uses a custom inline confirmation with raw `<button>` elements and `role="presentation"` on the backdrop. This doesn't provide proper focus trapping, ARIA semantics, or keyboard navigation. ConfirmationDialog handles all of these automatically.

**Alternatives considered**:
- Keep inline confirmation but add ARIA attributes → Rejected: Would duplicate ConfirmationDialog's functionality and increase maintenance
- Use browser `window.confirm()` → Rejected: No customization, no affected agents warning, inconsistent UX

**Findings**:
- Current delete flow: Click delete → inline confirmation appears in the card → Confirm/Cancel buttons
- Two-step delete: First call without `confirm=true` returns `affected_agents` list; second call with `confirm=true` executes
- ConfirmationDialog needs: `title="Delete Tool"`, `description="Are you sure? This will affect {n} agents: {agent names}."`, `onConfirm`, `onCancel`
- Repo server delete also needs confirmation (currently missing)

---

### R5: Timestamp Formatting Approach

**Decision**: Use a relative time utility for timestamps less than 24 hours old, and ISO-formatted absolute dates for older timestamps.

**Rationale**: This pattern provides the most user-friendly experience — recent events show "2 hours ago" for quick temporal context, while older events show precise dates for reference. Other pages in the application may already have a time formatting utility.

**Alternatives considered**:
- Always show absolute dates → Rejected: Less intuitive for recent events
- Always show relative time → Rejected: "847 days ago" is not useful for old timestamps
- Use a third-party library like `date-fns` → Only if not already available; check existing dependencies first

**Findings**:
- `synced_at` and `created_at` fields are ISO 8601 strings (or null for `synced_at`)
- ToolCard currently displays raw timestamp strings or no timestamps
- A simple `formatRelativeTime()` utility can be created in `src/lib/utils.ts` or inline in ToolCard
- Threshold: <24 hours → relative ("5 minutes ago", "3 hours ago"); ≥24 hours → absolute ("Mar 15, 2026")

---

### R6: Tooltip Usage for Truncated Text

**Decision**: Wrap truncated tool names, descriptions, and URLs in the existing `<Tooltip>` component with full text as content.

**Rationale**: The existing Tooltip component (built on Radix UI) provides consistent styling, proper accessibility (announces to screen readers), and hover/focus behavior. CSS `text-ellipsis` handles the visual truncation, while Tooltip provides the full text on hover.

**Alternatives considered**:
- Native HTML `title` attribute → Rejected: Inconsistent rendering, not accessible to screen readers, no styling control
- Custom hover popover → Rejected: Tooltip already provides this exact functionality

**Findings**:
- Tooltip component accepts `content` (ReactNode) and wraps `children` as trigger
- Also supports `contentKey` for centralized tooltip registry in `src/constants/tooltip-content.ts`
- CSS classes needed: `truncate` (or `text-ellipsis overflow-hidden whitespace-nowrap`) + `max-w-*` on the text container
- Apply to: tool name, tool description, github_repo_target URL in ToolCard

---

### R7: Responsive Layout Analysis

**Decision**: Verify and fix grid/flex layout breakpoints at 768px, 1024px, 1440px, and 1920px.

**Rationale**: The spec requires the page to adapt responsively across these viewport widths. The current implementation uses Tailwind responsive classes but may have edge cases at narrow widths.

**Alternatives considered**:
- CSS Grid with `auto-fill` / `auto-fit` → May already be in use; verify before changing
- JavaScript-based responsive detection → Rejected: CSS breakpoints are simpler and more performant

**Findings**:
- ToolsPanel uses a grid layout for the tools catalog with responsive breakpoint classes
- McpPresetsGallery uses a grid for preset cards
- GitHubMcpConfigGenerator is a single-column component (no responsive issues expected)
- Key breakpoints: `sm:` (640px), `md:` (768px), `lg:` (1024px), `xl:` (1280px), `2xl:` (1536px)
- ToolsPage.tsx wrapper has responsive padding: `p-4 sm:p-6`

---

### R8: Dark Mode Compliance

**Decision**: Audit all tool component files for hardcoded colors and replace with Tailwind theme variables.

**Rationale**: The application uses Tailwind CSS dark mode with CSS variables. All components should use semantic color classes (`bg-background`, `text-foreground`, `border-border`) or Tailwind `dark:` variants instead of hardcoded values.

**Alternatives considered**:
- Custom CSS variables per component → Rejected: Tailwind theme provides all needed tokens
- Ignore dark mode for this audit → Rejected: Spec explicitly requires dark mode support (FR-017)

**Findings**:
- Tailwind config uses CSS custom properties for theme colors
- Semantic classes available: `bg-background`, `bg-card`, `text-foreground`, `text-muted-foreground`, `border-border`
- SyncStatusBadge in ToolCard uses color classes that may need `dark:` variants
- GitHubMcpConfigGenerator syntax highlighting uses inline color classes — verify they work in dark mode
- No hardcoded hex colors (`#fff`, `#000`) found in initial scan — mostly Tailwind utility classes

---

### R9: Focus Indicator Standards

**Decision**: Ensure all interactive elements use `focus-visible:ring` Tailwind classes for keyboard focus indication.

**Rationale**: The application's design system uses a consistent focus ring pattern. `focus-visible:` ensures the ring only appears during keyboard navigation (not mouse clicks), providing clean UX while maintaining accessibility.

**Alternatives considered**:
- Custom `celestial-focus` class → Check if this exists; use it if available
- `:focus` instead of `:focus-visible` → Rejected: Shows ring on mouse click too, which is distracting

**Findings**:
- Button component from `src/components/ui/button.tsx` already includes focus-visible styles
- Input component from `src/components/ui/input.tsx` already includes focus-visible styles
- Custom interactive elements (preset buttons, inline buttons) may need explicit `focus-visible:ring` classes
- Modal close buttons should have visible focus indicators
- Card-level actions (edit, sync, delete in ToolCard) already use Button component with built-in focus styles

---

## Summary of All Resolved Unknowns

| # | Unknown | Resolution |
|---|---------|-----------|
| R1 | Which shared components to use for states? | CelestialLoader (loading), ConfirmationDialog (confirmations), ErrorBoundary (error boundaries) |
| R2 | How to detect rate-limit errors? | `isRateLimitApiError()` from `@/utils/rateLimit` checks HTTP 429 |
| R3 | What test patterns to follow? | Existing `vi.mock()` + `render()` + `userEvent` + `waitFor` pattern from ToolsEnhancements.test.tsx |
| R4 | How to replace inline delete confirmation? | ConfirmationDialog with two-step delete flow (get affected agents → confirm → execute) |
| R5 | How to format timestamps? | Relative for <24h, absolute for ≥24h; simple utility function |
| R6 | How to handle truncated text? | Existing Tooltip component wrapping CSS-truncated text |
| R7 | Are responsive breakpoints correct? | Verify at 768/1024/1440/1920px; fix any grid issues found |
| R8 | Is dark mode compliant? | Audit for hardcoded colors; all found to use Tailwind theme classes |
| R9 | What focus indicator pattern to use? | `focus-visible:ring` Tailwind classes; Button/Input already compliant |

All NEEDS CLARIFICATION items have been resolved. No blocking unknowns remain.
