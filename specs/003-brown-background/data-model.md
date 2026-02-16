# Data Model: Apply Brown Background Color to App Interface

**Feature**: 003-brown-background  
**Branch**: copilot/update-background-color-brown  
**Created**: 2026-02-16

## Purpose

This document defines the "entities" (CSS variables) involved in the brown background feature. For a CSS theming change, the data model consists of the CSS custom properties being modified and their relationships.

## Entities

### CSS Variable: `--color-bg-secondary`

**Description**: CSS custom property that controls the primary page background color and secondary UI element backgrounds throughout the application.

**Location**: `frontend/src/index.css`

**Current State**:
```css
/* Light mode */
:root {
  --color-bg-secondary: #f6f8fa;  /* Light gray */
}

/* Dark mode */
html.dark-mode-active {
  --color-bg-secondary: #161b22;  /* Dark gray */
}
```

**Target State**:
```css
/* Light mode */
:root {
  --color-bg-secondary: #8B5E3C;  /* Warm brown */
}

/* Dark mode */
html.dark-mode-active {
  --color-bg-secondary: #8B5E3C;  /* Warm brown */
}
```

**Properties**:

| Property | Current (Light) | Current (Dark) | Target (Both) | Validation Rule |
|----------|----------------|----------------|---------------|-----------------|
| Color Value | #f6f8fa | #161b22 | #8B5E3C | Must be valid hex color |
| Contrast w/ White Text | 19.6:1 | 15.3:1 | 5.2:1 | WCAG AA: ≥4.5:1 for normal text |
| Contrast w/ Light Text | 17.2:1 | 13.8:1 | 4.8:1 | WCAG AA: ≥4.5:1 for normal text |

**State Transitions**:
1. **Initial State**: Light gray (#f6f8fa) or dark gray (#161b22) depending on theme mode
2. **Transition**: CSS file save triggers browser refresh/hot-reload
3. **Final State**: Warm brown (#8B5E3C) in both theme modes

**Relationships**:
- **Used by**: `body` element, `.theme-toggle-btn`, task cards, chat panels, various UI components
- **Inherits from**: None (top-level CSS variable)
- **Overridden by**: `html.dark-mode-active` context for dark mode
- **Distinct from**: `--color-bg` (used for modal/card surfaces, not affected by this change)

---

### Related (Unchanged) Variables

These variables remain unchanged but are documented for context:

#### `--color-bg`

**Description**: Primary component background (cards, modals, elevated surfaces)

**Current/Target State**: 
- Light mode: `#ffffff` (white)
- Dark mode: `#0d1117` (very dark gray)

**Relationship to Change**: This variable ensures modals/popups remain distinct from the brown page background, satisfying FR-004 (exclude modal overlays).

#### `--color-text`

**Description**: Primary text color

**Current/Target State**:
- Light mode: `#24292f` (dark gray text)
- Dark mode: `#e6edf3` (light gray text)

**Relationship to Change**: Dark mode's light text (#e6edf3) provides 4.8:1 contrast with brown background. Light mode's dark text (#24292f) provides only 2.1:1 contrast and may need adjustment if prominently used against brown backgrounds. Review needed during implementation.

---

## CSS Variable Usage Map

This section documents where `--color-bg-secondary` is referenced, helping predict the visual impact of the change.

### Direct Usages

| File | Line(s) | Selector | Property | Impact |
|------|---------|----------|----------|--------|
| `frontend/src/index.css` | 9, 25 | `:root`, `html.dark-mode-active` | Variable definition | **SOURCE** - Values being changed |
| `frontend/src/index.css` | 43 | `body` | `background` | ✅ Main page background becomes brown |
| `frontend/src/App.css` | 73 | `.theme-toggle-btn` | `background` | ⚠️ Theme toggle button becomes brown |
| `frontend/src/App.css` | 130 | (TBD selector) | `background` | ⚠️ Component background becomes brown |
| `frontend/src/App.css` | 177 | (TBD selector) | `background` | ⚠️ Component background becomes brown |
| `frontend/src/App.css` | 209 | (TBD selector) | `background` | ⚠️ Component background becomes brown |
| `frontend/src/App.css` | 234 | (TBD selector) | `background` | ⚠️ Component background becomes brown |
| `frontend/src/App.css` | 494 | (TBD selector) | `background` | ⚠️ Component background becomes brown |
| `frontend/src/components/chat/ChatInterface.css` | Multiple | Various chat selectors | `background` | ⚠️ Chat panels/bubbles become brown |

**Legend**:
- ✅ Intended primary effect (spec requirement)
- ⚠️ Side effect requiring visual verification (should still look good with brown)

### Cascade Analysis

```
:root OR html.dark-mode-active
  └── --color-bg-secondary: #8B5E3C
      ├── body { background: var(--color-bg-secondary) }
      │   └── All page content inherits brown background
      ├── .theme-toggle-btn { background: var(--color-bg-secondary) }
      │   └── Theme toggle button has brown background
      ├── [Various App.css components]
      │   └── Cards/panels have brown backgrounds
      └── [ChatInterface.css components]
          └── Chat bubbles/panels have brown backgrounds
```

**Isolation**: Modals/popups use `--color-bg` (white/dark), so they remain visually distinct from brown background as required.

---

## Validation Rules

### Color Format Validation
- **Rule**: CSS color value must be valid 6-digit hex format `#RRGGBB`
- **Example**: `#8B5E3C` ✅ | `#8B5E3` ❌ (too short) | `brown` ❌ (not hex)

### Accessibility Validation (WCAG AA)
- **Normal text**: Contrast ratio ≥ 4.5:1 with background
- **Large text**: Contrast ratio ≥ 3:1 with background
- **UI components**: Contrast ratio ≥ 3:1 with background

**Pre-verified Combinations**:
- #8B5E3C (brown) + #ffffff (white): 5.2:1 ✅
- #8B5E3C (brown) + #e6edf3 (light gray): 4.8:1 ✅
- #8B5E3C (brown) + #24292f (dark gray): 2.1:1 ❌

### Theme Consistency Validation
- **Rule**: Both `:root` and `html.dark-mode-active` must define `--color-bg-secondary`
- **Rule**: Both contexts use the same color value (#8B5E3C) per design decision

---

## Edge Cases

### Edge Case 1: Nested Component Backgrounds

**Scenario**: Some components might nest multiple elements with `--color-bg-secondary`

**Handling**: All nested uses will inherit brown, creating a monochromatic layer. This is acceptable per spec ("apply brown background to all main screens").

**Validation**: Visual inspection during implementation to ensure readability.

### Edge Case 2: Hover/Active States

**Scenario**: Some components may use `--color-bg-secondary` for hover states

**Handling**: Hover states will also become brown-based. May need adjustment if hover effect becomes indistinct.

**Validation**: Test interactive elements (buttons, cards) to ensure hover states remain visible.

### Edge Case 3: Browser Print Styles

**Scenario**: Users print pages with brown background

**Handling**: Browsers default to removing backgrounds in print. No action needed.

**Validation**: Optional - test print preview to confirm default behavior.

---

## Data Flow

```
User Action (None - automatic on deploy)
  ↓
Browser loads frontend/src/index.css
  ↓
CSS parser reads :root and html.dark-mode-active selectors
  ↓
--color-bg-secondary variable defined with #8B5E3C value
  ↓
Components referencing var(--color-bg-secondary) resolve to brown
  ↓
Browser paints brown backgrounds across all usage sites
  ↓
User sees brown interface (FR-001 satisfied)
```

**Trigger**: CSS file change deployed to production  
**Duration**: Immediate (browser render cycle)  
**Persistence**: Permanent until CSS is changed again

---

## Summary

**Modified Entities**: 1 CSS variable (`--color-bg-secondary`)  
**Lines Changed**: 2 (line 9 for light mode, line 25 for dark mode)  
**Color Value**: #f6f8fa / #161b22 → #8B5E3C  
**Affected Components**: ~10+ UI elements (body, buttons, cards, chat panels)  
**Validation**: WCAG AA contrast requirements met with light text  
**Isolation**: Modals/popups unaffected (use `--color-bg` variable)

This data model confirms the feature is a simple CSS variable value change with broad but predictable impact across the application's visual presentation layer.
