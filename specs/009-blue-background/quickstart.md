# Quickstart: Add Blue Background Color to App

**Feature**: `009-blue-background`  
**Date**: 2026-02-23

---

## Prerequisites

- Node.js with dependencies installed (`cd frontend && npm install`)
- A modern browser for visual verification

## Implementation Steps

### Step 1: Update CSS Custom Properties

Edit `frontend/src/index.css` and update the token values:

**Light theme (`:root`):**
```css
:root {
  --color-primary: #539BF5;
  --color-secondary: #8B949E;
  --color-success: #3FB950;
  --color-warning: #D29922;
  --color-danger: #F85149;
  --color-bg: #1A3A5C;
  --color-bg-secondary: #1E4A6E;
  --color-border: #2A5A7E;
  --color-text: #E6EDF3;
  --color-text-secondary: #8B949E;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
```

**Dark theme (`html.dark-mode-active`):**
```css
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0F2233;
  --color-bg-secondary: #152D42;
  --color-border: #1E3D54;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Step 2: Prevent White Flash (Optional but Recommended)

Add inline background color to `frontend/index.html`:

```html
<body style="background-color: #1A3A5C;">
  <div id="root"></div>
  <script type="module" src="/src/main.tsx"></script>
</body>
```

### Step 3: Verify

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in a browser.

## Verification Checklist

### Visual Verification

- [ ] Blue background is visible on all pages (chat, board, settings)
- [ ] Blue background extends to full viewport on all screen sizes
- [ ] No white flash on initial page load
- [ ] Dark mode toggle produces a deeper blue (not white/black)
- [ ] Navigation between routes maintains blue background
- [ ] Scrolling long pages shows blue background throughout

### Contrast Verification

Use a contrast checker tool (e.g., WebAIM Contrast Checker) to verify:

- [ ] `#E6EDF3` on `#1A3A5C` → ratio ≥ 4.5:1 (light theme text)
- [ ] `#8B949E` on `#1A3A5C` → ratio ≥ 3.0:1 (light theme secondary text)
- [ ] `#E6EDF3` on `#0F2233` → ratio ≥ 4.5:1 (dark theme text)

### Component Compatibility

- [ ] Header renders correctly with blue background
- [ ] Sidebar is visually distinct
- [ ] Chat messages are readable
- [ ] Modal dialogs overlay correctly
- [ ] Cards and panels have their own backgrounds
- [ ] Buttons and form inputs are clearly visible
- [ ] Status badges and colored indicators remain legible

## Troubleshooting

| Issue | Solution |
|-------|---------|
| White flash on initial load | Add `style="background-color: #1A3A5C"` to `<body>` in `index.html` |
| Text unreadable on blue | Verify `--color-text` is set to `#E6EDF3` (light color) in `:root` |
| Dark mode looks same as light | Verify `--color-bg` in `html.dark-mode-active` is `#0F2233` (darker) |
| Component backgrounds unchanged | Components using `var(--color-bg)` auto-update; check for hardcoded values |
| Border invisible on blue | Verify `--color-border` is set to `#2A5A7E` (lighter blue) |
| Build fails | Run `npm run build` to check for TypeScript errors (CSS changes shouldn't cause build failures) |
