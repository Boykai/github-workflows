---
name: UI Aduit
about: Recurring chore — UI Aduit
title: '[CHORE] UI Aduit'
labels: chore
assignees: ''
---

## Plan: [PAGE_NAME] Page Audit

## TL;DR

Comprehensive audit of the **[PAGE_NAME]** page to ensure modern best practices, modular design, accurate text/copy, and zero bugs. Covers component decomposition, accessibility, error/loading/empty states, type safety, test coverage, and UI/UX polish.

---

## Audit Checklist

### 1. Component Architecture & Modularity

- [ ] **Single Responsibility**: Page file is ≤250 lines. If larger, extract sub-components into `src/components/[feature]/`
- [ ] **Feature folder structure**: All sub-components live in `src/components/[feature]/` (not inline in the page file)
- [ ] **No prop drilling >2 levels**: Use composition, context, or hook extraction instead
- [ ] **Reusable primitives**: Use existing `src/components/ui/` (Button, Card, Input, Tooltip, ConfirmationDialog, HoverCard) — don't reimplement
- [ ] **Shared components**: Use `CelestialLoader`, `ErrorBoundary`, `ProjectSelectionEmptyState`, `ThemedAgentIcon` from `src/components/common/` where applicable
- [ ] **Hook extraction**: Complex state logic (>15 lines of useState/useEffect/useCallback) extracted into `src/hooks/use[Feature].ts`
- [ ] **No business logic in JSX**: Computation and data transformation happens in hooks or helper functions, not inline in the render tree

### 2. Data Fetching & State Management

- [ ] **React Query for all API calls**: Uses `useQuery` / `useMutation` from TanStack Query — no raw `useEffect` + `fetch`
- [ ] **Query key conventions**: Follows `[feature].all / .list(id) / .detail(id)` pattern (see `pipelineKeys`, `appKeys` examples)
- [ ] **Optimistic updates where appropriate**: Mutations that update lists should `invalidateQueries` on success
- [ ] **staleTime configured**: Data that doesn't change frequently has a reasonable `staleTime` (e.g., 30s for lists, 60s for settings)
- [ ] **No duplicate API calls**: Check that the same data isn't fetched in both the page and a child component independently
- [ ] **Mutation error handling**: All `useMutation` calls have `onError` that surfaces user-visible feedback (toast, inline error, etc.)

### 3. Loading, Error & Empty States

- [ ] **Loading state**: Shows `<CelestialLoader size="md" />` or skeleton while data loads — never a blank screen
- [ ] **Error state**: API errors render a clear message with a retry action. Uses `isRateLimitApiError()` for rate limit detection
- [ ] **Empty state**: When data is loaded but collection is empty, shows a meaningful empty state (not just nothing)
- [ ] **Partial loading**: If page has multiple data sources, independent sections show their own loading/error states (don't let one failed section block the whole page)
- [ ] **Error boundary**: Page is wrapped in `<ErrorBoundary>` (either at route level in App.tsx or within the page)

### 4. Type Safety

- [ ] **No `any` types**: All props, state, API responses fully typed
- [ ] **No type assertions (`as`)**: Prefer type guards or discriminated unions
- [ ] **API response types match backend**: Types in `src/types/` aligned with Pydantic models. Date fields are `string` (ISO), nullable fields use `| null`
- [ ] **Event handler types explicit**: Form events use `React.FormEvent<HTMLFormElement>`, not generic `any`
- [ ] **Hook return types**: Custom hooks have explicit return type annotations or are inferrable without ambiguity

### 5. Accessibility (a11y)

- [ ] **All interactive elements keyboard-accessible**: Buttons, links, toggles, custom controls reachable via Tab and activated via Enter/Space
- [ ] **Focus management**: Dialogs/modals trap focus. When a dialog closes, focus returns to the trigger element
- [ ] **ARIA attributes**: Custom controls (dropdowns, toggles, tabs) have `role`, `aria-label`, `aria-expanded`, `aria-selected` as needed
- [ ] **Labels on all form fields**: Every `<input>`, `<select>`, `<textarea>` has a visible or `aria-label` label. ESLint `jsx-a11y/label-has-associated-control` enforced
- [ ] **Color contrast**: Text meets WCAG AA (4.5:1 ratio). Status indicators don't rely on color alone — use icon + text
- [ ] **Focus-visible styles**: All interactive elements use the `celestial-focus` class or Tailwind `focus-visible:` ring
- [ ] **Screen reader text**: Decorative icons have `aria-hidden="true"`. Meaningful icons have `aria-label`

### 6. Text, Copy & UX Polish

- [ ] **No placeholder text**: All user-visible strings are final, meaningful copy (no "TODO", "Lorem ipsum", "Test")
- [ ] **Consistent terminology**: Uses the same terms as the rest of the app (e.g., "pipeline" not "workflow", "chore" not "task", etc.)
- [ ] **Action button labels are verbs**: "Create Agent" not "New Agent", "Save Settings" not "Settings", "Delete" not "Remove"
- [ ] **Confirmation on destructive actions**: All delete/remove/stop actions use `<ConfirmationDialog>` — never immediate
- [ ] **Success feedback**: Mutations show success state (toast, status change, or inline message)
- [ ] **Error messages are user-friendly**: No raw error codes or stack traces. Format: "Could not [action]. [Reason, if known]. [Suggested next step]."
- [ ] **Timestamps formatted consistently**: Use relative time ("2 hours ago") for recent, absolute for older
- [ ] **Truncation with tooltip**: Long text (names, descriptions, URLs) truncated with `text-ellipsis` and full text in a `<Tooltip>`

### 7. Styling & Layout

- [ ] **Tailwind utility classes only**: No inline `style={}` attributes. Uses `cn()` for conditional classes
- [ ] **Responsive design**: Page isn't broken at viewport widths 768px–1920px. Grid/flex layouts adapt
- [ ] **Dark mode support**: Uses Tailwind `dark:` variants or CSS variables from the theme. No hardcoded colors like `#fff` or `bg-white`
- [ ] **Consistent spacing**: Uses Tailwind spacing scale (e.g., `gap-4`, `p-6`) — no arbitrary values like `p-[13px]`
- [ ] **Card/section consistency**: Content sections use `<Card>` from `src/components/ui/card.tsx` with consistent padding/rounding
- [ ] **Loading shimmer/skeleton**: Consider skeleton loading states instead of spinners for content areas

### 8. Performance

- [ ] **No unnecessary re-renders**: Expensive components wrapped in `React.memo()` where props are stable. Callbacks use `useCallback` only when passed to memoized children
- [ ] **Lists have stable keys**: Array renders use `key={item.id}` — never `key={index}`
- [ ] **Large lists virtualized**: If rendering >50 items, consider `react-window` or pagination
- [ ] **No sync computation in render**: Heavy transforms (sorting, filtering, grouping) wrapped in `useMemo`
- [ ] **Images/icons lazy loaded**: Non-critical images use `loading="lazy"`

### 9. Test Coverage

- [ ] **Hook tests exist**: Custom hooks for this page tested via `renderHook()` with mocked API
- [ ] **Component tests exist**: Key interactive components have `.test.tsx` files testing user interactions
- [ ] **Test patterns follow codebase conventions**: Uses `vi.mock('@/services/api', ...)`, `renderHook`, `waitFor`, `createWrapper()`
- [ ] **Edge cases covered**: Empty state, error state, loading state, rate limit error, long strings, null/missing data
- [ ] **No snapshot tests**: Prefer assertion-based tests over fragile snapshots

### 10. Code Hygiene

- [ ] **No dead code**: Unused imports, commented-out blocks, or unreachable branches removed
- [ ] **No console.log**: All removed or replaced with structured logging if needed
- [ ] **Imports use `@/` alias**: All project imports use `@/components/...`, `@/hooks/...`, `@/services/...` — not relative `../../`
- [ ] **File naming**: Components are PascalCase `.tsx`, hooks are `use*.ts`, types in `types/`, utilities in `lib/`
- [ ] **No magic strings**: Repeated strings (status values, route paths, query keys) defined as constants
- [ ] **ESLint clean**: `npx eslint src/pages/[PageName].tsx src/components/[feature]/ src/hooks/use[Feature].ts` — 0 warnings

---

## Implementation Steps

### Phase 1: Discovery & Assessment

1. **Read the page file** — Note line count, identify sub-components, hooks used, API calls made
2. **Read all related components** in `src/components/[feature]/`
3. **Read the related hook(s)** in `src/hooks/`
4. **Read the related API group** in `src/services/api.ts`
5. **Read the related types** in `src/types/`
6. **Run the page in browser** — Note visual issues, check dark mode, resize viewport
7. **Run existing tests** — `npx vitest run src/**/*[feature]*` — note what's covered
8. **Run lint** — `npx eslint src/pages/[PageName].tsx src/components/[feature]/` — note violations
9. **Score each checklist item** — Pass / Fail / N/A — produce a findings table

### Phase 2: Structural Fixes (if needed)

1. **Extract oversized page into sub-components** — Move self-contained sections into `src/components/[feature]/[SectionName].tsx`
2. **Extract complex state into hooks** — Move >15-line state blocks into `src/hooks/use[Feature].ts`
3. **Replace raw fetches with React Query** — If any `useEffect` + `fetch` patterns exist
4. **Add missing types** — Eliminate `any`, add explicit return types to hooks

### Phase 3: States & Error Handling

1. **Add/fix loading state** — `<CelestialLoader>` or skeleton
2. **Add/fix error state** — User-friendly message + retry button + rate limit detection
3. **Add/fix empty state** — Meaningful empty state with call-to-action
4. **Add confirmation dialogs** — For all destructive actions missing them

### Phase 4: a11y & UX Polish

1. **Add missing ARIA attributes** — roles, labels, expanded states
2. **Fix keyboard navigation** — Tab order, Enter/Space activation, focus trapping in modals
3. **Fix text/copy issues** — Consistent terminology, verb-based buttons, user-friendly errors
4. **Add tooltips for truncated text** — Long names, descriptions, URLs
5. **Verify dark mode** — All elements visible and contrasted

### Phase 5: Testing

1. **Write/update hook tests** — Cover happy path, error, loading, empty states
2. **Write/update component tests** — Cover user interactions, form submissions, dialog confirmations
3. **Verify all edge cases** — null data, rate limit errors, long strings, rapid clicks

### Phase 6: Validation

1. **`npx eslint src/pages/[PageName].tsx src/components/[feature]/`** — 0 warnings
2. **`npx tsc --noEmit`** — 0 type errors
3. **`npx vitest run`** — all tests pass
4. **Manual browser check** — light mode, dark mode, responsive, keyboard-only navigation

---

## Relevant Files (fill per page)

### Page & Components

- `solune/frontend/src/pages/[PageName].tsx` — The page
- `solune/frontend/src/components/[feature]/` — Feature components

### Hooks & API

- `solune/frontend/src/hooks/use[Feature].ts` — Data fetching / state hooks
- `solune/frontend/src/services/api.ts` — API call definitions (relevant group)

### Types

- `solune/frontend/src/types/index.ts` or `src/types/[feature].ts` — Type definitions

### Shared (reference, use as-is)

- `solune/frontend/src/components/ui/` — Button, Card, Input, Tooltip, ConfirmationDialog
- `solune/frontend/src/components/common/` — CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState
- `solune/frontend/src/lib/utils.ts` — `cn()` helper

### Tests

- `solune/frontend/src/hooks/use[Feature].test.ts`
- `solune/frontend/src/components/[feature]/*.test.tsx`

---

## Verification

1. `npx eslint src/pages/[PageName].tsx src/components/[feature]/` — 0 warnings
2. `npx tsc --noEmit` — 0 errors
3. `npx vitest run` — all tests pass
4. Browser: light mode, dark mode, viewport 768px → 1920px
5. Keyboard: Tab through all interactive elements, Enter/Space to activate
6. Screen reader: Verify labels read correctly (or use axe DevTools audit)
