# Feature Specification: Western/Cowboy UI Theme Refresh

**Feature Branch**: `019-western-theme-refresh`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Complete UI style refresh implementing a Western/Cowboy theme inspired by a ranch-style reference image. Replace the default slate/blue shadcn/ui theme with a Western-inspired design system using warm cream backgrounds, dark brown text, sunset-gold/terra-cotta accents, slab-serif display font for headings, and full dark mode support."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Western Design System & Global Theming (Priority: P1)

As a user opening the application, I want to see a cohesive Western/Cowboy-themed interface with warm cream backgrounds, dark brown text, sunset-gold accents, and distinctive western-style heading typography so that the application has a unique, branded identity inspired by the ranch aesthetic.

**Why this priority**: The design system (CSS variables, font configuration, Tailwind theme) is the foundation — every other visual change depends on it. Delivering this alone transforms the entire look of the app because ~80% of components inherit from CSS custom properties.

**Independent Test**: Can be fully tested by loading the app in a browser and visually confirming: cream/parchment backgrounds, dark brown text, gold/orange accent elements, and western slab-serif headings on all major views (login, home, board, settings).

**Acceptance Scenarios**:

1. **Given** the application is loaded in light mode, **When** viewing any page, **Then** the background displays warm cream/parchment tones, text renders in dark brown, and interactive accents (buttons, focus rings, highlighted elements) display in sunset gold or saddle brown.
2. **Given** the application is loaded, **When** viewing headings (h1, h2, h3) on any page, **Then** they render in a western-style slab-serif display font distinct from the body text font.
3. **Given** the application is loaded, **When** viewing body text, labels, and standard UI elements, **Then** they render in a clean, highly readable sans-serif font.
4. **Given** the light mode theme is active, **When** inspecting any component that previously used the default slate/blue palette, **Then** it now displays the western color palette without any remnants of the old blue/slate scheme.

---

### User Story 2 - Dark Mode Western Theme (Priority: P1)

As a user who prefers dark mode, I want the Western theme to include a full dark mode variant that maintains the cowboy aesthetic with deep espresso-brown backgrounds and gold accents so that I can use the app comfortably in low-light environments without losing the themed experience.

**Why this priority**: Dark mode is an existing feature with active users. Failing to update it would break the visual consistency and leave half the experience unthemed. It must ship alongside the light mode palette.

**Independent Test**: Can be fully tested by toggling to dark mode via the existing theme switch and verifying: deep brown backgrounds (not black), warm off-white text, gold accents, and legible contrast across all views.

**Acceptance Scenarios**:

1. **Given** the user toggles to dark mode, **When** viewing any page, **Then** backgrounds display deep espresso-brown tones, text renders in warm off-white, and accents display in sunset gold.
2. **Given** dark mode is active, **When** comparing against the light mode theme, **Then** the western aesthetic (color warmth, accent color, heading font) is consistently maintained across both modes.
3. **Given** dark mode is active, **When** reading body text and UI labels, **Then** all text meets WCAG AA contrast ratio requirements (minimum 4.5:1 for normal text, 3:1 for large text).

---

### User Story 3 - Updated UI Primitives & Interactive States (Priority: P2)

As a user interacting with buttons, cards, inputs, and other UI elements, I want them to feel tactile and themed with warm shadows, gold focus highlights, and subtle press animations so that the interaction experience matches the western aesthetic and feels polished.

**Why this priority**: While the design system handles color propagation automatically, interactive states (hover, focus, active) and component-level refinements (warm shadows, accent borders, press animations) require targeted updates to complete the experience.

**Independent Test**: Can be tested by tabbing through all interactive elements to verify gold focus rings, hovering over cards and buttons to verify warm shadow/border transitions, and clicking buttons to verify press scale effect.

**Acceptance Scenarios**:

1. **Given** the user hovers over a card element (issue card, agent card, chore card), **When** the hover state activates, **Then** the card displays a warm-tinted shadow and a subtle gold border highlight.
2. **Given** the user clicks a button, **When** the active/pressed state activates, **Then** the button exhibits a subtle scale-down animation for tactile feedback.
3. **Given** the user tabs to focus an interactive element (button, input, link), **When** the focus ring appears, **Then** it displays in sunset gold rather than the previous blue/slate ring color.
4. **Given** the user focuses a text input field, **When** typing begins, **Then** the input border highlights with a gold accent color.

---

### User Story 4 - Hardcoded Color Harmonization (Priority: P2)

As a user viewing status badges, warning banners, and other elements with hardcoded colors, I want them to harmonize with the western palette so that no component feels visually out of place against the warm-toned backgrounds.

**Why this priority**: Some components use hardcoded Tailwind color classes (amber, green, yellow, red) that bypass the CSS variable system. These must be manually audited and adjusted for palette harmony while preserving their semantic meaning.

**Independent Test**: Can be tested by navigating to views containing status badges (agent cards), warning banners (rate limit, signal conflict), and sync indicators, then confirming they visually harmonize with the surrounding western-themed elements.

**Acceptance Scenarios**:

1. **Given** a warning banner is displayed (rate limit, signal conflict), **When** viewing it against the western background, **Then** it uses theme-aware warm tones (gold-tinted warnings, terra-cotta errors) rather than generic amber/yellow/red classes.
2. **Given** an agent card displays a status badge, **When** viewing the badge, **Then** it uses western-harmonized colors (e.g., gold-tint for "pending" states, terra-cotta for "deletion" states) while retaining clear semantic meaning.
3. **Given** functional status indicators (sync dots: connected, polling, offline), **When** viewing them, **Then** they retain their standard green/yellow/red semantic colors as these convey real-time connection state.

---

### User Story 5 - Layout & Structural Enhancements (Priority: P3)

As a user navigating the application, I want the header, navigation, and page layout to incorporate subtle structural refinements that reinforce the western brand identity so that the theme feels intentional and complete rather than just a color swap.

**Why this priority**: Structural polish (branded header accents, refined navigation styling, favicon update) elevates the theme from a simple re-skin to a cohesive branded experience, but these are enhancements on top of the core palette work.

**Independent Test**: Can be tested by loading the app and inspecting: the header for western branding elements (display font on app name, gold accent border), the browser tab for a themed favicon, and navigation buttons for smooth transition effects.

**Acceptance Scenarios**:

1. **Given** the application is loaded, **When** viewing the header, **Then** the application name renders in the western display font and the header includes a subtle gold accent element (e.g., bottom border or separator).
2. **Given** the application is loaded, **When** viewing the browser tab, **Then** the favicon reflects a western-themed icon rather than the default framework icon.
3. **Given** the user switches between navigation views, **When** the active view indicator changes, **Then** the transition between active and inactive states is smooth and visually consistent with the theme.

### Edge Cases

- What happens if the western display font (Google Fonts) fails to load? The system falls back to Georgia, then to the generic serif stack, maintaining readability.
- How does the theme appear on high-contrast or accessibility mode? The system defers to OS-level high-contrast overrides while maintaining the warm palette as the default.
- What happens when dark mode is toggled rapidly? The existing ThemeProvider handles class toggling; the new palette simply redefines the CSS variable values without affecting toggle mechanics.
- What happens to components that use inline styles with statusColorToCSS()? These derive colors from GitHub's project status palette and remain unchanged — they are data-driven, not theme-driven.
- How do hardcoded semantic colors (green for success, red for errors) behave on the warm backgrounds? Their tones are softened slightly for harmony (e.g., green-600 instead of green-500 on cream) while preserving semantic clarity.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST render all pages using a unified Western/Cowboy color palette with warm cream backgrounds, dark brown text, and sunset-gold/terra-cotta accents in light mode.
- **FR-002**: System MUST provide a dark mode variant using deep espresso-brown backgrounds, warm off-white text, and sunset-gold accents that maintains the western aesthetic.
- **FR-003**: System MUST apply a western-style slab-serif display font to all heading elements (h1, h2, h3) and branding text across all views.
- **FR-004**: System MUST pair the display font with a clean, readable sans-serif font for all body text, labels, and standard UI elements.
- **FR-005**: System MUST update all shadcn/ui primitive components (buttons, cards, inputs) to inherit the western palette through CSS custom properties.
- **FR-006**: System MUST update all interactive states (hover, focus, active) on buttons, cards, inputs, and links to use the western palette (gold focus rings, warm shadows, themed hover highlights).
- **FR-007**: System MUST include a subtle press animation on button click for tactile feedback.
- **FR-008**: System MUST audit and update all hardcoded Tailwind color classes (amber, yellow, green, red, blue, purple) in component files to harmonize with the western palette.
- **FR-009**: System MUST retain standard semantic colors (green/yellow/red) for functional status indicators (sync status dots, connection states) that convey real-time meaning.
- **FR-010**: System MUST maintain WCAG AA contrast compliance (4.5:1 normal text, 3:1 large text) across both light and dark modes with the new palette.
- **FR-011**: System MUST gracefully degrade typography when the display font fails to load, falling back through Georgia to a generic serif stack.
- **FR-012**: System MUST apply warm-tinted box shadows on card elements to replace the default neutral shadows.
- **FR-013**: System MUST update the application favicon to a western-themed icon.
- **FR-014**: System MUST ensure all theme changes are purely visual — no alteration to business logic, data flow, or API contracts.

### Key Entities

- **Design Token Set (Light)**: CSS custom property values defining the light mode western palette — background, foreground, primary, secondary, accent, destructive, muted, border, input, ring, and radius tokens.
- **Design Token Set (Dark)**: CSS custom property values defining the dark mode western palette — same token set as light but shifted to dark espresso/gold tones.
- **Typography Configuration**: Font family definitions mapping display headings to the slab-serif stack and body text to the sans-serif stack, including fallback chains.
- **Hardcoded Color Inventory**: Catalog of component files containing Tailwind color classes that bypass CSS variables, with disposition decisions (keep, replace, soften) for each.

## Assumptions

- The existing ThemeProvider and dark-mode class-toggle mechanism continues to work unchanged; only the CSS variable values are redefined.
- The shadcn/ui components are configured to use CSS custom properties (confirmed via components.json `cssVariables: true`), so palette changes propagate automatically to most primitives.
- Google Fonts CDN remains available for the Rye display font; web-safe fallbacks (Georgia, serif) provide adequate degradation.
- No new UI components are created — this is a re-skin of existing components and layout.
- Agent avatar/logo customization (per-agent cowboy icons) is explicitly out of scope and deferred to a separate feature (see spec 001-cowboy-saloon-ui FR-004).
- No backend, API, or business logic changes are required or permitted.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of application views (login, home, board, settings) display the western color palette in both light and dark modes with no remnants of the previous slate/blue scheme.
- **SC-002**: All heading elements across the application render in the western display font, with body text in the sans-serif font.
- **SC-003**: All text-to-background color combinations meet WCAG AA contrast ratios (4.5:1 normal text, 3:1 large text) as verified by automated accessibility testing.
- **SC-004**: All existing automated tests (unit tests, accessibility tests, end-to-end tests) continue to pass without modification after the theme refresh.
- **SC-005**: Zero hardcoded color classes remain that clash with the western palette — all have been intentionally kept (semantic) or updated (decorative/theme-level).
- **SC-006**: Users can toggle between light and dark modes with the existing control, and both modes display a consistent western aesthetic.
- **SC-007**: All interactive elements (buttons, cards, inputs, links) exhibit updated hover, focus, and active states matching the western palette (gold focus rings, warm shadows, press animation).
- **SC-008**: The application renders correctly without layout breaks across desktop and mobile viewport widths.
