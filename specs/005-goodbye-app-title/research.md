# Research: Update App Title to "Goodbye"

**Feature**: 005-goodbye-app-title | **Date**: 2026-02-19

---

## R1: Current Title Locations

### Decision
The app title "Agent Projects" is hardcoded in **3 source files** and **3 E2E test files**. There is no centralized configuration, manifest, or i18n system.

### Rationale
- A full-text search of the repository confirms all occurrences.
- The title appears only in frontend files — the backend never references or serves it.
- Code comments referencing "Agent Projects" (in `types/index.ts` and `services/api.ts`) are not user-facing and do not need updating per spec scope.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Introduce a centralized title constant | Out of scope per spec: "Introducing a centralized configuration system for the app title (unless one already exists)" — none exists |
| Update code comments too | Comments are not user-facing; changing them would expand scope beyond the spec |

### Source File Inventory

| File | Line(s) | Content | User-Facing? |
|------|---------|---------|-------------|
| `frontend/index.html` | 7 | `<title>Agent Projects</title>` | Yes — browser tab |
| `frontend/src/App.tsx` | 72 | `<h1>Agent Projects</h1>` (login page) | Yes — page heading |
| `frontend/src/App.tsx` | 89 | `<h1>Agent Projects</h1>` (app header) | Yes — page heading |
| `frontend/src/types/index.ts` | 1 | Comment: "TypeScript types for Agent Projects API" | No — code comment |
| `frontend/src/services/api.ts` | 1 | Comment: "API client service for Agent Projects" | No — code comment |

### E2E Test Inventory

| File | Assertions |
|------|-----------|
| `frontend/e2e/auth.spec.ts` | 5 heading assertions + 1 title assertion referencing "Agent Projects" |
| `frontend/e2e/ui.spec.ts` | 2 heading assertions referencing "Agent Projects" |
| `frontend/e2e/integration.spec.ts` | 1 heading assertion referencing "Agent Projects" |

---

## R2: Manifest and Metadata Check

### Decision
No manifest file (`manifest.json`, `site.webmanifest`) or app-name meta tag exists in the project. Only the `<title>` tag in `index.html` serves as document metadata.

### Rationale
- File search for `manifest.json`, `site.webmanifest`, and `<meta name="application-name"` returned no results.
- The `index.html` contains only standard `<meta charset>` and `<meta name="viewport">` tags.
- No PWA (Progressive Web App) configuration exists.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Create a manifest.json | Out of scope — spec only requires updating existing references |

---

## R3: Internationalization (i18n) Check

### Decision
No i18n framework or localization files exist. The title is a plain hardcoded string.

### Rationale
- No i18n packages (react-intl, i18next, etc.) found in `package.json` dependencies.
- No translation files or locale directories found in the project.
- The app title is defined inline in HTML and JSX.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Set up i18n before changing the title | Out of scope — spec explicitly lists this as an assumption that no i18n exists |

---

## R4: Functional Logic Dependencies

### Decision
No application logic, routing, or API behavior depends on the title string "Agent Projects". The change is purely cosmetic.

### Rationale
- The title string is only used in HTML `<title>` tag and `<h1>` heading elements.
- No JavaScript/TypeScript code reads `document.title` for conditional logic.
- No backend endpoint references the title.
- E2E tests assert the title for verification purposes only — they do not drive application behavior.

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| N/A | No risk identified — the title is display-only |
