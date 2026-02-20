# Research: Update App Title to "Ready Set Go"

**Feature**: 007-app-title-ready-set-go | **Date**: 2026-02-20

---

## R1: Current Title Location Inventory

### Decision
The current app title "Agent Projects" appears in exactly 25 occurrences across 15 files. All occurrences are simple string literals — no dynamic construction, interpolation, or constant references.

### Rationale
A comprehensive `grep -rn "Agent Projects"` across the repository (excluding `node_modules/`, `.git/`, and `specs/`) confirms every location. The title is always used as-is — never split, concatenated, or derived from a variable. This means a direct string replacement is safe with no risk of breaking logic.

### File Inventory

| Category | File | Line(s) | Context |
|----------|------|---------|---------|
| **Frontend - HTML** | `frontend/index.html` | 7 | `<title>` tag |
| **Frontend - React** | `frontend/src/App.tsx` | 72, 89 | `<h1>` headers (unauthenticated + authenticated views) |
| **Frontend - Docstrings** | `frontend/src/services/api.ts` | 2 | Module docstring comment |
| **Frontend - Docstrings** | `frontend/src/types/index.ts` | 2 | Module docstring comment |
| **Frontend - E2E Tests** | `frontend/e2e/auth.spec.ts` | 12, 24, 38, 62, 99 | `toContainText` / `toHaveTitle` assertions |
| **Frontend - E2E Tests** | `frontend/e2e/ui.spec.ts` | 43, 67 | `toContainText` assertions |
| **Frontend - E2E Tests** | `frontend/e2e/integration.spec.ts` | 69 | `toContainText` assertion |
| **Backend - FastAPI** | `backend/src/main.py` | 75, 77, 85, 86 | Logger messages + FastAPI `title`/`description` |
| **Backend - Metadata** | `backend/pyproject.toml` | 4 | Project description |
| **Backend - Docstrings** | `backend/tests/test_api_e2e.py` | 2 | Module docstring comment |
| **Backend - Docs** | `backend/README.md` | 1, 3 | Heading + description paragraph |
| **DevContainer** | `.devcontainer/devcontainer.json` | 2 | Container `name` field |
| **DevContainer** | `.devcontainer/post-create.sh` | 7 | Setup script echo message |
| **Config** | `.env.example` | 2 | Header comment |
| **Docs** | `README.md` | 1 | Project heading |

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Extract title to a shared constant | Over-engineering for a cosmetic change; adds indirection where none exists. The spec explicitly states this is a branding change, not an architecture change |
| Use environment variable for title | Unnecessary complexity; the title is static and should be consistent across all environments |
| Partial replacement (frontend only) | Violates FR-003 and SC-002 — all references must be updated for brand consistency |

---

## R2: Replacement Safety Analysis

### Decision
Direct string replacement of "Agent Projects" → "Ready Set Go" is safe across all 15 files with no risk of unintended side effects.

### Rationale
- **No substring conflicts**: "Agent Projects" does not appear as part of any longer identifier, URL, package name, or code symbol
- **No regex patterns**: The E2E test on line 62 of `auth.spec.ts` uses `/Agent Projects/i` as a regex — replacing with `/Ready Set Go/i` is a direct swap
- **No interpolation**: All occurrences are plain string literals or comments
- **No database/config persistence**: The title is not stored in any database or persistent config that would need migration
- **Case sensitivity**: All current occurrences use exact "Agent Projects" casing. The replacement "Ready Set Go" uses consistent title case per FR-008

### Alternatives Considered
| Alternative | Why Rejected |
|---|---|
| Automated sed replacement | Manual per-file edits are safer and verifiable; only 15 files need changes |
| Regex-based replacement | Unnecessary — all occurrences are exact string matches |
