# Quickstart: Settings Page — Dynamic Value Fetching, Caching, and UX Simplification

**Feature**: `012-settings-dynamic-ux` | **Date**: 2026-02-28

## Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm
- Git
- A GitHub account with an OAuth token (for testing Copilot model fetching)

## Setup

### 1. Clone and Install

```bash
# From the repository root
cd backend
pip install -e ".[dev]"

cd ../frontend
npm install
```

### 2. Environment Configuration

Ensure `.env` (or environment variables) includes:

```bash
# Backend
AI_PROVIDER=copilot          # or azure_openai
GITHUB_CLIENT_ID=<your-github-oauth-client-id>
GITHUB_CLIENT_SECRET=<your-github-oauth-client-secret>

# Optional: Azure OpenAI (if using azure_openai provider)
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_ENDPOINT=<endpoint>

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
```

### 3. Run the Application

```bash
# Terminal 1: Backend
cd backend
uvicorn src.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 4. Navigate to Settings

Open `http://localhost:5173/#settings` in your browser.

## Feature-Specific Development Guide

### Backend: Model Fetcher Service

The new backend service lives in `backend/src/services/model_fetcher.py`. Key concepts:

- **`ModelFetchProvider`** (protocol): Abstract interface for providers. Implement `fetch_models(token)` to add a new provider.
- **`ModelFetcherService`**: Orchestrates caching, rate-limit handling, and provider dispatch. Singleton instance.
- **Cache key format**: `{provider}:{sha256(token)[:16]}`

To add a new provider:
1. Create a class implementing `ModelFetchProvider`
2. Register it in the provider registry dict in `model_fetcher.py`
3. Add the provider value to the `AIProvider` enum in `backend/src/models/settings.py`

### Backend: New API Endpoint

The endpoint `GET /settings/models/{provider}` is added in `backend/src/api/settings.py`:
- Validates the provider parameter
- Checks authentication prerequisites
- Delegates to `ModelFetcherService` for cached/fresh results
- Returns `ModelsResponse` (see `contracts/settings-api.yaml`)

### Frontend: Dynamic Dropdown Component

The reusable `DynamicDropdown` component (`frontend/src/components/settings/DynamicDropdown.tsx`) handles all states:

- **idle**: Dropdown with placeholder text
- **loading**: Spinner + disabled dropdown + `aria-busy="true"`
- **success**: Populated options + cache freshness indicator
- **error**: Error message + retry button + fallback to cached values
- **auth_required**: Inline prerequisite message with setup link
- **rate_limited**: Warning banner + cached values (if available)

### Frontend: useModelOptions Hook

```typescript
// Usage in a settings component
const { data, isLoading, error, refetch } = useModelOptions(provider);
// data: ModelsResponse
// Automatically refetches when provider changes
// Serves stale data while revalidating (TanStack Query staleTime)
```

### Frontend: Settings Page Layout

The `SettingsPage.tsx` is reorganized:
1. **PrimarySettings** component: Provider selector, Chat Model (dynamic), Agent Model (dynamic), Signal Connection
2. **AdvancedSettings** component: Collapsible section (collapsed by default) with Display, Workflow, Notifications, Allowed Models, Project settings

## Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/ -v

# Frontend unit tests
cd frontend
npm run test

# Frontend type checking
cd frontend
npm run type-check

# Frontend e2e tests (requires running app)
cd frontend
npm run test:e2e
```

## Key Files to Modify/Create

| File | Action | Purpose |
|------|--------|---------|
| `backend/src/services/model_fetcher.py` | CREATE | Provider-abstracted model fetching + cache |
| `backend/src/api/settings.py` | MODIFY | Add `/settings/models/{provider}` endpoint |
| `backend/src/models/settings.py` | MODIFY | Add `ModelOption`, `ModelsResponse` models |
| `frontend/src/components/settings/DynamicDropdown.tsx` | CREATE | Reusable dynamic dropdown component |
| `frontend/src/components/settings/PrimarySettings.tsx` | CREATE | Primary settings group component |
| `frontend/src/components/settings/AdvancedSettings.tsx` | CREATE | Collapsible advanced settings component |
| `frontend/src/hooks/useSettings.ts` | MODIFY | Add `useModelOptions()` hook |
| `frontend/src/services/api.ts` | MODIFY | Add `settingsApi.fetchModels()` |
| `frontend/src/pages/SettingsPage.tsx` | MODIFY | Reorganize layout with primary/advanced sections |
| `frontend/src/components/settings/GlobalSettings.tsx` | MODIFY | Extract primary AI settings to `PrimarySettings` |
