# Quickstart: Add Brown Background Color to App

**Feature**: `010-brown-background` | **Date**: 2026-02-22

## Prerequisites

- Node.js with npm (frontend)
- Modern browser for visual verification

## Development Setup

```bash
# 1. Switch to the feature branch
git checkout copilot/add-brown-background-color

# 2. Frontend: install dependencies
cd frontend
npm install
```

## Implementation Steps

### Step 1: Update CSS Custom Properties

Edit `frontend/src/index.css` — the only file that needs modification:

```css
/* Light mode — update :root */
:root {
  --color-bg: #4E342E;           /* Was #ffffff — Material Brown 800 */
  --color-bg-secondary: #5D4037;  /* Was #f6f8fa — Material Brown 700 */
  --color-text: #e6edf3;          /* Was #24292f — Light text for brown bg */
  --color-text-secondary: #8b949e; /* Was #57606a — Muted light text */
  --color-border: #6D4C41;        /* Was #d0d7de — Brown 600 border */
  /* All other variables remain unchanged */
}

/* Dark mode — update html.dark-mode-active */
html.dark-mode-active {
  --color-bg: #3E2723;           /* Was #0d1117 — Material Brown 900 */
  --color-bg-secondary: #4E342E;  /* Was #161b22 — Material Brown 800 */
  /* All other dark mode variables remain unchanged */
}
```

### Step 2: Visual Verification

```bash
# Start the frontend dev server
cd frontend
npm run dev
```

Open the browser and verify:
1. ✅ Brown background visible on all pages (chat, board, settings)
2. ✅ Text is readable (light text on brown background)
3. ✅ Toggle dark mode — darker brown variant appears
4. ✅ Cards, modals, and overlays layer correctly
5. ✅ Buttons, links, and interactive elements are visible
6. ✅ Responsive — check mobile, tablet, desktop viewports

## Verification Checklist

### Visual Checks
- [ ] Light mode: Brown background (`#4E342E`) visible globally
- [ ] Dark mode: Darker brown (`#3E2723`) visible globally
- [ ] Text contrast: All text readable on brown backgrounds
- [ ] Navigation: Header and sidebar blend with brown theme
- [ ] Forms: Input fields visible and usable
- [ ] Modals/overlays: No transparency bleed-through
- [ ] Responsive: Consistent on mobile, tablet, desktop

### Cross-Browser Checks
- [ ] Chrome: Renders correctly
- [ ] Firefox: Renders correctly
- [ ] Safari: Renders correctly
- [ ] Edge: Renders correctly

### Accessibility Checks
- [ ] Primary text contrast ≥ 4.5:1 against brown background
- [ ] Secondary text contrast ≥ 4.5:1 against brown background
- [ ] Interactive elements have visible focus indicators

## Common Pitfalls

- **Text contrast failure**: If text appears unreadable, ensure `--color-text` is set to a light value (`#e6edf3`) in both themes. The original dark text (`#24292f`) does not contrast well against brown.
- **Border visibility**: Default light-mode borders (`#d0d7de`) may not be visible against brown. Update `--color-border` to a brown-family color like `#6D4C41`.
- **Shadow visibility**: The existing `--shadow` values use rgba black, which provides depth on any background color. No changes needed.
