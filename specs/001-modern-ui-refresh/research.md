# Research: Modern UI Refresh

## Technology Choices

### CSS Framework
- **Decision**: Tailwind CSS
- **Rationale**: Provides utility-first CSS for rapid UI development, highly customizable, and integrates perfectly with headless UI libraries. It allows us to easily implement the "developer-focused & sleek" aesthetic.
- **Alternatives considered**: CSS Modules (too much boilerplate, harder to maintain global design system), Styled Components (runtime overhead, less ecosystem momentum).

### UI Component Library
- **Decision**: Shadcn UI (built on Radix UI primitives)
- **Rationale**: Provides accessible, unstyled components that we can fully customize with Tailwind CSS. It's not a traditional dependency; components are copied into the project, allowing full control over the markup and styles to achieve a bespoke look.
- **Alternatives considered**: Headless UI (less comprehensive than Radix), Material UI / Chakra UI (too generic, hard to customize to our specific aesthetic, "AI vibe coded" look).

### Icons
- **Decision**: Lucide React
- **Rationale**: Standard icon set used by Shadcn UI, clean, modern, and consistent look.
- **Alternatives considered**: Heroicons, FontAwesome.

### Theming Strategy
- **Decision**: CSS Variables with Tailwind CSS
- **Rationale**: Allows for easy implementation of light/dark modes and dynamic theming without needing to recompile CSS or use complex React context providers for every style change.
- **Alternatives considered**: Tailwind's `dark:` class strategy (less flexible for complex, multi-layered theming).
