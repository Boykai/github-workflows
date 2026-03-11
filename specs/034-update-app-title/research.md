# Research: Update App Title to "Hello World"

**Feature**: 034-update-app-title
**Date**: 2026-03-11
**Status**: Complete

## Research Tasks

### RT-1: Identify all user-facing "Solune" title references

**Decision**: Four files contain user-facing "Solune" title/branding text that must be updated.

**Rationale**: A comprehensive search of the entire `frontend/` directory for the string "Solune" was performed. Each occurrence was classified as either user-facing (visible to end users in the rendered application) or internal (code comments, test fixtures, functional descriptions). Only user-facing branding references are in scope per the specification assumptions.

**Findings**:

| File | Line | Context | Classification | Action |
|------|------|---------|---------------|--------|
| `frontend/index.html` | 7 | `<title>Solune</title>` | User-facing (browser tab) | **CHANGE** to "Hello World" |
| `frontend/src/layout/Sidebar.tsx` | 63 | `Solune` (sidebar branding text) | User-facing (sidebar header) | **CHANGE** to "Hello World" |
| `frontend/src/pages/LoginPage.tsx` | 45 | `Solune reframes GitHub operations...` | User-facing (login page description) | **CHANGE** "Solune" → "Hello World" |
| `frontend/src/pages/LoginPage.tsx` | 112 | `Solune` (login form heading) | User-facing (login page title) | **CHANGE** to "Hello World" |
| `frontend/src/pages/SettingsPage.tsx` | 85 | `Configure your preferences for Solune.` | User-facing (settings subtitle) | **CHANGE** "Solune" → "Hello World" |

### RT-2: Identify out-of-scope "Solune" references

**Decision**: The following references are out of scope and must NOT be changed.

**Rationale**: Per the specification assumptions, "The scope of this change is limited to user-facing title/branding text. Internal package names, code comments, and documentation references to 'Project Solune' are out of scope unless they directly affect the user-facing display."

**Out-of-scope references**:

| File | Context | Reason |
|------|---------|--------|
| `frontend/src/layout/Sidebar.tsx` | Line 2: JSDoc comment `Sidebar — vertical navigation with Solune branding...` | Code comment, not rendered |
| `frontend/src/pages/LoginPage.tsx` | Line 2: JSDoc comment `LoginPage — Solune-branded login page...` | Code comment, not rendered |
| `frontend/src/services/api.ts` | Line 550: `initiateLink(deviceName = 'Solune')` | Internal API parameter default, not displayed to user |
| `frontend/src/types/index.ts` | Line 1007: `// ============ Solune UI Redesign Types (025) ============` | Code comment |
| `frontend/src/constants.ts` | Line 60: `// ============ Solune Navigation ============` | Code comment |
| `frontend/src/constants/tooltip-content.ts` | Line 32: `Remove stale Solune-generated branches...` | Functional description (describes behavior, not branding) |
| `frontend/src/components/board/CleanUpConfirmModal.tsx` | Lines 69, 219: `Solune-generated items` | Functional description (describes asset ownership, not branding) |
| `frontend/src/pages/ProjectsPage.test.tsx` | Lines 33, 39: Test fixture data `name: 'Solune'` | Test data, not user-facing |
| `frontend/src/pages/AgentsPipelinePage.test.tsx` | Line 101: `name: 'Project Solune'` | Test data |
| `frontend/src/components/board/ProjectIssueLaunchPanel.test.tsx` | Line 70: `projectName="Solune"` | Test prop |
| `frontend/src/components/pipeline/SavedWorkflowsList.test.tsx` | Line 10: Test fixture | Test data |
| `backend/src/services/cleanup_service.py` | Multiple lines: `_is_solune_owned_pr`, `Solune-generated` | Internal logic comments and function names |
| `backend/src/services/copilot_polling/` | Multiple files: Comments referencing Solune | Internal code comments |
| `backend/tests/unit/` | Multiple test files | Test comments and descriptions |

### RT-3: Evaluate implementation approach

**Decision**: Direct inline string replacement in each file. No abstraction layer.

**Rationale**: The existing codebase uses inline string literals for all branding text. There is no centralized configuration, constants file, or i18n/localization system for the application title. Introducing one would violate Constitution Principle V (Simplicity and DRY / YAGNI) since it is not required by the specification.

**Alternatives considered**:

1. **Centralized title constant**: Create a `BRAND_NAME` constant in `constants.ts` and reference it everywhere. Rejected because: YAGNI — the spec does not require a reusable branding system, and only 4 files are affected.
2. **i18n/localization**: Add a localization framework. Rejected because: massively out of scope, not requested, and would add unnecessary complexity.
3. **Environment variable**: Make the title configurable via env vars. Rejected because: the spec explicitly states the title should be "Hello World" across all environments, not configurable.

### RT-4: Verify tagline preservation

**Decision**: Taglines ("Sun & Moon" and "Guided solar orbit") remain unchanged.

**Rationale**: Per FR-006 in the specification: "The sidebar taglines ('Sun & Moon' and 'Guided solar orbit') MUST remain unchanged unless explicitly updated as part of this feature." The login page workspace badge ("Sun & Moon Workspace") is similarly preserved as it is a tagline, not a title.

### RT-5: Cross-browser compatibility

**Decision**: No special handling needed for cross-browser compatibility.

**Rationale**: "Hello World" contains only ASCII characters with no special encoding requirements. The existing `<meta charset="UTF-8">` declaration in `index.html` is sufficient. All modern browsers render plain ASCII text identically in `<title>` tags and DOM text nodes.
