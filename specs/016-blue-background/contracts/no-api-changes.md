# API Contracts: Add Blue Background Color to App

**Feature**: 016-blue-background  
**Date**: 2026-03-03

## No API Changes

This feature is a **CSS-only change** that modifies existing CSS custom property values in `frontend/src/index.css`. No backend API endpoints are added, modified, or removed.

### Rationale

The blue background is applied entirely through the frontend theming system:
- The `--background` CSS variable is updated in `:root` and `.dark` selectors
- The existing Tailwind utility class `bg-background` (mapped to `hsl(var(--background))`) propagates the change to all components
- No server-side rendering, no API-driven theme configuration, and no backend color storage are involved

### Existing Endpoints Unaffected

The user settings API (`/api/v1/settings`) which handles theme preference (`dark`/`light`/`system`) is **not modified**. Theme toggling continues to work as before — only the color value that `--background` resolves to has changed.
