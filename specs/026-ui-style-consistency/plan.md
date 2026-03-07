# Implementation Plan: Audit & Update UI Components for Style Consistency

**Branch**: `026-ui-style-consistency` | **Date**: 2026-03-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/026-ui-style-consistency/spec.md`

## Summary

Comprehensive frontend audit and remediation of all UI components to enforce consistent use of the established design system tokens. The codebase has ~98 component files across 13,900+ lines in `frontend/src/`. The theme system (HSL CSS variables in `index.css`, Tailwind CSS v4 utility classes, CVA variants for base UI components) is architecturally sound, but ~60% of components use raw template literals instead of the `cn()` class-merging utility, 18+ files contain hardcoded Tailwind color classes instead of semantic theme tokens, and status/priority color mappings are scattered across multiple files instead of being centralized. The approach inventories all components, documents deviations in a structured audit report, remediates each component to use theme tokens and `cn()`, and verifies no visual regressions.

## Technical Context

**Language/Version**: TypeScript 5.9, React 19.2, Vite 7.3  
**Primary Dependencies**: Tailwind CSS v4 (@tailwindcss/vite), class-variance-authority (CVA) 0.7.1, clsx + tailwind-merge (via `cn()`), lucide-react 0.577, @dnd-kit, @radix-ui/react-slot  
**Storage**: N/A (frontend-only style changes; no data persistence changes)  
**Testing**: Vitest 4 + Testing Library + happy-dom (unit), Playwright 1.58 (E2E), jest-axe (a11y)  
**Target Platform**: Desktop browsers (Chrome, Firefox, Safari, Edge); responsive down to mobile viewports  
**Project Type**: Web application (frontend/ + backend/); changes limited to `frontend/` only  
**Performance Goals**: No increase in bundle size beyond trivial token centralization; no render performance regressions  
**Constraints**: No backend changes. No new features or components. No design system redesign — use existing tokens as-is. No accessibility changes beyond what results from correct token usage (e.g., improved color contrast).  
**Scale/Scope**: ~98 component files, ~13,900 LOC in `frontend/src/`. Estimated 40–50 files require remediation. 6 pages, 7 layout files, ~80 feature components across board/, chat/, settings/, agents/, chores/ directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | spec.md complete with 5 prioritized user stories (P1×3, P2×2), Given-When-Then acceptance scenarios, edge cases, scope exclusions |
| **II. Template-Driven** | ✅ PASS | All artifacts follow canonical templates; checklist/requirements.md already validated |
| **III. Agent-Orchestrated** | ✅ PASS | Sequential phase execution (specify → plan); plan hands off to /speckit.tasks for Phase 2 |
| **IV. Test Optionality** | ✅ PASS | Spec does not mandate new tests; existing test suite must pass after changes (FR-008). Visual regression verification is manual per acceptance criteria. |
| **V. Simplicity/DRY** | ✅ PASS | Approach favors centralization of existing patterns (move scattered colors to shared constants) rather than new abstractions. No new libraries. cn() adoption is applying an existing utility, not adding complexity. |

### Post-Phase 1 Re-Check

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Specification-First** | ✅ PASS | All design artifacts (research, data-model, contracts) trace to spec FRs and acceptance criteria |
| **II. Template-Driven** | ✅ PASS | plan.md, research.md, data-model.md, contracts/, quickstart.md all follow template structure |
| **III. Agent-Orchestrated** | ✅ PASS | Plan hands off to /speckit.tasks for Phase 2 task decomposition |
| **IV. Test Optionality** | ✅ PASS | No new tests mandated. Existing tests must pass (FR-008). Manual visual verification per acceptance criteria. |
| **V. Simplicity/DRY** | ✅ PASS | Centralizes scattered color mappings into constants.ts (DRY). Adopts existing cn() utility — no new patterns invented. Removes dead/deprecated components. |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/026-ui-style-consistency/
├── plan.md              # This file
├── research.md          # Phase 0: 8 research items (R1–R8)
├── data-model.md        # Phase 1: Audit entities, component inventory model, token catalog
├── quickstart.md        # Phase 1: Developer onboarding for audit & remediation workflow
├── contracts/
│   ├── style-tokens.md  # Phase 1: Design token contract (all CSS variables, expected usage)
│   └── components.md    # Phase 1: Component compliance contract (cn() usage, token rules)
├── checklists/
│   └── requirements.md  # Pre-existing: spec validation checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── index.css                           # Theme tokens (AUDITED, not changed — tokens are correct)
│   ├── constants.ts                        # MODIFIED: Centralized status/state color mappings added
│   ├── lib/utils.ts                        # EXISTING: cn() utility (no changes)
│   ├── components/
│   │   ├── ThemeProvider.tsx               # EXISTING: Theme switching (no changes)
│   │   ├── ui/
│   │   │   ├── button.tsx                  # EXISTING: Already uses cn() + CVA (compliant)
│   │   │   ├── card.tsx                    # EXISTING: Already uses cn() (compliant)
│   │   │   └── input.tsx                   # EXISTING: Already uses cn() (compliant)
│   │   ├── common/
│   │   │   └── ErrorBoundary.tsx           # MODIFIED: Replace inline style with Tailwind classes
│   │   ├── board/                          # MODIFIED: ~15 files — cn() adoption, token alignment
│   │   │   ├── IssueCard.tsx              # Key: Centralize priority colors
│   │   │   ├── IssueDetailModal.tsx       # Key: Replace status ternary chains
│   │   │   ├── ProjectBoard.tsx           # Key: cn() adoption
│   │   │   └── ...                        # Remaining board components
│   │   ├── chat/                           # MODIFIED: ~8 files — cn() adoption, token alignment
│   │   │   ├── MessageBubble.tsx          # Key: Replace template literals with cn()
│   │   │   ├── ChatPopup.tsx              # Key: Token alignment
│   │   │   └── ...                        # Remaining chat components
│   │   ├── agents/                         # MODIFIED: ~4 files — cn() adoption
│   │   │   ├── AddAgentModal.tsx          # Key: cn() adoption
│   │   │   └── ...
│   │   ├── chores/                         # MODIFIED: ~5 files — cn() adoption, token alignment
│   │   │   ├── ChoresPanel.tsx            # Key: cn() adoption
│   │   │   └── ...
│   │   └── settings/                       # MODIFIED: ~10 files — cn() adoption, token alignment
│   │       ├── SignalConnection.tsx        # Key: Centralize status colors
│   │       ├── McpSettings.tsx            # Key: Centralize indicator colors
│   │       └── ...
│   ├── pages/                              # MODIFIED: Minor token alignment where needed
│   │   ├── LoginPage.tsx                  # Review arbitrary values
│   │   ├── ProjectsPage.tsx               # Review sync status colors
│   │   └── ...
│   └── layout/                             # AUDITED: Mostly compliant, minor touch-ups
│       └── ...
└── tests/                                  # NO CHANGES to test files
```

**Structure Decision**: Web application (Option 2). All changes are within `frontend/src/`. No new directories are created. The approach modifies existing files in-place to adopt `cn()` and centralized theme tokens. New centralized color constants are added to the existing `constants.ts` file.

## Complexity Tracking

> No constitution violations. No complexity justifications needed.

*Table intentionally left empty — all design decisions favor simplicity per Principle V.*
