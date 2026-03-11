# Quickstart: Audit & Polish the Projects Page

**Feature Branch**: `033-projects-page-audit`
**Date**: 2026-03-10

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and `uv` (for backend, if running locally)
- A GitHub token configured in `.env` for API access

## Setup

```bash
# Clone and checkout
git checkout 033-projects-page-audit

# Install frontend dependencies
cd frontend
npm install

# Verify existing tests pass
npm run test
npm run lint
npm run type-check
```

## Development Workflow

### 1. Run the Frontend Dev Server

```bash
cd frontend
npm run dev
```

The Projects page is available at `http://localhost:5173/projects` (or the port shown in terminal).

### 2. Run the Backend (if testing with live data)

```bash
cd backend
uv run --extra dev uvicorn src.main:app --reload --port 8000
```

### 3. Audit Checklist

Work through the audit in priority order matching the spec:

#### P1: Visual Consistency (User Story 1)

- [ ] Compare typography (font family, sizes, weights) against other pages
- [ ] Verify spacing follows Tailwind's standard scale
- [ ] Check all colors reference design tokens (no hardcoded hex/rgb/hsl)
- [ ] Verify icons are from Lucide React and consistently sized
- [ ] Test light mode and dark mode switching

#### P1: Bug-Free Page States (User Story 2)

- [ ] Test loading state (CelestialLoader renders correctly)
- [ ] Test no-project-selected state (ProjectSelectionEmptyState)
- [ ] Test empty board state (no items message)
- [ ] Test error state (error banner with retry)
- [ ] Test rate limit state (countdown banner)
- [ ] Test populated board (no layout overflow/clipping)

#### P2: Accessibility (User Story 3)

- [ ] Tab through all interactive elements — verify focus order and indicators
- [ ] Test Escape key on all dropdowns and modals
- [ ] Verify ARIA attributes on custom controls
- [ ] Run contrast checker on muted text elements
- [ ] Test IssueDetailModal focus trap

#### P2: Responsive Layout (User Story 4)

- [ ] Test at 1280px+ (desktop)
- [ ] Test at 768px–1279px (tablet)
- [ ] Test at below 768px (mobile)
- [ ] Verify touch targets are 44×44px minimum on mobile
- [ ] Test browser resize transitions

#### P2: Interactive Elements (User Story 5)

- [ ] Test project selector (open, select, close, outside click)
- [ ] Test pipeline selector (open, select, close, Escape)
- [ ] Test blocking toggle (on/off/override states)
- [ ] Test toolbar filters, sorts, and groups
- [ ] Test board card click → modal open → modal close
- [ ] Test pipeline launch flow
- [ ] Test refresh button

#### P3: Performance & Code Quality (User Story 6)

- [ ] Review component boundaries for single responsibility
- [ ] Profile for unnecessary re-renders
- [ ] Verify no duplicate API requests
- [ ] Check data-fetching patterns and caching

### 4. Running Tests

```bash
# Unit tests (all)
cd frontend
npm run test

# Specific board component tests
npx vitest run src/components/board/

# Lint check
npm run lint

# Type check
npm run type-check

# E2E tests (requires running app)
npm run test:e2e
```

### 5. Accessibility Testing Tools

```bash
# Run accessibility tests (if configured)
npm run test:a11y

# Manual testing with browser DevTools:
# - Chrome Lighthouse → Accessibility audit
# - axe DevTools browser extension
# - Chrome DevTools → Rendering → Emulate prefers-reduced-motion
# - Chrome DevTools → Rendering → Emulate vision deficiencies
```

## Key Files to Audit

| Priority | File | Lines | Description |
|----------|------|-------|-------------|
| HIGH | `src/pages/ProjectsPage.tsx` | ~733 | Main page — all states, banners, inline components |
| HIGH | `src/components/board/IssueCard.tsx` | ~306 | Most rendered component — visual consistency critical |
| HIGH | `src/components/board/BoardColumn.tsx` | ~115 | Column layout and header |
| HIGH | `src/components/board/IssueDetailModal.tsx` | ~310 | Modal — focus trap, accessibility, responsive |
| MEDIUM | `src/components/board/BoardToolbar.tsx` | ~326 | Controls — accessibility, state feedback |
| MEDIUM | `src/components/board/ProjectIssueLaunchPanel.tsx` | ~491 | Launch panel — form accessibility |
| MEDIUM | `src/components/board/BlockingIssuePill.tsx` | ~152 | Pill — action accessibility |
| MEDIUM | `src/components/board/BlockingChainPanel.tsx` | ~147 | Panel — collapsible accessibility |
| MEDIUM | `src/components/board/ProjectBoard.tsx` | ~47 | Grid container — responsive layout |
| LOW | `src/components/board/RefreshButton.tsx` | ~35 | Simple button — verify focus state |
| LOW | `src/components/board/colorUtils.ts` | ~44 | Color mapping — verify token usage |

## Design Token Reference

All colors, typography, spacing, shadows, radii, and motion tokens are defined in `frontend/src/index.css`. Key custom classes used on the Projects page:

- `.celestial-panel` — Card/panel background with glow
- `.celestial-fade-in` — Entry animation
- `.moonwell` — Semi-transparent panel with backdrop blur
- `.solar-chip` / `.solar-chip-*` — Badge/chip variants
- `.project-pipeline-select` / `.project-pipeline-option` — Pipeline dropdown styling
- `.project-board-column` / `.project-board-card` — Board layout

## Output

After completing the audit, document findings in an audit summary covering:

1. All issues found (visual, accessibility, responsive, interactive, performance)
2. All changes made (with file references)
3. Any improvements deferred for future work (with justification)
