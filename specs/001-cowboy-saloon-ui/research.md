# Research Notes: Cowboy Saloon UI

## UI Theming Architecture
- **Decision:** Use Tailwind CSS variables based on shadcn/ui.
- **Rationale:** The project already utilizes Tailwind CSS with CSS custom properties (`--background`, `--primary`, etc.) defined in `frontend/src/index.css`. We will redefine these properties for `:root` (light mode) and `.dark` (dark mode) using western-style hue/saturation/lightness values (e.g., warm rustic browns, gold accents, faded parchment backgrounds). The manual theme toggle handles switching between standard and dark modes via a preexisting `ThemeProvider`.
- **Alternatives considered:** Writing custom SCSS classes per component. Rejected as it would fragment the styling architecture and violate DRY.

## Dynamic Agent Avatars
- **Decision:** Implement frontend mapping of agent distinct `slug` to western-themed SVG logos/components.
- **Rationale:** The agents list is fetched dynamically (`/workflow/agents`), returning objects containing a `slug`. Mapping the avatar visually on the frontend avoids unnecessary backend data alterations, keeping UI logic separated from API definitions. We will provide 3-4 custom inline SVGs (or asset imports) showcasing stylized generic local "cowboys" mapped to the existing standard agent slugs (e.g., `code-reviewer`, etc.) and a generic fallback cowboy logo.
- **Alternatives considered:** Updating backend database tables to include specific asset paths. Rejected since this strictly implements UX enhancements.

## Font Fallbacks and A11y Modes
- **Decision:** Employ standard web-safe fallback fonts in `tailwind.config.js` (`fontFamily` setting) and depend on OS high-contrast overrides.
- **Rationale:** Aligns with standard best practices (e.g., using `serif`, `Georgia` for a rustic feel, then falling back to `sans-serif`) requiring minimal code while ensuring 100% usability. The existing `ThemeProvider` is built around `.dark` class semantics which natively supports high contrast browser settings.
- **Alternatives considered:** Attempting to force-load local font files - rejected due to network performance considerations and clarification instructions recommending web-safe fonts.

## Component Animations
- **Decision:** Use Tailwind's pseudo-class utility variants (`hover:`, `active:`, `focus:`) to apply bouncy scaling or color shifts.
- **Rationale:** Aligns with the current application style, leveraging utility classes avoids creating bloat. Incorporating `transition-transform duration-200 hover:scale-105 active:scale-95` on interactive elements provides the requested dynamic and responsive interaction.
