# API Contracts: Add Green Background Color to App

**Feature**: 016-green-background  
**Date**: 2026-03-03

## No API Contracts Required

This feature is a CSS-only change that modifies design token values in `frontend/src/index.css`. No backend API endpoints are added, modified, or removed. No frontend API client changes are needed.

The change involves updating two CSS custom properties (`--background` and `--foreground`) in the existing `:root` and `.dark` selectors. These properties are consumed entirely within the browser's CSS rendering pipeline and do not involve any network requests or server-side logic.
