# API Contracts: Add Brown Background Color to App

**Feature**: `010-brown-background` | **Date**: 2026-02-22

> This feature introduces **no API changes**. It is a CSS-only modification to frontend design tokens (CSS custom property values in `index.css`).

## No New Endpoints

No backend changes are required. The brown background color is applied purely through CSS custom properties in the frontend.

## No Modified Endpoints

All existing API endpoints, request/response shapes, authentication, and error handling remain completely unchanged.

## CSS Contract (Design Tokens)

The only "contract" affected is the visual design token contract — the CSS custom properties that components depend on:

| Token | Type | Change |
|-------|------|--------|
| `--color-bg` | `color` | Value changed (white/dark → brown) |
| `--color-bg-secondary` | `color` | Value changed (light gray/dark → brown variant) |
| `--color-text` | `color` | Value changed in light mode (dark → light) |
| `--color-text-secondary` | `color` | Value changed in light mode (dark → light) |
| `--color-border` | `color` | Value changed in light mode (gray → brown-tinted) |

All components that reference these tokens via `var(--color-*)` will automatically adopt the new values. No component-level changes are needed.
