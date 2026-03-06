# Quickstart: Solune UI Redesign

**Feature Branch**: `025-solune-ui-redesign`  
**Date**: 2026-03-06

## Prerequisites

- Node.js 18+ (check with `node --version`)
- Git (on branch `025-solune-ui-redesign`)
- Backend running at `localhost:8000` (for API proxy)

## Setup

```bash
# Switch to feature branch
git checkout 025-solune-ui-redesign

# Install dependencies (adds react-router-dom)
cd frontend
npm install

# Start dev server
npm run dev
```

The app is available at `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

## First Change: Verify Router Works

After `react-router-dom` is added in Phase 1, the app should:

1. Load at `http://localhost:5173/` — renders the App (home) page
2. Navigate to `http://localhost:5173/projects` — renders the Projects page
3. Browser back/forward works without full reload
4. Direct URL access (paste `/settings` in address bar) works

## Project Structure (New Files)

```text
frontend/src/
├── layout/
│   ├── AppLayout.tsx          # Shell: Sidebar + TopBar + <Outlet /> + ChatPopup
│   ├── Sidebar.tsx            # Left nav with collapsible state
│   ├── TopBar.tsx             # Breadcrumb, notifications, theme toggle, avatar
│   ├── Breadcrumb.tsx         # Route-derived breadcrumbs
│   ├── ProjectSelector.tsx    # Project switcher modal/dropdown
│   └── NotificationBell.tsx   # Notification dropdown
├── pages/
│   ├── AppPage.tsx            # Home / welcome page
│   ├── ProjectsPage.tsx       # Board view (enhanced from ProjectBoardPage.tsx)
│   ├── AgentsPipelinePage.tsx  # Pipeline visualization
│   ├── AgentsPage.tsx         # Agent catalog + assignment map
│   ├── ChoresPage.tsx         # Chore catalog + cleanup
│   ├── SettingsPage.tsx       # Existing (restyled)
│   ├── LoginPage.tsx          # Auth gate page
│   └── NotFoundPage.tsx       # 404 catch-all
├── hooks/
│   ├── useSidebarState.ts     # Sidebar collapse persistence
│   ├── useNotifications.ts    # Aggregate agent + chore notifications
│   └── useRecentParentIssues.ts # Derive recent issues from board data
├── constants.ts               # NAV_ROUTES, PRIORITY_COLORS added
└── types/                     # NavRoute, SidebarState, Notification types added
```

## Key Files to Modify

| File | Change |
|------|--------|
| `frontend/package.json` | Add `react-router-dom` dependency |
| `frontend/index.html` | Replace title "Agent Projects" → "Solune", replace Rye font with Plus Jakarta Sans |
| `frontend/src/index.css` | Replace all HSL theme tokens (warm → purple/violet), update font-display, shadows, radius |
| `frontend/src/App.tsx` | Replace hash routing with `BrowserRouter` + `Routes` + `Route` configuration |
| `frontend/src/components/board/IssueCard.tsx` | Add priority badge colors, description snippet, label pills |
| `frontend/src/components/board/BoardColumn.tsx` | Add "+" button (scaffolding) |
| `frontend/src/components/board/ProjectBoard.tsx` | Add "Add new column" button (scaffolding) |
| `frontend/src/components/CowboyAvatar.tsx` | DELETE |

## Running Tests

```bash
cd frontend

# Unit tests
npm run test

# E2E tests (requires app + backend running)
npx playwright test
```

## Design Reference

- Primary color: Purple/violet (`262 80% 55%` HSL)
- Font display: Plus Jakarta Sans (500/600/700)
- Font body: Inter (already installed)
- Border radius: `0.5rem`
- Shadows: Neutral cool (`rgba(0,0,0,...)` base, no warm tones)
- Priority: P0=red, P1=orange, P2=blue, P3=green
