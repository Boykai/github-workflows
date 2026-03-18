# Quickstart: UI Audit

**Feature**: `052-ui-audit`
**Date**: 2026-03-18

---

## Prerequisites

- Node.js 22+ with npm
- Git
- Chrome/Chromium (for visual verification and DevTools a11y audit)

## Quick Verification Commands

### Frontend — Install Dependencies

```bash
cd solune/frontend
npm ci
```

### Frontend — Lint All Pages

```bash
cd solune/frontend

# Lint all page files
npx eslint src/pages/

# Lint specific page and its feature components
npx eslint src/pages/AppsPage.tsx src/components/apps/
npx eslint src/pages/AgentsPage.tsx src/components/agents/
npx eslint src/pages/AgentsPipelinePage.tsx src/components/pipeline/
npx eslint src/pages/ProjectsPage.tsx src/components/board/
npx eslint src/pages/ChoresPage.tsx src/components/chores/
npx eslint src/pages/SettingsPage.tsx src/components/settings/
npx eslint src/pages/HelpPage.tsx src/components/help/
npx eslint src/pages/ToolsPage.tsx src/components/tools/
npx eslint src/pages/LoginPage.tsx src/components/auth/
npx eslint src/pages/AppPage.tsx src/components/apps/
npx eslint src/pages/NotFoundPage.tsx
```

### Frontend — Type Check

```bash
cd solune/frontend

# Full type check
npx tsc --noEmit
```

### Frontend — Run All Tests

```bash
cd solune/frontend

# Run full test suite
npm run test

# Run tests for a specific page
npx vitest run src/pages/AppsPage.test.tsx
npx vitest run src/pages/AgentsPage.test.tsx
npx vitest run src/pages/ProjectsPage.test.tsx
```

### Frontend — Run Tests for Specific Hooks

```bash
cd solune/frontend

# Run hook tests
npx vitest run src/hooks/useApps.test.ts
npx vitest run src/hooks/useAgents.test.ts
npx vitest run src/hooks/useProjects.test.ts
npx vitest run src/hooks/useChores.test.ts
npx vitest run src/hooks/useTools.test.ts
npx vitest run src/hooks/useSettings.test.ts
```

### Frontend — Build Check

```bash
cd solune/frontend
npm run build
```

## Page Line Count Check

Quick check to identify pages exceeding the 250-line threshold:

```bash
cd solune/frontend
wc -l src/pages/*.tsx | sort -rn
```

Expected output identifying extraction candidates:
- `AppsPage.tsx` — 709 lines (exceeds threshold)
- `ProjectsPage.tsx` — 631 lines (exceeds threshold)
- `AgentsPipelinePage.tsx` — 417 lines (exceeds threshold)

## Audit Procedure Per Page

### Step 1: Gather Context

```bash
cd solune/frontend

# Read the page file
cat src/pages/[PageName].tsx

# Check line count
wc -l src/pages/[PageName].tsx

# Find related components
ls src/components/[feature]/

# Find related hooks
ls src/hooks/use[Feature]*.ts

# Find related tests
ls src/pages/[PageName].test.tsx src/hooks/use[Feature]*.test.ts src/components/[feature]/*.test.tsx 2>/dev/null
```

### Step 2: Run Automated Checks

```bash
cd solune/frontend

# Lint check
npx eslint src/pages/[PageName].tsx src/components/[feature]/ --max-warnings=0

# Type check
npx tsc --noEmit

# Run related tests
npx vitest run src/pages/[PageName].test.tsx src/hooks/use[Feature].test.ts
```

### Step 3: Scan for Common Issues

```bash
cd solune/frontend

# Check for 'any' types
grep -rn ': any' src/pages/[PageName].tsx src/components/[feature]/ src/hooks/use[Feature]*.ts

# Check for type assertions
grep -rn ' as ' src/pages/[PageName].tsx src/components/[feature]/

# Check for console.log
grep -rn 'console\.' src/pages/[PageName].tsx src/components/[feature]/

# Check for inline styles
grep -rn 'style=' src/pages/[PageName].tsx src/components/[feature]/

# Check for hardcoded colors
grep -rn '#[0-9a-fA-F]\{3,6\}' src/pages/[PageName].tsx src/components/[feature]/
grep -rn 'bg-white\|text-white\|bg-black\|text-black' src/pages/[PageName].tsx src/components/[feature]/

# Check for index keys
grep -rn 'key={index}' src/pages/[PageName].tsx src/components/[feature]/

# Check for relative imports
grep -rn "from '\.\." src/pages/[PageName].tsx src/components/[feature]/
grep -rn 'from "\.\.' src/pages/[PageName].tsx src/components/[feature]/

# Check for raw fetch/useEffect patterns
grep -rn 'useEffect.*fetch\|fetch(' src/pages/[PageName].tsx src/hooks/use[Feature]*.ts
```

### Step 4: Evaluate Checklist

Score each of the 60 checklist items as Pass/Fail/N/A using the criteria defined in `contracts/audit-checklist.md`.

### Step 5: Document Findings

Create a findings file at `specs/052-ui-audit/checklists/[page-name]-audit.md` using the output format defined in the audit checklist contract.

## Key Files to Reference

### Pages (audit targets)

| File | Lines | Primary Hook | Feature Components |
|------|-------|-------------|-------------------|
| `src/pages/AgentsPage.tsx` | 230 | `useAgents` | `src/components/agents/` |
| `src/pages/AgentsPipelinePage.tsx` | 417 | `usePipelineConfig` | `src/components/pipeline/` |
| `src/pages/AppPage.tsx` | 141 | `useApps` | `src/components/apps/` |
| `src/pages/AppsPage.tsx` | 709 | `useApps` | `src/components/apps/` |
| `src/pages/ChoresPage.tsx` | 166 | `useChores` | `src/components/chores/` |
| `src/pages/HelpPage.tsx` | 195 | N/A | `src/components/help/` |
| `src/pages/LoginPage.tsx` | 119 | `useAuth` | `src/components/auth/` |
| `src/pages/NotFoundPage.tsx` | 29 | N/A | N/A |
| `src/pages/ProjectsPage.tsx` | 631 | `useProjects` | `src/components/board/` |
| `src/pages/SettingsPage.tsx` | 107 | `useSettings` | `src/components/settings/` |
| `src/pages/ToolsPage.tsx` | 87 | `useTools` | `src/components/tools/` |

### Shared Components (use as-is, don't reimplement)

| Component | Path | Use For |
|-----------|------|---------|
| `Button` | `src/components/ui/button.tsx` | All button elements |
| `Card` | `src/components/ui/card.tsx` | Content sections |
| `Input` | `src/components/ui/input.tsx` | Form fields |
| `Tooltip` | `src/components/ui/tooltip.tsx` | Truncated text hover |
| `ConfirmationDialog` | `src/components/ui/confirmation-dialog.tsx` | Destructive actions |
| `HoverCard` | `src/components/ui/hover-card.tsx` | Rich previews |
| `CelestialLoader` | `src/components/common/CelestialLoader.tsx` | Loading states |
| `ErrorBoundary` | `src/components/common/ErrorBoundary.tsx` | Error boundaries |
| `ProjectSelectionEmptyState` | `src/components/common/ProjectSelectionEmptyState.tsx` | Empty states |

### Utilities

| Utility | Path | Purpose |
|---------|------|---------|
| `cn()` | `src/lib/utils.ts` | Conditional class merging (clsx + tailwind-merge) |
| `isRateLimitApiError()` | `src/services/api.ts` | Rate limit error detection |
| `ApiError` | `src/services/api.ts` | Typed API error class |

## Verification After Remediation

### Automated Checks

```bash
cd solune/frontend

# Full lint check (0 warnings)
npx eslint src/pages/ src/components/ src/hooks/ --max-warnings=0

# Full type check (0 errors)
npx tsc --noEmit

# Full test suite
npm run test

# Build check
npm run build
```

### Manual End-to-End Check

1. Start the dev server: `npm run dev`
2. Navigate to each page
3. Toggle dark mode — verify all elements visible and contrasted
4. Resize viewport from 320px to 1920px — verify no layout breakage
5. Tab through all interactive elements — verify focus is visible and correct
6. Trigger destructive actions — verify confirmation dialogs appear
7. Simulate API errors (disconnect network) — verify error states render correctly
8. Check empty states where applicable
