# Contract: Module Decomposition

**Phase**: 3 — Break Apart God Files
**Applies to**: `backend/src/services/github_projects/`, `frontend/src/services/`, `frontend/src/hooks/`

## Backend: GitHub Projects Service Decomposition

### Module Boundaries

```text
backend/src/services/github_projects/
├── __init__.py          # Public API exports, backward compatibility
├── service.py           # Orchestration facade, shared infrastructure
│                        # (retry logic, ETag cache, throttle, httpx client)
│                        # Target: ≤500 LOC
├── issues.py            # Issue CRUD, comments, state management
│                        # Target: ≤500 LOC
├── pull_requests.py     # PR creation, merge, review, completion detection
│                        # Target: ≤500 LOC
├── copilot.py           # Agent assignment, unassignment, review request
│                        # Target: ≤500 LOC
├── board.py             # Board data fetching, reconciliation
│                        # Target: ≤500 LOC
└── graphql.py           # GraphQL queries (existing, unchanged)
```

### Import Contract

```python
# Submodules import shared infrastructure from service.py
from src.services.github_projects.service import (
    GitHubProjectsService,
    get_authenticated_client,
    retry_with_backoff,
    etag_cache,
)

# External code continues to import from __init__.py (backward compatible)
from src.services.github_projects import github_projects_service
```

### Backward Compatibility

The `__init__.py` must re-export all public symbols that external code currently imports. The `github_projects_service` singleton (or its DI replacement) must remain accessible from the same import path.

## Frontend: API Service Decomposition

### Frontend Module Boundaries

```text
frontend/src/services/api/
├── index.ts             # Re-exports all public symbols
│                        # import { fetchProjects, sendMessage } from '@/services/api'
├── client.ts            # request<T>(), ApiError class, auth event listener
│                        # AbortSignal support (Phase 6)
│                        # Target: ≤200 LOC
├── projects.ts          # Project CRUD endpoints
│                        # Target: ≤200 LOC
├── chat.ts              # Chat message endpoints
│                        # Target: ≤200 LOC
├── agents.ts            # Agent CRUD endpoints
│                        # Target: ≤200 LOC
├── tools.ts             # MCP tool endpoints
│                        # Target: ≤200 LOC
└── board.ts             # Board data endpoints
│                        # Target: ≤200 LOC
```

### Frontend Import Contract

```typescript
// BEFORE:
import { fetchProjects, sendChatMessage } from '@/services/api';

// AFTER (same import path works via index.ts re-exports):
import { fetchProjects, sendChatMessage } from '@/services/api';

// NEW: Direct module imports also available
import { fetchProjects } from '@/services/api/projects';
import { sendChatMessage } from '@/services/api/chat';
```

### client.ts Contract

```typescript
// Core request function with AbortSignal support
export async function request<T>(
  endpoint: string,
  options?: RequestInit & { signal?: AbortSignal },
): Promise<T>;

// Error class
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown,
  );
}

// Auth event listener
export function onAuthError(callback: () => void): () => void;
```

## Frontend: Hook Decomposition

### usePipelineConfig Split

```text
frontend/src/hooks/
├── usePipelineConfig.ts      # Composition hook (imports sub-hooks)
│                              # Target: ≤100 LOC (orchestration only)
├── usePipelineState.ts        # Pipeline state management, selection
│                              # Target: ≤200 LOC
├── usePipelineMutations.ts    # Create, update, delete operations
│                              # Target: ≤200 LOC
└── usePipelineValidation.ts   # Stage validation, conflict detection
│                              # Target: ≤200 LOC
```

### Hook Composition Contract

```typescript
// usePipelineConfig.ts becomes a composition hook
export function usePipelineConfig() {
  const state = usePipelineState();
  const mutations = usePipelineMutations(state);
  const validation = usePipelineValidation(state);

  return {
    ...state,
    ...mutations,
    ...validation,
  };
}
```

### Hook Backward Compatibility

The original `usePipelineConfig` hook must maintain its existing return type. Consumers should not need to change their imports or destructuring patterns.

## File Size Constraints

| Category | Maximum LOC | Justification |
|----------|-------------|--------------|
| Backend service files | 500 | Constitution: files under 500 LOC |
| Frontend service modules | 400 | Spec constraint |
| Frontend hooks | 400 | Spec constraint |
| Frontend components | No hard limit | But single responsibility applies |

## Compliance Criteria

- [ ] `github_projects/service.py` reduced from 5,220 to ≤500 LOC
- [ ] All extracted backend modules are ≤500 LOC
- [ ] `services/api.ts` replaced by `services/api/` directory with re-export index
- [ ] All frontend API modules are ≤400 LOC
- [ ] `usePipelineConfig.ts` reduced to ≤100 LOC composition hook
- [ ] All sub-hooks are ≤200 LOC
- [ ] All existing imports continue to work (backward compatibility)
- [ ] All existing tests continue to pass
