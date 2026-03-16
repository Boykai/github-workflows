# Quickstart: Chores Page Audit — Modern Best Practices, Modular Design, and Zero Bugs

**Feature Branch**: `043-chores-page-audit`
**Date**: 2026-03-16

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and `uv` (for backend, if running locally)
- A GitHub token configured in `.env` for API access

## Setup

```bash
# Clone and checkout
git checkout 043-chores-page-audit

# Install frontend dependencies
cd solune/frontend
npm install

# Verify existing tests pass
npm run test
npm run lint
npm run type-check
```

## Development Workflow

### 1. Run the Frontend Dev Server

```bash
cd solune/frontend
npm run dev
```

The Chores page is available at `http://localhost:5173/chores` (or the port shown in terminal).

### 2. Run the Backend (if testing with live data)

```bash
cd solune/backend
uv run --extra dev uvicorn src.main:app --reload --port 8000
```

### 3. Audit Checklist

Work through the audit in priority order matching the spec:

#### P1: Correct and Complete Page States (User Story 1)

- [ ] Test loading state (CelestialLoader renders correctly)
- [ ] Test no-project-selected state (ProjectSelectionEmptyState)
- [ ] Test empty chores state (no chores — meaningful message with CTA)
- [ ] Test populated catalog (chore cards render correctly)
- [ ] Test error state (error banner with retry)
- [ ] Test rate limit state (isRateLimitApiError detection + banner)
- [ ] Test partial loading (one data source fails, others succeed)
- [ ] Verify no console errors in any state

#### P1: Modular Component Architecture and Type Safety (User Story 2)

- [ ] Decompose ChoresPanel (543 lines → ≤250 + sub-components)
- [ ] Decompose ChoreCard (584 lines → ≤250 + sub-components)
- [ ] Decompose AddChoreModal (356 lines → ≤250 + sub-components)
- [ ] Verify no prop drilling >2 levels after decomposition
- [ ] Eliminate all `any` types and type assertions (`as`)
- [ ] Add explicit types to all event handlers
- [ ] Extract complex state logic (>15 lines) into hooks
- [ ] Move business logic out of JSX render tree

#### P2: Accessibility (User Story 3)

- [ ] Tab through all interactive elements — verify focus order and indicators
- [ ] Test Escape key on AddChoreModal, ConfirmChoreModal, PipelineSelector
- [ ] Verify ARIA attributes on toggles (status, AI enhance), selectors, modals
- [ ] Verify all form inputs have labels (search input, schedule value, etc.)
- [ ] Run contrast checker on muted text elements
- [ ] Verify status indicators use icon + text (not color alone)
- [ ] Test focus trapping in modals (AddChoreModal, ConfirmChoreModal)
- [ ] Verify decorative icons have aria-hidden="true"

#### P2: Text, Copy, and UX Polish (User Story 4)

- [ ] Verify all text is final copy (no TODO, Lorem ipsum, placeholder)
- [ ] Verify consistent terminology ("chore" not "task", "trigger" not "run")
- [ ] Verify action buttons are verb-based ("Trigger Chore", "Delete Chore")
- [ ] Verify all destructive actions use ConfirmationDialog
- [ ] Verify all mutations show success feedback (toast/inline)
- [ ] Verify error messages follow "Could not [action]. [Reason]. [Next step]." format
- [ ] Verify long text truncated with tooltip
- [ ] Verify timestamps use relative time (recent) / absolute (older)

#### P2: Responsive Layout and Visual Consistency (User Story 5)

- [ ] Test at 1280px+ (desktop) — full grid visible
- [ ] Test at 768px–1279px (tablet) — reduced columns
- [ ] Test at below 768px (mobile) — cards stack, touch targets ≥44px
- [ ] Verify dark mode renders correctly (no hardcoded colors)
- [ ] Verify all styles use Tailwind utilities and cn() — no inline style={}
- [ ] Verify spacing uses Tailwind scale (no arbitrary px values)

#### P2: Data Fetching Best Practices (User Story 6)

- [ ] Verify all API calls use TanStack Query (no raw useEffect+fetch)
- [ ] Verify query keys follow choreKeys convention
- [ ] Verify no duplicate API calls between parent/child
- [ ] Verify staleTime configured on queries
- [ ] Verify all mutations have onError with user feedback
- [ ] Verify mutation success invalidates relevant queries

#### P3: Test Coverage (User Story 7)

- [ ] Verify hook tests cover happy path, error, loading, empty states
- [ ] Verify component tests cover user interactions
- [ ] Verify test patterns match codebase conventions
- [ ] Verify edge cases covered (rate limit, long strings, null data)
- [ ] Verify no snapshot tests

#### P3: Clean Code (User Story 8)

- [ ] Remove dead code, unused imports, commented-out blocks
- [ ] Remove all console.log statements
- [ ] Convert all relative imports to @/ alias
- [ ] Define repeated strings as constants
- [ ] Run ESLint — zero warnings

### 4. Running Tests

```bash
# Unit tests (all)
cd solune/frontend
npx vitest run

# Specific chores component tests
npx vitest run src/components/chores/

# Chores hook tests (if they exist)
npx vitest run src/hooks/useChores

# Lint check
npm run lint

# Type check
npm run type-check
```

### 5. Accessibility Testing Tools

```bash
# Manual testing with browser DevTools:
# - Chrome Lighthouse → Accessibility audit
# - axe DevTools browser extension
# - Chrome DevTools → Rendering → Emulate prefers-reduced-motion
# - Chrome DevTools → Rendering → Emulate vision deficiencies
```

## Key Files to Audit

| Priority | File | Lines | Description |
|----------|------|-------|-------------|
| HIGH | `src/pages/ChoresPage.tsx` | 166 | Main page — all states, hero, unsaved changes guard |
| HIGH | `src/components/chores/ChoresPanel.tsx` | 543 | Main panel — DECOMPOSE (search, sort, grid, save-all) |
| HIGH | `src/components/chores/ChoreCard.tsx` | 584 | Card — DECOMPOSE (header, actions, stats, settings) |
| HIGH | `src/components/chores/AddChoreModal.tsx` | 356 | Modal — DECOMPOSE (template selector, creation form) |
| MEDIUM | `src/components/chores/FeaturedRitualsPanel.tsx` | 204 | Featured stats — responsive layout, accessibility |
| MEDIUM | `src/components/chores/ChoreChatFlow.tsx` | 191 | Chat flow — error handling, accessibility |
| MEDIUM | `src/components/chores/ChoreInlineEditor.tsx` | 115 | Inline editor — conflict handling, dirty state |
| LOW | `src/components/chores/ChoreScheduleConfig.tsx` | 93 | Schedule config — accessibility, labels |
| LOW | `src/components/chores/ConfirmChoreModal.tsx` | 92 | Confirm dialog — focus trap, escape key |
| LOW | `src/components/chores/PipelineSelector.tsx` | 85 | Pipeline dropdown — ARIA, keyboard nav |
| REFERENCE | `src/hooks/useChores.ts` | 192 | Hook — error handlers, staleTime, query keys |

## Design Token Reference

All colors, typography, spacing, shadows, radii, and motion tokens are defined in `solune/frontend/src/index.css`. Key custom classes used on the Chores page:

- `.celestial-panel` — Card/panel background with glow
- `.celestial-fade-in` — Entry animation
- `.moonwell` — Semi-transparent panel with backdrop blur
- `.solar-chip` / `.solar-chip-*` — Badge/chip variants

Tooltip copy is centralized in `solune/frontend/src/constants/tooltip-content.ts`. Components should use `<Tooltip contentKey=...>` over inline strings.

## Output

After completing the audit, document findings in an audit summary covering:

1. All issues found (visual, accessibility, responsive, interactive, performance)
2. All changes made (with file references)
3. Any improvements deferred for future work (with justification)
