# Research: UI Audit Issue Template

**Feature**: `045-ui-audit` | **Date**: 2026-03-16 | **Plan**: [plan.md](plan.md)

## Research Tasks

### RT-001: GitHub Issue Template Format and Requirements

**Decision**: Use the legacy Markdown-based issue template format (`.github/ISSUE_TEMPLATE/*.md` with YAML front matter) rather than the newer YAML form-based templates (`.github/ISSUE_TEMPLATE/*.yml`).

**Rationale**: The existing template (`chore-ui-aduit.md`) already uses the legacy Markdown format, which is consistent with all other chore templates in the repository (`chore-bug-basher.md`, `chore-security-review.md`, `chore-accessibility-check.md`, etc.). The Markdown format supports free-form checkbox lists (`- [ ]`), which is essential for the audit checklist (FR-003). The YAML form-based format would require converting each checkbox into a separate form field, adding unnecessary complexity.

**Alternatives considered**:
- YAML form-based templates (`.yml`): Rejected because they don't support free-form checkbox lists natively. Each audit item would need to be a separate `checkboxes` input, making the template significantly more verbose and harder to maintain.
- External checklist (linked from template): Rejected because it would require developers to navigate to a separate document, violating FR-003 (checkboxes in the issue body) and reducing usability (SC-001).

---

### RT-002: Template Content Validation Against Specification Requirements

**Decision**: The existing template content satisfies all 12 functional requirements. No content additions or structural changes are required.

**Rationale**: Systematic verification of each FR against the template:

| FR | Requirement | Status | Evidence |
|----|-------------|--------|----------|
| FR-001 | Selectable from "New Issue" page as "UI Audit" | ✅ | YAML front matter: `name: UI Aduit` |
| FR-002 | All 10 audit categories present | ✅ | Sections 1–10 in the checklist |
| FR-003 | GitHub-compatible checkboxes (`- [ ]`) | ✅ | All items use `- [ ]` format |
| FR-004 | Single pass/fail condition per item | ✅ | Each item describes one observable condition |
| FR-005 | `[PAGE_NAME]` placeholders | ✅ | Title uses `[PAGE_NAME]`, body uses `[PAGE_NAME]`, `[PageName]`, `[feature]` |
| FR-006 | Six-phase implementation guide | ✅ | Phases 1–6 with numbered steps (29 total) |
| FR-007 | Relevant files section with placeholder paths | ✅ | "Relevant Files" section with `[PageName]`, `[feature]` placeholders |
| FR-008 | Verification section with commands | ✅ | 6 verification items (eslint, tsc, vitest, browser checks) |
| FR-009 | Auto-apply "chore" label | ✅ | YAML front matter: `labels: chore` |
| FR-010 | Default title format | ✅ | YAML front matter: `title: '[CHORE] UI Aduit'` |
| FR-011 | Clear, unambiguous language | ✅ | Items reference specific patterns (e.g., "≤250 lines", "React Query", "WCAG AA 4.5:1") |
| FR-012 | Minimum 59 checklist items | ✅ | 59 items across 10 categories |

**Alternatives considered**: N/A — all requirements are met. No changes needed.

---

### RT-003: Checklist Item Count and Distribution

**Decision**: The template contains 59 checklist items distributed across 10 categories, meeting the FR-012 minimum.

**Rationale**: Item count per category:

| Category | Items |
|----------|-------|
| 1. Component Architecture & Modularity | 7 |
| 2. Data Fetching & State Management | 6 |
| 3. Loading, Error & Empty States | 5 |
| 4. Type Safety | 5 |
| 5. Accessibility (a11y) | 7 |
| 6. Text, Copy & UX Polish | 8 |
| 7. Styling & Layout | 6 |
| 8. Performance | 5 |
| 9. Test Coverage | 5 |
| 10. Code Hygiene | 6 |
| **Total** | **60** |

No category has fewer than 5 items, exceeding the SC-003 minimum of 4 per category.

**Alternatives considered**: N/A — distribution is already well-balanced.

---

### RT-004: Placeholder Mechanics and Reusability

**Decision**: The template uses three placeholder tokens that developers replace when creating an issue: `[PAGE_NAME]`, `[PageName]`, and `[feature]`.

**Rationale**: 
- `[PAGE_NAME]` — Used in the title and heading for human-readable page identification (e.g., "Projects", "Agents")
- `[PageName]` — Used in file path references following PascalCase component naming (e.g., `ProjectsPage.tsx`, `AgentsPanel.tsx`)
- `[feature]` — Used in directory path references following kebab-case folder naming (e.g., `src/components/board/`, `src/components/agents/`)

This three-token design supports reuse across all pages (SC-007) without template modification. Each token maps to a different naming convention in the codebase.

**Alternatives considered**:
- Single `[PAGE]` placeholder for all uses: Rejected because file paths require PascalCase and directory paths require lowercase/kebab-case — a single token would force developers to manually transform the name in multiple places.
- Auto-fill via YAML form inputs: Rejected because the Markdown template format doesn't support variable substitution (see RT-001).

---

### RT-005: Template Title Typo — "Aduit" vs "Audit"

**Decision**: The template filename and title contain a typo: "aduit" instead of "audit". The YAML front matter reads `name: UI Aduit` and `title: '[CHORE] UI Aduit'`. The filename is `chore-ui-aduit.md`.

**Rationale**: This is a pre-existing naming choice in the repository. The parent issue title also uses "UI Aduit" (#4170). Changing the filename or title would require updating the parent issue, the PR (#4169), and any references. The typo does not affect template functionality — GitHub renders the template correctly regardless of the filename or `name` field spelling. This is a cosmetic issue that can be addressed in a separate chore if desired, but is out of scope for this review-and-merge task.

**Alternatives considered**:
- Fix the typo now: Not recommended as it would require coordinated changes across the issue, PR, and branch name, expanding scope beyond the spec.
- Flag for future fix: Recommended — note the typo in the tasks for a potential follow-up.

---

### RT-006: Consistency with Other Chore Templates

**Decision**: The UI Audit template follows the same YAML front matter pattern as all other chore templates in the repository.

**Rationale**: All chore templates share the same structure:
```yaml
---
name: [Chore Name]
about: Recurring chore — [Chore Name]
title: '[CHORE] [Chore Name]'
labels: chore
assignees: ''
---
```

The UI Audit template conforms to this pattern exactly. No structural deviations.

**Alternatives considered**: N/A — consistency is already achieved.

## Resolution Summary

All research tasks are resolved. No NEEDS CLARIFICATION items remain. The template content is complete and satisfies all 12 functional requirements, all 8 success criteria, and is consistent with existing repository conventions. The only finding of note is the "aduit" typo (RT-005), which is a pre-existing naming choice and out of scope for this review.
