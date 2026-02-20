# Quickstart: Codebase Cleanup & Refactor

**Feature**: `001-codebase-cleanup-refactor` | **Date**: 2026-02-20

## Overview

This guide provides developers with the patterns, conventions, and test skeletons needed to implement the codebase cleanup and refactor. The refactoring reorganizes existing code without changing external behavior.

## Prerequisites

```bash
# Backend setup
cd backend
pip install -e ".[dev]"

# Frontend setup
cd frontend
npm install
```

## Running Tests

```bash
# Backend tests (all)
cd backend && python -m pytest

# Backend tests (specific module)
cd backend && python -m pytest tests/unit/test_github_projects.py -v

# Frontend tests (all)
cd frontend && npm test

# Frontend tests (specific file)
cd frontend && npx vitest run src/hooks/useSettings.test.tsx
```

## Linting

```bash
# Backend
cd backend && ruff check src/ && ruff format --check src/

# Frontend
cd frontend && npm run lint && npm run type-check
```

## Pattern: Module Split (Backend)

### Converting a monolithic file to a package

1. Create the package directory and `__init__.py`:

```python
# backend/src/services/github_projects/__init__.py
"""GitHub Projects service — re-export facade.

Preserves backward compatibility: all public symbols are available
from `services.github_projects` as before.
"""

from services.github_projects._client import GitHubProjectsService

# Re-export all public methods (they are on the class, so importing the class suffices)
__all__ = ["GitHubProjectsService"]
```

2. Move related methods to sub-modules:

```python
# backend/src/services/github_projects/_client.py
"""HTTP client and GraphQL execution for GitHub API."""

import httpx

class GitHubProjectsService:
    """GitHub Projects V2 API service."""

    def __init__(self, access_token: str):
        self.client = httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_SECONDS,  # from constants
            headers={"Authorization": f"Bearer {access_token}"}
        )

    async def close(self):
        await self.client.aclose()

    async def _request_with_retry(self, method, url, **kwargs):
        # ... retry logic ...
        pass

    async def _graphql(self, query, variables=None):
        # ... GraphQL execution ...
        pass
```

3. Sub-modules extend the class (example pattern):

```python
# backend/src/services/github_projects/_issues.py
"""Issue and project item management."""

from services.github_projects._client import GitHubProjectsService

# Methods are defined on GitHubProjectsService
# The class is assembled by importing all sub-modules in __init__.py
```

### Key rules for module splits

- Original import path (`from services.github_projects import ...`) MUST continue to work
- Sub-module filenames start with `_` (private to package)
- Each sub-module has a module docstring describing its single responsibility
- No circular imports between sub-modules
- Shared state (the `httpx.AsyncClient`) lives in `_client.py`

## Pattern: Shared Utilities (Backend)

### Repository resolution

```python
# backend/src/services/shared/repo_utils.py
"""Shared repository resolution utilities."""


def resolve_repository(repo_data: dict) -> tuple[str, str]:
    """Extract owner and repo name from GitHub API repository data.

    Args:
        repo_data: Repository dict from GitHub API (webhook payload or API response).

    Returns:
        Tuple of (owner, repo_name).

    Raises:
        ValueError: If owner or repo name cannot be extracted.
    """
    owner = repo_data.get("owner", {}).get("login", "")
    name = repo_data.get("name", "")
    if not owner or not name:
        raise ValueError(f"Cannot resolve repository from data: {repo_data.get('full_name', 'unknown')}")
    return owner, name
```

## Pattern: Error Handling (Backend)

### Use domain exceptions, not HTTPException

```python
# ✅ Correct: Raise domain exception
from exceptions import NotFoundError, GitHubAPIError

async def get_project(project_id: str):
    project = await fetch_project(project_id)
    if not project:
        raise NotFoundError(f"Project {project_id} not found")
    return project

# ❌ Incorrect: Raise HTTPException directly
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="Not found")  # Don't do this
```

### Catch-all handler pattern

```python
# In main.py
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )
```

## Pattern: Named Constants (Backend)

```python
# In constants.py — add to existing file
# Polling & Timing
POLLING_INTERVAL_SECONDS = 60
HTTP_TIMEOUT_SECONDS = 30.0
SQLITE_BUSY_TIMEOUT_MS = 5000
COMPLETION_TIMEOUT_SECONDS = 120

# Collection Limits
MAX_COLLECTION_SIZE = 500
COLLECTION_TRIM_SIZE = 250

# Retry
MAX_RETRY_ATTEMPTS = 3
```

Usage:
```python
from constants import HTTP_TIMEOUT_SECONDS
client = httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS)
```

## Pattern: Frontend API Client Migration

### Before (direct fetch)

```typescript
// ❌ useWorkflow.ts — direct fetch
const response = await fetch(`/api/v1/workflow/start`, {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
});
```

### After (centralized client)

```typescript
// ✅ useWorkflow.ts — using api.ts client
import { workflowApi } from '@/services/api';

const result = await workflowApi.start(data);
```

```typescript
// In api.ts — add the missing API module
export const workflowApi = {
  start: (data: WorkflowStartRequest) =>
    request<WorkflowResponse>('/workflow/start', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  // ... other workflow operations
};
```

## Pattern: Error Boundary (Frontend)

```tsx
// frontend/src/components/common/ErrorBoundary.tsx
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={this.handleReset}>Try Again</button>
          <button onClick={() => window.location.reload()}>Reload Page</button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

## Pattern: Session State Hook (Frontend)

```typescript
// frontend/src/hooks/useSessionState.ts
import { useState, useCallback } from 'react';

export function useSessionState<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const [state, setState] = useState<T>(() => {
    try {
      const stored = sessionStorage.getItem(key);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  const setSessionState = useCallback((value: T) => {
    setState(value);
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // sessionStorage may be unavailable in some contexts
    }
  }, [key]);

  return [state, setSessionState];
}
```

## Test Skeleton: Backend Service

```python
# backend/tests/unit/test_session_store.py
"""Tests for SessionStore service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSessionStore:
    """Tests for session CRUD operations."""

    @pytest.fixture
    def mock_db(self):
        """Mock database connection."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.fetchone = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_create_session(self, mock_db):
        """Test creating a new session."""
        # Arrange
        from services.session_store import SessionStore
        store = SessionStore(mock_db)

        # Act
        session = await store.create_session(user_id="user123", access_token="token456")

        # Assert
        assert session is not None
        assert session.user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, mock_db):
        """Test getting a non-existent session returns None."""
        mock_db.fetchone.return_value = None
        from services.session_store import SessionStore
        store = SessionStore(mock_db)

        result = await store.get_session("nonexistent-id")

        assert result is None
```

## Test Skeleton: Frontend Hook

```tsx
// frontend/src/hooks/useSettings.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSettings } from './useSettings';

// Mock the API module
vi.mock('@/services/api', () => ({
  settingsApi: {
    getUserSettings: vi.fn(),
    updateUserPreferences: vi.fn(),
    getGlobalSettings: vi.fn(),
  },
}));

import { settingsApi } from '@/services/api';

const mockSettingsApi = settingsApi as unknown as {
  getUserSettings: ReturnType<typeof vi.fn>;
  updateUserPreferences: ReturnType<typeof vi.fn>;
  getGlobalSettings: ReturnType<typeof vi.fn>;
};

describe('useSettings', () => {
  let queryClient: QueryClient;

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  it('should load user settings on mount', async () => {
    // Arrange
    const mockSettings = { theme: 'dark', notifications: true };
    mockSettingsApi.getUserSettings.mockResolvedValue(mockSettings);

    // Act
    const { result } = renderHook(() => useSettings(), { wrapper });

    // Assert
    await waitFor(() => {
      expect(result.current.settings).toEqual(mockSettings);
    });
    expect(mockSettingsApi.getUserSettings).toHaveBeenCalledOnce();
  });

  it('should handle settings load error', async () => {
    // Arrange
    mockSettingsApi.getUserSettings.mockRejectedValue(new Error('Network error'));

    // Act
    const { result } = renderHook(() => useSettings(), { wrapper });

    // Assert
    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });
  });
});
```

## Verification Checklist

After implementation, verify:

- [ ] `cd backend && python -m pytest` — all existing tests pass
- [ ] `cd frontend && npm test` — all existing tests pass
- [ ] `cd backend && ruff check src/` — no lint errors
- [ ] `cd frontend && npm run lint` — no lint errors
- [ ] `cd frontend && npm run type-check` — no type errors
- [ ] No backend source file exceeds ~500 lines (run `wc -l backend/src/services/**/*.py`)
- [ ] `from services.github_projects import GitHubProjectsService` works (facade intact)
- [ ] `from services.copilot_polling import poll_for_copilot_completion` works (facade intact)
- [ ] All error responses match `{"error": "...", "status_code": N}` structure
- [ ] No direct `fetch()` calls in frontend hooks (only in `services/api.ts`)
