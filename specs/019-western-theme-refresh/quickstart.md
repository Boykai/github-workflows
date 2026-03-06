# Quick Start: Western/Cowboy UI Theme Refresh

**Branch**: `019-western-theme-refresh`

## Prerequisites

- Node.js (for running the frontend dev server)
- Access to the `frontend/` directory
- No backend setup needed — this is purely visual

## Implementation Order

The implementation MUST follow this dependency order:

```
Phase 1: Design System Foundation (US1 — P1)
├── 1. index.css          → CSS custom properties (:root + .dark)
├── 2. index.html          → Add Rye font to Google Fonts link
├── 3. tailwind.config.js  → Font families, warm shadows, convenience colors
└── 4. index.css (base)    → Add h1/h2/h3 font-family rule

Phase 2: UI Primitives (US3 — P2)
├── 5. button.tsx          → Press animation + optional western variant
├── 6. card.tsx            → Warm shadow
└── 7. input.tsx           → Gold focus border

Phase 3: Dark Mode Verification (US2 — P1)
└── 8. Visual test         → Toggle dark mode, verify all tokens in .dark block

Phase 4: Hardcoded Color Audit (US4 — P2)
├── 9.  App.tsx            → SignalBannerBar amber→accent tokens
├── 10. AgentCard.tsx      → Status badge colors
├── 11. ProjectBoardPage.tsx → Warning banner colors
├── 12. 17 more files      → Per disposition inventory in research.md RT-4
└── 13. Favicon            → Replace vite.svg

Phase 5: Layout Polish (US5 — P3)
├── 14. App.tsx            → Header branding font, gold accent border
└── 15. Page headings      → Apply font-display class
```

## Getting Started

### 1. Start the dev server

```bash
cd frontend
npm install
npm run dev
```

### 2. Make the design system changes FIRST

Start with `index.css` — replacing the CSS variables transforms ~80% of the UI automatically:

```css
/* frontend/src/index.css — Replace :root block with western tokens */
:root {
  --background: 39 50% 96%;
  --foreground: 24 30% 15%;
  --card: 39 40% 97%;
  --card-foreground: 24 30% 15%;
  --popover: 39 40% 97%;
  --popover-foreground: 24 30% 15%;
  --primary: 24 50% 22%;
  --primary-foreground: 40 60% 95%;
  --secondary: 33 30% 88%;
  --secondary-foreground: 24 30% 20%;
  --muted: 35 25% 90%;
  --muted-foreground: 24 15% 45%;
  --accent: 36 80% 55%;
  --accent-foreground: 24 50% 15%;
  --destructive: 0 60% 45%;
  --destructive-foreground: 40 60% 95%;
  --border: 30 20% 80%;
  --input: 30 20% 82%;
  --ring: 36 80% 55%;
  --radius: 0.375rem;
}
```

Save and check the browser — you should see warm cream backgrounds, brown text, and gold accents immediately.

### 3. Verify existing tests still pass

```bash
npm test
```

All existing tests should pass without modification since they test behavior, not visual appearance.

### 4. Check accessibility

```bash
# jest-axe tests are included in the existing test suite
npm test -- --reporter=verbose
```

Look for any contrast violations flagged by jest-axe on the new palette.

## Key Files Reference

| File | What to change | Impact |
|------|---------------|--------|
| `frontend/src/index.css` | CSS custom properties (`:root` + `.dark`) | ~80% of UI |
| `frontend/index.html` | Google Fonts `<link>` — add Rye | Typography |
| `frontend/tailwind.config.js` | `fontFamily`, `boxShadow`, `colors` extensions | Config |
| `frontend/src/components/ui/button.tsx` | Add `active:scale-[0.97]` to base | All buttons |
| `frontend/src/components/ui/card.tsx` | `shadow-warm-sm` | All cards |
| `frontend/src/components/ui/input.tsx` | `focus:border-accent` | All inputs |
| ~20 component `.tsx` files | Hardcoded Tailwind color classes | Per audit |

## Validation Checklist

- [ ] Light mode: cream backgrounds, brown text, gold accents visible
- [ ] Dark mode: espresso backgrounds, warm white text, gold accents visible
- [ ] Headings render in Rye (western slab-serif) font
- [ ] Body text renders in Inter (sans-serif)
- [ ] Cards have warm-tinted shadows
- [ ] Buttons scale down slightly on press
- [ ] Focus rings display in gold
- [ ] Input focus shows gold border
- [ ] `npm test` passes with no failures
- [ ] No WCAG AA contrast violations in jest-axe tests
- [ ] No remnant slate/blue theme colors visible
