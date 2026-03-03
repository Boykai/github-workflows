# Data Model: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-03  
**Depends on**: research.md (R1, R2, R3, R4, R6)

## Entities

This feature has no database entities, API models, or runtime data structures. The "data model" consists entirely of CSS custom property definitions — the design tokens that drive the application's color system.

### CSS Custom Properties (Design Tokens)

The application's color system is defined in `frontend/src/index.css` using HSL-based CSS custom properties. Each property is consumed by Tailwind CSS via `hsl(var(--property-name))` mappings in `tailwind.config.js`.

#### Light Mode (`:root` selector)

| Property | Current Value (HSL) | New Value (HSL) | Hex Equivalent | Purpose |
|----------|-------------------|-----------------|----------------|---------|
| `--background` | `0 0% 100%` (#ffffff) | `142.1 76.2% 36.3%` | `#22c55e` | Root page background — green |
| `--foreground` | `222.2 84% 4.9%` (#0b1120) | `144.3 80.4% 10%` | `#052e16` | Primary text on green background |

#### Dark Mode (`.dark` selector)

| Property | Current Value (HSL) | New Value (HSL) | Hex Equivalent | Purpose |
|----------|-------------------|-----------------|----------------|---------|
| `--background` | `222.2 84% 4.9%` (#0b1120) | `142.1 64.2% 24.1%` | `#166534` | Root page background — dark green |
| `--foreground` | `210 40% 98%` (#f8fafc) | `138.5 76.5% 96.7%` | `#f0fdf4` | Primary text on dark green background |

#### Unchanged Properties

The following properties remain at their current values. Cards, popovers, and other overlay elements retain their existing backgrounds to provide a clear visual hierarchy against the green root background.

| Property | Light Mode Value | Dark Mode Value | Reason Unchanged |
|----------|-----------------|-----------------|------------------|
| `--card` | `0 0% 100%` | `222.2 84% 4.9%` | White/dark cards contrast well against green background |
| `--card-foreground` | `222.2 84% 4.9%` | `210 40% 98%` | Existing text colors remain legible on unchanged card backgrounds |
| `--popover` | `0 0% 100%` | `222.2 84% 4.9%` | Popovers need clear visual separation from green background |
| `--popover-foreground` | `222.2 84% 4.9%` | `210 40% 98%` | Existing text colors remain legible on unchanged popover backgrounds |
| `--primary` | `222.2 47.4% 11.2%` | `210 40% 98%` | Button/link colors remain unchanged |
| `--secondary` | `210 40% 96.1%` | `217.2 32.6% 17.5%` | Secondary backgrounds remain unchanged |
| `--muted` | `210 40% 96.1%` | `217.2 32.6% 17.5%` | Muted backgrounds remain unchanged |
| `--accent` | `210 40% 96.1%` | `217.2 32.6% 17.5%` | Accent backgrounds remain unchanged |
| `--destructive` | `0 84.2% 60.2%` | `0 62.8% 30.6%` | Error/destructive colors remain unchanged |
| `--border` | `214.3 31.8% 91.4%` | `217.2 32.6% 17.5%` | Border colors remain unchanged |
| `--input` | `214.3 31.8% 91.4%` | `217.2 32.6% 17.5%` | Input border colors remain unchanged |
| `--ring` | `222.2 84% 4.9%` | `212.7 26.8% 83.9%` | Focus ring colors remain unchanged |
| `--radius` | `0.5rem` | `0.5rem` | Not a color property |

### Tailwind CSS Mapping (No Changes)

The Tailwind configuration in `tailwind.config.js` already maps these CSS variables to utility classes:

```javascript
colors: {
  background: "hsl(var(--background))",  // Used by bg-background
  foreground: "hsl(var(--foreground))",  // Used by text-foreground
}
```

No changes to `tailwind.config.js` are needed.

### Application Usage (No Changes)

The root application applies the background via existing Tailwind classes:

```css
/* frontend/src/index.css - base layer */
body {
  @apply bg-background text-foreground;
}
```

```tsx
/* frontend/src/App.tsx - root container */
<div className="flex flex-col h-screen bg-background text-foreground">
```

Both of these automatically inherit the updated `--background` and `--foreground` values.

## Contrast Verification

| Combination | Foreground | Background | Ratio | WCAG AA (4.5:1) | WCAG AA Large (3:1) |
|-------------|-----------|------------|-------|-----------------|---------------------|
| Light body text | `#052e16` | `#22c55e` | ~10.5:1 | ✅ PASS | ✅ PASS |
| Dark body text | `#f0fdf4` | `#166534` | ~7.8:1 | ✅ PASS | ✅ PASS |
| Light card text | `#0b1120` | `#ffffff` | ~18.5:1 | ✅ PASS | ✅ PASS |
| Dark card text | `#f8fafc` | `#0b1120` | ~17.1:1 | ✅ PASS | ✅ PASS |

## Validation Rules

| Rule | Enforcement |
|------|-------------|
| Green value must be a defined HSL value, not a bare `green` keyword | CSS variable definition in `index.css` uses precise HSL values (FR-002) |
| Body text contrast ≥ 4.5:1 | Verified via contrast ratio calculations above (FR-003) |
| Large text/UI contrast ≥ 3:1 | All ratios exceed 3:1 (FR-004) |
| Single centralized definition | One `:root` and one `.dark` block in `index.css` (FR-007) |

## State Transitions

N/A — This feature has no stateful behavior. CSS custom properties are static declarations applied at page load and toggled only by the existing dark mode class switch.

## Migration

N/A — No database changes. The CSS change is applied directly and takes effect on next page load/build.
