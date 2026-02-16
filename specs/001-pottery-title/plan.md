# Implementation Plan: Update Project Title to 'pottery'

**Branch**: `copilot/update-project-title-to-pottery-again` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-pottery-title/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Update the project title from "Welcome to Tech Connect 2026!" to "pottery" across all user-facing interfaces, documentation files, and configuration metadata. This is a cosmetic text replacement that preserves all technical package identifiers for backward compatibility. Changes target the HTML page title, README documentation, and human-readable descriptions in package.json and pyproject.toml files.

## Technical Context

**Language/Version**: TypeScript 5.4 (Frontend), Python 3.11+ (Backend)  
**Primary Dependencies**: React 18.3, Vite 5.4 (Frontend), FastAPI 0.109+ (Backend)  
**Storage**: N/A (text file changes only)  
**Testing**: Vitest, Playwright (Frontend), pytest (Backend)  
**Target Platform**: Web application (browser-based)
**Project Type**: Web application with frontend and backend  
**Performance Goals**: Text changes with zero performance impact  
**Constraints**: Must preserve package identifiers for backward compatibility  
**Scale/Scope**: 4 files to modify (1 HTML, 1 README, 2 package configs)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Evaluation

| Principle | Compliance | Notes |
|-----------|------------|-------|
| **I. Specification-First Development** | ✅ PASS | spec.md includes 3 prioritized user stories (P1: browser title, P2: documentation, P3: package metadata) with Given-When-Then scenarios. Scope clearly bounded to text changes only. |
| **II. Template-Driven Workflow** | ✅ PASS | Following canonical plan.md template. All required sections present. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | speckit.plan agent executing Phase 0-1, will hand off to speckit.tasks/speckit.implement. |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests are optional for text-only changes. E2E test exists (frontend/e2e/ui.spec.ts) that validates page title - will be updated as part of implementation. |
| **V. Simplicity and DRY** | ✅ PASS | Straightforward text replacements. No abstractions needed. YAGNI principles followed. |

**Gate Status**: ✅ **PASS** - No violations. All principles satisfied. Proceed to Phase 0.

### Post-Design Evaluation

| Principle | Compliance | Notes |
|-----------|------------|-------|
| **I. Specification-First Development** | ✅ PASS | Specification provided complete prioritized user stories. research.md, data-model.md, contracts/, and quickstart.md all align with spec requirements. No scope creep detected. |
| **II. Template-Driven Workflow** | ✅ PASS | All artifacts follow canonical templates: plan.md, research.md, data-model.md, contracts/file-changes.md, quickstart.md. No custom sections added beyond template structure. |
| **III. Agent-Orchestrated Execution** | ✅ PASS | speckit.plan completed Phase 0-1. Clear handoff to speckit.tasks (Phase 2) then speckit.implement (Phase 3). Single-responsibility maintained. |
| **IV. Test Optionality with Clarity** | ✅ PASS | Tests optional for text changes. Existing E2E test (frontend/e2e/ui.spec.ts) identified and will be updated as part of implementation to maintain test alignment. No new tests required. |
| **V. Simplicity and DRY** | ✅ PASS | Solution is maximally simple: direct text replacements in 5 files. No abstractions, no new dependencies, no premature optimization. YAGNI principles fully satisfied. |

**Gate Status**: ✅ **PASS** - All principles satisfied post-design. No violations. No complexity introduced.

**Summary**: This feature remains a straightforward text replacement task. All design artifacts (research, data model, contracts, quickstart) confirm the minimal scope and simple implementation approach. Ready to proceed to Phase 2 (tasks generation).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── index.html           # Browser page title (line 7)
├── package.json         # Package metadata (line 2: name remains unchanged)
└── src/
    ├── App.tsx          # Already references correct title
    └── components/

backend/
├── pyproject.toml       # Package metadata (line 2: name, line 4: description)
└── src/

README.md                # Project documentation (line 1: title)
```

**Structure Decision**: Web application structure with frontend and backend directories. Changes are limited to 4 files: frontend/index.html (HTML title tag), README.md (project title and references), frontend/package.json (description field only - name preserved), backend/pyproject.toml (description field only - name preserved).

## Complexity Tracking

No complexity violations to track. This is a simple text replacement feature with no abstraction, no new dependencies, and no architectural complexity.

---

## Phase Completion Summary

### ✅ Phase 0: Research & Analysis (COMPLETED)

**Artifacts Generated**:
- ✅ research.md (10 technology decisions documented)

**Key Findings**:
- Identified 5 files requiring changes: frontend/index.html, frontend/e2e/ui.spec.ts, README.md, frontend/package.json, backend/pyproject.toml
- Confirmed backward compatibility strategy (preserve package names)
- Validated no breaking changes or link dependencies
- Established lowercase "pottery" as consistent brand format

---

### ✅ Phase 1: Design & Contracts (COMPLETED)

**Artifacts Generated**:
- ✅ data-model.md (File change entities with validation rules)
- ✅ contracts/file-changes.md (5 contracts + 3 cross-cutting contracts)
- ✅ quickstart.md (10-step implementation guide with 50-minute estimate)
- ✅ Agent context updated (copilot-instructions.md)

**Design Decisions**:
- File change model with REPLACE, ADD_FIELD, UPDATE_FIELD types
- Prioritized implementation order: P1 (browser title) → P2 (docs) → P3 (package metadata)
- Comprehensive validation rules per file (JSON, TOML, HTML, Markdown syntax)
- Rollback strategy documented (simple text reversion)

---

### 🔄 Phase 2: Tasks Generation (NEXT)

**Command to Execute**: `/speckit.tasks` or `speckit.tasks` agent

**Expected Output**: `tasks.md` with dependency-ordered implementation tasks

**Input Artifacts**:
- spec.md (user stories and requirements)
- plan.md (this file - technical context and design)
- data-model.md (file change entities)
- contracts/file-changes.md (implementation contracts)

---

### 📋 Phase 3: Implementation (AFTER TASKS)

**Command to Execute**: `/speckit.implement` or `speckit.implement` agent

**Expected Outcome**:
- All 5 contracts fulfilled
- All tests passing (E2E test updated and validated)
- Browser displays "pottery" in tab title
- README updated with "pottery" branding
- Package metadata includes "pottery" descriptions
- Package names unchanged (backward compatible)

---

## Handoff Notes for Next Agent

**For `/speckit.tasks` Agent**:

1. **User Stories to Decompose**:
   - P1: Browser Tab Title Update (frontend/index.html, test update)
   - P2: Documentation Consistency (README.md)
   - P3: Package and Module Names (package.json, pyproject.toml)

2. **Implementation Order Suggested**:
   - Task Group 1: P1 changes (HTML + test) → verify in browser
   - Task Group 2: P2 changes (README) → verify markdown rendering
   - Task Group 3: P3 changes (package configs) → verify syntax validity

3. **Key Constraints**:
   - MUST preserve package identifiers (FR-005)
   - MUST use lowercase "pottery" everywhere (spec assumptions)
   - MUST maintain file formatting (FR-006)
   - MUST verify no broken links (FR-007)

4. **Verification Commands** (include in tasks):
   ```bash
   # HTML title check
   grep -n "<title>" frontend/index.html
   
   # Package name verification
   jq .name frontend/package.json
   grep "^name = " backend/pyproject.toml
   
   # E2E test
   cd frontend && npm run test:e2e
   ```

5. **Reference Documents**:
   - See `contracts/file-changes.md` for exact before/after states
   - See `quickstart.md` for detailed step-by-step instructions
   - See `data-model.md` for validation rules per file

---

## Plan Completion Status

| Artifact | Status | Location | Notes |
|----------|--------|----------|-------|
| plan.md | ✅ Complete | specs/001-pottery-title/plan.md | This file |
| research.md | ✅ Complete | specs/001-pottery-title/research.md | 10 decisions |
| data-model.md | ✅ Complete | specs/001-pottery-title/data-model.md | File change model |
| contracts/ | ✅ Complete | specs/001-pottery-title/contracts/file-changes.md | 5 contracts |
| quickstart.md | ✅ Complete | specs/001-pottery-title/quickstart.md | 10-step guide |
| Agent context | ✅ Updated | .github/agents/copilot-instructions.md | Technology stack |

**Planning Phase**: ✅ **COMPLETE** - Ready for Phase 2 (tasks generation)

**Branch**: `copilot/update-project-title-to-pottery-again`  
**PR**: #231  
**Next Command**: Execute `speckit.tasks` or `/speckit.tasks` to generate tasks.md
