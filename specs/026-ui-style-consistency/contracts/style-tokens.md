# Style Token Contract: Audit & Update UI Components for Style Consistency

**Feature Branch**: `026-ui-style-consistency`  
**Date**: 2026-03-07

> This contract defines the authoritative design tokens and their expected usage patterns. All components MUST reference these tokens — hardcoded alternatives are non-compliant unless documented as intentional exceptions.

## CSS Custom Properties (index.css)

### Core Palette Tokens

| Token | Light Mode (HSL) | Dark Mode (HSL) | Tailwind Usage |
|---|---|---|---|
| `--background` | `32 46% 92%` | `252 30% 6%` | `bg-background` |
| `--foreground` | `252 22% 15%` | `38 45% 89%` | `text-foreground` |
| `--card` | `34 50% 96%` | `253 28% 10%` | `bg-card` |
| `--card-foreground` | `252 22% 15%` | `38 45% 89%` | `text-card-foreground` |
| `--popover` | `34 50% 96%` | `253 28% 10%` | `bg-popover` |
| `--popover-foreground` | `252 22% 15%` | `38 45% 89%` | `text-popover-foreground` |
| `--panel` | `34 44% 94%` | `252 28% 8%` | `bg-panel` |
| `--primary` | `43 78% 58%` | `43 74% 57%` | `bg-primary`, `text-primary` |
| `--primary-foreground` | `248 27% 12%` | `248 27% 12%` | `text-primary-foreground` |
| `--secondary` | `28 30% 87%` | `252 22% 14%` | `bg-secondary` |
| `--secondary-foreground` | `252 22% 15%` | `38 40% 88%` | `text-secondary-foreground` |
| `--accent` | `251 42% 32%` | `253 35% 27%` | `bg-accent` |
| `--accent-foreground` | `38 45% 91%` | `38 45% 89%` | `text-accent-foreground` |
| `--destructive` | `0 72% 51%` | `0 72% 51%` | `bg-destructive` |
| `--destructive-foreground` | `0 0% 100%` | `0 0% 100%` | `text-destructive-foreground` |
| `--muted` | `32 28% 88%` | `252 22% 12%` | `bg-muted` |
| `--muted-foreground` | `250 10% 46%` | `250 10% 55%` | `text-muted-foreground` |
| `--border` | `34 22% 76%` | `252 18% 18%` | `border-border` |
| `--input` | `34 22% 76%` | `252 18% 18%` | `border-input` |
| `--ring` | `43 74% 57%` | `43 74% 57%` | `ring-ring` |

### Special Tokens

| Token | Light Mode | Dark Mode | Purpose |
|---|---|---|---|
| `--glow` | `44 100% 85%` | `44 80% 30%` | Glow/highlight effect |
| `--gold` | `42 78% 56%` | `42 78% 50%` | Gold accent color |
| `--night` | `250 27% 17%` | `253 30% 5%` | Deep dark background |
| `--radius` | `1rem` | `1rem` | Base border radius |

### Shadow Tokens

| Token | Value | Tailwind Usage |
|---|---|---|
| `--shadow-sm` | `0 8px 24px rgba(23,19,39,0.08)` | `shadow-sm` |
| `--shadow-default` | `0 16px 40px rgba(23,19,39,0.12)` | `shadow` |
| `--shadow-md` | `0 22px 50px rgba(23,19,39,0.16)` | `shadow-md` |
| `--shadow-lg` | `0 32px 72px rgba(10,8,18,0.22)` | `shadow-lg` |

### Font Tokens

| Token | Value | Tailwind Usage |
|---|---|---|
| `--font-display` | `'Plus Jakarta Sans', 'Inter', 'system-ui', sans-serif` | `font-display` (headings) |
| `--font-sans` | `'Inter', 'system-ui', sans-serif` | `font-sans` (body text) |

## TypeScript Color Constants (constants.ts)

### PRIORITY_COLORS (Existing)

```typescript
export const PRIORITY_COLORS: Record<string, { bg: string; text: string; label: string }> = {
  P0: { bg: 'bg-red-100/90 dark:bg-red-950/50', text: 'text-red-700 dark:text-red-300', label: 'Critical' },
  P1: { bg: 'bg-orange-100/90 dark:bg-orange-950/50', text: 'text-orange-700 dark:text-orange-300', label: 'High' },
  P2: { bg: 'bg-blue-100/90 dark:bg-blue-950/50', text: 'text-blue-700 dark:text-blue-300', label: 'Medium' },
  P3: { bg: 'bg-emerald-100/90 dark:bg-emerald-950/50', text: 'text-emerald-700 dark:text-emerald-300', label: 'Low' },
};
```

### STATUS_COLORS (New)

```typescript
export const STATUS_COLORS = {
  success: { bg: 'bg-green-500/10 dark:bg-green-500/15', text: 'text-green-600 dark:text-green-400', border: 'border-green-500/30 dark:border-green-500/20', dot: 'bg-green-500' },
  warning: { bg: 'bg-yellow-500/10 dark:bg-yellow-500/15', text: 'text-yellow-600 dark:text-yellow-400', border: 'border-yellow-500/30 dark:border-yellow-500/20', dot: 'bg-yellow-500' },
  error: { bg: 'bg-red-500/10 dark:bg-red-500/15', text: 'text-red-600 dark:text-red-400', border: 'border-red-500/30 dark:border-red-500/20', dot: 'bg-red-500' },
  info: { bg: 'bg-blue-500/10 dark:bg-blue-500/15', text: 'text-blue-600 dark:text-blue-400', border: 'border-blue-500/30 dark:border-blue-500/20', dot: 'bg-blue-500' },
  neutral: { bg: 'bg-muted', text: 'text-muted-foreground', border: 'border-border', dot: 'bg-muted-foreground' },
} as const;
```

### AGENT_SOURCE_COLORS (New)

```typescript
export const AGENT_SOURCE_COLORS: Record<string, { bg: string; text: string }> = {
  builtin: { bg: 'bg-blue-500/10 dark:bg-blue-500/15', text: 'text-blue-600 dark:text-blue-400' },
  custom: { bg: 'bg-purple-500/10 dark:bg-purple-500/15', text: 'text-purple-600 dark:text-purple-400' },
  community: { bg: 'bg-emerald-500/10 dark:bg-emerald-500/15', text: 'text-emerald-600 dark:text-emerald-400' },
};
```

## Usage Rules

### MUST use semantic tokens for:

| Visual Property | Correct Approach | Incorrect Approach |
|---|---|---|
| Page background | `bg-background` | `bg-gray-100` or `bg-[#f5f0eb]` |
| Text color | `text-foreground` or `text-muted-foreground` | `text-gray-900` or `text-[#1a1625]` |
| Card background | `bg-card` | `bg-white` or `bg-gray-50` |
| Primary action | `bg-primary text-primary-foreground` | `bg-yellow-500 text-black` |
| Border | `border-border` | `border-gray-300` |
| Focus ring | `ring-ring` | `ring-blue-500` |
| Shadow | `shadow-sm` / `shadow` / `shadow-md` / `shadow-lg` | `shadow-[0_4px_8px_rgba(0,0,0,0.1)]` |
| Border radius | `rounded-lg` (maps to `--radius`) | `rounded-[6px]` |

### MAY use Tailwind palette colors for:

| Use Case | Permitted Pattern | Rationale |
|---|---|---|
| Status indicators | `STATUS_COLORS.success.*` constant | Semantic status has standard color expectations |
| Priority badges | `PRIORITY_COLORS.*` constant | Already centralized |
| Agent source badges | `AGENT_SOURCE_COLORS.*` constant | Category identification |
| One-off decorative | `text-amber-500` (with `/* intentional */` comment) | Documented exception |

### MUST NOT:

- Use hex color values (`#fff`, `#1a1625`) in component files
- Use `rgb()` / `rgba()` in component files (these belong in `index.css` only)
- Use Tailwind color classes without `dark:` counterpart when the element is visible
- Duplicate the same color class combination in 2+ files (centralize instead)
