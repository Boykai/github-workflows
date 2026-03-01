# Quickstart: Deep UX/UI Review, Polish & Meaningful Frontend Test Coverage

**Feature**: 014-ux-ui-review-testing | **Date**: 2026-02-28

## Prerequisites

- Node.js 20+
- npm (ships with Node.js)
- Chrome/Chromium (for Lighthouse auditing and Playwright E2E)

## Setup

### Frontend

```bash
cd frontend
npm ci
```

### Install Playwright Browsers (first time only)

```bash
cd frontend
npx playwright install chromium
```

## Running Tests

### Frontend Unit/Integration Tests

```bash
# Run all frontend tests
cd frontend
npm test

# Run in watch mode (re-runs on file changes)
npm run test:watch

# Run with coverage
npm run test:coverage

# Run a specific test file
npx vitest run src/hooks/useAuth.test.tsx

# Run a specific component test
npx vitest run src/components/settings/McpSettings.test.tsx

# Run all tests matching a pattern
npx vitest run --reporter=verbose src/components/
```

### Frontend E2E Tests

```bash
# Run E2E tests (headless)
cd frontend
npm run test:e2e

# Run with visible browser
npm run test:e2e:headed

# Run with Playwright UI (interactive debugging)
npm run test:e2e:ui

# View last test report
npm run test:e2e:report

# Run a specific E2E test file
npx playwright test e2e/board-navigation.spec.ts
```

## Linting and Type Checking

```bash
cd frontend

# Lint (includes jsx-a11y rules after setup)
npm run lint

# Auto-fix lint issues
npm run lint:fix

# Type check
npm run type-check

# Build (validates types + produces bundle)
npm run build
```

## Accessibility Auditing

### Automated (in tests)

```bash
# Run tests — axe-core assertions will catch a11y violations
cd frontend
npm test
```

### Manual (Chrome DevTools)

1. Start the dev server: `cd frontend && npm run dev`
2. Open Chrome DevTools → Lighthouse tab
3. Select "Accessibility" category
4. Run audit on each customer-facing view:
   - Home page (`/`)
   - Project Board (`/#board`)
   - Settings (`/#settings`)

### Manual (axe DevTools Extension)

1. Install the [axe DevTools browser extension](https://www.deque.com/axe/devtools/)
2. Navigate to each customer-facing view
3. Run "Scan all of my page"
4. Document findings in the findings log

## Performance Auditing

### Lighthouse (Chrome DevTools)

1. Start the dev server: `cd frontend && npm run dev`
2. Open Chrome DevTools → Lighthouse tab
3. Select "Performance" category
4. Run audit on each customer-facing view
5. Record LCP, CLS, INP scores
6. Flag views with poor Core Web Vitals:
   - LCP > 2.5s = poor
   - INP > 200ms = poor
   - CLS > 0.1 = poor

### Bundle Analysis

```bash
cd frontend
npm run build
# Check dist/ size for large chunks
ls -lh dist/assets/
```

## Key Directories

| Path | Description |
|------|-------------|
| `frontend/src/index.css` | Design tokens (CSS custom properties for colors, radius) |
| `frontend/tailwind.config.js` | Tailwind configuration referencing CSS variables |
| `frontend/src/components/ui/` | UI primitives (button, card, input) |
| `frontend/src/components/board/` | Board components (columns, cards, modals) |
| `frontend/src/components/chat/` | Chat components (interface, messages) |
| `frontend/src/components/settings/` | Settings components (sections, forms) |
| `frontend/src/components/ThemeProvider.tsx` | Theme context (light/dark/system) |
| `frontend/src/test/setup.ts` | Vitest global setup + createMockApi() |
| `frontend/src/test/test-utils.tsx` | renderWithProviders, createTestQueryClient |
| `frontend/src/test/factories/` | Test data factories |
| `frontend/e2e/` | Playwright E2E tests |
| `frontend/eslint.config.js` | ESLint config (jsx-a11y rules to be added) |

## Workflow for This Feature

### 1. Visual Consistency Audit (User Story 1)
- Inspect each customer-facing view for typography, color, spacing, iconography consistency
- Verify all components use design tokens (no hardcoded values)
- Check all interactive elements for hover, focus, active, disabled states
- Log findings in the findings log

### 2. Accessibility Audit (User Story 2)
- Run axe-core / Lighthouse accessibility audit on all views
- Verify WCAG AA compliance (4.5:1 contrast, keyboard nav, ARIA attributes)
- Add `eslint-plugin-jsx-a11y` to ESLint config
- Test all UI states: loading, empty, error, success
- Log findings in the findings log

### 3. Form & Content Validation (User Story 3)
- Test all forms for inline validation (required fields, format errors, submission failures)
- Verify no full-page reloads on form submission
- Scan all views for placeholder/lorem ipsum text, broken images, console errors
- Log findings in the findings log

### 4. Automated Test Coverage (User Story 4)
- Write integration tests for critical user flows using behavior-driven approach
- Add axe-core accessibility assertions to component tests
- Add regression tests for every bug fixed during the audit
- Use existing test infrastructure (createMockApi, renderWithProviders, factories)

### 5. Responsive Layout Review (User Story 5)
- Test all views at mobile (≤768px), tablet (769–1024px), desktop (≥1025px)
- Verify no overflow, overlap, or broken elements
- Log findings in the findings log

### 6. Performance Audit & Documentation (User Story 6)
- Run Lighthouse performance audit on all customer-facing views
- Record LCP, CLS, INP scores
- Document all findings in structured findings log with severity ratings
- Integrate a11y linting + test assertions into CI pipeline

### 7. Verification
- Run full test suite: `cd frontend && npm test`
- Run lint: `cd frontend && npm run lint`
- Run type check: `cd frontend && npm run type-check`
- Run build: `cd frontend && npm run build`
- Verify CI passes on PR
