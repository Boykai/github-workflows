# Component Contracts: DRY Logging & Error Handling Modernization

**Feature**: 030-dry-error-handling | **Date**: 2026-03-08

## New Components

### ErrorAlert

**Location**: `frontend/src/components/common/ErrorAlert.tsx`
**Purpose**: Reusable error display component replacing scattered inline error markup across the application. Provides consistent styling, optional retry and dismiss actions.

```typescript
interface ErrorAlertProps {
  /** Error message to display to the user */
  message: string;
  /** Optional retry callback — renders a "Retry" button when provided */
  onRetry?: () => void;
  /** Optional dismiss callback — renders a dismiss (×) button when provided */
  onDismiss?: () => void;
  /** Additional CSS classes for the root element */
  className?: string;
}
```

**Behavior**:
- Always renders the `message` text with a warning icon (⚠️ or `AlertCircle` from lucide-react)
- When `onRetry` is provided: renders a "Retry" button aligned to the right
- When `onDismiss` is provided: renders an "×" dismiss button in the top-right corner
- When both `onRetry` and `onDismiss` are provided: both buttons render
- The `className` prop is merged with the default classes via `cn()` utility
- Accessible: uses `role="alert"` for screen reader announcement

**Styling** (matches existing destructive banners in ProjectsPage):
```tsx
<div
  role="alert"
  className={cn(
    "flex items-start gap-3 rounded-[1.1rem] border border-destructive/30 bg-destructive/10 p-4 text-destructive",
    className
  )}
>
  <span className="text-lg">⚠️</span>
  <div className="flex flex-col gap-1">
    <p>{message}</p>
  </div>
  {onRetry && (
    <button
      className="px-3 py-1.5 text-sm font-medium bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors ml-auto"
      onClick={onRetry}
    >
      Retry
    </button>
  )}
  {onDismiss && (
    <button
      className="text-destructive/60 hover:text-destructive transition-colors ml-auto"
      onClick={onDismiss}
      aria-label="Dismiss"
    >
      ✕
    </button>
  )}
</div>
```

**Replacement Targets**:

| Component | Current Error Display | ErrorAlert Replacement |
|-----------|----------------------|----------------------|
| `ProjectsPage.tsx` (refresh error) | Inline `div` with destructive styling | `<ErrorAlert message={refreshError.message} />` |
| `ProjectsPage.tsx` (projects error) | Inline `div` with ApiError details | `<ErrorAlert message={projectsError.message} />` |
| `ProjectsPage.tsx` (board error) | Inline `div` with Retry button | `<ErrorAlert message={boardError.message} onRetry={...} />` |
| `IssueRecommendationPreview.tsx` | Inline `div` with `bg-destructive/10` | `<ErrorAlert message={error} />` |
| `ChatInterface.tsx` (file errors) | Map over `fileErrors` array | `{fileErrors.map(err => <ErrorAlert key={err} message={err} />)}` |

**Note**: Rate-limit banners in `ProjectsPage.tsx` use `accent` colors (not `destructive`) and have different semantics (informational, not error). These are NOT replaced by `ErrorAlert` — they remain as custom inline displays.

---

## New Utilities

### Logger

**Location**: `frontend/src/utils/logger.ts`
**Purpose**: Centralized logging utility that wraps browser console methods with environment-aware gating. Serves as the single import for all frontend logging.

```typescript
interface Logger {
  /** Always emits, even in production — errors should never be silently suppressed */
  error: (...args: unknown[]) => void;
  /** Only emits in development mode */
  warn: (...args: unknown[]) => void;
  /** Only emits in development mode */
  info: (...args: unknown[]) => void;
}

export const logger: Logger;
```

**Behavior**:
- `logger.error(...)` → always calls `console.error(...)`
- `logger.warn(...)` → calls `console.warn(...)` only when `import.meta.env.DEV` is `true`
- `logger.info(...)` → calls `console.info(...)` only when `import.meta.env.DEV` is `true`
- No initialization required — import and use immediately
- Stateless — no configuration object, no setup function
- Tree-shakeable — Vite can eliminate `warn`/`info` implementations in production builds if dead code elimination applies

**Replacement Targets**:

| File | Current Call | Logger Replacement |
|------|-------------|-------------------|
| `ErrorBoundary.tsx` L30 | `console.error('ErrorBoundary caught:', ...)` | `logger.error('ErrorBoundary caught:', ...)` |
| `api.ts` L167 | `console.error('Auth-expired listener threw:', ...)` | `logger.error('Auth-expired listener threw:', ...)` |
| `useRealTimeSync.ts` L79 | `console.error('Failed to parse WebSocket message:', ...)` | `logger.error('Failed to parse WebSocket message:', ...)` |
| `usePipelineConfig.ts` L232 | `console.warn('Pipeline assignment failed:', ...)` | `logger.warn('Pipeline assignment failed:', ...)` |
| `AgentsPipelinePage.tsx` L62 | `console.warn('Failed to seed preset pipelines:', ...)` | `logger.warn('Failed to seed preset pipelines:', ...)` |

**Silent Catch Additions**:

| File | Catch Location | Logger Call to Add |
|------|---------------|-------------------|
| `useBoardControls.ts` L110 | JSON.parse failure | `logger.warn('Failed to parse board controls from localStorage')` |
| `useBoardControls.ts` L117 | localStorage.setItem failure | `logger.warn('Failed to save board controls to localStorage')` |
| `useSidebarState.ts` L10 | localStorage.getItem failure | `logger.warn('Failed to read sidebar state from localStorage')` |
| `useSidebarState.ts` L23 | localStorage.setItem failure | `logger.warn('Failed to save sidebar state to localStorage')` |
| `useAppTheme.ts` L39 | Settings API failure | `logger.warn('Failed to persist theme to server')` |
| `useRealTimeSync.ts` L173 | WebSocket constructor failure | `logger.info('WebSocket not available, falling back to polling')` |

---

## Modified Components

### App (Toaster Integration)

**Location**: `frontend/src/App.tsx`
**Purpose**: Application root — add Toaster provider and default mutation error handling.

**Changes**:
1. **Import**: `import { Toaster, toast } from 'sonner'`
2. **Toaster mount**: Add `<Toaster />` inside the return, after `<RouterProvider />`:
   ```tsx
   return (
     <QueryClientProvider client={queryClient}>
       <RouterProvider router={router} />
       <Toaster position="top-right" richColors />
     </QueryClientProvider>
   );
   ```
3. **QueryClient mutation default**: Add `mutations.onError` to `defaultOptions`:
   ```typescript
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

### main.tsx (Global Error Handlers)

**Location**: `frontend/src/main.tsx`
**Purpose**: Application entry point — add global unhandled error capture.

**Changes**: Add before the `createRoot` call:
```typescript
import { logger } from './utils/logger';

// Global unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
  logger.error('Unhandled promise rejection:', event.reason);
});

// Global uncaught error handler
window.onerror = (message, source, lineno, colno, error) => {
  logger.error('Uncaught error:', { message, source, lineno, colno, error });
};
```

### ErrorBoundary (Logger Integration)

**Location**: `frontend/src/components/common/ErrorBoundary.tsx`
**Purpose**: Existing error boundary — replace `console.error` with `logger.error`.

**Change**:
```typescript
// Before
componentDidCatch(error: Error, info: ErrorInfo): void {
  console.error('ErrorBoundary caught:', error, info.componentStack);
}

// After
componentDidCatch(error: Error, info: ErrorInfo): void {
  logger.error('ErrorBoundary caught:', error, info.componentStack);
}
```

---

## Query Key Impact

No changes to query keys. The `mutations.onError` default callback does not affect query key structure or caching behavior.

---

## Sonner Toaster Configuration

```tsx
<Toaster
  position="top-right"
  richColors               // Uses semantic colors (red for error, green for success)
  toastOptions={{
    className: 'text-sm',  // Match design system font size
  }}
/>
```

**Position**: `top-right` — standard location that doesn't interfere with the main content area or the sidebar.
**Rich Colors**: Enabled — provides automatic red/green/blue styling for error/success/info toasts, consistent with the destructive/success theme tokens.
**Auto-dismiss**: Default 5 seconds for all toast types.
