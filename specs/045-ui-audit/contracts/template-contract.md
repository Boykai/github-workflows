# Contract: Issue Template Format and Content

**Feature**: `045-ui-audit` | **Date**: 2026-03-16 | **Data Model**: [data-model.md](../data-model.md)

## Overview

This contract defines the structural and content requirements for the UI Audit issue template. Since this feature is a static Markdown file (not an API or runtime component), the contract specifies the file format, YAML front matter schema, and content structure that the template must conform to.

## YAML Front Matter Contract

### Schema

```yaml
---
name: "UI Audit"
about: "Recurring chore — UI Audit"
title: "[CHORE] UI Audit"
labels: "chore"
assignees: ""
---
```

### Field Requirements

| Field | Required | Type | Constraint | FR |
|-------|----------|------|------------|-----|
| `name` | Yes | String | Must match template display name | FR-001 |
| `about` | Yes | String | Must describe the template purpose | — |
| `title` | Yes | String | Must follow `[CHORE] <name>` format | FR-010 |
| `labels` | Yes | String | Must include `chore` | FR-009 |
| `assignees` | No | String | Empty string (no default assignee) | — |

## Checklist Content Contract

### Category Structure

Each audit category MUST follow this Markdown structure:

```markdown
### N. Category Name

- [ ] **Item Label**: Item description with specific, observable pass/fail condition
```

### Category Requirements

| # | Category Name | Min Items | FR |
|---|---------------|-----------|-----|
| 1 | Component Architecture & Modularity | 4 | FR-002 |
| 2 | Data Fetching & State Management | 4 | FR-002 |
| 3 | Loading, Error & Empty States | 4 | FR-002 |
| 4 | Type Safety | 4 | FR-002 |
| 5 | Accessibility (a11y) | 4 | FR-002 |
| 6 | Text, Copy & UX Polish | 4 | FR-002 |
| 7 | Styling & Layout | 4 | FR-002 |
| 8 | Performance | 4 | FR-002 |
| 9 | Test Coverage | 4 | FR-002 |
| 10 | Code Hygiene | 4 | FR-002 |

**Constraints**:
- Exactly 10 categories (FR-002)
- Each category ≥4 items (SC-003)
- Total items ≥59 (FR-012)
- All items use `- [ ]` checkbox format (FR-003)
- Each item describes a single pass/fail condition (FR-004)

### Checklist Item Format

Each item MUST follow:

```markdown
- [ ] **Bold Label**: Description that states a specific, observable condition
```

**Valid examples**:
- `- [ ] **Single Responsibility**: Page file is ≤250 lines. If larger, extract sub-components into solune/frontend/src/components/[feature]/`
- `- [ ] **React Query for all API calls**: Uses useQuery / useMutation from TanStack Query — no raw useEffect + fetch`
- `- [ ] **No any types**: All props, state, API responses fully typed`

**Invalid examples**:
- `- [ ] Check the component` — Too vague, not a pass/fail condition
- `- [ ] **Good code**: Code should be well-written` — Subjective, not observable
- `- [ ] **Performance**: Check performance and fix issues` — Multiple conditions in one item

## Placeholder Contract

### Tokens

| Token | Case Convention | Usage Context | Example Substitution |
|-------|-----------------|---------------|---------------------|
| `[PAGE_NAME]` | Human-readable | Title, headings | "Projects", "Agents Pipeline" |
| `[PageName]` | PascalCase | Page component file references | `ProjectsPage.tsx`, `AgentsPipelinePage.tsx` |
| `[Feature]` | PascalCase | Hook file references after `use` | `Projects`, `Agents`, `Tools` |
| `[feature]` | lowercase/kebab | Directory path references | `board`, `pipeline`, `agents` |

### Substitution Rules

- All four tokens MUST appear in the template body (FR-005)
- Developers replace tokens when creating an issue — no automated substitution
- The template MUST instruct developers to append the audited page name to the default title before submitting the issue
- After substitution, all file paths MUST point to valid locations in `solune/frontend/src/` (US4-AC1)

## Implementation Guide Contract

### Phase Structure

```markdown
### Phase N: Phase Name

N. Step description — specific, actionable instruction
```

### Phase Requirements

| Phase | Name | Depends On | Step Count |
|-------|------|------------|------------|
| 1 | Discovery & Assessment | None | 9 |
| 2 | Structural Fixes (if needed) | Phase 1 | 4 |
| 3 | States & Error Handling | Phase 2 | 4 |
| 4 | a11y & UX Polish | Phase 3 | 5 |
| 5 | Testing | Phase 4 | 3 |
| 6 | Validation | Phase 5 | 4 |

**Constraints**:
- Exactly 6 phases (FR-006)
- Sequential dependency chain — each phase depends only on preceding phases (US3-AC4)
- Steps are numbered sequentially within each phase

## Verification Section Contract

### Required Checks

| # | Check Type | Tool/Method | Pass Condition | FR |
|---|-----------|-------------|----------------|-----|
| 1 | Lint | `cd solune/frontend && npx eslint` with page, component, and hook paths | 0 warnings | FR-008 |
| 2 | Type check | `cd solune/frontend && npx tsc --noEmit` | 0 errors | FR-008 |
| 3 | Tests | `cd solune/frontend && npx vitest run` | All tests pass | FR-008 |
| 4 | Visual (light) | Manual browser check | No visual defects | FR-008 |
| 5 | Visual (dark) | Manual browser check in dark mode | No visual defects | FR-008 |
| 6 | Keyboard | Manual keyboard-only navigation | All elements reachable | FR-008 |

## Relevant Files Section Contract

### Required File Categories

| Category | Placeholder Paths | FR |
|----------|-------------------|-----|
| Page & Components | `solune/frontend/src/pages/[PageName].tsx`, `solune/frontend/src/components/[feature]/` | FR-007 |
| Hooks & API | `solune/frontend/src/hooks/use[Feature].ts`, `solune/frontend/src/services/api.ts` | FR-007 |
| Types | `solune/frontend/src/types/index.ts` or `solune/frontend/src/types/[feature].ts` | FR-007 |
| Shared | `solune/frontend/src/components/ui/`, `solune/frontend/src/components/common/`, `solune/frontend/src/lib/utils.ts` | FR-007 |
| Tests | `solune/frontend/src/hooks/use[Feature].test.ts`, `solune/frontend/src/pages/[PageName].test.tsx`, `solune/frontend/src/components/[feature]/**/*.test.tsx` | FR-007 |

**Constraints**:
- Paths use placeholder tokens defined in the Placeholder Contract above
- Shared component paths reference actual primitives (Button, Card, Input, Tooltip, ConfirmationDialog) and common components (CelestialLoader, ErrorBoundary, ProjectSelectionEmptyState) per US4-AC2
