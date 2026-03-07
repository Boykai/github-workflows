# Quickstart: Audit & Update UI Components for Style Consistency

**Feature Branch**: `026-ui-style-consistency`  
**Date**: 2026-03-07

## Prerequisites

- Node.js 18+ (check with `node --version`)
- Git (on branch `026-ui-style-consistency`)
- Backend running at `localhost:8000` (for API proxy, needed for visual verification)

## Setup

```bash
# Switch to feature branch
git checkout 026-ui-style-consistency

# Install dependencies (no new deps needed)
cd frontend
npm install

# Start dev server
npm run dev
```

The app is available at `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

## Audit Workflow

### Step 1: Capture Baseline Screenshots

Before making any changes, capture screenshots of every page in both light and dark modes:

```bash
# Pages to capture (6 pages × 2 modes = 12 screenshots):
# http://localhost:5173/           (AppPage - light & dark)
# http://localhost:5173/projects   (ProjectsPage - light & dark)
# http://localhost:5173/pipeline   (AgentsPipelinePage - light & dark)
# http://localhost:5173/agents     (AgentsPage - light & dark)
# http://localhost:5173/chores     (ChoresPage - light & dark)
# http://localhost:5173/settings   (SettingsPage - light & dark)
```

Toggle dark mode via the theme toggle in the TopBar.

### Step 2: Remediate Components

Work through components in this order (highest impact first):

1. **Add centralized constants** to `frontend/src/constants.ts` (`STATUS_COLORS`, `AGENT_SOURCE_COLORS`)
2. **Fix critical non-compliant components** (ErrorBoundary, SignalConnection, McpSettings, CleanUpSummary)
3. **Adopt cn() in board components** (IssueCard, IssueDetailModal, ProjectBoard, etc.)
4. **Adopt cn() in chat components** (MessageBubble, ChatPopup, etc.)
5. **Adopt cn() in settings components** (all settings files)
6. **Adopt cn() in remaining components** (agents, chores)
7. **Review pages** for token alignment

### Step 3: Verify Each Change

After each component update:

```bash
# Type check
cd frontend && npx tsc --noEmit

# Lint
cd frontend && npx eslint src/

# Unit tests
cd frontend && npm run test

# Build
cd frontend && npm run build
```

### Step 4: Visual Regression Check

Compare each page against baseline screenshots:

1. Navigate to the page in the browser
2. Toggle between light and dark modes
3. Verify colors, spacing, shadows, borders match expectations
4. Test interactive states: hover, focus, active, disabled
5. Resize viewport to check responsive behavior

## Key Files

| File | Purpose |
|------|---------|
| `frontend/src/index.css` | Theme tokens — **audit only, no changes expected** |
| `frontend/src/constants.ts` | **MODIFY**: Add `STATUS_COLORS`, `AGENT_SOURCE_COLORS` |
| `frontend/src/lib/utils.ts` | `cn()` utility — **no changes, import in new files** |
| `frontend/src/components/ThemeProvider.tsx` | Theme switching — **no changes** |
| `frontend/src/components/ui/*.tsx` | Base UI components — **already compliant** |
| `frontend/src/components/board/*.tsx` | Board components — **remediate ~15 files** |
| `frontend/src/components/chat/*.tsx` | Chat components — **remediate ~8 files** |
| `frontend/src/components/settings/*.tsx` | Settings components — **remediate ~10 files** |
| `frontend/src/components/agents/*.tsx` | Agent components — **remediate ~4 files** |
| `frontend/src/components/chores/*.tsx` | Chore components — **remediate ~5 files** |

## Common Remediation Patterns

### Pattern A: Template Literal → cn()

```typescript
// Before
import React from 'react';

// After — add cn import
import React from 'react';
import { cn } from '@/lib/utils';

// Before
className={`flex items-center ${isActive ? 'bg-primary' : 'bg-muted'}`}

// After
className={cn('flex items-center', isActive ? 'bg-primary' : 'bg-muted')}
```

### Pattern B: Hardcoded Status Colors → Constant

```typescript
// Before
className="bg-green-500/10 text-green-600 dark:text-green-400"

// After — import from constants
import { STATUS_COLORS } from '@/constants';
className={cn(STATUS_COLORS.success.bg, STATUS_COLORS.success.text)}
```

### Pattern C: Inline Style → Tailwind

```typescript
// Before
style={{ padding: '2rem', textAlign: 'center' }}

// After
className="p-8 text-center"
```

## Verification Commands

```bash
cd frontend

# Full verification pipeline
npm run build && npx tsc --noEmit && npx eslint src/ && npm run test

# Quick type check during development
npx tsc --noEmit --watch
```
