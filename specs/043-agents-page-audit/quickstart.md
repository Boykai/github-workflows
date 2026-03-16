# Quickstart: Agents Page Audit

**Feature Branch**: `043-agents-page-audit`
**Date**: 2026-03-16

## Prerequisites

- Node.js 20+ and npm
- Python 3.12+ and `uv` (for backend, if running locally)
- A GitHub token configured in `.env` for API access

## Setup

```bash
# Clone and checkout
git checkout 043-agents-page-audit

# Install frontend dependencies
cd solune/frontend
npm install

# Verify existing tests pass
npx vitest run
npm run lint
npm run type-check
```

## Development Workflow

### 1. Run the Frontend Dev Server

```bash
cd solune/frontend
npm run dev
```

The Agents page is available at `http://localhost:5173/agents` (or the port shown in terminal).

### 2. Run the Backend (if testing with live data)

```bash
cd solune/backend
uv run --extra dev uvicorn src.main:app --reload --port 8000
```

### 3. Audit Checklist

Work through the audit in priority order matching the spec:

#### P1: Modular Component Architecture (User Story 1)

- [ ] Verify AgentsPanel.tsx ≤250 lines (currently 565 — needs decomposition)
- [ ] Verify AddAgentModal.tsx ≤250 lines (currently 520 — needs decomposition)
- [ ] Verify AgentCard.tsx ≤250 lines (currently 286 — needs minor extraction)
- [ ] Verify AgentInlineEditor.tsx ≤250 lines (currently 272 — needs minor extraction)
- [ ] Verify AgentConfigRow.tsx ≤250 lines (currently 480 — needs decomposition)
- [ ] Verify AgentPresetSelector.tsx ≤250 lines (currently 519 — needs decomposition)
- [ ] Verify AgentTile.tsx ≤250 lines (currently 308 — needs minor extraction)
- [ ] Verify complex state extracted into hooks (8+ useState calls in AgentsPanel)
- [ ] Verify useAgentConfig.ts properly scoped (currently 349 lines, may need splitting)

#### P1: Reliable Loading, Error, and Empty States (User Story 2)

- [ ] Test loading state — CelestialLoader or skeleton visible during data fetch
- [ ] Test error state — user-friendly message with retry action
- [ ] Test rate limit error — detected via `isRateLimitApiError()` with specific guidance
- [ ] Test empty state — meaningful empty state with "Create Agent" CTA
- [ ] Test partial loading — independent sections have own loading/error states
- [ ] Test ErrorBoundary — recovery UI on unexpected rendering error

#### P2: Accessible Agent Management (User Story 3)

- [ ] Tab through all interactive elements — verify logical focus order
- [ ] Verify focus trapping in all modals/dialogs
- [ ] Verify focus return to trigger on dialog close
- [ ] Add missing ARIA attributes (see research.md R3 for gap analysis)
- [ ] Verify `.celestial-focus` on all interactive elements
- [ ] Verify status indicators use icon + text, not color alone

#### P2: Polished Text, Copy, and UX (User Story 4)

- [ ] No placeholder text (TODO, Lorem ipsum, Test)
- [ ] Verb-based action button labels
- [ ] ConfirmationDialog on all destructive actions
- [ ] Success feedback on all mutations (toast or inline)
- [ ] User-friendly error messages (no raw error codes)
- [ ] Long text truncated with Tooltip
- [ ] Timestamps formatted consistently

#### P3: Consistent Styling and Responsive Layout (User Story 5)

- [ ] Responsive at 768px, 1024px, 1440px, 1920px
- [ ] Dark mode — no hardcoded colors
- [ ] Tailwind utility classes only — no inline `style={}`
- [ ] Standard Tailwind spacing scale — no arbitrary values
- [ ] Card component usage consistent

#### P3: Test Coverage (User Story 6)

- [ ] Hook tests for useAgents, useAgentConfig, useAgentTools
- [ ] Component interaction tests for AgentsPanel, AddAgentModal, AgentCard
- [ ] Edge cases: empty, error, loading, rate limit, long strings, null data

#### P3: Performance and Code Hygiene (User Story 7)

- [ ] Zero ESLint warnings: `npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/`
- [ ] Zero TypeScript errors: `npx tsc --noEmit`
- [ ] No `any` types or `as` assertions
- [ ] No dead code, no `console.log`
- [ ] All imports use `@/` alias
- [ ] Stable keys on list renders (`key={item.id}`)
- [ ] Expensive computations memoized

## Validation Commands

```bash
cd solune/frontend

# Lint
npx eslint src/pages/AgentsPage.tsx src/components/agents/ src/components/board/

# Type check
npm run type-check

# Run all tests
npx vitest run

# Run agent-specific tests
npx vitest run --reporter=verbose src/components/agents/ src/components/board/ src/hooks/useAgent

# Accessibility audit (manual)
# 1. Open browser DevTools → Lighthouse → Accessibility
# 2. Or install axe DevTools extension
```

## Key Files Reference

| Category | Path | Notes |
|----------|------|-------|
| Page | `src/pages/AgentsPage.tsx` | Primary audit target (230 lines) |
| Catalog | `src/components/agents/` | 10 files, ~3,044 lines total |
| Board | `src/components/board/Agent*.tsx` | 7 files, ~1,981 lines total |
| Hooks | `src/hooks/useAgent*.ts` | 3 files, ~496 lines total |
| Types | `src/types/index.ts` | AgentConfig, AgentAssignment, etc. |
| API | `src/services/api.ts` | agentsApi group (lines ~892–951) |
| Tooltips | `src/constants/tooltip-content.ts` | Centralized tooltip strings |
| Design tokens | `src/index.css` | Celestial design system variables |
| Utils | `src/lib/utils.ts` | `cn()` helper for conditional classes |
