# Quickstart: Add Teal Background Color to App

**Feature**: 007-teal-background | **Branch**: `007-teal-background`

---

## Prerequisites

- Node.js ≥ 18 (for frontend development)
- Docker & Docker Compose installed (optional, for full-stack dev)
- Git

## Setup

### 1. Switch to feature branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git checkout 007-teal-background
```

### 2. Install dependencies (if not already installed)

```bash
cd frontend
npm install
cd ..
```

### 3. Start the application

```bash
# Option A: Docker Compose (full stack)
docker compose up --build -d

# Option B: Frontend only (for CSS changes)
cd frontend
npm run dev
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

## Implementation

### Single file to modify

```
frontend/src/index.css
```

### Changes required

1. **Add `--color-bg-app: #0D9488;`** to the `:root` block (after `--color-bg-secondary`)
2. **Add `--color-bg-app: #0F766E;`** to the `html.dark-mode-active` block
3. **Change `body` background** from `var(--color-bg-secondary)` to `var(--color-bg-app)`

### Verification

1. Open http://localhost:5173 — the login screen should show a teal (#0D9488) background
2. Log in — the main app should have teal visible behind/around the layout
3. Click the theme toggle (🌙/☀️) — background should switch to darker teal (#0F766E) in dark mode
4. Navigate between Chat and Project Board views — teal should persist with no white flash
5. Check that all cards, modals, sidebar, and header remain on their own white/dark backgrounds

### Contrast Verification

Use browser DevTools or an online contrast checker to verify:
- White text (#FFFFFF) on #0D9488: ratio ≥ 4.5:1 ✅
- White text (#FFFFFF) on #0F766E: ratio ≥ 4.5:1 ✅

## Testing

```bash
# Frontend type check
cd frontend && npm run type-check

# Frontend lint
cd frontend && npm run lint

# Frontend unit tests (existing — should all pass, no changes expected)
cd frontend && npm run test

# E2E tests (if Playwright is configured)
cd frontend && npx playwright test
```

## Rollback

To revert the teal background:
1. Remove `--color-bg-app` from both `:root` and `html.dark-mode-active`
2. Change `body` background back to `var(--color-bg-secondary)`
