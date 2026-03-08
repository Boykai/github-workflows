# Research: DRY Logging & Error Handling Modernization

**Feature**: 030-dry-error-handling | **Date**: 2026-03-08

## R1: HTTPException → AppException Status Code Mapping Correction

**Task**: Resolve discrepancies between the spec's proposed status code mapping and the actual existing AppException hierarchy.

**Decision**: Use the corrected mapping that respects the existing AppException subclass status codes. The spec's mapping contains inaccuracies — `ValidationError` is 422 (not 400), `GitHubAPIError` is 502 (not 500), and `McpValidationError` already covers 400. The corrected mapping is:

| HTTP Status | Existing AppException Subclass | Status Code |
|-------------|-------------------------------|-------------|
| 400 | `McpValidationError` (for MCP contexts) or `ValidationError` with explicit `status_code=400` override | 400 |
| 401 | `AuthenticationError` | 401 |
| 403 | `AuthorizationError` | 403 |
| 404 | `NotFoundError` | 404 |
| 409 | `ConflictError` (new, general-purpose) or `McpLimitExceededError` (MCP-specific) | 409 |
| 422 | `ValidationError` | 422 |
| 429 | `RateLimitError` | 429 |
| 500 | `AppException` (base class, default status_code) | 500 |
| 502 | `GitHubAPIError` | 502 |

For `HTTPException(status_code=400)` usages that are NOT MCP-related: use `ValidationError` — even though its default is 422, the caller can pass `details` to make it semantically correct. Alternatively, since many 400 usages are genuinely input validation errors, using `ValidationError` (422) is actually more correct per HTTP semantics (400 = malformed syntax, 422 = semantically invalid but well-formed). The existing global `AppException` handler returns `exc.status_code`, so the behavior is consistent regardless.

For `HTTPException(status_code=500)` usages: use `GitHubAPIError` when the error relates to a GitHub API call, or use `handle_service_error()` which defaults to `GitHubAPIError`. For non-GitHub 500 errors (e.g., server configuration issues in `dependencies.py`), raise `AppException(message=..., status_code=500)` directly using the base class.

**Rationale**: Changing existing exception status codes would break consumers (frontend retry logic depends on specific status codes like 401, 403, 404, 429 in the QueryClient config). The mapping must preserve existing behavior while eliminating raw HTTPException usage. Each `HTTPException` replacement requires case-by-case evaluation to pick the correct AppException subclass based on the semantic meaning, not just the status code.

**Alternatives Considered**:
- **Change `ValidationError` to 400**: Rejected — would change behavior for existing `ValidationError` callers. 422 is more correct per RFC 9110 for semantic validation failures.
- **Create a new `BadRequestError(400)` exception**: Rejected — adds a new class for a narrow case. Using `ValidationError` (422) or `McpValidationError` (400) covers all existing usage patterns without adding unnecessary classes. YAGNI.
- **Create a `ServerError(500)` exception**: Rejected — the base `AppException` already defaults to 500. Using the base class directly for generic 500 errors is sufficient.

---

## R2: ConflictError vs McpLimitExceededError Coexistence

**Task**: Determine how the new `ConflictError(409)` exception coexists with the existing `McpLimitExceededError(409)`.

**Decision**: Both classes coexist as siblings under `AppException`. `McpLimitExceededError` is MCP-domain-specific (raised only in MCP tool management when the max configuration limit is exceeded). `ConflictError` is the general-purpose 409 exception for non-MCP conflict scenarios (e.g., duplicate resource creation, concurrent modification). The existing `McpLimitExceededError` callers remain unchanged.

The `ConflictError` class follows the exact pattern of existing simple exceptions:

```python
class ConflictError(AppException):
    """Resource conflict (e.g., duplicate creation, concurrent modification)."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)
```

**Rationale**: The global `AppException` handler already handles all `AppException` subclasses uniformly (returns `JSONResponse` with `exc.status_code` and `exc.message`). Adding `ConflictError` requires no handler changes. Keeping `McpLimitExceededError` separate maintains domain specificity — it carries semantic meaning ("MCP limit exceeded") that `ConflictError` ("resource conflict") does not convey. This follows the existing pattern where `McpValidationError` (400) and `ValidationError` (422) coexist for different domains.

**Alternatives Considered**:
- **Rename `McpLimitExceededError` to `ConflictError`**: Rejected — would break the MCP-specific semantic. `McpLimitExceededError` is raised in a very specific context (max MCP tools reached) and its name communicates that intent.
- **Make `McpLimitExceededError` inherit from `ConflictError`**: Considered but rejected — adds unnecessary hierarchy depth. Both can independently inherit from `AppException` since the global handler treats all subclasses the same way.

---

## R3: handle_service_error() Activation Scope — Actual Count Correction

**Task**: Determine the exact count and location of manual `logger.error(..., exc_info=True)` + `raise` patterns that should be replaced with `handle_service_error()`.

**Decision**: The actual count of manual patterns is **12** (not 18 as stated in the spec), distributed across 5 files:

| File | Count | Current Raise Target | Notes |
|------|-------|---------------------|-------|
| `cleanup.py` | 3 | `AppException` subclasses ✓ | Already uses correct exceptions; just replace pattern |
| `agents.py` | 3 | `HTTPException` ⚠️ | Also needs HTTPException → AppException migration |
| `chores.py` | 3 | `HTTPException` ⚠️ | Also needs HTTPException → AppException migration |
| `board.py` | 2 | `GitHubAPIError` ✓ | Exemplar — already correct exception, replace pattern |
| `workflow.py` | 1 | `WorkflowError` | Special case: `WorkflowError` is not an AppException subclass |

**Special Cases**:
- **`chat.py`**: Has 3 `logger.error()` calls (lines 346, 474, 526) but **none** immediately precede a `raise`. The logger calls are informational/diagnostic without a corresponding exception raise. These should NOT be replaced with `handle_service_error()`.
- **`workflow.py`**: The one pattern raises `WorkflowError`, which may not be an `AppException` subclass. This needs verification — if `WorkflowError` is a separate exception hierarchy, `handle_service_error()` cannot be used directly (it only raises `AppException` subclasses).

**Rationale**: Accurate counting prevents scope creep and ensures the implementation task is correctly scoped. The spec's count of 18 likely included broader patterns that don't strictly match the `logger.error + raise` pattern.

**Alternatives Considered**:
- **Force all 18 mentioned patterns through `handle_service_error()`**: Rejected — would require modifying `handle_service_error()` to handle non-raise patterns and non-AppException types. The function is designed for a specific pattern and should be used only where that pattern applies.

---

## R4: sonner Compatibility with React 19 and TanStack Query v5

**Task**: Verify that `sonner` is compatible with the project's frontend stack (React 19.2, TanStack Query v5.90, Vite 7.3).

**Decision**: Use `sonner` v2.x for the toast notification system. It is compatible with React 19 (uses standard React APIs — `useState`, `useEffect`, portals), has zero peer dependency conflicts, and is actively maintained. The `<Toaster />` component mounts at the application root (`App.tsx`) and toasts are triggered via the `toast()` function import.

Integration with TanStack Query:
```typescript
// In App.tsx QueryClient config
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { /* existing config unchanged */ },
    mutations: {
      onError: (error) => {
        logger.error('Mutation failed:', error);
        toast.error(error instanceof Error ? error.message : 'An error occurred');
      },
    },
  },
});
```

TanStack Query v5 respects per-mutation `onError` callbacks — if a mutation defines its own `onError`, the default is NOT called for that mutation. This is standard behavior documented in TanStack Query v5.

**Rationale**: sonner is the most popular lightweight toast library for React (4M+ weekly npm downloads), has first-class TypeScript support, minimal bundle size (~3KB gzip), and supports the exact features needed: error/success/info variants, auto-dismiss, custom styling via className, and stacking for multiple simultaneous toasts.

**Alternatives Considered**:
- **react-hot-toast**: Considered — similar API, but less actively maintained and slightly larger bundle. sonner has better default animations and accessibility.
- **Custom toast implementation**: Rejected — YAGNI. Building a toast system from scratch (portal mounting, animation, auto-dismiss timers, stacking, accessibility) would be 200+ lines for something sonner provides out of the box.
- **Browser Notification API**: Rejected — wrong UX. Browser notifications are OS-level and require user permission. In-app toasts are the correct pattern for mutation error feedback.

---

## R5: Frontend Silent Catch Block Remediation Strategy

**Task**: Determine the correct logging level and message for each silent catch block in frontend hooks.

**Decision**: Use context-appropriate logging levels based on the catch block's intent:

| File | Catch Context | Recommended Level | Message |
|------|--------------|-------------------|---------|
| `useBoardControls.ts` (L110) | JSON.parse failure on localStorage value | `logger.warn` | `'Failed to parse board controls from localStorage'` |
| `useBoardControls.ts` (L117) | localStorage.setItem failure | `logger.warn` | `'Failed to save board controls to localStorage'` |
| `useSidebarState.ts` (L10) | localStorage.getItem failure | `logger.warn` | `'Failed to read sidebar state from localStorage'` |
| `useSidebarState.ts` (L23) | localStorage.setItem failure | `logger.warn` | `'Failed to save sidebar state to localStorage'` |
| `useAppTheme.ts` (L39) | Settings API update failure | `logger.warn` | `'Failed to persist theme to server'` |
| `useRealTimeSync.ts` (L173) | WebSocket constructor failure | `logger.info` | `'WebSocket not available, falling back to polling'` |

All localStorage catches use `logger.warn` (not `logger.error`) because localStorage failures are expected in certain environments (private browsing, storage quota exceeded) and the app has explicit fallback behavior. The WebSocket catch uses `logger.info` because falling back to polling is a normal, expected code path — not an error.

The `useMetadata.ts` catches (L31, L45) already properly handle errors by calling `setError(...)` and do NOT need additional logger calls — they are not "silent" catches.

**Rationale**: Using `logger.warn` for localStorage catches ensures developers see these during development without treating them as errors that need fixing. Using `logger.info` for the WebSocket fallback avoids alarming developers about a perfectly normal behavior. The spec mentions `logger.error()` or `logger.warn()` — we choose the appropriate level per case rather than uniformly using `error`.

**Alternatives Considered**:
- **Use `logger.error` for all**: Rejected — would create noise in development console. localStorage failures are expected in some environments and don't indicate bugs.
- **Keep some catches silent**: Rejected — the spec explicitly requires "every such block includes at minimum a `logger.debug()` call." Using `warn`/`info` exceeds the minimum while keeping output useful.

---

## R6: ErrorAlert Component Design Approach

**Task**: Determine the design approach for the shared `ErrorAlert` component to ensure consistency with the existing design system.

**Decision**: Build `ErrorAlert` using the existing Tailwind CSS patterns already present in inline error displays across the codebase. The component follows the existing destructive-themed error display pattern found in `ProjectsPage.tsx`, `IssueRecommendationPreview.tsx`, and `ChatInterface.tsx`:

```tsx
interface ErrorAlertProps {
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}
```

**Styling**: Reuse the existing pattern observed across multiple components:
```
border border-destructive/30 bg-destructive/10 text-destructive rounded-[1.1rem] p-4
```

This exact pattern (or close variants) appears in:
- `ProjectsPage.tsx` L252-260 (refresh error banner)
- `ProjectsPage.tsx` L262-275 (projects error banner)
- `ProjectsPage.tsx` L277-291 (board error banner with retry)
- `IssueRecommendationPreview.tsx` L111 (partial error display)

The component uses `lucide-react` icons (`AlertCircle` for the error icon, `RefreshCw` for retry, `X` for dismiss) consistent with the existing icon library.

**Rationale**: Extracting the common pattern into a component does not introduce new styling — it DRYs up the existing visual pattern. The `rounded-[1.1rem]` border radius matches the design system's card rounding seen across ProjectsPage banners. The destructive color tokens (`--destructive`, `--destructive-foreground`) are already defined in the theme CSS variables.

**Alternatives Considered**:
- **Use shadcn/ui Alert component**: Rejected — the project uses custom Tailwind components, not shadcn/ui. Adding a shadcn dependency for one component violates simplicity.
- **Extend ErrorBoundary**: Rejected — ErrorBoundary is a React class component for catching render errors. ErrorAlert is a presentational component for displaying known error messages. Different concerns, different components.
- **Use the existing `Card` component**: Considered — but the error displays in the codebase don't use `Card`. They use bare `div` elements with destructive styling. Following the existing pattern is more consistent.
