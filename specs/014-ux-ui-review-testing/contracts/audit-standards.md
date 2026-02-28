# Audit Standards Contract: 014-ux-ui-review-testing

**Date**: 2026-02-28

> This feature does not introduce new API endpoints. Instead of REST/GraphQL contracts, this document defines the **audit standards, testing conventions, and acceptance criteria** that all UX/UI review work and test code must follow.

## Visual Consistency Standards

### Design Token Usage
- All colors MUST reference CSS custom properties via Tailwind utility classes (e.g., `bg-primary`, `text-foreground`)
- No hardcoded hex (`#fff`), rgb (`rgb(0,0,0)`), or hsl (`hsl(0,0%,0%)`) values in component files
- Spacing MUST use Tailwind spacing scale (e.g., `p-4`, `gap-2`, `mt-6`)
- Border radius MUST use the `rounded-*` Tailwind classes backed by `--radius` token
- Font sizes MUST use Tailwind typography scale (`text-sm`, `text-base`, `text-lg`, etc.)

### Iconography
- All icons MUST come from the Lucide React library (already in use)
- Icons MUST have consistent sizing within context (e.g., `h-4 w-4` for inline, `h-5 w-5` for buttons)
- Decorative icons MUST have `aria-hidden="true"`
- Meaningful icons MUST have an accessible label (`aria-label` or adjacent text)

---

## Interactive Element Standards

### Required States
Every interactive element (button, link, input, dropdown, modal trigger) MUST implement:

| State | Tailwind Pattern | Verification |
|-------|-----------------|--------------|
| Default | Base styles | Visual inspection |
| Hover | `hover:bg-*`, `hover:text-*` | Mouse hover |
| Focus | `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` | Tab navigation |
| Active | `active:scale-*` or visual press feedback | Click/tap |
| Disabled | `disabled:opacity-50 disabled:pointer-events-none` | Set disabled prop |

### Keyboard Navigation
- All interactive elements MUST be reachable via Tab key
- Custom interactive elements (divs with `onClick`) MUST have `role="button"`, `tabIndex={0}`, and `onKeyDown` handler for Enter/Space
- Modal open/close MUST be keyboard-accessible (Escape to close)
- Focus MUST be trapped within open modals

---

## Accessibility Standards (WCAG AA)

### Color Contrast
- Normal text (< 18px or < 14px bold): minimum 4.5:1 contrast ratio
- Large text (≥ 18px or ≥ 14px bold): minimum 3:1 contrast ratio
- UI components and graphical objects: minimum 3:1 contrast ratio
- Verification: axe-core automated checks + manual spot-check with Chrome DevTools

### Semantic HTML
- Headings MUST follow hierarchical order (h1 → h2 → h3, no skipping)
- Lists MUST use `<ul>`, `<ol>`, `<li>` elements
- Forms MUST use `<label>` elements associated with inputs via `htmlFor`/`id`
- Navigation MUST use `<nav>` landmarks
- Main content MUST use `<main>` landmark

### ARIA Requirements
- `aria-label` on icon-only buttons and links
- `aria-hidden="true"` on decorative elements
- `aria-live="polite"` on dynamically updating status regions
- `aria-expanded` on expandable/collapsible sections
- `role="alert"` on error messages that need immediate attention

### ESLint Enforcement
```javascript
// eslint.config.js addition
import jsxA11y from 'eslint-plugin-jsx-a11y';

// Add to plugins and rules:
plugins: { 'jsx-a11y': jsxA11y },
rules: {
  ...jsxA11y.configs.recommended.rules,
}
```

---

## Form Validation Standards

### Inline Validation Contract
- Required field validation MUST display message without full-page reload
- Format validation MUST show message on blur or on submit (not on every keystroke)
- Submission failure MUST display inline error message with guidance
- Validation errors MUST clear when user corrects the input
- Form submit handler MUST call `event.preventDefault()`

### Error Message Format
- Field-level errors: Red text below the input field, associated via `aria-describedby`
- Form-level errors: Alert banner above or below the form with `role="alert"`
- Success messages: Green text/banner with auto-dismiss (using existing SettingsSection pattern)

---

## UI State Standards

### Required States per Data-Driven Component
Every component that fetches or displays data MUST handle:

| State | Implementation | User Feedback |
|-------|---------------|---------------|
| Loading | Spinner, skeleton, or "Loading..." text | Clear visual indicator that data is being fetched |
| Empty | Meaningful message with optional action | Tell user why empty and what to do |
| Error | Error message with retry option | Explain what went wrong and offer recovery |
| Success | Content displayed correctly | Data rendered as expected |

### State Transition Timing
- Loading indicators MUST appear within 100ms of data request
- Success/error toasts MUST auto-dismiss after a configurable timeout (use existing `TOAST_SUCCESS_MS`/`TOAST_ERROR_MS` constants)
- Loading state MUST not flash for fast responses (consider minimum display time or skip for < 200ms loads)

---

## Testing Conventions

### File Naming
- Hook tests: `frontend/src/hooks/<hookName>.test.tsx` (co-located)
- Component tests: `frontend/src/components/<category>/<ComponentName>.test.tsx` (co-located)
- Page tests: `frontend/src/pages/<PageName>.test.tsx` (co-located)
- E2E tests: `frontend/e2e/<flow-name>.spec.ts`

### Test Structure (AAA Pattern)
```typescript
describe('ComponentName', () => {
  it('describes expected user-visible behavior', async () => {
    // Arrange
    const mockData = createMockProject({ name: 'Test Project' });
    vi.mocked(api.projectsApi.list).mockResolvedValue([mockData]);

    // Act
    renderWithProviders(<ProjectSelector />);

    // Assert
    expect(await screen.findByRole('combobox')).toBeInTheDocument();
    expect(screen.getByText('Test Project')).toBeInTheDocument();
  });
});
```

### Query Priority (Behavior-Driven)
1. `getByRole` — preferred for all interactive elements
2. `getByLabelText` — for form inputs with labels
3. `getByText` — for static content and headings
4. `getByDisplayValue` — for filled form fields
5. `getByPlaceholderText` — when no label exists (flag as a11y issue)
6. `getByTestId` — last resort only, must be justified in PR description

### Accessibility Test Pattern
```typescript
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = renderWithProviders(<Component />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Mock Strategy
- Use `createMockApi()` from `src/test/setup.ts` for all API mocks
- Use factory functions from `src/test/factories/` for test data
- Use `renderWithProviders()` from `src/test/test-utils.tsx` for component rendering
- Use `userEvent` from `@testing-library/user-event` for user interactions
- Never mock internal component state — test via user interactions and visible output

### E2E Test Pattern (Playwright)
```typescript
import { test, expect } from '@playwright/test';

test('user can navigate to board and see columns', async ({ page }) => {
  await page.goto('/');
  await page.click('text=Go to Board');
  await expect(page.getByRole('heading', { name: 'Board' })).toBeVisible();
});
```

---

## Responsive Layout Standards

### Breakpoints
| Name | Width | Tailwind Prefix |
|------|-------|-----------------|
| Mobile | ≤768px | default (no prefix) |
| Tablet | 769–1024px | `md:` |
| Desktop | ≥1025px | `lg:` |

### Requirements per Breakpoint
- No horizontal overflow at any breakpoint
- No content clipping or overlapping elements
- Touch targets ≥ 44×44px on mobile
- Readable text without horizontal scrolling
- Navigation accessible on all breakpoints

---

## CI Integration Contract

### Accessibility in CI (via existing steps)
```yaml
# Covered by existing "Run tests" step — a11y assertions in component tests
- name: Run tests
  run: npm test

# Covered by existing "Lint" step — jsx-a11y rules
- name: Lint
  run: npm run lint
```

### No New CI Steps Required
- axe-core assertions run as part of Vitest unit tests
- jsx-a11y rules run as part of ESLint linting
- Both are already executed in the existing CI pipeline
