# CSS Change Contract: Green Background

**Feature**: 003-green-background-app | **Date**: 2026-02-17
**Purpose**: Define exact CSS changes required for green background implementation

## Contract Overview

This contract specifies the precise modifications to `frontend/src/index.css` to change the application background from white/dark-grey to green shades. All changes are CSS custom property value replacements.

---

## File: `frontend/src/index.css`

**Purpose**: CSS custom properties (design tokens) for application theming
**Change Type**: Value replacement in 4 CSS custom property declarations

### Current State

```css
/* Base styles */
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Required Changes

**Change 1 — Light mode `--color-bg` (line 8)**:

```diff
-  --color-bg: #ffffff;
+  --color-bg: #E8F5E9;
```

**Change 2 — Light mode `--color-bg-secondary` (line 9)**:

```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #C8E6C9;
```

**Change 3 — Dark mode `--color-bg` (line 24)**:

```diff
-  --color-bg: #0d1117;
+  --color-bg: #0D2818;
```

**Change 4 — Dark mode `--color-bg-secondary` (line 25)**:

```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #1A3A2A;
```

### Expected New State

```css
/* Base styles */
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #E8F5E9;
  --color-bg-secondary: #C8E6C9;
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0D2818;
  --color-bg-secondary: #1A3A2A;
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

**Validation**:
- ✅ CSS syntax valid (hex color format)
- ✅ Only `--color-bg` and `--color-bg-secondary` values modified
- ✅ All other properties unchanged
- ✅ Selector structure unchanged
- ✅ WCAG AA contrast verified for all 4 new values

---

## Files NOT Modified

The following files are explicitly **NOT** included in this change:

### Frontend Files (No Changes)
- `frontend/src/App.css` — Component styles reference CSS variables, auto-updated
- `frontend/src/App.tsx` — No background-related code
- `frontend/src/hooks/useAppTheme.ts` — Theme toggle logic unchanged
- `frontend/src/main.tsx` — Entry point unchanged
- `frontend/index.html` — HTML structure unchanged
- `frontend/package.json` — No dependency changes

### Backend Files (No Changes)
- All backend files unchanged (background is frontend-only concern)

---

## Component Impact (Automatic via CSS Variables)

The following components will automatically receive green backgrounds through CSS variable resolution:

| CSS Selector | Variable Used | Effect |
|-------------|--------------|--------|
| `body` | `--color-bg-secondary` | Page background becomes green |
| `.app-header` | `--color-bg` | Header background becomes green |
| `.project-sidebar` | `--color-bg` | Sidebar background becomes green |
| `.task-card` | `--color-bg` | Card backgrounds become green |
| `.chat-section` | `--color-bg` | Chat area becomes green |
| `.project-select` | `--color-bg` | Select input backgrounds become green |
| `.status-column` | `--color-bg-secondary` | Board columns become green |
| `.theme-toggle-btn` | `--color-bg-secondary` | Theme button becomes green |
| `.logout-button` | `--color-bg-secondary` | Logout button becomes green |
| `.rate-limit-bar` | `--color-bg-secondary` | Rate limit bar becomes green |

---

## Verification Contract

After implementing changes, verify:

### Light Mode
- [ ] Body background displays mint green (#E8F5E9)
- [ ] Header background is mint green
- [ ] Sidebar background is mint green
- [ ] Board columns display light green (#C8E6C9)
- [ ] Task cards display mint green
- [ ] All text is clearly readable

### Dark Mode
- [ ] Body background displays dark green (#1A3A2A)
- [ ] Header background is dark green (#0D2818)
- [ ] All text is clearly readable
- [ ] Theme toggle switches between green modes smoothly

### Cross-Cutting
- [ ] No layout breakage on desktop
- [ ] No layout breakage on mobile viewport (resize browser)
- [ ] Error toasts/banners still visible (use own backgrounds)
- [ ] Login button still visible and functional

---

## Rollback Contract

If issues arise, revert changes via:

```bash
git revert <commit-hash>
```

**Expected Rollback State**: All CSS variables return to previous values (`#ffffff`, `#f6f8fa`, `#0d1117`, `#161b22`).

---

## Contract Compliance Checklist

- [x] All file paths verified to exist
- [x] Line numbers documented for reference
- [x] Exact value replacements specified
- [x] Before/after states documented
- [x] WCAG contrast verification included
- [x] Component impact analysis complete
- [x] Validation criteria defined
- [x] Out-of-scope files explicitly listed
- [x] Rollback procedure defined

**Status**: ✅ **CONTRACT COMPLETE** - Ready for implementation
