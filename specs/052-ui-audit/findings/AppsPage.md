# Findings Report: AppsPage

**Page**: AppsPage.tsx | **Route**: /apps
**Audit Date**: 2026-03-18
**Auditor**: speckit.implement
**Line Count**: 707 (limit: 250) ⚠️ EXCEEDS by 2.8x
**Feature Dir**: src/components/apps/
**Related Hooks**: useApps, useCreateApp, useOwners, useStartApp, useStopApp, useDeleteApp

## Summary

| Dimension | Passed | Failed | N/A | Total |
|-----------|--------|--------|-----|-------|
| Component Architecture | 3 | 4 | 0 | 7 |
| Data Fetching | 5 | 1 | 0 | 6 |
| Loading/Error/Empty States | 5 | 0 | 0 | 5 |
| Type Safety | 4 | 1 | 0 | 5 |
| Accessibility | 5 | 2 | 0 | 7 |
| Copy & UX Polish | 6 | 2 | 0 | 8 |
| Styling & Layout | 3 | 3 | 0 | 6 |
| Performance | 4 | 1 | 0 | 5 |
| Test Coverage | 4 | 1 | 0 | 5 |
| Code Hygiene | 5 | 1 | 0 | 6 |
| **Total** | **44** | **16** | **0** | **60** |

**Overall**: 44/60 items passing

## Findings

### Critical: ARCH-01 — Page exceeds 250-line limit (707 lines)

**Dimension**: Component Architecture
**Checklist Item**: ARCH-01 — Single Responsibility (≤ 250 lines)
**Location**: `src/pages/AppsPage.tsx:1-707`
**Related FR**: FR-020

**Issue**: AppsPage.tsx is 707 lines — 2.8× the 250-line limit. The create dialog form (lines 384–703) is a large inline form with 15+ state variables and complex validation logic that should be extracted.

**Remediation**:
1. Extract the create dialog (lines 384–703) into `src/components/apps/CreateAppDialog.tsx`
2. Extract the `showSuccess`/`showError` feedback logic into a `useAppFeedback` hook or incorporate into existing `useApps.ts`
3. The `slugify` utility function should live in `src/utils/` or inside `useApps.ts`
4. After extraction, AppsPage should be under 250 lines

**Verification**:
```bash
wc -l src/pages/AppsPage.tsx
# Expected: < 250
```

---

### Major: ARCH-06 — Excessive inline state in page component

**Dimension**: Component Architecture
**Checklist Item**: ARCH-06 — Hook extraction
**Location**: `src/pages/AppsPage.tsx:36-77`
**Related FR**: FR-023

**Issue**: 15 `useState` calls inline in the page, including create-dialog form state (`displayName`, `aiEnhance`, `showAdvanced`, `repoType`, `repoOwner`, `repoVisibility`, `createProject`, `azureClientId`, `azureClientSecret`). These belong in the CreateAppDialog component or a `useCreateAppForm` hook.

**Remediation**:
Extract create-form state into the `CreateAppDialog` component.

---

### Major: ARCH-07 — Business logic inline in JSX

**Dimension**: Component Architecture
**Checklist Item**: ARCH-07 — No business logic in JSX
**Location**: `src/pages/AppsPage.tsx:104-115`
**Related FR**: FR-024

**Issue**: `slugify()` function and derived values `derivedName`/`derivedBranch` are defined in the page component. This is presentation-layer business logic that belongs in a hook or utility.

**Remediation**:
Move `slugify` to `src/utils/slugify.ts` and `derivedName`/`derivedBranch` computation into `CreateAppDialog`.

---

### Major: STYLE-03 — Hardcoded zinc/emerald colors instead of design tokens

**Dimension**: Styling & Layout
**Checklist Item**: STYLE-03 — Dark mode support
**Location**: `src/pages/AppsPage.tsx:283-707`
**Related FR**: FR-025

**Issue**: 52 instances of hardcoded `text-zinc-*`, `bg-zinc-*`, `text-emerald-*`, `bg-emerald-*` color classes scattered throughout the page and create dialog. These bypass the design token system (`bg-background`, `text-foreground`, `text-primary`, etc.) and may not correctly adapt to custom themes.

**Remediation**:
Replace hardcoded colors with design token classes:
- `text-zinc-900 dark:text-zinc-100` → `text-foreground`
- `text-zinc-500 dark:text-zinc-400` → `text-muted-foreground`
- `bg-emerald-600` → `bg-primary`
- `text-emerald-500/600` → `text-primary`
- `border-zinc-300 dark:border-zinc-700` → `border-border`
- `bg-zinc-800/50 dark:*` → `bg-muted`

---

### Major: STYLE-01 — Hardcoded focus ring colors

**Dimension**: Styling & Layout
**Checklist Item**: STYLE-01 — Tailwind only
**Location**: `src/pages/AppsPage.tsx:290-693`
**Related FR**: —

**Issue**: Focus rings hardcoded to `focus-visible:ring-emerald-500` instead of using `focus-visible:ring-primary` or the `celestial-focus` CSS class.

**Remediation**:
Replace `focus-visible:ring-emerald-500` with `focus-visible:ring-primary` throughout.

---

### Minor: A11Y-02 — Create dialog focus management

**Dimension**: Accessibility
**Checklist Item**: A11Y-02 — Focus management
**Location**: `src/pages/AppsPage.tsx:384-703`
**Related FR**: FR-009

**Issue**: The create dialog uses a custom `div[role="dialog"]` implementation. Focus is not explicitly moved to the dialog on open (no `autoFocus` on first field or `useEffect` to focus the dialog). The `Escape` key handler is implemented via `document.addEventListener` (L118–127), which is correct, but initial focus movement is missing.

**Remediation**:
Add `autoFocus` to the first input field in the dialog or use a `useEffect` to focus the dialog container on mount.

---

### Minor: A11Y-06 — Advanced options toggle missing ARIA expand state

**Dimension**: Accessibility
**Checklist Item**: A11Y-06 — Focus-visible styles
**Location**: `src/pages/AppsPage.tsx:647-657`
**Related FR**: FR-013

**Issue**: The "Advanced options" toggle button lacks `aria-expanded` attribute to communicate the expand state to screen readers.

**Remediation**:
Add `aria-expanded={showAdvanced}` to the advanced options toggle button.

---

### Minor: COPY-02 — Action button labels use "New" prefix inconsistently

**Dimension**: Copy & UX Polish
**Checklist Item**: COPY-02 — Consistent terminology / COPY-03 — Verb-based labels
**Location**: `src/pages/AppsPage.tsx:290-303`
**Related FR**: FR-015

**Issue**: Header has both "New Repository" and "Create App" buttons. Per the copy standard, action labels should be verb-based ("Create Repository" not "New Repository").

**Remediation**:
Change "New Repository" to "Create Repository".

---

### Minor: DATA-06 — assignPipelineMutation missing onError handler (ProjectsPage note)

**Dimension**: Data Fetching
**Checklist Item**: DATA-06 — Mutation error handling
**Location**: `src/pages/AppsPage.tsx` — all mutations have onError ✅

**Issue**: N/A — AppsPage mutations all have `onError` handlers. This is a pass.

---

### Minor: TEST-04 — No test for rate limit error scenario

**Dimension**: Test Coverage
**Checklist Item**: TEST-04 — Edge cases covered
**Location**: `src/hooks/useApps.test.tsx`
**Related FR**: FR-033

**Issue**: Existing hook tests may not cover the `isRateLimitApiError()` branch.

**Remediation**:
Add test case in `useApps.test.tsx` that mocks a rate-limit API error response and verifies the error state.

---

## Remediation Plan

### Phase 1: Structural Fixes
- [ ] ARCH-01 — Extract CreateAppDialog into `src/components/apps/CreateAppDialog.tsx`
- [ ] ARCH-06 — Move create-form state into CreateAppDialog
- [ ] ARCH-07 — Move slugify to utils, move derivedName/Branch into dialog

### Phase 2: States & Error Handling
- [ ] ✅ All states already properly handled (loading, error, empty, rate limit)

### Phase 3: Accessibility & UX
- [ ] A11Y-02 — Add autoFocus or useEffect to move focus on dialog open
- [ ] A11Y-06 — Add aria-expanded to advanced options toggle
- [ ] COPY-03 — Change "New Repository" to "Create Repository"

### Phase 4: Styling
- [ ] STYLE-03 — Replace hardcoded zinc/emerald colors with design tokens
- [ ] STYLE-01 — Replace focus-visible:ring-emerald-500 with ring-primary

### Phase 5: Validation
- [ ] ESLint: 0 warnings
- [ ] TypeScript: 0 errors
- [ ] Tests: all pass
- [ ] Visual: light mode, dark mode, 768px–1920px
