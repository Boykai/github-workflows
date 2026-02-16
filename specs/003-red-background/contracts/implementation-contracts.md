# Implementation Contracts: Red Background Color

**Branch**: `copilot/apply-red-background-color-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](../spec.md)

## Overview

This document defines the precise file modifications required to implement the red background color feature. Each contract specifies exact line numbers, changes, and verification criteria.

---

## Contract 1: Light Mode Background Color

**File**: `frontend/src/index.css`  
**Line**: 9  
**Type**: Modification  
**Priority**: P1 (Critical)

### Current State

```css
  --color-bg-secondary: #f6f8fa;
```

### New State

```css
  --color-bg-secondary: #ff0000;
```

### Rationale

- Changes light mode page background from light gray to red
- Fulfills FR-001: Apply red background color to main application container
- Pure red (#ff0000) provides maximum visual branding impact per research decision

### Verification Criteria

1. ✅ Line 9 contains `--color-bg-secondary: #ff0000;`
2. ✅ Hex value uses lowercase letters per codebase convention
3. ✅ CSS syntax is valid (property: value;)
4. ✅ Light mode shows red background when application loads

### Side Effects

- All elements using `var(--color-bg-secondary)` will become red
- May affect buttons, panels, and other surfaces using this variable
- Text contrast may become insufficient (addressed in Contract 3)

---

## Contract 2: Dark Mode Background Color

**File**: `frontend/src/index.css`  
**Line**: 25  
**Type**: Modification  
**Priority**: P1 (Critical)

### Current State

```css
  --color-bg-secondary: #161b22;
```

### New State

```css
  --color-bg-secondary: #8b0000;
```

### Rationale

- Changes dark mode page background from dark gray to dark red
- Fulfills FR-005: Apply red background in both light and dark themes
- Dark red (#8b0000) maintains red identity while appropriate for low-light viewing
- Prevents eye strain that would occur with bright red in dark mode

### Verification Criteria

1. ✅ Line 25 contains `--color-bg-secondary: #8b0000;`
2. ✅ Hex value uses lowercase letters per codebase convention
3. ✅ CSS syntax is valid (property: value;)
4. ✅ Dark mode shows dark red background when theme is toggled
5. ✅ Background color transitions smoothly when switching themes

### Side Effects

- All elements using `var(--color-bg-secondary)` in dark mode will become dark red
- Maintains consistency with light mode red branding

---

## Contract 3: Light Mode Text Color for Contrast

**File**: `frontend/src/index.css`  
**Line**: 11  
**Type**: Modification  
**Priority**: P1 (Critical)

### Current State

```css
  --color-text: #24292f;
```

### New State

```css
  --color-text: #ffffff;
```

### Rationale

- Changes light mode text from dark gray to white
- Fulfills FR-003: Maintain sufficient contrast for text on red background
- White text (#ffffff) on red background (#ff0000) provides ~4.0:1 contrast
- Improves readability on red background (dark text would be invisible)

### Verification Criteria

1. ✅ Line 11 contains `--color-text: #ffffff;`
2. ✅ Hex value uses lowercase letters per codebase convention
3. ✅ Text is readable on red background in light mode
4. ✅ Contrast ratio meets or approaches WCAG AA standard (4.5:1 for normal text)
5. ✅ All text throughout application updates to white

### Side Effects

- All text using `var(--color-text)` becomes white
- May affect text on non-red surfaces if components use `--color-text`
- Improves overall readability against red background

### Accessibility Note

White text on red (#ffffff on #ff0000) provides ~4.0:1 contrast ratio, which is slightly below WCAG AA standard for normal text (4.5:1) but acceptable for large text (3:1). May need to increase font-weight or font-size for some text if readability is insufficient during testing.

---

## Contract 4: Light Mode Secondary Text Color (Optional)

**File**: `frontend/src/index.css`  
**Line**: 13  
**Type**: Modification  
**Priority**: P2 (Optional - verify during testing)

### Current State

```css
  --color-text-secondary: #57606a;
```

### Potential New State

```css
  --color-text-secondary: #f0f0f0;
```

### Rationale

- Secondary text (medium gray) may not have sufficient contrast on red background
- Light gray (#f0f0f0) provides better readability while maintaining hierarchy
- May be needed depending on actual usage of secondary text in application

### Verification Criteria

1. ✅ Check if secondary text is readable during manual testing
2. ✅ If not readable, update line 13 to light gray (#f0f0f0)
3. ✅ Verify visual hierarchy is maintained (secondary text slightly less prominent than primary)

### Implementation Decision

**DECISION POINT**: Only implement this change if manual testing reveals secondary text is unreadable. If current secondary text color is sufficient, leave unchanged.

---

## Cross-Cutting Contract 1: Accessibility Verification

**Type**: Manual Testing  
**Priority**: P1 (Critical)

### Requirements

Per FR-003, verify WCAG AA compliance for all text and UI elements on red background.

### Test Cases

1. **Contrast Ratio Testing**
   - Test: White text (#ffffff) on red background (#ff0000)
   - Expected: ~4.0:1 contrast (acceptable for large text, marginal for normal text)
   - Tool: WebAIM Contrast Checker, Chrome DevTools Accessibility Panel

2. **Normal Text Readability**
   - Test: Read paragraph text in light mode on red background
   - Expected: Text is clearly readable without eye strain
   - Action: If not sufficient, increase font-weight or font-size

3. **Large Text Readability**
   - Test: Read headings and large text elements
   - Expected: Excellent readability (meets 3:1 standard)

4. **Dark Mode Contrast**
   - Test: Text on dark red background (#8b0000)
   - Expected: Good contrast (light text on dark red)

5. **Interactive Element Visibility**
   - Test: Buttons, inputs, links on red background
   - Expected: Clearly distinguishable and usable

### Verification Criteria

1. ✅ All text meets minimum WCAG AA contrast (4.5:1 for normal, 3:1 for large)
2. ✅ No accessibility warnings in automated tools (axe DevTools)
3. ✅ Manual reading test confirms comfort and clarity
4. ✅ Color blindness simulation shows adequate contrast

---

## Cross-Cutting Contract 2: Consistency Verification

**Type**: Manual Testing  
**Priority**: P1 (Critical)

### Requirements

Per FR-002, verify red background appears consistently across all primary screens.

### Test Cases

1. **Initial Page Load**
   - Test: Open application in browser
   - Expected: Red background visible immediately in light mode
   - Expected: Dark red background visible in dark mode

2. **Page Navigation**
   - Test: Navigate to different sections/pages
   - Expected: Red background persists across all screens
   - Expected: No flashing or color changes during navigation

3. **Theme Toggle**
   - Test: Switch between light and dark modes
   - Expected: Red background maintains in both themes (color adjusts)
   - Expected: Smooth transition without jarring color changes

4. **Component Backgrounds**
   - Test: Verify UI components (buttons, panels, cards)
   - Expected: Components maintain visual hierarchy and usability
   - Expected: Components using `--color-bg-secondary` become red (acceptable)

5. **Modal/Overlay Behavior**
   - Test: Open modals and overlays
   - Expected: Modals maintain distinct backgrounds (not red)
   - Expected: Clear visual separation from page background

### Verification Criteria

1. ✅ Red background visible on all primary screens (100% consistency)
2. ✅ Background color matches expected values (#ff0000 or #8b0000)
3. ✅ No visual inconsistencies or color variations
4. ✅ Theme switching maintains red background appropriately

---

## Cross-Cutting Contract 3: Component Usability

**Type**: Manual Testing  
**Priority**: P2 (Important)

### Requirements

Per FR-004, verify interactive elements remain usable on red background.

### Test Cases

1. **Button Visibility**
   - Test: Click all button types (primary, secondary, danger, etc.)
   - Expected: Buttons clearly visible and distinguishable
   - Expected: Hover/active states work correctly

2. **Input Field Usability**
   - Test: Type in text inputs, textareas
   - Expected: Input fields have clear borders and backgrounds
   - Expected: Typed text is readable

3. **Chat Interface**
   - Test: Send and receive chat messages
   - Expected: Chat bubbles distinguishable from background
   - Expected: Message text is readable

4. **Navigation Elements**
   - Test: Use navigation menus, tabs, links
   - Expected: Navigation clear and usable
   - Expected: Active/selected states visible

### Verification Criteria

1. ✅ All interactive elements respond to user actions
2. ✅ Visual feedback (hover, focus, active states) clearly visible
3. ✅ No confusion about clickable vs non-clickable elements
4. ✅ Overall UX remains smooth and intuitive

---

## Implementation Summary

### Mandatory Changes

| File | Line | Change | Priority |
|------|------|--------|----------|
| `frontend/src/index.css` | 9 | `--color-bg-secondary: #ff0000;` | P1 |
| `frontend/src/index.css` | 25 | `--color-bg-secondary: #8b0000;` | P1 |
| `frontend/src/index.css` | 11 | `--color-text: #ffffff;` | P1 |

### Optional Changes (Test-Dependent)

| File | Line | Change | Condition |
|------|------|--------|-----------|
| `frontend/src/index.css` | 13 | `--color-text-secondary: #f0f0f0;` | If secondary text unreadable |

### Total LOC Changes

- **Minimum**: 3 lines modified
- **Maximum**: 4 lines modified (if secondary text needs adjustment)
- **Files Affected**: 1 file (`frontend/src/index.css`)

### Testing Checklist

- [ ] Red background visible in light mode (#ff0000)
- [ ] Dark red background visible in dark mode (#8b0000)
- [ ] Text readable and meets contrast requirements
- [ ] All primary screens show consistent red background
- [ ] Interactive elements remain usable
- [ ] Theme switching works correctly
- [ ] No accessibility warnings from automated tools
- [ ] Manual testing confirms acceptable UX

---

## Rollback Plan

If implementation causes issues:

1. **Immediate Rollback**: Revert changes to `index.css` (restore original values)
2. **Partial Rollback**: Keep dark mode change, revert light mode if light mode has issues
3. **Iterative Fix**: Adjust specific components if overall approach is sound but specific elements problematic

### Original Values (for rollback)

```css
/* Light mode */
--color-bg-secondary: #f6f8fa;
--color-text: #24292f;

/* Dark mode */
--color-bg-secondary: #161b22;
```

---

## Notes

- This is a minimal-change implementation: 3-4 lines in 1 file
- Changes leverage existing CSS custom property system
- No component-level changes required (CSS cascade handles propagation)
- Manual testing is primary verification method (visual feature)
- Changes are reversible with simple git revert
