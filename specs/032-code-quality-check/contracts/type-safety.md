# Contract: Type Safety Standards

**Phase**: 4 — Type Safety & Strictness
**Applies to**: `backend/src/services/`, `backend/src/api/`, `frontend/src/`

## Backend: Return Type Annotations

### Standard Pattern

```python
# BEFORE (non-compliant — missing return type)
async def get_board_data(access_token, project_id):
    ...

# AFTER (compliant — explicit return type)
async def get_board_data(access_token: str, project_id: str) -> BoardData:
    ...
```

### TypedDict for Structured Returns

```python
# BEFORE (non-compliant — generic dict)
async def get_issue_summary(issue_id: str) -> dict:
    return {"title": title, "state": state, "assignees": assignees}

# AFTER (compliant — TypedDict)
from typing import TypedDict

class IssueSummary(TypedDict):
    title: str
    state: str
    assignees: list[str]

async def get_issue_summary(issue_id: str) -> IssueSummary:
    return {"title": title, "state": state, "assignees": assignees}
```

### Scope

All public functions in:

- `backend/src/services/**/*.py`
- `backend/src/api/**/*.py`
- `backend/src/utils.py`
- `backend/src/dependencies.py`

Private functions (prefixed with `_`) are encouraged but not required.

## Frontend: Strict TypeScript Configuration

### tsconfig.json Changes

```jsonc
{
  "compilerOptions": {
    // BEFORE
    "noUnusedLocals": false,
    "noUnusedParameters": false,

    // AFTER
    "noUnusedLocals": true,
    "noUnusedParameters": true
  }
}
```

### Handling Unused Parameters

```typescript
// BEFORE (non-compliant with strict checks)
function handleEvent(event: MouseEvent, index: number) {
  console.log(event.target);
  // index is unused
}

// AFTER (compliant — prefix unused params with _)
function handleEvent(event: MouseEvent, _index: number) {
  console.log(event.target);
}
```

### Handling Unused Locals

```typescript
// BEFORE (non-compliant)
const unusedHelper = () => {};
const result = compute();

// AFTER (compliant — remove unused, or prefix if needed for type inference)
const result = compute();
```

## Frontend: Unsafe Cast Elimination

### Replacement Pattern

```typescript
// BEFORE (non-compliant — unsafe cast)
const data = response as unknown as Record<string, unknown>;

// AFTER (compliant — discriminated union)
interface ChatResponse {
  type: 'message';
  content: string;
  timestamp: number;
}

interface ErrorResponse {
  type: 'error';
  message: string;
  code: number;
}

type ApiResponse = ChatResponse | ErrorResponse;

function isChatResponse(data: unknown): data is ChatResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'type' in data &&
    (data as { type: unknown }).type === 'message'
  );
}
```

### Type Guard Contract

All dynamic API response parsing must use type guards or validation:

```typescript
// Option 1: Type guard function
function isProjectData(data: unknown): data is ProjectData { ... }

// Option 2: Runtime validation (if zod is adopted)
const ProjectDataSchema = z.object({ ... });
const parsed = ProjectDataSchema.parse(data);
```

## Compliance Criteria

- [ ] 100% of public functions in backend services/api have explicit return type annotations
- [ ] `dict` returns replaced with `TypedDict` for structured data
- [ ] `tsconfig.json` has `noUnusedLocals: true` and `noUnusedParameters: true`
- [ ] Zero TypeScript compilation errors with strict unused checks
- [ ] Zero `as unknown as Record<string, unknown>` casts in production code
- [ ] Type guards defined for all dynamic API response parsing
