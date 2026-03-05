# Quickstart: Ruby-Colored Background Theme

**Feature**: 018-ruby-background-theme  
**Date**: 2026-03-05  
**Estimated Time**: ~30 minutes

## Prerequisites

- Node.js and npm installed
- Repository cloned and on the `018-ruby-background-theme` branch
- Frontend dependencies installed (`cd frontend && npm install`)

## Implementation Steps

### Step 1: Update Light Mode Background Token (5 min)

**File**: `frontend/src/index.css`

In the `:root` scope, change the `--background` and `--foreground` tokens:

```css
:root {
    --background: 355 80% 34%;    /* Ruby #9B111E (was: 0 0% 100%) */
    --foreground: 0 0% 100%;      /* White (was: 222.2 84% 4.9%) */
    /* ... all other tokens remain unchanged ... */
}
```

### Step 2: Update Dark Mode Background Token (5 min)

**File**: `frontend/src/index.css`

In the `.dark` scope, change the `--background` and `--foreground` tokens:

```css
.dark {
    --background: 355 80% 22%;    /* Dark Ruby #6B0C15 (was: 222.2 84% 4.9%) */
    --foreground: 0 0% 98%;       /* Near-white (was: 210 40% 98%) */
    /* ... all other tokens remain unchanged ... */
}
```

### Step 3: Add CSS Fallback (2 min)

**File**: `frontend/src/index.css`

In the `body` rule, add a static fallback before the `@apply` directive:

```css
body {
    background-color: #9B111E;  /* Fallback for browsers without CSS custom property support */
    color: #FFFFFF;              /* Fallback foreground */
    @apply bg-background text-foreground;
}
```

### Step 4: Verify (10 min)

1. Start the dev server: `cd frontend && npm run dev`
2. Open the app in a browser
3. **Check light mode**: Background should be ruby red (#9B111E), text should be white
4. **Toggle to dark mode**: Background should be dark ruby (#6B0C15), text should be near-white
5. **Check components**: Cards, modals, popovers, and inputs should retain their original surface colors
6. **Check responsive**: Resize browser to mobile (375px), tablet (768px), desktop (1440px) — ruby background should fill viewport at all sizes
7. **Contrast check**: Use a tool like [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) to verify:
   - Light mode: #FFFFFF on #9B111E → 5.57:1 (passes AA)
   - Dark mode: #FAFAFA on #6B0C15 → 8.2:1 (passes AA)

## Files Changed

| File | Change |
|------|--------|
| `frontend/src/index.css` | Update `--background` and `--foreground` tokens in `:root` and `.dark` scopes; add body fallback |

## No Changes Needed

| File | Reason |
|------|--------|
| `frontend/tailwind.config.js` | Already maps `background` to `hsl(var(--background))` — picks up new value automatically |
| `frontend/src/components/ThemeProvider.tsx` | Already toggles `.dark` class — works with new token values |
| `frontend/src/App.tsx` | Already uses `bg-background text-foreground` — inherits ruby theme |

## Rollback

To revert, restore the original token values in `frontend/src/index.css`:

```css
/* :root */
--background: 0 0% 100%;
--foreground: 222.2 84% 4.9%;

/* .dark */
--background: 222.2 84% 4.9%;
--foreground: 210 40% 98%;
```

And remove the `background-color` / `color` fallback lines from the `body` rule.
