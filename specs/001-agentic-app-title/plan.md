# Implementation Plan: Replace App Title with 'agentic'

**Branch**: `001-agentic-app-title` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-agentic-app-title/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Replace all instances of the current application title "Agent Projects" with the exact string "agentic" (all lowercase) across all user-facing and developer-facing surfaces: frontend HTML title, React component headers, E2E test assertions, backend FastAPI metadata and log messages, devcontainer configuration, setup scripts, project documentation (READMEs), and pyproject.toml. This is a straightforward text replacement task requiring no architectural changes, new dependencies, or data model updates. Typography and styling remain unchanged.

## Technical Context

**Language/Version**: TypeScript 5.4, Python 3.11, HTML5
**Primary Dependencies**: React 18.3, Vite 5.4, FastAPI
**Storage**: N/A (static content changes only)
**Testing**: Vitest (unit), Playwright (E2E), pytest (backend)
**Target Platform**: Modern web browsers (Chrome, Firefox, Safari, Edge); Linux server (backend)
**Project Type**: Web (frontend React SPA + backend Python API)
**Performance Goals**: N/A (no performance impact from string changes)
**Constraints**: Must maintain existing browser title and header functionality; exact casing "agentic" (all lowercase)
**Scale/Scope**: ~10 files changed across frontend, backend, devcontainer, and documentation; no database, API, or state management changes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation (Before Phase 0)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Complete spec.md with 2 prioritized user stories (P1: Consistent App Branding, P2: Developer & Configuration References), Given-When-Then scenarios, edge cases, and clear scope (text replacement only) |
| **II. Template-Driven** | ✅ PASS | Following plan-template.md structure. All sections populated per template requirements. No custom sections added. |
| **III. Agent-Orchestrated** | ✅ PASS | Single speckit.plan agent execution. Clear input (spec.md) and outputs (plan.md, research.md, data-model.md, contracts/, quickstart.md). Handoff to speckit.tasks next. |
| **IV. Test Optionality** | ✅ PASS | No new tests required. Existing E2E test assertions must be updated to reflect new title string. No new test infrastructure needed. |
| **V. Simplicity & DRY** | ✅ PASS | Minimal complexity: direct string replacements across ~10 files. No abstractions, no new patterns. Direct implementation matches YAGNI principle. |

**Pre-Design Gate Status**: ✅ **PASSED** - All principles satisfied. No violations requiring justification.

### Post-Design Evaluation (After Phase 1)

| Principle | Status | Justification |
|-----------|--------|---------------|
| **I. Specification-First** | ✅ PASS | Design artifacts (research.md, data-model.md, contracts/) align with spec requirements. No scope expansion. |
| **II. Template-Driven** | ✅ PASS | All Phase 0-1 artifacts follow prescribed templates. No deviations introduced. |
| **III. Agent-Orchestrated** | ✅ PASS | Phase 0-1 completed by single agent. Clean handoff state achieved. Ready for speckit.tasks. |
| **IV. Test Optionality** | ✅ PASS | Design confirms no new test infrastructure needed. E2E assertion updates are maintenance, not new tests. |
| **V. Simplicity & DRY** | ✅ PASS | Final design maintains simplicity: literal string replacements only. No complexity introduced. |

**Post-Design Gate Status**: ✅ **PASSED** - Design maintains constitutional compliance. No complexity tracking required.

## Project Structure

### Documentation (this feature)

```text
specs/001-agentic-app-title/
├── spec.md              # Feature specification (completed)
├── checklists/
│   └── requirements.md  # Spec validation checklist (completed)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (generated below)
├── data-model.md        # Phase 1 output (generated below)
├── quickstart.md        # Phase 1 output (generated below)
├── contracts/           # Phase 1 output (generated below)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # HTML page title (<title> tag, line 7)
├── src/
│   ├── App.tsx          # Application headers (login h1 line 72, authenticated h1 line 89)
│   └── [other files unchanged]
├── e2e/
│   ├── auth.spec.ts     # Title/heading assertions (lines 12, 24, 38, 62, 99)
│   ├── ui.spec.ts       # Heading assertions (lines 43, 67)
│   └── integration.spec.ts  # Heading assertion (line 69)
└── package.json         # No changes required

backend/
├── src/
│   └── main.py          # FastAPI title/description (lines 85-86), log messages (lines 75, 77)
├── README.md            # Backend documentation header (line 1)
└── pyproject.toml       # Project name and description (lines 2, 4)

.devcontainer/
├── devcontainer.json    # Container name (line 2)
└── post-create.sh       # Setup message (line 7)

README.md                # Root documentation header (line 1)
```

**Structure Decision**: Web application with React frontend + Python backend. Changes span frontend presentation layer, backend metadata, developer tooling, and documentation. All changes are text-only replacements with no structural modifications.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left minimal per constitution principle V (Simplicity).
