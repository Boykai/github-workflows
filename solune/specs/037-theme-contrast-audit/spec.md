# Feature Specification: Frontend Theme Audit — Light/Dark Mode Contrast & Style Consistency

**Feature Branch**: `037-theme-contrast-audit`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "Analyze entire frontend codebase, ensure that Light/Dark theme align with app style and theme. Ensure that ALL components and elements in app have proper contrast in both Light and Dark theme for best UI UX."

## Assumptions

- The application uses the **Celestial design system** with CSS custom properties (theme tokens) as the single source of truth for all color values.
- **WCAG 2.1 AA** is the target compliance level: ≥4.5:1 contrast ratio for normal text, ≥3:1 for large text (≥18px or ≥14px bold) and UI component boundaries.
- The theming mechanism uses a root-level class or data attribute (e.g., `dark` class on `<html>`) to toggle between Light and Dark modes.
- The **Project Solune app style guide** is the authoritative reference for approved color tokens, surface elevations, and interactive-state palettes.
- Dark theme backgrounds use elevated surface colors (not pure `#000000`); Light theme backgrounds avoid harsh pure white where design language calls for softer tones.
- Third-party and component-library elements (e.g., Radix UI primitives) are expected to inherit the active theme context; any that do not are considered defects.
- The audit scope covers every component, page, and shared UI element rendered in the browser — including overlays, modals, tooltips, skeleton loaders, scrollbars, code blocks, SVG/icon fills, and all interactive states (hover, focus, active, disabled).
- Automated contrast-checking tooling (e.g., axe-core, a custom WCAG contrast script, or Storybook a11y addon) will supplement manual review to programmatically flag failing elements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Hardcoded Color Elimination (Priority: P1)

As a frontend developer, I want every color value in the codebase to reference a shared theme token so that toggling between Light and Dark modes produces correct, consistent results without any element displaying a hardcoded color that breaks in either theme.

**Why this priority**: Hardcoded colors are the root cause of most theme-related visual defects. Eliminating them is a prerequisite for all other audit goals.

**Independent Test**: Run a codebase-wide search for raw hex (`#`), `rgb(`, `rgba(`, and `hsl(` values inside component and page files. Every match must either reference a theme token or be flagged and corrected. Verify visually in both themes that no element retains an out-of-theme color.

**Acceptance Scenarios**:

1. **Given** a component file contains a hardcoded color value (e.g., `color: #333`), **When** the audit is complete, **Then** the value has been replaced with the appropriate Celestial design-system token.
2. **Given** the Dark theme is active, **When** a user views any page, **Then** no element displays a color that was only correct in Light mode (and vice versa).
3. **Given** a developer runs the automated color-token linting check, **When** the scan completes, **Then** zero hardcoded color violations are reported.

---

### User Story 2 — WCAG AA Contrast Compliance (Priority: P1)

As a user (including those with low vision), I want all text, icons, and interactive-element boundaries to meet WCAG 2.1 AA contrast ratios in both Light and Dark modes so that content is legible and controls are distinguishable.

**Why this priority**: Contrast compliance is a core accessibility requirement affecting every user; failing it renders the product unusable for a significant audience segment.

**Independent Test**: Run an automated contrast-checking tool against every page/component in both themes. All body/small text must achieve ≥4.5:1, and all large text, headings, and UI component boundaries must achieve ≥3:1. Fix any failures and re-run to confirm zero violations.

**Acceptance Scenarios**:

1. **Given** the Light theme is active, **When** an automated contrast audit runs on all pages, **Then** every text-to-background pair meets or exceeds the applicable WCAG AA ratio.
2. **Given** the Dark theme is active, **When** the same automated contrast audit runs, **Then** every text-to-background pair meets or exceeds the applicable WCAG AA ratio.
3. **Given** a UI component boundary (e.g., button border, input outline), **When** measured against its adjacent background in either theme, **Then** the contrast ratio is ≥3:1.

---

### User Story 3 — Interactive-State Styling (Priority: P1)

As a user, I want every interactive element (button, link, input, dropdown, toggle) to display visually distinct and properly contrasted hover, focus, active, and disabled states in both themes so that I always know what I can interact with and what state the element is in.

**Why this priority**: Broken or invisible interactive states directly harm usability and accessibility — users cannot tell which element has focus or whether a button is disabled.

**Independent Test**: Manually tab through a representative set of pages in each theme, verifying that every focusable element shows a visible focus indicator, hover produces a discernible change, and disabled elements are visually muted yet still meet minimum contrast.

**Acceptance Scenarios**:

1. **Given** a button in its default state in Dark mode, **When** a user hovers over it, **Then** the hover style is visually distinct and the text-to-background contrast remains ≥4.5:1.
2. **Given** an input field in Light mode, **When** the field receives keyboard focus, **Then** a visible focus ring or border change appears with ≥3:1 contrast against its surroundings.
3. **Given** a disabled button in either theme, **When** viewed by a user, **Then** the button appears visually muted (indicating non-interactivity) while the label text still maintains ≥3:1 contrast against its background.

---

### User Story 4 — Component Variant Consistency (Priority: P2)

As a UX stakeholder, I want every component variant — buttons, badges, alerts, inputs, modals, tooltips, cards, navigation, sidebars, dropdowns — to render correctly and look visually consistent with the overall app style in both Light and Dark modes so that the product feels polished and cohesive.

**Why this priority**: Inconsistent component rendering across themes undermines brand trust and visual quality, even when individual contrast ratios pass.

**Independent Test**: Render each component variant in isolation (e.g., via Storybook or a test harness) in both themes. Compare against the approved style guide. Flag any visual inconsistency — mismatched surface colors, wrong border tokens, misaligned shadows, or broken iconography.

**Acceptance Scenarios**:

1. **Given** a modal dialog rendered in Dark mode, **When** compared to the Project Solune style guide, **Then** its background, border, shadow, and typography tokens match the approved Dark-mode palette.
2. **Given** a badge component with each semantic variant (success, warning, error, info, neutral), **When** rendered in both themes, **Then** every variant uses the correct Celestial token and maintains AA-compliant contrast.
3. **Given** a tooltip appears on hover in Light mode, **When** the user views the tooltip, **Then** it uses the correct surface, border, and text tokens from the style guide.

---

### User Story 5 — Theme-Switch Stability (Priority: P2)

As a user, I want to toggle between Light and Dark mode without experiencing visual glitches, unstyled content flashes (FOUC), or broken layouts on any page so that the theme-switching experience feels seamless.

**Why this priority**: Theme-switch glitches erode user confidence in the product's quality and can temporarily render content unreadable.

**Independent Test**: On each major page, toggle the theme rapidly (3–5 times) and observe for flash of unstyled content, layout shifts, or lingering incorrect colors. Verify that every element settles into the correct theme within one animation frame (or the configured transition duration).

**Acceptance Scenarios**:

1. **Given** a user is viewing any page in Light mode, **When** they toggle to Dark mode, **Then** all elements transition to Dark-mode styling with no visible flash of unstyled content.
2. **Given** a user rapidly toggles the theme three times, **When** the toggles complete, **Then** the final theme state is correct with no residual styling artifacts.
3. **Given** an animated theme transition is configured, **When** the user toggles the theme, **Then** the transition completes smoothly within the configured duration with no layout shift.

---

### User Story 6 — Third-Party Component Theme Inheritance (Priority: P3)

As a frontend developer, I want every third-party or embedded component-library element to correctly inherit the active theme context so that no element renders with default or mismatched styles.

**Why this priority**: Third-party components that ignore the theme context create visual outliers; while less common than custom component issues, they are harder to detect without explicit audit.

**Independent Test**: Enumerate all third-party UI components used in the application (e.g., Radix primitives, external date pickers, rich-text editors). Render each in both themes and verify they adopt the Celestial token palette rather than their default library styling.

**Acceptance Scenarios**:

1. **Given** a Radix UI Dialog rendered in Dark mode, **When** inspected, **Then** its surface, overlay, and text colors all derive from Celestial theme tokens — not Radix defaults.
2. **Given** any third-party component is rendered in Light mode, **When** the theme is toggled to Dark mode, **Then** the component's styling updates to match the Dark-mode palette without manual overrides or flicker.

---

### Edge Cases

- What happens when a component uses CSS `!important` on a color property — does it still respond to theme changes?
- How does the system handle SVG icons that embed `fill` or `stroke` attributes inline rather than inheriting from CSS?
- What happens when a skeleton loader or placeholder shimmer uses hardcoded gradient colors that do not adapt to the active theme?
- How does the system handle scrollbar styling (`::-webkit-scrollbar`) in browsers that support custom scrollbar colors?
- What happens when a code block or `<pre>` element uses a syntax-highlighting theme that conflicts with the active Light/Dark mode?
- How does the system handle overlapping layers (modals, drawers, tooltips) where the stacking context creates unexpected contrast pairings?
- What happens when a user's operating system preference (`prefers-color-scheme`) conflicts with the in-app theme toggle?
- How does the system handle images or media with transparent backgrounds that look correct in one theme but wrong in the other?
- What happens when a newly added component does not yet have Dark-mode token mappings defined?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST ensure every color value in frontend component and page files references a shared Celestial design-system token — no hardcoded hex, rgb, rgba, or hsl values that bypass the theming system.
- **FR-002**: System MUST ensure all normal/body text achieves a contrast ratio of ≥4.5:1 against its background in both Light and Dark modes.
- **FR-003**: System MUST ensure all large text (≥18px or ≥14px bold), headings, and UI component boundaries achieve a contrast ratio of ≥3:1 in both Light and Dark modes.
- **FR-004**: System MUST verify and correct hover, focus, active, and disabled states on all interactive elements so each state is visually distinct and meets applicable contrast thresholds in both themes.
- **FR-005**: System MUST ensure all component variants (buttons, badges, alerts, inputs, modals, tooltips, cards, navigation elements, sidebars, dropdowns) render correctly and consistently with the Project Solune style guide in both themes.
- **FR-006**: System MUST ensure Dark-mode surface backgrounds use elevated/tinted surface tokens (not pure `#000000`) consistent with the app's design language.
- **FR-007**: System MUST ensure Light-mode backgrounds avoid harsh pure white where the design language specifies softer surface tones.
- **FR-008**: System MUST align all theme color definitions and design tokens with the established Project Solune app style guide, removing any stale, duplicate, or conflicting token definitions.
- **FR-009**: System MUST verify that toggling between Light and Dark mode does not produce visual glitches, unstyled-content flashes (FOUC), or broken layouts on any page or component.
- **FR-010**: System SHOULD audit and correct any third-party or component-library elements that fail to inherit the active theme context.
- **FR-011**: System SHOULD document any new or updated design tokens introduced during the audit (variable names, Light and Dark values) to maintain a living style reference.
- **FR-012**: System MUST ensure the theming mechanism (root class/attribute, CSS custom properties) is correctly scoped and inherited throughout the entire component tree with no isolated subtrees that escape theme control.

### Key Entities

- **Theme Token**: A named CSS custom property (e.g., `--solar-bg-primary`) that maps to different color values in Light and Dark modes. Key attributes: token name, Light-mode value, Dark-mode value, usage category (background, text, border, shadow).
- **Component Variant**: A distinct visual configuration of a UI component (e.g., button-primary, badge-warning, alert-error). Key attributes: component name, variant name, applicable states (default, hover, focus, active, disabled), theme-token assignments.
- **Contrast Pair**: A measurable relationship between a foreground element (text, icon, border) and its background surface. Key attributes: foreground token, background token, calculated contrast ratio, WCAG compliance level (AA pass/fail).
- **Theme Context Scope**: The boundary within the component tree where a specific theme applies. Key attributes: root selector, inheritance chain, any isolated subtrees or portals that require explicit theme propagation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of color values in frontend component and page files reference Celestial design-system tokens — zero hardcoded color violations detected by automated scanning.
- **SC-002**: 100% of text-to-background contrast pairs in both Light and Dark modes meet WCAG 2.1 AA thresholds (≥4.5:1 normal text, ≥3:1 large text and UI boundaries) as verified by automated contrast-checking tooling.
- **SC-003**: Every interactive element (button, link, input, toggle, dropdown) displays a visually distinct and contrast-compliant hover, focus, active, and disabled state in both themes, confirmed through manual and automated review.
- **SC-004**: All component variants render consistently with the Project Solune style guide in both Light and Dark modes, with zero visual inconsistencies flagged during review.
- **SC-005**: Theme toggling on every page completes without visual glitches, FOUC, or layout shifts — verified by toggling 3+ times on each major page.
- **SC-006**: Zero third-party or component-library elements render with default/mismatched styles when the active theme context is applied.
- **SC-007**: All new or updated design tokens introduced during the audit are documented with their token name, Light-mode value, Dark-mode value, and usage category.
- **SC-008**: No Dark-mode surface uses pure `#000000` and no Light-mode surface uses harsh pure `#FFFFFF` where the design language specifies softer alternatives.
