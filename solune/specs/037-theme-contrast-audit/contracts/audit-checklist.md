# Audit Checklist Contract: Frontend Theme Audit

**Feature**: `037-theme-contrast-audit` | **Date**: 2026-03-12

## Purpose

Defines the systematic audit procedure for verifying Light/Dark theme compliance across all frontend components. Each section maps to specific functional requirements from the spec.

---

## 1. Token Compliance Scan (FR-001)

**Objective**: Verify zero hardcoded color values in component and page files.

### Procedure

1. Run automated scan for hardcoded color patterns in `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/layout/`:
   - Pattern: `#[0-9a-fA-F]{3,8}` (hex colors)
   - Pattern: `rgb\(` / `rgba\(` (RGB values)
   - Pattern: `hsl\(` / `hsla\(` followed by literal values (not `var(--`)
2. For each match, classify as:
   - **Violation**: Hardcoded color that should reference a theme token
   - **Exception**: Justified hardcoded color (with documented reason)
3. Fix all violations by replacing with appropriate Celestial design-system token.

### Known Exceptions

| File | Pattern | Justification |
|------|---------|---------------|
| `AgentAvatar.tsx` | SVG fill/stroke hex values | Decorative avatar illustrations; theme-independent visual identifiers |
| `colorUtils.ts` | GitHub status color hex values | External API color data; must match GitHub's visual language |
| `IssueCard.tsx` | Dynamic `#${safeColor}` labels | GitHub API label colors; rendered with alpha transparency |
| `index.css` | `rgba()` in `@theme` shadow definitions | Shadow tokens — to be converted to theme-aware values |
| `index.css` | `rgb()` in `solar-*` utility classes | Semantic color values with explicit `.dark` overrides |

### Pass Criteria

- Zero unclassified hardcoded color violations
- All exceptions documented with justification
- All violations fixed with token references

---

## 2. Contrast Ratio Verification (FR-002, FR-003)

**Objective**: All text and UI boundaries meet WCAG 2.1 AA thresholds.

### Procedure

1. For each contrast pair defined in `data-model.md`:
   - Resolve Light-mode HSL values to RGB
   - Resolve Dark-mode HSL values to RGB
   - Compute relative luminance: `L = 0.2126 * R + 0.7152 * G + 0.0722 * B`
   - Compute contrast ratio: `(L1 + 0.05) / (L2 + 0.05)` where L1 > L2
2. Apply thresholds:
   - Normal text (< 18px, or < 14px non-bold): ≥ 4.5:1
   - Large text (≥ 18px, or ≥ 14px bold), headings, UI boundaries: ≥ 3.0:1
3. Flag all failing pairs.
4. Fix by adjusting token lightness values (prefer adjusting the foreground; preserve background hierarchy).

### Pass Criteria

- 100% of text-to-background pairs meet applicable threshold
- 100% of UI boundary-to-background pairs meet ≥ 3.0:1
- Both Light and Dark modes verified

---

## 3. Interactive State Audit (FR-004)

**Objective**: Every interactive element has distinct, contrast-compliant states.

### Procedure

For each interactive component (buttons, links, inputs, toggles, dropdowns):

1. **Default state**: Verify text/icon contrast ≥ 4.5:1 in both themes
2. **Hover state**: Verify visible change + maintained contrast in both themes
3. **Focus state**: Verify visible focus indicator (ring/border) with ≥ 3:1 contrast against surroundings in both themes
4. **Active state**: Verify pressed/activated visual feedback in both themes
5. **Disabled state**: Verify visually muted appearance + text contrast ≥ 3:1 in both themes

### Component Checklist

| Component | Default | Hover | Focus | Active | Disabled |
|-----------|---------|-------|-------|--------|----------|
| Button (all variants) | ☐ | ☐ | ☐ | ☐ | ☐ |
| Input | ☐ | ☐ | ☐ | N/A | ☐ |
| Link | ☐ | ☐ | ☐ | ☐ | N/A |
| Dropdown trigger | ☐ | ☐ | ☐ | ☐ | ☐ |
| Toggle/Switch | ☐ | ☐ | ☐ | ☐ | ☐ |
| Sidebar nav items | ☐ | ☐ | ☐ | ☐ | N/A |
| Theme toggle button | ☐ | ☐ | ☐ | ☐ | N/A |
| Voice input button | ☐ | ☐ | ☐ | ☐ | ☐ |

### Pass Criteria

- All interactive elements have 5 verifiable states (or N/A justified)
- No state produces a contrast violation
- Focus indicators are visible in both themes

---

## 4. Component Variant Consistency (FR-005)

**Objective**: All component variants render consistently with the style guide in both themes.

### Procedure

For each component variant listed in `data-model.md`:

1. Render in Light mode — verify token assignments match style guide
2. Render in Dark mode — verify token assignments match style guide
3. Compare cross-theme: surface colors, borders, shadows, typography all use correct token mappings
4. Flag visual inconsistencies

### Component Categories

| Category | Components to Audit |
|----------|-------------------|
| Base UI | Button, Card, Input, Tooltip, ConfirmationDialog |
| Chips/Badges | solar-chip (7 variants), priority badges, sync status |
| Navigation | Sidebar, TopBar, Breadcrumb |
| Overlays | Modals, Popovers, Dropdowns, Notifications |
| Content | Chat messages, Pipeline cards, Agent tiles, Issue cards |
| Forms | Settings inputs, Agent config forms |
| Feedback | Loaders, Error states, Empty states |

### Pass Criteria

- Zero visual inconsistencies between themes
- All variants use correct Celestial tokens

---

## 5. Theme Token Alignment (FR-006, FR-007, FR-008)

**Objective**: All tokens align with the Project Solune style guide.

### Procedure

1. Verify no Dark-mode background uses pure `#000000` (HSL `0 0% 0%`)
2. Verify no Light-mode background uses harsh pure `#FFFFFF` (HSL `0 0% 100%`)
3. Identify and remove stale/duplicate/conflicting token definitions
4. Cross-reference token names against style guide naming conventions

### Current Background Token Analysis

| Token | Light Lightness | Dark Lightness | Pure Black/White? |
|-------|----------------|----------------|-------------------|
| `--background` | 95% | 7% | ✅ Neither |
| `--card` | 97% | 11% | ✅ Neither |
| `--popover` | 96% | 9% | ✅ Neither |
| `--panel` | 95% | 11% | ✅ Neither |
| `--secondary` | 89% | 17% | ✅ Neither |
| `--muted` | 90% | 13% | ✅ Neither |
| `--input` | 93% | 15% | ✅ Neither |
| `--night` | 19% | 5% | ✅ Neither |

### Pass Criteria

- Zero pure black or pure white backgrounds
- All tokens documented in token registry
- No stale or conflicting definitions

---

## 6. Theme-Switch Stability (FR-009)

**Objective**: No FOUC, glitches, or broken layouts during theme toggle.

### Procedure

For each major page:

1. Load in Light mode — verify correct rendering
2. Toggle to Dark mode — verify no flash or layout shift
3. Toggle back to Light — verify no flash or layout shift
4. Rapid toggle 3x — verify final state is correct
5. Refresh page — verify theme persists from localStorage

### Page Checklist

| Page | Light→Dark | Dark→Light | Rapid Toggle | Persistence |
|------|-----------|-----------|-------------|-------------|
| Login | ☐ | ☐ | ☐ | ☐ |
| Projects | ☐ | ☐ | ☐ | ☐ |
| Agents Pipeline | ☐ | ☐ | ☐ | ☐ |
| Agents | ☐ | ☐ | ☐ | ☐ |
| Tools | ☐ | ☐ | ☐ | ☐ |
| Settings | ☐ | ☐ | ☐ | ☐ |
| Chores | ☐ | ☐ | ☐ | ☐ |
| Not Found | ☐ | ☐ | ☐ | ☐ |

### Pass Criteria

- Zero FOUC or layout shifts across all pages
- Theme persists correctly after refresh
- Rapid toggling produces no artifacts

---

## 7. Third-Party Component Audit (FR-010)

**Objective**: All third-party components inherit theme context.

### Procedure

1. Enumerate all third-party UI components used:
   - Radix UI: Tooltip, Slot
   - Any other external UI libraries
2. For each: render in both themes, verify Celestial token adoption
3. Check portal-rendered content inherits `.dark` class

### Pass Criteria

- All third-party components adopt active theme
- No default/mismatched library styling visible

---

## 8. Token Documentation (FR-011)

**Objective**: All new/updated tokens documented.

### Procedure

1. After all fixes are applied, diff `index.css` against baseline
2. For each new or modified token, add entry to `token-registry.md`
3. Include: token name, Light value, Dark value, usage category, change reason

### Pass Criteria

- Token registry reflects all current tokens
- Change log included for any modifications
