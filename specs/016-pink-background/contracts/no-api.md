# API Contracts: Add Pink Background Color to App

**Feature**: 016-pink-background
**Date**: 2026-03-02

## No API Contracts Required

This feature is a pure CSS styling change that modifies existing CSS custom property values in `frontend/src/index.css`. It does not introduce, modify, or depend on any API endpoints.

**Rationale**:
- The background color is applied via CSS custom properties consumed by Tailwind CSS utilities
- No backend logic, data storage, or server-side rendering is involved
- No new frontend API client methods are needed
- The change is entirely declarative (CSS variable value swap)

**Affected interfaces** (non-API):
- `frontend/src/index.css` — CSS custom property `:root { --background }` and `.dark { --background }` values
- `frontend/tailwind.config.js` — Already configured to consume `--background` (no changes needed)
