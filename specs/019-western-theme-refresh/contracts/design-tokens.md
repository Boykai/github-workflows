# Design Token Contract: Western Theme

**Version**: 1.0.0  
**Format**: CSS Custom Properties (HSL triplets)  
**Consumer**: Tailwind CSS via `hsl(var(--token))` syntax in `tailwind.config.js`

---

## Contract: CSS Custom Property Interface

### Required Tokens

Every theme (light and dark) MUST define ALL of the following CSS custom properties in the `@layer base` block of `index.css`. Omitting any token will cause visual regressions in shadcn/ui components.

```css
/* REQUIRED: Color tokens — values are space-separated HSL triplets (no commas) */
/* Format: hue saturation% lightness%  e.g., "39 50% 96%" */

:root {
  /* Backgrounds */
  --background: <hsl-triplet>;      /* Page background */
  --card: <hsl-triplet>;            /* Card/elevated surface */
  --popover: <hsl-triplet>;         /* Popover/dropdown surface */
  --muted: <hsl-triplet>;           /* Muted/subtle background */
  --secondary: <hsl-triplet>;       /* Secondary surface */

  /* Text */
  --foreground: <hsl-triplet>;           /* Primary text */
  --card-foreground: <hsl-triplet>;      /* Text on card */
  --popover-foreground: <hsl-triplet>;   /* Text on popover */
  --muted-foreground: <hsl-triplet>;     /* Secondary/muted text */
  --secondary-foreground: <hsl-triplet>; /* Text on secondary */

  /* Interactive */
  --primary: <hsl-triplet>;              /* Primary action color */
  --primary-foreground: <hsl-triplet>;   /* Text on primary */
  --accent: <hsl-triplet>;              /* Accent/highlight color */
  --accent-foreground: <hsl-triplet>;    /* Text on accent */

  /* Semantic */
  --destructive: <hsl-triplet>;          /* Destructive/error color */
  --destructive-foreground: <hsl-triplet>; /* Text on destructive */

  /* Borders & Focus */
  --border: <hsl-triplet>;   /* Default border */
  --input: <hsl-triplet>;    /* Input border */
  --ring: <hsl-triplet>;     /* Focus ring */

  /* Layout */
  --radius: <length>;        /* Border radius base value */
}
```

### Invariants

1. **Contrast**: `--foreground` on `--background` MUST have ≥4.5:1 contrast ratio (WCAG AA)
2. **Contrast**: `--primary-foreground` on `--primary` MUST have ≥4.5:1 contrast ratio
3. **Contrast**: `--muted-foreground` on `--background` MUST have ≥4.5:1 contrast ratio
4. **Contrast**: `--destructive-foreground` on `--destructive` MUST have ≥4.5:1 contrast ratio
5. **Hierarchy**: `--card` lightness MUST differ from `--background` lightness (surface elevation)
6. **Consistency**: `--card-foreground` SHOULD equal `--foreground` (same text color on all surfaces)
7. **Dark mode**: `.dark` block MUST redefine ALL tokens — no inheritance from `:root`
8. **Format**: Values MUST be space-separated HSL triplets without `hsl()` wrapper (Tailwind adds it)

---

## Contract: Tailwind Font Family Extension

### Required Font Families

```js
// tailwind.config.js → theme.extend.fontFamily
fontFamily: {
  display: [<primary-display-font>, ...fallbacks],  // Heading/branding
  sans: [<primary-body-font>, ...fallbacks],         // Body text
}
```

### Invariants

1. **Display font**: MUST be a western-style slab-serif with Google Fonts CDN availability
2. **Sans font**: MUST be a highly readable sans-serif with weights 400, 500, 600, 700
3. **Fallbacks**: Both stacks MUST include at least one web-safe fallback and a generic family
4. **Base rule**: `h1, h2, h3` elements MUST be styled with `font-family: theme('fontFamily.display')` in the CSS base layer

---

## Contract: Tailwind Box Shadow Extension

### Required Shadow Tokens

```js
// tailwind.config.js → theme.extend.boxShadow
boxShadow: {
  'warm-sm': <css-shadow-value>,   // Subtle card elevation
  'warm': <css-shadow-value>,      // Standard elevation
  'warm-md': <css-shadow-value>,   // Hover/emphasis elevation
  'warm-lg': <css-shadow-value>,   // Modal/popover elevation
}
```

### Invariants

1. **Tint**: Shadow color MUST use the `--foreground` color's RGB equivalent (warm brown)
2. **Opacity**: Shadow opacity MUST be between 0.05 and 0.15 (subtle, not heavy)
3. **Structure**: Shadow spread/blur SHOULD match Tailwind default shadow structure for consistency

---

## Contract: Component Interactive States

### Button Base Class

```
transition-transform duration-150 active:scale-[0.97]
```

- MUST apply to ALL button variants
- MUST NOT exceed `scale(0.95)` (too aggressive)
- MUST NOT be slower than `duration-200` (feels laggy)

### Card Hover

Cards (issue, agent, chore) SHOULD exhibit:
- `hover:shadow-warm-md` — elevated warm shadow
- `hover:border-accent/40` — subtle gold border glow (optional)

### Input Focus

Text inputs SHOULD exhibit:
- `focus:border-accent` — gold border on focus
- Default `ring-ring` applies via CSS variable (already gold)

---

## Consuming This Contract

```
index.css (defines tokens)
    ↓
tailwind.config.js (maps tokens to utilities)
    ↓
shadcn/ui components (consume utilities)
    ↓
Feature components (inherit from primitives)
```

Any change to token values in `index.css` automatically propagates through this chain. Hardcoded Tailwind color classes (e.g., `bg-green-500`) bypass this chain and must be managed separately per the Hardcoded Color Inventory in `data-model.md`.
