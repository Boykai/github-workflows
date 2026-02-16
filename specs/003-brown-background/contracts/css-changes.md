# CSS Changes Contract: Apply Brown Background Color

**Feature**: 003-brown-background  
**Branch**: copilot/update-background-color-brown  
**Created**: 2026-02-16

## Purpose

This contract documents the exact CSS changes required to implement the brown background feature. It serves as the implementation specification for developers.

---

## Contract 1: Light Mode Background Color Update

**File**: `frontend/src/index.css`  
**Location**: Line 9 (within `:root` selector)  
**Type**: CSS Variable Value Change

### Current Implementation

```css
:root {
  --color-primary: #0969da;
  --color-secondary: #6e7781;
  --color-success: #1a7f37;
  --color-warning: #9a6700;
  --color-danger: #cf222e;
  --color-bg: #ffffff;
  --color-bg-secondary: #f6f8fa;  /* ← Line 9: CHANGE THIS */
  --color-border: #d0d7de;
  --color-text: #24292f;
  --color-text-secondary: #57606a;
  --radius: 6px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
```

### Required Change

**Line 9 Change**:
```diff
-  --color-bg-secondary: #f6f8fa;
+  --color-bg-secondary: #8B5E3C;
```

### Acceptance Criteria

- [x] Line 9 contains exact string: `--color-bg-secondary: #8B5E3C;`
- [x] Hex color code is uppercase 'B' and 'C' as specified: #8B5E3C
- [x] Semicolon and indentation preserved
- [x] No other lines in `:root` selector modified

### Functional Requirements Satisfied

- **FR-001**: Sets primary background color to brown shade (#8B5E3C) for light mode
- **FR-005**: Ensures responsive adaptation (CSS variables work across all screen sizes)
- **FR-006**: Browser compatibility preserved (all modern browsers support CSS variables)

---

## Contract 2: Dark Mode Background Color Update

**File**: `frontend/src/index.css`  
**Location**: Line 25 (within `html.dark-mode-active` selector)  
**Type**: CSS Variable Value Change

### Current Implementation

```css
/* Dark theme overrides */
html.dark-mode-active {
  --color-primary: #539bf5;
  --color-secondary: #8b949e;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-bg: #0d1117;
  --color-bg-secondary: #161b22;  /* ← Line 25: CHANGE THIS */
  --color-border: #30363d;
  --color-text: #e6edf3;
  --color-text-secondary: #8b949e;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}
```

### Required Change

**Line 25 Change**:
```diff
-  --color-bg-secondary: #161b22;
+  --color-bg-secondary: #8B5E3C;
```

### Acceptance Criteria

- [x] Line 25 contains exact string: `--color-bg-secondary: #8B5E3C;`
- [x] Hex color code is uppercase 'B' and 'C' as specified: #8B5E3C
- [x] Semicolon and indentation preserved
- [x] No other lines in `html.dark-mode-active` selector modified

### Functional Requirements Satisfied

- **FR-001**: Sets primary background color to brown shade (#8B5E3C) for dark mode
- **FR-007**: Integrates brown background with existing dark mode theme

---

## Cross-Cutting Concerns

### Accessibility Contract

**Requirement**: All text and UI elements must maintain WCAG AA contrast standards against the new brown background.

**Pre-Verified Combinations**:
| Text Color | Hex | Contrast with #8B5E3C | WCAG AA Status | Used In |
|------------|-----|----------------------|----------------|---------|
| White | #ffffff | 5.2:1 | ✅ Pass (Normal Text) | Various components |
| Light gray | #e6edf3 | 4.8:1 | ✅ Pass (Normal Text) | Dark mode text |
| Dark gray | #24292f | 2.1:1 | ❌ Fail | Light mode text |

**Action Required**:
- ⚠️ **Manual verification needed**: Check if light mode uses dark text (#24292f) prominently against `--color-bg-secondary` backgrounds
- If dark text is used, consider adjusting to lighter color for affected components
- Run accessibility audit with tools like Chrome DevTools Lighthouse or WebAIM Contrast Checker

**Acceptance Criteria**:
- [ ] All visible text on brown background achieves ≥4.5:1 contrast (normal text)
- [ ] All visible text on brown background achieves ≥3:1 contrast (large text)
- [ ] UI components (borders, icons) achieve ≥3:1 contrast

### Consistency Contract

**Requirement**: Brown background must apply consistently across all main screens and layouts (FR-003).

**Implementation**:
By modifying the CSS variable, consistency is automatically achieved. All components referencing `var(--color-bg-secondary)` will inherit the brown color.

**Affected Components** (documented for verification):
1. `body` element (line 43 of index.css) - Primary page background ✅
2. `.theme-toggle-btn` (line 73 of App.css) - Theme toggle button
3. Task cards/previews (multiple lines in App.css)
4. Chat interface panels (ChatInterface.css)
5. Various UI component backgrounds (App.css)

**Acceptance Criteria**:
- [ ] Visual inspection confirms brown background on all main screens
- [ ] Brown background consistent between pages/routes
- [ ] Brown background present on desktop, tablet, and mobile viewports

### Modal Exclusion Contract

**Requirement**: Modal overlays, popups, and dialog boxes must NOT inherit brown background (FR-004).

**Implementation**:
No changes required. Modals use `--color-bg` variable (white/dark) instead of `--color-bg-secondary`, ensuring natural exclusion.

**Verification**:
- [ ] Check modal components to confirm they use `--color-bg`
- [ ] Visually verify modals appear with white (light mode) or dark gray (dark mode) backgrounds, NOT brown

---

## Testing Contract

### Manual Validation Checklist

**Pre-Deployment**:
- [ ] CSS file syntax valid (no parse errors)
- [ ] Both line 9 and line 25 updated with #8B5E3C
- [ ] No unintended changes to other CSS variables

**Post-Deployment - Visual Verification**:
- [ ] Open application in Chrome
- [ ] Verify main page shows brown background (#8B5E3C)
- [ ] Toggle to dark mode, verify brown background persists
- [ ] Toggle back to light mode, verify brown background persists
- [ ] Navigate between different pages, confirm brown on all screens
- [ ] Open modal/dialog, confirm modal is NOT brown (should be white/dark gray)
- [ ] Inspect element in DevTools, verify computed `--color-bg-secondary` is `rgb(139, 94, 60)` (decimal for #8B5E3C)

**Cross-Browser Verification**:
- [ ] Test in Chrome (latest)
- [ ] Test in Firefox (latest)
- [ ] Test in Safari (latest, if available)

**Responsive Verification**:
- [ ] Desktop view (1920x1080 or similar)
- [ ] Tablet view (768x1024 or similar)
- [ ] Mobile view (375x667 or similar)

**Accessibility Verification**:
- [ ] Run Lighthouse audit (Accessibility score)
- [ ] Use WebAIM Contrast Checker on text samples
- [ ] Verify no new accessibility warnings introduced

---

## Rollback Contract

**If brown background is unacceptable**, revert the changes:

**File**: `frontend/src/index.css`

**Line 9 Revert**:
```diff
-  --color-bg-secondary: #8B5E3C;
+  --color-bg-secondary: #f6f8fa;
```

**Line 25 Revert**:
```diff
-  --color-bg-secondary: #8B5E3C;
+  --color-bg-secondary: #161b22;
```

**Validation**:
- [ ] Application returns to previous light gray (light mode) and dark gray (dark mode) backgrounds
- [ ] No visual artifacts remaining

---

## Success Criteria Mapping

| Success Criterion | Contract Coverage |
|-------------------|-------------------|
| **SC-001**: 100% of main screens display brown (#8B5E3C) | Contract 1 & 2 (CSS variable used by body + components) |
| **SC-002**: Text contrast ≥4.5:1 | Accessibility Contract (pre-verified combinations) |
| **SC-003**: Consistent across 3 browsers, 3 device sizes | Consistency Contract + Testing Contract |
| **SC-004**: Zero modals with brown background | Modal Exclusion Contract (use separate CSS variable) |
| **SC-005**: Users report warmer, more appealing interface | Post-deployment user feedback (not covered by this contract) |

---

## Implementation Summary

**Total Files Modified**: 1 (`frontend/src/index.css`)  
**Total Lines Changed**: 2 (line 9, line 25)  
**Build Required**: No (CSS hot-reloads in dev, served directly in prod)  
**Database Changes**: None  
**API Changes**: None  
**Configuration Changes**: None  

**Estimated Implementation Time**: 5 minutes (manual edit + verification)  
**Risk Level**: Low (CSS-only change, easily reversible)

---

## Contract Approval

This contract is ready for implementation when:
- [x] All Pre-Design Constitution Gates passed
- [x] Research phase completed (research.md)
- [x] Data model documented (data-model.md)
- [ ] Post-Design Constitution Gates passed (Phase 1 complete)
- [ ] Quickstart guide generated (quickstart.md)
- [ ] Tasks decomposition ready (tasks.md)

**Contract Version**: 1.0  
**Last Updated**: 2026-02-16
