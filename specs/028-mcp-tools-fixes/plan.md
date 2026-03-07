# Implementation Plan: Tools Page — Fix MCP Bugs, Broken Link, Repo Name Display, Discover Button & Auto-populate MCP Name

**Branch**: `028-mcp-tools-fixes` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/028-mcp-tools-fixes/spec.md`

## Summary

Fix five targeted issues on the existing Tools page MCP section: (1) Update the broken MCP documentation link to the correct GitHub Copilot MCP docs URL, (2) Display the repository name instead of owner in the Repository display bubble with dynamic sizing, (3) Add a "Discover" button linking to the GitHub MCP Registry at `https://github.com/mcp`, (4) Auto-populate the MCP Name field from uploaded/pasted MCP definition JSON using the first key under `mcpServers`, and (5) Fix MCP definition validation to accept `command`/`args`-style configs by inferring `stdio` type when `command` is present (and `http` when `url` is present) without an explicit `type` field. All changes are scoped to existing frontend components and backend validation logic — no new files, routes, or database changes required.

## Technical Context

**Language/Version**: TypeScript ~5.9 (frontend), Python 3.13 (backend)
**Primary Dependencies**: React 19.2, TanStack Query v5.90, Tailwind CSS v4, lucide-react 0.577 (frontend); FastAPI 0.135, aiosqlite 0.22 (backend)
**Storage**: N/A — no schema changes; existing SQLite tables unchanged
**Testing**: Vitest 4 + Testing Library (frontend), pytest + pytest-asyncio (backend)
**Target Platform**: Desktop browsers (768px+ viewport); Linux server (Docker)
**Project Type**: Web application (frontend/ + backend/)
**Performance Goals**: N/A — fixes and minor UI enhancements; no new performance constraints
**Constraints**: Must not break existing MCP upload, validation, or sync flows; must maintain backward compatibility with explicit `type` field configs
**Scale/Scope**: ~3 files modified in frontend, ~1 file modified in backend; zero new files, zero new endpoints, zero migrations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1–P3), Given-When-Then acceptance scenarios, 13 functional requirements (FR-001–FR-013), 10 success criteria, edge cases, key entities |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates in `.specify/templates/` |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan → tasks → implement) |
| **IV. Test Optionality** | ✅ PASS | Tests not explicitly mandated in spec; existing tests should continue to pass. Backend validation fix should be covered by existing test infrastructure if present |
| **V. Simplicity/DRY** | ✅ PASS | All changes modify existing code in-place — no new files, no new abstractions, no new routes. Validation type-inference logic adds minimal conditional branching. Auto-populate is a simple reactive effect. Link and display fixes are single-line changes |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design changes trace directly to spec FRs (FR-001–FR-013) and success criteria (SC-001–SC-010) |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to `/speckit.tasks` for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No additional tests mandated; existing tests unaffected by in-place validation changes |
| **V. Simplicity/DRY** | ✅ PASS | Zero new files. Validation fix adds 6 lines of type inference before the existing type check. Auto-populate adds one `useEffect` watching `configContent`. Link fix is a URL string replacement. Repo display fix changes one property access. Discover button adds one `<Button>` element. No premature abstractions |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/028-mcp-tools-fixes/
├── plan.md              # This file
├── research.md          # Phase 0: Research decisions (R1–R5)
├── data-model.md        # Phase 1: No new entities — documents validation logic changes only
├── quickstart.md        # Phase 1: Developer guide for applying fixes
├── contracts/
│   ├── api.md           # Phase 1: Backend validation contract changes
│   └── components.md    # Phase 1: Frontend component behavior changes
├── checklists/
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   └── services/
│       └── tools/
│           └── service.py              # MODIFIED: Update validate_mcp_config() and _extract_endpoint_url()

frontend/
├── src/
│   ├── pages/
│   │   └── ToolsPage.tsx               # MODIFIED: Fix docs link, repo display, add Discover button
│   └── components/
│       └── tools/
│           └── UploadMcpModal.tsx       # MODIFIED: Fix validateMcpJson(), add auto-populate name logic
```

**Structure Decision**: Web application (frontend/ + backend/). All changes are in-place modifications to existing files from the 027-mcp-tools-page feature. No new files, directories, or architectural changes needed.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

| Decision | Rationale | Alternative Considered |
|----------|-----------|----------------------|
| In-place validation fix (add type inference) | Minimal change — 6 lines of conditional logic before existing type check | Creating a separate `inferMcpType()` utility (rejected: over-abstraction for 3 conditions) |
| `useEffect` for auto-populate | React-idiomatic reactive approach that triggers on `configContent` change | `onChange` handler composition (rejected: more complex, harder to maintain, would require passing setter into handlers) |
| Direct property access fix for repo name | Simplest possible fix — change `repo.owner` → `repo.name` in one location | Creating a helper function (rejected: YAGNI for a single usage) |
