# Research: Update App Title to "Happy Place"

**Feature**: 005-update-app-title | **Date**: 2026-02-20

## Research Summary

This feature requires no external research. All unknowns from the Technical Context have been resolved through direct codebase inspection.

## Findings

### 1. Current Title Locations

- **Decision**: The title "Agent Projects" appears in 15+ files across frontend, backend, E2E tests, configuration, and documentation.
- **Rationale**: Codebase grep confirmed all locations. No dynamic title construction or environment-variable-based titles exist.
- **Alternatives considered**: None — direct codebase inspection is sufficient.

### 2. Replacement Strategy

- **Decision**: Direct string replacement of "Agent Projects" → "Happy Place" in all files.
- **Rationale**: The title is hardcoded as a literal string everywhere. No templating, i18n, or config-driven title system exists.
- **Alternatives considered**: Centralizing the title in a config constant was considered but rejected per Constitution Principle V (Simplicity/YAGNI) — the current direct approach is simpler and the feature spec does not require centralization.

### 3. Test Impact

- **Decision**: Update all E2E test assertions that reference the old title.
- **Rationale**: Playwright E2E tests (auth.spec.ts, ui.spec.ts, integration.spec.ts) assert on the title text. These must be updated to avoid test failures.
- **Alternatives considered**: None — test assertions must match the actual UI text.
