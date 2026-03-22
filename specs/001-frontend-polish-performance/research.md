# Research: Frontend Polish & Performance

**Feature**: 001-frontend-polish-performance
**Date**: 2026-03-22
**Status**: Complete — all unknowns resolved

## Research Tasks

### R1 — Lucide Icon Import Pattern: Barrel File vs. Direct Imports

**Context**: The spec requires creating a barrel file to centralize ~85 Lucide icon imports across ~68 files. Need to confirm best practices for barrel files with tree-shaking bundlers.

**Decision**: Manual barrel file at `src/lib/icons.ts` with named re-exports.

**Rationale**:
- Vite already tree-shakes lucide-react and isolates it into an `icons-vendor` chunk via `manualChunks` in `vite.config.ts`. The barrel file does not change bundle behavior — it is purely organizational.
- Named re-exports (`export { Icon1, Icon2 } from 'lucide-react'`) preserve tree-shaking in Vite/Rollup because ESM static analysis can trace which icons are actually consumed by importing modules.
- A barrel file provides a single audit point for icon usage, simplifies global find-and-replace operations, and prevents import path drift.
- Auto-generation scripts add maintenance overhead and tooling complexity. Manual maintenance is preferred per the spec's technical notes, given icon churn is infrequent.

**Alternatives Considered**:
1. **Keep direct imports**: Rejected — import drift across 68 files is hard to audit, and new developers add inconsistent paths.
2. **Auto-generated barrel via script**: Rejected for now — the icon set is stable; a script adds tooling complexity without proportional benefit. Can be introduced later if churn increases.
3. **Namespace re-export (`export * from 'lucide-react'`)**: Rejected — this would export all 1,500+ Lucide icons, defeating the purpose of explicit auditing and increasing IDE autocomplete noise. Only used icons should be exported.

---

### R2 — ESLint `no-restricted-imports` with Flat Config

**Context**: The frontend uses ESLint flat config format (`eslint.config.js`). Need to confirm the correct syntax for `no-restricted-imports` in flat config.

**Decision**: Use `no-restricted-imports` rule in a flat config object targeting `lucide-react` with a custom message.

**Rationale**:
- ESLint flat config supports all core rules including `no-restricted-imports`. The rule is specified as a standard `rules` entry within a config object.
- The rule should target `lucide-react` as a restricted path with a custom error message directing developers to `@/lib/icons`.
- The `LucideIcon` type import should be allowed via an exception pattern since it is a TypeScript type, not a component. However, since `LucideIcon` is re-exported from the barrel file, no exception is needed — all imports should come from the barrel.

**Alternatives Considered**:
1. **eslint-plugin-import `no-restricted-paths`**: Rejected — adds a plugin dependency; core `no-restricted-imports` is sufficient.
2. **Custom ESLint plugin**: Rejected — massive overkill for a single rule.

---

### R3 — Lightweight Chore Names Endpoint Design

**Context**: Need a backend endpoint returning only chore names for template membership checks. The existing `list_chores` endpoint returns full chore objects with pagination and filtering.

**Decision**: New `GET /{project_id}/chore-names` endpoint returning `list[str]` via a simple `SELECT name FROM chores WHERE project_id = ?` query.

**Rationale**:
- The endpoint serves a single purpose: set-membership checks of chore names against template names. Full chore objects (with schedule, status, config, etc.) are unnecessary payload.
- A dedicated endpoint is cleaner than adding a query parameter to the existing paginated endpoint, which would complicate its contract.
- Unpaginated response is appropriate because chore names are short strings and projects typically have <100 chores (even 1,000 names would be <50KB).
- No filtering or sorting needed — the consumer performs an in-memory `Set.has()` check.

**Alternatives Considered**:
1. **Add `?names_only=true` to existing list endpoint**: Rejected — pollutes the paginated endpoint's contract with a special mode that bypasses pagination.
2. **Fetch all chores unpaginated**: Rejected — unnecessarily large payload with full chore objects when only names are needed.
3. **Client-side accumulation across pages**: Rejected — requires multiple requests, race conditions during pagination, and complex client logic.

---

### R4 — TanStack Query Hook for Chore Names

**Context**: Need a React Query hook that fetches the complete chore names list with a 60-second stale time.

**Decision**: New `useAllChoreNames(projectId)` hook in `useChores.ts` using `useQuery` with `staleTime: 60_000`.

**Rationale**:
- 60-second stale time means the chore names are refetched at most once per minute, reducing backend load for what is effectively a background check.
- The hook returns `string[]` which is used in a `Set` for O(1) membership checks in `ChoresPanel`.
- Follows existing hook patterns in `useChores.ts` (e.g., `useChoreTemplates`, `useChoresListPaginated`).

**Alternatives Considered**:
1. **Reuse `useChoresList()` (deprecated legacy hook)**: Rejected — hook is deprecated and fetches full chore objects.
2. **Increase stale time to 5 minutes**: Rejected — 60 seconds provides a reasonable balance between freshness and request volume.

---

### R5 — Error Hint Classification Strategy

**Context**: Need to classify errors by HTTP status code and return structured hints. Must not parse error message strings.

**Decision**: Switch-based classification on HTTP status code with a `getErrorHint(error: unknown): ErrorHint` function.

**Rationale**:
- HTTP status codes are stable API contracts; error message strings change across API versions and are unreliable for classification.
- A simple switch/if-else on status code ranges (401/403 → auth, 404 → not found, 422 → validation, 429 → rate limit, 500+ → server error) is the most readable and maintainable approach.
- Network/CORS failures have no status code — detected by checking if the error is a `TypeError` (fetch failure) or has no `status` property.
- The return type `{ title: string; hint: string; action?: { label: string; href: string } }` covers all use cases: plain hint text, hint with navigation link.

**Alternatives Considered**:
1. **Error message string parsing (regex)**: Rejected per spec — fragile across API changes.
2. **Error class hierarchy**: Rejected — adds unnecessary abstraction; a simple utility function is sufficient per YAGNI.
3. **Centralized error handler middleware**: Rejected — too broad in scope; hints are presentation-layer concern.

---

### R6 — EmptyState `hint` Prop Extension

**Context**: EmptyState currently accepts `{ icon, title, description, actionLabel?, onAction? }`. Need to add optional `hint` prop.

**Decision**: Add optional `hint?: string` prop to `EmptyStateProps`. When provided, render a muted paragraph below the description.

**Rationale**:
- Minimal API surface change — a single optional string prop.
- Backward compatible — existing EmptyState usage is unaffected when `hint` is omitted.
- Matches the spec's UI/UX description: "muted paragraph below the existing error message."

**Alternatives Considered**:
1. **Separate `ErrorEmptyState` component**: Rejected — duplicates the EmptyState layout for a single extra line of text.
2. **Render `hint` as part of `description`**: Rejected — hints have different visual treatment (muted, smaller) and semantic meaning.

---

### R7 — Integration Points for Error Hints

**Context**: Need to identify exactly where `getErrorHint()` integrates in ErrorBoundary and ProjectBoardErrorBanners.

**Decision**: 
- **ErrorBoundary.tsx**: Call `getErrorHint(this.state.error)` in the `render()` method's error fallback. Display hint text as a muted paragraph below the existing `<pre>` error message. If action is present, render as a link.
- **ProjectBoardErrorBanners.tsx**: Call `getErrorHint(error)` for each error banner variant. Enhance rate limit banner with reset time and settings link. Enhance auth error banners with login link.
- **Pages (AgentsPage, ToolsPage, ChoresPage)**: Pass `hint={getErrorHint(error).hint}` when rendering error-variant EmptyState components (if they use EmptyState for errors). Note: current pages use `ProjectSelectionEmptyState` for missing project, not generic EmptyState for errors — integration may be limited to where error states actually render.

**Rationale**:
- Minimal touch points — only components that already display errors are modified.
- The `getErrorHint()` function is called at render time, not at error capture time, so it works with both class and function components.

**Alternatives Considered**:
1. **Error context provider**: Rejected — adds React context overhead for what is a simple utility call.
2. **Error middleware in API layer**: Rejected — hints are presentation concerns, not API concerns.
