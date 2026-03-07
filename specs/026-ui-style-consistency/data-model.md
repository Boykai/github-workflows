# Data Model: Audit & Update UI Components for Style Consistency

**Feature Branch**: `026-ui-style-consistency`  
**Date**: 2026-03-07

> This feature is frontend-only. No new backend entities are created. This document describes the **audit data model** (component inventory schema), **centralized color constants** (new TypeScript constants for status/state colors), and **component compliance rules** governing the remediation.

## Existing Entities (Preserved — No Changes)

These design system primitives from `frontend/src/index.css` and `frontend/src/constants.ts` are used as-is:

| Entity | Location | Description |
|---|---|---|
| CSS Theme Tokens | `index.css` `:root` / `.dark` | HSL custom properties: `--background`, `--foreground`, `--primary`, `--secondary`, `--accent`, `--destructive`, `--muted`, `--border`, `--card`, `--popover`, `--panel`, `--glow`, `--gold`, `--night`, `--radius` |
| Shadow Tokens | `index.css` `:root` / `.dark` | `--shadow-sm`, `--shadow-default`, `--shadow-md`, `--shadow-lg` |
| Font Tokens | `index.css` `:root` | `--font-display` (Plus Jakarta Sans), `--font-sans` (Inter) |
| Priority Colors | `constants.ts` `PRIORITY_COLORS` | `P0`=red, `P1`=orange, `P2`=blue, `P3`=emerald with light/dark bg+text classes |
| NAV_ROUTES | `constants.ts` | 6 route definitions with paths, labels, icons |
| cn() utility | `lib/utils.ts` | `clsx` + `tailwind-merge` class composition function |
| Button Variants | `ui/button.tsx` | CVA variants: default, destructive, outline, secondary, ghost, link × sm, default, lg, icon |
| Card Component | `ui/card.tsx` | Base card with celestial-panel styling, sub-components for header/title/content/footer |
| Input Component | `ui/input.tsx` | Base input with theme-aware border, focus ring |

## New Constants (Added to `constants.ts`)

### STATUS_COLORS

Centralized color classes for operational states used across multiple components. Replaces hardcoded color strings scattered across 18+ files.

```typescript
export const STATUS_COLORS = {
  success: {
    bg: 'bg-green-500/10 dark:bg-green-500/15',
    text: 'text-green-600 dark:text-green-400',
    border: 'border-green-500/30 dark:border-green-500/20',
    dot: 'bg-green-500',
  },
  warning: {
    bg: 'bg-yellow-500/10 dark:bg-yellow-500/15',
    text: 'text-yellow-600 dark:text-yellow-400',
    border: 'border-yellow-500/30 dark:border-yellow-500/20',
    dot: 'bg-yellow-500',
  },
  error: {
    bg: 'bg-red-500/10 dark:bg-red-500/15',
    text: 'text-red-600 dark:text-red-400',
    border: 'border-red-500/30 dark:border-red-500/20',
    dot: 'bg-red-500',
  },
  info: {
    bg: 'bg-blue-500/10 dark:bg-blue-500/15',
    text: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-500/30 dark:border-blue-500/20',
    dot: 'bg-blue-500',
  },
  neutral: {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    border: 'border-border',
    dot: 'bg-muted-foreground',
  },
} as const;
```

### AGENT_SOURCE_COLORS

Color mappings for agent source types (currently scattered across AddAgentPopover.tsx and AgentCard.tsx).

```typescript
export const AGENT_SOURCE_COLORS: Record<string, { bg: string; text: string }> = {
  builtin: { bg: 'bg-blue-500/10 dark:bg-blue-500/15', text: 'text-blue-600 dark:text-blue-400' },
  custom: { bg: 'bg-purple-500/10 dark:bg-purple-500/15', text: 'text-purple-600 dark:text-purple-400' },
  community: { bg: 'bg-emerald-500/10 dark:bg-emerald-500/15', text: 'text-emerald-600 dark:text-emerald-400' },
};
```

## Audit Report Schema

The component audit (User Story 1) produces a structured inventory. Each component is evaluated and assigned a compliance status.

### ComponentAuditEntry

```typescript
interface ComponentAuditEntry {
  file: string;              // Relative path from frontend/src/ (e.g., 'components/board/IssueCard.tsx')
  lineCount: number;         // Total lines in the file
  category: ComponentCategory;
  complianceStatus: 'compliant' | 'partially-compliant' | 'non-compliant';
  deviations: Deviation[];   // Empty array if compliant
  remediationPriority: 'critical' | 'moderate' | 'minor';
}
```

### Deviation

```typescript
interface Deviation {
  line: number;                // Line number of the deviation
  type: DeviationType;
  currentValue: string;        // What the code currently has (e.g., 'bg-green-500/10 text-green-600')
  expectedValue: string;       // What it should reference (e.g., 'STATUS_COLORS.success.bg + STATUS_COLORS.success.text')
  description: string;         // Human-readable explanation
}
```

### DeviationType

```typescript
type DeviationType =
  | 'hardcoded-color'          // Uses specific color class instead of theme token or centralized constant
  | 'missing-cn'               // Uses template literal instead of cn() for class composition
  | 'inline-style'             // Uses style={{}} with hardcoded values that could be Tailwind
  | 'missing-dark-variant'     // Light mode styling without corresponding dark: variant
  | 'inconsistent-radius'      // Border radius doesn't match theme's --radius token
  | 'inconsistent-shadow'      // Shadow doesn't use theme shadow tokens
  | 'deprecated-component';    // Component with zero import references
```

### ComponentCategory

```typescript
type ComponentCategory =
  | 'ui-base'          // components/ui/ — Button, Card, Input
  | 'layout'           // layout/ — AppLayout, Sidebar, TopBar, etc.
  | 'page'             // pages/ — AppPage, ProjectsPage, etc.
  | 'board'            // components/board/ — ProjectBoard, IssueCard, etc.
  | 'chat'             // components/chat/ — ChatPopup, MessageBubble, etc.
  | 'agents'           // components/agents/ — AgentCard, AddAgentModal, etc.
  | 'chores'           // components/chores/ — ChoresPanel, AddChoreModal, etc.
  | 'settings'         // components/settings/ — PrimarySettings, McpSettings, etc.
  | 'auth'             // components/auth/ — LoginButton
  | 'common';          // components/common/ — ErrorBoundary
```

## Component Inventory Summary

| Category | Files | Lines | Compliant | Partially | Non-Compliant |
|---|---|---|---|---|---|
| ui-base | 3 | ~215 | 3 | 0 | 0 |
| layout | 7 | ~618 | 5 | 2 | 0 |
| page | 8 | ~920 | 6 | 2 | 0 |
| board | 27 | ~2,100 | 12 | 10 | 5 |
| chat | 13 | ~1,200 | 5 | 5 | 3 |
| agents | 6 | ~650 | 2 | 2 | 2 |
| chores | 5 | ~900 | 0 | 3 | 2 |
| settings | 15 | ~1,450 | 5 | 5 | 5 |
| auth | 1 | ~50 | 1 | 0 | 0 |
| common | 1 | ~80 | 0 | 0 | 1 |
| **Total** | **86** | **~8,183** | **39** | **29** | **18** |

## Remediation Rules

### Rule 1: cn() Adoption

**When**: A component uses template literals or string concatenation for conditional class names.  
**Action**: Replace with `cn()` from `@/lib/utils`.

```typescript
// Before (non-compliant)
className={`px-4 py-2 ${isActive ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}

// After (compliant)
className={cn('px-4 py-2', isActive ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground')}
```

### Rule 2: Centralized Color Constants

**When**: A component uses hardcoded Tailwind color classes for status, state, or category indicators that appear in 2+ files.  
**Action**: Reference the centralized constant from `constants.ts`.

```typescript
// Before (non-compliant — repeated in 8+ files)
className="bg-green-500/10 text-green-600 dark:text-green-400"

// After (compliant)
className={cn(STATUS_COLORS.success.bg, STATUS_COLORS.success.text)}
```

### Rule 3: Inline Style Replacement

**When**: A component uses `style={{}}` with values that have Tailwind equivalents.  
**Action**: Replace with Tailwind utility classes.

```typescript
// Before (non-compliant)
style={{ padding: '2rem', textAlign: 'center' }}

// After (compliant)
className="p-8 text-center"
```

### Rule 4: Dark Mode Completeness

**When**: A component uses explicit light-mode colors without corresponding `dark:` variants.  
**Action**: Add appropriate `dark:` variant or use semantic theme token that auto-adapts.

### Rule 5: Intentional Exceptions

**When**: A component has a legitimate one-off value (e.g., specific width for a login form).  
**Action**: Document with an inline comment `/* intentional: [reason] */` and leave as-is.
