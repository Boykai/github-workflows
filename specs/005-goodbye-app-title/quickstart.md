# Quickstart: Update App Title to "Goodbye"

**Feature**: 005-goodbye-app-title | **Branch**: `005-goodbye-app-title`

---

## Prerequisites

- Node.js ≥ 18 (for frontend development)
- Docker & Docker Compose (optional, for full-stack development)

## Setup

### 1. Switch to feature branch

```bash
cd /home/runner/work/github-workflows/github-workflows
git checkout 005-goodbye-app-title
```

### 2. Start the application

```bash
# Option A: Docker (full stack)
docker compose up --build -d

# Option B: Frontend only (faster iteration)
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend (Docker): http://localhost:8000

## Verification

### Manual Verification

1. Open http://localhost:5173 in a browser
2. **Browser tab**: Verify the tab title displays "Goodbye"
3. **Login page**: Verify the `<h1>` heading reads "Goodbye" (when not authenticated)
4. **App header**: Verify the `<h1>` heading reads "Goodbye" (when authenticated)

### Automated Verification

```bash
cd frontend

# Run unit tests
npm run test

# Run E2E tests (requires the app to be running)
npm run test:e2e

# Type check
npm run type-check

# Lint
npm run lint
```

## Files Changed

| File | What Changed |
|------|-------------|
| `frontend/index.html` | `<title>` tag: "Agent Projects" → "Goodbye" |
| `frontend/src/App.tsx` | Two `<h1>` elements: "Agent Projects" → "Goodbye" |
| `frontend/e2e/auth.spec.ts` | Title/heading assertions updated to "Goodbye" |
| `frontend/e2e/ui.spec.ts` | Heading assertions updated to "Goodbye" |
| `frontend/e2e/integration.spec.ts` | Heading assertion updated to "Goodbye" |

## Troubleshooting

- **E2E tests fail with old title**: Ensure all instances of "Agent Projects" in E2E test assertions have been replaced with "Goodbye"
- **Browser shows cached title**: Hard-refresh (`Ctrl+Shift+R`) to clear the browser cache
