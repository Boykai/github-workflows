# Research: Update App Title to "Happy Place"

## R1: Current Title Locations

**Decision**: The current app title "Agent Projects" appears in ~20 locations across 15 files.

**Rationale**: A comprehensive codebase search identified all instances. The title appears in user-facing UI (index.html, App.tsx), backend metadata (main.py, pyproject.toml), developer tooling (.devcontainer, .env.example), documentation (README.md files), code comments, and E2E test assertions.

**Alternatives considered**: None — this is a factual audit, not a design decision.

## R2: Replacement Strategy

**Decision**: Direct string replacement of "Agent Projects" → "Happy Place" in all locations.

**Rationale**: The new title contains only standard ASCII characters and a space, so no encoding or escaping concerns. The replacement is 1:1 with no structural changes needed. All E2E tests that assert the title must also be updated.

**Alternatives considered**:
- Centralizing the title in a single config variable — rejected as over-engineering for a simple rename; would require adding a config system where none exists for this purpose.
- Partial replacement (UI only) — rejected as it would leave inconsistent branding across documentation and metadata.
