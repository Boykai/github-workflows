# Component Compliance Contract: Audit & Update UI Components for Style Consistency

**Feature Branch**: `026-ui-style-consistency`  
**Date**: 2026-03-07

> This contract defines the compliance rules each component MUST satisfy after remediation. Use this as the checklist during implementation and verification.

## Class Composition Contract

### Rule: All conditional className MUST use cn()

**Import**: `import { cn } from '@/lib/utils';`

**Compliant Patterns**:

```typescript
// Static classes (no cn needed)
className="flex items-center gap-2 text-sm text-muted-foreground"

// Conditional classes — MUST use cn()
className={cn(
  'flex items-center gap-2 px-4 py-2 rounded-lg',
  isActive && 'bg-primary text-primary-foreground',
  !isActive && 'bg-muted text-muted-foreground',
  className  // when accepting className prop
)}

// Ternary in cn() — acceptable
className={cn(
  'px-3 py-1 rounded-full text-xs font-medium',
  isConnected ? STATUS_COLORS.success.bg : STATUS_COLORS.error.bg,
  isConnected ? STATUS_COLORS.success.text : STATUS_COLORS.error.text,
)}
```

**Non-Compliant Patterns**:

```typescript
// Template literal with ternary — NOT compliant
className={`flex items-center ${isActive ? 'bg-primary' : 'bg-muted'}`}

// String concatenation — NOT compliant
className={'flex items-center ' + (isActive ? 'bg-primary' : 'bg-muted')}

// Array.join — NOT compliant
className={['flex', isActive && 'bg-primary'].filter(Boolean).join(' ')}
```

### Exception: Static-only className

Components with purely static class strings (no conditions, no props) do NOT need cn():

```typescript
// This is fine — no conditions
className="flex items-center gap-2 text-sm text-muted-foreground"
```

## Color Token Contract

### Semantic Theme Tokens

All components MUST use semantic theme tokens for core visual properties:

| Component Area | Required Token | Forbidden Alternative |
|---|---|---|
| Container background | `bg-background`, `bg-card`, `bg-panel`, `bg-popover` | `bg-white`, `bg-gray-*`, `bg-[#...]` |
| Text | `text-foreground`, `text-muted-foreground`, `text-*-foreground` | `text-gray-*`, `text-[#...]` |
| Borders | `border-border`, `border-input` | `border-gray-*` |
| Interactive highlight | `bg-primary`, `bg-accent`, `bg-secondary` | `bg-yellow-*`, `bg-purple-*` |
| Destructive actions | `bg-destructive`, `text-destructive` | `bg-red-600`, `text-red-*` (unless in STATUS_COLORS) |

### Status Color Constants

Status indicators MUST use centralized `STATUS_COLORS` from `constants.ts`:

| Semantic State | Constant | Used In |
|---|---|---|
| Connected / Success / Active | `STATUS_COLORS.success` | SignalConnection, McpSettings, CleanUpSummary, agent status |
| Warning / Degraded | `STATUS_COLORS.warning` | Rate limit warnings, partial failures |
| Error / Disconnected / Failed | `STATUS_COLORS.error` | Connection failures, task errors |
| Info / Pending | `STATUS_COLORS.info` | Loading states, information badges |
| Inactive / Default | `STATUS_COLORS.neutral` | Disabled states, placeholder |

### Priority Color Constants

Priority badges MUST use `PRIORITY_COLORS` from `constants.ts`:

```typescript
const priorityConfig = PRIORITY_COLORS[priority?.name] ?? PRIORITY_COLORS.P2;
```

## Dark Mode Contract

### Every visible element MUST work in both modes

**Rule**: If a component uses an explicit Tailwind color class (not a semantic token), it MUST have a corresponding `dark:` variant.

```typescript
// Compliant — semantic token auto-adapts
className="bg-card text-card-foreground"

// Compliant — explicit dark variant provided
className="bg-green-500/10 dark:bg-green-500/15 text-green-600 dark:text-green-400"

// Non-compliant — no dark variant
className="bg-green-100 text-green-800"  // ❌ invisible in dark mode
```

### STATUS_COLORS already include dark variants

When using centralized constants, dark mode is handled automatically:

```typescript
// Both light and dark variants are embedded in the constant
className={cn(STATUS_COLORS.success.bg, STATUS_COLORS.success.text)}
// Expands to: "bg-green-500/10 dark:bg-green-500/15 text-green-600 dark:text-green-400"
```

## Component-Specific Contracts

### High-Priority Remediation Targets

| Component | File | Key Changes |
|---|---|---|
| ErrorBoundary | `components/common/ErrorBoundary.tsx` | Replace `style={{ padding: '2rem', textAlign: 'center' }}` with `className="p-8 text-center"` |
| MessageBubble | `components/chat/MessageBubble.tsx` | Replace template literal class composition with `cn()` |
| IssueDetailModal | `components/board/IssueDetailModal.tsx` | Replace status ternary chains with `cn()` + centralized constants |
| IssueRecommendationPreview | `components/chat/IssueRecommendationPreview.tsx` | Replace nested ternary color chains with `cn()` + constants |
| AddAgentPopover | `components/board/AddAgentPopover.tsx` | Replace source-type ternary chains with `AGENT_SOURCE_COLORS` constant |
| SignalConnection | `components/settings/SignalConnection.tsx` | Replace 6+ hardcoded status color patterns with `STATUS_COLORS` |
| McpSettings | `components/settings/McpSettings.tsx` | Replace hardcoded green/yellow indicators with `STATUS_COLORS` |
| CleanUpSummary | `components/board/CleanUpSummary.tsx` | Replace 8+ identical green patterns with `STATUS_COLORS.success` |
| CleanUpConfirmModal | `components/board/CleanUpConfirmModal.tsx` | Replace repeated green styling with `STATUS_COLORS.success` |
| ChoresPanel | `components/chores/ChoresPanel.tsx` | Adopt `cn()` for conditional classes |

### Compliant Components (No Changes Needed)

| Component | File | Reason |
|---|---|---|
| Button | `components/ui/button.tsx` | Uses CVA + cn() — fully compliant |
| Card | `components/ui/card.tsx` | Uses cn() + semantic tokens — fully compliant |
| Input | `components/ui/input.tsx` | Uses cn() + semantic tokens — fully compliant |
| ChatInterface | `components/chat/ChatInterface.tsx` | Already uses cn() — compliant |
| LoginButton | `components/auth/LoginButton.tsx` | Simple, semantic tokens only |

## Build Verification Contract

After all remediations are applied:

1. `cd frontend && npm run build` — MUST succeed with zero errors
2. `cd frontend && npx tsc --noEmit` — MUST succeed with zero type errors
3. `cd frontend && npx eslint src/` — MUST produce no new warnings/errors
4. `cd frontend && npm run test` — All existing tests MUST pass
5. Visual check in light mode — No layout shifts, missing elements, or incorrect colors
6. Visual check in dark mode — All elements adapt correctly, no invisible text/borders
